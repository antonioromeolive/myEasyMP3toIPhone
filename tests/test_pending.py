# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le azioni sull'iPhone in attesa: spunte, voci per file e per brano dell'iPhone, riconciliazione, salvataggio, il
formato vecchio. Valori inventati."""

import json
from pathlib import Path

from myeasymp3toiphone.library import Track
from myeasymp3toiphone.pending import (
    DELETE, EDIT, PENDING_FILE, REMOVE, REPLACE, SEND, UPDATE, Pending, edit_needed, phone_key, still_needed, toggled,
    wanted,
)
from myeasymp3toiphone.phone_library import DEVICE_ABSENT, DEVICE_SAME, DEVICE_STALE
from myeasymp3toiphone.tags import TrackTags


class _Phone:
    def __init__(self, pid, **tags):
        self.pid = pid
        self.tags = TrackTags(**tags)


def test_toggle_rules():
    assert toggled(DEVICE_ABSENT, False, "", True) == SEND
    assert toggled(DEVICE_ABSENT, False, SEND, False) == ""              # annulla l'invio
    assert toggled(DEVICE_SAME, True, "", False) == REMOVE                # collegato: si toglie
    assert toggled(DEVICE_SAME, False, "", False) == ""                   # solo per i tag: mai
    assert toggled(DEVICE_STALE, False, UPDATE, False) == UPDATE
    assert toggled(DEVICE_SAME, True, REMOVE, True) == ""                 # annulla il "togli"
    assert toggled(DEVICE_STALE, True, UPDATE, True) == UPDATE
    assert toggled(DEVICE_STALE, True, REPLACE, True) == REPLACE          # Ricopia resta
    assert wanted(DEVICE_ABSENT, SEND) and not wanted(DEVICE_SAME, REMOVE) and wanted(DEVICE_STALE, "")
    assert not wanted(DEVICE_SAME, DELETE) and wanted(DEVICE_SAME, REPLACE)
    assert not still_needed(DEVICE_SAME, SEND) and still_needed(DEVICE_SAME, REMOVE)
    assert not still_needed(DEVICE_SAME, UPDATE) and still_needed(DEVICE_STALE, UPDATE)


def test_saved_and_reconciled(tmp_path):
    tracks = [Track(path=Path(f"C:/musica/{name}.mp3"), tags=TrackTags(title=name)) for name in ("a", "b", "c")]
    pending = Pending(tmp_path)
    pending.set(tracks[0].path, SEND)
    pending.set(tracks[1].path, REMOVE)
    pending.set(Path("D:/altro/x.mp3"), UPDATE)                          # non nella cartella aperta
    pending.save()
    again = Pending(tmp_path)
    counts = again.counts()
    assert (counts[SEND], counts[REMOVE], counts[UPDATE], again.total()) == (1, 1, 1, 3)
    assert again.get(tracks[0].path) == SEND
    statuses = {"a": DEVICE_SAME, "b": DEVICE_SAME, "c": DEVICE_ABSENT}   # "a" inviato; "b" non ancora tolto
    assert again.reconcile(tracks, lambda track: statuses[track.tags.title]) == 1
    assert again.get(tracks[0].path) == "" and again.get(tracks[1].path) == REMOVE
    assert again.get(Path("D:/altro/x.mp3")) == UPDATE
    (tmp_path / PENDING_FILE).write_text("non json", encoding="utf-8")
    assert Pending(tmp_path).total() == 0


def test_old_format_is_read(tmp_path):
    old = {"version": 1, "items": {"c:\\musica\\a.mp3": SEND, "c:\\musica\\b.mp3": "boh"}}
    (tmp_path / PENDING_FILE).write_text(json.dumps(old), encoding="utf-8")
    pending = Pending(tmp_path)
    assert pending.total() == 1 and pending.get(Path("C:/musica/a.mp3")) == SEND


def test_phone_entries_one_action_per_song(tmp_path):
    pending = Pending(tmp_path)
    song = Path("C:/musica/a.mp3")
    pending.set(song, UPDATE)                                             # dalla scheda PC
    pending.set_phone(7, REPLACE, song)                                   # dalla scheda iPhone: prende il posto
    assert pending.total() == 1 and pending.get(song) == REPLACE and pending.get_phone(7) == REPLACE
    pending.set(song, SEND)                                               # di nuovo per file: la voce iPhone va via
    assert pending.get_phone(7) == "" and pending.get(song) == SEND
    pending.set_phone(8, EDIT, values={"genre": "Rock"})
    pending.set_phone(8, EDIT, values={"year": 1999})                    # i valori si sommano
    assert pending.items[phone_key(8)]["values"] == {"genre": "Rock", "year": 1999}
    assert pending.get_phone(8) == "" and pending.get_phone(8, include_edit=True) == EDIT
    pending.set_phone(9, DELETE)
    pending.save()
    again = Pending(tmp_path)
    assert again.entries() == pending.entries()
    assert again.remove([phone_key(9), "pid:inesistente"]) == 1 and again.total() == 2


def test_phone_entries_reconciled(tmp_path):
    pending = Pending(tmp_path)
    pending.set_phone(1, DELETE)                                          # c'è ancora: resta
    pending.set_phone(2, DELETE)                                          # non c'è più: fatto
    pending.set_phone(3, EDIT, values={"genre": "Rock", "year": 2001})   # già così: fatto
    pending.set_phone(4, EDIT, values={"genre": "Jazz"})                 # ancora diverso: resta
    pending.set_phone(5, UPDATE, Path("C:/musica/e.mp3"))                 # update_needed decide
    phone = [_Phone(1), _Phone(3, genre="Rock", year="2001"), _Phone(4, genre="Pop"), _Phone(5)]
    assert edit_needed(phone[2], {"genre": "Jazz"}) and not edit_needed(phone[1], {"year": 2001})
    assert pending.reconcile_phone(phone, lambda item, path: False) == 3
    assert sorted(pending.items) == [phone_key(1), phone_key(4)]
