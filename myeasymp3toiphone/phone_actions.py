# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le azioni sull'app Musica dell'iPhone che la finestra offre: invia dal PC, rimpiazza con la versione del PC,
elimina, cambia i tag. Ogni azione è fatta di sessioni phone_sync.run_session, a gruppi; prima di ogni sessione si
scarica una copia fresca del database del telefono (identità, ancora, album e artisti già presenti).

I file del PC non si toccano: si invia una copia temporanea con le modifiche in sospeso (tags.prepare_copy).
Tutte le funzioni pubbliche sono bloccanti: vanno chiamate da un thread di lavoro."""

from __future__ import annotations

import logging
import random
import secrets
import shutil
import socket
import sqlite3
import string
import tempfile
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from . import iphone, phone_sync
from .library import UNKNOWN_ALBUM, UNKNOWN_ARTIST, group_name, is_cancelled
from .phone_sync import PhoneSyncError
from .tags import TagError, prepare_copy, read_cover

log = logging.getLogger(__name__)

BATCH_INSERTS = 25        # brani nuovi per sessione: l'audio di ognuno si carica mentre la sessione è aperta
BATCH_CHANGES = 400       # modifiche o eliminazioni per sessione (un file ne tiene al massimo 500)
DELETE_WAIT_NOTE = "L'iPhone toglie i file dei brani eliminati da solo, entro qualche minuto."

ProgressFn = Callable[[int, int, str], None]


@dataclass
class ActionReport:
    done: int = 0
    skipped: list = field(default_factory=list)   # (brano, motivo)
    errors: list = field(default_factory=list)    # (brano, messaggio)
    cancelled: bool = False
    sessions: int = 0

    def summary(self, verb: str) -> str:
        parts = [f"{self.done} brani {verb}"]
        if self.skipped:
            parts.append(f"{len(self.skipped)} saltati")
        if self.errors:
            parts.append(f"{len(self.errors)} non riusciti")
        if self.cancelled:
            parts.append("operazione annullata")
        result = ", ".join(parts)
        return result


def _now():
    result = datetime.now(timezone.utc).replace(tzinfo=None)
    return result


def _unsigned(value) -> int:
    result = int(value or 0) & 0xFFFFFFFFFFFFFFFF
    return result


class _Snapshot:
    """Una copia fresca del database dell'app Musica: quello che serve a preparare una sessione."""

    def __init__(self, folder: Path, identity, state) -> None:
        self.identity = identity
        self.state = state
        connection = sqlite3.connect(str(folder / "MediaLibrary.sqlitedb"))
        try:
            self.track_ids = self._ids(connection, "SELECT sync_id FROM item_store")
            self.album_ids = self._ids(connection, "SELECT sync_id FROM album")
            self.artist_ids = self._ids(connection, "SELECT sync_id FROM album_artist")
            self.artists = {}
            for name, sync_id in connection.execute("SELECT album_artist, sync_id FROM album_artist"):
                if name and sync_id:
                    self.artists.setdefault(group_name(str(name)), (_unsigned(sync_id), str(name)))
            self.albums = {}
            for album, artist, sync_id in connection.execute(
                    "SELECT a.album, aa.album_artist, a.sync_id FROM album a "
                    "LEFT JOIN album_artist aa ON aa.album_artist_pid = a.album_artist_pid"):
                if album and sync_id:
                    key = (group_name(str(album)), group_name(str(artist or "")))
                    self.albums.setdefault(key, (_unsigned(sync_id), str(album)))
            self.folders = []
            for (path,) in connection.execute("SELECT path FROM base_location"):
                if str(path).startswith("iTunes_Control/Music/F"):
                    self.folders.append(str(path))
            self.locations = set()
            for (location,) in connection.execute("SELECT location FROM item_extra"):
                if location:
                    self.locations.add(str(location).upper())
            # i numeri delle copertine: un nuovo numero sta sopra a tutti quelli del telefono (rustunes, docs/04 §10)
            highest = 99
            for table in ("artwork_token", "artwork"):
                for (token,) in connection.execute(f"SELECT artwork_token FROM {table}"):
                    text = str(token or "")
                    if text.isdigit() and len(text) <= 10:
                        highest = max(highest, int(text))
            self.next_cache_id = highest + 1
        finally:
            connection.close()
        self.folders.sort()
        if not self.folders:
            self.folders = ["iTunes_Control/Music/F00"]

    @staticmethod
    def _ids(connection, query: str) -> set:
        result = set()
        for (value,) in connection.execute(query):
            result.add(_unsigned(value))
        return result

    @staticmethod
    def _fresh(used: set) -> int:
        value = 0
        while value == 0 or value in used:
            value = secrets.randbits(63) | 1
        used.add(value)
        return value

    def new_track_id(self) -> int:
        result = self._fresh(self.track_ids)
        return result

    def new_album_id(self) -> int:
        result = self._fresh(self.album_ids)
        return result

    def new_artist_id(self) -> int:
        result = self._fresh(self.artist_ids)
        return result

    def new_cache_id(self) -> int:
        result = self.next_cache_id
        self.next_cache_id += 1
        return result

    def destination(self, pid: int, extension: str) -> str:
        """Fnn/ABCD.ext come le sceglie l'host di Apple: una cartella dell'iPhone e quattro lettere nuove."""
        folder = f"iTunes_Control/Music/F{pid % 50:02d}"
        if folder not in self.folders:
            folder = random.choice(self.folders)
        name = ""
        while not name or name.upper() in self.locations:
            name = "".join(random.choices(string.ascii_uppercase, k=4)) + extension
        self.locations.add(name.upper())
        result = f"{folder}/{name}"
        return result


async def _snapshot(lockdown, folder: Path) -> _Snapshot:
    from pymobiledevice3.services.afc import AfcService
    for old in folder.glob("MediaLibrary.sqlitedb*"):
        old.unlink()
    async with AfcService(lockdown) as afc:
        for name in ("MediaLibrary.sqlitedb", "MediaLibrary.sqlitedb-wal"):
            remote = "iTunes_Control/iTunes/" + name
            if await afc.exists(remote):
                (folder / name).write_bytes(await afc.get_file_contents(remote))
        prefs = await afc.get_file_contents(phone_sync.PREFS_PATH)
    identity = phone_sync.parse_prefs(prefs)
    state = phone_sync.read_catalog_state(folder / "MediaLibrary.sqlitedb")
    result = _Snapshot(folder, identity, state)
    return result


def _label(tags, fallback: str) -> str:
    result = f"{tags.album_artist or tags.artist or UNKNOWN_ARTIST} — {tags.title or fallback}"
    return result


async def _run(lockdown, snapshot: _Snapshot, operations: list, uploads: list, report: ActionReport):
    session = await phone_sync.run_session(lockdown, snapshot.identity, snapshot.state, socket.gethostname(),
                                           operations, uploads, _now())
    report.sessions += 1
    if session.declined:
        log.info("Sessione %s: %d richieste dell'iPhone rifiutate (copertine o brani di altre sessioni)",
                 session.anchor_after, len(session.declined))
    return session


# --------------------------------------------------------------------------- invio e rimpiazzo

@dataclass
class _Pending:
    track: object             # library.Track (tag con le modifiche in sospeso)
    cover: Optional[bytes]
    replaces: int = 0         # sync_id del brano dell'iPhone da togliere dopo l'invio (rimpiazzo)


async def _send_batches(pending: list, progress: Optional[ProgressFn], cancel, report: ActionReport) -> list:
    """Invia i brani a gruppi. Restituisce i _Pending inviati davvero."""
    sent = []
    work = Path(tempfile.mkdtemp(prefix="myEasyMP3toIPhone_invio_"))
    lockdown = await iphone._open_lockdown()
    try:
        start = 0
        failed = False
        while start < len(pending) and not failed and not is_cancelled(cancel):
            batch = pending[start:start + BATCH_INSERTS]
            snapshot = await _snapshot(lockdown, work)
            operations = []
            uploads = []
            included = []
            new_albums = {}
            new_artists = {}
            for index, item in enumerate(batch):
                track = item.track
                if progress is not None:
                    progress(start + index, len(pending), f"preparazione: {track.path.name}")
                try:
                    copy = work / f"{start + index}{track.path.suffix.lower()}"
                    shutil.copyfile(str(track.path), str(copy))
                    prepare_copy(copy, track.tags, item.cover)
                    audio = phone_sync.audio_info(copy)
                    tags = track.tags.copy()
                    tags.title = tags.title or track.title
                    artist_name = tags.album_artist or tags.artist or UNKNOWN_ARTIST
                    album_name = tags.album or UNKNOWN_ALBUM
                    artist_key = group_name(artist_name)
                    album_key = (group_name(album_name), artist_key)
                    if artist_key in snapshot.artists:
                        artist_pid, phone_name = snapshot.artists[artist_key]
                        if tags.album_artist:
                            tags.album_artist = phone_name   # la grafia dell'iPhone: niente artisti doppi
                    else:
                        artist_pid = new_artists.setdefault(artist_key, snapshot.new_artist_id())
                    if album_key in snapshot.albums:
                        album_pid, tags.album = snapshot.albums[album_key]
                    else:
                        album_pid = new_albums.setdefault(album_key, snapshot.new_album_id())
                    pid = snapshot.new_track_id()
                    cover = item.cover if item.cover is not None else read_cover(track.path)
                    cache_id = 0
                    checksum = 0
                    if phone_sync.is_supported_cover(cover):
                        cache_id = snapshot.new_cache_id()
                        checksum = phone_sync.cover_checksum(cover, audio.extension)
                    else:
                        cover = b""
                    operations.append(phone_sync.insert_track(pid, album_pid, artist_pid, tags, audio, cache_id,
                                                              checksum))
                    uploads.append(phone_sync.Upload(pid, copy, snapshot.destination(pid, audio.extension), cover))
                    included.append(item)
                except (PhoneSyncError, TagError, OSError) as exc:
                    report.errors.append((_label(track.tags, track.path.stem), str(exc)))
            if operations:
                if progress is not None:
                    progress(start, len(pending), f"invio all'iPhone di {len(operations)} brani")
                try:
                    await _run(lockdown, snapshot, operations, uploads, report)
                    report.done += len(included)
                    sent += included
                except PhoneSyncError as exc:
                    failed = True
                    for item in included:
                        report.errors.append((_label(item.track.tags, item.track.path.stem), str(exc)))
            for leftover in work.iterdir():
                if leftover.is_file() and not leftover.name.startswith("MediaLibrary"):
                    leftover.unlink()
            start += BATCH_INSERTS
        report.cancelled = is_cancelled(cancel)
    finally:
        await lockdown.close()
        shutil.rmtree(work, ignore_errors=True)
    return sent


async def _delete_batches(sync_ids: list, progress: Optional[ProgressFn], report: ActionReport) -> None:
    work = Path(tempfile.mkdtemp(prefix="myEasyMP3toIPhone_elimina_"))
    lockdown = await iphone._open_lockdown()
    try:
        start = 0
        failed = False
        while start < len(sync_ids) and not failed:
            batch = sync_ids[start:start + BATCH_CHANGES]
            if progress is not None:
                progress(start, len(sync_ids), f"eliminazione di {len(batch)} brani")
            snapshot = await _snapshot(lockdown, work)
            present = []
            for sync_id in batch:
                if sync_id in snapshot.track_ids:
                    present.append(sync_id)
                else:
                    report.skipped.append((f"{sync_id:016x}", "non è più sull'iPhone"))
            operations = []
            for sync_id in present:
                operations.append(phone_sync.delete_track(sync_id))
            if operations:
                try:
                    await _run(lockdown, snapshot, operations, [], report)
                    report.done += len(operations)
                except PhoneSyncError as exc:
                    failed = True
                    report.errors.append((f"{len(operations)} brani", str(exc)))
            start += BATCH_CHANGES
    finally:
        await lockdown.close()
        shutil.rmtree(work, ignore_errors=True)


def send_tracks(tracks: list, overlay, progress: Optional[ProgressFn] = None,
                cancel: Optional[threading.Event] = None) -> ActionReport:
    """I brani del PC (con le modifiche in sospeso già in track.tags) nell'app Musica dell'iPhone."""
    report = ActionReport()
    pending = []
    for track in tracks:
        if track.error:
            report.skipped.append((_label(track.tags, track.path.stem), track.error))
        else:
            pending.append(_Pending(track, overlay.cover_for(track.path) if overlay is not None else None))
    if pending:
        iphone._run(_send_batches(pending, progress, cancel, report))
    return report


def replace_tracks(pairs: list, overlay, progress: Optional[ProgressFn] = None,
                   cancel: Optional[threading.Event] = None) -> ActionReport:
    """pairs: (PhoneTrack, Track del PC). Prima si invia la versione del PC; solo per i brani inviati davvero si toglie
    la versione vecchia. Si perdono i conteggi degli ascolti e la presenza nelle playlist del brano vecchio."""
    report = ActionReport()
    pending = []
    for phone_track, track in pairs:
        if not phone_track.from_computer:
            report.skipped.append((_label(phone_track.tags, ""), "non è stato messo da un computer"))
        elif track.error:
            report.skipped.append((_label(track.tags, track.path.stem), track.error))
        else:
            cover = overlay.cover_for(track.path) if overlay is not None else None
            pending.append(_Pending(track, cover, phone_track.sync_id))

    async def work():
        sent = await _send_batches(pending, progress, cancel, report)
        old = []
        for item in sent:
            old.append(item.replaces)
        if old:
            removal = ActionReport()
            await _delete_batches(old, progress, removal)
            for name, message in removal.errors:
                report.errors.append((name, "versione vecchia non tolta: " + message))

    if pending:
        iphone._run(work())
    return report


def delete_tracks(phone_tracks: list, progress: Optional[ProgressFn] = None) -> ActionReport:
    report = ActionReport()
    sync_ids = []
    for item in phone_tracks:
        if item.from_computer:
            sync_ids.append(item.sync_id)
        else:
            report.skipped.append((_label(item.tags, ""), "non è stato messo da un computer"))
    if sync_ids:
        iphone._run(_delete_batches(sync_ids, progress, report))
    return report


# --------------------------------------------------------------------------- modifica dei tag

EDITABLE_FIELDS = ("title", "album", "genre", "year", "track_number", "disc_number")


def _update_item(phone_track, values: dict, snapshot: _Snapshot, new_albums: dict) -> Optional[dict]:
    """I campi di update_track per un brano, con le regole sicure; None se il brano va rimandato alla sessione dopo
    (un album nuovo che un altro brano di questa sessione sta già creando)."""
    item = {}
    deferred = False
    album_pid = phone_track.album_sync_id
    album = values.get("album")
    if album is not None:
        album = album.strip()
        if not album:
            raise PhoneSyncError("l'album non può essere vuoto")
        artist = phone_track.tags.album_artist or phone_track.tags.artist
        key = (group_name(album), group_name(artist))
        if key in snapshot.albums:
            album_pid, album = snapshot.albums[key]
        elif key in new_albums:
            deferred = True
        else:
            album_pid = snapshot.new_album_id()
            new_albums[key] = album_pid
        item["album"] = album
        item["sort_album"] = album
    title = values.get("title")
    if title is not None:
        title = title.strip()
        if not title:
            raise PhoneSyncError("il titolo non può essere vuoto")
        item["title"] = title
        item["sort_name"] = title
    if "album" in item or "title" in item:
        if not album_pid:
            raise PhoneSyncError("il brano non ha un album con identificativo: usa Rimpiazza con la versione del PC")
        item["album_pid"] = album_pid
    genre = values.get("genre")
    if genre is not None:
        genre = genre.strip()
        if not genre:
            raise PhoneSyncError("il genere non si può svuotare sull'iPhone")
        item["genre"] = genre
    for name in ("year", "track_number", "disc_number"):
        if values.get(name) is not None:
            item[name] = int(values[name])
    if item.get("disc_number") == 0:
        item["disc_number"] = 1      # l'iPhone tiene il disco 1 per un brano che non ne nomina
    if item.get("track_number") == 0:
        item["track_count"] = 0      # si svuotano insieme, come fa l'host di Apple
    result = None if deferred else item
    return result


def edit_tracks(phone_tracks: list, values: dict, progress: Optional[ProgressFn] = None) -> ActionReport:
    """Gli stessi valori su tutti i brani (values: i campi di EDITABLE_FIELDS da cambiare; year 0 lo svuota).
    Artista e artista dell'album no: sull'iPhone cambiarli rinominerebbe l'artista per tutti i suoi brani."""
    report = ActionReport()
    pending = []
    for item in phone_tracks:
        if item.from_computer:
            pending.append(item)
        else:
            report.skipped.append((_label(item.tags, ""), "non è stato messo da un computer"))

    async def work():
        folder = Path(tempfile.mkdtemp(prefix="myEasyMP3toIPhone_tag_"))
        lockdown = await iphone._open_lockdown()
        try:
            remaining = list(pending)
            failed = False
            while remaining and not failed:
                snapshot = await _snapshot(lockdown, folder)
                operations = []
                deferred = []
                new_albums = {}
                for phone_track in remaining:
                    if len(operations) >= BATCH_CHANGES:
                        deferred.append(phone_track)
                    elif phone_track.sync_id not in snapshot.track_ids:
                        report.skipped.append((_label(phone_track.tags, ""), "non è più sull'iPhone"))
                    else:
                        try:
                            item = _update_item(phone_track, values, snapshot, new_albums)
                            if item is None:
                                deferred.append(phone_track)
                            elif item:
                                operations.append(phone_sync.update_track(phone_track.sync_id, item))
                        except PhoneSyncError as exc:
                            report.errors.append((_label(phone_track.tags, ""), str(exc)))
                if progress is not None:
                    progress(len(pending) - len(remaining), len(pending), f"modifica di {len(operations)} brani")
                if operations:
                    try:
                        await _run(lockdown, snapshot, operations, [], report)
                        report.done += len(operations)
                    except PhoneSyncError as exc:
                        failed = True
                        report.errors.append((f"{len(operations)} brani", str(exc)))
                if not operations and deferred:
                    failed = True     # non dovrebbe succedere: niente sessioni a vuoto
                    report.errors.append((f"{len(deferred)} brani", "modifica non applicabile"))
                remaining = deferred
        finally:
            await lockdown.close()
            shutil.rmtree(folder, ignore_errors=True)

    if pending:
        iphone._run(work())
    return report
