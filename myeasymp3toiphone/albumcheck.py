"""Verifica album online: la completezza degli album confrontata con i cataloghi online.

Per ogni album locale si cercano le pubblicazioni (edizioni) corrispondenti in un catalogo, si sceglie la più
probabile e se ne confronta l'elenco delle tracce con i file presenti, segnalando le tracce mancanti e quelle in più.
I cataloghi, dal più veloce: Deezer e Apple Music (gratis, senza chiave), Discogs (con un token personale,
DISCOGS_TOKEN) e MusicBrainz (una richiesta al secondo). Con più cataloghi scelti si provano in quest'ordine, album per
album, finché uno dà l'album completo; se nessuno lo dà, vale il risultato migliore (meno tracce mancanti).
L'AI, se scelta, sceglie solo tra edizioni dubbie (punteggi vicini). CDDB/freedb ha chiuso nel 2020; il suo erede
gnudb vuole la struttura del CD (TOC), che dei file non hanno.
"""

import os
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
DEEZER_API_ROOT = "https://api.deezer.com/"
APPLE_API_ROOT = "https://itunes.apple.com/"
DISCOGS_API_ROOT = "https://api.discogs.com/"
DISCOGS_TOKEN_VAR = "DISCOGS_TOKEN"
SERVICE_DEEZER = "deezer"
SERVICE_APPLE = "apple"
SERVICE_DISCOGS = "discogs"
SERVICE_MUSICBRAINZ = "musicbrainz"
SERVICE_ORDER = (SERVICE_DEEZER, SERVICE_APPLE, SERVICE_DISCOGS, SERVICE_MUSICBRAINZ)   # dal più veloce
CLOSE_EDITIONS = 15         # due edizioni con punteggi così vicini sono un dubbio (l'AI, se scelta, decide)
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
    mb_score: int             # il punteggio del servizio (MusicBrainz) o quello dato dall'ordine dei risultati
    release_group_id: str = ""
    service: str = SERVICE_MUSICBRAINZ
    cover_url: str = ""
    url: str = ""

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
    service: str = SERVICE_MUSICBRAINZ
    service_label: str = "MusicBrainz"
    tried: list = field(default_factory=list)     # [(servizio, esito)] dei servizi provati, in ordine
    ai_reason: str = ""                           # se l'edizione l'ha scelta l'AI: il suo motivo

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
            result = f"Non trovato su {self.service_label}"
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

# --------------------------------------------------------------------------- i servizi

class _ServiceClient:
    """Un catalogo online: search_releases(artista, album) -> [ReleaseCandidate], get_expected_tracks(candidato) ->
    [ExpectedTrack], fetch_cover(candidato), release_url(candidato). Una richiesta alla volta, con l'intervallo
    minimo che il servizio chiede, e qualche tentativo se è sovraccarico."""

    service = ""
    label = ""
    min_interval = 1.0

    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT})
        self._last_request = 0.0
        self._lock = threading.Lock()

    def available(self) -> bool:
        result = True
        return result

    def _headers(self) -> dict:
        result = {}
        return result

    def _get(self, url: str, params: dict) -> dict:
        attempt = 0
        payload = None
        while payload is None and attempt < MAX_ATTEMPTS:
            attempt += 1
            with self._lock:
                wait = self.min_interval * attempt - (time.monotonic() - self._last_request)
                if wait > 0:
                    time.sleep(wait)
                try:
                    response = self._session.get(url, params=params, headers=self._headers(), timeout=20)
                except requests.RequestException as exc:
                    raise AlbumCheckError(f"connessione a {self.label} non riuscita ({type(exc).__name__})") from exc
                finally:
                    self._last_request = time.monotonic()
            if response.status_code == 200:
                try:
                    payload = response.json()
                except ValueError as exc:
                    raise AlbumCheckError(f"{self.label} ha risposto con dati non validi") from exc
            elif response.status_code in (429, 503) and attempt < MAX_ATTEMPTS:
                time.sleep(2.0 ** attempt)
            elif response.status_code in (429, 503):
                raise AlbumCheckError(f"{self.label} è sovraccarico in questo momento: riprova tra qualche minuto")
            elif response.status_code == 404:
                payload = {}
            else:
                raise AlbumCheckError(f"{self.label} ha risposto con l'errore {response.status_code}")
        return payload

    def _download_cover(self, url: str) -> Optional[bytes]:
        result = None
        if url:
            try:
                response = self._session.get(url, headers=self._headers(), timeout=30)
                if response.status_code == 200 and response.content:
                    result = response.content
            except requests.RequestException:
                result = None
        return result

    def fetch_cover(self, release: ReleaseCandidate) -> Optional[bytes]:
        result = self._download_cover(release.cover_url)
        return result

    def release_url(self, release: ReleaseCandidate) -> str:
        result = release.url
        return result


def _numbered_tracks(rows: list) -> list:
    """[ExpectedTrack] da [(disco, posizione, titolo, durata in ms)], con il numero di dischi e di tracce per disco."""
    discs = {}
    for disc, _position, _title, _length in rows:
        discs[disc] = discs.get(disc, 0) + 1
    ordered = sorted(discs)
    renumber = {}
    for index, disc in enumerate(ordered, start=1):
        renumber[disc] = index
    result = []
    for disc, position, title, length in rows:
        result.append(ExpectedTrack(disc=renumber[disc], position=position, title=title, length_ms=length,
                                    disc_total=len(ordered), disc_track_count=discs[disc]))
    return result


def _rank_score(index: int) -> int:
    """Il punteggio di un risultato secondo l'ordine del servizio (il primo è il più pertinente)."""
    result = max(0, 100 - 5 * index)
    return result


class DeezerClient(_ServiceClient):
    service = SERVICE_DEEZER
    label = "Deezer"
    min_interval = 0.15       # Deezer accetta 50 richieste ogni 5 secondi

    def search_releases(self, artist: str, album: str, limit: int = 15) -> list:
        query = f'album:"{album}"'
        if artist and artist != UNKNOWN_ARTIST:
            query = f'artist:"{artist}" ' + query
        data = self._get(DEEZER_API_ROOT + "search/album", {"q": query, "limit": limit})
        candidates = []
        for index, entry in enumerate(data.get("data", []) or []):
            candidates.append(ReleaseCandidate(
                id=str(entry.get("id", "")), title=entry.get("title", ""),
                artist=(entry.get("artist") or {}).get("name", ""), date="", country="",
                track_count=int(entry.get("nb_tracks", 0) or 0), formats=entry.get("record_type", "") or "",
                status="", mb_score=_rank_score(index), service=self.service,
                cover_url=entry.get("cover_xl", "") or entry.get("cover_big", "") or "",
                url=entry.get("link", "") or f"https://www.deezer.com/album/{entry.get('id', '')}"))
        return candidates

    def get_expected_tracks(self, release: ReleaseCandidate) -> list:
        album = self._get(DEEZER_API_ROOT + f"album/{release.id}", {})
        if album.get("release_date"):
            release.date = album["release_date"]
        data = self._get(DEEZER_API_ROOT + f"album/{release.id}/tracks", {"limit": 500})
        rows = []
        for entry in data.get("data", []) or []:
            rows.append((int(entry.get("disk_number", 1) or 1), int(entry.get("track_position", 0) or 0),
                         entry.get("title", ""), int(entry.get("duration", 0) or 0) * 1000))
        result = _numbered_tracks(rows)
        return result


def store_country() -> str:
    """Il paese del negozio di Apple: quello delle impostazioni di Windows (it-IT -> IT); US se non si sa."""
    result = "US"
    try:
        import ctypes
        buffer = ctypes.create_unicode_buffer(85)
        if ctypes.windll.kernel32.GetUserDefaultLocaleName(buffer, 85):
            parts = buffer.value.split("-")
            if len(parts) >= 2 and len(parts[-1]) == 2 and parts[-1].isalpha():
                result = parts[-1].upper()
    except (AttributeError, OSError):
        result = "US"
    return result


class AppleClient(_ServiceClient):
    service = SERVICE_APPLE
    label = "Apple Music"
    min_interval = 3.0        # l'iTunes Search API accetta circa 20 richieste al minuto

    def __init__(self) -> None:
        super().__init__()
        self.country = store_country()

    def search_releases(self, artist: str, album: str, limit: int = 15) -> list:
        term = album if not artist or artist == UNKNOWN_ARTIST else f"{artist} {album}"
        data = self._get(APPLE_API_ROOT + "search", {"term": term, "entity": "album", "limit": limit,
                                                     "country": self.country})
        candidates = []
        for index, entry in enumerate(data.get("results", []) or []):
            artwork = entry.get("artworkUrl100", "") or ""
            candidates.append(ReleaseCandidate(
                id=str(entry.get("collectionId", "")), title=entry.get("collectionName", ""),
                artist=entry.get("artistName", ""), date=(entry.get("releaseDate", "") or "")[:10],
                country=entry.get("country", "") or "", track_count=int(entry.get("trackCount", 0) or 0),
                formats="", status="", mb_score=_rank_score(index), service=self.service,
                cover_url=artwork.replace("100x100bb", "600x600bb"), url=entry.get("collectionViewUrl", "") or ""))
        return candidates

    def get_expected_tracks(self, release: ReleaseCandidate) -> list:
        data = self._get(APPLE_API_ROOT + "lookup", {"id": release.id, "entity": "song", "limit": 200,
                                                     "country": self.country})
        rows = []
        for entry in data.get("results", []) or []:
            if entry.get("wrapperType") == "track":
                rows.append((int(entry.get("discNumber", 1) or 1), int(entry.get("trackNumber", 0) or 0),
                             entry.get("trackName", ""), int(entry.get("trackTimeMillis", 0) or 0)))
        rows.sort(key=lambda row: (row[0], row[1]))
        result = _numbered_tracks(rows)
        return result


def _discogs_position(position: str, sequence: int) -> tuple:
    """(disco, numero) da una posizione di Discogs: "1-03", "CD2-5", "2.04", "7" o "A1" (lato di un vinile: un disco
    solo, numerato in ordine)."""
    text = position.strip()
    found = re.match(r"^(?:CD|DVD|Disc|Disco)?\s*(\d+)\s*[-.]\s*(\d+)$", text, re.IGNORECASE)
    if found:
        result = (int(found.group(1)), int(found.group(2)))
    elif text.isdigit():
        result = (1, int(text))
    else:
        result = (1, sequence)
    return result


def _discogs_length(text: str) -> int:
    parts = (text or "").split(":")
    seconds = 0
    for part in parts:
        seconds = seconds * 60 + (int(part) if part.strip().isdigit() else 0)
    result = seconds * 1000
    return result


class DiscogsClient(_ServiceClient):
    service = SERVICE_DISCOGS
    label = "Discogs"
    min_interval = 1.1        # 60 richieste al minuto con il token

    def _token(self) -> str:
        result = os.environ.get("DISCOGS_TOKEN", "").strip()     # DISCOGS_TOKEN_VAR
        return result

    def available(self) -> bool:
        result = bool(self._token())
        return result

    def _headers(self) -> dict:
        result = {}
        token = self._token()
        if token:
            result["Authorization"] = f"Discogs token={token}"
        return result

    def search_releases(self, artist: str, album: str, limit: int = 15) -> list:
        if not self.available():
            raise AlbumCheckError(f"Discogs vuole un token personale: la variabile {DISCOGS_TOKEN_VAR} non è impostata")
        params = {"type": "release", "release_title": album, "per_page": limit}
        if artist and artist != UNKNOWN_ARTIST:
            params["artist"] = artist
        data = self._get(DISCOGS_API_ROOT + "database/search", params)
        candidates = []
        for index, entry in enumerate(data.get("results", []) or []):
            title = entry.get("title", "") or ""
            found_artist, _sep, found_album = title.partition(" - ")
            candidates.append(ReleaseCandidate(
                id=str(entry.get("id", "")), title=found_album or title, artist=found_artist if found_album else "",
                date=str(entry.get("year", "") or ""), country=entry.get("country", "") or "", track_count=0,
                formats=" + ".join(entry.get("format", []) or []), status="", mb_score=_rank_score(index),
                service=self.service, cover_url=entry.get("cover_image", "") or "",
                url=f"https://www.discogs.com/release/{entry.get('id', '')}"))
        return candidates

    def get_expected_tracks(self, release: ReleaseCandidate) -> list:
        data = self._get(DISCOGS_API_ROOT + f"releases/{release.id}", {})
        rows = []
        sequence = 0
        for entry in data.get("tracklist", []) or []:
            kind = entry.get("type_", "track")
            if kind == "track" or (kind == "index" and entry.get("title")):
                sequence += 1
                disc, number = _discogs_position(entry.get("position", "") or "", sequence)
                rows.append((disc, number, entry.get("title", ""), _discogs_length(entry.get("duration", ""))))
        result = _numbered_tracks(rows)
        return result


class MusicBrainzClient(_ServiceClient):
    """MusicBrainz (niente header Accept: risponde 503 a "Accept: application/json", basta fmt=json)."""

    service = SERVICE_MUSICBRAINZ
    label = "MusicBrainz"
    min_interval = MIN_INTERVAL

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
                service=self.service,
                url=f"https://musicbrainz.org/release/{release['id']}",
            ))
        return candidates

    def get_expected_tracks(self, release) -> list:
        release_id = release.id if isinstance(release, ReleaseCandidate) else str(release)
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

    def fetch_cover(self, release: ReleaseCandidate) -> Optional[bytes]:
        """Copertina dell'edizione; se manca, quella generica dell'album (release group)."""
        result = self._download_cover(COVER_ROOT + f"release/{release.id}/front-500")
        if result is None and release.release_group_id:
            result = self._download_cover(COVER_ROOT + f"release-group/{release.release_group_id}/front-500")
        return result

    def release_url(self, release: ReleaseCandidate) -> str:
        result = f"https://musicbrainz.org/release/{release.id}"
        return result


def make_clients() -> dict:
    """{servizio: client} di tutti i cataloghi."""
    result = {SERVICE_DEEZER: DeezerClient(), SERVICE_APPLE: AppleClient(), SERVICE_DISCOGS: DiscogsClient(),
              SERVICE_MUSICBRAINZ: MusicBrainzClient()}
    return result


# --------------------------------------------------------------------------- logica di verifica

def expected_track_count(local_tracks: list) -> int:
    result = len(local_tracks)
    for track in local_tracks:
        result = max(result, track.tags.track_number or 0, track.tags.track_total or 0)
    return result


def choose_release(candidates: list, album: str, local_tracks: list) -> Optional[ReleaseCandidate]:
    """Sceglie l'edizione più probabile in base a punteggio, titolo e numero di tracce."""
    best = None
    best_score = None
    for candidate in candidates:
        score = _release_score(candidate, album, local_tracks)
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


def check_album(client, local_tracks: list,
                candidates: Optional[list] = None,
                chosen: Optional[ReleaseCandidate] = None, chooser=None) -> AlbumCheckResult:
    """Verifica un album su un catalogo. candidates/chosen permettono di ricalcolare con un'altra edizione.
    chooser(album, artista, brani, candidati) -> (candidato, motivo) o None: sceglie tra edizioni dubbie (l'AI)."""
    artist, album = local_tracks[0].album_key
    result = AlbumCheckResult(artist=artist, album=album, local_tracks=list(local_tracks), service=client.service,
                              service_label=client.label)
    if album == UNKNOWN_ALBUM:
        result.error = "l'album non ha un nome: compila il tag Album"
    else:
        try:
            if candidates is None:
                candidates = client.search_releases(artist, album)
            result.candidates = candidates
            if chosen is None:
                chosen = choose_release(candidates, album, local_tracks)
                if chosen is not None and chooser is not None and _doubtful(candidates, album, local_tracks):
                    picked = chooser(album, artist, local_tracks, candidates)
                    if picked is not None:
                        chosen, result.ai_reason = picked
            if chosen is not None:
                expected = client.get_expected_tracks(chosen)
                result.release = chosen
                result.matches, result.extra = match_tracks(expected, local_tracks)
        except AlbumCheckError as exc:
            result.error = str(exc)
    return result


def _release_score(candidate: ReleaseCandidate, album: str, local_tracks: list) -> float:
    wanted = expected_track_count(local_tracks)
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
    return score


def _doubtful(candidates: list, album: str, local_tracks: list) -> bool:
    """Le due edizioni migliori hanno punteggi vicini: un dubbio."""
    scores = []
    for candidate in candidates:
        scores.append(_release_score(candidate, album, local_tracks))
    scores.sort(reverse=True)
    result = len(scores) > 1 and scores[0] - scores[1] < CLOSE_EDITIONS
    return result


def _rank(result: AlbumCheckResult) -> tuple:
    """Più alto = migliore: completo, poi incompleto con meno tracce mancanti, poi non trovato, poi errore."""
    status = result.status
    if status == STATUS_COMPLETE:
        value = (3, 0)
    elif status == STATUS_INCOMPLETE:
        value = (2, -len(result.missing))
    elif status == STATUS_NOT_FOUND:
        value = (1, 0)
    else:
        value = (0, 0)
    return value


def check_album_services(clients: list, local_tracks: list, chooser=None) -> AlbumCheckResult:
    """Verifica un album provando i cataloghi in ordine finché uno lo dà completo; altrimenti il risultato migliore.
    Il risultato dice quali servizi sono stati provati e con che esito (tried)."""
    best = None
    tried = []
    index = 0
    while index < len(clients) and (best is None or best.status != STATUS_COMPLETE):
        client = clients[index]
        result = check_album(client, local_tracks, chooser=chooser)
        tried.append((client.label, result.status_text()))
        if best is None or _rank(result) > _rank(best):
            best = result
        index += 1
    if best is not None:
        best.tried = tried
    return best


AI_EDITION_SYSTEM = """You help check that a music album on the owner's PC is complete. You get the album as it is on the PC (artist, title, number of files and their titles) and a few editions found in an online catalog. Choose the edition that matches the files best: same track list, same number of tracks, the normal edition rather than a deluxe or a compilation unless the files say otherwise. Answer with its id, or "" if none fits. Write the reason in Italian, short."""

AI_EDITION_SCHEMA = {
    "type": "object",
    "properties": {"choice": {"type": "string"}, "reason": {"type": "string"}},
    "required": ["choice", "reason"],
    "additionalProperties": False,
}


def ai_chooser(provider):
    """Un chooser per check_album: l'AI sceglie tra le prime edizioni (solo quando sono dubbie)."""
    from .ai import AIError

    def choose(album: str, artist: str, local_tracks: list, candidates: list):
        lines = [f"PC: {artist} - {album}, {len(local_tracks)} files:"]
        for track in local_tracks[:40]:
            lines.append(f"  {track.tags.track_number or '?'}. {track.title}")
        options = {}
        for index, candidate in enumerate(candidates[:6], start=1):
            key = f"E{index}"
            options[key] = candidate
            lines.append(f"{key} | {candidate.label()}")
        picked = None
        try:
            reply = provider.ask_json(AI_EDITION_SYSTEM, "\n".join(lines), AI_EDITION_SCHEMA)
            chosen = options.get(str(reply.get("choice", "")))
            if chosen is not None:
                picked = (chosen, f"AI: {str(reply.get('reason', '')).strip()}")
        except AIError:
            picked = None
        return picked

    return choose


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
