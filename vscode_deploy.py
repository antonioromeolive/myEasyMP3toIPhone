# ------------------------------------------------------------------------------
# File:          vscode_deploy.py
# Project:       myLocalChat
# Author:        Antonio Romeo
# Version:       2.0.76
# Last modified: 2026-11-07
# Copyright (c) 2024-2026 Antonio Romeo
# License:       MIT - see LICENSE.TXT in the project root
# SPDX-License-Identifier: MIT
# ------------------------------------------------------------------------------

"""
vscode_deploy.py - copies the zip of a build and installs it, for any project: copy this file as it is.

The zip must hold one top folder, the name of the project (shutil.make_archive(base, "zip", root_dir, "<name>")):
- the zip is copied to MY_VSCODE_ZIP_DIR/<name>;
- the build is installed in MY_VSCODE_INSTALL_DIR/<name>: the folder there is renamed <name>.previous, the zip unpacked
  (when that fails, the folder is put back: e.g. while the program runs);
- the version in <name>.previous must have its zip in MY_VSCODE_ZIP_DIR/<name>: when no zip has its version number
  (version.txt), one is made, named like the new one with that number; then the folder is deleted. Without a zip the
  folder stays, the next build tries again first; one that cannot be deleted is renamed <name>.previous.<version>.TODELETE
  for you to delete.
Each folder is created when missing; a variable not set = that step skipped, with a notice printed last.
Standard library only. Use:
    python vscode_deploy.py <zip>
or, from a build script:
    import vscode_deploy
    vscode_deploy.deploy(archive)
"""
import glob
import os
import shutil
import sys
import tempfile
import time
import zipfile

ZIP_DIR_ENV_VAR     = "MY_VSCODE_ZIP_DIR"       #the zip of each build is copied to the <name> folder of this folder
INSTALL_DIR_ENV_VAR = "MY_VSCODE_INSTALL_DIR"   #the build is installed in the <name> folder of this folder
PREVIOUS_SUFFIX     = ".previous"               #the replaced install folder, until its version has a zip
TODELETE_SUFFIX     = ".TODELETE"               #the end of the name of a replaced folder that could not be deleted
VERSION_FILE        = "version.txt"             #version=<number>, at the top of a build or in its _internal folder


def top_folder(archive: str) -> str:
    """ the name of the one top folder of the zip; ValueError when it holds files at the top or several folders """
    names = set()
    with zipfile.ZipFile(archive) as zipped:
        for entry in zipped.namelist():
            if "/" in entry:
                names.add(entry.split("/", 1)[0])
            else:
                names.add("")               #a file at the top level
    if len(names) != 1 or "" in names:
        raise ValueError(f"{archive} must hold one top folder (the name of the project), it holds: "
                         f"{', '.join(sorted(name or '<files>' for name in names))}")
    result: str = names.pop()
    return result


def copy_archive(archive: str, folder: str) -> bool:
    """ copies the zip file to the folder (created when missing): written under a temporary name, then renamed, so
    that a zip is never seen (or synced) half written; False when it failed """
    target = os.path.join(folder, os.path.basename(archive))
    temporary = target + ".tmp"
    result: bool = True
    try:
        os.makedirs(folder, exist_ok=True)
        shutil.copyfile(archive, temporary)
        os.replace(temporary, target)
        print(f"Copied to {target}")
    except OSError as e:
        if os.path.exists(temporary):
            os.remove(temporary)
        print(f"NOT copied to {target} ({type(e).__name__}: {e}): close the programs using it, then build again")
        result = False
    return result


def installed_version(target: str) -> str:
    """ the version in the version file of an installed folder (at its top or in _internal), "" when there is none """
    result: str = ""
    for folder in (target, os.path.join(target, "_internal")):
        path = os.path.join(folder, VERSION_FILE)
        if not result and os.path.isfile(path):
            with open(path, encoding="utf-8") as version_file:
                for line in version_file:
                    if line.startswith("version="):
                        result = line.strip().split("=", 1)[1]
    return result


def archive_version(archive: str, name: str) -> str:
    """ the version in the version file of a zip (in its top folder or in _internal), "" when there is none """
    result: str = ""
    with zipfile.ZipFile(archive) as zipped:
        names = zipped.namelist()
        for path in (f"{name}/{VERSION_FILE}", f"{name}/_internal/{VERSION_FILE}"):
            if not result and path in names:
                for line in zipped.read(path).decode("utf-8").splitlines():
                    if line.startswith("version="):
                        result = line.strip().split("=", 1)[1]
    return result


def has_files(folder: str) -> bool:
    """ a file anywhere in the folder """
    result: bool = False
    for _, _, file_names in os.walk(folder):
        if file_names:
            result = True
    return result


def zip_name_of(archive: str, name: str, label: str) -> str:
    """ the name of the zip of the version <label>: as the new zip, with its version number replaced (the rest of the
    name is the label of the git tag and the platform of the new build) """
    base = os.path.basename(archive)
    start = f"{name}-{archive_version(archive, name)}"
    rest = base[len(start):] if base.startswith(start) else ".zip"
    result: str = f"{name}-{label}{rest}"
    return result


def zips_of_version(folder: str, name: str, version: str) -> list[str]:
    """ the zips of exactly that version: named for it, and with its number in their version file (by the name alone
    the -*.zip of 0.1.52 also finds 0.1.52-dev-windows-x64.zip, another version); a zip that cannot be read is not one """
    result: list[str] = []
    if version:
        start = os.path.join(glob.escape(folder), glob.escape(f"{name}-{version}"))
        for path in glob.glob(start + "-*.zip") + glob.glob(start + ".zip"):
            try:
                if archive_version(path, name) == version:
                    result.append(path)
            except (OSError, UnicodeError, zipfile.BadZipFile) as e:
                print(f"{path} is not used as the zip of version {version}: it cannot be read ({type(e).__name__})")
    return result


def keep_previous(archive: str, previous: str, folder: str, name: str) -> bool:
    """ the version in the replaced folder is in the folder of the zips: a zip with its version number, or one is made
    (top folder = the name of the project, as a zip of a build) in a temporary folder and copied there. A folder with no
    file holds no version. False when it could not be kept: the replaced folder must stay """
    version = installed_version(previous)
    label = version or time.strftime("%Y%m%d-%H%M")
    found = zips_of_version(folder, name, version)
    result: bool = True
    if not found and has_files(previous):
        temporary = tempfile.mkdtemp()
        try:
            made = os.path.join(temporary, zip_name_of(archive, name, label))
            with zipfile.ZipFile(made, "w", compression=zipfile.ZIP_DEFLATED, strict_timestamps=False) as zipped:
                for current, _, file_names in os.walk(previous):
                    for file_name in file_names:
                        path = os.path.join(current, file_name)
                        zipped.write(path, os.path.join(name, os.path.relpath(path, previous)))
            result = copy_archive(made, folder)
        except (OSError, ValueError) as e:
            print(f"The zip of version {label} was NOT made ({type(e).__name__}: {e})")
            result = False
        finally:
            shutil.rmtree(temporary, ignore_errors=True)
    return result


def retire_previous(archive: str, previous: str, folder: str, name: str) -> None:
    """ the replaced folder is deleted once its version is kept (folder "" = no folder of the zips: nothing to keep it
    in). What cannot be deleted is renamed <name>.previous.<version>.TODELETE, for the user to see and delete: no longer
    a version, and the name is free for the next install. While it cannot be kept (the only copy) or renamed, it stays,
    named in a notice, and the next build tries again """
    kept: bool = True
    if folder:
        kept = keep_previous(archive, previous, folder, name)
    if kept:
        label = installed_version(previous) or time.strftime("%Y%m%d-%H%M")
        shutil.rmtree(previous, ignore_errors=True)
        if os.path.exists(previous):
            marked = f"{previous}.{label}{TODELETE_SUFFIX}"
            try:
                os.rename(previous, marked)
                print(f"The replaced version could not be deleted: delete {marked} by hand")
            except OSError as e:
                print(f"The replaced version could not be deleted or renamed ({type(e).__name__})")
    if os.path.exists(previous):
        print(f"{previous} stays: the next build tries again, or delete it by hand")


def install_archive(archive: str, target: str, previous: str) -> bool:
    """ installs the build in target (the zip holds one folder, the name of target, unpacked next to it): the installed
    folder is renamed to previous, the zip unpacked; when the unpacking fails, what it wrote is deleted and the folder is
    put back. The rename fails while the folder is in use: nothing is installed. False when not installed """
    renamed: bool = False
    result: bool = False
    if os.path.exists(previous):             #left by an earlier build and still there: it holds the name
        print(f"NOT installed in {target}: {previous} is in the way; the version there is unchanged; close the windows "
              "open in that folder or delete it by hand, then build again")
    else:
        try:
            if os.path.exists(target):
                os.rename(target, previous)
                renamed = True
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with zipfile.ZipFile(archive) as zipped:
                zipped.extractall(os.path.dirname(target))
            print(f"Installed in {target}")
            result = True
        except OSError as e:
            if renamed and os.path.exists(target):
                shutil.rmtree(target, ignore_errors=True)
            if renamed:
                os.rename(previous, target)
            print(f"NOT installed in {target} ({type(e).__name__}: {e}): the version there is unchanged; close the "
                  "program or the windows open in that folder, then build again")
    return result


def deploy_folder(variable: str) -> str:
    """ the folder of the variable, its %NAME% / $NAME expanded (a value written with %OneDrive% stays unexpanded in
    the environment: used as is it was a folder of the current directory); "" when not set or not absolute """
    folder = os.path.expandvars(os.environ.get(variable, "")).strip()
    if folder and not os.path.isabs(folder):
        print(f"{variable} is not an absolute folder after expanding its variables: write the full path (a variable "
              "it names must be defined)")
        folder = ""
    return folder


def deploy(archive: str) -> None:
    """ copies the zip to the <name> folder of MY_VSCODE_ZIP_DIR, installs it in the <name> folder of
    MY_VSCODE_INSTALL_DIR (<name> = the top folder of the zip), then keeps the version replaced in the folder of the zips
    (retire_previous); for each variable not set the step is skipped and a notice, at the end of the output, asks to
    define it """
    name = top_folder(archive)
    zip_dir = deploy_folder(ZIP_DIR_ENV_VAR)
    install_dir = deploy_folder(INSTALL_DIR_ENV_VAR)
    zips = os.path.join(zip_dir, name) if zip_dir else ""
    missing = []
    if zip_dir:
        copy_archive(archive, zips)
    else:
        missing.append(f"  {ZIP_DIR_ENV_VAR:<24} the folder of the {name} folder the zip is copied to"
                       f"  -> the zip was NOT copied, and the version replaced stays only in {name}{PREVIOUS_SUFFIX}"
                       " until the next build")
    if install_dir:
        target = os.path.join(install_dir, name)
        previous = target + PREVIOUS_SUFFIX
        if os.path.exists(previous):         #left by an earlier build
            retire_previous(archive, previous, zips, name)
        installed = install_archive(archive, target, previous)
        if installed and zips and os.path.exists(previous):
            retire_previous(archive, previous, zips, name)
    else:
        missing.append(f"  {INSTALL_DIR_ENV_VAR:<24} the folder the {name} folder is installed in"
                       "  -> the build was NOT installed")
    if missing:
        line = "=" * 100
        print("\n".join([line, "PLEASE DEFINE THESE ENVIRONMENT VARIABLES (then build again):", *missing,
                         f"The build itself is complete: {archive}", line]))


def main() -> int:
    if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
        deploy(sys.argv[1])
        result: int = 0
    else:
        print("Use: python vscode_deploy.py <zip of the build>")
        result = 2
    return result


if __name__ == "__main__":
    sys.exit(main())
