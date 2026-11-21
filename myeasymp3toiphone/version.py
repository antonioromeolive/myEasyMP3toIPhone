# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La versione del programma, mostrata nel titolo e in Informazioni, scritta nei log.

"<major.minor>.<commit> (<data dell'ultimo commit>)", letta dal repository git locale (niente rete): per esempio
"0.1.18 (2026-11-21 16:01)". Con modifiche non ancora registrate è il numero che avrà il prossimo commit, marcato
-dev e datato dal file modificato più recente: "0.1.19-dev (2026-11-21 19:40)". Un repository senza commit dà
"<major.minor>.1-dev". Ogni versione letta da git è conservata in VERSION_FILE (fuori da git), mostrata quando git non
si può interrogare (la build, senza .git); senza nessuna delle due, la versione di pyproject.toml.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from functools import lru_cache
from pathlib import Path

log = logging.getLogger(__name__)

PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parent
VERSION_FILE = PACKAGE / "_version.txt"
DEFAULT = "0.1.0"
DATE_FORMAT = "%Y-%m-%d %H:%M"
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def _project_version() -> str:
    result = DEFAULT
    try:
        match = re.search(r'^version\s*=\s*"([^"]+)"', (REPO / "pyproject.toml").read_text(encoding="utf-8"), re.M)
        if match:
            result = match.group(1)
    except OSError:
        result = DEFAULT
    return result


def _base() -> str:
    result = ".".join(_project_version().split(".")[:2])
    return result


def _git(*args: str) -> str:
    out = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, timeout=10,
                         creationflags=CREATE_NO_WINDOW, check=True)
    result = out.stdout.strip()
    return result


def _commit_count() -> int:
    """I commit di HEAD; 0 in un repository che non ne ha ancora."""
    try:
        result = int(_git("rev-list", "--count", "HEAD"))
    except subprocess.CalledProcessError:
        result = 0
    return result


def _changed_files() -> list:
    changed = []
    for line in _git("status", "--porcelain", "--untracked-files=all").splitlines():
        changed.append(line[3:].split(" -> ")[-1].strip('"'))
    return changed


def from_git() -> str | None:
    """La versione secondo git, o None (nessun repository, git mancante, un errore)."""
    result = None
    if (REPO / ".git").exists() and shutil.which("git") is not None:
        try:
            count = _commit_count()
            changed = _changed_files()
            if count > 0 and not changed:
                when = _git("log", "-1", "--format=%cd", f"--date=format:{DATE_FORMAT}")
                result = f"{_base()}.{count} ({when})"
            else:
                times = []
                for name in changed:
                    try:
                        times.append((REPO / name).stat().st_mtime)
                    except OSError:
                        pass  # cancellato
                if times:
                    when = datetime.fromtimestamp(max(times))
                else:
                    when = datetime.now()
                result = f"{_base()}.{count + 1}-dev ({when.strftime(DATE_FORMAT)})"
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            log.debug("Versione da git non disponibile: %s", exc)
            result = None
    return result


def _save(version: str) -> None:
    """Conservata per quando git manca; sostituita in un solo passo."""
    try:
        current = ""
        if VERSION_FILE.is_file():
            current = VERSION_FILE.read_text(encoding="utf-8").strip()
        if current != version:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=PACKAGE, prefix="_version_", suffix=".tmp",
                                             delete=False) as temporary:
                temporary.write(version + "\n")
            os.replace(temporary.name, VERSION_FILE)
    except OSError as exc:
        log.debug("Impossibile salvare %s: %s", VERSION_FILE, exc)


@lru_cache(maxsize=1)
def app_version() -> str:
    result = from_git()
    if result is not None:
        _save(result)
    else:
        saved = ""
        try:
            saved = VERSION_FILE.read_text(encoding="utf-8").strip()
        except OSError:
            saved = ""
        result = saved or _project_version()
    return result


def file_version(version: str) -> tuple:
    """I quattro numeri della versione di un file Windows: "0.1.51-dev (…)" -> (0, 1, 51, 0)."""
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", version.strip())
    if match:
        result = (int(match.group(1)), int(match.group(2)), int(match.group(3)), 0)
    else:
        result = (0, 0, 0, 0)
    return result
