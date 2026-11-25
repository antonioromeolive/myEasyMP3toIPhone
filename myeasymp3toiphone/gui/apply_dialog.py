# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Applica: la finestra delle azioni sull'iPhone in attesa, raggruppate per specie (Copia, Ricopia, Usa i tag, Cambia i
tag, Elimina). La ✕ di una riga, o "Togli il gruppo", toglie le azioni dalla coda subito: non partono, il brano resta
com'è e si possono rimettere dalle schede. "Applica N azioni" fa partire quelle rimaste (jobs)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPushButton, QToolButton, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

from .. import estimate
from ..i18n import tr
from ..pending import DELETE, EDIT, REPLACE, SEND, UPDATE

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
)
EDIT_LABELS = {"title": "Titolo", "album": "Album", "genre": "Genere", "year": "Anno", "track_number": "N. traccia",
               "disc_number": "N. disco", "compilation": "Compilation"}


def songs(count: int) -> str:
    # "1 brano" fisso: un modello "{0} brano" tradurrebbe anche "stesso brano"
    result = "1 brano" if count == 1 else f"{count} brani"
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
            parts.append(f"{songs(count)} {tr(phrase)}")
    result = " · ".join(parts)
    return result


def describe(job) -> tuple:
    """(brano, dettaglio) di un'azione: "Artista — Titolo", e l'album o i campi che cambiano."""
    from ..phone_library import COMPARED_FIELDS, changed_fields
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
        labels = dict(COMPARED_FIELDS)
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
        self._tree.setColumnWidth(0, 420)
        self._tree.setColumnWidth(1, 330)
        self._footer = QLabel()
        self._footer.setWordWrap(True)
        self._footer.setStyleSheet("color: gray")
        self._buttons = QDialogButtonBox()
        self._apply = self._buttons.addButton(tr("Applica"), QDialogButtonBox.AcceptRole)
        self._apply.setProperty("role", "go")
        cancel = self._buttons.addButton(tr("Annulla"), QDialogButtonBox.RejectRole)
        cancel.setDefault(True)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self._header)
        layout.addWidget(self._tree, 1)
        layout.addWidget(self._footer)
        layout.addWidget(self._buttons)
        self._fill()

    def _fill(self) -> None:
        from .iphone_panel import SYNC_WARNING
        self._tree.clear()
        for action, label, sub, _phrase in GROUPS:
            members = []
            for job in self.jobs:
                if job.action == action:
                    members.append(job)
            if members:
                group = QTreeWidgetItem([f"{tr(label)} ({len(members)})", tr(sub), ""])
                font = group.font(0)
                font.setBold(True)
                group.setFont(0, font)
                self._tree.addTopLevelItem(group)
                keys = []
                for job in members:
                    keys.append(job.key)
                    name, detail = describe(job)
                    row = QTreeWidgetItem([name, detail, ""])
                    row.setToolTip(0, name)
                    row.setToolTip(1, detail)
                    group.addChild(row)
                    self._tree.setItemWidget(row, 2, self._remove_button("✕", tr("Togli questa azione: non parte"),
                                                                         [job.key]))
                self._tree.setItemWidget(group, 2, self._remove_button(tr("Togli il gruppo"),
                                                                       tr("Togli tutte le azioni di questo gruppo"),
                                                                       keys))
                group.setExpanded(True)
        count = len(self.jobs)
        if count:
            self._header.setText(f"<b>Azioni in attesa per {self._device}: {count}</b>. La ✕ toglie un'azione: non "
                                 "parte, il brano resta com'è e la rimetti dalle schede.")
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

    def _remove_button(self, text: str, tip: str, keys: list) -> QWidget:
        if text == "✕":
            button = QToolButton()
            button.setText(text)
        else:
            button = QPushButton(text)
        button.setToolTip(tip)
        button.clicked.connect(lambda: self._drop(keys))
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(button)
        row.addStretch(1)
        return holder

    def _drop(self, keys: list) -> None:
        self.jobs = self._remove(keys)
        self._fill()
