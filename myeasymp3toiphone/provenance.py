# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Da dove viene ogni brano dell'app Musica dell'iPhone: le impronte dell'audio e il registro della provenienza.

Impronta: un riassunto dell'audio che non cambia quando cambiano i tag, uguale per il file del PC e per la sua copia
sull'iPhone (anche se CopyTrans o il programma ne hanno riscritto i tag):
  * MP3: i primi 64 KB dopo il tag ID3v2;
  * FLAC: l'MD5 dell'audio decodificato che il file porta nella sua intestazione (STREAMINFO), o 64 KB di audio;
  * M4A: i primi 64 KB del blocco audio (mdat).
La stessa logica legge un file del PC o, a pezzi, un file dell'iPhone (fingerprint con una funzione read_at).

Registro: per ogni brano dell'iPhone (sync_id), il PC e il file da cui viene, con dimensione, data, le modifiche in
sospeso al momento dell'invio e l'impronta; e come è nato il collegamento. Sta nella cartella dati (REGISTRY_FILE) e
sull'iPhone (PHONE_REGISTRY, un file che l'iPhone non legge), così ogni PC vede anche le righe degli altri. Le
righe dei brani che non sono più sull'iPhone si tolgono.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import socket
import struct
import threading
import time
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Awaitable, Callable, Optional

log = logging.getLogger(__name__)

CHUNK = 64 * 1024
REGISTRY_FILE = "registro_iphone.json"
PHONE_FINGERPRINTS_FILE = "impronte_iphone.json"
PHONE_REGISTRY_FOLDER = "myEasyMP3toIPhone"
PHONE_REGISTRY = PHONE_REGISTRY_FOLDER + "/registro.json"
REGISTRY_VERSION = 1

HOW_SENT = "inviato"            # inviato da questo programma: certo
HOW_FINGERPRINT = "impronta"    # stesso audio: certo
HOW_RULES = "regole"            # durata e tag: molto probabile
HOW_AI = "ai"                   # scelto dall'AI, confermato da te
HOW_MANUAL = "a mano"
HOW_SAVED = "salvato"           # salvato sul PC dall'iPhone: certo

ReadAt = Callable[[int, int], Awaitable[bytes]]


# --------------------------------------------------------------------------- impronte

def _id3_size(head: bytes) -> int:
    size = 0
    if head[:3] == b"ID3" and len(head) >= 10:
        size = 10 + ((head[6] & 0x7F) << 21 | (head[7] & 0x7F) << 14 | (head[8] & 0x7F) << 7 | (head[9] & 0x7F))
        if head[5] & 0x10:
            size += 10        # piè di pagina
    return size


def _digest(prefix: str, data: bytes) -> str:
    result = prefix + hashlib.sha256(data).hexdigest()[:32] if data else ""
    return result


async def _mp3(read_at: ReadAt) -> str:
    start = _id3_size(await read_at(0, 10))
    result = _digest("mp3:", await read_at(start, CHUNK))
    return result


async def _flac(read_at: ReadAt) -> str:
    head = await read_at(0, 42)
    result = ""
    if head[:4] == b"fLaC" and len(head) == 42 and head[4] & 0x7F == 0:
        md5 = head[26:42]
        if any(md5):
            result = "flac:" + md5.hex()
    if not result and head[:4] == b"fLaC":
        offset = 4
        last = False
        steps = 0
        while not last and steps < 64:
            block = await read_at(offset, 4)
            if len(block) < 4:
                last = True
                offset = -1
            else:
                last = bool(block[0] & 0x80)
                offset += 4 + int.from_bytes(block[1:4], "big")
            steps += 1
        if offset > 0:
            result = _digest("flacpcm:", await read_at(offset, CHUNK))
    return result


async def _mp4(read_at: ReadAt, size: int) -> str:
    offset = 0
    result = ""
    steps = 0
    while not result and 0 <= offset < size and steps < 256:
        header = await read_at(offset, 16)
        steps += 1
        if len(header) < 8:
            offset = -1
        else:
            atom_size, kind = struct.unpack(">I4s", header[:8])
            header_size = 8
            if atom_size == 1 and len(header) == 16:
                atom_size = struct.unpack(">Q", header[8:16])[0]
                header_size = 16
            elif atom_size == 0:
                atom_size = size - offset
            if kind == b"mdat":
                result = _digest("mp4:", await read_at(offset + header_size, CHUNK))
            elif atom_size < header_size:
                offset = -1
            else:
                offset += atom_size
    return result


async def fingerprint(read_at: ReadAt, size: int, suffix: str) -> str:
    """L'impronta dell'audio ("" se il formato non è noto o il file è rovinato)."""
    suffix = suffix.lower()
    if suffix == ".mp3":
        result = await _mp3(read_at)
    elif suffix == ".flac":
        result = await _flac(read_at)
    elif suffix in (".m4a", ".m4b", ".mp4"):
        result = await _mp4(read_at, size)
    else:
        result = ""
    return result


async def file_fingerprint(path) -> str:
    """L'impronta di un file del PC (letto soltanto); "" se non si legge. Da usare dentro codice asincrono."""
    result = ""
    try:
        with open(path, "rb") as handle:
            async def read_at(offset: int, count: int) -> bytes:
                handle.seek(offset)
                data = handle.read(count)
                return data

            result = await fingerprint(read_at, os.fstat(handle.fileno()).st_size, Path(path).suffix)
    except OSError as exc:
        log.warning("Impronta non calcolata per %s: %s", path, exc)
    return result


def file_fingerprints(paths: list, progress=None, cancel: Optional[threading.Event] = None) -> dict:
    """{percorso: impronta} per file del PC (letti soltanto). Bloccante: non da dentro codice asincrono."""
    result = {}

    async def work():
        index = 0
        while index < len(paths) and not (cancel is not None and cancel.is_set()):
            path = paths[index]
            result[path] = await file_fingerprint(path)
            index += 1
            if progress is not None and index % 200 == 0:
                progress(index, len(paths), f"impronte dei file del PC: {index} di {len(paths)}")

    asyncio.run(work())
    return result


async def phone_fingerprint(afc, remote_path: str, size: int, suffix: str) -> str:
    """L'impronta di un file dell'iPhone, letto a pezzi (AFC)."""
    handle = await afc.fopen(remote_path.lstrip("/"), "r")
    try:
        async def read_at(offset: int, count: int) -> bytes:
            await afc.fseek(handle, offset)
            data = await afc.fread(handle, count)
            return data

        result = await fingerprint(read_at, size, suffix)
    finally:
        await afc.fclose(handle)
    return result


class PhoneFingerprints:
    """Le impronte dei file dell'iPhone già lette (cartella dati): un file dell'iPhone non cambia mai al suo posto
    (un brano rimpiazzato ha un file nuovo), quindi percorso e dimensione bastano a riconoscerlo."""

    def __init__(self, home: Path) -> None:
        self.home = home
        self.entries = {}
        try:
            data = json.loads((home / PHONE_FINGERPRINTS_FILE).read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self.entries = data
        except (OSError, ValueError):
            self.entries = {}

    def get(self, remote_path: str, size: int) -> str:
        entry = self.entries.get(remote_path)
        result = entry[1] if isinstance(entry, list) and len(entry) == 2 and entry[0] == size else ""
        return result

    def put(self, remote_path: str, size: int, value: str) -> None:
        self.entries[remote_path] = [size, value]

    def keep_only(self, remote_paths: set) -> None:
        for path in list(self.entries):
            if path not in remote_paths:
                del self.entries[path]

    def save(self) -> None:
        _write_json(self.home / PHONE_FINGERPRINTS_FILE, self.entries)


# --------------------------------------------------------------------------- registro

@dataclass
class Link:
    sync_id: int
    pc: str                 # il nome del computer
    path: str               # il file su quel computer
    size: int = 0
    mtime: float = 0.0
    signature: str = ""     # le modifiche in sospeso al momento del collegamento (overlay.signature)
    fingerprint: str = ""
    how: str = HOW_SENT
    date: str = ""

    @property
    def here(self) -> bool:
        result = self.pc.lower() == computer_name().lower()
        return result


LINK_FIELDS = {field.name for field in fields(Link)}


def computer_name() -> str:
    result = socket.gethostname()
    return result


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)


class Registry:
    def __init__(self) -> None:
        self.links = {}

    # ---------------------------------------------------------------- formato

    def to_bytes(self) -> bytes:
        rows = []
        for link in self.links.values():
            row = asdict(link)
            row["sync_id"] = f"{link.sync_id:016x}"
            rows.append(row)
        result = json.dumps({"version": REGISTRY_VERSION, "links": rows}, ensure_ascii=False).encode("utf-8")
        return result

    @classmethod
    def from_bytes(cls, data: bytes) -> "Registry":
        registry = cls()
        try:
            document = json.loads(data.decode("utf-8"))
            rows = document.get("links", []) if document.get("version") == REGISTRY_VERSION else []
            for row in rows:
                known = {}
                for name, value in row.items():
                    if name in LINK_FIELDS:
                        known[name] = value
                known["sync_id"] = int(str(known["sync_id"]), 16)
                link = Link(**known)
                if link.sync_id:
                    registry.links[link.sync_id] = link
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            log.warning("Registro della provenienza non leggibile, ignorato: %s", exc)
            registry.links = {}
        return registry

    @classmethod
    def load(cls, home: Path) -> "Registry":
        try:
            result = cls.from_bytes((home / REGISTRY_FILE).read_bytes())
        except OSError:
            result = cls()
        return result

    def save(self, home: Path) -> None:
        path = home / REGISTRY_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_bytes(self.to_bytes())
        os.replace(temporary, path)

    # ---------------------------------------------------------------- contenuto

    def record(self, link: Link) -> None:
        if not link.date:
            link.date = time.strftime("%Y-%m-%d %H:%M:%S")
        self.links[link.sync_id] = link

    def forget(self, sync_id: int) -> None:
        self.links.pop(sync_id, None)

    def get(self, sync_id: int) -> Optional[Link]:
        result = self.links.get(sync_id)
        return result

    def merge(self, other: "Registry") -> bool:
        """Unisce le righe di un'altra copia (quella dell'iPhone): per lo stesso brano vince la più recente.
        True se qualcosa è cambiato."""
        changed = False
        for sync_id, link in other.links.items():
            mine = self.links.get(sync_id)
            if mine is None or link.date > mine.date:
                self.links[sync_id] = link
                changed = True
        return changed

    def keep_only(self, sync_ids: set) -> bool:
        """Toglie le righe dei brani che non sono più sull'iPhone. True se ne ha tolte."""
        removed = False
        for sync_id in list(self.links):
            if sync_id not in sync_ids:
                del self.links[sync_id]
                removed = True
        return removed

    def __len__(self) -> int:
        result = len(self.links)
        return result


async def read_phone_registry(afc) -> Registry:
    if await afc.exists(PHONE_REGISTRY):
        result = Registry.from_bytes(await afc.get_file_contents(PHONE_REGISTRY))
    else:
        result = Registry()
    return result


async def write_phone_registry(afc, registry: Registry) -> None:
    """Sull'iPhone, in una cartella del programma che l'iPhone non legge: prima un file temporaneo, poi il nome."""
    if not await afc.exists(PHONE_REGISTRY_FOLDER):
        await afc.makedirs(PHONE_REGISTRY_FOLDER)
    temporary = PHONE_REGISTRY + ".tmp"
    data = registry.to_bytes()
    await afc.set_file_contents(temporary, data)
    if await afc.exists(PHONE_REGISTRY):
        await afc.rm(PHONE_REGISTRY)
    await afc.rename(temporary, PHONE_REGISTRY)


async def synchronize(afc, home: Path, phone_sync_ids: set) -> Registry:
    """Al collegamento: unisce il registro locale e quello dell'iPhone, toglie i brani che non ci sono più, salva
    entrambi se qualcosa è cambiato."""
    local = Registry.load(home)
    phone = await read_phone_registry(afc)
    merged = Registry()
    merged.merge(local)
    merged.merge(phone)
    merged.keep_only(phone_sync_ids)
    if merged.to_bytes() != local.to_bytes():
        merged.save(home)
    if merged.to_bytes() != phone.to_bytes():
        await write_phone_registry(afc, merged)
    return merged
