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


DISC_FOLDER = re.compile(r"^\W*(?:cd|disc|disco|disk|dvd)\W*\d+(?:\W|$)", re.IGNORECASE)
DISC_SUFFIX = re.compile(r"[\s\-_,.]*[\(\[]?\s*(?:cd|disc|disco|disk|dvd)\s*\d+\s*[\)\]]?\s*$", re.IGNORECASE)


def album_folder(path) -> str:
    """La cartella dell'album di un file (un album su più dischi è un album solo):
      * "Album\\CD1\\01.mp3", "Album\\cd 2 - studio\\01.mp3": la cartella sopra, "Album";
      * "Artista\\Album (Disc 1)\\01.mp3", "Artista\\Album CD2\\01.mp3": "Artista\\Album", il nome senza il disco
        (una cartella che magari non esiste: serve a mettere insieme i dischi);
      * altrimenti la cartella del file."""
    parent = Path(path).parent
    stripped = DISC_SUFFIX.sub("", parent.name)
    if DISC_FOLDER.match(parent.name) and parent.parent != parent:
        result = str(parent.parent)
    elif stripped and stripped != parent.name and parent.parent != parent:
        result = str(parent.parent / stripped)
    else:
        result = str(parent)
    return result


VARIOUS_ARTIST_KEYS = {"aavv", "artistivari", "variousartists", "various", "va", "autorivari", "vari",
                       "variartisti"}
LEADING_ZEROS = re.compile(r"(?<!\d)0+(?=\d)")
VARIOUS_KEY = "\x00"          # la chiave di tutti gli "artisti vari"
_extra_various_keys = set()   # i nomi aggiunti in Impostazioni (set_various_artist_names)


def _various_key(name: str) -> str:
    result = re.sub(r"[^a-z0-9]", "", group_name(name or ""))
    return result


def set_various_artist_names(names) -> None:
    """Gli altri nomi che valgono come "AA.VV." (Impostazioni → Altri nomi per "Artisti vari"): da richiamare
    all'avvio e dopo ogni cambio."""
    keys = set()
    for name in names:
        key = _various_key(name)
        if key:
            keys.add(key)
    _extra_various_keys.clear()
    _extra_various_keys.update(keys)


def is_various_artists(name: str) -> bool:
    """"AA.VV.", "Artisti vari", "Various Artists"… e i nomi aggiunti in Impostazioni: l'artista di una
    compilation."""
    key = _various_key(name)
    result = key in VARIOUS_ARTIST_KEYS or key in _extra_various_keys
    return result


def artist_group_key(name: str) -> str:
    """Il gruppo di un artista negli elenchi: senza maiuscole, accenti e spazi; tutti gli "artisti vari" (anche i
    nomi aggiunti in Impostazioni) sono un artista solo."""
    result = VARIOUS_KEY if is_various_artists(name) else group_name(name)
    return result


def phone_group_key(text: str) -> str:
    """Il nome di un artista o di un album come lo confronta l'iPhone, che con un nome "uguale" attacca il brano
    all'album o all'artista che ha già e ne tiene la grafia: senza maiuscole, accenti e spazi, gli zeri davanti ai
    numeri non contano ("Raccolta 01" = "Raccolta 1"), e "AA.VV." = "Artisti vari" = "Various Artists" (solo i nomi
    fissi: quelli aggiunti in Impostazioni l'iPhone non li conosce)."""
    key = LEADING_ZEROS.sub("", group_name(text or ""))
    result = VARIOUS_KEY if _various_key(key) in VARIOUS_ARTIST_KEYS else key
    return result


def preference(path, preferred) -> int:
    """Il posto di un file (o di una cartella) nell'ordine delle cartelle preferite (Impostazioni): 0 nella prima,
    1 nella seconda…, len(preferred) in nessuna. Una voce con una barra o i due punti è un percorso (vale con le
    sottocartelle); senza, è il nome di una cartella, in qualsiasi punto del percorso. Maiuscole e minuscole non
    contano."""
    parts = set()
    for part in Path(path).parts:
        parts.add(part.rstrip("\\/").casefold())
    text = str(Path(path)).casefold()
    result = len(preferred)
    index = 0
    while index < len(preferred) and result == len(preferred):
        entry = str(preferred[index]).strip()
        if entry:
            if "/" in entry or "\\" in entry or ":" in entry:
                folder = str(Path(entry)).casefold().rstrip("\\/")
                found = text == folder or text.startswith(folder + os.sep)
            else:
                found = entry.casefold() in parts
            if found:
                result = index
        index += 1
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


def _group_keys(pairs: list) -> list:
    """[(artista, album)] -> le stesse coppie come si mostrano negli elenchi: artisti e album che differiscono solo per
    maiuscole, accenti o spazi sono un gruppo solo, con la grafia più usata; tutti gli "artisti vari" ("AA.VV.",
    "Various Artists"…, artist_group_key) sono un artista solo, e i loro album con lo stesso nome un album solo."""
    artist_spellings = {}
    album_spellings = {}
    keys = []
    for artist, album in pairs:
        key = (artist_group_key(artist), group_name(album))
        keys.append(key)
        artist_spellings.setdefault(key[0], []).append(artist)
        album_spellings.setdefault(key, []).append(album)
    artists = {}
    for name, spellings in artist_spellings.items():
        artists[name] = best_spelling(spellings)
    albums = {}
    for key, spellings in album_spellings.items():
        albums[key] = best_spelling(spellings)
    result = []
    for key in keys:
        result.append((artists[key[0]], albums[key]))
    return result


def assign_groups(tracks: list) -> None:
    """Imposta Track.group_key (_group_keys). Da richiamare dopo ogni modifica dei tag."""
    pairs = []
    for track in tracks:
        pairs.append(track.raw_album_key)
    for track, key in zip(tracks, _group_keys(pairs)):
        track.group_key = key


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


def _tags_sort_key(item) -> tuple:
    tags = item.tags
    result = (tags.disc_number or 1, tags.track_number or 9999, (tags.title or "").lower())
    return result


def album_groups(items: list) -> dict:
    """{(artista, album): [elementi ordinati per disco e numero]} per elementi che hanno solo i tag (i brani
    dell'iPhone): come assign_groups e group_by_album (l'artista dell'album, o quello del brano; le grafie che
    differiscono per maiuscole, accenti o spazi insieme, con la più usata; gli "artisti vari" insieme), senza
    cambiare gli elementi."""
    pairs = []
    for item in items:
        pairs.append((item.tags.album_artist or item.tags.artist or UNKNOWN_ARTIST, item.tags.album or UNKNOWN_ALBUM))
    groups = {}
    for item, key in zip(items, _group_keys(pairs)):
        groups.setdefault(key, []).append(item)
    for members in groups.values():
        members.sort(key=_tags_sort_key)
    result = groups
    return result


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
