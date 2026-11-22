# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La conferma di Associa sorgenti: i brani dell'iPhone associati alla loro sorgente con l'impronta (certi) e le
proposte delle regole e dell'AI, da spuntare. Associa scrive il registro della provenienza; Annulla non cambia
niente."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout,
)

from .. import provenance
from ..i18n import tr

HOW_TEXT = {provenance.HOW_RULES: "regole", provenance.HOW_AI: "AI", provenance.HOW_FINGERPRINT: "impronta"}


def _phone_text(item) -> str:
    tags = item.tags
    result = f"{tags.artist or tags.album_artist} — {tags.title}  ({tags.album})"
    return result


def summary_text(outcome) -> str:
    lines = [f"<b>{len(outcome.certain)}</b> brani dell'iPhone ritrovati sul PC con l'impronta dell'audio: si "
             "associano alla loro sorgente senza chiedere."]
    if outcome.proposals:
        checked = sum(1 for proposal in outcome.proposals if proposal.checked)
        lines.append(f"<b>{len(outcome.proposals)}</b> proposte da controllare ({checked} già spuntate perché quasi "
                     "certe).")
    if outcome.foreign:
        lines.append(f"<b>{len(outcome.foreign)}</b> brani senza un file sul PC: restano <i>senza sorgente</i>, il "
                     "programma non li tocca.")
    if outcome.already:
        lines.append(f"{outcome.already} brani avevano già la sorgente.")
    if outcome.not_from_computer:
        lines.append(f"{outcome.not_from_computer} brani acquistati o scaricati sul telefono: non hanno una "
                     "sorgente.")
    for error in outcome.ai_errors[:2]:
        lines.append(f"<span style='color:#c33'>AI non riuscita: {error}</span>")
    result = "<br>".join(lines)
    return result


class AdoptionDialog(QDialog):
    def __init__(self, parent, outcome) -> None:
        super().__init__(parent)
        self.setWindowTitle("Associa sorgenti: i file del PC dei brani dell'iPhone")
        self.resize(1250, 640)
        self.outcome = outcome
        header = QLabel(summary_text(outcome))
        header.setWordWrap(True)
        header.setTextFormat(Qt.RichText)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Brano sull'iPhone", "File sul PC", "Come", "Perché"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.NoSelection)
        widths = [380, 420, 70]
        for column, width in enumerate(widths):
            self.tree.setColumnWidth(column, width)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(QHeaderView.Interactive)
        self._rows = []
        for proposal in outcome.proposals:
            row = QTreeWidgetItem([_phone_text(proposal.phone), str(proposal.pc.path),
                                   HOW_TEXT.get(proposal.how, proposal.how), tr(proposal.reason)])
            row.setFlags(row.flags() | Qt.ItemIsUserCheckable)
            row.setCheckState(0, Qt.Checked if proposal.checked else Qt.Unchecked)
            row.setToolTip(1, str(proposal.pc.path))
            row.setToolTip(3, proposal.reason)
            self.tree.addTopLevelItem(row)
            self._rows.append((row, proposal))
        self.tree.setVisible(bool(outcome.proposals))

        check_all = QPushButton("Spunta tutte")
        check_all.clicked.connect(lambda: self._set_all(Qt.Checked))
        check_none = QPushButton("Togli tutte")
        check_none.clicked.connect(lambda: self._set_all(Qt.Unchecked))
        tools = QHBoxLayout()
        tools.addWidget(check_all)
        tools.addWidget(check_none)
        tools.addStretch(1)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Associa")
        buttons.button(QDialogButtonBox.Cancel).setText("Annulla")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        note = QLabel("Associare scrive solo il registro della provenienza (sul PC e sull'iPhone): né i brani "
                      "dell'iPhone né i file del PC cambiano.")
        note.setWordWrap(True)
        note.setStyleSheet("color: gray")

        layout = QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(self.tree, 1)
        if outcome.proposals:
            layout.addLayout(tools)
        layout.addWidget(note)
        layout.addWidget(buttons)

    def _set_all(self, state) -> None:
        for row, _proposal in self._rows:
            row.setCheckState(0, state)

    def chosen(self) -> list:
        """Le proposte da collegare: tutte quelle con l'impronta e quelle spuntate."""
        result = list(self.outcome.certain)
        for row, proposal in self._rows:
            if row.checkState(0) == Qt.Checked:
                result.append(proposal)
        return result
