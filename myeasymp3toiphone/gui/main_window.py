# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Finestra principale di myEasyMP3toIPhone. Le cartelle aperte sono in sola lettura: le modifiche dei tag restano in
sospeso (overlay) e vanno solo sulle copie inviate all'iPhone, esportate o importate."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QByteArray, QItemSelectionModel, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QBrush, QColor, QFont, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow, QMenu,
    QMessageBox, QScrollArea, QSplitter, QStyle, QTableWidget, QTableWidgetItem, QTabWidget,
    QToolBar, QVBoxLayout, QWidget,
)

from ..albumcheck import MusicBrainzClient, check_album
from ..config import PRODUCT, AppSettings, config_dir
from ..library import assign_groups, copy_organized, group_by_album, scan_folder, track_sort_key
from .. import provenance
from ..phone_library import (
    DEVICE_ABSENT, DEVICE_SAME, DEVICE_STALE, PhoneIndex, comparison, device_status, load_listing,
    save_listing,
)
from ..overlay import TagOverlay
from ..tag_cache import TagCache
from ..tags import prepare_copy, protect_folder, read_cover
from ..version import app_version
from .about import AboutDialog
from .album_check_dialog import AlbumCheckDialog
from .browser import LibraryBrowser
from .compare_tip import comparison_html, show_on_tooltip
from .iphone_panel import IPhonePanel
from .scan_dialog import ScanLauncher
from .settings_dialog import SettingsDialog
from .tag_editor import TagEditor
from .worker import TaskRunner

APP_NAME = PRODUCT
# Il filtro per formato: (etichetta, estensioni); None = tutti
FORMATS = (("Tutti i formati", None), ("MP3", (".mp3",)), ("FLAC", (".flac",)), ("M4A / AAC", (".m4a",)),
           ("OGG / Opus", (".ogg", ".opus")))
SECONDS_PER_ALBUM_CHECK = 2.5

COLUMNS = ["#", "iPhone", "Titolo", "Artista", "Album", "Anno", "Genere", "Durata", "File"]
COL_NUMBER, COL_DEVICE, COL_TITLE, COL_ARTIST, COL_ALBUM, COL_YEAR, COL_GENRE, COL_LENGTH, COL_FILE = range(9)
DEVICE_TEXT = {DEVICE_SAME: "✔", DEVICE_STALE: "⟳", DEVICE_ABSENT: ""}
DEVICE_TIP = {DEVICE_SAME: "Nell'app Musica dell'iPhone c'è questo brano, con gli stessi tag",
              DEVICE_STALE: "Nell'app Musica dell'iPhone c'è questo brano, ma con tag diversi:",
              DEVICE_ABSENT: "Non è nell'app Musica dell'iPhone"}



def _format_length(seconds: float) -> str:
    total = int(round(seconds))
    result = f"{total // 60}:{total % 60:02d}"
    return result


def _number_item(value: Optional[int]) -> QTableWidgetItem:
    item = QTableWidgetItem()
    if value is not None:
        item.setData(Qt.DisplayRole, value)
    return item


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        # la versione intera, con la data: due build -dev dello stesso numero si distinguono (come myCalibreTools)
        self.setWindowTitle(f"{APP_NAME} {app_version()}")
        self.resize(1400, 820)
        self.app_settings = AppSettings.load()
        self._phone_index: Optional[PhoneIndex] = None   # la musica dell'app Musica, per la colonna "iPhone"
        self.phone_tracks = []     # la musica dell'app Musica (phone_library.PhoneTrack), letta o ricordata
        self.phone_label = ""      # di quale iPhone e quando
        self.registry = provenance.Registry.load(config_dir())   # da dove viene ogni brano dell'iPhone
        self.overlay = TagOverlay(config_dir())
        self.tag_cache = TagCache(config_dir())
        self.open_on_start: Optional[Path] = None   # --open CARTELLA: aperta all'avvio al posto della Libreria
        if self.app_settings.window_geometry:
            self.restoreGeometry(QByteArray.fromBase64(self.app_settings.window_geometry.encode("ascii")))
        self.mb_client = MusicBrainzClient()
        self.tracks = []
        self._visible = []
        self.root_folder: Optional[Path] = None
        self.check_results = {}

        self.runner = TaskRunner(self.statusBar())
        self.runner.error.connect(lambda title, message: QMessageBox.warning(self, title, message))
        self.runner.busy_changed.connect(self._busy_changed)

        self._build_toolbar()
        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_library_tab(), "PC")
        self.iphone_panel = IPhonePanel(self)
        self._tabs.addTab(self.iphone_panel, "iPhone")
        self.setCentralWidget(self._tabs)
        self.scan_launcher = ScanLauncher(self)
        QTimer.singleShot(0, self._startup)

    # ================================================================== costruzione interfaccia

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Azioni")
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.setIconSize(QSize(28, 28))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        style = self.style()
        definitions = [
            ("Libreria", QStyle.SP_DirHomeIcon, self.open_library,
             "Mostra la tua Libreria musicale", "Ctrl+L"),
            ("Apri cartella", QStyle.SP_DirOpenIcon, self._open_folder,
             "Mostra i brani di una cartella qualsiasi, in sola lettura: i file non vengono mai modificati",
             "Ctrl+O"),
            ("Importa cartella", QStyle.SP_ArrowDown, self._import_folder,
             "Copia una cartella nella Libreria, ordinandola per Artista/Album", "Ctrl+I"),
            ("Esporta", QStyle.SP_ArrowUp, self._export_selection,
             "Copia i brani selezionati in una cartella, ordinati per Artista/Album", "Ctrl+E"),
            ("Verifica album", QStyle.SP_DialogApplyButton, self._check_albums,
             "Controlla su MusicBrainz che gli album selezionati (o tutti) siano completi", "F5"),
            ("Controlla la musica", QStyle.SP_FileDialogContentsView, self._scan,
             "Cerca i problemi nella cartella aperta o sull'iPhone: file non aggiornati, album con pochi brani, "
             "collezioni divise su più album, brani duplicati (con l'AI, se configurata)", "F6"),
            ("Impostazioni", QStyle.SP_FileDialogDetailedView, self._open_settings,
             "Cartella della Libreria, profili AI e chiavi", "Ctrl+,"),
            ("Informazioni", QStyle.SP_MessageBoxInformation, self._open_about,
             "Versione, cartella dati, variabili d'ambiente e dove sono salvate le chiavi", None),
        ]
        self._task_actions = []
        for text, icon, slot, tip, shortcut in definitions:
            action = QAction(style.standardIcon(icon), text, self)
            action.setToolTip(tip)
            action.setStatusTip(tip)
            if shortcut is not None:
                action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(slot)
            toolbar.addAction(action)
            self._task_actions.append(action)

    def _build_library_tab(self) -> QWidget:
        self._search = QLineEdit()
        self._search.setPlaceholderText("Cerca per titolo, artista o album…")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(lambda _text: self._fill_table())
        self._folder_label = QLabel()
        self._folder_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._format = QComboBox()
        self._format.setToolTip("Mostra solo i brani di un formato: vale per gli elenchi, la tabella, l'esportazione, "
                                "Verifica album, la scansione e l'invio all'iPhone")
        for label, _extensions in FORMATS:
            self._format.addItem(label)
        self._format.currentIndexChanged.connect(lambda _index: self._rebuild_views())
        top = QHBoxLayout()
        top.addWidget(self._search, 1)
        top.addWidget(QLabel("Formato:"))
        top.addWidget(self._format)
        top.addWidget(self._folder_label, 1)

        self.browser = LibraryBrowser()
        self.browser.filter_changed.connect(self._fill_table)

        self._table = QTableWidget(0, len(COLUMNS))
        self._table.setHorizontalHeaderLabels(COLUMNS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setWordWrap(False)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        # nessun ordinamento iniziale: si mantiene l'ordine Artista/Album/Disco/Traccia finché l'utente non clicca
        # un'intestazione di colonna (Artista, Album, Titolo…), che poi mostra la freccia dell'ordinamento
        header.setSortIndicator(-1, Qt.AscendingOrder)
        header.setSortIndicatorShown(True)
        widths = [40, 50, 230, 160, 180, 50, 90, 55]
        for column, width in enumerate(widths):
            self._table.setColumnWidth(column, width)
        self._table.itemSelectionChanged.connect(self._selection_changed)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._table_menu)
        self._table.viewport().installEventFilter(self)    # il suggerimento della colonna iPhone, al passaggio

        self.editor = TagEditor()
        self.editor.apply_requested.connect(self._apply_tag_changes)
        self.editor.revert_requested.connect(self._revert_tag_changes)
        self.editor.cover_provider = self._cover_of
        self.editor.edited_check = lambda track: self.overlay.is_edited(track.path)
        self.editor.renumber_requested.connect(self._renumber_selection)
        editor_scroll = QScrollArea()
        editor_scroll.setWidget(self.editor)
        editor_scroll.setWidgetResizable(True)
        editor_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        editor_scroll.setMinimumWidth(320)

        left = QSplitter(Qt.Vertical)
        left.addWidget(self.browser)
        left.addWidget(self._table)
        left.setSizes([240, 520])
        left.setStretchFactor(1, 1)
        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(editor_scroll)
        splitter.setSizes([1040, 330])
        splitter.setStretchFactor(0, 1)

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addLayout(top)
        layout.addWidget(splitter, 1)
        return tab

    # ================================================================== avvio e cartelle

    def _load_device_listing(self) -> None:
        """L'ultimo elenco della musica dell'iPhone, per la colonna "iPhone" e la scheda iPhone anche a telefono
        scollegato."""
        listing = load_listing(config_dir())
        if listing:
            self._show_phone_tracks(listing["tracks"], f"{listing['device']}, elenco del {listing['saved_at']}")

    def show_iphone_connected(self, connected: bool) -> None:
        """Il titolo della scheda iPhone dice se è connesso ("iPhone ●" verde), anche quando si guarda la scheda PC."""
        index = self._tabs.indexOf(self.iphone_panel) if hasattr(self, "iphone_panel") else -1
        if index >= 0:
            self._tabs.setTabText(index, "iPhone ●" if connected else "iPhone")
            self._tabs.tabBar().setTabTextColor(index, QColor(60, 180, 100) if connected else QColor())
            self._tabs.setTabToolTip(index, "iPhone connesso" if connected else "iPhone non connesso")

    def set_registry(self, registry) -> None:
        """Il registro della provenienza è cambiato (collegamenti nuovi o tolti): confronti e viste da rifare."""
        self.registry = registry
        self._phone_index = PhoneIndex(self.phone_tracks, registry.links_here())
        self._fill_table()
        self.iphone_panel.pc_changed()

    def set_phone_tracks(self, tracks: list, device: str) -> None:
        """Chiamata dalla scheda iPhone quando ha letto la musica dell'app Musica: la salva e aggiorna le viste."""
        try:
            save_listing(config_dir(), device, tracks)
        except OSError:
            pass  # la colonna funziona lo stesso fino alla chiusura
        self._show_phone_tracks(tracks, f"{device}, letto ora")

    def _show_phone_tracks(self, tracks: list, label: str) -> None:
        self.phone_tracks = list(tracks)
        self.phone_label = label
        self._phone_index = PhoneIndex(tracks, self.registry.links_here())
        header = self._table.horizontalHeaderItem(COL_DEVICE)
        if header is not None:
            header.setToolTip(f"Nell'app Musica dell'iPhone ({label}): ✔ stesso brano, ⟳ stesso brano con tag "
                              "diversi, vuoto = non c'è")
        self.iphone_panel.set_phone_tracks(tracks, label)
        self._fill_table()

    def _startup(self) -> None:
        """All'avvio: --open, altrimenti l'ultima cartella usata (se c'è ancora), altrimenti la Libreria."""
        self._load_device_listing()
        library = self.library_dir()
        last = Path(self.app_settings.last_opened) if self.app_settings.last_opened else None
        if self.open_on_start is not None:
            self.load_folder(self.open_on_start)
        elif last is not None and last.is_dir():
            self.load_folder(last)
        elif library.is_dir():
            self.load_folder(library)
            if last is not None:
                self.statusBar().showMessage(f"L'ultima cartella usata non è disponibile ({last}): apro la "
                                             "Libreria", 15000)
        else:
            self.statusBar().showMessage(
                "Benvenuto! Premi \"Apri cartella\" per vedere la tua musica, o \"Importa cartella\" per copiarla "
                "nella Libreria.")

    def library_dir(self) -> Path:
        result = self.app_settings.library_path()
        return result

    def save_settings(self) -> None:
        self.app_settings.save()

    def _open_settings(self) -> None:
        before = self.library_dir()
        dialog = SettingsDialog(self.app_settings, self)
        if dialog.exec() and self.library_dir() != before:
            self.open_library()

    def _open_about(self) -> None:
        AboutDialog(self).exec()

    def _scan(self) -> None:
        self.scan_launcher.start()

    def open_library(self) -> None:
        library = self.library_dir()
        library.mkdir(parents=True, exist_ok=True)
        self.load_folder(library)

    def _open_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Cartella da aprire",
                                                  self.app_settings.last_folder)
        if folder:
            self.app_settings.last_folder = folder
            self.save_settings()
            self.load_folder(Path(folder))

    def load_folder(self, folder: Path) -> None:
        def work(progress, cancel):
            value = scan_folder(folder, progress, cancel, self.tag_cache)
            return value

        def done(tracks):
            protect_folder(folder)
            self.overlay.apply(tracks)
            self.tracks = tracks
            self.root_folder = folder
            self.app_settings.last_opened = str(folder)   # riaperta al prossimo avvio
            self.save_settings()
            self.check_results = {}
            if folder == self.library_dir():
                label = f"Libreria: {folder}"
            else:
                label = f"Cartella: {folder}"
            self._folder_label.setText(label)
            self._rebuild_views()
            self._tabs.setCurrentIndex(0)
            self.statusBar().showMessage(f"{len(tracks)} brani caricati (sola lettura: i file non vengono "
                                         "modificati)", 8000)
            self.iphone_panel.check_missing_sources()

        self.runner.run("Lettura brani", work, done)

    # ================================================================== navigatore e tabella

    def format_tracks(self) -> list:
        """I brani del formato scelto (tutti con "Tutti i formati")."""
        extensions = FORMATS[max(0, self._format.currentIndex())][1]
        if extensions is None:
            result = list(self.tracks)
        else:
            result = []
            for track in self.tracks:
                if track.path.suffix.lower() in extensions:
                    result.append(track)
        return result

    def _update_format_counts(self) -> None:
        counts = {}
        for track in self.tracks:
            suffix = track.path.suffix.lower()
            counts[suffix] = counts.get(suffix, 0) + 1
        for index, (label, extensions) in enumerate(FORMATS):
            if extensions is None:
                total = len(self.tracks)
            else:
                total = 0
                for extension in extensions:
                    total += counts.get(extension, 0)
            self._format.setItemText(index, f"{label} ({total})")

    def _rebuild_views(self, keep_tracks: Optional[set] = None) -> None:
        assign_groups(self.tracks)
        self._update_format_counts()
        self.browser.set_data(group_by_album(self.format_tracks()), self.check_results)
        self._fill_table(keep_tracks)
        self.iphone_panel.pc_changed()

    def _track_filter(self):
        """None = tutti; altrimenti (artisti, album) scelti nel navigatore."""
        result = self.browser.track_filter()
        return result

    @staticmethod
    def _passes(track, track_filter) -> bool:
        if track_filter is None:
            result = True
        else:
            artists, albums = track_filter
            if albums:
                result = track.album_key in albums
            else:
                result = track.album_key[0] in artists
        return result

    def _visible_tracks(self) -> list:
        track_filter = self._track_filter()
        needle = self._search.text().strip().lower()
        visible = []
        for track in self.format_tracks():
            shown = self._passes(track, track_filter)
            if shown and needle:
                haystack = " ".join([track.title, track.tags.artist, track.tags.album_artist,
                                     track.tags.album]).lower()
                shown = needle in haystack
            if shown:
                visible.append(track)
        visible.sort(key=lambda t: (t.album_key[0].lower(), t.album_key[1].lower()) + track_sort_key(t))
        return visible

    def _fill_table(self, keep_tracks: Optional[set] = None) -> None:
        if keep_tracks is None:
            keep_tracks = set()
            for track in self._selected_table_tracks():
                keep_tracks.add(id(track))
        self._visible = self._visible_tracks()
        self._table.blockSignals(True)
        self._table.setSortingEnabled(False)
        self._table.clearContents()
        self._table.setRowCount(len(self._visible))
        for row, track in enumerate(self._visible):
            tags = track.tags
            number = _number_item(tags.track_number)
            number.setData(Qt.UserRole, row)
            values = {
                COL_TITLE: track.title,
                COL_ARTIST: tags.artist,
                COL_ALBUM: tags.album,
                COL_YEAR: tags.year,
                COL_GENRE: tags.genre,
                COL_LENGTH: _format_length(track.length),
                COL_FILE: track.path.name,
            }
            status = DEVICE_ABSENT
            if self._phone_index is not None:
                status, _phone_track, _found = device_status(track, self._phone_index)
            values[COL_DEVICE] = DEVICE_TEXT[status]
            self._table.setItem(row, COL_NUMBER, number)
            for column, text in values.items():
                item = QTableWidgetItem(text)
                if track.error:
                    item.setForeground(QBrush(QColor(200, 40, 40)))
                    item.setToolTip(track.error)
                self._table.setItem(row, column, item)
            self._table.item(row, COL_FILE).setToolTip(str(track.path))
            if self.overlay.is_edited(track.path):
                title_item = self._table.item(row, COL_TITLE)
                font = QFont(title_item.font())
                font.setItalic(True)
                title_item.setFont(font)
                title_item.setForeground(QBrush(QColor(60, 130, 230)))
                title_item.setToolTip("Modificato per l'iPhone (il file sul PC non cambia):\n"
                                      + self.overlay.describe(track))
            device_item = self._table.item(row, COL_DEVICE)
            device_item.setTextAlignment(Qt.AlignCenter)
            if status == DEVICE_STALE:
                device_item.setForeground(QBrush(QColor(220, 140, 0)))
            elif status == DEVICE_SAME:
                device_item.setForeground(QBrush(QColor(30, 140, 60)))
        self._table.setSortingEnabled(True)
        selection = self._table.selectionModel()
        for row in range(self._table.rowCount()):
            if id(self._track_at_row(row)) in keep_tracks:
                selection.select(self._table.model().index(row, 0),
                                 QItemSelectionModel.Select | QItemSelectionModel.Rows)
        self._table.blockSignals(False)
        self._selection_changed()

    def _track_at_row(self, row: int):
        index = self._table.item(row, COL_NUMBER).data(Qt.UserRole)
        result = self._visible[index]
        return result

    def _selected_rows(self) -> list:
        rows = set()
        for index in self._table.selectionModel().selectedRows():
            rows.add(index.row())
        result = sorted(rows)
        return result

    def _selected_table_tracks(self) -> list:
        result = []
        for row in self._selected_rows():
            result.append(self._track_at_row(row))
        return result

    def eventFilter(self, watched, event) -> bool:
        handled = False
        if watched is self._table.viewport():
            handled = show_on_tooltip(event, self._table, self._table_tooltip_at)
        result = handled or super().eventFilter(watched, event)
        return result

    def _table_tooltip_at(self, position) -> str:
        """Il suggerimento della cella sotto il mouse: per la colonna iPhone la tabella del confronto."""
        row = self._table.rowAt(position.y())
        column = self._table.columnAt(position.x())
        result = ""
        if row >= 0 and column == COL_DEVICE:
            result = self.device_tooltip(self._track_at_row(row))
        elif row >= 0 and column >= 0:
            item = self._table.item(row, column)
            result = item.toolTip() if item is not None else ""
        return result

    def device_tooltip(self, track) -> str:
        result = ""
        if self._phone_index is not None and track is not None:
            status, phone_track, _found = device_status(track, self._phone_index)
            if phone_track is None:
                result = DEVICE_TIP[DEVICE_ABSENT]
            else:
                tags = phone_track.tags
                matched = f"{tags.artist or tags.album_artist} — {tags.title}  ({tags.album})"
                if self._phone_index.via_registry(track):
                    link = self.registry.get(phone_track.sync_id)
                    how = f"Abbinato dal registro della provenienza ({link.how if link else '?'}): certo"
                    certain = True
                else:
                    how = "Abbinato per artista, album e titolo: probabile, non certo"
                    certain = False
                result = comparison_html(DEVICE_TIP[status].rstrip(":"), matched, how, certain,
                                         comparison(track.tags, phone_track.tags))
        return result

    def _table_menu(self, position) -> None:
        """Tasto destro sui brani: invia all'iPhone quelli che non ci sono, rimpiazza quelli con tag diversi."""
        tracks = self._selected_table_tracks()
        if tracks:
            absent = []
            stale = []
            present = 0
            for track in tracks:
                status = DEVICE_ABSENT
                phone_track = None
                if self._phone_index is not None:
                    status, phone_track, _found = device_status(track, self._phone_index)
                if status == DEVICE_ABSENT:
                    absent.append(track)
                elif status == DEVICE_STALE and phone_track.from_computer:
                    stale.append((phone_track, track))
                else:
                    present += 1
            ready = self.iphone_panel.connected and not self.runner.is_busy
            menu = QMenu(self)
            send = menu.addAction(f"Invia all'iPhone ({len(absent)} brani che non ci sono)")
            send.setEnabled(ready and bool(absent))
            send.triggered.connect(lambda: self.iphone_panel.send_tracks(absent))
            replace = menu.addAction(f"Rimpiazza sull'iPhone ({len(stale)} brani con tag diversi ⟳)")
            replace.setEnabled(ready and bool(stale))
            replace.triggered.connect(lambda: self.iphone_panel.replace_pairs(stale))
            if present:
                note = menu.addAction(f"{present} brani già sull'iPhone uguali ✔")
                note.setEnabled(False)
            if not self.iphone_panel.connected:
                for action in (send, replace):
                    action.setToolTip("Connetti l'iPhone")
            menu.setToolTipsVisible(True)
            menu.exec(self._table.viewport().mapToGlobal(position))

    def selected_tracks(self) -> list:
        """Brani selezionati in tabella; altrimenti quelli dell'artista o dell'album scelti negli elenchi."""
        result = self._selected_table_tracks()
        if not result and self._track_filter() is not None:
            result = list(self._visible)
        return result

    def show_tracks(self, paths: set) -> None:
        """Mostra tutti i brani e seleziona quelli indicati (dalla finestra della scansione)."""
        self._tabs.setCurrentIndex(0)
        self._search.blockSignals(True)
        self._search.clear()
        self._search.blockSignals(False)
        self.browser.blockSignals(True)
        self.browser.clear_selection()
        self.browser.blockSignals(False)
        self._format.blockSignals(True)
        self._format.setCurrentIndex(0)
        self._format.blockSignals(False)
        self._rebuild_views()
        keep = set()
        for track in self.tracks:
            if str(track.path) in paths:
                keep.add(id(track))
        self._fill_table(keep)
        rows = self._selected_rows()
        if rows:
            self._table.scrollToItem(self._table.item(rows[0], COL_TITLE))
        self.activateWindow()

    def _selection_changed(self) -> None:
        self.editor.set_tracks(self._selected_table_tracks())

    def _busy_changed(self, busy: bool) -> None:
        for action in self._task_actions:
            action.setEnabled(not busy)
        self.editor.setEnabled(not busy)

    # ================================================================== modifica tag

    def apply_tag_changes(self, pairs: list, cover: Optional[bytes] = None, propagate: bool = True) -> None:
        """pairs: (Track, nuovi TrackTags o None se invariati). Le modifiche restano in sospeso nella cartella dati: i
        file sul PC non cambiano mai; valgono per le copie inviate all'iPhone, esportate o importate. propagate: poi
        chiede se aggiornare anche i brani dell'iPhone che vengono da questi file."""
        for track, new_tags in pairs:
            if new_tags is not None:
                self.overlay.set_tags(track, new_tags)
            if cover is not None:
                self.overlay.set_cover(track, cover)
        try:
            self.overlay.save()
            self.statusBar().showMessage(f"Modifiche salvate per l'iPhone su {len(pairs)} brani: i file sul PC "
                                         "non cambiano", 8000)
        except OSError as exc:
            QMessageBox.warning(self, "Modifiche", f"Modifiche NON salvate nella cartella dati: {exc}")
        self.refresh_after_tag_change()
        if propagate:
            tracks = []
            for track, _new_tags in pairs:
                tracks.append(track)
            self.iphone_panel.offer_phone_update(tracks, cover is not None)

    def _revert_tag_changes(self) -> None:
        tracks = []
        for track in self._selected_table_tracks():
            if self.overlay.is_edited(track.path):
                tracks.append(track)
        if tracks:
            for track in tracks:
                self.overlay.clear(track)
            try:
                self.overlay.save()
            except OSError as exc:
                QMessageBox.warning(self, "Modifiche", f"Cartella dati non scrivibile: {exc}")
            self.statusBar().showMessage(f"Tornati ai tag del file: {len(tracks)} brani", 5000)
            self.refresh_after_tag_change()
            self.iphone_panel.offer_phone_update(tracks, False)

    def prepare_copy_for(self, track, copy: Path) -> None:
        """Applica a una copia le modifiche in sospeso del brano (esportazione, importazione)."""
        if self.overlay.is_edited(track.path):
            prepare_copy(copy, track.tags, self.overlay.cover_for(track.path))

    def _cover_of(self, track):
        """La copertina da mostrare: quella nuova in sospeso, altrimenti quella del file."""
        result = self.overlay.cover_for(track.path)
        if result is None:
            result = read_cover(track.path)
        return result

    def _apply_tag_changes(self, changes: dict, cover) -> None:
        pairs = []
        for track in self._selected_table_tracks():
            new_tags = None
            if changes:
                new_tags = track.tags.copy()
                for name, value in changes.items():
                    setattr(new_tags, name, value)
            pairs.append((track, new_tags))
        if pairs:
            self.apply_tag_changes(pairs, cover)

    def _renumber_selection(self) -> None:
        tracks = self._selected_table_tracks()
        pairs = []
        for position, track in enumerate(tracks, start=1):
            new_tags = track.tags.copy()
            new_tags.track_number = position
            new_tags.track_total = len(tracks)
            pairs.append((track, new_tags))
        answer = QMessageBox.question(
            self, "Numera in ordine",
            f"Assegnare i numeri da 1 a {len(tracks)} ai brani selezionati, nell'ordine della tabella?")
        if answer == QMessageBox.Yes:
            self.apply_tag_changes(pairs, None)

    def store_check_result(self, result) -> None:
        self.check_results[(result.artist, result.album)] = result

    def refresh_after_tag_change(self) -> None:
        """Aggiorna viste e risultati di verifica dopo una modifica dei tag."""
        rekeyed = {}
        for result in self.check_results.values():
            key = result.local_tracks[0].album_key
            result.artist, result.album = key
            rekeyed[key] = result
        self.check_results = rekeyed
        keep = set()
        for track in self._selected_table_tracks():
            keep.add(id(track))
        self._rebuild_views(keep)

    # ================================================================== importa / esporta

    def _import_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Cartella da importare nella Libreria",
                                                  self.app_settings.last_import)
        if folder:
            self.app_settings.last_import = folder
            self.save_settings()
            library = self.library_dir()
            source = Path(folder)
            if source.resolve() == library.resolve():
                QMessageBox.information(self, "Importa", "Questa cartella è già la Libreria.")
            else:
                def work(progress, cancel):
                    tracks = scan_folder(source, progress, cancel, self.tag_cache)
                    self.overlay.apply(tracks)
                    value = copy_organized(tracks, library, move=False, progress=progress, cancel=cancel,
                                           prepare=self.prepare_copy_for,
                                           forced=lambda track: self.overlay.is_edited(track.path))
                    return value

                def done(report):
                    self._show_copy_report("Importa cartella", report)
                    self.open_library()

                self.runner.run("Importazione", work, done)

    def _export_selection(self) -> None:
        tracks = self.selected_tracks()
        if not tracks:
            QMessageBox.information(self, "Esporta",
                                    "Seleziona i brani in tabella, oppure scegli un artista o un album negli elenchi in alto.")
        else:
            folder = QFileDialog.getExistingDirectory(self, f"Cartella in cui esportare {len(tracks)} brani",
                                                      self.app_settings.last_export)
            if folder:
                self.app_settings.last_export = folder
                self.save_settings()

                def work(progress, cancel):
                    value = copy_organized(tracks, Path(folder), move=False, progress=progress, cancel=cancel,
                                           prepare=self.prepare_copy_for,
                                           forced=lambda track: self.overlay.is_edited(track.path))
                    return value

                self.runner.run("Esportazione", work,
                                lambda report: self._show_copy_report("Esporta", report))

    def _show_copy_report(self, title: str, report, verb: str = "copiati") -> None:
        message = report.summary().replace("copiati", verb)
        if report.errors:
            details = []
            for path, error in report.errors[:10]:
                details.append(f"{Path(path).name}: {error}")
            message += "\n\n" + "\n".join(details)
            QMessageBox.warning(self, title, message)
        else:
            QMessageBox.information(self, title, message)

    # ================================================================== verifica album

    def _albums_to_check(self) -> list:
        groups = group_by_album(self.format_tracks())
        track_filter = self._track_filter()
        selected = []
        for key in sorted(groups, key=lambda k: (k[0].lower(), k[1].lower())):
            if self._passes(groups[key][0], track_filter):
                selected.append(groups[key])
        return selected

    def _check_albums(self) -> None:
        albums = self._albums_to_check()
        proceed = bool(albums)
        if not albums:
            QMessageBox.information(self, "Verifica album", "Non ci sono album da verificare.")
        elif len(albums) > 10:
            minutes = max(1, round(len(albums) * SECONDS_PER_ALBUM_CHECK / 60))
            answer = QMessageBox.question(
                self, "Verifica album",
                f"Verificare {len(albums)} album su MusicBrainz?\n"
                f"Servono circa {minutes} minuti (il servizio accetta una richiesta al secondo).\n\n"
                "Per verificarne solo alcuni, sceglili negli elenchi Artisti o Album.")
            proceed = answer == QMessageBox.Yes
        if proceed:
            client = self.mb_client

            def work(progress, cancel):
                results = []
                index = 0
                while index < len(albums) and not cancel.is_set():
                    artist, album = albums[index][0].album_key
                    progress(index, len(albums), f"{artist} — {album}")
                    results.append(check_album(client, albums[index]))
                    index += 1
                return results

            self.runner.run("Verifica album", work, self._show_check_results)

    def _show_check_results(self, results: list) -> None:
        for result in results:
            self.store_check_result(result)
        self._rebuild_views()
        if results:
            dialog = AlbumCheckDialog(results, self)
            dialog.exec()
            self.refresh_after_tag_change()

    # ================================================================== chiusura

    def closeEvent(self, event) -> None:
        self.app_settings.window_geometry = bytes(self.saveGeometry().toBase64()).decode("ascii")
        self.save_settings()
        if self.runner.is_busy:
            answer = QMessageBox.question(self, APP_NAME,
                                          "C'è un'operazione in corso. Interromperla e uscire?")
            if answer == QMessageBox.Yes:
                self.runner.cancel()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
