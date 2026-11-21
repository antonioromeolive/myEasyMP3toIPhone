# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le modifiche dei tag in sospeso: i file sul PC sono in sola lettura e non cambiano mai.

Ogni modifica (editor, scansione, Verifica album, copertina) si salva qui, nella cartella dati, per percorso del file.
La Libreria mostra i valori modificati; le copie inviate all'iPhone (ed esportate o importate) li ricevono. Il file
originale resta com'è.

    modifiche_tag.json   {"files": {"<percorso>": {"tags": {campo: valore}, "cover": "<nome>.jpg"}}}
    copertine/           le immagini delle copertine nuove
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Optional

from .config import read_json, write_json
from .tags import TAG_FIELDS, TrackTags

log = logging.getLogger(__name__)

OVERLAY_FILE = "modifiche_tag.json"
COVERS_FOLDER = "copertine"
FIELD_NAMES = [name for name, _label in TAG_FIELDS]
FIELD_LABELS = dict(TAG_FIELDS)


def path_key(path) -> str:
    """La chiave di un file: percorso assoluto, senza differenze di maiuscole (Windows)."""
    result = os.path.normcase(os.path.abspath(str(path)))
    return result


def _image_extension(data: bytes) -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        result = ".png"
    else:
        result = ".jpg"
    return result


class TagOverlay:
    def __init__(self, home: Path) -> None:
        self.home = home
        self.entries = {}
        data = read_json(home / OVERLAY_FILE)
        if isinstance(data, dict) and isinstance(data.get("files"), dict):
            for key, entry in data["files"].items():
                if isinstance(entry, dict):
                    self.entries[key] = entry

    # ------------------------------------------------------------------ lettura

    def changes_for(self, path) -> dict:
        entry = self.entries.get(path_key(path), {})
        result = dict(entry.get("tags", {})) if isinstance(entry.get("tags"), dict) else {}
        return result

    def cover_for(self, path) -> Optional[bytes]:
        entry = self.entries.get(path_key(path), {})
        result = None
        name = entry.get("cover")
        if isinstance(name, str) and name:
            try:
                result = (self.home / COVERS_FOLDER / name).read_bytes()
            except OSError as exc:
                log.warning("Copertina modificata non trovata per %s: %s", path, exc)
                result = None
        return result

    def is_edited(self, path) -> bool:
        result = path_key(path) in self.entries
        return result

    def signature(self, path) -> str:
        """Cambia quando cambiano le modifiche di un file: "" se non ne ha."""
        entry = self.entries.get(path_key(path))
        if entry:
            text = json.dumps(entry, sort_keys=True, ensure_ascii=False)
            result = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
        else:
            result = ""
        return result

    def describe(self, track) -> str:
        """Le modifiche di un brano, per il suggerimento in tabella."""
        lines = []
        original = track.original_tags or track.tags
        for name, value in self.changes_for(track.path).items():
            before = getattr(original, name, "")
            lines.append(f"{FIELD_LABELS.get(name, name)}: {before if before not in (None, '') else '—'} → "
                         f"{value if value not in (None, '') else '—'}")
        if self.entries.get(path_key(track.path), {}).get("cover"):
            lines.append("Copertina nuova")
        result = "\n".join(lines)
        return result

    # ------------------------------------------------------------------ applicazione

    def effective(self, path, original: TrackTags) -> TrackTags:
        result = original.copy()
        for name, value in self.changes_for(path).items():
            if name in FIELD_NAMES:
                setattr(result, name, value)
        return result

    def apply(self, tracks: list) -> None:
        """I brani mostrano i tag modificati; quelli del file restano in Track.original_tags."""
        for track in tracks:
            if track.original_tags is None:
                track.original_tags = track.tags.copy()
            track.tags = self.effective(track.path, track.original_tags)

    # ------------------------------------------------------------------ modifica

    def set_tags(self, track, new_tags: TrackTags) -> None:
        """Salva in sospeso i campi di new_tags diversi da quelli del file."""
        original = track.original_tags or track.tags
        key = path_key(track.path)
        changes = {}
        for name in FIELD_NAMES:
            value = getattr(new_tags, name)
            if value != getattr(original, name):
                changes[name] = value
        entry = dict(self.entries.get(key, {}))
        if changes:
            entry["tags"] = changes
        else:
            entry.pop("tags", None)
        self._store(key, entry)
        if track.original_tags is None:
            track.original_tags = original.copy()
        track.tags = self.effective(track.path, track.original_tags)

    def set_cover(self, track, data: bytes) -> None:
        folder = self.home / COVERS_FOLDER
        folder.mkdir(parents=True, exist_ok=True)
        name = hashlib.sha1(data).hexdigest()[:20] + _image_extension(data)
        target = folder / name
        if not target.exists():
            target.write_bytes(data)
        key = path_key(track.path)
        entry = dict(self.entries.get(key, {}))
        entry["cover"] = name
        self._store(key, entry)

    def clear(self, track) -> None:
        """Torna ai tag del file."""
        self.entries.pop(path_key(track.path), None)
        if track.original_tags is not None:
            track.tags = track.original_tags.copy()

    def _store(self, key: str, entry: dict) -> None:
        if entry:
            self.entries[key] = entry
        else:
            self.entries.pop(key, None)

    def save(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        write_json(self.home / OVERLAY_FILE, {"files": self.entries})
