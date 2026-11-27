# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le varianti dei nomi d'artista: regole, duetti, gruppi dubbi con AI e MusicBrainz finti. Nomi inventati."""

from pathlib import Path

from myeasymp3toiphone import artist_names as an, scan
from myeasymp3toiphone.library import Track
from myeasymp3toiphone.tags import TrackTags


def _track(number, artist, album="Disco", title="Brano", album_artist=""):
    result = Track(path=Path(f"C:/musica/{number}.mp3"),
                   tags=TrackTags(title=f"{title} {number}", artist=artist, album=album, album_artist=album_artist,
                                  year="1990"))
    return result


def test_keys_duets_and_pairs():
    assert an.variant_key("Rossi Mario") == an.variant_key("mario  ROSSI") == an.variant_key("Mário Rossi")
    assert an.variant_key("The Gatti") == an.variant_key("Gatti") and an.variant_key("AC/DC") == an.variant_key("ACDC")
    assert an.duet_parts("Mario Rossi feat. Anna Verdi & Luca") == ["Mario Rossi", "Anna Verdi", "Luca"]
    solos = {an.variant_key("Mario Rossi"): "Mario Rossi"}
    assert an.duet_proposal("Mario Rossi & Anna Verdi", solos) == ("Mario Rossi", ["Anna Verdi"])
    assert an.duet_proposal("Neri & Bianchi", solos) is None                  # nessuno dei due da solo
    assert an.duet_proposal("Mario Rossi, Jr.", solos) is None
    assert an.with_guests("Canzone", ["Anna Verdi"]) == "Canzone (feat. Anna Verdi)"
    assert an.with_guests("Canzone (feat. X)", ["Anna Verdi"]) == "Canzone (feat. X)"
    names = {an.variant_key(n): n for n in ("Mario Rossi", "Rossi", "M. Rossi", "Mario Rosi", "Luca Bianchi")}
    found = {(a, b): why for a, b, why in an.candidate_pairs(names)}
    assert found[tuple(sorted((an.variant_key("Rossi"), an.variant_key("Mario Rossi"))))] == "solo il cognome"
    assert found[tuple(sorted((an.variant_key("M. Rossi"), an.variant_key("Mario Rossi"))))] == "iniziali"
    assert found[tuple(sorted((an.variant_key("Mario Rosi"), an.variant_key("Mario Rossi"))))] == "quasi uguali"
    assert all(an.variant_key("Luca Bianchi") not in pair for pair in found)
    groups = an.clusters(an.candidate_pairs(names))
    assert len(groups) == 1 and len(groups[0][0]) == 4


def test_word_order_is_a_certain_variant_and_duets_stay_as_they_are():
    """Un duetto ("A & B", anche come artista dell'album) è un nome come un altro: non si segnala e non si cambia."""
    tracks = [_track(1, "Mario Rossi"), _track(2, "Mario Rossi"), _track(3, "Rossi Mario"),
              _track(4, "Mario Rossi & Anna Verdi", album="Insieme", album_artist="Mario Rossi & Anna Verdi"),
              _track(5, "Mario Rossi & Anna Verdi", album="Altro", album_artist="Mario Rossi")]
    variants = scan.detect_artist_variants(tracks)
    assert len(variants) == 1 and dict(variants[0].fix.changes)[tracks[2].path] == {"artist": "Mario Rossi"}
    issues = scan.rule_issues(tracks, False, checks=frozenset({scan.CHECK_VARIANTS, scan.CHECK_SPLIT}))
    for issue in issues:
        changed = dict(issue.fix.changes) if issue.fix is not None else {}
        assert tracks[3].path not in changed and tracks[4].path not in changed, issue.title


def test_a_duet_without_album_artist_splitting_the_album_is_still_found():
    """Quello che divide l'album in Musica sì: nella stessa cartella un brano "A & B" senza artista dell'album."""
    tracks = []
    for number, artist in enumerate(["Mario Rossi", "Mario Rossi", "Mario Rossi & Anna Verdi"], start=1):
        tracks.append(Track(path=Path(f"C:/musica/Insieme/{number}.mp3"),
                            tags=TrackTags(title=f"Brano {number}", artist=artist, album="Insieme", year="1990")))
    issues = scan.rule_issues(tracks, False, checks=frozenset({scan.CHECK_VARIANTS, scan.CHECK_SPLIT}))
    [split] = [issue for issue in issues if issue.rule_id.startswith("R11")]
    changes = dict(split.fix.changes)
    # non una compilation: l'artista dell'album è quello principale, il duetto resta l'artista del brano
    assert changes[tracks[2].path] == {"album_artist": "Mario Rossi"} and changes[tracks[0].path] == \
        {"album_artist": "Mario Rossi"}


class NamesProvider:
    def __init__(self):
        self.profile = type("P", (), {"name": "finta"})()

    def ask_json(self, system, user, schema):
        groups = []
        current = None
        for line in user.splitlines():
            if line.startswith("G"):
                current = {"group": line, "same": [[]], "reason": "stesso cantante"}
                groups.append(current)
            elif current is not None and line.strip():
                name = line.strip().split(" | ")[0]
                if name != "Rossi":                     # "Rossi" da solo è un altro artista
                    current["same"][0].append(name)
        return {"groups": groups}


class FakeMusicBrainz:
    def __init__(self):
        self.asked = []

    def search_artists(self, name):
        self.asked.append(name)
        return [["Mario Rossi", "Rossi, Mario", "M. Rossi"]]


def test_doubtful_names_with_ai_or_musicbrainz():
    tracks = [_track(n, "Mario Rossi") for n in range(1, 6)] + [_track(6, "M. Rossi"), _track(7, "Rossi"),
                                                                 _track(8, "Luca Bianchi")]
    plain, errors = scan.detect_artist_doubts(tracks)
    assert errors == [] and len(plain) == 1 and plain[0].title.startswith("Forse")
    assert "da controllare" in plain[0].detail
    with_ai, _errors = scan.detect_artist_doubts(tracks, NamesProvider())
    assert len(with_ai) == 1 and with_ai[0].origin == scan.ORIGIN_AI
    assert dict(with_ai[0].fix.changes) == {tracks[5].path: {"artist": "Mario Rossi"}}   # "Rossi" escluso
    client = FakeMusicBrainz()
    with_mb, _errors = scan.detect_artist_doubts(tracks, None, client)
    assert client.asked == ["Mario Rossi"] and "MusicBrainz" in with_mb[0].detail
    assert dict(with_mb[0].fix.changes) == {tracks[5].path: {"artist": "Mario Rossi"}}
