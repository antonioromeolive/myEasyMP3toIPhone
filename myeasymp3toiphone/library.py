"""Scansione delle cartelle, raggruppamento per artista/album e organizzazione dei file."""

import logging
import os
import re
import shutil
import threading
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Callable, Optional

from .tags import TagError, TrackTags, is_audio_file, read_tags

log = logging.getLogger(__name__)

UNKNOWN_ARTIST = "Artista sconosciuto"
UNKNOWN_ALBUM = "Album sconosciuto"

ProgressFn = Callable[[int, int, str], None]
PrepareFn = Callable[["Track", Path], None]

_INVALID_CHARS = '<>:"/\\|?*'
_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}
_MAX_COMPONENT = 100
MTIME_TOLERANCE = 2.0  # secondi: FAT e alcuni dischi arrotondano le date


@dataclass
class Track:
    path: Path
    tags: TrackTags
    length: float = 0.0
    error: str = ""
    # (artista, album) come li mostra la Libreria: le grafie che differiscono solo per maiuscole, accenti o spazi
    # ("Queen"/"queen") sono un gruppo solo (assign_groups). None = i valori dei tag così come sono.
    group_key: Optional[tuple] = None
    # i tag letti dal file, quando tags contiene anche le modifiche in sospeso (overlay.TagOverlay.apply)
    original_tags: Optional[TrackTags] = None

    @property
    def display_artist(self) -> str:
        result = self.tags.album_artist or self.tags.artist or UNKNOWN_ARTIST
        return result

    @property
    def album_name(self) -> str:
        result = self.tags.album or UNKNOWN_ALBUM
        return result

    @property
    def raw_album_key(self) -> tuple:
        result = (self.display_artist, self.album_name)
        return result

    @property
    def album_key(self) -> tuple:
        if self.group_key is not None:
            result = self.group_key
        else:
            result = self.raw_album_key
        return result

    @property
    def title(self) -> str:
        result = self.tags.title or self.path.stem
        return result


@dataclass
class CopyReport:
    copied: list = field(default_factory=list)   # (sorgente, destinazione)
    updated: list = field(default_factory=list)  # (sorgente, destinazione) sostituita perché più vecchia
    skipped: list = field(default_factory=list)  # (sorgente, destinazione) identiche
    kept_newer: list = field(default_factory=list)  # (sorgente, destinazione) più recente, lasciata com'è
    errors: list = field(default_factory=list)   # (sorgente, messaggio)
    cancelled: bool = False

    def summary(self) -> str:
        parts = [f"{len(self.copied)} file copiati"]
        if self.updated:
            parts.append(f"{len(self.updated)} aggiornati")
        if self.skipped:
            parts.append(f"{len(self.skipped)} già presenti")
        if self.kept_newer:
            parts.append(f"{len(self.kept_newer)} lasciati perché la destinazione è più recente")
        if self.errors:
            parts.append(f"{len(self.errors)} errori")
        if self.cancelled:
            parts.append("operazione annullata")
        result = ", ".join(parts)
        return result


def is_cancelled(cancel: Optional[threading.Event]) -> bool:
    result = cancel is not None and cancel.is_set()
    return result


def load_track(path: Path) -> Track:
    """Un file che non si legge (danneggiato, bloccato, solo online in OneDrive…) diventa un brano con l'errore:
    non ferma mai la lettura della cartella."""
    try:
        tags, length = read_tags(path)
        result = Track(path=path, tags=tags, length=length)
    except TagError as exc:
        result = Track(path=path, tags=TrackTags(title=path.stem), error=str(exc))
    except Exception as exc:  # noqa: BLE001 - mutagen e il sistema possono sollevare di tutto su un file rovinato
        log.warning("File non leggibile %s: %s: %s", path, type(exc).__name__, exc)
        result = Track(path=path, tags=TrackTags(title=path.stem), error=f"{type(exc).__name__}: {exc}")
    return result


def _is_link(entry) -> bool:
    """Un collegamento simbolico o una giunzione: non si segue (come os.walk)."""
    result = entry.is_symlink()
    is_junction = getattr(entry, "is_junction", None)
    if not result and is_junction is not None:
        result = is_junction()
    return result


def find_audio_entries(folder: Path) -> list:
    """(percorso, dimensione, data di modifica) dei file audio, ordinati per percorso. Dimensione e data vengono
    dall'elenco della cartella (su Windows senza leggere ogni file): bastano a TagCache per sapere se un file è
    cambiato. Una cartella che non si legge si salta, come fa os.walk."""
    found = []
    pending = [str(folder)]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir() and not _is_link(entry):
                            pending.append(entry.path)
                        elif entry.is_file() and is_audio_file(Path(entry.name)):
                            info = entry.stat()
                            found.append((Path(entry.path), info.st_size, info.st_mtime))
                    except OSError:
                        pass  # un file sparito o bloccato mentre si elenca: lo si salta
        except OSError as exc:
            log.warning("Cartella non leggibile %s: %s", directory, exc)
    found.sort(key=lambda item: str(item[0]).lower())
    return found


def find_audio_files(folder: Path) -> list:
    found = []
    for path, _size, _mtime in find_audio_entries(folder):
        found.append(path)
    return found


READ_WORKERS = 8      # file letti in parallelo: su un disco esterno o di rete l'attesa è soprattutto I/O
READ_WINDOW = 256     # file affidati ai thread alla volta, per poter annullare presto


def load_tracks(files: list, progress: Optional[ProgressFn] = None,
                cancel: Optional[threading.Event] = None, cache=None, stats: Optional[list] = None,
                force: bool = False) -> list:
    """I brani dei file, nell'ordine dei file. Con una cache (tag_cache.TagCache) i file non cambiati non si
    rileggono; gli altri si leggono con più thread. stats: (dimensione, data) di ogni file, già note dall'elenco
    della cartella; senza, la cache le chiede al disco file per file. force: si rilegge tutto (la cache si
    aggiorna)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from .tag_cache import cached_track

    results = [None] * len(files)
    pending = []
    for index, path in enumerate(files):
        known = stats[index] if stats is not None else None
        track = None if force else cached_track(path, cache, known)
        if track is None:
            pending.append(index)
        else:
            results[index] = track
    done = len(files) - len(pending)
    if progress is not None:
        progress(done, len(files), f"{done} brani già noti, ne leggo {len(pending)}")
    with ThreadPoolExecutor(max_workers=READ_WORKERS) as pool:
        position = 0
        while position < len(pending) and not is_cancelled(cancel):
            futures = {}
            for index in pending[position:position + READ_WINDOW]:
                futures[pool.submit(load_track, files[index])] = index
            for future in as_completed(futures):
                track = future.result()
                results[futures[future]] = track
                if cache is not None:
                    cache.store(track)
                done += 1
                if progress is not None:
                    progress(done, len(files), track.path.name)
            position += READ_WINDOW
    tracks = []
    for track in results:
        if track is not None:
            tracks.append(track)
    return tracks


def scan_folder(folder: Path, progress: Optional[ProgressFn] = None,
                cancel: Optional[threading.Event] = None, cache=None, force: bool = False) -> list:
    files = []
    stats = []
    for path, size, mtime in find_audio_entries(folder):
        files.append(path)
        stats.append((size, mtime))
    result = load_tracks(files, progress, cancel, cache, stats, force)
    if cache is not None:
        cache.save()
    assign_groups(result)
    return result


@lru_cache(maxsize=65536)
def group_name(text: str) -> str:
    """Il nome che decide il gruppo: senza differenze di maiuscole, accenti e spazi. Ricordato: gli stessi artisti
    e album tornano su migliaia di brani a ogni apertura."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    kept = ""
    for char in decomposed:
        if not unicodedata.combining(char):
            kept += char
    result = re.sub(r"\s+", " ", kept).strip()
    return result


def best_spelling(values: list) -> str:
    """La grafia più usata; a parità, quella con più maiuscole ("Queen" prima di "queen")."""
    counted = Counter()
    for value in values:
        if value:
            counted[value] += 1
    result = ""
    best = None
    for value, count in counted.items():
        uppercase = 0
        for char in value:
            if char.isupper():
                uppercase += 1
        rank = (count, uppercase)
        if best is None or rank > best:
            best = rank
            result = value
    return result


def assign_groups(tracks: list) -> None:
    """Imposta Track.group_key: artisti e album che differiscono solo per maiuscole, accenti o spazi sono un gruppo
    solo, mostrato con la grafia più usata. Da richiamare dopo ogni modifica dei tag."""
    artist_spellings = {}
    album_spellings = {}
    for track in tracks:
        artist, album = track.raw_album_key
        artist_spellings.setdefault(group_name(artist), []).append(artist)
        album_spellings.setdefault((group_name(artist), group_name(album)), []).append(album)
    artists = {}
    for name, spellings in artist_spellings.items():
        artists[name] = best_spelling(spellings)
    albums = {}
    for name, spellings in album_spellings.items():
        albums[name] = best_spelling(spellings)
    for track in tracks:
        artist, album = track.raw_album_key
        artist_name = group_name(artist)
        track.group_key = (artists[artist_name], albums[(artist_name, group_name(album))])


def track_sort_key(track: Track) -> tuple:
    result = (track.tags.disc_number or 1, track.tags.track_number or 9999, track.title.lower())
    return result


def group_by_album(tracks: list) -> dict:
    """{(artista, album): [tracce ordinate per disco e numero]}"""
    groups = {}
    for track in tracks:
        groups.setdefault(track.album_key, []).append(track)
    for album_tracks in groups.values():
        album_tracks.sort(key=track_sort_key)
    return groups


def safe_name(text: str, fallback: str) -> str:
    """Rende un testo utilizzabile come nome di file o cartella su Windows."""
    cleaned = ""
    for char in text.strip():
        if char in _INVALID_CHARS or ord(char) < 32:
            cleaned += "_"
        else:
            cleaned += char
    cleaned = cleaned[:_MAX_COMPONENT].rstrip(" .")
    if not cleaned:
        cleaned = fallback
    if cleaned.upper().split(".")[0] in _RESERVED_NAMES:
        cleaned = "_" + cleaned
    return cleaned


def target_relative_path(track: Track) -> Path:
    """Percorso ordinato: Artista/Album (Anno)/[Disco-]NN - Titolo.ext"""
    tags = track.tags
    artist_dir = safe_name(track.display_artist, UNKNOWN_ARTIST)
    album_label = track.album_name
    if tags.year:
        album_label = f"{album_label} ({tags.year})"
    album_dir = safe_name(album_label, UNKNOWN_ALBUM)
    prefix = ""
    if tags.track_number is not None:
        prefix = f"{tags.track_number:02d} - "
        multi_disc = (tags.disc_total or 1) > 1 or (tags.disc_number or 1) > 1
        if multi_disc:
            prefix = f"{tags.disc_number or 1}-{prefix}"
    file_name = safe_name(prefix + track.title, track.path.stem) + track.path.suffix.lower()
    result = Path(artist_dir) / album_dir / file_name
    return result


def _unique_path(path: Path) -> Path:
    candidate = path
    counter = 2
    while candidate.exists():
        candidate = path.with_name(f"{path.stem} ({counter}){path.suffix}")
        counter += 1
    return candidate


def same_content(source: Path, destination: Path) -> bool:
    """Stessa dimensione e stessa data di modifica (copy2 la conserva): la stessa versione del file. La sola
    dimensione non basta: modificare i tag spesso non la cambia (l'ID3 ha spazio di riserva)."""
    source_stat = source.stat()
    destination_stat = destination.stat()
    result = (source_stat.st_size == destination_stat.st_size
              and abs(source_stat.st_mtime - destination_stat.st_mtime) <= MTIME_TOLERANCE)
    return result


def _copy_and_prepare(track: Track, destination: Path, prepare: Optional[PrepareFn]) -> None:
    """Una copia nuova del file; prepare applica alla COPIA le modifiche in sospeso, poi la copia prende la data
    dell'originale. L'originale non si tocca."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(track.path), str(destination))
    if prepare is not None:
        prepare(track, destination)
        source_stat = track.path.stat()
        os.utime(destination, (source_stat.st_atime, source_stat.st_mtime))


def _place_file(track: Track, destination: Path, move: bool, report: CopyReport,
                prepare: Optional[PrepareFn], forced: bool, overwrite: bool) -> None:
    """Copia: una destinazione identica si salta, una più vecchia si aggiorna, una più recente resta; un brano con
    modifiche in sospeso (forced) si copia sempre di nuovo. overwrite=False: una destinazione esistente non si tocca
    mai. Spostamento (solo da cartelle temporanee): non sovrascrive mai, il secondo prende un nome " (2)"."""
    source = track.path
    exists = destination.exists()
    if exists and os.path.samefile(source, destination):
        report.skipped.append((source, destination))
    elif exists and not overwrite:
        report.skipped.append((source, destination))
    elif exists and not forced and same_content(source, destination):
        report.skipped.append((source, destination))
    elif exists and not move:
        if forced or source.stat().st_mtime > destination.stat().st_mtime + MTIME_TOLERANCE:
            _copy_and_prepare(track, destination, prepare)
            report.updated.append((source, destination))
        else:
            report.kept_newer.append((source, destination))
    else:
        final = _unique_path(destination)
        if move:
            final.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(final))
            track.path = final
        else:
            _copy_and_prepare(track, final, prepare)
        report.copied.append((source, final))


def copy_organized(tracks: list, dest_root: Path, move: bool = False,
                   progress: Optional[ProgressFn] = None,
                   cancel: Optional[threading.Event] = None,
                   source_root: Optional[Path] = None,
                   prepare: Optional[PrepareFn] = None,
                   forced: Optional[Callable[[Track], bool]] = None,
                   overwrite: bool = True) -> CopyReport:
    """Copia (o sposta) le tracce in dest_root/Artista/Album/NN - Titolo.ext. I file di origine non cambiano mai.

    prepare(track, copia): applica alla copia le modifiche in sospeso; forced(track): True quando il brano ne ha, e
    la copia va rifatta. overwrite=False: le destinazioni esistenti restano come sono (importazione dall'iPhone).
    move=True si usa solo per file in cartelle temporanee; con source_root le cartelle rimaste vuote dentro
    source_root vengono eliminate (source_root stesso no).
    """
    report = CopyReport()
    index = 0
    while index < len(tracks) and not is_cancelled(cancel):
        track = tracks[index]
        if progress is not None:
            progress(index, len(tracks), track.path.name)
        destination = dest_root / target_relative_path(track)
        is_forced = forced is not None and forced(track)
        try:
            _place_file(track, destination, move, report, prepare, is_forced, overwrite)
        except (OSError, TagError) as exc:
            report.errors.append((track.path, str(exc)))
        index += 1
    report.cancelled = is_cancelled(cancel)
    if move and source_root is not None:
        _remove_empty_dirs(report, source_root)
    return report


def _is_strictly_inside(path: Path, root: Path) -> bool:
    resolved = path.resolve()
    result = resolved != root and root in resolved.parents
    return result


def _remove_empty_dirs(report: CopyReport, source_root: Path) -> None:
    """Dopo uno spostamento elimina le cartelle vuote rimaste dentro source_root."""
    root = source_root.resolve()
    folders = {source.parent for source, _destination in report.copied}
    for folder in sorted(folders, key=lambda p: len(p.parts), reverse=True):
        current = folder
        while (_is_strictly_inside(current, root) and current.is_dir()
               and not any(current.iterdir())):
            current.rmdir()
            current = current.parent
