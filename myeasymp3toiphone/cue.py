# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le immagini di un disco intero: un FLAC (o WAV, APE…) con tutte le tracce in un file solo e il foglio CUE che dice
dove comincia ognuna, accanto ("Album.cue") o dentro il FLAC. Per i Controlli un album così non ha "un brano solo"
né numeri di traccia mancanti. Solo lettura: i file non si toccano."""

from __future__ import annotations

import re
from pathlib import Path

CUE_SUFFIX = ".cue"
CUE_ENCODINGS = ("utf-8-sig", "cp1252")       # i CUE di EAC sono spesso in ANSI
MIN_TRACKS = 2                                 # un CUE con una traccia sola è un singolo, non un'immagine
LEAD_OUT = 170                                 # nel CUESHEET di un FLAC: la traccia finta di fine disco
FILE_LINE = re.compile(r'^\s*FILE\s+(?:"([^"]+)"|(\S+))', re.IGNORECASE)
TRACK_LINE = re.compile(r"^\s*TRACK\s+\d+", re.IGNORECASE)


def tracks_by_file(text: str) -> dict:
    """{nome del file senza estensione, in minuscolo: tracce} dal testo di un foglio CUE. Si confronta senza
    l'estensione: EAC scrive spesso FILE "Album.wav" anche quando il file è poi diventato Album.flac."""
    result = {}
    current = None
    for line in text.splitlines():
        found = FILE_LINE.match(line)
        if found:
            name = found.group(1) or found.group(2)
            current = Path(name.replace("\\", "/")).stem.casefold()
            result.setdefault(current, 0)
        elif current is not None and TRACK_LINE.match(line):
            result[current] += 1
    return result


def read_cue(path: Path) -> str:
    """Il testo di un foglio CUE ("" se non si legge)."""
    result = ""
    raw = b""
    try:
        raw = Path(path).read_bytes()
    except OSError:
        raw = b""
    index = 0
    decoded = False
    while not decoded and index < len(CUE_ENCODINGS):
        try:
            result = raw.decode(CUE_ENCODINGS[index])
            decoded = True
        except UnicodeDecodeError:
            index += 1
    return result


def folder_sheets(folder: Path) -> dict:
    """{nome del file audio senza estensione, in minuscolo: tracce} di tutti i CUE della cartella. Un CUE con lo stesso
    nome del file audio vale per quel file anche se dentro nomina un altro file."""
    result = {}
    sheets = []
    try:
        for entry in Path(folder).iterdir():
            if entry.suffix.casefold() == CUE_SUFFIX and entry.is_file():
                sheets.append(entry)
    except OSError:
        sheets = []
    for sheet in sheets:
        counts = tracks_by_file(read_cue(sheet))
        total = 0
        for name, count in counts.items():
            result[name] = max(result.get(name, 0), count)
            total += count
        own = sheet.stem.casefold()
        result[own] = max(result.get(own, 0), total)
    return result


def embedded_tracks(path: Path) -> int:
    """Le tracce del CUE dentro un FLAC (il blocco CUESHEET o il tag CUESHEET); 0 se non c'è o non si legge."""
    result = 0
    if Path(path).suffix.casefold() == ".flac":
        try:
            from mutagen.flac import FLAC
            audio = FLAC(str(path))
            if audio.cuesheet is not None:
                for track in audio.cuesheet.tracks:
                    if track.track_number != LEAD_OUT:
                        result += 1
            if result == 0 and audio.tags is not None:
                for text in audio.tags.get("cuesheet", []):
                    for count in tracks_by_file(text).values():
                        result = max(result, count)
        except Exception:  # noqa: BLE001 - un file che non si legge non è un'immagine, non un errore
            result = 0
    return result


def cue_images(tracks: list, embedded: bool = True) -> dict:
    """{percorso: tracce} dei brani che sono l'immagine di un disco intero (almeno MIN_TRACKS tracce nel CUE).
    embedded: guarda anche dentro i FLAC (apre i file: per pochi brani)."""
    sheets_of = {}
    result = {}
    for track in tracks:
        path = Path(track.path)
        folder = path.parent
        if folder not in sheets_of:
            sheets_of[folder] = folder_sheets(folder) if folder.is_dir() else {}
        count = sheets_of[folder].get(path.stem.casefold(), 0)
        if count < MIN_TRACKS and embedded:
            count = embedded_tracks(path)
        if count >= MIN_TRACKS:
            result[track.path] = count
    return result


def all_images(tracks: list, embedded: bool = True) -> bool:
    """True se tutti i brani (almeno uno) sono immagini di un disco intero."""
    images = cue_images(tracks, embedded) if tracks else {}
    result = bool(tracks) and len(images) == len(tracks)
    return result
