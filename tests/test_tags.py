# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La lettura di tutti i tipi di tag: ID3v2, APEv2, ID3v1 negli MP3, RIFF INFO e ID3 nei WAV. Nomi inventati."""

import struct

import pytest
from mutagen.apev2 import APEv2
from mutagen.id3 import ID3, TIT2

from conftest import write_mp3
from myeasymp3toiphone import tag_cache
from myeasymp3toiphone.tags import TagError, TrackTags, read_all_tags, read_tags, tag_kinds, write_tags


def _v1_block(title: str, artist: str, album: str, year: str, track: int, genre: int) -> bytes:
    def field(text: str, size: int) -> bytes:
        result = text.encode("latin-1")[:size].ljust(size, b"\x00")
        return result

    result = (b"TAG" + field(title, 30) + field(artist, 30) + field(album, 30) + field(year, 4) + field("", 28)
              + b"\x00" + bytes([track]) + bytes([genre]))
    return result


def test_mp3_with_only_ape_and_id3v1_is_read(tmp_path):
    path = tmp_path / "solo_ape.mp3"
    write_mp3(path)
    ape = APEv2()
    ape["Title"] = "Nuvola"
    ape["Artist"] = "Cantante Finto"
    ape["Track"] = "1/12"
    ape.save(str(path))
    with path.open("ab") as handle:
        handle.write(_v1_block("Nuvola v1", "Altro", "Concerto Finto", "1980", 1, 17))
    tags, _length, kinds = read_all_tags(path)
    assert (tags.title, tags.artist, tags.track_number, tags.track_total) == ("Nuvola", "Cantante Finto", 1, 12)
    assert (tags.album, tags.year, tags.genre) == ("Concerto Finto", "1980", "Rock")   # dal tag ID3v1
    assert kinds == ["APEv2", "ID3v1"]


def test_id3v2_wins_and_empty_fields_come_from_the_others(tmp_path):
    path = tmp_path / "misto.mp3"
    write_mp3(path)
    write_tags(path, TrackTags(title="Titolo v2", artist="Artista v2"))
    ape = APEv2()
    ape["Title"] = "Titolo APE"
    ape["Album"] = "Album APE"
    ape.save(str(path))
    tags = read_tags(path)[0]
    assert (tags.title, tags.artist, tags.album) == ("Titolo v2", "Artista v2", "Album APE")
    assert tag_kinds(path)[0].startswith("ID3v2") and "APEv2" in tag_kinds(path)


def _wav(path, info: dict, with_id3: bool = False) -> None:
    fmt = struct.pack("<HHIIHH", 1, 1, 8000, 16000, 2, 16)
    data = b"\x00\x00" * 800
    entries = b""
    for key, value in info.items():
        raw = value.encode("utf-8") + b"\x00"
        if len(raw) % 2:
            raw += b"\x00"
        entries += key + struct.pack("<I", len(raw)) + raw
    chunks = (b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(data)) + data
              + b"LIST" + struct.pack("<I", 4 + len(entries)) + b"INFO" + entries)
    path.write_bytes(b"RIFF" + struct.pack("<I", 4 + len(chunks)) + b"WAVE" + chunks)
    if with_id3:
        from mutagen.wave import WAVE
        audio = WAVE(str(path))
        audio.add_tags()
        audio.tags.add(TIT2(encoding=3, text=["Titolo ID3"]))
        audio.save()


def test_wav_riff_info_and_id3(tmp_path):
    path = tmp_path / "a.wav"
    _wav(path, {b"INAM": "Titolo INFO", b"IART": "Artista INFO", b"IPRD": "Album INFO", b"ICRD": "2001",
                b"ITRK": "4"})
    tags, length, kinds = read_all_tags(path)
    assert (tags.title, tags.artist, tags.album, tags.year, tags.track_number) == \
        ("Titolo INFO", "Artista INFO", "Album INFO", "2001", 4)
    assert kinds == ["RIFF INFO"] and length > 0
    both = tmp_path / "b.wav"
    _wav(both, {b"INAM": "Titolo INFO", b"IART": "Artista INFO"}, with_id3=True)
    tags, _length, kinds = read_all_tags(both)
    assert (tags.title, tags.artist) == ("Titolo ID3", "Artista INFO")
    assert kinds[0].startswith("ID3v2") and kinds[1] == "RIFF INFO"


def test_read_only_formats_are_never_written(tmp_path):
    path = tmp_path / "a.wav"
    _wav(path, {b"INAM": "X"})
    with pytest.raises(TagError):
        write_tags(path, TrackTags(title="Y"), new_copy=True)


def test_old_cache_entries_of_mp3_with_empty_fields_are_read_again(tmp_path):
    from myeasymp3toiphone.config import write_json
    home = tmp_path / "dati"
    home.mkdir()
    full = {"title": "T", "artist": "A", "album": "B", "year": "1999", "genre": "Pop", "track_number": 1}
    write_json(home / tag_cache.CACHE_FILE, {"version": 2, "files": {
        "c:/m/vuoto.mp3": {"s": 1, "m": 1.0, "t": {"title": ""}, "l": 1.0, "e": ""},
        "c:/m/pieno.mp3": {"s": 1, "m": 1.0, "t": full, "l": 1.0, "e": ""},
        "c:/m/vuoto.flac": {"s": 1, "m": 1.0, "t": {"title": ""}, "l": 1.0, "e": ""},
    }})
    cache = tag_cache.TagCache(home)
    assert len(cache) == 2 and "c:/m/vuoto.mp3" not in cache._entries
    assert ID3 is not None


def test_audio_format(tmp_path):
    from conftest import write_flac
    from myeasymp3toiphone.tags import audio_format
    write_mp3(tmp_path / "uno.mp3")
    write_flac(tmp_path / "due.flac")
    (tmp_path / "rotto.wav").write_bytes(b"non audio")
    assert audio_format(tmp_path / "uno.mp3") == "MP3 · 128 kbit/s"
    assert audio_format(tmp_path / "due.flac") == "FLAC · senza perdita"
    assert audio_format(tmp_path / "rotto.wav") == ""             # non si legge: niente
    assert audio_format(tmp_path / "manca.mp3") == ""
