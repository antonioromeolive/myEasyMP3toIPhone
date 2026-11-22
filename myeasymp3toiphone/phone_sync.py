# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Scrivere nella musica dell'app Musica dell'iPhone con il servizio di sincronizzazione di Apple, AirTrafficControl
(com.apple.atc): lo stesso che usano iTunes, Dispositivi Apple e CopyTrans Manager.

Il protocollo non è documentato da Apple. Questo modulo segue la ricostruzione di rustunes
(https://github.com/fbiba/rustunes, licenza MIT, (c) 2026 Feim Biba): la richiesta "Grappa" fissa da 84 byte, la
firma .cig dei file delle operazioni (AES + HMAC-SHA1), la sequenza dei messaggi e le operazioni insert_track,
update_track e delete_track. Provato da rustunes su iOS 26.7 e 27.0-27.2.1; Apple può cambiarlo a ogni aggiornamento.

Regole di sicurezza, tutte da rustunes:
  * sempre sessioni "Delta" (SyncTypes Media 1): mai un "Reset", che toglie i brani non rimandati;
  * la stessa identità di libreria (LibraryID) già scritta sul telefono (iTunesPrefs), mai una nuova;
  * l'ancora Media letta dal database del telefono deve coincidere con quella di ReadyForSync;
  * FinishedSyncingMetadata si manda solo dopo aver scritto e riletto il file delle operazioni firmato: una sessione
    chiusa prima non cambia niente nel database del telefono.
"""

from __future__ import annotations

import hmac
import io
import plistlib
import sqlite3
import struct
import zlib
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# --------------------------------------------------------------------------- Grappa e firma .cig

HOST_REQUEST = bytes([
    0x01, 0x01, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11,
    0x11, 0x11, 0x04, 0x40, 0xbc, 0x27, 0x85, 0xe0, 0xdb, 0xf1, 0x66, 0x36, 0x1e, 0x07, 0x98, 0x0a,
    0x5e, 0xa4, 0x8d, 0xba, 0x95, 0xb3, 0xb8, 0xea, 0x26, 0x5d, 0x62, 0xae, 0xfe, 0xa5, 0x1b, 0xb7,
    0xb1, 0x90, 0xe0, 0xb7, 0x71, 0x26, 0x29, 0x0a, 0xd3, 0x9b, 0xb1, 0x3f, 0xec, 0xc0, 0x8c, 0x25,
    0xa9, 0x56, 0x1c, 0x51, 0x7a, 0xc1, 0x1e, 0x64, 0x90, 0x5d, 0xa0, 0x29, 0xe6, 0x1b, 0xdf, 0xd0,
    0xba, 0x22, 0xc3, 0x13,
])
_WRAP_KEY = bytes([0x77, 0x76, 0xeb, 0x98, 0xab, 0x6c, 0xe6, 0x02, 0xe8, 0xe8, 0x92, 0xe4, 0x1b, 0xa7, 0xe9, 0x15])
_KEY_XOR = bytes([0xc6, 0xc7, 0xc4, 0xc5, 0xca, 0xcb, 0xc8, 0xc9, 0xce, 0xcf, 0xcc, 0xcd, 0xb2, 0xb3, 0xb0, 0xb1])
_TAG_XOR = bytes([0xf9, 0xfa, 0xfb, 0xfc, 0xfd, 0xfe, 0xff, 0xf0, 0xf1, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6, 0xf7, 0xe8,
                  0xe9, 0xea, 0xeb, 0xec])
MAX_OPERATION_BYTES = 4 * 1024 * 1024
MAX_OPERATIONS = 500            # operazioni in un file, update_db_info compresa (come l'host di Apple)


class PhoneSyncError(Exception):
    """Un controllo non superato o una risposta inattesa dell'iPhone: la sessione si ferma senza mandare altro."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PhoneSyncError(message)


def _aes(key: bytes, mode, data: bytes, decrypt: bool) -> bytes:
    cipher = Cipher(algorithms.AES(key), mode)
    worker = cipher.decryptor() if decrypt else cipher.encryptor()
    result = worker.update(data) + worker.finalize()
    return result


class Signer:
    """La firma dei file delle operazioni di una sessione, ricavata dalla risposta Grappa di ReadyForSync (83 byte).
    Niente __repr__: il materiale della sessione non va nei registri."""

    def __init__(self, reply: bytes) -> None:
        _require(len(reply) == 83, "la risposta Grappa deve essere di 83 byte")
        _require(reply[:2] == b"\x01\x01" and reply[18] == 64, "risposta Grappa di forma sconosciuta")
        decoded = _aes(bytes([0x95] * 16), modes.CBC(reply[2:18]), reply[19:83], decrypt=True)
        key = bytearray(16)
        for index in range(16):
            key[index] = decoded[1 + index] ^ decoded[39 + index] ^ _KEY_XOR[index]
        self._key = _aes(_WRAP_KEY, modes.ECB(), bytes(key), decrypt=False)
        mask = bytearray(20)
        for index in range(20):
            mask[index] = decoded[18 + index] ^ _TAG_XOR[index]
        self._mask = bytes(mask)

    def sign(self, operation: bytes) -> bytes:
        """La firma .cig (21 byte) dei byte esatti del file delle operazioni."""
        _require(0 < len(operation) <= MAX_OPERATION_BYTES, "file delle operazioni vuoto o troppo grande")
        tag = hmac.new(self._key, operation, sha1).digest()
        signature = bytearray([1])
        for index in range(20):
            signature.append(tag[index] ^ self._mask[index])
        result = bytes(signature)
        return result


# --------------------------------------------------------------------------- identità e ancore

PREFS_PATH = "iTunes_Control/iTunes/iTunesPrefs"
PREFS_PLIST_PATH = "iTunes_Control/iTunes/iTunesPrefs.plist"
CDB_PATH = "iTunes_Control/iTunes/iTunesCDB"
_PREFS_BYTES = 1232


@dataclass(frozen=True)
class LibraryIdentity:
    catalog_id: int
    user_id: int

    @property
    def library_id(self) -> str:
        result = f"{self.catalog_id ^ self.user_id:016X}"
        return result

    def __repr__(self) -> str:
        result = "LibraryIdentity(…)"   # non nei registri
        return result


def parse_prefs(data: bytes) -> LibraryIdentity:
    """L'identità della libreria da iTunesPrefs (dati "frpd") o dalla chiave iPodPrefs di iTunesPrefs.plist."""
    raw = data
    if not data.startswith(b"frpd"):
        try:
            document = plistlib.loads(data)
        except Exception as exc:  # noqa: BLE001 - plistlib solleva tipi diversi per un file rovinato
            raise PhoneSyncError("le preferenze dell'iPhone non sono né dati frpd né un plist") from exc
        raw = document.get("iPodPrefs") if isinstance(document, dict) else None
        _require(isinstance(raw, bytes), "il plist delle preferenze non contiene iPodPrefs")
    _require(len(raw) == _PREFS_BYTES and raw[:4] == b"frpd", "preferenze dell'iPhone di formato sconosciuto")
    _require(struct.unpack_from("<HH", raw, 4) == (1, 25), "versione delle preferenze diversa da 1.25")
    _require(raw[8] == 1, "le preferenze dicono che la libreria non è configurata")
    catalog_id, user_id = struct.unpack_from("<QQ", raw, 12)
    _require(catalog_id != 0 and user_id != 0 and catalog_id ^ user_id != 0, "identità della libreria nulla")
    result = LibraryIdentity(catalog_id, user_id)
    return result


@dataclass(frozen=True)
class CdbAnchors:
    media: int
    voice_memo: int
    database_pid: int


def parse_cdb_anchors(data: bytes) -> CdbAnchors:
    """Le ancore salvate da un host nell'iTunesCDB (sezione 11): formato 1.x o 2.x (zlib), versione 115 (iTunes
    12.13 per Windows) o 117 (Dispositivi Apple). Il telefono non legge mai questo file: serve solo da controllo."""
    _require(len(data) >= 0xf4, "iTunesCDB troncato")
    if data[:4] == b"mhbd":
        order = "<"
    elif data[:4] == b"dbhm":
        order = ">"
    else:
        raise PhoneSyncError("iTunesCDB di formato sconosciuto")
    header, total, major, minor, count = struct.unpack_from(order + "IIIII", data, 4)
    _require(header == 0xf4 and total == len(data) and minor in (115, 117) and 1 <= count <= 4096,
             "intestazione di iTunesCDB inattesa")
    sections = data[0xf4:]
    if (major, data[0xa8]) == (2, 1):
        sections = zlib.decompress(sections)
    else:
        _require((major, data[0xa8]) == (1, 0), "versione o compressione di iTunesCDB inattese")
    anchors = None
    offset = 0
    index = 0
    while index < count:
        _require(len(sections) - offset >= 16, "sezione di iTunesCDB troncata")
        magic, head, size, kind = struct.unpack_from(order + "IIII", sections, offset)
        _require(magic == 0x6473686d and 16 <= head <= size <= len(sections) - offset, "sezione di iTunesCDB rovinata")
        if kind == 11:
            _require(anchors is None and head == 0x60 and size == 0x90, "ancore di iTunesCDB di forma inattesa")
            anchors = struct.unpack_from(order + "IIII", sections, offset + head)
        offset += size
        index += 1
    _require(offset == len(sections) and anchors is not None, "ancore assenti in iTunesCDB")
    database_pid = struct.unpack_from(order + "Q", data, 0x48)[0]
    result = CdbAnchors(media=anchors[0], voice_memo=anchors[2], database_pid=database_pid)
    return result


@dataclass(frozen=True)
class CatalogState:
    """Quello che serve a una sessione, dal database dell'app Musica (una copia appena scaricata)."""
    database_pid: int
    primary_container_pid: int
    media_anchor: int
    user_version: int


def read_catalog_state(database: Path) -> CatalogState:
    connection = sqlite3.connect(str(database))
    try:
        rows = connection.execute("SELECT db_pid, primary_container_pid FROM db_info").fetchall()
        anchor_rows = connection.execute(
            "SELECT value FROM _MLDatabaseProperties WHERE key='MLSyncClientSyncAnchor'").fetchall()
        user_version = connection.execute("PRAGMA user_version").fetchone()[0]
    except sqlite3.Error as exc:
        raise PhoneSyncError(f"il database dell'app Musica non ha la forma attesa ({exc})") from exc
    finally:
        connection.close()
    _require(len(rows) == 1, "il database dell'app Musica non ha esattamente una riga db_info")
    _require(len(anchor_rows) == 1, "il database dell'app Musica non ha l'ancora di sincronizzazione")
    database_pid, container_pid = rows[0]
    _require(database_pid != 0 and container_pid != 0, "identità del database dell'app Musica nulla")
    try:
        anchor = int(str(anchor_rows[0][0]))
    except ValueError as exc:
        raise PhoneSyncError("ancora di sincronizzazione non numerica") from exc
    result = CatalogState(int(database_pid) & 0xFFFFFFFFFFFFFFFF, int(container_pid) & 0xFFFFFFFFFFFFFFFF,
                          anchor, int(user_version))
    return result


# --------------------------------------------------------------------------- messaggi

ATC_SERVICE = "com.apple.atc"
HOST_VERSION = "13.2.4.123"     # quella che rustunes annuncia: le versioni troppo vecchie sono rifiutate
VOICE_MEMO_ANCHOR = 1


def requesting_sync(identity: LibraryIdentity, host_name: str, media_anchor: int) -> dict:
    anchors = {"Media": str(media_anchor), "VoiceMemo": str(VOICE_MEMO_ANCHOR)}
    host = {"Grappa": HOST_REQUEST, "Version": HOST_VERSION, "LibraryID": identity.library_id,
            "SyncHostName": host_name, "SyncedDataclasses": ["Media"], "WindowsOSVersion": "10.0",
            "Type": "iTunes", "Wakeable": 0, "SyncedAssetTypes": ["Music"]}
    result = {"Session": 2, "Command": "RequestingSync",
              "Params": {"HostInfo": host, "DataclassAnchors": anchors, "Dataclasses": ["Media", "Book", "Keybag"]}}
    return result


def finished_syncing_metadata(new_anchor: int) -> dict:
    """La fine dei metadati di una sessione Delta (Media 1): mai un Reset (Media 2)."""
    anchors = {"Media": str(new_anchor), "VoiceMemo": str(VOICE_MEMO_ANCHOR)}
    result = {"Session": 2, "Command": "FinishedSyncingMetadata",
              "Params": {"DataclassAnchors": anchors, "SyncTypes": {"Media": 1, "Book": 0, "Keybag": 1}}}
    return result


def check_sync_allowed(params: dict) -> None:
    """La musica deve poter arrivare da un computer, a mano (ManualSync) e con il telefono non protetto."""
    _require(isinstance(params, dict), "SyncAllowed senza parametri")
    _require(params.get("ManualSync") is True,
             "l'iPhone non accetta la gestione manuale della musica (in iTunes: Gestisci manualmente musica)")
    _require(params.get("DataProtected") is False, "l'iPhone è bloccato: sbloccalo e riprova")
    _require(params.get("EducationModeEnabled") is False, "iPhone in modalità educativa")
    disabled = params.get("DisabledAssetTypes") or []
    _require("Music" not in disabled,
             "l'iPhone non accetta musica da un computer (probabilmente è attivo Sincronizza libreria di Apple Music)")


# --------------------------------------------------------------------------- sessione

class AtcSession:
    """Una connessione al servizio com.apple.atc. Da usare dentro un'unica operazione asincrona."""

    def __init__(self, service) -> None:
        self._service = service
        self.received = []      # i comandi ricevuti, per il registro (senza dati della sessione)
        self.sync_allowed = {}

    async def send(self, message: dict) -> None:
        await self._service.send_plist(message, endianity="<", fmt=plistlib.FMT_BINARY)

    async def receive(self) -> dict:
        """Il prossimo messaggio; un Ping riceve subito il suo Pong."""
        message = None
        while message is None:
            value = await self._service.recv_plist(endianity="<")
            _require(isinstance(value, dict) and isinstance(value.get("Command"), str), "messaggio ATC senza comando")
            self.received.append(value["Command"])
            if value["Command"] == "Ping":
                await self.send({"Session": value.get("Session", 1), "Command": "Pong"})
            else:
                message = value
        return message

    async def handshake(self) -> dict:
        """Ping, poi aspetta Pong, Capabilities e SyncAllowed. Restituisce i parametri di SyncAllowed."""
        await self.send({"Session": 1, "Command": "Ping"})
        pong = capable = allowed = False
        frames = 0
        while not (pong and capable and allowed) and frames < 64:
            message = await self.receive()
            frames += 1
            command = message["Command"]
            if command == "Pong":
                pong = True
            elif command == "Capabilities":
                info = (message.get("Params") or {}).get("GrappaSupportInfo") or {}
                _require(info.get("version") == 1 and info.get("deviceType") == 0 and
                         info.get("protocolVersion") == 1, "capacità Grappa dell'iPhone diverse da quelle note")
                capable = True
            elif command == "SyncAllowed":
                self.sync_allowed = dict(message.get("Params") or {})
                allowed = True
            elif command in ("InstalledAssets", "AssetMetrics"):
                pass
            else:
                raise PhoneSyncError(f"messaggio inatteso nella presentazione: {command}")
        _require(pong and capable and allowed, "presentazione con l'iPhone incompleta")
        result = self.sync_allowed
        return result

    async def request_sync(self, identity: LibraryIdentity, host_name: str, media_anchor: int) -> Signer:
        """RequestingSync e attesa di ReadyForSync, che deve riportare la stessa ancora Media."""
        check_sync_allowed(self.sync_allowed)
        await self.send(requesting_sync(identity, host_name, media_anchor))
        signer = None
        frames = 0
        while signer is None and frames < 64:
            message = await self.receive()
            frames += 1
            command = message["Command"]
            if command == "ReadyForSync":
                params = message.get("Params") or {}
                anchors = params.get("DataclassAnchors") or {}
                _require(str(anchors.get("Media")) == str(media_anchor),
                         f"l'iPhone ha un'ancora diversa da quella del suo database ({anchors.get('Media')} invece di "
                         f"{media_anchor}): rileggi la musica dell'iPhone e riprova")
                reply = (params.get("DeviceInfo") or {}).get("Grappa")
                _require(isinstance(reply, bytes), "ReadyForSync senza Grappa")
                signer = Signer(reply)
            elif command in ("SyncAllowed", "InstalledAssets", "AssetMetrics", "Progress"):
                pass
            elif command == "SyncFailed":
                raise PhoneSyncError(f"l'iPhone ha rifiutato la sincronizzazione (codice "
                                     f"{(message.get('Params') or {}).get('ErrorCode')})")
            else:
                raise PhoneSyncError(f"messaggio inatteso invece di ReadyForSync: {command}")
        _require(signer is not None, "l'iPhone non ha risposto ReadyForSync")
        return signer


def operation_file(revision: int, timestamp, operations: list) -> bytes:
    """Il file delle operazioni (plist binario) con la revisione che l'iPhone assegnerà (ancora + 1)."""
    _require(0 < len(operations) <= MAX_OPERATIONS, "numero di operazioni fuori dai limiti")
    buffer = io.BytesIO()
    plistlib.dump({"revision": revision, "timestamp": timestamp, "operations": operations}, buffer,
                  fmt=plistlib.FMT_BINARY, sort_keys=True)
    result = buffer.getvalue()
    return result


def update_db_info(state: CatalogState) -> dict:
    result = {"operation": "update_db_info", "pid": _signed(state.database_pid),
              "db_info": {"primary_container_pid": _signed(state.primary_container_pid)}}
    return result


def _signed(value: int) -> int:
    """Gli identificativi a 64 bit vanno nel plist come interi con segno."""
    result = value - (1 << 64) if value >= (1 << 63) else value
    return result


# --------------------------------------------------------------------------- operazioni

MPEG_FORMATS = {1: 301, 2: 302, 2.5: 303}        # versione MPEG -> audio_format (Layer III)
MPEG_CBR_KBPS = {1: (32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320),
                 2: (8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160),
                 2.5: (8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160)}
MPEG_RATES = {1: (32000, 44100, 48000), 2: (16000, 22050, 24000), 2.5: (8000, 11025, 12000)}


MPEG_KIND = "MPEG audio file"
FLAC_KIND = "FLAC audio file"       # l'iPhone non conosce questa descrizione (la tiene come 0) ma suona il file
AAC_KIND = "AAC audio file"
AAC_FORMATS = {2: 502, 5: 508, 29: 509}     # profilo AAC (mutagen: mp4a.40.N) -> audio_format


@dataclass(frozen=True)
class AudioInfo:
    audio_format: int
    bit_rate_kbps: int
    sample_rate: int
    channels: int
    samples: int
    kind: str = MPEG_KIND
    extension: str = ".mp3"     # quella del file sull'iPhone: deve corrispondere al formato

    @property
    def total_time_ms(self) -> int:
        result = self.samples * 1000 // self.sample_rate
        return result


def mp3_info(path: Path) -> AudioInfo:
    """Formato e durata di un MP3 (MPEG 1, 2 o 2.5, Layer III), come li vuole insert_track."""
    from mutagen.mp3 import MP3, BitrateMode
    try:
        info = MP3(str(path)).info
    except Exception as exc:  # noqa: BLE001 - mutagen solleva tipi diversi per un file rovinato
        raise PhoneSyncError(f"{path.name}: non è un MP3 leggibile ({exc})") from exc
    version = info.version
    _require(info.layer == 3 and version in MPEG_FORMATS, f"{path.name}: non è MPEG Layer III")
    _require(info.sample_rate in MPEG_RATES[version] and info.channels in (1, 2),
             f"{path.name}: frequenza o canali non validi per l'iPhone")
    kbps = int(round(info.bitrate / 1000))
    if info.bitrate_mode == BitrateMode.CBR or info.bitrate_mode == BitrateMode.UNKNOWN:
        _require(kbps in MPEG_CBR_KBPS[version], f"{path.name}: bitrate costante non standard ({kbps} kbit/s)")
    else:
        _require(8 <= kbps <= 320, f"{path.name}: bitrate medio fuori dai limiti ({kbps} kbit/s)")
    samples = int(round(info.length * info.sample_rate))
    _require(samples > 0, f"{path.name}: durata nulla")
    result = AudioInfo(MPEG_FORMATS[version], kbps, info.sample_rate, info.channels, samples)
    return result


def flac_info(path: Path) -> AudioInfo:
    """Un FLAC: l'iPhone lo suona così com'è (provato da rustunes), mono o stereo."""
    from mutagen.flac import FLAC
    try:
        info = FLAC(str(path)).info
    except Exception as exc:  # noqa: BLE001
        raise PhoneSyncError(f"{path.name}: non è un FLAC leggibile ({exc})") from exc
    _require(info.channels in (1, 2), f"{path.name}: l'iPhone accetta FLAC mono o stereo, non a {info.channels} canali")
    _require(info.total_samples > 0 and info.sample_rate > 0, f"{path.name}: durata nulla")
    seconds = info.total_samples / info.sample_rate
    kbps = max(1, int(round(path.stat().st_size * 8 / seconds / 1000)))
    result = AudioInfo(602, kbps, info.sample_rate, info.channels, info.total_samples, FLAC_KIND, ".flac")
    return result


def aac_info(path: Path) -> AudioInfo:
    """Un M4A in AAC (LC, HE, HE v2). Apple Lossless no: vuole un altro formato di inserimento."""
    from mutagen.mp4 import MP4
    try:
        info = MP4(str(path)).info
    except Exception as exc:  # noqa: BLE001
        raise PhoneSyncError(f"{path.name}: non è un M4A leggibile ({exc})") from exc
    codec = str(getattr(info, "codec", ""))
    profile = int(codec.rsplit(".", 1)[1]) if codec.startswith("mp4a.40.") and codec.rsplit(".", 1)[1].isdigit() else 0
    _require(profile in AAC_FORMATS, f"{path.name}: formato {codec or 'sconosciuto'} non ancora gestito (solo AAC)")
    _require(info.channels in (1, 2), f"{path.name}: solo mono o stereo")
    samples = int(round(info.length * info.sample_rate))
    _require(samples > 0, f"{path.name}: durata nulla")
    kbps = max(1, int(round(info.bitrate / 1000)))
    result = AudioInfo(AAC_FORMATS[profile], kbps, info.sample_rate, info.channels, samples, AAC_KIND, ".m4a")
    return result


AUDIO_READERS = {".mp3": mp3_info, ".flac": flac_info, ".m4a": aac_info}


def audio_info(path: Path) -> AudioInfo:
    reader = AUDIO_READERS.get(path.suffix.lower())
    _require(reader is not None, f"{path.name}: l'iPhone qui accetta MP3, FLAC e M4A (AAC)")
    result = reader(path)
    return result


def _text(value: str, name: str) -> str:
    text = (value or "").strip()
    _require(bool(text) and len(text.encode("utf-8")) <= 4096, f"{name} vuoto o troppo lungo")
    cleaned = ""
    for char in text:
        if ord(char) >= 32:
            cleaned += char
    result = cleaned
    return result


JPEG_MAGIC = bytes([0xFF, 0xD8, 0xFF])
PNG_MAGIC = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
COVER_OVERHEAD = {".mp3": 1, ".flac": 1, ".m4a": 17}   # artwork_checksum = byte dell'immagine + questo (rustunes)


def is_supported_cover(data) -> bool:
    """L'iPhone tiene JPEG e PNG così come sono."""
    result = bool(data) and (data[:3] == JPEG_MAGIC or data[:8] == PNG_MAGIC)
    return result


def cover_checksum(cover: bytes, extension: str) -> int:
    result = len(cover) + COVER_OVERHEAD.get(extension, 1)
    return result


def insert_track(pid: int, album_pid: int, artist_pid: int, tags, audio: AudioInfo, cover_cache_id: int = 0,
                 cover_checksum_value: int = 0) -> dict:
    """Un brano nuovo (tags: tags.TrackTags). album_pid e artist_pid: quelli di un album e di un artista dell'album
    già sull'iPhone (sync_id), oppure nuovi; l'iPhone crea l'album e l'artista una volta sola. Con una copertina,
    cover_cache_id (un numero nuovo, sopra quelli del telefono) e cover_checksum_value: l'iPhone la chiederà insieme
    all'audio (AssetParts 3)."""
    _require(len({pid, album_pid, artist_pid}) == 3 and 0 not in (pid, album_pid, artist_pid),
             "identificativi del brano non validi")
    title = _text(tags.title, "titolo")
    artist = _text(tags.artist or tags.album_artist or "Artista sconosciuto", "artista")
    album = _text(tags.album or "Album sconosciuto", "album")
    item = {"album_pid": _signed(album_pid), "artist_pid": _signed(artist_pid), "title": title, "sort_name": title,
            "artist": artist, "sort_artist": artist, "album": album, "sort_album": album, "is_song": True,
            "remember_bookmark": False, "artwork_checksum": cover_checksum_value if cover_cache_id else 0,
            "total_time_ms": audio.total_time_ms}
    if cover_cache_id:
        _require(cover_checksum_value > 0, "copertina senza dimensione")
        item["artwork_cache_id"] = cover_cache_id
    if tags.album_artist:
        album_artist = _text(tags.album_artist, "artista dell'album")
        item["album_artist"] = album_artist
        item["sort_album_artist"] = album_artist
        if tags.compilation:
            item["is_compilation"] = True      # l'iPhone vuole anche l'artista dell'album (rustunes)
    if tags.genre:
        item["genre"] = _text(tags.genre, "genere")
    year = _year(tags.year)
    if year:
        item["year"] = year
    for name, number, total in (("track", tags.track_number, tags.track_total),
                                ("disc", tags.disc_number, tags.disc_total)):
        if number:
            item[f"{name}_number"] = int(number)
            if total and total >= number:
                item[f"{name}_count"] = int(total)
    avformat = {"audio_format": audio.audio_format, "bit_rate": audio.bit_rate_kbps,
                "sample_rate": float(audio.sample_rate), "channels": audio.channels, "duration": audio.samples}
    stats = {"play_count_recent": 0, "play_count_user": 0, "skip_count_recent": 0, "skip_count_user": 0,
             "has_been_played": False}
    result = {"operation": "insert_track", "pid": _signed(pid), "item": item, "avformat_info": avformat,
              "location": {"kind": audio.kind}, "item_stats": stats}
    return result


def _year(text: str) -> int:
    digits = (text or "").strip()[:4]
    result = int(digits) if len(digits) == 4 and digits.isdigit() and 0 < int(digits) <= 9999 else 0
    return result


def update_track(sync_id: int, item: dict) -> dict:
    """Solo i campi sicuri (vedi rustunes, docs/05 §2): titolo con sort_name e album_pid attuale, genere, anno,
    numeri; l'album con sort_album e album_pid. Mai artista o artista dell'album: per quelli si rimpiazza il brano."""
    allowed = {"title", "sort_name", "album", "sort_album", "album_pid", "genre", "year", "track_number",
               "track_count", "disc_number", "disc_count"}
    _require(sync_id != 0 and bool(item), "aggiornamento vuoto")
    for key in item:
        _require(key in allowed, f"campo {key} non modificabile così")
    _require(("title" in item) == ("sort_name" in item), "titolo e sort_name vanno insieme")
    _require(("album" in item) == ("sort_album" in item), "album e sort_album vanno insieme")
    _require("album_pid" in item or not ({"title", "album"} & set(item)),
             "titolo e album vogliono anche album_pid")
    converted = {}
    for key, value in item.items():
        converted[key] = _signed(value) if key == "album_pid" else value
    result = {"operation": "update_track", "pid": _signed(sync_id), "item": converted}
    return result


def delete_track(sync_id: int) -> dict:
    _require(sync_id != 0, "brano senza sync_id")
    result = {"operation": "delete_track", "pid": _signed(sync_id)}
    return result


# --------------------------------------------------------------------------- una sessione completa

SYNC_MEDIA = "iTunes_Control/Sync/Media"
METADATA_PATH = SYNC_MEDIA + "/Sync_00000000.plist"
SIGNATURE_PATH = METADATA_PATH + ".cig"
AIRLOCK = "Airlock/Media"
AIRLOCK_ARTWORK = AIRLOCK + "/Artwork"
AUDIO_PART = 1
ARTWORK_PART = 2


@dataclass(frozen=True)
class Upload:
    """L'audio di un insert_track: il file sul PC (già pronto, con i tag), dove l'iPhone lo terrà e, se l'insert ne
    dichiara una, la copertina (JPEG o PNG)."""
    pid: int
    source: Path
    destination: str          # iTunes_Control/Music/Fnn/ABCD.mp3
    cover: bytes = b""


@dataclass
class SessionReport:
    anchor_before: int = 0
    anchor_after: int = 0
    operations: int = 0
    uploaded: list = None
    declined: list = None
    messages: list = None


async def _require_absent(afc, path: str) -> None:
    _require(not await afc.exists(path), f"sull'iPhone c'è già {path}: niente da fare")


async def run_session(lockdown, identity: LibraryIdentity, state: CatalogState, host_name: str,
                      operations: list, uploads: list, timestamp) -> SessionReport:
    """Una sessione Delta: file delle operazioni firmato, FinishedSyncingMetadata, l'audio chiesto, SyncFinished.
    state deve venire da una copia del database appena scaricata. Prima di FinishedSyncingMetadata ogni errore lascia
    il telefono com'era; dopo, il telefono applica le operazioni."""
    from pymobiledevice3.services.afc import AfcService

    report = SessionReport(anchor_before=state.media_anchor, operations=len(operations), uploaded=[], declined=[])
    by_asset = {}
    for upload in uploads:
        by_asset[str(_signed(upload.pid))] = upload
    revision = state.media_anchor + 1
    payload = operation_file(revision, timestamp, [update_db_info(state)] + list(operations))
    async with AfcService(lockdown) as afc:
        _require(await afc.exists(SYNC_MEDIA), "manca la cartella di sincronizzazione sull'iPhone")
        # un file delle operazioni lasciato da un'altra sessione verrebbe importato con il nostro: ci si ferma; altri
        # resti (es. una vecchia firma .cig2 senza il suo .plist) l'iPhone li ignora e restano dove sono
        pending = []
        for name in await afc.listdir(SYNC_MEDIA):
            if name.endswith(".plist") or name in (Path(METADATA_PATH).name, Path(SIGNATURE_PATH).name):
                pending.append(name)
        _require(not pending, f"nella cartella di sincronizzazione dell'iPhone c'è già {pending[0] if pending else ''}"
                              ": un'altra sincronizzazione non è finita, niente da fare")
        for asset_id, upload in by_asset.items():
            await _require_absent(afc, upload.destination)
            await _require_absent(afc, f"{AIRLOCK}/{asset_id}{upload.source.suffix.lower()}")
            await _require_absent(afc, f"{AIRLOCK}/{asset_id}")
        service = await lockdown.start_lockdown_service(ATC_SERVICE)
        session = AtcSession(service)
        try:
            await session.handshake()
            signer = await session.request_sync(identity, host_name, state.media_anchor)
            signature = signer.sign(payload)
            await afc.set_file_contents(METADATA_PATH, payload)
            await afc.set_file_contents(SIGNATURE_PATH, signature)
            _require(await afc.get_file_contents(METADATA_PATH) == payload and
                     await afc.get_file_contents(SIGNATURE_PATH) == signature,
                     "il file delle operazioni riletto dall'iPhone è diverso: non confermo niente")
            await session.send(finished_syncing_metadata(revision))
            finished = False
            while not finished:
                message = await session.receive()
                command = message["Command"]
                if command == "SyncFinished":
                    finished = True
                elif command == "AssetManifest":
                    await _serve_manifest(afc, session, message, by_asset, report)
                elif command in ("Progress", "SyncAllowed", "InstalledAssets", "AssetMetrics"):
                    pass
                elif command == "SyncFailed":
                    raise PhoneSyncError(f"l'iPhone ha interrotto la sincronizzazione (codice "
                                         f"{(message.get('Params') or {}).get('ErrorCode')})")
                elif command == "IdleExit":
                    raise PhoneSyncError("l'iPhone ha chiuso la sincronizzazione per inattività")
                else:
                    raise PhoneSyncError(f"messaggio inatteso durante la sincronizzazione: {command}")
            missing = []
            for asset_id in by_asset:
                if asset_id not in report.uploaded:
                    missing.append(asset_id)
            _require(not missing, "l'iPhone non ha chiesto l'audio di tutti i brani nuovi")
        finally:
            report.messages = list(session.received)
            await service.close()
    report.anchor_after = revision
    return report


async def _serve_manifest(afc, session: AtcSession, message: dict, by_asset: dict, report: SessionReport) -> None:
    """Carica l'audio dei brani di questa sessione; per tutto il resto (altri brani, copertine) risponde FileError,
    come fa rustunes con le richieste che non può soddisfare."""
    manifest = ((message.get("Params") or {}).get("AssetManifest") or {}).get("Media") or []
    for entry in manifest:
        asset_id = str(entry.get("AssetID", ""))
        parts = (entry.get("Variant") or {}).get("AssetParts")
        upload = by_asset.get(asset_id)
        # un brano di questa sessione: l'audio, e la copertina se e solo se l'insert ne ha dichiarata una
        # (il bit 4, Genius, che l'iPhone a volte aggiunge, non conta)
        wanted = False
        if upload is not None and isinstance(parts, int) and asset_id not in report.uploaded:
            wanted = bool(parts & AUDIO_PART) and bool(parts & ARTWORK_PART) == bool(upload.cover)
        if wanted:
            if parts & ARTWORK_PART:
                # prima la copertina, riletta; poi l'audio; un solo FileComplete le dichiara tutte e due
                if not await afc.exists(AIRLOCK_ARTWORK):
                    await afc.makedirs(AIRLOCK_ARTWORK)
                cover_path = f"{AIRLOCK_ARTWORK}/{asset_id}"
                await afc.set_file_contents(cover_path, upload.cover)
                _require(await afc.get_file_contents(cover_path) == upload.cover, "copertina riletta diversa")
            staged = f"{AIRLOCK}/{asset_id}{upload.source.suffix.lower()}"
            data = upload.source.read_bytes()
            await afc.set_file_contents(staged, data)
            stat = await afc.stat(staged)
            _require(int(stat.get("st_size", -1)) == len(data), "l'audio caricato ha una dimensione diversa")
            await afc.rename(staged, f"{AIRLOCK}/{asset_id}")
            await session.send({"Session": 2, "Command": "FileComplete",
                                "Params": {"AssetID": asset_id, "AssetPath": upload.destination,
                                           "Dataclass": "Media"}})
            report.uploaded.append(asset_id)
        else:
            await session.send({"Session": 2, "Command": "FileError",
                                "Params": {"AssetID": asset_id, "Dataclass": "Media", "ErrorCode": 16,
                                           "ErrorIsVisible": False}})
            report.declined.append((asset_id, parts))
