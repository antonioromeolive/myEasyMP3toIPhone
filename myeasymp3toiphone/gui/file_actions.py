# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""I comandi del tasto destro sui file, uguali nelle schede PC e iPhone: copiare negli appunti il nome dei file, il
percorso completo o la cartella (una riga per brano; le cartelle una volta sola) e aprire la cartella in Esplora
risorse. Solo lettura: i file non si toccano."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMenu

MAX_OPENED = 5      # cartelle aperte in Esplora risorse con un comando solo


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


def add_file_entries(menu: QMenu, paths: list, status=None) -> None:
    """Le voci Copia negli appunti (sottomenu: Nome del file / Percorso completo / Cartella) e Apri la cartella, per i
    file dati.
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

    def copy_folders() -> None:
        copy_text("\n".join(distinct))
        say(f"Copiate negli appunti {len(distinct)} cartelle")

    def open_folders() -> None:
        opened = open_in_explorer(paths)
        if opened == 0:
            say("Le cartelle non ci sono su questo PC (disco scollegato o file spostati)")
        elif len(distinct) > opened:
            say(f"Aperte le prime {opened} cartelle di {len(distinct)}")

    # le tre copie negli appunti stanno in un sottomenu: non si confondono con "Copia da PC a iPhone"
    clipboard = QMenu("Copia negli appunti", menu)
    entries = [
        (f"Nome del file ({count})", copy_names),
        (f"Percorso completo ({count})", copy_paths),
        (f"Cartella ({len(distinct)})", copy_folders),
    ]
    for text, slot in entries:
        action = clipboard.addAction(text)
        action.triggered.connect(slot)
    menu.addMenu(clipboard).setEnabled(count > 0)
    explorer = menu.addAction(f"Apri la cartella in Esplora risorse ({min(len(distinct), MAX_OPENED)})")
    explorer.setEnabled(count > 0)
    explorer.triggered.connect(open_folders)
