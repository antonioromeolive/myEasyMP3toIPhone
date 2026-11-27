# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Il navigatore della Libreria: due elenchi affiancati, Artisti e Album, ognuno ordinabile cliccando
sull'intestazione, che filtrano i brani mostrati in tabella.

    Artisti: un artista (o più, con Ctrl/Maiusc) -> l'elenco Album mostra solo i suoi album, la tabella i suoi brani
    Album:   un album (o più) -> la tabella mostra solo quei brani
    "(Tutti …)", sempre in cima, toglie il filtro di quell'elenco.

Tasto destro su una riga: la sceglie (se non lo era già) e chiede alla finestra il menu (menu_requested) per tutti
i brani della scelta (menu_tracks), interi: artisti o album completi, anche se Cerca ne nasconde una parte.

Con la musica dell'iPhone nota, ogni artista e album ha la spunta "sull'iPhone" a tre stati (tutti i brani, alcuni,
nessuno), in corsivo blu se dentro c'è una modifica in attesa; cliccarla mette o toglie tutti i suoi brani
(phone_toggled, poi in attesa fino ad Applica).
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .album_check_dialog import status_icon
from ..i18n import tr

SORT_ROLE = Qt.UserRole + 1    # il valore con cui si ordina una colonna (testo minuscolo o numero)
KEY_ROLE = Qt.UserRole         # l'artista, o la coppia (artista, album)
SHOWN_CHECK_ROLE = Qt.UserRole + 2   # lo stato della spunta "sull'iPhone" com'è stato mostrato (per riconoscere un clic)


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


def _make_list(headers: list, widths: list) -> QTreeWidget:
    """Un elenco con le colonne tutte trascinabili, nei due versi (una colonna "Stretch" o "ResizeToContents" non si
    può trascinare), con le larghezze iniziali date; se non ci stanno compare la barra di scorrimento."""
    widget = QTreeWidget()
    widget.setHeaderLabels(headers)
    widget.setRootIsDecorated(False)
    widget.setUniformRowHeights(True)
    widget.setAlternatingRowColors(True)
    widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
    widget.setSortingEnabled(True)
    header = widget.header()
    header.setSortIndicatorShown(True)
    header.setSectionResizeMode(QHeaderView.Interactive)
    header.setStretchLastSection(False)
    header.setMinimumSectionSize(30)
    for column, width in enumerate(widths):
        widget.setColumnWidth(column, width)
    widget.sortByColumn(0, Qt.AscendingOrder)
    return widget


class LibraryBrowser(QWidget):
    filter_changed = Signal()
    phone_toggled = Signal(list, bool)     # (brani, spunta messa): l'artista o l'album intero sull'iPhone o no
    menu_requested = Signal(QPoint)        # tasto destro su una riga: il punto dello schermo dove aprire il menu

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._groups = {}
        self._check_results = {}
        self.phone_state = None            # brani -> (Qt.CheckState, in attesa) o None; lo imposta la finestra
        self.menu_tracks = []              # i brani della scelta su cui si è aperto l'ultimo menu (tasto destro)
        self.artists = _make_list(["Artista", "Album", "Brani"], [260, 55, 60])
        self.albums = _make_list(["Album", "Artista", "Anno", "Brani"], [300, 220, 70, 55])
        self.artists.itemSelectionChanged.connect(self._artists_changed)
        self.albums.itemSelectionChanged.connect(self.filter_changed.emit)
        self.artists.itemChanged.connect(self._item_changed)
        self.albums.itemChanged.connect(self._item_changed)
        for widget in (self.artists, self.albums):
            widget.setContextMenuPolicy(Qt.CustomContextMenu)
            widget.customContextMenuRequested.connect(
                lambda position, widget=widget: self._menu_at(widget, position))
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
        self.artists.addTopLevelItem(SortableItem([tr(f"(Tutti gli artisti: {len(by_artist)})"), str(len(groups)), str(total)],
                                           ["", len(groups), total], pinned=True))
        for artist, (album_count, count) in by_artist.items():
            item = SortableItem([artist, str(album_count), str(count)], [artist.lower(), album_count, count])
            item.setData(0, KEY_ROLE, artist)
            self._show_phone_state(item)
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
        label = tr("(Tutti gli album") + (tr(" degli artisti scelti") if artists else "") + f": {len(rows)})"
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
            self._show_phone_state(item)
            self.albums.addTopLevelItem(item)
            if key in keep:
                item.setSelected(True)
        self.albums.setSortingEnabled(True)
        self.albums.blockSignals(False)

    def refresh_check_icons(self, check_results: dict) -> None:
        """Le icone di Verifica album online, man mano che arrivano gli esiti (senza rifare gli elenchi). Con i segnali
        fermi: cambiare l'icona di una riga non è un clic sulla sua spunta "sull'iPhone"."""
        self._check_results = check_results
        self.albums.blockSignals(True)
        for index in range(self.albums.topLevelItemCount()):
            item = self.albums.topLevelItem(index)
            key = item.data(0, KEY_ROLE)
            result = check_results.get(key) if isinstance(key, tuple) else None
            if result is not None:
                item.setIcon(0, status_icon(self, result.status))
                item.setToolTip(0, result.status_text())
        self.albums.blockSignals(False)

    # ------------------------------------------------------------------ spunte "sull'iPhone"

    def album_tracks(self, key) -> list:
        """I brani di un album (la chiave (artista, album) di selected_albums), per disco e numero."""
        result = list(self._groups.get(key, []))
        return result

    def tracks_of(self, item) -> list:
        """I brani di una riga: un artista (tutti i suoi album) o un album."""
        key = item.data(0, KEY_ROLE)
        result = []
        if isinstance(key, tuple):
            result = list(self._groups.get(key, []))
        elif key is not None:
            for (artist, _album), tracks in self._groups.items():
                if artist == key:
                    result += tracks
        return result

    def _show_phone_state(self, item) -> None:
        state = self.phone_state(self.tracks_of(item)) if self.phone_state is not None else None
        font = item.font(0)
        if state is None:
            item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
            item.setData(0, Qt.CheckStateRole, None)
            item.setData(0, SHOWN_CHECK_ROLE, None)
            font.setItalic(False)
            item.setForeground(0, QBrush())
        else:
            check, waiting = state
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, check)
            item.setData(0, SHOWN_CHECK_ROLE, int(check.value if hasattr(check, "value") else check))
            font.setItalic(waiting)
            item.setForeground(0, QBrush(QColor(40, 110, 230)) if waiting else QBrush())
        item.setFont(0, font)

    def refresh_phone_states(self) -> None:
        """Le spunte dopo un cambio (spunte in tabella, musica dell'iPhone letta, modifiche applicate)."""
        for widget in (self.artists, self.albums):
            widget.blockSignals(True)
            for index in range(widget.topLevelItemCount()):
                item = widget.topLevelItem(index)
                if not getattr(item, "pinned", False):
                    self._show_phone_state(item)
            widget.blockSignals(False)

    def _item_changed(self, item, column: int) -> None:
        """La spunta "sull'iPhone" cliccata. Solo se il suo stato è cambiato davvero rispetto a quello mostrato:
        un'altra modifica della riga (icona, testo, colore) non mette niente in attesa."""
        if column == 0 and self.phone_state is not None and not getattr(item, "pinned", False):
            check = item.checkState(0)
            now = int(check.value if hasattr(check, "value") else check)
            shown = item.data(0, SHOWN_CHECK_ROLE)
            tracks = self.tracks_of(item) if shown is not None and now != shown else []
            if tracks:
                item.setData(0, SHOWN_CHECK_ROLE, now)
                self.phone_toggled.emit(tracks, check == Qt.Checked)

    # ------------------------------------------------------------------ tasto destro

    def _menu_at(self, widget: QTreeWidget, position) -> None:
        """La riga sotto il mouse diventa la scelta (se non è già tra quelle scelte), poi il menu sui suoi brani
        (menu_tracks)."""
        item = widget.itemAt(position)
        if item is not None:
            if not item.isSelected():
                widget.clearSelection()
                item.setSelected(True)
            self.menu_tracks = self._tracks_of_selection(widget)
            self.menu_requested.emit(widget.viewport().mapToGlobal(position))

    def _tracks_of_selection(self, widget: QTreeWidget) -> list:
        """Tutti i brani delle righe scelte di un elenco, interi (Cerca non conta); con "(Tutti …)" tutte le righe
        dell'elenco."""
        pinned = False
        for item in widget.selectedItems():
            if getattr(item, "pinned", False):
                pinned = True
        rows = []
        for index in range(widget.topLevelItemCount()):
            item = widget.topLevelItem(index)
            if not getattr(item, "pinned", False) and (pinned or item.isSelected()):
                rows.append(item)
        result = []
        seen = set()
        for item in rows:
            for track in self.tracks_of(item):
                if id(track) not in seen:
                    seen.add(id(track))
                    result.append(track)
        return result

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
