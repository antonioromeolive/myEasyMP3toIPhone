# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La copia della cartella dati prima che una nuova versione ne cambi il formato, per poter tornare indietro.

DATA_FORMAT si alza A MANO in ogni commit che cambia il formato di un file della cartella dati in modo che una
versione precedente non lo sappia più leggere (un campo nuovo che le versioni vecchie ignorano non conta). Nessun test
può accorgersi di un aumento dimenticato.

Il file di registro (myEasyMP3toIPhone.home.txt: versione e formato dell'ultimo programma avviato su questa cartella) dà la
versione nel nome dello zip. Una cartella senza registro è nuova: nessuna copia.
"""

from __future__ import annotations

import os
import re
import stat
import time
import zipfile
from pathlib import Path
from typing import Callable

DATA_FORMAT = 3  # alzato a mano: vedi sopra. 2: il programma si chiama myEasyMP3toIPhone (file e chiavi rinominati);
#                 3: le azioni in attesa per l'iPhone hanno il formato 2 (iphone_in_attesa.json, pending.py)
RECORD_FILE_NAME = "myEasyMP3toIPhone.home.txt"
BACKUP_FOLDER = "Backup"
GUARD_FILE_NAME = "copia_in_corso.lock"
VERSION_KEY = "version"
DATA_FORMAT_KEY = "data_format"
NOT_COPIED_FOLDERS = {BACKUP_FOLDER.casefold()}
NOT_COPIED_SUFFIX = ".lock"
MOST_WAITING = 3600
USABLE_VERSION = re.compile(r"[\w.+-]+")

_notices: list = []


class BackupError(Exception):
    """La copia non si può fare: il messaggio dice perché e cosa fare, e il programma si ferma."""


def notices() -> list:
    """Gli avvisi raccolti all'avvio, prima che i log siano pronti."""
    result = list(_notices)
    _notices.clear()
    return result


def _lock(handle) -> None:
    handle.seek(0)
    if handle.read(1) == b"":
        handle.seek(0)
        handle.write(b"0")
        handle.flush()
    handle.seek(0)
    if os.name == "nt":
        import msvcrt
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock(handle) -> None:
    handle.seek(0)
    if os.name == "nt":
        import msvcrt
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def read_record(home: Path) -> dict:
    result = {}
    try:
        text = (home / RECORD_FILE_NAME).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        text = ""
    for line in text.splitlines():
        if "=" in line:
            key, value = line.strip().split("=", 1)
            result[key] = value
    return result


def write_record(home: Path, version: str) -> None:
    """Versione e formato di questo programma, quando sono cambiati: l'ultimo passo di ogni avvio."""
    text = f"{VERSION_KEY}={version}\n{DATA_FORMAT_KEY}={DATA_FORMAT}\n"
    path = home / RECORD_FILE_NAME
    try:
        current = ""
        if path.is_file():
            current = path.read_text(encoding="utf-8")
        if current != text:
            path.write_text(text, encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        _notices.append(f"{path} NON scritto ({type(exc).__name__}): una copia futura della cartella dati potrebbe "
                        "non dire con quale versione usarla. Controlla che la cartella sia scrivibile")


def backup_needed(home: Path) -> bool:
    """DATA_FORMAT è più alto di quello con cui la cartella è stata usata l'ultima volta."""
    written = read_record(home).get(DATA_FORMAT_KEY, "")
    result = written.isdigit() and int(written) < DATA_FORMAT
    return result


def backup_name(recorded: str, version: str) -> str:
    """Il nome dello zip: la versione da usare con questa copia, quando il registro la dice."""
    if recorded and USABLE_VERSION.fullmatch(recorded):
        which = f"for-{recorded}"
    else:
        which = f"before-{version}"
    result = f"myEasyMP3toIPhone-home-{which}-{time.strftime('%Y%m%d-%H%M')}.zip"
    return result


def zip_home(home: Path, target: Path, tick: Callable[[], None] = lambda: None) -> None:
    """La cartella dati tranne Backup al primo livello, con percorsi relativi: scompattata in una cartella dati è di
    nuovo quella cartella. Scritta con un nome temporaneo; nessuna data di file può fermarla."""
    temporary = target.with_name(target.name + ".tmp")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, strict_timestamps=False) as zipped:
            for folder, sub_folders, file_names in os.walk(home):
                if Path(folder) == home:
                    kept = []
                    for sub_folder in sub_folders:
                        if sub_folder.casefold() not in NOT_COPIED_FOLDERS:
                            kept.append(sub_folder)
                    sub_folders[:] = kept
                for file_name in file_names:
                    if not file_name.endswith(NOT_COPIED_SUFFIX):
                        path = Path(folder) / file_name
                        zipped.write(path, path.relative_to(home))
                        tick()
        os.chmod(temporary, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def _wait_for(guard, tick: Callable[[], None]) -> None:
    deadline = time.monotonic() + MOST_WAITING
    locked = False
    while not locked:
        try:
            _lock(guard)
            locked = True
        except OSError:
            if time.monotonic() > deadline:
                raise TimeoutError("un'altra copia del programma sta facendo la copia da troppo tempo") from None
            tick()
            time.sleep(0.2)


def backup_if_needed(home: Path, version: str, tick: Callable[[], None] = lambda: None,
                     announce: Callable[[str], None] = lambda text: None):
    """La copia della cartella dati quando serve: il suo percorso, altrimenti None; BackupError se non si può fare."""
    result = None
    if backup_needed(home):
        folder = home / BACKUP_FOLDER
        announce(f"Questa versione cambia il formato di alcuni file della cartella dati: la copio in {folder}. "
                 "Può richiedere qualche minuto.")
        try:
            folder.mkdir(exist_ok=True)
            with (folder / GUARD_FILE_NAME).open("a+b") as guard:
                _wait_for(guard, tick)
                try:
                    if backup_needed(home):
                        target = folder / backup_name(read_record(home).get(VERSION_KEY, ""), version)
                        zip_home(home, target, tick)
                        write_record(home, version)
                        result = target
                finally:
                    _unlock(guard)
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            raise BackupError(f"La copia della cartella dati NON è stata fatta ({type(exc).__name__}: {exc}). Il "
                              f"programma si ferma e la cartella dati resta com'è. Chiudi le altre finestre di "
                              f"myEasyMP3toIPhone, controlla lo spazio libero e che {folder} sia scrivibile, poi "
                              "riavvia.") from exc
    return result
