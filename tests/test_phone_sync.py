# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La scrittura nell'app Musica dell'iPhone (phone_sync, phone_actions) senza un iPhone: la firma confrontata con i
vettori di rustunes, identità e ancore, le operazioni e una sessione intera con un iPhone simulato. Valori inventati."""

import asyncio
import plistlib
import sqlite3
import struct
import zlib
from datetime import datetime
from pathlib import Path

import pytest

from conftest import write_flac, write_mp3
from myeasymp3toiphone import phone_actions, phone_sync as ps
from myeasymp3toiphone.tags import TrackTags

FIXTURES = Path(__file__).parent / "fixtures"


def test_signer_matches_rustunes_vectors():
    vectors = plistlib.loads((FIXTURES / "grappa-fixed-vectors.plist").read_bytes())
    assert len(vectors) == 4
    for vector in vectors:
        assert vector["request"] == ps.HOST_REQUEST
        assert ps.Signer(vector["reply"]).sign(vector["operation"]) == vector["sidecar"]
    reply = vectors[0]["reply"]
    with pytest.raises(ps.PhoneSyncError):
        ps.Signer(reply[:82])
    with pytest.raises(ps.PhoneSyncError):
        ps.Signer(bytes([0]) + reply[1:])
    with pytest.raises(ps.PhoneSyncError):
        ps.Signer(reply).sign(b"")


def _prefs(catalog=0x1122334455667788, user=0x0102030405060708, configured=1):
    raw = bytearray(1232)
    raw[:4] = b"frpd"
    raw[4:8] = struct.pack("<HH", 1, 25)
    raw[8] = configured
    raw[12:28] = struct.pack("<QQ", catalog, user)
    return bytes(raw)


def test_prefs_identity_raw_and_plist():
    raw = _prefs()
    identity = ps.parse_prefs(raw)
    assert identity.library_id == f"{0x1122334455667788 ^ 0x0102030405060708:016X}"
    assert ps.parse_prefs(plistlib.dumps({"iPodPrefs": raw})) == identity
    assert "1122" not in repr(identity)          # l'identità non va nei registri
    for broken in (raw[:100], _prefs(configured=0), _prefs(catalog=5, user=5), b"niente"):
        with pytest.raises(ps.PhoneSyncError):
            ps.parse_prefs(broken)


def test_cdb_anchors_compressed():
    section = struct.pack("<IIII", 0x6473686d, 0x60, 0x90, 11) + bytes(0x60 - 16) + struct.pack("<IIII", 7, 0, 1, 0)
    section += bytes(0x90 - len(section))
    other = struct.pack("<IIII", 0x6473686d, 16, 16, 3)
    body = zlib.compress(other + section)
    header = bytearray(0xf4)
    header[:4] = b"mhbd"
    struct.pack_into("<IIIII", header, 4, 0xf4, 0xf4 + len(body), 2, 115, 2)
    struct.pack_into("<Q", header, 0x48, 99)
    header[0xa8] = 1
    anchors = ps.parse_cdb_anchors(bytes(header) + body)
    assert (anchors.media, anchors.voice_memo, anchors.database_pid) == (7, 1, 99)


def test_catalog_state(tmp_path):
    database = tmp_path / "MediaLibrary.sqlitedb"
    connection = sqlite3.connect(str(database))
    connection.executescript("CREATE TABLE db_info (db_pid INTEGER, primary_container_pid INTEGER);"
                             "CREATE TABLE _MLDatabaseProperties (key TEXT, value TEXT);"
                             "INSERT INTO db_info VALUES (-5, 77);"
                             "INSERT INTO _MLDatabaseProperties VALUES ('MLSyncClientSyncAnchor', '12');"
                             "PRAGMA user_version = 2410000;")
    connection.commit()
    connection.close()
    state = ps.read_catalog_state(database)
    assert (state.database_pid, state.primary_container_pid, state.media_anchor) == ((1 << 64) - 5, 77, 12)


def test_audio_info_mp3_and_flac(tmp_path):
    write_mp3(tmp_path / "a.mp3", 400)
    mp3 = ps.audio_info(tmp_path / "a.mp3")
    assert (mp3.audio_format, mp3.bit_rate_kbps, mp3.sample_rate, mp3.kind, mp3.extension) == \
        (301, 128, 44100, ps.MPEG_KIND, ".mp3")
    assert mp3.total_time_ms == mp3.samples * 1000 // 44100 > 0
    write_flac(tmp_path / "b.flac")
    flac = ps.audio_info(tmp_path / "b.flac")
    assert (flac.audio_format, flac.samples, flac.channels, flac.extension) == (602, 88200, 2, ".flac")
    with pytest.raises(ps.PhoneSyncError):
        ps.audio_info(tmp_path / "c.ogg")


def test_operations():
    audio = ps.AudioInfo(301, 128, 44100, 2, 441000)
    tags = TrackTags(title="Titolo", artist="Artista", album="Album", album_artist="Vari", genre="Rock",
                     year="1999-05-01", track_number=3, track_total=10, disc_number=1)
    plain = ps.insert_track(11, 22, 33, tags, audio)
    item = plain["item"]
    assert (item["artwork_checksum"], "artwork_cache_id" in item, item["year"], item["track_count"]) == (0, False, 1999,
                                                                                                         10)
    assert item["album_artist"] == "Vari" and plain["location"] == {"kind": ps.MPEG_KIND}
    assert "is_compilation" not in item
    compilation = tags.copy()
    compilation.compilation = True
    assert ps.insert_track(11, 22, 33, compilation, audio)["item"]["is_compilation"] is True
    covered = ps.insert_track(11, 22, 33, tags, audio, 4391, ps.cover_checksum(b"x" * 100, ".mp3"))
    assert (covered["item"]["artwork_cache_id"], covered["item"]["artwork_checksum"]) == (4391, 101)
    assert ps.cover_checksum(b"x" * 100, ".m4a") == 117
    with pytest.raises(ps.PhoneSyncError):
        ps.insert_track(11, 11, 33, tags, audio)                    # identificativi uguali
    big = ps.update_track((1 << 64) - 1, {"title": "Nuovo", "sort_name": "Nuovo", "album_pid": (1 << 63) + 5})
    assert big["pid"] == -1 and big["item"]["album_pid"] == -(1 << 63) + 5   # 64 bit con segno nel plist
    for unsafe in ({"artist": "X"}, {"title": "X", "sort_name": "X"}, {"album": "Y", "sort_album": "Y"},
                   {"title": "X", "album_pid": 5}):
        with pytest.raises(ps.PhoneSyncError):
            ps.update_track(9, unsafe)
    assert ps.delete_track(9) == {"operation": "delete_track", "pid": 9}
    assert ps.is_supported_cover(bytes([0xFF, 0xD8, 0xFF, 0xE0])) and not ps.is_supported_cover(b"GIF89a")


def test_messages_are_delta_with_same_identity():
    identity = ps.parse_prefs(_prefs())
    request = ps.requesting_sync(identity, "PC", 41)
    host = request["Params"]["HostInfo"]
    assert host["LibraryID"] == identity.library_id and host["Grappa"] == ps.HOST_REQUEST
    assert request["Params"]["DataclassAnchors"] == {"Media": "41", "VoiceMemo": "1"}
    finished = ps.finished_syncing_metadata(42)
    assert finished["Params"]["SyncTypes"]["Media"] == 1          # mai un Reset (2)
    with pytest.raises(ps.PhoneSyncError):
        ps.check_sync_allowed({"ManualSync": False, "DataProtected": False, "EducationModeEnabled": False})
    with pytest.raises(ps.PhoneSyncError):
        ps.check_sync_allowed({"ManualSync": True, "DataProtected": False, "EducationModeEnabled": False,
                               "DisabledAssetTypes": ["Music"]})


# --------------------------------------------------------------------------- un iPhone simulato

class FakeAfc:
    def __init__(self, files):
        self.files = dict(files)
        self.log = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def exists(self, path):
        result = path in self.files or any(name.startswith(path + "/") for name in self.files)
        return result

    async def listdir(self, path):
        result = [".", ".."] + [name[len(path) + 1:] for name in self.files if name.startswith(path + "/")]
        return result

    async def makedirs(self, path):
        self.files[path + "/.cartella"] = b""

    async def set_file_contents(self, path, data):
        self.log.append(("scrive", path))
        self.files[path] = bytes(data)

    async def get_file_contents(self, path):
        return self.files[path]

    async def stat(self, path):
        return {"st_size": len(self.files[path])}

    async def rename(self, source, target):
        self.log.append(("rinomina", source, target))
        self.files[target] = self.files.pop(source)


class FakePhone:
    """Il servizio com.apple.atc di un iPhone: risponde come quello vero nelle sessioni registrate."""

    def __init__(self, afc, reply, foreign=True):
        self.afc = afc
        self.reply = reply
        self.foreign = foreign
        self.sent = []
        self.queue = []

    async def send_plist(self, message, endianity, fmt):
        assert endianity == "<" and fmt == plistlib.FMT_BINARY
        self.sent.append(message)
        command = message["Command"]
        if command == "Ping":
            self.queue += [{"Command": "Pong"},
                           {"Command": "Capabilities", "Params": {"GrappaSupportInfo": {
                               "version": 1, "deviceType": 0, "protocolVersion": 1}}},
                           {"Command": "InstalledAssets", "Params": {}},
                           {"Command": "SyncAllowed", "Params": {"ManualSync": True, "DataProtected": False,
                                                                 "EducationModeEnabled": False,
                                                                 "DisabledAssetTypes": []}}]
        elif command == "RequestingSync":
            anchor = message["Params"]["DataclassAnchors"]["Media"]
            self.queue += [{"Command": "Ping", "Session": 2},
                           {"Command": "ReadyForSync", "Session": 2, "Params": {
                               "DataclassAnchors": {"Media": anchor, "Book": "0"}, "DeviceInfo": {"Grappa": self.reply}}}]
        elif command == "FinishedSyncingMetadata":
            assert ps.METADATA_PATH in self.afc.files and ps.SIGNATURE_PATH in self.afc.files
            operations = plistlib.loads(self.afc.files[ps.METADATA_PATH])["operations"]
            manifest = []
            for operation in operations:
                if operation["operation"] == "insert_track":
                    parts = 3 if operation["item"].get("artwork_cache_id") else 1
                    manifest.append({"AssetID": str(operation["pid"]), "AssetType": "Music", "IsDownload": True,
                                     "Variant": {"AssetParts": parts}})
            if self.foreign:
                manifest.append({"AssetID": "4", "AssetType": "Music", "IsDownload": True,
                                 "Variant": {"AssetParts": 2}})
            self.queue += [{"Command": "Progress", "Params": {}}]
            if manifest:
                self.queue.append({"Command": "AssetManifest", "Params": {"AssetManifest": {"Media": manifest}}})
            else:
                self.queue.append({"Command": "SyncFinished"})
        elif command in ("FileComplete", "FileError"):
            answered = [m for m in self.sent if m["Command"] in ("FileComplete", "FileError")]
            pending = [m for m in self.queue if m["Command"] == "AssetManifest"]
            expected = sum(1 for m in self.sent if m["Command"] == "FinishedSyncingMetadata")
            if not pending and len(answered) == self._manifest_size() and expected:
                self.queue.append({"Command": "SyncFinished"})

    def _manifest_size(self):
        operations = plistlib.loads(self.afc.files[ps.METADATA_PATH])["operations"]
        result = sum(1 for o in operations if o["operation"] == "insert_track") + (1 if self.foreign else 0)
        return result

    async def recv_plist(self, endianity):
        return self.queue.pop(0)

    async def close(self):
        pass


class FakeLockdown:
    def __init__(self, phone):
        self.phone = phone

    async def start_lockdown_service(self, name):
        assert name == ps.ATC_SERVICE
        return self.phone


def _session(monkeypatch, afc, phone, operations, uploads):
    import pymobiledevice3.services.afc as afc_module
    monkeypatch.setattr(afc_module, "AfcService", lambda _lockdown: afc)
    identity = ps.parse_prefs(_prefs())
    state = ps.CatalogState(1234, 5678, 41, 2410000)
    result = asyncio.run(ps.run_session(FakeLockdown(phone), identity, state, "PC", operations, uploads,
                                        datetime(2026, 11, 21, 12, 0, 0)))
    return result


def test_session_with_cover_and_foreign_request(tmp_path, monkeypatch):
    reply = plistlib.loads((FIXTURES / "grappa-fixed-vectors.plist").read_bytes())[0]["reply"]
    afc = FakeAfc({ps.SYNC_MEDIA + "/Sync_00000001.plist.cig2": b"vecchio resto"})
    phone = FakePhone(afc, reply)
    audio_file = tmp_path / "a.mp3"
    write_mp3(audio_file, 100)
    cover = bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"immagine"
    operation = ps.insert_track(101, 202, 303, TrackTags(title="T", artist="A", album="B"),
                                ps.audio_info(audio_file), 4391, ps.cover_checksum(cover, ".mp3"))
    upload = ps.Upload(101, audio_file, "iTunes_Control/Music/F01/ABCD.mp3", cover)
    report = _session(monkeypatch, afc, phone, [operation], [upload])
    assert (report.anchor_before, report.anchor_after, report.uploaded) == (41, 42, ["101"])
    assert report.declined == [("4", 2)]                               # la copertina di un altro brano: rifiutata
    staged = plistlib.loads(afc.files[ps.METADATA_PATH])
    assert staged["revision"] == 42 and staged["operations"][0]["operation"] == "update_db_info"
    signer = ps.Signer(reply)
    assert afc.files[ps.SIGNATURE_PATH] == signer.sign(afc.files[ps.METADATA_PATH])
    commands = [m["Command"] for m in phone.sent]
    assert commands == ["Ping", "RequestingSync", "Pong", "FinishedSyncingMetadata", "FileComplete", "FileError"]
    finished = phone.sent[3]
    assert finished["Params"]["DataclassAnchors"]["Media"] == "42"
    writes = [entry for entry in afc.log if entry[0] in ("scrive", "rinomina")]
    assert writes.index(("scrive", ps.AIRLOCK_ARTWORK + "/101")) < writes.index(("scrive", ps.AIRLOCK + "/101.mp3"))
    assert afc.files[ps.AIRLOCK + "/101"] == audio_file.read_bytes()   # rinominato col solo AssetID
    complete = phone.sent[4]["Params"]
    assert complete == {"AssetID": "101", "AssetPath": "iTunes_Control/Music/F01/ABCD.mp3", "Dataclass": "Media"}


def test_session_refuses_pending_sync_and_writes_nothing(monkeypatch):
    afc = FakeAfc({ps.SYNC_MEDIA + "/Sync_00000003.plist": b"di un'altra sessione"})
    phone = FakePhone(afc, b"")
    with pytest.raises(ps.PhoneSyncError):
        _session(monkeypatch, afc, phone, [ps.delete_track(9)], [])
    assert phone.sent == [] and afc.log == []


def test_session_refuses_a_different_anchor(monkeypatch):
    reply = plistlib.loads((FIXTURES / "grappa-fixed-vectors.plist").read_bytes())[0]["reply"]
    afc = FakeAfc({ps.SYNC_MEDIA + "/.cartella": b""})
    phone = FakePhone(afc, reply, foreign=False)
    original = phone.send_plist

    async def other_anchor(message, endianity, fmt):
        await original(message, endianity, fmt)
        for queued in phone.queue:
            if queued["Command"] == "ReadyForSync":
                queued["Params"]["DataclassAnchors"]["Media"] = "40"

    phone.send_plist = other_anchor
    with pytest.raises(ps.PhoneSyncError):
        _session(monkeypatch, afc, phone, [ps.delete_track(9)], [])
    assert "FinishedSyncingMetadata" not in [m["Command"] for m in phone.sent] and afc.log == []


# --------------------------------------------------------------------------- regole di phone_actions

class FakeSnapshot:
    def __init__(self):
        self.albums = {("album esistente", "artista"): (555, "Album Esistente")}
        self.album_ids = {555}

    def new_album_id(self):
        result = max(self.album_ids) + 1
        self.album_ids.add(result)
        return result


def test_tag_edit_rules():
    from myeasymp3toiphone.phone_library import PhoneTrack
    track = PhoneTrack(1, "/x.mp3", 1, 1.0, TrackTags(title="T", artist="Artista", album="Vecchio"), sync_id=9,
                       album_sync_id=77)
    snapshot = FakeSnapshot()
    item = phone_actions._update_item(track, {"album": "album  ESISTENTE"}, snapshot, {})
    assert item == {"album": "Album Esistente", "sort_album": "Album Esistente", "album_pid": 555}  # grafia del telefono
    new_albums = {}
    first = phone_actions._update_item(track, {"album": "Nuovo"}, snapshot, new_albums)
    assert first["album_pid"] == 556
    assert phone_actions._update_item(track, {"album": "Nuovo"}, snapshot, new_albums) is None   # alla sessione dopo
    titled = phone_actions._update_item(track, {"title": "Altro", "year": 0, "track_number": 0}, snapshot, {})
    assert titled == {"title": "Altro", "sort_name": "Altro", "album_pid": 77, "year": 0, "track_number": 0,
                      "track_count": 0}
    with pytest.raises(ps.PhoneSyncError):
        phone_actions._update_item(track, {"genre": " "}, snapshot, {})
    flagged = phone_actions._update_item(track, {"compilation": True}, snapshot, {})
    assert flagged == {"is_compilation": True}                   # solo il brano: niente album_pid
    assert ps.update_track(9, flagged)["item"] == {"is_compilation": True}
    with pytest.raises(ps.PhoneSyncError):
        ps.update_track(9, {"is_compilation": 1})


def test_plan_updates_from_pc():
    from myeasymp3toiphone.library import Track
    from myeasymp3toiphone.phone_library import PhoneTrack

    def phone(sync_id, **values):
        base = dict(title="T", artist="Artista", album="Album", year="1990", genre="Pop", track_number=1)
        base.update(values)
        result = PhoneTrack(sync_id, "/x.mp3", 1, 1.0, TrackTags(**base), sync_id=sync_id, album_sync_id=7)
        return result

    def pc(name, **values):
        base = dict(title="T", artist="Artista", album="Album", year="1990", genre="Pop", track_number=1)
        base.update(values)
        result = Track(path=Path(f"C:/m/{name}.mp3"), tags=TrackTags(**base))
        return result

    pairs = [(phone(1), pc("uguale")),
             (phone(2), pc("titolo", title="Nuovo", year="2001-05-01", track_number=None)),
             (phone(3), pc("artista", artist="Altro", title="Nuovo")),
             (phone(4), pc("copertina")),
             (phone(5), pc("genere", genre="")),
             (phone(0), pc("comprato", title="X"))]
    edits, replacements = phone_actions.plan_updates(pairs, frozenset({str(Path("C:/m/copertina.mp3"))}))
    assert [(item.sync_id, values) for item, values in edits] == [(2, {"title": "Nuovo", "year": 2001,
                                                                       "track_number": 0})]
    assert [item.sync_id for item, _track in replacements] == [3, 4, 5]
