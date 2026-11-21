# -*- mode: python ; coding: utf-8 -*-
# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)
#
# Build PyInstaller della distribuzione: si esegue con  python build_dist.py  (scrive myeasymp3toiphone/_version.txt).
# Una cartella, dist/myEasyMP3toIPhone, con due programmi che condividono la cartella _internal:
#   myEasyMP3toIPhone       la finestra
#   myEasyMP3toIPhone-cli   la console: --env, --scan, --version, --selftest
# Accanto, da dist_files (build_dist.py): READ ME FIRST.txt e i due script dei collegamenti, che eseguono
# _internal/shortcuts.ps1.
import os

from PyInstaller.utils.win32.versioninfo import (FixedFileInfo, StringFileInfo, StringStruct, StringTable,
                                                 VarFileInfo, VarStruct, VSVersionInfo)

from myeasymp3toiphone.version import VERSION_FILE, file_version

PACKAGE = os.path.join(SPECPATH, "myeasymp3toiphone")
# Letti come file dal programma: il modello del file delle variabili e la versione mostrata (la build non ha git)
DATAS = []
for name in ("myEasyMP3toIPhone.TEMPLATE.env", "_version.txt"):
    DATAS.append((os.path.join(PACKAGE, name), "myeasymp3toiphone"))
DATAS.append((os.path.join(SPECPATH, "dist_files", "shortcuts.ps1"), "."))   # eseguito dagli script dei collegamenti
# L'SDK anthropic e pymobiledevice3 caricano alcuni moduli per nome: inclusi tutti quelli che il programma usa
HIDDEN = ["keyring.backends.Windows", "pymobiledevice3.services.afc", "pymobiledevice3.services.house_arrest",
          "pymobiledevice3.services.installation_proxy", "win32com", "win32com.client", "win32com.client.gencache",
          "pythoncom", "pywintypes"]   # iTunes (COM)
EXCLUDES = ["tkinter", "setuptools", "pkg_resources", "_distutils_hack", "pytest", "_pytest", "IPython",
            "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtPdf", "PySide6.Qt3DCore",
            "PySide6.QtQuick", "PySide6.QtQml"]
# File di Qt che il programma non usa (~27 MB): il renderer OpenGL software e le traduzioni di Qt
UNUSED_QT_FILES = ("opengl32sw.dll",)
UNUSED_QT_FOLDERS = (os.path.join("PySide6", "translations") + os.sep,)
ICON = os.path.join(SPECPATH, "icons", "myEasyMP3toIPhone.ico")
VERSION = VERSION_FILE.read_text(encoding="utf-8").strip()
COMPANY = "Antonio Romeo"
COPYRIGHT = "Copyright (c) 2026 Antonio Romeo"
PRODUCT = "myEasyMP3toIPhone"

# il programma -> (il suo script, console, la sua descrizione)
PROGRAMS = {
    "myEasyMP3toIPhone": ("myEasyMP3toIPhone.py", False, "myEasyMP3toIPhone - musica e iPhone"),
    "myEasyMP3toIPhone-cli": ("myEasyMP3toIPhone-cli.py", True, "myEasyMP3toIPhone (console)"),
}


def version_info(name, description):
    numbers = file_version(VERSION)
    strings = [StringStruct("CompanyName", COMPANY), StringStruct("FileDescription", description),
               StringStruct("FileVersion", ".".join(str(n) for n in numbers)), StringStruct("InternalName", name),
               StringStruct("LegalCopyright", COPYRIGHT), StringStruct("OriginalFilename", f"{name}.exe"),
               StringStruct("ProductName", PRODUCT), StringStruct("ProductVersion", VERSION.split(" ", 1)[0])]
    result = VSVersionInfo(ffi=FixedFileInfo(filevers=numbers, prodvers=numbers),
                           kids=[StringFileInfo([StringTable("041004B0", strings)]),   # italiano, Unicode
                                 VarFileInfo([VarStruct("Translation", [0x0410, 1200])])])
    return result


def program(analysis, pyz, name):
    """ il programma: bootstrap e hook dell'analisi, poi solo il suo script """
    script, console, description = PROGRAMS[name]
    scripts = []
    for entry in analysis.scripts:
        if entry[0] == name or entry[0] not in PROGRAMS:
            scripts.append(entry)
    result = EXE(pyz, scripts, exclude_binaries=True, name=name, console=console, icon=ICON,
                 version=version_info(name, description), upx=False)
    return result


def used(entries):
    result = []
    for entry in entries:
        dest = os.path.normpath(entry[0])
        if os.path.basename(dest) not in UNUSED_QT_FILES and not dest.startswith(UNUSED_QT_FOLDERS):
            result.append(entry)
    return result


SCRIPTS = []
for script, console, description in PROGRAMS.values():
    SCRIPTS.append(os.path.join(SPECPATH, "programs", script))
analysis = Analysis(SCRIPTS, pathex=[SPECPATH], datas=DATAS, hiddenimports=HIDDEN, excludes=EXCLUDES)
pyz = PYZ(analysis.pure)

EXECUTABLES = []
for name in PROGRAMS:
    EXECUTABLES.append(program(analysis, pyz, name))
COLLECT(*EXECUTABLES, used(analysis.binaries), used(analysis.datas), name="myEasyMP3toIPhone", upx=False)
