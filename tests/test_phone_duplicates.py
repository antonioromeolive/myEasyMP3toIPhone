# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""I doppioni sull'iPhone: stessa canzone nello stesso album (uno da tenere) o in più album (legittimo), quale copia
tenere, e la sostituzione all'invio. Nomi e valori inventati."""

import os
from pathlib import Path

from conftest import write_mp3
from myeasymp3toiphone import phone_duplicates
from myeasymp3toiphone.library import Track
from myeasymp3toiphone.phone_library import PhoneTrack
from myeasymp3toiphone.tags import TrackTags

KBPS_128 = 3_200_000      # 200 secondi a 128 kbit/s
KBPS_320 = 8_000_000      # 200 secondi a 320 kbit/s


def _phone(pid, title, album, size=KBPS_320, suffix=".mp3", artist="Gruppo Finto", length=200.0, sync_id=None,
           playlists=(), **values):
    values.setdefault("year", "1999")
    values.setdefault("genre", "Pop")
    values.setdefault("track_number", 1)
    tags = TrackTags(title=title, artist=artist, album=album, **values)
    result = PhoneTrack(pid=pid, remote_path=f"/iTunes_Control/Music/F01/{pid}{suffix}", size=size, length=length,
                        tags=tags, sync_id=pid + 100 if sync_id is None else sync_id, playlists=tuple(playlists))
    return result


def _pc(title, album, folder="C:/musica/Disco", artist="Gruppo Finto"):
    result = Track(path=Path(f"{folder}/{title}.mp3"), tags=TrackTags(title=title, artist=artist, album=album),
                   length=200.0)
    return result


def test_album_key_joins_the_spellings_of_one_album():
    key = phone_duplicates.album_key
    assert key("The Wall CD1") == key("The Wall (Disc 1)") == key("the wall") == "the wall"
    assert key("Raccolta (Cd3) {]-Gruppo-[}") == key("Raccolta")
    assert key("Raccolta") != key("Raccolta Due")


def test_same_album_is_a_duplicate_other_albums_are_not():
    phone = [_phone(1, "Uno", "Disco CD1"), _phone(2, "Uno", "Disco (Disc 1)", length=203.0),
             _phone(3, "Uno", "Raccolta"), _phone(4, "Due", "Disco CD1"), _phone(5, "Uno", "Disco", length=260.0)]
    found = phone_duplicates.find(phone, {}, {})
    assert len(found.sets) == 1 and sorted(item.pid for item in found.sets[0].copies) == [1, 2]
    assert sorted(item.pid for item in found.other_albums[3]) == [1, 2]     # la raccolta: legittima
    assert 4 not in found.set_of and 5 not in found.set_of                   # altro titolo, altra durata


def test_different_files_of_one_folder_are_different_songs_with_a_wrong_title():
    """Un album con i titoli sbagliati: due file diversi della stessa cartella con lo stesso titolo non sono un
    doppione; lo stesso file mandato due volte sì."""
    phone = [_phone(1, "Uno", "Disco"), _phone(2, "Uno", "Disco", length=201.0), _phone(3, "Uno", "Disco")]
    sources = {1: "C:/musica/Disco/01.mp3", 2: "C:/musica/Disco/02.mp3", 3: "C:/musica/Disco/01.mp3"}
    found = phone_duplicates.find(phone, sources, {})
    assert len(found.sets) == 1 and sorted(item.pid for item in found.sets[0].copies) == [1, 3]
    assert found.suspect == {1, 2, 3}          # lo stesso titolo su canzoni diverse dell'album


def test_the_copy_to_keep_correct_tags_first_then_quality():
    stale = _phone(1, "Uno", "Disco", size=KBPS_320)                      # tag diversi dal file del PC
    low = _phone(2, "Uno", "Disco", size=KBPS_128)
    found = phone_duplicates.find([stale, low], {}, {1: False, 2: True})
    assert found.sets[0].best.pid == 2
    assert found.sets[0].reasons[1] == "Da togliere: tag sbagliati (tag diversi dal file del PC)"

    found = phone_duplicates.find([_phone(1, "Uno", "Disco", size=KBPS_128), _phone(2, "Uno", "Disco")], {}, {})
    assert found.sets[0].best.pid == 2
    assert found.sets[0].reasons[1] == ("Da togliere: qualità più bassa (MP3 ~128 kbit/s contro MP3 ~320 "
                                        "kbit/s)")
    assert found.sets[0].reasons[2] == "Da tenere: MP3 ~320 kbit/s"

    # FLAC e MP3 a 320 valgono uguale: decidono i tag completi, poi le playlist; a parità di tutto l'MP3 a 320
    flac = _phone(1, "Uno", "Disco", size=30_000_000, suffix=".flac")
    mp3 = _phone(2, "Uno", "Disco", year="")
    assert phone_duplicates.find([flac, mp3], {}, {}).sets[0].best.pid == 1
    flac_listed = _phone(1, "Uno", "Disco", size=30_000_000, suffix=".flac", playlists=["Preferite"])
    found = phone_duplicates.find([flac_listed, _phone(2, "Uno", "Disco")], {}, {})
    assert found.sets[0].best.pid == 1 and found.sets[0].reasons[2] == "Da togliere: l'altra copia è in più playlist"
    found = phone_duplicates.find([flac, _phone(2, "Uno", "Disco")], {}, {})
    assert found.sets[0].best.pid == 2
    assert found.sets[0].reasons[1] == "Da togliere: a parità di tutto si preferisce MP3 ~320 kbit/s al FLAC"
    # sotto i 320 vince il FLAC
    found = phone_duplicates.find([flac, _phone(2, "Uno", "Disco", size=6_400_000)], {}, {})
    assert found.sets[0].best.pid == 1 and "qualità più bassa (MP3 ~256 kbit/s contro FLAC)" in found.sets[0].reasons[2]
    # due MP3 a 320 quasi uguali: il file più piccolo
    found = phone_duplicates.find([_phone(1, "Uno", "Disco", size=9_000_000), _phone(2, "Uno", "Disco")], {}, {})
    assert found.sets[0].best.pid == 2 and "file più grande" in found.sets[0].reasons[1]

    # nome dell'album con aggiunte tra graffe: tag sbagliati
    found = phone_duplicates.find([_phone(1, "Uno", "Disco {]-Gruppo-[}"), _phone(2, "Uno", "Disco")], {}, {})
    assert found.sets[0].best.pid == 2


def test_copies_to_remove_and_keep_this_one():
    phone = [_phone(1, "Uno", "Disco", size=KBPS_128), _phone(2, "Uno", "Disco"),
             _phone(3, "Uno", "Disco", size=KBPS_128, sync_id=0)]          # acquistata sul telefono
    found = phone_duplicates.find(phone, {}, {})
    assert found.sets[0].best.pid == 2
    assert [item.pid for item in found.to_remove([phone[0]])] == [1]      # la 3 il computer non la può togliere
    assert "un computer non la può togliere" in found.sets[0].reasons[3]
    assert [item.pid for item in found.others_of(phone[0])] == [2]        # tieni la 1: via la 2


def test_a_send_already_in_the_same_album_replaces_the_old_copy():
    phone = [_phone(1, "Uno", "Disco CD1", playlists=["Preferite"]), _phone(2, "Uno", "Disco"),
             _phone(3, "Due", "Raccolta"), _phone(4, "Tre", "Disco", sync_id=0),
             _phone(5, "Titolo vecchio", "Disco"), _phone(6, "Sei", "Disco")]
    sources = {5: "C:/musica/Disco/Cinque.mp3"}
    uno = _pc("Uno", "Disco")
    due = _pc("Due", "Disco")                     # sull'iPhone è in un altro album: si aggiunge
    tre = _pc("Tre", "Disco")                     # c'è, ma acquistato sul telefono
    cinque = _pc("Cinque", "Disco")               # lo stesso file già mandato, con un altro titolo
    sei = _pc("Sei", "Disco")                     # ha già un'azione in coda: non si tocca
    plan = phone_duplicates.send_plan([uno, due, tre, cinque, sei], phone, sources, busy={6})
    assert [(item.pid, track.tags.title) for item, track in plan.replaces] == [(1, "Uno"), (5, "Cinque")]
    assert [item.pid for item in plan.removes] == [2]                    # l'altra copia dello stesso album
    assert [track.tags.title for track in plan.sends] == ["Due", "Tre", "Sei"]
    assert [(track.tags.title, item.pid) for track, item in plan.kept_old] == [("Tre", 4)]


def test_panel_filters_buttons_and_send_replacement(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui import iphone_panel
    from myeasymp3toiphone.gui.main_window import MainWindow
    from myeasymp3toiphone.pending import DELETE, SEND, Job, file_key
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        window.tracks = []
        phone = [_phone(1, "Uno", "Disco", size=KBPS_128), _phone(2, "Uno", "Disco CD1"),
                 _phone(3, "Uno", "Raccolta"), _phone(4, "Due", "Disco")]
        window.set_phone_tracks(phone, "iPhone di prova")
        app.processEvents()
        panel = window.iphone_panel
        texts = [text for text, _rule in iphone_panel.SHOW_FILTERS]
        counts = dict(zip(texts, panel._show._counts))
        assert counts[iphone_panel.DUPLICATES_TEXT] == 2
        assert "Stessa canzone in più album (raccolte)" not in counts       # legittime: nessun filtro
        assert panel._actions.button("dedupe").isHidden()
        panel._show.setCurrentIndex(iphone_panel.DUPLICATES_FILTER)
        assert panel._count.text() == "2 di 4 brani"
        assert 1 in panel._marked and 2 in panel._marked
        assert "qualità più bassa" in panel._duplicate_note(phone[0])
        assert "La stessa canzone anche in: Raccolta" in panel._duplicate_note(phone[1])
        entries = panel.duplicate_entries([phone[1]])
        assert entries["keep"][0] == "Tieni questa copia, togli le altre (Elimina dall'iPhone): 1 brano"
        button = panel._actions.button("dedupe")
        assert not button.isHidden()
        assert button.text() == ("Togli le copie in più (Elimina dall'iPhone): 1 brano; resta la migliore di ogni "
                                 "canzone")
        button.click()
        assert window.pending.get_phone(1) == DELETE and window.pending.get_phone(2) == ""
        panel._show.setCurrentIndex(0)
        assert panel._marked == set()                       # senza il filtro le righe tornano normali

        file = tmp_path / "Due.mp3"
        write_mp3(file)
        track = Track(path=file, tags=TrackTags(title="Due", artist="Gruppo Finto", album="Disco"), length=200.0)
        jobs = [Job(key=file_key(file), action=SEND, track=track)]
        assert "sostituiscono la copia vecchia" in panel.jobs_notes(jobs)
        captured = {}

        def run_jobs(jobs, sends, removes, updates, replaces, edits, closing, then):
            captured.update(jobs=jobs, sends=sends, replaces=replaces)

        panel._run_jobs = run_jobs
        panel._connected = True
        panel.apply_jobs(jobs)
        assert captured["sends"] == [] and captured["replaces"] == [(phone[3], track)]
        assert captured["jobs"] == jobs                     # la Copia resta nella coda finché non è fatta
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()
