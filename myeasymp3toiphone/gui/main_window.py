# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Finestra principale di myEasyMP3toIPhone. Le cartelle aperte sono in sola lettura: le modifiche dei tag restano in
sospeso (overlay) e vanno solo sulle copie inviate all'iPhone, esportate o importate."""

import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QByteArray, QItemSelection, QItemSelectionModel, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox, QPushButton,
    QScrollArea, QSplitter, QStyle, QTableView, QTabWidget, QToolBar, QToolButton, QVBoxLayout, QWidget,
)

from ..albumcheck import (
    SERVICE_DISCOGS, SERVICE_MUSICBRAINZ, STATUS_COMPLETE, STATUS_INCOMPLETE, ai_chooser, check_album_services,
    make_clients,
)
from ..config import PRODUCT, AppSettings, config_dir
from ..i18n import tr
from ..library import (
    album_folder, assign_groups, copy_organized, group_by_album, load_track, scan_folder, set_various_artist_names,
    track_sort_key,
)
from .. import estimate, provenance
from ..phone_library import (
    DEVICE_ABSENT, DEVICE_SAME, DEVICE_STALE, PhoneIndex, comparison, device_status, differences, load_listing,
    save_listing,
)
from ..overlay import TagOverlay, path_key
from ..pending import (
    DELETE, EDIT, FILE_PREFIX, REMOVE, REPLACE, SEND, UPDATE, Job, Pending, key_pid, toggled, wanted,
)
from ..tag_cache import TagCache, cached_track
from ..tags import prepare_copy, protect_folder, read_cover
from ..version import app_version
from .about import AboutDialog
from .album_check_dialog import AlbumCheckDialog
from .checks_panel import ChecksPanel
from .apply_dialog import ApplyDialog, songs, summary
from .widgets import ActionBar, ChipBar
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
FINGERPRINT_SUFFIXES = {".mp3", ".flac", ".m4a", ".m4b", ".mp4"}   # provenance.fingerprint li sa leggere
FINGERPRINT_BATCH = 200       # impronte per giro: annullare (nuova cartella, uscita) aspetta al massimo un giro
FINGERPRINT_NOTICE = 100      # da quanti file in su lo si dice nella barra di stato
FINGERPRINTS_TO_DO, FINGERPRINTS_DONE = "impronte_da_fare", "impronte_fatte"   # i messaggi del lavoro in sottofondo
MUSIC_MARK = "*"              # last_opened: erano aperte le cartelle della musica
EXIT_NOW, EXIT_AFTER_APPLY, EXIT_CANCEL ="esci_ora", "esci_dopo_applica", "resta_aperto"   # all'uscita
PENDING_LOOK = {SEND: ("＋", QColor(40, 110, 230), QColor(40, 110, 230, 40)),
                REMOVE: ("－", QColor(210, 50, 50), QColor(230, 60, 90, 40)),
                DELETE: ("－", QColor(210, 50, 50), QColor(230, 60, 90, 40)),
                UPDATE: ("⟳", QColor(40, 110, 230), QColor(40, 110, 230, 40)),
                REPLACE: ("⟳", QColor(40, 110, 230), QColor(40, 110, 230, 40))}
PENDING_TIP = {SEND: "In attesa: da copiare da PC a iPhone (Applica)",
               REMOVE: "In attesa: da eliminare dall'iPhone (Applica)",
               DELETE: "In attesa: da eliminare dall'iPhone (Applica)",
               UPDATE: "In attesa: i tag da portare da PC a iPhone (Applica)",
               REPLACE: "In attesa: da ricopiare da PC a iPhone (Applica)"}
# i filtri a pulsanti della scheda PC: (chiave, testo, suggerimento); la chiave è una categoria di _categories
PC_CHIPS = [
    ("all", "Tutti", "Tutti i brani della cartella aperta (del formato scelto)"),
    ("absent", "Non sull'iPhone", "I brani che nell'app Musica dell'iPhone non ci sono (anche quelli in attesa di "
                                  "Copia da PC a iPhone)"),
    ("same", "✔ Uguali", "Sull'iPhone c'è questo brano, con la sorgente certa e gli stessi tag"),
    ("stale", "⟳ Tag diversi", "Sull'iPhone c'è questo brano, con la sorgente certa ma tag diversi: Usa i tag o Ricopia"),
    ("probable", "≈ Da rivedere", "Sull'iPhone c'è un brano con gli stessi tag, ma non è collegato a questo file: "
                                  "associalo nella scheda iPhone"),
    ("edited", "✎ Modificati", "Brani con modifiche dei tag in sospeso (i file non cambiano)"),
    ("pending", "＋ In attesa", "Brani con un'azione per l'iPhone in attesa di Applica"),
]
PHRASES = {SEND: "da copiare da PC a iPhone", REMOVE: "da eliminare dall'iPhone", DELETE: "da eliminare dall'iPhone",
           UPDATE: "con i tag da portare da PC a iPhone", REPLACE: "da ricopiare da PC a iPhone",
           EDIT: "con i tag da cambiare sull'iPhone"}



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
        self.open_on_start: Optional[Path] = None   # --open CARTELLA: aperta all'avvio al posto delle cartelle della musica
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
        self.root_folders = []     # le cartelle aperte: le cartelle della musica, o una con Apri cartella
        self.check_results = {}
        self._exit_checked = False     # le modifiche in attesa sono già state applicate (o lasciate) per uscire
        self._fingerprint_job = None   # le impronte in sottofondo (_start_fingerprints)
        self._by_path = {}             # overlay.path_key -> Track dei brani aperti (le azioni in attesa per file)
        self._last_pending = ""        # l'ultima cosa messa in attesa, sotto il totale nella barra blu

        self._album_label = QLabel()
        self._album_stop = QPushButton("Ferma")
        self._album_stop.setToolTip("Interrompe Verifica album online: i risultati già trovati restano")
        self._album_stop.clicked.connect(self._stop_album_check)
        self._album_results_button = QPushButton("Vedi")
        self._album_results_button.setToolTip("La linguetta Controlli, con la verifica e i suoi risultati")
        self._album_results_button.clicked.connect(lambda: self.show_checks(album=True))
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
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(6, 6, 6, 0)
        central_layout.addWidget(self._build_pending_bar())   # le azioni in attesa, in tutte le schede
        central_layout.addWidget(self._tabs, 1)
        self.setCentralWidget(central)
        self._update_pending_bar()
        self.scan_launcher = ScanLauncher(self)
        self.checks_panel = ChecksPanel(self)
        self._tabs.addTab(self.checks_panel, "Controlli")
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
            ("La mia musica", QStyle.SP_DirHomeIcon, self.open_music,
             "Mostra tutte le cartelle della musica di questo PC (Impostazioni → Cartelle della musica)", "Ctrl+L"),
            ("Apri cartella", QStyle.SP_DirOpenIcon, self._open_folder,
             "Mostra i brani di una cartella qualsiasi, in sola lettura: i file non vengono mai modificati",
             "Ctrl+O"),
            ("Importa cartella", QStyle.SP_ArrowDown, self._import_folder,
             "Copia una cartella nella Libreria, ordinandola per Artista/Album", "Ctrl+I"),
            ("Esporta", QStyle.SP_ArrowUp, self._export_selection,
             "Copia i brani selezionati in una cartella, ordinati per Artista/Album", "Ctrl+E"),
            ("Verifica album online", None, self._check_albums,
             "F7: la linguetta Controlli. Confronta gli album scelti (o tutti) con i cataloghi online (Deezer, Apple "
             "Music, Discogs, MusicBrainz): brani mancanti, tag giusti, copertina. In background", "F7"),
            ("Controlla la musica", None, self._scan,
             "F6: la linguetta Controlli. Cerca i problemi confrontando i tuoi brani tra loro (cartelle aperte o "
             "iPhone), senza cataloghi online: file non aggiornati, album con pochi brani, collezioni divise, artisti "
             "scritti in modi diversi, brani duplicati (con l'AI, se configurata)", "F6"),
            ("Impostazioni", GEAR, self._open_settings,
             "Cartelle della musica, AI della scansione, lingua, profili AI e chiavi", "Ctrl+,"),
            ("Informazioni", QStyle.SP_MessageBoxInformation, self._open_about,
             "Versione, cartella dati, variabili d'ambiente e dove sono salvate le chiavi", None),
        ]
        self._task_actions = []
        for text, icon, slot, tip, shortcut in definitions:
            if icon is None:                 # solo il tasto: Controlla e Verifica stanno nella linguetta Controlli
                action = QAction(text, self)
                self.addAction(action)
            else:
                action = QAction(gear_icon() if icon == GEAR else style.standardIcon(icon), text, self)
                toolbar.addAction(action)
            action.setToolTip(tip)
            action.setStatusTip(tip)
            if shortcut is not None:
                action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(slot)
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
        self._reload_button = QPushButton("Rileggi")
        self._reload_button.setToolTip("F5. Rilegge la cartella aperta: i file nuovi, tolti o cambiati (gli altri "
                                       "dalla cache dei tag). Con Maiusc premuto rilegge tutti i file da zero.")
        self._reload_button.clicked.connect(self.reload_folder)
        self._folders_combo = QComboBox()
        self._folders_combo.setToolTip("Quali cartelle mostrare: tutte le cartelle della musica di questo PC "
                                       "(Impostazioni), una sola, o un'altra cartella qualsiasi")
        self._folders_combo.activated.connect(self._folder_chosen)
        top = QHBoxLayout()
        top.addWidget(self._search, 1)
        top.addWidget(QLabel("Cartelle:"))
        top.addWidget(self._folders_combo)
        top.addWidget(QLabel("Formato:"))
        top.addWidget(self._format)
        top.addWidget(self._folder_label, 1)
        top.addWidget(self._reload_button)
        self._hidden_button = QPushButton()
        self._hidden_button.setToolTip("Le cartelle nascoste con il tasto destro: qui le mostri di nuovo")
        self._hidden_button.clicked.connect(self._show_hidden_folders)
        top.addWidget(self._hidden_button)
        self._update_hidden_button()
        self._fill_folder_combo()
        # i filtri a pulsanti, con quanti brani ha ognuno: fanno anche da legenda dei segni della colonna iPhone
        self._chips = ChipBar([text for _key, text, _tip in PC_CHIPS])
        self._chips.set_tips([tip for _key, _text, tip in PC_CHIPS])
        self._chips.currentIndexChanged.connect(lambda _index: self._fill_table())
        # la barra delle azioni sopra la tabella: le stesse voci del tasto destro, per i brani scelti
        self._actions = ActionBar([("copy", "go"), ("replace", ""), ("tags", ""), ("delete", "danger"),
                                   ("edit", ""), ("export", "")])

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
        # E sulla tabella dei brani: il cursore nell'editor dei tag (solo quando la tabella ha il fuoco: in Cerca la E
        # resta una lettera)
        edit_shortcut = QShortcut(QKeySequence("E"), self._table, context=Qt.WidgetShortcut)
        edit_shortcut.activated.connect(self._edit_current_track)
        # Canc sulla tabella: i brani selezionati in attesa per Elimina dall'iPhone (i file del PC mai)
        delete_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self._table, context=Qt.WidgetShortcut)
        delete_shortcut.activated.connect(self._remove_selected_from_phone)
        # F5, in tutta la finestra: Rileggi della scheda che si vede
        refresh_shortcut = QShortcut(QKeySequence(Qt.Key_F5), self)
        refresh_shortcut.activated.connect(self._refresh_current_tab)
        editor_scroll = QScrollArea()
        self._editor_scroll = editor_scroll
        editor_scroll.setWidget(self.editor)
        editor_scroll.setWidgetResizable(True)
        editor_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        editor_scroll.setMinimumWidth(320)
        # l'editor dei tag si chiude (✕) e si riapre con Cambia i tag o il tasto E
        self._editor_panel = QWidget()
        editor_title = QLabel("Cambia i tag")
        editor_title.setObjectName("panelTitle")
        close_editor = QToolButton()
        close_editor.setText("✕")
        close_editor.setToolTip("Chiude l'editor dei tag: si riapre con Cambia i tag o il tasto E")
        close_editor.clicked.connect(lambda: self._editor_panel.setVisible(False))
        editor_head = QHBoxLayout()
        editor_head.addWidget(editor_title, 1)
        editor_head.addWidget(close_editor)
        editor_layout = QVBoxLayout(self._editor_panel)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addLayout(editor_head)
        editor_layout.addWidget(editor_scroll, 1)

        tracks_box = QWidget()
        tracks_layout = QVBoxLayout(tracks_box)
        tracks_layout.setContentsMargins(0, 0, 0, 0)
        tracks_layout.setSpacing(4)
        tracks_layout.addWidget(self._actions)
        tracks_layout.addWidget(self._table, 1)
        left = QSplitter(Qt.Vertical)
        left.addWidget(self.browser)
        left.addWidget(tracks_box)
        left.setSizes([240, 520])
        left.setStretchFactor(1, 1)
        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(self._editor_panel)
        splitter.setSizes([1040, 330])
        splitter.setStretchFactor(0, 1)

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addLayout(top)
        layout.addWidget(self._chips)
        layout.addWidget(splitter, 1)
        self._update_action_bar()
        return tab

    def _build_pending_bar(self) -> QFrame:
        """La barra blu delle azioni sull'iPhone in attesa, sopra le schede: il totale, cosa c'è, l'ultima cosa
        aggiunta (già contata nel totale), Annulla tutto e Applica. Si vede quando c'è qualcosa da dire."""
        self._pending_bar = QFrame()
        self._pending_bar.setObjectName("pendingBar")
        self._pending_bar.setStyleSheet("QFrame#pendingBar { background: rgba(40, 110, 230, 30); "
                                        "border: 1px solid rgba(40, 110, 230, 90); border-radius: 6px; }")
        self._pending_label = QLabel()
        self._pending_label.setWordWrap(True)
        self._pending_last = QLabel()
        self._pending_last.setWordWrap(True)
        self._pending_last.setStyleSheet("color: #2e8b57")
        texts = QVBoxLayout()
        texts.setSpacing(2)
        texts.addWidget(self._pending_label)
        texts.addWidget(self._pending_last)
        self._undo_button = QPushButton("Annulla tutto")
        self._undo_button.setToolTip("Toglie tutte le azioni in attesa: sull'iPhone non cambia niente")
        self._undo_button.clicked.connect(self._undo_pending)
        self._apply_button = QPushButton("Applica…")
        self._apply_button.setProperty("role", "go")
        self._apply_button.clicked.connect(self._apply_pending)
        row = QHBoxLayout(self._pending_bar)
        row.setContentsMargins(10, 6, 10, 6)
        row.addLayout(texts, 1)
        row.addWidget(self._undo_button)
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
            self._tabs.tabBar().setTabTextColor(index, QColor(60, 180, 100) if connected else QColor())
            self._tabs.setTabToolTip(index, "iPhone connesso" if connected else "iPhone non connesso")
            self._update_tab_text()
            QTimer.singleShot(0, self._update_pending_bar)   # Applica si può premere solo a iPhone connesso

    def _update_tab_text(self) -> None:
        """Il titolo della scheda iPhone: "iPhone ●" se è connesso, con quante azioni sono in attesa."""
        index = self._tabs.indexOf(self.iphone_panel) if hasattr(self, "iphone_panel") else -1
        if index >= 0:
            text = "iPhone ●" if self.iphone_panel.connected else "iPhone"
            total = self.pending.total()
            if total:
                text += f" · {total} in attesa"
            self._tabs.setTabText(index, text)

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
        removed = self.pending.reconcile(self.tracks, lambda track: self._device_state(track)[0])
        removed += self.pending.reconcile_phone(tracks, self._update_still_needed)
        if removed:
            self._save_pending()
        self._model.device_header_tip = (f"Nell'app Musica dell'iPhone ({label}): ✔ stesso brano, ⟳ stesso brano "
                                         "con tag diversi, ≈ forse lo stesso (abbinato solo per i tag: da rivedere), "
                                         "vuoto = non c'è; la spunta: voglio il brano sull'iPhone")
        self.iphone_panel.set_phone_tracks(tracks, label)
        self._update_chip_counts()
        self._fill_table()
        self.browser.refresh_phone_states()
        self._update_pending_bar()

    def _startup(self) -> None:
        """All'avvio: --open; altrimenti quello che era aperto l'ultima volta: le cartelle della musica di questo
        computer (anche la prima volta) o una cartella aperta con Apri cartella, se c'è ancora; altrimenti le cartelle
        della musica."""
        self._load_device_listing()
        last = self.app_settings.last_opened
        music = self._existing_music_dirs()
        if self.open_on_start is not None:
            self.load_folder(self.open_on_start)
        elif last and last != MUSIC_MARK and Path(last).is_dir():
            self.load_folder(Path(last))
        elif music:
            self.open_music()
            if last and last != MUSIC_MARK:
                self.statusBar().showMessage(f"L'ultima cartella usata non è disponibile ({last}): apro le "
                                             "cartelle della musica", 15000)
        else:
            self.statusBar().showMessage(
                "Benvenuto! Premi \"Apri cartella\" per vedere la tua musica, o \"Importa cartella\" per copiarla "
                "nella Libreria. Le cartelle della musica di questo PC si scelgono in Impostazioni.")

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

    def music_dirs(self) -> list:
        """Le cartelle della musica di questo computer (Impostazioni), in ordine."""
        result = self.app_settings.music_dirs()
        return result

    def _existing_music_dirs(self) -> list:
        result = []
        for folder in self.music_dirs():
            if folder.is_dir():
                result.append(folder)
        return result

    def preferred_order(self) -> tuple:
        """Tra più copie dello stesso brano: prima le Cartelle preferite (nomi), poi l'ordine delle cartelle della
        musica (library.preference)."""
        order = list(self.app_settings.preferred_folders)
        for folder in self.music_dirs():
            order.append(str(folder))
        result = tuple(order)
        return result

    @property
    def root_folder(self) -> Optional[Path]:
        """La cartella aperta, se è una sola (None con più cartelle o nessuna)."""
        result = self.root_folders[0] if len(self.root_folders) == 1 else None
        return result

    def showing_music(self) -> bool:
        """Sono aperte le cartelle della musica di questo computer (tutte quelle che ci sono)."""
        opened = set()
        for folder in self.root_folders:
            opened.add(path_key(folder))
        music = set()
        for folder in self._existing_music_dirs():
            music.add(path_key(folder))
        result = bool(opened) and opened == music
        return result

    def is_open(self, path: Path) -> bool:
        """Il file è in una delle cartelle aperte."""
        result = False
        for folder in self.root_folders:
            if Path(path).is_relative_to(folder):
                result = True
        return result

    def open_description(self) -> str:
        """Cosa è aperto, per i messaggi: le cartelle della musica, o la cartella."""
        if self.showing_music() and len(self.root_folders) > 1:
            result = f"le cartelle della musica ({len(self.root_folders)})"
        elif self.root_folders:
            result = str(self.root_folders[0])
        else:
            result = ""
        return result

    def save_settings(self) -> None:
        self.app_settings.save()

    def _open_settings(self) -> None:
        before = (self.library_dir(), self.music_dirs())
        showing = self.showing_music()
        various = list(self.app_settings.various_artists)
        dialog = SettingsDialog(self.app_settings, self)
        if dialog.exec():
            self._model.refresh()                  # il percorso completo delle cartelle, se è cambiato
            self.iphone_panel.pc_changed()
            if self.app_settings.various_artists != various:     # gli elenchi Artisti si rifanno
                set_various_artist_names(self.app_settings.various_artists)
                self._rebuild_views()
                self.iphone_panel.regroup()
            self._fill_folder_combo()
            if (self.library_dir(), self.music_dirs()) != before and (showing or not self.root_folders):
                self.open_music()

    def _open_about(self) -> None:
        AboutDialog(self).exec()

    def _scan(self) -> None:
        """F6: la linguetta Controlli, su Controlla la musica."""
        self.show_checks()
        self.checks_panel.focus_scan()

    def show_checks(self, album: bool = False) -> None:
        self._tabs.setCurrentWidget(self.checks_panel)
        if album:
            self.checks_panel.results.setCurrentIndex(1)

    def open_music(self) -> None:
        """La mia musica: tutte le cartelle della musica di questo computer insieme (la Libreria si crea se manca)."""
        library = self.library_dir()
        if library in self.music_dirs():
            library.mkdir(parents=True, exist_ok=True)
        folders = self._existing_music_dirs()
        if folders:
            self.load_folders(folders)
        else:
            self.statusBar().showMessage("Le cartelle della musica di questo PC non ci sono (dischi scollegati?): "
                                         "sceglile in Impostazioni → Cartelle della musica", 15000)

    def open_library(self) -> None:
        """Per compatibilità: apre le cartelle della musica."""
        self.open_music()

    def _open_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Cartella da aprire",
                                                  self.app_settings.last_folder)
        if folder:
            self.app_settings.last_folder = folder
            self.save_settings()
            self.load_folder(Path(folder))

    def _fill_folder_combo(self) -> None:
        """La scelta "Cartelle" della scheda PC: tutte le cartelle della musica, ognuna da sola (la Libreria segnata),
        la cartella aperta con Apri cartella se è un'altra, e Apri un'altra cartella…"""
        combo = self._folders_combo
        combo.blockSignals(True)
        combo.clear()
        music = self.music_dirs()
        library = path_key(self.library_dir())
        combo.addItem(f"Tutte le cartelle della musica ({len(music)})", "*")
        combo.setItemData(0, "\n".join(str(folder) for folder in music), Qt.ToolTipRole)
        current = 0 if self.showing_music() else -1
        for folder in music:
            text = folder.name or str(folder)
            if path_key(folder) == library:
                text += tr(" (Libreria)")
            combo.addItem(text, str(folder))
            combo.setItemData(combo.count() - 1, str(folder), Qt.ToolTipRole)
            if current < 0 and self.root_folder is not None and path_key(self.root_folder) == path_key(folder):
                current = combo.count() - 1
        if current < 0 and self.root_folder is not None:
            combo.addItem(f"Altra: {self.root_folder.name or self.root_folder}", str(self.root_folder))
            combo.setItemData(combo.count() - 1, str(self.root_folder), Qt.ToolTipRole)
            current = combo.count() - 1
        combo.addItem("Apri un'altra cartella…", "")
        combo.setCurrentIndex(max(0, current))
        combo.blockSignals(False)

    def _folder_chosen(self, index: int) -> None:
        value = self._folders_combo.itemData(index)
        if value == "*":
            self.open_music()
        elif value:
            self.load_folder(Path(value))
        else:
            self._fill_folder_combo()           # torna a quello aperto, poi la finestra per scegliere
            self._open_folder()

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
        """Rileggi: rilegge le cartelle aperte; con Maiusc premuto tutti i file, senza la cache dei tag."""
        if not self.root_folders:
            QMessageBox.information(self, "Rileggi", "Nessuna cartella aperta")
        else:
            force = bool(QApplication.keyboardModifiers() & Qt.ShiftModifier)
            self.load_folders(list(self.root_folders), force)

    def load_folder(self, folder: Path, force: bool = False) -> None:
        self.load_folders([folder], force)

    def load_folders(self, folders: list, force: bool = False) -> None:
        """Legge le cartelle (una, o le cartelle della musica insieme) e le mostra nella scheda PC; un file in due
        cartelle annidate conta una volta."""
        if self._album_job is not None and self._album_job.running:
            self._stop_album_check()           # i risultati varrebbero per i brani di prima
        folders = list(folders)

        def work(progress, cancel):
            value = []
            seen = set()
            for folder in folders:
                if not cancel.is_set():
                    for track in scan_folder(folder, progress, cancel, self.tag_cache, force):
                        key = path_key(track.path)
                        if key not in seen:
                            seen.add(key)
                            value.append(track)
            return value

        def done(tracks):
            for folder in folders:
                protect_folder(folder)
            self.overlay.apply(tracks)
            self._all_tracks = tracks
            self.tracks = self._without_hidden(tracks)
            self.root_folders = folders
            showing_music = self.showing_music()
            self.app_settings.last_opened = MUSIC_MARK if showing_music else str(folders[0])   # al prossimo avvio
            self.save_settings()
            self.check_results = {}
            if showing_music and len(folders) > 1:
                label = f"Le cartelle della musica di questo PC: {', '.join(str(folder) for folder in folders)}"
            elif path_key(folders[0]) == path_key(self.library_dir()):
                label = f"Libreria: {folders[0]}"
            else:
                label = f"Cartella: {folders[0]}"
            self._folder_label.setText(label)
            self._folder_label.setToolTip("\n".join(str(folder) for folder in folders))
            self._fill_folder_combo()
            self._rebuild_views()
            self._tabs.setCurrentIndex(0)
            hidden = len(tracks) - len(self.tracks)
            text = f"{len(self.tracks)} brani caricati"
            if hidden:
                text += f" ({hidden} nelle cartelle nascoste)"
            self.statusBar().showMessage(text, 8000)
            self.iphone_panel.check_missing_sources()
            self._start_fingerprints()

        self._stop_fingerprints()                # erano per le cartelle di prima
        self.runner.run("Lettura brani", work, done)

    # ================================================================== impronte in sottofondo

    def _start_fingerprints(self) -> None:
        """In sottofondo, dopo l'apertura di una cartella: l'impronta dell'audio dei file che non ce l'hanno ancora
        nella cache dei tag (nuovi, spostati, cambiati), così un file spostato e rinominato si ritrova sempre
        (relocate). La prima volta tutta la cartella, poi solo i file nuovi o cambiati. Non blocca niente; la cache
        si salva alla fine."""
        paths = []
        for track in self.tracks:
            if not track.error and track.path.suffix.lower() in FINGERPRINT_SUFFIXES:
                paths.append(track.path)
        cache = self.tag_cache

        def work(progress, cancel, emit):
            missing = []
            for path in paths:
                if not cancel.is_set() and not cache.fingerprint(path):
                    missing.append(path)
            emit((FINGERPRINTS_TO_DO, len(missing)))
            done = 0
            start = 0
            while start < len(missing) and not cancel.is_set():
                batch = missing[start:start + FINGERPRINT_BATCH]
                for path, value in provenance.file_fingerprints(batch, None, cancel).items():
                    if value:
                        cache.store_fingerprint(path, value)
                        done += 1
                start += FINGERPRINT_BATCH
            emit((FINGERPRINTS_DONE, done))

        job = BackgroundJob(work)
        job.item.connect(self._fingerprints_news)
        job.finished.connect(self.tag_cache.save)
        self._fingerprint_job = job
        job.start()

    def _fingerprints_news(self, value) -> None:
        kind, count = value
        if kind == FINGERPRINTS_TO_DO and count >= FINGERPRINT_NOTICE:
            self.statusBar().showMessage(f"Impronte dell'audio in sottofondo: {count} file (servono per ritrovare i "
                                         "file spostati o rinominati)", 10000)
        elif kind == FINGERPRINTS_DONE and count >= FINGERPRINT_NOTICE:
            self.statusBar().showMessage(f"Impronte dell'audio calcolate: {count} file", 8000)

    def _stop_fingerprints(self) -> None:
        if self._fingerprint_job is not None and self._fingerprint_job.running:
            self._fingerprint_job.cancel()

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
        self._by_path = {}
        for track in self.tracks:
            self._by_path[path_key(track.path)] = track
        assign_groups(self.tracks)
        self._update_format_counts()
        self.browser.set_data(group_by_album(self.format_tracks()), self.check_results)
        self._update_chip_counts()
        self._fill_table(keep_tracks)
        self.iphone_panel.pc_changed()
        self._update_pending_bar()

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

    def _categories(self, track) -> set:
        """I filtri a pulsanti (PC_CHIPS) in cui sta un brano: tutti; non sull'iPhone, ✔, ⟳ o ≈ (come la colonna
        iPhone); modificato; in attesa."""
        result = {"all"}
        if self.overlay.is_edited(track.path):
            result.add("edited")
        if self._phone_index is not None and not track.error:
            if self.pending.get(track.path):
                result.add("pending")
            status, _phone_track, linked = self._device_state(track)
            if status == DEVICE_ABSENT:
                result.add("absent")
            elif not linked:
                result.add("probable")
            elif status == DEVICE_SAME:
                result.add("same")
            else:
                result.add("stale")
        return result

    def _update_chip_counts(self) -> None:
        """Il numero di brani di ogni filtro a pulsanti, tra quelli del formato scelto."""
        counts = {}
        for key, _text, _tip in PC_CHIPS:
            counts[key] = 0
        for track in self.format_tracks():
            for key in self._categories(track):
                counts[key] += 1
        values = []
        for key, _text, _tip in PC_CHIPS:
            values.append(counts[key])
        self._chips.set_counts(values)

    def _update_action_bar(self) -> None:
        """La barra delle azioni sopra la tabella: le voci del tasto destro (pc_entries) per i brani scelti (o, senza
        selezione, quelli dell'artista o dell'album scelti negli elenchi), più Cambia i tag ed Esporta."""
        if hasattr(self, "_actions"):
            tracks = self.selected_tracks()
            entries = self.pc_entries(tracks) if tracks else []
            bar = {}
            notes = []
            keys = ["copy", "replace", "tags", "delete"]
            index = 0
            for text, enabled, slot in entries:
                if slot is not None and index < len(keys):
                    bar[keys[index]] = (text, enabled, slot)
                    index += 1
                elif slot is None:
                    notes.append(text)
            for key in keys:
                if key not in bar:
                    bar[key] = (tr({"copy": "Copia da PC a iPhone", "replace": "Ricopia da PC a iPhone",
                                    "tags": "Usa i tag da PC a iPhone", "delete": "Elimina dall'iPhone"}[key]),
                                False, None)
            bar["edit"] = ("Cambia i tag…", bool(tracks), self._open_editor)
            bar["export"] = ("Esporta in una cartella…", bool(tracks), self._export_selection)
            if not tracks:
                who = "Scegli dei brani, o un artista o un album:"
            elif len(tracks) == 1:
                who = "1 brano scelto:"
            else:
                who = f"{len(tracks)} brani scelti:"
            self._actions.set_entries(who, bar, " · ".join(notes))

    def _open_editor(self) -> None:
        """Cambia i tag (barra delle azioni, tasto destro): l'editor a destra, con il cursore nel primo campo."""
        self._editor_panel.setVisible(True)
        if self.editor.focus_first_field():
            self._editor_scroll.ensureWidgetVisible(self.editor.focusWidget() or self.editor)

    def _visible_tracks(self) -> list:
        track_filter = self._track_filter()
        needle = self._search.text().strip().lower()
        chip = PC_CHIPS[self._chips.currentIndex()][0]
        visible = []
        for track in self.format_tracks():
            shown = self._passes(track, track_filter)
            if shown and chip != "all":
                shown = chip in self._categories(track)
            if shown and needle:
                haystack = " ".join([track.title, track.tags.artist, track.tags.album_artist,
                                     track.tags.album]).lower()
                shown = needle in haystack
            if shown:
                visible.append(track)
        # lo stesso album in due copie (due cartelle, o FLAC e MP3 nella stessa cartella): prima tutta una copia, poi
        # l'altra, non mescolate
        visible.sort(key=lambda t: (t.album_key[0].lower(), t.album_key[1].lower(), album_folder(t.path).lower(),
                                    t.path.suffix.lower()) + track_sort_key(t))
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

    # ------------------------------------------------------------------ mettere in attesa

    def queue_files(self, tracks: list, action: str) -> None:
        """Mette in attesa un'azione per file del PC (Copia, Ricopia, Usa i tag, Elimina dall'iPhone): parte con
        Applica. Usa i tag vale solo per i brani ⟳ associati, Ricopia ed Elimina per quelli con la sorgente certa
        (registro); un brano abbinato solo per i tag non si tocca: prima si associa la sorgente."""
        queued = []
        albums = set()
        for track in tracks:
            if not track.error:
                status, phone_track, linked = self._device_state(track)
                if action == SEND:
                    good = status == DEVICE_ABSENT
                elif action == UPDATE:
                    good = status == DEVICE_STALE and linked and phone_track.from_computer
                else:                         # Ricopia (anche una copertina nuova con gli stessi tag), Elimina
                    good = status != DEVICE_ABSENT and linked and phone_track.from_computer
                if good:
                    self.pending.set(track.path, action)
                    queued.append(track)
                    albums.add(track.album_key)
        if action == SEND and len(queued) > 1:
            text = f"Appena aggiunti: {len(queued)} brani ({len(albums)} album) {tr(PHRASES[action])}"
        else:
            text = f"Appena aggiunti: {songs(len(queued))} {tr(PHRASES[action])}"
        self.pending_changed(text if queued else "")

    def queue_pairs(self, pairs: list, action: str) -> None:
        """Ricopia o Usa i tag da PC a iPhone per coppie (PhoneTrack, Track) scelte nella scheda iPhone (anche con il
        file fuori dalle cartelle aperte)."""
        for phone_track, track in pairs:
            self.pending.set_phone(phone_track.pid, action, track.path)
        self.pending_changed(f"Appena aggiunti: {songs(len(pairs))} {tr(PHRASES[action])}" if pairs else "")

    def queue_deletes(self, phone_tracks: list) -> None:
        """Elimina dall'iPhone, per brani dell'iPhone messi da un computer."""
        count = 0
        for item in phone_tracks:
            if item.from_computer:
                link = self.registry.get(item.sync_id) if item.sync_id else None
                path = link.path if link is not None and link.here else None
                self.pending.set_phone(item.pid, DELETE, path)
                count += 1
        self.pending_changed(f"Appena aggiunti: {songs(count)} {tr(PHRASES[DELETE])}. I file del PC non cambiano."
                             if count else "")

    def queue_edits(self, phone_tracks: list, values: dict, extra: str = "") -> None:
        """Cambia i tag sull'iPhone: gli stessi valori per i brani scelti (messi da un computer)."""
        count = 0
        for item in phone_tracks:
            if item.from_computer:
                self.pending.set_phone(item.pid, EDIT, values=values)
                count += 1
        self.pending_changed(f"Appena aggiunti: {songs(count)} {tr(PHRASES[EDIT])}{tr(extra)}" if count else "")

    def pending_changed(self, message: str = "") -> None:
        """La coda è cambiata: si salva, si ridisegnano spunte e segni, la barra dice il totale e l'ultima cosa."""
        if message:
            self._last_pending = message
        self._save_pending()
        self._restyle_rows([])
        self.browser.refresh_phone_states()
        self._update_chip_counts()
        if PC_CHIPS[self._chips.currentIndex()][0] == "pending":
            self._fill_table()
        self._update_pending_bar()
        self.iphone_panel.pending_changed()

    def _update_still_needed(self, phone_track, path: str) -> bool:
        """Usa i tag da PC a iPhone è ancora da fare: il file del PC ha tag diversi da quelli dell'iPhone."""
        track = self.track_for_path(path)
        result = track is not None and bool(differences(track.tags, phone_track.tags))
        return result

    def track_for_path(self, path: str):
        """Il brano di un file del PC: quello aperto (con le modifiche in sospeso) o letto dal file; None se manca."""
        result = None
        if path:
            result = self._by_path.get(path_key(path))
            if result is None and Path(path).is_file():
                result = self.source_track(Path(path))
        return result

    def pending_jobs(self) -> list:
        """Le azioni in attesa che si possono fare ora (pending.Job): per un file del PC serve il brano aperto e,
        tranne Copia, il suo brano dell'iPhone collegato dal registro; per un brano dell'iPhone, che ci sia ancora.
        Le altre restano in attesa (un file di una cartella non aperta, l'iPhone non ancora letto)."""
        by_pid = {}
        for item in self.phone_tracks:
            by_pid[item.pid] = item
        jobs = []
        for key, entry in self.pending.entries():
            action = entry["action"]
            pid = key_pid(key)
            if pid is None:
                track = self._by_path.get(key[len(FILE_PREFIX):])
                if track is not None and not track.error and self._phone_index is not None:
                    status, phone_track, linked = self._device_state(track)
                    usable = phone_track is not None and linked and phone_track.from_computer
                    if action == SEND and status == DEVICE_ABSENT:
                        jobs.append(Job(key, SEND, track=track))
                    elif action == REMOVE and usable:
                        jobs.append(Job(key, DELETE, track=track, phone=phone_track))
                    elif action == UPDATE and status == DEVICE_STALE and usable:
                        jobs.append(Job(key, UPDATE, track=track, phone=phone_track))
                    elif action == REPLACE and usable:
                        jobs.append(Job(key, REPLACE, track=track, phone=phone_track))
            else:
                phone_track = by_pid.get(pid)
                if phone_track is not None and phone_track.from_computer:
                    if action == DELETE:
                        jobs.append(Job(key, DELETE, phone=phone_track))
                    elif action == EDIT:
                        jobs.append(Job(key, EDIT, phone=phone_track, values=dict(entry.get("values", {}))))
                    else:
                        track = self.track_for_path(entry.get("path", ""))
                        if track is not None:
                            jobs.append(Job(key, action, track=track, phone=phone_track))
        return jobs

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

    def _update_pending_bar(self) -> None:
        """La barra blu: il totale e cosa c'è ("4 brani da copiare da PC a iPhone · …"), sotto l'ultima cosa messa in
        attesa; Applica si preme a iPhone connesso e libero."""
        if hasattr(self, "_pending_bar"):
            total = self.pending.total()
            jobs = self.pending_jobs() if total else []
            self._pending_bar.setVisible(total > 0 or bool(self._last_pending))
            if total:
                detail = summary(jobs) + ". " if jobs else ""
                waiting = total - len(jobs)
                later = tr(f"{waiting} per brani non aperti ora (o con l'iPhone non ancora letto): partono quando ci "
                           "sono. ") if waiting else ""
                text = (f"<b>Azioni in attesa per l'iPhone: {total}.</b> {detail}{later}"
                        "Partono solo con Applica, a iPhone connesso.")
            else:
                text = "<b>Nessuna azione in attesa.</b> Copia, Ricopia, Usa i tag, Cambia i tag ed Elimina mettono " \
                       "qui le azioni per l'iPhone."
            self._pending_label.setText(text)
            self._pending_last.setText(self._last_pending)
            self._pending_last.setVisible(bool(self._last_pending))
            ready = self.iphone_panel.connected and not self.runner.is_busy
            self._apply_button.setText(f"Applica {len(jobs)} azioni…" if len(jobs) != 1 else "Applica 1 azione…")
            self._apply_button.setEnabled(bool(jobs))
            self._apply_button.setToolTip("" if ready else "L'elenco si vede anche così; per applicarle connetti "
                                                           "l'iPhone")
            self._undo_button.setEnabled(total > 0)
            self._update_tab_text()
            self._update_action_bar()

    def _undo_pending(self) -> None:
        total = self.pending.total()
        answer = QMessageBox.question(self, "Annulla tutto",
                                      f"Togliere tutte le {total} azioni in attesa per l'iPhone? Sull'iPhone non "
                                      "cambia niente; le spunte tornano come sono sull'iPhone.")
        if answer == QMessageBox.Yes:
            self.pending.clear()
            self._last_pending = "Tolte tutte le azioni in attesa: sull'iPhone non è cambiato niente."
            self.pending_changed()
            self._fill_table()

    def _remove_pending(self, keys: list) -> list:
        """Dalla finestra di Applica: toglie le azioni dalla coda e restituisce quelle rimaste."""
        removed = self.pending.remove(keys)
        if removed:
            self.pending_changed(f"Tolte {removed} azioni dalla coda: non partono.")
        result = self.pending_jobs()
        return result

    def _apply_pending(self) -> None:
        """Applica: la finestra con tutte le azioni (ognuna si toglie), poi le fa tutte insieme."""
        jobs = self.pending_jobs()
        if not jobs:
            QMessageBox.information(self, "Applica", "Nessuna azione da fare ora: quelle in attesa sono per brani non "
                                    "aperti o l'iPhone non è ancora stato letto.")
        else:
            panel = self.iphone_panel
            ready = panel.connected and not self.runner.is_busy
            dialog = ApplyDialog(self, jobs, self._remove_pending, panel.jobs_seconds, panel.jobs_notes, ready,
                                 panel.device_name)
            if dialog.exec() and dialog.jobs:
                panel.apply_jobs(dialog.jobs)

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

    def pc_entries(self, tracks: list) -> list:
        """Le azioni verso l'iPhone per brani del PC (tasto destro sulla tabella o su un artista/album, barra delle
        azioni): [(testo, attiva, funzione)], funzione None per una nota grigia. Tutte vanno in attesa e partono con
        Applica: Copia i brani che sull'iPhone non ci sono; Ricopia e Usa i tag quelli ⟳ con la sorgente certa
        (registro); Elimina quelli con la sorgente certa. Un brano abbinato solo per i tag (≈) non si tocca."""
        absent = []
        albums = set()
        stale = []
        linked_here = []
        seen = set()
        unlinked = 0
        waiting = 0
        for track in tracks:
            if not track.error and self._phone_index is not None:
                status, phone_track, linked = self._device_state(track)
                if self.pending.get(track.path):
                    waiting += 1
                elif status == DEVICE_ABSENT:
                    absent.append(track)
                    albums.add(track.album_key)
                elif linked and phone_track.from_computer and phone_track.pid not in seen:
                    seen.add(phone_track.pid)
                    linked_here.append(track)
                    if status == DEVICE_STALE:
                        stale.append(track)
                elif not linked:
                    unlinked += 1
        if len(absent) == 1:
            copy_text = "Copia 1 brano da PC a iPhone"
        elif absent:
            copy_text = f"Copia {len(absent)} brani ({len(albums)} album) da PC a iPhone"
        else:
            copy_text = "Copia da PC a iPhone: sull'iPhone ci sono già tutti"
        stale_text = songs(len(stale)) if stale else "nessun brano ⟳ con la sorgente"
        result = [
            (copy_text, bool(absent), lambda: self.queue_files(absent, SEND)),
            (f"Ricopia da PC a iPhone: {stale_text}", bool(stale), lambda: self.queue_files(stale, REPLACE)),
            (f"Usa i tag da PC a iPhone: {stale_text}", bool(stale), lambda: self.queue_files(stale, UPDATE)),
            (f"Elimina {songs(len(linked_here))} dall'iPhone" if linked_here else
             "Elimina dall'iPhone: nessun brano con la sorgente", bool(linked_here),
             lambda: self.queue_files(linked_here, REMOVE)),
        ]
        if waiting:
            result.append((f"{songs(waiting)} già in attesa (Applica)", False, None))
        if unlinked:
            result.append((f"{songs(unlinked)} sull'iPhone abbinati solo per i tag (≈): per toglierli o aggiornarli "
                           "prima associa la sorgente (scheda iPhone)", False, None))
        if self._phone_index is None:
            result.append(("Collega l'iPhone: la sua musica non è ancora stata letta", False, None))
        return result

    def browser_menu_entries(self, tracks: list) -> list:
        """Le voci del tasto destro su un artista o un album: le stesse dei brani (pc_entries), per tutti i suoi."""
        result = self.pc_entries(tracks)
        return result

    def _browser_menu(self, where) -> None:
        """Tasto destro su un artista o un album: le azioni verso l'iPhone per tutti i suoi brani."""
        show_entries_menu(self, self.browser_menu_entries(self.browser.menu_tracks), where, True)

    def _tracks_menu(self, where) -> None:
        """Tasto destro sui brani: le azioni verso l'iPhone (pc_entries, in attesa fino ad Applica), poi i comandi
        sui file e Nascondi la cartella."""
        tracks = self._selected_table_tracks()
        if tracks:
            menu = QMenu(self)
            for text, enabled, slot in self.pc_entries(tracks):
                action = menu.addAction(text)
                action.setEnabled(enabled)
                if slot is not None:
                    action.triggered.connect(slot)
            menu.addSeparator()
            edit = menu.addAction("Cambia i tag…")
            edit.triggered.connect(self._edit_current_track)
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

    def _refresh_current_tab(self) -> None:
        """F5: Rileggi della scheda che si vede (iPhone: rilegge la sua musica; le altre: le cartelle aperte)."""
        if self._tabs.currentWidget() is self.iphone_panel:
            self.iphone_panel.refresh()
        else:
            self.reload_folder()

    def _remove_selected_from_phone(self) -> None:
        """Canc sulla tabella: i brani selezionati (o quello su cui si è) che sono sull'iPhone con la sorgente certa
        vanno in attesa per Elimina dall'iPhone (parte con Applica). Sul PC non cambia niente."""
        current = self._table.currentIndex()
        if not self._selected_rows() and current.isValid():
            self._table.selectRow(current.row())
        removable = []
        for track in self._selected_table_tracks():
            if not track.error and self._phone_index is not None:
                status, phone_track, linked = self._device_state(track)
                if status != DEVICE_ABSENT and linked and phone_track.from_computer:
                    removable.append(track)
        if not removable:
            self.statusBar().showMessage("Nessuno dei brani selezionati è sull'iPhone con la sorgente associata", 8000)
        else:
            self.queue_files(removable, REMOVE)

    def _edit_current_track(self) -> None:
        """Il tasto E sulla tabella: il brano su cui si è (se nessuno è selezionato, quello con il cursore) nell'editor,
        con il cursore nel primo campo."""
        current = self._table.currentIndex()
        if not self._selected_rows() and current.isValid():
            self._table.selectRow(current.row())
        self._open_editor()

    def _selection_changed(self) -> None:
        """L'editor dei brani selezionati; senza brani selezionati ma con un album scelto negli elenchi, la copertina
        e il nome dell'album."""
        tracks = self._selected_table_tracks()
        albums = self.browser.selected_albums()
        if not tracks and len(albums) == 1:
            self.editor.show_album(self.browser.album_tracks(next(iter(albums))))
        else:
            self.editor.set_tracks(tracks)
        self._update_action_bar()

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
        la differenza si vede (⟳) e si allinea a mano (Usa i tag, o la casella "Anche sull'iPhone")."""
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
        """Salva modifiche dell'editor dei tag. Con la casella "Anche sull'iPhone" i brani con la sorgente certa
        sull'iPhone vanno in attesa: Usa i tag da PC a iPhone, o Ricopia se è cambiata la copertina."""
        tracks = self._selected_table_tracks()
        pairs = []
        for track in tracks:
            new_tags = None
            if changes:
                new_tags = track.tags.copy()
                for name, value in changes.items():
                    setattr(new_tags, name, value)
            pairs.append((track, new_tags))
        if pairs:
            also_phone = self.editor.also_phone.isChecked()
            self.editor.also_phone.setChecked(False)
            self.apply_tag_changes(pairs, cover)
            if also_phone:
                self.queue_files(tracks, REPLACE if cover is not None else UPDATE)

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
                    self.open_music()

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

    def albums_to_check(self) -> list:
        result = self._albums_to_check()
        return result

    def album_discogs_ready(self) -> bool:
        result = self.album_clients[SERVICE_DISCOGS].available()
        return result

    def _albums_to_check(self) -> list:
        groups = group_by_album(self.format_tracks())
        track_filter = self._track_filter()
        selected = []
        for key in sorted(groups, key=lambda k: (k[0].lower(), k[1].lower())):
            if self._passes(groups[key][0], track_filter):
                selected.append(groups[key])
        return selected

    def _check_albums(self) -> None:
        """F7: la linguetta Controlli, su Verifica album online."""
        self.show_checks(album=True)
        self.checks_panel.focus_album()

    def start_album_check_from_panel(self) -> None:
        """Avvia la verifica della linguetta Controlli, con le sue scelte (ricordate)."""
        albums = self._albums_to_check()
        options = self.checks_panel.album_options
        if self._album_job is not None and self._album_job.running:
            QMessageBox.information(self, "Verifica album online", "La verifica è già in corso: aspetta la fine o "
                                    "premi Ferma.")
        elif not albums:
            QMessageBox.information(self, "Verifica album online", "Non ci sono album da verificare.")
        else:
            provider = self.iphone_panel._ai_provider()
            settings = self.app_settings
            settings.album_services = options.services()
            settings.album_ai = options.use_ai
            self.save_settings()
            clients = []
            for service in options.services():
                clients.append(self.album_clients[service])
            chooser = ai_chooser(provider) if options.use_ai and provider is not None else None
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
        for widget in (self._album_label, self._album_results_button):
            widget.setVisible(True)
        self._album_stop.setVisible(False)              # Ferma sta nella linguetta Controlli
        self._album_panel_state(True, f"In corso: 0 di {len(albums)} album")
        job.start()

    def _album_panel_state(self, running: bool, text: str) -> None:
        panel = getattr(self, "checks_panel", None)
        if panel is not None:
            panel.album_state(running, text)

    def _album_checked(self, result) -> None:
        self._album_results.append(result)
        self.store_check_result(result)
        self.browser.refresh_check_icons(self.check_results)
        self._album_label.setText(f"Verifica album online: {len(self._album_results)} di {self._album_total}")
        self._album_panel_state(True, f"In corso: {len(self._album_results)} di {self._album_total} album")

    def _stop_album_check(self) -> None:
        if self._album_job is not None:
            self._album_job.cancel()
            self._album_stop.setEnabled(False)
            self._album_label.setText("Verifica album online: interruzione…")
            self._album_panel_state(True, "Interruzione…")

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
        self._album_panel_state(False, self._album_label.text())
        self._album_results_button.setVisible(bool(self._album_results))
        if self._album_results:
            self._open_album_results()

    def _open_album_results(self) -> None:
        """I risultati nella linguetta Controlli (si può continuare a usare il programma)."""
        if self._album_results:
            self.checks_panel.show_album_results(AlbumCheckDialog(self._album_results, self, embedded=True))

    # ================================================================== chiusura

    def closeEvent(self, event) -> None:
        if self._album_job is not None and self._album_job.running:
            self._album_job.cancel()
        self._stop_fingerprints()
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
                self.iphone_panel.apply_jobs(self.pending_jobs(), closing=True, then=self.close)
            else:
                event.ignore()

    def _ask_pending_on_exit(self) -> str:
        """Con azioni in attesa per l'iPhone che si possono fare chiede se applicarle prima di uscire, con il tempo
        stimato. EXIT_NOW, EXIT_AFTER_APPLY o EXIT_CANCEL."""
        jobs = self.pending_jobs()
        count = len(jobs)
        if not count:
            result = EXIT_NOW
        else:
            seconds = self.iphone_panel.jobs_seconds(jobs)
            text = (f"Ci sono azioni in attesa per l'iPhone non ancora applicate: {summary(jobs)}.\n\n"
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
