# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Collega a mano un brano dell'iPhone a un file del PC: i candidati più simili della cartella aperta (durata,
titolo, artista), oppure un file qualsiasi."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout,
)

from ..adoption import candidates
from ..tags import AUDIO_EXTENSIONS


def _duration(seconds: float) -> str:
    total = int(round(seconds))
    result = f"{total // 60}:{total % 60:02d}"
    return result


class LinkDialog(QDialog):
    def __init__(self, parent, phone_track, pc_tracks: list) -> None:
        super().__init__(parent)
        self.setWindowTitle("Collega a un file del PC")
        self.resize(900, 420)
        self.chosen: Optional[Path] = None
        tags = phone_track.tags
        header = QLabel(f"<b>{tags.artist or tags.album_artist} — {tags.title}</b> ({tags.album}, "
                        f"{_duration(phone_track.length)})<br>Scegli il file del PC che è questo brano:")
        header.setTextFormat(Qt.RichText)
        header.setWordWrap(True)
        by_length = []
        for index, track in enumerate(pc_tracks):
            if track.length > 0 and not track.error:
                by_length.append((track.length, index, track))
        by_length.sort(key=lambda entry: (entry[0], entry[1]))
        self.list = QListWidget()
        for score, track in candidates(phone_track, by_length):
            pc_tags = track.tags
            text = (f"{pc_tags.artist or pc_tags.album_artist} — {pc_tags.title or track.path.stem}  "
                    f"({pc_tags.album}, {_duration(track.length)})   {track.path}")
            row = QListWidgetItem(text)
            row.setData(Qt.UserRole, str(track.path))
            row.setToolTip(f"Somiglianza {score:.0%}")
            self.list.addItem(row)
        if self.list.count():
            self.list.setCurrentRow(0)
        else:
            self.list.addItem("Nessun file simile nella cartella aperta: scegli un file con il pulsante qui sotto.")
        self.list.itemDoubleClicked.connect(lambda _row: self._accept_current())
        other = QPushButton("Scegli un altro file…")
        other.clicked.connect(self._choose_file)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Collega")
        buttons.accepted.connect(self._accept_current)
        buttons.rejected.connect(self.reject)
        note = QLabel("Si scrive solo il registro della provenienza: né il brano dell'iPhone né il file cambiano.")
        note.setStyleSheet("color: gray")
        layout = QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(self.list, 1)
        layout.addWidget(other)
        layout.addWidget(note)
        layout.addWidget(buttons)

    def _accept_current(self) -> None:
        row = self.list.currentItem()
        value = row.data(Qt.UserRole) if row is not None else None
        if value:
            self.chosen = Path(value)
            self.accept()

    def _choose_file(self) -> None:
        patterns = " ".join(f"*{extension}" for extension in sorted(AUDIO_EXTENSIONS))
        path, _filter = QFileDialog.getOpenFileName(self, "Il file del PC", "", f"Audio ({patterns})")
        if path:
            self.chosen = Path(path)
            self.accept()
