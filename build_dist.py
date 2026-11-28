# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""
build_dist.py - costruisce la distribuzione: una cartella i cui programmi girano senza Python, e il suo zip.

Si esegue con l'ambiente virtuale del progetto, dove sono installati requirements.txt e requirements_build.txt:
    .venv\\Scripts\\python -m pip install -r requirements.txt -r requirements_build.txt
    .venv\\Scripts\\python build_dist.py
(oppure in VS Code: Terminale -> Esegui attività di compilazione, Ctrl+Shift+B).
Risultato: dist/myEasyMP3toIPhone (i programmi di myEasyMP3toIPhone.spec con la loro cartella _internal, README.md, LICENSE,
THIRD_PARTY_NOTICES.md e i
file di dist_files: READ ME FIRST.txt, Create shortcuts.cmd, Remove shortcuts.cmd, più version.txt con il numero
della versione, version=<versione>, in cima e in _internal) e
dist/myEasyMP3toIPhone-<versione>-<sistema>-<processore>.zip, con la versione data da git (version.py): 0.1.3, oppure
0.1.4-dev con modifiche non registrate. Degli zip precedenti in dist resta solo quello della build prima.
PyInstaller tiene la sua analisi in build/pyinstaller e la riusa: rifà solo quello che è cambiato. La butta e
ricomincia da zero (--clean) quando cambiano Python o le librerie installate nell'ambiente (l'elenco con le versioni
sta in build/pyinstaller/librerie.txt), oppure se si chiede: python build_dist.py --clean.
Prima di finire, controlla la build con myEasyMP3toIPhone-cli.exe --selftest.
Infine vscode_deploy.py copia lo zip nella cartella myEasyMP3toIPhone di MY_VSCODE_ZIP_DIR e lo installa nella cartella
myEasyMP3toIPhone di MY_VSCODE_INSTALL_DIR, conservando come zip la versione sostituita; ogni cartella myEasyMP3toIPhone viene
creata se manca; una variabile non impostata = quel passo saltato, con un avviso.
Le due variabili si leggono dal sistema e dal file delle variabili della cartella dati
(%USERPROFILE%\\.myEasyMP3toIPhone\\myEasyMP3toIPhone.env), con le stesse regole del programma. vscode_deploy.py eseguito da
solo legge invece solo le variabili del sistema.
"""
import glob
import os
import platform
import shutil
import subprocess
import sys

import vscode_deploy
from myeasymp3toiphone import env_file
from myeasymp3toiphone.config import home_folder
from myeasymp3toiphone.version import VERSION_FILE, from_git

PROGRAM_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
BUILD_DIRECTORY   = os.path.join(PROGRAM_DIRECTORY, "build")
DIST_DIRECTORY    = os.path.join(PROGRAM_DIRECTORY, "dist")
DIST_NAME         = "myEasyMP3toIPhone"
SPEC_FILE         = os.path.join(PROGRAM_DIRECTORY, "myEasyMP3toIPhone.spec")
TOP_FILES         = ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md")   #copiati accanto ai programmi
DIST_FILES_DIRECTORY = os.path.join(PROGRAM_DIRECTORY, "dist_files")   #anche questi, tranne INTERNAL_FILES
INTERNAL_FILES    = ("shortcuts.ps1",)   #messi in _internal da myEasyMP3toIPhone.spec
SELFTEST_PROGRAM  = "myEasyMP3toIPhone-cli.exe"
WORK_DIRECTORY    = os.path.join(BUILD_DIRECTORY, "pyinstaller")   #la cache di PyInstaller
LIBRARIES_FILE    = os.path.join(WORK_DIRECTORY, "librerie.txt")   #Python e le librerie dell'ultima build
CLEAN_OPTION      = "--clean"
SYSTEM_NAMES      = {"win32": "windows", "darwin": "macos"}
MACHINE_NAMES     = {"amd64": "x64", "x86_64": "x64", "aarch64": "arm64"}


def dist_platform() -> str:
    """ il sistema e il processore della build, come parte di un nome di file: windows-x64 """
    system = SYSTEM_NAMES.get(sys.platform, sys.platform)
    machine = platform.machine().lower()
    result: str = f"{system}-{MACHINE_NAMES.get(machine, machine)}"
    return result


def archive_base(version: str) -> str:
    result: str = os.path.join(DIST_DIRECTORY, f"{DIST_NAME}-{version}-{dist_platform()}")
    return result


def add_version_file(built: str, version: str) -> None:
    """ version.txt con il numero della versione costruita (version=0.1.93): in cima alla cartella, dove si vede
    aprendo lo zip, e in _internal; vscode_deploy.py li legge tutti e due. Riscritto a ogni build. """
    for folder in (built, os.path.join(built, "_internal")):
        path = os.path.join(folder, vscode_deploy.VERSION_FILE)
        with open(path, "w", encoding="utf-8") as version_file:
            version_file.write(f"version={version}\n")


def write_version() -> str:
    """ scrive la versione di git in myeasymp3toiphone/_version.txt (la build non ha git); restituisce il numero """
    version = from_git()
    if version is None:
        raise RuntimeError("La versione viene da git: costruisci nel repository git, con git installato")
    VERSION_FILE.write_text(version + "\n", encoding="utf-8")
    result: str = version.split(" ", 1)[0]
    return result


def add_top_files(built: str) -> None:
    sources = []
    for name in TOP_FILES:
        sources.append(os.path.join(PROGRAM_DIRECTORY, name))
    for name in sorted(os.listdir(DIST_FILES_DIRECTORY)):
        if name not in INTERNAL_FILES:
            sources.append(os.path.join(DIST_FILES_DIRECTORY, name))
    for source in sources:
        shutil.copyfile(source, os.path.join(built, os.path.basename(source)))


def remove_old_archives(archive: str) -> None:
    """ cancella gli zip di dist tranne il nuovo e quello della build precedente """
    others = []
    for path in glob.glob(os.path.join(DIST_DIRECTORY, f"{DIST_NAME}-*.zip")):
        if os.path.normcase(os.path.abspath(path)) != os.path.normcase(os.path.abspath(archive)):
            others.append(path)
    others.sort(key=os.path.getmtime, reverse=True)
    for path in others[1:]:
        try:
            os.remove(path)
            print(f"Cancellata la build vecchia {os.path.basename(path)}")
        except OSError as e:
            print(f"La build vecchia {path} non si è potuta cancellare ({type(e).__name__}: {e}): cancellala a mano")


def selftest(built: str) -> None:
    """ la build carica tutte le sue librerie: altrimenti si ferma prima dello zip e dell'installazione """
    program = os.path.join(built, SELFTEST_PROGRAM)
    completed = subprocess.run([program, "--selftest"], capture_output=True, text=True, timeout=300)
    print(completed.stdout)
    if completed.returncode != 0:
        print(completed.stderr)
        raise RuntimeError(f"{SELFTEST_PROGRAM} --selftest non è riuscito: la build non viene installata")


def installed_libraries() -> str:
    """ Python e le librerie installate nell'ambiente, ognuna con la sua versione, in ordine """
    from importlib import metadata
    names = []
    for distribution in metadata.distributions():
        names.append(f"{distribution.metadata['Name']}=={distribution.version}")
    names.sort(key=str.lower)
    result: str = f"python {sys.version}\n" + "\n".join(names) + "\n"
    return result


def clean_reason(arguments: list, libraries: str) -> str:
    """ perché buttare la cache di PyInstaller: chiesto, prima build, o Python e le librerie cambiati; "" per riusarla """
    try:
        with open(LIBRARIES_FILE, encoding="utf-8") as libraries_file:
            previous = libraries_file.read()
    except OSError:
        previous = None
    if CLEAN_OPTION in arguments:
        result = f"chiesto con {CLEAN_OPTION}"
    elif previous is None:
        result = "nessuna build precedente con l'elenco delle librerie"
    elif previous != libraries:
        result = "Python o le librerie installate sono cambiati dall'ultima build"
    else:
        result = ""
    return result


def remember_libraries(libraries: str) -> None:
    """ dopo una build riuscita: l'elenco con cui confrontare la prossima """
    with open(LIBRARIES_FILE, "w", encoding="utf-8") as libraries_file:
        libraries_file.write(libraries)


def load_variables() -> None:
    """ MY_VSCODE_ZIP_DIR e MY_VSCODE_INSTALL_DIR anche dal file delle variabili della cartella dati """
    for warning in env_file.load(env_file.env_file_path(home_folder())):
        print(f"Avviso: {warning}")


def main() -> int:
    import PyInstaller.__main__
    load_variables()
    version = write_version()
    libraries = installed_libraries()
    reason = clean_reason(sys.argv[1:], libraries)
    options = [SPEC_FILE, "--noconfirm", "--distpath", DIST_DIRECTORY, "--workpath", WORK_DIRECTORY]
    if reason:
        print(f"Build da zero ({reason})")
        options.append(CLEAN_OPTION)
    else:
        print(f"Build con la cache di PyInstaller (librerie invariate; da zero: build_dist.py {CLEAN_OPTION})")
    PyInstaller.__main__.run(options)
    remember_libraries(libraries)
    built = os.path.join(DIST_DIRECTORY, DIST_NAME)
    add_top_files(built)
    add_version_file(built, version)
    selftest(built)
    archive = shutil.make_archive(archive_base(version), "zip", DIST_DIRECTORY, DIST_NAME)
    print(f"Costruiti {built} e {archive}")
    remove_old_archives(archive)
    vscode_deploy.deploy(archive)
    result: int = 0
    return result


if __name__ == "__main__":
    sys.exit(main())
