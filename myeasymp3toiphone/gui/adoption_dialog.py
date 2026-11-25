# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Associa sorgenti, in una finestra sola per tutti i brani senza sorgente o per quelli scelti.

AdoptOptionsDialog: quali brani (tutti quelli senza sorgente o i selezionati), dove cercare (una cartella con le
sottocartelle, o tutta la Libreria) e con quali metodi oltre al nome della cartella (impronta dell'audio, AI).
AdoptionDialog: il risultato, con la certezza di ogni proposta e le spunte; si può scegliere un altro file per una
riga, e i brani non trovati si possono associare dopo uno alla volta. Associa scrive il registro della provenienza;
un brano senza spunta resta com'è; Annulla non cambia niente."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QButtonGroup, QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QPushButton, QRadioButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)

from .. import adoption, provenance
from ..i18n import tr
from ..library import load_track
from .source_dialog import choose_audio_file

HOW_TEXT = {provenance.HOW_RULES: "regole", provenance.HOW_AI: "AI", provenance.HOW_FINGERPRINT: "impronta",
            provenance.HOW_FOLDER: "cartella", provenance.HOW_MANUAL: "a mano"}
LEVEL_COLOR = {adoption.LEVEL_CERTAIN: QColor(30, 140, 60), adoption.LEVEL_VERY_LIKELY: QColor(30, 140, 60),
               adoption.LEVEL_LIKELY: QColor(40, 110, 230), adoption.LEVEL_CHECK: QColor(220, 140, 0),
               adoption.LEVEL_MANUAL: QColor(40, 110, 230)}
MISSING_COLOR = QColor(255, 120, 120, 70)
SECONDS_PER_PHONE_PRINT = 0.25


def _duration(seconds: float) -> str:
    total = int(round(seconds))
    result = f"{total // 60}:{total % 60:02d}"
    return result


def _phone_text(item) -> str:
    tags = item.tags
    result = f"{tags.artist or tags.album_artist} — {tags.title}  ({tags.album}, {_duration(item.length)})"
    return result


class AdoptOptionsDialog(QDialog):
    """Le scelte prima di cercare: scope ("tutti" o "selezionati"), folders() le cartelle (una scelta, o tutte le
    cartelle della musica di questo PC), use_fingerprint, use_ai."""

    def __init__(self, parent, unknown: int, selected: int, start: Path, music: list, to_read: int,
                 connected: bool, ai_name: str) -> None:
        super().__init__(parent)
        self.setWindowTitle("Associa sorgenti")
        self.resize(720, 380)
        self._music = list(music)
        self.all_button = QRadioButton(f"Tutti i brani senza sorgente ({unknown})")
        self.selected_button = QRadioButton(f"I brani selezionati ({selected}), anche con una sorgente")
        self.selected_button.setEnabled(selected > 0)
        group = QButtonGroup(self)
        group.addButton(self.all_button)
        group.addButton(self.selected_button)
        if selected > 0:
            self.selected_button.setChecked(True)
        else:
            self.all_button.setChecked(True)
        scope = QVBoxLayout()
        scope.addWidget(self.all_button)
        scope.addWidget(self.selected_button)

        self.folder_edit = QLineEdit(str(start))
        browse = QPushButton("Sfoglia…")
        browse.clicked.connect(self._browse)
        self.library_box = QCheckBox(f"Tutte le cartelle della musica di questo PC ({len(self._music)})")
        self.library_box.setToolTip("\n".join(str(folder) for folder in self._music))
        self.library_box.toggled.connect(self._library_toggled)
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder_edit, 1)
        folder_row.addWidget(browse)
        self._browse_button = browse
        where = QVBoxLayout()
        where.addLayout(folder_row)
        where.addWidget(self.library_box)

        folder_method = QCheckBox("Nome della cartella, titolo, numero e durata (veloce: non legge l'audio)")
        folder_method.setChecked(True)
        folder_method.setEnabled(False)
        minutes = max(1, round(to_read * SECONDS_PER_PHONE_PRINT / 60)) if to_read else 0
        if to_read and connected:
            print_text = (f"Al più {to_read} impronte da leggere dall'iPhone: circa {minutes} minuti; quelle lette si "
                          "ricordano")
        elif to_read:
            print_text = "Solo le impronte già lette: l'iPhone non è connesso"
        else:
            print_text = "Già lette tutte: veloce"
        self.fingerprint_box = QCheckBox("Impronta dell'audio, per i brani non trovati dal nome della cartella")
        self.fingerprint_box.setChecked(True)
        print_note = QLabel(print_text)
        print_note.setWordWrap(True)
        print_note.setStyleSheet("color: gray; margin-left: 22px;")
        self.ai_box = QCheckBox(f"AI per i dubbi ({ai_name})" if ai_name else
                                "AI per i dubbi (scegli l'AI della scansione in Impostazioni)")
        self.ai_box.setChecked(bool(ai_name))
        self.ai_box.setEnabled(bool(ai_name))
        methods = QVBoxLayout()
        methods.addWidget(folder_method)
        methods.addWidget(self.fingerprint_box)
        methods.addWidget(print_note)
        methods.addWidget(self.ai_box)

        form = QFormLayout()
        form.addRow("Brani", scope)
        form.addRow("Dove cercare (con le sottocartelle)", where)
        form.addRow("Come, in ordine", methods)
        note = QLabel("Alla fine vedi tutte le proposte, con la loro certezza e le spunte, prima di associare. Un "
                      "brano senza spunta resta com'è; né i brani dell'iPhone né i file del PC cambiano.")
        note.setWordWrap(True)
        note.setStyleSheet("color: gray")
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Cerca")
        buttons.button(QDialogButtonBox.Cancel).setText("Annulla")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addStretch(1)
        layout.addWidget(buttons)

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Dove cercare le sorgenti (anche nelle sottocartelle)",
                                                  self.folder_edit.text())
        if folder:
            self.folder_edit.setText(folder)

    def _library_toggled(self, checked: bool) -> None:
        self.folder_edit.setEnabled(not checked)
        self._browse_button.setEnabled(not checked)

    @property
    def selected_only(self) -> bool:
        result = self.selected_button.isChecked()
        return result

    def folders(self) -> list:
        if self.library_box.isChecked():
            result = list(self._music)
        else:
            result = [Path(self.folder_edit.text().strip())]
        return result

    @property
    def use_fingerprint(self) -> bool:
        result = self.fingerprint_box.isChecked()
        return result

    @property
    def use_ai(self) -> bool:
        result = self.ai_box.isChecked() and self.ai_box.isEnabled()
        return result


def summary_text(outcome) -> str:
    total = len(outcome.certain) + len(outcome.proposals)
    checked = len(outcome.certain)
    for proposal in outcome.proposals:
        if proposal.checked:
            checked += 1
    lines = [f"<b>{total}</b> brani dell'iPhone con una sorgente proposta sul PC ({checked} già spuntati perché "
             "certi o molto probabili)."]
    if outcome.certain:
        lines.append(f"{len(outcome.certain)} con l'impronta dell'audio (certi).")
    if outcome.by_folder:
        lines.append(f"{outcome.by_folder} dal nome della cartella, senza leggere l'audio.")
    if outcome.foreign:
        lines.append(f"<span style='color:#c33'><b>{len(outcome.foreign)}</b> brani non trovati</span> (in rosso): "
                     "restano <i>senza sorgente</i>, a meno che non scegli tu il file.")
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
    """chosen(): le proposte spuntate; missing: i brani ancora senza un file; one_by_one: associarli dopo uno alla
    volta (Associa sorgente)."""

    def __init__(self, parent, outcome) -> None:
        super().__init__(parent)
        self.setWindowTitle("Associa sorgenti: i file del PC dei brani dell'iPhone")
        self.resize(1300, 680)
        self.outcome = outcome
        header = QLabel(summary_text(outcome))
        header.setWordWrap(True)
        header.setTextFormat(Qt.RichText)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Brano sull'iPhone", "File sul PC", "Certezza", "Come", "Perché"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        widths = [360, 420, 110, 70]
        for column, width in enumerate(widths):
            self.tree.setColumnWidth(column, width)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(QHeaderView.Interactive)
        self._rows = []           # [riga, proposta o None, PhoneTrack]
        for proposal in list(outcome.certain) + list(outcome.proposals):
            self._add_row(proposal.phone, proposal)
        for item in outcome.foreign:
            self._add_row(item, None)
        self.tree.itemSelectionChanged.connect(self._selection_changed)

        check_all = QPushButton("Spunta tutte")
        check_all.clicked.connect(lambda: self._set_all(Qt.Checked))
        check_none = QPushButton("Togli tutte")
        check_none.clicked.connect(lambda: self._set_all(Qt.Unchecked))
        self.other_button = QPushButton("Scegli un altro file…")
        self.other_button.setToolTip("Per la riga selezionata: scegli tu il file del PC (anche per un brano non "
                                     "trovato)")
        self.other_button.setEnabled(False)
        self.other_button.clicked.connect(self._choose_other)
        tools = QHBoxLayout()
        tools.addWidget(check_all)
        tools.addWidget(check_none)
        tools.addWidget(self.other_button)
        tools.addStretch(1)
        self.one_by_one_box = QCheckBox(f"Dopo, associa uno alla volta i {len(outcome.foreign)} brani non trovati")
        self.one_by_one_box.setChecked(False)
        self.one_by_one_box.setVisible(bool(outcome.foreign))
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Associa")
        buttons.button(QDialogButtonBox.Cancel).setText("Annulla")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        note = QLabel("Associare scrive solo il registro della provenienza (sul PC e sull'iPhone): né i brani "
                      "dell'iPhone né i file del PC cambiano. Un brano senza spunta resta com'è.")
        note.setWordWrap(True)
        note.setStyleSheet("color: gray")

        layout = QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(self.tree, 1)
        layout.addLayout(tools)
        layout.addWidget(self.one_by_one_box)
        layout.addWidget(note)
        layout.addWidget(buttons)

    def _add_row(self, item, proposal) -> None:
        row = QTreeWidgetItem()
        self.tree.addTopLevelItem(row)
        entry = [row, proposal, item]
        self._rows.append(entry)
        self._show_entry(entry)

    def _show_entry(self, entry: list) -> None:
        row, proposal, item = entry
        row.setText(0, _phone_text(item))
        if proposal is None:
            row.setText(1, tr("non trovato"))
            row.setText(4, tr("nessun file simile"))
            for column in range(5):
                row.setBackground(column, QBrush(MISSING_COLOR))
            row.setFlags(row.flags() & ~Qt.ItemIsUserCheckable)
            row.setData(0, Qt.CheckStateRole, None)
        else:
            row.setText(1, str(proposal.pc.path))
            row.setToolTip(1, str(proposal.pc.path))
            row.setText(2, tr(proposal.level))
            color = LEVEL_COLOR.get(proposal.level)
            if color is not None:
                row.setForeground(2, QBrush(color))
            row.setText(3, tr(HOW_TEXT.get(proposal.how, proposal.how)))
            row.setText(4, tr(proposal.reason))
            row.setToolTip(4, tr(proposal.reason))
            for column in range(5):
                row.setBackground(column, QBrush())
            row.setFlags(row.flags() | Qt.ItemIsUserCheckable)
            row.setCheckState(0, Qt.Checked if proposal.checked else Qt.Unchecked)

    def _set_all(self, state) -> None:
        for row, proposal, _item in self._rows:
            if proposal is not None:
                row.setCheckState(0, state)

    def _selection_changed(self) -> None:
        self.other_button.setEnabled(bool(self.tree.selectedItems()))

    def _choose_other(self) -> None:
        selected = self.tree.selectedItems()
        entry = None
        for candidate in self._rows:
            if selected and candidate[0] is selected[0]:
                entry = candidate
        if entry is not None:
            start = str(entry[1].pc.path.parent) if entry[1] is not None else ""
            path = choose_audio_file(self, start)
            if path is not None:
                track = load_track(path)
                entry[1] = adoption.Proposal(entry[2], track, provenance.HOW_MANUAL, "scelto da te",
                                             checked=True, level=adoption.LEVEL_MANUAL)
                self._show_entry(entry)

    @property
    def missing(self) -> list:
        result = []
        for _row, proposal, item in self._rows:
            if proposal is None:
                result.append(item)
        return result

    @property
    def one_by_one(self) -> bool:
        result = bool(self.missing) and self.one_by_one_box.isChecked()
        return result

    def chosen(self) -> list:
        """Le proposte spuntate."""
        result = []
        for row, proposal, _item in self._rows:
            if proposal is not None and row.checkState(0) == Qt.Checked:
                result.append(proposal)
        return result
