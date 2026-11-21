# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Ogni test usa una cartella dati temporanea e un credential store finto in memoria: mai la cartella dati vera, mai
le chiavi vere. Nomi e valori dei test sono inventati."""

import os
import struct

import keyring
import pytest
from keyring.backend import KeyringBackend


class MemoryKeyring(KeyringBackend):
    priority = 1

    def __init__(self):
        super().__init__()
        self.store = {}

    def get_password(self, service, username):
        result = self.store.get((service, username))
        return result

    def set_password(self, service, username, password):
        self.store[(service, username)] = password

    def delete_password(self, service, username):
        self.store.pop((service, username), None)


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("MYEASYMP3TOIPHONE_HOME", str(home))
    monkeypatch.setenv("MYCALIBRETOOLS_HOME", str(tmp_path / "calibre_tools"))
    for name in list(os.environ):
        if name.startswith(("MY_TEST_", "OLLAMA_", "ANTHROPIC_", "OPENAI_", "AZURE_OPENAI_", "AZURE_FOUNDRY_")) or name == \
                "MYEASYMP3TOIPHONE_LOG_LEVEL":
            monkeypatch.delenv(name, raising=False)
    memory = MemoryKeyring()
    previous = keyring.get_keyring()
    keyring.set_keyring(memory)
    from myeasymp3toiphone import ai, env_file
    env_file._from_file.clear()
    monkeypatch.setattr(ai, "local_ollama_models", lambda *args, **kwargs: [])  # niente rete nei test
    # mai l'iPhone vero: la finestra controlla ogni pochi secondi se ne è collegato uno e si collegherebbe
    from myeasymp3toiphone import iphone
    monkeypatch.setattr(iphone, "device_present", lambda: False)
    # mai una finestra di messaggio che aspetta un clic (senza schermo bloccherebbe i test)
    from PySide6.QtWidgets import QMessageBox
    for kind in ("warning", "information", "question", "critical"):
        monkeypatch.setattr(QMessageBox, kind, staticmethod(lambda *args, **kwargs: QMessageBox.Yes))
    yield memory
    keyring.set_keyring(previous)
    env_file._from_file.clear()


def write_mp3(path, frames: int = 40) -> None:
    """Un MP3 minimo valido: frame MPEG1 Layer III 128 kbit/s 44,1 kHz vuoti."""
    frame = b"\xff\xfb\x90\x64" + b"\x00" * 413
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(frame * frames)


def write_flac(path) -> None:
    info = struct.pack(">HH", 4096, 4096) + b"\x00\x00\x00" * 2
    packed = (44100 << 44) | (1 << 41) | (15 << 36) | (44100 * 2)
    info += packed.to_bytes(8, "big") + b"\x00" * 16
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"fLaC" + bytes([0x80]) + len(info).to_bytes(3, "big") + info)
