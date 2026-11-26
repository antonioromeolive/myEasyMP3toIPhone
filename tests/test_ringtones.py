# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le suonerie: i .m4r sul PC (ffmpeg solo se c'è: altrimenti quei test si saltano), le operazioni e una sessione
Ringtone con un iPhone simulato, il catalogo dell'host, l'elenco dell'iPhone, la coda e Applica. Valori inventati."""

import array
import asyncio
import plistlib
from datetime import datetime
from pathlib import Path

import pytest

from conftest import write_mp3
from myeasymp3toiphone import phone_ringtones as pr, phone_sync as ps, ringtones
from myeasymp3toiphone.config import AppSettings
from myeasymp3toiphone.pending import RING_DELETE, RING_SEND, SEND, Job, Pending
from test_phone_sync import FIXTURES, FakeAfc, _prefs

FFMPEG = ringtones.find_ffmpeg()
needs_ffmpeg = pytest.mark.skipif(FFMPEG is None, reason="ffmpeg non installato")


# --------------------------------------------------------------------------- PC

def test_peaks_and_selection():
    samples = array.array("h", [0, 16384, -32768, 100] * 10)
    peaks = ringtones.peaks_from_pcm(samples.tobytes(), 4)
    assert len(peaks) == 4 and max(peaks) == 1.0 and min(peaks) >= 0.5
    assert ringtones.peaks_from_pcm(b"", 10) == []
    assert ringtones.clamp_selection(10, 80, 200) == (10, 10 + ringtones.MAX_SECONDS)   # al massimo ~40 s
    assert ringtones.clamp_selection(-5, 3, 200) == (0, 3)
    assert ringtones.clamp_selection(190, 230, 200) == (190, 200)                       # dentro il brano


def test_ffmpeg_commands(tmp_path):
    ffmpeg = Path("ffmpeg.exe")
    command = ringtones.ringtone_command(ffmpeg, Path("brano.mp3"), Path("s.m4r"), 12.5, 40.5, 0.5, 2.0, "Prova")
    assert "-n" in command                                       # mai sopra un file che c'è
    assert command[command.index("-ss") + 1] == "12.500" and command[command.index("-t") + 1] == "28.000"
    assert command[command.index("-af") + 1] == "afade=t=in:st=0:d=0.50,afade=t=out:st=26.00:d=2.00"
    assert command[command.index("-f") + 1] == "ipod" and "title=Prova" in command
    plain = ringtones.preview_command(ffmpeg, Path("brano.mp3"), Path("p.wav"), 0, 10, 0, 0)
    assert "-af" not in plain and plain[-1] == "p.wav"


def test_find_ffmpeg(tmp_path, monkeypatch):
    exe = tmp_path / "bin" / "ffmpeg.exe"
    exe.parent.mkdir()
    exe.write_bytes(b"")
    assert ringtones.find_ffmpeg(str(exe)) == exe
    assert ringtones.find_ffmpeg(str(exe.parent)) == exe        # anche la cartella
    assert ringtones.find_ffmpeg(str(tmp_path / "manca.exe")) is None
    monkeypatch.setattr(ringtones.shutil, "which", lambda name: None)
    assert ringtones.find_ffmpeg("") is None


def test_unique_target_rename_and_trash_rules(tmp_path):
    folder = tmp_path / "Suonerie"
    folder.mkdir()
    (folder / "Prova.m4r").write_bytes(b"x")
    assert ringtones.unique_target(folder, "Prova") == folder / "Prova (2).m4r"
    assert ringtones.unique_target(folder, "a/b:c") == folder / "a_b_c.m4r"
    renamed = ringtones.rename_ringtone(folder / "Prova.m4r", folder, "Nuova")
    assert renamed == folder / "Nuova.m4r" and renamed.exists()
    (folder / "Altra.m4r").write_bytes(b"y")
    with pytest.raises(ringtones.RingtoneError):
        ringtones.rename_ringtone(folder / "Altra.m4r", folder, "Nuova")      # c'è già
    other = tmp_path / "Musica" / "brano.m4r"
    other.parent.mkdir()
    other.write_bytes(b"z")
    with pytest.raises(ringtones.RingtoneError):
        ringtones.rename_ringtone(other, folder, "x")                         # fuori dalla cartella delle suonerie
    assert ringtones.in_folder(folder / "Altra.m4r", folder) and not ringtones.in_folder(other, folder)
    broken = ringtones.read_ringtone(folder / "Altra.m4r")
    assert broken.name == "Altra" and broken.error


def test_same_ringtone_and_settings(tmp_path, monkeypatch):
    assert ringtones.same_ringtone("Money", 30000, "money ", 30400)
    assert not ringtones.same_ringtone("Money", 30000, "Money", 26000)
    assert ringtones.same_ringtone("Money", 30000, "Money", 0)               # durata sconosciuta
    monkeypatch.setenv("CARTELLA_PROVA", str(tmp_path))
    settings = AppSettings(ringtone_folder="$CARTELLA_PROVA/Suonerie")
    assert settings.ringtone_path() == tmp_path / "Suonerie"
    assert AppSettings().ringtone_path() is None


@needs_ffmpeg
def test_create_ringtone_with_ffmpeg(tmp_path):
    source = tmp_path / "brano.m4a"
    ringtones._run_ffmpeg([str(FFMPEG), "-v", "error", "-nostdin", "-f", "lavfi", "-i", "sine=frequency=440:duration=60",
                           "-c:a", "aac", str(source)])
    total, peaks = ringtones.waveform(FFMPEG, source, 100)
    assert 59 < total < 61 and len(peaks) == 100 and max(peaks) > 0.1
    folder = tmp_path / "Suonerie"
    made = ringtones.create_ringtone(FFMPEG, source, folder, 5, 25, 0.5, 2, "La mia suoneria")
    assert made == folder / "La mia suoneria.m4r"
    facts = ringtones.read_ringtone(made)
    assert facts.name == "La mia suoneria" and 19500 < facts.duration_ms < 20500 and not facts.error
    second = ringtones.create_ringtone(FFMPEG, source, folder, 0, 10, 0, 0, "La mia suoneria")
    assert second.name == "La mia suoneria (2).m4r"                         # il primo file non si tocca
    assert [item.name for item in ringtones.list_folder(folder)] == ["La mia suoneria", "La mia suoneria"]
    with pytest.raises(ringtones.RingtoneError):
        ringtones.create_ringtone(FFMPEG, source, folder, 0, 45, 0, 0, "Troppo lunga")
    preview = ringtones.make_preview(FFMPEG, source, 1, 3, 0, 0)
    assert preview.stat().st_size > 1000
    preview.unlink()


# --------------------------------------------------------------------------- operazioni e sessione

def test_ringtone_operations():
    insert = ps.insert_ringtone(7, "  Money ", 30000, "0123456789ABCDEF")
    assert insert == {"operation": "insert_track", "pid": 7,
                      "item": {"title": "Money", "sort_name": "Money", "is_ringtone": True, "total_time_ms": 30000},
                      "ringtone_info": {"guid": "0123456789ABCDEF"}}
    for pid, ms, guid in ((0, 1000, "0123456789ABCDEF"), (7, 41000, "0123456789ABCDEF"), (7, 1000, "xyz")):
        with pytest.raises(ps.PhoneSyncError):
            ps.insert_ringtone(pid, "X", ms, guid)
    delete = ps.delete_ringtone(7, "/iTunes_Control/Ringtones/ABCD.m4r")
    assert delete["device_path"] == delete["path"] == "/iTunes_Control/Ringtones/ABCD.m4r"
    with pytest.raises(ps.PhoneSyncError):
        ps.delete_ringtone(7, "/Purchases/import_1.m4r")          # fatta sull'iPhone: non si toglie
    request = ps.requesting_ringtone_sync(ps.parse_prefs(_prefs()), "PC", 3)
    assert request["Params"]["Dataclasses"] == ["Ringtone", "Keybag"]
    assert request["Params"]["DataclassAnchors"] == {"Ringtone": "3"}       # niente Media
    finished = ps.finished_ringtone_metadata(4)["Params"]
    assert finished == {"DataclassAnchors": {"Ringtone": "4"}, "SyncTypes": {"Ringtone": 1, "Keybag": 1}}
    assert len(pr.new_guid()) == 16


class RingAfc(FakeAfc):
    async def rm(self, path):
        self.log.append(("toglie", path))
        del self.files[path]


class RingPhone:
    """Il servizio com.apple.atc di un iPhone per una sessione Ringtone (come quella vera del 26/11/2026)."""

    def __init__(self, afc, reply, anchor="2"):
        self.afc = afc
        self.reply = reply
        self.anchor = anchor
        self.sent = []
        self.queue = []

    async def send_plist(self, message, endianity, fmt):
        self.sent.append(message)
        command = message["Command"]
        if command == "Ping":
            self.queue += [{"Command": "Pong"},
                           {"Command": "Capabilities", "Params": {"GrappaSupportInfo": {
                               "version": 1, "deviceType": 0, "protocolVersion": 1}}},
                           {"Command": "AssetMetrics", "Params": {"Ringtone": {"_Count": 2}}},
                           {"Command": "SyncAllowed", "Params": {"ManualSync": True, "DataProtected": False,
                                                                 "EducationModeEnabled": False,
                                                                 "DisabledAssetTypes": []}}]
        elif command == "RequestingSync":
            self.queue += [{"Command": "ReadyForSync", "Session": 2, "Params": {
                "DataclassAnchors": {"Ringtone": self.anchor}, "DeviceInfo": {"Grappa": self.reply}}}]
        elif command == "FinishedSyncingMetadata":
            operations = plistlib.loads(self.afc.files[ps.RINGTONE_OPERATIONS_PATH])["operations"]
            manifest = []
            for operation in operations:
                if operation["operation"] == "insert_track":
                    manifest.append({"AssetID": str(operation["pid"]), "AssetType": "Unknown", "IsDownload": True})
                else:
                    name = operation["path"].lstrip("/")
                    self.afc.files.pop(name, None)            # l'iPhone toglie il file subito
            if manifest:
                self.queue.append({"Command": "AssetManifest", "Params": {"AssetManifest": {"Ringtone": manifest}}})
            else:
                self.queue.append({"Command": "SyncFinished"})
        elif command == "FileComplete":
            params = message["Params"]
            self.afc.files[params["AssetPath"]] = self.afc.files.pop(ps.RINGTONE_AIRLOCK + "/" + params["AssetID"])
            self.queue.append({"Command": "SyncFinished"})

    async def recv_plist(self, endianity):
        return self.queue.pop(0)

    async def close(self):
        pass


class RingLockdown:
    def __init__(self, phone):
        self.phone = phone

    async def start_lockdown_service(self, name):
        assert name == ps.ATC_SERVICE
        return self.phone

    async def close(self):
        pass


def _reply():
    result = plistlib.loads((FIXTURES / "grappa-fixed-vectors.plist").read_bytes())[0]["reply"]
    return result


def _ring_files(anchor="2"):
    files = {ps.RINGTONE_ANCHOR_PATH: plistlib.dumps({"syncAnchor": anchor}),
             ps.RINGTONE_SYNC + "/Sync_00000000.plist": plistlib.dumps({"revision": 2, "operations": []}),
             ps.RINGTONE_SYNC + "/Sync_00000000.plist.cig2": b"vecchia firma",
             ps.PREFS_PATH: _prefs()}
    return files


def test_ringtone_session_sends_and_cleans_old_files(tmp_path, monkeypatch):
    import pymobiledevice3.services.afc as afc_module
    afc = RingAfc(_ring_files())
    phone = RingPhone(afc, _reply())
    monkeypatch.setattr(afc_module, "AfcService", lambda _lockdown: afc)
    audio = tmp_path / "s.m4r"
    audio.write_bytes(b"audio della suoneria")
    operation = ps.insert_ringtone(101, "Prova", 8000, "0123456789ABCDEF")
    upload = ps.Upload(101, audio, ps.RINGTONE_FOLDER + "/ABCD.m4r")
    report = asyncio.run(ps.run_ringtone_session(RingLockdown(phone), ps.parse_prefs(_prefs()), "PC", [operation],
                                                 [upload], datetime(2026, 11, 26, 12, 0, 0)))
    assert (report.anchor_before, report.anchor_after, report.uploaded) == (2, 3, ["101"])
    assert ("toglie", ps.RINGTONE_SYNC + "/Sync_00000000.plist.cig2") in afc.log   # i resti già applicati
    staged = plistlib.loads(afc.files[ps.RINGTONE_OPERATIONS_PATH])
    assert staged["revision"] == 3 and staged["operations"] == [operation]       # niente update_db_info
    assert afc.files[ps.RINGTONE_SIGNATURE_PATH] == ps.Signer(_reply()).sign(afc.files[ps.RINGTONE_OPERATIONS_PATH])
    assert afc.files[ps.RINGTONE_FOLDER + "/ABCD.m4r"] == b"audio della suoneria"
    commands = [m["Command"] for m in phone.sent]
    assert commands == ["Ping", "RequestingSync", "FinishedSyncingMetadata", "FileComplete"]
    assert phone.sent[3]["Params"]["Dataclass"] == "Ringtone"
    assert not any(name.startswith(ps.SYNC_MEDIA) for name in afc.files)         # la musica non si tocca


def test_ringtone_session_refuses_unfinished_sync_and_other_anchor(monkeypatch):
    import pymobiledevice3.services.afc as afc_module
    files = _ring_files()
    files[ps.RINGTONE_SYNC + "/Sync_00000000.plist"] = plistlib.dumps({"revision": 5, "operations": []})
    afc = RingAfc(files)
    phone = RingPhone(afc, _reply())
    monkeypatch.setattr(afc_module, "AfcService", lambda _lockdown: afc)
    delete = ps.delete_ringtone(9, "/iTunes_Control/Ringtones/ABCD.m4r")
    with pytest.raises(ps.PhoneSyncError):
        asyncio.run(ps.run_ringtone_session(RingLockdown(phone), ps.parse_prefs(_prefs()), "PC", [delete], [],
                                            datetime(2026, 11, 26)))
    assert phone.sent == [] and afc.log == []
    afc = RingAfc(_ring_files())
    phone = RingPhone(afc, _reply(), anchor="7")
    monkeypatch.setattr(afc_module, "AfcService", lambda _lockdown: afc)
    with pytest.raises(ps.PhoneSyncError):
        asyncio.run(ps.run_ringtone_session(RingLockdown(phone), ps.parse_prefs(_prefs()), "PC", [delete], [],
                                            datetime(2026, 11, 26)))
    assert "FinishedSyncingMetadata" not in [m["Command"] for m in phone.sent]
    assert ps.RINGTONE_OPERATIONS_PATH not in afc.files


# --------------------------------------------------------------------------- l'iPhone: elenco e Applica

def test_catalog_round_trip():
    data = pr.catalog_bytes({"ABCD.m4r": ("Money", 12, "0123456789ABCDEF", 30000)})
    assert b"<?xml" in data
    assert pr.parse_catalog(data) == {"ABCD.m4r": ("Money", 12, "0123456789ABCDEF", 30000)}
    assert pr.parse_catalog(b"rovinato") == {}


def test_list_on_phone_three_kinds():
    files = {pr.CATALOG_PATH: pr.catalog_bytes({"ABCD.m4r": ("Mia", 12, "0123456789ABCDEF", 8000),
                                                "SPAR.m4r": ("Sparita", 13, "0123456789ABCDE0", 1000)}),
             ps.RINGTONE_FOLDER + "/ABCD.m4r": b"a",
             ps.RINGTONE_FOLDER + "/LXGU.m4r": b"resto",
             pr.PURCHASES_CATALOG_PATH: plistlib.dumps({"Ringtones": {"import_1.m4r": {"Name": "Money",
                                                                                          "GUID": "G"}}}),
             pr.PURCHASES_FOLDER + "/import_1.m4r": b"b"}
    items = asyncio.run(pr.list_on_phone(FakeAfc(files)))
    kinds = [(item.name, item.origin, item.removable) for item in items]
    assert kinds == [("Mia", pr.ORIGIN_COMPUTER, True), ("Money", pr.ORIGIN_PHONE, False),
                     ("LXGU", pr.ORIGIN_LEFTOVER, False)]                     # la sparita (senza file) no
    assert items[0].path == "/iTunes_Control/Ringtones/ABCD.m4r" and items[0].pid == 12


def test_apply_batch_updates_the_host_catalog(tmp_path, monkeypatch):
    import pymobiledevice3.services.afc as afc_module
    files = _ring_files()
    files[pr.CATALOG_PATH] = pr.catalog_bytes({"OLDX.m4r": ("Vecchia", 55, "0123456789ABCDEF", 9000)})
    files[ps.RINGTONE_FOLDER + "/OLDX.m4r"] = b"vecchia"
    afc = RingAfc(files)
    phone = RingPhone(afc, _reply())
    monkeypatch.setattr(afc_module, "AfcService", lambda _lockdown: afc)
    audio = tmp_path / "Nuova.m4r"
    audio.write_bytes(b"nuova")
    report = pr.ActionReport()
    sends = [pr.RingtoneSend("suoneria:x", audio, "Nuova", 8000)]
    old = pr.PhoneRingtone("Vecchia", "/iTunes_Control/Ringtones/OLDX.m4r", pr.ORIGIN_COMPUTER, 55)
    deletes = [pr.RingtoneDelete("suoneria_iphone:oldx.m4r", old)]
    asyncio.run(pr._apply_batch(RingLockdown(phone), ps.parse_prefs(_prefs()), sends, deletes, report))
    assert sorted(report.done_keys) == ["suoneria:x", "suoneria_iphone:oldx.m4r"] and not report.errors
    catalog = pr.parse_catalog(afc.files[pr.CATALOG_PATH])
    assert list(catalog.values())[0][0] == "Nuova" and "OLDX.m4r" not in catalog
    operations = plistlib.loads(afc.files[ps.RINGTONE_OPERATIONS_PATH])["operations"]
    assert [operation["operation"] for operation in operations] == ["delete_track", "insert_track"]


# --------------------------------------------------------------------------- coda e Applica

def test_pending_ringtones_round_trip(tmp_path):
    pending = Pending(tmp_path)
    m4r = tmp_path / "Prova.m4r"
    m4r.write_bytes(b"x")
    pending.set_ringtone(m4r, RING_SEND)
    ringtone = pr.PhoneRingtone("Vecchia", "/iTunes_Control/Ringtones/OLDX.m4r", pr.ORIGIN_COMPUTER, 55)
    pending.set_phone_ringtone(ringtone, RING_DELETE)
    pending.save()
    again = Pending(tmp_path)
    assert again.ringtone_action(m4r) == RING_SEND and again.phone_ringtone_action("OLDX.m4r") == RING_DELETE
    assert again.counts()[RING_SEND] == 1 and again.total() == 2
    # già sull'iPhone; e la suoneria da togliere che sull'iPhone non c'è più
    assert again.reconcile_ringtones(lambda path: True, []) == 2 and again.total() == 0
    again.set_ringtone(m4r, RING_SEND)
    m4r.unlink()
    assert again.reconcile_ringtones(lambda path: False) == 1          # il file non c'è più


def test_apply_dialog_texts_and_done_jobs():
    pytest.importorskip("PySide6")
    from myeasymp3toiphone.gui.apply_dialog import describe, summary
    from myeasymp3toiphone.gui.iphone_panel import done_jobs
    from myeasymp3toiphone.phone_actions import ActionReport
    pc = ringtones.RingtoneFile(Path("C:/Suonerie/Prova.m4r"), "Prova", 28000)
    phone = pr.PhoneRingtone("Vecchia", "/iTunes_Control/Ringtones/OLDX.m4r", pr.ORIGIN_COMPUTER, 55)
    jobs = [Job("suoneria:a", RING_SEND, track=pc), Job("suoneria:b", RING_SEND, track=pc),
            Job("suoneria_iphone:oldx.m4r", RING_DELETE, phone=phone)]
    assert summary(jobs) == ("2 suonerie da inviare da PC a iPhone · 1 suoneria da eliminare "
                             "dall'iPhone")
    assert describe(jobs[0]) == ("♪ Prova", "0:28 · Prova.m4r")
    assert describe(jobs[2]) == ("♪ Vecchia", "OLDX.m4r")
    report = ActionReport(done_keys=["suoneria:b"])
    assert done_jobs(jobs + [Job("file:x", SEND, track=pc)], report) == [jobs[1]]
