# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Finestra principale di myEasyMP3toIPhone. Le cartelle aperte sono in sola lettura: le modifiche dei tag restano in
sospeso (overlay) e vanno solo sulle copie inviate all'iPhone, esportate o importate."""

import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QByteArray, QItemSelection, QItemSelectionModel, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox, QPushButton, QScrollArea, QSplitter, QStyle, QTableView, QTabWidget,
    QToolBar, QVBoxLayout, QWidget,
)

from ..albumcheck import (
    SERVICE_DISCOGS, SERVICE_MUSICBRAINZ, STATUS_COMPLETE, STATUS_INCOMPLETE, ai_chooser, check_album_services,
    make_clients,
)
from ..config import PRODUCT, AppSettings, config_dir
from ..i18n import tr
from ..library import (
    assign_groups, copy_organized, group_by_album, load_track, scan_folder, set_various_artist_names, track_sort_key,
)
from .. import estimate, provenance
from ..phone_library import (
    DEVICE_ABSENT, DEVICE_SAME, DEVICE_STALE, PhoneIndex, comparison, device_status, load_listing,
    save_listing,
)
from ..overlay import TagOverlay
from ..pending import REMOVE, SEND, UPDATE, Pending, toggled, wanted
from ..tag_cache import TagCache, cached_track
from ..tags import prepare_copy, protect_folder, read_cover
from ..version import app_version
from .about import AboutDialog
from .album_check_dialog import AlbumCheckDialog, AlbumCheckOptionsDialog
from .browser import LibraryBrowser
from .compare_tip import comparison_html, show_on_tooltip
from .file_actions import add_file_entries
from .iphone_panel import IPhonePanel, show_entries_menu
from .scan_dialog import ScanLauncher
from .settings_dialog import SettingsDialog
from .tag_editor import TagEditor
from .theme import GEAR, gear_icon
from .track_model import COL_DEVICE, COL_TITLE, COLUMNS, TrackTableModel
from .worker import BackgroundJob, TaskRunner

APP_NAME = PRODUCT
# Il filtro per formato: (etichetta, estensioni); None = tutti
FORMATS = (("Tutti i formati", None), ("MP3", (".mp3",)), ("FLAC", (".flac",)), ("M4A / AAC", (".m4a",)),
           ("OGG / Opus", (".ogg", ".opus")), ("WMA / WAV / AIFF", (".wma", ".wav", ".aif", ".aiff")))

DEVICE_TIP = {DEVICE_SAME: "Nell'app Musica dell'iPhone c'è questo brano, con gli stessi tag",
              DEVICE_STALE: "Nell'app Musica dell'iPhone c'è questo brano, ma con tag diversi:",
              DEVICE_ABSENT: "Non è nell'app Musica dell'iPhone"}
# le modifiche in attesa (passo 5): segno, colore del segno, tinta della riga; diversi da quelli "fatti"
EXIT_NOW, EXIT_AFTER_APPLY, EXIT_CANCEL = "esci_ora", "esci_dopo_applica", "resta_aperto"   # all'uscita
PENDING_LOOK = {SEND: ("＋", QColor(40, 110, 230), QColor(40, 110, 230, 40)),
                REMOVE: ("－", QColor(210, 50, 50), QColor(230, 60, 90, 40)),
                UPDATE: ("⟳", QColor(40, 110, 230), QColor(40, 110, 230, 40))}
PENDING_TIP = {SEND: "In attesa: da inviare all'iPhone (Applica)",
               REMOVE: "In attesa: da togliere dall'iPhone (Applica)",
               UPDATE: "In attesa: da aggiornare sull'iPhone (Applica)"}



def _format_length(seconds: float) -> str:
    total = int(round(seconds))
    result = f"{total // 60}:{total % 60:02d}"
    return result




class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        # la versione intera, con la data: due build -dev dello stesso numero si distinguono (come myCalibreTools)
        self.setWindowTitle(f"{APP_NAME} {app_version()}")
        self.resize(1400, 820)
        self.app_settings = AppSettings.load()
        set_various_artist_names(self.app_settings.various_artists)
        self._phone_index: Optional[PhoneIndex] = None   # la musica dell'app Musica, per la colonna "iPhone"
        self.phone_tracks = []     # la musica dell'app Musica (phone_library.PhoneTrack), letta o ricordata
        self.phone_label = ""      # di quale iPhone e quando
        self.registry = provenance.Registry.load(config_dir())   # da dove viene ogni brano dell'iPhone
        self.overlay = TagOverlay(config_dir())
        self.tag_cache = TagCache(config_dir())
        self.pending = Pending(config_dir())   # le spunte della colonna iPhone non ancora applicate
        self._states = {}                      # id(brano) -> (stato, PhoneTrack, collegato): rifatto quando serve
        self.open_on_start: Optional[Path] = None   # --open CARTELLA: aperta all'avvio al posto della Libreria
        if self.app_settings.window_geometry:
            self.restoreGeometry(QByteArray.fromBase64(self.app_settings.window_geometry.encode("ascii")))
        self.album_clients = make_clients()      # i cataloghi di Verifica album online
        self.mb_client = self.album_clients[SERVICE_MUSICBRAINZ]   # anche per i nomi d'artista della scansione
        self._album_job = None                    # Verifica album online in background
        self._album_results = []
        self._album_total = 0
        self._album_dialog = None
        self.tracks = []           # i brani della cartella aperta, senza quelli delle cartelle nascoste
        self._all_tracks = []      # tutti i brani letti, anche quelli nascosti
        self._visible = []
        self.root_folder: Optional[Path] = None
        self.check_results = {}
        self._exit_checked = False     # le modifiche in attesa sono già state applicate (o lasciate) per uscire

        self._album_label = QLabel()
        self._album_stop = QPushButton("Ferma")
        self._album_stop.setToolTip("Interrompe Verifica album online: i risultati già trovati restano")
        self._album_stop.clicked.connect(self._stop_album_check)
        self._album_results_button = QPushButton("Risultati della verifica…")
        self._album_results_button.clicked.connect(self._open_album_results)
        for widget in (self._album_label, self._album_stop, self._album_results_button):
            self.statusBar().addPermanentWidget(widget)
            widget.setVisible(False)
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
            ("Verifica album online", QStyle.SP_DialogApplyButton, self._check_albums,
             "Confronta gli album scelti (o tutti) con i cataloghi online (Deezer, Apple Music, Discogs, "
             "MusicBrainz): brani mancanti, tag giusti, copertina. In background", "F5"),
            ("Controlla la musica", QStyle.SP_FileDialogContentsView, self._scan,
             "Cerca i problemi confrontando i tuoi brani tra loro (cartella aperta o iPhone), senza cataloghi "
             "online: file non aggiornati, album con pochi brani, collezioni divise, artisti scritti in modi "
             "diversi, brani duplicati (con l'AI, se configurata)", "F6"),
            ("Impostazioni", GEAR, self._open_settings,
             "Cartella della Libreria, profili AI e chiavi", "Ctrl+,"),
            ("Informazioni", QStyle.SP_MessageBoxInformation, self._open_about,
             "Versione, cartella dati, variabili d'ambiente e dove sono salvate le chiavi", None),
        ]
        self._task_actions = []
        for text, icon, slot, tip, shortcut in definitions:
            action = QAction(gear_icon() if icon == GEAR else style.standardIcon(icon), text, self)
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
                                "Verifica album online, la scansione e l'invio all'iPhone")
        for label, _extensions in FORMATS:
            self._format.addItem(tr(label))
        self._format.currentIndexChanged.connect(lambda _index: self._rebuild_views())
        self._reload_button = QPushButton("Aggiorna")
        self._reload_button.setToolTip("Rilegge la cartella aperta: i file nuovi, tolti o cambiati (gli altri dalla "
                                       "cache dei tag). Con Maiusc premuto rilegge tutti i file da zero.")
        self._reload_button.clicked.connect(self.reload_folder)
        top = QHBoxLayout()
        top.addWidget(self._search, 1)
        top.addWidget(QLabel("Formato:"))
        top.addWidget(self._format)
        top.addWidget(self._folder_label, 1)
        top.addWidget(self._reload_button)
        self._hidden_button = QPushButton()
        self._hidden_button.setToolTip("Le cartelle nascoste con il tasto destro: qui le mostri di nuovo")
        self._hidden_button.clicked.connect(self._show_hidden_folders)
        top.addWidget(self._hidden_button)
        self._update_hidden_button()

        self.browser = LibraryBrowser()
        self.browser.filter_changed.connect(self._fill_table)
        self.browser.phone_state = self._browser_phone_state
        self.browser.phone_toggled.connect(self.set_wanted)
        self.browser.menu_requested.connect(self._browser_menu)

        self._table = QTableView()
        self._model = TrackTableModel(self, PENDING_LOOK, PENDING_TIP)
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(self._table.fontMetrics().height() + 6)
        self._table.setAlternatingRowColors(False)    # le righe hanno la tinta del loro album (theme.album_bands)
        self._table.setWordWrap(False)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        header.setMinimumSectionSize(30)
        # nessun ordinamento iniziale: si mantiene l'ordine Artista/Album/Disco/Traccia finché l'utente non clicca
        # un'intestazione di colonna (Artista, Album, Titolo…), che poi mostra la freccia dell'ordinamento
        header.setSortIndicator(-1, Qt.AscendingOrder)
        header.setSortIndicatorShown(True)
        widths = [40, 50, 230, 160, 140, 180, 50, 90, 55, 220]
        for column, width in enumerate(widths):
            self._table.setColumnWidth(column, width)
        self._table.selectionModel().selectionChanged.connect(lambda _new, _old: self._selection_changed())
        self._table.setSortingEnabled(True)
        header.setSortIndicator(-1, Qt.AscendingOrder)
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
        layout.addWidget(self._build_pending_bar())
        return tab

    def _build_pending_bar(self) -> QFrame:
        """La barra delle modifiche all'iPhone in attesa: si vede solo quando ce ne sono."""
        self._pending_bar = QFrame()
        self._pending_bar.setStyleSheet("QFrame { background: rgba(40, 110, 230, 30); border-radius: 4px; }")
        self._pending_label = QLabel()
        undo = QPushButton("Annulla le modifiche")
        undo.clicked.connect(self._undo_pending)
        self._apply_button = QPushButton("Applica (PC → iPhone)…")
        self._apply_button.setProperty("role", "go")
        self._apply_button.clicked.connect(self._apply_pending)
        row = QHBoxLayout(self._pending_bar)
        row.setContentsMargins(8, 4, 8, 4)
        row.addWidget(self._pending_label, 1)
        row.addWidget(undo)
        row.addWidget(self._apply_button)
        self._pending_bar.setVisible(False)
        return self._pending_bar

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
            QTimer.singleShot(0, self._update_pending_bar)   # Applica si può premere solo a iPhone connesso

    def set_registry(self, registry) -> None:
        """Il registro della provenienza è cambiato (collegamenti nuovi o tolti): confronti e viste da rifare."""
        self.registry = registry
        self._phone_index = PhoneIndex(self.phone_tracks, registry.links_here())
        self._states = {}
        self._fill_table()
        self.browser.refresh_phone_states()
        self._update_pending_bar()
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
        self._states = {}
        if self.pending.reconcile(self.tracks, lambda track: self._device_state(track)[0]):
            self._save_pending()
        self._model.device_header_tip = (f"Nell'app Musica dell'iPhone ({label}): ✔ stesso brano, ⟳ stesso brano "
                                         "con tag diversi, ≈ forse lo stesso (abbinato solo per i tag: da rivedere), "
                                         "vuoto = non c'è; la spunta: voglio il brano sull'iPhone")
        self.iphone_panel.set_phone_tracks(tracks, label)
        self._fill_table()
        self.browser.refresh_phone_states()
        self._update_pending_bar()

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

    def source_track(self, path: Path):
        """Il brano di un file del PC fuori dalla cartella aperta (la sorgente di un brano dell'iPhone), con le
        modifiche in sospeso: dalla cache dei tag o letto dal file (solo lettura). None se non si legge."""
        track = cached_track(path, self.tag_cache)
        if track is None:
            track = load_track(path)
            if not track.error:
                self.tag_cache.store(track)
        if track.error:
            result = None
        else:
            self.overlay.apply([track])
            result = track
        return result

    def save_settings(self) -> None:
        self.app_settings.save()

    def _open_settings(self) -> None:
        before = self.library_dir()
        various = list(self.app_settings.various_artists)
        dialog = SettingsDialog(self.app_settings, self)
        if dialog.exec():
            self._model.refresh()                  # il percorso completo delle cartelle, se è cambiato
            self.iphone_panel.pc_changed()
            if self.app_settings.various_artists != various:     # gli elenchi Artisti si rifanno
                set_various_artist_names(self.app_settings.various_artists)
                self._rebuild_views()
                self.iphone_panel.regroup()
            if self.library_dir() != before:
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

    # ------------------------------------------------------------------ cartelle nascoste

    @staticmethod
    def _folder_key(folder) -> str:
        result = os.path.normcase(os.path.abspath(str(folder)))
        return result

    def _is_hidden(self, path: Path, hidden: list) -> bool:
        """Il file è in una cartella nascosta o in una sua sottocartella."""
        key = self._folder_key(path.parent)
        result = False
        for folder in hidden:
            if key == folder or key.startswith(folder.rstrip("\\/") + os.sep):
                result = True
        return result

    def _without_hidden(self, tracks: list) -> list:
        hidden = []
        for folder in self.app_settings.hidden_folders:
            hidden.append(self._folder_key(folder))
        result = []
        for track in tracks:
            if not hidden or not self._is_hidden(track.path, hidden):
                result.append(track)
        return result

    def _update_hidden_button(self) -> None:
        count = len(self.app_settings.hidden_folders)
        self._hidden_button.setText(f"Cartelle nascoste ({count})…")
        self._hidden_button.setVisible(count > 0)

    def hide_folders(self, folders: list) -> None:
        """Nasconde le cartelle (con le sottocartelle) nella scheda PC: i file non cambiano, si ricorda in
        settings.json."""
        known = set()
        for folder in self.app_settings.hidden_folders:
            known.add(self._folder_key(folder))
        added = 0
        for folder in folders:
            if self._folder_key(folder) not in known:
                self.app_settings.hidden_folders.append(str(folder))
                known.add(self._folder_key(folder))
                added += 1
        self.save_settings()
        self._apply_hidden()
        self.statusBar().showMessage(f"Nascoste {added} cartelle: le mostri di nuovo con Cartelle nascoste… in alto",
                                     10000)

    def _apply_hidden(self) -> None:
        before = len(self.tracks)
        self.tracks = self._without_hidden(self._all_tracks)
        self._update_hidden_button()
        if len(self.tracks) != before:
            self._rebuild_views()

    def _show_hidden_folders(self) -> None:
        """La finestra delle cartelle nascoste: quelle spuntate si mostrano di nuovo."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Cartelle nascoste")
        dialog.resize(700, 360)
        label = QLabel("Spunta le cartelle da mostrare di nuovo nella scheda PC (i file non sono mai cambiati).")
        label.setWordWrap(True)
        folders = QListWidget()
        for folder in self.app_settings.hidden_folders:
            item = QListWidgetItem(folder)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            folders.addItem(item)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Mostra le spuntate")
        buttons.button(QDialogButtonBox.Cancel).setText("Chiudi")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout = QVBoxLayout(dialog)
        layout.addWidget(label)
        layout.addWidget(folders, 1)
        layout.addWidget(buttons)
        if dialog.exec():
            kept = []
            for index in range(folders.count()):
                item = folders.item(index)
                if item.checkState() != Qt.Checked:
                    kept.append(item.text())
            self.app_settings.hidden_folders = kept
            self.save_settings()
            self._apply_hidden()

    def reload_folder(self) -> None:
        """Aggiorna: rilegge la cartella aperta; con Maiusc premuto tutti i file, senza la cache dei tag."""
        if self.root_folder is None:
            QMessageBox.information(self, "Aggiorna", "Nessuna cartella aperta")
        else:
            force = bool(QApplication.keyboardModifiers() & Qt.ShiftModifier)
            self.load_folder(self.root_folder, force)

    def load_folder(self, folder: Path, force: bool = False) -> None:
        if self._album_job is not None and self._album_job.running:
            self._stop_album_check()           # i risultati varrebbero per i brani della cartella di prima

        def work(progress, cancel):
            value = scan_folder(folder, progress, cancel, self.tag_cache, force)
            return value

        def done(tracks):
            protect_folder(folder)
            self.overlay.apply(tracks)
            self._all_tracks = tracks
            self.tracks = self._without_hidden(tracks)
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
            hidden = len(tracks) - len(self.tracks)
            text = f"{len(self.tracks)} brani caricati"
            if hidden:
                text += f" ({hidden} nelle cartelle nascoste)"
            self.statusBar().showMessage(text, 8000)
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
            self._format.setItemText(index, f"{tr(label)} ({total})")

    def _rebuild_views(self, keep_tracks: Optional[set] = None) -> None:
        self._states = {}
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
        self._model.set_tracks(self._visible)
        header = self._table.horizontalHeader()
        if header.sortIndicatorSection() >= 0:
            self._model.sort(header.sortIndicatorSection(), header.sortIndicatorOrder())
        selection = QItemSelection()
        last = len(COLUMNS) - 1
        for row in range(self._model.rowCount()):
            if id(self._model.track(row)) in keep_tracks:
                selection.select(self._model.index(row, 0), self._model.index(row, last))
        model = self._table.selectionModel()
        model.blockSignals(True)
        model.select(selection, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        model.blockSignals(False)
        self._table.viewport().update()
        self._selection_changed()

    # ================================================================== passo 5: spunte e modifiche in attesa

    def _device_state(self, track) -> tuple:
        """(stato, PhoneTrack o None, collegato dal registro) del brano rispetto all'iPhone, ricordato fino al prossimo
        cambio di brani, tag, registro o musica dell'iPhone."""
        key = id(track)
        result = self._states.get(key)
        if result is None:
            status = DEVICE_ABSENT
            phone_track = None
            linked = False
            if self._phone_index is not None and not track.error:
                status, phone_track, _found = device_status(track, self._phone_index)
                linked = phone_track is not None and self._phone_index.via_registry(track)
            result = (status, phone_track, linked)
            self._states[key] = result
        return result

    def phone_known(self) -> bool:
        """C'è un elenco della musica dell'iPhone (letto ora o ricordato): la colonna iPhone ha le spunte."""
        result = self._phone_index is not None
        return result

    def device_state(self, track) -> tuple:
        result = self._device_state(track)
        return result

    def device_checked(self, row: int, checked: bool) -> None:
        """Una spunta della colonna iPhone cambiata a mano: vale per tutte le righe selezionate, se la riga lo è."""
        if self._phone_index is not None:
            rows = self._selected_rows()
            if row not in rows:
                rows = [row]
            tracks = []
            for selected in rows:
                tracks.append(self._track_at_row(selected))
            self.set_wanted(tracks, checked)

    def set_wanted(self, tracks: list, checked: bool) -> None:
        """Mette o toglie la spunta "voglio questi brani sull'iPhone": le modifiche restano in attesa fino ad Applica."""
        if self._phone_index is not None:
            kept = 0
            for track in tracks:
                if not track.error:
                    status, _phone_track, linked = self._device_state(track)
                    action = self.pending.get(track.path)
                    new_action = toggled(status, linked, action, checked)
                    if not checked and status != DEVICE_ABSENT and not linked:
                        kept += 1
                    self.pending.set(track.path, new_action)
            self._save_pending()
            self._restyle_rows(tracks)
            self.browser.refresh_phone_states()
            self._update_pending_bar()
            if kept:
                self.statusBar().showMessage(
                    f"{kept} brani restano sull'iPhone: sono abbinati solo per i tag. Per toglierli da qui associa "
                    "prima la sorgente (scheda iPhone, tasto destro), oppure eliminali dalla scheda iPhone.", 15000)

    def mark_for_update(self, tracks: list) -> None:
        """I brani ⟳ associati (registro: sull'iPhone con tag diversi) in attesa di aggiornamento PC → iPhone. Un
        brano abbinato solo per i tag non si aggiorna: prima si associa la sorgente."""
        for track in tracks:
            status, _phone_track, linked = self._device_state(track)
            if status == DEVICE_STALE and linked:
                self.pending.set(track.path, UPDATE)
        self._save_pending()
        self._restyle_rows(tracks)
        self.browser.refresh_phone_states()
        self._update_pending_bar()

    def _restyle_rows(self, _tracks: list) -> None:
        """Le spunte e i segni della colonna iPhone da ridisegnare (il modello ricalcola solo le righe visibili)."""
        self._model.refresh()

    def _save_pending(self) -> None:
        try:
            self.pending.save()
        except OSError as exc:
            self.statusBar().showMessage(f"Modifiche in attesa non salvate nella cartella dati: {exc}", 10000)

    def _browser_phone_state(self, tracks: list):
        """(spunta di un artista o album negli elenchi, c'è qualcosa in attesa) o None senza la musica dell'iPhone."""
        result = None
        if self._phone_index is not None:
            on = 0
            usable = 0
            waiting = False
            for track in tracks:
                if not track.error:
                    usable += 1
                    action = self.pending.get(track.path)
                    waiting = waiting or bool(action)
                    if wanted(self._device_state(track)[0], action):
                        on += 1
            if usable and on == usable:
                state = Qt.Checked
            elif on:
                state = Qt.PartiallyChecked
            else:
                state = Qt.Unchecked
            result = (state, waiting)
        return result

    def pending_work(self) -> tuple:
        """(da inviare [Track], da togliere [PhoneTrack], da aggiornare [(PhoneTrack, Track)]) tra i brani aperti."""
        sends = []
        removes = []
        updates = []
        for track in self.tracks:
            action = self.pending.get(track.path)
            if action and not track.error:
                status, phone_track, linked = self._device_state(track)
                if action == SEND and status == DEVICE_ABSENT:
                    sends.append(track)
                elif action == REMOVE and phone_track is not None and linked and phone_track.from_computer:
                    removes.append(phone_track)
                elif action == UPDATE and status == DEVICE_STALE and linked and phone_track.from_computer:
                    updates.append((phone_track, track))       # solo i brani associati (registro)
        result = (sends, removes, updates)
        return result

    def _update_pending_bar(self) -> None:
        counts = self.pending.counts()
        total = counts[SEND] + counts[REMOVE] + counts[UPDATE]
        self._pending_bar.setVisible(total > 0)
        if total:
            self._pending_label.setText(
                f"<b>In attesa per l'iPhone (PC → iPhone):</b> {counts[SEND]} da inviare, {counts[REMOVE]} da "
                f"togliere, {counts[UPDATE]} da aggiornare")
            ready = self.iphone_panel.connected and not self.runner.is_busy
            self._apply_button.setEnabled(ready)
            self._apply_button.setToolTip("" if ready else "Connetti l'iPhone")

    def _undo_pending(self) -> None:
        counts = self.pending.counts()
        total = counts[SEND] + counts[REMOVE] + counts[UPDATE]
        answer = QMessageBox.question(self, "Annulla le modifiche",
                                      f"Annullare le {total} modifiche all'iPhone in attesa? Le spunte tornano come "
                                      "sono sull'iPhone.")
        if answer == QMessageBox.Yes:
            self.pending.clear()
            self._save_pending()
            self._fill_table()
            self.browser.refresh_phone_states()
            self._update_pending_bar()

    def _apply_pending(self) -> None:
        sends, removes, updates = self.pending_work()
        if sends or removes or updates:
            self.iphone_panel.apply_pending(sends, removes, updates)
        else:
            QMessageBox.information(self, "Applica", "Nessuna modifica da fare tra i brani della cartella aperta: le "
                                    "altre restano in attesa finché apri la cartella dei loro file.")

    def _track_at_row(self, row: int):
        result = self._model.track(row)
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
            result = self._model.data(self._model.index(row, column), Qt.ToolTipRole) or ""
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
        self._tracks_menu(self._table.viewport().mapToGlobal(position))

    def browser_menu_entries(self, tracks: list) -> list:
        """Le voci del tasto destro su un artista o un album (tutti i suoi brani): [(testo, attiva, funzione)].
        Invia quelli che non sono sull'iPhone; Rimuovi, Aggiorna (rimpiazza il file con quello del PC) e Aggiorna TAG
        (solo i tag, dove sono diversi: ⟳) quelli che ci sono con la sorgente certa (registro). Ognuna chiede
        conferma con il tempo stimato."""
        absent = []
        removable = []
        linked_pairs = []
        stale = []
        seen = set()
        unlinked = 0
        for track in tracks:
            if not track.error and self._phone_index is not None:
                status, phone_track, linked = self._device_state(track)
                if status == DEVICE_ABSENT:
                    absent.append(track)
                elif linked and phone_track.from_computer and phone_track.pid not in seen:
                    seen.add(phone_track.pid)
                    removable.append(phone_track)
                    linked_pairs.append((phone_track, track))
                    if status == DEVICE_STALE:
                        stale.append((phone_track, track))
                elif not linked:
                    unlinked += 1
        ready = self.iphone_panel.connected and not self.runner.is_busy
        result = [
            (f"Invia all'iPhone (PC → iPhone): {len(absent)} brani che non ci sono", ready and bool(absent),
             lambda: self.iphone_panel.send_tracks(absent)),
            (f"Rimuovi dall'iPhone: {len(removable)} brani", ready and bool(removable),
             lambda: self.iphone_panel.delete_items(removable)),
            (f"Aggiorna sull'iPhone (PC → iPhone): rimpiazza {len(linked_pairs)} brani con i file del PC",
             ready and bool(linked_pairs), lambda: self.iphone_panel.replace_pairs(linked_pairs)),
            (f"Aggiorna TAG sull'iPhone (PC → iPhone): {len(stale)} brani con tag diversi ⟳", ready and bool(stale),
             lambda: self.iphone_panel.update_pairs(stale, "Aggiorna TAG dal PC")),
        ]
        if unlinked:
            result.append((f"{unlinked} brani sull'iPhone abbinati solo per i tag: per toglierli o aggiornarli "
                           "prima associa la sorgente (scheda iPhone)", False, None))
        if self._phone_index is None:
            result.append(("Collega l'iPhone: la sua musica non è ancora stata letta", False, None))
        return result

    def _browser_menu(self, where) -> None:
        """Tasto destro su un artista o un album: invia, rimuovi, aggiorna per tutti i suoi brani."""
        show_entries_menu(self, self.browser_menu_entries(self.browser.menu_tracks), where,
                          self.iphone_panel.connected)

    def _tracks_menu(self, where) -> None:
        """Tasto destro sui brani: invia all'iPhone quelli che non ci sono, rimpiazza o aggiorna quelli associati con
        tag diversi (PC → iPhone). Quelli abbinati solo per i tag si contano a parte: prima si associano."""
        tracks = self._selected_table_tracks()
        if tracks:
            absent = []
            stale = []
            unlinked = 0
            present = 0
            for track in tracks:
                status, phone_track, linked = self._device_state(track)
                if status == DEVICE_ABSENT:
                    absent.append(track)
                elif status == DEVICE_STALE and phone_track.from_computer and linked:
                    stale.append((phone_track, track))
                elif status == DEVICE_STALE and phone_track.from_computer:
                    unlinked += 1
                else:
                    present += 1
            ready = self.iphone_panel.connected and not self.runner.is_busy
            menu = QMenu(self)
            send = menu.addAction(f"Invia all'iPhone (PC → iPhone): {len(absent)} brani che non ci sono")
            send.setEnabled(ready and bool(absent))
            send.triggered.connect(lambda: self.iphone_panel.send_tracks(absent))
            replace = menu.addAction(f"Rimpiazza sull'iPhone (PC → iPhone): {len(stale)} brani associati ⟳")
            replace.setEnabled(ready and bool(stale))
            replace.triggered.connect(lambda: self.iphone_panel.replace_pairs(stale))
            later_tracks = []
            for _phone_track, track in stale:
                later_tracks.append(track)
            later = menu.addAction(f"Aggiorna l'iPhone più tardi (PC → iPhone): {len(stale)} brani associati ⟳ "
                                   "in attesa")
            later.setEnabled(bool(stale) and not self.runner.is_busy)
            later.triggered.connect(lambda: self.mark_for_update(later_tracks))
            if unlinked:
                note = menu.addAction(f"{unlinked} brani con tag diversi abbinati solo per i tag: non si aggiornano, "
                                      "prima associa la sorgente (scheda iPhone)")
                note.setEnabled(False)
            if present:
                note = menu.addAction(f"{present} brani già sull'iPhone uguali ✔")
                note.setEnabled(False)
            if not self.iphone_panel.connected:
                for action in (send, replace):
                    action.setToolTip("Connetti l'iPhone")
            menu.addSeparator()
            paths = []
            for track in tracks:
                paths.append(track.path)
            add_file_entries(menu, paths, lambda text: self.statusBar().showMessage(text, 8000))
            menu.addSeparator()
            distinct = []
            for path in paths:
                if path.parent not in distinct:
                    distinct.append(path.parent)
            hide = menu.addAction(f"Nascondi la cartella ({len(distinct)})")
            hide.setToolTip("Non mostrare più i brani di questa cartella (e delle sue sottocartelle) nella scheda PC: "
                            "i file non cambiano; Cartelle nascoste… in alto le mostra di nuovo")
            hide.triggered.connect(lambda: self.hide_folders(distinct))
            menu.setToolTipsVisible(True)
            menu.exec(where)

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
            self._table.scrollTo(self._model.index(rows[0], COL_TITLE))
        self.activateWindow()

    def _selection_changed(self) -> None:
        self.editor.set_tracks(self._selected_table_tracks())

    def _busy_changed(self, busy: bool) -> None:
        for action in self._task_actions:
            action.setEnabled(not busy)
        self._reload_button.setEnabled(not busy)
        self.editor.setEnabled(not busy)
        QTimer.singleShot(0, self._update_pending_bar)

    # ================================================================== modifica tag

    def apply_tag_changes(self, pairs: list, cover: Optional[bytes] = None) -> None:
        """pairs: (Track, nuovi TrackTags o None se invariati). Le modifiche restano in sospeso nella cartella dati: i
        file sul PC non cambiano; valgono per le copie inviate all'iPhone, esportate o importate. L'iPhone non cambia:
        la differenza si vede (⟳) e si allinea a mano (scheda iPhone, Allinea i tag)."""
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
        if self._album_job is not None and self._album_job.running:
            QMessageBox.information(self, "Verifica album online", "La verifica è già in corso (barra di stato): "
                                    "aspetta la fine o premi Ferma.")
        elif not albums:
            QMessageBox.information(self, "Verifica album online", "Non ci sono album da verificare.")
        else:
            provider = self.iphone_panel._ai_provider()
            settings = self.app_settings
            dialog = AlbumCheckOptionsDialog(self, len(albums), list(settings.album_services), settings.album_ai,
                                             provider.profile.name if provider is not None else "",
                                             self.album_clients[SERVICE_DISCOGS].available())
            if dialog.exec():
                settings.album_services = dialog.services()
                settings.album_ai = dialog.use_ai
                self.save_settings()
                clients = []
                for service in dialog.services():
                    clients.append(self.album_clients[service])
                chooser = ai_chooser(provider) if dialog.use_ai and provider is not None else None
                self._start_album_check(albums, clients, chooser)

    def _start_album_check(self, albums: list, clients: list, chooser) -> None:
        """Verifica album online in background: il programma resta usabile, gli esiti arrivano album per album."""
        def work(progress, cancel, emit):
            index = 0
            while index < len(albums) and not cancel.is_set():
                artist, album = albums[index][0].album_key
                progress(index, len(albums), f"{artist} — {album}")
                emit(check_album_services(clients, albums[index], chooser))
                index += 1

        self._album_results = []
        self._album_total = len(albums)
        job = BackgroundJob(work)
        job.item.connect(self._album_checked)
        job.finished.connect(self._album_check_done)
        job.failed.connect(lambda message: self._album_check_done(message))
        self._album_job = job
        self._album_label.setText(f"Verifica album online: 0 di {len(albums)}")
        for widget in (self._album_label, self._album_stop):
            widget.setVisible(True)
        self._album_stop.setEnabled(True)
        self._album_results_button.setVisible(False)
        job.start()

    def _album_checked(self, result) -> None:
        self._album_results.append(result)
        self.store_check_result(result)
        self.browser.refresh_check_icons(self.check_results)
        self._album_label.setText(f"Verifica album online: {len(self._album_results)} di {self._album_total}")
        self._album_results_button.setVisible(True)

    def _stop_album_check(self) -> None:
        if self._album_job is not None:
            self._album_job.cancel()
            self._album_stop.setEnabled(False)
            self._album_label.setText("Verifica album online: interruzione…")

    def _album_summary(self) -> str:
        complete = 0
        incomplete = 0
        for result in self._album_results:
            if result.status == STATUS_COMPLETE:
                complete += 1
            elif result.status == STATUS_INCOMPLETE:
                incomplete += 1
        other = len(self._album_results) - complete - incomplete
        text = f"{len(self._album_results)} album: {complete} completi, {incomplete} incompleti, {other} non trovati"
        return text

    def _album_check_done(self, error: str = "") -> None:
        cancelled = self._album_job is not None and self._album_job.cancelled
        self._album_stop.setVisible(False)
        if error:
            self._album_label.setText(f"Verifica album online non riuscita: {error}")
        elif cancelled:
            self._album_label.setText(f"Verifica album online interrotta: {self._album_summary()}")
        else:
            self._album_label.setText(f"Verifica album online finita: {self._album_summary()}")
        self._album_results_button.setVisible(bool(self._album_results))
        if self._album_results and not cancelled:
            self._open_album_results()

    def _open_album_results(self) -> None:
        """La finestra dei risultati, non modale: si può continuare a usare il programma."""
        if self._album_dialog is not None:
            self._album_dialog.close()
        if self._album_results:
            dialog = AlbumCheckDialog(self._album_results, self)
            dialog.finished.connect(lambda _code: self.refresh_after_tag_change())
            self._album_dialog = dialog
            dialog.show()

    # ================================================================== chiusura

    def closeEvent(self, event) -> None:
        if self._album_job is not None and self._album_job.running:
            self._album_job.cancel()
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
        elif self._exit_checked:
            event.accept()
        else:
            choice = self._ask_pending_on_exit()
            if choice == EXIT_NOW:
                event.accept()
            elif choice == EXIT_AFTER_APPLY:
                event.ignore()
                self._exit_checked = True        # alla fine di Applica si esce, senza chiedere di nuovo
                sends, removes, updates = self.pending_work()
                self.iphone_panel.apply_pending(sends, removes, updates, closing=True, then=self.close)
            else:
                event.ignore()

    def _ask_pending_on_exit(self) -> str:
        """Con modifiche in attesa per l'iPhone (tra i brani aperti) chiede se applicarle prima di uscire, con il
        tempo stimato. EXIT_NOW, EXIT_AFTER_APPLY o EXIT_CANCEL."""
        sends, removes, updates = self.pending_work()
        count = len(sends) + len(removes) + len(updates)
        if not count:
            result = EXIT_NOW
        else:
            seconds = self.iphone_panel.pending_seconds(sends, removes, updates)
            text = (f"Ci sono modifiche in attesa per l'iPhone (PC → iPhone) non ancora applicate: {len(sends)} da "
                    f"inviare, {len(removes)} da togliere, {len(updates)} da aggiornare.\n\n"
                    + estimate.summary(count, seconds))
            box = QMessageBox(QMessageBox.Warning, APP_NAME, "", QMessageBox.NoButton, self)
            apply_button = None
            if self.iphone_panel.connected:
                text += "\n\nApplicarle prima di uscire? Il programma si chiude alla fine."
                apply_button = box.addButton("Applica ed esci", QMessageBox.AcceptRole)
            else:
                text += ("\n\nL'iPhone non è collegato, quindi ora non si possono applicare. Se esci restano in attesa "
                         "per la prossima volta; per applicarle ora collega l'iPhone e premi Applica.")
            exit_button = box.addButton("Esci senza applicare", QMessageBox.DestructiveRole)
            cancel_button = box.addButton("Annulla", QMessageBox.RejectRole)
            box.setText(text)
            box.setDefaultButton(apply_button if apply_button is not None else cancel_button)
            box.exec()
            clicked = box.clickedButton()
            if apply_button is not None and clicked is apply_button:
                result = EXIT_AFTER_APPLY
            elif clicked is exit_button:
                result = EXIT_NOW
            else:
                result = EXIT_CANCEL
        return result
