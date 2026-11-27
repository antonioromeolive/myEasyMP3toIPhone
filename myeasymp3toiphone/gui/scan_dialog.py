# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Il controllo della linguetta Controlli: su cosa (le scelte di check_options), le regole, l'Analisi AI e la Verifica
online (anche solo sugli album con problemi), il rapporto nella cartella dati e i risultati per album
(check_results)."""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox

from ..ai import make_provider
from ..albumcheck import ai_chooser, check_album_services
from ..check_flow import Target, group_by_album as entries_by_album, online_issues
from ..config import config_dir, load_profiles
from ..library import UNKNOWN_ALBUM, group_by_album, scan_folder
from ..phone_library import tracks_for_scan
from ..scan import (
    CHECK_DUPLICATES, CHECK_FILES, CHECK_VARIANTS, albums_of_issues, is_cancelled, save_report, scan_tracks,
)
from .check_options import SIDE_PC, SIDE_PHONE

TITLE = "Controlla la musica"
REPORTS_FOLDER = "scansioni"


def online_check(scanned: list, issues: list, clients: list, flagged_only: bool, chooser, progress, cancel) -> list:
    """Verifica online gli album dei brani controllati (con flagged_only solo quelli toccati dai problemi): i
    risultati (albumcheck.AlbumCheckResult), uno per album. Gli album senza nome si saltano."""
    groups = group_by_album(scanned)
    wanted = albums_of_issues(issues, scanned) if flagged_only else None
    keys = []
    for key in sorted(groups, key=lambda k: (k[0].lower(), k[1].lower())):
        if key[1] != UNKNOWN_ALBUM and (wanted is None or key in wanted):
            keys.append(key)
    results = []
    index = 0
    while index < len(keys) and not is_cancelled(cancel):
        artist, album = keys[index]
        progress(index, len(keys), f"verifica online: {artist} — {album}")
        results.append(check_album_services(clients, groups[keys[index]], chooser))
        index += 1
    return results


class ScanLauncher:
    def __init__(self, window) -> None:
        self.window = window
        self.library_tracks = []
        self._last_phone = []          # [(Track della scansione, PhoneTrack)] dell'ultimo controllo dell'iPhone

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

        def work(progress, cancel):
            prints = {}
            if CHECK_DUPLICATES in checks:
                progress(0, 0, "impronte dell'audio")
                prints = pc_fingerprints(tracks, tag_cache, progress, cancel)
            report = scan_tracks(tracks, target, choices["provider"], check_files=CHECK_FILES in checks,
                                 progress=progress, cancel=cancel, checks=checks, fingerprints=prints,
                                 musicbrainz=musicbrainz, ai_flagged_only=choices["ai_flagged"])
            results = self._online(tracks, report, choices, progress, cancel)
            value = (report, results)
            return value

        window.runner.run(TITLE, work, lambda value: self._show(value[0], value[1], SIDE_PC, tracks, []))

    def _start_device(self, items: list, choices: dict) -> None:
        from ..provenance import PhoneFingerprints
        window = self.window
        checks = choices["checks"]
        music = [folder for folder in window.music_dirs() if folder.is_dir()]
        loaded = list(window.tracks) if window.showing_music() else None
        target = f"iPhone, {len(items)} brani ({window.phone_label})"
        musicbrainz = choices["musicbrainz"] if CHECK_VARIANTS in checks else None

        def work(progress, cancel):
            scanned = tracks_for_scan(items)
            library_tracks = loaded
            if library_tracks is None:
                library_tracks = []
                for folder in music:
                    library_tracks.extend(scan_folder(folder, progress, cancel, window.tag_cache))
                library_tracks = window.without_hidden(library_tracks)   # non le cartelle escluse
            window.overlay.apply(library_tracks)
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
                                 keep_phone_fixes=True)
            results = self._online(scanned, report, choices, progress, cancel)
            value = (report, results, scanned, library_tracks)
            return value

        def done(value):
            report, results, scanned, library_tracks = value
            self.library_tracks = library_tracks
            self._show(report, results, SIDE_PHONE, scanned, list(zip(scanned, items)))

        window.runner.run(f"{TITLE} (iPhone)", work, done)

    @staticmethod
    def _online(scanned: list, report, choices: dict, progress, cancel) -> list:
        """La Verifica online, se è scelta: i suoi problemi entrano nel rapporto; restituisce i risultati."""
        results = []
        if choices["clients"] and not is_cancelled(cancel):
            results = online_check(scanned, report.issues, choices["clients"], choices["online_flagged"],
                                   choices["chooser"], progress, cancel)
            number = 0
            for result in results:
                number += 1
                report.issues.extend(online_issues(result, number))
            report.issues.sort(key=lambda issue: issue.sort_key())
            report.cancelled = report.cancelled or is_cancelled(cancel)
        return results

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

    def _show(self, report, results: list, side: str, scanned: list, phone_pairs: list) -> None:
        from .check_results import CheckResultsView
        window = self.window
        self._last_phone = phone_pairs
        saved = None
        try:
            saved = save_report(report, config_dir() / REPORTS_FOLDER)
        except OSError as exc:
            QMessageBox.warning(window, TITLE, f"Rapporto non salvato: {exc}")
        online = {}
        for result in results:
            if result.local_tracks:
                online[result.local_tracks[0].album_key] = result
            if side == SIDE_PC:
                window.store_check_result(result)           # l'icona accanto all'album negli elenchi
        if results and side == SIDE_PC:
            window.browser.refresh_check_icons(window.check_results)
        entries = entries_by_album(report.issues, self._resolver(side, scanned, phone_pairs))
        window.checks_panel.show_results(CheckResultsView(self, report, entries, saved, online, side))
