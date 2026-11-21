# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Quello che il programma fa per primo, prima di leggere qualsiasi impostazione: la cartella dati, la sua copia quando
un formato cambia (home_backup), le migrazioni, il registro della versione, i log."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Callable

from . import env_file, environment, home_backup
from .ai import ensure_default_profile
from pathlib import Path

from .config import (
    DEFAULT_SCAN_PROFILE, HOME_ENV_VAR, KEYRING_SERVICE, OLD_KEYRING_SERVICE, OLD_PRODUCT, SETTINGS_FILE, AppSettings,
    config_dir, home_env_ignored, load_profiles, move_old_secret, server_entry,
)
from .version import app_version

FAILED = 1
LOG_FILE = "myEasyMP3toIPhone.log"
LOG_BYTES = 5 * 1024 * 1024
LOG_BACKUPS = 3
# Le impostazioni della prima versione (CopiaStiMP3), nel registro di Windows: QSettings(organizzazione, programma)
OLD_QSETTINGS = ("CopiaStiMP3", "CopiaStiMP3")
OLD_QSETTINGS_KEYS = {"library_dir": "library_dir", "last_folder": "last_folder", "last_import": "last_import",
                      "last_export": "last_export", "iphone/last_app": "iphone_last_app"}

log = logging.getLogger(__name__)
_notices: list = []


OLD_RECORD_FILE = f"{OLD_PRODUCT}.home.txt"
OLD_ENV_FILE = f"{OLD_PRODUCT}.env"
OLD_ENV_PREFIX = "MYCOPIASTIMP3_"
NEW_ENV_PREFIX = "MYEASYMP3TOIPHONE_"


def _adopt_old_record(home: Path) -> None:
    """Il registro del nome precedente prende il nome nuovo PRIMA della copia di sicurezza: così la copia si fa (il
    formato dei dati era 1) e porta nel nome la versione con cui usarla."""
    old = home / OLD_RECORD_FILE
    new = home / home_backup.RECORD_FILE_NAME
    if old.is_file() and not new.exists():
        old.rename(new)


def migrate_from_old_name(home: Path) -> None:
    """Dopo la copia di sicurezza: i file e le chiavi del nome precedente (myCopiaStiMP3) passano a quello nuovo.
    Ogni passo si fa solo se trova qualcosa del nome vecchio, quindi una volta sola."""
    old_env = home / OLD_ENV_FILE
    new_env = env_file.env_file_path(home)
    if old_env.is_file() and not new_env.exists():
        text = old_env.read_text(encoding="utf-8-sig")
        new_env.write_text(text.replace(OLD_ENV_PREFIX, NEW_ENV_PREFIX), encoding="utf-8")
        old_env.unlink()
        _notices.append(f"File delle variabili rinominato in {new_env} (MYCOPIASTIMP3_… -> MYEASYMP3TOIPHONE_…)")
    settings = AppSettings.load(home)
    changed = False
    old_library = Path.home() / "Music" / OLD_PRODUCT
    if not settings.library_dir and old_library.is_dir():
        settings.library_dir = str(old_library)
        changed = True
    old_copies = Path.home() / "Music" / f"{OLD_PRODUCT} per iTunes"
    if not settings.itunes_dir and old_copies.is_dir():
        settings.itunes_dir = str(old_copies)   # iTunes usa le copie dove sono: non si spostano
        changed = True
    if changed:
        settings.save(home)
    moved = 0
    for profile in load_profiles(home):
        for entry in (profile.name, server_entry(profile.name)):
            if move_old_secret(entry):
                moved += 1
    if moved:
        _notices.append(f"{moved} chiavi spostate nel credential store da {OLD_KEYRING_SERVICE} a {KEYRING_SERVICE}")


def migrate_old_settings(home) -> bool:
    """Una volta per cartella dati: le impostazioni della prima versione, nel registro, vanno in settings.json.
    True quando ne ha trovate."""
    found = False
    if not (home / SETTINGS_FILE).exists():
        from PySide6.QtCore import QSettings
        old = QSettings(*OLD_QSETTINGS)
        settings = AppSettings()
        for old_key, new_key in OLD_QSETTINGS_KEYS.items():
            value = old.value(old_key, "")
            if isinstance(value, str) and value:
                setattr(settings, new_key, value)
                found = True
        if found:
            settings.save(home)
            _notices.append("Impostazioni della versione precedente (registro di Windows) copiate in "
                            f"{home / SETTINGS_FILE}")
    return found


def prepare(tick: Callable[[], None] = lambda: None, announce: Callable[[str], None] = lambda text: None) -> None:
    """In quest'ordine: la copia, prima che cambi qualcosa nella cartella dati; il file delle variabili, letto prima
    che qualcosa legga una variabile (i log ne leggono una: setup_logging viene dopo); le migrazioni; il file delle
    variabili aggiornato con i nomi in uso; il registro, per ultimo.
    OSError: la cartella dati non si può usare; home_backup.BackupError: la copia non si può fare."""
    home = config_dir()
    if home_env_ignored():
        _notices.append(f"{HOME_ENV_VAR} ignorata: non è un percorso completo. La cartella dati è {home}")
    version = app_version().split(" ", 1)[0]
    _adopt_old_record(home)
    home_backup.backup_if_needed(home, version, tick, announce)
    migrate_from_old_name(home)
    variables_file = env_file.env_file_path(home)
    _notices.extend(env_file.load(variables_file))
    migrate_old_settings(home)
    if ensure_default_profile(home):
        _notices.append(f"Creato il profilo AI \"{DEFAULT_SCAN_PROFILE}\" (Ollama su questo computer) per la scansione")
    _notices.extend(env_file.update(variables_file, env_file.TEMPLATE_PATH, env_file.names_in_use(home)))
    home_backup.write_record(home, version)


def setup_logging() -> None:
    """Il log nella cartella dati, a rotazione; poi gli avvisi raccolti prima che fosse pronto."""
    handler = RotatingFileHandler(config_dir() / LOG_FILE, maxBytes=LOG_BYTES, backupCount=LOG_BACKUPS,
                                  encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(environment.log_level())
    root.addHandler(handler)
    log.info("myEasyMP3toIPhone %s avviato", app_version())
    for text in _notices + home_backup.notices():
        log.warning("%s", text)
    _notices.clear()


class _WindowNotice:
    """Senza console: mentre si fa la copia lo dice in una piccola finestra."""

    def __init__(self) -> None:
        self.label = None

    def announce(self, text: str) -> None:
        from PySide6.QtWidgets import QApplication, QLabel
        app = QApplication.instance() or QApplication(sys.argv)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setMargin(20)
        self.label.setWindowTitle("myEasyMP3toIPhone")
        self.label.resize(480, 120)
        self.label.show()
        app.processEvents()

    def tick(self) -> None:
        if self.label is not None:
            from PySide6.QtWidgets import QApplication
            QApplication.instance().processEvents()

    def close(self) -> None:
        if self.label is not None:
            self.label.close()
            self.label = None


def _show_failure(text: str, in_console: bool) -> None:
    if in_console:
        print(text, file=sys.stderr)
    else:
        from PySide6.QtWidgets import QApplication, QMessageBox
        _app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "myEasyMP3toIPhone non può partire", text)


def ready(in_console: bool = False) -> bool:
    """True quando il programma può proseguire; altrimenti ha detto perché, in console o in una finestra."""
    notice = _WindowNotice()
    tick = notice.tick
    announce = notice.announce
    if in_console:
        tick = lambda: None  # noqa: E731
        announce = lambda text: print(text, file=sys.stderr, flush=True)  # noqa: E731
    result = True
    try:
        prepare(tick, announce)
        setup_logging()
    except home_backup.BackupError as exc:
        result = False
        _show_failure(str(exc), in_console)
    except OSError as exc:
        result = False
        _show_failure(f"La cartella dati non si può usare ({type(exc).__name__}: {exc}): il programma si ferma. "
                      f"Controlla la cartella, o la variabile {HOME_ENV_VAR} che la sceglie.", in_console)
    finally:
        notice.close()
    return result
