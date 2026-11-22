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
    # cartella non più disponibile: la Libreria, con un avviso
    AppSettings(library_dir=str(library), last_opened=str(tmp_path / "sparita")).save()
    window = mw.MainWindow()
    _wait(window, app)
    assert window.root_folder == library
    assert AppSettings.load().last_opened == str(library)   # ora l'ultima usata è la Libreria


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
