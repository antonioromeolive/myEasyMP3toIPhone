# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le suonerie dell'iPhone: leggerle, inviarne ed eliminarne (sessioni phone_sync.run_ringtone_session, solo da
Applica) e copiarle sul PC.

Sull'iPhone ce ne sono di tre specie:
  * messe da un computer: i file in /iTunes_Control/Ringtones, elencati nel catalogo dell'host
    /iTunes_Control/iTunes/Ringtones.plist (come lo scrive l'host di Apple: Name, GUID, Total Time, PID; l'iPhone non
    lo legge, è la memoria del computer). Solo queste si tolgono dal computer;
  * fatte sull'iPhone (GarageBand, l'app File): in /Purchases, elencate in /Purchases/Ringtones.plist. Si leggono e
    si copiano sul PC, non si tolgono;
  * resti: file in /iTunes_Control/Ringtones che nessun catalogo elenca (di un altro programma, o di una
    sincronizzazione vecchia): non sono tra le suonerie dell'iPhone. Si possono copiare sul PC.

Tutte le funzioni pubbliche sono bloccanti: vanno chiamate da un thread di lavoro."""

from __future__ import annotations

import io
import logging
import plistlib
import posixpath
import random
import secrets
import socket
import string
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from pymobiledevice3.exceptions import PyMobileDevice3Exception

from . import iphone, phone_sync
from .phone_actions import ActionReport
from .phone_sync import PhoneSyncError
from .ringtones import RINGTONE_SUFFIX, unique_target

log = logging.getLogger(__name__)

CATALOG_PATH = "iTunes_Control/iTunes/Ringtones.plist"
PURCHASES_FOLDER = "Purchases"
PURCHASES_CATALOG_PATH = PURCHASES_FOLDER + "/Ringtones.plist"
ORIGIN_COMPUTER = "computer"     # messa da un computer: si toglie con Elimina dall'iPhone
ORIGIN_PHONE = "iphone"          # fatta sull'iPhone: solo lettura
ORIGIN_LEFTOVER = "resto"        # un file che nessun catalogo elenca: non è tra le suonerie dell'iPhone
BATCH = 50                       # suonerie per sessione
READ_LIMIT = 4 * 1024 * 1024     # i file più grandi non si scaricano solo per leggerne titolo e durata

ProgressFn = Callable[[int, int, str], None]


@dataclass
class PhoneRingtone:
    name: str
    path: str               # "/iTunes_Control/Ringtones/ABCD.m4r" o "/Purchases/import_….m4r"
    origin: str
    pid: int = 0
    guid: str = ""
    duration_ms: int = 0
    size: int = 0

    @property
    def file_name(self) -> str:
        result = posixpath.basename(self.path)
        return result

    @property
    def removable(self) -> bool:
        """Si toglie dall'iPhone: messa da un computer, con il suo identificativo."""
        result = self.origin == ORIGIN_COMPUTER and self.pid != 0
        return result


def _plist(data: bytes) -> dict:
    try:
        document = plistlib.loads(data)
    except Exception:  # noqa: BLE001 - plistlib solleva tipi diversi per un file rovinato
        document = {}
    result = document.get("Ringtones") if isinstance(document, dict) else None
    if not isinstance(result, dict):
        result = {}
    return result


def _int(value) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        result = 0
    return result


def parse_catalog(data: bytes) -> dict:
    """Il catalogo delle suonerie messe da un computer: {nome del file: (nome, PID, GUID, durata in ms)}."""
    result = {}
    for file_name, entry in _plist(data).items():
        if isinstance(entry, dict):
            result[str(file_name)] = (str(entry.get("Name") or Path(str(file_name)).stem), _int(entry.get("PID")),
                                      str(entry.get("GUID") or ""), _int(entry.get("Total Time")))
    return result


def catalog_bytes(entries: dict) -> bytes:
    """Il catalogo dell'host (XML, come lo scrive l'host di Apple) da {nome del file: (nome, PID, GUID, ms)}."""
    ringtones = {}
    for file_name, (name, pid, guid, duration) in sorted(entries.items()):
        ringtones[file_name] = {"Name": name, "GUID": guid, "Total Time": int(duration), "PID": int(pid),
                                "Protected Content": False}
    result = plistlib.dumps({"Ringtones": ringtones}, fmt=plistlib.FMT_XML)
    return result


def _audio_facts(data: bytes) -> tuple:
    """(titolo, durata in ms) di un .m4r scaricato; ("", 0) se non si legge."""
    from mutagen.mp4 import MP4
    try:
        audio = MP4(io.BytesIO(data))
        titles = audio.tags.get("\xa9nam") if audio.tags else None
        title = str(titles[0]).strip() if titles else ""
        result = (title, int(round(audio.info.length * 1000)))
    except Exception:  # noqa: BLE001 - mutagen solleva tipi diversi per un file rovinato
        result = ("", 0)
    return result


async def _files(afc, folder: str) -> dict:
    """{nome del file: dimensione} dei .m4r di una cartella dell'iPhone ({} se non c'è)."""
    result = {}
    if await afc.exists(folder):
        for name in await afc.listdir(folder):
            if name.lower().endswith(RINGTONE_SUFFIX):
                info = await afc.stat(f"{folder}/{name}")
                result[name] = _int(info.get("st_size"))
    return result


async def _duration(afc, path: str, size: int, known: int) -> tuple:
    """(titolo, durata) dal file, se la durata non è già nota (o il titolo serve) e il file è piccolo."""
    result = ("", known)
    if size and size <= READ_LIMIT:
        title, duration = _audio_facts(await afc.get_file_contents(path.lstrip("/")))
        result = (title, known or duration)
    return result


async def list_on_phone(afc) -> list:
    """Tutte le suonerie dell'iPhone (PhoneRingtone), per specie e nome."""
    result = []
    catalog = {}
    if await afc.exists(CATALOG_PATH):
        catalog = parse_catalog(await afc.get_file_contents(CATALOG_PATH))
    folder = phone_sync.RINGTONE_FOLDER
    for file_name, size in sorted((await _files(afc, folder)).items()):
        path = f"/{folder}/{file_name}"
        entry = catalog.get(file_name)
        if entry is not None:
            name, pid, guid, duration = entry
            if not duration:
                duration = (await _duration(afc, path, size, 0))[1]
            result.append(PhoneRingtone(name, path, ORIGIN_COMPUTER, pid, guid, duration, size))
        else:
            title, duration = await _duration(afc, path, size, 0)
            result.append(PhoneRingtone(title or Path(file_name).stem, path, ORIGIN_LEFTOVER, 0, "", duration, size))
    purchases = {}
    if await afc.exists(PURCHASES_CATALOG_PATH):
        purchases = _plist(await afc.get_file_contents(PURCHASES_CATALOG_PATH))
    present = await _files(afc, PURCHASES_FOLDER)
    for file_name, entry in sorted(purchases.items()):
        if isinstance(entry, dict) and file_name in present:
            path = f"/{PURCHASES_FOLDER}/{file_name}"
            duration = (await _duration(afc, path, present[file_name], _int(entry.get("Total Time"))))[1]
            result.append(PhoneRingtone(str(entry.get("Name") or Path(file_name).stem), path, ORIGIN_PHONE, 0,
                                        str(entry.get("GUID") or ""), duration, present[file_name]))
    order = {ORIGIN_COMPUTER: 0, ORIGIN_PHONE: 1, ORIGIN_LEFTOVER: 2}
    result.sort(key=lambda item: (order.get(item.origin, 3), item.name.casefold()))
    return result


async def _list() -> list:
    from pymobiledevice3.services.afc import AfcService
    lockdown = await iphone._open_lockdown()
    try:
        async with AfcService(lockdown) as afc:
            result = await list_on_phone(afc)
    finally:
        await lockdown.close()
    return result


def list_ringtones() -> list:
    """Le suonerie dell'iPhone (PhoneRingtone)."""
    result = iphone._run(_list())
    return result


# --------------------------------------------------------------------------- invio ed eliminazione (Applica)

@dataclass
class RingtoneSend:
    """Una suoneria da inviare: la chiave della coda, il file del PC (.m4r AAC), il nome e la durata."""
    key: str
    path: Path
    name: str
    duration_ms: int


@dataclass
class RingtoneDelete:
    key: str
    ringtone: PhoneRingtone


def new_guid() -> str:
    """16 cifre esadecimali: l'ora in secondi e un numero a caso (come l'host)."""
    result = f"{int(time.time()) & 0xFFFFFFFF:08X}{secrets.randbits(32):08X}"
    return result


def _new_file_name(used: set) -> str:
    name = ""
    while not name or name.upper() in used:
        name = "".join(random.choices(string.ascii_uppercase, k=4)) + RINGTONE_SUFFIX
    used.add(name.upper())
    result = name
    return result


def _check_send(item: RingtoneSend) -> str:
    """Perché una suoneria non si può inviare ("" se si può)."""
    from .ringtones import read_ringtone
    facts = read_ringtone(item.path)
    if not item.path.is_file():
        result = "il file non c'è più"
    elif facts.error:
        result = f"il file {facts.error}"
    elif facts.duration_ms > phone_sync.MAX_RINGTONE_MS:
        result = "dura più di 40 secondi: l'iPhone non la accetta"
    else:
        result = ""
    return result


async def _apply_batch(lockdown, identity, sends: list, deletes: list, report: ActionReport) -> None:
    """Una sessione: le suonerie da inviare e da togliere; poi il catalogo dell'host aggiornato."""
    from pymobiledevice3.services.afc import AfcService
    async with AfcService(lockdown) as afc:
        catalog = {}
        if await afc.exists(CATALOG_PATH):
            catalog = parse_catalog(await afc.get_file_contents(CATALOG_PATH))
        used = set()
        for name in (await _files(afc, phone_sync.RINGTONE_FOLDER)):
            used.add(name.upper())
    operations = []
    uploads = []
    added = {}
    for item in deletes:
        operations.append(phone_sync.delete_ringtone(item.ringtone.pid, item.ringtone.path))
    for item in sends:
        pid = secrets.randbits(63) | 1
        file_name = _new_file_name(used)
        guid = new_guid()
        operations.append(phone_sync.insert_ringtone(pid, item.name, item.duration_ms, guid))
        uploads.append(phone_sync.Upload(pid, item.path, f"{phone_sync.RINGTONE_FOLDER}/{file_name}"))
        added[file_name] = (item.name, pid, guid, item.duration_ms, item.key)
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
    session = await phone_sync.run_ringtone_session(lockdown, identity, socket.gethostname(), operations, uploads,
                                                    timestamp)
    report.sessions += 1
    async with AfcService(lockdown) as afc:
        present = await _files(afc, phone_sync.RINGTONE_FOLDER)
        for item in deletes:
            if item.ringtone.file_name not in present:
                report.done += 1
                report.done_keys.append(item.key)
                catalog.pop(item.ringtone.file_name, None)
            else:
                report.errors.append((item.ringtone.name, "l'iPhone non l'ha tolta"))
        for file_name, (name, pid, guid, duration, key) in added.items():
            if file_name in present and str(pid) in session.uploaded:
                report.done += 1
                report.done_keys.append(key)
                catalog[file_name] = (name, pid, guid, duration)
            else:
                report.errors.append((name, "l'iPhone non l'ha ricevuta"))
        kept = {}
        for file_name, entry in catalog.items():
            if file_name in present:
                kept[file_name] = entry
        await afc.set_file_contents(CATALOG_PATH, catalog_bytes(kept))


async def _apply(sends: list, deletes: list, progress: Optional[ProgressFn], cancel) -> ActionReport:
    from pymobiledevice3.services.afc import AfcService
    report = ActionReport()
    ready = []
    for item in sends:
        reason = _check_send(item)
        if reason:
            report.errors.append((item.name, reason))
        else:
            ready.append(item)
    removable = []
    for item in deletes:
        if item.ringtone.removable:
            removable.append(item)
        else:
            report.errors.append((item.ringtone.name, "fatta sull'iPhone: un computer non la può togliere"))
    lockdown = await iphone._open_lockdown()
    try:
        async with AfcService(lockdown) as afc:
            identity = phone_sync.parse_prefs(await afc.get_file_contents(phone_sync.PREFS_PATH))
        index = 0
        total = len(ready) + len(removable)
        while (index < len(ready) or index < len(removable)) and not (cancel is not None and cancel.is_set()):
            batch_sends = ready[index:index + BATCH]
            batch_deletes = removable[index:index + BATCH]
            if progress is not None:
                progress(index, total, "suonerie")
            try:
                await _apply_batch(lockdown, identity, batch_sends, batch_deletes, report)
            except PhoneSyncError as exc:
                for item in batch_sends:
                    report.errors.append((item.name, str(exc)))
                for item in batch_deletes:
                    report.errors.append((item.ringtone.name, str(exc)))
            index += BATCH
    finally:
        await lockdown.close()
    report.cancelled = cancel is not None and cancel.is_set()
    return report


def apply_ringtones(sends: list, deletes: list, progress: Optional[ProgressFn] = None,
                    cancel: Optional[threading.Event] = None) -> ActionReport:
    """Invia (RingtoneSend) e toglie (RingtoneDelete) le suonerie; report.done_keys: le chiavi delle azioni fatte."""
    result = iphone._run(_apply(sends, deletes, progress, cancel))
    return result


# --------------------------------------------------------------------------- copia sul PC

async def _download(items: list, folder: Path, progress: Optional[ProgressFn], cancel) -> tuple:
    from pymobiledevice3.services.afc import AfcService
    saved = []
    errors = []
    lockdown = await iphone._open_lockdown()
    try:
        async with AfcService(lockdown) as afc:
            index = 0
            while index < len(items) and not (cancel is not None and cancel.is_set()):
                item = items[index]
                if progress is not None:
                    progress(index, len(items), item.name)
                try:
                    data = await afc.get_file_contents(item.path.lstrip("/"))
                    folder.mkdir(parents=True, exist_ok=True)
                    target = unique_target(folder, item.name)
                    with open(target, "xb") as handle:       # "x": mai sopra un file che c'è
                        handle.write(data)
                    saved.append(target)
                except (OSError, PyMobileDevice3Exception) as exc:
                    errors.append((item.name, str(exc)))
                index += 1
    finally:
        await lockdown.close()
    result = (saved, errors)
    return result


def download_ringtones(items: list, folder: Path, progress: Optional[ProgressFn] = None,
                       cancel: Optional[threading.Event] = None) -> tuple:
    """Copia da iPhone a PC: ogni suoneria come file nuovo nella cartella (il suo nome, " (2)" se c'è già).
    Restituisce ([file salvati], [(nome, motivo)])."""
    result = iphone._run(_download(items, folder, progress, cancel))
    return result
