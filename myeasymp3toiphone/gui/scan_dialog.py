# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Il controllo della linguetta Controlli: su cosa (le scelte di check_options), le regole, l'Analisi AI e la Verifica
online (anche solo sugli album con problemi), il rapporto nella cartella dati e i risultati per album
(check_results)."""

from __future__ import annotations

import copy

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

from ..accepted import Accepted
from ..ai import make_provider
from ..albumcheck import ai_chooser, check_album_services
from ..check_flow import Target, filter_accepted, group_by_album as entries_by_album, online_issues
from ..config import config_dir, load_profiles
from ..library import UNKNOWN_ALBUM, group_by_album, scan_folder
from ..phone_library import tracks_for_scan
from ..scan import (
    CHECK_DUPLICATES, CHECK_FILES, CHECK_VARIANTS, ORIGIN_AI, ORIGIN_ONLINE, ai_review, albums_of_issues,
    ScanReport, drop_repeated, enabled, is_cancelled, report_text, save_report, scan_tracks,
)
from .check_options import SIDE_PC, SIDE_PHONE

TITLE = "Controlla la musica"
LIVE_SCANNED = "brani_controllati"     # i risultati man mano: i brani, i problemi, un album verificato online
LIVE_ISSUES = "problemi_finora"
LIVE_ONLINE = "album_verificato"
LIVE_DELAY_MS = 1500                   # i risultati man mano si ridisegnano al più una volta ogni tanto
STAGE_AI = "di_nuovo_ai"
STAGE_ONLINE = "di_nuovo_online"
REPORTS_FOLDER = "scansioni"


def online_check(scanned: list, issues: list, clients: list, flagged_only: bool, chooser, progress, cancel,
                 on_result=None, skip=None) -> list:
    """Verifica online gli album dei brani controllati (con flagged_only solo quelli toccati dai problemi): i
    risultati (albumcheck.AlbumCheckResult), uno per album, anche man mano con on_result(risultato). Gli album senza
    nome si saltano, e quelli per cui skip(album_key) (vanno bene così)."""
    groups = group_by_album(scanned)
    wanted = albums_of_issues(issues, scanned) if flagged_only else None
    keys = []
    for key in sorted(groups, key=lambda k: (k[0].lower(), k[1].lower())):
        if key[1] != UNKNOWN_ALBUM and (wanted is None or key in wanted) and (skip is None or not skip(key)):
            keys.append(key)
    results = []
    index = 0
    while index < len(keys) and not is_cancelled(cancel):
        artist, album = keys[index]
        progress(index, len(keys), f"verifica online: {artist} — {album}")
        result = check_album_services(clients, groups[keys[index]], chooser)
        results.append(result)
        if on_result is not None and not is_cancelled(cancel):
            on_result(result)
        index += 1
    return results


class ScanLauncher:
    def __init__(self, window) -> None:
        self.window = window
        self.library_tracks = []
        self._last_phone = []          # [(Track della scansione, PhoneTrack)] dell'ultimo controllo dell'iPhone
        self._last = {}                # l'ultimo controllo: rapporto, brani, risultati online (_show)
        self.applied = set()           # le correzioni già applicate dei suoi risultati (check_results)
        self._online_count = 0         # per i rule_id W*.N della Verifica online
        self.accepted = Accepted(config_dir())   # gli album che vanno bene così (accepted.py)
        self.show_accepted = False     # nei risultati anche i problemi che vanno bene così

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

    def _options(self):
        result = self.window.checks_panel.options
        return result

    def run(self, override: tuple = None) -> None:
        """Il controllo con le scelte della linguetta (ricordate nelle impostazioni). override: (parte, brani) al
        posto di quello che dice il riquadro "Si controlla" (Controlla di nuovo questi album)."""
        window = self.window
        options = self._options()
        if window.runner.is_busy:
            QMessageBox.information(window, TITLE, "Aspetta la fine dell'operazione in corso.")
        else:
            settings = window.app_settings
            settings.scan_use_ai = options.ai_box.isChecked()
            settings.scan_checks_off = options.checks_off()
            settings.scan_musicbrainz = options.musicbrainz.isChecked()
            settings.scan_ai_flagged = options.ai_flagged.isChecked()
            settings.scan_online = options.online_box.isChecked()
            settings.scan_online_flagged = options.online_flagged.isChecked()
            services = []
            for service, box in options.service_boxes.items():
                if box.isChecked():
                    services.append(service)
            settings.album_services = services
            window.save_settings()
            if override is not None:
                side, items = override
            else:
                side, items, _sentence, _names = options.scope()
            profile = self._profile()
            provider = make_provider(profile) if options.ai_on() and profile is not None else None
            self.accepted = Accepted(config_dir())     # anche dopo un cambio in Impostazioni
            clients = []
            for service in options.online_services():
                clients.append(window.album_clients[service])
            choices = {
                "checks": options.checks(),
                "provider": provider,
                "ai_flagged": options.ai_flagged_only(),
                "clients": clients,
                "online_flagged": options.online_flagged_only(),
                "chooser": ai_chooser(provider) if provider is not None and clients else None,
                "musicbrainz": window.mb_client if options.musicbrainz.isChecked() else None,
                "ai_skip": self.accepted.skip_ai,
                "online_skip": self.accepted.skip_online,
            }
            if not items:
                QMessageBox.information(window, TITLE, "Non c'è niente da controllare.")
            elif side == SIDE_PHONE:
                self._start_device(items, choices)
            else:
                self._start_local(items, choices)

    def run_again(self, keys: set, side: str) -> None:
        """Controlla di nuovo questi album: lo stesso controllo solo sugli album scelti nei risultati."""
        if side == SIDE_PHONE:
            items = []
            for scanned, item in self._last_phone:
                if scanned.album_key in keys:
                    items.append(item)
        else:
            items = []
            for track in self.window.format_tracks():
                if track.album_key in keys:
                    items.append(track)
        self.run((side, items))

    def _start_local(self, tracks: list, choices: dict) -> None:
        from ..adoption import pc_fingerprints
        window = self.window
        checks = choices["checks"]
        target = f"PC, {len(tracks)} brani"
        self.library_tracks = tracks
        tag_cache = window.tag_cache
        musicbrainz = choices["musicbrainz"] if CHECK_VARIANTS in checks else None

        def work(progress, cancel, emit):
            emit((LIVE_SCANNED, tracks, [], None))
            prints = {}
            if CHECK_DUPLICATES in checks:
                progress(0, 0, "impronte dell'audio")
                prints = pc_fingerprints(tracks, tag_cache, progress, cancel)
            report = scan_tracks(tracks, target, choices["provider"], check_files=CHECK_FILES in checks,
                                 progress=progress, cancel=cancel, checks=checks, fingerprints=prints,
                                 musicbrainz=musicbrainz, ai_flagged_only=choices["ai_flagged"],
                                 partial=lambda issues: emit((LIVE_ISSUES, issues)), ai_skip=choices["ai_skip"])
            emit((LIVE_ISSUES, list(report.issues)))
            results = self._online(tracks, report, choices, progress, cancel, emit)
            value = (report, results)
            return value

        self._begin(SIDE_PC, target)
        started = window.runner.run(TITLE, work,
                                    lambda value: self._show(value[0], value[1], SIDE_PC, tracks, [], checks),
                                    on_error=self._failed, on_item=self._live_item)
        self._started(started)

    def _start_device(self, items: list, choices: dict) -> None:
        from ..provenance import PhoneFingerprints
        window = self.window
        checks = choices["checks"]
        music = [folder for folder in window.music_dirs() if folder.is_dir()]
        loaded = list(window.tracks) if window.showing_music() else None
        target = f"iPhone, {len(items)} brani ({window.phone_label})"
        musicbrainz = choices["musicbrainz"] if CHECK_VARIANTS in checks else None

        def work(progress, cancel, emit):
            scanned = tracks_for_scan(items)
            library_tracks = loaded
            if library_tracks is None:
                library_tracks = []
                for folder in music:
                    library_tracks.extend(scan_folder(folder, progress, cancel, window.tag_cache))
                library_tracks = window.without_hidden(library_tracks)   # non le cartelle escluse
            window.overlay.apply(library_tracks)
            emit((LIVE_SCANNED, scanned, list(zip(scanned, items)), library_tracks))
            known = PhoneFingerprints(config_dir())
            prints = {}
            for track, item in zip(scanned, items):
                value = known.get(item.remote_path, item.size)    # solo quelle già lette da Associa sorgenti
                if value:
                    prints[str(track.path)] = value
            # il confronto con il PC vale per i brani controllati; i fantasmi e i brani senza sorgente pure
            report = scan_tracks(scanned, target, choices["provider"], check_files=False, phone_tracks=items,
                                 library_tracks=library_tracks, progress=progress, cancel=cancel, checks=checks,
                                 fingerprints=prints, musicbrainz=musicbrainz, ai_flagged_only=choices["ai_flagged"],
                                 keep_phone_fixes=True, partial=lambda issues: emit((LIVE_ISSUES, issues)),
                                 ai_skip=choices["ai_skip"])
            emit((LIVE_ISSUES, list(report.issues)))
            results = self._online(scanned, report, choices, progress, cancel, emit)
            value = (report, results, scanned, library_tracks)
            return value

        def done(value):
            report, results, scanned, library_tracks = value
            self.library_tracks = library_tracks
            self._show(report, results, SIDE_PHONE, scanned, list(zip(scanned, items)), checks)

        self._begin(SIDE_PHONE, target)
        started = window.runner.run(f"{TITLE} (iPhone)", work, done, on_error=self._failed, on_item=self._live_item)
        self._started(started)

    @staticmethod
    def _online(scanned: list, report, choices: dict, progress, cancel, emit=None) -> list:
        """La Verifica online, se è scelta: i suoi problemi entrano nel rapporto; restituisce i risultati. Annullata
        (anche prima di cominciare, durante l'AI) è come non scelta: niente risultati, e il rapporto lo dice."""
        results = []
        if choices["clients"]:
            if not is_cancelled(cancel):
                on_result = (lambda result: emit((LIVE_ONLINE, result))) if emit is not None else None
                results = online_check(scanned, report.issues, choices["clients"], choices["online_flagged"],
                                       choices["chooser"], progress, cancel, on_result, choices["online_skip"])
            if is_cancelled(cancel):
                results = []
                if "Verifica online" not in report.stopped:
                    report.stopped.append("Verifica online")
            number = 0
            for result in results:
                number += 1
                report.issues.extend(online_issues(result, number))
            report.issues.sort(key=lambda issue: issue.sort_key())
        return results

    # ------------------------------------------------------------------ man mano

    def _begin(self, side: str, target: str) -> None:
        """Un controllo comincia: il pulsante diventa Ferma, i risultati arriveranno man mano."""
        self._live = {"side": side, "target": target, "scanned": [], "pairs": [], "issues": [], "online": [],
                      "resolve": None}
        self._live_pending = False
        self._options().set_running(True)

    def _started(self, started: bool) -> None:
        if not started:
            self._options().set_running(False)

    def _failed(self, message: str) -> None:
        self._live = None
        self._options().set_running(False)
        QMessageBox.warning(self.window, TITLE, f"Il controllo non è riuscito: {message}")

    def _live_item(self, item) -> None:
        """Un risultato parziale dal controllo in corso: i brani, i problemi finora, un album verificato online. Si
        ridisegna al più ogni LIVE_DELAY_MS."""
        live = getattr(self, "_live", None)
        if live is not None:
            kind = item[0]
            if kind == LIVE_SCANNED:
                live["scanned"] = item[1]
                live["pairs"] = item[2]
                if item[3] is not None:
                    self.library_tracks = item[3]
                live["resolve"] = None
            elif kind == LIVE_ISSUES:
                live["issues"] = item[1]
            else:
                live["online"].append(item[1])
            if not self._live_pending and kind != LIVE_SCANNED:
                self._live_pending = True
                QTimer.singleShot(LIVE_DELAY_MS, self._show_live)

    def _show_live(self) -> None:
        from .check_results import CheckResultsView
        self._live_pending = False
        live = getattr(self, "_live", None)
        if live is not None and live["scanned"]:
            scanned = live["scanned"]
            if live["resolve"] is None:
                live["resolve"] = self._resolver(live["side"], scanned, live["pairs"])
                live["albums"] = len(group_by_album(scanned))
            report = ScanReport(target=live["target"], tracks_scanned=len(scanned), albums_scanned=live["albums"])
            issues = list(live["issues"])
            online = {}
            number = 0
            for result in live["online"]:
                number += 1
                issues.extend(online_issues(result, number))
                if result.local_tracks:
                    online[result.local_tracks[0].album_key] = result
            issues.sort(key=lambda issue: issue.sort_key())
            report.issues = issues
            entries, hidden = filter_accepted(entries_by_album(issues, live["resolve"]), self.accepted,
                                              self.show_accepted)
            panel = self.window.checks_panel
            state = panel.results.state() if isinstance(panel.results, CheckResultsView) else None
            view = CheckResultsView(self, report, entries, None, online, live["side"], live=True, hidden=hidden)
            view.restore(state)
            panel.show_results(view, switch=False)

    # ------------------------------------------------------------------ di nuovo, solo l'AI o solo online

    def online_clients(self) -> list:
        """I cataloghi scelti nella linguetta (anche con la Verifica online spenta), per Controlla online."""
        options = self._options()
        result = []
        for service, box in options.service_boxes.items():
            if box.isChecked() and box.isEnabled():
                result.append(self.window.album_clients[service])
        return result

    def _inside(self, issue, keys: set) -> bool:
        """Tutti i file del problema sono brani degli album keys (dell'ultimo controllo)."""
        by_path = self._last["by_path"]
        result = bool(issue.files)
        for path in issue.files:
            track = by_path.get(str(path))
            if track is None or track.album_key not in keys:
                result = False
        return result

    def recheck(self, stage: str, keys: set) -> None:
        """Dai risultati, tasto destro: di nuovo l'Analisi AI (STAGE_AI) o la Verifica online (STAGE_ONLINE), solo
        sugli album keys; i loro risultati di prima si sostituiscono. Annullato: restano quelli di prima."""
        window = self.window
        last = self._last
        scanned = []
        for track in last["scanned"]:
            if track.album_key in keys:
                scanned.append(track)
        profile = self._profile()
        if window.runner.is_busy:
            QMessageBox.information(window, TITLE, "Aspetta la fine dell'operazione in corso.")
        elif not scanned:
            QMessageBox.information(window, TITLE, "Questi album non sono tra quelli controllati.")
        elif stage == STAGE_AI and profile is None:
            QMessageBox.information(window, TITLE, "Scegli l'AI della scansione in Impostazioni → Generale.")
        elif stage == STAGE_AI:
            self._recheck_ai(make_provider(profile), scanned, keys)
        elif not self.online_clients():
            QMessageBox.information(window, TITLE, "Scegli almeno un catalogo sotto Verifica online.")
        else:
            self._recheck_online(scanned, keys)

    def _recheck_ai(self, provider, scanned: list, keys: set) -> None:
        report = self._last["report"]
        pairs = []
        for issue in report.issues:
            if issue.rule_id and issue.origin != ORIGIN_AI and self._touches(issue, keys):
                copied = copy.copy(issue)
                copied.ai_note = ""
                pairs.append((issue, copied))
        copies = []
        for _original, copied in pairs:
            copies.append(copied)

        def work(progress, cancel):
            found, errors = ai_review(provider, scanned, copies, progress, cancel)
            value = (found, errors, is_cancelled(cancel))
            return value

        def done(value):
            found, errors, cancelled = value
            self._options().set_running(False)
            if cancelled:
                self.window.statusBar().showMessage("Analisi AI annullata: i risultati restano quelli di prima", 8000)
            else:
                for original, copied in pairs:
                    original.ai_note = copied.ai_note
                kept = []
                for issue in report.issues:
                    if not (issue.origin == ORIGIN_AI and not issue.rule_id and self._inside(issue, keys)):
                        kept.append(issue)
                checks = self._last["checks"]
                for issue in drop_repeated(found, kept):
                    if not checks or enabled(issue, checks):
                        kept.append(issue)
                kept.sort(key=lambda issue: issue.sort_key())
                report.issues = kept
                report.ai_profile = provider.profile.name
                report.ai_errors = errors
                self._refresh()

        self._options().set_running(True)
        self._started(self.window.runner.run(f"Analisi AI di {len(keys)} album", work, done, on_error=self._failed))

    def _recheck_online(self, scanned: list, keys: set) -> None:
        report = self._last["report"]
        clients = self.online_clients()
        profile = self._profile()
        options = self._options()
        chooser = ai_chooser(make_provider(profile)) if profile is not None and options.ai_on() else None

        def work(progress, cancel):
            results = online_check(scanned, [], clients, False, chooser, progress, cancel)
            value = (results, is_cancelled(cancel))
            return value

        def done(value):
            results, cancelled = value
            self._options().set_running(False)
            if cancelled:
                self.window.statusBar().showMessage("Verifica online annullata: i risultati restano quelli di prima",
                                                    8000)
            else:
                kept = []
                for issue in report.issues:
                    if not (issue.origin == ORIGIN_ONLINE and self._inside(issue, keys)):
                        kept.append(issue)
                for result in results:
                    self._online_count += 1
                    kept.extend(online_issues(result, self._online_count))
                    self._remember_online(result)
                kept.sort(key=lambda issue: issue.sort_key())
                report.issues = kept
                if "Verifica online" in report.stopped:
                    report.stopped.remove("Verifica online")
                self._refresh()

        self._options().set_running(True)
        self._started(self.window.runner.run(f"Verifica online di {len(keys)} album", work, done,
                                             on_error=self._failed))

    def _touches(self, issue, keys: set) -> bool:
        by_path = self._last["by_path"]
        result = False
        for path in issue.files:
            track = by_path.get(str(path))
            if track is not None and track.album_key in keys:
                result = True
        return result

    def _remember_online(self, result) -> None:
        if result.local_tracks:
            self._last["online"][result.local_tracks[0].album_key] = result
            if self._last["side"] == SIDE_PC:
                self.window.store_check_result(result)           # l'icona accanto all'album negli elenchi

    # ------------------------------------------------------------------ va bene così

    def set_accepted(self, pairs: list, accepted: bool) -> None:
        """Segna (o toglie) "va bene così" per [(album_key, tipo)] e rifà i risultati."""
        for key, kind in pairs:
            if accepted:
                self.accepted.accept(key, kind)
            else:
                self.accepted.remove(key, kind)
        try:
            self.accepted.save()
        except OSError as exc:
            QMessageBox.warning(self.window, TITLE, f"Non salvato nella cartella dati: {exc}")
        self._redraw()

    def set_show_accepted(self, show: bool) -> None:
        self.show_accepted = show
        self._redraw()

    def _redraw(self) -> None:
        """I risultati rifatti con la lista "va bene così" (anche durante un controllo)."""
        if getattr(self, "_live", None) is not None:
            self._show_live()
        elif self._last:
            self._refresh(save=False)

    # ------------------------------------------------------------------ i risultati

    def _resolver(self, side: str, scanned: list, phone_pairs: list):
        """resolve(percorso) -> check_flow.Target (sempre lo stesso per lo stesso file), con il brano dell'altra parte
        se è collegato con certezza (registro)."""
        window = self.window
        by_path = {}
        if side == SIDE_PHONE:
            for track, item in phone_pairs:
                by_path[str(track.path)] = (track, None, item)
            for track in self.library_tracks:
                by_path.setdefault(str(track.path), (track, track, None))
        else:
            for track in scanned:
                by_path[str(track.path)] = (track, track, None)
        cache = {}

        def resolve(path):
            key = str(path)
            if key not in cache:
                found = by_path.get(key)
                target = None
                if found is not None:
                    track, pc, item = found
                    if item is not None:
                        target = Target(track, pc=window.iphone_panel.linked_pc(item), phone=item)
                    else:
                        target = Target(track, pc=pc, phone=window.linked_phone(pc))
                cache[key] = target
            result = cache[key]
            return result

        return resolve

    def _show(self, report, results: list, side: str, scanned: list, phone_pairs: list, checks=frozenset()) -> None:
        """I risultati di un controllo nuovo: si ricordano (per Controlla con l'AI / online) e si mostrano. Se l'AI era
        scelta e non ha risposto, lo dice un messaggio."""
        window = self.window
        self._live = None
        self._options().set_running(False)
        self._last_phone = phone_pairs
        by_path = {}
        for track in scanned:
            by_path[str(track.path)] = track
        self._last = {"report": report, "side": side, "scanned": scanned, "phone_pairs": phone_pairs, "online": {},
                      "by_path": by_path, "checks": checks, "saved": None,
                      "resolve": self._resolver(side, scanned, phone_pairs)}
        self.applied = set()
        self._online_count = len(results)
        try:
            self._last["saved"] = save_report(report, config_dir() / REPORTS_FOLDER)
        except OSError as exc:
            QMessageBox.warning(window, TITLE, f"Rapporto non salvato: {exc}")
        for result in results:
            self._remember_online(result)
        self._refresh(save=False)
        if report.ai_errors:
            shown = "\n".join(f"• {error[:300]}" for error in report.ai_errors[:3])
            QMessageBox.warning(window, TITLE, f"L'AI non ha risposto come doveva ({len(report.ai_errors)} errori): "
                                f"dove è mancata, i risultati sono solo quelli delle regole.\n\n{shown}")

    def _refresh(self, save: bool = True) -> None:
        """I risultati per album rifatti dal rapporto (dopo un controllo, o dopo Controlla con l'AI / online)."""
        from .check_results import CheckResultsView
        window = self.window
        last = self._last
        report = last["report"]
        if save and last["saved"] is not None:
            try:
                last["saved"].write_text(report_text(report), encoding="utf-8")
            except OSError as exc:
                QMessageBox.warning(window, TITLE, f"Rapporto non salvato: {exc}")
        if last["online"] and last["side"] == SIDE_PC:
            window.browser.refresh_check_icons(window.check_results)
        entries, hidden = filter_accepted(entries_by_album(report.issues, last["resolve"]), self.accepted,
                                          self.show_accepted)
        panel = window.checks_panel
        state = panel.results.state() if isinstance(panel.results, CheckResultsView) else None
        view = CheckResultsView(self, report, entries, last["saved"], last["online"], last["side"], hidden=hidden)
        view.restore(state)
        panel.show_results(view)
