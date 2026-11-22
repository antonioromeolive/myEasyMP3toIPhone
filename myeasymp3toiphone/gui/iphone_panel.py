"""Scheda iPhone: collegamento, la musica dell'app Musica (com'è nell'app, confrontata con il PC) e, con il tasto
destro, salva su PC, rimpiazza con la versione del PC, cambia i tag, elimina. L'invio dal PC parte dalla scheda PC.
La scrittura sull'iPhone passa per phone_actions (il servizio di sincronizzazione di Apple)."""

import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QTreeWidget, QVBoxLayout, QWidget,
)

from .. import adoption, iphone, phone_actions, provenance
from ..config import config_dir
from ..library import Track, copy_organized
from ..phone_library import DEVICE_SAME, DEVICE_STALE, describe_differences, pc_matches
from .browser import SORT_ROLE, SortableItem

DEVICE_POLL_MS = 3000   # ogni quanto si guarda se è stato collegato (o scollegato) un iPhone
DOWNLOAD_TEMP_FOLDER = ".salvataggio_iphone"
PID_ROLE = Qt.UserRole
COLUMNS = ["N.", "Sul PC", "Titolo", "Artista", "Album", "Anno", "Genere", "Durata"]
COL_NUMBER, COL_PC, COL_TITLE, COL_ARTIST, COL_ALBUM, COL_YEAR, COL_GENRE, COL_LENGTH = range(len(COLUMNS))
COLUMN_WIDTHS = {COL_NUMBER: 50, COL_PC: 60, COL_TITLE: 300, COL_ARTIST: 200, COL_ALBUM: 240, COL_YEAR: 55,
                 COL_GENRE: 110, COL_LENGTH: 60}
PC_TEXT = {DEVICE_SAME: "✔", DEVICE_STALE: "⟳"}
PC_TIP = {DEVICE_SAME: "Sul PC c'è lo stesso brano, con gli stessi tag",
          DEVICE_STALE: "Sul PC c'è lo stesso brano, ma con tag diversi:\n"}
NOT_ON_PC_TIP = "Non è nella cartella aperta sul PC (confronto per artista, album e titolo)"
MUSIC_APP_REFRESH = ("Se l'app Musica era aperta, chiudila del tutto e riaprila per vedere le modifiche (cerca "
                     "nella tua libreria, non in Apple Music).")
SYNC_WARNING = ("Non premere mai \"Sincronizza\" in iTunes o in Dispositivi Apple: con la musica messa da un altro "
                "programma, iTunes la toglierebbe dall'iPhone.")

INFO_TEXT = (
    "<b>Come funziona.</b> Qui vedi la musica dell'app <b>Musica</b> dell'iPhone, con i titoli, gli artisti e gli "
    "album che mostra l'app. La colonna <b>Sul PC</b> la confronta con la cartella aperta nella scheda PC: "
    "✔ stesso brano, ⟳ stesso brano con tag diversi, vuoto = non c'è.<br>"
    "Tasto destro su uno o più brani: <b>Salva su PC</b>, <b>Mostra nella scheda PC</b>, <b>Rimpiazza con la "
    "versione del PC</b> (per i ⟳), <b>Cambia tag</b>, <b>Elimina dall'iPhone</b>. Per mandare brani nuovi: tasto "
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
        note = QLabel(f"{len(phone_tracks)} brani. Artista e artista dell'album non si cambiano qui: sull'iPhone "
                      "rinominerebbero l'artista per tutti i suoi brani. Cambiali nella scheda PC, poi usa "
                      "<i>Rimpiazza con la versione del PC</i>. Anno o numero 0: lo svuota.")
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
        self._by_pid = {}
        self._matches = {}
        self._pc_dirty = True

        self._status = QLabel("iPhone non collegato")
        self._status.setStyleSheet("font-size: 15px; font-weight: bold;")
        self._connect_button = QPushButton("Collega iPhone")
        self._connect_button.clicked.connect(self.connect_device)
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
        search_row = QHBoxLayout()
        search_row.addWidget(self._search, 1)
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
        header = self._music_view.header()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)
        for column, width in COLUMN_WIDTHS.items():
            self._music_view.setColumnWidth(column, width)
        header.setSectionResizeMode(COL_TITLE, QHeaderView.Stretch)

        self._refresh_button = QPushButton("Aggiorna elenco")
        self._refresh_button.setToolTip("Rilegge la musica dell'app Musica dall'iPhone collegato")
        self._refresh_button.clicked.connect(self._refresh_music)
        self._save_button = QPushButton("Salva i selezionati sul PC…")
        self._save_button.clicked.connect(self._save_selected)
        self._adopt_button = QPushButton("Collega al PC…")
        self._adopt_button.setToolTip("Ritrova nella cartella aperta sul PC il file di ogni brano dell'iPhone "
                                      "(impronta dell'audio, poi regole e AI per i dubbi) e lo scrive nel registro "
                                      "della provenienza. Né i brani né i file cambiano.")
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

    def _fill_music(self) -> None:
        self._matches = pc_matches(self._phone_tracks, self._window.tracks)
        self._pc_dirty = False
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
                COL_TITLE: (tags.title, tags.title.lower()),
                COL_ARTIST: (tags.artist, item.display_artist.lower()),
                COL_ALBUM: (tags.album, tags.album.lower()),
                COL_YEAR: (tags.year, tags.year),
                COL_GENRE: (tags.genre, tags.genre.lower()),
                COL_LENGTH: (_format_length(item.length), int(item.length)),
            }
            texts = []
            keys = []
            for column in range(len(COLUMNS)):
                text, key = cells[column]
                texts.append(text)
                keys.append(key)
            row = SortableItem(texts, keys)
            row.setData(COL_TITLE, PID_ROLE, item.pid)
            row.setToolTip(COL_TITLE, self._origin_text(item))
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
        result += "\n" + item.remote_path
        return result

    def _set_pc_cell(self, row, pid: int) -> None:
        match = self._matches.get(pid)
        if match is None:
            row.setText(COL_PC, "")
            row.setToolTip(COL_PC, NOT_ON_PC_TIP)
            row.setData(COL_PC, SORT_ROLE, 0)
            row.setForeground(COL_PC, QBrush())
        else:
            status, _track, found = match
            row.setText(COL_PC, PC_TEXT[status])
            tip = PC_TIP[status]
            if found:
                tip += describe_differences(found)
            row.setToolTip(COL_PC, tip)
            row.setData(COL_PC, SORT_ROLE, 2 if status == DEVICE_SAME else 1)
            color = QColor(30, 140, 60) if status == DEVICE_SAME else QColor(220, 140, 0)
            row.setForeground(COL_PC, QBrush(color))
        row.setTextAlignment(COL_PC, Qt.AlignCenter)

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
        self._matches = pc_matches(self._phone_tracks, self._window.tracks)
        self._pc_dirty = False
        view = self._music_view
        view.setSortingEnabled(False)
        for index in range(view.topLevelItemCount()):
            row = view.topLevelItem(index)
            self._set_pc_cell(row, row.data(COL_TITLE, PID_ROLE))
        view.setSortingEnabled(True)

    def _apply_search(self) -> None:
        words = self._search.text().casefold().split()
        shown = 0
        view = self._music_view
        for index in range(view.topLevelItemCount()):
            row = view.topLevelItem(index)
            text = " ".join([row.text(COL_TITLE), row.text(COL_ARTIST), row.text(COL_ALBUM)]).casefold()
            visible = True
            for word in words:
                if word not in text:
                    visible = False
            row.setHidden(not visible)
            if visible:
                shown += 1
        total = view.topLevelItemCount()
        if words:
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
        """(brano dell'iPhone, brano del PC) per i brani selezionati con ⟳."""
        result = []
        for item in items:
            match = self._matches.get(item.pid)
            if match is not None and match[0] == DEVICE_STALE and item.from_computer:
                result.append((item, match[1]))
        return result

    def _show_menu(self, position) -> None:
        items = self._selected_phone_tracks()
        if items:
            ready = self._connected and not self._window.runner.is_busy
            on_pc = []
            for item in items:
                match = self._matches.get(item.pid)
                if match is not None:
                    on_pc.append(match[1])
            writable = []
            for item in items:
                if item.from_computer:
                    writable.append(item)
            stale = self._stale_pairs(items)
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
                        action.setToolTip("Collega l'iPhone")
                    action.triggered.connect(slot)
            menu.setToolTipsVisible(True)
            menu.exec(self._music_view.viewport().mapToGlobal(position))

    def _refresh_music(self) -> None:
        if self._connected and not self._window.runner.is_busy:
            def work(progress, _cancel):
                progress(0, 0, "lettura della musica dell'app Musica")
                value = iphone.list_music_app()
                return value

            self._window.runner.run("Lettura dell'iPhone", work, self._music_read)

    def _music_read(self, tracks: list) -> None:
        self._window.set_phone_tracks(tracks, self._device_name)

    # ------------------------------------------------------------------ scrittura sull'iPhone

    def _write(self, title: str, verb: str, action) -> None:
        """Esegue action(progress, cancel) -> ActionReport, poi rilegge la musica dell'iPhone e mostra l'esito."""
        def work(progress, cancel):
            report = action(progress, cancel)
            progress(0, 0, "rilettura della musica dell'iPhone")
            tracks = iphone.list_music_app()
            registry = provenance.Registry.load(config_dir())
            value = (report, tracks, registry)
            return value

        def done(value):
            report, tracks, registry = value
            self._window.registry = registry
            self._window.set_phone_tracks(tracks, self._device_name)
            message = _report_text(report, verb)
            if report.done:
                message += "\n\n" + MUSIC_APP_REFRESH
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
        text = (f"Rimpiazzare {len(pairs)} brani dell'iPhone con la versione del PC?\n\n"
                "Prima si invia la versione del PC, poi si toglie quella vecchia. I brani rimpiazzati perdono "
                "il conteggio degli ascolti e spariscono dalle playlist fatte sull'iPhone.")
        if self._confirm("Rimpiazza", text):
            overlay = self._window.overlay

            def action(progress, cancel):
                value = phone_actions.replace_tracks(pairs, overlay, progress, cancel, config_dir())
                return value

            self._write("Rimpiazzo sull'iPhone", "rimpiazzati", action)

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

                def action(progress, _cancel):
                    value = phone_actions.edit_tracks(items, values, progress)
                    return value

                self._write("Cambia tag sull'iPhone", "modificati", action)

    def _delete_selected(self) -> None:
        items = []
        for item in self._selected_phone_tracks():
            if item.from_computer:
                items.append(item)
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
        window = self._window
        if not window.tracks:
            QMessageBox.information(self, "Collega al PC", "Apri prima nella scheda PC la cartella con la tua musica.")
        else:
            unknown = 0
            known_prints = provenance.PhoneFingerprints(config_dir())
            to_read = 0
            for item in self._phone_tracks:
                if item.from_computer and window.registry.get(item.sync_id) is None:
                    unknown += 1
                    if not known_prints.get(item.remote_path, item.size):
                        to_read += 1
            provider = self._ai_provider()
            minutes = max(1, round(to_read * 0.25 / 60)) if to_read else 0
            text = (f"Collegare {unknown} brani dell'iPhone ai file della cartella aperta ({len(window.tracks)} "
                    "brani)?\n\n")
            if to_read:
                text += (f"Prima legge l'impronta dell'audio di {to_read} brani dall'iPhone: circa {minutes} minuti. "
                         "Puoi annullare e riprendere: quelle già lette si ricordano.\n\n")
            if provider is not None:
                text += f"I casi dubbi li confronta l'AI ({provider.profile.name}).\n\n"
            else:
                text += "I casi dubbi te li mostro da controllare (l'AI della scansione è spenta).\n\n"
            text += "Alla fine vedi tutto prima di confermare; i brani e i file non cambiano."
            if QMessageBox.question(self, "Collega al PC", text) == QMessageBox.Yes:
                phone_tracks = list(self._phone_tracks)
                pc_tracks = list(window.tracks)
                registry = window.registry
                tag_cache = window.tag_cache

                def work(progress, cancel):
                    value = adoption.adopt(phone_tracks, pc_tracks, registry, config_dir(), tag_cache, provider,
                                           progress, cancel)
                    return value

                window.runner.run("Collegamento al PC", work, self._adopted)

    def _adopted(self, outcome) -> None:
        from .adoption_dialog import AdoptionDialog
        window = self._window
        if outcome.cancelled:
            QMessageBox.information(self, "Collega al PC", "Interrotto. Le impronte già lette sono ricordate: "
                                    "riprendi quando vuoi con Collega al PC.")
        else:
            dialog = AdoptionDialog(self, outcome)
            if dialog.exec():
                chosen = dialog.chosen()
                registry = window.registry
                for proposal in chosen:
                    registry.record(adoption.link_for(proposal, window.overlay,
                                                      window.tag_cache.fingerprint(proposal.pc.path)))

                def work(progress, _cancel):
                    progress(0, 0, "registro della provenienza sull'iPhone")
                    iphone.store_registry(config_dir(), registry)
                    value = len(chosen)
                    return value

                def done(count):
                    self._fill_music()
                    QMessageBox.information(self, "Collega al PC", f"{count} brani collegati ai file del PC.")

                window.runner.run("Registro della provenienza", work, done)

    # ------------------------------------------------------------------ salva su PC

    def _save_selected(self) -> None:
        items = self._selected_phone_tracks()
        if not items:
            QMessageBox.information(self, "Salva su PC", "Seleziona prima uno o più brani nell'elenco.")
        elif not self._connected:
            QMessageBox.information(self, "Salva su PC", "Collega l'iPhone per copiarne i brani sul PC.")
        else:
            start = str(self._window.library_dir())
            folder = QFileDialog.getExistingDirectory(
                self, "Dove salvare i brani (in cartelle Artista/Album)", start)
            if folder:
                self._save_to(items, Path(folder))

    def _save_to(self, items: list, target: Path) -> None:
        """Ogni brano si scarica in una cartella temporanea dentro target e poi va in Artista/Album (Anno)/NN -
        Titolo, con i nomi che mostra l'app Musica. Solo file nuovi: un file già presente non si sostituisce mai."""
        def work(progress, cancel):
            temp = target / DOWNLOAD_TEMP_FOLDER
            try:
                transfer, downloaded = iphone.download_music(items, temp, progress, cancel)
                tracks = []
                for item, local in downloaded:
                    tracks.append(Track(path=local, tags=item.tags.copy(), length=item.length))
                copy_report = copy_organized(tracks, target, move=True, progress=progress, cancel=cancel,
                                             overwrite=False)
            finally:
                shutil.rmtree(temp, ignore_errors=True)
            value = (transfer, copy_report, target)
            return value

        self._window.runner.run("Salvataggio dall'iPhone", work, self._after_save)

    def _after_save(self, value) -> None:
        transfer, copy_report, target = value
        message = (f"Copiati dall'iPhone: {len(transfer.done)}\n"
                   f"Nella cartella {target}: {copy_report.summary()}")
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
        self._refresh_button.setEnabled(self._connected)
        self._save_button.setEnabled(self._connected)
        self._adopt_button.setEnabled(self._connected)

    @property
    def connected(self) -> bool:
        result = self._connected
        return result

    def _check_device(self) -> None:
        """Ogni pochi secondi: un iPhone appena collegato si collega da solo (la prima volta l'iPhone chiede
        "Autorizza"), uno scollegato si segna come tale. Senza driver Apple lo dice una volta."""
        present = iphone.device_present()
        if present is None:
            if not self._driver_warned:
                self._driver_warned = True
                self._status.setText("Driver Apple mancante: installa l'app gratuita \"Dispositivi Apple\" dal "
                                     "Microsoft Store (oppure iTunes)")
        elif not present:
            self._auto_tried = False
            if self._connected:
                self._connected = False
                self._status.setText("iPhone scollegato")
                self._update_enabled()
                self._window.statusBar().showMessage("iPhone scollegato", 5000)
            elif self._driver_warned or self._status.text() == "iPhone non collegato":
                self._driver_warned = False
                self._status.setText("Collega l'iPhone con il cavo USB e sbloccalo")
        elif not self._connected and not self._auto_tried and not self._window.runner.is_busy:
            self._auto_tried = True
            self._status.setText("iPhone rilevato: collegamento… se l'iPhone lo chiede, tocca \"Autorizza\" e "
                                 "inserisci il codice")
            self._window.statusBar().showMessage("iPhone rilevato: collegamento in corso", 5000)
            self.connect_device(auto=True)

    def _show_error(self, message: str) -> None:
        self._connected = False
        self._status.setText("iPhone non collegato")
        self._update_enabled()
        QMessageBox.warning(self, "iPhone", message)

    def _show_auto_error(self, message: str) -> None:
        """Il collegamento automatico non riuscito non apre finestre: lo dice qui; "Collega iPhone" riprova."""
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
        self._window.runner.run("Collegamento iPhone", work, self._connected_ok, on_error)

    def _connected_ok(self, value) -> None:
        info, tracks, registry = value
        self._window.registry = registry
        self._connected = True
        self._device_name = info.name
        self._status.setText("Collegato: " + info.label())
        self._window.statusBar().showMessage("iPhone collegato: " + info.label(), 8000)
        self._update_enabled()
        self._window.set_phone_tracks(tracks, info.name)
