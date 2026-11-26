# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La scheda Suonerie: a sinistra i .m4r della cartella delle suonerie del PC (creati con Crea una suoneria o già
presenti), a destra le suonerie dell'iPhone.

Verso l'iPhone (Invia come suoneria, Elimina dall'iPhone) tutto va in attesa e parte con Applica, come per la musica.
Copia da iPhone a PC è subito e crea solo file nuovi. Rinomina e Sposta nel cestino valgono solo per i .m4r della
cartella delle suonerie, dopo una conferma."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QGroupBox, QHBoxLayout, QInputDialog, QLabel, QMenu, QMessageBox, QPushButton,
    QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .. import phone_ringtones, ringtones
from ..i18n import tr
from ..overlay import path_key
from ..pending import RING_DELETE, RING_SEND
from .apply_dialog import ringtones_text
from .file_actions import add_file_entries
from .ringtone_dialog import Player

PENDING_COLOR = QColor(40, 110, 230)
SAME_COLOR = QColor(30, 140, 60)
ORIGIN_NAMES = {phone_ringtones.ORIGIN_COMPUTER: "messa da un computer",
                phone_ringtones.ORIGIN_PHONE: "fatta sull'iPhone",
                phone_ringtones.ORIGIN_LEFTOVER: "resto, non attiva"}
ORIGIN_TIPS = {phone_ringtones.ORIGIN_COMPUTER: "Inviata da un computer: si toglie con Elimina dall'iPhone",
               phone_ringtones.ORIGIN_PHONE: "Fatta sull'iPhone (GarageBand, app File): un computer non la può "
                                             "togliere, la puoi copiare sul PC",
               phone_ringtones.ORIGIN_LEFTOVER: "Un file rimasto nella cartella delle suonerie dell'iPhone che nessun "
                                                "elenco registra: non è tra le suonerie che l'iPhone mostra. La puoi "
                                                "copiare sul PC"}
PATH_ROLE = Qt.UserRole
INFO_TEXT = (
    "<b>Le suonerie.</b> A sinistra i file <b>.m4r</b> della cartella delle suonerie del PC: li crei con <b>Crea una "
    "suoneria…</b> (tasto destro su un brano nella scheda PC o iPhone) o ce li metti tu. <b>Invia come suoneria (PC → "
    "iPhone)</b> li mette in attesa: partono con <b>Applica</b>, come la musica. A destra le suonerie dell'iPhone: "
    "<b>Copia da iPhone a PC</b> le salva nella cartella delle suonerie (file nuovi); <b>Elimina dall'iPhone</b> "
    "toglie quelle messe da un computer (in attesa fino ad Applica). Sull'iPhone le trovi in Impostazioni → Suoni e "
    "feedback aptico → Suoneria, in cima all'elenco.")


class RingtonesPanel(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self._window = window
        self._pc = []                 # ringtones.RingtoneFile della cartella
        self._by_key = {}             # path_key -> RingtoneFile
        self._phone = None            # [PhoneRingtone] lette dall'iPhone; None = non ancora lette
        self._phone_read_for = ""     # il nome dell'iPhone da cui sono state lette
        self._player = Player(lambda _seconds: None, lambda: None,
                              lambda message: QMessageBox.warning(self, tr("Ascolta"), message))

        info = QLabel(INFO_TEXT)
        info.setWordWrap(True)
        info.setTextFormat(Qt.RichText)

        self._folder_label = QLabel()
        self._folder_label.setWordWrap(True)
        self._folder_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        choose = QPushButton("Scegli la cartella…")
        choose.setToolTip("La cartella delle suonerie (anche in Impostazioni → Suonerie)")
        choose.clicked.connect(self.choose_folder)
        reread = QPushButton("Rileggi")
        reread.clicked.connect(self.refresh_pc)
        self._pc_view = self._tree(["Nome", "Durata", "Sull'iPhone", "File"], (260, 60, 160, 260))
        self._pc_view.customContextMenuRequested.connect(self._pc_menu)
        self._pc_view.itemSelectionChanged.connect(self._update_buttons)
        self._send_button = QPushButton("Invia come suoneria (PC → iPhone)")
        self._send_button.setProperty("role", "go")
        self._send_button.clicked.connect(lambda: self.queue_send(self._selected_pc()))
        self._listen_button = QPushButton("Ascolta")
        self._listen_button.clicked.connect(self._listen)
        self._rename_button = QPushButton("Rinomina…")
        self._rename_button.clicked.connect(self._rename)
        self._trash_button = QPushButton("Sposta nel cestino…")
        self._trash_button.clicked.connect(self._trash)
        pc_top = QHBoxLayout()
        pc_top.addWidget(self._folder_label, 1)
        pc_top.addWidget(choose)
        pc_top.addWidget(reread)
        pc_buttons = QHBoxLayout()
        for button in (self._send_button, self._listen_button, self._rename_button, self._trash_button):
            pc_buttons.addWidget(button)
        pc_buttons.addStretch(1)
        pc_box = QGroupBox("Sul PC: la cartella delle suonerie")
        pc_layout = QVBoxLayout(pc_box)
        pc_layout.addLayout(pc_top)
        pc_layout.addWidget(self._pc_view, 1)
        pc_layout.addLayout(pc_buttons)

        self._phone_label = QLabel()
        self._phone_label.setWordWrap(True)
        self._phone_read = QPushButton("Leggi le suonerie dell'iPhone")
        self._phone_read.clicked.connect(self.refresh_phone)
        self._phone_view = self._tree(["Nome", "Durata", "Specie", "Sul PC", "File sull'iPhone"],
                                      (240, 60, 140, 60, 260))
        self._phone_view.customContextMenuRequested.connect(self._phone_menu)
        self._phone_view.itemSelectionChanged.connect(self._update_buttons)
        self._save_button = QPushButton("Copia da iPhone a PC")
        self._save_button.clicked.connect(lambda: self.save_to_pc(self._selected_phone()))
        self._delete_button = QPushButton("Elimina dall'iPhone")
        self._delete_button.clicked.connect(lambda: self.queue_delete(self._selected_phone()))
        phone_top = QHBoxLayout()
        phone_top.addWidget(self._phone_label, 1)
        phone_top.addWidget(self._phone_read)
        phone_buttons = QHBoxLayout()
        phone_buttons.addWidget(self._save_button)
        phone_buttons.addWidget(self._delete_button)
        phone_buttons.addStretch(1)
        phone_box = QGroupBox("Sull'iPhone")
        phone_layout = QVBoxLayout(phone_box)
        phone_layout.addLayout(phone_top)
        phone_layout.addWidget(self._phone_view, 1)
        phone_layout.addLayout(phone_buttons)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(pc_box)
        splitter.addWidget(phone_box)
        splitter.setSizes([600, 600])
        layout = QVBoxLayout(self)
        layout.addWidget(info)
        layout.addWidget(splitter, 1)
        self.refresh_pc()
        self._fill_phone()

    @staticmethod
    def _tree(headers: list, widths: tuple) -> QTreeWidget:
        tree = QTreeWidget()
        tree.setHeaderLabels(headers)
        tree.setRootIsDecorated(False)
        tree.setUniformRowHeights(True)
        tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.setSortingEnabled(True)
        tree.sortByColumn(0, Qt.AscendingOrder)
        for column, width in enumerate(widths):
            tree.setColumnWidth(column, width)
        return tree

    # ------------------------------------------------------------------ la cartella del PC

    def folder(self):
        result = self._window.app_settings.ringtone_path()
        return result

    def choose_folder(self):
        """La finestra per scegliere la cartella delle suonerie; restituisce la cartella (o None se annullata)."""
        settings = self._window.app_settings
        start = str(self.folder() or self._window.library_dir())
        chosen = QFileDialog.getExistingDirectory(self, "La cartella delle suonerie", start)
        result = None
        if chosen:
            settings.ringtone_folder = chosen
            self._window.save_settings()
            self._window.ringtone_folder_changed()
            result = Path(chosen)
        return result

    def ensure_folder(self):
        """La cartella delle suonerie; se non è ancora stata scelta, la si sceglie ora (None se annullato)."""
        result = self.folder()
        if result is None:
            QMessageBox.information(self, tr("Suonerie"), tr("Scegli prima la cartella delle suonerie: lì vanno le "
                                                             "suonerie create e quelle copiate dall'iPhone."))
            result = self.choose_folder()
        return result

    def refresh_pc(self) -> None:
        folder = self.folder()
        if folder is None:
            self._folder_label.setText(tr("<i>Cartella delle suonerie non ancora scelta</i>"))
        elif not folder.is_dir():
            self._folder_label.setText(tr(f"<b>{folder}</b> (non c'è ancora: si crea con la prima suoneria)"))
        else:
            self._folder_label.setText(f"<b>{folder}</b>")
        self._pc = ringtones.list_folder(folder)
        self._by_key = {}
        for item in self._pc:
            self._by_key[path_key(item.path)] = item
        self._reconcile()
        self._fill_pc()

    def pc_ringtone(self, path) -> ringtones.RingtoneFile:
        """Il .m4r (nome e durata) dall'ultimo elenco, o letto ora."""
        result = self._by_key.get(path_key(path))
        if result is None:
            result = ringtones.read_ringtone(Path(path))
            self._by_key[path_key(path)] = result
        return result

    def on_phone(self, path) -> bool:
        """La suoneria del PC c'è già sull'iPhone (stesso nome, durata entro 1 s); False senza l'elenco."""
        result = False
        if self._phone is not None:
            item = self.pc_ringtone(path)
            for ringtone in self._phone:
                if ringtone.origin != phone_ringtones.ORIGIN_LEFTOVER and ringtones.same_ringtone(
                        item.name, item.duration_ms, ringtone.name, ringtone.duration_ms):
                    result = True
        return result

    def _on_pc(self, ringtone) -> bool:
        result = False
        for item in self._pc:
            if ringtones.same_ringtone(item.name, item.duration_ms, ringtone.name, ringtone.duration_ms):
                result = True
        return result

    def _fill_pc(self) -> None:
        view = self._pc_view
        view.setSortingEnabled(False)
        view.clear()
        italic = QFont()
        italic.setItalic(True)
        pending = self._window.pending
        rows = []
        for item in self._pc:
            action = pending.ringtone_action(item.path)
            if action == RING_SEND:
                state = tr("＋ in attesa (Applica)")
            elif self.on_phone(item.path):
                state = "✔"
            elif item.error:
                state = tr(f"non si invia: {item.error}")
            elif item.duration_ms > ringtones.MAX_SECONDS * 1000 + 500:
                state = tr("troppo lunga (max 40 s)")
            else:
                state = ""
            row = QTreeWidgetItem([item.name, ringtones.format_ms(item.duration_ms), state, item.path.name])
            row.setData(0, PATH_ROLE, str(item.path))
            row.setToolTip(3, str(item.path))
            if action:
                row.setFont(0, italic)
                row.setForeground(0, QBrush(PENDING_COLOR))
            elif state == "✔":
                row.setForeground(2, QBrush(SAME_COLOR))
            rows.append(row)
        view.addTopLevelItems(rows)
        view.setSortingEnabled(True)
        self._update_buttons()

    def _selected_pc(self) -> list:
        result = []
        for row in self._pc_view.selectedItems():
            result.append(self.pc_ringtone(row.data(0, PATH_ROLE)))
        return result

    # ------------------------------------------------------------------ l'iPhone

    def refresh_phone(self) -> None:
        """Legge le suonerie dell'iPhone (a iPhone connesso e libero)."""
        panel = self._window.iphone_panel
        if not panel.connected:
            QMessageBox.information(self, tr("Suonerie"), tr("Connetti l'iPhone per leggerne le suonerie."))
        elif not self._window.runner.is_busy:
            def work(progress, _cancel):
                progress(0, 0, "lettura delle suonerie dell'iPhone")
                value = phone_ringtones.list_ringtones()
                return value

            self._window.runner.run("Suonerie dell'iPhone", work, self._phone_listed)

    def _phone_listed(self, items: list) -> None:
        self._phone = list(items)
        self._phone_read_for = self._window.iphone_panel.device_name
        self._reconcile()
        self._fill_phone()
        self._fill_pc()

    def tab_shown(self) -> None:
        """La scheda è stata aperta: con l'iPhone connesso e le suonerie non ancora lette, si leggono."""
        panel = self._window.iphone_panel
        if panel.connected and (self._phone is None or self._phone_read_for != panel.device_name):
            self.refresh_phone()
        else:
            self._fill_phone()

    def _fill_phone(self) -> None:
        view = self._phone_view
        view.setSortingEnabled(False)
        view.clear()
        if self._phone is None:
            self._phone_label.setText(tr("Suonerie dell'iPhone non ancora lette."))
        else:
            self._phone_label.setText(tr(f"{len(self._phone)} suonerie su {self._phone_read_for}"))
            italic = QFont()
            italic.setItalic(True)
            pending = self._window.pending
            rows = []
            for ringtone in self._phone:
                row = QTreeWidgetItem([ringtone.name, ringtones.format_ms(ringtone.duration_ms),
                                       tr(ORIGIN_NAMES.get(ringtone.origin, ringtone.origin)),
                                       "✔" if self._on_pc(ringtone) else "", ringtone.path])
                row.setData(0, PATH_ROLE, ringtone.path)
                row.setToolTip(2, tr(ORIGIN_TIPS.get(ringtone.origin, "")))
                if pending.phone_ringtone_action(ringtone.file_name) == RING_DELETE:
                    row.setFont(0, italic)
                    row.setForeground(0, QBrush(PENDING_COLOR))
                    row.setToolTip(0, tr("In attesa: da eliminare dall'iPhone (Applica)"))
                elif ringtone.origin == phone_ringtones.ORIGIN_LEFTOVER:
                    for column in range(5):
                        row.setForeground(column, QBrush(QColor(140, 140, 140)))
                rows.append(row)
            view.addTopLevelItems(rows)
        view.setSortingEnabled(True)
        self._update_buttons()

    def _selected_phone(self) -> list:
        by_path = {}
        for ringtone in self._phone or []:
            by_path[ringtone.path] = ringtone
        result = []
        for row in self._phone_view.selectedItems():
            ringtone = by_path.get(row.data(0, PATH_ROLE))
            if ringtone is not None:
                result.append(ringtone)
        return result

    # ------------------------------------------------------------------ azioni

    def _update_buttons(self) -> None:
        pc = self._selected_pc() if hasattr(self, "_send_button") else []
        sendable = self._sendable(pc)
        self._send_button.setEnabled(bool(sendable))
        self._listen_button.setEnabled(len(pc) == 1 and Player.available())
        self._rename_button.setEnabled(len(pc) == 1)
        self._trash_button.setEnabled(bool(pc))
        phone = self._selected_phone()
        connected = self._window.iphone_panel.connected
        self._save_button.setEnabled(bool(phone) and connected and not self._window.runner.is_busy)
        removable = [ringtone for ringtone in phone if ringtone.removable]
        self._delete_button.setEnabled(bool(removable))
        self._phone_read.setEnabled(connected)

    def _sendable(self, items: list) -> list:
        result = []
        for item in items:
            if not item.error and item.duration_ms <= ringtones.MAX_SECONDS * 1000 + 500:
                result.append(item)
        return result

    def queue_send(self, items: list) -> None:
        """Invia come suoneria (PC → iPhone): in attesa fino ad Applica."""
        sendable = self._sendable(items)
        for item in sendable:
            self._window.pending.set_ringtone(item.path, RING_SEND)
        skipped = len(items) - len(sendable)
        message = tr(f"Appena aggiunte: {ringtones_text(len(sendable))} da inviare da PC a iPhone.") if sendable else ""
        if skipped:
            message += tr(f" {skipped} non si possono inviare (non AAC o più lunghe di 40 s).")
        self._window.pending_changed(message.strip())

    def queue_delete(self, items: list) -> None:
        """Elimina dall'iPhone le suonerie messe da un computer: in attesa fino ad Applica."""
        count = 0
        for ringtone in items:
            if ringtone.removable:
                self._window.pending.set_phone_ringtone(ringtone, RING_DELETE)
                count += 1
        message = tr(f"Appena aggiunte: {ringtones_text(count)} da eliminare dall'iPhone. I file del PC non cambiano.") \
            if count else tr("Nessuna suoneria da eliminare: quelle scelte non sono state messe da un computer")
        self._window.pending_changed(message)

    def _listen(self) -> None:
        items = self._selected_pc()
        ffmpeg = ringtones.find_ffmpeg(self._window.app_settings.ffmpeg_path)
        if len(items) == 1 and ffmpeg is None:
            QMessageBox.information(self, tr("Ascolta"), tr(ringtones.FFMPEG_MISSING))
        elif len(items) == 1:
            item = items[0]
            self._player.play(ffmpeg, item.path, 0.0, max(0.5, item.duration_ms / 1000), 0.0, 0.0)

    def _rename(self) -> None:
        items = self._selected_pc()
        if len(items) == 1:
            item = items[0]
            text, accepted = QInputDialog.getText(self, tr("Rinomina"), tr(f"Il nuovo nome del file {item.path.name} "
                                                                           "(senza .m4r):"), text=item.path.stem)
            if accepted and text.strip() and text.strip() != item.path.stem:
                try:
                    target = ringtones.rename_ringtone(item.path, self.folder(), text.strip())
                    if self._window.pending.ringtone_action(item.path):
                        self._window.pending.set_ringtone(item.path, "")
                        self._window.pending.set_ringtone(target, RING_SEND)
                        self._window.pending_changed()
                    self._window.statusBar().showMessage(tr(f"Rinominato in {target.name}"), 8000)
                except (ringtones.RingtoneError, OSError) as exc:
                    QMessageBox.warning(self, tr("Rinomina"), str(exc))
                self.refresh_pc()

    def _trash(self) -> None:
        items = []
        for item in self._selected_pc():
            if ringtones.in_folder(item.path, self.folder()):
                items.append(item)
        if items:
            names = []
            for item in items[:15]:
                names.append(f"• {item.path.name}")
            if len(items) > 15:
                names.append(tr(f"… e altri {len(items) - 15}"))
            answer = QMessageBox.question(self, tr("Sposta nel cestino"),
                                          tr(f"Spostare nel Cestino di Windows {len(items)} file della cartella delle "
                                             "suonerie?") + "\n\n" + "\n".join(names) + "\n\n" +
                                          tr("Si recuperano dal Cestino. Sull'iPhone non cambia niente."),
                                          QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer == QMessageBox.Yes:
                failed = []
                for item in items:
                    if QFile.moveToTrash(str(item.path)):
                        self._window.pending.set_ringtone(item.path, "")
                    else:
                        failed.append(item.path.name)
                self._window.pending_changed()
                if failed:
                    QMessageBox.warning(self, tr("Sposta nel cestino"),
                                        tr("Non spostati nel Cestino:") + "\n" + "\n".join(failed))
                self.refresh_pc()

    def save_to_pc(self, items: list) -> None:
        """Copia da iPhone a PC: subito, come file nuovi nella cartella delle suonerie."""
        panel = self._window.iphone_panel
        if items and not panel.connected:
            QMessageBox.information(self, tr("Copia da iPhone a PC"), tr("Connetti l'iPhone per copiarne le suonerie "
                                                                         "sul PC."))
        elif items and not self._window.runner.is_busy:
            folder = self.ensure_folder()
            if folder is not None:
                def work(progress, cancel):
                    value = phone_ringtones.download_ringtones(items, folder, progress, cancel)
                    return value

                self._window.runner.run("Copia delle suonerie da iPhone a PC", work, self._saved)

    def _saved(self, value) -> None:
        saved, errors = value
        message = tr(f"Copiate da iPhone a PC: {ringtones_text(len(saved))}, nella cartella {self.folder()}.")
        if errors:
            lines = []
            for name, reason in errors[:10]:
                lines.append(f"• {name}: {reason}")
            message += "\n\n" + tr("Non copiate:") + "\n" + "\n".join(lines)
        QMessageBox.information(self, tr("Copia da iPhone a PC"), message)
        self.refresh_pc()

    def pending_changed(self) -> None:
        self._fill_pc()
        self._fill_phone()

    def _reconcile(self) -> None:
        phone = self._phone
        removed = self._window.pending.reconcile_ringtones(self.on_phone, phone)
        if removed:
            self._window.pending_changed()

    def after_apply(self) -> None:
        """Dopo Applica con azioni sulle suonerie: rilegge la cartella e, se si può, l'iPhone."""
        self.refresh_pc()
        if self._window.iphone_panel.connected and not self._window.runner.is_busy:
            self.refresh_phone()

    # ------------------------------------------------------------------ menu

    def _pc_menu(self, position) -> None:
        items = self._selected_pc()
        if items:
            menu = QMenu(self)
            send = menu.addAction(self._send_button.text())
            send.setEnabled(bool(self._sendable(items)))
            send.triggered.connect(lambda: self.queue_send(items))
            listen = menu.addAction("Ascolta")
            listen.setEnabled(len(items) == 1 and Player.available())
            listen.triggered.connect(self._listen)
            menu.addSeparator()
            rename = menu.addAction("Rinomina…")
            rename.setEnabled(len(items) == 1)
            rename.triggered.connect(self._rename)
            trash = menu.addAction("Sposta nel cestino…")
            trash.triggered.connect(self._trash)
            menu.addSeparator()
            paths = []
            for item in items:
                paths.append(item.path)
            add_file_entries(menu, paths, lambda text: self._window.statusBar().showMessage(text, 8000))
            menu.exec(self._pc_view.viewport().mapToGlobal(position))

    def _phone_menu(self, position) -> None:
        items = self._selected_phone()
        if items:
            menu = QMenu(self)
            save = menu.addAction(f"Copia {len(items)} suonerie da iPhone a PC" if len(items) != 1 else
                                  "Copia la suoneria da iPhone a PC")
            save.setEnabled(self._window.iphone_panel.connected and not self._window.runner.is_busy)
            save.triggered.connect(lambda: self.save_to_pc(items))
            removable = [ringtone for ringtone in items if ringtone.removable]
            delete = menu.addAction(f"Elimina dall'iPhone ({len(removable)})" if removable else
                                    "Elimina dall'iPhone: solo quelle messe da un computer")
            delete.setEnabled(bool(removable))
            delete.triggered.connect(lambda: self.queue_delete(removable))
            menu.exec(self._phone_view.viewport().mapToGlobal(position))

    def iphone_connection_changed(self) -> None:
        self._update_buttons()
