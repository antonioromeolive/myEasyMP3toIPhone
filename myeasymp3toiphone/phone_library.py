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

from .library import Track, group_name, target_relative_path
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
GROUPED_FIELDS = {"artist", "album_artist", "album"}

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

# le playlist normali: non la libreria (nascosta), non le smart (si aggiornano da sole), non le cartelle
_PLAYLIST_QUERY = """
SELECT ci.item_pid, c.name
FROM container_item ci
JOIN container c ON c.container_pid = ci.container_pid
WHERE c.distinguished_kind = 0 AND c.is_hidden = 0 AND c.smart_criteria IS NULL AND c.smart_is_folder = 0
      AND c.name != ''
ORDER BY c.name, ci.position
"""


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
    missing_file: bool = False   # "fantasma": nel database dell'app Musica, ma il suo file sull'iPhone non c'è

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
                playlist_rows = []      # senza le playlist si va avanti: servono solo come promemoria
        finally:
            connection.close()
    except sqlite3.Error as exc:
        raise PhoneLibraryError(f"il database dell'app Musica non si legge ({exc})") from exc
    playlists = {}
    for item_pid, name in playlist_rows:
        names = playlists.setdefault(int(item_pid), [])
        if name not in names:
            names.append(_text(name))
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
                                 playlists=tuple(playlists.get(int(pid), ()))))
    tracks.sort(key=lambda item: (group_name(item.display_artist), group_name(item.tags.album),
                                  item.tags.disc_number or 1, item.tags.track_number or 9999,
                                  group_name(item.tags.title)))
    return tracks


# --------------------------------------------------------------------------- elenco nella cartella dati

def save_listing(home: Path, device: str, tracks: list) -> None:
    rows = []
    playlists = {}
    missing = []
    for item in tracks:
        rows.append([item.pid, item.remote_path, item.size, item.length, asdict(item.tags), item.sync_id,
                     item.album_sync_id, item.artist_sync_id])
        if item.playlists:
            playlists[str(item.pid)] = list(item.playlists)
        if item.missing_file:
            missing.append(item.pid)
    # playlist e fantasmi a parte: le righe restano quelle che le versioni precedenti sanno leggere
    data = {"version": LISTING_VERSION, "device": device, "saved_at": time.strftime("%Y-%m-%d %H:%M"),
            "tracks": rows, "playlists": playlists, "missing_files": missing}
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
            missing = set()
            for pid in data.get("missing_files") or []:
                missing.add(int(pid))
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
                                         playlists=tuple(names), missing_file=int(pid) in missing))
            result = {"device": str(data.get("device", "")), "saved_at": str(data.get("saved_at", "")),
                      "tracks": tracks}
    except (OSError, ValueError, TypeError, AttributeError):
        result = {}
    return result


# --------------------------------------------------------------------------- confronto con il PC

def _match_key(tags: TrackTags) -> tuple:
    result = (group_name(tags.title), group_name(tags.album))
    return result


def _artist_names(tags: TrackTags) -> set:
    names = set()
    for value in (tags.artist, tags.album_artist):
        if value:
            names.add(group_name(value))
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
    confronta solo se almeno uno dei due ce l'ha (altrimenti ripete la differenza dell'artista). Artisti e album si
    confrontano senza maiuscole, accenti e spazi: sull'iPhone sono gruppi, e l'invio si unisce al gruppo che c'è già con
    la sua grafia ("Artisti Vari" per "Artisti vari"), quindi quella differenza non si può né si deve correggere."""
    result = []
    for name, label in COMPARED_FIELDS:
        pc_value = _comparable(name, pc_tags)
        phone_value = _comparable(name, phone_tags)
        relevant = name != "album_artist" or bool(pc_tags.album_artist or phone_tags.album_artist)
        if name in GROUPED_FIELDS:
            same = group_name(str(pc_value)) == group_name(str(phone_value))
        else:
            same = pc_value == phone_value
        if relevant:
            result.append((label, _shown(name, pc_value), _shown(name, phone_value), not same))
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


def playlist_reminder(phone_tracks: list) -> str:
    """Le playlist dell'iPhone in cui rimettere a mano i brani (dopo un rimpiazzo): una riga per playlist."""
    by_playlist = {}
    for item in phone_tracks:
        for name in item.playlists:
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
