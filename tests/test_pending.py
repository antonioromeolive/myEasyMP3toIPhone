# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le modifiche all'iPhone in attesa (passo 5): spunte, azioni, riconciliazione, salvataggio. Valori inventati."""

from pathlib import Path

from myeasymp3toiphone.library import Track
from myeasymp3toiphone.pending import REMOVE, SEND, UPDATE, Pending, still_needed, toggled, wanted
from myeasymp3toiphone.phone_library import DEVICE_ABSENT, DEVICE_SAME, DEVICE_STALE
from myeasymp3toiphone.tags import TrackTags


def test_toggle_rules():
    assert toggled(DEVICE_ABSENT, False, "", True) == SEND
    assert toggled(DEVICE_ABSENT, False, SEND, False) == ""              # annulla l'invio
    assert toggled(DEVICE_SAME, True, "", False) == REMOVE                # collegato: si toglie
    assert toggled(DEVICE_SAME, False, "", False) == ""                   # solo per i tag: mai
    assert toggled(DEVICE_STALE, False, UPDATE, False) == UPDATE
    assert toggled(DEVICE_SAME, True, REMOVE, True) == ""                 # annulla il "togli"
    assert toggled(DEVICE_STALE, True, UPDATE, True) == UPDATE
    assert wanted(DEVICE_ABSENT, SEND) and not wanted(DEVICE_SAME, REMOVE) and wanted(DEVICE_STALE, "")
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
    assert again.counts() == {SEND: 1, REMOVE: 1, UPDATE: 1} and again.get(tracks[0].path) == SEND
    statuses = {"a": DEVICE_SAME, "b": DEVICE_SAME, "c": DEVICE_ABSENT}   # "a" inviato; "b" non ancora tolto
    assert again.reconcile(tracks, lambda track: statuses[track.tags.title]) == 1
    assert again.get(tracks[0].path) == "" and again.get(tracks[1].path) == REMOVE
    assert again.get(Path("D:/altro/x.mp3")) == UPDATE
    (tmp_path / "iphone_in_attesa.json").write_text("non json", encoding="utf-8")
    assert Pending(tmp_path).counts() == {SEND: 0, REMOVE: 0, UPDATE: 0}
