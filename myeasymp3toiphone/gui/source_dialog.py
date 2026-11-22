# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Associa sorgente: il file del PC da cui viene un brano dell'iPhone.

SourceDialog: un brano; i file possibili in una tabella, il più probabile per primo (adoption.rank_sources), oppure
un file qualsiasi. Più brani: Associa sorgenti (adoption_dialog).
Si scrive solo il registro della provenienza: né i brani dell'iPhone né i file del PC cambiano."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QFileDialog, QHeaderView, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)

from .. import provenance
from ..i18n import tr
from ..tags import AUDIO_EXTENSIONS

HOW_TEXT = {provenance.HOW_RULES: "regole", provenance.HOW_AI: "AI", provenance.HOW_FINGERPRINT: "impronta",
            provenance.HOW_MANUAL: "a mano", provenance.HOW_SENT: "inviato", provenance.HOW_SAVED: "salvato"}
NOTE = "Si scrive solo il registro della provenienza: né i brani dell'iPhone né i file del PC cambiano."


def _duration(seconds: float) -> str:
    total = int(round(seconds))
    result = f"{total // 60}:{total % 60:02d}"
    return result


def _phone_text(item) -> str:
    tags = item.tags
    result = f"{tags.artist or tags.album_artist} — {tags.title}  ({tags.album}, {_duration(item.length)})"
    return result


def _note_label() -> QLabel:
    result = QLabel(NOTE)
    result.setWordWrap(True)
    result.setStyleSheet("color: gray")
    return result


def _table(headers: list, widths: list) -> QTreeWidget:
    result = QTreeWidget()
    result.setHeaderLabels(headers)
    result.setRootIsDecorated(False)
    result.setAlternatingRowColors(True)
    for column, width in enumerate(widths):
        result.setColumnWidth(column, width)
    result.header().setStretchLastSection(True)
    result.header().setSectionResizeMode(QHeaderView.Interactive)
    return result


def choose_audio_file(parent, start: str = "") -> Optional[Path]:
    patterns = " ".join(f"*{extension}" for extension in sorted(AUDIO_EXTENSIONS))
    path, _filter = QFileDialog.getOpenFileName(parent, "Il file del PC", start, f"Audio ({patterns})")
    result = Path(path) if path else None
    return result


class SourceDialog(QDialog):
    """chosen: il file scelto; how: come (quello della proposta se è la prima, consigliata; "a mano" altrimenti)."""

    def __init__(self, parent, phone_track, proposals: list, current=None, queue_left: int = 0) -> None:
        super().__init__(parent)
        self.setWindowTitle("Associa sorgente")
        self.resize(1200, 460)
        self.chosen: Optional[Path] = None
        self.how = provenance.HOW_MANUAL
        self.skipped = False
        text = f"<b>{_phone_text(phone_track)}</b>"
        if current is not None:
            where = current.path if current.here else f"{current.path} (sul computer {current.pc})"
            text += (f"<br>Sorgente attuale: {where} — {HOW_TEXT.get(current.how, current.how)}. "
                     "Scegliendo un altro file la sostituisci.")
        text += "<br>Scegli il file del PC da cui viene questo brano (il primo è il più probabile):"
        header = QLabel(text)
        header.setTextFormat(Qt.RichText)
        header.setWordWrap(True)
        self.table = _table(["Titolo", "Artista", "Album", "Durata", "Percorso", "Perché"],
                            [220, 170, 190, 55, 330])
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._proposals = proposals
        bold = QFont()
        bold.setBold(True)
        for index, proposal in enumerate(proposals):
            track = proposal.pc
            tags = track.tags
            reason = proposal.reason
            if index == 0:
                reason = "consigliato — " + reason
            row = QTreeWidgetItem([tags.title or track.path.stem, tags.artist or tags.album_artist, tags.album,
                                   _duration(track.length), str(track.path), tr(reason)])
            row.setData(0, Qt.UserRole, index)
            row.setToolTip(4, str(track.path))
            row.setToolTip(5, reason)
            if index == 0:
                for column in range(6):
                    row.setFont(column, bold)
            self.table.addTopLevelItem(row)
        if proposals:
            self.table.setCurrentItem(self.table.topLevelItem(0))
        else:
            empty = QTreeWidgetItem([tr("Nessun file simile nella cartella aperta: scegli un file con il pulsante qui "
                                     "sotto.")])
            empty.setFlags(Qt.NoItemFlags)
            self.table.addTopLevelItem(empty)
        self.table.itemDoubleClicked.connect(lambda _row, _column: self._accept_current())
        other = QPushButton("Scegli un altro file…")
        other.clicked.connect(self._choose_file)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Associa")
        buttons.button(QDialogButtonBox.Ok).setEnabled(bool(proposals))
        buttons.button(QDialogButtonBox.Cancel).setText("Annulla")
        buttons.accepted.connect(self._accept_current)
        buttons.rejected.connect(self.reject)
        if queue_left:
            skip = buttons.addButton(f"Salta (ne restano {queue_left})", QDialogButtonBox.ActionRole)
            skip.clicked.connect(self._skip)
        layout = QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(self.table, 1)
        layout.addWidget(other, 0, Qt.AlignLeft)
        layout.addWidget(_note_label())
        layout.addWidget(buttons)

    def _accept_current(self) -> None:
        row = self.table.currentItem()
        index = row.data(0, Qt.UserRole) if row is not None else None
        if index is not None:
            proposal = self._proposals[index]
            self.chosen = Path(proposal.pc.path)
            self.how = proposal.how if index == 0 else provenance.HOW_MANUAL
            self.accept()

    def _choose_file(self) -> None:
        start = ""
        if self._proposals:
            start = str(Path(self._proposals[0].pc.path).parent)
        path = choose_audio_file(self, start)
        if path is not None:
            self.chosen = path
            self.how = provenance.HOW_MANUAL
            self.accept()

    def _skip(self) -> None:
        self.skipped = True
        self.reject()
