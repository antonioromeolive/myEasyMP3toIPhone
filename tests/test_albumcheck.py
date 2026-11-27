# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Verifica album online: i cataloghi (risposte finte, nessuna rete), l'ordine dei servizi. Nomi e valori inventati."""

from pathlib import Path

from myeasymp3toiphone import albumcheck
from myeasymp3toiphone.albumcheck import (
    STATUS_COMPLETE, STATUS_INCOMPLETE, STATUS_NOT_FOUND, AlbumCheckError, ExpectedTrack, ReleaseCandidate,
)
from myeasymp3toiphone.library import Track, assign_groups
from myeasymp3toiphone.tags import TrackTags


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status_code = status
        self.content = b"img"

    def json(self):
        return self.payload


class FakeSession:
    """Risponde secondo l'inizio dell'indirizzo; ricorda le richieste (e le intestazioni)."""

    def __init__(self, answers):
        self.answers = answers
        self.seen = []
        self.headers = {}

    def get(self, url, params=None, headers=None, timeout=0):
        self.seen.append((url, dict(params or {}), dict(headers or {})))
        payload = None
        for prefix, value in self.answers.items():
            if url.startswith(prefix) and payload is None:
                payload = value
        return FakeResponse(payload if payload is not None else {}, 200 if payload is not None else 404)


def _client(cls, answers):
    client = cls()
    client.min_interval = 0
    client._session = FakeSession(answers)
    return client


def _album(titles, artist="Cantante Finto", album="Disco Finto"):
    tracks = []
    for number, title in enumerate(titles, start=1):
        tracks.append(Track(path=Path(f"C:/m/{album}/{number:02d} {title}.mp3"),
                            tags=TrackTags(title=title, artist=artist, album=album, track_number=number)))
    assign_groups(tracks)
    return tracks


def test_deezer_search_and_tracks():
    client = _client(albumcheck.DeezerClient, {
        "https://api.deezer.com/search/album": {"data": [
            {"id": 5, "title": "Disco Finto", "nb_tracks": 2, "record_type": "album", "artist": {"name": "Cantante"},
             "cover_xl": "https://img/5.jpg", "link": "https://www.deezer.com/album/5"}]},
        "https://api.deezer.com/album/5/tracks": {"data": [
            {"title": "Uno", "duration": 100, "track_position": 1, "disk_number": 1},
            {"title": "Due", "duration": 120, "track_position": 2, "disk_number": 1}]},
        "https://api.deezer.com/album/5": {"release_date": "1999-05-01"},
    })
    candidates = client.search_releases("Cantante", "Disco Finto")
    assert candidates[0].service == "deezer" and candidates[0].track_count == 2
    assert 'artist:"Cantante"' in client._session.seen[0][1]["q"]
    tracks = client.get_expected_tracks(candidates[0])
    assert [(t.disc, t.position, t.title, t.length_ms) for t in tracks] == [(1, 1, "Uno", 100000), (1, 2, "Due", 120000)]
    assert candidates[0].date == "1999-05-01" and client.release_url(candidates[0]).endswith("/album/5")


def test_apple_search_and_tracks():
    client = _client(albumcheck.AppleClient, {
        "https://itunes.apple.com/search": {"results": [
            {"collectionId": 9, "collectionName": "Disco Finto", "artistName": "Cantante", "trackCount": 3,
             "releaseDate": "1999-05-01T07:00:00Z", "artworkUrl100": "https://img/100x100bb.jpg"}]},
        "https://itunes.apple.com/lookup": {"results": [
            {"wrapperType": "collection"},
            {"wrapperType": "track", "trackName": "Tre", "trackNumber": 1, "discNumber": 2, "trackTimeMillis": 5},
            {"wrapperType": "track", "trackName": "Uno", "trackNumber": 1, "discNumber": 1, "trackTimeMillis": 5},
            {"wrapperType": "track", "trackName": "Due", "trackNumber": 2, "discNumber": 1, "trackTimeMillis": 5}]},
    })
    candidate = client.search_releases("Cantante", "Disco Finto")[0]
    assert candidate.date == "1999-05-01" and candidate.cover_url.endswith("600x600bb.jpg")
    tracks = client.get_expected_tracks(candidate)
    assert [(t.disc, t.position, t.title, t.disc_total, t.disc_track_count) for t in tracks] == \
        [(1, 1, "Uno", 2, 2), (1, 2, "Due", 2, 2), (2, 1, "Tre", 2, 1)]


def test_discogs_needs_the_token_and_sends_it_only_in_the_header(monkeypatch):
    monkeypatch.delenv(albumcheck.DISCOGS_TOKEN_VAR, raising=False)
    client = _client(albumcheck.DiscogsClient, {})
    assert not client.available()
    try:
        client.search_releases("A", "B")
        raised = False
    except AlbumCheckError:
        raised = True
    assert raised
    monkeypatch.setenv(albumcheck.DISCOGS_TOKEN_VAR, "token-finto-di-prova")
    client = _client(albumcheck.DiscogsClient, {
        "https://api.discogs.com/database/search": {"results": [
            {"id": 3, "title": "Cantante - Disco Finto", "year": "1999", "format": ["CD", "Album"]}]},
        "https://api.discogs.com/releases/3": {"tracklist": [
            {"position": "", "type_": "heading", "title": "Lato A"},
            {"position": "1-01", "type_": "track", "title": "Uno", "duration": "3:05"},
            {"position": "2-01", "type_": "track", "title": "Due", "duration": ""}]},
    })
    candidate = client.search_releases("Cantante", "Disco Finto")[0]
    assert (candidate.artist, candidate.title, candidate.formats) == ("Cantante", "Disco Finto", "CD + Album")
    tracks = client.get_expected_tracks(candidate)
    assert [(t.disc, t.position, t.title, t.length_ms) for t in tracks] == [(1, 1, "Uno", 185000), (2, 1, "Due", 0)]
    for url, params, headers in client._session.seen:
        assert "token-finto-di-prova" not in url and "token-finto-di-prova" not in str(params)
        assert headers["Authorization"] == "Discogs token=token-finto-di-prova"


def test_discogs_positions():
    assert albumcheck._discogs_position("CD2-05", 9) == (2, 5)
    assert albumcheck._discogs_position("7", 9) == (1, 7)
    assert albumcheck._discogs_position("B2", 9) == (1, 9)


class FakeService:
    def __init__(self, service, tracks):
        self.service = service
        self.label = service.capitalize()
        self.tracks = tracks
        self.calls = 0

    def search_releases(self, artist, album):
        self.calls += 1
        result = []
        if self.tracks is not None:
            result = [ReleaseCandidate(id="1", title=album, artist=artist, date="", country="",
                                       track_count=len(self.tracks), formats="", status="", mb_score=100,
                                       service=self.service)]
        return result

    def get_expected_tracks(self, release):
        result = []
        for number, title in enumerate(self.tracks, start=1):
            result.append(ExpectedTrack(1, number, title, 0, 1, len(self.tracks)))
        return result


def test_services_in_order_until_one_is_complete():
    local = _album(["Uno", "Due"])
    missing = FakeService("deezer", None)
    partial = FakeService("apple", ["Uno", "Due", "Tre"])
    full = FakeService("discogs", ["Uno", "Due"])
    never = FakeService("musicbrainz", ["Uno", "Due"])
    result = albumcheck.check_album_services([missing, partial, full, never], local)
    assert result.status == STATUS_COMPLETE and result.service == "discogs" and never.calls == 0
    assert [label for label, _status in result.tried] == ["Deezer", "Apple", "Discogs"]
    best = albumcheck.check_album_services([missing, partial], local)        # nessuno completo: il migliore
    assert best.status == STATUS_INCOMPLETE and best.service == "apple" and len(best.missing) == 1
    none = albumcheck.check_album_services([missing], local)
    assert none.status == STATUS_NOT_FOUND and "Deezer" in none.status_text()


def test_every_rule_says_what_to_do():
    from myeasymp3toiphone import scan
    from myeasymp3toiphone.accepted import TYPE_LABELS
    rules = ["R2", "R3", "R5", "R6", "R7", "R8", "R9", "R10", "R11", "R12", "R13", "R14", "R15", "R16",
             "I1", "I2", "I3", "I4"]
    for number in range(18, 32):                 # le regole di checks_requirements.md: anche il nome per "va bene così"
        rules.append(f"R{number}")
        assert f"R{number}" in TYPE_LABELS
    for rule in rules:
        assert scan.advice(scan.Issue(scan.KIND_SPLIT, scan.SEVERITY_LOW, "t", "d", rule_id=f"{rule}.1")), rule
    for kind in scan.AI_KINDS:
        assert scan.advice(scan.Issue(kind, scan.SEVERITY_LOW, "t", "d", origin=scan.ORIGIN_AI)), kind
