# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La linguetta Controlli, sotto: i risultati per album. Ogni album ha i suoi problemi (con Cosa fare) e, sotto, le
correzioni proposte, una riga per brano e campo (ora → diventa), con una casella; la casella dell'album e quella del
problema accendono o spengono tutte le loro righe. Applica le correzioni scelte le manda dalla parte giusta
(check_flow.plan_apply): PC e iPhone per i brani collegati, solo PC, solo iPhone (sempre in attesa)."""

from __future__ import annotations

from difflib import SequenceMatcher
from html import escape
from pathlib import Path

from PySide6.QtCore import QPointF, QUrl, Qt
from PySide6.QtGui import QBrush, QColor, QDesktopServices, QTextDocument
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QMenu,
    QMessageBox,
    QPushButton, QSplitter, QStyle, QStyledItemDelegate, QStyleOptionViewItem, QTextBrowser, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from ..check_flow import FIELD_LABELS, OTHER_KEY, SIDE_BOTH, SIDE_LABELS, SIDE_PC, SIDE_PHONE, plan_apply
from ..i18n import tr
from ..pending import UPDATE
from ..scan import ORIGIN_AI, SEVERITY_HIGH, SEVERITY_INFO, SEVERITY_MEDIUM, advice
from ..tags import OLD_TAG_NAMES
from .file_actions import add_file_entries
from .pc_write import offer_pc_write, shown_value

COLUMNS = ["Album, problema, brano", "Correzione", "Dove", "Campo", "Ora", "Diventa", "Gravità", "Origine"]
COL_NAME, COL_FIX, COL_SIDE, COL_FIELD, COL_OLD, COL_NEW, COL_SEVERITY, COL_ORIGIN = range(len(COLUMNS))
ORANGE = QColor(210, 130, 0)
AUTO_TIP = "Si corregge qui: lascia accese le caselle delle righe che vuoi e premi Applica le correzioni scelte"
MANUAL_TIP = "Nessuna correzione automatica: leggi Cosa fare (sotto, o qui)"
KIND_ROLE = Qt.UserRole           # ROW_ALBUM, ROW_PROBLEM, ROW_FIX
ROW_ALBUM = "riga_album"
ROW_PROBLEM = "riga_problema"
ROW_FIX = "riga_correzione"
REF_ROLE = Qt.UserRole + 1        # l'indice nell'elenco degli album, dei problemi o delle righe
GREEN = QColor(30, 140, 60)
GREY = QColor(130, 130, 130)
SIDE_COLORS = {SIDE_BOTH: QColor(70, 160, 100), SIDE_PC: QColor(70, 140, 210), SIDE_PHONE: QColor(170, 110, 210)}
DIFF_ROLE = Qt.UserRole + 2       # (testo, pezzi) delle colonne Ora e Diventa: i caratteri che cambiano, evidenziati


def diff_pieces(old: str, new: str) -> tuple:
    """([(pezzo, cambia)] di old, [(pezzo, cambia)] di new): i caratteri diversi tra i due testi, per vedere subito
    una differenza piccola ("to" → "To", uno spazio in più)."""
    old_pieces = []
    new_pieces = []
    matcher = SequenceMatcher(None, old, new, autojunk=False)
    for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        changed = tag != "equal"
        if old_end > old_start:
            old_pieces.append((old[old_start:old_end], changed))
        if new_end > new_start:
            new_pieces.append((new[new_start:new_end], changed))
    result = (old_pieces, new_pieces)
    return result


def _pieces_html(pieces: list) -> str:
    """I pezzi in HTML: quelli che cambiano in grassetto, sottolineati e su fondo giallo chiaro; gli spazi visibili."""
    parts = []
    for text, changed in pieces:
        shown = escape(text).replace(" ", "&nbsp;")
        if changed:
            if not text.strip():
                shown = "␣" * len(text)                 # uno spazio che cambia: si vede
            parts.append(f"<b><u style='background-color: rgba(255, 210, 0, 90)'>{shown}</u></b>")
        else:
            parts.append(shown)
    result = "".join(parts)
    return result


class DiffDelegate(QStyledItemDelegate):
    """Le colonne Ora e Diventa: i caratteri che cambiano evidenziati (DIFF_ROLE). Quando il testo della cella non è
    più quello (la ✔ di una correzione applicata), la cella si disegna come le altre."""

    def paint(self, painter, option, index) -> None:
        data = index.data(DIFF_ROLE)
        text = index.data(Qt.DisplayRole)
        if data is not None and data[0] == text:
            options = QStyleOptionViewItem(option)
            self.initStyleOption(options, index)
            options.text = ""
            widget = options.widget
            style = widget.style() if widget is not None else None
            if style is not None:
                style.drawControl(QStyle.CE_ItemViewItem, options, painter, widget)
            selected = bool(option.state & QStyle.State_Selected)
            brush = index.data(Qt.ForegroundRole)
            color = option.palette.highlightedText().color() if selected or brush is None else brush.color()
            document = QTextDocument()
            document.setDefaultFont(options.font)
            document.setDocumentMargin(0)
            document.setHtml(f"<span style='color: {color.name()}; white-space: pre'>{_pieces_html(data[1])}</span>")
            painter.save()
            painter.setClipRect(option.rect)
            top = option.rect.top() + max(0, (option.rect.height() - document.size().height()) / 2)
            painter.translate(QPointF(option.rect.left() + 4, top))
            document.drawContents(painter)
            painter.restore()
        else:
            super().paint(painter, option, index)


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
        self.old_files = QCheckBox("Togli i vecchi tag dai file (prima vedi l'elenco da approvare; i loro valori "
                                   "passano nel tag ID3v2)")
        for box in (self.both_files, self.both_phone, self.pc_files, self.old_files):
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
        if plan.old_tags:
            group = QGroupBox(f"{len(plan.old_tags)} MP3 del PC con vecchi tag (ID3v1, APE)")
            box_layout = QVBoxLayout(group)
            box_layout.addWidget(self.old_files)
            box_layout.addWidget(_gray("Spenta: i file restano così. Le copie per l'iPhone ne sono comunque senza."))
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
        if plan.conflicts:
            lines = []
            for name, field_label, values in plan.conflicts[:8]:
                shown = " / ".join(f"«{value}»" for value in values)
                lines.append(f"• {name}, {field_label}: {shown} → vale «{values[-1]}»")
            if len(plan.conflicts) > 8:
                lines.append(f"… e altri {len(plan.conflicts) - 8}")
            joined = "\n".join(lines)
            note = QLabel(f"Due correzioni scelte vogliono valori diversi nello stesso campo:\n{joined}\nSe vuoi l'altro "
                          "valore: Annulla, togli la casella della riga che non vuoi (nei risultati) e premi di nuovo "
                          "Applica le correzioni scelte.")
            note.setWordWrap(True)
            note.setStyleSheet("color: rgb(210, 130, 0)")
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


_ICON_CACHE = {}       # gravità -> QIcon


def _item(columns: int, texts: dict) -> QTreeWidgetItem:
    """Una riga dei risultati con i testi delle colonne date (le altre vuote)."""
    values = []
    for column in range(columns):
        values.append(texts.get(column, ""))
    result = QTreeWidgetItem(values)
    return result


def _row_key(row) -> tuple:
    """Una correzione, riconoscibile anche nei risultati rifatti: il file, il campo, il valore nuovo."""
    result = (str(row.target.scanned.path), row.name, repr(row.new))
    return result


def _albums_text(keys: list) -> str:
    """Gli album dove si corregge un problema, per nome: «…Famous Last Words», «Altro»."""
    names = []
    for key in keys[:3]:
        names.append(f"«{key[1]}»")
    result = ", ".join(names) + (f" e altri {len(keys) - 3}" if len(keys) > 3 else "")
    return result


def _gray(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet("color: gray")
    return label


class CheckResultsView(QWidget):
    """I risultati del controllo per album. launcher: il ScanLauncher (la finestra, Controlla di nuovo); entries:
    check_flow.AlbumEntry; online: {album: albumcheck.AlbumCheckResult} della Verifica online; side: SIDE_PC o SIDE_PHONE."""

    def __init__(self, launcher, report, entries: list, saved, online: dict, side: str, live: bool = False,
                 hidden: int = 0, ai_running: bool = False) -> None:
        super().__init__(launcher.window)
        self.live = live             # il controllo è ancora in corso: risultati parziali, Applica alla fine
        self.ai_running = ai_running   # l'Analisi AI va in background: i suoi risultati si aggiungono man mano
        self.hidden = hidden         # i problemi che vanno bene così (nascosti, o mostrati in grigio)
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
        for column, width in ((COL_NAME, 420), (COL_FIX, 150), (COL_SIDE, 100), (COL_FIELD, 110), (COL_OLD, 170), (COL_NEW, 170),
                              (COL_SEVERITY, 60), (COL_ORIGIN, 60)):
            self.tree.setColumnWidth(column, width)
        self._diff_delegate = DiffDelegate(self.tree)
        self.tree.setItemDelegateForColumn(COL_OLD, self._diff_delegate)
        self.tree.setItemDelegateForColumn(COL_NEW, self._diff_delegate)
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

        self.show_accepted = QCheckBox()
        self.show_accepted.setChecked(launcher.show_accepted)
        self.show_accepted.setText(f"Mostra anche quelli che vanno bene così ({hidden})")
        self.show_accepted.setVisible(hidden > 0 or launcher.show_accepted)
        self.show_accepted.setToolTip("I problemi segnati \"va bene così\" (tasto destro): in grigio, e da lì si "
                                      "tolgono. Anche in Impostazioni → Controlli")
        self.show_accepted.toggled.connect(launcher.set_show_accepted)
        layout = QVBoxLayout(self)
        layout.addWidget(self.header)
        layout.addWidget(self.show_accepted)
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
                f"brani, {escape(report.target)}): {self._problem_count()} problemi")
        information = len(report.issues) - self._problem_count()
        if information:
            text += (f" e {information} informazioni (in grigio: album incompleti, dettagli che sull'iPhone non "
                     "cambiano niente; le loro correzioni partono spente)")
        if self.live:
            text = ("<b style='color:#d28200'>Controllo in corso: i risultati arrivano man mano.</b> Applica le "
                    "correzioni scelte si può usare alla fine.<br>") + text
        elif self.ai_running:
            text = ("<b style='color:#d28200'>Analisi AI in corso, in background:</b> i suoi risultati si aggiungono "
                    "man mano. Intanto puoi già applicare le correzioni.<br>") + text
        if report.ai_profile:
            text += f" — analisi AI con {escape(report.ai_profile)}"
        if report.online_notes:
            text += (f"<br><span style='color: gray'>{len(report.online_notes)} album non trovati nei cataloghi "
                     "online: non sono problemi, l'elenco è nel rapporto (Apri il rapporto).</span>")
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

    def _problem_count(self) -> int:
        count = 0
        for issue in self.report.issues:
            if issue.severity != SEVERITY_INFO:
                count += 1
        return count

    def _icon(self, severity: str):
        """L'icona della gravità, presa una volta sola per tipo: chiederla al sistema per ogni riga costava secondi
        con migliaia di righe (la finestra non rispondeva durante i risultati man mano)."""
        if severity not in _ICON_CACHE:
            style = self.style()
            if severity == SEVERITY_HIGH:
                _ICON_CACHE[severity] = style.standardIcon(QStyle.SP_MessageBoxCritical)
            elif severity == SEVERITY_MEDIUM:
                _ICON_CACHE[severity] = style.standardIcon(QStyle.SP_MessageBoxWarning)
            elif severity == SEVERITY_INFO:
                _ICON_CACHE[severity] = style.standardIcon(QStyle.SP_FileDialogInfoView)
            else:
                _ICON_CACHE[severity] = style.standardIcon(QStyle.SP_MessageBoxInformation)
        result = _ICON_CACHE[severity]
        return result

    def _fill(self) -> None:
        self.tree.blockSignals(True)
        checkable = Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate
        for entry_index, entry in enumerate(self.entries):
            title = entry.title + (f" ({entry.year})" if entry.year else "")
            top = _item(len(COLUMNS), {COL_NAME: title, COL_SIDE: tr(SIDE_LABELS.get(entry.side, "")),
                                       COL_SEVERITY: tr(entry.severity)})
            automatic = 0
            manual = 0
            elsewhere = 0
            open_rows = 0
            information = 0
            for problem in entry.problems:
                if not problem.accepted and problem.issue.severity == SEVERITY_INFO:
                    information += 1
                    open_rows += len(problem.rows)
                elif not problem.accepted and problem.rows:
                    automatic += 1
                    open_rows += len(problem.rows)
                elif not problem.accepted and problem.elsewhere:
                    elsewhere += 1
                elif not problem.accepted:
                    manual += 1
            parts = []
            if automatic:
                parts.append(f"{automatic} automatiche")
            if manual:
                parts.append(f"{manual} a mano")
            if information:
                parts.append(f"{information} informazioni")
            if parts:
                summary = ", ".join(parts)
            elif elsewhere:
                summary = "si corregge nell'altro album"
            else:
                summary = "va bene così"
            top.setText(COL_FIX, summary)
            top.setForeground(COL_FIX, QBrush(GREEN if not manual else ORANGE))
            if not automatic and not manual:
                for column in range(len(COLUMNS)):
                    top.setForeground(column, QBrush(GREY))      # solo informazioni, o niente da fare qui
            top.setToolTip(COL_FIX, "Problemi che si correggono qui (con le caselle) e problemi da sistemare a mano "
                                    "(Cosa fare, nel dettaglio sotto)")
            font = top.font(COL_NAME)
            font.setBold(True)
            top.setFont(COL_NAME, font)
            top.setIcon(COL_NAME, self._icon(entry.severity))
            top.setData(COL_NAME, KIND_ROLE, ROW_ALBUM)
            top.setData(COL_NAME, REF_ROLE, entry_index)
            if entry.side in SIDE_COLORS:
                top.setForeground(COL_SIDE, QBrush(SIDE_COLORS[entry.side]))
            if open_rows:
                # non AutoTristate: un problema senza correzioni (senza casella) toglierebbe la casella all'album
                top.setFlags(top.flags() | Qt.ItemIsUserCheckable)
                top.setCheckState(COL_NAME, Qt.Checked)
            self.tree.addTopLevelItem(top)
            for problem in entry.problems:
                issue = problem.issue
                child = _item(len(COLUMNS), {COL_NAME: tr(issue.title), COL_SEVERITY: tr(issue.severity),
                                             COL_ORIGIN: tr(issue.origin)})
                if problem.accepted:
                    child.setText(COL_FIX, "va bene così")
                    child.setToolTip(COL_FIX, "Segnato \"va bene così\": i controlli non lo mostrano più (tasto "
                                              "destro → Togli \"va bene così\")")
                elif problem.rows:
                    child.setText(COL_FIX, f"automatica ({len(problem.rows)})")
                    child.setForeground(COL_FIX, QBrush(GREEN))
                    child.setToolTip(COL_FIX, AUTO_TIP)
                elif problem.elsewhere:
                    child.setText(COL_FIX, "nell'altro album")
                    child.setToolTip(COL_FIX, f"Qui c'è già la forma giusta: si corregge con la correzione automatica "
                                              f"di {_albums_text(problem.elsewhere)}. Qui non c'è niente da fare.")
                    for column in range(len(COLUMNS)):
                        child.setForeground(column, QBrush(GREY))
                else:
                    child.setText(COL_FIX, "a mano")
                    child.setForeground(COL_FIX, QBrush(ORANGE))
                    suggestion = advice(issue)
                    child.setToolTip(COL_FIX, f"{tr(MANUAL_TIP)}\n\n{tr(suggestion)}" if suggestion else MANUAL_TIP)
                child.setIcon(COL_NAME, self._icon(issue.severity))
                child.setData(COL_NAME, KIND_ROLE, ROW_PROBLEM)
                child.setData(COL_NAME, REF_ROLE, len(self._problems))
                self._problems.append((entry_index, problem))
                information = issue.severity == SEVERITY_INFO
                if issue.ai_note or problem.accepted or information:
                    for column in range(len(COLUMNS)):
                        child.setForeground(column, QBrush(GREY))
                if information:
                    child.setToolTip(COL_NAME, "Informazione: sull'iPhone non crea confusione. La correzione, se c'è, "
                                               "parte spenta: accendila se vuoi")
                if issue.ai_note:
                    child.setToolTip(COL_NAME, f"L'AI ritiene che non sia un problema: {issue.ai_note}")
                if problem.rows and not problem.accepted:
                    child.setFlags(child.flags() | checkable)
                    child.setCheckState(COL_NAME, Qt.Unchecked if information else Qt.Checked)
                top.addChild(child)
                if problem.accepted:
                    self._add_accepted_rows(child, problem)
                for row in ([] if problem.accepted else problem.rows):
                    leaf = _item(len(COLUMNS), {COL_NAME: row.target.name, COL_SIDE: tr(SIDE_LABELS[row.target.side]),
                                                COL_FIELD: tr(FIELD_LABELS.get(row.name, row.name)),
                                                COL_OLD: shown_value(row.name, row.old),
                                                COL_NEW: shown_value(row.name, row.new)})
                    leaf.setForeground(COL_SIDE, QBrush(SIDE_COLORS[row.target.side]))
                    leaf.setForeground(COL_OLD, QBrush(QColor(200, 80, 70)))
                    leaf.setForeground(COL_NEW, QBrush(GREEN))
                    old_text = leaf.text(COL_OLD)
                    new_text = leaf.text(COL_NEW)
                    if isinstance(row.old, str) and isinstance(row.new, str) and old_text and new_text:
                        old_pieces, new_pieces = diff_pieces(old_text, new_text)
                        leaf.setData(COL_OLD, DIFF_ROLE, (old_text, old_pieces))
                        leaf.setData(COL_NEW, DIFF_ROLE, (new_text, new_pieces))
                    leaf.setData(COL_NAME, KIND_ROLE, ROW_FIX)
                    leaf.setData(COL_NAME, REF_ROLE, len(self._rows))
                    leaf.setFlags(leaf.flags() | Qt.ItemIsUserCheckable)
                    child.addChild(leaf)
                    leaf.setCheckState(COL_NAME, Qt.Unchecked if issue.ai_note or information else Qt.Checked)
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

    def _accept_entries(self, menu) -> None:
        """Le voci "va bene così" del tasto destro: per i problemi scelti (il loro tipo, nel loro album), per gli album
        scelti (tutto l'album), e per togliere quelli già segnati."""
        from ..accepted import WHOLE_ALBUM, problem_type, type_label
        problems = []
        accepted = []
        for item in self.tree.selectedItems():
            kind = item.data(COL_NAME, KIND_ROLE)
            if kind == ROW_FIX:
                item = item.parent()
                kind = ROW_PROBLEM
            if kind == ROW_PROBLEM:
                entry_index, problem = self._problems[item.data(COL_NAME, REF_ROLE)]
                key = self.entries[entry_index].key
                pair = (key, problem_type(problem.issue))
                if problem.accepted and self.launcher.accepted.skip_ai(key):
                    pair = (key, WHOLE_ALBUM)            # segnato per tutto l'album: si toglie quello
                if key != OTHER_KEY and pair not in problems and pair not in accepted:
                    if problem.accepted:
                        accepted.append(pair)
                    else:
                        problems.append(pair)
        albums = []
        for entry in self._selected_entries():
            if entry.key != OTHER_KEY:
                albums.append((entry.key, WHOLE_ALBUM))
        launcher = self.launcher
        if problems:
            labels = []
            for _key, kind in problems:
                label = tr(type_label(kind))
                if label not in labels:
                    labels.append(label)
            action = menu.addAction(f"Va bene così: {', '.join(labels)} (per questo album)")
            action.setToolTip("I controlli non mostreranno più questo tipo di problema per questo album, qualunque "
                              "cosa propongano; si toglie da qui (Mostra anche quelli che vanno bene così) o da "
                              "Impostazioni → Controlli")
            action.triggered.connect(lambda: launcher.set_accepted(problems, True))
        if albums:
            action = menu.addAction(f"Va bene così: tutto l'album ({len(albums)} album)")
            action.setToolTip("Nessun problema di questi album si mostrerà più, e l'AI e la Verifica online li saltano")
            action.triggered.connect(lambda: launcher.set_accepted(albums, True))
        whole = []
        for key, kind in albums:
            if launcher.accepted.is_accepted(key, WHOLE_ALBUM) and launcher.accepted.skip_ai(key):
                whole.append((key, kind))
        if accepted or whole:
            action = menu.addAction("Togli \"va bene così\"")
            action.triggered.connect(lambda: launcher.set_accepted(accepted + whole, False))

    def state(self) -> dict:
        """Cosa si vede e cosa è scelto (album e problemi aperti, righe spente, selezione, scorrimento), per ritrovarlo
        dopo che i risultati si rifanno."""
        expanded = set()
        selected = set()
        for index in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(index)
            key = self.entries[top.data(COL_NAME, REF_ROLE)].key
            if top.isExpanded():
                expanded.add(key)
            if top.isSelected():
                selected.add(key)
            for child_index in range(top.childCount()):
                child = top.child(child_index)
                if child.isExpanded():
                    expanded.add((key, child.text(COL_NAME)))
        off = set()
        for index, item in enumerate(self._row_items):
            if index not in self._applied and item.checkState(COL_NAME) != Qt.Checked:
                off.add(_row_key(self._rows[index]))
        result = {"expanded": expanded, "selected": selected, "off": off,
                  "scroll": self.tree.verticalScrollBar().value()}
        return result

    def restore(self, state) -> None:
        """Ritrova lo stato di prima (state(); None: com'è)."""
        if state is not None:
            self.tree.blockSignals(True)
            for index in range(self.tree.topLevelItemCount()):
                top = self.tree.topLevelItem(index)
                key = self.entries[top.data(COL_NAME, REF_ROLE)].key
                top.setExpanded(key in state["expanded"])
                top.setSelected(key in state["selected"])
                for child_index in range(top.childCount()):
                    child = top.child(child_index)
                    child.setExpanded((key, child.text(COL_NAME)) in state["expanded"])
            for index, item in enumerate(self._row_items):
                if index not in self._applied and _row_key(self._rows[index]) in state["off"]:
                    item.setCheckState(COL_NAME, Qt.Unchecked)
            for index in range(self.tree.topLevelItemCount()):
                self._sync_album(self.tree.topLevelItem(index))
            self.tree.blockSignals(False)
            self.tree.verticalScrollBar().setValue(state["scroll"])
            self._show_detail()

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
        self._accept_entries(menu)
        self._trash_entries(menu)
        menu.addSeparator()
        # i file del PC dei brani scelti (di un problema o di un album: tutti i suoi): copiare il percorso della
        # cartella per correggere a mano, o aprirla
        add_file_entries(menu, self._pc_paths(),
                         lambda text: self.window.statusBar().showMessage(text, 8000),
                         tagscan=self.window.app_settings.tagscan_path)
        menu.addSeparator()
        for button in (self.show_button, self.again_button, self.online_button):
            action = menu.addAction(button.text())
            action.setEnabled(button.isEnabled())
            action.triggered.connect(button.click)
        menu.setToolTipsVisible(True)
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def _trash_entries(self, menu) -> None:
        """Per le copie doppie di un album (R32: qualità peggiore; R33: la stessa copia due volte) scelte nei
        risultati: Sposta nel cestino la copia in …, una voce per copia. È l'unico caso in cui il programma toglie
        file del PC, e sempre dopo l'elenco dei file e la conferma, nel Cestino di Windows."""
        from ..library import album_folder, short_folder
        seen = set()
        for item in self.tree.selectedItems():
            if item.data(COL_NAME, KIND_ROLE) == ROW_PROBLEM:
                _entry_index, problem = self._problems[item.data(COL_NAME, REF_ROLE)]
                rule = problem.issue.rule_id.split(".", 1)[0]
                if rule in ("R32", "R33") and not problem.accepted:
                    copies = {}
                    for path in problem.files:
                        copies.setdefault((album_folder(path), Path(path).suffix.casefold()), []).append(Path(path))
                    for (folder, _suffix), paths in sorted(copies.items()):
                        key = tuple(sorted(str(path) for path in paths))
                        if key not in seen:
                            seen.add(key)
                            text = (f"Sposta nel cestino questa copia ({len(paths)} file)…" if rule == "R32" else
                                    f"Sposta nel cestino la copia in {short_folder(folder)} ({len(paths)} file)…")
                            action = menu.addAction(text)
                            action.setToolTip("Mostra l'elenco dei file e chiede conferma; si recuperano dal Cestino "
                                              "di Windows")
                            action.triggered.connect(
                                lambda _checked=False, chosen=paths, issue=problem.issue: self._trash_copy(chosen, issue))

    def _trash_copy(self, paths: list, issue) -> None:
        """Sposta nel Cestino di Windows i file di una copia doppia, dopo l'elenco e la conferma; poi Rileggi."""
        from PySide6.QtCore import QFile
        existing = []
        for path in paths:
            if path.is_file():
                existing.append(path)
        if not existing:
            QMessageBox.information(self, "Sposta nel cestino", "I file non ci sono più su questo PC.")
        else:
            names = []
            for path in existing[:15]:
                names.append(f"• {path}")
            if len(existing) > 15:
                names.append(f"… e altri {len(existing) - 15}")
            box = QMessageBox(QMessageBox.Warning, "Sposta nel cestino",
                              f"Spostare nel Cestino di Windows {len(existing)} file di questa copia dell'album?",
                              QMessageBox.Yes | QMessageBox.No, self)
            box.setInformativeText(issue.detail + "\n\n" + "\n".join(names) + "\n\nSi recuperano dal Cestino. "
                                   "Sull'iPhone non cambia niente.")
            box.setDefaultButton(QMessageBox.No)
            if box.exec() == QMessageBox.Yes:
                failed = []
                moved = 0
                for path in existing:
                    if QFile.moveToTrash(str(path)):
                        moved += 1
                    else:
                        failed.append(str(path))
                if failed:
                    QMessageBox.warning(self, "Sposta nel cestino", "Non spostati nel Cestino:\n" + "\n".join(failed))
                self.window.statusBar().showMessage(f"{moved} file nel Cestino. Rileggo la cartella: poi Controlla di "
                                                    "nuovo questi album per aggiornare i risultati.", 10000)
                self.window.reload_folder()

    @staticmethod
    def _add_accepted_rows(child, problem) -> None:
        """Le correzioni di un problema che va bene così: si vedono, in grigio, ma senza casella."""
        for row in problem.rows:
            leaf = _item(len(COLUMNS), {COL_NAME: row.target.name, COL_SIDE: tr(SIDE_LABELS[row.target.side]),
                                        COL_FIELD: tr(FIELD_LABELS.get(row.name, row.name)),
                                        COL_OLD: shown_value(row.name, row.old), COL_NEW: shown_value(row.name, row.new)})
            leaf.setFlags(leaf.flags() & ~Qt.ItemIsUserCheckable)
            for column in range(len(COLUMNS)):
                leaf.setForeground(column, QBrush(GREY))
            child.addChild(leaf)

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
        """La casella dell'album secondo le sue correzioni ancora da applicare (solo gli album che ne hanno, senza
        quelle che vanno bene così)."""
        open_rows = False
        for problem in self.entries[top.data(COL_NAME, REF_ROLE)].problems:
            if problem.rows and not problem.accepted:
                open_rows = True
        if open_rows:
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

    def _pc_paths(self) -> list:
        """I file del PC dei brani delle righe selezionate (quelli solo sull'iPhone non ne hanno)."""
        result = []
        for target in self._selected_targets():
            if target.pc is not None and target.pc.path not in result:
                result.append(target.pc.path)
        return result

    def _update_buttons(self) -> None:
        chosen = len(self.chosen_rows())
        self.apply_button.setEnabled(chosen > 0 and not self.live)
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
                html = self._album_html(entry)
        else:
            html = ("<p>Seleziona un album o un problema per vederne i dettagli e cosa fare.</p><p><b>Correzione "
                    "automatica</b> (in verde): il problema ha righe con la casella; lascia accese quelle che vuoi e "
                    "premi <i>Applica le correzioni scelte</i>. <b>A mano</b> (in arancione): il programma non lo "
                    "corregge da solo; <i>Cosa fare</i> dice come.</p>")
        self.detail.setHtml(html)
        self._update_buttons()

    @staticmethod
    def _album_html(entry) -> str:
        """Il dettaglio di un album: i problemi che si correggono qui e quelli da fare a mano, con Cosa fare."""
        automatic = ""
        manual = ""
        elsewhere = ""
        for problem in entry.problems:
            suggestion = advice(problem.issue)
            line = f"<li><b>{escape(tr(problem.issue.title))}</b>"
            if suggestion:
                line += f"<br>{escape(tr(suggestion))}"
            line += "</li>"
            if problem.rows:
                automatic += line
            elif problem.elsewhere:
                elsewhere += (f"<li><b>{escape(tr(problem.issue.title))}</b><br>"
                              f"{escape(_albums_text(problem.elsewhere))}</li>")
            else:
                manual += line
        html = f"<h3>{escape(entry.title)}</h3><p>{escape(tr(SIDE_LABELS.get(entry.side, '')))}</p>"
        if automatic:
            html += ("<p style='color:#1e8c3c'><b>Si correggono qui</b>: lascia accese le caselle delle righe che vuoi "
                     f"e premi <i>Applica le correzioni scelte</i>.</p><ul>{automatic}</ul>")
        if manual:
            html += (f"<p style='color:#d28200'><b>Da fare a mano</b> (nessuna correzione automatica):</p>"
                     f"<ul>{manual}</ul>")
        if elsewhere:
            html += ("<p style='color:gray'><b>Si correggono nell'altro album</b> (qui c'è già la forma giusta, niente "
                     f"da fare):</p><ul>{elsewhere}</ul>")
        return html

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
            removed = self._run_plan(plan, dialog)
            done = []
            for index in indexes:
                row = self._rows[index]
                # un vecchio tag è fatto solo se è stato tolto davvero (l'elenco approvato con la sua casella)
                if row.name not in OLD_TAG_NAMES or (id(row.target.pc), row.name) in removed:
                    done.append(index)
            self._mark_applied(done)

    def _run_plan(self, plan, dialog) -> set:
        """Le correzioni dalla parte giusta: sul PC in sospeso (e nei file, dopo l'elenco da approvare), sull'iPhone
        in attesa (Usa i tag da PC a iPhone per i collegati, Cambia i tag per quelli solo sull'iPhone). Restituisce
        i vecchi tag tolti dai file, {(id del brano del PC, tags.OLD_ID3V1 / OLD_APE)}."""
        removed = set()
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
        old_tags = {}
        written = {id(track) for track in to_write}
        if dialog.old_files.isChecked():
            for track, names in plan.old_tags:
                old_tags[id(track)] = names
                if id(track) not in written:
                    written.add(id(track))
                    to_write.append(track)
        if to_write:
            approved = offer_pc_write(window, self, to_write, "Applica le correzioni",
                                      "si scrivono nel file le correzioni dei campi scelti", old_tags)
            for track, _tags, fields in approved:
                for name in fields:
                    if name in OLD_TAG_NAMES:
                        removed.add((id(track), name))
        elif pairs:
            window.statusBar().showMessage(f"Correzioni salvate in sospeso su {len(pairs)} brani del PC: i file non "
                                           "cambiano", 8000)
        result = removed
        return result

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
