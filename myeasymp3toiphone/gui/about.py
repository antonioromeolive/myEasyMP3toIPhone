# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La finestra Informazioni: versione, autore, cartella dati, file delle variabili, il valore usato per ogni variabile
d'ambiente e da dove viene (file o sistema), e dove è salvata la chiave di ogni profilo AI: mai una chiave."""

from __future__ import annotations

from html import escape

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFrame, QTextBrowser, QVBoxLayout, QWidget

from .. import env_file, environment
from ..config import PRODUCT, home_folder
from ..version import app_version

AUTHOR = "Antonio Romeo"
CREDIT = "with Claude Code et al."
LICENSE = "MIT License"


def about_html() -> str:
    rows = ""
    for name, value in environment.value_rows():
        where = env_file.source(name)
        origin = f" <i>({where})</i>" if where else ""
        rows += f"<tr><td><code>{escape(name)}</code></td><td>&nbsp;&nbsp;{escape(value)}{origin}</td></tr>"
    keys = ""
    for name, where in environment.key_rows():
        keys += f"<tr><td>{escape(name)}</td><td>&nbsp;&nbsp;{escape(where)}</td></tr>"
    if keys:
        keys = f"<p><b>Le chiavi API dei profili AI</b>: dove è salvata ciascuna, mai la chiave.</p><table>{keys}</table>"
    variables_file = env_file.env_file_path(home_folder())
    result = (f"<h3>{PRODUCT}</h3>"
              f"<p>Versione {escape(app_version())}</p>"
              f"<p>Autore: <b>{AUTHOR}</b> ({CREDIT})<br>{LICENSE}</p>"
              f"<p>Cartella dati: <code>{escape(str(home_folder()))}</code><br>"
              f"File delle variabili: <code>{escape(str(variables_file))}</code></p>"
              f"<p><b>Variabili d'ambiente</b> e valore usato: <i>(file)</i> = scritto nel file delle variabili, "
              f"<i>(sistema)</i> = dalle variabili di Windows. Riavvia il programma dopo averne cambiata una.</p>"
              f"<table>{rows}</table>{keys}")
    return result


class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Informazioni su {PRODUCT}")
        self.text = QTextBrowser()
        self.text.setHtml(about_html())
        self.text.setOpenExternalLinks(True)
        self.text.setFrameShape(QFrame.NoFrame)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addWidget(buttons)
        self.resize(680, 560)
