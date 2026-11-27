# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La musica dell'app Musica dell'iPhone: lettura del database (un database finto con le stesse tabelle), elenco nella
cartella dati, confronto con il PC, scansione e scheda iPhone. Nomi e valori inventati, nessun iPhone vero."""

import os
import shutil
import sqlite3
from pathlib import Path

from conftest import write_mp3
from myeasymp3toiphone import phone_library, scan
from myeasymp3toiphone.config import config_dir
from myeasymp3toiphone.library import Track, scan_folder
from myeasymp3toiphone.phone_library import (
    DEVICE_ABSENT, DEVICE_SAME, DEVICE_STALE, PhoneIndex, PhoneTrack, device_status, differences, read_music_database,
)
from myeasymp3toiphone.tags import TrackTags, write_tags

SCHEMA = """
CREATE TABLE item (item_pid INTEGER PRIMARY KEY, media_type INTEGER, item_artist_pid INTEGER, album_pid INTEGER,
                   album_artist_pid INTEGER, genre_id INTEGER, disc_number INTEGER, track_number INTEGER,
                   base_location_id INTEGER, is_compilation INTEGER DEFAULT 0);
CREATE TABLE item_extra (item_pid INTEGER PRIMARY KEY, title TEXT, disc_count INTEGER, track_count INTEGER,
                         total_time_ms INTEGER, year INTEGER, location TEXT, file_size INTEGER);
CREATE TABLE item_artist (item_artist_pid INTEGER PRIMARY KEY, item_artist TEXT);
CREATE TABLE album_artist (album_artist_pid INTEGER PRIMARY KEY, album_artist TEXT, sync_id INTEGER);
CREATE TABLE album (album_pid INTEGER PRIMARY KEY, album TEXT, album_artist_pid INTEGER, sync_id INTEGER);
CREATE TABLE item_store (item_pid INTEGER PRIMARY KEY, sync_id INTEGER);
CREATE TABLE genre (genre_id INTEGER PRIMARY KEY, genre TEXT);
CREATE TABLE base_location (base_location_id INTEGER PRIMARY KEY, path TEXT);
"""


def _add(connection, pid, title, artist, album, year=0, track=0, disc=0, genre=0, location="", base=1,
         album_artist=0, ms=200000):
    connection.execute("INSERT INTO item VALUES (?, 8, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (pid, artist, album, album_artist, genre, disc, track, base, 1 if album_artist else 0))
    connection.execute("INSERT INTO item_extra VALUES (?, ?, 1, 12, ?, ?, ?, 5000000)",
                       (pid, title, ms, year, location))
    connection.execute("INSERT INTO item_store VALUES (?, ?)", (pid, -pid))   # sync_id negativo: 64 bit con segno


def _database(path: Path, wal: bool = False):
    """Un database come quello dell'iPhone. Con wal=True le righe restano nel file -wal (connessione aperta)."""
    connection = sqlite3.connect(str(path))
    if wal:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA wal_autocheckpoint=0")
    connection.executescript(SCHEMA)
    connection.executemany("INSERT INTO item_artist VALUES (?, ?)", [(1, "Artista Uno"), (2, "Artista Due")])
    connection.executemany("INSERT INTO album_artist VALUES (?, ?, ?)", [(1, "Artisti vari", 7001)])
    connection.executemany("INSERT INTO album VALUES (?, ?, ?, ?)", [(1, "Album Primo", 0, 8001),
                                                                    (2, "Raccolta", 1, 8002)])
    connection.executemany("INSERT INTO genre VALUES (?, ?)", [(1, "Rock")])
    connection.executemany("INSERT INTO base_location VALUES (?, ?)", [(1, "iTunes_Control/Music/F01")])
    _add(connection, 101, "Canzone A", 1, 1, year=1991, track=1, genre=1, location="ABCD.mp3")
    _add(connection, 102, "Canzone B", 1, 1, year=1991, track=2, disc=2, location="EFGH.mp3")
    _add(connection, 103, "Canzone C", 2, 2, location="IJKL.mp3", album_artist=1)
    _add(connection, 104, "Solo in streaming", 2, 2, location="", base=0)   # nessun file sull'iPhone
    connection.commit()
    return connection


def _phone(pid, title, artist, album, **values):
    tags = TrackTags(title=title, artist=artist, album=album, **values)
    result = PhoneTrack(pid=pid, remote_path=f"/iTunes_Control/Music/F01/{pid}.mp3", size=100, length=200.0,
                        tags=tags)
    return result


def _pc(title, artist, album, **values):
    result = Track(path=Path(f"C:/musica/{artist}/{album}/{title}.mp3"),
                   tags=TrackTags(title=title, artist=artist, album=album, **values))
    return result


def test_read_music_database(tmp_path):
    _database(tmp_path / "MediaLibrary.sqlitedb").close()
    tracks = read_music_database(tmp_path / "MediaLibrary.sqlitedb")
    assert [t.pid for t in tracks] == [101, 102, 103]            # ordinati per artista/album; lo streaming no
    first = tracks[0]
    assert first.remote_path == "/iTunes_Control/Music/F01/ABCD.mp3" and first.length == 200.0
    assert (first.tags.title, first.tags.artist, first.tags.album, first.tags.year, first.tags.genre,
            first.tags.track_number, first.tags.disc_number) == ("Canzone A", "Artista Uno", "Album Primo", "1991",
                                                                "Rock", 1, None)
    assert tracks[1].tags.disc_number == 2
    third = tracks[2]
    assert third.tags.album_artist == "Artisti vari" and third.tags.year == "" and third.tags.track_number is None
    assert third.display_artist == "Artisti vari" and third.tags.compilation and not first.tags.compilation
    assert third.sync_id == (1 << 64) - 103 and third.album_sync_id == 8002 and third.artist_sync_id == 7001
    assert first.from_computer and first.album_sync_id == 8001


def test_playlists_of_each_track(tmp_path):
    connection = _database(tmp_path / "MediaLibrary.sqlitedb")
    connection.executescript("""
CREATE TABLE container (container_pid INTEGER PRIMARY KEY, distinguished_kind INTEGER, is_hidden INTEGER,
                        smart_criteria BLOB, smart_is_folder INTEGER, name TEXT);
CREATE TABLE container_item (container_item_pid INTEGER PRIMARY KEY, container_pid INTEGER, item_pid INTEGER,
                             position INTEGER);
INSERT INTO container VALUES (1, 0, 1, NULL, 0, 'Libreria'), (2, 0, 0, NULL, 0, 'In auto'),
                             (3, 0, 0, x'00', 0, 'Smart'), (4, 10000, 1, NULL, 0, 'Cronologia'),
                             (5, 0, 0, NULL, 0, 'Corsa');
INSERT INTO container_item VALUES (1, 1, 101, 0), (2, 2, 101, 0), (3, 3, 101, 0), (4, 4, 101, 0), (5, 5, 101, 1),
                                  (6, 5, 102, 0), (7, 2, 101, 3);
""")
    connection.commit()
    connection.close()
    tracks = {t.pid: t for t in read_music_database(tmp_path / "MediaLibrary.sqlitedb")}
    assert tracks[101].playlists == ("Corsa", "In auto") and tracks[102].playlists == ("Corsa",)
    assert tracks[103].playlists == ()
    phone_library.save_listing(tmp_path, "iPhone", list(tracks.values()))
    again = {t.pid: t for t in phone_library.load_listing(tmp_path)["tracks"]}
    assert again[101].playlists == ("Corsa", "In auto")
    reminder = phone_library.playlist_reminder(list(tracks.values()))
    assert reminder.splitlines() == ["• Corsa: Canzone A, Canzone B", "• In auto: Canzone A"]


def test_playlists_of_a_computer_are_told_apart(tmp_path):
    """Le playlist messe da un computer (sync_id) si rifanno da sole dopo un rimpiazzo: il promemoria nomina solo
    quelle fatte sul telefono; i brani di ogni playlist si leggono nel loro ordine."""
    connection = _database(tmp_path / "MediaLibrary.sqlitedb")
    connection.executescript("""
CREATE TABLE container (container_pid INTEGER PRIMARY KEY, distinguished_kind INTEGER, is_hidden INTEGER,
                        smart_criteria BLOB, smart_is_folder INTEGER, name TEXT, sync_id INTEGER);
CREATE TABLE container_item (container_item_pid INTEGER PRIMARY KEY, container_pid INTEGER, item_pid INTEGER,
                             position INTEGER);
CREATE TABLE db_info (primary_container_pid INTEGER);
INSERT INTO db_info VALUES (1);
INSERT INTO container VALUES (1, 0, 1, NULL, 0, 'Libreria', 0), (2, 0, 0, NULL, 0, 'In auto', 0),
                             (5, 0, 0, NULL, 0, '♪ Gruppo Finto', -9001);
INSERT INTO container_item VALUES (1, 1, 101, 0), (2, 2, 101, 0), (5, 5, 101, 1), (6, 5, 102, 0);
""")
    connection.commit()
    connection.close()
    tracks = {t.pid: t for t in read_music_database(tmp_path / "MediaLibrary.sqlitedb")}
    assert tracks[101].playlists == ("In auto", "♪ Gruppo Finto")
    assert tracks[101].computer_playlists == ("♪ Gruppo Finto",) and tracks[102].computer_playlists == ("♪ Gruppo Finto",)
    items = [tracks[101], tracks[102]]
    assert phone_library.playlist_reminder(items).splitlines() == ["• In auto: Canzone A"]
    assert phone_library.playlist_reminder(items, from_computer=True).splitlines() == [
        "• ♪ Gruppo Finto: Canzone A, Canzone B"]
    phone_library.save_listing(tmp_path, "iPhone", list(tracks.values()))
    again = {t.pid: t for t in phone_library.load_listing(tmp_path)["tracks"]}
    assert again[101].computer_playlists == ("♪ Gruppo Finto",)
    members = {}
    for playlist, sync_ids in phone_library.playlist_members(tmp_path / "MediaLibrary.sqlitedb"):
        members[playlist.name] = (playlist.from_computer, sync_ids)
    big = 1 << 64
    assert members == {"In auto": (False, [big - 101]), "♪ Gruppo Finto": (True, [big - 102, big - 101])}


def test_playlist_after_a_replacement_keeps_its_order():
    """Dopo un rimpiazzo la playlist ha il brano nuovo al posto di quello vecchio; un brano sparito esce; se un brano
    nuovo non c'è ancora, la playlist non si rifà (per non perderlo)."""
    from myeasymp3toiphone.phone_actions import _replaced_ids, _Pending, restored_members
    assert restored_members([1, 2, 3, 4], {2: 20}, {1, 20, 3}) == ([1, 20, 3], True)    # il 4 non c'è più
    assert restored_members([1, 2], {2: 20}, {1}) == ([1], False)
    sent = [_Pending(None, None, 2), _Pending(None, None, 5), _Pending(None, None, 0)]
    sent[0].sent_as, sent[1].sent_as, sent[2].sent_as = 20, 50, 70
    assert _replaced_ids(sent, [2]) == {2: 20}           # il 5 vecchio non è stato tolto: due copie, niente scambio
    from myeasymp3toiphone.gui.iphone_panel import apply_report_text
    from myeasymp3toiphone.phone_actions import ActionReport
    report = ActionReport(playlists_restored=["♪ Gruppo Finto", "Corsa"])
    assert "• 2 playlist rifatte con i brani ricopiati: ♪ Gruppo Finto, Corsa" in apply_report_text(report, [], 0)


def test_read_music_database_with_pending_wal_and_no_shm(tmp_path):
    """Il programma scarica il database e il file -wal, non il -shm: le ultime modifiche devono esserci."""
    source = tmp_path / "iphone"
    source.mkdir()
    connection = _database(source / "MediaLibrary.sqlitedb", wal=True)
    try:
        assert (source / "MediaLibrary.sqlitedb-wal").stat().st_size > 0
        copy = tmp_path / "copia"
        copy.mkdir()
        for name in ("MediaLibrary.sqlitedb", "MediaLibrary.sqlitedb-wal"):
            shutil.copyfile(source / name, copy / name)
    finally:
        connection.close()
    assert len(read_music_database(copy / "MediaLibrary.sqlitedb")) == 3


def test_unreadable_database_gives_readable_error(tmp_path):
    (tmp_path / "MediaLibrary.sqlitedb").write_bytes(b"non un database")
    try:
        read_music_database(tmp_path / "MediaLibrary.sqlitedb")
        raised = False
    except phone_library.PhoneLibraryError as exc:
        raised = "non si legge" in str(exc)
    assert raised


def test_listing_round_trip(tmp_path):
    tracks = [_phone(1, "Canzone A", "Artista Uno", "Album Primo", year="1991", track_number=1)]
    phone_library.save_listing(tmp_path, "iPhone di prova", tracks)
    listing = phone_library.load_listing(tmp_path)
    assert listing["device"] == "iPhone di prova" and listing["tracks"] == tracks
    assert phone_library.load_listing(tmp_path / "nessuna") == {}


def test_device_status_by_artist_album_and_title():
    phone = [_phone(1, "Canzone A", "Artista Uno", "Album Primo", year="1991", track_number=1),
             _phone(2, "Intro", "Artista Uno", "Album Primo", year="1991", track_number=2)]
    index = PhoneIndex(phone)
    same = _pc("canzone  a", "ARTISTA UNO", "Album Primo", year="1991-05-01", track_number=1)
    status, item, found = device_status(same, index)
    assert item.pid == 1 and status == DEVICE_STALE and [label for label, _pc_value, _value in found] == \
        ["Titolo"]   # ritrovato senza badare a maiuscole e spazi; gli spazi diversi sono una differenza, le sole
    # maiuscole no (l'artista)
    exact = _pc("Canzone A", "Artista Uno", "Album Primo", year="1991", track_number=1, disc_number=1)
    assert device_status(exact, index)[0] == DEVICE_SAME   # anno e disco 1 / nessun disco sono uguali
    other_artist = _pc("Intro", "Artista Due", "Album Primo")
    assert device_status(other_artist, index)[0] == DEVICE_ABSENT   # stesso titolo e album, artista diverso
    edited = _pc("Canzone A (nuovo)", "Artista Uno", "Album Primo", year="1991", track_number=1)
    edited.original_tags = TrackTags(title="Canzone A", artist="Artista Uno", album="Album Primo", year="1991",
                                     track_number=1)
    status, item, found = device_status(edited, index)     # rinominato sul PC: si ritrova con i tag del file
    assert item.pid == 1 and status == DEVICE_STALE and found[0][1:] == ("Canzone A (nuovo)", "Canzone A")
    assert "sul PC \"Canzone A (nuovo)\"" in phone_library.describe_differences(found)


def test_compare_with_library_and_scan(tmp_path):
    for number, title in enumerate(["Canzone A", "Canzone B", "Canzone C"], start=1):
        write_mp3(tmp_path / f"{number}.mp3", 40)
        write_tags(tmp_path / f"{number}.mp3", TrackTags(title=title, artist="Artista Uno", album="Album Primo",
                                                         year="1991", track_number=number))
    library = scan_folder(tmp_path)
    phone = [_phone(1, "Canzone A", "Artista Uno", "Album Primo", year="1991", track_number=1),
             _phone(2, "Canzone B", "Artista Uno", "Album Primo", year="1990", track_number=2),
             _phone(3, "Altra", "Artista Due", "Album Secondo"),
             _phone(4, "Altra", "Artista Due", "Album Secondo")]
    issues = scan.compare_with_library(phone, library)
    by_rule = {issue.rule_id: issue for issue in issues}
    assert set(by_rule) == {"I1", "I2.1", "I3"}
    assert [Path(p).name for p in by_rule["I1"].files] == ["2.mp3"]          # anno diverso
    assert [Path(p).name for p in by_rule["I2.1"].files] == ["3.mp3"]        # manca sull'iPhone
    assert len(by_rule["I3"].files) == 2 and all(issue.fix is None for issue in issues)
    tracks = phone_library.tracks_for_scan(phone)
    assert len({str(t.path) for t in tracks}) == 4                            # i doppi hanno percorsi distinti
    assert str(tracks[0].path) == os.path.join("iPhone", "Artista Uno", "Album Primo (1991)", "01 - Canzone A.mp3")
    report = scan.scan_tracks(tracks, "iPhone", check_files=False, phone_tracks=phone, library_tracks=library)
    kinds = {issue.kind for issue in report.issues}
    assert scan.KIND_DUPLICATE in kinds and scan.KIND_ONLY_ON_DEVICE in kinds


def test_iphone_tab_shows_music_and_pc_status(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui import iphone_panel
    from myeasymp3toiphone.gui.main_window import COL_DEVICE, MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        window.tracks = [_pc("Canzone A", "Artista Uno", "Album Primo", year="1991", track_number=1),
                         _pc("Canzone B", "Artista Uno", "Album Primo", year="1991", track_number=2)]
        window._rebuild_views()
        phone = [_phone(1, "Canzone A", "Artista Uno", "Album Primo", year="1991", track_number=1),
                 _phone(2, "Canzone B", "Artista Uno", "Album Primo", year="1990", track_number=2),
                 _phone(3, "Solo qui", "Artista Due", "Album Secondo")]
        window.set_phone_tracks(phone, "iPhone di prova")
        assert phone_library.load_listing(config_dir())["device"] == "iPhone di prova"   # ricordato
        panel = window.iphone_panel
        panel.pc_changed()
        panel._refresh_pc_column()
        view = panel._music_view
        statuses = {}
        for index in range(view.topLevelItemCount()):
            row = view.topLevelItem(index)
            statuses[row.text(iphone_panel.COL_TITLE)] = row.text(iphone_panel.COL_PC)
        # abbinati solo per i tag: da rivedere (≈), sia nella scheda iPhone sia nella colonna iPhone del PC
        assert statuses == {"Canzone A": "≈", "Canzone B": "≈", "Solo qui": ""}
        table_status = set()
        for row in range(window._model.rowCount()):
            table_status.add(window._model.data(window._model.index(row, COL_DEVICE)))
        assert table_status == {"≈"}
        from myeasymp3toiphone.gui.track_model import COL_FILE, COL_FOLDER
        assert window._model.data(window._model.index(0, COL_FOLDER)) == "Album Primo"      # la cartella, poi il file
        assert window._model.data(window._model.index(0, COL_FILE)).endswith(".mp3")
        window.app_settings.show_full_path = True
        assert window._model.data(window._model.index(0, COL_FOLDER)) == str(window._model.track(0).path.parent)
        window.app_settings.show_full_path = False
        panel._search.setText("solo")
        assert panel._count.text() == "1 di 3 brani"
    finally:
        window.close()
        app.processEvents()


def test_registry_link_wins_over_tag_match(tmp_path):
    """Un file collegato nel registro è quel brano; un doppione con gli stessi tag non lo "ruba"."""
    from myeasymp3toiphone.overlay import path_key
    phone = [_phone(1, "Canzone A", "Artista Uno", "Hits 2005")]
    phone[0].sync_id = 77
    linked = _pc("Canzone A", "Artista Uno", "Album vero")              # tag diversi: si trova solo dal registro
    linked.path = tmp_path / "vero.mp3"
    duplicate = _pc("Canzone A", "Artista Uno", "Hits 2005")            # tag uguali ma non è il file collegato
    index = PhoneIndex(phone, {path_key(linked.path): 77})
    assert index.find(linked) is phone[0] and index.find(duplicate) is None
    status, _item, found = device_status(linked, index)
    assert status == DEVICE_STALE and [label for label, _a, _b in found] == ["Album"]
    assert PhoneIndex(phone).find(duplicate) is phone[0]                 # senza registro: per tag, come prima


def test_iphone_tab_origin_column_and_filter(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import provenance
    from myeasymp3toiphone.gui import iphone_panel
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        here = tmp_path / "presente.mp3"
        here.write_bytes(b"x")
        phone = [_phone(1, "Collegato", "A", "B"), _phone(2, "Sparito", "A", "B"), _phone(3, "Ignoto", "A", "B"),
                 _phone(4, "Comprato", "A", "B")]
        for item, sync_id in zip(phone, (11, 12, 13, 0)):
            item.sync_id = sync_id
        registry = provenance.Registry()
        registry.record(provenance.Link(sync_id=11, pc=provenance.computer_name(), path=str(here)))
        registry.record(provenance.Link(sync_id=12, pc=provenance.computer_name(), path=str(tmp_path / "via.mp3")))
        window.registry = registry
        window.set_phone_tracks(phone, "iPhone di prova")
        panel = window.iphone_panel
        origins = {}
        view = panel._music_view
        for index in range(view.topLevelItemCount()):
            row = view.topLevelItem(index)
            origins[row.text(iphone_panel.COL_TITLE)] = row.text(iphone_panel.COL_ORIGIN)
        assert origins == {"Collegato": iphone_panel.ORIGIN_HERE, "Sparito": iphone_panel.ORIGIN_MISSING,
                           "Ignoto": iphone_panel.ORIGIN_UNKNOWN, "Comprato": iphone_panel.ORIGIN_PHONE}
        panel._show.setCurrentIndex(1)                     # solo sull'iPhone
        assert panel._count.text() == "1 di 4 brani"
        panel._show.setCurrentIndex(4)                     # file del PC non trovato
        assert panel._count.text() == "1 di 4 brani"
    finally:
        window.close()
        app.processEvents()


def test_comparison_table_tooltips(tmp_path):
    """Il suggerimento di ✔/⟳: il brano abbinato, come (registro = certo, tag = probabile), i tag affiancati."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import provenance
    from myeasymp3toiphone.gui.main_window import MainWindow
    rows = phone_library.comparison(TrackTags(title="T", artist="A", album="B", year="1991", compilation=True),
                                    TrackTags(title="T", artist="a", album="B", year="1990"))
    assert ("Anno", "1991", "1990", True) in rows and ("Artista", "A", "a", False) in rows   # le maiuscole no
    assert ("Compilation", "sì", "no", True) in rows
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        pc = [_pc("Canzone A", "Artista Uno", "Album Primo", year="1991", track_number=1),
              _pc("Canzone B", "Artista Uno", "Album Primo", year="1991", track_number=2)]
        window.tracks = pc
        phone = [_phone(1, "Canzone A", "Artista Uno", "Album Primo", year="1991", track_number=1),
                 _phone(2, "Canzone B", "Artista Uno", "Album Primo", year="1990", track_number=2)]
        phone[1].sync_id = 22
        window.set_phone_tracks(phone, "iPhone di prova")
        stale = window.iphone_panel.pc_tooltip(2)
        assert "<table" in stale and "Canzone B.mp3" in stale and "probabile" in stale
        assert "<td>1991</td><td>1990</td>" in stale and "font-weight:bold" in stale
        same = window.device_tooltip(pc[0])
        assert "Canzone A" in same and "font-weight:bold" not in same
        registry = provenance.Registry()
        registry.record(provenance.Link(sync_id=22, pc=provenance.computer_name(), path=str(pc[1].path),
                                        how=provenance.HOW_FINGERPRINT))
        window.set_registry(registry)
        assert "certo" in window.iphone_panel.pc_tooltip(2) and "impronta" in window.device_tooltip(pc[1])
        assert window.iphone_panel.pc_tooltip(999).startswith("Non è")
    finally:
        window.close()
        app.processEvents()


def test_connect_button_and_manual_disconnect(monkeypatch):
    """Connetti (verde) / Disconnetti (rosso); dopo Disconnetti niente riconnessione automatica finché il cavo non
    viene staccato; il titolo della scheda dice se l'iPhone è connesso."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import iphone
    from myeasymp3toiphone.gui import iphone_panel
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        panel = window.iphone_panel
        attempts = []
        monkeypatch.setattr(panel, "connect_device", lambda auto=False: attempts.append(auto))
        button = panel._connect_button
        assert button.text() == iphone_panel.CONNECT_TEXT and button.property("role") == "go"
        panel._connected = True
        panel._update_enabled()
        assert button.text() == iphone_panel.DISCONNECT_TEXT and button.property("role") == "danger"
        tab = window._tabs.indexOf(panel)
        assert window._tabs.tabText(tab) == "iPhone ●"
        button.click()                                           # Disconnetti
        assert not panel.connected and button.text() == iphone_panel.CONNECT_TEXT
        assert window._tabs.tabText(tab) == "iPhone"
        monkeypatch.setattr(iphone, "device_present", lambda: True)
        panel._check_device()
        assert attempts == []                                    # attaccato, ma disconnesso a mano: niente
        monkeypatch.setattr(iphone, "device_present", lambda: False)
        panel._check_device()                                    # cavo staccato
        monkeypatch.setattr(iphone, "device_present", lambda: True)
        panel._check_device()                                    # riattaccato: si riconnette da solo
        assert attempts == [True]
        button.click()                                           # Connetti a mano
        assert attempts == [True, False]
    finally:
        window.close()
        app.processEvents()


def test_phantom_tracks_marked_saved_and_reported(tmp_path):
    from myeasymp3toiphone import iphone, scan
    tracks = [_phone(1, "Uno", "A", "B"), _phone(2, "Due", "A", "B"),
              PhoneTrack(3, "/Purchases/X.m4a", 1, 1.0, TrackTags(title="Tre"))]
    tracks[1].remote_path = "/iTunes_Control/Music/F05/W0084007.mp3"
    iphone.mark_missing_files(tracks, {"/itunes_control/music/f01/1.mp3"})
    assert [t.missing_file for t in tracks] == [False, True, False]     # fuori dalla cartella della musica: no
    phone_library.save_listing(tmp_path, "iPhone", tracks)
    again = phone_library.load_listing(tmp_path)["tracks"]
    assert [t.missing_file for t in again] == [False, True, False]
    issues = scan.detect_phantoms(again)
    assert len(issues) == 1 and issues[0].kind == scan.KIND_UNREADABLE and "W0084007" in issues[0].files[0]
    iphone.mark_missing_files(tracks, None)                              # cartelle non lette: non si cambia niente
    assert tracks[1].missing_file


def test_sync_finished_notice_never_fails(monkeypatch):
    from myeasymp3toiphone import iphone

    async def no_phone():
        raise iphone.IPhoneError("nessun iPhone")

    monkeypatch.setattr(iphone, "_open_lockdown", no_phone)
    assert iphone.post_sync_finished() is False


def test_pc_column_states_source_outside_open_folder_and_probable(tmp_path, monkeypatch):
    """✔/⟳ dalla sorgente del registro anche fuori dalla cartella aperta, ✖ se il file non c'è più, ≈ per i tag;
    il filtro "Da rivedere", la colonna File della sorgente e Associa le probabili."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import provenance
    from myeasymp3toiphone.gui import iphone_panel
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        outside = tmp_path / "altrove" / "Fuori.mp3"
        write_mp3(outside)
        write_tags(outside, TrackTags(title="Fuori", artist="Artista Uno", album="Album Primo", year="1991"))
        window.tracks = [_pc("Per tag", "Artista Uno", "Album Primo")]
        window._rebuild_views()
        phone = [_phone(1, "Fuori", "Artista Uno", "Album Primo", year="1990"),
                 _phone(2, "Sparito", "Artista Uno", "Album Primo"),
                 _phone(3, "Per tag", "Artista Uno", "Album Primo"),
                 _phone(4, "Fuori", "Artista Uno", "Album Primo", year="1991")]
        for item, sync_id in zip(phone, (31, 32, 33, 34)):
            item.sync_id = sync_id
        registry = provenance.Registry()
        registry.record(provenance.Link(sync_id=31, pc=provenance.computer_name(), path=str(outside)))
        registry.record(provenance.Link(sync_id=34, pc=provenance.computer_name(), path=str(outside)))
        registry.record(provenance.Link(sync_id=32, pc=provenance.computer_name(), path=str(tmp_path / "via.mp3")))
        window.registry = registry
        window.set_phone_tracks(phone, "iPhone di prova")
        panel = window.iphone_panel
        view = panel._music_view
        states = {}
        files = {}
        for index in range(view.topLevelItemCount()):
            row = view.topLevelItem(index)
            pid = row.data(iphone_panel.COL_TITLE, iphone_panel.PID_ROLE)
            states[pid] = row.text(iphone_panel.COL_PC)
            files[pid] = row.text(iphone_panel.COL_SOURCE_FILE)
        assert states == {1: "⟳", 2: "✖", 3: "≈", 4: "✔"}
        assert files[1] == "Fuori.mp3" and files[3] == "Per tag.mp3"        # 3: una proposta, in rosso
        texts = [text for text, _rule in iphone_panel.SHOW_FILTERS]
        panel._show.setCurrentIndex(texts.index("Con una sorgente proposta (in rosso)"))
        assert panel._count.text() == "1 di 4 brani"
        panel._show.setCurrentIndex(0)
        assert [item.pid for item in panel._with_proposal(phone)] == [3]
        assert "fuori dalla cartella aperta" in panel.pc_tooltip(1) and "non c'è più" in panel.pc_tooltip(2)
        assert [item.pid for item, _track in panel._stale_pairs(phone)] == [1]
        window.app_settings.show_full_path = True
        panel.pc_changed()
        panel._refresh_pc_column()
        for index in range(view.topLevelItemCount()):
            row = view.topLevelItem(index)
            if row.data(iphone_panel.COL_TITLE, iphone_panel.PID_ROLE) == 1:
                assert row.text(iphone_panel.COL_SOURCE_FOLDER) == str(outside.parent)
                assert row.text(iphone_panel.COL_SOURCE_FILE) == "Fuori.mp3"
        window.app_settings.show_full_path = False
        texts = [text for text, _rule in iphone_panel.SHOW_FILTERS]
        panel._show.setCurrentIndex(texts.index("Da rivedere: abbinati solo per i tag (≈)"))
        assert panel._count.text() == "1 di 4 brani"
        panel._show.setCurrentIndex(0)
        assert [item.pid for item in panel._probable(phone)] == [3]
        panel._link_probable(panel._probable(phone))           # QMessageBox.question dei test risponde Sì
        app.processEvents()
        assert window.registry.get(33) is not None and window.registry.get(33).how == provenance.HOW_RULES
        panel.pc_changed()
        panel._refresh_pc_column()
        assert panel._with_proposal(phone) == []                 # associata: non è più una proposta
        import time
        from myeasymp3toiphone.tags import read_tags

        def wait_idle():
            deadline = time.monotonic() + 10
            while window.runner.is_busy and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(0.01)
            app.processEvents()

        wait_idle()
        shown = []
        monkeypatch.setattr(iphone_panel.AlignToPcDialog, "exec", lambda dialog: shown.append(dialog) or False)
        panel._align_to_pc(panel._stale_pairs(phone))            # l'elenco dei file, Annulla: niente cambia
        wait_idle()
        assert len(shown) == 1 and read_tags(outside)[0].year == "1991"
        monkeypatch.setattr(iphone_panel.AlignToPcDialog, "exec", lambda dialog: True)
        panel._align_to_pc(panel._stale_pairs(phone))            # vale l'iPhone: l'anno 1990 si scrive nel file
        wait_idle()
        assert read_tags(outside)[0].year == "1990" and not window.overlay.is_edited(outside)
    finally:
        window.close()
        app.processEvents()


def test_link_proposed_source(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import provenance
    from myeasymp3toiphone.gui import iphone_panel
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        window.tracks = [_pc("Canzone A", "Artista Uno", "Album Primo")]
        window._rebuild_views()
        phone = [_phone(1, "Canzone A", "Artista Uno", "Album Primo")]
        phone[0].sync_id = 41
        window.set_phone_tracks(phone, "iPhone di prova")
        panel = window.iphone_panel
        row = panel._music_view.topLevelItem(0)
        assert row.data(iphone_panel.COL_SOURCE_FILE, iphone_panel.PROPOSED_ROLE)
        assert row.foreground(iphone_panel.COL_SOURCE_FILE).color() == iphone_panel.PROPOSED_COLOR
        panel._link_proposed(panel._with_proposal(phone))
        app.processEvents()
        assert window.registry.get(41).how == provenance.HOW_FOLDER
        panel.pc_changed()
        panel._refresh_pc_column()
        row = panel._music_view.topLevelItem(0)
        assert not row.data(iphone_panel.COL_SOURCE_FILE, iphone_panel.PROPOSED_ROLE)
        assert row.text(iphone_panel.COL_SOURCE_FILE) == "Canzone A.mp3"
    finally:
        window.close()
        app.processEvents()


def test_only_linked_tracks_are_updated_from_the_pc(tmp_path):
    """Aggiornare l'iPhone (PC → iPhone) vale solo per i brani associati dal registro; un brano abbinato solo per i
    tag, anche con tag diversi, non va in attesa e non si aggiorna."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import provenance
    from myeasymp3toiphone.gui.main_window import MainWindow
    from myeasymp3toiphone.pending import UPDATE
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        linked = _pc("Canzone A", "Artista Uno", "Album Primo", year="1991")
        by_tags = _pc("Canzone B", "Artista Uno", "Album Primo", year="1991")
        window.tracks = [linked, by_tags]
        window._rebuild_views()
        phone = [_phone(1, "Canzone A", "Artista Uno", "Album Primo", year="1990"),
                 _phone(2, "Canzone B", "Artista Uno", "Album Primo", year="1990")]
        phone[0].sync_id = 11
        phone[1].sync_id = 22
        window.set_phone_tracks(phone, "iPhone di prova")
        registry = provenance.Registry()
        registry.record(provenance.Link(sync_id=11, pc=provenance.computer_name(), path=str(linked.path)))
        window.set_registry(registry)
        assert window.device_state(linked)[2] and not window.device_state(by_tags)[2]
        window.queue_files([linked, by_tags], UPDATE)
        assert window.pending.get(linked.path) == UPDATE and not window.pending.get(by_tags.path)
        window.pending.set(by_tags.path, UPDATE)               # rimasto da una versione precedente
        updates = [(job.phone, job.track) for job in window.pending_jobs() if job.action == UPDATE]
        assert updates == [(phone[0], linked)]
    finally:
        window.close()
        app.processEvents()


def test_red_proposal_from_folder_name_without_whole_album(tmp_path):
    """Un brano che l'album intero non trova (l'altro brano dell'album sull'iPhone non è sul PC) ha comunque la
    proposta in rosso dal nome della cartella."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui import iphone_panel
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        track = _pc("Canzone A", "Artista Uno", "Album Primo", track_number=1)
        track.length = 200.0
        window.tracks = [track]
        window._rebuild_views()
        phone = [_phone(1, "Canzone A", "Artista Uno", "Album Primo", track_number=1),
                 _phone(2, "Non sul PC", "Artista Uno", "Album Primo", track_number=2)]
        phone[0].sync_id = 51
        phone[1].sync_id = 52
        panel = window.iphone_panel
        window.set_phone_tracks(phone, "iPhone di prova")
        assert panel._proposed[1].pc is track and panel._proposed[1].how == "cartella" and 2 not in panel._proposed
        rows = {}
        for index in range(panel._music_view.topLevelItemCount()):
            row = panel._music_view.topLevelItem(index)
            rows[row.text(iphone_panel.COL_TITLE)] = row
        assert rows["Canzone A"].data(iphone_panel.COL_SOURCE_FILE, iphone_panel.PROPOSED_ROLE)
        assert not rows["Non sul PC"].data(iphone_panel.COL_SOURCE_FILE, iphone_panel.PROPOSED_ROLE)
    finally:
        window.close()
        app.processEvents()


def test_comparison_like_the_iphone_groups_albums_and_artists():
    """L'iPhone tiene la grafia del suo album o artista "uguale": "01" = "1", maiuscole (phone_group_key, per
    l'invio). Il confronto invece conta anche la grafia: fa giallo, e l'aggiornamento la corregge reinviando l'album
    intero. "AA.VV." e "Artisti Vari" per l'iPhone sono nomi diversi."""
    from myeasymp3toiphone.library import phone_group_key
    from myeasymp3toiphone.phone_library import spelling_differences
    assert phone_group_key("Raccolta 01 - Estate") == phone_group_key("Raccolta 1 - Estate")
    assert phone_group_key("AA.VV.") != phone_group_key("Artisti Vari") != phone_group_key("Various Artists")
    assert phone_group_key("Festival 1990") != phone_group_key("Festival 199")
    assert phone_group_key("Disco 10") != phone_group_key("Disco 1")
    pc = TrackTags(title="Uno", artist="Anna", album="Raccolta 01 - Estate", album_artist="AA.VV.", compilation=True)
    phone = TrackTags(title="Uno", artist="Anna", album="Raccolta 1 - Estate", album_artist="aa.vv.",
                      compilation=True)
    assert [label for label, _a, _b in differences(pc, phone)] == ["Album"]   # "aa.vv.": solo le maiuscole
    assert spelling_differences(pc, phone) == ["album"]       # solo grafia: album intero da reinviare
    phone.album_artist = "Artisti Vari"                   # un altro artista per l'iPhone: si rimpiazza e basta
    assert spelling_differences(pc, phone) == ["album"]


def test_album_groups_of_phone_tracks():
    from myeasymp3toiphone.library import album_groups
    phone = [_phone(1, "Due", "Gruppo Finto", "Disco Uno", track_number=2),
             _phone(2, "Uno", "gruppo finto", "disco uno", track_number=1),
             _phone(3, "Ospite", "Cantante Finto", "Raccolta Finta", album_artist="AA.VV."),
             _phone(4, "Altro", "Gruppo Finto", "Disco Due")]
    groups = album_groups(phone)
    assert len(groups) == 3
    orders = []
    for members in groups.values():
        pids = []
        for item in members:
            pids.append(item.pid)
        orders.append(pids)
    assert [2, 1] in orders                                       # le grafie insieme, per numero di traccia
    assert ("AA.VV.", "Raccolta Finta") in groups                 # l'artista dell'album vince su quello del brano


def test_artist_and_album_lists_and_album_bands_in_both_tabs(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui import iphone_panel
    from myeasymp3toiphone.gui.main_window import MainWindow
    from myeasymp3toiphone.gui.theme import ALBUM_BANDS, album_bands
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        assert album_bands(["a", "a", "a", "b", "c", "c"]) == [(0, 0), (0, 1), (0, 0), (1, 0), (0, 0), (0, 1)]
        phone = [_phone(1, "Uno", "Gruppo Finto", "Disco Uno"), _phone(2, "Due", "Gruppo Finto", "Disco Due"),
                 _phone(3, "Tre", "Altro Finto", "Disco Tre"), _phone(4, "Quattro", "Altro Finto", "Disco Tre")]
        window.set_phone_tracks(phone, "iPhone di prova")
        panel = window.iphone_panel
        browser = panel._browser
        assert browser.artists.topLevelItemCount() == 3               # "(Tutti…)" e due artisti
        assert browser.albums.topLevelItemCount() == 4                # "(Tutti…)" e tre album
        view = panel._music_view
        view.sortByColumn(iphone_panel.COL_ALBUM, Qt.AscendingOrder)
        app.processEvents()
        shown = []
        for index in range(view.topLevelItemCount()):
            shown.append(view.bands[view.topLevelItem(index).data(iphone_panel.COL_TITLE, iphone_panel.PID_ROLE)])
        # Disco Due, Disco Tre (due brani), Disco Uno
        assert shown == [ALBUM_BANDS[0][0], ALBUM_BANDS[1][0], ALBUM_BANDS[1][1], ALBUM_BANDS[0][0]]
        for index in range(browser.artists.topLevelItemCount()):
            item = browser.artists.topLevelItem(index)
            if item.text(0) == "Gruppo Finto":
                item.setSelected(True)
        assert panel._count.text() == "2 di 4 brani"
        assert browser.albums.topLevelItemCount() == 3                # solo i suoi album
        assert len(view.bands) == 2                                   # le tinte solo per le righe che si vedono
        for index in range(browser.albums.topLevelItemCount()):
            item = browser.albums.topLevelItem(index)
            if item.text(0) == "Disco Due":
                item.setSelected(True)
        assert panel._count.text() == "1 di 4 brani"

        model = window._model
        model.set_tracks([_pc("Uno", "Gruppo Finto", "Disco Uno"), _pc("Due", "Gruppo Finto", "Disco Uno"),
                          _pc("Tre", "Altro Finto", "Disco Tre")])
        colors = []
        for row in range(model.rowCount()):
            colors.append(model.data(model.index(row, 0), Qt.BackgroundRole).color())
        assert colors == [ALBUM_BANDS[0][0], ALBUM_BANDS[0][1], ALBUM_BANDS[1][0]]
    finally:
        window.close()
        app.processEvents()


def test_various_artists_are_one_artist_with_extra_names():
    from myeasymp3toiphone.library import album_groups, assign_groups, phone_group_key, set_various_artist_names
    phone = [_phone(1, "Uno", "Cantante Finto", "Raccolta Finta", album_artist="AA.VV."),
             _phone(2, "Due", "Altro Finto", "Raccolta Finta", album_artist="Various Artists"),
             _phone(3, "Tre", "Terzo Finto", "Altra Raccolta", album_artist="AA.VV."),
             _phone(4, "Quattro", "Quarto Finto", "Disco Strano", album_artist="Misti Finti")]
    groups = album_groups(phone)
    artists = set()
    for artist, _album in groups:
        artists.add(artist)
    assert artists == {"AA.VV.", "Misti Finti"}                  # la grafia più usata
    assert len(groups) == 3                                        # "Raccolta Finta" è un album solo
    pc = [_pc("Uno", "Cantante Finto", "Raccolta Finta", album_artist="Various Artists"),
          _pc("Due", "Altro Finto", "Raccolta Finta", album_artist="VA")]
    assign_groups(pc)
    assert pc[0].album_key == pc[1].album_key
    try:
        set_various_artist_names(["Misti Finti", " "])
        artists = set()
        for artist, _album in album_groups(phone):
            artists.add(artist)
        assert artists == {"AA.VV."}
        assert phone_group_key("Misti Finti") != phone_group_key("AA.VV.")   # l'iPhone non conosce i nomi aggiunti
    finally:
        set_various_artist_names([])


def test_right_click_menus_on_artists_and_albums(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import provenance
    from myeasymp3toiphone.gui import iphone_panel, main_window
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    for module in (iphone_panel, main_window):          # nessun menu che aspetta un clic
        monkeypatch.setattr(module, "show_entries_menu", lambda *args: None)
    window = MainWindow()
    try:
        here = [_pc("Uno", "Gruppo Finto", "Disco Uno"), _pc("Due", "Gruppo Finto", "Disco Uno"),
                _pc("Tre", "Gruppo Finto", "Disco Uno")]
        window.tracks = here
        phone = [_phone(1, "Uno", "Gruppo Finto", "Disco Uno"), _phone(2, "Due", "Gruppo Finto", "Disco Uno",
                                                                       year="1999")]
        phone[0].sync_id, phone[1].sync_id = 11, 12
        registry = provenance.Registry()
        for item, track in zip(phone, here):
            registry.record(provenance.Link(sync_id=item.sync_id, pc=provenance.computer_name(),
                                            path=str(track.path)))
        window.registry = registry
        window.set_phone_tracks(phone, "iPhone di prova")
        window._rebuild_views()
        browser = window.browser
        browser.show()
        app.processEvents()
        target = None
        for index in range(browser.albums.topLevelItemCount()):
            item = browser.albums.topLevelItem(index)
            if item.text(0) == "Disco Uno":
                target = item
        browser._menu_at(browser.albums, browser.albums.visualItemRect(target).center())
        assert browser.selected_albums() == {("Gruppo Finto", "Disco Uno")}
        assert len(browser.menu_tracks) == 3                          # l'album intero
        texts = []
        for text, enabled, _slot in window.browser_menu_entries(browser.menu_tracks):
            texts.append((text, enabled))
        assert texts[0] == ("Copia 1 brano da PC a iPhone", True)     # "Tre": in attesa anche senza iPhone
        assert texts[1] == ("Ricopia da PC a iPhone: 1 brano", True)  # "Due": anno diverso
        assert texts[2] == ("Usa i tag da PC a iPhone: 1 brano", True)
        assert texts[3] == ("Elimina 2 brani dall'iPhone", True)      # i due con la sorgente certa

        panel = window.iphone_panel
        phone_browser = panel._browser
        phone_browser.show()
        app.processEvents()
        for index in range(phone_browser.albums.topLevelItemCount()):
            item = phone_browser.albums.topLevelItem(index)
            if item.text(0) == "Disco Uno":
                target = item
        phone_browser._menu_at(phone_browser.albums, phone_browser.albums.visualItemRect(target).center())
        entries = {}
        for text, enabled, _slot in panel.browser_menu_entries(phone_browser.menu_tracks):
            entries[text] = enabled
        assert entries["Copia 2 brani da iPhone a PC…"] is False     # subito: serve l'iPhone connesso
        assert entries["Ricopia da PC a iPhone: 1 brano"] and entries["Usa i tag da PC a iPhone: 1 brano"]
        assert entries["Usa i tag da iPhone a PC: 1 brano…"] and entries["Cambia i tag: 2 brani…"]
        assert entries["Copia i brani mancanti degli album da PC a iPhone: 1 brano (1 album)"]   # "Tre" manca
        assert entries["Ricopia le copertine da PC a iPhone: 0 album senza immagine"] is False
        assert entries["Elimina 2 brani dall'iPhone"]
        phone.append(_phone(3, "Senza sorgente", "Gruppo Finto", "Disco Uno"))
        phone[2].sync_id = 13
        window.set_phone_tracks(phone, "iPhone di prova")
        texts = [text for text, _enabled, _slot in panel.browser_menu_entries(phone)]
        assert "Ricopia da PC a iPhone: 1 brano" in texts and "Elimina 3 brani dall'iPhone" in texts
        before = phone_browser.menu_tracks
        phone_browser._menu_at(phone_browser.albums, QPoint(-50, -50))     # fuori dalle righe: niente menu
        assert phone_browser.menu_tracks is before
    finally:
        window.close()
        app.processEvents()


def test_time_estimate():
    from myeasymp3toiphone import estimate
    assert estimate.seconds([]) == 0
    assert estimate.describe(estimate.seconds([8_000_000] * 10)) == "meno di un minuto"
    # 40 sessioni da 3 s, 1000 x 0,2 s, 8 GB a 12 MB/s, 2 s per rileggere: 989 s
    assert estimate.describe(estimate.seconds([8_000_000] * 1000)) == "circa 17 minuti"
    assert estimate.describe(3600) == "circa 1 ora"
    assert estimate.describe(3601) == "circa 1 ora e 1 minuti"
    assert estimate.summary(3, 30) == "Brani: 3. Tempo stimato: meno di un minuto."
    assert estimate.file_size("C:/non/esiste.mp3") == estimate.DEFAULT_SIZE


def test_exit_with_pending_changes_asks_first(tmp_path, monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui import main_window
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        assert window._ask_pending_on_exit() == main_window.EXIT_NOW              # niente in attesa
        from myeasymp3toiphone.pending import SEND, Job
        track = _pc("Nuovo", "Gruppo Finto", "Disco Uno")
        monkeypatch.setattr(window, "pending_jobs", lambda: [Job("file:nuovo", SEND, track=track)])
        # iPhone non collegato: solo "Esci senza applicare" e "Annulla" (i test scelgono il primo)
        assert window._ask_pending_on_exit() == main_window.EXIT_NOW
        monkeypatch.setattr(type(window.iphone_panel), "connected", property(lambda self: True))
        applied = []
        monkeypatch.setattr(window.iphone_panel, "apply_jobs",
                            lambda *args, **kwargs: applied.append(kwargs))
        assert window._ask_pending_on_exit() == main_window.EXIT_AFTER_APPLY       # "Applica ed esci"
        window.close()
        assert applied and applied[0]["closing"] and window._exit_checked
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_spelling_differences_and_alignment_plan(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import phone_actions, provenance
    from myeasymp3toiphone.gui.main_window import MainWindow
    from myeasymp3toiphone.phone_library import spelling_differences
    pc = TrackTags(title="Uno", artist="Gruppo Finto", album="Raccolta 1")
    assert spelling_differences(pc, TrackTags(title="Uno", artist="GRUPPO FINTO", album="Raccolta 01")) == ["album"]
    assert spelling_differences(pc, TrackTags(title="Uno", artist="Gruppo Finto", album="Raccolta 1")) == []
    assert spelling_differences(pc, TrackTags(title="Uno", artist="Altro", album="Altra raccolta")) == []
    assert phone_actions.service_padding(3) == 97
    assert phone_actions.service_padding(100) == 0
    assert phone_actions.service_padding(450) == 50           # l'ultima sessione toglie 50 + 50
    assert phone_actions.service_padding(0) == 100

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        files = []
        for name in ("uno", "due", "tre"):
            path = tmp_path / f"{name}.mp3"
            write_mp3(path)
            files.append(path)
        here = [Track(path=files[0], tags=TrackTags(title="Uno", artist="Gruppo Finto", album="Raccolta 1")),
                Track(path=files[1], tags=TrackTags(title="Due", artist="Gruppo Finto", album="Raccolta 1")),
                Track(path=files[2], tags=TrackTags(title="Tre", artist="Gruppo Finto", album="Altro disco"))]
        window.tracks = here
        phone = [_phone(1, "Uno", "Gruppo Finto", "Raccolta 01"), _phone(2, "Due", "Gruppo Finto", "Raccolta 01"),
                 _phone(3, "Tre", "Gruppo Finto", "Altro disco")]
        for item, sync_id in zip(phone, (11, 12, 13)):
            item.sync_id = sync_id
            item.artist_sync_id = 500
        phone[0].album_sync_id = phone[1].album_sync_id = 700
        phone[2].album_sync_id = 701
        registry = provenance.Registry()
        for item, track in zip(phone, here):
            registry.record(provenance.Link(sync_id=item.sync_id, pc=provenance.computer_name(),
                                            path=str(track.path)))
        window.registry = registry
        window.set_phone_tracks(phone, "iPhone di prova")
        panel = window.iphone_panel
        pairs, blocked = panel.spelling_plan([phone[0]])
        assert sorted(item.pid for item, _track in pairs) == [1, 2]     # l'album intero, non l'altro dell'artista
        assert blocked == 0
        panel._show.setCurrentIndex(panel._show.findText("Sorgente con tag diversi (⟳)"))
        assert panel._count.text() == "2 di 3 brani"                  # la grafia diversa è una differenza
        # un aggiornamento di "Uno" e "Tre": "Uno" porta con sé il suo album intero, "Tre" si aggiorna come sempre
        rest, whole, blocked = panel.split_for_spelling([(phone[0], here[0]), (phone[2], here[2])])
        assert [item.pid for item, _track in rest] == [3]
        assert sorted(item.pid for item, _track in whole) == [1, 2] and blocked == 0
        registry.forget(12)                                          # un brano dell'album senza sorgente
        window.set_phone_tracks(phone, "iPhone di prova")
        pairs, blocked = panel.spelling_plan([phone[0]])
        assert pairs == [] and blocked == 1
        rest, whole, blocked = panel.split_for_spelling([(phone[0], here[0])])
        assert [item.pid for item, _track in rest] == [1] and whole == [] and blocked == 1   # come sempre, e avvisa
    finally:
        window.close()
        app.processEvents()


def test_short_folder_names_disc_folders_with_their_album():
    from myeasymp3toiphone.library import short_folder
    assert short_folder(r"D:\musica\Album Finto\CD1") == r"Album Finto\CD1"
    assert short_folder("D:/musica/Album Finto/Disk 2") == r"Album Finto\Disk 2"
    assert short_folder(r"D:\musica\Album Finto\cd 2 - studio") == r"Album Finto\cd 2 - studio"
    assert short_folder(r"D:\musica\Album Finto") == "Album Finto"
    assert short_folder(r"D:\musica\Album Finto (Disc 1)") == "Album Finto (Disc 1)"   # il nome dice già l'album
    assert short_folder(r"D:\CD1") == "CD1"                                           # sopra c'è solo l'unità
    assert short_folder(r"D:\musica\Cdrom raccolta") == "Cdrom raccolta"             # non è un disco


def test_same_album_in_two_folders_one_after_the_other_with_own_tint():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui.main_window import MainWindow
    from myeasymp3toiphone.gui.theme import ALBUM_BANDS
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        def copy(folder, title, number):
            result = Track(path=Path(f"D:/{folder}/Disco Finto/{number:02d}.mp3"),
                           tags=TrackTags(title=title, artist="Gruppo Finto", album="Disco Finto",
                                          track_number=number))
            return result

        window.tracks = [copy("musica.flac", "Uno", 1), copy("musica.mp3", "Uno", 1),
                         copy("musica.flac", "Due", 2), copy("musica.mp3", "Due", 2),
                         Track(path=Path("D:/insieme/Terzo Finto/01.flac"),
                               tags=TrackTags(title="F", artist="Gruppo Finto", album="Terzo Finto", track_number=1)),
                         Track(path=Path("D:/insieme/Terzo Finto/01.mp3"),
                               tags=TrackTags(title="F", artist="Gruppo Finto", album="Terzo Finto", track_number=1)),
                         Track(path=Path("D:/insieme/Terzo Finto/02.flac"),
                               tags=TrackTags(title="G", artist="Gruppo Finto", album="Terzo Finto", track_number=2)),
                         Track(path=Path("D:/musica.mp3/Doppio Finto/CD1/01.mp3"),
                               tags=TrackTags(title="A", artist="Gruppo Finto", album="Doppio Finto", track_number=1)),
                         Track(path=Path("D:/musica.mp3/Doppio Finto/CD2/01.mp3"),
                               tags=TrackTags(title="B", artist="Gruppo Finto", album="Doppio Finto",
                                              track_number=1, disc_number=2))]
        window._rebuild_views()
        model = window._model
        order = []
        colors = []
        for row in range(model.rowCount()):
            order.append(str(model.track(row).path.parent.parent.name) + "/" + model.track(row).title)
            colors.append(model.data(model.index(row, 0), Qt.BackgroundRole).color())
        assert order == ["musica.flac/Uno", "musica.flac/Due", "musica.mp3/Uno", "musica.mp3/Due",
                         "Doppio Finto/A", "Doppio Finto/B", "insieme/F", "insieme/G", "insieme/F"]
        assert colors == [ALBUM_BANDS[0][0], ALBUM_BANDS[0][1], ALBUM_BANDS[1][0], ALBUM_BANDS[1][1],
                          ALBUM_BANDS[0][0], ALBUM_BANDS[0][1],          # CD1 e CD2: un album, una tinta
                          ALBUM_BANDS[1][0], ALBUM_BANDS[1][1],          # stessa cartella: prima i FLAC...
                          ALBUM_BANDS[0][0]]                             # ...poi gli MP3, con l'altra tinta
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_albums_without_cover_read_saved_and_planned(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import provenance
    from myeasymp3toiphone.gui.main_window import MainWindow
    path = tmp_path / "MediaLibrary.sqlitedb"
    connection = _database(path)
    connection.executescript("CREATE TABLE best_artwork_token (entity_pid INTEGER, entity_type INTEGER, "
                             "artwork_type INTEGER, available_artwork_token TEXT);"
                             "INSERT INTO best_artwork_token VALUES (2, 4, 6, '700');"      # "Raccolta": immagine
                             "INSERT INTO best_artwork_token VALUES (1, 4, 6, '');")        # "Album Primo": vuota
    connection.commit()
    connection.close()
    tracks = read_music_database(path)
    flags = {}
    for item in tracks:
        flags[item.tags.title] = item.album_without_cover
    assert flags == {"Canzone A": True, "Canzone B": True, "Canzone C": False}
    phone_library.save_listing(tmp_path, "iPhone di prova", tracks)
    again = {}
    for item in phone_library.load_listing(tmp_path)["tracks"]:
        again[item.tags.title] = item.album_without_cover
    assert again == flags

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        files = []
        for name in ("a", "b"):
            file = tmp_path / f"{name}.mp3"
            write_mp3(file)
            files.append(file)
        window.tracks = [Track(path=files[0], tags=TrackTags(title="Uno", artist="Gruppo Finto", album="Disco")),
                         Track(path=files[1], tags=TrackTags(title="Due", artist="Gruppo Finto", album="Disco"))]
        phone = [_phone(1, "Uno", "Gruppo Finto", "Disco"), _phone(2, "Due", "Gruppo Finto", "Disco"),
                 _phone(3, "Tre", "Gruppo Finto", "Altro")]
        for item, sync_id, album in zip(phone, (11, 12, 13), (700, 700, 701)):
            item.sync_id = sync_id
            item.album_sync_id = album
            item.album_without_cover = True
        registry = provenance.Registry()
        for item, track in zip(phone, window.tracks):
            registry.record(provenance.Link(sync_id=item.sync_id, pc=provenance.computer_name(),
                                            path=str(track.path)))
        window.registry = registry
        window.set_phone_tracks(phone, "iPhone di prova")
        panel = window.iphone_panel
        # i file del PC senza copertina: la Ricopia non darebbe l'immagine all'album, non si propone
        pairs, no_source, no_cover = panel.cover_plan([phone[0], phone[2]])
        assert pairs == [] and no_source == 1 and no_cover == 1       # "Altro": nessun brano con la sorgente
        window.cover_of = lambda track: b"immagine" if track.path == files[1] else None
        panel._compare_with_pc()                                       # si dimentica cosa sapeva delle copertine
        pairs, no_source, no_cover = panel.cover_plan([phone[0], phone[2]])
        assert sorted(item.pid for item, _track in pairs) == [1, 2]    # l'album intero (una copertina basta)
        assert no_source == 1 and no_cover == 0
        assert panel._actions.button("cover").isHidden()               # nessun album senza immagine scelto
        from myeasymp3toiphone.gui.iphone_panel import COVERLESS_FILTER
        panel._show.setCurrentIndex(COVERLESS_FILTER)                  # Mostra: album senza immagine
        assert panel._count.text() == "3 di 3 brani"
        button = panel._actions.button("cover")                        # il pulsante per sistemarli, nella barra
        assert not button.isHidden() and button.isEnabled()
        assert button.text().startswith("Ricopia le copertine da PC a iPhone: 1 album senza immagine; 1 senza")
        button.click()
        assert window.pending.get_phone(1) == "ricopia" and window.pending.get_phone(2) == "ricopia"
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_tracks_in_the_wrong_album_read_saved_and_refiled(tmp_path):
    """Un brano con l'artista dell'album "Artisti vari" che sull'iPhone sta nella riga di un album di "AA.VV.":
    l'app Musica lo mostra in un altro album. Si legge, si ricorda nell'elenco salvato, si filtra e si rimette a posto
    con Ricopia anche se i tag coincidono (✔)."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import provenance
    from myeasymp3toiphone.gui.iphone_panel import MISFILED_FILTER
    from myeasymp3toiphone.gui.main_window import MainWindow
    path = tmp_path / "MediaLibrary.sqlitedb"
    connection = _database(path)
    connection.execute("INSERT INTO album_artist VALUES (2, 'AA.VV.', 7002)")
    connection.execute("INSERT INTO album VALUES (3, 'Raccolta', 2, 8002)")      # la riga doppia, stesso sync_id
    _add(connection, 105, "Canzone D", 2, 3, location="MNOP.mp3", album_artist=1)
    connection.commit()
    connection.close()
    tracks = read_music_database(path)
    rows = {}
    for item in tracks:
        rows[item.tags.title] = item.album_row_artist
    assert rows == {"Canzone A": "", "Canzone B": "", "Canzone C": "", "Canzone D": "AA.VV."}
    phone_library.save_listing(tmp_path, "iPhone di prova", tracks)
    again = {}
    for item in phone_library.load_listing(tmp_path)["tracks"]:
        again[item.tags.title] = item.album_row_artist
    assert again == rows

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        file = tmp_path / "d.mp3"
        write_mp3(file)
        window.tracks = [Track(path=file, tags=TrackTags(title="Uno", artist="Gruppo Finto", album="Disco"))]
        phone = [_phone(1, "Uno", "Gruppo Finto", "Disco"), _phone(2, "Due", "Gruppo Finto", "Disco")]
        phone[0].sync_id = 11
        phone[0].album_row_artist = "AA.VV."              # ✔: stessi tag del PC, ma nell'album sbagliato
        phone[1].sync_id = 12
        phone[1].album_row_artist = "AA.VV."              # senza sorgente: non si può
        registry = provenance.Registry()
        registry.record(provenance.Link(sync_id=11, pc=provenance.computer_name(), path=str(file)))
        window.registry = registry
        window.set_phone_tracks(phone, "iPhone di prova")
        app.processEvents()
        panel = window.iphone_panel
        pairs, blocked = panel.refile_plan(phone)
        assert [item.pid for item, _track in pairs] == [1] and blocked == 1
        assert panel._actions.button("refile").isHidden()
        panel._show.setCurrentIndex(MISFILED_FILTER)
        assert panel._count.text() == "2 di 2 brani"
        button = panel._actions.button("refile")
        assert not button.isHidden() and button.isEnabled()
        assert button.text() == "Rimetti nell'album giusto (Ricopia da PC a iPhone): 1 brano, 1 album; 1 senza sorgente sul PC"
        button.click()
        assert window.pending.get_phone(1) == "ricopia" and window.pending.get_phone(2) == ""
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_choosing_an_album_shows_its_cover_without_selected_tracks():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice
    from PySide6.QtGui import QColor, QImage
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    image = QImage(20, 20, QImage.Format_RGB32)
    image.fill(QColor(200, 30, 30))
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, "PNG")
    png = bytes(data)
    window = MainWindow()
    try:
        tracks = [_pc("Uno", "Gruppo Finto", "Disco Uno", track_number=1),
                  _pc("Due", "Gruppo Finto", "Disco Uno", track_number=2),
                  _pc("Tre", "Altro Finto", "Disco Tre")]
        window.tracks = tracks
        window.editor.cover_provider = lambda track: png if track.title == "Due" else None   # il primo non ce l'ha
        window._rebuild_views()
        browser = window.browser
        for index in range(browser.albums.topLevelItemCount()):
            item = browser.albums.topLevelItem(index)
            if item.text(0) == "Disco Uno":
                item.setSelected(True)
        app.processEvents()
        editor = window.editor
        assert not editor._cover_label.pixmap().isNull()             # la copertina dell'album
        assert "Disco Uno" in editor._header.text() and "2 brani" in editor._header.text()
        assert not editor._cover_button.isEnabled()                  # niente da modificare senza brani
        window._table.selectRow(0)
        app.processEvents()
        assert editor._header.text() == "Uno.mp3"                    # un brano selezionato: l'editor normale
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_iphone_tag_panel_follows_the_chosen_artist_or_album():
    """Scheda iPhone: un brano selezionato e poi un altro artista o album scelti negli elenchi; il riquadro dei tag
    non resta sul brano di prima, ormai nascosto: mostra l'album scelto (nome, brani) o niente."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        phone = [_phone(1, "Uno", "Gruppo Finto", "Disco Uno"), _phone(2, "Due", "Gruppo Finto", "Disco Uno"),
                 _phone(3, "Tre", "Altro Finto", "Disco Tre")]
        window.set_phone_tracks(phone, "iPhone di prova")
        app.processEvents()                       # l'elenco si rifà dopo, con il confronto con il PC
        panel = window.iphone_panel
        tags = panel._tag_panel
        view = panel._music_view
        for index in range(view.topLevelItemCount()):
            row = view.topLevelItem(index)
            row.setSelected(row.text(3) == "Uno")
        app.processEvents()
        assert tags._header.text() == "Uno"
        browser = panel._browser
        for index in range(browser.albums.topLevelItemCount()):
            item = browser.albums.topLevelItem(index)
            item.setSelected(item.text(0) == "Disco Tre")
        app.processEvents()
        assert "Disco Tre" in tags._header.text() and "1 brani" in tags._header.text()
        assert not tags._save_button.isEnabled()
        for index in range(browser.artists.topLevelItemCount()):
            item = browser.artists.topLevelItem(index)
            item.setSelected(item.text(0) == "Altro Finto")
        app.processEvents()
        assert tags._header.text() == "Seleziona uno o più brani"   # un artista, nessun album: niente di vecchio
        for index in range(browser.artists.topLevelItemCount()):
            item = browser.artists.topLevelItem(index)
            item.setSelected(item.text(0) == "Gruppo Finto")
        app.processEvents()
        assert tags._header.text() == "Uno"            # il brano selezionato si vede di nuovo: torna nel riquadro
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_align_to_pc_writes_only_the_chosen_fields():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QDialogButtonBox
    from myeasymp3toiphone.gui.iphone_panel import AlignToPcDialog
    app = QApplication.instance() or QApplication([])
    one = _pc("Uno", "Anna", "Raccolta", album_artist="AA.VV.", year="2001")
    two = _pc("Due", "Anna", "Raccolta", album_artist="AA.VV.")
    new_one = one.tags.copy()
    new_one.album_artist, new_one.year = "Artisti Vari", "1999"
    new_two = two.tags.copy()
    new_two.album_artist = "Artisti Vari"
    dialog = AlignToPcDialog(None, [(one, new_one, ["album_artist", "year"]), (two, new_two, ["album_artist"])])
    assert dialog._boxes["album_artist"].text().endswith("(2 file)") and dialog._boxes["year"].text().endswith("(1 file)")
    dialog._boxes["year"].setChecked(False)                 # l'anno corretto sul PC non torna indietro
    plan = dialog.chosen_plan()
    assert [(track.tags.title, tags.album_artist, tags.year, fields) for track, tags, fields in plan] == [
        ("Uno", "Artisti Vari", "2001", ["album_artist"]), ("Due", "Artisti Vari", "", ["album_artist"])]
    assert dialog._buttons.button(QDialogButtonBox.Ok).text() == "Modifica 2 file"
    dialog._boxes["album_artist"].setChecked(False)
    assert dialog.chosen_plan() == [] and not dialog._buttons.button(QDialogButtonBox.Ok).isEnabled()
    dialog.close()
    app.processEvents()


def test_key_e_goes_to_the_tag_editor(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        window.tracks = [_pc("Uno", "Gruppo Finto", "Disco Uno", track_number=1),
                         _pc("Due", "Gruppo Finto", "Disco Uno", track_number=2)]
        window._rebuild_views()
        window._table.setCurrentIndex(window._model.index(1, 0))
        window._table.clearSelection()
        window._edit_current_track()                                 # E: il brano con il cursore, nell'editor
        assert [track.title for track in window._selected_table_tracks()] == ["Due"]
        title = window.editor._editors["title"]
        assert title.text() == "Due" and title.selectedText() == "Due"

        panel = window.iphone_panel
        window.set_phone_tracks([_phone(1, "Uno", "Gruppo Finto", "Disco Uno")], "iPhone di prova")
        opened = []
        monkeypatch.setattr(panel, "_edit_selected", lambda: opened.append(len(panel._selected_phone_tracks())))
        panel._music_view.setCurrentItem(panel._music_view.topLevelItem(0))
        panel._music_view.clearSelection()
        panel._edit_current()                                # Cambia i tag sul brano: va in attesa, anche senza iPhone
        assert opened == [1]
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_moved_sources_are_found_again(tmp_path, monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import adoption, provenance
    from myeasymp3toiphone.gui.main_window import MainWindow
    from myeasymp3toiphone.overlay import path_key
    from myeasymp3toiphone.relocate import REASON_SAME_AUDIO, REASON_SAME_FILE_AUDIO, relocate

    def mp3(folder, name, frames):
        path = tmp_path / folder / name
        write_mp3(path, frames)
        return Track(path=path, tags=TrackTags(title=name, artist="Gruppo Finto", album="Disco Finto"))

    moved_print = mp3("nuova", "01 Uno.mp3", 40)          # spostato e rinominato: lo ritrova l'impronta
    moved_name = mp3("nuova", "02 Due.mp3", 50)           # spostato: stesso nome e dimensione
    other_audio = mp3("altra", "03 Tre.mp3", 60)          # stesso nome e dimensione, ma un altro audio
    taken = mp3("presa", "04 Quattro.mp3", 70)            # già la sorgente di un altro brano

    class Cache:
        def fingerprint_index(self):
            return {"impronta-uno": [path_key(moved_print.path)]}

        def fingerprint(self, path):
            return "impronta-uno" if path == moved_print.path else ""

    prints = {moved_name.path: "impronta-due", other_audio.path: "impronta-diversa"}
    phone = [_phone(index, title, "Gruppo Finto", "Disco Finto") for index, title in enumerate("abcd", start=1)]
    for item in phone:
        item.sync_id = item.pid

    def link(item, old, size, printed):
        return provenance.Link(sync_id=item.pid, pc=provenance.computer_name(), path=str(tmp_path / "vecchia" / old),
                               size=size, fingerprint=printed)

    missing = [(phone[0], link(phone[0], "Uno.mp3", 1, "impronta-uno")),
               (phone[1], link(phone[1], "02 Due.mp3", moved_name.path.stat().st_size, "impronta-due")),
               (phone[2], link(phone[2], "03 Tre.mp3", other_audio.path.stat().st_size, "impronta-tre")),
               (phone[3], link(phone[3], "04 Quattro.mp3", taken.path.stat().st_size, ""))]
    found = relocate(missing, [moved_print, moved_name, other_audio, taken], Cache(), taken={path_key(taken.path)},
                     printer=lambda path: prints.get(path, ""))
    assert found[1].pc is moved_print and found[1].reason == REASON_SAME_AUDIO
    assert found[1].how == provenance.HOW_FINGERPRINT and found[1].level == adoption.LEVEL_CERTAIN
    assert found[2].pc is moved_name and found[2].reason == REASON_SAME_FILE_AUDIO
    assert 3 not in found or found[3].pc is not other_audio   # un altro audio: non è lui
    assert 4 not in found or found[4].pc is not taken         # un file già associato non si ruba

    app = QApplication.instance() or QApplication([])
    from myeasymp3toiphone.gui.missing_dialog import ACTION_RELINK, MissingSourcesDialog
    dialog = MissingSourcesDialog(None, missing, False, {1: found[1], 2: found[2]})
    assert dialog.tree.topLevelItem(0).text(3) == r"nuova\01 Uno.mp3" and dialog.tree.topLevelItem(2).text(3) == ""
    dialog._choose(ACTION_RELINK)
    assert dialog.action == ACTION_RELINK and len(dialog.chosen()) == 4
    window = MainWindow()
    try:
        registry = provenance.Registry()
        for item, old in missing:
            registry.record(old)
        window.registry = registry
        saved = []
        monkeypatch.setattr(window.iphone_panel, "_store_registry", lambda reg, message, then=None: saved.append(message))
        window.iphone_panel._relink(missing, {1: found[1], 2: found[2]}, [phone[0], phone[1], phone[2]])
        assert registry.get(1).path == str(moved_print.path) and registry.get(1).fingerprint == "impronta-uno"
        assert registry.get(2).path == str(moved_name.path)
        assert registry.get(3).path == str(tmp_path / "vecchia" / "03 Tre.mp3")      # non ritrovato: com'era
        assert saved == ["Ritrovati e associati 2 file spostati"]
    finally:
        window._exit_checked = True
        window.close()
        dialog.close()
        app.processEvents()


def test_fingerprints_in_the_background_only_once(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    import time
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui import main_window
    from myeasymp3toiphone.gui.main_window import MainWindow
    from myeasymp3toiphone.library import load_track
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        tracks = []
        for number in range(3):
            path = tmp_path / f"brano{number}.mp3"
            write_mp3(path, 40 + number)
            track = load_track(path)
            window.tag_cache.store(track)
            tracks.append(track)
        window.tracks = tracks
        news = []

        def run():
            window._start_fingerprints()
            window._fingerprint_job.item.connect(news.append)
            start = time.time()
            while window._fingerprint_job.running and time.time() - start < 20:
                app.processEvents()
                time.sleep(0.01)
            app.processEvents()

        run()
        for track in tracks:
            assert window.tag_cache.fingerprint(track.path).startswith("mp3:")
        assert (main_window.FINGERPRINTS_DONE, 3) in news
        news.clear()
        run()                                                    # la seconda volta: niente da ricalcolare
        assert (main_window.FINGERPRINTS_TO_DO, 0) in news and (main_window.FINGERPRINTS_DONE, 0) in news
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_link_source_to_a_file_that_is_gone_does_not_crash(tmp_path, monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import provenance
    from myeasymp3toiphone.gui import source_dialog
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])

    class Chosen:
        def __init__(self, *args):
            self.chosen = tmp_path / "spostato" / "01.mp3"         # nell'elenco di prima, ora non c'è più
            self.how = provenance.HOW_MANUAL
            self.skipped = False

        def exec(self):
            return True

    monkeypatch.setattr(source_dialog, "SourceDialog", Chosen)
    window = MainWindow()
    try:
        item = _phone(1, "Uno", "Gruppo Finto", "Disco")
        item.sync_id = 11
        window.registry = provenance.Registry()
        panel = window.iphone_panel
        moved_on = []
        monkeypatch.setattr(panel, "_next_source", lambda: moved_on.append(True))
        panel._show_sources(item, [])
        assert moved_on == [True] and window.registry.get(11) is None   # niente nel registro, si va avanti
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_keys_f5_and_delete(tmp_path, monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import provenance
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        panel = window.iphone_panel
        calls = []
        monkeypatch.setattr(window, "reload_folder", lambda: calls.append("PC"))
        monkeypatch.setattr(panel, "refresh", lambda: calls.append("iPhone"))
        window._tabs.setCurrentIndex(0)
        window._refresh_current_tab()
        window._tabs.setCurrentWidget(panel)
        window._refresh_current_tab()
        assert calls == ["PC", "iPhone"]                              # F5: Aggiorna della scheda che si vede

        here = [_pc("Uno", "Gruppo Finto", "Disco"), _pc("Due", "Gruppo Finto", "Disco")]
        window.tracks = here
        phone = [_phone(1, "Uno", "Gruppo Finto", "Disco")]
        phone[0].sync_id = 11
        registry = provenance.Registry()
        registry.record(provenance.Link(sync_id=11, pc=provenance.computer_name(), path=str(here[0].path)))
        window.registry = registry
        window.set_phone_tracks(phone, "iPhone di prova")
        window._rebuild_views()
        from myeasymp3toiphone.pending import REMOVE
        window._table.selectAll()
        window._remove_selected_from_phone()        # Canc: in attesa solo quello sull'iPhone, associato (senza iPhone)
        assert window.pending.get(here[0].path) == REMOVE and not window.pending.get(here[1].path)
        assert "Elimina" in window._pending_label.text() or "eliminare" in window._pending_label.text()

        deleted = []
        monkeypatch.setattr(panel, "_delete_selected", lambda: deleted.append(len(panel._selected_phone_tracks())))
        panel._music_view.setCurrentItem(panel._music_view.topLevelItem(0))
        panel._music_view.clearSelection()
        panel._delete_current()                                      # Canc nella scheda iPhone: Elimina, in attesa
        assert deleted == [1]
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_complete_the_album_sends_only_the_missing_tracks_of_that_copy(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import provenance
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        def track(folder, title, number, suffix=".mp3"):
            result = Track(path=Path(f"D:/{folder}/Disco Finto/{number:02d}{suffix}"),
                           tags=TrackTags(title=title, artist="Gruppo Finto", album="Disco Finto", track_number=number))
            return result

        mp3 = [track("musica", "Uno", 1), track("musica", "Due", 2), track("musica", "Tre", 3)]
        flac = [track("musica.flac", "Due", 2, ".flac")]                # un'altra copia: non si manda
        window.tracks = mp3 + flac
        phone = [_phone(1, "Uno", "Gruppo Finto", "Disco Finto", track_number=1),
                 _phone(2, "Altro", "Gruppo Finto", "Altro Disco")]
        phone[0].sync_id, phone[1].sync_id = 11, 12
        registry = provenance.Registry()
        registry.record(provenance.Link(sync_id=11, pc=provenance.computer_name(), path=str(mp3[0].path)))
        window.registry = registry
        window.set_phone_tracks(phone, "iPhone di prova")
        window._rebuild_views()
        panel = window.iphone_panel
        sends, albums = panel.complete_plan([phone[0]])
        assert [item.title for item in sends] == ["Due", "Tre"] and albums == 1
        assert panel.complete_plan([phone[1]]) == ([], 0)          # senza sorgente associata: niente
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_warning_for_songs_already_on_the_iphone_in_another_format(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui.main_window import MainWindow
    from myeasymp3toiphone.phone_library import format_duplicates

    def pc(folder, title, suffix, length=200.0, album="Raccolta Finta"):
        return Track(path=Path(f"D:/{folder}/{title}{suffix}"), length=length,
                     tags=TrackTags(title=title, artist="Cantante Finto", album=album))

    phone = [_phone(1, "Uno", "Cantante Finto", "Raccolta Finta")]      # sull'iPhone in MP3, 200 s
    flac_one = pc("musica.flac", "Uno", ".flac", 201.0)                 # la stessa canzone in FLAC: avviso
    other_album = pc("altro", "Uno", ".mp3", 200.0, "Altro Disco")      # stesso formato, altra raccolta: niente
    live = pc("musica.flac", "Uno", ".flac", 260.0)                     # altra durata (dal vivo): niente
    two_mp3 = pc("musica.ok", "Due", ".mp3")                            # nello stesso invio due formati: se ne
    two_flac = pc("musica.flac", "Due", ".flac")                        # tiene uno, la cartella preferita
    duplicates, remaining = format_duplicates([flac_one, other_album, live, two_flac, two_mp3], phone,
                                              ("musica.ok", "musica.flac"))
    assert [(track.path.parent.name, track.tags.title) for track, _reason in duplicates] == [
        ("musica.flac", "Uno"), ("musica.flac", "Due")]
    assert "sull'iPhone in MP3" in duplicates[0][1] and "nello stesso invio" in duplicates[1][1]
    assert remaining == [other_album, live, two_mp3]

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        window.set_phone_tracks(phone, "iPhone di prova")
        panel = window.iphone_panel
        from myeasymp3toiphone.overlay import path_key
        from myeasymp3toiphone.pending import FILE_PREFIX, SEND, Job
        sent = []
        monkeypatch.setattr(panel, "_run_jobs", lambda jobs, sends, *args: sent.append(sends))
        monkeypatch.setattr(panel, "_connected", True)
        window.pending.set(flac_one.path, SEND)
        window.pending.set(other_album.path, SEND)
        panel.apply_jobs([Job(FILE_PREFIX + path_key(flac_one.path), SEND, track=flac_one),
                          Job(FILE_PREFIX + path_key(other_album.path), SEND, track=other_album)])  # "Invia senza questi"
        assert sent == [[other_album]]
        assert window.pending.get(flac_one.path) == "" and window.pending.get(other_album.path) == SEND  # fuori coda
        assert "Tolto dalla coda 1 brano" in window.statusBar().currentMessage() or \
            "Tolto dalla coda 1 brano" in window._pending_last.text()
        panel.apply_jobs([Job("a", SEND, track=flac_one)])        # erano tutti doppioni: niente da copiare
        assert sent == [[other_album]] and "Niente da applicare" in window.statusBar().currentMessage()
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_everything_for_the_iphone_waits_for_apply(tmp_path, monkeypatch):
    """Copia, Ricopia, Usa i tag, Cambia i tag ed Elimina vanno in attesa dalle due schede, anche senza iPhone; la
    finestra di Applica le elenca e la ✕ ne toglie una dalla coda."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import provenance
    from myeasymp3toiphone.gui.apply_dialog import ApplyDialog, summary
    from myeasymp3toiphone.gui.main_window import MainWindow
    from myeasymp3toiphone.pending import DELETE, EDIT, REPLACE, SEND
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        here = [_pc("Uno", "Gruppo Finto", "Disco"), _pc("Due", "Gruppo Finto", "Disco", year="2001"),
                _pc("Tre", "Gruppo Finto", "Disco")]
        window.tracks = here
        phone = [_phone(1, "Uno", "Gruppo Finto", "Disco"), _phone(2, "Due", "Gruppo Finto", "Disco", year="2000"),
                 _phone(3, "Solo qui", "Altro Gruppo", "Altro Disco")]
        phone[0].sync_id, phone[1].sync_id, phone[2].sync_id = 11, 12, 13
        registry = provenance.Registry()
        for item, track in zip(phone[:2], here[:2]):
            registry.record(provenance.Link(sync_id=item.sync_id, pc=provenance.computer_name(), path=str(track.path)))
        window.registry = registry
        window.set_phone_tracks(phone, "iPhone di prova")
        window._rebuild_views()
        panel = window.iphone_panel
        assert not panel.connected
        window.queue_files(here, SEND)                               # solo "Tre" non è sull'iPhone
        assert window._pending_last.text() == "Appena aggiunti: 1 brano da copiare da PC a iPhone"
        panel._fill_music()
        window.queue_pairs(panel._stale_pairs(phone), REPLACE)       # "Due" dalla scheda iPhone
        window.queue_deletes([phone[2]])
        window.queue_edits([phone[0]], {"genre": "Rock"})
        jobs = window.pending_jobs()
        assert sorted(job.action for job in jobs) == sorted([SEND, REPLACE, DELETE, EDIT])
        assert summary(jobs).startswith("1 brano da copiare da PC a iPhone · 1 brano da ricopiare")
        tab = window._tabs.indexOf(panel)
        assert window._tabs.tabText(tab) == "iPhone · 4 in attesa"
        assert window._apply_button.isEnabled() and window._apply_button.text() == "Applica 4 azioni…"
        dialog = ApplyDialog(window, jobs, window._remove_pending, panel.jobs_seconds, panel.jobs_notes, False,
                             "iPhone di prova")
        assert not dialog._apply.isEnabled()                         # iPhone non connesso: si guarda soltanto
        delete_key = [job.key for job in jobs if job.action == DELETE]
        dialog._drop(delete_key)                                     # la ✕ di "Elimina"
        assert len(dialog.jobs) == 3 and window.pending.total() == 3
        dialog.close()
        assert "iPhone · 3 in attesa" == window._tabs.tabText(tab)

        # la ✕ si clicca nella terza colonna; "Togli le selezionate" e Canc tolgono le righe scelte
        from PySide6.QtCore import QEvent, Qt
        from PySide6.QtGui import QKeyEvent
        dialog = ApplyDialog(window, window.pending_jobs(), window._remove_pending, panel.jobs_seconds,
                             panel.jobs_notes, False, "iPhone di prova")
        tree = dialog._tree
        assert tree.topLevelItemCount() == 3 and not dialog._remove_selected.isEnabled()
        first_group = tree.topLevelItem(0)
        dialog._clicked(first_group.child(0), 0)                     # clic sul nome: niente
        assert len(dialog.jobs) == 3
        dialog._clicked(first_group.child(0), 2)                     # clic sulla ✕
        assert len(dialog.jobs) == 2 and window.pending.total() == 2
        tree.topLevelItem(0).child(0).setSelected(True)
        assert dialog._remove_selected.isEnabled()
        dialog._drop_selected()
        assert len(dialog.jobs) == 1 and tree.topLevelItemCount() == 1
        tree.topLevelItem(0).setSelected(True)                       # il gruppo intero, con Canc
        dialog.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier))
        assert dialog.jobs == [] and window.pending.total() == 0 and not dialog._apply.isEnabled()
        dialog.close()

        # Cambia i tag (il riquadro a destra, riaperto dopo la ✕) con "Anche sul PC": gli stessi tag sul file del PC,
        # in sospeso; la casella si rispegne
        panel._tag_box.setVisible(False)
        panel._edit_items([phone[1]])
        tags_panel = panel._tag_panel
        assert not panel._tag_box.isHidden() and tags_panel.fields["title"].text() == phone[1].tags.title
        assert tags_panel._also_pc.isEnabled()
        tags_panel.fields["genre"].setText("Jazz")
        tags_panel._also_pc.setChecked(True)
        tags_panel._check()
        assert window.overlay.is_edited(here[1].path) and here[1].tags.genre == "Jazz"
        assert "sul PC gli stessi tag" in window._pending_last.text() and not tags_panel._also_pc.isChecked()
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_change_tags_on_the_iphone_checks_and_converts_the_values(monkeypatch):
    """Cambia i tag (riquadro della scheda iPhone): i numeri si controllano ("²" no), un campo uguale o vuoto non
    cambia, 0 svuota; artista e tracce totali non si cambiano; con più brani il titolo non si cambia e i valori diversi
    lo dicono; i brani non messi da un computer si vedono ma non si cambiano; con "Anche sul PC" i valori diventano
    quelli di un TrackTags del PC."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QMessageBox
    from myeasymp3toiphone.gui.iphone_panel import _pc_value
    from myeasymp3toiphone.gui.phone_tag_panel import ONE_AT_A_TIME, PhoneTagPanel
    from myeasymp3toiphone.gui.tag_editor import MIXED
    app = QApplication.instance() or QApplication([])
    warnings = []
    queued = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args[2]))
    monkeypatch.setattr(QMessageBox, "information", lambda *args: warnings.append(args[2]))
    panel = PhoneTagPanel()
    panel.queue_requested.connect(lambda items, values, also_pc: queued.append((len(items), values, also_pc)))
    one = _phone(1, "Uno", "Gruppo Finto", "Disco", year="2000")
    one.sync_id = 11
    panel.set_tracks([one], 1)
    assert panel.fields["artist"].isReadOnly() and not panel.fields["title"].isReadOnly()
    assert panel.fields["track_total"].isReadOnly() and panel._also_pc.isEnabled()
    assert not panel._save_button.isEnabled()
    panel.fields["year"].setText("²")
    panel._check()
    assert warnings == ["year: serve un numero"] and queued == []
    panel.fields["year"].setText("0")                                   # 0 svuota
    panel.fields["track_number"].setText(" 7 ")
    panel.fields["album"].setText("Disco")                              # uguale: non cambia
    panel.fields["artist"].setText("Altro")                             # non si cambia sull'iPhone
    panel._check()
    assert queued == [(1, {"year": 0, "track_number": 7}, False)]

    two = _phone(2, "Due", "Gruppo Finto", "Disco", year="2001")
    two.sync_id = 12
    bought = _phone(3, "Tre", "Gruppo Finto", "Disco")                  # sync_id 0: acquistato sul telefono
    panel.set_tracks([one, two, bought], 0)
    assert not panel.fields["title"].isEnabled() and panel.fields["title"].placeholderText() == ONE_AT_A_TIME
    assert panel.fields["year"].placeholderText() == MIXED and panel.fields["album"].text() == "Disco"
    assert "1 dei brani scelti" in panel._kinds.text() and not panel._also_pc.isEnabled()
    panel.fields["genre"].setText("Jazz")
    panel._check()
    assert queued[-1] == (2, {"genre": "Jazz"}, False)
    panel.set_tracks([bought])
    assert not panel.fields["album"].isEnabled() and not panel.focus_first_field()
    assert (_pc_value("year", 0), _pc_value("year", 1999), _pc_value("track_number", 0),
            _pc_value("disc_number", 2), _pc_value("compilation", 1), _pc_value("genre", "Jazz")) == \
        ("", "1999", None, 2, True, "Jazz")
    panel.close()
    app.processEvents()


def test_filter_chips_and_action_bars(tmp_path):
    """I filtri a pulsanti contano i brani e filtrano la tabella; la barra delle azioni ha le voci del tasto destro
    per i brani scelti; il menu Strumenti della scheda iPhone si riempie all'apertura."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import provenance
    from myeasymp3toiphone.gui import iphone_panel, main_window
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        here = [_pc("Uno", "Gruppo Finto", "Disco"), _pc("Due", "Gruppo Finto", "Disco", year="2001"),
                _pc("Tre", "Gruppo Finto", "Disco"), _pc("Quattro", "Gruppo Finto", "Disco")]
        window.tracks = here
        phone = [_phone(1, "Uno", "Gruppo Finto", "Disco"), _phone(2, "Due", "Gruppo Finto", "Disco", year="2000"),
                 _phone(4, "Quattro", "Gruppo Finto", "Disco")]
        phone[0].sync_id, phone[1].sync_id, phone[2].sync_id = 11, 12, 14
        registry = provenance.Registry()
        for item, track in zip(phone[:2], here[:2]):
            registry.record(provenance.Link(sync_id=item.sync_id, pc=provenance.computer_name(), path=str(track.path)))
        window.registry = registry
        window.set_phone_tracks(phone, "iPhone di prova")
        window._rebuild_views()
        keys = [key for key, _text, _tip in main_window.PC_CHIPS]
        counts = dict(zip(keys, window._chips._counts))
        assert counts == {"all": 4, "absent": 1, "same": 1, "stale": 1, "probable": 1, "edited": 0, "stray": 0,
                          "pending": 0}
        window._chips.setCurrentIndex(keys.index("stale"))
        assert [track.title for track in window._visible] == ["Due"]
        window._table.selectAll()
        bar = window._actions
        assert bar._who.text() == "1 brano scelto:"
        assert bar.button("replace").text() == "Ricopia da PC a iPhone: 1 brano" and bar.button("replace").isEnabled()
        assert not bar.button("copy").isEnabled()
        bar.button("tags").click()                                   # Usa i tag da PC a iPhone: in attesa
        assert window.pending.total() == 1 and dict(zip(keys, window._chips._counts))["pending"] == 1
        window._chips.setCurrentIndex(0)

        panel = window.iphone_panel
        panel._fill_music()
        texts = [text for text, _rule in iphone_panel.SHOW_FILTERS]
        shown = dict(zip(texts, panel._show._counts))
        assert shown["Tutti i brani"] == 3 and shown["Da rivedere: abbinati solo per i tag (≈)"] == 1
        panel._music_view.selectAll()
        assert panel._actions._who.text() == "3 brani scelti:"
        assert panel._actions.button("delete").text() == "Elimina 3 brani dall'iPhone"
        panel._fill_tools()
        tools = [action.text() for action in panel._tools.actions() if action.text()]
        assert "Associa al file sul PC tutti i brani senza sorgente…" in tools
        assert any(text.startswith("Usa i tag da iPhone a PC: 1 brano") for text in tools)
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_empty_filter_goes_back_to_all_and_hidden_tracks_are_told(tmp_path):
    """Il filtro "In attesa" dopo che la coda si svuota torna su Tutti (prima la tabella restava vuota mentre l'album
    diceva 20 brani); quando un filtro nasconde dei brani la nota lo dice, con Mostra tutti."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui import main_window
    from myeasymp3toiphone.gui.main_window import MainWindow
    from myeasymp3toiphone.pending import SEND
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        here = [_pc("Uno", "Gruppo Finto", "Disco"), _pc("Due", "Gruppo Finto", "Disco")]
        window.tracks = here
        window.set_phone_tracks([_phone(9, "Altro", "Altro Gruppo", "Altro Disco")], "iPhone di prova")
        window._rebuild_views()
        keys = [key for key, _text, _tip in main_window.PC_CHIPS]
        window.queue_files([here[0]], SEND)
        window._chips.setCurrentIndex(keys.index("pending"))
        assert [track.title for track in window._visible] == ["Uno"]
        chips = window._chips
        assert not chips._note.isHidden() and "si vedono 1 di 2 brani" in chips._note.text()
        window._undo_pending()                                   # la coda si svuota (QMessageBox: Sì)
        assert chips.currentIndex() == 0 and len(window._visible) == 2
        assert chips._note.isHidden() and chips._reset.isHidden()
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_apply_removes_done_actions_and_tells_what_it_did(tmp_path):
    """Alla fine di Applica le azioni riuscite escono subito dalla coda (anche se l'iPhone aggiorna il suo elenco più
    tardi), quelle non riuscite restano; il messaggio dice cosa è stato fatto, per specie, e perché il resto no."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import phone_actions
    from myeasymp3toiphone.gui import iphone_panel
    from myeasymp3toiphone.gui.main_window import MainWindow
    from myeasymp3toiphone.pending import DELETE, SEND
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        here = [_pc("Uno", "Gruppo Finto", "Disco"), _pc("Due", "Gruppo Finto", "Disco")]
        window.tracks = here
        phone = [_phone(9, "Vecchio", "Gruppo Finto", "Disco")]
        phone[0].sync_id = 99
        window.set_phone_tracks(phone, "iPhone di prova")
        window._rebuild_views()
        window.queue_files(here, SEND)
        window.queue_deletes(phone)
        jobs = window.pending_jobs()
        assert len(jobs) == 3
        report = phone_actions.ActionReport(done=2, sent_tracks=[here[0]], done_sync_ids=[99],
                                            errors=[("Gruppo Finto — Due", "Due.mp3: non è un MP3 leggibile")])
        done = iphone_panel.done_jobs(jobs, report)
        assert sorted(job.action for job in done) == sorted([SEND, DELETE])
        text = iphone_panel.apply_report_text(report, done, len(jobs))
        assert "• 1 brano copiato da PC a iPhone" in text and "• 1 brano eliminato dall'iPhone" in text
        assert "1 azione non è riuscita: resta in attesa" in text and "Due.mp3: non è un MP3 leggibile" in text
        window.pending_done([job.key for job in done], len(jobs) - len(done))
        assert window.pending.total() == 1 and window.pending.get(here[1].path) == SEND
        assert window._apply_button.text() == "Applica 1 azione…"
        assert window._pending_last.text() == "Applicate 2 azioni sull'iPhone; 1 non riuscita resta in attesa."
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_after_apply_reread_if_the_iphone_does_not_show_the_changes_yet(monkeypatch):
    """Dopo Applica: se l'elenco riletto non mostra ancora un brano copiato (o mostra ancora uno eliminato) la
    musica dell'iPhone si rilegge da sola dopo qualche secondo, al più qualche volta; se mostra tutto, no."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui import iphone_panel
    from myeasymp3toiphone.gui.main_window import MainWindow
    from myeasymp3toiphone.pending import DELETE, SEND, Job
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        sent = _pc("Nuovo", "Gruppo Finto", "Disco")
        window.tracks = [sent]
        old = _phone(9, "Vecchio", "Gruppo Finto", "Disco")
        old.sync_id = 99
        window.set_phone_tracks([old], "iPhone di prova")
        window._rebuild_views()
        panel = window.iphone_panel
        jobs = [Job("file:nuovo", SEND, track=sent), Job("pid:9", DELETE, phone=old)]
        assert panel.lagging(jobs) == jobs                    # il nuovo non c'è, il vecchio c'è ancora
        scheduled = []
        monkeypatch.setattr(iphone_panel.QTimer, "singleShot", lambda ms, slot: scheduled.append(ms))
        monkeypatch.setattr(panel, "_connected", True)
        panel._recheck_later(jobs, iphone_panel.RECHECK_TRIES)
        assert scheduled == [iphone_panel.RECHECK_SECONDS * 1000]
        window.set_phone_tracks([_phone(10, "Nuovo", "Gruppo Finto", "Disco")], "iPhone di prova")   # aggiornato
        assert panel.lagging(jobs) == []
        panel._recheck_later(jobs, iphone_panel.RECHECK_TRIES)
        assert len(scheduled) == 1                            # niente da aspettare
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_stop_never_leaves_an_album_half_sent():
    """Ferma durante l'invio: si finisce l'album già cominciato (anche oltre un gruppo), poi ci si ferma; un brano non
    resta mai a metà (ogni gruppo è una sessione intera)."""
    from types import SimpleNamespace
    from myeasymp3toiphone import phone_actions

    def item(album, number):
        tags = TrackTags(title=f"Brano {number}", artist="Gruppo Finto", album=album, track_number=number)
        return SimpleNamespace(track=SimpleNamespace(tags=tags))

    mixed = [item("Primo", 1), item("Secondo", 1), item("Primo", 2), item("Secondo", 2)]
    ordered = phone_actions.by_album(mixed)
    assert [(i.track.tags.album, i.track.tags.track_number) for i in ordered] == [
        ("Primo", 1), ("Primo", 2), ("Secondo", 1), ("Secondo", 2)]
    big = [item("Lungo", number) for number in range(1, 31)] + [item("Corto", number) for number in range(1, 4)]
    assert phone_actions.batch_end(big, 0, False) == 25                  # di solito: gruppi di 25
    assert phone_actions.batch_end(big, 0, True) == 0                    # Ferma prima di cominciare: niente
    assert phone_actions.batch_end(big, 25, True) == 30                  # Ferma a metà di "Lungo": lo si finisce
    assert phone_actions.batch_end(big, 30, True) == 30                  # finito "Lungo": "Corto" non comincia
    assert phone_actions.batch_end(big, 30, False) == 33


def _button_color(app, button):
    app.processEvents()
    image = button.grab().toImage()
    result = image.pixelColor(image.width() // 2, 3).name()
    return result


def test_apply_button_turns_red_while_applying(monkeypatch):
    """Durante Applica il pulsante dice Ferma ed è rosso davvero (non solo il testo), alla fine torna verde."""
    import threading
    import time
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui import main_window as mw
    from myeasymp3toiphone.gui import theme
    from myeasymp3toiphone.pending import SEND
    app = QApplication.instance() or QApplication([])
    theme.apply_theme(app)
    window = mw.MainWindow()
    window.show()
    release = threading.Event()
    try:
        here = [_pc("Uno", "Gruppo Finto", "Disco")]
        window.tracks = here
        window.set_phone_tracks([], "iPhone di prova")
        window._rebuild_views()
        window.queue_files(here, SEND)
        assert _button_color(app, window._apply_button) == theme.GREEN

        def fake_apply(jobs, closing=False, then=None):
            window.runner.run("prova", lambda progress, cancel: release.wait(10), lambda value: None)

        monkeypatch.setattr(window.iphone_panel, "apply_jobs", fake_apply)
        monkeypatch.setattr(mw.ApplyDialog, "exec", lambda dialog: 1)
        window._apply_clicked()
        app.processEvents()
        assert window._apply_button.text() == "Ferma" and window._apply_button.isEnabled()
        assert _button_color(app, window._apply_button) == theme.RED
        release.set()
        deadline = time.time() + 5
        while window.runner.is_busy and time.time() < deadline:
            app.processEvents()
        app.processEvents()
        assert window._apply_button.text() == "Applica 1 azione…"
        assert _button_color(app, window._apply_button) == theme.GREEN
    finally:
        release.set()
        window._exit_checked = True
        window.close()
