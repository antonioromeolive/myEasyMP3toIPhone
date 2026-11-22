# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

import os
import stat
import time

import pytest
from mutagen.id3 import ID3

from conftest import write_mp3
from myeasymp3toiphone import scan
from myeasymp3toiphone.library import copy_organized, scan_folder, target_relative_path
from myeasymp3toiphone.tags import TrackTags, read_tags, write_tags


def _tagged(path, frames: int = 40, **values):
    write_mp3(path, frames)
    write_tags(path, TrackTags(**values))


def test_id3_saved_as_v23_with_year_readable(tmp_path):
    path = tmp_path / "a.mp3"
    _tagged(path, title="T", artist="A", album="B", year="1999", track_number=1)
    id3 = ID3(str(path), translate=False)  # come è scritto nel file, senza la conversione in memoria a v2.4
    assert id3.version[:2] == (2, 3)
    assert "TYER" in id3 and "TDRC" not in id3
    assert read_tags(path)[0].year == "1999"


def test_copy_skips_identical_updates_older_keeps_newer(tmp_path):
    source = tmp_path / "src" / "x.mp3"
    _tagged(source, title="Uno", artist="A", album="B", track_number=1)
    library = tmp_path / "lib"
    first = copy_organized(scan_folder(tmp_path / "src"), library)
    assert len(first.copied) == 1
    again = copy_organized(scan_folder(tmp_path / "src"), library)
    assert len(again.skipped) == 1
    # tag modificati: stessa dimensione, data più recente -> aggiornato
    tags = read_tags(source)[0]
    tags.genre = "Rock"
    write_tags(source, tags)
    later = time.time() + 60
    os.utime(source, (later, later))
    updated = copy_organized(scan_folder(tmp_path / "src"), library)
    assert len(updated.updated) == 1
    destination = library / target_relative_path(scan_folder(tmp_path / "src")[0])
    assert read_tags(destination)[0].genre == "Rock"
    older = time.time() - 3600
    os.utime(source, (older, older))
    kept = copy_organized(scan_folder(tmp_path / "src"), library)
    assert len(kept.kept_newer) == 1


def test_move_never_overwrites(tmp_path):
    root = tmp_path / "root"
    _tagged(root / "a" / "1.mp3", title="Intro", artist="A", album="B")
    _tagged(root / "b" / "2.mp3", frames=50, title="Intro", artist="A", album="B")
    report = copy_organized(scan_folder(root), root, move=True, source_root=root)
    assert len(report.copied) == 2
    assert len(scan_folder(root)) == 2


def test_file_problems_are_informational_and_files_untouched(tmp_path):
    stale = tmp_path / "v1.mp3"
    _tagged(stale, title="Nuovo titolo", artist="A", album="B")
    with stale.open("ab") as handle:  # un vecchio ID3v1 con un altro titolo, in fondo
        handle.write(b"TAG" + b"Vecchio titolo".ljust(30, b"\x00") + b"A".ljust(30, b"\x00")
                     + b"B".ljust(30, b"\x00") + b"1999" + b"\x00" * 30 + b"\x00")
    v24 = tmp_path / "v24.mp3"
    _tagged(v24, title="X", artist="A", album="B")
    ID3(str(v24)).save(str(v24), v2_version=4)
    before = {path.name: path.read_bytes() for path in tmp_path.glob("*.mp3")}
    issues = scan.detect_file_problems(scan_folder(tmp_path))
    by_rule = {issue.rule_id: issue for issue in issues}
    assert set(by_rule) == {"R2"}
    assert [p.name for p in by_rule["R2"].files] == ["v1.mp3"]
    assert by_rule["R2"].fix is None and by_rule["R2"].severity == scan.SEVERITY_LOW
    assert {path.name: path.read_bytes() for path in tmp_path.glob("*.mp3")} == before


def test_few_tracks_and_split_collections(tmp_path):
    album = tmp_path / "Compilation"
    _tagged(album / "01.mp3", title="Uno", artist="Rossi", album="Estate 2020", track_number=1, track_total=10)
    _tagged(album / "02.mp3", title="Due", artist="Bianchi", album="Estate 2020", track_number=2, track_total=10)
    _tagged(tmp_path / "Band" / "a.mp3", title="A", artist="The Band", album="Live (CD 1)", track_number=1)
    _tagged(tmp_path / "Band2" / "b.mp3", title="B", artist="the band", album="Live (CD 2)", track_number=1)
    tracks = scan_folder(tmp_path)
    issues = scan.rule_issues(tracks, check_files=False)
    titles = " | ".join(issue.title for issue in issues)
    assert "su almeno 10" in titles
    folder_split = [i for i in issues if i.rule_id.startswith("R11")]
    assert folder_split and folder_split[0].fix is not None
    name_split = [i for i in issues if i.rule_id.startswith("R12")]
    assert name_split
    changes = dict((p.name, v) for p, v in name_split[0].fix.changes)
    assert changes["b.mp3"]["disc_number"] == 2 and changes["b.mp3"]["album"] == "Live"
    from myeasymp3toiphone.overlay import TagOverlay
    overlay = TagOverlay(tmp_path / "home")
    tracks = scan_folder(album)
    by_path = {str(t.path): t for t in tracks}
    for path, values in scan.tag_changes_of(folder_split[0].fix):
        track = by_path[str(path)]
        new_tags = track.tags.copy()
        for name, value in values.items():
            setattr(new_tags, name, value)
        overlay.set_tags(track, new_tags)
    overlay.save()
    reloaded = scan_folder(album)
    assert {t.album_key for t in reloaded} == {("Bianchi", "Estate 2020"), ("Rossi", "Estate 2020")}  # disco intatto
    TagOverlay(tmp_path / "home").apply(reloaded)
    from myeasymp3toiphone.library import assign_groups
    assign_groups(reloaded)
    assert {t.album_key for t in reloaded} == {(scan.VARIOUS_ARTISTS, "Estate 2020")}


class FakeProvider:
    def __init__(self, reply):
        self.reply = reply
        self.profile = type("P", (), {"name": "finto"})()
        self.seen = ""

    def ask_json(self, system, user, schema):
        self.seen = user
        return self.reply


def test_ai_review_maps_albums_and_marks_false_positives(tmp_path):
    _tagged(tmp_path / "a" / "1.mp3", title="X", artist="Queen", album="Greatest Hits", track_number=1)
    _tagged(tmp_path / "b" / "1.mp3", title="Y", artist="ABBA", album="Greatest Hits", track_number=1)
    tracks = scan_folder(tmp_path)
    rules = scan.rule_issues(tracks, check_files=False)
    split = [i for i in rules if i.rule_id.startswith("R13")][0]
    reply = {"issues": [{"kind": "tag_mancanti", "severity": "bassa", "title": "Genere mancante", "explanation": "e",
                         "albums": ["A1", "A99"], "fix_album": "", "fix_album_artist": "", "fix_artist": "",
                         "fix_year": "19x", "fix_genre": "Pop"}],
             "false_positives": [{"rule_id": split.rule_id, "reason": "album diversi"}]}
    provider = FakeProvider(reply)
    found, errors = scan.ai_review(provider, tracks, rules)
    assert errors == []
    assert split.ai_note == "album diversi"
    assert len(found) == 1 and found[0].fix is not None
    assert all(values == {"genre": "Pop"} for _path, values in found[0].fix.changes)
    assert "A1 | album artist:" in provider.seen


def test_case_variants_are_one_group_shown_with_capitals(tmp_path):
    _tagged(tmp_path / "a" / "1.mp3", title="X", artist="Queen", album="Live at Wembley", track_number=1)
    _tagged(tmp_path / "b" / "2.mp3", title="Y", artist="queen", album="live at  wembley", track_number=2)
    from myeasymp3toiphone.library import group_by_album
    groups = group_by_album(scan_folder(tmp_path))
    assert list(groups) == [("Queen", "Live at Wembley")]
    # la scansione segnala comunque la grafia diversa nei tag
    issues = scan.detect_artist_variants(scan_folder(tmp_path))
    assert issues and dict((p.name, v) for p, v in issues[0].fix.changes)["2.mp3"] == {"artist": "Queen"}


def test_same_song_on_different_albums_is_not_a_duplicate(tmp_path):
    _tagged(tmp_path / "Hits" / "Song.mp3", title="Song", artist="A", album="Original", track_number=1)
    _tagged(tmp_path / "Hits" / "Song (2).mp3", frames=50, title="Song", artist="A", album="Raccolta",
            track_number=1)
    assert scan.detect_duplicates(scan_folder(tmp_path)) == []
    _tagged(tmp_path / "Same" / "Song.mp3", title="Song", artist="A", album="Uno", track_number=1)
    _tagged(tmp_path / "Same" / "Song (2).mp3", frames=50, title="Song", artist="A", album="Uno", track_number=1)
    issues = scan.detect_duplicates(scan_folder(tmp_path))
    assert {issue.rule_id for issue in issues} == {"R7", "R8"}
    assert all(issue.fix is None for issue in issues)  # quale tenere lo decide l'utente


def test_overlay_never_touches_files_and_copies_get_changes(tmp_path):
    from myeasymp3toiphone.overlay import TagOverlay
    from myeasymp3toiphone.tags import TagError, is_protected, prepare_copy, protect_folder, read_cover
    source = tmp_path / "musica" / "a.mp3"
    _tagged(source, title="Vecchio", artist="A", album="B", track_number=1)
    with source.open("ab") as handle:
        handle.write(b"TAG" + b"Vecchio".ljust(30, b"\x00") + b"A".ljust(90, b"\x00") + b"\x00" * 35)
    protect_folder(tmp_path / "musica")
    assert is_protected(source)
    original = source.read_bytes()
    try:
        write_tags(source, TrackTags(title="X"))
        raised = False
    except TagError:
        raised = True
    assert raised and source.read_bytes() == original
    track = scan_folder(tmp_path / "musica")[0]
    overlay = TagOverlay(tmp_path / "home")
    new_tags = track.tags.copy()
    new_tags.title = "Nuovo"
    overlay.set_tags(track, new_tags)
    overlay.set_cover(track, b"\x89PNG\r\n\x1a\n" + b"0" * 20)
    signature = overlay.signature(track.path)
    overlay.save()
    assert source.read_bytes() == original
    assert track.tags.title == "Nuovo" and track.original_tags.title == "Vecchio"
    # la copia esportata riceve le modifiche, l'originale no
    from myeasymp3toiphone.library import copy_organized
    report = copy_organized([track], tmp_path / "export", prepare=lambda t, c: prepare_copy(c, t.tags,
                            overlay.cover_for(t.path)), forced=lambda t: overlay.is_edited(t.path))
    copy = report.copied[0][1]
    assert read_tags(copy)[0].title == "Nuovo" and read_cover(copy) is not None
    assert b"TAG" not in copy.read_bytes()[-128:-125]   # niente ID3v1 nella copia
    assert source.read_bytes() == original
    # una modifica nuova: la copia si rifà
    again = track.tags.copy()
    again.genre = "Rock"   # un campo che non cambia il nome del file: la stessa copia va rifatta
    overlay.set_tags(track, again)
    assert overlay.signature(track.path) != signature
    report = copy_organized([track], tmp_path / "export", prepare=lambda t, c: prepare_copy(c, t.tags, None),
                            forced=lambda t: overlay.is_edited(t.path))
    assert report.updated and read_tags(report.updated[0][1])[0].genre == "Rock"
    overlay.clear(track)
    assert track.tags.title == "Vecchio" and not overlay.is_edited(track.path)


def test_import_never_overwrites(tmp_path):
    from myeasymp3toiphone.library import copy_organized
    _tagged(tmp_path / "tmp" / "a.mp3", frames=50, title="Uno", artist="A", album="B", track_number=1)
    _tagged(tmp_path / "lib" / "A" / "B" / "01 - Uno.mp3", title="Uno", artist="A", album="B", track_number=1)
    existing = (tmp_path / "lib" / "A" / "B" / "01 - Uno.mp3").read_bytes()
    report = copy_organized(scan_folder(tmp_path / "tmp"), tmp_path / "lib", move=True, overwrite=False)
    assert report.skipped and (tmp_path / "lib" / "A" / "B" / "01 - Uno.mp3").read_bytes() == existing


def test_tag_cache_reuses_unchanged_files(tmp_path):
    from myeasymp3toiphone.tag_cache import TagCache
    _tagged(tmp_path / "m" / "a.mp3", title="Uno", artist="A", album="B", track_number=1)
    _tagged(tmp_path / "m" / "b.mp3", frames=45, title="Due", artist="A", album="B", track_number=2)
    cache = TagCache(tmp_path / "home")
    first = scan_folder(tmp_path / "m", cache=cache)
    assert [t.title for t in first] == ["Uno", "Due"] and len(cache) == 2
    again = TagCache(tmp_path / "home")   # riletta dal file
    assert again.lookup(tmp_path / "m" / "a.mp3")[0].title == "Uno"
    tags = read_tags(tmp_path / "m" / "a.mp3")[0]
    tags.title = "Uno bis"
    write_tags(tmp_path / "m" / "a.mp3", tags)
    later = time.time() + 30
    os.utime(tmp_path / "m" / "a.mp3", (later, later))
    assert again.lookup(tmp_path / "m" / "a.mp3") is None   # file cambiato: si rilegge
    assert [t.title for t in scan_folder(tmp_path / "m", cache=again)] == ["Uno bis", "Due"]


def test_reopening_uses_the_folder_listing_not_one_stat_per_file(tmp_path, monkeypatch):
    """Riaprire una cartella grande: dimensione e data vengono dall'elenco della cartella, non da un stat() per
    file (lento su dischi esterni e di rete); i valori sono gli stessi che la cache ha salvato."""
    from pathlib import Path

    from myeasymp3toiphone import library
    from myeasymp3toiphone.tag_cache import TagCache
    _tagged(tmp_path / "m" / "x" / "a.mp3", title="Uno", artist="A", album="B", track_number=1)
    _tagged(tmp_path / "m" / "b.mp3", frames=45, title="Due", artist="A", album="B", track_number=2)
    (tmp_path / "m" / "note.txt").write_text("non è musica")
    cache = TagCache(tmp_path / "home")
    scan_folder(tmp_path / "m", cache=cache)
    entries = library.find_audio_entries(tmp_path / "m")
    assert [path.name for path, _size, _mtime in entries] == ["b.mp3", "a.mp3"]
    assert library.find_audio_files(tmp_path / "m") == [path for path, _size, _mtime in entries]
    original_stat = Path.stat

    def no_stat_of_audio(self, *args, **kwargs):
        assert self.suffix != ".mp3", f"stat() su {self.name}: doveva bastare l'elenco della cartella"
        result = original_stat(self, *args, **kwargs)
        return result

    monkeypatch.setattr(Path, "stat", no_stat_of_audio)
    monkeypatch.setattr(library, "load_track", lambda path: pytest.fail(f"{path.name} riletto: era in cache"))
    again = scan_folder(tmp_path / "m", cache=TagCache(tmp_path / "home"))
    assert sorted(t.title for t in again) == ["Due", "Uno"]
