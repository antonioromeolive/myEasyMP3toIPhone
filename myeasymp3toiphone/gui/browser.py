# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Il navigatore della Libreria: due elenchi affiancati, Artisti e Album, ognuno ordinabile cliccando
sull'intestazione, che filtrano i brani mostrati in tabella.

    Artisti: un artista (o più, con Ctrl/Maiusc) -> l'elenco Album mostra solo i suoi album, la tabella i suoi brani
    Album:   un album (o più) -> la tabella mostra solo quei brani
    "(Tutti …)", sempre in cima, toglie il filtro di quell'elenco.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .album_check_dialog import status_icon

SORT_ROLE = Qt.UserRole + 1    # il valore con cui si ordina una colonna (testo minuscolo o numero)
KEY_ROLE = Qt.UserRole         # l'artista, o la coppia (artista, album)


class SortableItem(QTreeWidgetItem):
    """Una riga ordinabile per valore; la riga "(Tutti …)" resta sempre in cima, in entrambi i versi."""

    def __init__(self, texts: list, sort_values: list, pinned: bool = False) -> None:
        super().__init__(texts)
        self.pinned = pinned
        for column, value in enumerate(sort_values):
            self.setData(column, SORT_ROLE, value)
        for column in range(1, len(texts)):
            if isinstance(sort_values[column], int):
                self.setTextAlignment(column, Qt.AlignRight | Qt.AlignVCenter)

    def __lt__(self, other) -> bool:
        tree = self.treeWidget()
        ascending = tree is None or tree.header().sortIndicatorOrder() == Qt.AscendingOrder
        if self.pinned or other.pinned:
            if ascending:
                result = self.pinned and not other.pinned
            else:
                result = other.pinned and not self.pinned
        else:
            column = tree.sortColumn() if tree is not None else 0
            mine = self.data(column, SORT_ROLE)
            theirs = other.data(column, SORT_ROLE)
            if type(mine) is type(theirs):
                result = mine < theirs
            else:
                result = str(mine) < str(theirs)
        return result


def _make_list(headers: list) -> QTreeWidget:
    widget = QTreeWidget()
    widget.setHeaderLabels(headers)
    widget.setRootIsDecorated(False)
    widget.setUniformRowHeights(True)
    widget.setAlternatingRowColors(True)
    widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
    widget.setSortingEnabled(True)
    header = widget.header()
    header.setSortIndicatorShown(True)
    header.setSectionResizeMode(0, QHeaderView.Stretch)
    header.setStretchLastSection(False)
    for column in range(1, len(headers)):
        header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
    widget.sortByColumn(0, Qt.AscendingOrder)
    return widget


class LibraryBrowser(QWidget):
    filter_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._groups = {}
        self._check_results = {}
        self.artists = _make_list(["Artista", "Album", "Brani"])
        self.albums = _make_list(["Album", "Artista", "Anno", "Brani"])
        self.artists.itemSelectionChanged.connect(self._artists_changed)
        self.albums.itemSelectionChanged.connect(self.filter_changed.emit)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        for title, widget in (("Artisti", self.artists), ("Album", self.albums)):
            column = QVBoxLayout()
            label = QLabel(f"<b>{title}</b>")
            column.addWidget(label)
            column.addWidget(widget)
            layout.addLayout(column, 1)

    # ------------------------------------------------------------------ dati

    def set_data(self, groups: dict, check_results: dict) -> None:
        """groups: {(artista, album): [brani]} (library.group_by_album). Conserva le selezioni ancora valide."""
        self._groups = groups
        self._check_results = check_results
        chosen_artists = self.selected_artists()
        chosen_albums = self.selected_albums()
        by_artist = {}
        for (artist, album), tracks in groups.items():
            entry = by_artist.setdefault(artist, [0, 0])
            entry[0] += 1
            entry[1] += len(tracks)
        self.artists.blockSignals(True)
        self.artists.setSortingEnabled(False)
        self.artists.clear()
        total = 0
        for _artist, (_albums, count) in by_artist.items():
            total += count
        self.artists.addTopLevelItem(SortableItem([f"(Tutti gli artisti: {len(by_artist)})", str(len(groups)), str(total)],
                                           ["", len(groups), total], pinned=True))
        for artist, (album_count, count) in by_artist.items():
            item = SortableItem([artist, str(album_count), str(count)], [artist.lower(), album_count, count])
            item.setData(0, KEY_ROLE, artist)
            self.artists.addTopLevelItem(item)
            if artist in chosen_artists:
                item.setSelected(True)
        self.artists.setSortingEnabled(True)
        self.artists.blockSignals(False)
        self._fill_albums(chosen_albums)

    def _fill_albums(self, keep: set) -> None:
        artists = self.selected_artists()
        self.albums.blockSignals(True)
        self.albums.setSortingEnabled(False)
        self.albums.clear()
        rows = []
        for key, tracks in self._groups.items():
            if not artists or key[0] in artists:
                rows.append((key, tracks))
        shown_tracks = 0
        for _key, tracks in rows:
            shown_tracks += len(tracks)
        label = "(Tutti gli album" + (" degli artisti scelti" if artists else "") + f": {len(rows)})"
        self.albums.addTopLevelItem(SortableItem([label, "", "", str(shown_tracks)], ["", "", "", shown_tracks], pinned=True))
        for key, tracks in rows:
            artist, album = key
            years = sorted({track.tags.year for track in tracks if track.tags.year})
            year = years[0] if len(years) == 1 else ("-".join([years[0], years[-1]]) if years else "")
            item = SortableItem([album, artist, year, str(len(tracks))], [album.lower(), artist.lower(), year, len(tracks)])
            item.setData(0, KEY_ROLE, key)
            result = self._check_results.get(key)
            if result is not None:
                item.setIcon(0, status_icon(self, result.status))
                item.setToolTip(0, result.status_text())
            self.albums.addTopLevelItem(item)
            if key in keep:
                item.setSelected(True)
        self.albums.setSortingEnabled(True)
        self.albums.blockSignals(False)

    # ------------------------------------------------------------------ selezione

    def _selected_keys(self, widget: QTreeWidget) -> set:
        keys = set()
        pinned = False
        for item in widget.selectedItems():
            if getattr(item, "pinned", False):
                pinned = True
            else:
                keys.add(item.data(0, KEY_ROLE))
        if pinned:
            keys = set()
        return keys

    def selected_artists(self) -> set:
        result = self._selected_keys(self.artists)
        return result

    def selected_albums(self) -> set:
        result = self._selected_keys(self.albums)
        return result

    def _artists_changed(self) -> None:
        """Un artista scelto (o "(Tutti)") mostra tutti i suoi brani: la scelta di album fatta prima si azzera."""
        self._fill_albums(set())
        self.filter_changed.emit()

    def track_filter(self):
        """None = tutti i brani; altrimenti (artisti, album): gli album scelti contano più degli artisti."""
        artists = self.selected_artists()
        albums = self.selected_albums()
        if not artists and not albums:
            result = None
        else:
            result = (artists, albums)
        return result

    def clear_selection(self) -> None:
        self.artists.blockSignals(True)
        self.artists.clearSelection()
        self.artists.blockSignals(False)
        self._fill_albums(set())
