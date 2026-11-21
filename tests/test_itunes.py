# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""L'invio a iTunes con un iTunes finto: mai quello vero nei test."""

import subprocess

import pytest

from conftest import write_flac, write_mp3
from myeasymp3toiphone import itunes
from myeasymp3toiphone.library import scan_folder
from myeasymp3toiphone.overlay import TagOverlay
from myeasymp3toiphone.tags import TrackTags, read_cover, read_tags, write_cover, write_tags


class FakeTrack:
    def __init__(self, bridge, pid):
        self.bridge = bridge
        self.pid = pid

    def UpdateInfoFromFile(self):
        self.bridge.refreshed.append(self.pid)

    def Delete(self):
        self.bridge.library.pop(tuple(self.pid), None)


class FakeITunes:
    def __init__(self):
        self.library = {}
        self.refreshed = []
        self.synced = False
        self.next_id = 1

    def find(self, pid):
        result = None
        if pid and tuple(pid) in self.library:
            result = FakeTrack(self, pid)
        return result

    def add(self, path):
        pid = [0, self.next_id]
        self.next_id += 1
        self.library[tuple(pid)] = path
        return pid

    def sync(self):
        self.synced = True
        return ["iPhone di prova"]

    def close(self):
        pass


def _setup(tmp_path):
    source = tmp_path / "musica" / "a.mp3"
    write_mp3(source)
    write_tags(source, TrackTags(title="Uno", artist="A", album="B", track_number=1))
    return source


def test_send_copies_skips_updates_and_moves(tmp_path):
    source = _setup(tmp_path)
    original = source.read_bytes()
    home = tmp_path / "home"
    root = tmp_path / "copie"
    overlay = TagOverlay(home)
    fake = FakeITunes()
    tracks = scan_folder(tmp_path / "musica")
    report = itunes.send_to_itunes(tracks, root, overlay, home, True, bridge_factory=lambda: fake)
    assert len(report.added) == 1 and report.synced == ["iPhone di prova"]
    copy = root / "A" / "B" / "01 - Uno.mp3"
    assert copy.exists() and read_tags(copy)[0].title == "Uno"
    assert source.read_bytes() == original
    # di nuovo, niente cambiato: saltato
    report = itunes.send_to_itunes(scan_folder(tmp_path / "musica"), root, overlay, home, False,
                                   bridge_factory=lambda: fake)
    assert report.skipped == 1 and not report.added and not fake.refreshed
    # una modifica in sospeso che non cambia il nome: la stessa copia si aggiorna
    tracks = scan_folder(tmp_path / "musica")
    new_tags = tracks[0].tags.copy()
    new_tags.genre = "Rock"
    overlay.set_tags(tracks[0], new_tags)
    report = itunes.send_to_itunes(tracks, root, overlay, home, False, bridge_factory=lambda: fake)
    assert len(report.updated) == 1 and fake.refreshed and read_tags(copy)[0].genre == "Rock"
    # un album diverso: copia nuova, quella vecchia e il brano vecchio di iTunes tolti
    tracks = scan_folder(tmp_path / "musica")
    overlay.apply(tracks)
    moved = tracks[0].tags.copy()
    moved.album = "C"
    overlay.set_tags(tracks[0], moved)
    report = itunes.send_to_itunes(tracks, root, overlay, home, False, bridge_factory=lambda: fake)
    assert len(report.added) == 1 and not copy.exists() and not (root / "A" / "B").exists()
    assert (root / "A" / "C" / "01 - Uno.mp3").exists() and len(fake.library) == 1
    assert source.read_bytes() == original


def test_flac_without_ffmpeg_is_skipped(tmp_path, monkeypatch):
    write_flac(tmp_path / "musica" / "a.flac")
    write_tags(tmp_path / "musica" / "a.flac", TrackTags(title="F", artist="A", album="B", track_number=1))
    monkeypatch.setattr(itunes, "find_ffmpeg", lambda: None)
    report = itunes.send_to_itunes(scan_folder(tmp_path / "musica"), tmp_path / "copie", TagOverlay(tmp_path / "h"),
                                   tmp_path / "h", False, bridge_factory=FakeITunes)
    assert len(report.needs_ffmpeg) == 1 and not report.added


@pytest.mark.skipif(itunes.find_ffmpeg() is None, reason="ffmpeg non installato")
def test_flac_becomes_alac_with_tags_and_cover(tmp_path):
    source = tmp_path / "musica" / "a.flac"
    source.parent.mkdir(parents=True)
    subprocess.run([itunes.find_ffmpeg(), "-nostdin", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "anullsrc=r=44100:cl=stereo", "-t", "1", "-c:a", "flac", str(source)], check=True)
    write_tags(source, TrackTags(title="Lossless", artist="A", album="B", track_number=3, year="2020"))
    write_cover(source, b"\x89PNG\r\n\x1a\n" + b"0" * 30)
    original = source.read_bytes()
    report = itunes.send_to_itunes(scan_folder(tmp_path / "musica"), tmp_path / "copie", TagOverlay(tmp_path / "h"),
                                   tmp_path / "h", False, bridge_factory=FakeITunes)
    copy = tmp_path / "copie" / "A" / "B (2020)" / "03 - Lossless.m4a"
    assert len(report.added) == 1 and copy.exists()
    assert read_tags(copy)[0].title == "Lossless" and read_cover(copy) is not None
    assert source.read_bytes() == original
