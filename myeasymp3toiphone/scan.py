# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La scansione della libreria (sul PC, sul posto) o della musica sull'iPhone, per trovare i problemi tipici. L'elenco
completo delle regole, il loro ordine e il perché sono in checks_requirements.md; in breve, a livelli:

  1. file: illeggibili (R5), percorsi troppo lunghi (R19), vecchi tag ID3v1/APE (R2, R3), formati non supportati (R18);
  2. campi del brano: tag mancanti o segnaposto (R6), numero o artista nel titolo (R20), spazi in più (R21), lettere
     accentate rovinate (R22);
  3. nomi: lo stesso artista scritto in modi diversi (R23 maiuscole/accenti/spazi, R14 punteggiatura/ordine, R16
     forse lo stesso), in tutta la musica;
  4. coerenza dell'album: cartella divisa (R11), album scritto in modi diversi (R12, R13, R24), artista dell'album
     (R25, R26), spunta Compilation (R27), album che l'iPhone unisce (R28), numeri e totali (R30, R31);
  5. completezza: numeri di traccia mancanti (R9), album di 1-2 brani (R10);
  6. doppioni: copie "(2)" (R7), stesso numero e titolo (R8), stesso numero e titoli diversi (R29), stesso brano
     (R15).

Ogni livello vede le correzioni di quelli prima come già fatte (scan_rules.RuleView). Sull'iPhone girano le regole
di prima (fino a R16), più il confronto con il PC (I1-I4). Poi, se c'è un profilo AI, l'AI riceve una tabella compatta
degli album e i problemi trovati: li conferma o li scarta, ne aggiunge altri e propone le correzioni dei tag.
"""

from __future__ import annotations

import logging
import os
import re
import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import mutagen
from mutagen.apev2 import APENoHeaderError, APEv2

from .library import (
    UNKNOWN_ALBUM, UNKNOWN_ARTIST, Track, album_folder, assign_groups, best_spelling, group_by_album,
    is_cancelled,
)
from .artist_names import (
    candidate_pairs, clusters, duet_parts, musicbrainz_keys, variant_key,
)
from .artist_names import ask_ai as ask_ai_names
from . import cue
from .i18n import tr
from .names import LEVEL_PUNCT, POLICY_MOST, choose_spelling, fold
from .phone_library import DEVICE_ABSENT, DEVICE_STALE, PhoneIndex, device_status
from .tags import OLD_APE, OLD_ID3V1, OLD_TAG_REMOVED, TrackTags

log = logging.getLogger(__name__)

KIND_NOT_UPDATED = "non_aggiornato"
KIND_FEW_TRACKS = "album_incompleto"
KIND_SPLIT = "collezione_divisa"
KIND_DUPLICATE = "duplicato"
KIND_MISSING_TAGS = "tag_mancanti"
KIND_UNREADABLE = "illeggibile"
KIND_ONLY_ON_DEVICE = "solo_su_iphone"
KIND_ONLINE = "catalogo_online"          # Verifica online: tag diversi da quelli del catalogo
KIND_FORMAT = "formato_non_supportato"
KIND_NAMES = "nomi_scritti_diversi"
KIND_LABELS = {
    KIND_NOT_UPDATED: "File che non si aggiornano",
    KIND_FEW_TRACKS: "Album con pochi brani o numeri sbagliati",
    KIND_SPLIT: "Album divisi o incoerenti",
    KIND_DUPLICATE: "Brani duplicati",
    KIND_MISSING_TAGS: "Tag mancanti o scritti male",
    KIND_UNREADABLE: "File illeggibili",
    KIND_ONLY_ON_DEVICE: "Solo sull'iPhone",
    KIND_ONLINE: "Diversi dal catalogo online",
    KIND_FORMAT: "Formati non supportati",
    KIND_NAMES: "Nomi scritti in modi diversi",
}
AI_KINDS = (KIND_NOT_UPDATED, KIND_FEW_TRACKS, KIND_SPLIT, KIND_DUPLICATE, KIND_MISSING_TAGS)

SEVERITY_HIGH = "alta"
SEVERITY_MEDIUM = "media"
SEVERITY_LOW = "bassa"
SEVERITY_ORDER = {SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 1, SEVERITY_LOW: 2}

ORIGIN_RULE = "regola"
ORIGIN_AI = "AI"
ORIGIN_ONLINE = "online"

FIX_TAGS = "tags"            # modifiche dei tag: restano in sospeso (overlay), i file sul PC non cambiano

VARIOUS_ARTISTS = "Artisti Vari"      # con le iniziali maiuscole (D-1), come quello che l'iPhone ha già
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
    (CHECK_FILES, "File: vecchi tag e formati",
     "MP3 con un vecchio tag ID3v1 diverso o un tag APE; file che non sono MP3, FLAC o M4A; sull'iPhone, brani con "
     "tag diversi da quelli del PC"),
    (CHECK_FEW, "Album con pochi brani o numeri sbagliati",
     "numeri di traccia mancanti, meno brani del totale dichiarato, album di 1-2 brani, numeri di disco mancanti, "
     "totali diversi tra i brani"),
    (CHECK_SPLIT, "Album divisi o incoerenti",
     "una cartella con album diversi, lo stesso album scritto in modi diversi o con \"CD 1\" nel nome, artista "
     "dell'album diverso o mancante, spunta Compilation, album che l'iPhone unirebbe"),
    (CHECK_VARIANTS, "Nomi scritti in modi diversi",
     "lo stesso artista con maiuscole, accenti o spazi diversi (\"Queen\" e \"queen\"), \"The Beatles\" e "
     "\"Beatles\", \"AC/DC\" e \"ACDC\": una grafia sola in tutta la musica"),
    (CHECK_MISSING, "Tag mancanti o scritti male",
     "brani senza titolo, album o artista o con un segnaposto (\"Unknown Artist\", \"Track 01\"), numero o artista "
     "nel titolo, spazi in più, lettere accentate rovinate"),
    (CHECK_UNREADABLE, "File illeggibili", "file danneggiati, bloccati, disponibili solo online o con il percorso "
     "troppo lungo"),
    (CHECK_DUPLICATES, "Brani duplicati",
     "lo stesso brano due volte nello stesso album e formato: stesso audio anche con tag diversi, oppure stessa "
     "durata, titolo e artista; vanno bene una copia in un altro formato (FLAC e MP3) o in un altro album, e le "
     "versioni nominate nel titolo (Unplugged, Live, Remix…)"),
)
ALL_CHECKS = frozenset(check_id for check_id, _label, _note in CHECKS)
KIND_CHECK = {KIND_NOT_UPDATED: CHECK_FILES, KIND_FEW_TRACKS: CHECK_FEW, KIND_SPLIT: CHECK_SPLIT,
              KIND_DUPLICATE: CHECK_DUPLICATES, KIND_MISSING_TAGS: CHECK_MISSING, KIND_UNREADABLE: CHECK_UNREADABLE,
              KIND_FORMAT: CHECK_FILES, KIND_NAMES: CHECK_VARIANTS}
AI_REVIEW_CHECKS = frozenset({CHECK_FILES, CHECK_FEW, CHECK_SPLIT, CHECK_VARIANTS, CHECK_MISSING})  # per album
SAME_SONG_TOLERANCE = 2.0     # secondi: lo stesso brano in due file ha quasi la stessa durata
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
    step: int = 99         # il passo delle regole che l'ha trovato (rule_issues): a parità di campo vince il passo dopo

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
    cancelled: bool = False         # annullato durante le regole: i loro risultati sono parziali
    stopped: list = field(default_factory=list)   # annullati dopo le regole (AI, MusicBrainz, Verifica online): senza
    online_notes: list = field(default_factory=list)   # gli album che la Verifica online non ha trovato (solo rapporto)

    def counts(self) -> dict:
        result = Counter()
        for issue in self.issues:
            result[issue.kind] += 1
        return dict(result)


# --------------------------------------------------------------------------- testi

def _plain(text: str) -> str:
    """Senza maiuscole, accenti e punteggiatura (names.LEVEL_PUNCT)."""
    result = fold(text, LEVEL_PUNCT)
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


def _numbers_count(count: int) -> str:
    if count == 1:
        result = "1 numero"
    else:
        result = f"{count} numeri"
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


def _old_tag_changes(paths: list, name: str) -> list:
    """Le correzioni "togli questo vecchio tag" (tags.OLD_ID3V1, OLD_APE): una per file."""
    result = []
    for path in paths:
        result.append((path, {name: OLD_TAG_REMOVED}))
    return result


def detect_file_problems(tracks: list, progress: Optional[ProgressFn] = None,
                         cancel: Optional[threading.Event] = None) -> list:
    """MP3 con un vecchio ID3v1 diverso o con un tag APE: le copie inviate all'iPhone ne sono ripulite
    (tags.prepare_copy); la correzione li toglie anche dai file del PC, solo dopo l'elenco approvato (gui.pc_write)."""
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
    cleaned = (" Le copie inviate all'iPhone ne sono già ripulite. Applica la correzione lo toglie anche dai file "
               "del PC, dopo l'elenco dei file da approvare (i suoi valori passano prima nel tag ID3v2).")
    issues = []
    if v1_stale:
        issues.append(Issue(
            KIND_NOT_UPDATED, SEVERITY_LOW, f"{len(v1_stale)} MP3 con un vecchio tag ID3v1 diverso",
            "Oltre al tag moderno (ID3v2) questi file hanno un vecchio tag ID3v1 con valori diversi: alcuni lettori, "
            "autoradio e app leggono quello e mostrano i valori vecchi." + cleaned, v1_stale,
            Fix(FIX_TAGS, "Togli il tag ID3v1 dai file del PC", changes=_old_tag_changes(v1_stale, OLD_ID3V1)),
            rule_id="R2"))
    if with_ape:
        issues.append(Issue(
            KIND_NOT_UPDATED, SEVERITY_LOW, f"{len(with_ape)} MP3 con un tag APE",
            "Questi file hanno anche un tag APE (di solito lasciato da programmi di normalizzazione del volume): "
            "alcuni lettori lo leggono al posto dell'ID3." + cleaned, with_ape,
            Fix(FIX_TAGS, "Togli il tag APE dai file del PC", changes=_old_tag_changes(with_ape, OLD_APE)),
            rule_id="R3"))
    return issues


def detect_unreadable(tracks: list) -> list:
    """R5: i file che non si leggono. Quelli con il percorso troppo lungo li spiega R19 (scan_rules)."""
    from .scan_rules import MAX_PATH
    broken = []
    for track in tracks:
        if track.error and len(str(track.path)) < MAX_PATH:
            broken.append(track.path)
    issues = []
    if broken:
        issues.append(Issue(KIND_UNREADABLE, SEVERITY_HIGH, f"{len(broken)} file illeggibili",
                            "Questi file non si possono leggere: sono danneggiati o non sono davvero file audio.",
                            broken, rule_id="R5"))
    return issues


PLACEHOLDER_KEYS = frozenset({
    "unknown", "unknown artist", "unknown album", "unknown title", "no artist", "no album", "artist", "album",
    "sconosciuto", "artista sconosciuto", "album sconosciuto", "artista", "senza titolo", "senza nome", "untitled",
    "various", "title", "titolo",
})
PLACEHOLDER_TITLE = re.compile(r"^(?:track|traccia|brano|pista|audio track|titolo|title|untitled|senza titolo)"
                               r"(?: ?\d+)?$")


def is_placeholder(name: str, value: str) -> bool:
    """Un valore che tiene il posto di quello vero: "Unknown Artist", "Album sconosciuto", "Track 01"."""
    plain = _plain(value or "")
    if name == "title":
        result = bool(PLACEHOLDER_TITLE.match(plain))
    else:
        result = plain in PLACEHOLDER_KEYS and plain != "various"
    return result


def _empty(track: Track, name: str) -> bool:
    value = getattr(track.tags, name) or ""
    result = not value or is_placeholder(name, value)
    return result


def _guess_from_path(track: Track) -> dict:
    """Album e artista dalle cartelle (…/Artista/Album/file), titolo dal nome del file senza "NN - ", al posto dei
    campi vuoti o segnaposto; mai un segnaposto né il valore che c'è già."""
    guessed = {}
    folder = track.path.parent.name
    match = YEAR_SUFFIX.match(folder)
    if match:
        folder = match.group(1)
    artist_folder = track.path.parent.parent.name
    if _empty(track, "album") and folder:
        guessed["album"] = folder
    if _empty(track, "artist") and _empty(track, "album_artist") and artist_folder:
        guessed["artist"] = artist_folder
    if _empty(track, "title"):
        title_match = TRACK_PREFIX.match(track.path.stem)
        if title_match:
            guessed["title"] = title_match.group(3).strip()
        else:
            guessed["title"] = track.path.stem
    result = {}
    for name, value in guessed.items():
        if value != (getattr(track.tags, name) or "") and not is_placeholder(name, value):
            result[name] = value
    return result


def detect_missing_tags(tracks: list) -> list:
    """R6: brani senza titolo, album o artista, o con un segnaposto ("Unknown Artist", "Track 01"); la correzione li
    ricava dai nomi di cartelle e file, quando ci sono."""
    by_folder = {}
    for track in tracks:
        missing = not track.error and (_empty(track, "title") or _empty(track, "album")
                                       or (_empty(track, "artist") and _empty(track, "album_artist")))
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
            "Titolo, album o artista mancano o sono un segnaposto (\"Unknown Artist\", \"Album sconosciuto\", "
            "\"Track 01\"): sull'iPhone i brani finiscono in \"Album sconosciuto\" / \"Artista sconosciuto\" e la "
            "collezione appare divisa.",
            [track.path for track in folder_tracks], fix, rule_id=f"R6.{number}"))
    return issues


def _same_place(first: Track, second: Track) -> bool:
    """Due brani dello stesso album e dello stesso formato: solo lì due copie dello stesso brano sono un doppione."""
    result = first.album_key == second.album_key and first.path.suffix.lower() == second.path.suffix.lower()
    return result


def one_per_format(paths: list) -> bool:
    """Le copie di un brano sono una per formato (un FLAC e un MP3…): tenere lo stesso album in più formati va bene,
    non è un doppione. Due file dello stesso formato sì."""
    suffixes = []
    for path in paths:
        suffixes.append(Path(path).suffix.lower())
    result = len(suffixes) > 1 and len(set(suffixes)) == len(suffixes)
    return result


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
            # nella stessa cartella dell'album: due copie in cartelle diverse le dicono R32 e R33 (copie dell'album)
            key = (track.album_key, album_folder(track.path), track.tags.disc_number or 1, track.tags.track_number,
                   _plain(track.tags.title))
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
        if len(paths) > 1 and not one_per_format(paths):    # un FLAC e un MP3 dello stesso brano: va bene
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


def track_gaps(album_tracks: list) -> list:
    """I numeri di traccia che mancano ("5", o "2-3" per il disco 2), fino al più alto o alle tracce totali
    dichiarate. Di solito ogni disco riparte da 1; se invece i numeri dei dischi non si ripetono mai (disco 1: 1-16,
    disco 2: 17-30…) la numerazione è unica per tutto l'album e i buchi si cercano sull'insieme."""
    by_disc = _numbers_by_disc(album_tracks)
    totals = {}
    for track in album_tracks:
        disc = track.tags.disc_number or 1
        totals[disc] = max(totals.get(disc, 0), track.tags.track_total or 0)
    union = set()
    counted = 0
    for numbers in by_disc.values():
        union |= numbers
        counted += len(numbers)
    gaps = []
    if len(by_disc) > 1 and counted == len(union):          # numerazione unica su tutti i dischi
        highest = max(max(union), max(totals.values()))
        for position in range(1, highest + 1):
            if position not in union:
                gaps.append(str(position))
    else:
        for disc, numbers in sorted(by_disc.items()):
            highest = max(max(numbers), totals.get(disc, 0))
            for position in range(1, highest + 1):
                if position not in numbers:
                    gaps.append(f"{disc}-{position}" if disc > 1 else str(position))
    result = gaps
    return result


def album_gaps(album_tracks: list) -> tuple:
    """(numeri mancanti, brani della copia contata): un album tenuto in più formati (FLAC e MP3) sono più copie,
    magari numerate in modo diverso (una disco per disco, l'altra di seguito): i numeri si contano copia per copia e
    vale la più completa (a parità, quella con più brani)."""
    by_format = {}
    for track in album_tracks:
        by_format.setdefault(track.path.suffix.casefold(), []).append(track)
    best_gaps = None
    best_copy = album_tracks
    for suffix in sorted(by_format):
        copy = by_format[suffix]
        gaps = track_gaps(copy)
        better = best_gaps is None or len(gaps) < len(best_gaps) or \
            (len(gaps) == len(best_gaps) and len(copy) > len(best_copy))
        if better:
            best_gaps = gaps
            best_copy = copy
    result = (best_gaps or [], best_copy)
    return result


def _with_context(album_tracks: list, context: dict) -> list:
    """I brani dell'album controllati e quelli dello stesso album fuori dalla scelta (context: {(artista, album) in
    minuscolo: [brani]}), una volta sola."""
    result = list(album_tracks)
    seen = set()
    for track in album_tracks:
        seen.add(os.path.normcase(str(track.path)))
    key = album_tracks[0].album_key
    for track in context.get((key[0].casefold(), key[1].casefold()), []):
        path = os.path.normcase(str(track.path))
        if path not in seen:
            seen.add(path)
            result.append(track)
    return result


def detect_few_tracks(tracks: list, context: Optional[list] = None) -> list:
    """Album con numeri di traccia mancanti (R9) o con 1-2 brani (R10). context: tutti i brani della musica, quando si
    controlla solo una parte: un album va giudicato intero, anche con i brani che non sono stati scelti."""
    issues = []
    number = 0
    groups = group_by_album(tracks)
    by_key = {}
    for track in context or []:
        key = track.album_key
        by_key.setdefault((key[0].casefold(), key[1].casefold()), []).append(track)
    for key in sorted(groups, key=lambda k: (k[0].lower(), k[1].lower())):
        artist, album = key
        album_tracks = _with_context(groups[key], by_key) if by_key else groups[key]
        if album != UNKNOWN_ALBUM:
            number += 1
            gaps, copy = album_gaps(album_tracks)
            count = len(copy)
            files = [track.path for track in album_tracks]
            # FLAC + CUE: un file solo con tutte le tracce, i numeri "mancanti" sono dentro (cue.py)
            whole_disc = bool(gaps or count <= 2) and cue.all_images(album_tracks)
            if gaps and not whole_disc:
                positions = set()
                for track in copy:
                    if track.tags.track_number:
                        positions.add((track.tags.disc_number or 1, track.tags.track_number))
                expected = max(count, len(positions) + len(gaps))      # i numeri diversi, non i file
                severity = SEVERITY_HIGH if count * 2 <= expected else SEVERITY_MEDIUM
                shown = ", ".join(gaps[:15]) + ("…" if len(gaps) > 15 else "")
                issues.append(Issue(
                    KIND_FEW_TRACKS, severity, f"{artist} — {album}: mancano {_numbers_count(len(gaps))} di traccia "
                    f"({_tracks_text(count)} qui, l'album ne ha almeno {expected})",
                    f"Mancano i numeri di traccia {shown}. \"Verifica album online\" controlla l'elenco completo "
                    "nei cataloghi online.", files, rule_id=f"R9.{number}"))
            elif count <= 2 and not whole_disc:
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


def _duet_principal(tracks: list) -> str:
    """L'artista principale quando gli artisti dei brani sono lui da solo e i suoi duetti ("A", "A & B", "A feat.
    C"): la sua grafia più usata tra i brani in cui è da solo. "" se gli artisti sono davvero diversi."""
    firsts = set()
    solos = []
    for track in tracks:
        if track.tags.artist:
            parts = duet_parts(track.tags.artist)
            firsts.add(variant_key(parts[0]))
            if len(parts) == 1:
                solos.append(track.tags.artist)
    result = ""
    if len(firsts) == 1 and solos:
        result = _most_common(solos)
    return result


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
            principal = _duet_principal(folder_tracks)
            if not album_artist:
                if principal:
                    album_artist = principal         # "A" e "A & B": l'album è di A, non una compilation
                elif len(artists) > 1:
                    album_artist = VARIOUS_ARTISTS
                else:
                    album_artist = _most_common([t.tags.artist for t in folder_tracks])
            names = sorted({f"{k[0]} — {k[1]}" for k in keys})
            changes = _with_disc_numbers(_unify_changes(folder_tracks, {"album": album, "album_artist": album_artist}),
                                         folder_tracks)
            issues.append(Issue(
                KIND_SPLIT, SEVERITY_HIGH, f"{_short(folder)}: un album diviso in {len(keys)}",
                "I brani di questa cartella risultano in album diversi: " + "; ".join(names) + ". Di solito "
                f"l'\"Artista album\" manca o è scritto in modo diverso: per una compilation va messo \"{VARIOUS_ARTISTS}\" "
                "su tutti i brani. Un \"CD 1\"/\"Disc 2\" nel nome passa nel campo N. disco.",
                [t.path for t in folder_tracks],
                Fix(FIX_TAGS, f"Album \"{album}\", artista album \"{album_artist}\" su tutti i brani",
                    changes=changes),
                rule_id=f"R11.{number}"))
    return issues


def _with_disc_numbers(changes: list, tracks: list) -> list:
    """Le correzioni con in più il numero del disco preso dal nome dell'album ("Album (CD 2)" → N. disco 2), per i
    brani che lo hanno nel nome: togliere "CD 2" dal nome senza scriverlo nel numero lo perderebbe."""
    by_path = {}
    order = []
    for path, values in changes:
        by_path[path] = dict(values)
        order.append(path)
    for track in tracks:
        _base, disc = split_disc_marker(track.tags.album or "")
        if disc is not None and track.tags.disc_number != disc:
            if track.path not in by_path:
                by_path[track.path] = {}
                order.append(track.path)
            by_path[track.path]["disc_number"] = disc
    result = []
    for path in order:
        result.append((path, by_path[path]))
    return result


def _spellings_title(album: str, keys: list) -> str:
    """Il titolo di "lo stesso album scritto in modi diversi": le forme da correggere per nome. Se tra le forme c'è
    già quella giusta, "X" anche come "X - CD1", "X - CD2"; altrimenti "X" scritto in N modi diversi: …"""
    others = []
    for key in sorted(keys, key=lambda k: k[1].casefold()):
        if key[1] != album and f"\"{key[1]}\"" not in others:
            others.append(f"\"{key[1]}\"")
    shown = ", ".join(others[:3]) + (f" e altri {len(others) - 3}" if len(others) > 3 else "")
    if not others:                                   # stesso nome, artista scritto diverso
        result = f"\"{album}\" scritto in {len(keys)} modi diversi"
    elif len(others) < len(keys):
        result = f"\"{album}\" anche come {shown}"
    else:
        result = f"\"{album}\" scritto in {len(keys)} modi diversi: {shown}"
    return result


def _touches(tracks: list, selected: Optional[set]) -> bool:
    """Qualcuno dei brani è tra quelli controllati (selected: i percorsi; None: tutti)."""
    result = selected is None
    for track in tracks:
        if not result and str(track.path) in selected:
            result = True
    return result


def detect_split_names(tracks: list, selected: Optional[set] = None) -> list:
    """Lo stesso album scritto in modi diversi (punteggiatura, "CD 2") o diviso per artista. tracks: tutta la musica;
    selected: i percorsi dei brani controllati (None: tutti), i soli problemi che li toccano."""
    groups = group_by_album(tracks)
    by_name = {}
    for key, album_tracks in groups.items():
        if key[1] != UNKNOWN_ALBUM:
            by_name.setdefault(album_norm(key[1]), []).append(key)
    issues = []
    number = 0
    for norm, keys in sorted(by_name.items()):
        all_tracks = []
        for key in keys:
            all_tracks += groups[key]
        if len(keys) > 1 and _touches(all_tracks, selected):
            number += 1
            same_artist = len({artist_norm(key[0]) for key in keys}) == 1
            album = _most_common([split_disc_marker(t.tags.album)[0] for t in all_tracks])
            names = "; ".join(sorted(f"{k[0]} — {k[1]}" for k in keys))
            changes = []
            if same_artist:
                spellings = []
                counts = {}
                for track in all_tracks:
                    value = track.tags.album_artist or track.tags.artist
                    if value:
                        if value not in counts:
                            spellings.append(value)
                            counts[value] = 0
                        counts[value] += 1
                album_artist = choose_spelling(spellings, counts, POLICY_MOST).spelling
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
                    KIND_SPLIT, SEVERITY_HIGH, _spellings_title(album, keys),
                    f"Lo stesso album compare come: {names}. La punteggiatura o un \"CD 1\"/\"Disc 2\" nel nome lo "
                    "dividono; il numero del disco va nel campo N. disco.",
                    [t.path for t in all_tracks],
                    Fix(FIX_TAGS, f"Album \"{album}\" e artista album \"{album_artist}\" su tutti i brani, numero "
                        "del disco dal nome", changes=changes), rule_id=f"R12.{number}"))
            else:
                # una compilation senza artista dell'album: sull'iPhone diventa un album per cantante. Si propone
                # "Artisti Vari", salvo che la Verifica online trovi l'album di un artista preciso (allora il
                # problema si toglie: check_flow.drop_disproved_compilations, e W2 propone quell'artista)
                folders = {t.path.parent for t in all_tracks}
                years = {t.tags.year for t in all_tracks if t.tags.year}
                no_album_artist = all(not t.tags.album_artist for t in all_tracks)
                if no_album_artist:
                    fix = Fix(FIX_TAGS, f"Artista album \"{VARIOUS_ARTISTS}\" e album \"{album}\" su tutti i brani",
                              changes=_unify_changes(all_tracks, {"album": album, "album_artist": VARIOUS_ARTISTS}))
                    detail = (f"L'album compare come: {names}. Senza artista dell'album, sull'iPhone ogni cantante forma "
                              f"un album a parte: la correzione mette \"{VARIOUS_ARTISTS}\" e la spunta Compilation. "
                              "Con la Verifica online, se il catalogo trova l'album di un artista preciso, questo "
                              "problema sparisce e la correzione online propone quell'artista.")
                    if len(folders) > 1 and len(years) > 1:
                        detail += (" Le cartelle e gli anni sono diversi: forse sono album diversi con lo stesso "
                                   "nome.")
                    detail += (" Non verificato online: se non hai fatto la Verifica online, tasto destro → "
                               "Controlla online per esserne sicuro.")
                    issues.append(Issue(
                        KIND_SPLIT, SEVERITY_MEDIUM, f"\"{album}\" diviso tra {len(keys)} artisti", detail,
                        [t.path for t in all_tracks], fix, rule_id=f"R13.{number}"))
    return issues


def detect_artist_variants(tracks: list, selected: Optional[set] = None) -> list:
    """R14: lo stesso artista scritto in modi diversi, certo: "The Beatles"/"Beatles", "AC/DC"/"ACDC", "Battiato
    Franco"/"Franco Battiato" (names.LEVEL_WORDS), nell'artista dei brani e nell'artista dell'album. Le differenze di
    sole maiuscole, accenti e spazi le trova R23 (scan_rules), che gira prima. tracks: tutta la musica; selected: i
    percorsi dei brani controllati (None: tutti). Vince la grafia con le iniziali maiuscole più usata (D-2)."""
    from .scan_rules import _name_usage, _rename_changes
    usage = _name_usage(tracks, variant_key)
    issues = []
    number = 0
    for norm in sorted(usage):
        spellings, counts, paths = usage[norm]
        forms = set()
        for spelling in spellings:
            forms.add(_plain(spelling))
        touched = selected is None or bool(paths & selected)
        if len(spellings) > 1 and len(forms) > 1 and touched:
            number += 1
            chosen = choose_spelling(spellings, counts, POLICY_MOST).spelling
            changes = _rename_changes(tracks, set(spellings), chosen)
            files = []
            for track in tracks:
                if str(track.path) in paths:
                    files.append(track.path)
            issues.append(Issue(
                KIND_NAMES, SEVERITY_MEDIUM, f"Artista scritto in {len(spellings)} modi: " + ", ".join(sorted(spellings)),
                "Le varianti dividono la collezione dell'artista negli elenchi e sull'iPhone. Vince la grafia con le "
                "iniziali maiuscole, la più usata.", files,
                Fix(FIX_TAGS, f"Scrivi ovunque \"{chosen}\"", changes=changes), rule_id=f"R14.{number}"))
    return issues


def _artist_context(tracks: list) -> tuple:
    """({variant_key: grafia più usata}, {variant_key: (brani, "album (anno); …")}, {variant_key: [brani]})."""
    by_key = {}
    for track in tracks:
        name = track.display_artist
        if name != UNKNOWN_ARTIST and len(duet_parts(name)) == 1:
            by_key.setdefault(variant_key(name), []).append(track)
    names = {}
    context = {}
    for key, key_tracks in by_key.items():
        spellings = []
        counts = {}
        for track in key_tracks:
            if track.display_artist not in counts:
                spellings.append(track.display_artist)
                counts[track.display_artist] = 0
            counts[track.display_artist] += 1
        names[key] = choose_spelling(spellings, counts, POLICY_MOST).spelling      # come R14 e R23 (D-2)
        albums = []
        for track in key_tracks:
            label = f"{track.tags.album} ({track.tags.year})" if track.tags.year else track.tags.album
            if label and label not in albums and len(albums) < 3:
                albums.append(label)
        context[key] = (len(key_tracks), "; ".join(albums))
    result = (names, context, by_key)
    return result


def _unify_artist(keys: list, names: dict, context: dict, by_key: dict) -> tuple:
    """(grafia scelta, file, modifiche) per unire i nomi delle chiavi: la grafia con le iniziali maiuscole più usata
    (più brani, D-2)."""
    spellings = []
    counts = {}
    for key in keys:
        spellings.append(names[key])
        counts[names[key]] = context[key][0]
    chosen = choose_spelling(spellings, counts, POLICY_MOST).spelling
    files = []
    changes = []
    for key in keys:
        for track in by_key[key]:
            files.append(track.path)
            wanted = {}
            if track.tags.album_artist and variant_key(track.tags.album_artist) in keys \
                    and track.tags.album_artist != chosen:
                wanted["album_artist"] = chosen
            if track.tags.artist and variant_key(track.tags.artist) in keys and track.tags.artist != chosen:
                wanted["artist"] = chosen
            if wanted:
                changes.append((track.path, wanted))
    result = (chosen, files, changes)
    return result


def detect_artist_doubts(tracks: list, provider=None, musicbrainz=None, progress: Optional[ProgressFn] = None,
                         cancel: Optional[threading.Event] = None, context: Optional[list] = None) -> tuple:
    """R16: i nomi forse dello stesso artista: solo il cognome ("Battiato"), iniziali ("F. Battiato"), errori di
    battitura. Decide MusicBrainz (se chiesto: nome e alias dello stesso artista), poi l'AI (con album e anni); senza
    nessuno dei due restano "da controllare". context: tutta la musica, quando tracks è una parte: i nomi si cercano
    in tutta, ma si tengono solo i gruppi con un nome dei brani controllati. (problemi con la correzione verso la
    forma con le iniziali maiuscole più usata, errori)."""
    from .albumcheck import AlbumCheckError
    everything = list(tracks)
    if context:
        seen = set()
        for track in tracks:
            seen.add(str(track.path))
        for track in context:
            if str(track.path) not in seen:
                everything.append(track)
    names, context_of, by_key = _artist_context(everything)
    mine = set()
    for track in tracks:
        mine.add(variant_key(track.display_artist))
    groups = []
    for members, why in clusters(candidate_pairs(names)):
        touched = False
        for key in members:
            if key in mine:
                touched = True
        if touched:
            groups.append((members, why))
    context = context_of
    decided = {}
    errors = []
    if musicbrainz is not None:
        index = 0
        while index < len(groups) and not is_cancelled(cancel) and not errors:
            members, _why = groups[index]
            if progress is not None:
                progress(index, len(groups), f"MusicBrainz: nomi d'artista dubbi ({index + 1} di {len(groups)})")
            biggest = members[0]
            for key in members:
                if context[key][0] > context[biggest][0]:
                    biggest = key
            try:
                known = musicbrainz_keys(musicbrainz, names[biggest])
            except AlbumCheckError as exc:
                errors.append(f"nomi degli artisti su MusicBrainz: {exc}")
                known = set()
            matched = []
            for key in members:
                if key in known:
                    matched.append(key)
            if len(matched) > 1:
                decided[index] = ([matched], ORIGIN_RULE, "nomi o alias dello stesso artista su MusicBrainz")
            index += 1
    if provider is not None and not is_cancelled(cancel):
        open_indexes = []
        for index in range(len(groups)):
            if index not in decided:
                open_indexes.append(index)
        asked = []
        for index in open_indexes:
            asked.append(groups[index])
        answers, ai_errors = ask_ai_names(provider, asked, names, context, progress, cancel)
        errors += ai_errors
        for position, (sets, reason) in answers.items():
            decided[open_indexes[position]] = (sets, ORIGIN_AI, f"AI: {reason}" if reason else "AI")
    issues = []
    number = 0
    for index, (members, why) in enumerate(groups):
        sets, origin, reason = decided.get(index, ([members], ORIGIN_RULE, ""))
        confirmed = index in decided
        if not confirmed:
            reason = "da controllare: " + ", ".join(sorted(set(why.values())))
        for keys in sets:
            number += 1
            chosen, files, changes = _unify_artist(keys, names, context, by_key)
            written = []
            for key in keys:
                written.append(f"{names[key]} ({_tracks_text(context[key][0])})")
            title = ("Lo stesso artista scritto in modi diversi: " if confirmed else "Forse lo stesso artista: ") \
                + ", ".join(written)
            issues.append(Issue(
                KIND_NAMES, SEVERITY_MEDIUM if confirmed else SEVERITY_LOW, title,
                f"Le varianti dividono la collezione dell'artista negli elenchi e sull'iPhone ({reason}). Vince la "
                "grafia con le iniziali maiuscole, la più usata.", files,
                Fix(FIX_TAGS, f"Scrivi ovunque \"{chosen}\"", changes=changes) if changes else None,
                origin=origin, rule_id=f"R16.{number}"))
    result = (issues, errors)
    return result


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
    copies = []                    # le copie dello stesso album (R32, R33): i loro doppioni brano per brano (R8) no
    for issue in issues:
        if issue.rule_id.split(".", 1)[0] in ("R32", "R33"):
            copies.append(issue)
    splits = []                    # le collezioni divise: non R24-R28, che guardano un album intero
    for issue in issues:
        if issue.rule_id.split(".", 1)[0] in ("R11", "R12", "R13"):
            splits.append(issue)
    kept = []
    for issue in issues:
        drop = ((issue.rule_id.startswith("R13") and _covered(issue, folders))
                or (issue.rule_id.startswith("R10") and _covered(issue, splits))
                or (issue.rule_id.split(".", 1)[0] == "R8" and _covered(issue, copies)))
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


def rule_steps(view, check_files: bool, progress: Optional[ProgressFn] = None,
               cancel: Optional[threading.Event] = None, pc: bool = True) -> list:
    """I passi delle regole, nell'ordine dei livelli (checks_requirements.md, sezione 6): [(controllo, si fa,
    funzione che restituisce i problemi)]. view: scan_rules.RuleView. pc: le regole nuove (R18-R31) solo sul PC."""
    from . import scan_rules as more
    selected = view.selected_paths() if view.partial else None
    whole = view.all if view.partial else None
    result = [
        # 1. file
        (CHECK_UNREADABLE, True, lambda: detect_unreadable(view.selected)),
        (CHECK_UNREADABLE, pc, lambda: more.detect_long_paths(view.selected)),
        (CHECK_FILES, check_files, lambda: detect_file_problems(view.selected, progress, cancel)),
        (CHECK_FILES, check_files and pc, lambda: more.detect_unsupported_formats(view.selected)),
        # 2. campi del brano
        (CHECK_MISSING, True, lambda: detect_missing_tags(view.selected)),
        (CHECK_MISSING, pc, lambda: more.detect_title_prefixes(view.selected)),
        (CHECK_MISSING, pc, lambda: more.detect_spaces(view.selected)),
        (CHECK_MISSING, pc, lambda: more.detect_mojibake(view.selected)),
        # 3. nomi, in tutta la musica
        (CHECK_VARIANTS, pc, lambda: more.detect_spelling_variants(view)),
        (CHECK_VARIANTS, True, lambda: detect_artist_variants(view.all, selected)),
        # 4. coerenza dell'album
        (CHECK_SPLIT, True, lambda: detect_split_folders(view.selected)),
        (CHECK_SPLIT, True, lambda: detect_split_names(view.all, selected)),
        (CHECK_SPLIT, pc, lambda: more.detect_album_name_spellings(view)),
        (CHECK_SPLIT, pc, lambda: more.detect_album_artist_spellings(view)),
        (CHECK_SPLIT, pc, lambda: more.detect_album_artist_from_artist(view)),
        (CHECK_SPLIT, pc, lambda: more.detect_compilation_flags(view)),
        (CHECK_SPLIT, pc, lambda: more.detect_phone_merges(view)),
        (CHECK_FEW, pc, lambda: more.detect_number_clashes(view)),
        (CHECK_FEW, pc, lambda: more.detect_track_numbers(view)),
        # 5. completezza
        (CHECK_FEW, True, lambda: detect_few_tracks(view.selected, whole)),
        # 6. doppioni (R15, lo stesso brano con l'impronta, gira dopo: scan_tracks)
        (CHECK_DUPLICATES, pc, lambda: more.detect_album_copies(view)),
        (CHECK_DUPLICATES, True, lambda: detect_duplicates(view.selected)),
    ]
    return result


def rule_issues(tracks: list, check_files: bool, progress: Optional[ProgressFn] = None,
                cancel: Optional[threading.Event] = None, checks: frozenset = ALL_CHECKS,
                context: Optional[list] = None, pc: bool = True) -> list:
    """I problemi delle regole dei controlli scelti, a livelli: ogni passo vede le correzioni dei passi prima come
    già fatte (scan_rules.RuleView), e ogni problema ricorda il suo passo (Issue.step). context: tutta la musica,
    quando tracks è una parte (nomi e album si giudicano interi). pc: False per la musica dell'iPhone."""
    from .scan_rules import RuleView
    view = RuleView(tracks, context)
    issues = []
    step = 0
    for check, wanted, find in rule_steps(view, check_files, progress, cancel, pc):
        step += 1
        if wanted and check in checks:
            found = find()
            for issue in found:
                issue.step = step
            view.apply(found)
            issues += found
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
    """Lo stesso brano più volte nello stesso album e nello stesso formato: (problemi, errori). Una copia in un altro
    formato (FLAC e MP3) o in un altro album (una raccolta) non si segnala.
      * stesso audio (impronta): certo;
      * stesso artista e titolo, durata entro 2 secondi, audio diverso (due codifiche): lo stesso brano, se titolo e
        album non nominano versioni diverse (live, unplugged, remix, demo…);
      * con versioni diverse nominate sono due registrazioni (tenute apposta): non si segnalano.
    provider non si usa più (le coppie dubbie le decideva l'AI): resta per chi chiama. Un problema per artista, una
    riga per brano; nessuna correzione: quale copia tenere lo decide l'utente. skip: i file già segnalati come doppi
    nello stesso album."""
    clusters = _Clusters()
    by_print = {}
    for track in tracks:
        value = fingerprints.get(str(track.path), "")
        if value and not track.error and str(track.path) not in skip:
            by_print.setdefault(value, []).append(track)
    for group in by_print.values():
        for other in group[1:]:
            clusters.join(group[0], other)
    errors = []
    for first, second in suspicious_pairs(tracks, fingerprints):
        # versioni diverse nominate nel titolo o nell'album ("Piove" e "Piove (Unplugged)"): due registrazioni,
        # tenute apposta; non è un doppione e non serve chiedere all'AI
        same_version = version_marks(first) == version_marks(second)
        if str(first.path) not in skip and str(second.path) not in skip and same_version:
            clusters.join(first, second)
    by_artist = {}
    for members, notes in clusters.groups():
        # un doppione è lo stesso brano due volte nello stesso album e nello stesso formato: una copia in un altro
        # formato (FLAC e MP3) o in un altro album (una raccolta) va bene
        counts = {}
        for track in members:
            place = (track.album_key, track.path.suffix.lower())
            counts[place] = counts.get(place, 0) + 1
        repeated = []
        for track in members:
            if counts[(track.album_key, track.path.suffix.lower())] > 1:
                repeated.append(track)
        if repeated:
            by_artist.setdefault(repeated[0].display_artist, []).append((repeated, notes))
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
        listed = "\n".join(shown)
        detail = (f"Lo stesso brano più volte nello stesso album e nello stesso formato: di solito una copia in più da "
                  f"togliere; quale tenere lo decidi tu (Mostra i brani). Le copie in un altro formato (FLAC e MP3) e "
                  f"lo stesso brano in un altro album (una raccolta) non si segnalano.\n{listed}")
        issues.append(Issue(KIND_DUPLICATE, SEVERITY_LOW, f"{artist}: {_tracks_text(len(songs))} in più copie",
                            detail, files, origin=ORIGIN_AI if used_ai else ORIGIN_RULE, rule_id=f"R15.{number}"))
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
            "salvali sul PC dalla scheda iPhone (tasto destro → Copia da iPhone a PC); a volte sono solo scritti in modo "
            "diverso.", names, rule_id="I3"))
    return issues


# --------------------------------------------------------------------------- AI

AI_SYSTEM = """You audit a personal music library for an organizer app. Each album line gives an id, the album \
artist, the album, the years, the number of tracks, the track numbers present, the declared track total, the \
folder and the genres. The rule findings were computed by simple rules.

Find the problems the owner usually has:
- "non_aggiornato": files whose tags will not show as updated (only if the data shows it);
- "album_incompleto": albums with few tracks or missing track numbers. The "mancanti" column is computed for you \
(a box set may number its tracks across all the discs): with "mancanti: nessuno" no number is missing. An album with \
an "immagine CUE" column is a \
whole disc in one file (FLAC + CUE): never report it as incomplete;
- "collezione_divisa": one collection split into several albums: the same album with different spellings, a disc \
marker in the album name, a compilation without album artist, the same artist spelled differently. A duet name \
("A & B") is a name like any other: report it only if it splits one album in several;
- "duplicato": the same track twice INSIDE the same album, or the same album twice. The same song on several different albums (the original album and a compilation, a live album) is legitimate: never report it. The same album kept in several formats (the "formati" column lists more than one, for example flac and mp3, and the tracks are about twice the numbers) is legitimate too: never report it;
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
        missing = ",".join(album_gaps(album_tracks)[0][:20]) or "nessuno"
        text = (f"A{index} | album artist: {key[0]} | album: {key[1]} | anni: {','.join(years) or '-'} | brani: "
                f"{len(album_tracks)} | numeri: {_numbers_text(album_tracks)} | totale dichiarato: {declared or '-'} "
                f"| mancanti: {missing} | cartella: {folder} | generi: {','.join(genres) or '-'}")
        formats = sorted({t.path.suffix.lower().lstrip(".") for t in album_tracks})
        if len(formats) > 1:
            text += f" | formati: {','.join(formats)}"
        images = cue.cue_images(album_tracks) if len(album_tracks) <= 2 else {}
        if images and len(images) == len(album_tracks):
            text += f" | immagine CUE: {sum(images.values())} tracce in {len(images)} file"
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


def album_batches(keys: list, groups: dict, max_albums: int, max_tracks: int) -> list:
    """Gli album (keys, in ordine) divisi nelle richieste all'AI: in ognuna al massimo max_albums album e max_tracks
    brani. Un album non si divide mai: se da solo supera max_tracks va in una richiesta sua, intero."""
    albums_limit = max(1, int(max_albums))
    tracks_limit = max(1, int(max_tracks))
    batches = []
    current = []
    counted = 0
    for key in keys:
        size = len(groups[key])
        if current and (len(current) >= albums_limit or counted + size > tracks_limit):
            batches.append(current)
            current = []
            counted = 0
        current.append(key)
        counted += size
    if current:
        batches.append(current)
    result = batches
    return result


SPLIT_FRAGMENT_TRACKS = 3     # un album di al massimo tanti brani può essere un pezzo di una compilation divisa


def ai_requests(groups: dict, max_albums: int, max_tracks: int) -> list:
    """Gli album divisi nelle richieste all'AI. Insieme solo gli album che hanno qualcosa in comune: lo stesso
    artista dell'album (anche scritto in modi diversi: artist_names.variant_key), oppure lo stesso nome d'album
    quando almeno uno dei due ha al massimo SPLIT_FRAGMENT_TRACKS brani (i pezzi di una compilation senza artista
    dell'album; due album veri con lo stesso nome, "Greatest Hits" di due artisti, no). L'artista dei brani non
    conta: una compilation con artista dell'album è un gruppo solo. Ogni gruppo si divide secondo i limiti
    (album_batches); gruppi diversi non stanno mai nella stessa richiesta."""
    keys = sorted(groups, key=lambda k: (artist_norm(k[0]), album_norm(k[1])))
    parent = {}
    for key in keys:
        parent[key] = key

    def root(key):
        top = key
        while parent[top] != top:
            top = parent[top]
        return top

    def join(first, second):
        parent[root(second)] = root(first)

    by_artist = {}
    by_album = {}
    for key in keys:
        by_artist.setdefault(variant_key(key[0]) or artist_norm(key[0]), []).append(key)
        if key[1] != UNKNOWN_ALBUM:
            by_album.setdefault(album_norm(key[1]), []).append(key)
    for same in by_artist.values():
        for other in same[1:]:
            join(same[0], other)
    for same in by_album.values():
        for position, first in enumerate(same):
            for second in same[position + 1:]:
                if min(len(groups[first]), len(groups[second])) <= SPLIT_FRAGMENT_TRACKS:
                    join(first, second)
    clusters = {}
    order = []
    for key in keys:
        top = root(key)
        if top not in clusters:
            clusters[top] = []
            order.append(top)
        clusters[top].append(key)
    result = []
    for top in order:
        members = sorted(clusters[top], key=lambda k: (album_norm(k[1]), artist_norm(k[0])))
        result.extend(album_batches(members, groups, max_albums, max_tracks))
    return result


def ai_review(provider, tracks: list, issues: list, progress: Optional[ProgressFn] = None,
              cancel: Optional[threading.Event] = None, on_found: Optional[Callable[[list], None]] = None) -> tuple:
    """(nuovi problemi dell'AI, errori). Segna sulle regole che l'AI scarta il suo motivo (Issue.ai_note). Le
    richieste raggruppano gli album che hanno qualcosa in comune (ai_requests) e rispettano i limiti del profilo
    (batch_albums, batch_tracks). on_found(problemi finora): dopo ogni richiesta, per mostrarli man mano."""
    from .ai import AIError
    from .config import ProviderProfile

    groups = group_by_album(tracks)
    path_to_key = {}
    for key, album_tracks in groups.items():
        for track in album_tracks:
            path_to_key[str(track.path)] = key
    by_rule_id = {issue.rule_id: issue for issue in issues if issue.rule_id}
    found = []
    errors = []
    max_albums = getattr(provider.profile, "batch_albums", ProviderProfile.batch_albums)
    max_tracks = getattr(provider.profile, "batch_tracks", ProviderProfile.batch_tracks)
    chunks = ai_requests(groups, max_albums, max_tracks)
    index = 0
    while index < len(chunks) and not is_cancelled(cancel) and not getattr(provider, "gave_up", False):
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
        if on_found is not None and not is_cancelled(cancel):
            on_found(list(found))
        index += 1
    result = (found, errors)
    return result


# --------------------------------------------------------------------------- scansione completa

def albums_of_issues(issues: list, tracks: list) -> set:
    """Gli album (album_key) dei brani toccati dai problemi."""
    by_path = {}
    for track in tracks:
        by_path[str(track.path)] = track
    result = set()
    for issue in issues:
        for path in issue.files:
            track = by_path.get(str(path))
            if track is not None:
                result.add(track.album_key)
    return result


def tracks_of_albums(tracks: list, albums: set) -> list:
    result = []
    for track in tracks:
        if track.album_key in albums:
            result.append(track)
    return result


def scan_tracks(tracks: list, target: str, provider=None, check_files: bool = True,
                phone_tracks: Optional[list] = None, library_tracks: Optional[list] = None,
                progress: Optional[ProgressFn] = None, cancel: Optional[threading.Event] = None,
                checks: frozenset = ALL_CHECKS, fingerprints: Optional[dict] = None,
                musicbrainz=None, ai_flagged_only: bool = False, keep_phone_fixes: bool = False,
                partial: Optional[Callable[[list], None]] = None,
                ai_skip: Optional[Callable[[tuple], bool]] = None,
                album_context: Optional[list] = None,
                fingerprint_fn: Optional[Callable[[], dict]] = None) -> ScanReport:
    """Il controllo: le regole dei controlli scelti (checks), poi l'AI se c'è un fornitore. Con phone_tracks (la
    musica dell'app Musica, i cui brani sono anche tracks) è dell'iPhone, confrontato con library_tracks.
    fingerprints: {percorso: impronta dell'audio} per i brani duplicati (senza, solo quelli sospetti per i tag).
    fingerprint_fn() -> fingerprints: calcolate solo quando servono, per R15 dopo tutte le altre regole: i risultati
    delle regole (partial) arrivano prima del calcolo delle impronte, che è lento.
    musicbrainz: un albumcheck.MusicBrainzClient per controllare anche lì i nomi d'artista dubbi (lento).
    ai_flagged_only: l'AI guarda solo gli album dove le regole hanno trovato qualcosa (nessuno: niente AI). Senza
    controlli scelti (Solo AI) l'AI guarda tutti gli album e ogni suo problema si tiene.
    keep_phone_fixes: le correzioni dei brani dell'iPhone restano (la linguetta Controlli le applica dalla parte giusta);
    senza, si tolgono e il dettaglio dice di correggere sul PC.
    partial(problemi): i risultati man mano (una copia dell'elenco): dopo le regole e dopo l'analisi AI.
    ai_skip(album_key): gli album che l'analisi AI salta (quelli che vanno bene così per intero).
    album_context: tutti i brani della musica quando tracks è una parte: gli album incompleti si giudicano interi."""
    assign_groups(tracks)
    report = ScanReport(target=target, tracks_scanned=len(tracks), albums_scanned=len(group_by_album(tracks)))
    issues = rule_issues(tracks, check_files, progress, cancel, checks, album_context, pc=phone_tracks is None)
    rules_cut = is_cancelled(cancel)
    if partial is not None:
        partial(list(issues))
    only_ai = not checks
    if provider is not None and not rules_cut and (checks & AI_REVIEW_CHECKS or only_ai):
        reviewed = tracks
        if ai_flagged_only and not only_ai:
            reviewed = tracks_of_albums(tracks, albums_of_issues(issues, tracks))
        if ai_skip is not None:
            wanted = []
            for track in reviewed:
                if not ai_skip(track.album_key):
                    wanted.append(track)
            reviewed = wanted
        if reviewed:
            def found_so_far(found: list) -> None:
                shown = list(issues)
                for issue in drop_repeated(found, issues):
                    if only_ai or enabled(issue, checks):
                        shown.append(issue)
                partial(shown)

            on_found = found_so_far if partial is not None else None
            found, errors = ai_review(provider, reviewed, issues, progress, cancel, on_found)
            if is_cancelled(cancel):
                # Annulla durante l'AI: come se non fosse stata scelta (anche i suoi giudizi sulle regole)
                _stopped(report, "Analisi AI")
                for issue in issues:
                    issue.ai_note = ""
            else:
                report.ai_profile = provider.profile.name
                for issue in drop_repeated(found, issues):
                    if only_ai or enabled(issue, checks):
                        issues.append(issue)
                report.ai_errors = errors
                if partial is not None:
                    partial(list(issues))
    if CHECK_VARIANTS in checks and not rules_cut:
        if progress is not None:
            progress(0, 0, "nomi d'artista dubbi")
        helper = provider if not is_cancelled(cancel) else None
        catalog = musicbrainz if not is_cancelled(cancel) else None
        found, errors = detect_artist_doubts(tracks, helper, catalog, progress, cancel, album_context)
        if (helper is not None or catalog is not None) and is_cancelled(cancel):
            _stopped(report, "Analisi AI" if helper is not None else "MusicBrainz")
            found, errors = detect_artist_doubts(tracks, None, None, progress, None, album_context)  # solo regole
        issues += found
        report.ai_errors += errors
    if CHECK_DUPLICATES in checks and not rules_cut:
        skip = set()
        for issue in issues:
            if issue.kind == KIND_DUPLICATE:
                for path in issue.files:
                    skip.add(str(path))
        if fingerprints is None and fingerprint_fn is not None and not is_cancelled(cancel):
            fingerprints = fingerprint_fn()
        if progress is not None:
            progress(0, 0, "brani duplicati")
        helper = provider if not is_cancelled(cancel) else None
        found, errors = detect_same_songs(tracks, fingerprints or {}, helper, progress, cancel, frozenset(skip))
        if helper is not None and is_cancelled(cancel):
            _stopped(report, "Analisi AI")
            found, errors = detect_same_songs(tracks, fingerprints or {}, None, progress, None, frozenset(skip))
        issues += found
        report.ai_errors += errors
        if helper is not None and not is_cancelled(cancel):
            report.ai_profile = provider.profile.name
    if phone_tracks is not None:
        if not keep_phone_fixes:
            # senza la linguetta Controlli (console): le correzioni si fanno sui brani del PC
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
    report.cancelled = rules_cut
    if report.stopped:
        report.ai_errors = []          # gli errori di un passo annullato non contano
    unique = []
    for error in report.ai_errors:     # dopo che l'AI ha smesso, lo stesso errore per ogni richiesta
        if error not in unique:
            unique.append(error)
    report.ai_errors = unique
    return report


def _stopped(report: ScanReport, stage: str) -> None:
    if stage not in report.stopped:
        report.stopped.append(stage)


# --------------------------------------------------------------------------- cosa fare

CHECK_ONLINE = "Verifica online questi album"
_MANUAL_DUPLICATE = ("Mostra i brani. Se sono davvero lo stesso brano, tieni una copia e sposta l'altra fuori dalle "
                     "cartelle della musica con Esplora file (il programma non cancella i file del PC). Se sono due "
                     "versioni diverse tenute apposta, scrivi la versione nel titolo (Cambia i tag: \"(Live)\", "
                     "\"(Unplugged)\"…) e non saranno più segnalate. Per i doppioni sull'iPhone: scheda iPhone, "
                     "Mostra → \"Doppioni: stessa canzone nello stesso album\".")
_MANUAL_UNREADABLE = ("Mostra i brani e prova ad aprirli in Esplora file. Se sono su OneDrive: tasto destro → Mantieni "
                      "sempre su questo dispositivo. Se sono danneggiati, ricopiali dall'originale o riscaricali, poi "
                      "Rileggi (F5).")
_MANUAL_TAGS = "Mostra i brani, poi Cambia i tag (tasto E) e scrivi titolo, album e artista."
_ONLY_ON_DEVICE = ("Per tenerli: scheda iPhone, tasto destro → Copia da iPhone a PC. Se non servono: Elimina "
                   "dall'iPhone, poi Applica. Se sul PC ci sono ma scritti in modo diverso, correggi i tag sul PC.")
# il suggerimento di ogni regola (rule_id senza il numero), anche quando non c'è una correzione automatica
ADVICE = {
    "R2": "Niente di urgente: le copie inviate all'iPhone sono già senza il vecchio tag. Per pulire anche i file del PC: "
          "Applica la correzione, poi approva l'elenco dei file (il tag ID3v1 si toglie, i valori restano nell'ID3v2).",
    "R3": "Niente di urgente: le copie inviate all'iPhone sono già senza il tag APE. Per pulire anche i file del PC: "
          "Applica la correzione, poi approva l'elenco dei file (il tag APE si toglie, i valori restano nell'ID3v2).",
    "R5": _MANUAL_UNREADABLE,
    "R6": "Applica la correzione (se c'è) ricava i tag dai nomi di file e cartelle: controlla la colonna Diventa. "
          "Altrimenti Mostra i brani, poi Cambia i tag (tasto E) e scrivi titolo, album e artista al posto di quelli "
          "vuoti o segnaposto (\"Unknown Artist\", \"Track 01\").",
    "R7": "Mostra i brani e confronta le due copie (tag, durata, qualità nell'editor dei tag). Tieni la migliore e "
          "sposta l'altra fuori dalle cartelle della musica con Esplora file (il programma non cancella i file del PC).",
    "R8": "Mostra i brani. Se sono lo stesso brano, tieni una copia e sposta l'altra fuori dalle cartelle della musica "
          "con Esplora file. Se sono brani diversi, titolo o numero di traccia sono sbagliati: correggili con Cambia i "
          "tag (tasto E).",
    "R9": "Premi Verifica online questi album: i cataloghi dicono quali brani mancano e quali sono i tag giusti. Se i brani mancano "
          "davvero, aggiungili alla cartella; se è sbagliato il numero di traccia, correggilo con Cambia i tag.",
    "R10": "Se è un singolo, o vuoi solo questi brani: tasto destro sull'album → Va bene così, e non sarà più segnalato. "
           "Se sono brani di un album più grande finiti a parte, Mostra i brani e con Cambia i tag (tasto E) scrivi "
           "album e artista dell'album uguali a quelli degli altri brani; per sapere com'è l'album intero: tasto destro "
           "→ Controlla online.",
    "R11": "Applica la correzione mette lo stesso album e lo stesso artista dell'album su tutti i brani della cartella. "
           "Se la cartella contiene davvero album diversi, ignora.",
    "R12": "Applica la correzione unifica il nome dell'album e sposta \"CD 1\" / \"Disc 2\" nel numero del disco.",
    "R13": "Se è una compilation: Applica la correzione (se c'è), oppure Mostra i brani e Cambia i tag (tasto E) con "
           f"artista dell'album \"{VARIOUS_ARTISTS}\" su tutti. Se sono album diversi che si chiamano allo stesso modo: "
           "tasto destro sull'album → Va bene così.",
    "R14": "Applica la correzione scrive ovunque la grafia scelta (anche negli album fuori dalla selezione: compaiono "
           "nei risultati). Per sceglierne un'altra: Mostra i brani, Cambia i tag (tasto E) e scrivila su tutti, poi "
           "Controlla di nuovo questi album.",
    "R15": _MANUAL_DUPLICATE,
    "R16": "Se è davvero lo stesso artista: Applica la correzione (vince la forma più usata). Se non sei sicuro, accendi "
           "MusicBrainz o l'AI e ripeti il controllo. Se sono artisti diversi, ignora.",
    "R18": "Converti questi file in MP3 (320 kbps) o in FLAC con un programma di conversione (per esempio foobar2000 o "
           "fre:ac), controllando che copi anche i tag. Metti i file convertiti nella stessa cartella, sposta gli "
           "originali fuori dalle cartelle della musica con Esplora file (il programma non cancella i file del PC) e "
           "premi Rileggi (F5). Se non ti servono sull'iPhone: tasto destro sull'album → Va bene così.",
    "R19": "Accorcia il percorso: in Esplora file rinomina con un nome più corto la cartella dell'artista o dell'album "
           "(o spostala più vicino alla cartella della musica), poi premi Rileggi (F5). Per arrivare alla cartella: "
           "tasto destro sul problema → Apri la cartella in Esplora risorse.",
    "R20": "Applica la correzione lascia nel titolo solo il titolo. Se il numero o il nome fa parte del titolo vero "
           "(per esempio \"1999 - …\"), togli la casella di quella riga prima di applicare.",
    "R21": "Applica la correzione: cambiano solo gli spazi in più, nessun rischio.",
    "R22": "Con la correzione (lettere rovinate come \"Ã©\"): controlla la colonna Diventa e Applica. Con il carattere "
           "\"�\" la lettera è persa: Mostra i brani, Cambia i tag (tasto E) e riscrivi a mano titolo, artista o "
           "album; oppure tasto destro sull'album → Controlla online, per prendere i tag dal catalogo.",
    "R23": "Applica la correzione scrive ovunque la grafia scelta (anche negli album fuori dalla selezione: compaiono "
           "nei risultati). Con \"Accenti diversi\" controlla prima quale accento è giusto. Per un'altra grafia: "
           "Mostra i brani, Cambia i tag (tasto E) e scrivila su tutti, poi Controlla di nuovo questi album.",
    "R24": "Applica la correzione scrive il nome più usato su tutti i brani dell'album. Per un'altra grafia: Mostra i "
           "brani, Cambia i tag (tasto E) e scrivi il nome dell'album su tutti i brani.",
    "R25": "Applica la correzione scrive lo stesso artista dell'album su tutti i brani. Per un'altra grafia: Mostra i "
           "brani, seleziona tutti i brani dell'album e in Cambia i tag (tasto E) scrivi l'artista dell'album.",
    "R26": "Applica la correzione. Se è davvero una compilation di un solo artista: tasto destro sull'album → Va bene "
           "così.",
    "R27": f"Applica la correzione. Se l'album è davvero una compilation ma la correzione spegne la spunta, scrivi "
           f"\"{VARIOUS_ARTISTS}\" come artista dell'album (Mostra i brani, Cambia i tag, tasto E) e Controlla di nuovo "
           "questi album.",
    "R28": "Se sono lo stesso album: Applica la correzione. Se sono album diversi: non applicare; Mostra i brani, "
           "Cambia i tag (tasto E) e dai a uno dei due un nome che resti diverso anche senza gli zeri (per esempio "
           "con l'anno: \"Raccolta 1 (1998)\").",
    "R29": "Se c'è la correzione (numeri presi dai nomi dei file): controlla la colonna Diventa e Applica. Altrimenti "
           "Mostra i brani e guarda le cartelle. Se sono due album diversi con lo stesso nome (due \"Greatest Hits\", "
           "due edizioni), dai a uno dei due un nome diverso con Cambia i tag (tasto E), per esempio con l'anno o "
           "l'edizione: \"Greatest Hits (1981)\". Se è lo stesso album con i numeri sbagliati, correggi N. traccia (e "
           "N. disco) dei brani sbagliati. Poi Controlla di nuovo questi album.",
    "R30": "Mostra i brani e correggi con Cambia i tag (tasto E): il N. disco dei brani che non l'hanno (lo dicono di "
           "solito la cartella o il nome del file, \"CD2\"), oppure il numero o il totale sbagliato. I numeri giusti "
           "dell'edizione: tasto destro sull'album → Controlla online.",
    "R31": "Applica la correzione scrive su tutti i brani il totale più frequente. Se è sbagliato proprio quello: "
           "Mostra i brani e scrivi il totale giusto con Cambia i tag (tasto E) su tutti.",
    "R32": "Se non ti servono i brani che ci sono solo in questa copia (il dettaglio li nomina): tasto destro sul "
           "problema → Sposta nel cestino questa copia, controlla l'elenco dei file e conferma (si recuperano dal "
           "Cestino di Windows). Oppure spostala a mano fuori dalle cartelle della musica con Esplora file. Se la "
           "vuoi tenere: tasto destro sull'album → Va bene così.",
    "R33": "Tasto destro sul problema → Sposta nel cestino la copia in … (scegli quale togliere), controlla l'elenco "
           "dei file e conferma (si recuperano dal Cestino di Windows). Se le vuoi tenere tutte e due: tasto destro "
           "sull'album → Va bene così.",
    "I1": "Mostra i brani, poi nella scheda PC Usa i tag da PC a iPhone e Applica. Se sono giusti quelli dell'iPhone: "
          "scheda iPhone, Usa i tag da iPhone a PC.",
    "I2": "Mostra i brani, poi Copia da PC a iPhone e Applica. Se sull'iPhone non li vuoi, ignora.",
    "I3": _ONLY_ON_DEVICE,
    "I4": "Scheda iPhone: Mostra → \"Senza file sull'iPhone (fantasmi)\", seleziona i brani, Elimina dall'iPhone e "
          "Applica.",
    "W1": "Se i brani ti servono, aggiungili alla cartella dell'album. Se l'edizione trovata non è la tua, Dettagli "
          "della verifica online per sceglierne un'altra.",
    "W2": "Applica le correzioni scelte scrive i tag del catalogo. Controlla prima l'edizione (Dettagli della verifica "
          "online): se non è la tua, sceglierne un'altra cambia le correzioni.",
    "W3": "Controlla che artista e album siano scritti bene, poi riprova; oppure prova un altro catalogo.",
}
# i problemi trovati dall'AI (senza una regola): per tipo
KIND_ADVICE = {
    KIND_NOT_UPDATED: "Mostra i brani e confronta i tag con Cambia i tag (tasto E).",
    KIND_FEW_TRACKS: "Premi Verifica online questi album: i cataloghi dicono quali brani mancano.",
    KIND_SPLIT: "Applica la correzione (se c'è); altrimenti Mostra i brani e rendi uguali album e artista dell'album "
                "con Cambia i tag. Se l'AI si sbaglia, ignora.",
    KIND_DUPLICATE: _MANUAL_DUPLICATE,
    KIND_MISSING_TAGS: _MANUAL_TAGS,
    KIND_UNREADABLE: _MANUAL_UNREADABLE,
    KIND_ONLY_ON_DEVICE: _ONLY_ON_DEVICE,
    KIND_ONLINE: "Applica le correzioni scelte scrive i tag del catalogo; controlla prima l'edizione.",
    KIND_FORMAT: "Converti i file in MP3 o FLAC con un programma di conversione, poi Rileggi (F5).",
    KIND_NAMES: "Applica la correzione (se c'è); altrimenti Mostra i brani e scrivi lo stesso nome su tutti con Cambia "
                "i tag (tasto E).",
}


def advice(issue: Issue) -> str:
    """Cosa fare per il problema, in una o due frasi: con la sua regola, altrimenti con il suo tipo; "" se non c'è."""
    rule = issue.rule_id.split(".", 1)[0]
    if rule in ADVICE:
        result = ADVICE[rule]
    else:
        result = KIND_ADVICE.get(issue.kind, "")
    return result


def report_text(report: ScanReport) -> str:
    lines = [f"Controllo di {report.target} — {time.strftime('%Y-%m-%d %H:%M')}",
             f"{report.tracks_scanned} brani, {report.albums_scanned} album, {len(report.issues)} problemi"]
    if report.ai_profile:
        lines.append(f"Analisi AI: {report.ai_profile}")
    for error in report.ai_errors:
        lines.append(f"Errore AI: {error}")
    if report.cancelled:
        lines.append("Controllo interrotto: i risultati sono parziali")
    if report.stopped:
        lines.append(f"Annullati: {', '.join(report.stopped)} (i risultati sono quelli senza)")
    if report.online_notes:
        lines.append(f"Verifica online: {len(report.online_notes)} album non trovati nei cataloghi (non sono problemi)")
        for note in report.online_notes:
            lines.append(f"    - {note}")
    for issue in report.issues:
        lines += ["", f"[{issue.severity}] {KIND_LABELS.get(issue.kind, issue.kind)} ({issue.origin}): {issue.title}",
                  f"    {issue.detail}"]
        if issue.ai_note:
            lines.append(f"    AI: {issue.ai_note}")
        if issue.fix is not None:
            lines.append(f"    Correzione proposta: {issue.fix.description}")
        suggestion = advice(issue)
        if suggestion:
            lines.append(f"    Cosa fare: {suggestion}")
        for path in issue.files[:50]:
            lines.append(f"    - {path}")
        if len(issue.files) > 50:
            lines.append(f"    … e altri {len(issue.files) - 50}")
    translated = []
    for line in lines:
        translated.append(tr(line))
    result = "\n".join(translated) + "\n"
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
