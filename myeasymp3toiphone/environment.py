# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le variabili d'ambiente del programma, impostate nel file delle variabili della cartella dati (env_file) o nel
sistema: cosa sono, il rapporto di cosa è impostato e da dove viene (--env, mai un valore), il valore usato
(Informazioni…, mai una chiave) e dove è salvata la chiave di ogni profilo AI. Vedi "Quale valore vince" nel README.
"""

from __future__ import annotations

import logging
import os
import re
import sys
from urllib.parse import urlsplit, urlunsplit

from . import env_file
from .config import (
    HOME_ENV_VAR, OLLAMA, ProviderProfile, home_env_ignored, home_folder, is_variable_name, load_profiles,
    secret_store, variables_named_in_settings,
)

# Ogni variabile che il programma legge, tranne quelle nominate dalle Impostazioni e quelle di sistema (APPDATA…).
# Un test confronta questo elenco con il codice.
VARIABLES = (HOME_ENV_VAR, "MYEASYMP3TOIPHONE_LOG_LEVEL", "OLLAMA_API_BASE", "OLLAMA_API_KEY", "AZURE_FOUNDRY_EP",
             "AZURE_FOUNDRY_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "MYCALIBRETOOLS_HOME")
# Lette da build_dist.py e vscode_deploy.py: nel rapporto solo quando il programma gira dai sorgenti.
BUILD_VARIABLES = ("MY_VSCODE_ZIP_DIR", "MY_VSCODE_INSTALL_DIR")
NOT_SET = " (la variabile non è impostata)"
NO_KEY = "nessuna chiave"
SECRET_NAME = re.compile(r"KEY|PASSWORD|PASSWD|PWD|SECRET|TOKEN|CREDENTIAL", re.IGNORECASE)


def status(name: str) -> str:
    """Se una variabile ha un valore: mai il valore, nemmeno in parte."""
    where = env_file.source(name)
    if name == HOME_ENV_VAR and home_env_ignored():
        result = "impostata, ignorata: non è un percorso completo"
    elif where:
        result = f"impostata ({where})"
    else:
        result = "N/A"
    return result


def report_rows() -> list:
    names = list(VARIABLES)
    try:
        template_lines = env_file.TEMPLATE_PATH.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError):
        template_lines = []
    for name in env_file.parse_lines(template_lines)[0]:
        if name not in names:
            names.append(name)
    if not getattr(sys, "frozen", False):
        names += BUILD_VARIABLES
    for name in variables_named_in_settings(home_folder()):
        if name not in names:
            names.append(name)
    result = []
    for name in names:
        result.append((name, status(name)))
    return result


def log_level() -> int:
    requested = os.environ.get("MYEASYMP3TOIPHONE_LOG_LEVEL", "").upper()
    default = logging.DEBUG if "--debug" in sys.argv[1:] else logging.INFO
    result = getattr(logging, requested, default)
    if not isinstance(result, int):
        result = default
    return result


def _without_credentials(value: str) -> str:
    result = value
    if "://" in value:
        try:
            parts = urlsplit(value)
            result = urlunsplit((parts.scheme, parts.netloc.rpartition("@")[2], parts.path, "", ""))
        except ValueError:
            result = "impostata"
    return result


def _value_used(name: str) -> str:
    value = os.environ.get(name, "")
    if name == HOME_ENV_VAR:
        result = str(home_folder())
        if home_env_ignored():
            result += " (il valore impostato è ignorato: non è un percorso completo)"
        elif not value:
            result += NOT_SET
    elif name == "MYEASYMP3TOIPHONE_LOG_LEVEL":
        result = logging.getLevelName(log_level())
        if not value:
            result += NOT_SET
        elif not isinstance(getattr(logging, value.upper(), None), int):
            result += " (il valore impostato non è un livello)"
    elif value:
        result = _without_credentials(value)
    else:
        result = "N/A"
    return result


def value_rows() -> list:
    """(nome, valore usato) per Informazioni…: una variabile di chiave o di password dice solo "impostata"."""
    key_variables = []
    for profile in load_profiles(home_folder()):
        key_variables.append(profile.api_key_variable)
    result = []
    for name, where in report_rows():
        if name in key_variables or SECRET_NAME.search(name):
            result.append((name, where))
        else:
            result.append((name, _value_used(name)))
    return result


def key_source(profile: ProviderProfile) -> str:
    """Dove è salvata la chiave di un profilo: mai la chiave."""
    variable = profile.api_key_variable
    if profile.key_from_variable():
        result = f"la variabile d'ambiente ${variable}"
    else:
        store = secret_store(profile.name)
        if store:
            saved = f"la chiave salvata in {store}"
        else:
            saved = NO_KEY
        if is_variable_name(variable):
            result = f"${variable} non ha valore: {saved}"
        else:
            result = saved
    return result


def uses_a_key(profile: ProviderProfile) -> bool:
    """Ogni tipo di AI tranne Ollama, che chiede una chiave solo per un server non locale."""
    result = profile.kind != OLLAMA or key_source(profile) != NO_KEY
    return result


def key_rows() -> list:
    result = []
    for profile in load_profiles(home_folder()):
        if uses_a_key(profile):
            result.append((profile.name, key_source(profile)))
    return result


def _aligned(rows: list) -> list:
    width = 0
    for name, _where in rows:
        width = max(width, len(name))
    lines = []
    for name, where in rows:
        lines.append(f"  {name:<{width}} = {where}")
    return lines


def report_text() -> str:
    """Quello che stampa --env."""
    lines = [f"Cartella dati: {home_folder()}", "",
             f"Variabili d'ambiente. Impostale in {env_file.env_file_path(home_folder())}: un valore scritto lì vince, "
             "una riga vuota usa quello del sistema", ""]
    lines += _aligned(report_rows())
    keys = key_rows()
    if keys:
        lines += ["", "Le chiavi API dei profili AI:"] + _aligned(keys)
    result = "\n".join(lines)
    return result
