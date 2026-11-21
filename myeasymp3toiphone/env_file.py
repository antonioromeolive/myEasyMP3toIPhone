# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Il file delle variabili della cartella dati: ~/.myEasyMP3toIPhone/myEasyMP3toIPhone.env.

Un solo file con tutte le variabili d'ambiente che il programma legge, letto a ogni avvio comunque il programma sia
avviato (anche da un collegamento, che non esegue nessuno script). Il modello myEasyMP3toIPhone.TEMPLATE.env, distribuito
con il programma, elenca ogni variabile con il valore vuoto.

Significato di una riga:
    NOME=valore     si usa valore, anche quando il sistema ha un altro valore per NOME
    NOME=$ALTRA     il valore di ALTRA: da questo file se qui ne ha uno, altrimenti dal sistema
    NOME=           il valore di NOME nel sistema; nessuno se il sistema non ne ha
    NOME=$NOME      come NOME=, senza avviso
    NOME=$$testo    il testo letterale $testo

Regole: UTF-8 con o senza BOM; spazi intorno al valore e una coppia di virgolette uguali tolti; niente commenti in
fondo alla riga (una chiave può contenere #); $ALTRA vale solo per un valore intero; se un nome compare due volte vale
l'ultimo. Tutti i valori si calcolano sull'ambiente del sistema com'era PRIMA di applicare il file, poi si impostano
insieme: il risultato non dipende dall'ordine delle righe. Un valore del sistema si usa così com'è, mai come
riferimento. Un ciclo o un riferimento che finisce senza valore: avviso con il solo nome a sinistra dell'=, e la riga
non si usa. MYEASYMP3TOIPHONE_HOME non si può impostare qui (dice dov'è questo file). Gli avvisi nominano righe o variabili,
mai quello che è scritto dopo l'=: potrebbe essere una chiave.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
from pathlib import Path

from .config import HOME_ENV_VAR, load_profiles, variable_in

ENV_FILE_NAME = "myEasyMP3toIPhone.env"
TEMPLATE_FILE_NAME = "myEasyMP3toIPhone.TEMPLATE.env"
TEMPLATE_PATH = Path(__file__).resolve().parent / TEMPLATE_FILE_NAME
SETTING = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)[ \t]*=(.*)")
LISTED = re.compile(r"^[ \t]*#?[ \t]*([A-Za-z_][A-Za-z0-9_]*)[ \t]*=", re.M)
ADDED_COMMENT = "# Aggiunte da myEasyMP3toIPhone: variabili lette dal programma o dalle tue Impostazioni"

_from_file: set = set()


def env_file_path(home: Path) -> Path:
    result = home / ENV_FILE_NAME
    return result


def parse_lines(lines: list) -> tuple:
    """(nome -> valore come scritto, anche vuoto; numeri delle righe che non sono né impostazioni, né commenti, né
    vuote)."""
    values = {}
    bad_lines = []
    number = 0
    for line in lines:
        number += 1
        text = line.strip()
        if text and not text.startswith("#"):
            match = SETTING.fullmatch(text)
            if match:
                value = match.group(2).strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                values[match.group(1)] = value
            else:
                bad_lines.append(number)
    result = (values, bad_lines)
    return result


def _literal(value: str) -> str:
    if value.startswith("$$"):
        result = value[1:]
    else:
        result = value
    return result


def resolve(name: str, values: dict, system: dict) -> tuple:
    """(valore, problema) di una riga del file: problema "" se va bene, "ciclo" o "senza valore" altrimenti. Un
    $ALTRA continua dal valore che ALTRA ha nel file, se non è vuoto, altrimenti prende quello del sistema."""
    seen = {name}
    current_value = values[name]
    value = ""
    problem = ""
    pending = True
    while pending:
        other = variable_in(current_value)
        in_file = values.get(other, "")
        if in_file == f"${other}":
            in_file = ""  # ALTRA=$ALTRA nel file vuol dire: ALTRA del sistema
        if not other:
            value = _literal(current_value)
            pending = False
        elif in_file and other not in seen:
            seen.add(other)
            current_value = in_file
        elif in_file:
            problem = "ciclo"
            pending = False
        else:
            value = system.get(other, "")
            pending = False
    if not problem and not value:
        problem = "senza valore"
    result = (value, problem)
    return result


def compute(values: dict, system: dict) -> tuple:
    """(nome -> valore da impostare, avvisi). Le righe vuote e NOME=$NOME lasciano il valore del sistema."""
    resolved = {}
    warnings = []
    for name, written in values.items():
        if written and written != f"${name}":
            if name == HOME_ENV_VAR:
                warnings.append(f"{name} ignorata nel file delle variabili: la cartella dati si sceglie prima di "
                                f"leggerlo. Usa la variabile di sistema {name} e lascia vuota questa riga")
            else:
                value, problem = resolve(name, values, system)
                if problem == "ciclo":
                    warnings.append(f"{name}: i riferimenti $NOME formano un ciclo, la riga non si usa")
                elif problem:
                    warnings.append(f"{name} legge una variabile senza valore: la riga non si usa (un valore che "
                                    "inizia davvero con $ si scrive $$)")
                else:
                    resolved[name] = value
    result = (resolved, warnings)
    return result


def load(env_file: Path) -> list:
    """Imposta le variabili del file nell'ambiente del programma; restituisce gli avvisi (senza valori)."""
    _from_file.clear()
    warnings = []
    lines = []
    try:
        lines = env_file.read_text(encoding="utf-8-sig").splitlines()
    except FileNotFoundError:
        lines = []
    except (OSError, UnicodeError) as exc:
        warnings.append(f"{env_file} NON letto ({type(exc).__name__}): le sue variabili non sono impostate. "
                        "Controlla che sia leggibile e salvato in UTF-8")
    values, bad_lines = parse_lines(lines)
    if bad_lines:
        numbers = ", ".join(str(number) for number in bad_lines)
        warnings.append(f"{env_file}: righe ignorate {numbers}, non sono NOME=valore (correggile o iniziale con #)")
    resolved, problems = compute(values, dict(os.environ))
    warnings += problems
    for name, value in resolved.items():
        os.environ[name] = value
        _from_file.add(name)
    return warnings


def source(name: str) -> str:
    """Da dove viene il valore: "file", "sistema", "" quando non ne ha."""
    if name in _from_file:
        result = "file"
    elif os.environ.get(name):
        result = "sistema"
    else:
        result = ""
    return result


def names_in_use(home: Path) -> list:
    """I nomi $NOME letti dalla configurazione della cartella dati: chiavi e server dei profili AI."""
    result = []
    for profile in load_profiles(home):
        for name in (profile.api_key_variable, variable_in(profile.base_url)):
            if name and name not in result:
                result.append(name)
    return result


def update(env_file: Path, template: Path, in_use: list) -> list:
    """Il file manca: copia del modello, leggibile solo dal proprietario. Poi aggiunge in fondo, vuoti, i nomi del
    modello e quelli in uso che non elenca (anche commentati). Non cambia mai una riga e non scrive mai un valore.
    Restituisce i messaggi (solo nomi)."""
    messages = []
    try:
        if not env_file.exists():
            shutil.copyfile(template, env_file)
            os.chmod(env_file, stat.S_IRUSR | stat.S_IWUSR)
            messages.append(f"Creato {env_file}")
        wanted = list(parse_lines(template.read_text(encoding="utf-8-sig").splitlines())[0]) + list(in_use)
        listed = set(LISTED.findall(env_file.read_text(encoding="utf-8-sig")))
        missing = []
        for name in wanted:
            if name not in listed and name not in missing and name != HOME_ENV_VAR:
                missing.append(name)
        if missing:
            with env_file.open("a", encoding="utf-8") as current:
                current.write(f"\n{ADDED_COMMENT}\n")
                for name in missing:
                    current.write(f"{name}=\n")
            messages.append(f"Aggiunte a {env_file}: {', '.join(missing)}")
    except (OSError, UnicodeError) as exc:
        messages.append(f"{env_file} NON aggiornato ({type(exc).__name__}): controlla che sia scrivibile e in UTF-8")
    return messages
