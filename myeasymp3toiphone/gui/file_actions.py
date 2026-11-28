# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""I comandi del tasto destro sui file, uguali nelle schede PC e iPhone: copiare negli appunti il nome dei file, il
percorso completo o la cartella (una riga per brano; le cartelle una volta sola), aprire la cartella in Esplora
risorse o in TagScanner (un programma per i tag che l'utente installa da sé). Queste voci non scrivono niente;
TagScanner cambia i file direttamente, fuori da questo programma, e Rileggi (F5) mostra poi i tag nuovi."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication, QMenu

MAX_OPENED = 5      # cartelle aperte in Esplora risorse con un comando solo
TAGSCAN_EXE = "Tagscan.exe"
TAGSCAN_FOLDER = "TagScanner"
PROGRAMS_ENV_VAR = ("ProgramFiles", "ProgramFiles(x86)")     # Programmi, Programmi (x86)
USER_PROGRAMS_ENV_VAR = "LOCALAPPDATA"                       # i programmi dell'utente: …\AppData\Local\Programs
USER_PROGRAMS_FOLDER = "Programs"
TAGSCAN_MISSING = ("TagScanner non trovato. Se l'hai installato in un posto diverso dal solito, scegli il file "
                   "Tagscan.exe in Impostazioni → Generale → TagScanner.")


def tagscan_places() -> list:
    """I posti soliti di Tagscan.exe: Programmi, Programmi (x86), i programmi dell'utente."""
    result = []
    for variable in PROGRAMS_ENV_VAR:
        base = os.environ.get(variable, "")
        if base:
            result.append(Path(base) / TAGSCAN_FOLDER / TAGSCAN_EXE)
    base = os.environ.get(USER_PROGRAMS_ENV_VAR, "")
    if base:
        result.append(Path(base) / USER_PROGRAMS_FOLDER / TAGSCAN_FOLDER / TAGSCAN_EXE)
    return result


def find_tagscan(setting: str = "") -> Optional[Path]:
    """TagScanner: il file scelto in Impostazioni (o la cartella che lo contiene), altrimenti il primo dei posti
    soliti; None se non c'è."""
    result = None
    text = os.path.expandvars((setting or "").strip().strip('"'))
    if text:
        candidate = Path(text).expanduser()
        if candidate.is_dir():
            candidate = candidate / TAGSCAN_EXE
        if candidate.is_file():
            result = candidate
    else:
        for candidate in tagscan_places():
            if result is None and candidate.is_file():
                result = candidate
    return result


def start_folder(paths: list) -> str:
    """La cartella da cui far partire TagScanner: quella dei file; con file in più cartelle, la cartella che le
    contiene tutte (un album con CD1 e CD2: la cartella dell'album); su dischi diversi, quella del primo file."""
    distinct = folders(paths)
    result = ""
    if len(distinct) == 1:
        result = distinct[0]
    elif distinct:
        try:
            result = os.path.commonpath(distinct)
        except ValueError:
            result = distinct[0]
        if not result or len(result) <= 3:            # solo "C:\": troppo in alto
            result = distinct[0]
    return result


def open_in_tagscan(executable: Path, paths: list) -> str:
    """Apre TagScanner sulla cartella dei file (start_folder): la cartella aperta, "" se non c'è."""
    folder = start_folder(paths)
    result = ""
    if folder and Path(folder).is_dir():
        subprocess.Popen([str(executable), folder])   # noqa: S603 - il programma scelto dall'utente
        result = folder
    return result


def names_text(paths: list) -> str:
    lines = []
    for path in paths:
        lines.append(Path(path).name)
    result = "\n".join(lines)
    return result


def paths_text(paths: list) -> str:
    lines = []
    for path in paths:
        lines.append(str(path))
    result = "\n".join(lines)
    return result


def folders(paths: list) -> list:
    """Le cartelle dei file, una volta sola, nell'ordine dei file."""
    result = []
    seen = set()
    for path in paths:
        folder = str(Path(path).parent)
        if folder.casefold() not in seen:
            seen.add(folder.casefold())
            result.append(folder)
    return result


def copy_text(text: str) -> None:
    QApplication.clipboard().setText(text)


def open_in_explorer(paths: list) -> int:
    """Apre in Esplora risorse le cartelle dei file che ci sono (un file solo: selezionato). Restituisce quante."""
    existing = []
    for path in paths:
        if Path(path).exists():
            existing.append(Path(path))
    opened = 0
    if len(existing) == 1 and sys.platform == "win32":
        subprocess.Popen(["explorer", "/select,", str(existing[0])])   # noqa: S603, S607 - Esplora risorse
        opened = 1
    else:
        for folder in folders(existing)[:MAX_OPENED]:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", folder])   # noqa: S603, S607
            opened += 1
    return opened


def add_file_entries(menu: QMenu, paths: list, status=None, tagscan: Optional[str] = None) -> None:
    """Le voci Copia negli appunti (sottomenu: Nome del file / Percorso completo / Nome e Percorso della cartella),
    Apri la cartella e, con tagscan (l'impostazione tagscan_path, anche ""), Apri in TagScanner, per i file dati.
    status(testo): dove dire cosa è successo (la barra di stato)."""
    count = len(paths)
    distinct = folders(paths)

    def say(text: str) -> None:
        if status is not None:
            status(text)

    def copy_names() -> None:
        copy_text(names_text(paths))
        say(f"Copiati negli appunti i nomi di {count} file")

    def copy_paths() -> None:
        copy_text(paths_text(paths))
        say(f"Copiati negli appunti i percorsi di {count} file")

    def copy_folder_names() -> None:
        copy_text(names_text(distinct))
        say(f"Copiati negli appunti i nomi di {len(distinct)} cartelle")

    def copy_folders() -> None:
        copy_text("\n".join(distinct))
        say(f"Copiati negli appunti i percorsi di {len(distinct)} cartelle")

    def open_folders() -> None:
        opened = open_in_explorer(paths)
        if opened == 0:
            say("Le cartelle non ci sono su questo PC (disco scollegato o file spostati)")
        elif len(distinct) > opened:
            say(f"Aperte le prime {opened} cartelle di {len(distinct)}")

    # le copie negli appunti stanno in un sottomenu: non si confondono con "Copia da PC a iPhone"
    clipboard = QMenu("Copia negli appunti", menu)
    entries = [
        (f"Nome del file ({count})", copy_names),
        (f"Percorso completo ({count})", copy_paths),
        (f"Nome della cartella ({len(distinct)})", copy_folder_names),
        (f"Percorso della cartella ({len(distinct)})", copy_folders),
    ]
    for text, slot in entries:
        action = clipboard.addAction(text)
        action.triggered.connect(slot)
    menu.addMenu(clipboard).setEnabled(count > 0)
    explorer = menu.addAction(f"Apri la cartella in Esplora risorse ({min(len(distinct), MAX_OPENED)})")
    explorer.setEnabled(count > 0)
    explorer.triggered.connect(open_folders)
    if tagscan is not None:
        add_tagscan_entry(menu, paths, tagscan, status)


def add_tagscan_entry(menu: QMenu, paths: list, setting: str, status=None) -> None:
    """La voce Apri in TagScanner: la cartella dei file (o quella che contiene le loro cartelle). Senza TagScanner
    la voce è spenta e dice dove sceglierlo."""
    executable = find_tagscan(setting)
    folder = start_folder(paths)

    def start() -> None:
        opened = open_in_tagscan(executable, paths)
        if status is not None and opened:
            status(f"TagScanner aperto su {opened}: quando hai finito di cambiare i tag, premi Rileggi (F5)")
        elif status is not None:
            status("La cartella non c'è su questo PC (disco scollegato o file spostati)")

    if executable is None:
        action = menu.addAction("Apri in TagScanner (non trovato: Impostazioni → Generale)")
        action.setEnabled(False)
        action.setToolTip(TAGSCAN_MISSING)
    else:
        action = menu.addAction("Apri in TagScanner")
        action.setEnabled(bool(folder))
        action.setToolTip(f"Apre TagScanner sulla cartella {folder}. TagScanner cambia i file direttamente, fuori da "
                          "questo programma: quando hai finito, Rileggi (F5) mostra i tag nuovi.")
        action.triggered.connect(start)
