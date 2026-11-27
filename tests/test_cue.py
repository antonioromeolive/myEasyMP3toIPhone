# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""FLAC + CUE: un file solo con tutto il disco non è un album di un brano né un album con le tracce mancanti. Nomi e
valori inventati."""

from pathlib import Path

from test_albumcheck import FakeService
from myeasymp3toiphone import albumcheck, check_flow, cue, scan
from myeasymp3toiphone.library import Track
from myeasymp3toiphone.tags import TrackTags

SHEET = """REM GENRE Rock
PERFORMER "Gruppo Finto"
TITLE "Disco Finto"
FILE "Gruppo Finto - Disco Finto.wav" WAVE
  TRACK 01 AUDIO
    TITLE "Uno"
    INDEX 01 00:00:00
  TRACK 02 AUDIO
    TITLE "Due"
    INDEX 01 04:10:00
  TRACK 03 AUDIO
    TITLE "Tre"
    INDEX 01 08:02:00
"""


def _image(folder: Path, name: str = "Gruppo Finto - Disco Finto", **values) -> Track:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.flac"
    path.write_bytes(b"non un vero FLAC")
    tags = TrackTags(title=values.pop("title", "Disco Finto"), artist="Gruppo Finto", album="Disco Finto", **values)
    result = Track(path=path, tags=tags)
    return result


def test_the_sheet_says_which_file_holds_how_many_tracks(tmp_path):
    assert cue.tracks_by_file(SHEET) == {"gruppo finto - disco finto": 3}      # .wav nel CUE, .flac sul disco
    folder = tmp_path / "Gruppo Finto - Disco Finto (FLAC CUE)"
    image = _image(folder)
    (folder / "Gruppo Finto - Disco Finto.cue").write_text(SHEET, encoding="cp1252")
    single = _image(folder, "Altro")                                            # nessun CUE lo nomina
    assert cue.cue_images([image, single]) == {image.path: 3}
    assert cue.all_images([image]) and not cue.all_images([image, single]) and not cue.all_images([])
    # un CUE con lo stesso nome del file vale anche se dentro nomina un altro file; accenti in ANSI
    other = tmp_path / "Altro disco"
    renamed = _image(other, "Città")
    (other / "Città.cue").write_bytes(SHEET.replace("Gruppo Finto - Disco Finto.wav", "CDImage.ape")
                                      .encode("cp1252"))
    assert cue.cue_images([renamed]) == {renamed.path: 3}
    one_track = tmp_path / "Singolo"
    lonely = _image(one_track, "Singolo")
    (one_track / "Singolo.cue").write_text('FILE "Singolo.wav" WAVE\n  TRACK 01 AUDIO\n', encoding="utf-8")
    assert cue.cue_images([lonely]) == {}                                       # una traccia: è un singolo


def test_a_whole_disc_image_is_not_an_album_with_one_track(tmp_path):
    folder = tmp_path / "Disco"
    image = _image(folder, track_number=1, track_total=3)                       # "1 di 3": i numeri 2 e 3 "mancano"
    alone = _image(tmp_path / "Solo", "Senza CUE")
    alone.tags.album = "Altro Disco"
    found = {issue.rule_id.split(".")[0]: issue.files for issue in scan.detect_few_tracks([image, alone])}
    assert found == {"R9": [image.path], "R10": [alone.path]}                   # senza CUE: 1 di 3, e un brano solo
    (folder / "Disco.cue").write_text(SHEET.replace("Gruppo Finto - Disco Finto.wav", "Gruppo Finto - Disco Finto"
                                                                                       ".flac"), encoding="utf-8")
    found = {issue.rule_id.split(".")[0]: issue.files for issue in scan.detect_few_tracks([image, alone])}
    assert found == {"R10": [alone.path]}                                       # con il CUE: l'immagine va bene
    lines = scan.album_lines({("Gruppo Finto", "Disco Finto"): [image]}, [("Gruppo Finto", "Disco Finto")])
    assert "immagine CUE: 3 tracce in 1 file" in lines[0][1]                    # lo sa anche l'AI


def test_the_online_check_of_an_image_gives_only_the_album_fields(tmp_path):
    folder = tmp_path / "Disco"
    image = _image(folder, title="Disco Finto (immagine)", track_number=1, year="1990")
    (folder / "Gruppo Finto - Disco Finto.cue").write_text(SHEET, encoding="utf-8")
    result = albumcheck.check_album_services([FakeService("deezer", ["Disco Finto (immagine)", "Due", "Tre"])],
                                             [image])
    issues = check_flow.online_issues(result, 1)
    assert [issue.rule_id for issue in issues if issue.rule_id.startswith("W1")] == []     # niente brani "mancanti"
    for issue in issues:
        if issue.fix is not None:
            for _path, values in issue.fix.changes:
                assert set(values) <= set(check_flow.CUE_FIELDS)                  # mai titolo o numero del brano
