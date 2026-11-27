# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La musica dell'app Musica dell'iPhone, com'è nell'app: titoli, artisti e album vengono dal suo database
(/iTunes_Control/iTunes/MediaLibrary.sqlitedb), non dai file, che sull'iPhone hanno nomi casuali (F12/ABCD.mp3).

Qui: la lettura di una COPIA del database (iphone.list_music_app la scarica), l'elenco salvato nella cartella dati
(per la colonna "iPhone" anche a telefono scollegato) e il confronto con i brani del PC per artista, album e titolo.
Il database dell'iPhone non si scrive mai."""

from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Optional

from .library import Track, group_name, phone_group_key, target_relative_path
from .tags import TrackTags

DATABASE_NAME = "MediaLibrary.sqlitedb"
LISTING_FILE = "iphone_musica.json"
LISTING_VERSION = 1
TAG_FIELD_NAMES = {field.name for field in fields(TrackTags)}

DEVICE_SAME = "same"      # c'è, con gli stessi tag
DEVICE_STALE = "stale"    # c'è, ma i tag sono diversi
DEVICE_ABSENT = ""        # non c'è

# i campi confrontati tra PC e iPhone, con il nome mostrato
COMPARED_FIELDS = (("title", "Titolo"), ("artist", "Artista"), ("album_artist", "Artista album"), ("album", "Album"),
                   ("year", "Anno"), ("genre", "Genere"), ("track_number", "N. traccia"), ("disc_number", "N. disco"),
                   ("compilation", "Compilation"))

_QUERY = """
SELECT i.item_pid, e.title, ia.item_artist, aa.album_artist, a.album, g.genre, e.year, i.track_number,
       e.track_count, i.disc_number, e.disc_count, e.total_time_ms, e.location, e.file_size, b.path,
       s.sync_id, a.sync_id, aa.sync_id, i.is_compilation
FROM item i
JOIN item_extra e ON e.item_pid = i.item_pid
LEFT JOIN item_store s ON s.item_pid = i.item_pid
LEFT JOIN item_artist ia ON ia.item_artist_pid = i.item_artist_pid
LEFT JOIN album_artist aa ON aa.album_artist_pid = i.album_artist_pid
LEFT JOIN album a ON a.album_pid = i.album_pid
LEFT JOIN genre g ON g.genre_id = i.genre_id
LEFT JOIN base_location b ON b.base_location_id = i.base_location_id
WHERE e.location IS NOT NULL AND e.location != '' AND b.path IS NOT NULL AND b.path != ''
"""

# gli album (sync_id) senza l'immagine dell'album: nessuna riga best_artwork_token dell'album (entity_type 4) con
# un'immagine. Succede agli album messi da altri programmi anche se i brani hanno la copertina (24/11/2026: 59 album
# su 234, nessuno di quelli inviati da qui); un rimpiazzo dal PC la fa scegliere all'iPhone
_COVERLESS_ALBUM_QUERY = """
SELECT a.sync_id FROM album a
WHERE NOT EXISTS (SELECT 1 FROM best_artwork_token b
                  WHERE b.entity_pid = a.album_pid AND b.entity_type = 4
                        AND COALESCE(b.available_artwork_token, '') != '')
"""

# i brani che stanno nella riga di un album con un altro artista dell'album: l'app Musica mostra l'album con
# l'artista della riga, il programma con quello del brano. Succede quando l'artista dell'album di un brano è cambiato
# sul posto: il brano resta nell'album vecchio (26/11/2026: 26 brani in 3 album, uno doppio "AA.VV." / "Artisti Vari"
# con lo stesso sync_id). Una Ricopia lo rimette nell'album giusto.
_MISFILED_QUERY = """
SELECT i.item_pid, aa.album_artist
FROM item i
JOIN album a ON a.album_pid = i.album_pid
LEFT JOIN album_artist aa ON aa.album_artist_pid = a.album_artist_pid
WHERE a.album_artist_pid IS NOT NULL AND a.album_artist_pid != 0 AND i.album_artist_pid != a.album_artist_pid
"""

# le playlist normali: non la libreria (nascosta), non le smart (si aggiornano da sole), non le cartelle
_PLAYLIST_QUERY = """
SELECT ci.item_pid, c.name, c.sync_id
FROM container_item ci
JOIN container c ON c.container_pid = ci.container_pid
WHERE c.distinguished_kind = 0 AND c.is_hidden = 0 AND c.smart_criteria IS NULL AND c.smart_is_folder = 0
      AND c.name != ''
ORDER BY c.name, ci.position
"""


# le stesse playlist normali, con il loro sync_id: diverso da 0 se le ha messe un computer (solo quelle un computer
# può cancellare); 0 se fatte sul telefono (rustunes, docs/05)
_CONTAINER_QUERY = """
SELECT c.container_pid, c.sync_id, c.name, COUNT(ci.item_pid)
FROM container c
LEFT JOIN container_item ci ON ci.container_pid = c.container_pid
WHERE c.distinguished_kind = 0 AND c.is_hidden = 0 AND c.smart_criteria IS NULL AND c.smart_is_folder = 0
GROUP BY c.container_pid
ORDER BY c.name
"""

# i brani (sync_id) delle playlist normali, nell'ordine della playlist
_MEMBERS_QUERY = """
SELECT ci.container_pid, s.sync_id
FROM container_item ci
JOIN container c ON c.container_pid = ci.container_pid
JOIN item_store s ON s.item_pid = ci.item_pid
WHERE c.distinguished_kind = 0 AND c.is_hidden = 0 AND c.smart_criteria IS NULL AND c.smart_is_folder = 0
ORDER BY ci.container_pid, ci.position
"""


@dataclass
class PhonePlaylist:
    pid: int                  # container_pid nel database dell'iPhone
    sync_id: int              # 0: fatta sul telefono
    name: str
    count: int                # brani

    @property
    def from_computer(self) -> bool:
        result = self.sync_id != 0
        return result


class PhoneLibraryError(Exception):
    """Il database dell'app Musica non si legge (versione di iOS diversa, copia incompleta…)."""


@dataclass
class PhoneTrack:
    pid: int              # l'identificativo interno del brano nel database dell'iPhone
    remote_path: str      # il file sull'iPhone: /iTunes_Control/Music/F12/ABCD.mp3
    size: int
    length: float         # secondi
    tags: TrackTags
    sync_id: int = 0      # l'identificativo con cui un computer lo aggiorna o lo elimina (0: non messo da un computer)
    album_sync_id: int = 0
    artist_sync_id: int = 0   # dell'artista dell'album
    playlists: tuple = ()     # le playlist fatte a mano che lo contengono (non le smart)
    computer_playlists: tuple = ()   # quelle tra loro messe da un computer: dopo un rimpiazzo si rifanno da sole
    missing_file: bool = False   # "fantasma": nel database dell'app Musica, ma il suo file sull'iPhone non c'è
    album_without_cover: bool = False   # il suo album sull'iPhone non ha l'immagine (_COVERLESS_ALBUM_QUERY)
    # l'artista dell'album con cui l'app Musica mostra il suo album, quando è diverso da quello del brano
    # (_MISFILED_QUERY); "" se coincidono
    album_row_artist: str = ""

    @property
    def misfiled(self) -> bool:
        """Sta in un album che l'app Musica mostra con un altro artista dell'album: una Ricopia lo sistema."""
        result = bool(self.album_row_artist)
        return result

    @property
    def from_computer(self) -> bool:
        """Messo sull'iPhone da un computer (iTunes, CopyTrans, questo programma): solo questi si aggiornano."""
        result = self.sync_id != 0
        return result

    @property
    def display_artist(self) -> str:
        result = self.tags.album_artist or self.tags.artist
        return result

    def as_track(self) -> Track:
        """Un brano per la scansione e per "Salva su PC", con i tag che mostra l'app Musica."""
        result = Track(path=Path(self.remote_path), tags=self.tags.copy(), length=self.length)
        return result


def _text(value) -> str:
    result = str(value).strip() if value is not None else ""
    return result


def _number(value) -> Optional[int]:
    """I numeri del database: 0 vuol dire che il tag manca."""
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        number = 0
    result = number if number > 0 else None
    return result


def _unsigned(value) -> int:
    """Gli identificativi a 64 bit, che SQLite tiene con il segno."""
    result = int(value or 0) & 0xFFFFFFFFFFFFFFFF
    return result


def _of_computer(names, from_computer: set) -> tuple:
    """Le playlist tra names messe da un computer."""
    found = []
    for name in names:
        if name in from_computer:
            found.append(name)
    result = tuple(found)
    return result


def read_music_database(path: Path) -> list:
    """I brani con un file sull'iPhone (non quelli solo in streaming), dalla copia del database in path. Se accanto
    c'è il file -wal, SQLite ne legge anche le ultime modifiche."""
    tracks = []
    try:
        connection = sqlite3.connect(str(path))
        try:
            rows = connection.execute(_QUERY).fetchall()
            try:
                playlist_rows = connection.execute(_PLAYLIST_QUERY).fetchall()
            except sqlite3.Error:
                try:                    # senza sync_id delle playlist: tutte come fatte sul telefono
                    playlist_rows = connection.execute(_PLAYLIST_QUERY.replace(", c.sync_id", ", 0")).fetchall()
                except sqlite3.Error:
                    playlist_rows = []  # senza le playlist si va avanti: servono solo come promemoria
            coverless = set()
            try:
                for (album_sync_id,) in connection.execute(_COVERLESS_ALBUM_QUERY):
                    if album_sync_id:
                        coverless.add(_unsigned(album_sync_id))
            except sqlite3.Error:
                coverless = set()       # tabella diversa (un altro iOS): nessun album segnato
            misfiled = {}
            try:
                for item_pid, row_artist in connection.execute(_MISFILED_QUERY):
                    misfiled[int(item_pid)] = _text(row_artist) or "?"
            except sqlite3.Error:
                misfiled = {}           # tabella diversa (un altro iOS): nessun brano segnato
        finally:
            connection.close()
    except sqlite3.Error as exc:
        raise PhoneLibraryError(f"il database dell'app Musica non si legge ({exc})") from exc
    playlists = {}
    from_computer = set()
    for item_pid, name, container_sync_id in playlist_rows:
        names = playlists.setdefault(int(item_pid), [])
        if _text(name) not in names:
            names.append(_text(name))
        if _unsigned(container_sync_id):
            from_computer.add(_text(name))
    for (pid, title, artist, album_artist, album, genre, year, track_number, track_count, disc_number, disc_count,
         total_ms, location, file_size, base, sync_id, album_sync_id, artist_sync_id, compilation) in rows:
        year_number = _number(year)
        tags = TrackTags(title=_text(title), artist=_text(artist), album_artist=_text(album_artist),
                         album=_text(album), track_number=_number(track_number), track_total=_number(track_count),
                         disc_number=_number(disc_number), disc_total=_number(disc_count),
                         year=str(year_number) if year_number else "", genre=_text(genre),
                         compilation=bool(compilation))
        remote = "/" + _text(base).strip("/") + "/" + _text(location)
        tracks.append(PhoneTrack(pid=int(pid), remote_path=remote, size=int(file_size or 0),
                                 length=(_number(total_ms) or 0) / 1000.0, tags=tags, sync_id=_unsigned(sync_id),
                                 album_sync_id=_unsigned(album_sync_id), artist_sync_id=_unsigned(artist_sync_id),
                                 playlists=tuple(playlists.get(int(pid), ())),
                                 computer_playlists=_of_computer(playlists.get(int(pid), ()), from_computer),
                                 album_without_cover=_unsigned(album_sync_id) in coverless,
                                 album_row_artist=misfiled.get(int(pid), "")))
    tracks.sort(key=lambda item: (group_name(item.display_artist), group_name(item.tags.album),
                                  item.tags.disc_number or 1, item.tags.track_number or 9999,
                                  group_name(item.tags.title)))
    return tracks


def read_playlists(path: Path) -> list:
    """Le playlist normali dell'iPhone (PhonePlaylist: non la libreria, non le smart, non le cartelle), dalla copia del
    database in path; mai la playlist principale della libreria (db_info)."""
    try:
        connection = sqlite3.connect(str(path))
        try:
            rows = connection.execute(_CONTAINER_QUERY).fetchall()
            primary = set()
            for (value,) in connection.execute("SELECT primary_container_pid FROM db_info"):
                primary.add(_unsigned(value))
        finally:
            connection.close()
    except sqlite3.Error as exc:
        raise PhoneLibraryError(f"le playlist dell'app Musica non si leggono ({exc})") from exc
    result = []
    for pid, sync_id, name, count in rows:
        if _unsigned(pid) not in primary and _text(name):
            result.append(PhonePlaylist(pid=_unsigned(pid), sync_id=_unsigned(sync_id), name=_text(name),
                                        count=int(count or 0)))
    return result


def playlist_members(path: Path) -> list:
    """[(PhonePlaylist, [sync_id dei brani, nell'ordine])] delle playlist normali, dalla copia del database in path."""
    playlists = read_playlists(path)
    members = {}
    try:
        connection = sqlite3.connect(str(path))
        try:
            for container_pid, sync_id in connection.execute(_MEMBERS_QUERY):
                if _unsigned(sync_id):
                    members.setdefault(_unsigned(container_pid), []).append(_unsigned(sync_id))
        finally:
            connection.close()
    except sqlite3.Error as exc:
        raise PhoneLibraryError(f"le playlist dell'app Musica non si leggono ({exc})") from exc
    result = []
    for playlist in playlists:
        result.append((playlist, members.get(playlist.pid, [])))
    return result


def container_ids(path: Path) -> set:
    """Tutti gli identificativi delle playlist dell'iPhone (container_pid e sync_id): uno nuovo non deve essere tra
    questi."""
    result = set()
    try:
        connection = sqlite3.connect(str(path))
        try:
            for pid, sync_id in connection.execute("SELECT container_pid, sync_id FROM container"):
                result.add(_unsigned(pid))
                result.add(_unsigned(sync_id))
        finally:
            connection.close()
    except sqlite3.Error as exc:
        raise PhoneLibraryError(f"le playlist dell'app Musica non si leggono ({exc})") from exc
    return result


# --------------------------------------------------------------------------- elenco nella cartella dati

def save_listing(home: Path, device: str, tracks: list) -> None:
    rows = []
    playlists = {}
    from_computer = set()
    missing = []
    coverless = []
    misfiled = {}
    for item in tracks:
        rows.append([item.pid, item.remote_path, item.size, item.length, asdict(item.tags), item.sync_id,
                     item.album_sync_id, item.artist_sync_id])
        if item.playlists:
            playlists[str(item.pid)] = list(item.playlists)
        from_computer.update(item.computer_playlists)
        if item.missing_file:
            missing.append(item.pid)
        if item.album_without_cover:
            coverless.append(item.pid)
        if item.album_row_artist:
            misfiled[str(item.pid)] = item.album_row_artist
    # playlist, fantasmi, album senza immagine e brani nell'album sbagliato a parte: le righe restano quelle che le
    # versioni precedenti sanno leggere
    data = {"version": LISTING_VERSION, "device": device, "saved_at": time.strftime("%Y-%m-%d %H:%M"),
            "tracks": rows, "playlists": playlists, "computer_playlists": sorted(from_computer),
            "missing_files": missing, "albums_without_cover": coverless, "album_row_artists": misfiled}
    home.mkdir(parents=True, exist_ok=True)
    path = home / LISTING_FILE
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)


def load_listing(home: Path) -> dict:
    """{"device", "saved_at", "tracks": [PhoneTrack]}; vuoto se manca o non è leggibile."""
    result = {}
    try:
        data = json.loads((home / LISTING_FILE).read_text(encoding="utf-8"))
        if data.get("version") == LISTING_VERSION:
            tracks = []
            playlists = data.get("playlists") or {}
            from_computer = set()
            for name in data.get("computer_playlists") or []:
                from_computer.add(str(name))
            missing = set()
            for pid in data.get("missing_files") or []:
                missing.add(int(pid))
            coverless = set()
            for pid in data.get("albums_without_cover") or []:
                coverless.add(int(pid))
            misfiled = data.get("album_row_artists") or {}
            for pid, remote, size, length, values, sync_id, album_sync_id, artist_sync_id in data.get("tracks", []):
                known = {}
                for name, value in values.items():
                    if name in TAG_FIELD_NAMES:
                        known[name] = value
                names = []
                for name in playlists.get(str(pid), []):
                    names.append(str(name))
                tracks.append(PhoneTrack(pid=int(pid), remote_path=str(remote), size=int(size),
                                         length=float(length), tags=TrackTags(**known), sync_id=int(sync_id),
                                         album_sync_id=int(album_sync_id), artist_sync_id=int(artist_sync_id),
                                         playlists=tuple(names),
                                         computer_playlists=_of_computer(names, from_computer),
                                         missing_file=int(pid) in missing,
                                         album_without_cover=int(pid) in coverless,
                                         album_row_artist=str(misfiled.get(str(pid), ""))))
            result = {"device": str(data.get("device", "")), "saved_at": str(data.get("saved_at", "")),
                      "tracks": tracks}
    except (OSError, ValueError, TypeError, AttributeError):
        result = {}
    return result


# --------------------------------------------------------------------------- confronto con il PC

def _match_key(tags: TrackTags) -> tuple:
    result = (group_name(tags.title), phone_group_key(tags.album))
    return result


def _artist_names(tags: TrackTags) -> set:
    names = set()
    for value in (tags.artist, tags.album_artist):
        if value:
            names.add(phone_group_key(value))
    return names


class PhoneIndex:
    """I brani dell'iPhone, per ritrovare quello di un brano del PC. Prima il registro della provenienza (links:
    {overlay.path_key del file: sync_id}, i collegamenti di questo PC): quel file è quel brano. Poi, per i brani non
    collegati, stesso titolo e album (senza differenze di maiuscole, accenti e spazi) e un artista in comune: un
    brano collegato a un file non si abbina per tag a un altro (un doppione sul PC non lo "ruba")."""

    def __init__(self, tracks: list, links: Optional[dict] = None) -> None:
        self.tracks = list(tracks)
        by_sync = {}
        for item in self.tracks:
            if item.sync_id:
                by_sync[item.sync_id] = item
        self._by_path = {}
        linked = set()
        for key, sync_id in (links or {}).items():
            item = by_sync.get(sync_id)
            if item is not None:
                self._by_path[key] = item
                linked.add(item.pid)
        self._by_key = {}
        for item in self.tracks:
            if item.pid not in linked:
                self._by_key.setdefault(_match_key(item.tags), []).append(item)

    def __len__(self) -> int:
        result = len(self.tracks)
        return result

    def _lookup(self, tags: TrackTags) -> Optional[PhoneTrack]:
        result = None
        wanted = _artist_names(tags)
        for item in self._by_key.get(_match_key(tags), []):
            phone_artists = _artist_names(item.tags)
            if result is None and (not phone_artists or not wanted or phone_artists & wanted):
                result = item
        return result

    def via_registry(self, track: Track) -> bool:
        """True se il brano del PC è abbinato dal registro della provenienza (certo), non solo per tag."""
        from .overlay import path_key
        result = bool(self._by_path) and path_key(track.path) in self._by_path
        return result

    def find(self, track: Track) -> Optional[PhoneTrack]:
        """Il brano sull'iPhone: quello collegato al file nel registro; altrimenti cercato con i tag mostrati e, se
        diversi, con quelli del file (prima di una modifica in sospeso)."""
        from .overlay import path_key
        result = self._by_path.get(path_key(track.path)) if self._by_path else None
        if result is None:
            result = self._lookup(track.tags)
        if result is None and track.original_tags is not None:
            result = self._lookup(track.original_tags)
        return result


def _comparable(name: str, tags: TrackTags):
    value = getattr(tags, name)
    if name == "album_artist":
        result = (tags.album_artist or tags.artist).strip()
    elif name == "year":
        result = (value or "").strip()[:4]
    elif name == "disc_number":
        result = value or 1
    elif isinstance(value, str):
        result = value.strip()
    else:
        result = value
    return result


def _shown(name: str, value) -> str:
    """Un valore confrontato, come si mostra: "" per un tag vuoto, sì/no per la compilation."""
    if name == "compilation":
        result = "sì" if value else "no"
    elif value is None:
        result = ""
    else:
        result = str(value)
    return result


def comparison(pc_tags: TrackTags, phone_tags: TrackTags) -> list:
    """(nome del campo, valore sul PC, valore sull'iPhone, diverso) per ogni campo confrontato. "Artista album" si
    confronta solo se almeno uno dei due ce l'ha (altrimenti ripete la differenza dell'artista). Due testi diversi
    solo per le maiuscole sono uguali (scelta dell'utente, 27/11/2026: l'iPhone resta com'è, se serve si ricopia a
    mano). Il resto si confronta com'è scritto, anche artisti e album: un'altra grafia (zeri, accenti, spazi:
    spelling_differences) è una differenza, che l'aggiornamento dal PC corregge reinviando l'album intero
    (phone_actions.align_spelling), perché l'iPhone tiene la grafia del suo gruppo finché esiste."""
    result = []
    for name, label in COMPARED_FIELDS:
        pc_value = _comparable(name, pc_tags)
        phone_value = _comparable(name, phone_tags)
        relevant = name != "album_artist" or bool(pc_tags.album_artist or phone_tags.album_artist)
        if isinstance(pc_value, str) and isinstance(phone_value, str):
            same = pc_value.casefold() == phone_value.casefold()
        else:
            same = pc_value == phone_value
        if relevant:
            result.append((label, _shown(name, pc_value), _shown(name, phone_value), not same))
    return result


def spelling_differences(pc_tags: TrackTags, phone_tags: TrackTags) -> list:
    """"album" e/o "album_artist" quando il PC e l'iPhone li scrivono in modo diverso ma l'iPhone li considera
    uguali (phone_group_key: maiuscole, accenti, spazi, zeri). L'artista dell'album è quello effettivo:
    l'artista dell'album o, senza, quello del brano. comparison non li segnala: un invio non li corregge, perché
    l'iPhone tiene la grafia che ha già finché l'album o l'artista esiste, anche vuoto (prove del 24/11/2026). Le sole
    maiuscole non contano (come in comparison): per quelle l'album non si ricopia."""
    result = []
    pc_album = pc_tags.album or ""
    phone_album = phone_tags.album or ""
    if pc_album.casefold() != phone_album.casefold() and phone_group_key(pc_album) == phone_group_key(phone_album):
        result.append("album")
    pc_artist = pc_tags.album_artist or pc_tags.artist or ""
    phone_artist = phone_tags.album_artist or phone_tags.artist or ""
    if pc_artist.casefold() != phone_artist.casefold() and phone_group_key(pc_artist) == phone_group_key(phone_artist):
        result.append("album_artist")
    return result


SAME_SONG_SECONDS = 2.0       # due brani con lo stesso artista e titolo sono la stessa canzone se la durata è questa


def _song_key(tags: TrackTags) -> tuple:
    result = (group_name(tags.artist or tags.album_artist or ""), group_name(tags.title or ""))
    return result


def _same_length(first: float, second: float) -> bool:
    """Durate uguali entro SAME_SONG_SECONDS; una durata che non si conosce (0) non esclude niente."""
    result = not first or not second or abs(first - second) <= SAME_SONG_SECONDS
    return result


def format_duplicates(sends: list, phone_tracks: list, preferred: tuple = ()) -> tuple:
    """Prima di un invio: ([(Track, motivo)] dei brani che sono la stessa canzone di una già sull'iPhone o di un altro
    brano dello stesso invio, ma in un altro formato (stesso artista, stesso titolo, durata entro SAME_SONG_SECONDS,
    estensione diversa), [Track] da inviare senza quelli). Tra due copie nello stesso invio si tiene quella della
    prima cartella preferita (library.preference), poi il percorso più corto. Lo stesso brano nello stesso formato
    (un'altra raccolta) non conta."""
    from .library import preference
    on_phone = {}
    for item in phone_tracks:
        on_phone.setdefault(_song_key(item.tags), []).append((Path(item.remote_path).suffix.lower(), item.length))
    groups = {}
    for track in sends:
        groups.setdefault(_song_key(track.tags), []).append(track)
    duplicates = []
    dropped = set()
    for key, tracks in groups.items():
        ordered = sorted(tracks, key=lambda track: (preference(track.path, preferred), len(str(track.path))))
        kept = []
        for track in ordered:
            suffix = track.path.suffix.lower()
            reason = ""
            for phone_suffix, length in on_phone.get(key, []):
                if not reason and phone_suffix != suffix and _same_length(length, track.length):
                    reason = f"c'è già sull'iPhone in {phone_suffix[1:].upper()}"
            for other in kept:
                if not reason and other.path.suffix.lower() != suffix and _same_length(other.length, track.length):
                    reason = f"nello stesso invio c'è anche in {other.path.suffix[1:].upper()}: {other.path.parent.name}"
            if reason:
                duplicates.append((track, reason))
                dropped.add(id(track))
            else:
                kept.append(track)
    remaining = []
    for track in sends:
        if id(track) not in dropped:
            remaining.append(track)
    result = (duplicates, remaining)
    return result


def changed_fields(pc_tags: TrackTags, phone_tags: TrackTags) -> list:
    """I nomi dei campi (COMPARED_FIELDS) diversi tra il PC e l'iPhone, con le regole di comparison."""
    labels = {}
    for name, label in COMPARED_FIELDS:
        labels[label] = name
    result = []
    for label, _pc_value, _phone_value, differs in comparison(pc_tags, phone_tags):
        if differs:
            result.append(labels[label])
    return result


def playlist_reminder(phone_tracks: list, from_computer: bool = False) -> str:
    """Le playlist dell'iPhone che contengono i brani da rimpiazzare, una riga per playlist: quelle fatte sul telefono
    (da sistemare a mano: il computer non le può cambiare) o, con from_computer, quelle messe da un computer (si
    rifanno da sole con i brani nuovi, phone_actions)."""
    by_playlist = {}
    for item in phone_tracks:
        for name in item.playlists:
            if (name in item.computer_playlists) == from_computer:
                by_playlist.setdefault(name, []).append(item.tags.title or "?")
    lines = []
    for name in sorted(by_playlist, key=str.lower):
        titles = by_playlist[name]
        shown = ", ".join(titles[:6]) + (f" e altri {len(titles) - 6}" if len(titles) > 6 else "")
        lines.append(f"• {name}: {shown}")
    result = "\n".join(lines)
    return result


def differences(pc_tags: TrackTags, phone_tags: TrackTags) -> list:
    """(nome del campo, valore sul PC, valore sull'iPhone) per ogni campo diverso (vedi comparison)."""
    result = []
    for label, pc_value, phone_value, differs in comparison(pc_tags, phone_tags):
        if differs:
            result.append((label, pc_value, phone_value))
    return result


def describe_differences(found: list) -> str:
    lines = []
    for label, pc_value, phone_value in found:
        lines.append(f"{label}: sul PC \"{pc_value}\", sull'iPhone \"{phone_value}\"")
    result = "\n".join(lines)
    return result


def device_status(track: Track, index: PhoneIndex) -> tuple:
    """(stato, PhoneTrack o None, differenze) del brano del PC rispetto all'iPhone."""
    item = index.find(track) if not track.error else None
    if item is None:
        result = (DEVICE_ABSENT, None, [])
    else:
        found = differences(track.tags, item.tags)
        result = (DEVICE_STALE if found else DEVICE_SAME, item, found)
    return result


def pc_matches(phone_tracks: list, pc_tracks: list, links: Optional[dict] = None) -> dict:
    """{pid del brano dell'iPhone: (stato, brano del PC, differenze, dal registro)} per i brani dell'iPhone che sono
    sul PC (links: i collegamenti del registro, come in PhoneIndex). Un abbinamento dal registro vince su uno per tag."""
    index = PhoneIndex(phone_tracks, links)
    result = {}
    for track in pc_tracks:
        status, item, found = device_status(track, index)
        if item is not None:
            via = index.via_registry(track)
            current = result.get(item.pid)
            if current is None or (via and not current[3]):
                result[item.pid] = (status, track, found, via)
    return result


def tracks_for_scan(phone_tracks: list) -> list:
    """I brani dell'iPhone come Track per la scansione, con un percorso leggibile al posto del nome casuale
    (iPhone/Artista/Album (Anno)/NN - Titolo.ext), unico anche per i brani doppi."""
    result = []
    used = set()
    for item in phone_tracks:
        track = item.as_track()
        relative = Path("iPhone") / target_relative_path(track)
        candidate = relative
        counter = 2
        while str(candidate).casefold() in used:
            candidate = relative.with_name(f"{relative.stem} ({counter}){relative.suffix}")
            counter += 1
        used.add(str(candidate).casefold())
        track.path = candidate
        result.append(track)
    return result
