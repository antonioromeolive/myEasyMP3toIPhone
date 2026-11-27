# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le correzioni sul PC: solo in sospeso (i file non cambiano) o anche nei file (solo dopo l'elenco dei file e dei
campi approvato; i campi spenti restano in sospeso). Nomi e valori inventati."""

import os
import time

from conftest import write_mp3
from myeasymp3toiphone import scan
from myeasymp3toiphone.library import scan_folder
from myeasymp3toiphone.tags import TrackTags, read_tags, write_tags


def _tagged(path, **values):
    write_mp3(path)
    write_tags(path, TrackTags(**values))


def test_fix_only_in_suspense_or_also_in_the_pc_files(tmp_path, monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.check_flow import SIDE_PC, group_by_album
    from myeasymp3toiphone.gui import check_results, pc_write
    from myeasymp3toiphone.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    folder = tmp_path / "Raccolta"
    one, two = folder / "01.mp3", folder / "02.mp3"
    _tagged(one, title="Uno", artist="Anna Finta", album="Raccolta", year="2001")
    _tagged(two, title="Due", artist="Bruno Finto", album="Raccolta", year="2001")
    window = MainWindow()

    def wait_idle():
        deadline = time.monotonic() + 10
        while window.runner.is_busy and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
        app.processEvents()

    def view_for(changes):
        issue = scan.Issue(scan.KIND_SPLIT, scan.SEVERITY_HIGH, "Raccolta divisa", "d", [one, two],
                           scan.Fix(scan.FIX_TAGS, "Artista album \"Artisti vari\"", changes=changes), rule_id="R11.1")
        report = scan.ScanReport(target="prova", issues=[issue], tracks_scanned=2, albums_scanned=2)
        launcher = window.scan_launcher
        launcher.applied = set()                 # ogni vista come dopo un controllo nuovo
        entries = group_by_album(report.issues, launcher._resolver(SIDE_PC, window.tracks, []))
        result = check_results.CheckResultsView(launcher, report, entries, None, {}, SIDE_PC)
        return result

    def files_too(on):
        def answer(dialog):
            dialog.pc_files.setChecked(on)
            return True
        return answer

    try:
        window.tracks = scan_folder(folder)
        window._rebuild_views()
        changes = [(one, {"album_artist": "Artisti vari", "year": "1999"}), (two, {"album_artist": "Artisti vari"})]

        # nei file no: in sospeso, i file non cambiano
        monkeypatch.setattr(check_results.ApplyDestinationsDialog, "exec", files_too(False))
        view = view_for(changes)
        view.apply_button.click()
        wait_idle()
        assert read_tags(one)[0].album_artist == "" and window.overlay.is_edited(one)
        view.close()

        # anche nei file: l'elenco, con l'anno spento; si scrive solo l'artista dell'album
        changes = [(one, {"album_artist": "Vari Artisti", "year": "1998"}), (two, {"album_artist": "Vari Artisti"})]
        shown = []

        def approve(pc_dialog):
            shown.append(pc_dialog)
            pc_dialog._boxes["year"].setChecked(False)
            return True

        monkeypatch.setattr(check_results.ApplyDestinationsDialog, "exec", files_too(True))
        monkeypatch.setattr(pc_write.PcWriteDialog, "exec", approve)
        view = view_for(changes)
        view.apply_button.click()
        wait_idle()
        assert len(shown) == 1 and set(shown[0]._boxes) == {"album_artist", "year"}
        assert [read_tags(path)[0].album_artist for path in (one, two)] == ["Vari Artisti", "Vari Artisti"]
        assert read_tags(one)[0].year == "2001"                     # campo spento: il file non cambia
        assert window.overlay.is_edited(one) and not window.overlay.is_edited(two)   # l'anno resta per l'iPhone
        view.close()

        # Annulla nell'elenco: niente cambia nei file
        monkeypatch.setattr(pc_write.PcWriteDialog, "exec", lambda pc_dialog: False)
        view = view_for([(two, {"genre": "Pop"})])
        view.apply_button.click()
        wait_idle()
        assert read_tags(two)[0].genre == "" and window.overlay.is_edited(two)
        view.close()
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def test_pending_plan_skips_read_only_files_and_repeats(tmp_path):
    from myeasymp3toiphone.gui.pc_write import pending_plan
    from myeasymp3toiphone.library import Track
    from pathlib import Path
    track = Track(path=Path("C:/m/Disco/01.mp3"), tags=TrackTags(title="Uno", year="1999"))
    track.original_tags = TrackTags(title="Uno", year="2001")
    wma = Track(path=Path("C:/m/Disco/02.wma"), tags=TrackTags(title="Due", year="1999"))
    wma.original_tags = TrackTags(title="Due", year="2001")
    same = Track(path=Path("C:/m/Disco/03.mp3"), tags=TrackTags(title="Tre"))
    same.original_tags = TrackTags(title="Tre")
    plan = pending_plan([track, wma, same, track])
    assert [(item.path.name, fields) for item, _tags, fields in plan] == [("01.mp3", ["year"])]


def test_old_id3v1_and_ape_tags_leave_the_pc_files_only_after_the_approved_list(tmp_path, monkeypatch):
    """R2 e R3 come correzioni: i vecchi tag (ID3v1 diverso, APE) si tolgono dai file del PC solo dopo l'elenco
    approvato (c'è → tolto); i valori che c'erano solo lì (qui l'album, solo nell'APE) passano prima nell'ID3v2."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from mutagen.apev2 import APEv2
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.check_flow import SIDE_PC, group_by_album, plan_apply
    from myeasymp3toiphone.gui import check_results, pc_write
    from myeasymp3toiphone.gui.main_window import MainWindow
    from myeasymp3toiphone.tags import OLD_APE, OLD_ID3V1, tag_kinds
    app = QApplication.instance() or QApplication([])
    folder = tmp_path / "Disco"
    path = folder / "01.mp3"
    _tagged(path, title="Titolo nuovo", artist="Anna Finta")
    ape = APEv2()
    ape["Album"] = "Album solo APE"
    ape.save(str(path))
    with path.open("ab") as handle:                                # un ID3v1 con il titolo vecchio, in fondo
        handle.write(b"TAG" + b"Titolo vecchio".ljust(30, b"\x00") + b"Anna Finta".ljust(30, b"\x00")
                     + b"".ljust(30, b"\x00") + b"1999" + b"\x00" * 30 + b"\x00")
    window = MainWindow()
    shown = []

    def approve(pc_dialog):
        shown.append(pc_dialog)
        return True

    try:
        window.tracks = scan_folder(folder)
        window._rebuild_views()
        assert window.tracks[0].tags.album == "Album solo APE"
        issues = scan.detect_file_problems(window.tracks)
        assert sorted(issue.rule_id for issue in issues) == ["R2", "R3"]
        report = scan.ScanReport(target="prova", issues=issues, tracks_scanned=1, albums_scanned=1)
        launcher = window.scan_launcher
        launcher.applied = set()
        entries = group_by_album(report.issues, launcher._resolver(SIDE_PC, window.tracks, []))
        rows = []
        for entry in entries:
            for problem in entry.problems:
                rows += problem.rows
        assert sorted((row.name, row.old, row.new) for row in rows) == [(OLD_APE, "c'è", "tolto"),
                                                                       (OLD_ID3V1, "c'è", "tolto")]
        plan = plan_apply(rows)
        assert plan.pc == [] and plan.linked == []                  # nessun campo: solo i vecchi tag
        assert [sorted(names) for _track, names in plan.old_tags] == [sorted([OLD_ID3V1, OLD_APE])]

        # Annulla nell'elenco: il file non cambia
        before = path.read_bytes()
        monkeypatch.setattr(check_results.ApplyDestinationsDialog, "exec", lambda dialog: True)
        monkeypatch.setattr(pc_write.PcWriteDialog, "exec", lambda pc_dialog: False)
        view = check_results.CheckResultsView(launcher, report, entries, None, {}, SIDE_PC)
        view.apply_button.click()
        _wait_idle(window, app)
        assert path.read_bytes() == before
        assert len(view.chosen_rows()) == 2                         # non tolti: restano da applicare, senza ✔
        view.close()

        # approvato: l'elenco li mostra (c'è → tolto), poi restano solo l'ID3v2 e i valori
        monkeypatch.setattr(pc_write.PcWriteDialog, "exec", approve)
        view = check_results.CheckResultsView(launcher, report, entries, None, {}, SIDE_PC)
        assert len(view.chosen_rows()) == 2
        view.apply_button.click()
        _wait_idle(window, app)
        assert len(shown) == 1 and set(shown[0]._boxes) == {OLD_ID3V1, OLD_APE}
        tree = shown[0]._tree
        assert sorted(tree.topLevelItem(index).text(2) + " → " + tree.topLevelItem(index).text(3)
                      for index in range(tree.topLevelItemCount())) == ["c'è → tolto", "c'è → tolto"]
        kinds = tag_kinds(path)
        assert "APEv2" not in kinds and "ID3v1" not in kinds and kinds[0].startswith("ID3v2")
        tags = read_tags(path)[0]
        assert (tags.title, tags.artist, tags.album) == ("Titolo nuovo", "Anna Finta", "Album solo APE")
        assert [issue.rule_id for issue in scan.detect_file_problems(scan_folder(folder))] == []
        assert view.chosen_rows() == []                              # tolti davvero: ora sono applicati
        view.close()
    finally:
        window._exit_checked = True
        window.close()
        app.processEvents()


def _wait_idle(window, app):
    deadline = time.monotonic() + 10
    while window.runner.is_busy and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()
