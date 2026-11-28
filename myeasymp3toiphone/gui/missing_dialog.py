# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""L'avviso delle sorgenti sparite: brani dell'iPhone il cui file sul PC non c'è più (spostato o cancellato, per
esempio un doppione). Si decide **per album**, non brano per brano: per ogni album una copia dello stesso album nella
libreria (stesso artista dell'album e titolo: relocate.missing_albums, con i brani ritrovati lì), togliere
l'associazione (il brano resta sull'iPhone senza sorgente), eliminarlo dall'iPhone (in attesa: solo se sul PC
l'album non c'è più) o lasciarlo per più tardi. Cancellare dall'iPhone non tocca mai il PC;
associare scrive solo il registro della provenienza."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout,
)

from ..library import short_folder
from .theme import set_role

CHOICE_FOLDER = "scelta_cartella"
CHOICE_FORGET = "scelta_togli"
CHOICE_DELETE = "scelta_elimina"
CHOICE_LATER = "scelta_dopo"


class MissingSourcesDialog(QDialog):
    """albums: relocate.MissingAlbum. decisions(): [(MissingAlbum, scelta, {pid: Proposal})] degli album con una
    scelta (non "più tardi")."""

    def __init__(self, parent, albums: list, connected: bool) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sorgenti sparite dal PC")
        self.resize(1200, 560)
        self._albums = albums
        self._combos = []
        tracks = 0
        found_albums = 0
        for album in albums:
            tracks += len(album.rows)
            if album.candidates:
                found_albums += 1
        header = QLabel(f"<b>{tracks}</b> brani dell'iPhone, in <b>{len(albums)}</b> album, vengono da file di questo PC "
                        "che non ci sono più (spostati o cancellati). Per <b>"
                        f"{found_albums}</b> album c'è nella libreria lo stesso album (stesso artista dell'album e "
                        "titolo): è già scelto nella colonna <i>Cosa fare</i>. Per ogni album scegli la copia da "
                        "associare, togli l'associazione, eliminalo dall'iPhone (solo se sul PC l'album non c'è più) o "
                        "lascia per più tardi; poi <i>Applica le scelte</i>.<br>Se i file sono su un disco che ora non "
                        "è collegato, collegalo e premi <i>Più tardi</i>.")
        header.setTextFormat(Qt.RichText)
        header.setWordWrap(True)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Album sull'iPhone", "Brani", "Cartella di prima", "Cosa fare", "Ritrovato"])
        self.tree.setSelectionMode(QAbstractItemView.NoSelection)
        self.tree.setAlternatingRowColors(True)
        for column, width in enumerate([320, 50, 300, 360]):
            self.tree.setColumnWidth(column, width)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(QHeaderView.Interactive)
        for album in albums:
            top = QTreeWidgetItem([f"{album.key[0]} — {album.key[1]}", str(len(album.rows)),
                                   short_folder(album.old_folder), "", ""])
            top.setToolTip(2, album.old_folder)
            for item, link in album.rows:
                child = QTreeWidgetItem([item.tags.title, "", link.path.rsplit("\\", 1)[-1], "", ""])
                child.setToolTip(2, link.path)
                top.addChild(child)
            self.tree.addTopLevelItem(top)
            combo = QComboBox()
            self._fill_combo(combo, album)
            combo.currentIndexChanged.connect(
                lambda _index, album=album, combo=combo, top=top: self._chosen(album, combo, top))
            self.tree.setItemWidget(top, 3, combo)
            self._combos.append((album, combo, top))
            self._show_found(album, combo, top)

        all_found = QPushButton("Tutti: lo stesso album nella libreria")
        all_found.setToolTip("Per ogni album che c'è nella libreria, la prima copia proposta; gli altri più tardi")
        all_found.clicked.connect(lambda: self._set_all(CHOICE_FOLDER))
        all_forget = QPushButton("Tutti: togli l'associazione")
        all_forget.setToolTip("Restano sull'iPhone, senza sorgente sul PC")
        all_forget.clicked.connect(lambda: self._set_all(CHOICE_FORGET))
        all_later = QPushButton("Tutti: più tardi")
        all_later.clicked.connect(lambda: self._set_all(CHOICE_LATER))
        apply = QPushButton("Applica le scelte")
        set_role(apply, "go")
        apply.clicked.connect(self.accept)
        later = QPushButton("Più tardi")
        later.clicked.connect(self.reject)
        tools = QHBoxLayout()
        tools.addWidget(QLabel("Per tutti gli album:"))
        tools.addWidget(all_found)
        tools.addWidget(all_forget)
        tools.addWidget(all_later)
        tools.addStretch(1)
        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(apply)
        actions.addWidget(later)
        note = QLabel("Associare scrive solo il registro della provenienza: i file non cambiano. \"Elimina dall'iPhone\" "
                      "va in attesa e parte con Applica (barra blu); sul PC non cambia niente. Li ritrovi quando vuoi "
                      "nella scheda iPhone con il filtro \"File del PC non trovato\".")
        note.setWordWrap(True)
        note.setStyleSheet("color: gray")
        layout = QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(self.tree, 1)
        layout.addLayout(tools)
        layout.addWidget(note)
        layout.addLayout(actions)

    # ------------------------------------------------------------------ le scelte

    def _fill_combo(self, combo: QComboBox, album) -> None:
        combo.blockSignals(True)
        combo.clear()
        total = len(album.rows)
        for index, candidate in enumerate(album.candidates):
            combo.addItem(f"Associa all'album in {short_folder(candidate.folder)} ({len(candidate.proposals)} di "
                          f"{total} brani)", (CHOICE_FOLDER, index))
            combo.setItemData(combo.count() - 1, candidate.folder, Qt.ToolTipRole)
        combo.addItem("Togli l'associazione (resta sull'iPhone senza sorgente)", (CHOICE_FORGET, -1))
        if not album.candidates:                 # sul PC l'album non c'è più
            combo.addItem("Elimina dall'iPhone (in attesa)", (CHOICE_DELETE, -1))
        combo.addItem("Più tardi", (CHOICE_LATER, -1))
        combo.setCurrentIndex(0 if album.candidates else combo.count() - 1)
        combo.blockSignals(False)

    def _chosen(self, album, combo: QComboBox, top) -> None:
        self._show_found(album, combo, top)

    def _show_found(self, album, combo: QComboBox, top) -> None:
        """La colonna Ritrovato: per ogni brano il file che diventa la sorgente con la scelta di ora."""
        kind, index = combo.currentData()
        proposals = album.candidates[index].proposals if kind == CHOICE_FOLDER else {}
        for row_index, (item, _link) in enumerate(album.rows):
            child = top.child(row_index)
            proposal = proposals.get(item.pid)
            child.setText(4, proposal.pc.path.name if proposal is not None else "")
            child.setToolTip(4, f"{proposal.pc.path}\n{proposal.reason}" if proposal is not None else "")
        if kind == CHOICE_FOLDER:
            missing = len(album.rows) - len(proposals)
            top.setText(4, f"{len(proposals)} ritrovati" + (f", {missing} no (restano così)" if missing else ""))
        elif not album.candidates:
            top.setText(4, "sul PC l'album non c'è più")
        else:
            top.setText(4, "")

    def _set_all(self, kind: str) -> None:
        for album, combo, top in self._combos:
            wanted = combo.count() - 1                       # più tardi
            if kind == CHOICE_FOLDER and album.candidates:
                wanted = 0
            elif kind != CHOICE_FOLDER:
                for index in range(combo.count()):
                    if combo.itemData(index)[0] == kind:
                        wanted = index
            combo.blockSignals(True)
            combo.setCurrentIndex(wanted)
            combo.blockSignals(False)
            self._show_found(album, combo, top)

    def decisions(self) -> list:
        result = []
        for album, combo, _top in self._combos:
            kind, index = combo.currentData()
            if kind == CHOICE_FOLDER:
                result.append((album, kind, dict(album.candidates[index].proposals)))
            elif kind in (CHOICE_FORGET, CHOICE_DELETE):
                result.append((album, kind, {}))
        return result
