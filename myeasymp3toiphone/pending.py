# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le modifiche all'iPhone in attesa (il "passo 5"): nella colonna iPhone della scheda PC una spunta vuol dire
"voglio questo brano sull'iPhone". Mettere o togliere una spunta non fa niente subito: segna il brano da inviare, da
togliere o da aggiornare; *Applica* fa tutto insieme quando l'iPhone è connesso.

Le modifiche si ricordano nella cartella dati (iphone_in_attesa.json), per percorso del file del PC. Togliere una
spunta vale solo per i brani che sull'iPhone vengono da quel file (registro della provenienza): un brano abbinato
solo per i tag non si toglie mai con una spunta. Dopo ogni lettura dell'iPhone quelle già fatte si tolgono da sole
(reconcile)."""

from __future__ import annotations

from pathlib import Path

from .config import read_json, write_json
from .overlay import path_key
from .phone_library import DEVICE_ABSENT, DEVICE_STALE

PENDING_FILE = "iphone_in_attesa.json"
PENDING_VERSION = 1
SEND = "invia"
REMOVE = "togli"
UPDATE = "aggiorna"
ACTIONS = (SEND, REMOVE, UPDATE)


def wanted(status: str, action: str) -> bool:
    """La spunta: il brano sarà sull'iPhone dopo Applica?"""
    if action == SEND:
        result = True
    elif action == REMOVE:
        result = False
    else:
        result = status != DEVICE_ABSENT
    return result


def toggled(status: str, linked: bool, action: str, checked: bool) -> str:
    """L'azione in attesa dopo aver messo (checked) o tolto la spunta. linked: il brano dell'iPhone viene da questo
    file (registro), l'unico caso in cui togliere la spunta lo toglie dall'iPhone."""
    present = status != DEVICE_ABSENT
    if checked and present:
        result = UPDATE if action == UPDATE else ""        # annulla un "togli"
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
    """Un'azione in attesa che non è ancora fatta (dopo una lettura dell'iPhone)."""
    if action == SEND:
        result = status == DEVICE_ABSENT
    elif action == REMOVE:
        result = status != DEVICE_ABSENT
    elif action == UPDATE:
        result = status == DEVICE_STALE
    else:
        result = False
    return result


class Pending:
    """{chiave del file del PC (overlay.path_key): azione} salvato nella cartella dati."""

    def __init__(self, home: Path) -> None:
        self.home = home
        self.items = {}
        data = read_json(home / PENDING_FILE)
        if isinstance(data, dict) and data.get("version") == PENDING_VERSION and isinstance(data.get("items"), dict):
            for key, action in data["items"].items():
                if action in ACTIONS:
                    self.items[str(key)] = action

    def get(self, path) -> str:
        result = self.items.get(path_key(path), "")
        return result

    def set(self, path, action: str) -> None:
        key = path_key(path)
        if action:
            self.items[key] = action
        else:
            self.items.pop(key, None)

    def counts(self) -> dict:
        result = {SEND: 0, REMOVE: 0, UPDATE: 0}
        for action in self.items.values():
            result[action] += 1
        return result

    def clear(self) -> None:
        self.items = {}

    def reconcile(self, tracks: list, status_of) -> int:
        """Toglie le azioni già fatte o non più possibili per i brani (status_of(track) -> stato); i file che non
        sono tra i brani (un'altra cartella aperta) restano. Restituisce quante ne ha tolte."""
        removed = 0
        for track in tracks:
            key = path_key(track.path)
            action = self.items.get(key)
            if action and not still_needed(status_of(track), action):
                del self.items[key]
                removed += 1
        return removed

    def save(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        write_json(self.home / PENDING_FILE, {"version": PENDING_VERSION, "items": self.items})
