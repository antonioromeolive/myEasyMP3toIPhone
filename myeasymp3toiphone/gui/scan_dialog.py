# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Controlla la musica dall'interfaccia: cosa controllare (i brani aperti o la musica dell'app Musica dell'iPhone) e
quali controlli fare, l'avvio e i risultati, da cui si applicano le correzioni. Scelte e risultati stanno nella
linguetta Controlli (embedded=True: dentro la linguetta, con "Avvia il controllo" e senza "Chiudi")."""

from __future__ import annotations

from html import escape

from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QDialogButtonBox, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QMessageBox, QPushButton, QRadioButton, QSplitter, QStyle, QTextBrowser, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)

from ..ai import make_provider
from ..config import config_dir, load_profiles
from ..i18n import tr
from ..library import scan_folder
from ..phone_library import tracks_for_scan
from ..scan import (
    CHECK_DUPLICATES, CHECK_FILES, CHECK_VARIANTS, CHECKS, KIND_LABELS, ORIGIN_AI, SEVERITY_HIGH, SEVERITY_MEDIUM, save_report,
    scan_tracks, tag_changes_of,
)

TITLE = "Controlla la musica"
REPORTS_FOLDER = "scansioni"
GREEN = QColor(30, 140, 60)
GREY = QColor(130, 130, 130)


class ScanTargetDialog(QDialog):
    """Cosa controllare, quali controlli fare (ricordati) e se usare l'AI. embedded: dentro la linguetta Controlli,
    con il pulsante "Avvia il controllo" (start_requested) al posto di Avvia/Annulla; refresh() rifà le scelte che
    dipendono da cosa è aperto."""

    start_requested = Signal()

    def __init__(self, window, phone_count: int, profile_name: str, embedded: bool = False) -> None:
        super().__init__(window)
        self.setWindowTitle(TITLE)
        if embedded:
            self.setWindowFlags(Qt.Widget)
        self.local = QRadioButton()
        self.device = QRadioButton()

        off = set(window.app_settings.scan_checks_off)
        self.boxes = {}
        grid = QGridLayout()
        for row, (check_id, label, note) in enumerate(CHECKS):
            box = QCheckBox(label)
            box.setChecked(check_id not in off)
            box.toggled.connect(self._update_start)
            explanation = QLabel(note)
            explanation.setWordWrap(True)
            explanation.setStyleSheet("color: gray")
            grid.addWidget(box, row, 0, Qt.AlignTop)
            grid.addWidget(explanation, row, 1)
            self.boxes[check_id] = box
        self.musicbrainz = QCheckBox("…e i nomi dubbi anche su MusicBrainz (nomi e alias dell'artista; lento: un "
                                     "artista al secondo, serve internet)")
        self.musicbrainz.setChecked(window.app_settings.scan_musicbrainz)
        self.boxes[CHECK_VARIANTS].toggled.connect(self.musicbrainz.setEnabled)
        self.musicbrainz.setEnabled(self.boxes[CHECK_VARIANTS].isChecked())
        grid.addWidget(self.musicbrainz, len(CHECKS), 0, 1, 2)
        grid.setColumnStretch(1, 1)
        group = QGroupBox("Cosa controllare")
        group.setLayout(grid)
        all_button = QPushButton("Tutti")
        all_button.clicked.connect(lambda: self._set_all(True))
        none_button = QPushButton("Nessuno")
        none_button.clicked.connect(lambda: self._set_all(False))
        choose = QHBoxLayout()
        choose.addWidget(all_button)
        choose.addWidget(none_button)
        choose.addStretch(1)

        self.use_ai = QCheckBox()
        note = QLabel("Brani duplicati: la prima volta si legge l'impronta dell'audio di ogni file (qualche minuto per "
                      "una collezione grande), poi si ricorda. Il rapporto resta nella cartella dati (scansioni).")
        note.setWordWrap(True)
        note.setStyleSheet("color: gray")
        layout = QVBoxLayout(self)
        layout.addWidget(self.local)
        layout.addWidget(self.device)
        layout.addWidget(group)
        layout.addLayout(choose)
        layout.addWidget(self.use_ai)
        layout.addWidget(note)
        if embedded:
            self.start_button = QPushButton("Avvia il controllo")
            self.start_button.setProperty("role", "go")
            self.start_button.clicked.connect(self.start_requested.emit)
            start_row = QHBoxLayout()
            start_row.addStretch(1)
            start_row.addWidget(self.start_button)
            layout.addLayout(start_row)
        else:
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            self.start_button = buttons.button(QDialogButtonBox.Ok)
            self.start_button.setText("Avvia")
            buttons.button(QDialogButtonBox.Cancel).setText("Annulla")
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)
            self.resize(760, 520)
        self.refresh(window, phone_count, profile_name)

    def refresh(self, window, phone_count: int, profile_name: str) -> None:
        """Le scelte che dipendono da cosa è aperto: i brani della scheda PC, la musica dell'iPhone, il profilo AI."""
        opened = window.open_description()
        self.local.setText(f"I brani aperti nella scheda PC ({opened})" if opened else "Nessuna cartella aperta")
        self.local.setEnabled(bool(opened) and bool(window.tracks))
        if phone_count:
            self.device.setText(f"La musica dell'app Musica dell'iPhone ({phone_count} brani, {window.phone_label}), "
                                "confrontata con le cartelle della musica del PC")
        else:
            self.device.setText("L'iPhone (connettilo una volta: la sua musica resta ricordata)")
        self.device.setEnabled(phone_count > 0)
        if self.local.isEnabled() and not self.device.isChecked():
            self.local.setChecked(True)
        elif not self.local.isEnabled():
            self.device.setChecked(self.device.isEnabled())
        self.use_ai.setText(f"Usa l'AI ({profile_name})" if profile_name else "Usa l'AI (scegli un profilo in "
                            "Impostazioni → Generale)")
        self.use_ai.setEnabled(bool(profile_name))
        self.use_ai.setChecked(bool(profile_name) and window.app_settings.scan_use_ai)
        self._update_start()

    def _set_all(self, checked: bool) -> None:
        for box in self.boxes.values():
            box.setChecked(checked)

    def _update_start(self) -> None:
        self.start_button.setEnabled((self.local.isEnabled() or self.device.isEnabled()) and bool(self.checks()))

    def checks(self) -> frozenset:
        chosen = set()
        for check_id, box in self.boxes.items():
            if box.isChecked():
                chosen.add(check_id)
        result = frozenset(chosen)
        return result

    def checks_off(self) -> list:
        result = []
        for check_id, box in self.boxes.items():
            if not box.isChecked():
                result.append(check_id)
        return result


class ScanLauncher:
    def __init__(self, window) -> None:
        self.window = window
        self.library_tracks = []
        self.musicbrainz = None

    def _profile(self):
        result = None
        name = self.window.app_settings.scan_profile
        for profile in load_profiles():
            if profile.name == name:
                result = profile
        return result

    def profile_name(self) -> str:
        profile = self._profile()
        result = profile.name if profile is not None else ""
        return result

    def start(self) -> None:
        """Le scelte in una finestra, poi il controllo (senza la linguetta Controlli)."""
        window = self.window
        dialog = ScanTargetDialog(window, len(window.phone_tracks), self.profile_name())
        if dialog.exec():
            self.run(dialog)

    def run(self, dialog) -> None:
        """Il controllo con le scelte fatte (finestra o linguetta Controlli), ricordate nelle impostazioni."""
        window = self.window
        profile = self._profile()
        if window.runner.is_busy:
            QMessageBox.information(window, TITLE, "Aspetta la fine dell'operazione in corso.")
        else:
            window.app_settings.scan_use_ai = dialog.use_ai.isChecked()
            window.app_settings.scan_checks_off = dialog.checks_off()
            window.app_settings.scan_musicbrainz = dialog.musicbrainz.isChecked()
            window.save_settings()
            provider = None
            if dialog.use_ai.isChecked() and profile is not None:
                provider = make_provider(profile)
            checks = dialog.checks()
            self.musicbrainz = None
            if dialog.musicbrainz.isChecked() and CHECK_VARIANTS in checks:
                self.musicbrainz = window.mb_client
            if dialog.device.isChecked():
                self._start_device(provider, checks)
            else:
                self._start_local(provider, checks)

    def _start_local(self, provider, checks: frozenset) -> None:
        from ..adoption import pc_fingerprints
        window = self.window
        tracks = window.format_tracks()
        target = window.open_description()
        self.library_tracks = tracks
        tag_cache = window.tag_cache
        musicbrainz = self.musicbrainz

        def work(progress, cancel):
            prints = {}
            if CHECK_DUPLICATES in checks:
                progress(0, 0, "impronte dell'audio")
                prints = pc_fingerprints(tracks, tag_cache, progress, cancel)
            value = scan_tracks(tracks, target, provider, check_files=CHECK_FILES in checks, progress=progress,
                                cancel=cancel, checks=checks, fingerprints=prints, musicbrainz=musicbrainz)
            return value

        window.runner.run("Controllo della musica", work, self._show)

    def _start_device(self, provider, checks: frozenset) -> None:
        from pathlib import Path

        from ..provenance import PhoneFingerprints
        window = self.window
        music = [folder for folder in window.music_dirs() if folder.is_dir()]
        loaded = list(window.tracks) if window.showing_music() else None
        phone_tracks = list(window.phone_tracks)
        target = f"iPhone, app Musica ({window.phone_label})"
        musicbrainz = self.musicbrainz

        def work(progress, cancel):
            tracks = tracks_for_scan(phone_tracks)
            library_tracks = loaded
            if library_tracks is None:
                library_tracks = []
                for folder in music:
                    library_tracks.extend(scan_folder(folder, progress, cancel, window.tag_cache))
                library_tracks = window.without_hidden(library_tracks)   # non le cartelle escluse
            window.overlay.apply(library_tracks)
            known = PhoneFingerprints(config_dir())
            prints = {}
            for item in phone_tracks:
                value = known.get(item.remote_path, item.size)    # solo quelle già lette da Associa sorgenti
                if value:
                    prints[str(Path(item.remote_path))] = value
            report = scan_tracks(tracks, target, provider, check_files=False, phone_tracks=phone_tracks,
                                 library_tracks=library_tracks, progress=progress, cancel=cancel, checks=checks,
                                 fingerprints=prints, musicbrainz=musicbrainz)
            value = (report, library_tracks)
            return value

        def done(value):
            report, library_tracks = value
            self.library_tracks = library_tracks
            self._show(report)

        window.runner.run("Controllo della musica dell'iPhone", work, done)

    def _show(self, report) -> None:
        saved = None
        try:
            saved = save_report(report, config_dir() / REPORTS_FOLDER)
        except OSError as exc:
            QMessageBox.warning(self.window, TITLE, f"Rapporto non salvato: {exc}")
        panel = getattr(self.window, "checks_panel", None)
        if panel is not None:
            panel.show_scan_results(ScanDialog(report, saved, self, embedded=True))
        else:
            ScanDialog(report, saved, self).exec()


class ScanDialog(QDialog):
    """I risultati di Controlla la musica; embedded: dentro la linguetta Controlli, senza "Chiudi"."""

    def __init__(self, report, saved, launcher: ScanLauncher, embedded: bool = False) -> None:
        super().__init__(launcher.window)
        self.setWindowTitle(f"{TITLE}: {report.target}")
        if embedded:
            self.setWindowFlags(Qt.Widget)
        else:
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
            summary += " — <b>controllo interrotto: risultati parziali</b>"
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
        buttons = QHBoxLayout()
        buttons.addWidget(self.fix_button)
        buttons.addWidget(self.show_button)
        buttons.addStretch(1)
        buttons.addWidget(open_button)
        if not embedded:
            close_button = QPushButton("Chiudi")
            close_button.clicked.connect(self.accept)
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
                top = QTreeWidgetItem([f"{tr(KIND_LABELS[kind])} ({len(issues)})", "", "", ""])
                font = top.font(0)
                font.setBold(True)
                top.setFont(0, font)
                top.setFlags(top.flags() & ~Qt.ItemIsSelectable)
                self.tree.addTopLevelItem(top)
                for issue in issues:
                    fix_text = "sì" if issue.fix is not None else ""
                    child = QTreeWidgetItem([tr(issue.title), tr(issue.severity), tr(issue.origin), tr(fix_text)])
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
            detail = escape(tr(issue.detail)).replace("\n", "<br>")
            html = f"<h3>{escape(tr(issue.title))}</h3><p>{detail}</p>"
            if issue.origin == ORIGIN_AI:
                html += "<p><i>Trovato dall'AI.</i></p>"
            if issue.ai_note:
                html += f"<p><b>L'AI ritiene che non sia un problema:</b> {escape(issue.ai_note)}</p>"
            if index in self.fixed:
                html += "<p style='color:#1e8c3c'><b>Correzione applicata.</b></p>"
            elif issue.fix is not None:
                html += f"<p><b>Correzione proposta:</b> {escape(tr(issue.fix.description))}</p>"
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
