# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""L'avviso delle sorgenti sparite: brani dell'iPhone il cui file sul PC non c'è più (spostato o cancellato, per
esempio un doppione). Prima il programma li cerca nella cartella aperta (relocate: stesso audio, stesso nome e
dimensione, l'album in una cartella) e mostra dove li ha ritrovati. Per quelli spuntati: associare i file ritrovati,
cercare un'altra sorgente, lasciarli senza sorgente, o eliminarli anche dall'iPhone. Cancellare dall'iPhone non tocca
mai il PC; associare scrive solo il registro della provenienza."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout,
)

from ..library import short_folder
from .theme import mark_danger, set_role

ACTION_SEARCH = "search"
ACTION_ORPHAN = "orphan"
ACTION_DELETE = "delete"
ACTION_RELINK = "associa_ritrovati"


class MissingSourcesDialog(QDialog):
    """action: ACTION_* scelta (None = più tardi); chosen(): i PhoneTrack spuntati."""

    def __init__(self, parent, rows: list, connected: bool, found: dict = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sorgenti sparite dal PC")
        self.resize(1100, 480)
        self.action = None
        found = found or {}
        header = QLabel(f"<b>{len(rows)}</b> brani dell'iPhone vengono da file di questo PC che non ci sono più "
                        f"(spostati o cancellati). <b>{len(found)}</b> li ho ritrovati nella cartella aperta: colonna "
                        "<i>Ritrovato sul PC</i>. Il programma non li toglie dall'iPhone da solo: scegli tu cosa fare "
                        "con quelli spuntati.<br>Se il file è su un disco che ora non è collegato, collegalo e premi "
                        "<i>Più tardi</i>.")
        header.setTextFormat(Qt.RichText)
        header.setWordWrap(True)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Brano sull'iPhone", "Album", "Il file che non c'è più", "Ritrovato sul PC"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.NoSelection)
        for column, width in enumerate([300, 200, 300]):
            self.tree.setColumnWidth(column, width)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(QHeaderView.Interactive)
        self._rows = []
        for item, link in rows:
            tags = item.tags
            proposal = found.get(item.pid)
            where = ""
            if proposal is not None:
                where = short_folder(proposal.pc.path.parent) + "\\" + proposal.pc.path.name
            row = QTreeWidgetItem([f"{item.display_artist} — {tags.title}", tags.album, link.path, where])
            row.setFlags(row.flags() | Qt.ItemIsUserCheckable)
            row.setCheckState(0, Qt.Checked)
            row.setToolTip(2, link.path)
            if proposal is not None:
                row.setToolTip(3, f"{proposal.pc.path}\n{proposal.reason}")
            self.tree.addTopLevelItem(row)
            self._rows.append((row, item))

        check_all = QPushButton("Spunta tutti")
        check_all.clicked.connect(lambda: self._set_all(Qt.Checked))
        check_none = QPushButton("Togli tutti")
        check_none.clicked.connect(lambda: self._set_all(Qt.Unchecked))
        relink = QPushButton(f"Associa i file ritrovati ({len(found)})")
        relink.setToolTip("I brani spuntati con un file nella colonna Ritrovato sul PC: quel file diventa la loro "
                          "sorgente (si scrive solo il registro della provenienza)")
        relink.setEnabled(bool(found))
        set_role(relink, "go")
        relink.clicked.connect(lambda: self._choose(ACTION_RELINK))
        search = QPushButton("Cerca un'altra sorgente…")
        search.setToolTip("Uno alla volta, la finestra di Associa sorgente: per prima la copia con lo stesso audio")
        search.clicked.connect(lambda: self._choose(ACTION_SEARCH))
        orphan = QPushButton("Lascia senza sorgente")
        orphan.setToolTip("Restano sull'iPhone come brani senza sorgente")
        orphan.clicked.connect(lambda: self._choose(ACTION_ORPHAN))
        delete = QPushButton("Elimina dall'iPhone…")
        delete.setToolTip("Toglie i brani dall'iPhone (chiede conferma); sul PC non cambia niente" if connected
                          else "Connetti l'iPhone")
        delete.setEnabled(connected)
        mark_danger(delete)
        delete.clicked.connect(lambda: self._choose(ACTION_DELETE))
        later = QPushButton("Più tardi")
        later.clicked.connect(self.reject)
        tools = QHBoxLayout()
        tools.addWidget(check_all)
        tools.addWidget(check_none)
        tools.addStretch(1)
        actions = QHBoxLayout()
        actions.addWidget(relink)
        actions.addWidget(search)
        actions.addWidget(orphan)
        actions.addWidget(delete)
        actions.addStretch(1)
        actions.addWidget(later)
        note = QLabel("Li ritrovi quando vuoi con Mostra → \"File del PC non trovato\" e il tasto destro.")
        note.setStyleSheet("color: gray")
        layout = QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(self.tree, 1)
        layout.addLayout(tools)
        layout.addWidget(note)
        layout.addLayout(actions)

    def _set_all(self, state) -> None:
        for row, _item in self._rows:
            row.setCheckState(0, state)

    def _choose(self, action: str) -> None:
        if self.chosen():
            self.action = action
            self.accept()

    def chosen(self) -> list:
        result = []
        for row, item in self._rows:
            if row.checkState(0) == Qt.Checked:
                result.append(item)
        return result
