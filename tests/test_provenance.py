# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Impronte dell'audio e registro della provenienza, senza iPhone. Valori inventati."""

import asyncio
import struct

from conftest import write_flac, write_mp3
from myeasymp3toiphone import provenance
from myeasymp3toiphone.provenance import Link, Registry
from myeasymp3toiphone.tags import TrackTags, prepare_copy, write_tags


def _prints(*paths):
    found = provenance.file_fingerprints([str(path) for path in paths])
    result = [found[str(path)] for path in paths]
    return result


def test_mp3_fingerprint_ignores_tags(tmp_path):
    write_mp3(tmp_path / "a.mp3", 200)
    write_mp3(tmp_path / "b.mp3", 200)
    write_tags(tmp_path / "a.mp3", TrackTags(title="Uno", artist="A"))
    prepare_copy(tmp_path / "b.mp3", TrackTags(title="Titolo tutto diverso", artist="B", album_artist="Artisti vari",
                                               album="Raccolta", compilation=True))
    first, second = _prints(tmp_path / "a.mp3", tmp_path / "b.mp3")
    assert first.startswith("mp3:") and first == second           # stesso audio, tag diversi
    data = bytearray((tmp_path / "b.mp3").read_bytes())
    data[-200] ^= 0xFF                                            # un byte dell'audio
    (tmp_path / "c.mp3").write_bytes(bytes(data[:-100]))
    write_mp3(tmp_path / "d.mp3", 199)
    (tmp_path / "d.mp3").write_bytes(b"\xff\xfb\x90\x64" + b"\x01" * 413 + (tmp_path / "d.mp3").read_bytes())
    assert _prints(tmp_path / "d.mp3")[0] != first


def test_flac_fingerprint_uses_streaminfo_md5(tmp_path):
    write_flac(tmp_path / "a.flac")
    assert _prints(tmp_path / "a.flac")[0] == ""                       # niente audio, niente impronta
    with open(tmp_path / "a.flac", "ab") as handle:
        handle.write(b"\xff\xf8" + bytes(range(200)))                  # un po' di "audio" dopo l'intestazione
    assert _prints(tmp_path / "a.flac")[0].startswith("flacpcm:")     # MD5 a zero: si usa l'audio
    data = bytearray((tmp_path / "a.flac").read_bytes())
    data[26:42] = bytes(range(1, 17))                                 # l'MD5 dell'audio decodificato
    (tmp_path / "b.flac").write_bytes(bytes(data))
    assert _prints(tmp_path / "b.flac")[0] == "flac:" + bytes(range(1, 17)).hex()


def test_mp4_fingerprint_finds_mdat(tmp_path):
    def atom(kind, payload):
        return struct.pack(">I4s", 8 + len(payload), kind) + payload
    audio = bytes(range(256)) * 40
    (tmp_path / "a.m4a").write_bytes(atom(b"ftyp", b"M4A \x00\x00\x00\x00") + atom(b"moov", b"x" * 300) +
                                     atom(b"mdat", audio))
    (tmp_path / "b.m4a").write_bytes(atom(b"ftyp", b"M4A \x00\x00\x00\x00") + atom(b"moov", b"tag diversi" * 9) +
                                     atom(b"mdat", audio))
    first, second = _prints(tmp_path / "a.m4a", tmp_path / "b.m4a")
    assert first.startswith("mp4:") and first == second


def test_registry_merge_prune_and_format(tmp_path):
    local = Registry()
    local.record(Link(sync_id=1, pc="PC-UNO", path="C:/m/a.mp3", date="2026-11-20 10:00:00"))
    local.record(Link(sync_id=2, pc="PC-UNO", path="C:/m/b.mp3", date="2026-11-20 10:00:00"))
    phone = Registry()
    phone.record(Link(sync_id=2, pc="PC-DUE", path="D:/x/b.mp3", date="2026-11-21 10:00:00"))   # più recente
    phone.record(Link(sync_id=(1 << 64) - 3, pc="PC-DUE", path="D:/x/c.mp3", how=provenance.HOW_AI))
    assert local.merge(phone)
    assert local.get(2).pc == "PC-DUE" and local.get((1 << 64) - 3).how == provenance.HOW_AI
    assert local.keep_only({2, (1 << 64) - 3}) and local.get(1) is None
    again = Registry.from_bytes(local.to_bytes())
    assert again.to_bytes() == local.to_bytes() and len(again) == 2
    assert len(Registry.from_bytes(b"non json")) == 0
    local.save(tmp_path)
    assert len(Registry.load(tmp_path)) == 2 and len(Registry.load(tmp_path / "nessuna")) == 0


class FakeAfc:
    def __init__(self):
        self.files = {}

    async def exists(self, path):
        return path in self.files or any(name.startswith(path + "/") for name in self.files)

    async def makedirs(self, path):
        self.files[path + "/.cartella"] = b""

    async def get_file_contents(self, path):
        return self.files[path]

    async def set_file_contents(self, path, data):
        self.files[path] = bytes(data)

    async def rm(self, path):
        self.files.pop(path, None)
        return []

    async def rename(self, source, target):
        self.files[target] = self.files.pop(source)


def test_synchronize_with_phone_copy(tmp_path):
    afc = FakeAfc()
    other_pc = Registry()
    other_pc.record(Link(sync_id=7, pc="PC-ALTRO", path="D:/x/a.mp3"))
    other_pc.record(Link(sync_id=8, pc="PC-ALTRO", path="D:/x/sparito.mp3"))
    afc.files[provenance.PHONE_REGISTRY] = other_pc.to_bytes()
    mine = Registry()
    mine.record(Link(sync_id=9, pc=provenance.computer_name(), path="C:/m/b.mp3"))
    mine.save(tmp_path)
    merged = asyncio.run(provenance.synchronize(afc, tmp_path, {7, 9}))       # l'8 non è più sull'iPhone
    assert sorted(merged.links) == [7, 9] and merged.get(9).here and not merged.get(7).here
    assert sorted(Registry.from_bytes(afc.files[provenance.PHONE_REGISTRY]).links) == [7, 9]
    assert sorted(Registry.load(tmp_path).links) == [7, 9]
    assert provenance.PHONE_REGISTRY + ".tmp" not in afc.files
