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
    local = _album(["uno", "Due"])                                 # "uno": minuscolo, il catalogo dice "Uno"
    result = albumcheck.check_album_services([FakeService("deezer", ["Uno", "Due", "Tre"])], local)
    issues = check_flow.online_issues(result, 1)
    by_rule = {issue.rule_id: issue for issue in issues}
    assert set(by_rule) == {"W1.1", "W2.1"}
    assert "mancano 1 di 3 brani" in by_rule["W1.1"].title and "03 Tre" in by_rule["W1.1"].detail
    changes = dict((Path(path).name, values) for path, values in by_rule["W2.1"].fix.changes)
    assert changes["01 uno.mp3"]["title"] == "Uno" and changes["01 uno.mp3"]["track_total"] == 3
    missing = albumcheck.check_album_services([FakeService("deezer", None)], local)
    assert [issue.rule_id for issue in check_flow.online_issues(missing, 2)] == ["W3.2"]
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
    from PySide6.QtWidgets import QApplication
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
