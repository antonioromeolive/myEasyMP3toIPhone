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

Un brano ha al massimo un'azione (Cambia i tag a parte): una nuova voce per lo stesso file toglie quella vecchia.
Dopo ogni lettura dell'iPhone quelle già fatte, o non più possibili, si tolgono da sole (reconcile,
reconcile_phone). La versione 1 del file (solo voci per file) si legge ancora."""

from __future__ import annotations

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
FILE_ACTIONS = (SEND, REMOVE, UPDATE, REPLACE)
PHONE_ACTIONS = (DELETE, EDIT, UPDATE, REPLACE)
ACTIONS = (SEND, REMOVE, UPDATE, REPLACE, DELETE, EDIT)
FILE_PREFIX = "file:"
PHONE_PREFIX = "pid:"
EDIT_FIELDS = ("title", "album", "genre", "year", "track_number", "disc_number", "compilation")


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
            if good_file or good_phone:
                kept = {"action": action}
                if isinstance(entry.get("path"), str) and entry["path"]:
                    kept["path"] = entry["path"]
                if action == EDIT and isinstance(entry.get("values"), dict):
                    values = {}
                    for name, value in entry["values"].items():
                        if name in EDIT_FIELDS:
                            values[name] = value
                    kept["values"] = values
                if action != EDIT or kept.get("values"):
                    self.items[key] = kept

    # ------------------------------------------------------------------ per file del PC

    def get(self, path) -> str:
        """L'azione in attesa per un file del PC: la sua voce, o quella di un brano dell'iPhone che viene da lui."""
        key = path_key(path)
        entry = self.items.get(FILE_PREFIX + key)
        result = entry["action"] if entry is not None else ""
        if not result:
            for item_key, item in self.items.items():
                if not result and item["action"] != EDIT and item_key.startswith(PHONE_PREFIX) and \
                        item.get("path") and path_key(item["path"]) == key:
                    result = item["action"]
        return result

    def set(self, path, action: str) -> None:
        """La voce di un file del PC ("" la toglie); toglie le altre azioni sullo stesso file (Cambia i tag a parte)."""
        key = path_key(path)
        self._drop_path(key)
        if action:
            self.items[FILE_PREFIX + key] = {"action": action}

    def _drop_path(self, key: str) -> None:
        for item_key in list(self.items):
            item = self.items[item_key]
            same_file = item_key == FILE_PREFIX + key or \
                (bool(item.get("path")) and item["action"] != EDIT and path_key(item["path"]) == key)
            if same_file:
                del self.items[item_key]

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
        if action == EDIT:
            entry = self.items.get(key)
            merged = dict(entry.get("values", {})) if entry is not None and entry["action"] == EDIT else {}
            merged.update(values or {})
            self.items[key] = {"action": EDIT, "values": merged}
        else:
            if path:
                self._drop_path(path_key(path))
            self.items.pop(key, None)
            entry = {"action": action}
            if path:
                entry["path"] = str(path)
            self.items[key] = entry

    # ------------------------------------------------------------------ insieme

    def remove(self, keys) -> int:
        removed = 0
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

    def reconcile(self, tracks: list, status_of) -> int:
        """Toglie le azioni già fatte o non più possibili per i file del PC tra i brani (status_of(track) -> stato); i
        file che non sono tra i brani (un'altra cartella aperta) restano. Restituisce quante ne ha tolte."""
        removed = 0
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

    def save(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        write_json(self.home / PENDING_FILE, {"version": PENDING_VERSION, "items": self.items})
