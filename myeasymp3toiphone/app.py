# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""L'avvio del programma: la finestra (main) e la console (cli_main).

Finestra (myEasyMP3toIPhone.exe, o python main.py):
    --open CARTELLA         apre quella cartella all'avvio, al posto delle cartelle della musica (non si salva)

Console (myEasyMP3toIPhone-cli.exe, o python main.py --cli):
    --version               la versione
    --env                   le variabili d'ambiente, "impostata (file)", "impostata (sistema)" o "N/A": mai un valore
    --scan CARTELLA         la scansione di una cartella, con le sole regole; il rapporto va anche in scansioni/
    --ai PROFILO            con --scan: anche l'analisi AI con quel profilo
    --selftest              carica tutte le librerie del programma (per controllare una build)
"""

from __future__ import annotations

import sys
from pathlib import Path

from . import startup

CLI_HELP = __doc__.split("Console", 1)[1]


CRASH_FILE = "crash.log"
INSTANCE_LOCK = "myEasyMP3toIPhone.instance.lock"   # una sola finestra alla volta (home_backup non copia i .lock)
STREAMS_FILE = "myEasyMP3toIPhone.output.log"
_crash_file = None


def install_error_handlers(home: Path) -> None:
    """La finestra non ha console: quello che andrebbe sulla console va in un file della cartella dati, gli errori non
    gestiti (thread principale e altri) e i messaggi di Qt nel log, un crash nativo in crash.log (faulthandler).
    Senza questo un errore stampato su una console che non c'è chiude il programma senza lasciare traccia."""
    import faulthandler
    import logging
    import threading

    global _crash_file
    log = logging.getLogger("myeasymp3toiphone")
    if sys.stdout is None or sys.stderr is None:
        output = open(home / STREAMS_FILE, "a", encoding="utf-8", buffering=1)  # noqa: SIM115 - resta aperto
        if sys.stdout is None:
            sys.stdout = output
        if sys.stderr is None:
            sys.stderr = output
    _crash_file = open(home / CRASH_FILE, "a", encoding="utf-8")  # noqa: SIM115 - resta aperto per faulthandler
    faulthandler.enable(file=_crash_file, all_threads=True)

    def log_exception(kind, value, trace):
        log.critical("Errore non gestito", exc_info=(kind, value, trace))

    def log_thread_exception(arguments):
        log.critical("Errore non gestito nel thread %s", arguments.thread.name if arguments.thread else "?",
                     exc_info=(arguments.exc_type, arguments.exc_value, arguments.exc_traceback))

    sys.excepthook = log_exception
    threading.excepthook = log_thread_exception

    from PySide6.QtCore import QtMsgType, qInstallMessageHandler

    levels = {QtMsgType.QtDebugMsg: logging.DEBUG, QtMsgType.QtInfoMsg: logging.INFO,
              QtMsgType.QtWarningMsg: logging.WARNING, QtMsgType.QtCriticalMsg: logging.ERROR,
              QtMsgType.QtFatalMsg: logging.CRITICAL}

    def log_qt_message(kind, _context, message):
        logging.getLogger("qt").log(levels.get(kind, logging.WARNING), "%s", message)

    qInstallMessageHandler(log_qt_message)


def main() -> int:
    """La finestra: una sola copia alla volta (un lucchetto nella cartella dati)."""
    result = startup.FAILED
    if startup.ready(in_console=False):
        from PySide6.QtCore import QLockFile
        from PySide6.QtWidgets import QApplication, QMessageBox

        from . import i18n
        from .config import PRODUCT, AppSettings, config_dir
        i18n.set_language(AppSettings.load().language)
        if i18n.english():
            i18n.install_qt_hooks()       # prima di importare l'interfaccia: le sue classi passano da tr()
        from .gui.main_window import MainWindow
        from .gui.theme import apply_theme, install_italian

        install_error_handlers(config_dir())
        app = QApplication.instance() or QApplication(sys.argv)
        app.setApplicationName(PRODUCT)
        apply_theme(app)
        if not i18n.english() and not install_italian(app):
            import logging
            logging.getLogger("myeasymp3toiphone").info("Traduzione italiana dei pulsanti di Qt non trovata: "
                                                        "restano in inglese")
        instance_lock = QLockFile(str(config_dir() / INSTANCE_LOCK))
        instance_lock.setStaleLockTime(0)   # il lucchetto di un programma chiuso male si riconosce e si riprende
        if instance_lock.tryLock(200):
            window = MainWindow()
            folder = _option_value(sys.argv[1:], "--open")
            if folder:
                window.open_on_start = Path(folder)
            window.show()
            result = app.exec()
            instance_lock.unlock()
        else:
            QMessageBox.information(None, PRODUCT, "myEasyMP3toIPhone è già aperto: usa la finestra che c'è già.\n\n"
                                    "Due copie aperte insieme si contendono la cartella dati.")
            result = 0
    return result


def _option_value(arguments: list, option: str) -> str:
    result = ""
    if option in arguments:
        position = arguments.index(option)
        if position + 1 < len(arguments):
            result = arguments[position + 1]
    return result


def selftest() -> int:
    """Carica i moduli che la build deve contenere e controlla i file distribuiti con il programma."""
    import importlib

    from . import env_file

    modules = ("PySide6.QtWidgets", "PySide6.QtGui", "mutagen.mp3", "mutagen.mp4", "mutagen.flac", "mutagen.oggopus",
               "mutagen.apev2", "mutagen.asf", "mutagen.wave", "mutagen.aiff",
               "requests", "keyring", "anthropic", "pymobiledevice3.lockdown", "pymobiledevice3.usbmux",
               "pymobiledevice3.services.afc",
               "cryptography.hazmat.primitives.ciphers", "sqlite3",
               "myeasymp3toiphone.gui.main_window", "myeasymp3toiphone.scan",
               "myeasymp3toiphone.phone_sync", "myeasymp3toiphone.phone_actions", "myeasymp3toiphone.i18n_en")
    failed = 0
    for name in modules:
        try:
            importlib.import_module(name)
            print(f"ok      {name}")
        except Exception as exc:  # noqa: BLE001 - ogni modulo per conto suo
            failed += 1
            print(f"ERRORE  {name}: {type(exc).__name__}: {exc}")
    if env_file.TEMPLATE_PATH.is_file():
        print(f"ok      {env_file.TEMPLATE_FILE_NAME}")
    else:
        failed += 1
        print(f"ERRORE  manca {env_file.TEMPLATE_PATH}")
    import keyring
    print(f"info    credential store: {type(keyring.get_keyring()).__name__}")
    result = 1 if failed else 0
    return result


def _scan(folder: str, profile_name: str) -> int:
    from .ai import make_provider
    from .config import config_dir, load_profiles
    from .library import scan_folder
    from .scan import report_text, save_report, scan_tracks

    provider = None
    result = 0
    if profile_name:
        for profile in load_profiles():
            if profile.name == profile_name:
                provider = make_provider(profile)
        if provider is None:
            print(f"Profilo AI {profile_name!r} non trovato (Impostazioni → Profili AI)", file=sys.stderr)
            result = 2
    if result == 0:
        path = Path(folder)
        if not path.is_dir():
            print(f"Cartella non trovata: {folder}", file=sys.stderr)
            result = 2
        else:
            from .adoption import pc_fingerprints
            from .tag_cache import TagCache
            cache = TagCache(config_dir())
            tracks = scan_folder(path, cache=cache)
            report = scan_tracks(tracks, str(path), provider, fingerprints=pc_fingerprints(tracks, cache))
            print(report_text(report))
            print(f"Rapporto salvato in {save_report(report, config_dir() / 'scansioni')}")
    return result


def cli_main() -> int:
    arguments = sys.argv[1:]
    if "--version" in arguments:
        from .version import app_version
        print(app_version())
        result = 0
    elif "--selftest" in arguments:
        result = selftest()
    elif not startup.ready(in_console=True):
        result = startup.FAILED
    elif "--env" in arguments:
        from .environment import report_text
        print(report_text())
        result = 0
    elif "--scan" in arguments:
        result = _scan(_option_value(arguments, "--scan"), _option_value(arguments, "--ai"))
    else:
        print("myEasyMP3toIPhone, console" + CLI_HELP)
        result = 0
    return result
