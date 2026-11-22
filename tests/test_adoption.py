# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""L'adozione dei brani già sull'iPhone: impronta, regole, AI. Impronte e AI finte, nessun iPhone. Valori inventati."""

import threading
from pathlib import Path

from myeasymp3toiphone import adoption, provenance
from myeasymp3toiphone.library import Track
from myeasymp3toiphone.phone_library import PhoneTrack
from myeasymp3toiphone.provenance import Link, Registry
from myeasymp3toiphone.tags import TrackTags


def _phone(sync_id, title, artist, album, length=200.0, album_artist="", from_computer=True):
    tags = TrackTags(title=title, artist=artist, album=album, album_artist=album_artist)
    result = PhoneTrack(pid=sync_id, remote_path=f"/iTunes_Control/Music/F01/{sync_id}.mp3", size=1, length=length,
                        tags=tags, sync_id=sync_id if from_computer else 0)
    return result


def _pc(path, title, artist, album, length=200.0, album_artist=""):
    result = Track(path=Path(path), tags=TrackTags(title=title, artist=artist, album=album, album_artist=album_artist),
                   length=length)
    return result


class FakeProvider:
    """Un'AI finta: per ogni brano sceglie il candidato nella cartella indicata (o nessuno)."""

    def __init__(self, folder, confidence):
        self.folder = folder
        self.confidence = confidence
        self.seen = ""
        self.profile = type("P", (), {"name": "finta"})()

    def ask_json(self, system, user, schema):
        self.seen += user
        matches = []
        for line in user.splitlines():
            if line.strip().startswith("T") and ".C" in line.split("|")[0] and f"folder: {self.folder}" in line:
                candidate = line.split("|")[0].strip()
                matches.append({"track": candidate.split(".")[0], "candidate": candidate,
                                 "confidence": self.confidence, "reason": "scelta finta"})
        return {"matches": matches}


def _run(monkeypatch, phone, pc, phone_prints, pc_prints, registry=None, provider=None, cancel=None):
    monkeypatch.setattr(adoption, "phone_fingerprints", lambda tracks, home, progress, cancel: dict(phone_prints))
    monkeypatch.setattr(adoption, "pc_fingerprints", lambda tracks, cache, progress, cancel: dict(pc_prints))
    result = adoption.adopt(phone, pc, registry or Registry(), Path("."), None, provider, None, cancel)
    return result


def test_fingerprint_finds_compilation_tracks_and_closest_copy(monkeypatch):
    phone = [_phone(1, "Canzone", "Cantante", "Hits 2005", album_artist="Artisti Vari"),
             _phone(2, "Altra", "Altro", "Album")]
    pc = [_pc("C:/m/Cantante/Album vero/01 - Canzone.mp3", "Canzone (remaster)", "Cantante", "Album vero"),
          _pc("C:/m/Raccolte/Hits 2005/05 - Canzone.mp3", "Canzone", "Cantante", "Hits 2005",
              album_artist="Artisti vari"),
          _pc("C:/m/Altro/Album/01 - Altra.mp3", "Titolo sbagliato", "Nessuno", "Niente")]
    outcome = _run(monkeypatch, phone, pc, {1: "mp3:a", 2: "mp3:b"},
                   {str(pc[0].path): "mp3:a", str(pc[1].path): "mp3:a", str(pc[2].path): "mp3:b"})
    links = {p.phone.sync_id: p for p in outcome.certain}
    assert links[1].pc is pc[1] and "2 copie" in links[1].reason        # la copia con i tag uguali
    assert links[2].pc is pc[2] and links[2].how == provenance.HOW_FINGERPRINT   # tag tutti diversi, stesso audio
    assert outcome.proposals == [] and outcome.foreign == []


def test_rules_ai_foreign_and_known(monkeypatch):
    phone = [_phone(1, "Estate", "Bruno", "Live 1990", length=180.0),           # regole
             _phone(2, "Notte", "Carla", "Raccolta", length=240.0),              # dubbio: due versioni
             _phone(3, "Mai sentita", "Nessuno", "Boh", length=99.0),            # estraneo
             _phone(4, "Nota", "Dario", "Album", length=150.0),                  # già nel registro
             _phone(5, "Comprata", "Ezio", "Store", from_computer=False)]
    pc = [_pc("C:/m/Bruno/Estate/01 - Estate.mp3", "Estate", "Bruno", "Estate", length=181.0),
          _pc("C:/m/Carla/Notte/01 - Notte.mp3", "Notte", "Carla", "Notte", length=239.5),
          _pc("C:/m/Carla/Live/07 - Notte (live).mp3", "Notte (live)", "Carla", "Live", length=241.0)]
    registry = Registry()
    registry.record(Link(sync_id=4, pc="PC", path="C:/m/x.mp3"))
    provider = FakeProvider("Carla/Notte", "high")
    outcome = _run(monkeypatch, phone, pc, {1: "mp3:x", 2: "mp3:y", 3: "mp3:z"}, {}, registry, provider)
    by_id = {p.phone.sync_id: p for p in outcome.proposals}
    assert by_id[1].how == provenance.HOW_RULES and by_id[1].checked and by_id[1].pc is pc[0]
    assert by_id[2].how == provenance.HOW_AI and by_id[2].checked and by_id[2].pc is pc[1]
    assert "folder: Carla/Live" in provider.seen and "T1.C2" in provider.seen     # il contesto della cartella
    assert "(live)" in provider.seen          # "Notte" e "Notte (live)" sembrano uguali alle regole: decide l'AI
    assert [t.sync_id for t in outcome.foreign] == [3]
    assert (outcome.already, outcome.not_from_computer) == (1, 1)


def test_doubtful_without_ai_or_with_unsure_ai_is_unchecked(monkeypatch):
    phone = [_phone(2, "Notte", "Carla", "Raccolta", length=240.0)]
    pc = [_pc("C:/m/x/a.mp3", "Notte", "Carla", "Notte", length=239.5),
          _pc("C:/m/y/b.mp3", "Notte (live)", "Carla", "Live", length=241.0)]
    without = _run(monkeypatch, phone, pc, {}, {})
    assert len(without.proposals) == 1 and not without.proposals[0].checked
    unsure = _run(monkeypatch, phone, pc, {}, {}, provider=FakeProvider("m/y", "low"))
    assert unsure.proposals[0].how == provenance.HOW_AI and unsure.proposals[0].pc is pc[1]
    assert not unsure.proposals[0].checked                 # l'AI non è sicura: da controllare


def test_cancelled_adoption_proposes_nothing(monkeypatch):
    cancel = threading.Event()
    cancel.set()
    phone = [_phone(1, "Estate", "Bruno", "Live")]
    pc = [_pc("C:/m/a.mp3", "Estate", "Bruno", "Estate")]
    outcome = _run(monkeypatch, phone, pc, {}, {}, cancel=cancel)
    assert outcome.cancelled and outcome.certain == [] and outcome.proposals == [] and outcome.foreign == []


def test_link_for_records_how_and_file(tmp_path):
    path = tmp_path / "a.mp3"
    path.write_bytes(b"x" * 10)
    proposal = adoption.Proposal(_phone(7, "T", "A", "B"), _pc(path, "T", "A", "B"), provenance.HOW_AI, "motivo")
    link = adoption.link_for(proposal, None, "mp3:abc")
    assert (link.sync_id, link.path, link.size, link.how, link.fingerprint) == (7, str(path), 10, "ai", "mp3:abc")
    assert link.here
