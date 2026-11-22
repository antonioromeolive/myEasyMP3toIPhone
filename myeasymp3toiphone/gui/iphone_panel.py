"""Scheda iPhone: connessione, la musica dell'app Musica (com'è nell'app, confrontata con il PC) e, con il tasto
destro, salva su PC, rimpiazza con la versione del PC, cambia i tag, elimina. L'invio dal PC parte dalla scheda PC.
La scrittura sull'iPhone passa per phone_actions (il servizio di sincronizzazione di Apple)."""

import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QTreeWidget, QVBoxLayout, QWidget,
)

from .. import adoption, iphone, phone_actions, provenance
from ..config import config_dir
from ..i18n import tr
from ..library import Track, copy_organized, scan_folder
from ..phone_library import DEVICE_SAME, DEVICE_STALE, comparison, differences, pc_matches, playlist_reminder
from .compare_tip import comparison_html, show_on_tooltip
from .file_actions import add_file_entries
from .theme import set_role
from .browser import SORT_ROLE, SortableItem

DEVICE_POLL_MS = 3000   # ogni quanto si guarda se è stato collegato (o scollegato) un iPhone
DOWNLOAD_TEMP_FOLDER = ".salvataggio_iphone"
PID_ROLE = Qt.UserRole
COLUMNS = ["N.", "Sul PC", "Sorgente", "Titolo", "Artista", "Artista album", "Album", "Anno", "Genere", "Durata",
           "File della sorgente"]
(COL_NUMBER, COL_PC, COL_ORIGIN, COL_TITLE, COL_ARTIST, COL_ALBUM_ARTIST, COL_ALBUM, COL_YEAR, COL_GENRE,
 COL_LENGTH, COL_SOURCE_FILE) = range(len(COLUMNS))
COLUMN_WIDTHS = {COL_NUMBER: 50, COL_PC: 60, COL_ORIGIN: 110, COL_TITLE: 260, COL_ARTIST: 180, COL_ALBUM_ARTIST: 150,
                 COL_ALBUM: 220, COL_YEAR: 55, COL_GENRE: 100, COL_LENGTH: 60, COL_SOURCE_FILE: 320}
PC_STATE_ROLE = Qt.UserRole + 8   # lo stato della colonna Sul PC (PC_*), per il filtro Mostra
# la colonna Sul PC: com'è il brano dell'iPhone rispetto al PC
PC_SAME = "uguale"            # ✔ la sorgente certa (registro), stessi tag
PC_STALE = "tag diversi"      # ⟳ la sorgente certa, tag diversi: si può rimpiazzare
PC_PROBABLE = "probabile"     # ≈ un file con titolo, album e artista uguali, ma non è certo che sia lui: da rivedere
PC_MISSING = "sparito"        # ✖ il registro ha una sorgente su questo PC, ma il file non c'è più
PC_NONE = ""                  #   non trovato
PC_LOOK = {PC_SAME: ("✔", QColor(30, 140, 60), 4), PC_STALE: ("⟳", QColor(220, 140, 0), 3),
           PC_PROBABLE: ("≈", QColor(130, 130, 130), 2), PC_MISSING: ("✖", QColor(200, 40, 40), 1),
           PC_NONE: ("", None, 0)}
# l'origine di un brano dell'iPhone, secondo il registro della provenienza
ORIGIN_HERE = "questo PC"
ORIGIN_UNKNOWN = "nessuna"
ORIGIN_PHONE = "telefono"
ORIGIN_MISSING = "file non trovato"
ORIGIN_ROLE = Qt.UserRole + 7     # l'origine com'è nel codice (il testo della cella può essere tradotto)
ORIGIN_NO_FILE = "senza file"     # brano "fantasma": il suo file sull'iPhone non c'è
# il filtro "Mostra": (testo, funzione (origine, stato di Sul PC) -> visibile)
SHOW_FILTERS = [
    ("Tutti i brani", lambda origin, pc: True),
    ("Senza sorgente (solo sull'iPhone)", lambda origin, pc: origin == ORIGIN_UNKNOWN),
    ("Con la sorgente su questo PC", lambda origin, pc: origin == ORIGIN_HERE),
    ("Da altri computer", lambda origin, pc: origin not in (ORIGIN_HERE, ORIGIN_UNKNOWN, ORIGIN_PHONE, ORIGIN_MISSING,
                                                            ORIGIN_NO_FILE)),
    ("File del PC non trovato", lambda origin, pc: origin == ORIGIN_MISSING),
    ("Acquistati o scaricati sul telefono", lambda origin, pc: origin == ORIGIN_PHONE),
    ("Senza file sull'iPhone (fantasmi)", lambda origin, pc: origin == ORIGIN_NO_FILE),
    ("Da rivedere: abbinati solo per i tag (≈)", lambda origin, pc: pc == PC_PROBABLE),
    ("Sorgente con tag diversi (⟳)", lambda origin, pc: pc == PC_STALE),
]
PC_TIP = {PC_SAME: "Sul PC c'è la sorgente di questo brano, con gli stessi tag",
          PC_STALE: "Sul PC c'è la sorgente di questo brano, ma con tag diversi",
          PC_PROBABLE: "Da rivedere: sul PC c'è un brano con lo stesso titolo, album e artista, ma non è certo che "
                       "sia la sorgente"}
NOT_ON_PC_TIP = "Non è nella cartella aperta sul PC (confronto per artista, album e titolo)"
MUSIC_APP_REFRESH = ("Se l'app Musica era aperta, chiudila del tutto e riaprila per vedere le modifiche (cerca "
                     "nella tua libreria, non in Apple Music).")
NOT_CONNECTED = "iPhone non connesso"
CONNECT_TEXT = "Connetti iPhone"
DISCONNECT_TEXT = "Disconnetti iPhone"
CONNECTED, CONNECTING, NOT_CONNECTED_STATE = "connesso", "connessione", "non connesso"
SYNC_WARNING = ("Non premere mai \"Sincronizza\" in iTunes o in Dispositivi Apple: con la musica messa da un altro "
                "programma, iTunes la toglierebbe dall'iPhone.")

INFO_TEXT = (
    "<b>Come funziona.</b> Qui vedi la musica dell'app <b>Musica</b> dell'iPhone, con i titoli, gli artisti e gli "
    "album che mostra l'app. La colonna <b>Sul PC</b> la confronta con il PC: ✔ la sorgente, stessi tag; ⟳ la "
    "sorgente, tag diversi; ≈ da rivedere (un brano con gli stessi tag nella cartella aperta, non certo); ✖ la "
    "sorgente non c'è più; vuoto = non trovato. <b>Sorgente</b>: il file da cui viene il brano (questo PC, un altro "
    "computer, nessuna, telefono); <b>Associa sorgenti</b> la ritrova, <b>Mostra</b> filtra.<br>"
    "Tasto destro su uno o più brani: <b>Salva su PC</b>, <b>Mostra nella scheda PC</b>, <b>Rimpiazza con la "
    "versione del PC</b> (per i ⟳), <b>Cambia tag</b>, <b>Associa sorgente</b>, <b>Togli sorgente</b>, "
    "<b>Elimina dall'iPhone</b>. Per mandare brani nuovi: tasto "
    "destro nella scheda PC → <b>Invia all'iPhone</b>. I file del PC non cambiano mai.<br>"
    f"<b>Attenzione:</b> {SYNC_WARNING}"
)


def _format_length(seconds: float) -> str:
    total = int(round(seconds))
    result = f"{total // 60}:{total % 60:02d}" if total > 0 else ""
    return result


def _report_text(report, verb: str) -> str:
    message = report.summary(verb) + "."
    for title, items in (("Saltati", report.skipped), ("Non riusciti", report.errors)):
        if items:
            lines = []
            for name, reason in items[:10]:
                lines.append(f"• {name}: {reason}")
            if len(items) > 10:
                lines.append(f"… e altri {len(items) - 10}")
            message += f"\n\n{title}:\n" + "\n".join(lines)
    return message


def _pc_value(name: str, value):
    """Un valore di Cambia tag come tag del PC: anno in testo, 0 = vuoto."""
    if name == "year":
        result = str(value) if value else ""
    elif name in ("track_number", "disc_number"):
        result = int(value) if value else None
    else:
        result = value
    return result


def _playlist_note(phone_tracks: list) -> str:
    """Il promemoria delle playlist da sistemare a mano dopo un rimpiazzo ("" se non ce ne sono)."""
    reminder = playlist_reminder(phone_tracks)
    result = ""
    if reminder:
        result = ("\n\nI brani rimpiazzati non sono più nelle playlist fatte sull'iPhone: rimettili a mano (app "
                  "Musica, playlist, Modifica, Aggiungi musica):\n" + reminder)
    return result


class PhoneTagDialog(QDialog):
    """Cambia i tag dei brani dell'iPhone. Un campo vuoto non cambia; per più brani, il titolo non si cambia."""

    def __init__(self, parent, phone_tracks: list) -> None:
        super().__init__(parent)
        self.setWindowTitle("Cambia tag sull'iPhone")
        single = phone_tracks[0].tags if len(phone_tracks) == 1 else None
        self.fields = {}
        form = QFormLayout()
        for name, label in (("title", "Titolo"), ("album", "Album"), ("genre", "Genere"), ("year", "Anno"),
                            ("track_number", "N. traccia"), ("disc_number", "N. disco")):
            edit = QLineEdit()
            if single is not None:
                value = getattr(single, name)
                edit.setText("" if value in (None, "") else str(value))
            else:
                edit.setPlaceholderText("(invariato)")
            if name == "title" and single is None:
                edit.setEnabled(False)
                edit.setPlaceholderText("(si cambia un brano alla volta)")
            self.fields[name] = edit
            form.addRow(label + ":", edit)
        self._original = {}
        for name, edit in self.fields.items():
            self._original[name] = edit.text()
        flags = set()
        for item in phone_tracks:
            flags.add(bool(item.tags.compilation))
        self.compilation = QCheckBox("Compilation (album di artisti vari)")
        if len(flags) > 1:
            self.compilation.setTristate(True)
            self.compilation.setCheckState(Qt.PartiallyChecked)
            self.compilation.setToolTip("Valori diversi tra i brani scelti: lasciala così per non cambiarla.")
        else:
            self.compilation.setChecked(True in flags)
        self._original_compilation = self.compilation.checkState()
        form.addRow("", self.compilation)
        note = QLabel(f"{len(phone_tracks)} brani. Artista e artista dell'album non si cambiano qui: sull'iPhone "
                      "rinominerebbero l'artista per tutti i suoi brani. Cambiali nella scheda PC, poi usa "
                      "<i>Rimpiazza con la versione del PC</i>. Anno o numero 0: lo svuota.<br>Una compilation "
                      "vuole anche l'artista dell'album <i>Artisti vari</i>: se nell'app Musica i brani non si "
                      "raccolgono in un solo album, metti la spunta e \"Artisti vari\" nella scheda PC e usa "
                      "<i>Rimpiazza con la versione del PC</i>.")
        note.setWordWrap(True)
        note.setTextFormat(Qt.RichText)
        note.setStyleSheet("color: gray")
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Applica sull'iPhone")
        buttons.accepted.connect(self._check)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addWidget(buttons)
        self.values = {}
        self.resize(480, 300)

    def _check(self) -> None:
        values = {}
        problem = ""
        for name, edit in self.fields.items():
            text = edit.text().strip()
            if edit.isEnabled() and text and text != self._original[name]:
                if name in ("year", "track_number", "disc_number"):
                    if text.isdigit() and int(text) <= 9999:
                        values[name] = int(text)
                    else:
                        problem = f"{name.replace('_', ' ')}: serve un numero"
                else:
                    values[name] = text
        state = self.compilation.checkState()
        if state != self._original_compilation and state != Qt.PartiallyChecked:
            values["compilation"] = state == Qt.Checked
        if problem:
            QMessageBox.warning(self, "Cambia tag", problem)
        elif not values:
            QMessageBox.information(self, "Cambia tag", "Non hai cambiato niente.")
        else:
            self.values = values
            self.accept()


class IPhonePanel(QWidget):
    def __init__(self, window) -> None:
        super().__init__(window)
        self._window = window
        self._connected = False
        self._device_name = "iPhone"
        self._phone_tracks = []
        self._source_queue = []       # brani da associare uno alla volta (Associa sorgente da una cartella)
        self._warned_missing = set()  # sync_id già segnalati come sorgente sparita in questa sessione
        self._by_pid = {}
        self._matches = {}
        self._pc_states = {}          # pid -> (PC_*, Track del PC o None): la colonna Sul PC
        self._pc_dirty = True

        self._status = QLabel(NOT_CONNECTED)
        self._status.setStyleSheet("font-size: 15px; font-weight: bold;")
        self._connect_button = QPushButton(CONNECT_TEXT)
        self._connect_button.setMinimumWidth(170)
        self._connect_button.clicked.connect(self._toggle_connection)
        self._manual_off = False      # disconnesso a mano: niente riconnessione automatica fino al cavo staccato
        top = QHBoxLayout()
        top.addWidget(self._status, 1)
        top.addWidget(self._connect_button)

        info = QLabel(INFO_TEXT)
        info.setWordWrap(True)
        info.setTextFormat(Qt.RichText)
        info.setStyleSheet("background: palette(alternate-base); padding: 8px; border-radius: 4px;")

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(info)
        layout.addWidget(self._build_music_box(), 1)
        self._update_enabled()
        self._auto_tried = False      # già tentato il collegamento automatico per questo iPhone collegato
        self._driver_warned = False
        self._poll = QTimer(self)
        self._poll.setInterval(DEVICE_POLL_MS)
        self._poll.timeout.connect(self._check_device)
        self._poll.start()
        QTimer.singleShot(1500, self._check_device)

    # ------------------------------------------------------------------ elenco dell'app Musica

    def _build_music_box(self) -> QGroupBox:
        self._search = QLineEdit()
        self._search.setPlaceholderText("Cerca per titolo, artista o album…")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._apply_search)
        self._count = QLabel()
        self._show = QComboBox()
        for text, _rule in SHOW_FILTERS:
            self._show.addItem(tr(text))
        self._show.setToolTip("Quali brani mostrare, secondo la loro origine (il registro della provenienza)")
        self._show.currentIndexChanged.connect(lambda _index: self._apply_search())
        search_row = QHBoxLayout()
        search_row.addWidget(self._search, 1)
        search_row.addWidget(QLabel("Mostra:"))
        search_row.addWidget(self._show)
        search_row.addWidget(self._count)

        self._music_view = QTreeWidget()
        self._music_view.setHeaderLabels(COLUMNS)
        self._music_view.setRootIsDecorated(False)
        self._music_view.setAlternatingRowColors(True)
        self._music_view.setUniformRowHeights(True)
        self._music_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._music_view.setSortingEnabled(True)
        self._music_view.sortByColumn(COL_ARTIST, Qt.AscendingOrder)
        self._music_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._music_view.customContextMenuRequested.connect(self._show_menu)
        self._music_view.viewport().installEventFilter(self)    # il suggerimento di Sul PC, al passaggio del mouse
        header = self._music_view.header()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)
        for column, width in COLUMN_WIDTHS.items():
            self._music_view.setColumnWidth(column, width)
        header.setSectionResizeMode(COL_TITLE, QHeaderView.Stretch)

        self._refresh_button = QPushButton("Aggiorna")
        self._refresh_button.setToolTip("Rilegge la musica dell'app Musica dall'iPhone connesso; senza iPhone rifà "
                                        "il confronto con il PC")
        self._refresh_button.clicked.connect(self._refresh_music)
        self._save_button = QPushButton("Salva i selezionati sul PC…")
        self._save_button.clicked.connect(self._save_selected)
        self._adopt_button = QPushButton("Associa sorgenti…")
        self._adopt_button.setToolTip("Ritrova sul PC la sorgente (il file) dei brani dell'iPhone, di quelli "
                                      "selezionati o di tutti quelli senza sorgente: nome della cartella, impronta "
                                      "dell'audio, regole e AI per i dubbi. Scrive solo il registro della "
                                      "provenienza: né i brani né i file cambiano.")
        self._adopt_button.clicked.connect(self._adopt)
        self._listing_note = QLabel()
        self._listing_note.setStyleSheet("color: gray")
        buttons = QHBoxLayout()
        buttons.addWidget(self._refresh_button)
        buttons.addWidget(self._save_button)
        buttons.addWidget(self._adopt_button)
        buttons.addStretch(1)
        buttons.addWidget(self._listing_note)

        box = QGroupBox("Musica nell'app Musica dell'iPhone")
        box_layout = QVBoxLayout(box)
        box_layout.addLayout(search_row)
        box_layout.addWidget(self._music_view, 1)
        box_layout.addLayout(buttons)
        return box

    def set_phone_tracks(self, tracks: list, note: str) -> None:
        """L'elenco da mostrare (letto ora dall'iPhone o salvato l'ultima volta); note dice da dove viene."""
        self._phone_tracks = list(tracks)
        self._by_pid = {}
        for item in self._phone_tracks:
            self._by_pid[item.pid] = item
        self._listing_note.setText(note)
        self._fill_music()

    def _links(self) -> dict:
        result = self._window.registry.links_here()
        return result

    def _origin(self, item) -> str:
        """La parola della colonna Origine (e del filtro Mostra)."""
        link = self._window.registry.get(item.sync_id) if item.sync_id else None
        if item.missing_file:
            result = ORIGIN_NO_FILE
        elif not item.from_computer:
            result = ORIGIN_PHONE
        elif link is None:
            result = ORIGIN_UNKNOWN
        elif not link.here:
            result = link.pc
        elif Path(link.path).is_file():
            result = ORIGIN_HERE
        else:
            result = ORIGIN_MISSING
        return result

    def _compare_with_pc(self) -> None:
        """Rifà i confronti con il PC: gli abbinamenti con la cartella aperta e lo stato della colonna Sul PC."""
        self._matches = pc_matches(self._phone_tracks, self._window.tracks, self._links())
        self._pc_states = {}
        for item in self._phone_tracks:
            self._pc_states[item.pid] = self._pc_state(item)
        self._window.tag_cache.save()     # le sorgenti fuori dalla cartella aperta lette ora
        self._pc_dirty = False

    def _pc_state(self, item) -> tuple:
        """(PC_*, Track del PC o None). La sorgente del registro vale anche fuori dalla cartella aperta: il file si
        legge (solo lettura, con la cache dei tag) e si confronta."""
        match = self._matches.get(item.pid)
        link = self._window.registry.get(item.sync_id) if item.sync_id else None
        if link is not None and link.here and match is not None and match[3]:
            result = (PC_SAME if match[0] == DEVICE_SAME else PC_STALE, match[1])
        elif link is not None and link.here and Path(link.path).is_file():
            track = self._window.source_track(Path(link.path))
            if track is None:
                result = (PC_MISSING, None)
            elif differences(track.tags, item.tags):
                result = (PC_STALE, track)
            else:
                result = (PC_SAME, track)
        elif link is not None and link.here:
            result = (PC_MISSING, None)
        elif match is not None:
            result = (PC_PROBABLE, match[1])
        else:
            result = (PC_NONE, None)
        return result

    def _fill_music(self) -> None:
        self._compare_with_pc()
        view = self._music_view
        view.setSortingEnabled(False)
        view.clear()
        rows = []
        for item in self._phone_tracks:
            tags = item.tags
            number = ""
            if tags.track_number:
                number = str(tags.track_number)
                if (tags.disc_number or 1) > 1:
                    number = f"{tags.disc_number}-{tags.track_number}"
            cells = {
                COL_NUMBER: (number, (tags.disc_number or 1) * 1000 + (tags.track_number or 0)),
                COL_PC: ("", 0),
                COL_ORIGIN: ("", ""),
                COL_TITLE: (tags.title, tags.title.lower()),
                COL_ARTIST: (tags.artist, item.display_artist.lower()),
                COL_ALBUM_ARTIST: (tags.album_artist, tags.album_artist.lower()),
                COL_ALBUM: (tags.album, tags.album.lower()),
                COL_YEAR: (tags.year, tags.year),
                COL_GENRE: (tags.genre, tags.genre.lower()),
                COL_LENGTH: (_format_length(item.length), int(item.length)),
                COL_SOURCE_FILE: ("", ""),
            }
            texts = []
            keys = []
            for column in range(len(COLUMNS)):
                text, key = cells[column]
                texts.append(text)
                keys.append(key)
            row = SortableItem(texts, keys)
            row.setData(COL_TITLE, PID_ROLE, item.pid)
            self._set_origin_cell(row, item)
            self._set_pc_cell(row, item.pid)
            rows.append(row)
        view.addTopLevelItems(rows)
        view.setSortingEnabled(True)
        self._apply_search()

    def _origin_text(self, item) -> str:
        """Da dove viene il brano, secondo il registro della provenienza."""
        link = self._window.registry.get(item.sync_id) if item.sync_id else None
        if not item.from_computer:
            result = "Messo sull'iPhone dal telefono stesso (acquisto o download): non si gestisce da un computer"
        elif link is None:
            result = "Origine sconosciuta: messo sull'iPhone da un altro programma o da un altro computer"
        else:
            where = "questo PC" if link.here else link.pc
            result = f"Da {where} ({link.how}, {link.date}):\n{link.path}"
        if item.missing_file:
            result = ("Brano \"fantasma\": è nell'elenco dell'app Musica, ma il suo file sull'iPhone non c'è, quindi "
                      "non si può ascoltare. Toglilo con Elimina dall'iPhone (tasto destro).\n" + result)
        result += "\n" + item.remote_path
        return result

    def _set_origin_cell(self, row, item) -> None:
        origin = self._origin(item)
        row.setText(COL_ORIGIN, origin)
        row.setData(COL_ORIGIN, ORIGIN_ROLE, origin)     # il filtro Mostra usa questo, non il testo (tradotto)
        row.setData(COL_ORIGIN, SORT_ROLE, origin.lower())
        tip = self._origin_text(item)
        row.setToolTip(COL_ORIGIN, tip)
        row.setToolTip(COL_TITLE, tip)
        source = self._source_text(item)
        row.setText(COL_SOURCE_FILE, source)
        row.setData(COL_SOURCE_FILE, SORT_ROLE, source.lower())
        row.setToolTip(COL_SOURCE_FILE, self._source_path(item))
        if origin in (ORIGIN_MISSING, ORIGIN_NO_FILE):
            row.setForeground(COL_ORIGIN, QBrush(QColor(200, 40, 40)))
        elif origin == ORIGIN_UNKNOWN:
            row.setForeground(COL_ORIGIN, QBrush(QColor(220, 140, 0)))
        else:
            row.setForeground(COL_ORIGIN, QBrush())

    def _source_path(self, item) -> str:
        """Il percorso del file della sorgente, con il computer se non è questo ("" senza sorgente)."""
        link = self._window.registry.get(item.sync_id) if item.sync_id else None
        if link is None:
            result = ""
        elif link.here:
            result = link.path
        else:
            result = f"{link.pc}: {link.path}"
        return result

    def _source_text(self, item) -> str:
        """La colonna File della sorgente: il percorso completo o il solo nome (Impostazioni), con il computer se
        non è questo."""
        link = self._window.registry.get(item.sync_id) if item.sync_id else None
        if link is None:
            result = ""
        else:
            shown = link.path if self._window.app_settings.show_full_path else Path(link.path.replace("\\", "/")).name
            result = shown if link.here else f"{link.pc}: {shown}"
        return result

    def _set_pc_cell(self, row, pid: int) -> None:
        state = self._pc_states.get(pid, (PC_NONE, None))[0]
        text, color, order = PC_LOOK[state]
        row.setText(COL_PC, text)
        row.setData(COL_PC, SORT_ROLE, order)
        row.setData(COL_PC, PC_STATE_ROLE, state)
        row.setForeground(COL_PC, QBrush(color) if color is not None else QBrush())
        if state == PC_NONE:
            row.setToolTip(COL_PC, NOT_ON_PC_TIP)
        row.setTextAlignment(COL_PC, Qt.AlignCenter)

    def eventFilter(self, watched, event) -> bool:
        handled = False
        if watched is self._music_view.viewport():
            handled = show_on_tooltip(event, self._music_view, self._tooltip_at)
        result = handled or super().eventFilter(watched, event)
        return result

    def _tooltip_at(self, position) -> str:
        """Il suggerimento della cella sotto il mouse: la tabella del confronto per Sul PC, il testo della cella per
        le altre colonne."""
        view = self._music_view
        row = view.itemAt(position)
        column = view.columnAt(position.x())
        result = ""
        if row is not None and column == COL_PC:
            result = self.pc_tooltip(row.data(COL_TITLE, PID_ROLE))
        elif row is not None:
            result = row.toolTip(column)
        return result

    def pc_tooltip(self, pid) -> str:
        item = self._by_pid.get(pid)
        state, track = self._pc_states.get(pid, (PC_NONE, None))
        link = self._window.registry.get(item.sync_id) if item is not None and item.sync_id else None
        if item is None or state == PC_NONE:
            result = NOT_ON_PC_TIP
        elif state == PC_MISSING:
            result = (f"La sorgente di questo brano non c'è più sul PC:\n{link.path if link else '?'}\n"
                      "(spostata o cancellata). Il brano resta sull'iPhone: tasto destro → Associa sorgente per "
                      "sceglierne un'altra.")
        else:
            certain = state in (PC_SAME, PC_STALE)
            if certain:
                how = f"Abbinato dal registro della provenienza ({link.how if link else '?'}): certo"
                if not self._in_open_folder(track):
                    how += " (fuori dalla cartella aperta)"
            else:
                how = ("Abbinato per artista, album e titolo: probabile, non certo. Se è giusto, tasto destro → "
                       "Associa le probabili")
            result = comparison_html(PC_TIP[state], str(track.path), how, certain, comparison(track.tags, item.tags))
        return result

    def _in_open_folder(self, track) -> bool:
        root = self._window.root_folder
        result = track is not None and root is not None and track.path.is_relative_to(root)
        return result

    def pc_changed(self) -> None:
        """I brani del PC sono cambiati (cartella aperta, tag modificati): la colonna "Sul PC" va rifatta, subito se
        la scheda si vede, altrimenti quando la si apre."""
        self._pc_dirty = True
        if self.isVisible():
            self._refresh_pc_column()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._pc_dirty:
            self._refresh_pc_column()

    def _refresh_pc_column(self) -> None:
        """Le colonne Sul PC, Sorgente e File della sorgente, dopo un cambio dei brani del PC o del registro."""
        self._compare_with_pc()
        view = self._music_view
        view.setSortingEnabled(False)
        for index in range(view.topLevelItemCount()):
            row = view.topLevelItem(index)
            pid = row.data(COL_TITLE, PID_ROLE)
            item = self._by_pid.get(pid)
            if item is not None:
                self._set_origin_cell(row, item)
            self._set_pc_cell(row, pid)
        view.setSortingEnabled(True)
        self._apply_search()

    def _apply_search(self) -> None:
        words = self._search.text().casefold().split()
        rule = SHOW_FILTERS[max(0, self._show.currentIndex())][1]
        shown = 0
        view = self._music_view
        for index in range(view.topLevelItemCount()):
            row = view.topLevelItem(index)
            text = " ".join([row.text(COL_TITLE), row.text(COL_ARTIST), row.text(COL_ALBUM)]).casefold()
            visible = rule(row.data(COL_ORIGIN, ORIGIN_ROLE), row.data(COL_PC, PC_STATE_ROLE))
            for word in words:
                if word not in text:
                    visible = False
            row.setHidden(not visible)
            if visible:
                shown += 1
        total = view.topLevelItemCount()
        if words or self._show.currentIndex() > 0:
            self._count.setText(f"{shown} di {total} brani")
        else:
            self._count.setText(f"{total} brani")

    def _selected_phone_tracks(self) -> list:
        result = []
        for row in self._music_view.selectedItems():
            item = self._by_pid.get(row.data(COL_TITLE, PID_ROLE))
            if item is not None and not row.isHidden():
                result.append(item)
        return result

    def _stale_pairs(self, items: list) -> list:
        """(brano dell'iPhone, brano del PC) per i brani selezionati con ⟳ (la sorgente, anche fuori dalla cartella
        aperta) o ≈ con tag diversi."""
        result = []
        for item in items:
            state, track = self._pc_states.get(item.pid, (PC_NONE, None))
            match = self._matches.get(item.pid)
            if state == PC_STALE and item.from_computer:
                result.append((item, track))
            elif state == PC_PROBABLE and match[0] == DEVICE_STALE and item.from_computer:
                result.append((item, track))
        return result

    def _probable(self, items: list) -> list:
        """I brani scelti con ≈ (abbinati solo per i tag), da associare a quel file."""
        result = []
        for item in items:
            if self._pc_states.get(item.pid, (PC_NONE, None))[0] == PC_PROBABLE and item.sync_id:
                result.append(item)
        return result

    def _link_probable(self, items: list) -> None:
        """Associa le probabili: il file abbinato per i tag diventa la sorgente (registro)."""
        answer = QMessageBox.question(
            self, "Associa le probabili",
            f"Associare {len(items)} brani dell'iPhone al file del PC con lo stesso titolo, album e artista (≈)?\n\n"
            "Controlla prima che siano giusti (il suggerimento di ≈ li confronta). Scrive solo il registro della "
            "provenienza: né i brani né i file cambiano.")
        if answer == QMessageBox.Yes:
            window = self._window
            registry = window.registry
            for item in items:
                track = self._pc_states[item.pid][1]
                proposal = adoption.Proposal(item, track, provenance.HOW_RULES, "stessi titolo, album e artista")
                registry.record(adoption.link_for(proposal, window.overlay, window.tag_cache.fingerprint(track.path)))
            self._store_registry(registry, f"Sorgente associata a {len(items)} brani")

    def _source_paths(self, items: list) -> list:
        """I file delle sorgenti dei brani scelti (quelli che ne hanno una)."""
        result = []
        for item in items:
            link = self._window.registry.get(item.sync_id) if item.sync_id else None
            if link is not None:
                result.append(link.path)
        return result

    def _show_menu(self, position) -> None:
        items = self._selected_phone_tracks()
        if items:
            ready = self._connected and not self._window.runner.is_busy
            on_pc = []
            for item in items:
                track = self._pc_states.get(item.pid, (PC_NONE, None))[1]
                if track is not None and self._in_open_folder(track):
                    on_pc.append(track)
            probable = self._probable(items)
            writable = []
            for item in items:
                if item.from_computer:
                    writable.append(item)
            stale = self._stale_pairs(items)
            linked_here = []
            for item in items:
                link = self._window.registry.get(item.sync_id) if item.sync_id else None
                if link is not None and link.here:
                    linked_here.append(item)
            if len(writable) == 1:
                source_text = "Associa sorgente…"
            else:
                source_text = f"Associa sorgenti… ({len(writable)} brani)"
            menu = QMenu(self)
            entries = [
                (f"Salva su PC… ({len(items)} brani)", self._save_selected, ready),
                (f"Mostra nella scheda PC ({len(on_pc)} brani)",
                 lambda: self._window.show_tracks({str(track.path) for track in on_pc}), bool(on_pc)),
                None,
                (f"Rimpiazza con la versione del PC ({len(stale)} brani ⟳)", self._replace_selected,
                 ready and bool(stale)),
                (f"Cambia tag… ({len(writable)} brani)", self._edit_selected, ready and bool(writable)),
                None,
                (source_text, lambda: self._link_sources(writable),
                 bool(writable) and not self._window.runner.is_busy),
                (f"Associa le probabili ≈ ({len(probable)} brani)", lambda: self._link_probable(probable),
                 bool(probable) and not self._window.runner.is_busy),
                (f"Togli sorgente ({len(linked_here)} brani)", lambda: self._unlink(linked_here),
                 bool(linked_here) and not self._window.runner.is_busy),
                None,
                (f"Elimina dall'iPhone… ({len(writable)} brani)", self._delete_selected, ready and bool(writable)),
            ]
            for entry in entries:
                if entry is None:
                    menu.addSeparator()
                else:
                    text, slot, enabled = entry
                    action = menu.addAction(text)
                    action.setEnabled(enabled)
                    if not self._connected:
                        action.setToolTip("Connetti l'iPhone")
                    action.triggered.connect(slot)
            menu.addSeparator()
            sources = QMenu("File della sorgente", menu)
            add_file_entries(sources, self._source_paths(items),
                             lambda text: self._window.statusBar().showMessage(text, 8000))
            menu.addMenu(sources).setEnabled(bool(self._source_paths(items)))
            menu.setToolTipsVisible(True)
            menu.exec(self._music_view.viewport().mapToGlobal(position))

    def _refresh_music(self) -> None:
        if not self._connected:
            self.pc_changed()
            self._window.statusBar().showMessage("iPhone non connesso: rifatto il confronto con il PC sull'ultimo "
                                                 "elenco letto", 8000)
        elif not self._window.runner.is_busy:
            def work(progress, _cancel):
                progress(0, 0, "lettura della musica dell'app Musica")
                value = iphone.list_music_app()
                return value

            self._window.runner.run("Lettura dell'iPhone", work, self._music_read)

    def _music_read(self, tracks: list) -> None:
        self._window.set_phone_tracks(tracks, self._device_name)
        self.check_missing_sources()
        self._report_phantoms()

    def _report_phantoms(self) -> None:
        """Dopo la lettura dell'iPhone: quanti brani non hanno il file (si vedono con Mostra)."""
        count = 0
        for item in self._phone_tracks:
            if item.missing_file:
                count += 1
        if count:
            self._window.statusBar().showMessage(
                f"{count} brani dell'iPhone senza file (fantasmi): Mostra → \"Senza file sull'iPhone\", poi tasto "
                "destro → Elimina dall'iPhone", 20000)

    # ------------------------------------------------------------------ sorgenti sparite

    def missing_sources(self) -> list:
        """(PhoneTrack, Link) dei brani la cui sorgente su questo PC non c'è più. Un file su un disco che non c'è
        (unità scollegata) non conta: non è sparito."""
        result = []
        drives = {}
        for item in self._phone_tracks:
            link = self._window.registry.get(item.sync_id) if item.sync_id else None
            if link is not None and link.here:
                path = Path(link.path)
                anchor = path.anchor
                if anchor not in drives:
                    drives[anchor] = bool(anchor) and Path(anchor).exists()
                if drives[anchor] and not path.is_file():
                    result.append((item, link))
        return result

    def check_missing_sources(self) -> None:
        """All'apertura di una cartella e alla lettura dell'iPhone: l'avviso per le sorgenti sparite, una volta sola
        per brano in ogni sessione del programma."""
        if not self._window.runner.is_busy:
            rows = []
            for item, link in self.missing_sources():
                if item.sync_id not in self._warned_missing:
                    rows.append((item, link))
                    self._warned_missing.add(item.sync_id)
            if rows:
                QTimer.singleShot(0, lambda: self._show_missing(rows))

    def _show_missing(self, rows: list) -> None:
        from .missing_dialog import ACTION_DELETE, ACTION_ORPHAN, ACTION_SEARCH, MissingSourcesDialog
        dialog = MissingSourcesDialog(self, rows, self._connected)
        if dialog.exec() and not self._window.runner.is_busy:
            chosen = dialog.chosen()
            if dialog.action == ACTION_SEARCH:
                self._source_queue = chosen[1:]
                self._link_one(chosen[0])
            elif dialog.action == ACTION_ORPHAN:
                registry = self._window.registry
                for item in chosen:
                    registry.forget(item.sync_id)
                self._store_registry(registry, f"{len(chosen)} brani ora sono senza sorgente")
            elif dialog.action == ACTION_DELETE:
                self._delete_items(chosen)

    # ------------------------------------------------------------------ scrittura sull'iPhone

    def _write(self, title: str, verb: str, action, note: str = "", after=None) -> None:
        """Esegue action(progress, cancel) -> ActionReport, poi rilegge la musica dell'iPhone e mostra l'esito (con
        note in fondo, se qualcosa è riuscito). after(report), se c'è, prima del messaggio."""
        def work(progress, cancel):
            report = action(progress, cancel)
            if report.done:
                iphone.post_sync_finished()       # l'app Musica aperta può rileggere la libreria (esperimento)
            progress(0, 0, "rilettura della musica dell'iPhone")
            tracks = iphone.list_music_app()
            registry = provenance.Registry.load(config_dir())
            value = (report, tracks, registry)
            return value

        def done(value):
            report, tracks, registry = value
            self._window.registry = registry        # prima: i confronti dei brani nuovi lo usano
            self._window.set_phone_tracks(tracks, self._device_name)
            if after is not None:
                after(report)
            message = _report_text(report, verb)
            if report.done:
                message += note + "\n\n" + MUSIC_APP_REFRESH
            QMessageBox.information(self, title, message)

        self._window.runner.run(title, work, done)

    def _confirm(self, title: str, text: str) -> bool:
        answer = QMessageBox.question(self, title, text + "\n\n" + SYNC_WARNING)
        result = answer == QMessageBox.Yes
        return result

    def send_tracks(self, tracks: list) -> None:
        """Dalla scheda PC: i brani nell'app Musica dell'iPhone (con le modifiche in sospeso)."""
        formats = {}
        for track in tracks:
            suffix = track.path.suffix.lower()
            formats[suffix] = formats.get(suffix, 0) + 1
        described = ", ".join(f"{count} {suffix[1:].upper()}" for suffix, count in sorted(formats.items()))
        text = (f"Inviare {len(tracks)} brani all'app Musica dell'iPhone ({described})?\n\n"
                "Vanno copie con i tag e la copertina modificati: i file del PC non cambiano.")
        if self._confirm("Invia all'iPhone", text):
            overlay = self._window.overlay

            def action(progress, cancel):
                value = phone_actions.send_tracks(tracks, overlay, progress, cancel, config_dir())
                return value

            self._write("Invio all'iPhone", "inviati", action)

    def replace_pairs(self, pairs: list) -> None:
        """(brano dell'iPhone, brano del PC): la versione del PC prende il posto di quella dell'iPhone."""
        phone_tracks = []
        for phone_track, _track in pairs:
            phone_tracks.append(phone_track)
        text = (f"Rimpiazzare {len(pairs)} brani dell'iPhone con la versione del PC?\n\n"
                "Prima si invia la versione del PC, poi si toglie quella vecchia. I brani rimpiazzati perdono "
                "il conteggio degli ascolti e spariscono dalle playlist fatte sull'iPhone.")
        reminder = playlist_reminder(phone_tracks)
        if reminder:
            text += "\n\nSono nelle playlist (alla fine te le ricordo, per rimetterli a mano):\n" + reminder
        if self._confirm("Rimpiazza", text):
            overlay = self._window.overlay

            def action(progress, cancel):
                value = phone_actions.replace_tracks(pairs, overlay, progress, cancel, config_dir())
                return value

            self._write("Rimpiazzo sull'iPhone", "rimpiazzati", action, _playlist_note(phone_tracks))

    def apply_pending(self, sends: list, removes: list, updates: list) -> None:
        """Le modifiche in attesa della scheda PC (passo 5) tutte insieme: invia (Track), togli (PhoneTrack), aggiorna
        ((PhoneTrack, Track): Cambia tag o Rimpiazza, come per una modifica dei tag)."""
        edits, replacements = phone_actions.plan_updates(updates)
        lines = []
        if sends:
            lines.append(f"• {len(sends)} brani da inviare")
        if removes:
            lines.append(f"• {len(removes)} brani da togliere dall'iPhone (sul PC non cambia niente)")
        if edits:
            lines.append(f"• {len(edits)} brani da aggiornare con Cambia tag (restano ascolti e playlist)")
        if replacements:
            lines.append(f"• {len(replacements)} brani da rimpiazzare (artista, artista dell'album o un campo da "
                         "svuotare: perdono ascolti e playlist)")
        replaced = []
        for phone_track, _track in replacements:
            replaced.append(phone_track)
        text = "Applicare all'iPhone le modifiche in attesa?\n\n" + "\n".join(lines)
        reminder = playlist_reminder(replaced)
        if reminder:
            text += "\n\nI brani da rimpiazzare sono nelle playlist (alla fine te le ricordo):\n" + reminder
        if lines and self._confirm("Applica", text):
            overlay = self._window.overlay

            def action(progress, cancel):
                report = phone_actions.ActionReport()
                if sends:
                    report.add(phone_actions.send_tracks(sends, overlay, progress, cancel, config_dir()))
                if removes and not cancel.is_set():
                    report.add(phone_actions.delete_tracks(removes, progress, config_dir()))
                if (edits or replacements) and not cancel.is_set():
                    report.add(phone_actions.update_from_pc(edits, replacements, overlay, progress, cancel,
                                                            config_dir()))
                return report

            self._write("Applica all'iPhone", "sistemati sull'iPhone", action, _playlist_note(replaced))

    def offer_phone_update(self, tracks: list, cover: bool) -> None:
        """Dopo una modifica dei tag sul PC: i brani dell'iPhone che vengono da questi file (registro della
        provenienza) e ora sono diversi si aggiornano anche lì? I campi sicuri con Cambia tag, artisti e copertina
        con Rimpiazza. Si chiede ogni volta."""
        from ..overlay import path_key
        window = self._window
        links = window.registry.links_here()
        by_sync = {}
        for item in window.phone_tracks:
            if item.sync_id:
                by_sync[item.sync_id] = item
        pairs = []
        covers = set()
        for track in tracks:
            sync_id = links.get(path_key(track.path))
            phone_track = by_sync.get(sync_id) if sync_id else None
            if phone_track is not None:
                pairs.append((phone_track, track))
                if cover:
                    covers.add(str(track.path))
        edits, replacements = phone_actions.plan_updates(pairs, frozenset(covers))
        total = len(edits) + len(replacements)
        if total and not (self._connected and not window.runner.is_busy):
            changed = set()
            for phone_track, _detail in edits + replacements:
                changed.add(id(phone_track))
            stale_tracks = []
            for phone_track, track in pairs:
                if id(phone_track) in changed:
                    stale_tracks.append(track)
            window.mark_for_update(stale_tracks)
            window.statusBar().showMessage(f"{total} brani sull'iPhone vengono da questi file e ora sono diversi: "
                                           "sono in attesa di aggiornamento (⟳ blu), premi Applica quando l'iPhone "
                                           "è connesso", 15000)
        elif total:
            if total == 1 and len(tracks) == 1:
                text = "Il brano modificato è anche sull'iPhone. Aggiornarlo anche lì?\n"
            elif total == len(tracks):
                text = f"I {total} brani modificati sono anche sull'iPhone. Aggiornarli anche lì?\n"
            else:
                text = f"{total} dei {len(tracks)} brani modificati sono anche sull'iPhone. Aggiornarli anche lì?\n"
            if edits:
                text += (f"\n• {len(edits)} con Cambia tag (titolo, album, genere, anno, numeri, compilation): "
                         "restano ascolti e playlist.")
            if replacements:
                text += (f"\n• {len(replacements)} con Rimpiazza (artista, artista dell'album o copertina): perdono "
                         "ascolti e playlist; alla fine ti dico in quali playlist rimetterli.")
            alone = len(tracks) - len(pairs)
            if alone:
                text += f"\n\n{alone} brani non sono sull'iPhone o lì non vengono da questi file: cambiano solo sul PC."
            if self._confirm("Aggiorna anche l'iPhone", text):
                overlay = window.overlay
                replaced = []
                for phone_track, _track in replacements:
                    replaced.append(phone_track)

                def action(progress, cancel):
                    value = phone_actions.update_from_pc(edits, replacements, overlay, progress, cancel, config_dir())
                    return value

                self._write("Aggiornamento dell'iPhone", "aggiornati", action, _playlist_note(replaced))

    def _replace_selected(self) -> None:
        pairs = self._stale_pairs(self._selected_phone_tracks())
        if pairs:
            self.replace_pairs(pairs)

    def _edit_selected(self) -> None:
        items = []
        for item in self._selected_phone_tracks():
            if item.from_computer:
                items.append(item)
        if items:
            dialog = PhoneTagDialog(self, items)
            if dialog.exec():
                values = dialog.values
                linked = self._linked_files(items)
                answer = QMessageBox.No
                if linked:
                    answer = QMessageBox.question(
                        self, "Cambia tag",
                        f"{len(linked)} dei {len(items)} brani vengono da file di questo PC. Salvare le stesse "
                        "modifiche anche per quei file?\n\nSul PC le modifiche restano in sospeso (i file non "
                        "cambiano) e valgono per le copie inviate, esportate o importate.",
                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

                def action(progress, _cancel):
                    value = phone_actions.edit_tracks(items, values, progress)
                    return value

                def after(report):
                    if report.done:
                        self._apply_to_pc(linked, values)

                if answer == QMessageBox.Yes:
                    self._write("Cambia tag sull'iPhone", "modificati", action, after=after)
                elif answer == QMessageBox.No:
                    self._write("Cambia tag sull'iPhone", "modificati", action)

    def _linked_files(self, items: list) -> list:
        """(PhoneTrack, file del PC) per i brani che vengono da un file di questo computer che c'è ancora."""
        result = []
        for item in items:
            link = self._window.registry.get(item.sync_id) if item.sync_id else None
            if link is not None and link.here and Path(link.path).is_file():
                result.append((item, Path(link.path)))
        return result

    def _apply_to_pc(self, linked: list, values: dict) -> None:
        """Le modifiche di Cambia tag anche sui file del PC collegati: in sospeso (overlay), anche se non sono nella
        cartella aperta."""
        from ..library import load_track
        from ..overlay import path_key
        window = self._window
        opened = {}
        for track in window.tracks:
            opened[path_key(track.path)] = track
        pairs = []
        for _item, path in linked:
            track = opened.get(path_key(path))
            if track is None:
                track = load_track(path)
                window.overlay.apply([track])
            if not track.error:
                new_tags = track.tags.copy()
                for name, value in values.items():
                    setattr(new_tags, name, _pc_value(name, value))
                pairs.append((track, new_tags))
        if pairs:
            window.apply_tag_changes(pairs, None, propagate=False)

    def _delete_selected(self) -> None:
        items = []
        for item in self._selected_phone_tracks():
            if item.from_computer:
                items.append(item)
        self._delete_items(items)

    def _delete_items(self, items: list) -> None:
        if items:
            names = []
            for item in items[:8]:
                names.append(f"• {item.display_artist} — {item.tags.title}")
            if len(items) > 8:
                names.append(f"… e altri {len(items) - 8}")
            text = (f"Eliminare {len(items)} brani dall'app Musica dell'iPhone?\n\n" + "\n".join(names) +
                    "\n\nSpariscono dall'iPhone con i loro ascolti. Sul PC non cambia niente. "
                    + phone_actions.DELETE_WAIT_NOTE)
            if self._confirm("Elimina dall'iPhone", text):
                def action(progress, _cancel):
                    value = phone_actions.delete_tracks(items, progress, config_dir())
                    return value

                self._write("Eliminazione dall'iPhone", "eliminati", action)

    # ------------------------------------------------------------------ collega al PC (adozione)

    def _ai_provider(self):
        """Il fornitore AI della scansione, se c'è e se la scansione usa l'AI; altrimenti None."""
        from ..ai import make_provider
        from ..config import load_profiles
        settings = self._window.app_settings
        result = None
        if settings.scan_use_ai:
            for profile in load_profiles():
                if profile.name == settings.scan_profile:
                    result = make_provider(profile)
        return result

    def _adopt(self) -> None:
        """Il pulsante Associa sorgenti: i brani scelti, se ce ne sono, altrimenti tutti quelli senza sorgente."""
        writable = []
        for item in self._selected_phone_tracks():
            if item.from_computer:
                writable.append(item)
        self._open_adopt(writable)

    def _open_adopt(self, selected: list) -> None:
        """Associa sorgenti: dove cercare e come (AdoptOptionsDialog), poi la ricerca in background."""
        from .adoption_dialog import AdoptOptionsDialog
        window = self._window
        known_prints = provenance.PhoneFingerprints(config_dir())
        unknown = []
        for item in self._phone_tracks:
            if item.from_computer and window.registry.get(item.sync_id) is None:
                unknown.append(item)
        to_read = 0
        for item in (selected or unknown):
            if not known_prints.get(item.remote_path, item.size):
                to_read += 1
        provider = self._ai_provider()
        library = window.library_dir()
        dialog = AdoptOptionsDialog(self, len(unknown), len(selected), self._folder_for(selected or unknown), library,
                                    to_read, self._connected, provider.profile.name if provider is not None else "")
        if dialog.exec():
            folder = dialog.folder()
            items = list(selected) if dialog.selected_only else unknown
            if not folder.is_dir():
                QMessageBox.warning(self, "Associa sorgenti", f"La cartella non c'è: {folder}")
            elif not items:
                QMessageBox.information(self, "Associa sorgenti", "Nessun brano da associare.")
            else:
                self._run_adopt(items, folder, dialog.use_fingerprint, provider if dialog.use_ai else None,
                                dialog.selected_only)

    def _run_adopt(self, items: list, folder: Path, use_fingerprint: bool, provider, replace_known: bool) -> None:
        window = self._window
        root = window.root_folder
        opened = None
        if root is not None and folder.is_relative_to(root):
            opened = list(window.tracks)
        registry = window.registry
        tag_cache = window.tag_cache
        read_phone = self._connected

        def work(progress, cancel):
            if opened is None:
                progress(0, 0, f"lettura di {folder}")
                pc_tracks = scan_folder(folder, progress, cancel, tag_cache)
                window.overlay.apply(pc_tracks)
            else:
                pc_tracks = []
                for track in opened:
                    if track.path.is_relative_to(folder):
                        pc_tracks.append(track)
            value = adoption.adopt(items, pc_tracks, registry, config_dir(), tag_cache, provider, progress, cancel,
                                   use_fingerprint, read_phone, replace_known)
            return value

        window.runner.run("Associazione delle sorgenti", work, self._adopted)

    def _adopted(self, outcome) -> None:
        from .adoption_dialog import AdoptionDialog
        window = self._window
        if outcome.cancelled:
            QMessageBox.information(self, "Associa sorgenti", "Interrotto. Le impronte già lette sono ricordate: "
                                    "riprendi quando vuoi con Associa sorgenti.")
        else:
            dialog = AdoptionDialog(self, outcome)
            if dialog.exec():
                chosen = dialog.chosen()
                self._source_queue = list(dialog.missing) if dialog.one_by_one else []
                registry = window.registry
                replaced = 0
                for proposal in chosen:
                    current = registry.get(proposal.phone.sync_id)
                    if current is not None:
                        replaced += 1
                    registry.record(adoption.link_for(proposal, window.overlay,
                                                      window.tag_cache.fingerprint(proposal.pc.path)))
                message = f"Sorgente associata a {len(chosen)} brani"
                if replaced:
                    message += f" ({replaced} sostituite)"
                if chosen:
                    self._store_registry(registry, message, self._next_source)
                else:
                    self._next_source()

    def _store_registry(self, registry, message: str, then=None) -> None:
        """Salva il registro (PC e iPhone, se connesso) e rifà i confronti; poi then(), se c'è."""
        window = self._window
        connected = self._connected

        def work(progress, _cancel):
            progress(0, 0, "registro della provenienza")
            if connected:
                iphone.store_registry(config_dir(), registry)
            else:
                registry.save(config_dir())   # sull'iPhone al prossimo collegamento
            value = message
            return value

        def done(text):
            window.set_registry(registry)
            window.statusBar().showMessage(text, 8000)
            if then is not None:
                then()

        window.runner.run("Registro della provenienza", work, done)

    # ------------------------------------------------------------------ associa sorgente

    def _link_sources(self, items: list) -> None:
        """Un brano: i file possibili, il più probabile per primo. Più brani: Associa sorgenti per quei brani."""
        self._source_queue = []
        if len(items) == 1:
            self._link_one(items[0])
        elif items:
            self._open_adopt(items)

    def _next_source(self) -> None:
        """Il prossimo brano da associare uno alla volta (quelli non trovati nella cartella)."""
        if self._source_queue:
            item = self._source_queue.pop(0)
            self._link_one(item)

    def _link_one(self, item) -> None:
        window = self._window
        pc_tracks = list(window.tracks)
        provider = self._ai_provider()
        read_phone = self._connected
        tag_cache = window.tag_cache

        def work(progress, _cancel):
            progress(0, 0, "ricerca dei file possibili")
            value = adoption.rank_sources(item, pc_tracks, config_dir(), tag_cache, provider, read_phone)
            return value

        window.runner.run("Associa sorgente", work, lambda proposals: self._choose_source(item, proposals))

    def _choose_source(self, item, proposals: list) -> None:
        from .source_dialog import SourceDialog
        window = self._window
        current = window.registry.get(item.sync_id)
        dialog = SourceDialog(self, item, proposals, current, len(self._source_queue))
        if dialog.exec() and dialog.chosen is not None:
            path = dialog.chosen
            accepted = True
            if current is not None and (not current.here or Path(current.path) != path):
                where = "" if current.here else f" (sul computer {current.pc})"
                answer = QMessageBox.question(self, "Associa sorgente",
                                              f"Il brano ha già una sorgente:\n{current.path}{where}\n\n"
                                              f"Sostituirla con:\n{path}?")
                accepted = answer == QMessageBox.Yes
            if accepted:
                registry = window.registry
                registry.record(self._link_to(item, path, dialog.how))
                self._store_registry(registry, f"Sorgente associata: {path}", self._next_source)
            else:
                self._next_source()
        elif dialog.skipped:
            self._next_source()
        else:
            self._source_queue = []

    def _link_to(self, item, path: Path, how: str):
        """La riga del registro: il brano dell'iPhone viene dal file path."""
        window = self._window
        printed = window.tag_cache.fingerprint(path) or provenance.file_fingerprints([str(path)]).get(str(path), "")
        info = path.stat()
        result = provenance.Link(sync_id=item.sync_id, pc=provenance.computer_name(), path=str(path),
                                 size=info.st_size, mtime=info.st_mtime, signature=window.overlay.signature(path),
                                 fingerprint=printed, how=how)
        return result

    def _folder_for(self, items: list) -> Path:
        """La cartella da proporre: quella più usata dalle sorgenti già note dei brani scelti o dei loro album."""
        from ..library import group_name
        window = self._window
        albums = set()
        for item in items:
            albums.add(group_name(item.tags.album))
        counts = {}
        for item in self._phone_tracks:
            link = window.registry.get(item.sync_id) if item.sync_id else None
            if link is not None and link.here and group_name(item.tags.album) in albums:
                folder = str(Path(link.path).parent)
                counts[folder] = counts.get(folder, 0) + 1
        result = window.root_folder or window.library_dir()
        best = 0
        for folder, count in counts.items():
            if count > best:
                best = count
                result = Path(folder)
        return result

    def _unlink(self, items: list) -> None:
        if items:
            answer = QMessageBox.question(
                self, "Togli sorgente",
                f"Togliere la sorgente (il file del PC) di {len(items)} brani dell'iPhone?\n\n"
                "I brani restano sull'iPhone e i file sul PC: diventano brani senza sorgente.")
            if answer == QMessageBox.Yes:
                registry = self._window.registry
                for item in items:
                    registry.forget(item.sync_id)
                self._store_registry(registry, f"Tolta la sorgente di {len(items)} brani")

    # ------------------------------------------------------------------ salva su PC

    def _save_selected(self) -> None:
        items = self._selected_phone_tracks()
        if not items:
            QMessageBox.information(self, "Salva su PC", "Seleziona prima uno o più brani nell'elenco.")
        elif not self._connected:
            QMessageBox.information(self, "Salva su PC", "Connetti l'iPhone per copiarne i brani sul PC.")
        else:
            start = str(self._window.library_dir())
            folder = QFileDialog.getExistingDirectory(
                self, "Dove salvare i brani (in cartelle Artista/Album)", start)
            if folder:
                self._save_to(items, Path(folder))

    def _save_to(self, items: list, target: Path) -> None:
        """Ogni brano si scarica in una cartella temporanea dentro target e poi va in Artista/Album (Anno)/NN -
        Titolo, con i nomi che mostra l'app Musica. Solo file nuovi: un file già presente non si sostituisce mai."""
        registry = self._window.registry
        connected = self._connected

        def work(progress, cancel):
            temp = target / DOWNLOAD_TEMP_FOLDER
            linked = 0
            try:
                transfer, downloaded = iphone.download_music(items, temp, progress, cancel)
                tracks = []
                by_local = {}
                for item, local in downloaded:
                    tracks.append(Track(path=local, tags=item.tags.copy(), length=item.length))
                    by_local[str(local)] = item
                prints = provenance.file_fingerprints(list(by_local))
                copy_report = copy_organized(tracks, target, move=True, progress=progress, cancel=cancel,
                                             overwrite=False)
                # ogni brano salvato (o già presente con lo stesso audio) si collega al suo file
                pairs = copy_report.copied + copy_report.skipped
                placed = provenance.file_fingerprints([str(destination) for _source, destination in pairs])
                for source, destination in pairs:
                    item = by_local.get(str(source))
                    printed = prints.get(str(source), "")
                    if item is not None and item.sync_id and printed and placed.get(str(destination)) == printed:
                        info = Path(destination).stat()
                        registry.record(provenance.Link(sync_id=item.sync_id, pc=provenance.computer_name(),
                                                        path=str(destination), size=info.st_size,
                                                        mtime=info.st_mtime, fingerprint=printed,
                                                        how=provenance.HOW_SAVED))
                        linked += 1
            finally:
                shutil.rmtree(temp, ignore_errors=True)
            if linked and connected:
                iphone.store_registry(config_dir(), registry)
            elif linked:
                registry.save(config_dir())
            value = (transfer, copy_report, target, linked)
            return value

        self._window.runner.run("Salvataggio dall'iPhone", work, self._after_save)

    def _after_save(self, value) -> None:
        transfer, copy_report, target, linked = value
        message = (f"Copiati dall'iPhone: {len(transfer.done)}\n"
                   f"Nella cartella {target}: {copy_report.summary()}\n"
                   f"Associati ai file salvati (sorgente): {linked}")
        self._window.set_registry(self._window.registry)
        if transfer.errors:
            details = []
            for name, error in transfer.errors[:10]:
                details.append(f"{name}: {error}")
            message += "\n\nNon copiati:\n" + "\n".join(details)
        if transfer.cancelled or copy_report.cancelled:
            message += "\n\nOperazione annullata."
        QMessageBox.information(self, "Salva su PC", message)
        if self._window.root_folder == target:
            self._window.load_folder(target)

    # ------------------------------------------------------------------ stato e collegamento

    def _update_enabled(self) -> None:
        self._refresh_button.setEnabled(True)
        self._save_button.setEnabled(self._connected)
        self._adopt_button.setEnabled(True)
        self._show_connection(CONNECTED if self._connected else NOT_CONNECTED_STATE)

    def _show_connection(self, state: str) -> None:
        """Il pulsante dice cosa fa: verde "Connetti iPhone", "Connessione…", rosso "Disconnetti iPhone"; il titolo
        della scheda mostra se l'iPhone è connesso anche dalla scheda PC."""
        button = self._connect_button
        if state == CONNECTED:
            button.setText(DISCONNECT_TEXT)
            set_role(button, "danger")
            button.setEnabled(True)
            button.setToolTip("Chiude la connessione: il programma non si riconnette da solo finché non premi "
                              "Connetti iPhone o stacchi e riattacchi il cavo")
        elif state == CONNECTING:
            button.setText("Connessione…")
            set_role(button, "")
            button.setEnabled(False)
        else:
            button.setText(CONNECT_TEXT)
            set_role(button, "go")
            button.setEnabled(True)
            button.setToolTip("Si connette all'iPhone attaccato con il cavo e ne legge la musica")
        self._window.show_iphone_connected(state == CONNECTED)

    def _toggle_connection(self) -> None:
        if self._connected:
            self.disconnect_device()
        elif not self._window.runner.is_busy:
            self._manual_off = False
            self.connect_device()

    def disconnect_device(self) -> None:
        self._connected = False
        self._manual_off = True
        self._auto_tried = True
        self._status.setText("iPhone disconnesso: premi Connetti iPhone per riconnetterlo")
        self._update_enabled()
        self._window.statusBar().showMessage("iPhone disconnesso", 5000)

    @property
    def connected(self) -> bool:
        result = self._connected
        return result

    def _check_device(self) -> None:
        """Ogni pochi secondi: un iPhone appena attaccato si connette da solo (la prima volta l'iPhone chiede
        "Autorizza"), uno staccato si segna come disconnesso. Dopo Disconnetti niente riconnessione automatica finché
        il cavo non viene staccato. Senza driver Apple lo dice una volta."""
        present = iphone.device_present()
        if present is None:
            if not self._driver_warned:
                self._driver_warned = True
                self._status.setText("Driver Apple mancante: installa l'app gratuita \"Dispositivi Apple\" dal "
                                     "Microsoft Store (oppure iTunes)")
        elif not present:
            self._auto_tried = False
            self._manual_off = False      # cavo staccato: al prossimo attacco ci si riconnette da soli
            if self._connected:
                self._connected = False
                self._status.setText("iPhone disconnesso (cavo staccato)")
                self._update_enabled()
                self._window.statusBar().showMessage("iPhone disconnesso", 5000)
            elif self._driver_warned or self._status.text() in (NOT_CONNECTED, tr(NOT_CONNECTED), ""):
                self._driver_warned = False
                self._status.setText("Attacca l'iPhone con il cavo USB e sbloccalo")
        elif (not self._connected and not self._auto_tried and not self._manual_off
              and not self._window.runner.is_busy):
            self._auto_tried = True
            self._status.setText("iPhone rilevato: connessione… se l'iPhone lo chiede, tocca \"Autorizza\" e "
                                 "inserisci il codice")
            self._window.statusBar().showMessage("iPhone rilevato: connessione in corso", 5000)
            self.connect_device(auto=True)

    def _show_error(self, message: str) -> None:
        self._connected = False
        self._status.setText(NOT_CONNECTED)
        self._update_enabled()
        QMessageBox.warning(self, "iPhone", message)

    def _show_auto_error(self, message: str) -> None:
        """La connessione automatica non riuscita non apre finestre: lo dice qui; "Connetti iPhone" riprova."""
        self._connected = False
        self._status.setText(message.replace("\n\n", " "))
        self._update_enabled()

    def connect_device(self, auto: bool = False) -> None:
        def work(progress, _cancel):
            progress(0, 0, "se l'iPhone lo chiede, tocca Autorizza e inserisci il codice")
            info = iphone.get_device_info()
            progress(0, 0, "lettura della musica dell'app Musica")
            tracks = iphone.list_music_app()
            progress(0, 0, "registro della provenienza")
            sync_ids = set()
            for track in tracks:
                if track.sync_id:
                    sync_ids.add(track.sync_id)
            registry = iphone.sync_registry(config_dir(), sync_ids)
            value = (info, tracks, registry)
            return value

        if auto:
            on_error = self._show_auto_error
        else:
            on_error = self._show_error
        if self._window.runner.run("Connessione all'iPhone", work, self._connected_ok, on_error):
            self._show_connection(CONNECTING)

    def _connected_ok(self, value) -> None:
        info, tracks, registry = value
        self._window.registry = registry
        self._connected = True
        self._device_name = info.name
        self._status.setText("Connesso: " + info.label())
        self._window.statusBar().showMessage("iPhone connesso: " + info.label(), 8000)
        self._update_enabled()
        self._window.set_phone_tracks(tracks, info.name)
        self.check_missing_sources()
        self._report_phantoms()
