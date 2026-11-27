# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La linguetta Controlli: in alto le scelte (su cosa, cosa controllare: le regole, l'Analisi AI, la Verifica online;
check_options), sotto i risultati dell'ultimo controllo, per album (check_results). F6 e F7 la aprono; le scelte si
rifanno ogni volta che la linguetta si vede: dipendono da cosa è scelto nelle schede PC e iPhone."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QSplitter, QVBoxLayout, QWidget

from .check_options import CheckOptions
from .icons import icon


def _placeholder(text: str) -> QLabel:
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)
    label.setWordWrap(True)
    label.setObjectName("deviceInfo")
    return label


class ChecksPanel(QWidget):
    def __init__(self, window) -> None:
        super().__init__(window)
        self._window = window
        self.options = CheckOptions(window)
        self.options.start_requested.connect(lambda: window.scan_launcher.run())
        self.options.start_button.setIcon(icon("play", "white"))
        card = QFrame()
        card.setObjectName("checkCard")
        heading = QLabel("Controlla la musica  <span style='color: gray; font-weight: normal'>F6</span>")
        heading.setObjectName("cardTitle")
        heading.setTextFormat(Qt.RichText)
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(heading)
        card_layout.addWidget(self.options, 1)
        self.results = _placeholder("Qui compaiono i risultati del controllo, per album: i problemi, cosa fare e le "
                                    "correzioni da applicare.")
        self._splitter = QSplitter(Qt.Vertical)
        self._splitter.addWidget(card)
        self._splitter.addWidget(self.results)
        self._splitter.setSizes([400, 450])
        self._splitter.setStretchFactor(1, 1)
        layout = QVBoxLayout(self)
        layout.addWidget(self._splitter, 1)

    def refresh(self) -> None:
        """Le scelte che dipendono da cosa è aperto e scelto nelle schede."""
        self.options.refresh()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh()

    def show_results(self, widget: QWidget) -> None:
        """I risultati nuovi al posto di quelli di prima."""
        old = self.results
        self._splitter.replaceWidget(1, widget)
        self.results = widget
        old.deleteLater()
        self._window.show_checks()

    def focus_scan(self) -> None:
        self.options.start_button.setFocus()
