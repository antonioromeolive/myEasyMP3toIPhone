# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La linguetta Controlli: Controlla la musica (F6) e Verifica album online (F7) affiancati, ognuno con le sue scelte
e il suo pulsante per partire, e sotto i risultati dell'ultimo controllo e dell'ultima verifica (prima erano finestre
a parte). Le scelte si rifanno ogni volta che la linguetta si vede: dipendono da cosa è aperto."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSplitter, QTabWidget, QVBoxLayout, QWidget

from .album_check_dialog import AlbumCheckOptionsDialog
from .scan_dialog import ScanTargetDialog

SCAN_PAGE, ALBUM_PAGE = 0, 1


def _card(title: str, key: str, subtitle: str, content: QWidget) -> QFrame:
    """Un riquadro con il titolo (e il tasto), una riga di spiegazione e il contenuto."""
    card = QFrame()
    card.setObjectName("checkCard")
    heading = QLabel(f"{title}  <span style='color: gray; font-weight: normal'>{key}</span>")
    heading.setObjectName("cardTitle")
    heading.setTextFormat(Qt.RichText)
    note = QLabel(subtitle)
    note.setObjectName("deviceInfo")
    note.setWordWrap(True)
    layout = QVBoxLayout(card)
    layout.addWidget(heading)
    layout.addWidget(note)
    layout.addWidget(content, 1)
    return card


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
        launcher = window.scan_launcher
        settings = window.app_settings
        self.scan_options = ScanTargetDialog(window, len(window.phone_tracks), launcher.profile_name(), embedded=True)
        self.scan_options.start_requested.connect(lambda: launcher.run(self.scan_options))
        self.album_options = AlbumCheckOptionsDialog(self, 0, list(settings.album_services), settings.album_ai,
                                                     launcher.profile_name(), window.album_discogs_ready(),
                                                     embedded=True)
        self.album_options.start_requested.connect(window.start_album_check_from_panel)
        self.album_options.stop_button.clicked.connect(window._stop_album_check)
        cards = QWidget()
        row = QHBoxLayout(cards)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(_card("Controlla la musica", "F6", "Confronta i tuoi brani tra loro (e con l'iPhone), senza "
                            "cataloghi online: doppioni, artisti scritti in modi diversi, album divisi, tag mancanti.",
                            self.scan_options), 1)
        row.addWidget(_card("Verifica album online", "F7", "Confronta gli album con i cataloghi su internet: brani "
                            "mancanti, tag giusti, copertina. In background.", self.album_options), 1)
        self.results = QTabWidget()
        self.results.addTab(_placeholder("Qui compaiono i risultati di Controlla la musica."), "Risultati del controllo")
        self.results.addTab(_placeholder("Qui compaiono i risultati di Verifica album online, alla fine o quando la fermi."),
                            "Risultati della verifica")
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(cards)
        splitter.addWidget(self.results)
        splitter.setSizes([430, 420])
        splitter.setStretchFactor(1, 1)
        layout = QVBoxLayout(self)
        layout.addWidget(splitter, 1)

    def refresh(self) -> None:
        """Le scelte che dipendono da cosa è aperto: brani, musica dell'iPhone, album scelti, profilo AI."""
        window = self._window
        name = window.scan_launcher.profile_name()
        self.scan_options.refresh(window, len(window.phone_tracks), name)
        self.album_options.refresh(len(window.albums_to_check()), name, window.app_settings.album_ai)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh()

    def _replace_page(self, index: int, widget: QWidget, title: str) -> None:
        old = self.results.widget(index)
        self.results.removeTab(index)
        self.results.insertTab(index, widget, title)
        if old is not None:
            old.deleteLater()
        self.results.setCurrentIndex(index)

    def show_scan_results(self, widget: QWidget) -> None:
        self._replace_page(SCAN_PAGE, widget, "Risultati del controllo")
        self._window.show_checks()

    def show_album_results(self, widget: QWidget) -> None:
        self._replace_page(ALBUM_PAGE, widget, "Risultati della verifica")

    def album_state(self, running: bool, text: str) -> None:
        self.album_options.set_running(running, text)

    def focus_scan(self) -> None:
        self.scan_options.start_button.setFocus()

    def focus_album(self) -> None:
        self.album_options.start_button.setFocus()
