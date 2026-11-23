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


# --------------------------------------------------------------------------- Associa sorgente

def _fake_prints(monkeypatch, phone_print, pc_prints):
    monkeypatch.setattr(adoption, "_phone_print", lambda track, home, read_phone, cancel=None: phone_print)
    monkeypatch.setattr(adoption, "pc_fingerprints", lambda tracks, cache, progress=None, cancel=None: dict(pc_prints))


def test_rank_sources_fingerprint_first_without_title_filter(monkeypatch):
    phone = _phone(1, "Canzone", "Cantante", "Hits 2005", album_artist="Artisti Vari")
    pc = [_pc("C:/m/Cantante/Album/01 - Canzone.mp3", "Canzone", "Cantante", "Album"),
          _pc("C:/m/Raccolte/Hits/05 - Traccia 05.mp3", "Traccia 05", "", "Hits", length=201.5),
          _pc("C:/m/Lontano/01 - Canzone.mp3", "Canzone", "Cantante", "Altro", length=260.0)]
    _fake_prints(monkeypatch, "mp3:x", {str(pc[1].path): "mp3:x", str(pc[0].path): "mp3:y"})
    ranked = adoption.rank_sources(phone, pc, Path("."))
    assert ranked[0].pc is pc[1] and ranked[0].how == provenance.HOW_FINGERPRINT      # titolo diverso, stesso audio
    assert ranked[1].pc is pc[0] and ranked[1].how == provenance.HOW_RULES
    assert all(proposal.pc is not pc[2] for proposal in ranked)                         # durata troppo diversa


def test_rank_sources_asks_ai_only_when_close(monkeypatch):
    phone = _phone(2, "Notte", "Carla", "Raccolta", length=240.0)
    pc = [_pc("C:/m/Carla/Notte/01 - Notte.mp3", "Notte", "Carla", "Notte", length=239.5),
          _pc("C:/m/Carla/Live/07 - Notte.mp3", "Notte", "Carla", "Live", length=241.0)]
    _fake_prints(monkeypatch, "", {})
    provider = FakeProvider("Carla/Live", "medium")
    ranked = adoption.rank_sources(phone, pc, Path("."), provider=provider)
    assert ranked[0].pc is pc[1] and ranked[0].how == provenance.HOW_AI
    assert ranked[0].reason == "AI (media): scelta finta"                               # la sicurezza in italiano
    assert [proposal.pc for proposal in ranked[1:]] == [pc[0]]
    clear = _phone(3, "Estate", "Bruno", "Estate", length=180.0)
    silent = FakeProvider("Bruno", "high")
    ranked = adoption.rank_sources(clear, [_pc("C:/m/Bruno/01 - Estate.mp3", "Estate", "Bruno", "Estate", 181.0)],
                                   Path("."), provider=silent)
    assert ranked[0].how == provenance.HOW_RULES and silent.seen == ""                 # un solo candidato sicuro


class StuckProvider(FakeProvider):
    """Un'AI che non risponde finché il test non la libera (un server lento o bloccato)."""

    def __init__(self):
        super().__init__("", "high")
        self.release = threading.Event()

    def ask_json(self, system, user, schema):
        self.release.wait(30)
        result = super().ask_json(system, user, schema)
        return result


def test_rank_sources_cancel_does_not_wait_for_the_ai(monkeypatch):
    phone = _phone(2, "Notte", "Carla", "Raccolta", length=240.0)
    pc = [_pc("C:/m/Carla/Notte/01 - Notte.mp3", "Notte", "Carla", "Notte", length=239.5),
          _pc("C:/m/Carla/Live/07 - Notte.mp3", "Notte", "Carla", "Live", length=241.0)]
    _fake_prints(monkeypatch, "", {})
    provider = StuckProvider()
    cancel = threading.Event()
    timer = threading.Timer(0.3, cancel.set)
    timer.start()
    try:
        ranked = adoption.rank_sources(phone, pc, Path("."), provider=provider, cancel=cancel)
        assert ranked is None and not provider.release.is_set()      # annullato mentre l'AI non rispondeva ancora
    finally:
        provider.release.set()
        timer.cancel()


def _numbered(sync_id, title, album, number, length):
    item = _phone(sync_id, title, "Anna", album, length=length)
    item.tags.track_number = number
    return item


def _numbered_pc(path, title, number, length):
    track = _pc(path, title, "Anna", "", length=length)
    track.tags.track_number = number
    return track


def test_folder_name_first_then_fingerprint_only_for_the_rest(monkeypatch):
    """Il nome della cartella contiene l'album: con titolo, numero e durata uguali basta (niente impronta); senza
    il numero è probabile e l'impronta, se c'è, lo rende certo; un titolo solo simile resta da controllare."""
    phone = [_numbered(1, "Uno", "Il Disco Bello", 1, 100.0),
             _numbered(2, "Due", "Il Disco Bello", None, 120.0),
             _numbered(3, "Tre!", "Il Disco Bello", 3, 140.0),
             _numbered(4, "Quattro", "Altro album", 4, 160.0)]
    pc = [_numbered_pc("C:/m/Anna - Il disco bello (1999)/CD1/01 Uno.mp3", "Uno", 1, 100.4),
          _numbered_pc("C:/m/Anna - Il disco bello (1999)/CD1/02 Due.mp3", "Due", 2, 120.2),
          _numbered_pc("C:/m/Anna - Il disco bello (1999)/CD1/03 Tre.mp3", "Tree", 3, 139.0),
          _numbered_pc("C:/m/Varie/x.mp3", "Quattro", 4, 160.0)]
    asked = []

    def phone_prints(tracks, home, progress, cancel):
        asked.extend(item.sync_id for item in tracks)
        return {2: "mp3:due"}

    monkeypatch.setattr(adoption, "phone_fingerprints", phone_prints)
    monkeypatch.setattr(adoption, "pc_fingerprints", lambda tracks, cache, progress, cancel:
                        {str(pc[1].path): "mp3:due"})
    outcome = adoption.adopt(phone, pc, Registry(), Path("."), None, None, None, None)
    assert sorted(asked) == [2, 3, 4]                       # il brano 1 non ha bisogno dell'impronta
    by_id = {p.phone.sync_id: p for p in outcome.proposals + outcome.certain}
    assert by_id[1].how == provenance.HOW_FOLDER and by_id[1].level == adoption.LEVEL_VERY_LIKELY
    assert by_id[1].checked and by_id[1].pc is pc[0]
    assert by_id[2].how == provenance.HOW_FINGERPRINT and by_id[2].level == adoption.LEVEL_CERTAIN
    assert by_id[3].how == provenance.HOW_FOLDER and not by_id[3].checked
    assert by_id[4].how == provenance.HOW_RULES and by_id[4].pc is pc[3]    # nessuna cartella: le regole
    assert outcome.by_folder == 2


def test_without_fingerprint_or_phone_only_folder_and_rules(monkeypatch, tmp_path):
    phone = [_numbered(2, "Due", "Il Disco Bello", None, 120.0)]
    pc = [_numbered_pc("C:/m/Il Disco Bello/02 Due.mp3", "Due", 2, 120.2)]

    def never(*args):
        raise AssertionError("l'iPhone non si legge")

    monkeypatch.setattr(adoption, "phone_fingerprints", never)
    monkeypatch.setattr(adoption, "pc_fingerprints", never)
    outcome = adoption.adopt(phone, pc, Registry(), tmp_path, use_fingerprint=False)
    assert outcome.proposals[0].level == adoption.LEVEL_LIKELY and outcome.proposals[0].checked
    monkeypatch.setattr(adoption, "pc_fingerprints", lambda tracks, cache, progress, cancel: {})
    known = adoption.adopt(phone, pc, Registry(), tmp_path, read_phone=False)  # solo le impronte ricordate
    assert known.proposals[0].how == provenance.HOW_FOLDER


def test_replace_known_includes_tracks_with_a_source(monkeypatch):
    phone = [_phone(4, "Nota", "Dario", "Album", length=150.0)]
    pc = [_pc("C:/m/Dario/Album/01 - Nota.mp3", "Nota", "Dario", "Album", length=150.0)]
    registry = Registry()
    registry.record(Link(sync_id=4, pc="PC", path="C:/m/x.mp3"))
    monkeypatch.setattr(adoption, "phone_fingerprints", lambda tracks, home, progress, cancel: {})
    monkeypatch.setattr(adoption, "pc_fingerprints", lambda tracks, cache, progress, cancel: {})
    assert adoption.adopt(phone, pc, registry, Path(".")).already == 1
    assert len(adoption.adopt(phone, pc, registry, Path("."), replace_known=True).proposals) == 1


def test_adoption_dialogs(tmp_path):
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui.adoption_dialog import AdoptionDialog, AdoptOptionsDialog
    app = QApplication.instance() or QApplication([])
    options = AdoptOptionsDialog(None, 40, 3, tmp_path, tmp_path / "Libreria", 10, False, "")
    assert options.selected_only and options.use_fingerprint and not options.use_ai
    assert options.folder() == tmp_path
    options.library_box.setChecked(True)
    assert options.folder() == tmp_path / "Libreria" and not options.folder_edit.isEnabled()
    outcome = adoption.AdoptionResult()
    sure = adoption.Proposal(_phone(1, "Uno", "A", "B"), _pc("C:/m/1.mp3", "Uno", "A", "B"),
                             provenance.HOW_FINGERPRINT, "stesso audio", level=adoption.LEVEL_CERTAIN)
    doubt = adoption.Proposal(_phone(2, "Due", "A", "B"), _pc("C:/m/2.mp3", "Due", "A", "B"), provenance.HOW_RULES,
                              "controlla", checked=False, level=adoption.LEVEL_CHECK)
    outcome.certain = [sure]
    outcome.proposals = [doubt]
    outcome.foreign = [_phone(3, "Tre", "A", "B")]
    dialog = AdoptionDialog(None, outcome)
    assert dialog.chosen() == [sure]                     # quella da controllare non è spuntata
    dialog._rows[0][0].setCheckState(0, Qt.Unchecked)    # anche una certa si può togliere: resta com'è
    assert dialog.chosen() == []
    assert [item.sync_id for item in dialog.missing] == [3] and not dialog.one_by_one
    dialog.one_by_one_box.setChecked(True)
    assert dialog.one_by_one
    dialog.close()
    options.close()
    app.processEvents()


def test_album_folder_matches_needs_one_folder_for_the_whole_album():
    """La sorgente proposta: tutti i brani dell'album dell'iPhone nella stessa cartella del PC, stesso titolo e
    durata; un album sparso in più cartelle non ha proposte."""
    phone = [_numbered(1, "Uno", "Disco Primo", 1, 100.0), _numbered(2, "Due (remaster)", "Disco Primo", 2, 120.0),
             _numbered(3, "Tre", "Sparso", 1, 140.0), _numbered(4, "Quattro", "Sparso", 2, 160.0),
             _numbered(5, "Cinque", "Doppio", 1, 180.0)]
    pc = [_numbered_pc("C:/m/Anna/Disco Primo/01 Uno.mp3", "Uno", 1, 100.5),
          _numbered_pc("C:/m/Anna/Disco Primo/02 - Due.mp3", "", 2, 119.0),          # titolo solo nel nome del file
          _numbered_pc("C:/m/Raccolta/01 Uno.mp3", "Uno", 7, 100.0),                 # l'altro brano non c'è
          _numbered_pc("C:/m/A/Tre.mp3", "Tre", 1, 140.0),
          _numbered_pc("C:/m/B/Quattro.mp3", "Quattro", 2, 160.0),
          _numbered_pc("C:/m/C/Cinque.mp3", "Cinque", 1, 250.0)]                     # durata diversa
    matches = adoption.album_folder_matches(phone, pc)
    assert matches == {1: pc[0], 2: pc[1]}


def test_album_folder_matches_album_on_several_disc_folders():
    """Un album su più dischi, una cartella per disco ("cd 1 - studio", "cd 2 - live") e i numeri che ricominciano:
    la cartella dell'album è quella sopra; una seconda copia più lontana non vince."""
    phone = []
    pc = []
    copy = []
    songs = [(1, 1, "Prima", 200.0), (1, 2, "Seconda", 210.0), (2, 1, "Terza", 220.0), (2, 2, "Prima", 300.0)]
    for index, (disc, number, title, length) in enumerate(songs):
        item = _numbered(index + 1, title, "Tutto Questo", number, length)
        item.tags.disc_number = disc
        phone.append(item)
        folder = "cd 1 - studio" if disc == 1 else "cd 2 - live"
        track = _numbered_pc(f"C:/m/Anna/Tutto Questo/{folder}/{number:02d} - {title}.mp3", title, number, length)
        track.tags.disc_number = disc
        pc.append(track)
        copy.append(_numbered_pc(f"C:/copia/vecchi/Anna/Tutto Questo/{folder}/{number:02d} - {title}.mp3",
                                 title, number, length))
    matches = adoption.album_folder_matches(phone, copy + pc)
    assert matches == {1: pc[0], 2: pc[1], 3: pc[2], 4: pc[3]}        # il percorso più corto, disco per disco
    from myeasymp3toiphone.library import album_folder
    assert album_folder("C:/m/A/Disco/CD2/01.mp3") == str(Path("C:/m/A/Disco"))
    assert album_folder("C:/m/A/Disco/Cdrom/01.mp3") == str(Path("C:/m/A/Disco/Cdrom"))


# --------------------------------------------------------------------------- cartelle preferite

PREFERRED = ("musica.buona", "musica.flac", "C:/raccolte")


def test_preference_order_names_and_paths():
    from myeasymp3toiphone.library import preference
    assert preference("D:/x/Musica.Buona/Anna/01.mp3", PREFERRED) == 0           # nome, maiuscole a parte
    assert preference("D:/x/musica.flac/Anna/01.flac", PREFERRED) == 1
    assert preference("C:/Raccolte/Estate/01.mp3", PREFERRED) == 2               # percorso, con le sottocartelle
    assert preference("C:/raccolte2/Estate/01.mp3", PREFERRED) == 3              # un altro nome: in nessuna
    assert preference("D:/x/musica.buona.vecchia/01.mp3", PREFERRED) == 3        # il nome intero, non un pezzo
    assert preference("D:/x/a.mp3", ()) == 0


def test_preferred_copy_wins_everywhere():
    phone = [_numbered(1, "Uno", "Disco", 1, 100.0), _numbered(2, "Due", "Disco", 2, 120.0)]
    near = [_numbered_pc("C:/m/Anna/Disco/01 Uno.mp3", "Uno", 1, 100.0),
            _numbered_pc("C:/m/Anna/Disco/02 Due.mp3", "Due", 2, 120.0)]
    far = [_numbered_pc("D:/archivio/musica.buona/Anna/Disco/01 Uno.mp3", "Uno", 1, 100.0),
           _numbered_pc("D:/archivio/musica.buona/Anna/Disco/02 Due.mp3", "Due", 2, 120.0)]
    assert adoption.album_folder_matches(phone, near + far) == {1: near[0], 2: near[1]}       # il più corto
    assert adoption.album_folder_matches(phone, near + far, PREFERRED) == {1: far[0], 2: far[1]}
    # copie uguali: un candidato solo, quello preferito, e la regola è sicura (niente AI)
    by_length = adoption._by_length(near + far)
    assert [track for _score, track in adoption.candidates(phone[0], by_length, PREFERRED)] == [far[0]]
    outcome = _run_preferred(phone[:1], near + far)
    assert outcome.proposals[0].pc is far[0] and outcome.proposals[0].level == adoption.LEVEL_VERY_LIKELY
    # stesso audio in più copie: la preferita, anche con un tag in più di differenza
    far[0].tags.album = "Disco (remaster)"
    assert adoption._closest_copy(phone[0], [near[0], far[0]], PREFERRED) is far[0]
    assert adoption._closest_copy(phone[0], [near[0], far[0]]) is near[0]


def _run_preferred(phone, pc):
    result = adoption.adopt(phone, pc, Registry(), Path("."), None, None, None, None, False, False, False, PREFERRED)
    return result


def test_disc_number_at_the_end_of_the_folder_and_phone_duplicates():
    from myeasymp3toiphone.library import album_folder
    assert album_folder("C:/m/Anna/Dal vivo (Disc 2)/01.mp3") == str(Path("C:/m/Anna/Dal vivo"))
    assert album_folder("C:/m/Anna/Il meglio CD1/01.mp3") == str(Path("C:/m/Anna/Il meglio"))
    assert album_folder("C:/m/Anna/Canzoni 1999/01.mp3") == str(Path("C:/m/Anna/Canzoni 1999"))     # un anno resta
    phone = []
    pc = []
    for disc in (1, 2):
        item = _numbered(disc, f"Brano {disc}", "Dal vivo", 1, 200.0 + disc * 10)
        item.tags.disc_number = disc
        phone.append(item)
        track = _numbered_pc(f"C:/m/Anna/Dal vivo (Disc {disc})/01 Brano {disc}.mp3", f"Brano {disc}", 1,
                             200.0 + disc * 10)
        track.tags.disc_number = disc
        pc.append(track)
    double = _numbered(3, "Brano 1", "Dal vivo", 1, 211.0)           # doppione sull'iPhone
    double.tags.disc_number = 1
    matches = adoption.album_folder_matches(phone + [double], pc)
    assert matches == {1: pc[0], 2: pc[1]}                            # l'album resta proposto, il doppione no


def test_automatic_proposals_folder_name_and_taken_files():
    from myeasymp3toiphone.overlay import path_key
    phone = [_numbered(1, "Uno", "Disco", 1, 100.0), _numbered(2, "Solo qui", "Disco", 2, 300.0)]
    pc = [_numbered_pc("C:/m/Anna/Disco/01 Uno.mp3", "Uno", 1, 100.0)]
    found = adoption.automatic_proposals(phone, pc)
    assert list(found) == [1] and found[1].how == provenance.HOW_FOLDER     # l'album intero no, la cartella sì
    assert adoption.automatic_proposals(phone, pc, (), {path_key(pc[0].path)}) == {}   # già di un altro brano
