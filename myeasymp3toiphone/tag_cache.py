# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""I tag già letti, conservati nella cartella dati (cache_tag.json): riaprire una cartella grande rilegge solo i file
cambiati. Una voce vale finché il file ha la stessa dimensione e la stessa data di modifica. I file non si toccano."""

from __future__ import annotations

import logging
import threading
from dataclasses import asdict, fields
from pathlib import Path
from typing import Optional

from .config import read_json, write_json
from .overlay import path_key
from .tags import TrackTags

log = logging.getLogger(__name__)

CACHE_FILE = "cache_tag.json"
CACHE_VERSION = 3   # 2: anche la spunta compilation; 3: negli MP3 anche i tag APEv2 e ID3v1
TAG_FIELD_NAMES = {field.name for field in fields(TrackTags)}
# Dalla versione 2: un MP3 con uno di questi campi vuoti si rilegge (APEv2 o ID3v1 potrebbero riempirlo); le altre
# voci valgono ancora, così una cartella grande non si rilegge tutta.
REREAD_IF_EMPTY = ("title", "artist", "album", "year", "genre", "track_number")


def _still_valid_v2(key: str, entry) -> bool:
    result = isinstance(entry, dict)
    if result and key.lower().endswith(".mp3"):
        tags = entry.get("t") or {}
        for name in REREAD_IF_EMPTY:
            if tags.get(name) in (None, ""):
                result = False
    return result


class TagCache:
    def __init__(self, home: Path) -> None:
        self.home = home
        self._lock = threading.Lock()
        self._dirty = False
        self._entries = {}
        data = read_json(home / CACHE_FILE)
        if isinstance(data, dict) and data.get("version") == CACHE_VERSION and isinstance(data.get("files"), dict):
            self._entries = data["files"]
        elif isinstance(data, dict) and data.get("version") == 2 and isinstance(data.get("files"), dict):
            for key, entry in data["files"].items():
                if _still_valid_v2(key, entry):
                    self._entries[key] = entry
            self._dirty = True

    def lookup(self, path: Path, stat: Optional[tuple] = None):
        """(TrackTags, durata, errore) se la voce vale ancora per il file com'è ora; altrimenti None.
        stat: (dimensione, data di modifica) già noti dall'elenco della cartella; senza, si chiedono al disco."""
        result = None
        entry = self._entries.get(path_key(path))
        if isinstance(entry, dict):
            try:
                if stat is None:
                    info = path.stat()
                    stat = (info.st_size, info.st_mtime)
                if entry.get("s") == stat[0] and entry.get("m") == stat[1]:
                    values = {}
                    for name, value in (entry.get("t") or {}).items():
                        if name in TAG_FIELD_NAMES:
                            values[name] = value
                    result = (TrackTags(**values), float(entry.get("l", 0.0)), str(entry.get("e", "")))
            except (OSError, TypeError, ValueError):
                result = None
        return result

    def store(self, track) -> None:
        try:
            info = track.path.stat()
            entry = {"s": info.st_size, "m": info.st_mtime, "t": asdict(track.original_tags or track.tags),
                     "l": track.length, "e": track.error}
            with self._lock:
                self._entries[path_key(track.path)] = entry
                self._dirty = True
        except OSError:
            pass  # un file sparito nel frattempo: niente da ricordare

    def fingerprint(self, path: Path) -> str:
        """L'impronta dell'audio già calcolata (provenance), se la voce vale ancora per il file; altrimenti ""."""
        result = ""
        entry = self._entries.get(path_key(path))
        if isinstance(entry, dict) and entry.get("f"):
            try:
                info = path.stat()
                if entry.get("s") == info.st_size and entry.get("m") == info.st_mtime:
                    result = str(entry["f"])
            except OSError:
                result = ""
        return result

    def store_fingerprint(self, path: Path, value: str) -> None:
        """Si aggiunge alla voce dei tag del file (che deve esserci e valere): cambia il file, si perde con lei."""
        with self._lock:
            entry = self._entries.get(path_key(path))
            if isinstance(entry, dict) and value:
                entry["f"] = value
                self._dirty = True

    def save(self) -> None:
        if self._dirty:
            with self._lock:
                data = {"version": CACHE_VERSION, "files": dict(self._entries)}
                self._dirty = False
            try:
                self.home.mkdir(parents=True, exist_ok=True)
                write_json(self.home / CACHE_FILE, data)
            except OSError as exc:
                log.warning("Cache dei tag NON salvata: %s", exc)

    def __len__(self) -> int:
        result = len(self._entries)
        return result


def cached_track(path: Path, cache: Optional[TagCache], stat: Optional[tuple] = None):
    """Il brano dalla cache, o None se va letto dal file. stat: come in TagCache.lookup."""
    result = None
    if cache is not None:
        found = cache.lookup(path, stat)
        if found is not None:
            from .library import Track
            tags, length, error = found
            result = Track(path=path, tags=tags, length=length, error=error)
    return result
