# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La scansione della libreria (sul PC, sul posto) o della musica sull'iPhone, per trovare i problemi tipici:

  * file che non vengono aggiornati: sola lettura, tag ID3v1 o APE con valori vecchi che alcuni lettori leggono per
    primi, ID3 v2.4/v2.2 che Windows e diverse app non leggono, copie doppie "Titolo (2)", brani nell'app Musica
    dell'iPhone con tag diversi da quelli del PC;
  * album con pochi brani: numeri di traccia mancanti, meno brani del totale dichiarato, album di uno o due brani;
  * collezioni divise su più album: la stessa cartella con album diversi, lo stesso album scritto in modi diversi
    (maiuscole, "CD1"/"Disc 2"), compilation senza "Artista album", lo stesso artista scritto in modi diversi.

Prima le regole (locali, veloci e gratuite), poi, se c'è un profilo AI, l'AI riceve una tabella compatta degli album e
i problemi trovati: li conferma o li scarta, ne aggiunge altri e propone le correzioni dei tag.
"""

from __future__ import annotations

import logging
import os
import re
import threading
import time
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import mutagen
from mutagen.apev2 import APENoHeaderError, APEv2

from .library import (
    UNKNOWN_ALBUM, UNKNOWN_ARTIST, Track, assign_groups, best_spelling, group_by_album, is_cancelled,
)
from .phone_library import DEVICE_ABSENT, DEVICE_STALE, PhoneIndex, device_status
from .tags import TrackTags

log = logging.getLogger(__name__)

KIND_NOT_UPDATED = "non_aggiornato"
KIND_FEW_TRACKS = "album_incompleto"
KIND_SPLIT = "collezione_divisa"
KIND_DUPLICATE = "duplicato"
KIND_MISSING_TAGS = "tag_mancanti"
KIND_UNREADABLE = "illeggibile"
KIND_ONLY_ON_DEVICE = "solo_su_iphone"
KIND_LABELS = {
    KIND_NOT_UPDATED: "File che non si aggiornano",
    KIND_FEW_TRACKS: "Album con pochi brani",
    KIND_SPLIT: "Collezioni divise su più album",
    KIND_DUPLICATE: "Brani duplicati",
    KIND_MISSING_TAGS: "Tag mancanti",
    KIND_UNREADABLE: "File illeggibili",
    KIND_ONLY_ON_DEVICE: "Solo sull'iPhone",
}
AI_KINDS = (KIND_NOT_UPDATED, KIND_FEW_TRACKS, KIND_SPLIT, KIND_DUPLICATE, KIND_MISSING_TAGS)

SEVERITY_HIGH = "alta"
SEVERITY_MEDIUM = "media"
SEVERITY_LOW = "bassa"
SEVERITY_ORDER = {SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 1, SEVERITY_LOW: 2}

ORIGIN_RULE = "regola"
ORIGIN_AI = "AI"

FIX_TAGS = "tags"            # modifiche dei tag: restano in sospeso (overlay), i file sul PC non cambiano

VARIOUS_ARTISTS = "Artisti vari"
AI_CHUNK_ALBUMS = 100
DISC_MARKER = re.compile(r"[\s\-–,:]*[\(\[]?\s*(?:disc|disco|disk|cd)\s*(\d{1,2})\s*[\)\]]?\s*$", re.IGNORECASE)
NUMBERED_COPY = re.compile(r"^(.*) \((\d+)\)$")
YEAR_SUFFIX = re.compile(r"^(.*?)\s*\((\d{4})\)$")
TRACK_PREFIX = re.compile(r"^(?:(\d{1,2})-)?(\d{1,3})\s*-\s*(.+)$")
FIX_FIELDS = ("album", "album_artist", "artist", "year", "genre")

# i controlli che si possono scegliere: (id, nome, spiegazione in una riga)
CHECK_FILES = "file"
CHECK_FEW = "pochi_brani"
CHECK_SPLIT = "collezioni_divise"
CHECK_VARIANTS = "artisti"
CHECK_MISSING = "tag_mancanti"
CHECK_UNREADABLE = "illeggibili"
CHECK_DUPLICATES = "duplicati"
CHECKS = (
    (CHECK_FILES, "File che non si aggiornano",
     "MP3 con un vecchio tag ID3v1 diverso o un tag APE; sull'iPhone, brani con tag diversi da quelli del PC"),
    (CHECK_FEW, "Album con pochi brani",
     "numeri di traccia mancanti, meno brani del totale dichiarato, album di 1-2 brani"),
    (CHECK_SPLIT, "Collezioni divise su più album",
     "una cartella con album diversi, lo stesso album scritto in modi diversi o con \"CD 1\" nel nome, "
     "compilation senza artista dell'album"),
    (CHECK_VARIANTS, "Artisti scritti in modi diversi", "\"The Beatles\" e \"Beatles\", maiuscole, \"AC/DC\" e \"ACDC\""),
    (CHECK_MISSING, "Tag mancanti", "brani senza titolo, album o artista"),
    (CHECK_UNREADABLE, "File illeggibili", "file danneggiati, bloccati o disponibili solo online"),
    (CHECK_DUPLICATES, "Brani duplicati",
     "lo stesso brano in più file: stesso audio anche con tag diversi, oppure stessa durata, titolo e artista in "
     "file diversi (un MP3 e un FLAC); l'AI guarda solo le coppie sospette"),
)
ALL_CHECKS = frozenset(check_id for check_id, _label, _note in CHECKS)
KIND_CHECK = {KIND_NOT_UPDATED: CHECK_FILES, KIND_FEW_TRACKS: CHECK_FEW, KIND_SPLIT: CHECK_SPLIT,
              KIND_DUPLICATE: CHECK_DUPLICATES, KIND_MISSING_TAGS: CHECK_MISSING, KIND_UNREADABLE: CHECK_UNREADABLE}
AI_REVIEW_CHECKS = frozenset({CHECK_FILES, CHECK_FEW, CHECK_SPLIT, CHECK_VARIANTS, CHECK_MISSING})  # per album
SAME_SONG_TOLERANCE = 2.0     # secondi: lo stesso brano in due file ha quasi la stessa durata
AI_PAIRS_BATCH = 25
AI_MAX_PAIRS = 400            # oltre, le coppie restano "da controllare" senza AI (un'AI locale è lenta)
TITLE_EXTRA = re.compile(r"\s*[\(\[][^\)\]]*[\)\]]|\s+-\s+.*$")

ProgressFn = Callable[[int, int, str], None]


@dataclass
class Fix:
    action: str
    description: str
    changes: list = field(default_factory=list)   # FIX_TAGS: [(Path, {campo: valore})]
    files: list = field(default_factory=list)     # le altre azioni: [Path] (o percorsi sull'iPhone)


@dataclass
class Issue:
    kind: str
    severity: str
    title: str
    detail: str
    files: list = field(default_factory=list)
    fix: Optional[Fix] = None
    origin: str = ORIGIN_RULE
    rule_id: str = ""
    ai_note: str = ""

    def sort_key(self) -> tuple:
        result = (SEVERITY_ORDER.get(self.severity, 3), self.kind, self.title.lower())
        return result


@dataclass
class ScanReport:
    target: str
    issues: list = field(default_factory=list)
    tracks_scanned: int = 0
    albums_scanned: int = 0
    ai_profile: str = ""
    ai_errors: list = field(default_factory=list)
    cancelled: bool = False

    def counts(self) -> dict:
        result = Counter()
        for issue in self.issues:
            result[issue.kind] += 1
        return dict(result)


# --------------------------------------------------------------------------- testi

def _plain(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    kept = ""
    for char in decomposed:
        if not unicodedata.combining(char):
            kept += char
    result = re.sub(r"[^a-z0-9]+", " ", kept.replace("&", " and ")).strip()
    return result


def split_disc_marker(album: str) -> tuple:
    """"Album (CD 2)" -> ("Album", 2); "Album" -> ("Album", None)."""
    match = DISC_MARKER.search(album)
    if match and match.start() > 0:
        result = (album[:match.start()].strip(), int(match.group(1)))
    else:
        result = (album, None)
    return result


def album_norm(album: str) -> str:
    base, _disc = split_disc_marker(album)
    result = _plain(base)
    return result


def artist_norm(artist: str) -> str:
    plain = _plain(artist)
    if plain.startswith("the "):
        plain = plain[4:]
    result = plain.replace(" ", "")
    return result


def _most_common(values: list) -> str:
    result = best_spelling(values)
    return result


def _tracks_text(count: int) -> str:
    if count == 1:
        result = "1 brano"
    else:
        result = f"{count} brani"
    return result


def _short(path) -> str:
    parts = Path(path).parts
    result = str(Path(*parts[-3:])) if len(parts) >= 3 else str(path)
    return result


# --------------------------------------------------------------------------- regole: file

def _id3v1_fields(path: Path) -> dict:
    """Titolo, artista e album del tag ID3v1 (gli ultimi 128 byte), se c'è."""
    result = {}
    try:
        with path.open("rb") as handle:
            handle.seek(-128, os.SEEK_END)
            block = handle.read(128)
        if block[:3] == b"TAG":
            for name, start in (("title", 3), ("artist", 33), ("album", 63)):
                result[name] = block[start:start + 30].split(b"\x00")[0].decode("latin-1").strip()
    except OSError:
        result = {}
    return result


def _v1_differs(v1: dict, tags: TrackTags) -> bool:
    differs = False
    for name, value in v1.items():
        current = getattr(tags, name) or ""
        if value and _plain(value) != _plain(current[:30]):
            differs = True
    return differs


def _has_ape(path: Path) -> bool:
    try:
        APEv2(str(path))
        result = True
    except (APENoHeaderError, mutagen.MutagenError):
        result = False
    return result


def detect_file_problems(tracks: list, progress: Optional[ProgressFn] = None,
                         cancel: Optional[threading.Event] = None) -> list:
    """MP3 con un vecchio ID3v1 diverso o con un tag APE: sul PC restano così (sola lettura), le copie inviate
    all'iPhone ne sono ripulite (tags.prepare_copy). Solo un'informazione, nessuna correzione."""
    v1_stale = []
    with_ape = []
    index = 0
    while index < len(tracks) and not is_cancelled(cancel):
        track = tracks[index]
        if progress is not None:
            progress(index, len(tracks), f"controllo file: {track.path.name}")
        if not track.error and track.path.suffix.lower() == ".mp3":
            v1 = _id3v1_fields(track.path)
            if v1 and _v1_differs(v1, track.original_tags or track.tags):
                v1_stale.append(track.path)
            if _has_ape(track.path):
                with_ape.append(track.path)
        index += 1
    cleaned = (" Sul PC il file resta com'è (sola lettura); le copie inviate all'iPhone ne sono ripulite "
               "automaticamente.")
    issues = []
    if v1_stale:
        issues.append(Issue(
            KIND_NOT_UPDATED, SEVERITY_LOW, f"{len(v1_stale)} MP3 con un vecchio tag ID3v1 diverso",
            "Oltre al tag moderno (ID3v2) questi file hanno un vecchio tag ID3v1 con valori diversi: alcuni lettori, "
            "autoradio e app leggono quello e mostrano i valori vecchi." + cleaned, v1_stale, rule_id="R2"))
    if with_ape:
        issues.append(Issue(
            KIND_NOT_UPDATED, SEVERITY_LOW, f"{len(with_ape)} MP3 con un tag APE",
            "Questi file hanno anche un tag APE (di solito lasciato da programmi di normalizzazione del volume): "
            "alcuni lettori lo leggono al posto dell'ID3." + cleaned, with_ape, rule_id="R3"))
    return issues


def detect_unreadable(tracks: list) -> list:
    broken = []
    for track in tracks:
        if track.error:
            broken.append(track.path)
    issues = []
    if broken:
        issues.append(Issue(KIND_UNREADABLE, SEVERITY_HIGH, f"{len(broken)} file illeggibili",
                            "Questi file non si possono leggere: sono danneggiati o non sono davvero file audio.",
                            broken, rule_id="R5"))
    return issues


def _guess_from_path(track: Track) -> dict:
    """Album e artista dalle cartelle (…/Artista/Album/file), titolo dal nome del file senza "NN - "."""
    guessed = {}
    folder = track.path.parent.name
    match = YEAR_SUFFIX.match(folder)
    if match:
        folder = match.group(1)
    artist_folder = track.path.parent.parent.name
    if not track.tags.album and folder:
        guessed["album"] = folder
    if not track.tags.artist and not track.tags.album_artist and artist_folder:
        guessed["artist"] = artist_folder
    if not track.tags.title:
        title_match = TRACK_PREFIX.match(track.path.stem)
        if title_match:
            guessed["title"] = title_match.group(3).strip()
        else:
            guessed["title"] = track.path.stem
    return guessed


def detect_missing_tags(tracks: list) -> list:
    by_folder = {}
    for track in tracks:
        missing = not track.error and (not track.tags.title or not track.tags.album
                                       or not (track.tags.artist or track.tags.album_artist))
        if missing:
            by_folder.setdefault(track.path.parent, []).append(track)
    issues = []
    number = 0
    for folder, folder_tracks in sorted(by_folder.items(), key=lambda item: str(item[0]).lower()):
        number += 1
        changes = []
        for track in folder_tracks:
            guessed = _guess_from_path(track)
            if guessed:
                changes.append((track.path, guessed))
        fix = None
        if changes:
            fix = Fix(FIX_TAGS, "Ricava titolo, album e artista dai nomi di file e cartelle", changes=changes)
        issues.append(Issue(
            KIND_MISSING_TAGS, SEVERITY_MEDIUM, f"{len(folder_tracks)} brani senza titolo, album o artista in "
            f"{_short(folder)}",
            "Senza album o artista i brani finiscono in \"Album sconosciuto\" / \"Artista sconosciuto\" e la "
            "collezione appare divisa.",
            [track.path for track in folder_tracks], fix, rule_id=f"R6.{number}"))
    return issues


def detect_duplicates(tracks: list) -> list:
    """Doppioni solo DENTRO lo stesso album: una copia "Titolo (2).mp3" accanto all'originale con lo stesso album, e
    brani con lo stesso album, numero e titolo. Lo stesso brano in album diversi (l'album originale e una raccolta) è
    legittimo e non si segnala. Nessuna correzione automatica: quale copia tenere lo decide l'utente."""
    by_path = {str(track.path).casefold(): track for track in tracks}
    numbered = []
    for track in tracks:
        match = NUMBERED_COPY.match(track.path.stem)
        if match:
            original = by_path.get(str(track.path.with_name(match.group(1) + track.path.suffix)).casefold())
            if original is not None and original.album_key == track.album_key:
                numbered.append((original.path, track.path))
    same = {}
    for track in tracks:
        if not track.error and track.tags.album and track.tags.title:
            key = (track.album_key, track.tags.disc_number or 1, track.tags.track_number, _plain(track.tags.title))
            same.setdefault(key, []).append(track.path)
    issues = []
    if numbered:
        files = []
        for original, copy in numbered:
            files += [original, copy]
        issues.append(Issue(
            KIND_DUPLICATE, SEVERITY_HIGH, f"{len(numbered)} brani copiati due volte (\"… (2)\")",
            "Accanto al file c'è una sua copia con \" (2)\" nel nome, nello stesso album: di solito una delle due è "
            "la versione vecchia, "
            "con i tag non aggiornati. Ascoltale e tieni la più recente.",
            files, rule_id="R7"))
    groups = []
    for paths in same.values():
        if len(paths) > 1:
            groups.append(paths)
    if groups:
        files = []
        for paths in groups:
            files += paths
        issues.append(Issue(
            KIND_DUPLICATE, SEVERITY_MEDIUM, f"{len(groups)} brani presenti più volte nello stesso album",
            "Più file hanno lo stesso album, numero di traccia e titolo.", files, rule_id="R8"))
    return issues


# --------------------------------------------------------------------------- regole: album

def _numbers_by_disc(album_tracks: list) -> dict:
    numbers = {}
    for track in album_tracks:
        if track.tags.track_number:
            numbers.setdefault(track.tags.disc_number or 1, set()).add(track.tags.track_number)
    return numbers


def detect_few_tracks(tracks: list) -> list:
    issues = []
    number = 0
    groups = group_by_album(tracks)
    for key in sorted(groups, key=lambda k: (k[0].lower(), k[1].lower())):
        artist, album = key
        album_tracks = groups[key]
        if album != UNKNOWN_ALBUM:
            number += 1
            declared = 0
            for track in album_tracks:
                declared = max(declared, track.tags.track_total or 0)
            gaps = []
            for disc, numbers in sorted(_numbers_by_disc(album_tracks).items()):
                highest = max(max(numbers), declared if disc == 1 else 0)
                for position in range(1, highest + 1):
                    if position not in numbers:
                        gaps.append(f"{disc}-{position}" if disc > 1 else str(position))
            count = len(album_tracks)
            files = [track.path for track in album_tracks]
            if gaps:
                expected = count + len(gaps)
                severity = SEVERITY_HIGH if count * 2 <= expected else SEVERITY_MEDIUM
                shown = ", ".join(gaps[:15]) + ("…" if len(gaps) > 15 else "")
                issues.append(Issue(
                    KIND_FEW_TRACKS, severity, f"{artist} — {album}: {_tracks_text(count)} su almeno {expected}",
                    f"Mancano i numeri di traccia {shown}. \"Verifica album\" controlla l'elenco completo su "
                    "MusicBrainz.", files, rule_id=f"R9.{number}"))
            elif count <= 2:
                issues.append(Issue(
                    KIND_FEW_TRACKS, SEVERITY_LOW, f"{artist} — {album}: solo {_tracks_text(count)}",
                    "Può essere un singolo, oppure un album di cui hai solo pochi brani, oppure brani di un album "
                    "finiti in un album a parte per un tag scritto diversamente.", files, rule_id=f"R10.{number}"))
    return issues


def _unify_changes(tracks: list, values: dict) -> list:
    """Le modifiche per portare i brani ai valori dati. "Artisti vari" come artista dell'album porta con sé la spunta
    compilation: senza, l'app Musica dell'iPhone divide l'album in un album per artista."""
    if values.get("album_artist") == VARIOUS_ARTISTS:
        values = dict(values)
        values["compilation"] = True
    changes = []
    for track in tracks:
        wanted = {}
        for name, value in values.items():
            if value is not None and (getattr(track.tags, name) or "") != value:
                wanted[name] = value
        if wanted:
            changes.append((track.path, wanted))
    return changes


def detect_split_folders(tracks: list) -> list:
    """Una cartella i cui brani stanno in album diversi: quasi sempre un album diviso da tag non uniformi."""
    by_folder = {}
    for track in tracks:
        if not track.error:
            by_folder.setdefault(track.path.parent, []).append(track)
    issues = []
    number = 0
    for folder, folder_tracks in sorted(by_folder.items(), key=lambda item: str(item[0]).lower()):
        keys = {track.album_key for track in folder_tracks}
        albums = {album_norm(track.tags.album) for track in folder_tracks if track.tags.album}
        if len(keys) > 1 and len(albums) <= 1 and len(folder_tracks) >= 2:
            number += 1
            album = _most_common([split_disc_marker(t.tags.album)[0] for t in folder_tracks])
            artists = {artist_norm(t.tags.artist) for t in folder_tracks if t.tags.artist}
            album_artist = _most_common([t.tags.album_artist for t in folder_tracks])
            if not album_artist:
                if len(artists) > 1:
                    album_artist = VARIOUS_ARTISTS
                else:
                    album_artist = _most_common([t.tags.artist for t in folder_tracks])
            names = sorted({f"{k[0]} — {k[1]}" for k in keys})
            issues.append(Issue(
                KIND_SPLIT, SEVERITY_HIGH, f"{_short(folder)}: un album diviso in {len(keys)}",
                "I brani di questa cartella risultano in album diversi: " + "; ".join(names) + ". Di solito "
                "l'\"Artista album\" manca o è scritto in modo diverso: per una compilation va messo \"Artisti "
                "vari\" su tutti i brani.",
                [t.path for t in folder_tracks],
                Fix(FIX_TAGS, f"Album \"{album}\", artista album \"{album_artist}\" su tutti i brani",
                    changes=_unify_changes(folder_tracks, {"album": album, "album_artist": album_artist})),
                rule_id=f"R11.{number}"))
    return issues


def detect_split_names(tracks: list) -> list:
    """Lo stesso album scritto in modi diversi (maiuscole, "CD 2", punteggiatura) o diviso per artista."""
    groups = group_by_album(tracks)
    by_name = {}
    for key, album_tracks in groups.items():
        if key[1] != UNKNOWN_ALBUM:
            by_name.setdefault(album_norm(key[1]), []).append(key)
    issues = []
    number = 0
    for norm, keys in sorted(by_name.items()):
        if len(keys) > 1:
            number += 1
            all_tracks = []
            for key in keys:
                all_tracks += groups[key]
            same_artist = len({artist_norm(key[0]) for key in keys}) == 1
            album = _most_common([split_disc_marker(t.tags.album)[0] for t in all_tracks])
            names = "; ".join(sorted(f"{k[0]} — {k[1]}" for k in keys))
            changes = []
            if same_artist:
                album_artist = _most_common([t.tags.album_artist or t.tags.artist for t in all_tracks])
                for track in all_tracks:
                    wanted = {}
                    base, disc = split_disc_marker(track.tags.album)
                    if track.tags.album != album:
                        wanted["album"] = album
                    if disc is not None and track.tags.disc_number != disc:
                        wanted["disc_number"] = disc
                    if (track.tags.album_artist or "") != album_artist:
                        wanted["album_artist"] = album_artist
                    if wanted:
                        changes.append((track.path, wanted))
                issues.append(Issue(
                    KIND_SPLIT, SEVERITY_HIGH, f"\"{album}\" scritto in {len(keys)} modi diversi",
                    f"Lo stesso album compare come: {names}. Maiuscole, punteggiatura o un \"CD 1\"/\"Disc 2\" nel "
                    "nome lo dividono; il numero del disco va nel campo N. disco.",
                    [t.path for t in all_tracks],
                    Fix(FIX_TAGS, f"Album \"{album}\" e artista album \"{album_artist}\" su tutti i brani, numero "
                        "del disco dal nome", changes=changes), rule_id=f"R12.{number}"))
            else:
                folders = {t.path.parent for t in all_tracks}
                years = {t.tags.year for t in all_tracks if t.tags.year}
                no_album_artist = all(not t.tags.album_artist for t in all_tracks)
                likely = no_album_artist and (len(folders) == 1 or len(years) == 1)
                severity = SEVERITY_MEDIUM if likely else SEVERITY_LOW
                fix = None
                if likely:
                    fix = Fix(FIX_TAGS, f"Artista album \"{VARIOUS_ARTISTS}\" e album \"{album}\" su tutti i brani",
                              changes=_unify_changes(all_tracks, {"album": album, "album_artist": VARIOUS_ARTISTS}))
                issues.append(Issue(
                    KIND_SPLIT, severity, f"\"{album}\" diviso tra {len(keys)} artisti",
                    f"L'album compare come: {names}. Se è una compilation, senza \"Artista album\" ogni artista "
                    "forma un album a parte. Se invece sono album diversi con lo stesso nome, ignora.",
                    [t.path for t in all_tracks], fix, rule_id=f"R13.{number}"))
    return issues


def detect_artist_variants(tracks: list) -> list:
    """Lo stesso artista scritto in modi diversi ("The Beatles"/"Beatles", "AC/DC"/"ACDC", maiuscole)."""
    by_norm = {}
    for track in tracks:
        name = track.display_artist
        if name != UNKNOWN_ARTIST:
            by_norm.setdefault(artist_norm(name), []).append(track)
    issues = []
    number = 0
    for norm, artist_tracks in sorted(by_norm.items()):
        written = {t.display_artist for t in artist_tracks}
        if len(written) > 1 and norm:
            number += 1
            chosen = _most_common([t.display_artist for t in artist_tracks])
            changes = []
            for track in artist_tracks:
                wanted = {}
                if track.tags.album_artist and track.tags.album_artist != chosen:
                    wanted["album_artist"] = chosen
                if track.tags.artist and artist_norm(track.tags.artist) == norm and track.tags.artist != chosen:
                    wanted["artist"] = chosen
                if wanted:
                    changes.append((track.path, wanted))
            issues.append(Issue(
                KIND_SPLIT, SEVERITY_MEDIUM, f"Artista scritto in {len(written)} modi: " + ", ".join(sorted(written)),
                "Le varianti dividono la collezione dell'artista negli elenchi e sull'iPhone.",
                [t.path for t in artist_tracks],
                Fix(FIX_TAGS, f"Scrivi ovunque \"{chosen}\"", changes=changes), rule_id=f"R14.{number}"))
    return issues


def _file_set(issue: Issue) -> set:
    result = {str(path) for path in issue.files}
    return result


def _covered(issue: Issue, others: list) -> bool:
    """I file del problema sono tutti dentro quelli di uno degli altri."""
    files = _file_set(issue)
    result = False
    for other in others:
        if other is not issue and files and files <= _file_set(other):
            result = True
    return result


def merge_overlapping(issues: list) -> list:
    """Un problema solo quando più regole descrivono lo stesso: la compilation divisa nella stessa cartella (R11)
    contiene "diviso tra artisti" (R13); un album di 1-2 brani che fa parte di una collezione divisa (R10) non è un
    problema a sé; un album incompleto che è anche diviso lo dice."""
    folders = [issue for issue in issues if issue.rule_id.startswith("R11")]
    splits = [issue for issue in issues if issue.kind == KIND_SPLIT]
    kept = []
    for issue in issues:
        drop = ((issue.rule_id.startswith("R13") and _covered(issue, folders))
                or (issue.rule_id.startswith("R10") and _covered(issue, splits)))
        if issue.rule_id.startswith("R9") and _covered(issue, splits):
            issue.detail += (" L'album è anche diviso in più parti: correggi prima la divisione, poi ripeti la "
                             "scansione.")
        if not drop:
            kept.append(issue)
    return kept


def drop_repeated(ai_issues: list, found_by_rules: list) -> list:
    """Le proposte dell'AI che ripetono un problema già trovato dalle regole (stesso tipo, stessi file)."""
    kept = []
    for issue in ai_issues:
        same_kind = [rule for rule in found_by_rules if rule.kind == issue.kind]
        if not _covered(issue, same_kind):
            kept.append(issue)
    return kept


def rule_issues(tracks: list, check_files: bool, progress: Optional[ProgressFn] = None,
                cancel: Optional[threading.Event] = None, checks: frozenset = ALL_CHECKS) -> list:
    issues = []
    if CHECK_UNREADABLE in checks:
        issues += detect_unreadable(tracks)
    if check_files and CHECK_FILES in checks:
        issues += detect_file_problems(tracks, progress, cancel)
    if CHECK_DUPLICATES in checks:
        issues += detect_duplicates(tracks)
    if CHECK_MISSING in checks:
        issues += detect_missing_tags(tracks)
    if CHECK_FEW in checks:
        issues += detect_few_tracks(tracks)
    if CHECK_SPLIT in checks:
        issues += detect_split_folders(tracks)
        issues += detect_split_names(tracks)
    if CHECK_VARIANTS in checks:
        issues += detect_artist_variants(tracks)
    result = merge_overlapping(issues)
    return result


def enabled(issue: Issue, checks: frozenset) -> bool:
    """Un problema trovato dall'AI o dal confronto con l'iPhone si tiene solo se il suo controllo è scelto."""
    check = KIND_CHECK.get(issue.kind)
    result = check is None or check in checks
    return result


# --------------------------------------------------------------------------- brani duplicati (stesso brano)

def title_core(title: str) -> str:
    """Il titolo senza le aggiunte tra parentesi o dopo " - " ("Brano (Remastered 2011)", "Brano - Live")."""
    result = _plain(TITLE_EXTRA.sub("", title or "")) or _plain(title or "")
    return result


def _song_key(track) -> tuple:
    result = (artist_norm(track.tags.artist or track.tags.album_artist), title_core(track.tags.title))
    return result


VERSION_WORDS = re.compile(
    r"\b(live|dal vivo|en vivo|unplugged|remix|rmx|mix|edit|acoustic|acustic[ao]|demo|instrumental|strumentale|"
    r"karaoke|reprise|extended|version|versione|cover|orchestral|piano)\b")


def version_marks(track) -> frozenset:
    """Le parole che distinguono una versione (live, remix, demo…) nel titolo o nell'album."""
    found = set()
    text = _plain(f"{track.tags.title} {track.tags.album}")
    for match in VERSION_WORDS.finditer(text):
        found.add(match.group(1))
    result = frozenset(found)
    return result


def suspicious_pairs(tracks: list, fingerprints: dict) -> list:
    """Le coppie di file che sembrano lo stesso brano con un audio diverso: stesso artista e titolo (senza le
    aggiunte tra parentesi), durata entro SAME_SONG_TOLERANCE, impronta diversa o mancante. Le copie con la stessa
    impronta contano una volta sola (quella è già certa)."""
    by_song = {}
    for track in tracks:
        if not track.error and track.length > 0 and track.tags.title:
            key = _song_key(track)
            if key[0] and key[1]:
                by_song.setdefault(key, []).append(track)
    result = []
    for group in by_song.values():
        representatives = []
        seen_prints = set()
        for track in group:
            value = fingerprints.get(str(track.path), "")
            if not value or value not in seen_prints:
                representatives.append(track)
                if value:
                    seen_prints.add(value)
        if len(representatives) > 1:
            representatives.sort(key=lambda track: (track.length, str(track.path).lower()))
            for first_index, first in enumerate(representatives):
                second_index = first_index + 1
                while (second_index < len(representatives)
                       and representatives[second_index].length - first.length <= SAME_SONG_TOLERANCE):
                    result.append((first, representatives[second_index]))
                    second_index += 1
    return result


AI_PAIRS_SYSTEM = """You help find duplicate songs in a personal music library. Each line is a pair of files with \
the same artist, a similar title and almost the same duration, but different audio data and different version \
words. Decide for each pair whether both files are the SAME recording (same performance: another format, bitrate or \
encoding, a remaster of the same master, the same track on an album and on a compilation) or DIFFERENT versions \
(live, remix, edit, acoustic, demo, re-recording, cover, another language). Use title details, album names and \
folder names. Answer for every pair; confidence "high" only when the details agree. Write the reason in Italian, \
short and concrete."""

AI_PAIRS_SCHEMA = {
    "type": "object",
    "properties": {
        "pairs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pair": {"type": "string"},
                    "same": {"type": "boolean"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "reason": {"type": "string"},
                },
                "required": ["pair", "same", "confidence", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["pairs"],
    "additionalProperties": False,
}


def _pair_side(track) -> str:
    tags = track.tags
    folder = "/".join(Path(track.path).parent.parts[-2:])
    total = int(round(track.length))
    result = (f"{tags.title} | artist: {tags.artist or tags.album_artist} | album: {tags.album} | "
              f"{total // 60}:{total % 60:02d} | {Path(track.path).suffix.lower().lstrip('.')} | folder: {folder}")
    return result


def ai_pairs(provider, pairs: list, progress: Optional[ProgressFn] = None,
             cancel: Optional[threading.Event] = None) -> tuple:
    """({indice della coppia: (stesso brano, motivo)}, errori). Le coppie senza risposta non ci sono."""
    from .ai import AIError
    verdicts = {}
    errors = []
    start = 0
    while start < len(pairs) and not is_cancelled(cancel) and not errors:
        batch = pairs[start:start + AI_PAIRS_BATCH]
        if progress is not None:
            progress(start, len(pairs), f"l'AI confronta {len(batch)} coppie di versioni forse diverse")
        lines = []
        for offset, (first, second) in enumerate(batch):
            lines.append(f"P{start + offset + 1}\n   A: {_pair_side(first)}\n   B: {_pair_side(second)}")
        try:
            reply = provider.ask_json(AI_PAIRS_SYSTEM, "PAIRS\n" + "\n".join(lines), AI_PAIRS_SCHEMA)
            for answer in reply.get("pairs", []):
                label = str(answer.get("pair", ""))
                if label.startswith("P") and label[1:].isdigit():
                    index = int(label[1:]) - 1
                    if start <= index < start + len(batch):
                        confidence = str(answer.get("confidence", "low"))
                        reason = f"AI ({confidence}): {str(answer.get('reason', '')).strip()}"
                        verdicts[index] = (bool(answer.get("same")), reason)
        except AIError as exc:
            errors.append(f"brani duplicati: {exc}")
            log.warning("Confronto dei brani duplicati con l'AI non riuscito: %s", exc)
        start += AI_PAIRS_BATCH
    result = (verdicts, errors)
    return result


class _Clusters:
    """Gruppi di file dello stesso brano (unione di coppie)."""

    def __init__(self) -> None:
        self.parent = {}
        self.tracks = {}
        self.notes = {}

    def _root(self, key: str) -> str:
        root = key
        while self.parent[root] != root:
            root = self.parent[root]
        self.parent[key] = root
        return root

    def add(self, track) -> str:
        key = str(track.path)
        if key not in self.parent:
            self.parent[key] = key
            self.tracks[key] = track
        result = self._root(key)
        return result

    def join(self, first, second, note: str = "") -> None:
        first_root = self.add(first)
        second_root = self.add(second)
        notes = self.notes.pop(second_root, []) if first_root != second_root else []
        if first_root != second_root:
            self.parent[second_root] = first_root
        merged = self.notes.setdefault(first_root, [])
        for text in notes + ([note] if note else []):
            if text not in merged:
                merged.append(text)

    def groups(self) -> list:
        """[([Track], [note])], i file in ordine di percorso."""
        by_root = {}
        for key, track in self.tracks.items():
            by_root.setdefault(self._root(key), []).append(track)
        result = []
        for root, members in by_root.items():
            if len(members) > 1:
                members.sort(key=lambda track: str(track.path).lower())
                result.append((members, self.notes.get(root, [])))
        result.sort(key=lambda entry: str(entry[0][0].path).lower())
        return result


def _copy_line(tracks: list, prints: dict) -> str:
    places = []
    for track in tracks:
        places.append(f"{track.tags.album or _short(Path(track.path).parent)} "
                      f"({Path(track.path).suffix.lower().lstrip('.')})")
    values = set()
    for track in tracks:
        values.add(prints.get(str(track.path), "") or str(track.path))
    how = "stesso audio" if len(values) == 1 else "stesso brano, file diversi"
    result = f"«{tracks[0].tags.title}» — {how}: " + "; ".join(places)
    return result


def detect_same_songs(tracks: list, fingerprints: dict, provider=None, progress: Optional[ProgressFn] = None,
                      cancel: Optional[threading.Event] = None, skip: frozenset = frozenset()) -> tuple:
    """Lo stesso brano in più file, anche in album diversi: (problemi, errori dell'AI).
      * stesso audio (impronta): certo;
      * stesso artista e titolo, durata entro 2 secondi, audio diverso (un MP3 e un FLAC, due codifiche): lo stesso
        brano, se titolo e album non nominano versioni diverse (live, remix, demo…);
      * con versioni diverse nominate la coppia è dubbia: decide l'AI, se c'è (solo queste coppie, mai tutti i brani);
        senza AI resta "da controllare".
    Un problema per artista, una riga per brano; nessuna correzione: quale copia tenere lo decide l'utente. skip: i
    file già segnalati come doppi nello stesso album."""
    clusters = _Clusters()
    by_print = {}
    for track in tracks:
        value = fingerprints.get(str(track.path), "")
        if value and not track.error and str(track.path) not in skip:
            by_print.setdefault(value, []).append(track)
    for group in by_print.values():
        for other in group[1:]:
            clusters.join(group[0], other)
    doubtful = []
    for first, second in suspicious_pairs(tracks, fingerprints):
        if str(first.path) not in skip and str(second.path) not in skip:
            if version_marks(first) == version_marks(second):
                clusters.join(first, second)
            else:
                doubtful.append((first, second))
    verdicts = {}
    errors = []
    if provider is not None and doubtful and not is_cancelled(cancel):
        verdicts, errors = ai_pairs(provider, doubtful[:AI_MAX_PAIRS], progress, cancel)
    for index, (first, second) in enumerate(doubtful):
        same, reason = verdicts.get(index, (True, "da controllare: forse versioni diverse"))
        if same:
            clusters.join(first, second, reason)
    by_artist = {}
    for members, notes in clusters.groups():
        by_artist.setdefault(members[0].display_artist, []).append((members, notes))
    issues = []
    number = 0
    for artist in sorted(by_artist, key=str.lower):
        songs = by_artist[artist]
        number += 1
        files = []
        lines = []
        used_ai = False
        for members, notes in songs:
            for track in members:
                files.append(track.path)
            line = _copy_line(members, fingerprints)
            if notes:
                line += " (" + "; ".join(notes) + ")"
                used_ai = used_ai or any(note.startswith("AI") for note in notes)
            lines.append(line)
        shown = lines[:10]
        if len(lines) > 10:
            shown.append(f"… e altri {len(lines) - 10}")
        detail = ("Lo stesso brano in più file. Può essere giusto (l'album originale e una raccolta, un MP3 e un FLAC "
                  "tenuti apposta) oppure un doppione da togliere: quale tenere lo decidi tu (Mostra i brani).\n"
                  + "\n".join(shown))
        issues.append(Issue(KIND_DUPLICATE, SEVERITY_LOW, f"{artist}: {_tracks_text(len(songs))} in più copie",
                            detail, files, origin=ORIGIN_AI if used_ai else ORIGIN_RULE, rule_id=f"R15.{number}"))
    if len(doubtful) > AI_MAX_PAIRS and provider is not None:
        errors.append(f"brani duplicati: l'AI ha visto le prime {AI_MAX_PAIRS} coppie dubbie su {len(doubtful)}; le "
                      "altre sono segnate \"da controllare\"")
    result = (issues, errors)
    return result


# --------------------------------------------------------------------------- iPhone

def detect_phantoms(phone_tracks: list) -> list:
    """I brani "fantasma" dell'iPhone: nell'elenco dell'app Musica, ma senza il loro file (PhoneTrack.missing_file,
    segnato alla lettura dall'iPhone)."""
    names = []
    for item in phone_tracks:
        if item.missing_file:
            names.append(f"{item.display_artist} — {item.tags.album} — {item.tags.title} ({item.remote_path})")
    issues = []
    if names:
        issues.append(Issue(
            KIND_UNREADABLE, SEVERITY_HIGH, f"{_tracks_text(len(names))} dell'iPhone senza file (fantasmi)",
            "Sono nell'elenco dell'app Musica, ma il loro file sull'iPhone non c'è: non si possono ascoltare. "
            "Toglili dalla scheda iPhone: Mostra → \"Senza file sull'iPhone\", tasto destro → Elimina dall'iPhone. "
            "Sul PC non cambia niente.", names, rule_id="I4"))
    return issues


def compare_with_library(phone_tracks: list, library_tracks: list) -> list:
    """La musica dell'app Musica dell'iPhone (phone_library.PhoneTrack) confrontata con la Libreria del PC, per
    artista, album e titolo. Sull'iPhone il programma non scrive: i problemi non hanno correzioni automatiche."""
    index = PhoneIndex(phone_tracks)
    stale = []
    missing_by_album = {}
    present_albums = set()
    found_pids = set()
    for track in library_tracks:
        if not track.error:
            status, item, _found = device_status(track, index)
            if status == DEVICE_ABSENT:
                missing_by_album.setdefault(track.album_key, []).append(track)
            else:
                found_pids.add(item.pid)
                present_albums.add(track.album_key)
                if status == DEVICE_STALE:
                    stale.append(track)
    issues = []
    if stale:
        issues.append(Issue(
            KIND_NOT_UPDATED, SEVERITY_HIGH, f"{len(stale)} brani sull'iPhone con tag diversi da quelli del PC",
            "Il brano è nell'app Musica dell'iPhone, ma titolo, artista, album, anno, genere o numeri non sono "
            "quelli del PC (per esempio dopo una modifica sul PC). Nella scheda PC, la colonna iPhone mostra le "
            "differenze.", [t.path for t in stale], rule_id="I1"))
    incomplete = []
    for key, tracks in missing_by_album.items():
        if key in present_albums:
            incomplete.append((key, tracks))
    number = 0
    for key, tracks in sorted(incomplete, key=lambda item: (item[0][0].lower(), item[0][1].lower())):
        number += 1
        issues.append(Issue(
            KIND_FEW_TRACKS, SEVERITY_MEDIUM, f"{key[0]} — {key[1]}: mancano {_tracks_text(len(tracks))} sull'iPhone",
            "Sul PC l'album ha più brani di quelli nell'app Musica dell'iPhone.", [t.path for t in tracks],
            rule_id=f"I2.{number}"))
    orphans = []
    for item in phone_tracks:
        if item.pid not in found_pids:
            orphans.append(item)
    if orphans:
        names = []
        for item in orphans:
            names.append(f"{item.display_artist} — {item.tags.album} — {item.tags.title}")
        issues.append(Issue(
            KIND_ONLY_ON_DEVICE, SEVERITY_MEDIUM, f"{len(orphans)} brani sull'iPhone che non sono sul PC",
            "Non c'è un brano con lo stesso artista, album e titolo nella Libreria del PC. Se vuoi conservarli, "
            "salvali sul PC dalla scheda iPhone (tasto destro → Salva su PC); a volte sono solo scritti in modo "
            "diverso.", names, rule_id="I3"))
    return issues


# --------------------------------------------------------------------------- AI

AI_SYSTEM = """You audit a personal music library for an organizer app. Each album line gives an id, the album \
artist, the album, the years, the number of tracks, the track numbers present, the declared track total, the \
folder and the genres. The rule findings were computed by simple rules.

Find the problems the owner usually has:
- "non_aggiornato": files whose tags will not show as updated (only if the data shows it);
- "album_incompleto": albums with few tracks or missing track numbers;
- "collezione_divisa": one collection split into several albums: the same album with different spellings, a disc \
marker in the album name, a compilation without album artist, the same artist spelled differently, featured artists \
in the album artist;
- "duplicato": the same track twice INSIDE the same album, or the same album twice. The same song on several different albums (the original album and a compilation, a live album) is legitimate: never report it;
- "tag_mancanti": missing or placeholder tags.

Rules:
- Confirm a rule finding only by not listing it in false_positives; list in false_positives the rule ids that are \
not real problems (for example different albums that only share a generic name such as "Greatest Hits").
- Add in issues only problems the rule findings do not already describe, or a better fix for one of them.
- A fix sets fields on EVERY track of the albums listed: give the actual text to write (an album NAME, never an \
album id such as A3), or "" to leave a field unchanged. Use "Artisti vari" as album artist of a compilation. year is \
four digits or "".
- Use only album ids that appear in the table. Write title, explanation and reason in Italian, short and concrete.
- Return no issue at all rather than a doubtful one."""

AI_SCHEMA = {
    "type": "object",
    "properties": {
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "enum": list(AI_KINDS)},
                    "severity": {"type": "string", "enum": [SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW]},
                    "title": {"type": "string"},
                    "explanation": {"type": "string"},
                    "albums": {"type": "array", "items": {"type": "string"}},
                    "fix_album": {"type": "string"},
                    "fix_album_artist": {"type": "string"},
                    "fix_artist": {"type": "string"},
                    "fix_year": {"type": "string"},
                    "fix_genre": {"type": "string"},
                },
                "required": ["kind", "severity", "title", "explanation", "albums", "fix_album", "fix_album_artist",
                             "fix_artist", "fix_year", "fix_genre"],
                "additionalProperties": False,
            },
        },
        "false_positives": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"rule_id": {"type": "string"}, "reason": {"type": "string"}},
                "required": ["rule_id", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["issues", "false_positives"],
    "additionalProperties": False,
}


def _numbers_text(album_tracks: list) -> str:
    parts = []
    for disc, numbers in sorted(_numbers_by_disc(album_tracks).items()):
        listed = ",".join(str(n) for n in sorted(numbers))
        if disc > 1:
            parts.append(f"disco {disc}: {listed}")
        else:
            parts.append(listed)
    result = "; ".join(parts) or "nessuno"
    return result


def album_lines(groups: dict, keys: list) -> list:
    """(id, riga) per ogni album: una tabella compatta, senza percorsi completi."""
    lines = []
    for index, key in enumerate(keys, start=1):
        album_tracks = groups[key]
        years = sorted({t.tags.year for t in album_tracks if t.tags.year})
        genres = sorted({t.tags.genre for t in album_tracks if t.tags.genre})
        declared = max([t.tags.track_total or 0 for t in album_tracks] + [0])
        artists = sorted({t.tags.artist for t in album_tracks if t.tags.artist and t.tags.artist != key[0]})
        folder = "/".join(album_tracks[0].path.parent.parts[-2:])
        text = (f"A{index} | album artist: {key[0]} | album: {key[1]} | anni: {','.join(years) or '-'} | brani: "
                f"{len(album_tracks)} | numeri: {_numbers_text(album_tracks)} | totale dichiarato: {declared or '-'} "
                f"| cartella: {folder} | generi: {','.join(genres) or '-'}")
        if artists:
            text += f" | altri artisti: {', '.join(artists[:6])}"
        lines.append((f"A{index}", text))
    return lines


def _issue_from_ai(item: dict, ids: dict, groups: dict) -> Optional[Issue]:
    keys = []
    for album_id in item.get("albums", []):
        if album_id in ids:
            keys.append(ids[album_id])
    result = None
    if keys:
        tracks = []
        for key in keys:
            tracks += groups[key]
        values = {}
        for name in FIX_FIELDS:
            value = str(item.get(f"fix_{name}", "")).strip()
            if name == "year" and value and not re.fullmatch(r"\d{4}", value):
                value = ""
            if re.fullmatch(r"A\d+", value):
                value = ""  # un id della tabella scritto al posto del valore (capita ai modelli piccoli)
            if value:
                values[name] = value
        fix = None
        changes = _unify_changes(tracks, values) if values else []
        if changes and item.get("kind") != KIND_DUPLICATE:  # quale doppione tenere lo decide l'utente
            described = ", ".join(f"{name} \"{value}\"" for name, value in values.items())
            fix = Fix(FIX_TAGS, f"Imposta {described} su tutti i brani", changes=changes)
        result = Issue(item.get("kind", KIND_SPLIT), item.get("severity", SEVERITY_LOW),
                       str(item.get("title", "")).strip() or "Problema trovato dall'AI",
                       str(item.get("explanation", "")).strip(), [t.path for t in tracks], fix, ORIGIN_AI)
    return result


def _rule_issue_albums(issue: Issue, path_to_key: dict) -> set:
    keys = set()
    for path in issue.files:
        key = path_to_key.get(str(path))
        if key is not None:
            keys.add(key)
    return keys


def ai_review(provider, tracks: list, issues: list, progress: Optional[ProgressFn] = None,
              cancel: Optional[threading.Event] = None) -> tuple:
    """(nuovi problemi dell'AI, errori). Segna sulle regole che l'AI scarta il suo motivo (Issue.ai_note)."""
    from .ai import AIError

    groups = group_by_album(tracks)
    keys = sorted(groups, key=lambda k: (album_norm(k[1]), artist_norm(k[0])))
    path_to_key = {}
    for key, album_tracks in groups.items():
        for track in album_tracks:
            path_to_key[str(track.path)] = key
    by_rule_id = {issue.rule_id: issue for issue in issues if issue.rule_id}
    found = []
    errors = []
    chunks = []
    start = 0
    while start < len(keys):
        chunks.append(keys[start:start + AI_CHUNK_ALBUMS])
        start += AI_CHUNK_ALBUMS
    index = 0
    while index < len(chunks) and not is_cancelled(cancel):
        chunk = chunks[index]
        if progress is not None:
            progress(index, len(chunks), f"analisi AI {index + 1} di {len(chunks)}")
        lines = album_lines(groups, chunk)
        ids = {}
        for (album_id, _text), key in zip(lines, chunk):
            ids[album_id] = key
        id_of = {key: album_id for album_id, key in ids.items()}
        rule_lines = []
        for issue in issues:
            albums = _rule_issue_albums(issue, path_to_key) & set(chunk)
            if albums and issue.rule_id:
                listed = ",".join(sorted(id_of[key] for key in albums))
                rule_lines.append(f"{issue.rule_id} | {issue.kind} | {issue.title} | album: {listed}")
        user = ("ALBUMS\n" + "\n".join(text for _id, text in lines) + "\n\nRULE FINDINGS\n"
                + ("\n".join(rule_lines) or "none"))
        try:
            data = provider.ask_json(AI_SYSTEM, user, AI_SCHEMA)
            for item in data.get("issues", []):
                if isinstance(item, dict):
                    issue = _issue_from_ai(item, ids, groups)
                    if issue is not None:
                        found.append(issue)
            for item in data.get("false_positives", []):
                rule = by_rule_id.get(str(item.get("rule_id", "")))
                if rule is not None:
                    rule.ai_note = str(item.get("reason", "")).strip() or "L'AI ritiene che non sia un problema"
        except AIError as exc:
            errors.append(str(exc))
            log.warning("Analisi AI non riuscita: %s", exc)
        index += 1
    result = (found, errors)
    return result


# --------------------------------------------------------------------------- scansione completa

def scan_tracks(tracks: list, target: str, provider=None, check_files: bool = True,
                phone_tracks: Optional[list] = None, library_tracks: Optional[list] = None,
                progress: Optional[ProgressFn] = None, cancel: Optional[threading.Event] = None,
                checks: frozenset = ALL_CHECKS, fingerprints: Optional[dict] = None) -> ScanReport:
    """Il controllo: le regole dei controlli scelti (checks), poi l'AI se c'è un fornitore. Con phone_tracks (la
    musica dell'app Musica, i cui brani sono anche tracks) è dell'iPhone, confrontato con library_tracks.
    fingerprints: {percorso: impronta dell'audio} per i brani duplicati (senza, solo quelli sospetti per i tag)."""
    assign_groups(tracks)
    report = ScanReport(target=target, tracks_scanned=len(tracks), albums_scanned=len(group_by_album(tracks)))
    issues = rule_issues(tracks, check_files, progress, cancel, checks)
    if provider is not None and not is_cancelled(cancel) and checks & AI_REVIEW_CHECKS:
        report.ai_profile = provider.profile.name
        found, errors = ai_review(provider, tracks, issues, progress, cancel)
        for issue in drop_repeated(found, issues):
            if enabled(issue, checks):
                issues.append(issue)
        report.ai_errors = errors
    if CHECK_DUPLICATES in checks and not is_cancelled(cancel):
        skip = set()
        for issue in issues:
            if issue.kind == KIND_DUPLICATE:
                for path in issue.files:
                    skip.add(str(path))
        if progress is not None:
            progress(0, 0, "brani duplicati")
        found, errors = detect_same_songs(tracks, fingerprints or {}, provider, progress, cancel, frozenset(skip))
        issues += found
        report.ai_errors += errors
        if provider is not None:
            report.ai_profile = provider.profile.name
    if phone_tracks is not None:
        # sull'iPhone il programma non scrive: le correzioni si fanno sui brani del PC
        for issue in issues:
            if issue.fix is not None:
                issue.fix = None
                issue.detail += " Correggi i brani sul PC (scheda PC)."
        if library_tracks is not None:
            for issue in compare_with_library(phone_tracks, library_tracks):
                if enabled(issue, checks):
                    issues.append(issue)
        if CHECK_UNREADABLE in checks:
            issues += detect_phantoms(phone_tracks)
    issues.sort(key=lambda issue: issue.sort_key())
    report.issues = issues
    report.cancelled = is_cancelled(cancel)
    return report


def report_text(report: ScanReport) -> str:
    lines = [f"Controllo di {report.target} — {time.strftime('%Y-%m-%d %H:%M')}",
             f"{report.tracks_scanned} brani, {report.albums_scanned} album, {len(report.issues)} problemi"]
    if report.ai_profile:
        lines.append(f"Analisi AI: {report.ai_profile}")
    for error in report.ai_errors:
        lines.append(f"Errore AI: {error}")
    if report.cancelled:
        lines.append("Controllo interrotto: i risultati sono parziali")
    for issue in report.issues:
        lines += ["", f"[{issue.severity}] {KIND_LABELS.get(issue.kind, issue.kind)} ({issue.origin}): {issue.title}",
                  f"    {issue.detail}"]
        if issue.ai_note:
            lines.append(f"    AI: {issue.ai_note}")
        if issue.fix is not None:
            lines.append(f"    Correzione proposta: {issue.fix.description}")
        for path in issue.files[:50]:
            lines.append(f"    - {path}")
        if len(issue.files) > 50:
            lines.append(f"    … e altri {len(issue.files) - 50}")
    result = "\n".join(lines) + "\n"
    return result


def save_report(report: ScanReport, folder: Path) -> Path:
    """Il rapporto in testo nella cartella dati (scansioni/), conservato."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"scansione_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    path.write_text(report_text(report), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- correzioni

def tag_changes_of(fix: Fix) -> list:
    """Le modifiche dei tag di una correzione FIX_TAGS: [(percorso, {campo: valore})]. Nessun file viene scritto:
    chi chiama le mette in sospeso (overlay) per le copie dell'iPhone."""
    result = []
    if fix.action == FIX_TAGS:
        for path, values in fix.changes:
            result.append((Path(path), dict(values)))
    return result
