# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Verifica album online: i cataloghi (risposte finte, nessuna rete), l'ordine dei servizi, la verifica in
background. Nomi e valori inventati."""

import os
import time
from pathlib import Path

from myeasymp3toiphone import albumcheck
from myeasymp3toiphone.albumcheck import (
    STATUS_COMPLETE, STATUS_INCOMPLETE, STATUS_NOT_FOUND, AlbumCheckError, ExpectedTrack, ReleaseCandidate,
)
from myeasymp3toiphone.library import Track, assign_groups
from myeasymp3toiphone.tags import TrackTags


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status_code = status
        self.content = b"img"

    def json(self):
        return self.payload


class FakeSession:
    """Risponde secondo l'inizio dell'indirizzo; ricorda le richieste (e le intestazioni)."""

    def __init__(self, answers):
        self.answers = answers
        self.seen = []
        self.headers = {}

    def get(self, url, params=None, headers=None, timeout=0):
        self.seen.append((url, dict(params or {}), dict(headers or {})))
        payload = None
        for prefix, value in self.answers.items():
            if url.startswith(prefix) and payload is None:
                payload = value
        return FakeResponse(payload if payload is not None else {}, 200 if payload is not None else 404)


def _client(cls, answers):
    client = cls()
    client.min_interval = 0
    client._session = FakeSession(answers)
    return client


def _album(titles, artist="Cantante Finto", album="Disco Finto"):
    tracks = []
    for number, title in enumerate(titles, start=1):
        tracks.append(Track(path=Path(f"C:/m/{album}/{number:02d} {title}.mp3"),
                            tags=TrackTags(title=title, artist=artist, album=album, track_number=number)))
    assign_groups(tracks)
    return tracks


def test_deezer_search_and_tracks():
    client = _client(albumcheck.DeezerClient, {
        "https://api.deezer.com/search/album": {"data": [
            {"id": 5, "title": "Disco Finto", "nb_tracks": 2, "record_type": "album", "artist": {"name": "Cantante"},
             "cover_xl": "https://img/5.jpg", "link": "https://www.deezer.com/album/5"}]},
        "https://api.deezer.com/album/5/tracks": {"data": [
            {"title": "Uno", "duration": 100, "track_position": 1, "disk_number": 1},
            {"title": "Due", "duration": 120, "track_position": 2, "disk_number": 1}]},
        "https://api.deezer.com/album/5": {"release_date": "1999-05-01"},
    })
    candidates = client.search_releases("Cantante", "Disco Finto")
    assert candidates[0].service == "deezer" and candidates[0].track_count == 2
    assert 'artist:"Cantante"' in client._session.seen[0][1]["q"]
    tracks = client.get_expected_tracks(candidates[0])
    assert [(t.disc, t.position, t.title, t.length_ms) for t in tracks] == [(1, 1, "Uno", 100000), (1, 2, "Due", 120000)]
    assert candidates[0].date == "1999-05-01" and client.release_url(candidates[0]).endswith("/album/5")


def test_apple_search_and_tracks():
    client = _client(albumcheck.AppleClient, {
        "https://itunes.apple.com/search": {"results": [
            {"collectionId": 9, "collectionName": "Disco Finto", "artistName": "Cantante", "trackCount": 3,
             "releaseDate": "1999-05-01T07:00:00Z", "artworkUrl100": "https://img/100x100bb.jpg"}]},
        "https://itunes.apple.com/lookup": {"results": [
            {"wrapperType": "collection"},
            {"wrapperType": "track", "trackName": "Tre", "trackNumber": 1, "discNumber": 2, "trackTimeMillis": 5},
            {"wrapperType": "track", "trackName": "Uno", "trackNumber": 1, "discNumber": 1, "trackTimeMillis": 5},
            {"wrapperType": "track", "trackName": "Due", "trackNumber": 2, "discNumber": 1, "trackTimeMillis": 5}]},
    })
    candidate = client.search_releases("Cantante", "Disco Finto")[0]
    assert candidate.date == "1999-05-01" and candidate.cover_url.endswith("600x600bb.jpg")
    tracks = client.get_expected_tracks(candidate)
    assert [(t.disc, t.position, t.title, t.disc_total, t.disc_track_count) for t in tracks] == \
        [(1, 1, "Uno", 2, 2), (1, 2, "Due", 2, 2), (2, 1, "Tre", 2, 1)]


def test_discogs_needs_the_token_and_sends_it_only_in_the_header(monkeypatch):
    monkeypatch.delenv(albumcheck.DISCOGS_TOKEN_VAR, raising=False)
    client = _client(albumcheck.DiscogsClient, {})
    assert not client.available()
    try:
        client.search_releases("A", "B")
        raised = False
    except AlbumCheckError:
        raised = True
    assert raised
    monkeypatch.setenv(albumcheck.DISCOGS_TOKEN_VAR, "token-finto-di-prova")
    client = _client(albumcheck.DiscogsClient, {
        "https://api.discogs.com/database/search": {"results": [
            {"id": 3, "title": "Cantante - Disco Finto", "year": "1999", "format": ["CD", "Album"]}]},
        "https://api.discogs.com/releases/3": {"tracklist": [
            {"position": "", "type_": "heading", "title": "Lato A"},
            {"position": "1-01", "type_": "track", "title": "Uno", "duration": "3:05"},
            {"position": "2-01", "type_": "track", "title": "Due", "duration": ""}]},
    })
    candidate = client.search_releases("Cantante", "Disco Finto")[0]
    assert (candidate.artist, candidate.title, candidate.formats) == ("Cantante", "Disco Finto", "CD + Album")
    tracks = client.get_expected_tracks(candidate)
    assert [(t.disc, t.position, t.title, t.length_ms) for t in tracks] == [(1, 1, "Uno", 185000), (2, 1, "Due", 0)]
    for url, params, headers in client._session.seen:
        assert "token-finto-di-prova" not in url and "token-finto-di-prova" not in str(params)
        assert headers["Authorization"] == "Discogs token=token-finto-di-prova"


def test_discogs_positions():
    assert albumcheck._discogs_position("CD2-05", 9) == (2, 5)
    assert albumcheck._discogs_position("7", 9) == (1, 7)
    assert albumcheck._discogs_position("B2", 9) == (1, 9)


class FakeService:
    def __init__(self, service, tracks):
        self.service = service
        self.label = service.capitalize()
        self.tracks = tracks
        self.calls = 0

    def search_releases(self, artist, album):
        self.calls += 1
        result = []
        if self.tracks is not None:
            result = [ReleaseCandidate(id="1", title=album, artist=artist, date="", country="",
                                       track_count=len(self.tracks), formats="", status="", mb_score=100,
                                       service=self.service)]
        return result

    def get_expected_tracks(self, release):
        result = []
        for number, title in enumerate(self.tracks, start=1):
            result.append(ExpectedTrack(1, number, title, 0, 1, len(self.tracks)))
        return result


def test_services_in_order_until_one_is_complete():
    local = _album(["Uno", "Due"])
    missing = FakeService("deezer", None)
    partial = FakeService("apple", ["Uno", "Due", "Tre"])
    full = FakeService("discogs", ["Uno", "Due"])
    never = FakeService("musicbrainz", ["Uno", "Due"])
    result = albumcheck.check_album_services([missing, partial, full, never], local)
    assert result.status == STATUS_COMPLETE and result.service == "discogs" and never.calls == 0
    assert [label for label, _status in result.tried] == ["Deezer", "Apple", "Discogs"]
    best = albumcheck.check_album_services([missing, partial], local)        # nessuno completo: il migliore
    assert best.status == STATUS_INCOMPLETE and best.service == "apple" and len(best.missing) == 1
    none = albumcheck.check_album_services([missing], local)
    assert none.status == STATUS_NOT_FOUND and "Deezer" in none.status_text()


def test_album_check_runs_in_background_and_updates_the_window(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        window.tracks = _album(["Uno", "Due"])
        window._rebuild_views()
        window._open_album_results = lambda: None            # niente finestra dei risultati nel test
        window._start_album_check([window.tracks], [FakeService("deezer", ["Uno", "Due"])], None)
        assert not window.runner.is_busy                     # il programma resta usabile
        deadline = time.monotonic() + 10
        while window._album_job.running and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
        app.processEvents()
        assert len(window._album_results) == 1 and window._album_results[0].status == STATUS_COMPLETE
        assert window.check_results and "finita" in window._album_label.text()
    finally:
        window.close()
        app.processEvents()


def test_album_check_options_dialog():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui.album_check_dialog import AlbumCheckOptionsDialog
    app = QApplication.instance() or QApplication([])
    dialog = AlbumCheckOptionsDialog(None, 12, ["deezer", "apple", "discogs"], True, "", False)
    assert dialog.services() == ["deezer", "apple"]           # Discogs senza token: spento
    assert not dialog.use_ai                                   # senza profilo AI
    dialog.boxes["musicbrainz"].setChecked(True)
    assert dialog.services() == ["deezer", "apple", "musicbrainz"]
    dialog.close()
    app.processEvents()


def test_checks_tab_runs_the_album_check_and_shows_results(monkeypatch):
    """La linguetta Controlli: F7 la apre; Avvia la verifica parte con le scelte del riquadro; durante c'è Ferma; alla
    fine i risultati compaiono sotto, senza finestre a parte."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui.album_check_dialog import AlbumCheckDialog
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        window.tracks = _album(["Uno", "Due"])
        window._rebuild_views()
        panel = window.checks_panel
        assert window._tabs.tabText(window._tabs.indexOf(panel)) == "Controlli"
        window._check_albums()                                      # F7
        assert window._tabs.currentWidget() is panel
        panel.refresh()
        options = panel.album_options
        assert "Verificare l'album Cantante Finto — Disco Finto" in options._header.text()
        assert options.start_button.isEnabled()
        window.album_clients["deezer"] = FakeService("deezer", ["Uno", "Due"])
        options.boxes["apple"].setChecked(False)
        options.boxes["deezer"].setChecked(True)
        options.start_button.click()
        assert not options.stop_button.isHidden() or not window._album_job.running
        deadline = time.monotonic() + 10
        while window._album_job.running and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
        app.processEvents()
        assert isinstance(panel.results.widget(1), AlbumCheckDialog)
        assert options.stop_button.isHidden() and "finita" in options.progress.text()
        window._scan()                                              # F6: Controlla la musica, nella stessa linguetta
        assert window._tabs.currentWidget() is panel
    finally:
        window.close()
        app.processEvents()


def test_scan_results_check_the_albums_of_the_selected_problems_and_say_what_to_do():
    """Nei risultati di Controlla la musica: Verifica online questi album prende gli album interi dei problemi
    selezionati, non quelli scelti nella scheda PC; ogni problema dice cosa fare."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone import scan
    from myeasymp3toiphone.gui.main_window import MainWindow
    from myeasymp3toiphone.gui.scan_dialog import ScanDialog
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        first = _album(["Uno", "Due", "Tre"])
        other = _album(["Quattro"], album="Altro Disco")
        window.tracks = first + other
        assign_groups(window.tracks)
        window._rebuild_views()
        launcher = window.scan_launcher
        launcher.library_tracks = list(window.tracks)
        issue = scan.Issue(scan.KIND_FEW_TRACKS, scan.SEVERITY_HIGH, "Disco Finto: 1 brano su almeno 3", "d",
                           [first[0].path], rule_id="R9.1")
        report = scan.ScanReport(target="prova", issues=[issue], tracks_scanned=4, albums_scanned=2)
        dialog = ScanDialog(report, None, launcher, embedded=True)
        assert not dialog.online_button.isEnabled()                  # niente selezionato
        top = dialog.tree.topLevelItem(0)
        top.child(0).setSelected(True)
        assert dialog.online_button.isEnabled()
        assert "Cosa fare:" in dialog.detail.toHtml()
        started = []
        window.start_album_check_from_panel = lambda albums=None: started.append(albums)
        dialog.online_button.click()
        assert len(started) == 1 and len(started[0]) == 1           # l'album del problema, intero
        assert sorted(track.tags.title for track in started[0][0]) == ["Due", "Tre", "Uno"]
        dialog.close()
    finally:
        window.close()
        app.processEvents()


def test_every_rule_says_what_to_do():
    from myeasymp3toiphone import scan
    for rule in ("R2", "R3", "R5", "R6", "R7", "R8", "R9", "R10", "R11", "R12", "R13", "R14", "R15", "R16", "R17",
                 "I1", "I2", "I3", "I4"):
        assert scan.advice(scan.Issue(scan.KIND_SPLIT, scan.SEVERITY_LOW, "t", "d", rule_id=f"{rule}.1")), rule
    for kind in scan.AI_KINDS:
        assert scan.advice(scan.Issue(kind, scan.SEVERITY_LOW, "t", "d", origin=scan.ORIGIN_AI)), kind
