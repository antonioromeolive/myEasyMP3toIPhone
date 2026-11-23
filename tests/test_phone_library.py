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
        ["Titolo"]       # ritrovato senza badare a maiuscole e spazi; il titolo differisce, l'artista (un gruppo) no
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
    assert ("Anno", "1991", "1990", True) in rows and ("Artista", "A", "a", False) in rows
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
        assert [item.pid for item, _track in panel._aligned_pairs(phone)] == [1]
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
        panel._align_to_pc(panel._aligned_pairs(phone))          # l'elenco dei file, Annulla: niente cambia
        wait_idle()
        assert len(shown) == 1 and read_tags(outside)[0].year == "1991"
        monkeypatch.setattr(iphone_panel.AlignToPcDialog, "exec", lambda dialog: True)
        panel._align_to_pc(panel._aligned_pairs(phone))          # vale l'iPhone: l'anno 1990 si scrive nel file
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
        window.mark_for_update([linked, by_tags])
        assert window.pending.get(linked.path) == UPDATE and not window.pending.get(by_tags.path)
        window.pending.set(by_tags.path, UPDATE)               # rimasto da una versione precedente
        _sends, _removes, updates = window.pending_work()
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
    """L'iPhone tiene la grafia del suo album o artista "uguale": "01" = "1", "AA.VV." = "Artisti Vari". Quelle
    differenze non si possono correggere con un invio e non fanno giallo; le altre sì."""
    from myeasymp3toiphone.library import phone_group_key
    assert phone_group_key("Raccolta 01 - Estate") == phone_group_key("Raccolta 1 - Estate")
    assert phone_group_key("AA.VV.") == phone_group_key("Artisti Vari") == phone_group_key("Various Artists")
    assert phone_group_key("Festival 1990") != phone_group_key("Festival 199")
    assert phone_group_key("Disco 10") != phone_group_key("Disco 1")
    pc = TrackTags(title="Uno", artist="Anna", album="Raccolta 01 - Estate", album_artist="AA.VV.", compilation=True)
    phone = TrackTags(title="Uno", artist="Anna", album="Raccolta 1 - Estate", album_artist="Artisti Vari",
                      compilation=True)
    assert differences(pc, phone) == []
    phone.album_artist = "Michael Rossi"
    assert [label for label, _a, _b in differences(pc, phone)] == ["Artista album"]
