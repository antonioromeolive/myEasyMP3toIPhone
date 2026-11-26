# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le azioni sull'iPhone in attesa: tutto ciò che scrive sull'iPhone non parte subito, va qui; *Applica* le mostra in
una finestra (ognuna si può togliere) e le fa tutte insieme quando l'iPhone è connesso.

Due specie di voci, salvate nella cartella dati (iphone_in_attesa.json):

- per un **file del PC** (chiave "file:" + overlay.path_key): Copia da PC a iPhone (SEND), la spunta tolta (REMOVE),
  Usa i tag da PC a iPhone (UPDATE), Ricopia da PC a iPhone (REPLACE). Valgono per i brani delle cartelle aperte:
  il brano dell'iPhone si ritrova con il registro della provenienza al momento di Applica. Le spunte della colonna
  iPhone (scheda PC) scrivono queste: una spunta tolta toglie dall'iPhone solo un brano collegato dal registro;
- per un **brano dell'iPhone** (chiave "pid:" + il suo identificativo): Elimina dall'iPhone (DELETE), Cambia i tag
  (EDIT, con i valori), Ricopia e Usa i tag scelti nella scheda iPhone (REPLACE, UPDATE, con il file del PC in
  "path"). Valgono anche per un file del PC fuori dalle cartelle aperte.

- per le **suonerie**: Invia come suoneria da PC a iPhone (RING_SEND, chiave "suoneria:" + overlay.path_key del .m4r,
  con il file in "path") ed Elimina la suoneria dall'iPhone (RING_DELETE, chiave "suoneria_iphone:" + il nome del file
  sull'iPhone, con "path", "pid" e "name"). Una versione precedente del programma le salta (e salvando le perde).

Un brano ha al massimo un'azione (Cambia i tag a parte): una nuova voce per lo stesso file toglie quella vecchia.
Dopo ogni lettura dell'iPhone quelle già fatte, o non più possibili, si tolgono da sole (reconcile,
reconcile_phone). La versione 1 del file (solo voci per file) si legge ancora."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from .config import read_json, write_json
from .overlay import path_key
from .phone_library import DEVICE_ABSENT, DEVICE_STALE

PENDING_FILE = "iphone_in_attesa.json"
PENDING_VERSION = 2
OLD_VERSION = 1
SEND = "invia"
REMOVE = "togli"
UPDATE = "aggiorna"
REPLACE = "ricopia"
DELETE = "elimina"
EDIT = "cambia_tag"
RING_SEND = "suoneria_invia"
RING_DELETE = "suoneria_elimina"
FILE_ACTIONS = (SEND, REMOVE, UPDATE, REPLACE)
PHONE_ACTIONS = (DELETE, EDIT, UPDATE, REPLACE)
RING_ACTIONS = (RING_SEND, RING_DELETE)
ACTIONS = (SEND, REMOVE, UPDATE, REPLACE, DELETE, EDIT, RING_SEND, RING_DELETE)
FILE_PREFIX = "file:"
PHONE_PREFIX = "pid:"
RING_PREFIX = "suoneria:"
RING_PHONE_PREFIX = "suoneria_iphone:"
EDIT_FIELDS = ("title", "album", "genre", "year", "track_number", "disc_number", "compilation")
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"     # "at": quando la voce è entrata in coda (come le date del registro)


def _now() -> str:
    result = time.strftime(TIME_FORMAT)
    return result


def wanted(status: str, action: str) -> bool:
    """La spunta: il brano sarà sull'iPhone dopo Applica?"""
    if action == SEND:
        result = True
    elif action in (REMOVE, DELETE):
        result = False
    else:
        result = status != DEVICE_ABSENT
    return result


def toggled(status: str, linked: bool, action: str, checked: bool) -> str:
    """L'azione in attesa dopo aver messo (checked) o tolto la spunta. linked: il brano dell'iPhone viene da questo
    file (registro), l'unico caso in cui togliere la spunta lo toglie dall'iPhone."""
    present = status != DEVICE_ABSENT
    if checked and present:
        result = action if action in (UPDATE, REPLACE) else ""   # annulla un "togli"; Usa i tag e Ricopia restano
    elif checked:
        result = SEND
    elif not present:
        result = ""                                        # annulla un "invia"
    elif linked:
        result = REMOVE
    else:
        result = action                                    # abbinato solo per i tag: non si toglie
    return result


def still_needed(status: str, action: str) -> bool:
    """Un'azione in attesa per un file del PC che non è ancora fatta (dopo una lettura dell'iPhone)."""
    if action == SEND:
        result = status == DEVICE_ABSENT
    elif action in (REMOVE, DELETE, REPLACE):
        result = status != DEVICE_ABSENT
    elif action == UPDATE:
        result = status == DEVICE_STALE
    else:
        result = False
    return result


def _same_value(name: str, current, value) -> bool:
    """Un valore di Cambia i tag è già quello del brano dell'iPhone (anno e numeri come numeri, 0 = vuoto)."""
    if name == "compilation":
        result = bool(current) == bool(value)
    elif name in ("year", "track_number", "disc_number"):
        digits = str(current or "").strip()[:4]
        result = (int(digits) if digits.isdigit() else 0) == int(value or 0)
    else:
        result = str(current or "").strip() == str(value or "").strip()
    return result


def edit_needed(phone_track, values: dict) -> bool:
    """Cambia i tag: almeno un valore è ancora diverso da quello del brano dell'iPhone."""
    result = False
    for name, value in values.items():
        if not _same_value(name, getattr(phone_track.tags, name, None), value):
            result = True
    return result


@dataclass
class Job:
    """Un'azione in attesa pronta per Applica: la chiave (per toglierla), l'azione, il brano del PC e/o
    dell'iPhone, i valori di Cambia i tag."""
    key: str
    action: str
    track: object = None
    phone: object = None
    values: dict = field(default_factory=dict)


def file_key(path) -> str:
    result = FILE_PREFIX + path_key(path)
    return result


def phone_key(pid) -> str:
    result = PHONE_PREFIX + str(pid)
    return result


def key_pid(key: str):
    """Il pid di una chiave "pid:…" (None per le altre)."""
    result = None
    if key.startswith(PHONE_PREFIX):
        text = key[len(PHONE_PREFIX):]
        result = int(text) if text.lstrip("-").isdigit() else None
    return result


class Pending:
    """{chiave: {"action": …, "path": il file del PC (voci "pid:"), "values": {…}}} salvato nella cartella dati."""

    def __init__(self, home: Path) -> None:
        self.home = home
        self.items = {}
        self._version = 0             # cresce a ogni cambio delle voci (la cache di _phone_paths)
        self._paths_cache = None
        data = read_json(home / PENDING_FILE)
        if isinstance(data, dict) and isinstance(data.get("items"), dict):
            if data.get("version") == OLD_VERSION:
                for key, action in data["items"].items():
                    if action in (SEND, REMOVE, UPDATE):
                        self.items[FILE_PREFIX + str(key)] = {"action": action}
            elif data.get("version") == PENDING_VERSION:
                for key, entry in data["items"].items():
                    self._load_entry(str(key), entry)

    def _load_entry(self, key: str, entry) -> None:
        if isinstance(entry, dict):
            action = entry.get("action")
            good_file = key.startswith(FILE_PREFIX) and action in FILE_ACTIONS
            good_phone = key_pid(key) is not None and action in PHONE_ACTIONS
            good_ring = ((key.startswith(RING_PREFIX) and action == RING_SEND) or
                         (key.startswith(RING_PHONE_PREFIX) and action == RING_DELETE))
            if good_ring:
                self._load_ring_entry(key, entry)
            elif good_file or good_phone:
                kept = {"action": action}
                if isinstance(entry.get("path"), str) and entry["path"]:
                    kept["path"] = entry["path"]
                if isinstance(entry.get("at"), str):
                    kept["at"] = entry["at"]
                if action == EDIT and isinstance(entry.get("values"), dict):
                    values = {}
                    for name, value in entry["values"].items():
                        if name in EDIT_FIELDS:
                            values[name] = value
                    kept["values"] = values
                if action != EDIT or kept.get("values"):
                    self.items[key] = kept

    def _load_ring_entry(self, key: str, entry: dict) -> None:
        """Una voce delle suonerie: serve il percorso (e per l'eliminazione il pid dell'iPhone)."""
        path = entry.get("path")
        pid = entry.get("pid")
        if isinstance(path, str) and path and (entry["action"] == RING_SEND or isinstance(pid, int)):
            kept = {"action": entry["action"], "path": path}
            if entry["action"] == RING_DELETE:
                kept["pid"] = pid
                kept["name"] = str(entry.get("name") or "")
            if isinstance(entry.get("at"), str):
                kept["at"] = entry["at"]
            self.items[key] = kept

    # ------------------------------------------------------------------ per file del PC

    def get(self, path) -> str:
        """L'azione in attesa per un file del PC: la sua voce, o quella di un brano dell'iPhone che viene da lui."""
        key = path_key(path)
        entry = self.items.get(FILE_PREFIX + key)
        if entry is not None:
            result = entry["action"]
        else:
            result = self._phone_paths().get(key, "")
        return result

    def _phone_paths(self) -> dict:
        """{path_key del file del PC: azione} delle voci per brano dell'iPhone (Cambia i tag no)."""
        result = self._phone_index()[0]
        return result

    def _phone_index(self) -> tuple:
        """({path_key: azione}, {path_key: [chiavi delle voci]}) delle voci per brano dell'iPhone con un file del PC
        (Cambia i tag no), rifatto solo quando cambiano le voci dell'iPhone: get() si chiama per ogni brano mostrato e
        set() per ogni brano messo in coda (una Copia di migliaia di brani)."""
        if self._paths_cache is None or self._paths_cache[0] != self._version:
            paths = {}
            keys = {}
            for item_key, item in self.items.items():
                if item["action"] != EDIT and item_key.startswith(PHONE_PREFIX) and item.get("path"):
                    file_key = path_key(item["path"])
                    paths[file_key] = item["action"]
                    keys.setdefault(file_key, []).append(item_key)
            self._paths_cache = (self._version, (paths, keys))
        result = self._paths_cache[1]
        return result

    def set(self, path, action: str) -> None:
        """La voce di un file del PC ("" la toglie); toglie le altre azioni sullo stesso file (Cambia i tag a parte).
        Le voci dei file non entrano nell'indice dell'iPhone: _version cresce solo se se ne toglie una dell'iPhone."""
        key = path_key(path)
        self._drop_path(key)
        if action:
            self.items[FILE_PREFIX + key] = {"action": action, "at": _now()}

    def _drop_path(self, key: str) -> None:
        self.items.pop(FILE_PREFIX + key, None)
        phone_keys = list(self._phone_index()[1].get(key, []))
        for item_key in phone_keys:
            if self.items.pop(item_key, None) is not None:
                self._version += 1

    # ------------------------------------------------------------------ per brano dell'iPhone

    def get_phone(self, pid, include_edit: bool = False) -> str:
        entry = self.items.get(phone_key(pid))
        result = ""
        if entry is not None and (include_edit or entry["action"] != EDIT):
            result = entry["action"]
        return result

    def set_phone(self, pid, action: str, path=None, values: dict = None) -> None:
        """La voce di un brano dell'iPhone; path: il suo file del PC (Ricopia, Usa i tag), le cui altre voci si
        tolgono. Cambia i tag (EDIT) unisce i valori nuovi a quelli già in attesa."""
        key = phone_key(pid)
        if path and action != EDIT:
            self._drop_path(path_key(path))   # con l'indice prima che cambi (_version qui sotto)
        self._version += 1
        if action == EDIT:
            entry = self.items.get(key)
            merged = dict(entry.get("values", {})) if entry is not None and entry["action"] == EDIT else {}
            merged.update(values or {})
            self.items[key] = {"action": EDIT, "values": merged, "at": _now()}
        else:
            self.items.pop(key, None)
            entry = {"action": action, "at": _now()}
            if path:
                entry["path"] = str(path)
            self.items[key] = entry

    # ------------------------------------------------------------------ suonerie

    def ringtone_action(self, path) -> str:
        """L'azione in attesa per un .m4r del PC ("" se non c'è)."""
        entry = self.items.get(RING_PREFIX + path_key(path))
        result = entry["action"] if entry is not None else ""
        return result

    def set_ringtone(self, path, action: str) -> None:
        """Invia come suoneria (RING_SEND) un .m4r del PC; "" toglie la voce."""
        key = RING_PREFIX + path_key(path)
        self.items.pop(key, None)
        if action:
            self.items[key] = {"action": action, "path": str(path), "at": _now()}

    def phone_ringtone_action(self, file_name: str) -> str:
        entry = self.items.get(RING_PHONE_PREFIX + file_name.lower())
        result = entry["action"] if entry is not None else ""
        return result

    def set_phone_ringtone(self, ringtone, action: str) -> None:
        """Elimina dall'iPhone (RING_DELETE) una suoneria messa da un computer (phone_ringtones.PhoneRingtone); ""
        toglie la voce."""
        key = RING_PHONE_PREFIX + ringtone.file_name.lower()
        self.items.pop(key, None)
        if action:
            self.items[key] = {"action": action, "path": ringtone.path, "pid": int(ringtone.pid),
                               "name": ringtone.name, "at": _now()}

    def reconcile_ringtones(self, on_phone, phone_ringtones=None) -> int:
        """Toglie le azioni sulle suonerie già fatte o non più possibili: un .m4r da inviare che non c'è più o che
        sull'iPhone c'è già (on_phone(path) -> bool); con l'elenco dell'iPhone (phone_ringtones), una suoneria da
        togliere che lì non c'è più. Restituisce quante ne ha tolte."""
        present = None
        if phone_ringtones is not None:
            present = set()
            for ringtone in phone_ringtones:
                present.add(ringtone.file_name.lower())
        removed = 0
        for key in list(self.items):
            entry = self.items[key]
            drop = False
            if key.startswith(RING_PREFIX):
                drop = not Path(entry["path"]).is_file() or on_phone(Path(entry["path"]))
            elif key.startswith(RING_PHONE_PREFIX) and present is not None:
                drop = key[len(RING_PHONE_PREFIX):] not in present
            if drop:
                del self.items[key]
                removed += 1
        return removed

    # ------------------------------------------------------------------ insieme

    def remove(self, keys) -> int:
        removed = 0
        self._version += 1
        for key in keys:
            if self.items.pop(key, None) is not None:
                removed += 1
        return removed

    def entries(self) -> list:
        result = list(self.items.items())
        return result

    def counts(self) -> dict:
        result = {}
        for action in ACTIONS:
            result[action] = 0
        for entry in self.items.values():
            result[entry["action"]] += 1
        return result

    def total(self) -> int:
        result = len(self.items)
        return result

    def clear(self) -> None:
        self.items = {}
        self._version += 1

    def reconcile(self, tracks: list, status_of) -> int:
        """Toglie le azioni già fatte o non più possibili per i file del PC tra i brani (status_of(track) -> stato); i
        file che non sono tra i brani (un'altra cartella aperta) restano. Restituisce quante ne ha tolte."""
        removed = 0
        self._version += 1
        for track in tracks:
            key = FILE_PREFIX + path_key(track.path)
            entry = self.items.get(key)
            if entry is not None and not still_needed(status_of(track), entry["action"]):
                del self.items[key]
                removed += 1
        return removed

    def reconcile_phone(self, phone_tracks: list, update_needed) -> int:
        """Dopo una lettura dell'iPhone: toglie le voci dei brani che non ci sono più (eliminati, ricopiati: il brano
        nuovo ha un altro identificativo), quelle di Cambia i tag già fatte e quelle di Usa i tag senza più differenze
        (update_needed(PhoneTrack, path) -> bool). Restituisce quante ne ha tolte."""
        by_pid = {}
        for item in phone_tracks:
            by_pid[item.pid] = item
        removed = 0
        self._version += 1
        for key in list(self.items):
            pid = key_pid(key)
            if pid is not None:
                entry = self.items[key]
                phone_track = by_pid.get(pid)
                if phone_track is None:
                    keep = False
                elif entry["action"] == EDIT:
                    keep = edit_needed(phone_track, entry.get("values", {}))
                elif entry["action"] == UPDATE:
                    keep = update_needed(phone_track, entry.get("path", ""))
                else:
                    keep = True
                if not keep:
                    del self.items[key]
                    removed += 1
        return removed

    def reconcile_sent(self, sent_since) -> int:
        """Toglie le Ricopia già fatte: sent_since(chiave del file, ora) dice se quel file è stato mandato
        all'iPhone da quell'ora in poi (registro della provenienza). Una voce senza ora (versioni precedenti) vale da
        sempre. Restituisce quante ne ha tolte."""
        removed = 0
        self._version += 1
        for key in list(self.items):
            entry = self.items[key]
            if entry["action"] == REPLACE:
                if key.startswith(FILE_PREFIX):
                    target = key[len(FILE_PREFIX):]
                else:
                    target = path_key(entry["path"]) if entry.get("path") else ""
                if target and sent_since(target, entry.get("at", "")):
                    del self.items[key]
                    removed += 1
        return removed

    def save(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        write_json(self.home / PENDING_FILE, {"version": PENDING_VERSION, "items": self.items})
