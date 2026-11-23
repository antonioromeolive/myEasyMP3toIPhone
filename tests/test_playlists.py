# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Playlist per artista e per compilation: il piano, le operazioni, la lettura dal database, la finestra. Nessun
iPhone. Nomi e cartelle inventati."""

import sqlite3
from datetime import datetime

import pytest

from myeasymp3toiphone import phone_sync as ps
from myeasymp3toiphone import playlists
from myeasymp3toiphone.phone_library import PhonePlaylist, PhoneTrack, container_ids, read_playlists
from myeasymp3toiphone.tags import TrackTags

_next = [1000]


def _track(title, artist, album, number=1, album_artist="", year="", disc=None, compilation=False, sync=True):
    _next[0] += 1
    tags = TrackTags(title=title, artist=artist, album=album, album_artist=album_artist, track_number=number,
                     year=year, disc_number=disc, compilation=compilation)
    result = PhoneTrack(pid=_next[0], remote_path=f"/iTunes_Control/Music/F01/{_next[0]}.mp3", size=1, length=200.0,
                        tags=tags, sync_id=_next[0] if sync else 0)
    return result


def _album(artist, album, count, year="", album_artist=None, disc=None):
    result = []
    for number in range(1, count + 1):
        result.append(_track(f"{album} {number}", artist, album, number,
                             artist if album_artist is None else album_artist, year, disc))
    return result


def _by_name(plan):
    result = {}
    for playlist in plan.create:
        result[playlist.name] = playlist
    return result


def test_artist_playlists_need_two_albums_and_five_tracks():
    tracks = (_album("Rosa Neri", "Secondo", 4, "1975") + _album("Rosa Neri", "Primo", 4, "1971")
              + _album("Bruno Blu", "Unico", 12, "1980")                         # un album solo
              + _album("Gino Verdi", "A", 2) + _album("Gino Verdi", "B", 2)       # due album, 4 brani
              + [_track("Ospite", "Altro Artista", "Secondo", 9, "Rosa Neri")])   # conta l'artista dell'album
    tracks += _album("Rosa Neri", "Terzo", 3, "1979") + [_track("Comprata", "Rosa Neri", "Store", sync=False)]
    plan = playlists.plan(tracks, [], {})
    created = _by_name(plan)
    assert list(created) == ["♪ Rosa Neri"]
    rosa = created["♪ Rosa Neri"]
    assert rosa.kind == playlists.KIND_ARTIST and rosa.albums == ["Primo", "Secondo", "Terzo"]    # per anno
    assert len(rosa.tracks) == 12 and rosa.tracks[0].tags.title == "Primo 1"
    assert [t.tags.title for t in rosa.tracks[4:9]] == ["Secondo 1", "Secondo 2", "Secondo 3", "Secondo 4", "Ospite"]
    assert plan.left_out == 1 and all(member != 0 for member in rosa.members)


def test_discs_of_one_album_count_as_one_album():
    tracks = _album("Anna", "Doppio (CD 1)", 6, disc=1) + _album("Anna", "Doppio (CD 2)", 6, disc=2)
    assert playlists.plan(tracks, [], {}).create == []
    tracks += _album("Anna", "Altro", 3)
    assert [p.name for p in playlists.plan(tracks, [], {}).create] == ["♪ Anna"]


def test_compilations_by_various_artists_series_and_many_artists():
    tracks = []
    for volume in (2, 1, 10):
        for number in range(1, 4):
            tracks.append(_track(f"Hit {volume}.{number}", f"Cantante {number}", f"Raccolta Ottanta Vol. {volume}", number,
                                 "AA.VV."))
    big = []
    for number in range(1, 22):                       # nessun "AA.VV.": tanti artisti diversi
        big.append(_track(f"Canzone {number}", f"Artista {number % 7}", "Estate Grande", number))
    small = [_track("Sola", "X", "Piccola", 1, "Artisti vari"), _track("Altra", "Y", "Piccola", 2, "Artisti vari")]
    plan = playlists.plan(tracks + big + small, [], {})
    created = _by_name(plan)
    assert set(created) == {"♪ Raccolta Ottanta", "♪ Estate Grande"}       # "Piccola": un album, pochi brani
    series = created["♪ Raccolta Ottanta"]
    assert series.kind == playlists.KIND_COMPILATION
    assert series.albums == ["Raccolta Ottanta Vol. 1", "Raccolta Ottanta Vol. 2", "Raccolta Ottanta Vol. 10"]
    assert [t.tags.title for t in series.tracks[:4]] == ["Hit 1.1", "Hit 1.2", "Hit 1.3", "Hit 2.1"]
    assert "♪ Artista 1" not in created               # i brani di una compilation non fanno playlist per artista


def test_compilations_grouped_by_root_folder():
    tracks = []
    sources = {}
    names = ["Raccolta Mare (primo)", "Mare d'estate 2", "Le canzoni del mare 3"]
    for index, album in enumerate(names):
        for number in range(1, 4):
            item = _track(f"T{index}{number}", f"A{number}", album, number, "AA.VV.")
            tracks.append(item)
            sources[item.sync_id] = f"F:\\Musica\\Mare\\{album}\\CD1\\{number:02d}.mp3"
    other = _track("Z", "B", "Festival 1992", 1, "AA.VV.")
    tracks.append(other)
    sources[other.sync_id] = "F:\\Musica\\Mare\\Festival 1992\\01.mp3"     # nella radice, ma non è "Mare"
    plan = playlists.plan(tracks, [], {})
    assert plan.create == []                                               # senza cartelle: tre album diversi
    plan = playlists.plan(tracks, [], sources)
    created = _by_name(plan)
    assert list(created) == ["♪ Mare"]                                   # il nome della cartella radice
    assert created["♪ Mare"].albums == ["Le canzoni del mare 3", "Mare d'estate 2", "Raccolta Mare (primo)"]


def test_delete_every_computer_playlist_keep_phone_ones():
    phone_made = PhonePlaylist(pid=5, sync_id=0, name="Corsa", count=3)
    copytrans = PhonePlaylist(pid=6, sync_id=66, name="Album X", count=10)
    plan = playlists.plan([], [phone_made, copytrans], {})
    assert plan.delete == [copytrans] and plan.kept == [phone_made]


def test_series_helpers():
    assert playlists.series_key("Raccolta Ottanta - Vol. 3 (CD 2)") == playlists.series_key("Raccolta Ottanta Volume 1")
    assert playlists.series_name("Raccolta Ottanta Vol. 3") == "Raccolta Ottanta"
    assert playlists.series_name("Festival 1992") == "Festival 1992"
    assert playlists.is_various("AA.VV.") and playlists.is_various("Various Artists") and not playlists.is_various("Ava")


def test_playlist_operations():
    when = datetime(2026, 11, 23, 8, 0, 0)
    operation = ps.insert_playlist(2 ** 63 + 5, "♪ Rosa Neri", [11, 2 ** 64 - 1], when)
    assert operation["operation"] == "insert_playlist" and operation["pid"] < 0
    assert operation["container"] == {"name": "♪ Rosa Neri", "date_created": when, "date_modified": when}
    assert operation["item_to_container"] == [11, -1]
    assert operation["container_ui"]["play_order"] == 1 and operation["container_ui"]["shuffle_items"] is False
    assert ps.delete_playlist(66) == {"operation": "delete_playlist", "pid": 66}
    with pytest.raises(ps.PhoneSyncError):
        ps.delete_playlist(0)                      # fatta sul telefono
    with pytest.raises(ps.PhoneSyncError):
        ps.insert_playlist(7, "Vuota", [], when)
    with pytest.raises(ps.PhoneSyncError):
        ps.insert_playlist(7, "Con un brano del telefono", [0], when)
    assert ps.operation_file(1, when, [operation])     # entra in un file delle operazioni


def test_read_playlists_and_ids(tmp_path):
    path = tmp_path / "MediaLibrary.sqlitedb"
    connection = sqlite3.connect(str(path))
    connection.executescript("""
CREATE TABLE container (container_pid INTEGER PRIMARY KEY, sync_id INTEGER, distinguished_kind INTEGER,
                        is_hidden INTEGER, smart_criteria BLOB, smart_is_folder INTEGER, name TEXT);
CREATE TABLE container_item (container_item_pid INTEGER PRIMARY KEY, container_pid INTEGER, item_pid INTEGER);
CREATE TABLE db_info (db_pid INTEGER, primary_container_pid INTEGER);
INSERT INTO db_info VALUES (9, 1);
INSERT INTO container VALUES (1, 1, 0, 0, NULL, 0, 'Libreria'), (2, 0, 0, 0, NULL, 0, 'Corsa'),
                             (3, -5, 0, 0, NULL, 0, 'Album X'), (4, 44, 0, 0, x'00', 0, 'Smart'),
                             (7, 77, 200, 0, NULL, 0, 'Preferiti');
INSERT INTO container_item VALUES (1, 2, 101), (2, 2, 102), (3, 3, 101);
""")
    connection.commit()
    connection.close()
    found = read_playlists(path)
    assert [(p.name, p.sync_id, p.count, p.from_computer) for p in found] == \
        [("Album X", 2 ** 64 - 5, 1, True), ("Corsa", 0, 2, False)]
    assert {1, 2, 3, 2 ** 64 - 5, 44, 77} <= container_ids(path)


def test_playlist_dialog():
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui.playlist_dialog import TEST_NAME, PlaylistDialog
    app = QApplication.instance() or QApplication([])
    tracks = _album("Rosa Neri", "Primo", 4, "1971") + _album("Rosa Neri", "Secondo", 4, "1975")
    tracks += _album("Gino Verdi", "A", 3) + _album("Gino Verdi", "B", 3)
    plan = playlists.plan(tracks, [PhonePlaylist(1, 0, "Corsa", 2), PhonePlaylist(2, 9, "Album X", 3)], {})
    dialog = PlaylistDialog(None, plan)
    assert len(dialog.chosen()) == 2 and dialog.test_playlist().name == TEST_NAME
    first_row = dialog._created[0][0]
    first_row.setCheckState(0, Qt.Unchecked)
    assert [p.name for p in dialog.chosen()] == ["♪ Rosa Neri"] and dialog.test_playlist().tracks[0].sync_id
    dialog._created[1][0].setCheckState(0, Qt.Unchecked)
    assert not dialog.test_button.isEnabled() and dialog.apply_button.isEnabled()     # restano da cancellare
    app.processEvents()
