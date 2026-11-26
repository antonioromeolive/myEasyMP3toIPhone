# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le suonerie sul PC: i file .m4r (AAC, al massimo ~40 s) della cartella delle suonerie, e Crea una suoneria da un
brano con ffmpeg (che l'utente installa da sé: il programma non lo distribuisce).

Crea una suoneria scrive solo un file NUOVO nella cartella delle suonerie (ffmpeg -n: mai sopra un file che c'è): il
brano non cambia. Rinomina e Sposta nel cestino valgono solo per i .m4r della cartella delle suonerie, dopo una
conferma (la finestra)."""

from __future__ import annotations

import array
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .library import safe_name
from .overlay import path_key

log = logging.getLogger(__name__)

RINGTONE_SUFFIX = ".m4r"
MAX_SECONDS = 39.5          # l'iPhone rifiuta una suoneria oltre i 40 s: un po' di margine per l'AAC
DEFAULT_SECONDS = 30.0      # il pezzo proposto all'apertura della finestra
PEAK_RATE = 4000            # campioni al secondo letti per la forma d'onda (mono)
AAC_BITRATE = "192k"
FFMPEG_TIMEOUT = 300
FFMPEG_MISSING = ("Per creare una suoneria serve ffmpeg, che il programma non contiene: installalo (per esempio "
                  "winget install ffmpeg) e, se non è nel PATH, scegli il file ffmpeg.exe in Impostazioni → Suonerie.")


class RingtoneError(Exception):
    """Un errore con un messaggio leggibile dall'utente (ffmpeg mancante o non riuscito, file non valido)."""


@dataclass
class RingtoneFile:
    """Un .m4r della cartella delle suonerie: il nome (il titolo nei tag, altrimenti il nome del file) e la durata."""
    path: Path
    name: str
    duration_ms: int = 0
    size: int = 0
    error: str = ""


def find_ffmpeg(setting: str = "") -> Optional[Path]:
    """ffmpeg: il file scelto in Impostazioni (o la cartella che lo contiene), altrimenti quello nel PATH; None se
    non c'è."""
    result = None
    text = os.path.expandvars((setting or "").strip().strip('"'))
    if text:
        candidate = Path(text).expanduser()
        if candidate.is_dir():
            candidate = candidate / "ffmpeg.exe"
        if candidate.is_file():
            result = candidate
    else:
        found = shutil.which("ffmpeg")
        if found:
            result = Path(found)
    return result


def _run_ffmpeg(arguments: list, binary: bool = False):
    """ffmpeg senza finestra della console; RingtoneError con le ultime righe dell'errore se non riesce."""
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    try:
        completed = subprocess.run(arguments, capture_output=True, timeout=FFMPEG_TIMEOUT, creationflags=flags,
                                   stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RingtoneError(f"ffmpeg non è partito: {exc}") from exc
    if completed.returncode != 0:
        lines = completed.stderr.decode("utf-8", "replace").strip().splitlines()
        raise RingtoneError("ffmpeg non è riuscito: " + (" / ".join(lines[-3:]) if lines else
                                                          f"codice {completed.returncode}"))
    result = completed.stdout if binary else completed.stdout.decode("utf-8", "replace")
    return result


def peaks_from_pcm(data: bytes, buckets: int) -> list:
    """I picchi (0…1) di audio PCM a 16 bit mono, in buckets gruppi: la forma d'onda da disegnare."""
    samples = array.array("h")
    samples.frombytes(data[:len(data) - len(data) % 2])
    if sys.byteorder != "little":
        samples.byteswap()
    result = []
    count = len(samples)
    if count and buckets > 0:
        index = 0
        while index < buckets:
            start = count * index // buckets
            end = max(start + 1, count * (index + 1) // buckets)
            chunk = samples[start:end]
            peak = max(max(chunk), -min(chunk)) if len(chunk) else 0
            result.append(min(1.0, peak / 32768.0))
            index += 1
    return result


def waveform(ffmpeg: Path, source: Path, buckets: int = 1200) -> tuple:
    """(durata in secondi, picchi) del brano, letto da ffmpeg in mono a PEAK_RATE campioni al secondo."""
    data = _run_ffmpeg([str(ffmpeg), "-v", "error", "-nostdin", "-i", str(source), "-vn", "-ac", "1",
                        "-ar", str(PEAK_RATE), "-f", "s16le", "-"], binary=True)
    seconds = (len(data) // 2) / PEAK_RATE
    if seconds <= 0:
        raise RingtoneError(f"{source.name}: ffmpeg non ha letto audio")
    result = (seconds, peaks_from_pcm(data, buckets))
    return result


def clamp_selection(start: float, end: float, total: float) -> tuple:
    """Inizio e fine validi: dentro il brano, fine dopo l'inizio, al massimo MAX_SECONDS (si accorcia la fine)."""
    begin = min(max(0.0, start), max(0.0, total - 0.1))
    finish = min(max(begin + 0.1, end), total)
    if finish - begin > MAX_SECONDS:
        finish = begin + MAX_SECONDS
    result = (round(begin, 2), round(finish, 2))
    return result


def _filters(length: float, fade_in: float, fade_out: float) -> list:
    """I filtri di ffmpeg per le dissolvenze (0 = niente), dentro un pezzo lungo length secondi."""
    result = []
    if fade_in > 0:
        result.append(f"afade=t=in:st=0:d={min(fade_in, length):.2f}")
    if fade_out > 0:
        duration = min(fade_out, length)
        result.append(f"afade=t=out:st={max(0.0, length - duration):.2f}:d={duration:.2f}")
    return result


def ringtone_command(ffmpeg: Path, source: Path, target: Path, start: float, end: float, fade_in: float,
                     fade_out: float, title: str) -> list:
    """Il comando di ffmpeg per il pezzo start…end (secondi) in AAC dentro un .m4r, con il titolo nei tag; -n: se
    il file c'è già ffmpeg non lo sovrascrive."""
    length = end - start
    result = [str(ffmpeg), "-v", "error", "-nostdin", "-n", "-ss", f"{start:.3f}", "-t", f"{length:.3f}",
              "-i", str(source), "-vn", "-map_metadata", "-1"]
    filters = _filters(length, fade_in, fade_out)
    if filters:
        result += ["-af", ",".join(filters)]
    result += ["-ac", "2", "-ar", "44100", "-c:a", "aac", "-b:a", AAC_BITRATE, "-metadata", f"title={title}",
               "-movflags", "+faststart", "-f", "ipod", str(target)]
    return result


def preview_command(ffmpeg: Path, source: Path, target: Path, start: float, end: float, fade_in: float,
                    fade_out: float) -> list:
    """Il comando per il WAV temporaneo che si ascolta nella finestra."""
    length = end - start
    result = [str(ffmpeg), "-v", "error", "-nostdin", "-y", "-ss", f"{start:.3f}", "-t", f"{length:.3f}",
              "-i", str(source), "-vn"]
    filters = _filters(length, fade_in, fade_out)
    if filters:
        result += ["-af", ",".join(filters)]
    result += ["-ac", "2", "-ar", "44100", "-f", "wav", str(target)]
    return result


def make_preview(ffmpeg: Path, source: Path, start: float, end: float, fade_in: float, fade_out: float) -> Path:
    """Il pezzo scelto in un WAV temporaneo (chi chiama lo cancella)."""
    handle, name = tempfile.mkstemp(prefix="myEasyMP3toIPhone_suoneria_", suffix=".wav")
    os.close(handle)
    target = Path(name)
    try:
        _run_ffmpeg(preview_command(ffmpeg, source, target, start, end, fade_in, fade_out))
    except RingtoneError:
        target.unlink(missing_ok=True)
        raise
    return target


def unique_target(folder: Path, title: str) -> Path:
    """Il file nuovo per una suoneria: il titolo come nome, con " (2)", " (3)"… se c'è già."""
    base = safe_name(title, "Suoneria")
    candidate = folder / (base + RINGTONE_SUFFIX)
    counter = 2
    while candidate.exists():
        candidate = folder / f"{base} ({counter}){RINGTONE_SUFFIX}"
        counter += 1
    return candidate


def create_ringtone(ffmpeg: Path, source: Path, folder: Path, start: float, end: float, fade_in: float,
                    fade_out: float, title: str) -> Path:
    """Crea la suoneria come file nuovo nella cartella delle suonerie (che si crea se manca) e la restituisce. Il
    brano non cambia; un file con lo stesso nome non si sovrascrive mai."""
    if end - start > MAX_SECONDS + 0.01 or end <= start:
        raise RingtoneError(f"Una suoneria dura al massimo {MAX_SECONDS:g} secondi.")
    folder.mkdir(parents=True, exist_ok=True)
    target = unique_target(folder, title)
    try:
        _run_ffmpeg(ringtone_command(ffmpeg, source, target, start, end, fade_in, fade_out, title.strip()))
    except RingtoneError:
        if target.exists() and target.stat().st_size == 0:
            target.unlink(missing_ok=True)       # un file vuoto lasciato da ffmpeg interrotto
        raise
    result = target
    return result


def read_ringtone(path: Path) -> RingtoneFile:
    """Nome e durata di un .m4r (mutagen); error se non è un AAC leggibile."""
    from mutagen.mp4 import MP4
    name = path.stem
    duration = 0
    size = 0
    error = ""
    try:
        size = path.stat().st_size
        audio = MP4(str(path))
        titles = audio.tags.get("\xa9nam") if audio.tags else None
        if titles and str(titles[0]).strip():
            name = str(titles[0]).strip()
        duration = int(round(audio.info.length * 1000))
        if not str(getattr(audio.info, "codec", "")).startswith("mp4a.40."):
            error = "non è AAC"
    except Exception as exc:  # noqa: BLE001 - mutagen solleva tipi diversi per un file rovinato
        error = f"non si legge ({exc})"
    result = RingtoneFile(path=path, name=name, duration_ms=duration, size=size, error=error)
    return result


def list_folder(folder: Optional[Path]) -> list:
    """I .m4r della cartella delle suonerie (non le sottocartelle), per nome."""
    result = []
    if folder is not None and folder.is_dir():
        paths = []
        for entry in folder.iterdir():
            if entry.is_file() and entry.suffix.lower() == RINGTONE_SUFFIX:
                paths.append(entry)
        paths.sort(key=lambda item: item.name.casefold())
        for path in paths:
            result.append(read_ringtone(path))
    return result


def in_folder(path: Path, folder: Optional[Path]) -> bool:
    """Il file sta direttamente nella cartella delle suonerie (le sole dove Rinomina e Cestino sono ammessi)."""
    result = (folder is not None and path.suffix.lower() == RINGTONE_SUFFIX
              and path_key(path.parent) == path_key(folder))
    return result


def rename_ringtone(path: Path, folder: Optional[Path], new_name: str) -> Path:
    """Rinomina un .m4r della cartella delle suonerie (il nome nuovo senza estensione); mai sopra un altro file."""
    if not in_folder(path, folder):
        raise RingtoneError("Si rinominano solo le suonerie della cartella delle suonerie.")
    target = path.with_name(safe_name(new_name, path.stem) + RINGTONE_SUFFIX)
    if target.exists() and path_key(target) != path_key(path):
        raise RingtoneError(f"C'è già un file {target.name}.")
    path.rename(target)
    result = target
    return result


def same_ringtone(name: str, duration_ms: int, other_name: str, other_ms: int) -> bool:
    """Una suoneria del PC e una dell'iPhone sono la stessa: stesso nome (maiuscole a parte) e durata entro 1 s
    (la durata dell'iPhone può mancare)."""
    same_name = name.strip().casefold() == other_name.strip().casefold()
    close = not duration_ms or not other_ms or abs(duration_ms - other_ms) <= 1000
    result = same_name and close
    return result


def format_ms(duration_ms: int) -> str:
    total = int(round(duration_ms / 1000))
    result = f"{total // 60}:{total % 60:02d}" if duration_ms > 0 else ""
    return result
