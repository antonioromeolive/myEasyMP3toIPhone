# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La linguetta Controlli: la Verifica online come problemi, i risultati per album, dove va ogni correzione (PC e
iPhone per i brani collegati, solo PC, solo iPhone), l'AI solo sugli album con problemi e Solo AI, la scelta di cosa
controllare dalla selezione delle schede. Nomi e valori inventati."""

import os
import time
from pathlib import Path

from conftest import write_mp3
from test_albumcheck import FakeService, _album
from myeasymp3toiphone import albumcheck, check_flow, scan
from myeasymp3toiphone.library import Track, assign_groups, scan_folder
from myeasymp3toiphone.phone_library import PhoneTrack
from myeasymp3toiphone.tags import TrackTags, read_tags, write_tags


def _phone(pid, title, album, sync_id=None, **values):
    tags = TrackTags(title=title, artist="Gruppo Finto", album=album, **values)
    result = PhoneTrack(pid=pid, remote_path=f"/iTunes_Control/Music/F01/{pid}.mp3", size=4_000_000, length=200.0,
                        tags=tags, sync_id=pid + 100 if sync_id is None else sync_id)
    return result


def test_online_check_becomes_problems_with_fixes():
    local = _album(["uno", "Due"])                     # "uno": minuscolo, il catalogo dice "Uno": è uguale
    result = albumcheck.check_album_services([FakeService("deezer", ["Uno", "Due", "Tre"])], local)
    issues = check_flow.online_issues(result, 1)
    by_rule = {issue.rule_id: issue for issue in issues}
    assert set(by_rule) == {"W1.1", "W2.1"}
    assert "mancano 1 di 3 brani" in by_rule["W1.1"].title and "03 Tre" in by_rule["W1.1"].detail
    changes = dict((Path(path).name, values) for path, values in by_rule["W2.1"].fix.changes)
    assert "title" not in changes["01 uno.mp3"] and changes["01 uno.mp3"]["track_total"] == 3   # le maiuscole no
    missing = albumcheck.check_album_services([FakeService("deezer", None)], local)
    assert check_flow.online_issues(missing, 2) == []                 # non trovato: non è un problema
    assert "Non trovato" in check_flow.online_note(missing) and check_flow.online_note(result) == ""
    assert scan.advice(by_rule["W2.1"]) and scan.advice(by_rule["W1.1"])


def test_results_by_album_and_the_side_of_each_track():
    first = _album(["Uno", "Due"], album="Primo")
    second = _album(["Tre"], album="Secondo")
    linked_phone = _phone(1, "Uno", "Primo")
    targets = {}
    for track in first + second:
        phone = linked_phone if track.tags.title == "Uno" else None
        targets[str(track.path)] = check_flow.Target(track, pc=track, phone=phone)
    issue = scan.Issue(scan.KIND_SPLIT, scan.SEVERITY_LOW, "Artista scritto in 2 modi", "d",
                       [track.path for track in first + second],
                       scan.Fix(scan.FIX_TAGS, "Scrivi ovunque", changes=[(first[0].path, {"artist": "Cantante"}),
                                                                          (second[0].path, {"artist": "Cantante"})]),
                       rule_id="R14.1")
    grave = scan.Issue(scan.KIND_FEW_TRACKS, scan.SEVERITY_HIGH, "Secondo: 1 brano su almeno 3", "d",
                       [second[0].path], rule_id="R9.1")
    entries = check_flow.group_by_album([issue, grave, scan.Issue(scan.KIND_ONLY_ON_DEVICE, scan.SEVERITY_MEDIUM,
                                                                  "Solo sull'iPhone", "d", ["A — B — C"],
                                                                  rule_id="I3")],
                                        lambda path: targets.get(str(path)))
    assert [entry.title for entry in entries] == ["Cantante Finto — Secondo", "Cantante Finto — Primo",
                                                  "Altri problemi"]         # il più grave prima, gli altri in fondo
    secondo, primo, _other = entries
    assert len(secondo.problems) == 2 and secondo.side == check_flow.SIDE_PC
    assert primo.side == check_flow.SIDE_MIXED                             # un brano collegato, uno solo sul PC
    rows = primo.rows()
    assert [(row.target.name, row.name, row.old, row.new) for row in rows] == [("01 Uno", "artist", "Cantante Finto",
                                                                                "Cantante")]
    assert rows[0].target.side == check_flow.SIDE_BOTH


def test_where_each_fix_goes():
    pc_only = Track(path=Path("C:/m/Disco/01.mp3"), tags=TrackTags(title="Uno", album="Disco"))
    linked_pc = Track(path=Path("C:/m/Disco/02.mp3"), tags=TrackTags(title="Due", album="Disco"))
    linked = _phone(2, "Due", "Disco")
    alone = _phone(3, "Tre", "Disco")
    bought = _phone(4, "Quattro", "Disco", sync_id=0)               # acquistato sul telefono
    targets = [check_flow.Target(pc_only, pc=pc_only), check_flow.Target(linked_pc, pc=linked_pc, phone=linked),
               check_flow.Target(alone.as_track(), phone=alone), check_flow.Target(bought.as_track(), phone=bought)]
    rows = [check_flow.Row(targets[0], "album", "Disco", "Disco Vero", 0),
            check_flow.Row(targets[1], "album", "Disco", "Disco Vero", 0),
            check_flow.Row(targets[2], "album", "Disco", "Disco Vero", 0),
            check_flow.Row(targets[2], "year", "", "1999", 0),
            check_flow.Row(targets[2], "album_artist", "", "Artisti vari", 0),
            check_flow.Row(targets[3], "album", "Disco", "Disco Vero", 0)]
    plan = check_flow.plan_apply(rows)
    assert [track.tags.title for track, _values in plan.pc] == ["Uno", "Due"]        # sul PC: solo PC e collegati
    assert plan.linked == [(linked, linked_pc)]                                      # sull'iPhone: Usa i tag
    assert plan.phone == [(alone, {"album": "Disco Vero", "year": 1999})]            # solo iPhone: Cambia i tag
    reasons = " ".join(reason for _name, reason in plan.blocked)
    assert "Artista album" in reasons and "non è stato messo da un computer" in reasons
    assert plan.count(check_flow.SIDE_PC) == 1 and plan.count(check_flow.SIDE_BOTH) == 1


class SeeingProvider:
    def __init__(self):
        self.profile = type("P", (), {"name": "finto", "batch_albums": 25, "batch_tracks": 400})()
        self.seen = []

    def ask_json(self, system, user, schema):
        self.seen.append(user)
        return {"issues": [{"kind": "tag_mancanti", "severity": "bassa", "title": "Genere mancante", "explanation": "e",
                            "albums": ["A1"], "fix_album": "", "fix_album_artist": "", "fix_artist": "",
                            "fix_year": "", "fix_genre": "Pop"}], "false_positives": []}


def test_ai_only_on_albums_with_problems_and_only_ai(tmp_path):
    def tagged(path, **values):
        write_mp3(path)
        write_tags(path, TrackTags(**values))

    tagged(tmp_path / "Buchi" / "1.mp3", title="X", artist="Gruppo", album="Buchi", track_number=1, track_total=3)
    tagged(tmp_path / "Buchi" / "3.mp3", title="Y", artist="Gruppo", album="Buchi", track_number=3, track_total=3)
    for number in (1, 2, 3):
        tagged(tmp_path / "Intero" / f"{number}.mp3", title=f"Z{number}", artist="Gruppo", album="Intero",
               track_number=number, track_total=3, genre="Rock", year="2001")
    tracks = scan_folder(tmp_path)
    provider = SeeingProvider()
    report = scan.scan_tracks(tracks, "prova", provider, check_files=False,
                              checks=frozenset({scan.CHECK_FEW, scan.CHECK_MISSING}), ai_flagged_only=True)
    assert len(provider.seen) == 1 and "Buchi" in provider.seen[0] and "Intero" not in provider.seen[0]
    assert any(issue.origin == scan.ORIGIN_AI for issue in report.issues)
    provider = SeeingProvider()
    report = scan.scan_tracks(tracks, "prova", provider, check_files=False, checks=frozenset(), ai_flagged_only=True)
    assert "Buchi" in provider.seen[0] and "Intero" in provider.seen[0]       # Solo AI: tutti gli album
    assert [issue.origin for issue in report.issues] == [scan.ORIGIN_AI]      # e i suoi problemi si tengono


def _wait(window, app):
    deadline = time.monotonic() + 15
    while window.runner.is_busy and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()


def test_checks_tab_scope_results_by_album_and_apply(tmp_path, monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QMenu
    from myeasymp3toiphone.gui import check_results, pc_write
    from myeasymp3toiphone.gui.check_results import CheckResultsView
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    folder = tmp_path / "Dal Vivo"
    for number, title in enumerate(["Uno", "Due"], start=1):
        path = folder / f"0{number}.mp3"
        write_mp3(path)
        write_tags(path, TrackTags(title=title, artist="Anna Finta", album=f"Dal Vivo (CD {number})",
                                   track_number=1))
    window = MainWindow()
    try:
        window.tracks = scan_folder(folder)
        window._rebuild_views()
        panel = window.checks_panel
        options = panel.options
        window._scan()                                                  # F6 dalla scheda PC: il PC
        assert options.side == check_flow.SIDE_PC and "tutti i brani della scheda PC" in options.scope_label.text()
        albums = window.browser.albums                                 # un album negli elenchi
        for index in range(albums.topLevelItemCount()):
            if albums.topLevelItem(index).text(0) == "Dal Vivo (CD 1)":
                albums.topLevelItem(index).setSelected(True)
        app.processEvents()
        panel.refresh()
        assert "l'album" in options.scope_label.text() and "Dal Vivo (CD 1)" in options.scope_label.text()
        options.all_button.click()                                      # Tutto il PC
        assert "tutti i brani" in options.scope_label.text()
        for check_id, box in options.boxes.items():
            box.setChecked(check_id == scan.CHECK_SPLIT)
        options.online_box.setChecked(False)
        options.start_button.click()
        _wait(window, app)
        view = panel.results
        assert isinstance(view, CheckResultsView)
        assert [entry.title for entry in view.entries] == ["Anna Finta — Dal Vivo (CD 1)", "Anna Finta — Dal Vivo (CD 2)"]
        assert view.chosen_rows() and view.apply_button.isEnabled()
        first_album = view.tree.topLevelItem(0)
        first_album.setCheckState(0, Qt.Unchecked)                    # la casella dell'album spegne le sue righe
        rows = view.chosen_rows()
        assert rows and all(row.target.scanned.album_key[1] == "Dal Vivo (CD 2)" for row in rows)
        problem = first_album.child(0)                                  # tasto destro su un problema: i suoi file
        problem.setSelected(True)
        assert view._pc_paths() == [folder / "01.mp3"]
        menu = QMenu()
        check_results.add_file_entries(menu, view._pc_paths())
        clipboard = menu.actions()[0].menu()
        [folder_action] = [action for action in clipboard.actions() if action.text().startswith("Percorso della cart")]
        folder_action.trigger()
        assert QApplication.clipboard().text() == str(folder)
        problem.setSelected(False)

        def destinations(dialog):
            dialog.pc_files.setChecked(True)
            return True

        monkeypatch.setattr(check_results.ApplyDestinationsDialog, "exec", destinations)
        monkeypatch.setattr(pc_write.PcWriteDialog, "exec", lambda dialog: True)
        view.apply_button.click()
        _wait(window, app)
        tags = read_tags(folder / "02.mp3")[0]
        assert tags.album == "Dal Vivo" and tags.disc_number == 2               # scritto nel file, approvato
        assert read_tags(folder / "01.mp3")[0].album == "Dal Vivo (CD 1)"        # l'album spento non cambia
        assert not view.chosen_rows() and not view.apply_button.isEnabled()       # applicate: non si riapplicano
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_phone_only_fixes_go_to_the_queue_and_linked_ones_both_ways(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui import check_results
    from myeasymp3toiphone.gui.main_window import MainWindow
    from myeasymp3toiphone.pending import EDIT, UPDATE
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        phone = [_phone(1, "Uno", "Dal Vivo (CD 1)", track_number=1), _phone(2, "Due", "Dal Vivo (CD 2)", track_number=1)]
        window.set_phone_tracks(phone, "iPhone di prova")
        app.processEvents()
        linked_pc = Track(path=Path("C:/m/Dal Vivo/02.mp3"), tags=phone[1].tags.copy())
        assign_groups([linked_pc])
        monkeypatch.setattr(window.iphone_panel, "linked_pc", lambda item: linked_pc if item.pid == 2 else None)
        applied = []
        monkeypatch.setattr(window, "apply_tag_changes", lambda pairs, cover=None: applied.extend(pairs))
        options = window.checks_panel.options
        options.set_side(check_flow.SIDE_PHONE)
        assert "tutta la musica dell'iPhone" in options.scope_label.text()
        for check_id, box in options.boxes.items():
            box.setChecked(check_id == scan.CHECK_SPLIT)
        options.online_box.setChecked(False)
        options.start_button.click()
        _wait(window, app)
        view = window.checks_panel.results
        sides = {row.target.phone.pid: row.target.side for row in view.chosen_rows()}
        assert sides == {1: check_flow.SIDE_PHONE, 2: check_flow.SIDE_BOTH}

        def destinations(dialog):
            dialog.both_files.setChecked(False)                    # sul PC solo in sospeso
            return True

        monkeypatch.setattr(check_results.ApplyDestinationsDialog, "exec", destinations)
        view.apply_button.click()
        assert window.pending.get_phone(1, include_edit=True) == EDIT              # solo iPhone: Cambia i tag
        assert window.pending.get_phone(2) == UPDATE                               # collegato: Usa i tag da PC
        assert [track for track, _tags in applied] == [linked_pc]                  # e sul PC, in sospeso
        assert applied[0][1].album == "Dal Vivo"
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


class CancellingProvider(SeeingProvider):
    """Un'AI che a metà della prima richiesta riceve Annulla."""

    def __init__(self, cancel):
        super().__init__()
        self.cancel = cancel

    def ask_json(self, system, user, schema):
        self.cancel.set()
        result = super().ask_json(system, user, schema)
        return result


def test_cancel_during_the_ai_keeps_every_rule_and_drops_the_ai(tmp_path):
    import threading

    def tagged(path, frames=40, **values):
        write_mp3(path, frames)
        write_tags(path, TrackTags(**values))

    tagged(tmp_path / "Buchi" / "1.mp3", title="X", artist="Gruppo", album="Buchi", track_number=1, track_total=3)
    tagged(tmp_path / "Buchi" / "3.mp3", title="Y", artist="Gruppo", album="Buchi", track_number=3, track_total=3)
    tagged(tmp_path / "Raccolta" / "1.mp3", title="X", artist="Gruppo", album="Raccolta", track_number=1,
           track_total=2)
    tagged(tmp_path / "Raccolta" / "2.mp3", title="X", artist="Gruppo", album="Raccolta", track_number=2,
           track_total=2)                                       # lo stesso brano due volte: un doppione
    tracks = scan_folder(tmp_path)
    cancel = threading.Event()
    checks = frozenset({scan.CHECK_FEW, scan.CHECK_MISSING, scan.CHECK_DUPLICATES})
    report = scan.scan_tracks(tracks, "prova", CancellingProvider(cancel), check_files=False, checks=checks,
                              cancel=cancel)
    without_ai = scan.scan_tracks(tracks, "prova", None, check_files=False, checks=checks)
    assert report.stopped == ["Analisi AI"] and not report.cancelled and not report.ai_profile
    assert [issue.rule_id for issue in report.issues] == [issue.rule_id for issue in without_ai.issues]
    assert any(issue.rule_id.startswith("R15") for issue in report.issues)     # i doppioni, dopo l'AI, ci sono
    assert all(issue.origin != scan.ORIGIN_AI and not issue.ai_note for issue in report.issues)
    assert "Annullati: Analisi AI" in scan.report_text(report)


def test_cancel_during_the_online_check_and_check_again_from_the_results(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui import scan_dialog
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    class SlowService(FakeService):
        def search_releases(self, artist, album):
            time.sleep(0.3)
            return super().search_releases(artist, album)

    try:
        window.tracks = _album(["Uno", "Due"], album="Primo") + _album(["Tre"], album="Secondo")
        window._rebuild_views()
        window._scan()
        options = window.checks_panel.options
        for check_id, box in options.boxes.items():
            box.setChecked(check_id in (scan.CHECK_FEW, scan.CHECK_MISSING))
        options.ai_box.setChecked(False)
        options.online_box.setChecked(True)
        options.online_flagged.setChecked(False)
        window.album_clients["deezer"] = SlowService("deezer", ["Uno", "Due", "Tre"])
        for service, box in options.service_boxes.items():
            box.setChecked(service == "deezer")
        options.start_button.click()
        deadline = time.monotonic() + 0.2
        while time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
        window.runner.cancel()                                          # Annulla durante la verifica online
        _wait(window, app)
        view = window.checks_panel.results
        assert view.report.stopped == ["Verifica online"] and "Annullati: Verifica online" in view.header.text()
        assert all(issue.origin != scan.ORIGIN_ONLINE for issue in view.report.issues)
        assert {entry.key[1] for entry in view.entries} == {"Primo", "Secondo"}   # le regole: 1-2 brani
        second = [entry.key for entry in view.entries if entry.key[1] == "Secondo"][0]

        # tasto destro: Controlla online, solo su "Secondo"
        launcher = window.scan_launcher
        launcher.recheck(scan_dialog.STAGE_ONLINE, {second})
        _wait(window, app)
        view = window.checks_panel.results
        online = [issue for issue in view.report.issues if issue.origin == scan.ORIGIN_ONLINE]
        assert online and all("Secondo" in issue.title for issue in online)
        assert view.report.stopped == []

        # tasto destro: Controlla con l'AI, solo su "Secondo"
        provider = SeeingProvider()
        monkeypatch.setattr(launcher, "_profile", lambda: object())
        monkeypatch.setattr(scan_dialog, "make_provider", lambda profile: provider)
        launcher.recheck(scan_dialog.STAGE_AI, {second})
        _wait(window, app)
        assert len(provider.seen) == 1 and "Secondo" in provider.seen[0] and "Primo" not in provider.seen[0]
        view = window.checks_panel.results
        assert any(issue.origin == scan.ORIGIN_AI for issue in view.report.issues)
        launcher.recheck(scan_dialog.STAGE_AI, {second})        # di nuovo: si sostituisce, non si somma
        _wait(window, app)
        assert len([issue for issue in window.checks_panel.results.report.issues
                    if issue.origin == scan.ORIGIN_AI]) == 1
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_the_ai_stops_after_errors_in_a_row_and_asks_ollama_not_to_think():
    from myeasymp3toiphone import ai
    from myeasymp3toiphone.config import ProviderProfile
    profile = ProviderProfile(name="prova", base_url="http://localhost:11434", model="finto", max_failures=2)
    provider = ai.OllamaProvider(profile)
    bodies = []

    def failing(label, url, body, headers):
        bodies.append(dict(body))
        raise ai.AIError("Ollama: richiesta non riuscita (timeout)")

    provider._post = failing
    for _attempt in range(2):
        try:
            provider.ask_json("s", "u", {})
        except ai.AIError:
            pass
    assert provider.gave_up and len(bodies) == 2 and bodies[0]["think"] is False
    try:
        provider.ask_json("s", "u", {})
    except ai.AIError as exc:
        assert "disattivata dopo 2 errori di fila" in str(exc)
    assert len(bodies) == 2                                   # nessuna richiesta in più: non si aspetta il server

    answers = [ai.AIError('Ollama: errore 400: {"error":"think value \\"false\\" is not supported"}'),
               {"message": {"content": "{\"ok\": true}"}}]
    sent = []

    def old_server(label, url, body, headers):
        sent.append(dict(body))
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    provider = ai.OllamaProvider(profile)
    provider._post = old_server
    assert provider.ask_json("s", "u", {}) == {"ok": True}
    assert "think" in sent[0] and "think" not in sent[1] and provider.failures == 0


def test_results_arrive_while_the_check_runs_and_the_button_stops_it(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui import scan_dialog
    from myeasymp3toiphone.gui.check_results import CheckResultsView
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(scan_dialog, "LIVE_DELAY_MS", 10)
    window = MainWindow()

    class SlowService(FakeService):
        def search_releases(self, artist, album):
            time.sleep(0.4)
            return super().search_releases(artist, album)

    try:
        window.tracks = (_album(["Uno", "Due"], album="Primo") + _album(["Tre"], album="Secondo")
                         + _album(["Quattro"], album="Terzo"))
        window._rebuild_views()
        window._scan()
        options = window.checks_panel.options
        for check_id, box in options.boxes.items():
            box.setChecked(check_id == scan.CHECK_FEW)
        options.ai_box.setChecked(False)
        options.online_box.setChecked(True)
        options.online_flagged.setChecked(False)
        window.album_clients["deezer"] = SlowService("deezer", ["Uno", "Due", "Tre"])
        for service, box in options.service_boxes.items():
            box.setChecked(service == "deezer")
        window.show()                                                     # i risultati man mano: con la linguetta visibile
        options.start_button.click()
        assert options.start_button.text() == "Ferma il controllo"
        live = None
        deadline = time.monotonic() + 10
        while live is None and window.runner.is_busy and time.monotonic() < deadline:
            app.processEvents()
            view = window.checks_panel.results
            if isinstance(view, CheckResultsView) and view.live:
                live = view
            time.sleep(0.01)
        assert live is not None and not live.apply_button.isEnabled()      # risultati man mano, Applica alla fine
        assert "Controllo in corso" in live.header.text()
        assert not options.phase_label.isHidden() and "Regole" in options.phase_label.text()
        assert "Verifica online" in options.phase_label.text()
        live.tree.topLevelItem(0).setCheckState(0, Qt.Unchecked)           # spento durante il controllo
        off = len(live.chosen_rows())
        _wait(window, app)
        final = window.checks_panel.results
        assert not final.live and options.start_button.text() == "Avvia il controllo"
        assert len(final.chosen_rows()) < len(final._rows) or off == 0     # la scelta fatta durante resta
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_stop_button_cancels_like_annulla(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    class SlowService(FakeService):
        def search_releases(self, artist, album):
            time.sleep(0.3)
            return super().search_releases(artist, album)

    try:
        window.tracks = _album(["Uno", "Due"], album="Primo") + _album(["Tre"], album="Secondo")
        window._rebuild_views()
        window._scan()
        options = window.checks_panel.options
        for check_id, box in options.boxes.items():
            box.setChecked(check_id == scan.CHECK_FEW)
        options.ai_box.setChecked(False)
        options.online_box.setChecked(True)
        options.online_flagged.setChecked(False)
        window.album_clients["deezer"] = SlowService("deezer", ["Uno", "Due", "Tre"])
        for service, box in options.service_boxes.items():
            box.setChecked(service == "deezer")
        options.start_button.click()
        options.start_button.click()                                      # Ferma il controllo
        assert options.start_button.text() == "Mi fermo…" and not options.start_button.isEnabled()
        _wait(window, app)
        view = window.checks_panel.results
        assert view.report.stopped == ["Verifica online"] and options.start_button.isEnabled()
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_ai_requests_group_albums_by_album_artist_and_split_compilations():
    groups = {("Queen", "Greatest Hits"): [1] * 17, ("ABBA", "Greatest Hits"): [1] * 19,
              ("Cantante Uno", "Estate 2020"): [1], ("Cantante Due", "Estate 2020"): [1, 1],
              ("The Beatles", "Help"): [1] * 14, ("Beatles", "Abbey Road"): [1] * 17,
              ("Artisti vari", "Festival"): [1] * 20, ("Solista", "Primo"): [1] * 10}
    requests = scan.ai_requests(groups, 10, 200)
    together = {frozenset(request) for request in requests}
    assert frozenset({("Queen", "Greatest Hits")}) in together and frozenset({("ABBA", "Greatest Hits")}) in together
    assert frozenset({("Cantante Uno", "Estate 2020"), ("Cantante Due", "Estate 2020")}) in together   # una compilation
    assert frozenset({("The Beatles", "Help"), ("Beatles", "Abbey Road")}) in together                # stesso artista
    assert frozenset({("Artisti vari", "Festival")}) in together and frozenset({("Solista", "Primo")}) in together
    assert len(requests) == 6
    big = {("Gruppo", f"Album {number}"): [1] * 12 for number in range(5)}
    assert [len(request) for request in scan.ai_requests(big, 2, 200)] == [2, 2, 1]          # i limiti dentro il gruppo


def test_ai_results_arrive_after_every_request(tmp_path):
    def tagged(path, **values):
        write_mp3(path)
        write_tags(path, TrackTags(**values))

    for artist in ("Gruppo", "Altro Gruppo"):
        tagged(tmp_path / artist / "1.mp3", title="X", artist=artist, album=f"Disco di {artist}", track_number=1)
    tracks = scan_folder(tmp_path)
    seen = []
    scan.scan_tracks(tracks, "prova", SeeingProvider(), check_files=False, checks=frozenset({scan.CHECK_MISSING}),
                     partial=lambda issues: seen.append(len(issues)))
    # dopo le regole, dopo ognuna delle due richieste (due artisti: due richieste), alla fine dell'analisi
    assert seen[0] == 0 and seen[1] == 1 and seen[2] == 2 and len(seen) == 4


def test_the_same_album_in_flac_and_mp3_is_not_a_duplicate(tmp_path):
    def tagged(path, frames=40, **values):
        write_mp3(path, frames)
        write_tags(path, TrackTags(**values))

    for folder in ("FLAC", "MP3"):
        tagged(tmp_path / "Disco" / folder / "01.mp3", title="Uno", artist="Gruppo", album="Disco", track_number=1)
    for path in (tmp_path / "Disco" / "FLAC").glob("*.mp3"):
        path.rename(path.with_suffix(".flac"))          # una copia per formato (il contenuto non conta per la regola)
    tracks = [track for track in scan_folder(tmp_path)]
    from myeasymp3toiphone.library import Track
    flac = Track(path=tmp_path / "Disco" / "FLAC" / "01.flac", tags=tracks[0].tags.copy(), length=tracks[0].length)
    mp3 = [track for track in tracks if track.path.suffix == ".mp3"][0]
    assign_groups([flac, mp3])
    assert scan.one_per_format([flac.path, mp3.path]) and not scan.one_per_format([mp3.path, mp3.path])
    assert scan.detect_duplicates([flac, mp3]) == []                                   # FLAC e MP3: va bene
    issues, _errors = scan.detect_same_songs([flac, mp3], {})
    assert issues == []
    again = Track(path=tmp_path / "Disco" / "Altra copia" / "01.mp3", tags=mp3.tags.copy(), length=mp3.length)
    assign_groups([flac, mp3, again])
    assert [issue.rule_id for issue in scan.detect_duplicates([flac, mp3, again])] == ["R8"]   # due MP3: doppione
    lines = scan.album_lines({mp3.album_key: [flac, mp3]}, [mp3.album_key])
    assert "formati: flac,mp3" in lines[0][1]                                          # l'AI vede i formati


def test_online_check_of_an_album_in_flac_and_mp3():
    from myeasymp3toiphone.library import Track
    tracks = []
    for suffix in (".flac", ".mp3"):
        for number, title in enumerate(["Uno", "Due", "Tre"], start=1):
            tracks.append(Track(path=Path(f"C:/m/Disco{suffix}/{number:02d} {title}{suffix}"),
                                tags=TrackTags(title=title, artist="Cantante Finto", album="Disco Finto",
                                               track_number=number)))
    assign_groups(tracks)
    primary, copies = albumcheck.split_formats(tracks)
    assert {track.path.suffix for track in primary} == {".flac"} and [len(group) for group in copies] == [3]
    result = albumcheck.check_album_services([FakeService("deezer", ["Uno", "Due", "Tre"])], tracks)
    assert result.status == albumcheck.STATUS_COMPLETE and result.extra == []     # gli MP3 non sono "in più"
    assert len(result.copies) == 3 and "3 copie in un altro formato" in result.status_text()
    fixes = [issue for issue in check_flow.online_issues(result, 1) if issue.fix is not None]
    changed = {Path(path).suffix for path, _values in fixes[0].fix.changes}
    assert changed == {".flac", ".mp3"}                                          # le correzioni anche alle copie
    mixed = tracks[:2] + [Track(path=Path("C:/m/Disco/03 Altro.m4a"),
                                tags=TrackTags(title="Altro", artist="Cantante Finto", album="Disco Finto"))]
    assert albumcheck.split_formats(mixed)[1] == []                     # formati diversi per brani diversi: intero


def test_albums_that_are_fine_as_they_are(tmp_path):
    from myeasymp3toiphone.accepted import ONLINE_TYPE, WHOLE_ALBUM, Accepted, problem_type, type_label
    accepted = Accepted(tmp_path)
    accepted.accept(("Alex Finto", "The Platinum Collection"), ONLINE_TYPE)
    accepted.accept(("Gruppo", "Disco"), WHOLE_ALBUM)
    accepted.save()
    again = Accepted(tmp_path)                                               # si ritrova, anche scritto diverso
    assert again.is_accepted(("ALEX FINTO", "the platinum collection (CD 1)"), ONLINE_TYPE)
    assert not again.is_accepted(("Alex Finto", "The Platinum Collection"), "R9")
    assert again.is_accepted(("Gruppo", "Disco"), "R9") and again.skip_ai(("Gruppo", "Disco"))
    assert again.skip_online(("Alex Finto", "The Platinum Collection")) and not again.skip_ai(("Alex Finto",
                                                                                                "The Platinum Collection"))
    assert [type_label(kind) for _key, kind, _when in again.rows()] == ["differenze con il catalogo online",
                                                                        "tutto l'album"]
    issue = scan.Issue(scan.KIND_ONLINE, scan.SEVERITY_LOW, "t", "d", rule_id="W2.4")
    assert problem_type(issue) == ONLINE_TYPE
    assert problem_type(scan.Issue(scan.KIND_SPLIT, scan.SEVERITY_LOW, "t", "d", origin=scan.ORIGIN_AI)) == \
        "AI_collezione_divisa"
    again.remove(("Gruppo", "Disco"), WHOLE_ALBUM)
    assert not again.is_accepted(("Gruppo", "Disco"), "R9") and len(again.rows()) == 1

    first = _album(["Uno"], album="Primo")
    second = _album(["Due"], album="Secondo")
    targets = {}
    for track in first + second:
        targets[str(track.path)] = check_flow.Target(track, pc=track)
    issues = [scan.Issue(scan.KIND_FEW_TRACKS, scan.SEVERITY_LOW, "Primo: solo 1 brano", "d", [first[0].path],
                         rule_id="R10.1"),
              scan.Issue(scan.KIND_FEW_TRACKS, scan.SEVERITY_LOW, "Secondo: solo 1 brano", "d", [second[0].path],
                         rule_id="R10.2")]
    marks = Accepted(tmp_path / "altro")
    marks.accept(first[0].album_key, "R10")
    entries, hidden = check_flow.filter_accepted(check_flow.group_by_album(issues, lambda p: targets.get(str(p))),
                                                 marks, False)
    assert hidden == 1 and [entry.key[1] for entry in entries] == ["Secondo"]
    shown, hidden = check_flow.filter_accepted(check_flow.group_by_album(issues, lambda p: targets.get(str(p))),
                                               marks, True)
    assert hidden == 1 and len(shown) == 2 and [p.accepted for e in shown for p in e.problems].count(True) == 1


def test_fine_as_they_are_in_the_results_and_skipped_online(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.accepted import ONLINE_TYPE, WHOLE_ALBUM
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        window.tracks = _album(["Uno", "Due"], album="Primo") + _album(["Tre"], album="Secondo")
        window._rebuild_views()
        window._scan()
        options = window.checks_panel.options
        for check_id, box in options.boxes.items():
            box.setChecked(check_id == scan.CHECK_FEW)
        options.ai_box.setChecked(False)
        options.online_box.setChecked(False)
        options.start_button.click()
        _wait(window, app)
        launcher = window.scan_launcher
        view = window.checks_panel.results
        primo = [entry.key for entry in view.entries if entry.key[1] == "Primo"][0]
        launcher.set_accepted([(primo, "R10")], True)                     # va bene così: un tipo, un album
        view = window.checks_panel.results
        assert [entry.key[1] for entry in view.entries] == ["Secondo"] and view.hidden == 1
        assert not view.show_accepted.isHidden()
        view.show_accepted.setChecked(True)                               # mostrati in grigio
        view = window.checks_panel.results
        shown = [entry for entry in view.entries if entry.key == primo][0]
        assert shown.problems[0].accepted
        launcher.set_accepted([(primo, "R10")], False)                    # Togli "va bene così"
        launcher.set_show_accepted(False)
        assert len(window.checks_panel.results.entries) == 2

        launcher.set_accepted([(primo, ONLINE_TYPE)], True)                # la Verifica online lo salta
        options.online_box.setChecked(True)
        options.online_flagged.setChecked(False)
        service = FakeService("deezer", ["Tre"])
        window.album_clients["deezer"] = service
        for name, box in options.service_boxes.items():
            box.setChecked(name == "deezer")
        options.start_button.click()
        _wait(window, app)
        assert service.calls == 1                                          # solo "Secondo"
        launcher.set_accepted([(primo, ONLINE_TYPE), (primo, WHOLE_ALBUM)], False)
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_the_ai_runs_after_the_online_check_in_background(monkeypatch):
    """Regole e Verifica online, poi i risultati sono già usabili e l'Analisi AI va in un lavoro a parte: il programma
    resta libero (runner non occupato), il pulsante è Ferma l'AI, alla fine i problemi dell'AI entrano nel rapporto."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui import scan_dialog
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])

    class SlowProvider(SeeingProvider):
        def ask_json(self, system, user, schema):
            time.sleep(0.3)
            return super().ask_json(system, user, schema)

    provider = SlowProvider()
    from PySide6.QtWidgets import QMessageBox
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *args, **kwargs: warnings.append(args[2])))
    window = MainWindow()
    try:
        window.tracks = _album(["Uno"], album="Primo") + _album(["Due"], artist="Altro Cantante", album="Secondo")
        window._rebuild_views()
        window._scan()
        options = window.checks_panel.options
        for check_id, box in options.boxes.items():
            box.setChecked(check_id in (scan.CHECK_FEW, scan.CHECK_MISSING))
        launcher = window.scan_launcher
        monkeypatch.setattr(launcher, "_profile", lambda: object())
        monkeypatch.setattr(scan_dialog, "make_provider", lambda profile: provider)
        options.ai_box.setEnabled(True)
        options.ai_box.setChecked(True)
        options.ai_flagged.setChecked(False)
        options.online_box.setChecked(False)
        options.start_button.click()
        deadline = time.monotonic() + 10
        while window.runner.is_busy and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
        assert launcher.ai_running() and not window.runner.is_busy                  # l'AI non occupa il programma
        assert options.start_button.text() == "Ferma l'AI"
        assert window.checks_panel.results.apply_button is not None                 # i risultati ci sono già
        deadline = time.monotonic() + 60                                             # macchina lenta: con calma
        while launcher.ai_running() and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
        app.processEvents()
        report = window.checks_panel.results.report
        assert warnings == []
        assert len(provider.seen) == 2                                              # un artista per richiesta
        assert any(issue.origin == scan.ORIGIN_AI for issue in report.issues) and report.ai_profile == "finto"
        assert options.start_button.text() == "Avvia il controllo"
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_a_problem_fixed_in_the_other_album_is_not_manual_here():
    """ "Ultime Parole" e "…Ultime Parole": la correzione è tutta nell'album scritto male; sotto quello giusto il
    problema dice "nell'altro album", non "a mano", e non ne alza la gravità."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui.check_results import COL_FIX, CheckResultsView
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    right = _album(["Uno", "Due"], album="Ultime Parole")
    wrong = _album(["Tre"], album="…Ultime Parole")
    targets = {}
    for track in right + wrong:
        targets[str(track.path)] = check_flow.Target(track, pc=track)
    issue = scan.Issue(scan.KIND_SPLIT, scan.SEVERITY_HIGH, '"Ultime Parole" anche come "…Ultime Parole"', "d",
                       [track.path for track in right + wrong],
                       scan.Fix(scan.FIX_TAGS, "Album", changes=[(wrong[0].path, {"album": "Ultime Parole"})]),
                       rule_id="R12.1")
    entries = check_flow.group_by_album([issue], lambda path: targets.get(str(path)))
    by_album = {entry.key[1]: entry for entry in entries}
    assert by_album["…Ultime Parole"].problems[0].rows and not by_album["…Ultime Parole"].problems[0].elsewhere
    assert by_album["Ultime Parole"].problems[0].elsewhere == [("Cantante Finto", "…Ultime Parole")]
    assert by_album["Ultime Parole"].severity == scan.SEVERITY_LOW and by_album["…Ultime Parole"].severity == \
        scan.SEVERITY_HIGH
    assert [entry.key[1] for entry in entries] == ["…Ultime Parole", "Ultime Parole"]   # quello da correggere prima
    window = MainWindow()
    try:
        report = scan.ScanReport(target="prova", issues=[issue], tracks_scanned=3, albums_scanned=2)
        view = CheckResultsView(window.scan_launcher, report, entries, None, {}, check_flow.SIDE_PC)
        texts = {}
        for index in range(view.tree.topLevelItemCount()):
            top = view.tree.topLevelItem(index)
            texts[top.text(0)] = (top.text(COL_FIX), top.child(0).text(COL_FIX))
        assert texts["Cantante Finto — …Ultime Parole"] == ("1 automatiche", "automatica (1)")
        assert texts["Cantante Finto — Ultime Parole"] == ("si corregge nell'altro album", "nell'altro album")
        view.close()
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()
