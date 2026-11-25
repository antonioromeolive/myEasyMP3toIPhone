# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le azioni sull'app Musica dell'iPhone che la finestra offre: invia dal PC, rimpiazza con la versione del PC,
elimina, cambia i tag. Ogni azione è fatta di sessioni phone_sync.run_session, a gruppi; prima di ogni sessione si
scarica una copia fresca del database del telefono (identità, ancora, album e artisti già presenti).

I file del PC non si toccano: si invia una copia temporanea con le modifiche in sospeso (tags.prepare_copy).
Tutte le funzioni pubbliche sono bloccanti: vanno chiamate da un thread di lavoro."""

from __future__ import annotations

import asyncio

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

from . import iphone, phone_sync, provenance
from .library import UNKNOWN_ALBUM, UNKNOWN_ARTIST, is_cancelled, phone_group_key
from .phone_library import spelling_differences
from .phone_sync import PhoneSyncError
from .scan import VARIOUS_ARTISTS
from .tags import TagError, prepare_copy, read_cover

log = logging.getLogger(__name__)

BATCH_INSERTS = 25        # brani nuovi per sessione: l'audio di ognuno si carica mentre la sessione è aperta
RECHECK_DELETE_SECONDS = 3   # un brano da eliminare che il database non mostra: si guarda di nuovo dopo
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
    sent_tracks: list = field(default_factory=list)    # i brani del PC copiati davvero (library.Track)
    done_sync_ids: list = field(default_factory=list)  # i brani dell'iPhone eliminati o cambiati davvero

    def add(self, other: "ActionReport") -> None:
        """Somma l'esito di un'altra azione (più azioni in un'operazione sola)."""
        self.done += other.done
        self.skipped += other.skipped
        self.errors += other.errors
        self.sent_tracks += other.sent_tracks
        self.done_sync_ids += other.done_sync_ids
        self.cancelled = self.cancelled or other.cancelled
        self.sessions += other.sessions

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
                    self.artists.setdefault(phone_group_key(str(name)), (_unsigned(sync_id), str(name)))
            self.albums = {}
            for album, artist, sync_id in connection.execute(
                    "SELECT a.album, aa.album_artist, a.sync_id FROM album a "
                    "LEFT JOIN album_artist aa ON aa.album_artist_pid = a.album_artist_pid"):
                if album and sync_id:
                    key = (phone_group_key(str(album)), phone_group_key(str(artist or "")))
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


async def _store_registry(lockdown, home: Optional[Path], registry) -> None:
    """Il registro della provenienza, dopo un'azione: nella cartella dati e sull'iPhone. Un errore qui non annulla
    l'azione già fatta: lo si scrive nel registro del programma e si rimedia al prossimo collegamento."""
    from pymobiledevice3.services.afc import AfcService
    if home is not None and registry is not None:
        try:
            registry.save(home)
            async with AfcService(lockdown) as afc:
                await provenance.write_phone_registry(afc, registry)
        except Exception as exc:  # noqa: BLE001 - il registro è un aiuto, non deve far fallire l'azione
            log.warning("Registro della provenienza non salvato sull'iPhone: %s", exc)


async def _link_for(sync_id: int, item, overlay):
    path = item.track.path
    info = path.stat()
    printed = await provenance.file_fingerprint(path)
    result = provenance.Link(sync_id=sync_id, pc=provenance.computer_name(), path=str(path), size=info.st_size,
                             mtime=info.st_mtime, signature=overlay.signature(path) if overlay is not None else "",
                             fingerprint=printed, how=provenance.HOW_SENT)
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
    sent_as: int = 0          # il sync_id che ha preso sull'iPhone


async def _send_batches(pending: list, progress: Optional[ProgressFn], cancel, report: ActionReport,
                        registry=None, overlay=None, home: Optional[Path] = None) -> list:
    """Invia i brani a gruppi. Restituisce i _Pending inviati davvero; con un registro, ne registra la provenienza."""
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
                    if tags.compilation and not tags.album_artist:
                        tags.album_artist = VARIOUS_ARTISTS   # l'iPhone vuole la compilation con l'artista dell'album
                    artist_name = tags.album_artist or tags.artist or UNKNOWN_ARTIST
                    album_name = tags.album or UNKNOWN_ALBUM
                    artist_key = phone_group_key(artist_name)
                    album_key = (phone_group_key(album_name), artist_key)
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
                    item.sent_as = pid
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
                    # il messaggio nomina il file del PC, non la copia temporanea ("0.mp3")
                    message = str(exc).replace(f"{start + index}{track.path.suffix.lower()}", track.path.name, 1)
                    report.errors.append((_label(track.tags, track.path.stem), message))
            if operations:
                if progress is not None:
                    progress(start, len(pending), f"invio all'iPhone di {len(operations)} brani")
                try:
                    await _run(lockdown, snapshot, operations, uploads, report)
                    report.done += len(included)
                    sent += included
                    for item in included:
                        report.sent_tracks.append(item.track)
                    if registry is not None:
                        for item in included:
                            try:
                                registry.record(await _link_for(item.sent_as, item, overlay))
                            except Exception as exc:  # noqa: BLE001 - l'invio è fatto: il registro non lo annulla
                                log.warning("Provenienza non registrata per %s: %s", item.track.path, exc)
                except PhoneSyncError as exc:
                    failed = True
                    for item in included:
                        report.errors.append((_label(item.track.tags, item.track.path.stem), str(exc)))
            for leftover in work.iterdir():
                if leftover.is_file() and not leftover.name.startswith("MediaLibrary"):
                    leftover.unlink()
            start += BATCH_INSERTS
        report.cancelled = is_cancelled(cancel)
        if sent:
            await _store_registry(lockdown, home, registry)
    finally:
        await lockdown.close()
        shutil.rmtree(work, ignore_errors=True)
    return sent


async def _delete_batches(sync_ids: list, progress: Optional[ProgressFn], report: ActionReport, registry=None,
                          home: Optional[Path] = None) -> None:
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
            missing = []
            for sync_id in batch:
                if sync_id not in snapshot.track_ids:
                    missing.append(sync_id)
            if missing:
                # subito dopo un invio il database dell'iPhone può non essere ancora a posto: una seconda occhiata
                # dopo qualche secondo prima di dire che il brano non c'è
                await asyncio.sleep(RECHECK_DELETE_SECONDS)
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
                    report.done_sync_ids += present
                    if registry is not None:
                        for sync_id in present:
                            registry.forget(sync_id)
                except PhoneSyncError as exc:
                    failed = True
                    report.errors.append((f"{len(operations)} brani", str(exc)))
            start += BATCH_CHANGES
        if report.done:
            await _store_registry(lockdown, home, registry)
    finally:
        await lockdown.close()
        shutil.rmtree(work, ignore_errors=True)


def send_tracks(tracks: list, overlay, progress: Optional[ProgressFn] = None,
                cancel: Optional[threading.Event] = None, home: Optional[Path] = None) -> ActionReport:
    """I brani del PC (con le modifiche in sospeso già in track.tags) nell'app Musica dell'iPhone. Con home (la
    cartella dati), la provenienza di ogni brano inviato va nel registro, sul PC e sull'iPhone."""
    report = ActionReport()
    pending = []
    for track in tracks:
        if track.error:
            report.skipped.append((_label(track.tags, track.path.stem), track.error))
        else:
            pending.append(_Pending(track, overlay.cover_for(track.path) if overlay is not None else None))
    if pending:
        registry = provenance.Registry.load(home) if home is not None else None
        iphone._run(_send_batches(pending, progress, cancel, report, registry, overlay, home))
    return report


def replace_tracks(pairs: list, overlay, progress: Optional[ProgressFn] = None,
                   cancel: Optional[threading.Event] = None, home: Optional[Path] = None) -> ActionReport:
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

    registry = provenance.Registry.load(home) if home is not None else None

    async def work():
        sent = await _send_batches(pending, progress, cancel, report, registry, overlay, home)
        old = []
        for item in sent:
            old.append(item.replaces)
        if old:
            removal = ActionReport()
            await _delete_batches(old, progress, removal, registry, home)
            # la versione vecchia rimasta sull'iPhone si dice: altrimenti restano due copie senza saperlo
            for name, message in removal.errors + removal.skipped:
                report.errors.append((name, "versione vecchia non tolta dall'iPhone (ora ci sono due copie: "
                                            "elimina quella vecchia): " + message))

    if pending:
        iphone._run(work())
    return report


# --------------------------------------------------------------------------- allinea la grafia degli album

SERVICE_NAME = "myEasyMP3toIPhone servizio"   # album, artista e titolo dei brani di servizio
SERVICE_MINIMUM = 100     # brani tolti nell'ultima sessione: con 100 l'iPhone ha cancellato album e artisti vuoti
SERVICE_FRAME = b"\xff\xfb\x90\x64" + b"\x00" * 413   # MPEG1 Layer III 128 kbit/s 44,1 kHz, silenzio
SERVICE_FRAMES = 120      # circa 3 secondi, 50 kB
SERVICE_SIZE = len(SERVICE_FRAME) * SERVICE_FRAMES


def is_service_track(tags) -> bool:
    """Un brano di servizio rimasto sull'iPhone (un'operazione interrotta): si toglie alla prossima."""
    result = (tags.album or "") == SERVICE_NAME
    return result


def service_padding(removed: int) -> int:
    """Quanti brani di servizio servono perché l'ultima sessione di eliminazione (BATCH_CHANGES per sessione) ne tolga
    almeno SERVICE_MINIMUM. La regola dell'iPhone non è nota (rustunes, docs/05: 16, 32, 100, 200 e 499 brani hanno
    pulito, 4, 8 e 90 no; qui 3 e 19 no, 100 sì)."""
    rest = removed % BATCH_CHANGES
    result = SERVICE_MINIMUM - rest if 0 < rest < SERVICE_MINIMUM else 0
    if removed == 0:
        result = SERVICE_MINIMUM
    return result


def _service_pending(count: int, folder: Path) -> list:
    from .library import Track
    from .tags import TrackTags
    result = []
    for number in range(1, count + 1):
        path = folder / f"servizio{number}.mp3"
        path.write_bytes(SERVICE_FRAME * SERVICE_FRAMES)
        tags = TrackTags(title=f"{SERVICE_NAME} {number}", artist=SERVICE_NAME, album_artist=SERVICE_NAME,
                         album=SERVICE_NAME, track_number=number, genre=SERVICE_NAME)
        result.append(_Pending(Track(path=path, tags=tags, length=3.0), None))
    return result


async def _groups_left(album_keys: set, artist_keys: set) -> tuple:
    """(album rimasti, artisti rimasti, sync_id dei brani) secondo una copia fresca del database dell'iPhone."""
    folder = Path(tempfile.mkdtemp(prefix="myEasyMP3toIPhone_controllo_"))
    lockdown = await iphone._open_lockdown()
    try:
        snapshot = await _snapshot(lockdown, folder)
    finally:
        await lockdown.close()
        shutil.rmtree(folder, ignore_errors=True)
    albums = set()
    for key in album_keys:
        if key in snapshot.albums:
            albums.add(key)
    artists = set()
    for key in artist_keys:
        if key in snapshot.artists:
            artists.add(key)
    result = (albums, artists, snapshot.track_ids)
    return result


def align_spelling(pairs: list, overlay, progress: Optional[ProgressFn] = None,
                   cancel: Optional[threading.Event] = None, home: Optional[Path] = None,
                   leftovers: tuple = ()) -> ActionReport:
    """Gli album (interi) che il PC scrive in modo diverso prendono la grafia del PC: pairs (PhoneTrack, Track del PC).
    L'iPhone tiene la grafia di un album o di un artista finché la sua riga esiste, anche vuota, e la cancella solo
    in certe sessioni di eliminazione (con 100 brani sì). Quindi: brani di servizio (service_padding), una sessione
    che toglie i brani degli album e quelli di servizio, il controllo che album e artisti vecchi siano spariti, il
    reinvio dal PC. Il reinvio si fa sempre (non si annulla: i brani sono già stati tolti), anche se i nomi vecchi
    sono rimasti: allora tornano con quelli, e l'errore lo dice. leftovers: brani di servizio rimasti, da togliere."""
    report = ActionReport()
    registry = provenance.Registry.load(home) if home is not None else None
    album_keys = set()
    artist_keys = set()
    for phone_track, track in pairs:
        artist = phone_track.tags.album_artist or phone_track.tags.artist or ""
        album_keys.add((phone_group_key(phone_track.tags.album or ""), phone_group_key(artist)))
        if "album_artist" in spelling_differences(track.tags, phone_track.tags):
            artist_keys.add(phone_group_key(artist))     # solo gli artisti da riscrivere: gli altri restano

    async def work():
        folder = Path(tempfile.mkdtemp(prefix="myEasyMP3toIPhone_servizio_"))
        try:
            service = _service_pending(service_padding(len(pairs) + len(leftovers)), folder)
            service_report = ActionReport()
            sent_service = await _send_batches(service, progress, cancel, service_report)
            report.errors += service_report.errors
            if is_cancelled(cancel) or len(sent_service) < len(service):
                report.cancelled = is_cancelled(cancel)
                if sent_service:
                    service_ids = []
                    for item in sent_service:
                        service_ids.append(item.sent_as)
                    await _delete_batches(service_ids, progress, ActionReport())
            else:
                ids = []
                for phone_track, _track in pairs:
                    ids.append(phone_track.sync_id)
                for item in leftovers:
                    ids.append(item.sync_id)
                for item in sent_service:
                    ids.append(item.sent_as)
                removal = ActionReport()
                await _delete_batches(ids, progress, removal, registry, home)
                for name, message in removal.errors:
                    report.errors.append((name, "eliminazione: " + message))
                if progress is not None:
                    progress(0, 0, "controllo dei nomi sull'iPhone")
                albums_left, artists_left, present = await _groups_left(album_keys, artist_keys)
                pending = []
                for phone_track, track in pairs:
                    if phone_track.sync_id not in present:      # tolto davvero: si reinvia
                        cover = overlay.cover_for(track.path) if overlay is not None else None
                        pending.append(_Pending(track, cover))
                await _send_batches(pending, progress, None, report, registry, overlay, home)
                if albums_left or artists_left:
                    report.errors.append((f"{len(albums_left)} album e {len(artists_left)} artisti",
                                          "l'iPhone non ha cancellato i nomi vecchi: i brani sono tornati con la "
                                          "grafia dell'iPhone (si può riprovare più tardi)"))
        finally:
            shutil.rmtree(folder, ignore_errors=True)

    iphone._run(work())
    return report


def delete_tracks(phone_tracks: list, progress: Optional[ProgressFn] = None,
                  home: Optional[Path] = None) -> ActionReport:
    report = ActionReport()
    sync_ids = []
    for item in phone_tracks:
        if item.from_computer:
            sync_ids.append(item.sync_id)
        else:
            report.skipped.append((_label(item.tags, ""), "non è stato messo da un computer"))
    if sync_ids:
        registry = provenance.Registry.load(home) if home is not None else None
        iphone._run(_delete_batches(sync_ids, progress, report, registry, home))
    return report


# --------------------------------------------------------------------------- modifica dei tag

EDITABLE_FIELDS = ("title", "album", "genre", "year", "track_number", "disc_number", "compilation")


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
        key = (phone_group_key(album), phone_group_key(artist))
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
            raise PhoneSyncError("il brano non ha un album con identificativo: usa Ricopia da PC a iPhone")
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
    if values.get("compilation") is not None:
        item["is_compilation"] = bool(values["compilation"])
    result = None if deferred else item
    return result


def edit_tracks(phone_tracks: list, values: dict, progress: Optional[ProgressFn] = None) -> ActionReport:
    """Gli stessi valori su tutti i brani (values: i campi di EDITABLE_FIELDS da cambiare; year 0 lo svuota).
    Artista e artista dell'album no: sull'iPhone cambiarli rinominerebbe l'artista per tutti i suoi brani."""
    entries = []
    for item in phone_tracks:
        entries.append((item, values))
    result = edit_each(entries, progress)
    return result


def edit_each(entries: list, progress: Optional[ProgressFn] = None) -> ActionReport:
    """Come edit_tracks, con valori diversi per ogni brano: entries (PhoneTrack, values)."""
    report = ActionReport()
    pending = []
    for item, values in entries:
        if item.from_computer:
            pending.append((item, values))
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
                changed = []          # i sync_id delle modifiche di questa sessione
                deferred = []
                new_albums = {}
                for phone_track, values in remaining:
                    if len(operations) >= BATCH_CHANGES:
                        deferred.append((phone_track, values))
                    elif phone_track.sync_id not in snapshot.track_ids:
                        report.skipped.append((_label(phone_track.tags, ""), "non è più sull'iPhone"))
                    else:
                        try:
                            item = _update_item(phone_track, values, snapshot, new_albums)
                            if item is None:
                                deferred.append((phone_track, values))
                            elif item:
                                operations.append(phone_sync.update_track(phone_track.sync_id, item))
                                changed.append(phone_track.sync_id)
                            else:
                                report.done_sync_ids.append(phone_track.sync_id)   # già così: niente da fare
                        except PhoneSyncError as exc:
                            report.errors.append((_label(phone_track.tags, ""), str(exc)))
                if progress is not None:
                    progress(len(pending) - len(remaining), len(pending), f"modifica di {len(operations)} brani")
                if operations:
                    try:
                        await _run(lockdown, snapshot, operations, [], report)
                        report.done += len(operations)
                        report.done_sync_ids += changed
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


# --------------------------------------------------------------------------- dal PC all'iPhone

REPLACE_ONLY = {"artist", "album_artist"}     # sull'iPhone non si cambiano senza rinominare l'artista per tutti


def _phone_value(name: str, value):
    """Un tag del PC come lo vuole _update_item: anno e numeri interi (0 = vuoto), compilation booleana."""
    if name == "year":
        digits = str(value or "").strip()[:4]
        result = int(digits) if digits.isdigit() else 0
    elif name in ("track_number", "disc_number"):
        result = int(value or 0)
    elif name == "compilation":
        result = bool(value)
    else:
        result = str(value or "").strip()
    return result


def plan_updates(pairs: list, cover_changed: frozenset = frozenset()) -> tuple:
    """pairs: (PhoneTrack, Track del PC) dopo una modifica sul PC. (modifiche [(PhoneTrack, values)] per edit_each,
    rimpiazzi [(PhoneTrack, Track)] per replace_tracks): si rimpiazzano i brani con artista o artista dell'album
    diversi, con una copertina nuova (cover_changed: i percorsi) o con un titolo, album o genere da svuotare."""
    from .phone_library import changed_fields
    edits = []
    replacements = []
    for phone_track, track in pairs:
        if phone_track.from_computer:
            needs_replace = str(track.path) in cover_changed
            values = {}
            for name in changed_fields(track.tags, phone_track.tags):
                value = _phone_value(name, getattr(track.tags, name))
                if name in REPLACE_ONLY or (name in ("title", "album", "genre") and not value):
                    needs_replace = True
                else:
                    values[name] = value
            if needs_replace:
                replacements.append((phone_track, track))
            elif values:
                edits.append((phone_track, values))
    result = (edits, replacements)
    return result


def update_from_pc(edits: list, replacements: list, overlay, progress: Optional[ProgressFn] = None,
                   cancel: Optional[threading.Event] = None, home: Optional[Path] = None) -> ActionReport:
    """Le modifiche fatte sul PC anche sull'iPhone: prima i campi sicuri (edit_each), poi i rimpiazzi."""
    report = edit_each(edits, progress) if edits else ActionReport()
    if replacements and not is_cancelled(cancel):
        report.add(replace_tracks(replacements, overlay, progress, cancel, home))
    return report


# --------------------------------------------------------------------------- playlist

BATCH_PLAYLISTS = 100     # playlist create o cancellate per sessione


@dataclass
class PlaylistReport:
    created: list = field(default_factory=list)      # nomi delle playlist create
    deleted: list = field(default_factory=list)      # nomi delle playlist cancellate
    skipped: list = field(default_factory=list)      # (nome, motivo)
    errors: list = field(default_factory=list)       # (che cosa, errore)
    sessions: int = 0
    cancelled: bool = False


def _playlist_operations(batch: list, snapshot: _Snapshot, folder: Path, report: PlaylistReport) -> tuple:
    """Le operazioni di un gruppo [(crea?, playlist)], controllate sul database appena scaricato: (operazioni,
    [(crea?, nome)])."""
    from .phone_library import DATABASE_NAME, container_ids, read_playlists
    used = container_ids(folder / DATABASE_NAME)
    deletable = set()
    for playlist in read_playlists(folder / DATABASE_NAME):
        if playlist.from_computer:
            deletable.add(playlist.sync_id)
    operations = []
    names = []
    for create, playlist in batch:
        if create:
            members = []
            for sync_id in playlist.members:
                if sync_id in snapshot.track_ids:
                    members.append(sync_id)
            if members:
                operations.append(phone_sync.insert_playlist(_Snapshot._fresh(used), playlist.name, members, _now()))
                names.append((True, playlist.name))
            else:
                report.skipped.append((playlist.name, "nessuno dei suoi brani è più sull'iPhone"))
        elif playlist.sync_id in deletable:
            operations.append(phone_sync.delete_playlist(playlist.sync_id))
            names.append((False, playlist.name))
        else:
            report.skipped.append((playlist.name, "non è più sull'iPhone"))
    result = (operations, names)
    return result


async def _playlist_batches(steps: list, progress: Optional[ProgressFn], cancel, report: PlaylistReport) -> None:
    work = Path(tempfile.mkdtemp(prefix="myEasyMP3toIPhone_playlist_"))
    lockdown = await iphone._open_lockdown()
    try:
        start = 0
        failed = False
        while start < len(steps) and not failed and not is_cancelled(cancel):
            batch = steps[start:start + BATCH_PLAYLISTS]
            if progress is not None:
                progress(start, len(steps), f"playlist: {start} di {len(steps)}")
            snapshot = await _snapshot(lockdown, work)
            operations, names = _playlist_operations(batch, snapshot, work, report)
            if operations:
                try:
                    await _run(lockdown, snapshot, operations, [], report)
                    for create, name in names:
                        if create:
                            report.created.append(name)
                        else:
                            report.deleted.append(name)
                except PhoneSyncError as exc:
                    failed = True
                    report.errors.append((f"{len(operations)} playlist", str(exc)))
            start += BATCH_PLAYLISTS
        report.cancelled = is_cancelled(cancel)
    finally:
        await lockdown.close()
        shutil.rmtree(work, ignore_errors=True)


def rebuild_playlists(create: list, delete: list, progress: Optional[ProgressFn] = None,
                      cancel: Optional[threading.Event] = None) -> PlaylistReport:
    """Crea le playlist create (playlists.PlannedPlaylist), poi cancella quelle in delete (PhonePlaylist messe da un
    computer). Prima le nuove: se una sessione non riesce, le vecchie ci sono ancora. I brani non cambiano."""
    report = PlaylistReport()
    steps = []
    for playlist in create:
        steps.append((True, playlist))
    for playlist in delete:
        if playlist.from_computer:
            steps.append((False, playlist))
        else:
            report.skipped.append((playlist.name, "fatta sul telefono: il computer non la può cancellare"))
    if steps:
        iphone._run(_playlist_batches(steps, progress, cancel, report))
    return report
