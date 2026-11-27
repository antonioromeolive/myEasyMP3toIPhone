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
        assert [read_tags(path)[0].album_artist for path in (one, two)] == ["Artisti vari", "Artisti vari"]
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
