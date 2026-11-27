# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from myeasymp3toiphone.gui.browser import KEY_ROLE, LibraryBrowser
from myeasymp3toiphone.library import Track, assign_groups, group_by_album
from myeasymp3toiphone.tags import TrackTags


def _tracks():
    rows = [("Queen", "Innuendo", "1991", 3), ("Queen", "A Night at the Opera", "1975", 2),
            ("ABBA", "Arrival", "1976", 4)]
    tracks = []
    for artist, album, year, count in rows:
        for number in range(1, count + 1):
            tags = TrackTags(title=f"{album} {number}", artist=artist, album=album, year=year, track_number=number)
            tracks.append(Track(path=__import__("pathlib").Path(f"C:/m/{artist}/{album}/{number}.mp3"), tags=tags))
    assign_groups(tracks)
    return tracks


def _texts(widget, column=0):
    result = []
    for index in range(widget.topLevelItemCount()):
        result.append(widget.topLevelItem(index).text(column))
    return result


def test_artist_then_album_filter_and_pinned_row():
    _app = QApplication.instance() or QApplication([])
    browser = LibraryBrowser()
    browser.set_data(group_by_album(_tracks()), {})
    assert _texts(browser.artists)[0].startswith("(Tutti gli artisti: 2)")
    assert _texts(browser.artists)[1:] == ["ABBA", "Queen"]
    assert browser.track_filter() is None
    # ordinamento decrescente per nome: "(Tutti …)" resta in cima
    browser.artists.sortByColumn(0, Qt.DescendingOrder)
    assert _texts(browser.artists)[0].startswith("(Tutti") and _texts(browser.artists)[1:] == ["Queen", "ABBA"]
    # ordinamento per numero di brani
    browser.artists.sortByColumn(2, Qt.DescendingOrder)
    assert _texts(browser.artists)[1:] == ["Queen", "ABBA"]
    # un artista: gli album si riducono ai suoi
    queen = [browser.artists.topLevelItem(i) for i in range(3) if browser.artists.topLevelItem(i).text(0) == "Queen"]
    queen[0].setSelected(True)
    assert browser.track_filter() == ({"Queen"}, set())
    assert sorted(_texts(browser.albums)[1:]) == ["A Night at the Opera", "Innuendo"]
    # un album
    for index in range(browser.albums.topLevelItemCount()):
        item = browser.albums.topLevelItem(index)
        if item.text(0) == "Innuendo":
            item.setSelected(True)
    assert browser.track_filter() == ({"Queen"}, {("Queen", "Innuendo")})
    # i dati ricaricati conservano la scelta
    browser.set_data(group_by_album(_tracks()), {})
    assert browser.track_filter() == ({"Queen"}, {("Queen", "Innuendo")})
    browser.clear_selection()
    assert browser.track_filter() is None
    assert browser.albums.topLevelItem(1).data(0, KEY_ROLE) is not None


def test_choosing_an_artist_resets_the_album_choice():
    _app = QApplication.instance() or QApplication([])
    browser = LibraryBrowser()
    browser.set_data(group_by_album(_tracks()), {})
    for index in range(browser.albums.topLevelItemCount()):
        if browser.albums.topLevelItem(index).text(0) == "Arrival":
            browser.albums.topLevelItem(index).setSelected(True)
    assert browser.track_filter() == (set(), {("ABBA", "Arrival")})
    browser.artists.topLevelItem(0).setSelected(True)   # "(Tutti gli artisti)"
    assert browser.track_filter() is None


def test_format_filter_in_main_window(tmp_path, monkeypatch):
    from myeasymp3toiphone.gui import main_window as mw
    _app = QApplication.instance() or QApplication([])
    window = mw.MainWindow()
    tracks = _tracks()
    tracks[0].path = tracks[0].path.with_suffix(".flac")
    window.tracks = tracks
    window._rebuild_views()
    assert window._format.itemText(2) == "FLAC (1)" and window._format.itemText(1) == "MP3 (8)"
    window._format.setCurrentIndex(2)
    assert [t.path.suffix for t in window.format_tracks()] == [".flac"]
    assert window._model.rowCount() == 1


def _wait(window, app, seconds=20):
    import time
    end = time.time() + seconds
    app.processEvents()
    time.sleep(0.1)
    while window.runner.is_busy and time.time() < end:
        app.processEvents()
        time.sleep(0.02)
    app.processEvents()


def test_last_opened_folder_is_reopened(tmp_path):
    from conftest import write_mp3
    from myeasymp3toiphone.config import AppSettings
    from myeasymp3toiphone.gui import main_window as mw
    app = QApplication.instance() or QApplication([])
    music = tmp_path / "musica"
    write_mp3(music / "a.mp3")
    library = tmp_path / "libreria"
    library.mkdir()
    AppSettings(library_dir=str(library), last_opened=str(music)).save()
    window = mw.MainWindow()   # _startup parte da solo, con il primo giro di eventi
    _wait(window, app)
    assert window.root_folder == music and len(window.tracks) == 1
    # cartella non più disponibile: le cartelle della musica (qui la Libreria sola), con un avviso
    AppSettings(library_dir=str(library), last_opened=str(tmp_path / "sparita")).save()
    window = mw.MainWindow()
    _wait(window, app)
    assert window.root_folder == library and window.showing_music()
    assert AppSettings.load().last_opened == mw.MUSIC_MARK      # ora sono aperte le cartelle della musica


def test_music_folders_of_this_computer(tmp_path):
    """Più cartelle della musica per questo computer: si aprono insieme, la Libreria è una di loro, l'ordine vale tra
    copie uguali; le cartelle di un altro computer non si usano."""
    from conftest import write_mp3
    from myeasymp3toiphone.config import AppSettings, computer_name
    from myeasymp3toiphone.gui import main_window as mw
    app = QApplication.instance() or QApplication([])
    first = tmp_path / "Musica"
    second = tmp_path / "Archivio FLAC"
    write_mp3(first / "Gruppo" / "a.mp3")
    write_mp3(second / "Gruppo" / "b.mp3")
    write_mp3(second / "Gruppo" / "c.mp3")
    settings = AppSettings(last_opened=mw.MUSIC_MARK)
    settings.set_music_dirs([str(first), str(second)], str(second))
    settings.music_folders["ALTRO-PC"] = {"folders": ["Z:\\Altrove"], "library": "Z:\\Altrove"}
    settings.save()
    loaded = AppSettings.load()
    assert loaded.music_dirs() == [first, second] and loaded.library_path() == second
    assert loaded.library_dir == str(second)                    # una versione precedente trova la Libreria
    assert loaded.other_computers() == {"ALTRO-PC": ["Z:\\Altrove"]} and computer_name() in loaded.music_folders
    window = mw.MainWindow()
    _wait(window, app)
    assert window.root_folders == [first, second] and len(window.tracks) == 3 and window.showing_music()
    assert window.root_folder is None and window.is_open(second / "Gruppo" / "b.mp3")
    assert window.preferred_order()[-2:] == (str(first), str(second))
    assert window._folders_combo.currentIndex() == 0 and window._folders_combo.count() == 4   # tutte, 2, altra…
    assert "(Libreria)" in window._folders_combo.itemText(2)
    window.load_folder(first)                                   # una sola dall'elenco
    _wait(window, app)
    assert window.root_folder == first and not window.showing_music() and window._folders_combo.currentIndex() == 1
    window._exit_checked = True
    window.close()


def test_nested_music_folders_read_once(tmp_path, monkeypatch):
    """Una cartella della musica dentro un'altra (la Libreria dentro la cartella principale) si legge una volta sola;
    in Impostazioni la stessa cartella scritta con "/" non si aggiunge due volte."""
    from pathlib import Path
    from conftest import write_mp3
    from myeasymp3toiphone.config import AppSettings
    from myeasymp3toiphone.gui import main_window as mw
    from myeasymp3toiphone.gui.settings_dialog import SettingsDialog
    app = QApplication.instance() or QApplication([])
    main = tmp_path / "Musica"
    library = main / "Libreria"
    write_mp3(main / "Gruppo" / "a.mp3")
    write_mp3(library / "Gruppo" / "b.mp3")
    assert mw.outermost_folders([library, main, Path(str(main).upper())]) == [main]
    assert mw.outermost_folders([main, tmp_path / "Musica2"]) == [main, tmp_path / "Musica2"]
    scanned = []
    original = mw.scan_folder

    def counting(folder, *args):
        scanned.append(folder)
        result = original(folder, *args)
        return result

    monkeypatch.setattr(mw, "scan_folder", counting)
    settings = AppSettings(last_opened=mw.MUSIC_MARK)
    settings.set_music_dirs([str(main), str(library)], str(library))
    settings.save()
    window = mw.MainWindow()
    _wait(window, app)
    assert scanned == [main] and len(window.tracks) == 2 and window.showing_music()
    window._exit_checked = True
    window.close()
    dialog = SettingsDialog(AppSettings.load())
    count = dialog.f_list.count()
    assert not dialog.add_music_folder(str(main).replace("\\", "/"))
    assert dialog.add_music_folder(str(tmp_path / "Altro").replace("\\", "/"))
    assert dialog.f_list.count() == count + 1 and dialog.music_folders()[-1] == str(tmp_path / "Altro")
    dialog.reject()

    # Associa sorgenti: le cartelle che ci sono (una volta sola), quelle scollegate a parte, il campo vuoto non vale
    from myeasymp3toiphone.gui.iphone_panel import adopt_folders
    gone = tmp_path / "Disco scollegato"
    assert adopt_folders([main, library, gone]) == ([main], [str(gone)])
    assert adopt_folders([Path("")]) == ([], [])


def test_settings_folders_tab_remove_library_open_folder_and_excluded(tmp_path):
    """Impostazioni → Cartelle della musica: la Libreria si toglie se resta un'altra cartella (diventa Libreria la
    prima che resta), la cartella aperta con Apri cartella si aggiunge con un pulsante, le cartelle escluse sono
    hidden_folders."""
    from myeasymp3toiphone.config import AppSettings
    from myeasymp3toiphone.gui.settings_dialog import SettingsDialog
    QApplication.instance() or QApplication([])
    library = tmp_path / "Libreria"
    opened = tmp_path / "Musica"
    opened.mkdir()
    settings = AppSettings(library_dir=str(library), last_opened=str(opened),
                           hidden_folders=[str(opened / "Vecchie")])
    dialog = SettingsDialog(settings)
    assert dialog.music_folders() == [str(library)]
    dialog.f_list.setCurrentRow(0)
    assert not dialog.f_remove.isEnabled()                       # l'ultima cartella non si toglie
    assert dialog.open_folder() == str(opened) and not dialog.f_add_open.isHidden()
    dialog._add_open_folder()
    assert dialog.music_folders() == [str(library), str(opened)] and dialog.open_folder() == ""
    assert dialog.f_add_open.isHidden()
    dialog.f_list.setCurrentRow(0)
    assert dialog.f_remove.isEnabled()
    dialog._remove_folder()                                       # la Libreria: diventa Libreria quella che resta
    assert dialog.music_folders() == [str(opened)] and dialog._library == str(opened)
    assert dialog.excluded_folders() == [str(opened / "Vecchie")]
    assert dialog.add_excluded_folder(str(opened / "Suonerie").replace("\\", "/"))
    assert not dialog.add_excluded_folder(str(opened / "SUONERIE"))
    dialog.x_list.setCurrentRow(0)
    dialog._remove_excluded()
    dialog.accept()
    assert settings.hidden_folders == [str(opened / "Suonerie")]
    assert settings.music_dirs() == [opened] and settings.library_path() == opened


def test_hide_folder_in_pc_tab(tmp_path):
    """Nascondi la cartella: i suoi brani (e quelli delle sottocartelle) spariscono dalla scheda PC, si ricorda, si
    mostrano di nuovo. I file non cambiano."""
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from pathlib import Path
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.config import AppSettings
    from myeasymp3toiphone.gui.main_window import MainWindow
    from myeasymp3toiphone.library import Track, assign_groups
    from myeasymp3toiphone.tags import TrackTags
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        tracks = []
        for folder, title in (("A", "Uno"), ("A/CD2", "Due"), ("AB", "Tre"), ("B", "Quattro")):
            tracks.append(Track(path=Path(f"C:/musica/{folder}/{title}.mp3"),
                                tags=TrackTags(title=title, artist="X", album="Y")))
        assign_groups(tracks)
        window._all_tracks = list(tracks)
        window.tracks = list(tracks)
        window._rebuild_views()
        window.hide_folders([Path("C:/musica/A")])
        assert sorted(track.title for track in window.tracks) == ["Quattro", "Tre"]     # "AB" non è dentro "A"
        assert AppSettings.load().hidden_folders == [str(Path("C:/musica/A"))]
        assert window._hidden_button.text().startswith("Cartelle nascoste (1)")
        window.app_settings.hidden_folders = []
        window._apply_hidden()
        assert len(window.tracks) == 4
    finally:
        window.close()
        app.processEvents()


def test_clipboard_menu_copies_folder_names_and_paths():
    """Copia negli appunti: nome e percorso della cartella, ogni cartella una volta sola."""
    from pathlib import Path
    from PySide6.QtWidgets import QMenu
    from myeasymp3toiphone.gui.file_actions import add_file_entries
    app = QApplication.instance() or QApplication([])
    paths = [Path("C:/m/Gruppo Finto/Disco Uno/1.mp3"), Path("C:/m/Gruppo Finto/Disco Uno/2.mp3"),
             Path("C:/m/Gruppo Finto/Disco Due/1.mp3")]
    said = []
    menu = QMenu()
    add_file_entries(menu, paths, said.append)
    clipboard = menu.actions()[0].menu()
    actions = {}
    for action in clipboard.actions():
        actions[action.text()] = action
    assert list(actions) == ["Nome del file (3)", "Percorso completo (3)", "Nome della cartella (2)",
                             "Percorso della cartella (2)"]
    actions["Nome della cartella (2)"].trigger()
    assert app.clipboard().text() == "Disco Uno\nDisco Due"
    actions["Percorso della cartella (2)"].trigger()
    assert app.clipboard().text().splitlines() == [str(paths[0].parent), str(paths[2].parent)]
    assert said[-1] == "Copiati negli appunti i percorsi di 2 cartelle"


def test_changing_an_album_row_is_not_a_click_on_its_iphone_tick():
    """Una spunta "sull'iPhone" a metà (album solo in parte sull'iPhone) non deve diventare "toglilo" quando la riga
    cambia per altro (l'icona della Verifica online): era successo, con 45 brani messi in coda da eliminare."""
    from types import SimpleNamespace
    _app = QApplication.instance() or QApplication([])
    browser = LibraryBrowser()
    browser.phone_state = lambda tracks: (Qt.PartiallyChecked, False)
    browser.set_data(group_by_album(_tracks()), {})
    emitted = []
    browser.phone_toggled.connect(lambda tracks, checked: emitted.append((len(tracks), checked)))
    result = SimpleNamespace(status="incomplete", status_text=lambda: "Incompleto")
    browser.refresh_check_icons({("Queen", "Innuendo"): result})
    item = None
    for index in range(browser.albums.topLevelItemCount()):
        if browser.albums.topLevelItem(index).data(0, KEY_ROLE) == ("Queen", "Innuendo"):
            item = browser.albums.topLevelItem(index)
    item.setToolTip(0, "un altro cambio della riga")                 # anche senza segnali fermi: niente
    item.setText(0, "Innuendo")
    assert emitted == []
    item.setCheckState(0, Qt.Unchecked)                              # il clic vero sulla spunta
    assert emitted == [(3, False)]
