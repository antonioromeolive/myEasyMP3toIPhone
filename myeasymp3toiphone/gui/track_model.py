# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Il modello della tabella dei brani della scheda PC: le celle si calcolano solo quando si vedono, quindi mostrare o
filtrare decine di migliaia di brani è immediato (prima ogni riempimento creava una cella per ogni valore).

Il modello non decide niente: chiede alla finestra (owner) lo stato rispetto all'iPhone, le modifiche in attesa e
quelle in sospeso, e le passa la spunta della colonna iPhone (owner.device_checked)."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QBrush, QColor, QFont

from ..library import album_folder, short_folder, track_sort_key
from ..i18n import tr
from ..pending import wanted
from ..phone_library import DEVICE_ABSENT, DEVICE_SAME, DEVICE_STALE
from .theme import album_band, album_bands

COLUMNS = ["#", "iPhone", "Titolo", "Artista", "Artista album", "Album", "Anno", "Genere", "Durata", "Cartella",
           "File"]
(COL_NUMBER, COL_DEVICE, COL_TITLE, COL_ARTIST, COL_ALBUM_ARTIST, COL_ALBUM, COL_YEAR, COL_GENRE, COL_LENGTH,
 COL_FOLDER, COL_FILE) = range(len(COLUMNS))
DEVICE_TEXT = {DEVICE_SAME: "✔", DEVICE_STALE: "⟳", DEVICE_ABSENT: ""}
DEVICE_COLOR = {DEVICE_SAME: QColor(30, 140, 60), DEVICE_STALE: QColor(220, 140, 0)}
DEVICE_ORDER = {DEVICE_SAME: 0, DEVICE_STALE: 1, DEVICE_ABSENT: 3}
PROBABLE_TEXT = "≈"                     # sull'iPhone c'è un brano con gli stessi tag, ma non è collegato a questo file
PROBABLE_COLOR = QColor(130, 130, 130)
PROBABLE_ORDER = 2
ERROR_COLOR = QColor(200, 40, 40)
EDITED_COLOR = QColor(60, 130, 230)
DIFFERENT_COLOR = QColor(230, 180, 0)    # il file è la sorgente di un brano dell'iPhone, ma i tag sono diversi
STRAY_COLOR = QColor(205, 70, 195)       # il brano sta fuori dalla cartella del resto del suo album


def format_length(seconds: float) -> str:
    total = int(round(seconds))
    result = f"{total // 60}:{total % 60:02d}"
    return result


class TrackTableModel(QAbstractTableModel):
    def __init__(self, owner, pending_look: dict, pending_tip: dict) -> None:
        super().__init__(owner)
        self.owner = owner
        self.rows = []
        self.pending_look = pending_look      # azione -> (segno, colore, tinta della riga)
        self.pending_tip = pending_tip
        self.device_header_tip = ""
        self._italic = QFont()
        self._italic.setItalic(True)
        self._bold = QFont()
        self._bold.setBold(True)
        self._bands = []                      # per riga: (tinta, chiara/scura) del suo album (theme.album_bands)

    # ------------------------------------------------------------------ dati

    def set_tracks(self, tracks: list) -> None:
        self.beginResetModel()
        self.rows = list(tracks)
        self._update_bands()
        self.endResetModel()

    def _update_bands(self) -> None:
        """La tinta cambia con l'album e, per lo stesso album in due copie, con la copia: la cartella
        (library.album_folder: "CD1" e "CD2" dello stesso album restano insieme) e il formato (FLAC e MP3 nella stessa
        cartella sono due copie)."""
        keys = []
        folders = {}
        for track in self.rows:
            parent = track.path.parent
            if parent not in folders:
                folders[parent] = album_folder(track.path).lower()
            keys.append((track.album_key, folders[parent], track.path.suffix.lower()))
        self._bands = album_bands(keys)

    def _background(self, row: int, track):
        """La tinta dell'album, sempre (un'azione in attesa si vede dal segno della colonna iPhone, in blu)."""
        band, shade = self._bands[row]
        result = QBrush(album_band(band, shade))
        return result

    def track(self, row: int):
        result = self.rows[row]
        return result

    def refresh(self) -> None:
        """Le celle vanno ridisegnate (spunte, stato dell'iPhone): la vista rilegge solo quelle visibili."""
        if self.rows:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.rows) - 1, len(COLUMNS) - 1))

    def rowCount(self, parent=QModelIndex()) -> int:
        result = 0 if parent.isValid() else len(self.rows)
        return result

    def columnCount(self, parent=QModelIndex()) -> int:
        result = 0 if parent.isValid() else len(COLUMNS)
        return result

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        result = None
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            result = tr(COLUMNS[section])
        elif orientation == Qt.Horizontal and role == Qt.ToolTipRole and section == COL_DEVICE:
            result = tr(self.device_header_tip) or None
        return result

    def _action(self, track) -> str:
        result = self.owner.pending.get(track.path) if self.owner.phone_known() else ""
        return result

    def _text(self, track, column: int) -> str:
        tags = track.tags
        if column == COL_NUMBER:
            result = str(tags.track_number) if tags.track_number is not None else ""
        elif column == COL_DEVICE:
            action = self._action(track)
            status, _phone_track, linked = self.owner.device_state(track)
            if action:
                result = self.pending_look[action][0]
            elif status != DEVICE_ABSENT and not linked:
                result = PROBABLE_TEXT
            else:
                result = DEVICE_TEXT[status]
        elif column == COL_TITLE:
            result = track.title
        elif column == COL_ARTIST:
            result = tags.artist
        elif column == COL_ALBUM_ARTIST:
            result = tags.album_artist
        elif column == COL_ALBUM:
            result = tags.album
        elif column == COL_YEAR:
            result = tags.year
        elif column == COL_GENRE:
            result = tags.genre
        elif column == COL_LENGTH:
            result = format_length(track.length)
        elif column == COL_FOLDER:
            result = self._folder_text(track)
        else:
            result = track.path.name
        return result

    def _folder_text(self, track) -> str:
        """La cartella del file: il percorso completo o il solo nome (Impostazioni → Mostra il percorso completo delle
        cartelle); per una cartella di disco anche quella sopra ("Album\\CD1", library.short_folder)."""
        settings = getattr(self.owner, "app_settings", None)
        folder = track.path.parent
        result = str(folder) if settings is not None and settings.show_full_path else short_folder(folder)
        return result

    def _foreground(self, track, column: int):
        result = None
        if track.error:
            result = QBrush(ERROR_COLOR)
        elif column == COL_TITLE and self.owner.overlay.is_edited(track.path):
            result = QBrush(EDITED_COLOR)
        elif column == COL_FOLDER and self.owner.stray_folder(track):
            result = QBrush(STRAY_COLOR)
        elif column in (COL_FILE, COL_FOLDER) and self._linked_but_different(track):
            result = QBrush(DIFFERENT_COLOR)
        elif column == COL_DEVICE:
            action = self._action(track)
            status, _phone_track, linked = self.owner.device_state(track)
            if action:
                result = QBrush(self.pending_look[action][1])
            elif status != DEVICE_ABSENT and not linked:
                result = QBrush(PROBABLE_COLOR)
            else:
                color = DEVICE_COLOR.get(status)
                result = QBrush(color) if color is not None else None
        return result

    def _linked_but_different(self, track) -> bool:
        """Il file è la sorgente certa di un brano dell'iPhone (registro) e i tag sono diversi (⟳)."""
        result = False
        if self.owner.phone_known() and not track.error:
            status, _phone_track, linked = self.owner.device_state(track)
            result = linked and status == DEVICE_STALE
        return result

    def _tooltip(self, track, column: int):
        result = None
        if track.error:
            result = tr(track.error)
        elif column == COL_FOLDER and self.owner.stray_folder(track):
            result = tr(f"{track.path}\nIl resto dell'album è in un'altra cartella:\n{self.owner.stray_folder(track)}\n"
                        "Sull'iPhone questi brani finiscono nello stesso album.")
        elif column in (COL_FILE, COL_FOLDER) and self._linked_but_different(track):
            result = tr(f"{track.path}\nSull'iPhone questo brano ha tag diversi: Usa i tag da PC a iPhone o da "
                        "iPhone a PC (tasto destro) sceglie quali tenere")
        elif column in (COL_FILE, COL_FOLDER):
            result = str(track.path)
        elif column == COL_TITLE and self.owner.overlay.is_edited(track.path):
            result = tr("Modificato per l'iPhone (il file sul PC non cambia):\n" + self.owner.overlay.describe(track))
        return result

    def checkable(self, track) -> bool:
        """La spunta si può cambiare: un brano da inviare, uno collegato dal registro, o uno con un'azione in attesa;
        non un brano abbinato solo per i tag (non si toglie con una spunta)."""
        result = False
        if self.owner.phone_known() and not track.error:
            status, _phone_track, linked = self.owner.device_state(track)
            result = status == DEVICE_ABSENT or linked or bool(self._action(track))
        return result

    def data(self, index, role=Qt.DisplayRole):
        result = None
        if index.isValid():
            track = self.rows[index.row()]
            column = index.column()
            if role == Qt.DisplayRole:
                result = self._text(track, column)
            elif role == Qt.ForegroundRole:
                result = self._foreground(track, column)
            elif role == Qt.FontRole and column == COL_TITLE and self.owner.overlay.is_edited(track.path):
                result = self._italic
            elif role == Qt.FontRole and column == COL_FOLDER and self.owner.stray_folder(track):
                result = self._bold
            elif role == Qt.ToolTipRole:
                result = self._tooltip(track, column)
            elif role == Qt.TextAlignmentRole and column == COL_DEVICE:
                result = int(Qt.AlignCenter)
            elif role == Qt.CheckStateRole and column == COL_DEVICE and self.owner.phone_known() and not track.error:
                status = self.owner.device_state(track)[0]
                result = Qt.Checked if wanted(status, self._action(track)) else Qt.Unchecked
            elif role == Qt.BackgroundRole:
                result = self._background(index.row(), track)
        return result

    def flags(self, index):
        result = Qt.NoItemFlags
        if index.isValid():
            result = Qt.ItemIsEnabled | Qt.ItemIsSelectable
            if index.column() == COL_DEVICE and self.checkable(self.rows[index.row()]):
                result |= Qt.ItemIsUserCheckable
        return result

    def setData(self, index, value, role=Qt.EditRole) -> bool:
        result = False
        if index.isValid() and role == Qt.CheckStateRole and index.column() == COL_DEVICE:
            checked = Qt.CheckState(value) == Qt.Checked if not isinstance(value, bool) else value
            self.owner.device_checked(index.row(), checked)
            result = True
        return result

    # ------------------------------------------------------------------ ordinamento

    def _sort_key(self, column: int):
        if column == COL_NUMBER:
            result = track_sort_key
        elif column == COL_DEVICE:
            result = self._device_order
        elif column == COL_LENGTH:
            result = lambda track: track.length   # noqa: E731
        elif column == COL_FILE:
            result = lambda track: track.path.name.lower()   # noqa: E731
        elif column == COL_FOLDER:
            result = lambda track: str(track.path).lower()   # noqa: E731
        else:
            result = lambda track: self._text(track, column).lower()   # noqa: E731
        return result

    def _device_order(self, track) -> int:
        status, _phone_track, linked = self.owner.device_state(track)
        result = PROBABLE_ORDER if status != DEVICE_ABSENT and not linked else DEVICE_ORDER[status]
        return result

    def sort(self, column: int, order=Qt.AscendingOrder) -> None:
        """Ordina per colonna mantenendo la selezione; -1 (nessun ordinamento) lascia l'ordine Artista/Album/Traccia."""
        if 0 <= column < len(COLUMNS) and self.rows:
            self.layoutAboutToBeChanged.emit()
            persistent = self.persistentIndexList()
            before = []
            for index in persistent:
                before.append((self.rows[index.row()], index.column()))
            self.rows.sort(key=self._sort_key(column), reverse=order == Qt.DescendingOrder)
            self._update_bands()
            position = {}
            for row, track in enumerate(self.rows):
                position[id(track)] = row
            after = []
            for track, index_column in before:
                after.append(self.index(position[id(track)], index_column))
            self.changePersistentIndexList(persistent, after)
            self.layoutChanged.emit()
