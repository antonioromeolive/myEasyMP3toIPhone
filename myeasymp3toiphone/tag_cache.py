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
CACHE_VERSION = 1
TAG_FIELD_NAMES = {field.name for field in fields(TrackTags)}


class TagCache:
    def __init__(self, home: Path) -> None:
        self.home = home
        self._lock = threading.Lock()
        self._dirty = False
        self._entries = {}
        data = read_json(home / CACHE_FILE)
        if isinstance(data, dict) and data.get("version") == CACHE_VERSION and isinstance(data.get("files"), dict):
            self._entries = data["files"]

    def lookup(self, path: Path):
        """(TrackTags, durata, errore) se la voce vale ancora per il file com'è ora; altrimenti None."""
        result = None
        entry = self._entries.get(path_key(path))
        if isinstance(entry, dict):
            try:
                info = path.stat()
                if entry.get("s") == info.st_size and entry.get("m") == info.st_mtime:
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


def cached_track(path: Path, cache: Optional[TagCache]):
    """Il brano dalla cache, o None se va letto dal file."""
    result = None
    if cache is not None:
        found = cache.lookup(path)
        if found is not None:
            from .library import Track
            tags, length, error = found
            result = Track(path=path, tags=tags, length=length, error=error)
    return result
