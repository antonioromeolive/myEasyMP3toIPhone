# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La linguetta Controlli, sotto: i risultati per album. Ogni album ha i suoi problemi (con Cosa fare) e, sotto, le
correzioni proposte, una riga per brano e campo (ora → diventa), con una casella; la casella dell'album e quella del
problema accendono o spengono tutte le loro righe. Applica le correzioni scelte le manda dalla parte giusta
(check_flow.plan_apply): PC e iPhone per i brani collegati, solo PC, solo iPhone (sempre in attesa)."""

from __future__ import annotations

from html import escape

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QBrush, QColor, QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QMenu,
    QMessageBox,
    QPushButton, QSplitter, QStyle, QTextBrowser, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from ..check_flow import FIELD_LABELS, OTHER_KEY, SIDE_BOTH, SIDE_LABELS, SIDE_PC, SIDE_PHONE, plan_apply
from ..i18n import tr
from ..pending import UPDATE
from ..scan import ORIGIN_AI, SEVERITY_HIGH, SEVERITY_MEDIUM, advice
from .pc_write import offer_pc_write, shown_value

COLUMNS = ["Album, problema, brano", "Dove", "Campo", "Ora", "Diventa", "Gravità", "Origine"]
COL_NAME, COL_SIDE, COL_FIELD, COL_OLD, COL_NEW, COL_SEVERITY, COL_ORIGIN = range(len(COLUMNS))
KIND_ROLE = Qt.UserRole           # ROW_ALBUM, ROW_PROBLEM, ROW_FIX
ROW_ALBUM = "riga_album"
ROW_PROBLEM = "riga_problema"
ROW_FIX = "riga_correzione"
REF_ROLE = Qt.UserRole + 1        # l'indice nell'elenco degli album, dei problemi o delle righe
GREEN = QColor(30, 140, 60)
GREY = QColor(130, 130, 130)
SIDE_COLORS = {SIDE_BOTH: QColor(70, 160, 100), SIDE_PC: QColor(70, 140, 210), SIDE_PHONE: QColor(170, 110, 210)}


class ApplyDestinationsDialog(QDialog):
    """Dove vanno le correzioni scelte, secondo dove c'è il brano: collegati (PC e iPhone), solo PC, solo iPhone."""

    def __init__(self, parent, plan) -> None:
        super().__init__(parent)
        self.setWindowTitle("Applica le correzioni scelte")
        self.resize(640, 420)
        layout = QVBoxLayout(self)
        intro = QLabel("Dove va ogni correzione dipende da dove c'è il brano.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.both_files = QCheckBox("Sul PC: scrivi nei file (prima vedi l'elenco di ogni file e campo, da approvare)")
        self.both_phone = QCheckBox("Sull'iPhone: Usa i tag da PC a iPhone, in attesa (parte con Applica)")
        self.pc_files = QCheckBox("Sul PC: scrivi nei file (prima vedi l'elenco di ogni file e campo, da approvare)")
        for box in (self.both_files, self.both_phone, self.pc_files):
            box.setChecked(True)
        unchecked = "Spenta: sul PC le correzioni restano in sospeso, solo per le copie (i file non cambiano)."
        linked = plan.count(SIDE_BOTH)
        if linked:
            group = QGroupBox(f"{linked} brani sul PC e sull'iPhone (collegati)")
            box_layout = QVBoxLayout(group)
            box_layout.addWidget(self.both_files)
            box_layout.addWidget(_gray(unchecked))
            box_layout.addWidget(self.both_phone)
            layout.addWidget(group)
        pc_only = plan.count(SIDE_PC)
        if pc_only:
            group = QGroupBox(f"{pc_only} brani solo sul PC")
            box_layout = QVBoxLayout(group)
            box_layout.addWidget(self.pc_files)
            box_layout.addWidget(_gray(unchecked))
            layout.addWidget(group)
        if plan.phone:
            group = QGroupBox(f"{len(plan.phone)} brani solo sull'iPhone")
            box_layout = QVBoxLayout(group)
            box_layout.addWidget(_gray("Cambia i tag sull'iPhone, in attesa (parte con Applica). Sul PC non c'è niente "
                                       "da cambiare."))
            layout.addWidget(group)
        if plan.blocked:
            lines = []
            for name, reason in plan.blocked[:8]:
                lines.append(f"• {name}: {reason}")
            if len(plan.blocked) > 8:
                lines.append(f"… e altri {len(plan.blocked) - 8}")
            joined = "\n".join(lines)
            note = QLabel(f"Non si possono fare:\n{joined}")
            note.setWordWrap(True)
            layout.addWidget(note)
        layout.addWidget(_gray("Ogni scrittura sull'iPhone va in attesa e parte con Applica (barra blu), dove ogni "
                               "azione si toglie con la ✕. Nei file del PC si scrive solo dopo l'elenco di ogni file e "
                               "campo (Modifica N file; non si può annullare)."))
        layout.addStretch(1)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Continua")
        buttons.button(QDialogButtonBox.Cancel).setText("Annulla")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


def _row_key(row) -> tuple:
    """Una correzione, riconoscibile anche nei risultati rifatti: il file, il campo, il valore nuovo."""
    result = (str(row.target.scanned.path), row.name, repr(row.new))
    return result


def _gray(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet("color: gray")
    return label


class CheckResultsView(QWidget):
    """I risultati del controllo per album. launcher: il ScanLauncher (la finestra, Controlla di nuovo); entries:
    check_flow.AlbumEntry; online: {album: albumcheck.AlbumCheckResult} della Verifica online; side: SIDE_PC o SIDE_PHONE."""

    def __init__(self, launcher, report, entries: list, saved, online: dict, side: str) -> None:
        super().__init__(launcher.window)
        self.launcher = launcher
        self.window = launcher.window
        self.report = report
        self.entries = entries
        self.saved = saved
        self.online = online
        self.side = side
        self._problems = []          # (indice dell'album, AlbumProblem)
        self._rows = []              # check_flow.Row
        self._row_items = []         # QTreeWidgetItem delle righe, nello stesso ordine
        self._applied = set()        # gli indici delle righe già applicate

        self.header = QLabel()
        self.header.setWordWrap(True)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(COLUMNS)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.header().setSectionResizeMode(QHeaderView.Interactive)
        for column, width in ((COL_NAME, 420), (COL_SIDE, 100), (COL_FIELD, 110), (COL_OLD, 170), (COL_NEW, 170),
                              (COL_SEVERITY, 60), (COL_ORIGIN, 60)):
            self.tree.setColumnWidth(column, width)
        self.tree.itemSelectionChanged.connect(self._show_detail)
        self.tree.itemChanged.connect(self._item_changed)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._menu)
        self.detail = QTextBrowser()
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.tree)
        splitter.addWidget(self.detail)
        splitter.setSizes([420, 160])

        self.apply_button = QPushButton("Applica le correzioni scelte…")
        self.apply_button.setProperty("role", "go")
        self.apply_button.clicked.connect(self._apply)
        self.show_button = QPushButton("Mostra i brani")
        self.show_button.setToolTip("Seleziona i brani degli album o dei problemi scelti nella loro scheda")
        self.show_button.clicked.connect(self._show_tracks)
        self.again_button = QPushButton("Controlla di nuovo questi album")
        self.again_button.setToolTip("Lo stesso controllo, con le scelte di sopra, solo sugli album scelti qui")
        self.again_button.clicked.connect(self._check_again)
        self.online_button = QPushButton("Dettagli della verifica online")
        self.online_button.setToolTip("Le tracce dell'edizione trovata e i tuoi file; un'altra edizione, la copertina")
        self.online_button.clicked.connect(self._online_details)
        open_button = QPushButton("Apri il rapporto")
        open_button.setEnabled(saved is not None)
        open_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(saved))))
        self.count_label = _gray("")
        buttons = QHBoxLayout()
        buttons.addWidget(self.show_button)
        buttons.addWidget(self.again_button)
        buttons.addWidget(self.online_button)
        buttons.addWidget(open_button)
        buttons.addStretch(1)
        buttons.addWidget(self.count_label)
        buttons.addWidget(self.apply_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.header)
        layout.addWidget(splitter, 1)
        layout.addLayout(buttons)
        self._fill_header()
        self._fill()
        self._show_detail()
        self._update_buttons()

    # ------------------------------------------------------------------ riempire

    def _fill_header(self) -> None:
        report = self.report
        albums = 0
        for entry in self.entries:
            if entry.key != OTHER_KEY:
                albums += 1
        text = (f"<b>{albums} album con problemi</b> su {report.albums_scanned} controllati ({report.tracks_scanned} "
                f"brani, {escape(report.target)}): {len(report.issues)} problemi")
        if report.ai_profile:
            text += f" — analisi AI con {escape(report.ai_profile)}"
        if report.cancelled:
            text += " — <b>controllo interrotto: risultati parziali</b>"
        if report.stopped:
            names = []
            for stage in report.stopped:
                names.append(tr(stage))
            text += (f"<br><b>Annullati: {escape(', '.join(names))}</b> — i risultati sono quelli senza "
                     "(tasto destro sugli album: Controlla con l'AI, Controlla online)")
        for error in report.ai_errors[:3]:
            text += f"<br><span style='color:#c33'>Errore AI: {escape(error)}</span>"
        self.header.setText(text)

    def _icon(self, severity: str):
        style = self.style()
        if severity == SEVERITY_HIGH:
            result = style.standardIcon(QStyle.SP_MessageBoxCritical)
        elif severity == SEVERITY_MEDIUM:
            result = style.standardIcon(QStyle.SP_MessageBoxWarning)
        else:
            result = style.standardIcon(QStyle.SP_MessageBoxInformation)
        return result

    def _fill(self) -> None:
        self.tree.blockSignals(True)
        checkable = Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate
        for entry_index, entry in enumerate(self.entries):
            title = entry.title + (f" ({entry.year})" if entry.year else "")
            top = QTreeWidgetItem([title, tr(SIDE_LABELS.get(entry.side, "")), "", "", "", tr(entry.severity), ""])
            font = top.font(COL_NAME)
            font.setBold(True)
            top.setFont(COL_NAME, font)
            top.setIcon(COL_NAME, self._icon(entry.severity))
            top.setData(COL_NAME, KIND_ROLE, ROW_ALBUM)
            top.setData(COL_NAME, REF_ROLE, entry_index)
            if entry.side in SIDE_COLORS:
                top.setForeground(COL_SIDE, QBrush(SIDE_COLORS[entry.side]))
            if entry.rows():
                # non AutoTristate: un problema senza correzioni (senza casella) toglierebbe la casella all'album
                top.setFlags(top.flags() | Qt.ItemIsUserCheckable)
                top.setCheckState(COL_NAME, Qt.Checked)
            self.tree.addTopLevelItem(top)
            for problem in entry.problems:
                issue = problem.issue
                child = QTreeWidgetItem([tr(issue.title), "", "", "", "", tr(issue.severity), tr(issue.origin)])
                child.setIcon(COL_NAME, self._icon(issue.severity))
                child.setData(COL_NAME, KIND_ROLE, ROW_PROBLEM)
                child.setData(COL_NAME, REF_ROLE, len(self._problems))
                self._problems.append((entry_index, problem))
                if issue.ai_note:
                    for column in range(len(COLUMNS)):
                        child.setForeground(column, QBrush(GREY))
                    child.setToolTip(COL_NAME, f"L'AI ritiene che non sia un problema: {issue.ai_note}")
                if problem.rows:
                    child.setFlags(child.flags() | checkable)
                    child.setCheckState(COL_NAME, Qt.Checked)
                top.addChild(child)
                for row in problem.rows:
                    leaf = QTreeWidgetItem([row.target.name, tr(SIDE_LABELS[row.target.side]),
                                            tr(FIELD_LABELS.get(row.name, row.name)), shown_value(row.name, row.old),
                                            shown_value(row.name, row.new), "", ""])
                    leaf.setForeground(COL_SIDE, QBrush(SIDE_COLORS[row.target.side]))
                    leaf.setForeground(COL_OLD, QBrush(QColor(200, 80, 70)))
                    leaf.setForeground(COL_NEW, QBrush(GREEN))
                    leaf.setData(COL_NAME, KIND_ROLE, ROW_FIX)
                    leaf.setData(COL_NAME, REF_ROLE, len(self._rows))
                    leaf.setFlags(leaf.flags() | Qt.ItemIsUserCheckable)
                    child.addChild(leaf)
                    leaf.setCheckState(COL_NAME, Qt.Unchecked if issue.ai_note else Qt.Checked)
                    self._rows.append(row)
                    self._row_items.append(leaf)
        for index in range(self.tree.topLevelItemCount()):
            self._sync_album(self.tree.topLevelItem(index))
        if self.tree.topLevelItemCount():
            self.tree.topLevelItem(0).setExpanded(True)
        self.tree.blockSignals(False)
        done = []
        for index, row in enumerate(self._rows):
            if _row_key(row) in self.launcher.applied:       # già applicata prima di rifare i risultati
                done.append(index)
        if done:
            self._mark_applied(done)

    def _menu(self, position) -> None:
        """Tasto destro sui risultati: di nuovo l'AI o la Verifica online, solo sugli album scelti; e le azioni dei
        pulsanti."""
        from .scan_dialog import STAGE_AI, STAGE_ONLINE
        keys = set()
        for entry in self._selected_entries():
            if entry.key != OTHER_KEY:
                keys.add(entry.key)
        launcher = self.launcher
        menu = QMenu(self)
        ai = menu.addAction(f"Controlla con l'AI ({len(keys)} album)")
        ai.setEnabled(bool(keys) and bool(launcher.profile_name()))
        ai.setToolTip("Di nuovo l'Analisi AI, solo su questi album: i loro risultati dell'AI si sostituiscono")
        ai.triggered.connect(lambda: launcher.recheck(STAGE_AI, keys))
        online = menu.addAction(f"Controlla online ({len(keys)} album)")
        online.setEnabled(bool(keys) and bool(launcher.online_clients()))
        online.setToolTip("Di nuovo la Verifica online, con i cataloghi scelti sopra, solo su questi album")
        online.triggered.connect(lambda: launcher.recheck(STAGE_ONLINE, keys))
        menu.addSeparator()
        for button in (self.show_button, self.again_button, self.online_button):
            action = menu.addAction(button.text())
            action.setEnabled(button.isEnabled())
            action.triggered.connect(button.click)
        menu.setToolTipsVisible(True)
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def _item_changed(self, item, column: int) -> None:
        """La casella di un album accende o spegne tutte le sue correzioni; quella di una correzione o di un problema
        rifà quella del suo album (accesa, spenta o a metà)."""
        if column == COL_NAME:
            self.tree.blockSignals(True)
            if item.data(COL_NAME, KIND_ROLE) == ROW_ALBUM:
                state = Qt.Unchecked if item.checkState(COL_NAME) == Qt.Unchecked else Qt.Checked
                for index in range(item.childCount()):
                    problem = item.child(index)
                    for row_index in range(problem.childCount()):
                        leaf = problem.child(row_index)
                        if leaf.flags() & Qt.ItemIsUserCheckable:
                            leaf.setCheckState(COL_NAME, state)
            top = item
            while top.parent() is not None:
                top = top.parent()
            self._sync_album(top)
            self.tree.blockSignals(False)
            self.tree.viewport().update()
        self._update_buttons()

    def _sync_album(self, top) -> None:
        """La casella dell'album secondo le sue correzioni ancora da applicare (solo gli album che ne hanno)."""
        if self.entries[top.data(COL_NAME, REF_ROLE)].rows():
            on = 0
            total = 0
            for index in range(top.childCount()):
                problem = top.child(index)
                for row_index in range(problem.childCount()):
                    leaf = problem.child(row_index)
                    if leaf.flags() & Qt.ItemIsUserCheckable:
                        total += 1
                        if leaf.checkState(COL_NAME) == Qt.Checked:
                            on += 1
            if total == 0 or on == 0:
                state = Qt.Unchecked
            elif on == total:
                state = Qt.Checked
            else:
                state = Qt.PartiallyChecked
            top.setCheckState(COL_NAME, state)

    # ------------------------------------------------------------------ la scelta

    def chosen_rows(self) -> list:
        """Le correzioni con la casella accesa e non ancora applicate."""
        result = []
        for index, item in enumerate(self._row_items):
            if index not in self._applied and item.checkState(COL_NAME) == Qt.Checked:
                result.append(self._rows[index])
        return result

    def _selected_entries(self) -> list:
        """Gli album delle righe selezionate (album, problema o brano)."""
        result = []
        for item in self.tree.selectedItems():
            top = item
            while top.parent() is not None:
                top = top.parent()
            entry = self.entries[top.data(COL_NAME, REF_ROLE)]
            if entry not in result:
                result.append(entry)
        return result

    def _selected_targets(self) -> list:
        """I brani delle righe selezionate: di un brano, del suo problema, o di tutto l'album."""
        result = []
        for item in self.tree.selectedItems():
            kind = item.data(COL_NAME, KIND_ROLE)
            if kind == ROW_FIX:
                found = [self._rows[item.data(COL_NAME, REF_ROLE)].target]
            elif kind == ROW_PROBLEM:
                entry_index, problem = self._problems[item.data(COL_NAME, REF_ROLE)]
                found = []
                for target in self.entries[entry_index].targets:
                    if target.scanned.path in problem.files or str(target.scanned.path) in problem.files:
                        found.append(target)
                for row in problem.rows:
                    found.append(row.target)
            else:
                found = list(self.entries[item.data(COL_NAME, REF_ROLE)].targets)
            for target in found:
                if target not in result:
                    result.append(target)
        return result

    def _update_buttons(self) -> None:
        chosen = len(self.chosen_rows())
        self.apply_button.setEnabled(chosen > 0)
        self.count_label.setText(f"{chosen} correzioni scelte" if chosen else "Nessuna correzione scelta")
        entries = self._selected_entries()
        real = []
        for entry in entries:
            if entry.key != OTHER_KEY:
                real.append(entry)
        self.show_button.setEnabled(bool(self._selected_targets()))
        self.again_button.setEnabled(bool(real))
        online = len(real) == 1 and real[0].key in self.online and self.side == SIDE_PC
        self.online_button.setEnabled(online)

    def _show_detail(self) -> None:
        items = self.tree.selectedItems()
        html = ""
        if items:
            item = items[0]
            kind = item.data(COL_NAME, KIND_ROLE)
            if kind == ROW_FIX:
                item = item.parent()
                kind = ROW_PROBLEM
            if kind == ROW_PROBLEM:
                _entry_index, problem = self._problems[item.data(COL_NAME, REF_ROLE)]
                html = self._problem_html(problem)
            else:
                entry = self.entries[item.data(COL_NAME, REF_ROLE)]
                html = f"<h3>{escape(entry.title)}</h3><p>{escape(tr(SIDE_LABELS.get(entry.side, '')))}</p>"
                for problem in entry.problems:
                    suggestion = advice(problem.issue)
                    html += f"<p><b>{escape(tr(problem.issue.title))}</b>"
                    if suggestion:
                        html += f"<br><i>Cosa fare:</i> {escape(tr(suggestion))}"
                    html += "</p>"
        else:
            html = ("<p>Seleziona un album o un problema per vederne i dettagli e cosa fare. Le caselle scelgono le "
                    "correzioni da applicare.</p>")
        self.detail.setHtml(html)
        self._update_buttons()

    def _problem_html(self, problem) -> str:
        issue = problem.issue
        detail = escape(tr(issue.detail)).replace("\n", "<br>")
        html = f"<h3>{escape(tr(issue.title))}</h3><p>{detail}</p>"
        if issue.origin == ORIGIN_AI:
            html += "<p><i>Trovato dall'AI.</i></p>"
        if issue.ai_note:
            html += (f"<p><b>L'AI ritiene che non sia un problema:</b> {escape(issue.ai_note)} (le sue correzioni sono "
                     "spente)</p>")
        if issue.fix is not None:
            html += f"<p><b>Correzione proposta:</b> {escape(tr(issue.fix.description))}</p>"
        suggestion = advice(issue)
        if suggestion:
            html += f"<p><b>Cosa fare:</b> {escape(tr(suggestion))}</p>"
        files = ""
        for path in problem.files[:100]:
            files += f"<li>{escape(str(path))}</li>"
        more = f"<p>… e altri {len(problem.files) - 100}</p>" if len(problem.files) > 100 else ""
        html += f"<p><b>{len(problem.files)} file in questo album:</b></p><ul>{files}</ul>{more}"
        return html

    # ------------------------------------------------------------------ azioni

    def _show_tracks(self) -> None:
        targets = self._selected_targets()
        if self.side == SIDE_PC:
            paths = set()
            for target in targets:
                if target.pc is not None:
                    paths.add(str(target.pc.path))
            self.window.show_tracks(paths)
        else:
            pids = set()
            for target in targets:
                if target.phone is not None:
                    pids.add(target.phone.pid)
            self.window.iphone_panel.show_pids(pids)

    def _check_again(self) -> None:
        keys = set()
        for entry in self._selected_entries():
            if entry.key != OTHER_KEY:
                keys.add(entry.key)
        if keys:
            self.launcher.run_again(keys, self.side)

    def _online_details(self) -> None:
        entries = self._selected_entries()
        if len(entries) == 1 and entries[0].key in self.online:
            from .album_check_dialog import AlbumCheckDialog
            AlbumCheckDialog([self.online[entries[0].key]], self.window).exec()

    def _apply(self) -> None:
        chosen = []
        indexes = []
        for index, item in enumerate(self._row_items):
            if index not in self._applied and item.checkState(COL_NAME) == Qt.Checked:
                chosen.append(self._rows[index])
                indexes.append(index)
        plan = plan_apply(chosen)
        dialog = ApplyDestinationsDialog(self, plan)
        if chosen and dialog.exec():
            self._run_plan(plan, dialog)
            self._mark_applied(indexes)

    def _run_plan(self, plan, dialog) -> None:
        """Le correzioni dalla parte giusta: sul PC in sospeso (e nei file, dopo l'elenco da approvare), sull'iPhone
        in attesa (Usa i tag da PC a iPhone per i collegati, Cambia i tag per quelli solo sull'iPhone)."""
        window = self.window
        pairs = []
        for track, values in plan.pc:
            new_tags = track.tags.copy()
            for name, value in values.items():
                setattr(new_tags, name, value)
            pairs.append((track, new_tags))
        if pairs:
            window.apply_tag_changes(pairs)
        if plan.linked and dialog.both_phone.isChecked():
            window.queue_pairs(plan.linked, UPDATE)
        if plan.phone:
            window.queue_edit_values(plan.phone)
        linked_ids = set()
        for _item, track in plan.linked:
            linked_ids.add(id(track))
        to_write = []
        for track, _values in plan.pc:
            linked = id(track) in linked_ids
            if (linked and dialog.both_files.isChecked()) or (not linked and dialog.pc_files.isChecked()):
                to_write.append(track)
        if to_write:
            offer_pc_write(window, self, to_write, "Applica le correzioni",
                           "si scrivono nel file le correzioni dei campi scelti")
        elif pairs:
            window.statusBar().showMessage(f"Correzioni salvate in sospeso su {len(pairs)} brani del PC: i file non "
                                           "cambiano", 8000)

    def _mark_applied(self, indexes: list) -> None:
        self.tree.blockSignals(True)
        for index in indexes:
            self._applied.add(index)
            self.launcher.applied.add(_row_key(self._rows[index]))
            item = self._row_items[index]
            item.setCheckState(COL_NAME, Qt.Unchecked)
            item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable & ~Qt.ItemIsEnabled)
            item.setText(COL_NEW, item.text(COL_NEW) + "  ✔")
            item.setToolTip(COL_NAME, "Correzione applicata")
        for index in range(self.tree.topLevelItemCount()):
            self._sync_album(self.tree.topLevelItem(index))
        self.tree.blockSignals(False)
        self._update_buttons()
