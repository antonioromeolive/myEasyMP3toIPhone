"""Scheda iPhone: connessione, la musica dell'app Musica (com'è nell'app, confrontata con il PC) e le azioni sui
brani: verso l'iPhone (Ricopia, Usa i tag da PC a iPhone, Cambia i tag, Elimina) vanno in attesa fino ad Applica;
verso il PC (Copia da iPhone a PC, Usa i tag da iPhone a PC) e le associazioni sono subito, con la loro conferma.
La scrittura sull'iPhone passa per phone_actions (il servizio di sincronizzazione di Apple)."""

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QScrollArea, QSplitter, QToolButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .. import adoption, estimate, iphone, phone_actions, phone_duplicates, phone_ringtones, provenance
from ..config import config_dir
from ..i18n import tr
from ..library import Track, album_folder, album_groups, copy_organized, group_name, scan_folder, short_folder
from ..pending import DELETE, EDIT, REMOVE, REPLACE, RING_ACTIONS, RING_DELETE, RING_SEND, SEND, UPDATE
from ..phone_library import (
    DEVICE_ABSENT, DEVICE_SAME, comparison, differences, format_duplicates, pc_matches, playlist_reminder,
    spelling_differences,
)
from .apply_dialog import songs
from .icons import icon
from .widgets import ICON_COLOR, ActionBar, ChipBar
from .compare_tip import comparison_html, show_on_tooltip
from .file_actions import add_file_entries
from .phone_tag_panel import PhoneTagPanel
from .tag_editor import ALBUM_COVER_TRIES as COVER_TRIES
from .theme import album_band, album_bands, set_role
from .browser import SORT_ROLE, LibraryBrowser, SortableItem

DEVICE_POLL_MS = 3000   # ogni quanto si guarda se è stato collegato (o scollegato) un iPhone
DOWNLOAD_TEMP_FOLDER = ".salvataggio_iphone"
PID_ROLE = Qt.UserRole
COLUMNS = ["N.", "Sul PC", "Sorgente", "Titolo", "Artista", "Artista album", "Album", "Anno", "Genere", "Durata",
           "Cartella della sorgente", "File della sorgente"]
(COL_NUMBER, COL_PC, COL_ORIGIN, COL_TITLE, COL_ARTIST, COL_ALBUM_ARTIST, COL_ALBUM, COL_YEAR, COL_GENRE,
 COL_LENGTH, COL_SOURCE_FOLDER, COL_SOURCE_FILE) = range(len(COLUMNS))
COLUMN_WIDTHS = {COL_NUMBER: 50, COL_PC: 60, COL_ORIGIN: 110, COL_TITLE: 260, COL_ARTIST: 180, COL_ALBUM_ARTIST: 150,
                 COL_ALBUM: 220, COL_YEAR: 55, COL_GENRE: 100, COL_LENGTH: 60, COL_SOURCE_FOLDER: 240,
                 COL_SOURCE_FILE: 240}
PC_STATE_ROLE = Qt.UserRole + 8   # lo stato della colonna Sul PC (PC_*), per il filtro Mostra
PROPOSED_ROLE = Qt.UserRole + 9   # la colonna File della sorgente mostra una sorgente proposta (in rosso)
PROPOSED_COLOR = QColor(200, 40, 40)
DIFFERENT_COLOR = QColor(230, 180, 0)   # la sorgente è certa ma i tag sono diversi (⟳): resta associata
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
@dataclass(frozen=True)
class RowFacts:
    """Quello che i filtri a pulsanti sanno di una riga."""
    origin: str            # ORIGIN_*
    pc: str                # PC_*, la colonna Sul PC
    proposed: bool         # una sorgente proposta (in rosso)
    coverless: bool        # album senza immagine sull'iPhone
    misfiled: bool         # nell'album sbagliato sull'iPhone
    duplicate: bool        # doppione: la stessa canzone nello stesso album
    other_albums: bool     # la stessa canzone anche in altri album (legittimo)


DUPLICATES_TEXT = "Doppioni: stessa canzone nello stesso album"
OTHER_ALBUMS_TEXT = "Stessa canzone in più album (raccolte)"
# il filtro "Mostra": (testo, funzione (RowFacts) -> visibile)
SHOW_FILTERS = [
    ("Tutti i brani", lambda row: True),
    ("Senza sorgente (solo sull'iPhone)", lambda row: row.origin == ORIGIN_UNKNOWN),
    ("Con la sorgente su questo PC", lambda row: row.origin == ORIGIN_HERE),
    ("Da altri computer", lambda row: row.origin not in (ORIGIN_HERE, ORIGIN_UNKNOWN, ORIGIN_PHONE, ORIGIN_MISSING,
                                                         ORIGIN_NO_FILE)),
    ("File del PC non trovato", lambda row: row.origin == ORIGIN_MISSING),
    ("Acquistati o scaricati sul telefono", lambda row: row.origin == ORIGIN_PHONE),
    ("Senza file sull'iPhone (fantasmi)", lambda row: row.origin == ORIGIN_NO_FILE),
    ("Da rivedere: abbinati solo per i tag (≈)", lambda row: row.pc == PC_PROBABLE),
    ("Sorgente con tag diversi (⟳)", lambda row: row.pc == PC_STALE),
    ("Con una sorgente proposta (in rosso)", lambda row: bool(row.proposed)),
    ("Album senza immagine sull'iPhone", lambda row: row.coverless),
    ("Nell'album sbagliato sull'iPhone", lambda row: row.misfiled),
    (DUPLICATES_TEXT, lambda row: row.duplicate),
    (OTHER_ALBUMS_TEXT, lambda row: row.other_albums),
]
_FILTER_TEXTS = [text for text, _rule in SHOW_FILTERS]
COVERLESS_FILTER = _FILTER_TEXTS.index("Album senza immagine sull'iPhone")   # la barra mostra Ricopia le copertine
MISFILED_FILTER = _FILTER_TEXTS.index("Nell'album sbagliato sull'iPhone")    # e Rimetti nell'album giusto
DUPLICATES_FILTER = _FILTER_TEXTS.index(DUPLICATES_TEXT)                     # e Togli le copie in più
DROP_COLOR = QColor(150, 150, 150)     # con il filtro dei doppioni: le copie da togliere, barrate e grigie
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

RECHECK_SECONDS = 5           # dopo Applica: se l'iPhone non mostra ancora le modifiche, si rilegge dopo…
RECHECK_TRIES = 3             # …al più tante volte
PENDING_COLOR = QColor(40, 110, 230)       # il titolo di un brano con un'azione in attesa (in corsivo)
PENDING_NAMES = {SEND: "Copia da PC a iPhone", REMOVE: "Elimina dall'iPhone", DELETE: "Elimina dall'iPhone",
                 UPDATE: "Usa i tag da PC a iPhone", REPLACE: "Ricopia da PC a iPhone",
                 EDIT: "Cambia i tag sull'iPhone"}


def adopt_folders(folders: list) -> tuple:
    """Dove cerca Associa sorgenti: (cartelle che ci sono, senza quelle dentro un'altra; [cartelle che non ci sono]).
    Un percorso vuoto (campo non scritto) non vale: Path("") sarebbe la cartella corrente del programma."""
    from .main_window import outermost_folders
    existing = []
    missing = []
    for folder in folders:
        text = str(folder).strip()
        if text in ("", "."):
            pass
        elif Path(text).is_dir():
            existing.append(Path(text))
        else:
            missing.append(text)
    result = (outermost_folders(existing), missing)
    return result


def _pc_value(name: str, value):
    """Un valore di Cambia i tag (scheda iPhone) come lo vuole un TrackTags del PC: anno come testo, numeri interi
    (0 = vuoto), compilation booleana."""
    if name == "year":
        result = str(value) if value else ""
    elif name in ("track_number", "disc_number"):
        result = int(value) if value else None
    elif name == "compilation":
        result = bool(value)
    else:
        result = str(value)
    return result


# le voci del tasto destro sui brani dell'iPhone, in ordine (None: separatore)
PHONE_MENU_ORDER = ("save", "show_pc", None, "replace", "tags", "tags_to_pc", "edit", "complete", "cover", None, "link",
                    "probable", "proposed", "unlink", None, "keep", "dedupe", "delete", "note")
# i pulsanti della barra delle azioni senza brani scelti
BAR_LABELS = {"save": "Copia da iPhone a PC…", "replace": "Ricopia da PC a iPhone", "tags": "Usa i tag da PC a iPhone",
              "edit": "Cambia i tag…", "link": "Associa al file sul PC…", "delete": "Elimina dall'iPhone"}

INFO_TEXT = (
    "<b>Come funziona.</b> Qui vedi la musica dell'app <b>Musica</b> dell'iPhone, con i titoli, gli artisti e gli "
    "album che mostra l'app. La colonna <b>Sul PC</b> la confronta con il PC: ✔ la sorgente, stessi tag; ⟳ la "
    "sorgente, tag diversi; ≈ da rivedere (un brano con gli stessi tag nella cartella aperta, non certo); ✖ la "
    "sorgente non c'è più; vuoto = non trovato. <b>Sorgente</b>: il file da cui viene il brano (questo PC, un altro "
    "computer, nessuna, telefono); <b>Associa sorgenti</b> la ritrova, <b>Mostra</b> filtra.<br>"
    "Tasto destro su uno o più brani: <b>Copia da iPhone a PC</b>, <b>Ricopia da PC a iPhone</b> e <b>Usa i tag da "
    "PC a iPhone</b> (per i ⟳), <b>Usa i tag da iPhone a PC</b>, <b>Cambia i tag</b>, <b>Associa al file sul "
    "PC</b>, <b>Elimina dall'iPhone</b>. Quello che cambia l'iPhone va in attesa (la barra blu in alto) e parte con "
    "<b>Applica</b>. Per copiare brani nuovi: scheda PC → <b>Copia da PC a iPhone</b>. PC e iPhone non si allineano "
    "da soli (i file del PC cambiano solo dopo la tua conferma).<br>"
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


def done_jobs(jobs: list, report) -> list:
    """Le azioni di Applica riuscite davvero, dall'esito (brani del PC copiati, brani dell'iPhone eliminati o
    cambiati): Copia e Ricopia per il brano del PC, Elimina e Cambia i tag per il brano dell'iPhone, Usa i tag per
    l'uno o l'altro (dove basta si cambiano i tag, altrimenti si ricopia)."""
    sent = set()
    for track in report.sent_tracks:
        sent.add(id(track))
    changed = set(report.done_sync_ids)
    result = []
    keys = set(report.done_keys)
    for job in jobs:
        by_track = job.track is not None and id(job.track) in sent
        by_phone = job.phone is not None and getattr(job.phone, "sync_id", 0) in changed
        if job.action in RING_ACTIONS:
            done = job.key in keys
        elif job.action in (SEND, REPLACE):
            done = by_track
        elif job.action == UPDATE:
            done = by_track or by_phone
        else:
            done = by_phone
        if done:
            result.append(job)
    return result


# il resoconto di Applica: cosa è stato fatto, per specie di azione
DONE_TEXT = ((SEND, "brano copiato da PC a iPhone", "brani copiati da PC a iPhone"),
             (REPLACE, "brano ricopiato da PC a iPhone", "brani ricopiati da PC a iPhone"),
             (UPDATE, "brano con i tag presi dal PC", "brani con i tag presi dal PC"),
             (EDIT, "brano con i tag cambiati sull'iPhone", "brani con i tag cambiati sull'iPhone"),
             (DELETE, "brano eliminato dall'iPhone", "brani eliminati dall'iPhone"),
             (RING_SEND, "suoneria inviata da PC a iPhone", "suonerie inviate da PC a iPhone"),
             (RING_DELETE, "suoneria eliminata dall'iPhone", "suonerie eliminate dall'iPhone"))


def apply_report_text(report, done: list, total: int) -> str:
    """Il messaggio alla fine di Applica: le azioni fatte, per specie ("• 12 brani copiati da PC a iPhone"), poi quelle
    non riuscite (restano in attesa) con il motivo."""
    lines = []
    for action, one, many in DONE_TEXT:
        count = 0
        for job in done:
            if job.action == action:
                count += 1
        if count == 1:
            lines.append(f"• 1 {tr(one)}")
        elif count:
            lines.append(f"• {count} {tr(many)}")
    restored = report.playlists_restored
    if restored:
        shown = ", ".join(restored[:6]) + (f" e altre {len(restored) - 6}" if len(restored) > 6 else "")
        lines.append(tr(f"• {len(restored)} playlist rifatte con i brani ricopiati: {shown}"))
    if lines:
        message = tr("Fatto sull'iPhone:") + "\n" + "\n".join(lines)
    else:
        message = tr("Sull'iPhone non è cambiato niente.")
    left = total - len(done)
    if left == 1:
        message += "\n\n" + tr("1 azione non è riuscita: resta in attesa (barra blu, Applica) per riprovarla.")
    elif left:
        message += "\n\n" + tr(f"{left} azioni non sono riuscite: restano in attesa (barra blu, Applica) per "
                                 "riprovarle.")
    for title, items in (("Motivi", report.errors), ("Saltati", report.skipped)):
        if items:
            reasons = []
            for name, reason in items[:10]:
                reasons.append(f"• {name}: {reason}")
            if len(items) > 10:
                reasons.append(f"… e altri {len(items) - 10}")
            message += f"\n\n{tr(title)}:\n" + "\n".join(reasons)
    if report.cancelled:
        message += "\n\n" + tr("Operazione interrotta: le azioni non fatte restano in attesa.")
    return message


def _playlist_report_text(report, phone_playlists: list) -> str:
    """L'esito di Playlist per artista; controlla sulla musica riletta che le playlist create ci siano davvero."""
    present = set()
    for playlist in phone_playlists:
        if playlist.from_computer:
            present.add(playlist.name)
    missing = []
    for name in report.created:
        if name not in present:
            missing.append(name)
    message = f"{len(report.created)} playlist create, {len(report.deleted)} cancellate."
    if missing and len(missing) == len(report.created):
        message += ("\n\nMa sull'iPhone le playlist create non ci sono. Se è attiva Sincronizza libreria (iCloud: "
                    "Impostazioni, Musica), l'iPhone accetta le playlist da un computer senza crearle.")
    elif missing:
        message += f"\n\nNon risultano sull'iPhone: {', '.join(missing[:10])}"
    for title, items in (("Saltate", report.skipped), ("Non riuscite", report.errors)):
        if items:
            lines = []
            for name, reason in items[:10]:
                lines.append(f"• {name}: {reason}")
            if len(items) > 10:
                lines.append(f"… e altri {len(items) - 10}")
            message += f"\n\n{title}:\n" + "\n".join(lines)
    if report.cancelled:
        message += "\n\nOperazione annullata."
    if report.created or report.deleted:
        message += "\n\n" + MUSIC_APP_REFRESH
    return message


def _playlist_note(phone_tracks: list) -> str:
    """Il promemoria delle playlist fatte sul telefono da sistemare a mano dopo un rimpiazzo ("" se non ce ne sono):
    quelle messe da un computer si rifanno da sole (phone_actions._restore_playlists) e le dice l'esito."""
    reminder = playlist_reminder(phone_tracks)
    result = ""
    if reminder:
        result = ("\n\nI brani ricopiati non sono più nelle playlist fatte sul telefono, che il computer non può "
                  "cambiare: rimettili a mano (app Musica, playlist, Modifica, Aggiungi musica). Quelle messe da un "
                  "computer (anche le ♪ di Playlist per artista) si rifanno da sole:\n" + reminder)
    return result


class AlignToPcDialog(QDialog):
    """Usa i tag da iPhone a PC: l'elenco dei file che verranno modificati, con ogni campo (ora → diventa). Una
    casella per campo, con quanti file cambia: si scrivono solo i campi scelti (chosen_plan), così una correzione fatta
    sul PC in un altro campo non torna indietro. Si scrive solo con Modifica i file."""

    def __init__(self, parent, plan: list) -> None:
        super().__init__(parent)
        from ..phone_library import COMPARED_FIELDS
        self.setWindowTitle("Usa i tag da iPhone a PC: modifica dei file del PC")
        self.resize(1000, 520)
        self._plan = plan
        self._labels = {}
        for name, label in COMPARED_FIELDS:
            self._labels[name] = label
        counts = {}
        for _track, _new_tags, fields in plan:
            for name in fields:
                counts[name] = counts.get(name, 0) + 1
        self._header = QLabel()
        self._header.setWordWrap(True)
        self._boxes = {}
        choices = QHBoxLayout()
        choices.addWidget(QLabel("Campi da scrivere:"))
        for name, _label in COMPARED_FIELDS:
            if name in counts:
                box = QCheckBox(f"{tr(self._labels[name])} ({counts[name]} file)")
                box.setChecked(True)
                box.toggled.connect(lambda _checked: self._refresh())
                self._boxes[name] = box
                choices.addWidget(box)
        choices.addStretch(1)
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["File", "Campo", "Ora sul PC", "Diventa"])
        self._tree.setRootIsDecorated(False)
        self._tree.setAlternatingRowColors(True)
        for column, width in enumerate((420, 110, 200)):
            self._tree.setColumnWidth(column, width)
        self._buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._buttons.button(QDialogButtonBox.Ok).setProperty("role", "danger")
        self._buttons.button(QDialogButtonBox.Cancel).setText("Annulla")
        self._buttons.button(QDialogButtonBox.Cancel).setDefault(True)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self._header)
        layout.addLayout(choices)
        layout.addWidget(self._tree, 1)
        layout.addWidget(self._buttons)
        self._refresh()

    def chosen_plan(self) -> list:
        """Il piano con i soli campi scelti: (brano, tag nuovi, campi); i file senza campi scelti non ci sono."""
        result = []
        for track, new_tags, fields in self._plan:
            kept = []
            for name in fields:
                if self._boxes[name].isChecked():
                    kept.append(name)
            if kept:
                tags = track.tags.copy()
                for name in kept:
                    setattr(tags, name, getattr(new_tags, name))
                result.append((track, tags, kept))
        return result

    def _refresh(self) -> None:
        from ..phone_library import _shown
        plan = self.chosen_plan()
        self._header.setText(f"<b>Questi {len(plan)} file del PC verranno modificati</b>: si scrivono nel file i tag "
                             "dell'iPhone dei campi scelti. Non si può annullare.")
        self._tree.clear()
        rows = []
        for track, new_tags, fields in plan:
            first = True
            for name in fields:
                row = QTreeWidgetItem([str(track.path) if first else "", tr(self._labels.get(name, name)),
                                       _shown(name, getattr(track.tags, name)), _shown(name, getattr(new_tags, name))])
                row.setToolTip(0, str(track.path))
                rows.append(row)
                first = False
        self._tree.addTopLevelItems(rows)
        accept = self._buttons.button(QDialogButtonBox.Ok)
        accept.setText(f"Modifica {len(plan)} file")
        accept.setEnabled(bool(plan))


def show_entries_menu(parent, entries: list, where, connected: bool) -> None:
    """Un menu da [(testo, attiva, funzione)] (funzione None: una nota grigia), aperto nel punto where dello schermo."""
    menu = QMenu(parent)
    for text, enabled, slot in entries:
        action = menu.addAction(text)
        action.setEnabled(enabled)
        if slot is not None:
            action.triggered.connect(slot)
            if not connected:
                action.setToolTip("Connetti l'iPhone")
    menu.setToolTipsVisible(True)
    menu.exec(where)


class BandedTree(QTreeWidget):
    """L'elenco dei brani dell'iPhone: lo sfondo di ogni riga è la tinta del suo album (bands: pid -> QColor, rifatto
    dopo ogni ordinamento e filtro), sotto la selezione e il testo; le celle non cambiano."""

    def __init__(self) -> None:
        super().__init__()
        self.bands = {}

    def drawRow(self, painter, option, index) -> None:
        item = self.itemFromIndex(index)
        color = self.bands.get(item.data(COL_TITLE, PID_ROLE)) if item is not None else None
        if color is not None:
            painter.fillRect(QRect(0, option.rect.y(), self.viewport().width(), option.rect.height()), color)
        super().drawRow(painter, option, index)


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
        self._album_of = {}           # pid -> (artista, album) degli elenchi Artisti e Album
        self._matches = {}
        self._pc_states = {}          # pid -> (PC_*, Track del PC o None): la colonna Sul PC
        self._spelling = {}           # pid -> ["album", "album_artist"]: scritti diversamente dal PC (sorgente certa)
        self._proposed = {}           # pid -> adoption.Proposal: la sorgente proposta, in rosso
        self._cover_known = {}        # sync_id dell'album -> i suoi file del PC hanno la copertina (cover_plan)
        self._duplicates = phone_duplicates.Duplicates()   # doppioni e stessa canzone in più album (_compare_with_pc)
        self._marked = set()          # pid delle righe segnate come doppioni (barrate o in grassetto)
        self._tag_shown = None        # cosa mostra il riquadro dei tag: si rifà solo quando cambia
        self._pc_dirty = True

        self._manual_off = False      # disconnesso a mano: niente riconnessione automatica fino al cavo staccato
        layout = QVBoxLayout(self)
        layout.addWidget(self._build_device_card())
        layout.addWidget(self._build_music_box(), 1)
        self._update_tag_panel()
        self._update_enabled()
        self._auto_tried = False      # già tentato il collegamento automatico per questo iPhone collegato
        self._driver_warned = False
        self._poll = QTimer(self)
        self._poll.setInterval(DEVICE_POLL_MS)
        self._poll.timeout.connect(self._check_device)
        self._poll.start()
        QTimer.singleShot(1500, self._check_device)

    def _build_device_card(self) -> QFrame:
        """Il riquadro dell'iPhone, in cima: nome e stato, quanti brani e di quando è l'elenco, Rileggi,
        Connetti/Disconnetti, ? (come funziona) e l'avviso di non sincronizzare con iTunes."""
        card = QFrame()
        card.setObjectName("deviceCard")
        phone_icon = QLabel()
        phone_icon.setPixmap(icon("phone", ICON_COLOR).pixmap(36, 36))
        self._status = QLabel(NOT_CONNECTED)
        self._status.setObjectName("deviceName")
        self._listing_note = QLabel()
        self._listing_note.setObjectName("deviceInfo")
        self._listing_note.setWordWrap(True)
        texts = QVBoxLayout()
        texts.setSpacing(2)
        texts.addWidget(self._status)
        texts.addWidget(self._listing_note)
        self._refresh_button = QPushButton("Rileggi")
        self._refresh_button.setToolTip("F5. Rilegge la musica dell'app Musica dall'iPhone connesso; senza iPhone rifà "
                                        "il confronto con il PC")
        self._refresh_button.clicked.connect(self._refresh_music)
        self._refresh_button.setIcon(icon("refresh", ICON_COLOR))
        self._connect_button = QPushButton(CONNECT_TEXT)
        self._connect_button.setIcon(icon("phone", "white"))
        self._connect_button.setMinimumWidth(170)
        self._connect_button.clicked.connect(self._toggle_connection)
        self._help_button = QToolButton()
        self._help_button.setText("?")
        self._help_button.setIcon(icon("help", ICON_COLOR))
        self._help_button.setCheckable(True)
        self._help_button.setToolTip("Come funziona: i segni delle colonne e dove sono le azioni")
        self._info = QLabel(INFO_TEXT)
        self._info.setWordWrap(True)
        self._info.setTextFormat(Qt.RichText)
        self._info.setObjectName("helpText")
        self._info.setVisible(False)
        self._help_button.toggled.connect(self._info.setVisible)
        warning = QLabel(f"⚠ {SYNC_WARNING}")
        warning.setObjectName("warningLine")
        warning.setWordWrap(True)
        top = QHBoxLayout()
        top.addWidget(phone_icon)
        top.addLayout(texts, 1)
        top.addWidget(self._refresh_button)
        top.addWidget(self._connect_button)
        top.addWidget(self._help_button)
        layout = QVBoxLayout(card)
        layout.addLayout(top)
        layout.addWidget(warning)
        layout.addWidget(self._info)
        return card

    # ------------------------------------------------------------------ elenco dell'app Musica

    def _build_music_box(self) -> QWidget:
        self._search = QLineEdit()
        self._search.setPlaceholderText("Cerca per titolo, artista o album…")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._apply_search)
        self._count = QLabel()
        # i filtri a pulsanti (prima il menu "Mostra"), con quanti brani ha ognuno
        self._show = ChipBar([text for text, _rule in SHOW_FILTERS])
        self._show.currentIndexChanged.connect(lambda _index: self._apply_search())
        search_row = QHBoxLayout()
        search_row.addWidget(self._search, 1)
        search_row.addWidget(self._count)

        self._music_view = BandedTree()
        self._music_view.setHeaderLabels(COLUMNS)
        self._music_view.setRootIsDecorated(False)
        self._music_view.setAlternatingRowColors(False)    # le righe hanno la tinta del loro album
        self._music_view.setUniformRowHeights(True)
        self._music_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._music_view.setSortingEnabled(True)
        self._music_view.sortByColumn(COL_ARTIST, Qt.AscendingOrder)
        self._music_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._music_view.customContextMenuRequested.connect(self._show_menu)
        self._music_view.viewport().installEventFilter(self)    # il suggerimento di Sul PC, al passaggio del mouse
        self._music_view.itemSelectionChanged.connect(self._update_action_bar)
        self._music_view.itemSelectionChanged.connect(self._update_tag_panel)
        edit_shortcut = QShortcut(QKeySequence("E"), self._music_view, context=Qt.WidgetShortcut)
        edit_shortcut.activated.connect(self._edit_current)       # E: Cambia i tag sul brano su cui si è
        delete_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self._music_view, context=Qt.WidgetShortcut)
        delete_shortcut.activated.connect(self._delete_current)   # Canc: Elimina dall'iPhone, in attesa
        header = self._music_view.header()
        # dopo l'ordinamento (che la vista fa su questo stesso segnale) le tinte degli album si rifanno
        header.sortIndicatorChanged.connect(lambda _column, _order: QTimer.singleShot(0, self._update_bands))
        header.setSectionResizeMode(QHeaderView.Interactive)   # tutte trascinabili, nei due versi
        header.setStretchLastSection(True)
        header.setMinimumSectionSize(30)
        for column, width in COLUMN_WIDTHS.items():
            self._music_view.setColumnWidth(column, width)

        # la barra delle azioni sopra i brani: le stesse voci del tasto destro, per i brani scelti; Strumenti per le
        # azioni su tutti i brani (Associa, Playlist…)
        self._actions = ActionBar([("save", ""), ("replace", ""), ("tags", ""), ("edit", ""), ("link", ""),
                                   ("cover", ""), ("refile", ""), ("dedupe", "danger"), ("keep", "danger"),
                                   ("delete", "danger")])
        self._tools = QMenu(self)
        self._tools.aboutToShow.connect(self._fill_tools)
        self._actions.set_menu(self._tools)

        self._browser = LibraryBrowser()       # Artisti e Album, come nella scheda PC (senza spunte)
        self._browser.filter_changed.connect(self._apply_search)
        self._browser.menu_requested.connect(self._browser_menu)
        tracks_box = QWidget()
        tracks_layout = QVBoxLayout(tracks_box)
        tracks_layout.setContentsMargins(0, 0, 0, 0)
        tracks_layout.setSpacing(4)
        tracks_layout.addWidget(self._actions)
        tracks_layout.addWidget(self._music_view, 1)
        lists = QSplitter(Qt.Vertical)
        lists.addWidget(self._browser)
        lists.addWidget(tracks_box)
        lists.setSizes([240, 520])
        lists.setStretchFactor(1, 1)
        # a destra i tag dei brani scelti, come l'editor della scheda PC: si chiude (✕) e si riapre con Cambia i tag
        # o il tasto E
        splitter = QSplitter()
        splitter.addWidget(lists)
        splitter.addWidget(self._build_tag_panel())
        splitter.setSizes([1040, 330])
        splitter.setStretchFactor(0, 1)

        box = QWidget()
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.addLayout(search_row)
        box_layout.addWidget(self._show)
        box_layout.addWidget(splitter, 1)
        return box

    def _build_tag_panel(self) -> QWidget:
        """Il riquadro dei tag a destra, con il titolo e la ✕ come nella scheda PC."""
        self._tag_panel = PhoneTagPanel()
        self._tag_panel.queue_requested.connect(self._queue_tag_edit)
        self._tag_scroll = QScrollArea()
        self._tag_scroll.setWidget(self._tag_panel)
        self._tag_scroll.setWidgetResizable(True)
        self._tag_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._tag_scroll.setMinimumWidth(320)
        self._tag_box = QWidget()
        title = QLabel("Cambia i tag")
        title.setObjectName("panelTitle")
        close = QToolButton()
        close.setText("✕")
        close.setToolTip("Chiude l'editor dei tag: si riapre con Cambia i tag o il tasto E")
        close.clicked.connect(lambda: self._tag_box.setVisible(False))
        head = QHBoxLayout()
        head.addWidget(title, 1)
        head.addWidget(close)
        layout = QVBoxLayout(self._tag_box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(head)
        layout.addWidget(self._tag_scroll, 1)
        return self._tag_box

    def _update_tag_panel(self) -> None:
        """Il riquadro dei tag (se è aperto) segue quello che si vede: i brani selezionati ancora visibili; senza, con
        un album scelto negli elenchi, la sua copertina e il suo nome (come nella scheda PC); altrimenti vuoto. Si rifà
        solo quando cambia, così una ricerca non cancella quello che si sta scrivendo."""
        if hasattr(self, "_tag_panel") and not self._tag_box.isHidden():
            items = self._selected_phone_tracks()
            albums = self._browser.selected_albums()
            album = None
            if not items and len(albums) == 1:
                album = next(iter(albums))
            pids = []
            for item in items:
                pids.append(item.pid)
            shown = (tuple(pids), album)
            if shown != self._tag_shown:
                self._tag_shown = shown
                if album is not None:
                    members = self._browser.album_tracks(album)
                    cover, note = self._cover_for(members)
                    self._tag_panel.show_album(members, cover, note)
                else:
                    self._show_in_tag_panel(items)

    def _show_in_tag_panel(self, items: list) -> None:
        """Il riquadro dei tag con items: quanti hanno il file associato su questo PC e la copertina di quel file."""
        linked = self._linked_tracks(items)
        cover, note = self._cover_for(items)
        self._tag_panel.set_tracks(items, len(linked), cover, note)

    def _linked_tracks(self, items: list) -> list:
        """I file del PC (Track) associati con certezza ai brani dell'iPhone items."""
        result = []
        for item in items:
            state, track = self._pc_states.get(item.pid, (PC_NONE, None))
            if state in (PC_SAME, PC_STALE) and track is not None:
                result.append(track)
        return result

    def _cover_for(self, items: list) -> tuple:
        """(immagine o None, da dove viene) per il riquadro dei tag: quella del file associato sul PC, per brani di un
        solo album (l'immagine che ha l'iPhone non si legge da qui)."""
        cover = None
        note = ""
        albums = set()
        for item in items:
            albums.add((group_name(item.display_artist), group_name(item.tags.album)))
        coverless = False
        for item in items:
            if item.album_without_cover:
                coverless = True
        if len(albums) == 1:
            linked = self._linked_tracks(items[:COVER_TRIES])
            index = 0
            while cover is None and index < len(linked):
                cover = self._window.cover_of(linked[index])
                index += 1
            if cover is not None:
                note = "Dal file associato sul PC"
            elif linked:
                note = "Il file associato sul PC non ha la copertina"
            else:
                note = "Nessun file associato sul PC: l'immagine che ha l'iPhone non si legge da qui"
        elif albums:
            note = "Brani di album diversi"
        if coverless:
            note += ("\nSull'iPhone l'album non ha l'immagine: il pulsante Ricopia le copertine da PC a iPhone, nella "
                     "barra sopra i brani")
        row_artists = set()
        for item in items:
            if item.misfiled:
                row_artists.add(item.album_row_artist)
        if row_artists:
            names = ", ".join(sorted(row_artists))
            note += (f"\nNell'app Musica sta in un album di \"{names}\", non del suo artista dell'album: il pulsante "
                     "Rimetti nell'album giusto, nella barra sopra i brani")
        if len(items) == 1:
            note += self._duplicate_note(items[0])
        result = (cover, note.strip())
        return result

    def _duplicate_note(self, item) -> str:
        """Per il riquadro dei tag: le altre copie della stessa canzone nello stesso album (e quale tenere) o in altri
        album (legittime)."""
        result = ""
        chosen = self._duplicates.set_of.get(item.pid)
        if chosen is not None:
            result += (f"\nDoppione: {len(chosen.copies)} copie di questa canzone nello stesso album. "
                       f"{chosen.reasons.get(item.pid, '')}. Nella barra sopra i brani: Togli le copie in più, o "
                       "Tieni questa copia")
        elsewhere = self._duplicates.other_albums.get(item.pid, [])
        if elsewhere:
            albums = []
            for other in elsewhere:
                if other.tags.album not in albums:
                    albums.append(other.tags.album)
            result += "\nLa stessa canzone anche in: " + ", ".join(albums)
        return result

    def _bar_items(self) -> list:
        """I brani per la barra delle azioni: quelli selezionati o, senza selezione, quelli dell'artista o dell'album
        scelti negli elenchi (quelli che si vedono)."""
        result = self._selected_phone_tracks()
        if not result and self._browser.track_filter() is not None:
            view = self._music_view
            for index in range(view.topLevelItemCount()):
                row = view.topLevelItem(index)
                item = self._by_pid.get(row.data(COL_TITLE, PID_ROLE))
                if item is not None and not row.isHidden():
                    result.append(item)
        return result

    def _update_action_bar(self) -> None:
        if hasattr(self, "_actions"):
            items = self._bar_items()
            entries = self._phone_entry_map(items) if items else {}
            bar = {}
            for key in ("save", "replace", "tags", "edit", "link", "delete"):
                if key in entries:
                    bar[key] = entries[key]
                else:
                    bar[key] = (tr(BAR_LABELS[key]), False, None)
            cover = self._cover_bar_entry(items)
            if cover is not None:                      # senza voce il pulsante si nasconde
                bar["cover"] = cover
            refile = self._refile_bar_entry(items)
            if refile is not None:
                bar["refile"] = refile
            bar.update(self.duplicate_entries(items, visible_too=True))
            if not items:
                who = "Scegli dei brani, o un artista o un album:"
            elif len(items) == 1:
                who = "1 brano scelto:"
            else:
                who = f"{len(items)} brani scelti:"
            self._actions.set_entries(who, bar, entries.get("note", ("", False, None))[0])

    def _fill_tools(self) -> None:
        """Il menu Strumenti: le azioni per i brani scelti che non stanno nella barra e quelle su tutti i brani."""
        menu = self._tools
        menu.clear()
        items = self._bar_items()
        everything = list(self._phone_tracks)
        entries = self._phone_entry_map(items) if items else {}
        rows = [
            entries.get("tags_to_pc", ("Usa i tag da iPhone a PC: scegli dei brani ⟳…", False, None)),
            entries.get("show_pc", ("Mostra nella scheda PC: scegli dei brani", False, None)),
            None,
            self._complete_entry(items if items else everything),
            self._cover_entry(items if items else everything),
            None,
            ("Associa al file sul PC tutti i brani senza sorgente…", not self._window.runner.is_busy, self._adopt),
            entries.get("probable", ("Associa le probabili ≈: scegli dei brani", False, None)),
            entries.get("proposed", ("Associa la sorgente proposta in rosso: scegli dei brani", False, None)),
            entries.get("unlink", ("Togli la sorgente: scegli dei brani", False, None)),
            None,
            ("Rifai le playlist per artista sull'iPhone…", self._connected and not self._window.runner.is_busy,
             self._plan_playlists),
        ]
        for row in rows:
            if row is None:
                menu.addSeparator()
            else:
                text, enabled, slot = row
                action = menu.addAction(text)
                action.setEnabled(enabled and slot is not None)
                if slot is not None:
                    action.triggered.connect(slot)

    def set_phone_tracks(self, tracks: list, note: str) -> None:
        """L'elenco da mostrare (letto ora dall'iPhone o salvato l'ultima volta); note dice da dove viene."""
        self._phone_tracks = list(tracks)
        self._by_pid = {}
        for item in self._phone_tracks:
            self._by_pid[item.pid] = item
        self._group_albums()
        self._listing_note.setText(f"{songs(len(tracks))} nell'app Musica · {note}")
        self._fill_music()

    def _group_albums(self) -> None:
        groups = album_groups(self._phone_tracks)
        self._album_of = {}
        for key, members in groups.items():
            for item in members:
                self._album_of[item.pid] = key
        self._browser.set_data(groups, {})

    def regroup(self) -> None:
        """Gli elenchi Artisti e Album e le tinte degli album, dopo un cambio dei nomi di "Artisti vari"."""
        self._group_albums()
        self._apply_search()

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
        self._spelling = {}
        self._cover_known = {}
        self._tag_shown = None
        for item in self._phone_tracks:
            self._pc_states[item.pid] = self._pc_state(item)
            state, track = self._pc_states[item.pid]
            if state in (PC_SAME, PC_STALE):
                fields = spelling_differences(track.tags, item.tags)
                if fields:
                    self._spelling[item.pid] = fields
        self._window.tag_cache.save()     # le sorgenti fuori dalla cartella aperta lette ora
        unlinked = []
        for item in self._phone_tracks:
            if item.from_computer and item.sync_id and self._window.registry.get(item.sync_id) is None:
                unlinked.append(item)
        # album intero, nome della cartella, regole: senza leggere l'audio (circa un secondo e mezzo per 500 brani
        # non associati e 15.000 file sul PC)
        self._proposed = adoption.automatic_proposals(unlinked, self._window.tracks,
                                                      self._window.preferred_order(),
                                                      set(self._window.registry.links_here()))
        same_tags = {}
        for item in self._phone_tracks:
            state = self._pc_states[item.pid][0]
            if state in (PC_SAME, PC_STALE):
                same_tags[item.pid] = state == PC_SAME
        self._duplicates = phone_duplicates.find(self._phone_tracks, self._registry_paths(self._phone_tracks),
                                                 same_tags)
        self._pc_dirty = False

    def _registry_paths(self, items: list) -> dict:
        """{pid: il file del PC associato nel registro} (anche di un altro computer): per riconoscere i doppioni."""
        result = {}
        for item in items:
            link = self._window.registry.get(item.sync_id) if item.sync_id else None
            if link is not None:
                result[item.pid] = link.path
        return result

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
                COL_SOURCE_FOLDER: ("", ""),
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
        self.pending_changed()

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
        folder, name = self._source_texts(item)
        proposal = self._proposed.get(item.pid)
        tip = self._source_path(item)
        is_proposal = not name and proposal is not None
        if is_proposal:
            proposed = proposal.pc
            folder = self._folder_text(str(proposed.path.parent))
            name = proposed.path.name
            tip = (f"Sorgente proposta, non ancora associata ({proposal.level}):\n{proposed.path}\n"
                   f"{proposal.reason}. Tasto destro → Associa questa sorgente.")
        different = not is_proposal and self._pc_states.get(item.pid, (PC_NONE, None))[0] == PC_STALE
        if different:
            tip += ("\nI tag sono diversi da quelli dell'iPhone: il file resta la sorgente. Tasto destro → Usa i "
                    "tag da PC a iPhone o da iPhone a PC per scegliere quali tenere.")
        if is_proposal:
            brush = QBrush(PROPOSED_COLOR)
        elif different:
            brush = QBrush(DIFFERENT_COLOR)
        else:
            brush = QBrush()
        for column, text in ((COL_SOURCE_FOLDER, folder), (COL_SOURCE_FILE, name)):
            row.setText(column, text)
            row.setData(column, SORT_ROLE, text.lower())
            row.setForeground(column, brush)
            row.setToolTip(column, tip)
        row.setData(COL_SOURCE_FILE, PROPOSED_ROLE, is_proposal)
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

    def _folder_text(self, folder: str) -> str:
        """Una cartella come si mostra: il percorso completo o il solo nome (Impostazioni); per una cartella di disco
        anche quella sopra ("Album\\CD1", library.short_folder)."""
        result = folder if self._window.app_settings.show_full_path else short_folder(folder)
        return result

    def _source_texts(self, item) -> tuple:
        """(Cartella della sorgente, File della sorgente): la cartella con il computer davanti se non è questo; ("", "")
        senza sorgente."""
        link = self._window.registry.get(item.sync_id) if item.sync_id else None
        if link is None:
            result = ("", "")
        else:
            plain = Path(link.path.replace("\\", "/"))
            folder = self._folder_text(str(Path(link.path).parent))
            result = (folder if link.here else f"{link.pc}: {folder}", plain.name)
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
        result = track is not None and self._window.is_open(track.path)
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
        chosen_rule = max(0, self._show.currentIndex())
        chosen = self._browser.track_filter()     # None, o (artisti, album) scelti negli elenchi
        shown = 0
        without_rule = 0                          # quanti si vedrebbero con il filtro Tutti
        counts = [0] * len(SHOW_FILTERS)          # quanti brani ha ogni filtro a pulsanti (tutti i brani)
        view = self._music_view
        for index in range(view.topLevelItemCount()):
            row = view.topLevelItem(index)
            text = " ".join([row.text(COL_TITLE), row.text(COL_ARTIST), row.text(COL_ALBUM)]).casefold()
            pid = row.data(COL_TITLE, PID_ROLE)
            item = self._by_pid.get(pid)
            facts = RowFacts(row.data(COL_ORIGIN, ORIGIN_ROLE), row.data(COL_PC, PC_STATE_ROLE),
                             row.data(COL_SOURCE_FILE, PROPOSED_ROLE), item is not None and item.album_without_cover,
                             item is not None and item.misfiled, pid in self._duplicates.set_of,
                             pid in self._duplicates.other_albums)
            for position, (_text, rule) in enumerate(SHOW_FILTERS):
                if rule(facts):
                    counts[position] += 1
            matches = True                            # Cerca e gli elenchi Artisti/Album, senza il filtro
            for word in words:
                if word not in text:
                    matches = False
            if matches and chosen is not None:
                matches = self._in_chosen(row.data(COL_TITLE, PID_ROLE), chosen)
            if matches:
                without_rule += 1
            visible = matches and SHOW_FILTERS[chosen_rule][1](facts)
            row.setHidden(not visible)
            if visible:
                shown += 1
        if self._show.set_counts(counts):
            self._apply_search()                      # il filtro scelto era rimasto vuoto: di nuovo con Tutti
        else:
            self._mark_duplicates(self._show.currentIndex() == DUPLICATES_FILTER)
            self._update_bands()
            self._show.set_shown(shown, without_rule)
            total = view.topLevelItemCount()
            if words or self._show.currentIndex() > 0 or chosen is not None:
                self._count.setText(f"{shown} di {total} brani")
            else:
                self._count.setText(f"{total} brani")
            self._update_action_bar()
            self._update_tag_panel()     # un brano selezionato ora nascosto non resta nel riquadro dei tag

    def _mark_duplicates(self, on: bool) -> None:
        """Con il filtro dei doppioni: la copia da tenere in grassetto, quelle da togliere barrate e grigie, il perché
        nel suggerimento dell'album. Il titolo resta com'è (corsivo blu per le azioni in attesa). Senza il filtro, le
        righe tornano normali."""
        view = self._music_view
        plain_columns = (COL_NUMBER, COL_ARTIST, COL_ALBUM_ARTIST, COL_ALBUM, COL_YEAR, COL_GENRE, COL_LENGTH)
        marked = set()
        for index in range(view.topLevelItemCount()):
            row = view.topLevelItem(index)
            pid = row.data(COL_TITLE, PID_ROLE)
            chosen = self._duplicates.set_of.get(pid) if on else None
            if chosen is not None:
                keep = chosen.best.pid == pid
                font = QFont()
                font.setBold(keep)
                font.setStrikeOut(not keep)
                brush = QBrush() if keep else QBrush(DROP_COLOR)
                for column in plain_columns:
                    row.setFont(column, font)
                    row.setForeground(column, brush)
                row.setToolTip(COL_ALBUM, chosen.reasons.get(pid, ""))
                marked.add(pid)
            elif pid in self._marked:
                for column in plain_columns:
                    row.setFont(column, QFont())
                    row.setForeground(column, QBrush())
                row.setToolTip(COL_ALBUM, "")
        self._marked = marked

    def _update_bands(self) -> None:
        """Le tinte degli album, per le righe che si vedono nell'ordine in cui si vedono."""
        view = self._music_view
        pids = []
        keys = []
        for index in range(view.topLevelItemCount()):
            row = view.topLevelItem(index)
            if not row.isHidden():
                pid = row.data(COL_TITLE, PID_ROLE)
                pids.append(pid)
                keys.append(self._album_of.get(pid))
        bands = {}
        for pid, (band, shade) in zip(pids, album_bands(keys)):
            bands[pid] = album_band(band, shade)
        view.bands = bands
        view.viewport().update()

    def spelling_plan(self, items: list) -> tuple:
        """Allinea la grafia per i brani scelti: (coppie (PhoneTrack, Track) da togliere e reinviare, album che non si
        possono allineare). Si prende ogni album intero con un brano scritto diversamente; se è diverso l'artista
        dell'album, tutti gli album di quell'artista (sull'iPhone la sua riga è una sola). Un album o un artista si
        allinea solo se tutti i suoi brani hanno la sorgente certa su questo PC."""
        albums = set()
        artists = set()
        for item in items:
            fields = self._spelling.get(item.pid, [])
            if fields:
                albums.add(item.album_sync_id)
            if "album_artist" in fields:
                artists.add(item.artist_sync_id)
        complete_albums = {}
        complete_artists = {}
        for item in self._phone_tracks:
            linked = self._pc_states.get(item.pid, (PC_NONE, None))[0] in (PC_SAME, PC_STALE)
            if item.album_sync_id in albums:
                complete_albums[item.album_sync_id] = complete_albums.get(item.album_sync_id, True) and linked
            if item.artist_sync_id in artists:
                complete_artists[item.artist_sync_id] = complete_artists.get(item.artist_sync_id, True) and linked
        chosen = set()
        blocked = 0
        for album, complete in complete_albums.items():
            if complete:
                chosen.add(album)
            else:
                blocked += 1
        for item in self._phone_tracks:
            if complete_artists.get(item.artist_sync_id, False):
                chosen.add(item.album_sync_id)
        for artist, complete in complete_artists.items():
            if not complete:
                blocked += 1
        pairs = []
        for item in self._phone_tracks:
            if item.album_sync_id in chosen and item.album_sync_id:
                pairs.append((item, self._pc_states[item.pid][1]))
        result = (pairs, blocked)
        return result

    def complete_plan(self, items: list) -> tuple:
        """Completa l'album: (brani del PC da inviare, album). Per i brani scelti con la sorgente certa (✔, ⟳) la loro
        copia dell'album sul PC (stessa cartella, con i dischi insieme, e stesso album) e, di quella, i brani che
        sull'iPhone non ci sono. Un brano abbinato solo per i tag (≈) non conta: potrebbe portare all'album
        sbagliato. Solo i formati che si inviano (MP3, FLAC, M4A AAC)."""
        from ..phone_sync import AUDIO_READERS
        window = self._window
        wanted = set()
        for item in items:
            state, track = self._pc_states.get(item.pid, (PC_NONE, None))
            if state in (PC_SAME, PC_STALE) and track is not None:
                wanted.add((album_folder(track.path).lower(), group_name(track.tags.album)))
        sends = []
        albums = set()
        if wanted:
            for track in window.tracks:
                key = (album_folder(track.path).lower(), group_name(track.tags.album))
                if key in wanted and not track.error and track.path.suffix.lower() in AUDIO_READERS and \
                        window.device_state(track)[0] == DEVICE_ABSENT:
                    sends.append(track)
                    albums.add(key)
        result = (sends, len(albums))
        return result

    def _complete_entry(self, items: list) -> tuple:
        """La voce Copia i brani mancanti degli album (ex Completa l'album) per i brani scelti: (testo, attiva,
        funzione); va in attesa."""
        sends, albums = self.complete_plan(items)
        if sends:
            text = f"Copia i brani mancanti degli album da PC a iPhone: {songs(len(sends))} ({albums} album)"
        else:
            text = ("Copia i brani mancanti degli album da PC a iPhone: non manca niente (o i brani non hanno la "
                    "sorgente)")
        result = (text, bool(sends), lambda: self._window.queue_files(sends, SEND))
        return result

    def _pc_has_cover(self, album_sync_id: int, tracks: list) -> bool:
        """Almeno uno dei primi COVER_TRIES file associati dell'album ha la copertina (anche nuova, in sospeso): solo
        allora una Ricopia dà l'immagine all'album sull'iPhone. Si ricorda fino al prossimo confronto con il PC."""
        if album_sync_id not in self._cover_known:
            found = False
            index = 0
            while not found and index < len(tracks) and index < COVER_TRIES:
                found = self._window.cover_of(tracks[index]) is not None
                index += 1
            self._cover_known[album_sync_id] = found
        result = self._cover_known[album_sync_id]
        return result

    def cover_plan(self, items: list) -> tuple:
        """Sistema le copertine per i brani scelti: (coppie (PhoneTrack, Track) da rimpiazzare dal PC, album senza
        sorgente, album senza copertina neanche sul PC). Gli album senza immagine sull'iPhone, interi: tutti i loro
        brani con la sorgente certa su questo PC; un rimpiazzo dal PC fa scegliere all'iPhone l'immagine dell'album
        (provato il 24/11/2026). Non si può per un album senza nessun brano con la sorgente, né per uno i cui file del
        PC non hanno la copertina (la Ricopia non gliela darebbe)."""
        albums = set()
        for item in items:
            if item.album_without_cover and item.album_sync_id:
                albums.add(item.album_sync_id)
        linked = {}
        for item in self._phone_tracks:
            if item.album_sync_id in albums and item.from_computer:
                state, track = self._pc_states.get(item.pid, (PC_NONE, None))
                if state in (PC_SAME, PC_STALE):
                    linked.setdefault(item.album_sync_id, []).append((item, track))
        pairs = []
        no_cover = 0
        for album_sync_id, album_pairs in linked.items():
            tracks = []
            for _item, track in album_pairs:
                tracks.append(track)
            if self._pc_has_cover(album_sync_id, tracks):
                pairs.extend(album_pairs)
            else:
                no_cover += 1
        result = (pairs, len(albums) - len(linked), no_cover)
        return result

    def _cover_entry(self, items: list) -> tuple:
        """La voce Ricopia le copertine (ex Sistema le copertine) per i brani scelti: (testo, attiva, funzione). Gli
        album sull'iPhone senza immagine, anche se i brani hanno la copertina (album messi da altri programmi):
        ricopiando i loro brani dal PC l'iPhone la sceglie. Va in attesa come Ricopia."""
        pairs, no_source, no_cover = self.cover_plan(items)
        albums = set()
        for item, _track in pairs:
            albums.add(item.album_sync_id)
        text = f"Ricopia le copertine da PC a iPhone: {len(albums)} album senza immagine"
        if no_source:
            text += f"; {no_source} senza sorgente sul PC"
        if no_cover:
            text += f"; {no_cover} senza copertina anche sul PC"
        result = (text, bool(pairs), lambda: self._window.queue_pairs(pairs, REPLACE))
        return result

    def _visible_phone_tracks(self) -> list:
        result = []
        for index in range(self._music_view.topLevelItemCount()):
            row = self._music_view.topLevelItem(index)
            item = self._by_pid.get(row.data(COL_TITLE, PID_ROLE))
            if item is not None and not row.isHidden():
                result.append(item)
        return result

    def _cover_bar_entry(self, items: list):
        """Il pulsante Ricopia le copertine nella barra: con il filtro "Album senza immagine sull'iPhone" (per i brani
        scelti o, senza scelta, per tutti quelli che si vedono) o quando tra i brani scelti c'è un album senza
        immagine. None quando non serve (il pulsante si nasconde)."""
        targets = list(items)
        if self._show.currentIndex() == COVERLESS_FILTER and not targets:
            targets = self._visible_phone_tracks()
        coverless = False
        for item in targets:
            if item.album_without_cover:
                coverless = True
        result = self._cover_entry(targets) if coverless else None
        return result

    def refile_plan(self, items: list) -> tuple:
        """I brani di items che l'app Musica mostra in un album con un altro artista dell'album (misfiled): (coppie
        (PhoneTrack, Track) da ricopiare dal PC, quanti non si possono perché senza la sorgente certa). Si ricopiano
        anche se i tag coincidono (✔): il difetto è nella riga dell'album sull'iPhone, che il confronto non vede."""
        pairs = []
        blocked = 0
        for item in items:
            if item.misfiled:
                state, track = self._pc_states.get(item.pid, (PC_NONE, None))
                if item.from_computer and state in (PC_SAME, PC_STALE) and track is not None:
                    pairs.append((item, track))
                else:
                    blocked += 1
        result = (pairs, blocked)
        return result

    def _refile_bar_entry(self, items: list):
        """Il pulsante Ricopia da PC a iPhone per i brani nell'album sbagliato: con il filtro "Nell'album sbagliato
        sull'iPhone" (i brani scelti o, senza scelta, quelli che si vedono) o quando tra i brani scelti ce n'è uno.
        None quando non serve."""
        targets = list(items)
        if self._show.currentIndex() == MISFILED_FILTER and not targets:
            targets = self._visible_phone_tracks()
        pairs, blocked = self.refile_plan(targets)
        result = None
        if pairs or blocked:
            albums = set()
            for item, _track in pairs:
                albums.add(item.album_sync_id)
            text = f"Rimetti nell'album giusto (Ricopia da PC a iPhone): {songs(len(pairs))}, {len(albums)} album"
            if blocked:
                text += f"; {blocked} senza sorgente sul PC"
            result = (text, bool(pairs), lambda: self._window.queue_pairs(pairs, REPLACE))
        return result

    def duplicate_entries(self, items: list, visible_too: bool = False) -> dict:
        """Le voci per i doppioni: "dedupe" (Togli le copie in più: di ogni canzone toccata dai brani scelti si tiene
        la copia migliore) e "keep" (Tieni questa copia: un brano scelto, si tolgono le altre copie dello stesso
        album). visible_too: con il filtro dei doppioni e nessun brano scelto, per tutti quelli che si vedono. Solo
        le voci che servono; vanno in attesa come Elimina dall'iPhone."""
        targets = list(items)
        if visible_too and not targets and self._show.currentIndex() == DUPLICATES_FILTER:
            targets = self._visible_phone_tracks()
        result = {}
        drops = self._duplicates.to_remove(targets)
        if drops:
            result["dedupe"] = (f"Togli le copie in più (Elimina dall'iPhone): {songs(len(drops))}; resta la "
                                "migliore di ogni canzone", True, lambda: self._window.queue_deletes(drops))
        if len(items) == 1:
            others = self._duplicates.others_of(items[0])
            if others:
                result["keep"] = (f"Tieni questa copia, togli le altre (Elimina dall'iPhone): {songs(len(others))}",
                                  True, lambda: self._window.queue_deletes(others))
        return result

    def _service_leftovers(self) -> list:
        """I brani di servizio rimasti sull'iPhone da un'operazione interrotta: si tolgono con i prossimi."""
        result = []
        for item in self._phone_tracks:
            if phone_actions.is_service_track(item.tags) and item.from_computer:
                result.append(item)
        return result

    def split_for_spelling(self, pairs: list) -> tuple:
        """Prima di ogni aggiornamento dal PC: (coppie da aggiornare come sempre, coppie degli album interi da togliere e
        reinviare perché l'iPhone prenda la grafia del PC, album con la grafia diversa che non si possono reinviare
        interi). Un brano associato con l'album o l'artista dell'album scritto in modo diverso dal PC (_spelling) porta
        con sé il suo album intero, o tutti gli album dell'artista (spelling_plan): l'iPhone tiene la grafia del suo
        gruppo finché esiste, e solo togliendolo tutto la cambia (phone_actions.align_spelling)."""
        items = []
        for phone_track, _track in pairs:
            if self._spelling.get(phone_track.pid):
                items.append(phone_track)
        whole = []
        blocked = 0
        if items:
            whole, blocked = self.spelling_plan(items)
        taken = set()
        for phone_track, _track in whole:
            taken.add(phone_track.pid)
        rest = []
        for phone_track, track in pairs:
            if phone_track.pid not in taken:
                rest.append((phone_track, track))
        result = (rest, whole, blocked)
        return result

    def _spelling_cost(self, whole: list) -> tuple:
        """(byte di ogni brano da inviare, brani da togliere) per reinviare gli album interi, con i brani di servizio."""
        sizes = []
        removes = 0
        if whole:
            leftovers = self._service_leftovers()
            padding = phone_actions.service_padding(len(whole) + len(leftovers))
            sizes = [phone_actions.SERVICE_SIZE] * padding
            for _phone_track, track in whole:
                sizes.append(estimate.file_size(track.path))
            removes = len(whole) + padding + len(leftovers)
        result = (sizes, removes)
        return result

    @staticmethod
    def _spelling_text(whole: list, blocked: int) -> str:
        """Le righe della conferma per gli album da reinviare interi per la grafia."""
        albums = set()
        for phone_track, _track in whole:
            albums.add(phone_track.album_sync_id)
        text = ""
        if whole:
            text = (f"\n\nGrafia: {len(albums)} album hanno il nome dell'album o dell'artista scritto in modo diverso "
                    "dal PC (maiuscole, zeri, accenti). L'iPhone tiene il nome che ha già, quindi questi album si "
                    f"tolgono interi e si reinviano dal PC: {len(whole)} brani, anche quelli dello stesso album non "
                    "scelti, con qualche brano di servizio di 3 secondi che si toglie subito.")
        if blocked:
            text += (f"\n\n{blocked} album con la grafia diversa hanno brani senza sorgente associata: non si possono "
                     "reinviare interi e restano con la grafia dell'iPhone.")
        return text

    def _with_spelling(self, whole: list, action):
        """action(progress, cancel) preceduta dal reinvio degli album interi per la grafia."""
        overlay = self._window.overlay
        leftovers = tuple(self._service_leftovers())

        def combined(progress, cancel):
            report = phone_actions.ActionReport()
            if whole:
                report.add(phone_actions.align_spelling(whole, overlay, progress, cancel, config_dir(), leftovers))
            if not cancel.is_set():
                report.add(action(progress, cancel))
            return report

        return combined

    def _in_chosen(self, pid, chosen: tuple) -> bool:
        """Il brano è tra gli album scelti negli elenchi o, senza album scelti, tra gli artisti scelti."""
        artists, albums = chosen
        key = self._album_of.get(pid)
        if key is None:
            result = False
        elif albums:
            result = key in albums
        else:
            result = key[0] in artists
        return result

    def _selected_phone_tracks(self) -> list:
        result = []
        for row in self._music_view.selectedItems():
            item = self._by_pid.get(row.data(COL_TITLE, PID_ROLE))
            if item is not None and not row.isHidden():
                result.append(item)
        return result

    def _stale_pairs(self, items: list) -> list:
        """(brano dell'iPhone, brano del PC) per i brani selezionati con ⟳: solo quelli associati (la sorgente nel
        registro, anche fuori dalla cartella aperta). Un brano ≈, abbinato solo per i tag, non si aggiorna dal PC:
        prima si associa."""
        result = []
        for item in items:
            state, track = self._pc_states.get(item.pid, (PC_NONE, None))
            if state == PC_STALE and item.from_computer:
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

    def _with_proposal(self, items: list) -> list:
        """I brani scelti con una sorgente proposta (in rosso) e ancora senza sorgente."""
        result = []
        for item in items:
            if item.pid in self._proposed and item.sync_id and self._window.registry.get(item.sync_id) is None:
                result.append(item)
        return result

    def _link_proposed(self, items: list) -> None:
        """Associa questa sorgente: la proposta in rosso diventa la sorgente (registro); il nome torna normale."""
        window = self._window
        registry = window.registry
        for item in items:
            proposal = self._proposed[item.pid]
            registry.record(adoption.link_for(proposal, window.overlay,
                                              window.tag_cache.fingerprint(proposal.pc.path)))
        self._store_registry(registry, f"Sorgente associata a {len(items)} brani")

    def _align_to_pc(self, pairs: list) -> None:
        """Usa i tag da iPhone a PC: i tag diversi dell'iPhone si SCRIVONO nei file del PC, dopo che l'utente ha
        visto l'elenco dei file e dei campi e l'ha approvato (AlignToPcDialog). Le modifiche in sospeso di quei file
        entrano nel file insieme; la copertina in sospeso resta in sospeso."""
        from ..phone_library import changed_fields
        from ..tags import READ_ONLY_EXTENSIONS
        plan = []
        for item, track in pairs:
            fields = changed_fields(track.tags, item.tags)
            if fields and track.path.suffix.lower() not in READ_ONLY_EXTENSIONS:
                new_tags = track.tags.copy()
                for name in fields:
                    setattr(new_tags, name, getattr(item.tags, name))
                plan.append((track, new_tags, fields))
        if not plan:
            QMessageBox.information(self, "Usa i tag da iPhone a PC", "Sul PC non c'è niente da cambiare.")
        else:
            dialog = AlignToPcDialog(self, plan)
            if dialog.exec():
                self._write_pc_tags(dialog.chosen_plan())

    def _write_pc_tags(self, plan: list) -> None:
        """Scrive i tag approvati nei file del PC (tags.write_tags_approved) e li rilegge."""
        from ..library import load_track
        from ..tags import TagError, write_tags_approved
        window = self._window

        def work(progress, _cancel):
            done = []
            errors = []
            for index, (track, new_tags, _fields) in enumerate(plan):
                progress(index, len(plan), track.path.name)
                try:
                    write_tags_approved(track.path, new_tags)
                    done.append((track, load_track(track.path)))
                except (TagError, OSError) as exc:
                    errors.append(f"{track.path.name}: {exc}")
            value = (done, errors)
            return value

        def finished(value):
            done, errors = value
            for track, fresh in done:
                track.original_tags = fresh.tags.copy()
                track.length = fresh.length or track.length
                window.overlay.set_tags(track, fresh.tags)     # i campi ora nel file non sono più in sospeso
                window.tag_cache.store(track)
            try:
                window.overlay.save()
            except OSError:
                pass  # resta come prima: al prossimo avvio le modifiche in sospeso coincidono con il file
            window.tag_cache.save()
            window.refresh_after_tag_change()
            message = f"Tag scritti in {len(done)} file del PC"
            if errors:
                QMessageBox.warning(self, "Usa i tag da iPhone a PC", message + ". Non riusciti:\n" + "\n".join(errors[:10]))
            else:
                window.statusBar().showMessage(message, 8000)

        window.runner.run("Usa i tag da iPhone a PC", work, finished)

    def _align_to_phone(self, pairs: list) -> None:
        """Usa i tag da PC a iPhone: in attesa (Applica). Dove basta si cambiano i tag (restano ascolti e playlist),
        con artista diverso o un campo da svuotare il brano si ricopia; gli album scritti diversamente si ricopiano
        interi (split_for_spelling)."""
        self._window.queue_pairs(pairs, UPDATE)

    def _source_paths(self, items: list) -> list:
        """I file delle sorgenti dei brani scelti (quelli che ne hanno una)."""
        result = []
        for item in items:
            link = self._window.registry.get(item.sync_id) if item.sync_id else None
            if link is not None:
                result.append(link.path)
        return result

    def _show_menu(self, position) -> None:
        self._tracks_menu(self._music_view.viewport().mapToGlobal(position))

    def _phone_entry_map(self, items: list) -> dict:
        """Le azioni per brani dell'iPhone, per nome: {chiave: (testo, attiva, funzione)}; "note" è una nota grigia
        (funzione None). Quelle verso l'iPhone vanno in attesa (Applica) e non chiedono l'iPhone connesso; Copia da
        iPhone a PC, Usa i tag da iPhone a PC e le associazioni sono subito, con la loro conferma."""
        busy = self._window.runner.is_busy
        writable = []
        for item in items:
            if item.from_computer:
                writable.append(item)
        on_pc = []
        for item in items:
            track = self._pc_states.get(item.pid, (PC_NONE, None))[1]
            if track is not None and self._in_open_folder(track):
                on_pc.append(track)
        stale = self._stale_pairs(items)
        probable = self._probable(items)
        proposed = self._with_proposal(items)
        linked_here = []
        for item in items:
            link = self._window.registry.get(item.sync_id) if item.sync_id else None
            if link is not None and link.here:
                linked_here.append(item)
        stale_text = songs(len(stale)) if stale else "nessun brano ⟳ con la sorgente"
        result = {
            "save": (f"Copia {songs(len(items))} da iPhone a PC…", self._connected and not busy,
                     lambda: self._save_selected(items)),
            "show_pc": (f"Mostra nella scheda PC ({songs(len(on_pc))})", bool(on_pc),
                        lambda: self._window.show_tracks({str(track.path) for track in on_pc})),
            "replace": (f"Ricopia da PC a iPhone: {stale_text}", bool(stale),
                        lambda: self._window.queue_pairs(stale, REPLACE)),
            "tags": (f"Usa i tag da PC a iPhone: {stale_text}", bool(stale), lambda: self._align_to_phone(stale)),
            "tags_to_pc": (f"Usa i tag da iPhone a PC: {stale_text}…", bool(stale) and not busy,
                           lambda: self._align_to_pc(stale)),
            "edit": (f"Cambia i tag: {songs(len(writable))}…", bool(writable), lambda: self._edit_items(writable)),
            "complete": self._complete_entry(items),
            "cover": self._cover_entry(items),
            "link": ("Associa al file sul PC…" if len(writable) == 1 else
                     f"Associa al file sul PC: {songs(len(writable))}…", bool(writable) and not busy,
                     lambda: self._link_sources(writable)),
            "probable": (f"Associa le probabili ≈: {songs(len(probable))}", bool(probable) and not busy,
                         lambda: self._link_probable(probable)),
            "proposed": (f"Associa la sorgente proposta in rosso: {songs(len(proposed))}", bool(proposed) and not busy,
                         lambda: self._link_proposed(proposed)),
            "unlink": (f"Togli la sorgente: {songs(len(linked_here))}", bool(linked_here) and not busy,
                       lambda: self._unlink(linked_here)),
            "delete": (f"Elimina {songs(len(writable))} dall'iPhone" if writable else
                       "Elimina dall'iPhone: nessun brano", bool(writable),
                       lambda: self._window.queue_deletes(writable)),
        }
        result.update(self.duplicate_entries(items))
        if len(writable) < len(items):
            result["note"] = (f"{songs(len(items) - len(writable))} acquistati o scaricati sul telefono: un computer "
                              "non li può cambiare né togliere", False, None)
        return result

    def phone_entries(self, items: list) -> list:
        """Le voci del tasto destro sui brani dell'iPhone, in ordine (None: un separatore): [(testo, attiva,
        funzione)], funzione None per una nota grigia."""
        entries = self._phone_entry_map(items)
        result = []
        for key in PHONE_MENU_ORDER:
            if key is None:
                result.append(None)
            elif key in entries:
                result.append(entries[key])
        return result

    def browser_menu_entries(self, items: list) -> list:
        """Le voci del tasto destro su un artista o un album: le stesse dei brani (phone_entries), senza separatori."""
        result = []
        for entry in self.phone_entries(items):
            if entry is not None:
                result.append(entry)
        return result

    def _browser_menu(self, where) -> None:
        """Tasto destro su un artista o un album: le azioni per tutti i suoi brani."""
        show_entries_menu(self, self.browser_menu_entries(self._browser.menu_tracks), where, True)

    def _tracks_menu(self, where) -> None:
        items = self._selected_phone_tracks()
        if items:
            menu = QMenu(self)
            for entry in self.phone_entries(items):
                if entry is None:
                    menu.addSeparator()
                else:
                    text, enabled, slot = entry
                    action = menu.addAction(text)
                    action.setEnabled(enabled)
                    if slot is not None:
                        action.triggered.connect(slot)
            menu.addSeparator()
            self._add_ringtone_entry(menu, items)
            menu.addSeparator()
            sources = QMenu("File della sorgente", menu)
            add_file_entries(sources, self._source_paths(items),
                             lambda text: self._window.statusBar().showMessage(text, 8000))
            menu.addMenu(sources).setEnabled(bool(self._source_paths(items)))
            menu.setToolTipsVisible(True)
            menu.exec(where)

    def _add_ringtone_entry(self, menu, items: list) -> None:
        """Crea una suoneria da un brano dell'iPhone: dal suo file sul PC (la sorgente) se c'è, altrimenti da una
        copia letta dall'iPhone (connesso), che si toglie alla fine."""
        window = self._window
        text, enabled, tip = window.ringtone_entry(len(items) == 1)
        source = None
        if len(items) == 1:
            link = window.registry.get(items[0].sync_id) if items[0].sync_id else None
            if link is not None and link.here and Path(link.path).is_file():
                source = Path(link.path)
            elif enabled and not (self._connected and not window.runner.is_busy):
                enabled = False
                tip = "Connetti l'iPhone: il brano si legge dall'iPhone (sola lettura)"
        action = menu.addAction(text)
        action.setEnabled(enabled)
        action.setToolTip(tip)
        if len(items) == 1:
            item = items[0]
            label = f"{item.display_artist} — {item.tags.title}"
            if source is not None:
                action.triggered.connect(lambda: window.create_ringtone(source, item.tags.title, label))
            else:
                action.triggered.connect(lambda: self._ringtone_from_phone(item, label))

    def _ringtone_from_phone(self, item, label: str) -> None:
        """Legge il brano dall'iPhone in una cartella temporanea, poi Crea una suoneria."""
        folder = Path(tempfile.mkdtemp(prefix="myEasyMP3toIPhone_brano_"))

        def work(progress, cancel):
            report, downloaded = iphone.download_music([item], folder, progress, cancel)
            if not downloaded:
                reason = report.errors[0][1] if report.errors else "non letto"
                raise iphone.IPhoneError(f"Il brano non si legge dall'iPhone: {reason}")
            value = downloaded[0][1]
            return value

        def done(path) -> None:
            self._window.create_ringtone(Path(path), item.tags.title, label,
                                         cleanup=lambda: shutil.rmtree(folder, ignore_errors=True))

        def failed(message: str) -> None:
            shutil.rmtree(folder, ignore_errors=True)
            QMessageBox.warning(self, "Crea una suoneria", message)

        self._window.runner.run("Lettura del brano dall'iPhone", work, done, failed)

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

    def lagging(self, jobs: list) -> list:
        """Le azioni fatte che l'elenco riletto non mostra ancora: un brano copiato che non c'è, uno eliminato che
        c'è ancora (l'iPhone aggiorna il suo database poco dopo la sincronizzazione)."""
        result = []
        for job in jobs:
            if job.action in (SEND, REPLACE) and job.track is not None:
                missing = self._window.device_state(job.track)[0] == DEVICE_ABSENT
            elif job.action == DELETE and job.phone is not None:
                missing = job.phone.pid in self._by_pid
            else:
                missing = False
            if missing:
                result.append(job)
        return result

    def _recheck_later(self, jobs: list, tries: int) -> None:
        """Se l'elenco non mostra ancora quello che Applica ha fatto, lo rilegge da solo dopo RECHECK_SECONDS."""
        waiting = self.lagging(jobs)
        if waiting and tries > 0 and self._connected:
            self._window.statusBar().showMessage(
                f"L'iPhone non mostra ancora {songs(len(waiting))}: lo rileggo tra {RECHECK_SECONDS} secondi", 8000)
            QTimer.singleShot(RECHECK_SECONDS * 1000, lambda: self._recheck(waiting, tries - 1))

    def _recheck(self, jobs: list, tries: int) -> None:
        if self._connected and not self._window.runner.is_busy:
            def work(progress, _cancel):
                progress(0, 0, "rilettura della musica dell'app Musica")
                value = iphone.list_music_app()
                return value

            def done(tracks):
                self._music_read(tracks)
                self._recheck_later(jobs, tries)

            self._window.runner.run("Rilettura dell'iPhone", work, done)
        elif self._connected and tries > 0:
            self._recheck_later(jobs, tries)          # un'operazione in corso: si riprova più tardi

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

    def relocated(self, rows: list) -> dict:
        """{pid: adoption.Proposal}: i file spostati ritrovati nella cartella aperta (relocate.relocate)."""
        from ..relocate import relocate
        window = self._window
        result = relocate(rows, window.tracks, window.tag_cache, window.preferred_order(),
                          set(window.registry.links_here()))
        return result

    def _show_missing(self, rows: list) -> None:
        from .missing_dialog import ACTION_DELETE, ACTION_ORPHAN, ACTION_RELINK, ACTION_SEARCH, MissingSourcesDialog
        found = self.relocated(rows)
        dialog = MissingSourcesDialog(self, rows, self._connected, found)
        if dialog.exec() and not self._window.runner.is_busy:
            chosen = dialog.chosen()
            if dialog.action == ACTION_RELINK:
                self._relink(rows, found, chosen)
            elif dialog.action == ACTION_SEARCH:
                self._source_queue = chosen[1:]
                self._link_one(chosen[0])
            elif dialog.action == ACTION_ORPHAN:
                registry = self._window.registry
                for item in chosen:
                    registry.forget(item.sync_id)
                self._store_registry(registry, f"{len(chosen)} brani ora sono senza sorgente")
            elif dialog.action == ACTION_DELETE:
                self._window.queue_deletes(chosen)

    def _relink(self, rows: list, found: dict, chosen: list) -> None:
        """Associa i file ritrovati: per i brani spuntati che ne hanno uno, il file ritrovato diventa la sorgente
        (registro). Con lo stesso audio l'impronta è quella che il registro aveva già."""
        window = self._window
        registry = window.registry
        old_prints = {}
        for item, link in rows:
            old_prints[item.pid] = link.fingerprint
        count = 0
        for item in chosen:
            proposal = found.get(item.pid)
            if proposal is not None:
                if proposal.how == provenance.HOW_FINGERPRINT:
                    printed = old_prints.get(item.pid, "")
                else:
                    printed = window.tag_cache.fingerprint(proposal.pc.path)
                registry.record(adoption.link_for(proposal, window.overlay, printed))
                count += 1
        self._store_registry(registry, f"Ritrovati e associati {count} file spostati")

    # ------------------------------------------------------------------ scrittura sull'iPhone

    def _write(self, title: str, verb: str, action, note: str = "", after=None, quiet: bool = False,
               then=None, describe=None) -> None:
        """Esegue action(progress, cancel) -> ActionReport, poi rilegge la musica dell'iPhone e mostra l'esito (con
        note in fondo, se qualcosa è riuscito). after(report), se c'è, prima del messaggio. quiet: l'esito solo se
        qualcosa non è riuscito. then(), se c'è, per ultimo (anche se l'azione si interrompe con un errore)."""
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
            message = describe(report) if describe is not None else _report_text(report, verb)
            if report.done:
                message += note + "\n\n" + MUSIC_APP_REFRESH
            if not quiet:
                QMessageBox.information(self, title, message)
            elif report.errors:
                QMessageBox.warning(self, title, message)
            if then is not None:
                then()

        def failed(message: str) -> None:
            QMessageBox.warning(self, title, message)
            if then is not None:
                then()

        self._window.runner.run(title, work, done, failed)

    def _confirm(self, title: str, text: str) -> bool:
        """Conferma o Annulla (Annulla è la scelta predefinita: Invio da solo non fa partire niente)."""
        box = QMessageBox(QMessageBox.Question, title, text + "\n\n" + SYNC_WARNING, QMessageBox.NoButton, self)
        accept = box.addButton("Conferma", QMessageBox.AcceptRole)
        cancel = box.addButton("Annulla", QMessageBox.RejectRole)
        box.setDefaultButton(cancel)
        box.exec()
        result = box.clickedButton() is accept
        return result

    def check_duplicates(self, sends: list) -> tuple:
        """Prima di un invio: se qualche brano c'è già sull'iPhone in un altro formato (o nello stesso invio in due
        formati, phone_library.format_duplicates), un avviso con l'elenco: Invia senza questi (la scelta
        predefinita), Invia anche questi o Annulla. (si va avanti: False solo con Annulla, brani da inviare: anche
        nessuno, se erano tutti doppioni)."""
        duplicates, remaining = format_duplicates(sends, self._phone_tracks,
                                                  self._window.preferred_order())
        result = (True, sends)
        if duplicates:
            lines = []
            for track, reason in duplicates[:10]:
                artist = track.tags.artist or track.tags.album_artist
                lines.append(f"• {artist} — {track.tags.title} ({track.path.suffix[1:].upper()}): {reason}")
            if len(duplicates) > 10:
                lines.append(f"… e altri {len(duplicates) - 10}")
            text = (f"{len(duplicates)} dei {len(sends)} brani da inviare ci sono già sull'iPhone in un altro formato "
                    "(stesso artista, titolo e durata), o ci sono due volte in questo invio:\n\n" + "\n".join(lines) +
                    "\n\nInviandoli, sull'iPhone avresti la stessa canzone due volte.")
            box = QMessageBox(QMessageBox.Warning, "Brani già presenti in un altro formato", text, QMessageBox.NoButton,
                              self)
            skip = box.addButton(f"Invia senza questi ({len(remaining)} brani)", QMessageBox.AcceptRole)
            everything = box.addButton(f"Invia anche questi ({len(sends)} brani)", QMessageBox.ActionRole)
            box.addButton("Annulla", QMessageBox.RejectRole)
            box.setDefaultButton(skip)
            box.exec()
            clicked = box.clickedButton()
            if clicked is skip:
                result = (True, remaining)          # anche vuoto: si va avanti, senza invii
            elif clicked is everything:
                result = (True, sends)
            else:
                result = (False, [])
        return result

    def jobs_seconds(self, jobs: list) -> float:
        """Il tempo stimato di Applica (estimate.seconds), con gli album da ricopiare interi per la grafia."""
        sends, removes, updates, replaces, edits = self._split_jobs(jobs)
        rest, whole, _blocked = self.split_for_spelling(updates + replaces)
        taken = set()
        for phone_track, _track in whole:
            taken.add(phone_track.pid)
        update_rest = []
        for phone_track, track in updates:
            if phone_track.pid not in taken:
                update_rest.append((phone_track, track))
        tag_edits, replacements = phone_actions.plan_updates(update_rest)
        sizes, spelling_removes = self._spelling_cost(whole)
        for track in sends:
            sizes.append(estimate.file_size(track.path))
        for job in jobs:
            if job.action == RING_SEND:
                sizes.append(estimate.file_size(job.track.path))
        replaced = 0
        for _phone_track, track in replacements:
            sizes.append(estimate.file_size(track.path))
            replaced += 1
        for phone_track, track in replaces:
            if phone_track.pid not in taken:
                sizes.append(estimate.file_size(track.path))
                replaced += 1
        plan = self.send_plan(jobs)           # i file sono già tra quelli da copiare: si contano le copie vecchie
        replaced += len(plan.replaces) + len(plan.removes)
        result = estimate.seconds(sizes, removes=len(removes) + replaced + spelling_removes,
                                  edits=len(tag_edits) + len(edits))
        return result

    def jobs_notes(self, jobs: list) -> str:
        """Le righe in più della finestra di Applica: gli album da ricopiare interi per la grafia, le playlist da
        sistemare a mano dopo un rimpiazzo."""
        _sends, _removes, updates, replaces, _edits = self._split_jobs(jobs)
        plan = self.send_plan(jobs)
        replaces = replaces + plan.replaces
        _rest, whole, blocked = self.split_for_spelling(updates + replaces)
        text = self._spelling_text(whole, blocked) + self._send_plan_text(plan)
        replaced = []
        for phone_track, _track in replaces + whole:
            replaced.append(phone_track)
        automatic = playlist_reminder(replaced, from_computer=True)
        if automatic:
            text += ("\n\nI brani da ricopiare sono in playlist messe da un computer: si rifanno da sole, con i "
                     "brani nuovi al loro posto:\n" + automatic)
        reminder = playlist_reminder(replaced)
        if reminder:
            text += ("\n\nI brani da ricopiare sono in playlist fatte sul telefono: il computer non le può cambiare, "
                     "andranno sistemate a mano (alla fine te le ricordo):\n" + reminder)
        return text

    def send_plan(self, jobs: list):
        """Copia da PC a iPhone di brani che sull'iPhone ci sono già nello stesso album (o lo stesso file già
        mandato): sostituiscono la copia vecchia, con una Ricopia, invece di aggiungerne un'altra
        (phone_duplicates.send_plan). I brani dell'iPhone che hanno già un'azione in coda non si toccano due volte."""
        sends, removes, updates, replaces, edits = self._split_jobs(jobs)
        busy = set()
        for item in removes:
            busy.add(item.pid)
        for phone_track, _other in updates + replaces + edits:
            busy.add(phone_track.pid)
        result = phone_duplicates.send_plan(sends, self._phone_tracks, self._registry_paths(self._phone_tracks),
                                            busy)
        return result

    @staticmethod
    def _send_plan_text(plan) -> str:
        """La nota della finestra di Applica per le sostituzioni all'invio."""
        text = ""
        if plan.replaces:
            text += (f"\n\n{songs(len(plan.replaces))} da copiare ci sono già sull'iPhone nello stesso album: "
                     "sostituiscono la copia vecchia (prima si copia il nuovo, poi si toglie il vecchio; le playlist "
                     "messe da un computer si rifanno da sole)")
            if plan.removes:
                text += f". Si tolgono anche altre {songs(len(plan.removes))} dello stesso album"
            text += "."
        if plan.kept_old:
            text += (f"\n\n{songs(len(plan.kept_old))} da copiare ci sono già sull'iPhone nello stesso album, "
                     "acquistati o scaricati sul telefono: un computer non li può togliere, resteranno due copie.")
        return text

    @staticmethod
    def _split_jobs(jobs: list) -> tuple:
        """(da copiare [Track], da eliminare [PhoneTrack], Usa i tag [(PhoneTrack, Track)], Ricopia [(PhoneTrack,
        Track)], Cambia i tag [(PhoneTrack, valori)])."""
        sends = []
        removes = []
        updates = []
        replaces = []
        edits = []
        for job in jobs:
            if job.action == SEND:
                sends.append(job.track)
            elif job.action == DELETE:
                removes.append(job.phone)
            elif job.action == UPDATE:
                updates.append((job.phone, job.track))
            elif job.action == REPLACE:
                replaces.append((job.phone, job.track))
            elif job.action == EDIT:
                edits.append((job.phone, job.values))
        result = (sends, removes, updates, replaces, edits)
        return result

    def apply_jobs(self, jobs: list, closing: bool = False, then=None) -> None:
        """Applica le azioni scelte nella finestra di Applica (già confermate lì): prima l'avviso per i brani da
        copiare che sull'iPhone ci sono già in un altro formato (check_duplicates; non all'uscita, dove si è già
        confermato). Con "Invia senza questi" i brani lasciati fuori escono dalla coda: l'hai deciso tu, non sono un
        errore (altrimenti ogni Applica li riproporrebbe). closing: all'uscita dal programma (nessun messaggio se
        tutto riesce); then(), se c'è, alla fine."""
        sends, removes, updates, replaces, edits = self._split_jobs(jobs)
        plan = self.send_plan(jobs)       # già sull'iPhone nello stesso album: si sostituisce, non si aggiunge
        sends = plan.sends
        replaces = replaces + plan.replaces
        removes = removes + plan.removes
        ring_jobs = []
        for job in jobs:
            if job.action in RING_ACTIONS:
                ring_jobs.append(job)
        proceed = True
        if sends and not closing:
            proceed, kept = self.check_duplicates(sends)      # Annulla ferma tutto Applica
            kept_ids = set()
            for track in kept:
                kept_ids.add(id(track))
            for _phone_track, track in plan.replaces:          # le sostituzioni restano
                kept_ids.add(id(track))
            dropped = []
            remaining = []
            for job in jobs:
                if job.action == SEND and id(job.track) not in kept_ids:
                    dropped.append(job)
                else:
                    remaining.append(job)
            if proceed and dropped:
                self._window.pending_skipped([job.key for job in dropped])
                jobs = remaining
            sends = kept
        anything = bool(sends or removes or updates or replaces or edits or ring_jobs)
        if proceed and anything and (self._connected or closing):
            self._run_jobs(jobs, sends, removes, updates, replaces, edits, closing, then)
        elif proceed and anything:
            QMessageBox.information(self, "Applica", "Connetti l'iPhone per applicare le azioni in attesa.")
        elif proceed:
            self._window.statusBar().showMessage("Niente da applicare: i brani da copiare erano già sull'iPhone in "
                                                 "un altro formato", 8000)
        if closing and not (proceed and anything) and then is not None:
            then()            # niente da fare davvero: si esce lo stesso

    def _run_jobs(self, jobs: list, sends: list, removes: list, updates: list, replaces: list, edits: list,
                  closing: bool, then) -> None:
        """Le azioni tutte insieme: copia, elimina, cambia i tag, poi Usa i tag e Ricopia (gli album con la grafia
        diversa si ricopiano interi, split_for_spelling)."""
        rest, whole, _blocked = self.split_for_spelling(updates + replaces)
        taken = set()
        for phone_track, _track in whole:
            taken.add(phone_track.pid)
        update_rest = []
        for phone_track, track in updates:
            if phone_track.pid not in taken:
                update_rest.append((phone_track, track))
        replace_rest = []
        for phone_track, track in replaces:
            if phone_track.pid not in taken:
                replace_rest.append((phone_track, track))
        tag_edits, replacements = phone_actions.plan_updates(update_rest)
        replacements = replacements + replace_rest
        ring_sends = []
        ring_deletes = []
        for job in jobs:
            if job.action == RING_SEND:
                ring_sends.append(phone_ringtones.RingtoneSend(job.key, job.track.path, job.track.name,
                                                                job.track.duration_ms))
            elif job.action == RING_DELETE:
                ring_deletes.append(phone_ringtones.RingtoneDelete(job.key, job.phone))
        replaced = []
        for phone_track, _track in replacements + whole:
            replaced.append(phone_track)
        overlay = self._window.overlay
        edit_entries = list(edits) + list(tag_edits)

        def updates_action(progress, cancel):
            value = phone_actions.ActionReport()
            if edit_entries or replacements:
                value = phone_actions.update_from_pc(edit_entries, replacements, overlay, progress, cancel,
                                                     config_dir())
            return value

        spelling_and_updates = self._with_spelling(whole, updates_action)

        def action(progress, cancel):
            report = phone_actions.ActionReport()
            if sends:
                report.add(phone_actions.send_tracks(sends, overlay, progress, cancel, config_dir()))
            if removes and not cancel.is_set():
                report.add(phone_actions.delete_tracks(removes, progress, config_dir()))
            if (edit_entries or replacements or whole) and not cancel.is_set():
                report.add(spelling_and_updates(progress, cancel))
            if (ring_sends or ring_deletes) and not cancel.is_set():
                report.add(phone_ringtones.apply_ringtones(ring_sends, ring_deletes, progress, cancel))
            return report

        outcome = {"done": []}

        def after(report):
            # le azioni riuscite escono subito dalla coda (l'iPhone può aggiornare il suo elenco più tardi);
            # quelle non riuscite restano, per riprovarle
            outcome["done"] = done_jobs(jobs, report)
            keys = []
            for job in outcome["done"]:
                keys.append(job.key)
            self._window.pending_done(keys, len(jobs) - len(keys))
            self._recheck_later(outcome["done"], RECHECK_TRIES)
            if ring_sends or ring_deletes:
                QTimer.singleShot(0, self._window.ringtones_panel.after_apply)

        self._write("Applica sull'iPhone", "", action, _playlist_note(replaced), after=after, quiet=closing,
                    then=then, describe=lambda report: apply_report_text(report, outcome["done"], len(jobs)))

    def refresh(self) -> None:
        """Il pulsante Rileggi (e F5): rilegge la musica dell'iPhone, o senza iPhone rifà il confronto con il PC."""
        self._refresh_music()

    def _delete_current(self) -> None:
        """Il tasto Canc sull'elenco: Elimina dall'iPhone i brani selezionati (se nessuno lo è, quello con il
        cursore), in attesa fino ad Applica."""
        current = self._music_view.currentItem()
        if not self._music_view.selectedItems() and current is not None:
            current.setSelected(True)
        self._delete_selected()

    def _edit_current(self) -> None:
        """Il tasto E sull'elenco: Cambia i tag sui brani selezionati (se nessuno lo è, su quello con il cursore)."""
        current = self._music_view.currentItem()
        if not self._music_view.selectedItems() and current is not None:
            current.setSelected(True)
        self._edit_selected()

    def _edit_selected(self) -> None:
        self._edit_items(self._selected_phone_tracks())

    def _edit_items(self, items: list) -> None:
        """Cambia i tag sull'iPhone: il riquadro dei tag a destra (si riapre se era chiuso) con items, il cursore nel
        primo campo. Con Metti in attesa vanno in attesa fino ad Applica (_queue_tag_edit)."""
        if items:
            self._tag_box.setVisible(True)
            self._show_in_tag_panel(items)
            if self._tag_panel.focus_first_field():
                self._tag_scroll.ensureWidgetVisible(self._tag_panel.focusWidget() or self._tag_panel)

    def _queue_tag_edit(self, items: list, values: dict, also_pc: bool) -> None:
        """Metti in attesa del riquadro dei tag. Con la casella "Anche sul PC" gli stessi tag vanno sui file del PC
        associati come modifiche in sospeso (i file non cambiano)."""
        linked = self._linked_tracks(items)
        extra = ""
        if also_pc and linked:
            pairs = []
            for track in linked:
                new_tags = track.tags.copy()
                for name, value in values.items():
                    setattr(new_tags, name, _pc_value(name, value))
                pairs.append((track, new_tags))
            self._window.apply_tag_changes(pairs)
            extra = f"; sul PC gli stessi tag per {songs(len(linked))}, in sospeso (i file non cambiano)"
        self._window.queue_edits(items, values, extra)

    def _delete_selected(self) -> None:
        items = []
        for item in self._selected_phone_tracks():
            if item.from_computer:
                items.append(item)
        if items:
            self._window.queue_deletes(items)
        else:
            self._window.statusBar().showMessage("Nessun brano da eliminare: quelli scelti non sono stati messi da un "
                                                 "computer", 8000)

    def pending_changed(self) -> None:
        """La coda delle azioni in attesa è cambiata: i brani con un'azione hanno il titolo in corsivo blu e lo dicono
        nel suggerimento."""
        window = self._window
        view = self._music_view
        italic = QFont()
        italic.setItalic(True)
        for index in range(view.topLevelItemCount()):
            row = view.topLevelItem(index)
            pid = row.data(COL_TITLE, PID_ROLE)
            item = self._by_pid.get(pid)
            action = window.pending.get_phone(pid, include_edit=True) if item is not None else ""
            if not action and item is not None and item.sync_id:
                link = window.registry.get(item.sync_id)
                if link is not None and link.here:
                    action = window.pending.get(link.path)
            if action:
                row.setFont(COL_TITLE, italic)
                row.setForeground(COL_TITLE, QBrush(PENDING_COLOR))
                row.setToolTip(COL_TITLE, f"In attesa: {PENDING_NAMES.get(action, action)} (Applica)")
            elif row.font(COL_TITLE).italic():
                row.setFont(COL_TITLE, QFont())
                row.setForeground(COL_TITLE, QBrush())
                row.setToolTip(COL_TITLE, self._origin_text(item) if item is not None else "")

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
        dialog = AdoptOptionsDialog(self, len(unknown), len(selected), self._folder_for(selected or unknown),
                                    window.music_dirs(), to_read, self._connected,
                                    provider.profile.name if provider is not None else "")
        if dialog.exec():
            items = list(selected) if dialog.selected_only else unknown
            found, missing = adopt_folders(dialog.folders())
            if not found:
                if missing:
                    QMessageBox.warning(self, "Associa sorgenti", f"La cartella non c'è: {', '.join(missing)}")
                else:
                    QMessageBox.warning(self, "Associa sorgenti", "Scrivi la cartella dove cercare.")
            elif not items:
                QMessageBox.information(self, "Associa sorgenti", "Nessun brano da associare.")
            else:
                if missing:                    # una cartella della musica su un disco scollegato: le altre sì
                    window.statusBar().showMessage(f"Associa sorgenti: cartelle che non ci sono, saltate: "
                                                   f"{', '.join(missing)}", 15000)
                self._run_adopt(items, found, dialog.use_fingerprint, provider if dialog.use_ai else None,
                                dialog.selected_only)

    def _run_adopt(self, items: list, folders: list, use_fingerprint: bool, provider, replace_known: bool) -> None:
        """Cerca le sorgenti nelle cartelle (con le sottocartelle): se sono tutte dentro le cartelle aperte si usano i
        brani già letti, altrimenti si leggono."""
        window = self._window
        opened = list(window.tracks)
        for folder in folders:
            if not window.is_open(folder):
                opened = None
        registry = window.registry
        tag_cache = window.tag_cache
        read_phone = self._connected
        preferred = window.preferred_order()

        def work(progress, cancel):
            pc_tracks = []
            if opened is None:
                for folder in folders:
                    progress(0, 0, f"lettura di {folder}")
                    pc_tracks.extend(scan_folder(folder, progress, cancel, tag_cache))
                pc_tracks = window.without_hidden(pc_tracks)          # non le cartelle escluse
                window.overlay.apply(pc_tracks)
            else:
                for track in opened:
                    inside = False
                    for folder in folders:
                        if track.path.is_relative_to(folder):
                            inside = True
                    if inside:
                        pc_tracks.append(track)
            value = adoption.adopt(items, pc_tracks, registry, config_dir(), tag_cache, provider, progress, cancel,
                                   use_fingerprint, read_phone, replace_known, preferred)
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

    # ------------------------------------------------------------------ playlist per artista

    def _plan_playlists(self) -> None:
        """Legge musica e playlist dall'iPhone e prepara il piano (playlists.plan), poi lo mostra."""
        from ..playlists import plan, source_paths

        def work(progress, _cancel):
            progress(0, 0, "lettura della musica e delle playlist dell'iPhone")
            tracks, phone_playlists = iphone.list_music_app_playlists()
            registry = provenance.Registry.load(config_dir())
            value = (tracks, plan(tracks, phone_playlists, source_paths(registry)))
            return value

        self._window.runner.run("Playlist per artista", work, self._show_playlist_plan)

    def _show_playlist_plan(self, value) -> None:
        from .playlist_dialog import ACTION_TEST, TEST_NAME, PlaylistDialog
        tracks, plan = value
        self._window.set_phone_tracks(tracks, self._device_name)
        dialog = PlaylistDialog(self, plan)
        if dialog.exec():
            if dialog.action == ACTION_TEST:
                test = dialog.test_playlist()
                create = [test]
                delete = []
                text = (f"Creare sull'iPhone la playlist di prova \"{TEST_NAME}\" ({len(test.tracks)} brani)? Non "
                        "si cancella niente.")
            else:
                create = dialog.chosen()
                delete = list(plan.delete)
                text = (f"Creare {len(create)} playlist e cancellare {len(delete)} playlist messe da un computer?\n\n"
                        "Le playlist cancellate non si possono recuperare; i brani restano sull'iPhone.")
            if self._confirm("Playlist per artista", text):
                self._rebuild_playlists(create, delete)

    def _rebuild_playlists(self, create: list, delete: list) -> None:
        window = self._window

        def work(progress, cancel):
            report = phone_actions.rebuild_playlists(create, delete, progress, cancel)
            if report.created or report.deleted:
                iphone.post_sync_finished()
            progress(0, 0, "rilettura della musica dell'iPhone")
            tracks, phone_playlists = iphone.list_music_app_playlists()
            value = (report, tracks, phone_playlists)
            return value

        def done(value):
            report, tracks, phone_playlists = value
            window.set_phone_tracks(tracks, self._device_name)
            QMessageBox.information(self, "Playlist per artista", _playlist_report_text(report, phone_playlists))

        window.runner.run("Playlist sull'iPhone", work, done)

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
        preferred = window.preferred_order()

        def work(progress, cancel):
            progress(0, 0, "ricerca dei file possibili")
            value = adoption.rank_sources(item, pc_tracks, config_dir(), tag_cache, provider, read_phone, progress,
                                          cancel, preferred)
            return value

        window.runner.run("Associa sorgente", work, lambda proposals: self._choose_source(item, proposals))

    def _choose_source(self, item, proposals) -> None:
        """proposals: None se la ricerca è stata annullata (si ferma anche la coda dei brani da associare)."""
        if proposals is None:
            self._source_queue = []
            self._window.statusBar().showMessage("Associa sorgente annullata", 8000)
        else:
            self._show_sources(item, proposals)

    def _show_sources(self, item, proposals: list) -> None:
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
            if accepted and not Path(path).is_file():
                # l'elenco dei brani del PC è di prima che il file fosse spostato o rinominato
                QMessageBox.warning(self, "Associa sorgente", f"Questo file non c'è più:\n{path}\n\nForse è stato "
                                    "spostato o rinominato dopo l'apertura della cartella: premi Aggiorna nella scheda "
                                    "PC e riprova.")
                self._next_source()
            elif accepted:
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

    def _save_selected(self, items: list = None) -> None:
        """Copia da iPhone a PC: i brani scelti (o quelli selezionati), subito, dopo la scelta della cartella."""
        if items is None:
            items = self._selected_phone_tracks()
        if not items:
            QMessageBox.information(self, "Copia da iPhone a PC", "Seleziona prima uno o più brani nell'elenco.")
        elif not self._connected:
            QMessageBox.information(self, "Copia da iPhone a PC", "Connetti l'iPhone per copiarne i brani sul PC.")
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
        QMessageBox.information(self, "Copia da iPhone a PC", message)
        if self._window.is_open(target):
            self._window.reload_folder()

    # ------------------------------------------------------------------ stato e collegamento

    def _update_enabled(self) -> None:
        self._refresh_button.setEnabled(True)
        self._update_action_bar()
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

    @property
    def device_name(self) -> str:
        result = self._device_name
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
