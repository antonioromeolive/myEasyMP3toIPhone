# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Playlist per artista e per compilation: il piano (playlists.plan) prima di scrivere sull'iPhone.

Si vedono le playlist da creare (con le spunte), quelle da cancellare (tutte quelle messe da un computer) e quelle
che restano (fatte sul telefono). Prova crea solo una copia della prima playlist spuntata, chiamata "♪ PROVA", e
non cancella niente: per vedere sul telefono che tutto va, prima di farlo davvero. I brani non cambiano mai."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QHeaderView, QLabel, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)

from .. import playlists
from ..i18n import tr

ACTION_TEST = "azione_prova"
ACTION_APPLY = "azione_applica"
TEST_NAME = playlists.MARK + "PROVA"
KIND_TEXT = {playlists.KIND_ARTIST: "artista", playlists.KIND_COMPILATION: "compilation"}
MAX_TOOLTIP_ALBUMS = 30


def _section(tree: QTreeWidget, title: str) -> QTreeWidgetItem:
    result = QTreeWidgetItem([tr(title)])
    font = QFont()
    font.setBold(True)
    result.setFont(0, font)
    result.setFlags(Qt.ItemIsEnabled)
    tree.addTopLevelItem(result)
    return result


class PlaylistDialog(QDialog):
    """action: ACTION_TEST o ACTION_APPLY dopo exec(); chosen(): le PlannedPlaylist spuntate."""

    def __init__(self, parent, plan: playlists.PlaylistPlan) -> None:
        super().__init__(parent)
        self.setWindowTitle("Playlist per artista e per compilation")
        self.resize(900, 620)
        self.action = ""
        self._plan = plan
        text = (f"<b>{len(plan.create)} playlist da creare</b> (quelle spuntate) e <b>{len(plan.delete)} da "
                "cancellare</b>: tutte quelle messe da un computer (CopyTrans, iTunes, questo programma), comprese "
                "quelle fatte le volte prima.<br>Per artista: gli artisti dell'album con almeno "
                f"{playlists.MIN_ALBUMS} album e {playlists.MIN_TRACKS} brani. Per compilation: i volumi della "
                f"stessa serie insieme, o un album solo con almeno {playlists.MIN_COMPILATION_TRACKS} brani.<br>"
                "I brani non cambiano: cambiano solo le playlist. Prima si creano le nuove, poi si cancellano le "
                "vecchie.")
        if plan.kept:
            text += (f"<br>{len(plan.kept)} playlist fatte sull'iPhone restano: il computer non le può toccare "
                     "(cancellale a mano, se vuoi).")
        if plan.left_out:
            text += (f"<br>{plan.left_out} brani non messi da un computer (o senza file) non possono stare in "
                     "queste playlist.")
        header = QLabel(text)
        header.setTextFormat(Qt.RichText)
        header.setWordWrap(True)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Playlist", "Tipo", "Album", "Brani"])
        self.tree.setColumnWidth(0, 420)
        self.tree.setColumnWidth(1, 110)
        self.tree.setColumnWidth(2, 70)
        self.tree.header().setSectionResizeMode(QHeaderView.Interactive)
        self._created = []
        create = _section(self.tree, f"Da creare ({len(plan.create)})")
        for playlist in plan.create:
            row = QTreeWidgetItem([playlist.name, tr(KIND_TEXT.get(playlist.kind, playlist.kind)),
                                   str(len(playlist.albums)), str(len(playlist.tracks))])
            row.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
            row.setCheckState(0, Qt.Checked)
            shown = playlist.albums[:MAX_TOOLTIP_ALBUMS]
            if len(playlist.albums) > MAX_TOOLTIP_ALBUMS:
                shown.append("…")
            row.setToolTip(0, "\n".join(shown))
            create.addChild(row)
            self._created.append((row, playlist))
        delete = _section(self.tree, f"Da cancellare: messe da un computer ({len(plan.delete)})")
        for playlist in plan.delete:
            delete.addChild(QTreeWidgetItem([playlist.name, "", "", str(playlist.count)]))
        if plan.kept:
            kept = _section(self.tree, f"Restano: fatte sull'iPhone ({len(plan.kept)})")
            for playlist in plan.kept:
                kept.addChild(QTreeWidgetItem([playlist.name, "", "", str(playlist.count)]))
        create.setExpanded(True)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.apply_button = buttons.button(QDialogButtonBox.Ok)
        self.apply_button.setText("Crea e cancella…")
        buttons.button(QDialogButtonBox.Cancel).setText("Annulla")
        self.test_button = buttons.addButton("Prova", QDialogButtonBox.ActionRole)
        self.test_button.setToolTip(f"Crea solo \"{TEST_NAME}\", una copia della prima playlist spuntata, e non "
                                    "cancella niente: guarda sul telefono che ci sia, con i brani in ordine. La "
                                    "cancella la prossima volta, con le altre messe da un computer.")
        self.test_button.clicked.connect(self._test)
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        self.tree.itemChanged.connect(lambda _item, _column: self._update_buttons())
        layout = QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(self.tree, 1)
        layout.addWidget(buttons)
        self._update_buttons()

    def chosen(self) -> list:
        result = []
        for row, playlist in self._created:
            if row.checkState(0) == Qt.Checked:
                result.append(playlist)
        return result

    def test_playlist(self):
        """La playlist della prova: la prima spuntata con il nome TEST_NAME (None se nessuna è spuntata)."""
        chosen = self.chosen()
        result = None
        if chosen:
            first = chosen[0]
            result = playlists.PlannedPlaylist(TEST_NAME, first.kind, first.tracks, first.albums)
        return result

    def _update_buttons(self) -> None:
        some = bool(self.chosen())
        self.test_button.setEnabled(some)
        self.apply_button.setEnabled(some or bool(self._plan.delete))

    def _test(self) -> None:
        self.action = ACTION_TEST
        self.accept()

    def _apply(self) -> None:
        self.action = ACTION_APPLY
        self.accept()
