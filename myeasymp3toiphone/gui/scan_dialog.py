# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La scansione dall'interfaccia: cosa scansionare (la cartella aperta o la musica dell'app Musica dell'iPhone), l'avvio
e la finestra dei risultati, da cui si applicano le correzioni."""

from __future__ import annotations

from html import escape

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QBrush, QColor, QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QDialogButtonBox, QHBoxLayout, QHeaderView, QLabel, QMessageBox,
    QPushButton, QRadioButton, QSplitter, QStyle, QTextBrowser, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)

from ..ai import make_provider
from ..config import config_dir, load_profiles
from ..library import scan_folder
from ..phone_library import tracks_for_scan
from ..scan import KIND_LABELS, ORIGIN_AI, SEVERITY_HIGH, SEVERITY_MEDIUM, save_report, scan_tracks, tag_changes_of

REPORTS_FOLDER = "scansioni"
GREEN = QColor(30, 140, 60)
GREY = QColor(130, 130, 130)


class ScanTargetDialog(QDialog):
    """Cosa scansionare e se usare l'AI."""

    def __init__(self, window, phone_count: int, profile_name: str) -> None:
        super().__init__(window)
        self.setWindowTitle("Scansione")
        folder = window.root_folder
        self.local = QRadioButton(f"I brani della cartella aperta ({folder})" if folder else "Nessuna cartella aperta")
        self.local.setEnabled(folder is not None and bool(window.tracks))
        if phone_count:
            self.device = QRadioButton(f"La musica dell'app Musica dell'iPhone ({phone_count} brani, "
                                       f"{window.phone_label}), confrontata con la Libreria")
        else:
            self.device = QRadioButton("L'iPhone (connettilo una volta: la sua musica resta ricordata)")
        self.device.setEnabled(phone_count > 0)
        if self.local.isEnabled():
            self.local.setChecked(True)
        else:
            self.device.setChecked(self.device.isEnabled())
        self.use_ai = QCheckBox(f"Usa l'AI ({profile_name})" if profile_name else "Usa l'AI (scegli un profilo in "
                                "Impostazioni → Generale)")
        self.use_ai.setEnabled(bool(profile_name))
        self.use_ai.setChecked(bool(profile_name) and window.app_settings.scan_use_ai)
        note = QLabel("La scansione cerca: file che non si aggiornano, album con pochi brani, collezioni divise su più "
                      "album, brani doppi e tag mancanti. Il rapporto resta nella cartella dati (scansioni).")
        note.setWordWrap(True)
        note.setStyleSheet("color: gray")
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Avvia")
        buttons.button(QDialogButtonBox.Ok).setEnabled(self.local.isEnabled() or self.device.isEnabled())
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.local)
        layout.addWidget(self.device)
        layout.addWidget(self.use_ai)
        layout.addWidget(note)
        layout.addWidget(buttons)
        self.resize(620, 220)


class ScanLauncher:
    def __init__(self, window) -> None:
        self.window = window
        self.library_tracks = []

    def _profile(self):
        result = None
        name = self.window.app_settings.scan_profile
        for profile in load_profiles():
            if profile.name == name:
                result = profile
        return result

    def start(self) -> None:
        window = self.window
        profile = self._profile()
        dialog = ScanTargetDialog(window, len(window.phone_tracks), profile.name if profile else "")
        if dialog.exec():
            window.app_settings.scan_use_ai = dialog.use_ai.isChecked()
            window.save_settings()
            provider = None
            if dialog.use_ai.isChecked() and profile is not None:
                provider = make_provider(profile)
            if dialog.device.isChecked():
                self._start_device(provider)
            else:
                self._start_local(provider)

    def _start_local(self, provider) -> None:
        window = self.window
        tracks = window.format_tracks()
        target = str(window.root_folder)
        self.library_tracks = tracks

        def work(progress, cancel):
            value = scan_tracks(tracks, target, provider, check_files=True, progress=progress, cancel=cancel)
            return value

        window.runner.run("Scansione", work, self._show)

    def _start_device(self, provider) -> None:
        window = self.window
        library = window.library_dir()
        loaded = list(window.tracks) if window.root_folder == library else None
        phone_tracks = list(window.phone_tracks)
        target = f"iPhone, app Musica ({window.phone_label})"

        def work(progress, cancel):
            tracks = tracks_for_scan(phone_tracks)
            library_tracks = loaded
            if library_tracks is None:
                library_tracks = scan_folder(library, progress, cancel, window.tag_cache) if library.is_dir() else []
            window.overlay.apply(library_tracks)
            report = scan_tracks(tracks, target, provider, check_files=False, phone_tracks=phone_tracks,
                                 library_tracks=library_tracks, progress=progress, cancel=cancel)
            value = (report, library_tracks)
            return value

        def done(value):
            report, library_tracks = value
            self.library_tracks = library_tracks
            self._show(report)

        window.runner.run("Scansione dell'iPhone", work, done)

    def _show(self, report) -> None:
        saved = None
        try:
            saved = save_report(report, config_dir() / REPORTS_FOLDER)
        except OSError as exc:
            QMessageBox.warning(self.window, "Scansione", f"Rapporto non salvato: {exc}")
        ScanDialog(report, saved, self).exec()


class ScanDialog(QDialog):
    def __init__(self, report, saved, launcher: ScanLauncher) -> None:
        super().__init__(launcher.window)
        self.setWindowTitle(f"Scansione: {report.target}")
        self.resize(1150, 680)
        self.report = report
        self.saved = saved
        self.launcher = launcher
        self.window = launcher.window
        self.fixed = set()

        summary = (f"<b>{len(report.issues)} problemi</b> in {report.tracks_scanned} brani e "
                   f"{report.albums_scanned} album")
        if report.ai_profile:
            summary += f" — analisi AI con {escape(report.ai_profile)}"
        if report.cancelled:
            summary += " — <b>scansione interrotta: risultati parziali</b>"
        for error in report.ai_errors[:3]:
            summary += f"<br><span style='color:#c33'>Errore AI: {escape(error)}</span>"
        header = QLabel(summary)
        header.setWordWrap(True)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Problema", "Gravità", "Origine", "Correzione"])
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setStretchLastSection(False)
        self.tree.setColumnWidth(1, 70)
        self.tree.setColumnWidth(2, 70)
        self.tree.setColumnWidth(3, 110)
        self.tree.itemSelectionChanged.connect(self._show_detail)
        self.detail = QTextBrowser()
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.tree)
        splitter.addWidget(self.detail)
        splitter.setSizes([420, 200])

        self.fix_button = QPushButton("Applica la correzione")
        self.fix_button.clicked.connect(self._apply)
        self.show_button = QPushButton("Mostra i brani")
        self.show_button.setToolTip("Seleziona questi brani nella scheda PC")
        self.show_button.clicked.connect(self._show_tracks)
        open_button = QPushButton("Apri il rapporto")
        open_button.setEnabled(saved is not None)
        open_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(saved))))
        close_button = QPushButton("Chiudi")
        close_button.clicked.connect(self.accept)
        buttons = QHBoxLayout()
        buttons.addWidget(self.fix_button)
        buttons.addWidget(self.show_button)
        buttons.addStretch(1)
        buttons.addWidget(open_button)
        buttons.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(splitter, 1)
        layout.addLayout(buttons)
        self._fill()
        self._show_detail()

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
        by_kind = {}
        for issue in self.report.issues:
            by_kind.setdefault(issue.kind, []).append(issue)
        for kind in KIND_LABELS:
            issues = by_kind.get(kind, [])
            if issues:
                top = QTreeWidgetItem([f"{KIND_LABELS[kind]} ({len(issues)})", "", "", ""])
                font = top.font(0)
                font.setBold(True)
                top.setFont(0, font)
                top.setFlags(top.flags() & ~Qt.ItemIsSelectable)
                self.tree.addTopLevelItem(top)
                for issue in issues:
                    fix_text = "sì" if issue.fix is not None else ""
                    child = QTreeWidgetItem([issue.title, issue.severity, issue.origin, fix_text])
                    child.setIcon(0, self._icon(issue.severity))
                    child.setData(0, Qt.UserRole, self.report.issues.index(issue))
                    if issue.ai_note:
                        for column in range(4):
                            child.setForeground(column, QBrush(GREY))
                        child.setToolTip(0, f"L'AI ritiene che non sia un problema: {issue.ai_note}")
                    top.addChild(child)
                top.setExpanded(True)

    def _selected_issues(self) -> list:
        result = []
        for item in self.tree.selectedItems():
            index = item.data(0, Qt.UserRole)
            if index is not None:
                result.append((index, self.report.issues[index]))
        return result

    def _show_detail(self) -> None:
        selected = self._selected_issues()
        if selected:
            index, issue = selected[0]
            html = f"<h3>{escape(issue.title)}</h3><p>{escape(issue.detail)}</p>"
            if issue.origin == ORIGIN_AI:
                html += "<p><i>Trovato dall'AI.</i></p>"
            if issue.ai_note:
                html += f"<p><b>L'AI ritiene che non sia un problema:</b> {escape(issue.ai_note)}</p>"
            if index in self.fixed:
                html += "<p style='color:#1e8c3c'><b>Correzione applicata.</b></p>"
            elif issue.fix is not None:
                html += f"<p><b>Correzione proposta:</b> {escape(issue.fix.description)}</p>"
            files = "".join(f"<li>{escape(str(path))}</li>" for path in issue.files[:200])
            more = f"<p>… e altri {len(issue.files) - 200}</p>" if len(issue.files) > 200 else ""
            html += f"<p><b>{len(issue.files)} file:</b></p><ul>{files}</ul>{more}"
            self.detail.setHtml(html)
        else:
            self.detail.setHtml("<p>Seleziona un problema per vederne i dettagli.</p>")
        fixable = False
        for index, issue in selected:
            fixable = fixable or (issue.fix is not None and index not in self.fixed)
        self.fix_button.setEnabled(fixable)
        self.show_button.setEnabled(bool(selected))

    def _show_tracks(self) -> None:
        paths = set()
        for _index, issue in self._selected_issues():
            for path in issue.files:
                paths.add(str(path))
        self.window.show_tracks(paths)

    def _mark_fixed(self, indexes: list) -> None:
        for index in indexes:
            self.fixed.add(index)
        iterator = []
        for top_index in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(top_index)
            for child_index in range(top.childCount()):
                iterator.append(top.child(child_index))
        for item in iterator:
            if item.data(0, Qt.UserRole) in self.fixed:
                item.setText(3, "applicata")
                item.setForeground(3, QBrush(GREEN))
        self._show_detail()

    def _apply(self) -> None:
        local = []
        for index, issue in self._selected_issues():
            if issue.fix is not None and index not in self.fixed:
                local.append((index, issue))
        if local:
            self._apply_local(local)

    def _apply_local(self, items: list) -> None:
        """Le correzioni dei tag restano in sospeso per le copie dell'iPhone: i file sul PC non cambiano."""
        descriptions = "\n".join(f"• {issue.fix.description}" for _index, issue in items)
        answer = QMessageBox.question(
            self, "Applica la correzione",
            f"Salvare queste modifiche per l'iPhone?\n\n{descriptions}\n\nI file sul PC non cambiano: le modifiche "
            "vanno sulle copie che invierai all'iPhone.")
        if answer == QMessageBox.Yes:
            by_path = {}
            for track in self.window.tracks:
                by_path[str(track.path)] = track
            pairs = []
            missing = 0
            for _index, issue in items:
                for path, values in tag_changes_of(issue.fix):
                    track = by_path.get(str(path))
                    if track is None:
                        missing += 1
                    else:
                        new_tags = track.tags.copy()
                        for name, value in values.items():
                            setattr(new_tags, name, value)
                        pairs.append((track, new_tags))
            self.window.apply_tag_changes(pairs)
            self._mark_fixed([index for index, _issue in items])
            message = f"Modifiche salvate per l'iPhone su {len(pairs)} brani. Inviali all'iPhone per applicarle."
            if missing:
                message += f"\n{missing} brani non sono più nella cartella aperta: ripeti la scansione."
            QMessageBox.information(self, "Applica la correzione", message)
