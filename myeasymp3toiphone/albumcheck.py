"""Verifica di completezza degli album tramite il database online MusicBrainz.

Per ogni album locale si cercano le pubblicazioni (release) corrispondenti su
MusicBrainz, si sceglie la più probabile e se ne confronta la lista tracce con
i file presenti, segnalando le tracce mancanti e quelle in più.
"""

import re
import threading
import time
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Optional

import requests

from .library import UNKNOWN_ALBUM, UNKNOWN_ARTIST, Track
from .tags import TrackTags

API_ROOT = "https://musicbrainz.org/ws/2/"
COVER_ROOT = "https://coverartarchive.org/"
USER_AGENT = "myEasyMP3toIPhone/1.0 (Windows music organizer)"
MIN_INTERVAL = 1.1          # MusicBrainz consente circa una richiesta al secondo
MAX_ATTEMPTS = 5           # su 503/429 riprova dopo 2, 4, 8, 16 secondi
VIDEO_FORMATS = ("DVD", "Blu-ray", "VHS")

STATUS_COMPLETE = "complete"
STATUS_INCOMPLETE = "incomplete"
STATUS_NOT_FOUND = "not_found"
STATUS_ERROR = "error"


class AlbumCheckError(Exception):
    """Errore di comunicazione con MusicBrainz."""


@dataclass
class ReleaseCandidate:
    id: str
    title: str
    artist: str
    date: str
    country: str
    track_count: int
    formats: str
    status: str
    mb_score: int
    release_group_id: str = ""

    def label(self) -> str:
        details = [self.date or "data ?", self.country or "paese ?", self.formats or "formato ?",
                   f"{self.track_count} tracce"]
        result = f"{self.title} — {self.artist} ({', '.join(details)})"
        return result


@dataclass
class ExpectedTrack:
    disc: int
    position: int
    title: str
    length_ms: int
    disc_total: int
    disc_track_count: int

    def position_label(self) -> str:
        if self.disc_total > 1:
            result = f"{self.disc}-{self.position:02d}"
        else:
            result = f"{self.position:02d}"
        return result


@dataclass
class TrackMatch:
    expected: ExpectedTrack
    local: Optional[Track]


@dataclass
class AlbumCheckResult:
    artist: str
    album: str
    local_tracks: list
    candidates: list = field(default_factory=list)
    release: Optional[ReleaseCandidate] = None
    matches: list = field(default_factory=list)
    extra: list = field(default_factory=list)
    error: str = ""

    @property
    def missing(self) -> list:
        result = []
        for match in self.matches:
            if match.local is None:
                result.append(match.expected)
        return result

    @property
    def status(self) -> str:
        if self.error:
            result = STATUS_ERROR
        elif self.release is None:
            result = STATUS_NOT_FOUND
        elif self.missing:
            result = STATUS_INCOMPLETE
        else:
            result = STATUS_COMPLETE
        return result

    def status_text(self) -> str:
        status = self.status
        if status == STATUS_ERROR:
            result = f"Errore: {self.error}"
        elif status == STATUS_NOT_FOUND:
            result = "Non trovato su MusicBrainz"
        elif status == STATUS_INCOMPLETE:
            result = f"Incompleto: mancano {len(self.missing)} di {len(self.matches)} tracce"
        else:
            result = f"Completo ({len(self.matches)} tracce)"
        if status in (STATUS_COMPLETE, STATUS_INCOMPLETE) and self.extra:
            result += f", {len(self.extra)} tracce non riconosciute"
        return result


# --------------------------------------------------------------------------- confronto testi

def normalize(text: str) -> str:
    """Testo semplificato per il confronto: minuscolo, senza accenti, parentesi e punteggiatura."""
    lowered = unicodedata.normalize("NFKD", text.lower())
    plain = ""
    for char in lowered:
        if not unicodedata.combining(char):
            plain += char
    without_brackets = re.sub(r"[\(\[][^\)\]]*[\)\]]", " ", plain)
    if not without_brackets.strip():
        without_brackets = plain
    words = re.sub(r"[^a-z0-9]+", " ", without_brackets.replace("&", " and ")).strip()
    # "01 titolo" (numero di traccia nel nome del file) -> "titolo"
    result = re.sub(r"^\d{1,3}\s+(?=\S)", "", words)
    return result


def similarity(first: str, second: str) -> float:
    a = normalize(first)
    b = normalize(second)
    if not a or not b:
        result = 0.0
    elif a == b:
        result = 1.0
    else:
        result = SequenceMatcher(None, a, b).ratio()
    return result


def _lucene_phrase(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    result = f'"{escaped}"'
    return result


def _credit_name(credits: list) -> str:
    result = ""
    for credit in credits or []:
        result += credit.get("name", "") + credit.get("joinphrase", "")
    return result.strip()


# --------------------------------------------------------------------------- client MusicBrainz

class MusicBrainzClient:
    def __init__(self) -> None:
        self._session = requests.Session()
        # niente header Accept: MusicBrainz risponde 503 a "Accept: application/json" (basta fmt=json)
        self._session.headers.update({"User-Agent": USER_AGENT})
        self._last_request = 0.0
        self._lock = threading.Lock()

    def _get(self, url: str, params: dict) -> dict:
        attempt = 0
        payload = None
        while payload is None and attempt < MAX_ATTEMPTS:
            attempt += 1
            with self._lock:
                wait = MIN_INTERVAL * attempt - (time.monotonic() - self._last_request)
                if wait > 0:
                    time.sleep(wait)
                try:
                    response = self._session.get(url, params=params, timeout=20)
                except requests.RequestException as exc:
                    raise AlbumCheckError(f"connessione a MusicBrainz non riuscita ({exc})") from exc
                finally:
                    self._last_request = time.monotonic()
            if response.status_code == 200:
                payload = response.json()
            elif response.status_code in (429, 503) and attempt < MAX_ATTEMPTS:
                time.sleep(2.0 ** attempt)
            elif response.status_code in (429, 503):
                raise AlbumCheckError("MusicBrainz è sovraccarico in questo momento: riprova tra qualche minuto")
            else:
                raise AlbumCheckError(f"MusicBrainz ha risposto con l'errore {response.status_code}")
        return payload

    def search_artists(self, name: str, min_score: int = 90) -> list:
        """Il primo artista trovato per name, se il punteggio è almeno min_score: [[nome, nome per l'ordinamento,
        alias…]] (al più uno); [] se non c'è."""
        data = self._get(API_ROOT + "artist/", {"query": f"artist:{_lucene_phrase(name)}", "fmt": "json",
                                                "limit": 3})
        result = []
        artists = data.get("artists", [])
        if artists and int(artists[0].get("score", 0) or 0) >= min_score:
            first = artists[0]
            names = [first.get("name", ""), first.get("sort-name", "")]
            for alias in first.get("aliases", []) or []:
                names.append(alias.get("name", ""))
                names.append(alias.get("sort-name", ""))
            result.append(names)
        return result

    def search_releases(self, artist: str, album: str, limit: int = 15) -> list:
        query = f"release:{_lucene_phrase(album)}"
        if artist and artist != UNKNOWN_ARTIST:
            query += f" AND artist:{_lucene_phrase(artist)}"
        data = self._get(API_ROOT + "release/", {"query": query, "fmt": "json", "limit": limit})
        candidates = []
        for release in data.get("releases", []):
            formats = []
            for medium in release.get("media", []):
                medium_format = medium.get("format") or ""
                if medium_format and medium_format not in formats:
                    formats.append(medium_format)
            candidates.append(ReleaseCandidate(
                id=release["id"],
                title=release.get("title", ""),
                artist=_credit_name(release.get("artist-credit", [])),
                date=release.get("date", ""),
                country=release.get("country", ""),
                track_count=int(release.get("track-count", 0) or 0),
                formats=" + ".join(formats),
                status=release.get("status", ""),
                mb_score=int(release.get("score", 0) or 0),
                release_group_id=(release.get("release-group") or {}).get("id", ""),
            ))
        return candidates

    def get_expected_tracks(self, release_id: str) -> list:
        data = self._get(API_ROOT + f"release/{release_id}", {"inc": "recordings", "fmt": "json"})
        audio_media = []
        for medium in data.get("media", []):
            medium_format = medium.get("format") or ""
            is_video = False
            for video in VIDEO_FORMATS:
                if video in medium_format:
                    is_video = True
            if not is_video:
                audio_media.append(medium)
        expected = []
        disc = 0
        for medium in audio_media:
            disc += 1
            tracks = medium.get("tracks", [])
            for track in tracks:
                expected.append(ExpectedTrack(
                    disc=disc,
                    position=int(track.get("position", 0) or 0),
                    title=track.get("title", ""),
                    length_ms=int(track.get("length") or 0),
                    disc_total=len(audio_media),
                    disc_track_count=len(tracks),
                ))
        return expected

    def _download_cover(self, url: str) -> Optional[bytes]:
        result = None
        try:
            response = self._session.get(url, timeout=30)
            if response.status_code == 200 and response.content:
                result = response.content
        except requests.RequestException:
            result = None
        return result

    def fetch_cover(self, release: ReleaseCandidate) -> Optional[bytes]:
        """Copertina dell'edizione; se manca, quella generica dell'album (release group)."""
        result = self._download_cover(COVER_ROOT + f"release/{release.id}/front-500")
        if result is None and release.release_group_id:
            result = self._download_cover(COVER_ROOT + f"release-group/{release.release_group_id}/front-500")
        return result


# --------------------------------------------------------------------------- logica di verifica

def expected_track_count(local_tracks: list) -> int:
    result = len(local_tracks)
    for track in local_tracks:
        result = max(result, track.tags.track_number or 0, track.tags.track_total or 0)
    return result


def choose_release(candidates: list, album: str, local_tracks: list) -> Optional[ReleaseCandidate]:
    """Sceglie l'edizione più probabile in base a punteggio, titolo e numero di tracce."""
    wanted = expected_track_count(local_tracks)
    best = None
    best_score = None
    for candidate in candidates:
        score = float(candidate.mb_score)
        if candidate.track_count == wanted:
            score += 40
        elif candidate.track_count >= len(local_tracks):
            score += 15
        else:
            score -= 40
        if candidate.status == "Official":
            score += 10
        score += 20 * similarity(album, candidate.title)
        if best_score is None or score > best_score:
            best = candidate
            best_score = score
    return best


def match_tracks(expected: list, local_tracks: list) -> tuple:
    """Abbina tracce attese e locali. Restituisce (lista di TrackMatch, tracce locali in più)."""
    pairs = []
    for exp_index, exp in enumerate(expected):
        for loc_index, track in enumerate(local_tracks):
            title_score = similarity(exp.title, track.title)
            same_position = (track.tags.track_number == exp.position
                             and (track.tags.disc_number or 1) == exp.disc)
            acceptable = (title_score >= 0.8
                          or (same_position and title_score >= 0.4)
                          or (same_position and not track.tags.title))
            if acceptable:
                bonus = 0.3 if same_position else 0.0
                pairs.append((title_score + bonus, exp_index, loc_index))
    pairs.sort(key=lambda item: item[0], reverse=True)
    assigned_expected = {}
    used_local = set()
    for _score, exp_index, loc_index in pairs:
        if exp_index not in assigned_expected and loc_index not in used_local:
            assigned_expected[exp_index] = local_tracks[loc_index]
            used_local.add(loc_index)
    matches = []
    for exp_index, exp in enumerate(expected):
        matches.append(TrackMatch(expected=exp, local=assigned_expected.get(exp_index)))
    extra = []
    for loc_index, track in enumerate(local_tracks):
        if loc_index not in used_local:
            extra.append(track)
    result = (matches, extra)
    return result


def check_album(client: MusicBrainzClient, local_tracks: list,
                candidates: Optional[list] = None,
                chosen: Optional[ReleaseCandidate] = None) -> AlbumCheckResult:
    """Verifica un album. candidates/chosen permettono di ricalcolare con un'altra edizione."""
    artist, album = local_tracks[0].album_key
    result = AlbumCheckResult(artist=artist, album=album, local_tracks=list(local_tracks))
    if album == UNKNOWN_ALBUM:
        result.error = "l'album non ha un nome: compila il tag Album"
    else:
        try:
            if candidates is None:
                candidates = client.search_releases(artist, album)
            result.candidates = candidates
            if chosen is None:
                chosen = choose_release(candidates, album, local_tracks)
            if chosen is not None:
                expected = client.get_expected_tracks(chosen.id)
                result.release = chosen
                result.matches, result.extra = match_tracks(expected, local_tracks)
        except AlbumCheckError as exc:
            result.error = str(exc)
    return result


def corrected_tags(match: TrackMatch, release: ReleaseCandidate) -> TrackTags:
    """Tag della traccia locale corretti secondo i dati MusicBrainz."""
    tags = match.local.tags.copy()
    exp = match.expected
    tags.title = exp.title
    tags.track_number = exp.position
    tags.track_total = exp.disc_track_count
    tags.disc_number = exp.disc
    tags.disc_total = exp.disc_total
    tags.album = release.title
    tags.album_artist = release.artist
    if not tags.artist:
        tags.artist = release.artist
    if release.date:
        tags.year = release.date[:4]
    return tags
