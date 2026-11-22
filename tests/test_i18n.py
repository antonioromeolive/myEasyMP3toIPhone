# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""L'interfaccia in inglese: catalogo completo, traduzioni dei testi composti, finestra vera in un processo a parte
(gli agganci a Qt cambiano le classi di PySide6 del processo). Cartella dati temporanea."""

import importlib.util
import subprocess
import sys
from pathlib import Path

from myeasymp3toiphone import i18n

ROOT = Path(__file__).resolve().parent.parent

WINDOW_CODE = """
from myeasymp3toiphone import i18n
i18n.set_language("en")
i18n.install_qt_hooks()
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication
app = QApplication([])
from myeasymp3toiphone.gui.main_window import MainWindow
window = MainWindow()
window._startup = lambda: None
texts = sorted({action.text() for action in window.findChildren(QAction)})
print("|".join(texts))
print(window._tabs.tabText(0), "/", window.iphone_panel._connect_button.text(), "/", window._search.placeholderText())
print(window._model.headerData(2, Qt.Horizontal))
"""


def test_every_text_of_the_code_has_an_english_translation():
    spec = importlib.util.spec_from_file_location("i18n_catalog", ROOT / "tools" / "i18n_catalog.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.missing() == []          # un testo nuovo: aggiungilo a myeasymp3toiphone/i18n_en.py


def test_translations():
    try:
        i18n.set_language("it")
        assert i18n.tr("Annulla") == "Annulla"
        i18n.set_language("en")
        assert i18n.tr("Annulla") == "Cancel"
        assert i18n.tr("Sorgente associata a 12 brani") == "Source linked to 12 tracks"
        assert i18n.tr("Il brano ha già una sorgente:\nC:/a.mp3\n\nSostituirla con:\nC:/b.mp3?") == \
            "The track already has a source:\nC:/a.mp3\n\nReplace it with:\nC:/b.mp3?"
        assert i18n.tr("Rimpiazza\n\nNon premere mai \"Sincronizza\" in iTunes o in Dispositivi Apple: con la musica "
                       "messa da un altro programma, iTunes la toglierebbe dall'iPhone.").startswith("Replace\n\nNever")
        assert i18n.tr("<b>3</b> brani dell'iPhone ritrovati sul PC con l'impronta dell'audio: si associano alla loro "
                       "sorgente senza chiedere.").startswith("<b>3</b> iPhone tracks found")
        assert i18n.tr("Caruso") == "Caruso"                  # un dato resta com'è
        assert i18n.tr_exact("questo PC") == "this PC" and i18n.tr_exact("Rossi — Disco") == "Rossi — Disco"
        assert "in English" in i18n.prompt("Write the reason in Italian.")
    finally:
        i18n.set_language("it")


def test_english_window(tmp_path, monkeypatch):
    monkeypatch.setenv("MYEASYMP3TOIPHONE_HOME", str(tmp_path))
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("PYTHONIOENCODING", "utf-8")
    output = subprocess.run([sys.executable, "-c", WINDOW_CODE], cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", timeout=120)
    assert output.returncode == 0, output.stderr[-2000:]
    lines = output.stdout.splitlines()
    assert "Check the music" in lines[0] and "Open folder" in lines[0] and "Controlla la musica" not in lines[0]
    assert lines[1] == "PC / Connect iPhone / Search by title, artist or album…"
    assert lines[2] == "Title"
