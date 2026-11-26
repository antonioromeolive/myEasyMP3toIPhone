# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Applica: la finestra delle azioni sull'iPhone in attesa, raggruppate per specie (Copia, Ricopia, Usa i tag, Cambia i
tag, Elimina, e le suonerie). La ✕ di una riga, o "Togli il gruppo", toglie le azioni dalla coda subito: non partono, il brano resta
com'è e si possono rimettere dalle schede. "Applica N azioni" fa partire quelle rimaste (jobs)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)

from .. import estimate
from ..i18n import tr
from ..pending import DELETE, EDIT, REPLACE, RING_ACTIONS, RING_DELETE, RING_SEND, SEND, UPDATE

# (azione, nome del gruppo, cosa fa, la frase della barra "in attesa")
GROUPS = (
    (SEND, "Copia da PC a iPhone", "brani che sull'iPhone non ci sono", "da copiare da PC a iPhone"),
    (REPLACE, "Ricopia da PC a iPhone",
     "il file sull'iPhone è sostituito da quello del PC: perde ascolti e playlist", "da ricopiare da PC a iPhone"),
    (UPDATE, "Usa i tag da PC a iPhone", "solo i tag: sull'iPhone diventano quelli del PC",
     "con i tag da portare da PC a iPhone"),
    (EDIT, "Cambia i tag sull'iPhone", "i tag scritti con Cambia i tag nella scheda iPhone",
     "con i tag da cambiare sull'iPhone"),
    (DELETE, "Elimina dall'iPhone", "i file del PC non cambiano", "da eliminare dall'iPhone"),
    (RING_SEND, "Invia come suoneria (PC → iPhone)", "i .m4r della cartella delle suonerie",
     "da inviare da PC a iPhone"),
    (RING_DELETE, "Elimina le suonerie dall'iPhone", "solo quelle messe da un computer; i file del PC non cambiano",
     "da eliminare dall'iPhone"),
)
REMOVE_COLOR = QColor(192, 57, 43)     # la ✕ e "Togli il gruppo"
MAX_EXPANDED = 300                     # un gruppo più grande si apre chiuso (si apre con la freccia)
EDIT_LABELS = {"title": "Titolo", "album": "Album", "genre": "Genere", "year": "Anno", "track_number": "N. traccia",
               "disc_number": "N. disco", "compilation": "Compilation"}


def songs(count: int) -> str:
    # "1 brano" fisso: un modello "{0} brano" tradurrebbe anche "stesso brano"
    result = "1 brano" if count == 1 else f"{count} brani"
    return result


def ringtones_text(count: int) -> str:
    result = "1 suoneria" if count == 1 else f"{count} suonerie"
    return result


def counted(action: str, count: int) -> str:
    """"3 brani" o, per le azioni sulle suonerie, "3 suonerie"."""
    result = ringtones_text(count) if action in RING_ACTIONS else songs(count)
    return result


def summary(jobs: list) -> str:
    """"4 brani da copiare da PC a iPhone · 1 brano da eliminare dall'iPhone" (vuota senza azioni)."""
    parts = []
    for action, _label, _sub, phrase in GROUPS:
        count = 0
        for job in jobs:
            if job.action == action:
                count += 1
        if count:
            parts.append(f"{counted(action, count)} {tr(phrase)}")
    result = " · ".join(parts)
    return result


def describe(job) -> tuple:
    """(brano, dettaglio) di un'azione: "Artista — Titolo", e l'album o i campi che cambiano."""
    from ..phone_library import COMPARED_FIELDS, changed_fields
    from ..ringtones import format_ms
    if job.action == RING_SEND:
        result = (f"♪ {job.track.name}", f"{format_ms(job.track.duration_ms)} · {job.track.path.name}")
    elif job.action == RING_DELETE:
        result = (f"♪ {job.phone.name}", job.phone.file_name)
    else:
        result = _describe_track(job, COMPARED_FIELDS, changed_fields)
    return result


def _describe_track(job, compared_fields, changed_fields) -> tuple:
    if job.phone is not None:
        tags = job.phone.tags
        artist = job.phone.display_artist
    else:
        tags = job.track.tags
        artist = tags.artist or tags.album_artist
    name = f"{artist} — {tags.title}"
    if job.action == SEND:
        detail = f"{tags.album} · {job.track.path.suffix[1:].upper()}"
    elif job.action in (UPDATE, REPLACE) and job.track is not None:
        labels = dict(compared_fields)
        fields = []
        for field_name in changed_fields(job.track.tags, tags):
            fields.append(tr(labels.get(field_name, field_name)))
        detail = tr(f"tag diversi: {', '.join(fields)}") if fields else tags.album
    elif job.action == EDIT:
        changes = []
        for field_name, value in job.values.items():
            changes.append(f"{tr(EDIT_LABELS.get(field_name, field_name))} → {value}")
        detail = ", ".join(changes)
    else:
        detail = tags.album
    result = (name, detail)
    return result


class ApplyDialog(QDialog):
    """jobs: le azioni (pending.Job); remove(chiavi) -> azioni rimaste, dopo averle tolte dalla coda; seconds(jobs) ->
    il tempo stimato; notes(jobs) -> righe in più (grafia, playlist); ready: l'iPhone è connesso e libero."""

    def __init__(self, parent, jobs: list, remove, seconds, notes, ready: bool, device: str) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("Applica le azioni in attesa sull'iPhone"))
        self.resize(900, 600)
        self.jobs = list(jobs)
        self._remove = remove
        self._seconds = seconds
        self._notes = notes
        self._ready = ready
        self._device = device
        self._header = QLabel()
        self._header.setWordWrap(True)
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels([tr("Brano"), tr("Dettaglio"), ""])
        self._tree.setRootIsDecorated(True)
        self._tree.setUniformRowHeights(True)
        self._tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._tree.setColumnWidth(0, 420)
        self._tree.setColumnWidth(1, 330)
        self._tree.itemClicked.connect(self._clicked)
        self._tree.itemSelectionChanged.connect(
            lambda: self._remove_selected.setEnabled(bool(self._selected_keys())))
        self._footer = QLabel()
        self._footer.setWordWrap(True)
        self._footer.setStyleSheet("color: gray")
        self._buttons = QDialogButtonBox()
        self._apply = self._buttons.addButton(tr("Applica"), QDialogButtonBox.AcceptRole)
        self._apply.setProperty("role", "go")
        cancel = self._buttons.addButton(tr("Annulla"), QDialogButtonBox.RejectRole)
        cancel.setDefault(True)
        self._remove_selected = QPushButton("Togli le selezionate")
        self._remove_selected.setToolTip("Toglie dalla coda le azioni delle righe selezionate (anche il tasto Canc)")
        self._remove_selected.clicked.connect(self._drop_selected)
        self._buttons.addButton(self._remove_selected, QDialogButtonBox.ResetRole)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self._header)
        layout.addWidget(self._tree, 1)
        layout.addWidget(self._footer)
        layout.addWidget(self._buttons)
        self._fill()

    def _fill(self) -> None:
        """Le azioni per gruppo. La terza colonna ha la ✕ (una riga) o "Togli il gruppo": un clic le toglie. Niente
        widget per riga: con migliaia di azioni (una Copia di tutta la libreria) la finestra si apre subito."""
        from .iphone_panel import SYNC_WARNING
        self._tree.setUpdatesEnabled(False)
        self._tree.clear()
        bold = None
        for action, label, sub, _phrase in GROUPS:
            members = []
            for job in self.jobs:
                if job.action == action:
                    members.append(job)
            if members:
                keys = []
                for job in members:
                    keys.append(job.key)
                group = QTreeWidgetItem([f"{tr(label)} ({len(members)})", tr(sub), tr("Togli il gruppo")])
                if bold is None:
                    bold = group.font(0)
                    bold.setBold(True)
                group.setFont(0, bold)
                group.setData(2, Qt.UserRole, keys)
                group.setToolTip(2, tr("Togli tutte le azioni di questo gruppo"))
                group.setForeground(2, QBrush(REMOVE_COLOR))
                rows = []
                for job in members:
                    name, detail = describe(job)
                    row = QTreeWidgetItem([name, detail, "✕"])
                    row.setToolTip(0, name)
                    row.setToolTip(1, detail)
                    row.setToolTip(2, tr("Togli questa azione: non parte"))
                    row.setData(2, Qt.UserRole, [job.key])
                    row.setForeground(2, QBrush(REMOVE_COLOR))
                    row.setTextAlignment(2, Qt.AlignCenter)
                    rows.append(row)
                group.addChildren(rows)
                self._tree.addTopLevelItem(group)
                group.setExpanded(len(members) <= MAX_EXPANDED)
        self._tree.setUpdatesEnabled(True)
        count = len(self.jobs)
        if count:
            self._header.setText(f"<b>Azioni in attesa per {self._device}: {count}</b>. La ✕ (o Canc sulle righe "
                                 "selezionate) toglie un'azione: non parte, il brano resta com'è e la rimetti dalle "
                                 "schede.")
        else:
            self._header.setText("<b>Nessuna azione</b>: le hai tolte tutte.")
        footer = estimate.summary(count, self._seconds(self.jobs)) if count else ""
        notes = self._notes(self.jobs) if count else ""
        footer += notes + "\n\n" + SYNC_WARNING
        if not self._ready:
            footer += "\n\nPer applicarle connetti l'iPhone (e aspetta la fine dell'operazione in corso)."
        self._footer.setText(footer.strip())
        self._apply.setText(f"Applica {count} azioni" if count != 1 else "Applica 1 azione")
        self._apply.setEnabled(bool(count) and self._ready)
        self._remove_selected.setEnabled(False)

    def _clicked(self, item, column: int) -> None:
        keys = item.data(2, Qt.UserRole)
        if column == 2 and keys:
            self._drop(list(keys))

    def _selected_keys(self) -> list:
        result = []
        for item in self._tree.selectedItems():
            for key in item.data(2, Qt.UserRole) or []:
                if key not in result:
                    result.append(key)
        return result

    def _drop_selected(self) -> None:
        keys = self._selected_keys()
        if keys:
            self._drop(keys)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Delete and self._selected_keys():
            self._drop_selected()
        else:
            super().keyPressEvent(event)

    def _drop(self, keys: list) -> None:
        self.jobs = self._remove(keys)
        self._fill()
