# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""L'invio all'app Musica dell'iPhone tramite iTunes, con la sua interfaccia di automazione ufficiale (COM
iTunes.Application).

Per ogni brano: una copia, nella cartella delle copie per iTunes, con i tag e la copertina modificati (le modifiche in
sospeso; i FLAC convertiti in ALAC con ffmpeg, perché l'app Musica non li legge); la copia va nella libreria di
iTunes, nella playlist "myEasyMP3toIPhone"; poi, se richiesto, iTunes sincronizza l'iPhone. I file originali non si
toccano mai. iTunes usa le copie dove sono: la cartella delle copie va conservata.

Il registro itunes_aggiunti.json (cartella dati) ricorda per ogni file originale la sua copia e il brano di iTunes
(ID permanente): un invio successivo salta quello che non è cambiato e aggiorna il resto, senza doppioni.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from .config import read_json, write_json
from .library import is_cancelled, target_relative_path
from .overlay import path_key
from .tags import TagError, prepare_copy, read_cover

log = logging.getLogger(__name__)

MANIFEST_FILE = "itunes_aggiunti.json"
PLAYLIST_NAME = "myEasyMP3toIPhone"
OLD_PLAYLIST_NAME = "myCopiaStiMP3"   # il nome precedente: la playlist si rinomina, i brani restano
IPOD_SOURCE_KIND = 2            # ITSourceKindIPod: un iPhone/iPod collegato a iTunes
MTIME_TOLERANCE = 2.0
SAVE_EVERY = 50
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
WINGET_FFMPEG = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe"
FFMPEG_INSTALL = ["winget", "install", "--id", "Gyan.FFmpeg", "--exact", "--scope", "user",
                  "--accept-source-agreements", "--accept-package-agreements", "--disable-interactivity"]

ProgressFn = Callable[[int, int, str], None]


class ITunesError(Exception):
    """Un errore di iTunes o della conversione, con un messaggio leggibile."""


@dataclass
class ITunesReport:
    added: list = field(default_factory=list)
    updated: list = field(default_factory=list)
    skipped: int = 0
    needs_ffmpeg: list = field(default_factory=list)
    errors: list = field(default_factory=list)       # (percorso, messaggio)
    synced: list = field(default_factory=list)       # i nomi dei dispositivi sincronizzati
    cancelled: bool = False

    def summary(self) -> str:
        parts = [f"{len(self.added)} brani aggiunti a iTunes", f"{len(self.updated)} aggiornati",
                 f"{self.skipped} già presenti"]
        if self.needs_ffmpeg:
            parts.append(f"{len(self.needs_ffmpeg)} FLAC saltati (manca ffmpeg)")
        if self.errors:
            parts.append(f"{len(self.errors)} errori")
        if self.cancelled:
            parts.append("operazione annullata")
        result = ", ".join(parts)
        return result


# --------------------------------------------------------------------------- ffmpeg

def find_ffmpeg() -> Optional[str]:
    """ffmpeg nel PATH, oppure quello installato da winget per l'utente."""
    result = shutil.which("ffmpeg")
    if result is None and WINGET_FFMPEG.is_file():
        result = str(WINGET_FFMPEG)
    return result


def install_ffmpeg() -> str:
    """Installa ffmpeg per l'utente con winget (gratuito). Restituisce l'esito, leggibile."""
    try:
        completed = subprocess.run(FFMPEG_INSTALL, capture_output=True, text=True, timeout=900,
                                   creationflags=CREATE_NO_WINDOW)
        output = (completed.stdout or "") + (completed.stderr or "")
        if find_ffmpeg() is not None:
            result = "ffmpeg installato."
        else:
            result = f"ffmpeg NON installato (codice {completed.returncode}): {output.strip()[-400:]}"
    except (OSError, subprocess.SubprocessError) as exc:
        result = f"winget non disponibile ({exc}): installa ffmpeg a mano da https://www.gyan.dev/ffmpeg/builds/"
    return result


# --------------------------------------------------------------------------- copie

def copy_path_for(track, root: Path) -> Path:
    """La copia per iTunes: Artista/Album (Anno)/NN - Titolo, con .m4a (ALAC) al posto di .flac."""
    relative = target_relative_path(track)
    if track.path.suffix.lower() == ".flac":
        relative = relative.with_suffix(".m4a")
    result = root / relative
    return result


def _convert_to_alac(source: Path, target: Path, ffmpeg: str) -> None:
    command = [ffmpeg, "-nostdin", "-y", "-loglevel", "error", "-i", str(source), "-map", "0:a:0", "-c:a", "alac",
               "-map_metadata", "0", str(target)]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=600,
                                   creationflags=CREATE_NO_WINDOW)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ITunesError(f"conversione in ALAC non riuscita ({exc})") from exc
    if completed.returncode != 0:
        raise ITunesError(f"conversione in ALAC non riuscita: {completed.stderr.strip()[-300:]}")


def make_copy(track, target: Path, overlay, ffmpeg: Optional[str]) -> None:
    """La copia per iTunes, scritta con un nome temporaneo e poi rinominata. L'originale si legge soltanto."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f"{target.stem}.tmp{target.suffix}")
    cover = overlay.cover_for(track.path) if overlay is not None else None
    try:
        if track.path.suffix.lower() == ".flac":
            if ffmpeg is None:
                raise ITunesError("per i FLAC serve ffmpeg")
            _convert_to_alac(track.path, temporary, ffmpeg)
            if cover is None:
                cover = read_cover(track.path)   # ffmpeg non porta la copertina nel .m4a
        else:
            shutil.copyfile(str(track.path), str(temporary))
        prepare_copy(temporary, track.tags, cover)
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def _remove_old_copy(old: Path, root: Path) -> None:
    """Cancella una copia vecchia, solo se è dentro la cartella delle copie (mai altrove), e le cartelle vuote."""
    root_resolved = root.resolve()
    try:
        resolved = old.resolve()
        inside = root_resolved in resolved.parents
        if inside and resolved.is_file():
            resolved.unlink()
            folder = resolved.parent
            while folder != root_resolved and root_resolved in folder.parents and not any(folder.iterdir()):
                folder.rmdir()
                folder = folder.parent
    except OSError as exc:
        log.warning("Copia vecchia per iTunes non cancellata %s: %s", old, exc)


# --------------------------------------------------------------------------- iTunes (COM)

class ITunes:
    """iTunes aperto con l'interfaccia di automazione. Va usato in un solo thread (quello che lo crea)."""

    def __init__(self) -> None:
        import pythoncom
        from win32com.client import CastTo, gencache

        pythoncom.CoInitialize()
        self._cast = CastTo
        try:
            self.app = gencache.EnsureDispatch("iTunes.Application")
        except Exception as exc:  # noqa: BLE001 - COM restituisce errori di molti tipi
            pythoncom.CoUninitialize()
            raise ITunesError(f"iTunes non si apre ({exc}). È installato? (Microsoft Store: iTunes)") from exc
        self.playlist = self._playlist()

    def _playlist(self):
        found = None
        playlists = self.app.LibrarySource.Playlists
        for index in range(1, playlists.Count + 1):
            item = playlists.Item(index)
            if found is None and item.Name == PLAYLIST_NAME:
                found = item
        if found is None:
            for index in range(1, playlists.Count + 1):
                item = playlists.Item(index)
                if found is None and item.Name == OLD_PLAYLIST_NAME:
                    item.Name = PLAYLIST_NAME
                    found = item
        if found is None:
            found = self.app.CreatePlaylist(PLAYLIST_NAME)
        result = self._cast(found, "IITUserPlaylist")
        return result

    def find(self, pid) -> Optional[object]:
        """Il brano di iTunes con quell'ID permanente (alto, basso), o None se non c'è più."""
        result = None
        if pid:
            found = self.app.LibraryPlaylist.Tracks.ItemByPersistentID(int(pid[0]), int(pid[1]))
            if found is not None:
                result = self._cast(found, "IITFileOrCDTrack")
        return result

    def add(self, path: Path) -> list:
        """Aggiunge un file alla libreria e alla playlist: il suo ID permanente [alto, basso]."""
        import time
        status = self.playlist.AddFile(str(path))
        if status is None:
            raise ITunesError(f"iTunes non ha accettato {path.name}")
        while status.InProgress:
            time.sleep(0.1)
        tracks = status.Tracks
        if tracks is None or tracks.Count == 0:
            raise ITunesError(f"iTunes non ha aggiunto {path.name} (formato non supportato?)")
        track = tracks.Item(1)
        result = [int(self.app.ITObjectPersistentIDHigh(track)), int(self.app.ITObjectPersistentIDLow(track))]
        return result

    def devices(self) -> list:
        names = []
        sources = self.app.Sources
        for index in range(1, sources.Count + 1):
            source = sources.Item(index)
            if source.Kind == IPOD_SOURCE_KIND:
                names.append(source.Name)
        return names

    def sync(self) -> list:
        """Avvia la sincronizzazione di ogni iPhone/iPod collegato a iTunes; restituisce i loro nomi."""
        synced = []
        sources = self.app.Sources
        for index in range(1, sources.Count + 1):
            source = sources.Item(index)
            if source.Kind == IPOD_SOURCE_KIND:
                self._cast(source, "IITIPodSource").UpdateIPod()
                synced.append(source.Name)
        return synced

    def close(self) -> None:
        """Lascia iTunes aperto (una sincronizzazione può essere in corso) e libera l'interfaccia."""
        import pythoncom
        self.playlist = None
        self.app = None
        pythoncom.CoUninitialize()


# --------------------------------------------------------------------------- invio

def _unchanged(entry: dict, info, signature: str, target: Path) -> bool:
    result = (bool(entry) and entry.get("size") == info.st_size
              and abs(float(entry.get("mtime", 0)) - info.st_mtime) <= MTIME_TOLERANCE
              and entry.get("signature", "") == signature and entry.get("copy") == str(target) and target.exists())
    return result


def send_to_itunes(tracks: list, root: Path, overlay, home: Path, sync: bool,
                   progress: Optional[ProgressFn] = None, cancel: Optional[threading.Event] = None,
                   bridge_factory: Callable[[], object] = ITunes) -> ITunesReport:
    """I brani (con le modifiche in sospeso già applicate in track.tags) nella playlist "myEasyMP3toIPhone" di iTunes;
    con sync=True poi iTunes sincronizza l'iPhone."""
    report = ITunesReport()
    ffmpeg = find_ffmpeg()
    home.mkdir(parents=True, exist_ok=True)
    data = read_json(home / MANIFEST_FILE)
    manifest = data if isinstance(data, dict) else {}
    if progress is not None:
        progress(0, len(tracks), "apertura di iTunes")
    bridge = bridge_factory()
    try:
        index = 0
        while index < len(tracks) and not is_cancelled(cancel):
            track = tracks[index]
            if progress is not None:
                progress(index, len(tracks), track.path.name)
            key = path_key(track.path)
            entry = manifest.get(key, {}) if isinstance(manifest.get(key), dict) else {}
            target = copy_path_for(track, root)
            flac = track.path.suffix.lower() == ".flac"
            try:
                if track.error:
                    raise ITunesError(track.error)
                info = track.path.stat()
                signature = overlay.signature(track.path) if overlay is not None else ""
                current = bridge.find(entry.get("pid"))
                if current is not None and _unchanged(entry, info, signature, target):
                    report.skipped += 1
                elif flac and ffmpeg is None:
                    report.needs_ffmpeg.append(track.path)
                else:
                    old_copy = entry.get("copy")
                    if old_copy and old_copy != str(target):
                        if current is not None:
                            current.Delete()
                            current = None
                        _remove_old_copy(Path(old_copy), root)
                    make_copy(track, target, overlay, ffmpeg)
                    if current is not None:
                        current.UpdateInfoFromFile()
                        pid = entry.get("pid")
                        report.updated.append(track.path)
                    else:
                        pid = bridge.add(target)
                        report.added.append(track.path)
                    manifest[key] = {"copy": str(target), "size": info.st_size, "mtime": info.st_mtime,
                                     "signature": signature, "pid": pid}
            except (OSError, ITunesError, TagError) as exc:
                report.errors.append((track.path, str(exc)))
            except Exception as exc:  # noqa: BLE001 - errori COM di iTunes
                report.errors.append((track.path, f"iTunes: {exc}"))
            index += 1
            if index % SAVE_EVERY == 0:
                write_json(home / MANIFEST_FILE, manifest)
        report.cancelled = is_cancelled(cancel)
        if sync and not report.cancelled:
            if progress is not None:
                progress(len(tracks), len(tracks), "sincronizzazione dell'iPhone")
            report.synced = bridge.sync()
    finally:
        try:
            write_json(home / MANIFEST_FILE, manifest)
        finally:
            bridge.close()
    return report
