# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Gli album che "vanno bene così" (linguetta Controlli): per un album, un tipo di problema, o tutto l'album, che i
controlli non mostrano più, qualunque cosa propongano in futuro (scelta dell'utente: per esempio tenere le differenze
con il catalogo online). L'album si riconosce da artista dell'album e nome dell'album senza maiuscole, accenti,
punteggiatura né "CD 1"; rinominato, non vale più. Nella cartella dati, controlli_va_bene.json: le versioni
precedenti del programma lo ignorano. Si toglie dai risultati (Mostra anche quelli che vanno bene così) o da
Impostazioni → Controlli."""

from __future__ import annotations

import time
from pathlib import Path

from .config import read_json, write_json
from .scan import KIND_LABELS, album_norm, artist_norm

ACCEPTED_FILE = "controlli_va_bene.json"
ACCEPTED_VERSION = 1
WHOLE_ALBUM = "tutto_l_album"
ONLINE_TYPE = "W"              # tutte le differenze con il catalogo online: brani mancanti, tag diversi, non trovato
AI_PREFIX = "AI_"
TIME_FORMAT = "%Y-%m-%d %H:%M"
# il nome di ogni tipo di problema (la regola senza il numero), per i menu e per Impostazioni
TYPE_LABELS = {
    WHOLE_ALBUM: "tutto l'album",
    ONLINE_TYPE: "differenze con il catalogo online",
    "R2": "vecchio tag ID3v1",
    "R3": "tag APE",
    "R5": "file illeggibili",
    "R6": "tag mancanti",
    "R7": "copie \"(2)\"",
    "R8": "brani più volte nell'album",
    "R9": "numeri di traccia mancanti",
    "R10": "album con 1-2 brani",
    "R11": "cartella divisa in più album",
    "R12": "album scritto in modi diversi",
    "R13": "compilation divisa per artista",
    "R14": "artista scritto in modi diversi",
    "R15": "brani duplicati",
    "R16": "forse lo stesso artista",
    "R17": "duetti",            # regola tolta: resta per i "va bene così" già salvati
    "I1": "tag diversi tra PC e iPhone",
    "I2": "brani che mancano sull'iPhone",
    "I4": "brani fantasma sull'iPhone",
}


def problem_type(issue) -> str:
    """Il tipo di un problema per "va bene così": la sua regola (R9, I2…), ONLINE_TYPE per la Verifica online,
    AI_ + il tipo per i problemi trovati dall'AI."""
    rule = issue.rule_id.split(".", 1)[0] if issue.rule_id else ""
    if rule.startswith("W"):
        result = ONLINE_TYPE
    elif rule:
        result = rule
    else:
        result = AI_PREFIX + issue.kind
    return result


def type_label(kind: str) -> str:
    if kind.startswith(AI_PREFIX):
        result = f"AI: {KIND_LABELS.get(kind[len(AI_PREFIX):], kind[len(AI_PREFIX):])}"
    else:
        result = TYPE_LABELS.get(kind, kind)
    return result


def album_id(key: tuple) -> str:
    result = f"{artist_norm(key[0])}|{album_norm(key[1])}"
    return result


class Accepted:
    """{album_id: {"artist": …, "album": …, "types": {tipo: quando}}} salvato in controlli_va_bene.json."""

    def __init__(self, home: Path) -> None:
        self.home = home
        self.items = {}
        data = read_json(home / ACCEPTED_FILE)
        if isinstance(data, dict) and isinstance(data.get("albums"), dict):
            for identifier, entry in data["albums"].items():
                good = (isinstance(entry, dict) and isinstance(entry.get("types"), dict)
                        and isinstance(entry.get("artist"), str) and isinstance(entry.get("album"), str))
                if good and entry["types"]:
                    self.items[str(identifier)] = {"artist": entry["artist"], "album": entry["album"],
                                                   "types": dict(entry["types"])}

    def is_accepted(self, key: tuple, kind: str) -> bool:
        """Quel tipo di problema va bene così per l'album (o tutto l'album)."""
        entry = self.items.get(album_id(key))
        result = entry is not None and (WHOLE_ALBUM in entry["types"] or kind in entry["types"])
        return result

    def skip_online(self, key: tuple) -> bool:
        """La Verifica online non serve: tutto l'album, o le differenze con il catalogo, vanno bene così."""
        result = self.is_accepted(key, ONLINE_TYPE)
        return result

    def skip_ai(self, key: tuple) -> bool:
        entry = self.items.get(album_id(key))
        result = entry is not None and WHOLE_ALBUM in entry["types"]
        return result

    def accept(self, key: tuple, kind: str) -> None:
        identifier = album_id(key)
        entry = self.items.setdefault(identifier, {"artist": key[0], "album": key[1], "types": {}})
        entry["types"][kind] = time.strftime(TIME_FORMAT)

    def remove(self, key: tuple, kind: str) -> None:
        """Toglie "va bene così" per quel tipo (WHOLE_ALBUM: per tutto l'album, non i tipi segnati uno per uno)."""
        identifier = album_id(key)
        entry = self.items.get(identifier)
        if entry is not None:
            entry["types"].pop(kind, None)
            if not entry["types"]:
                del self.items[identifier]

    def rows(self) -> list:
        """[((artista, album), tipo, quando)], per album."""
        result = []
        for identifier in sorted(self.items, key=lambda name: (self.items[name]["artist"].lower(),
                                                               self.items[name]["album"].lower())):
            entry = self.items[identifier]
            for kind, when in sorted(entry["types"].items()):
                result.append(((entry["artist"], entry["album"]), kind, when))
        return result

    def save(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        write_json(self.home / ACCEPTED_FILE, {"version": ACCEPTED_VERSION, "albums": self.items})
