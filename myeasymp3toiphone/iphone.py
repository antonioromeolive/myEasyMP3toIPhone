"""Comunicazione con l'iPhone tramite pymobiledevice3.

Richiede il servizio Apple Mobile Device (installato dall'app "Dispositivi Apple"
del Microsoft Store oppure da iTunes), che ascolta sulla porta locale 27015.

Cosa si fa, senza jailbreak e senza mai scrivere sull'iPhone:
  * leggere la musica dell'app Musica com'è nell'app: si scarica una copia del suo database
    (/iTunes_Control/iTunes/MediaLibrary.sqlitedb) e la si legge sul PC (phone_library);
  * copiare sul PC i file di quei brani (/iTunes_Control/Music/F12/ABCD.mp3).
Scrivere nella libreria dell'app Musica non è possibile senza iTunes o un programma come CopyTrans Manager: Apple non
espone un protocollo pubblico per aggiornarne il database, e scriverlo a mano può rovinare la libreria del telefono.

Tutte le funzioni pubbliche sono bloccanti: vanno chiamate da un thread di lavoro.
"""

import asyncio
import logging
import posixpath
import shutil
import socket
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from pymobiledevice3.exceptions import (
    NotTrustedError,
    PairingDialogResponsePendingError,
    PasswordRequiredError,
    PyMobileDevice3Exception,
    UserDeniedPairingError,
)
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.afc import AfcService
from pymobiledevice3.usbmux import list_devices

from .phone_library import DATABASE_NAME, PhoneLibraryError, read_music_database
from .phone_sync import PhoneSyncError

USBMUXD_ADDRESS = ("127.0.0.1", 27015)
MUSIC_DATABASE_FOLDER = "/iTunes_Control/iTunes"
# il database e il suo registro delle ultime modifiche; il file -shm no: SQLite lo ricostruisce dal registro
MUSIC_DATABASE_FILES = (DATABASE_NAME, DATABASE_NAME + "-wal")
PAIR_TIMEOUT = 60

DRIVER_MESSAGE = (
    "Il servizio Apple per i dispositivi non è attivo.\n\n"
    "Installa l'app gratuita \"Dispositivi Apple\" dal Microsoft Store "
    "(oppure iTunes), poi ricollega l'iPhone."
)
NO_DEVICE_MESSAGE = "Nessun iPhone collegato. Collega l'iPhone con il cavo USB e sbloccalo."
NO_MUSIC_MESSAGE = "Sull'iPhone non c'è la libreria dell'app Musica (nessun brano è mai stato caricato)."

ProgressFn = Callable[[int, int, str], None]
log = logging.getLogger(__name__)


class IPhoneError(Exception):
    """Errore di comunicazione con l'iPhone, con un messaggio leggibile dall'utente."""


@dataclass
class DeviceInfo:
    name: str
    model: str
    ios_version: str

    def label(self) -> str:
        result = f"{self.name} — {self.model}, iOS {self.ios_version}"
        return result


@dataclass
class TransferReport:
    done: list
    skipped: list
    errors: list      # (percorso, messaggio)
    cancelled: bool = False

    def summary(self) -> str:
        parts = [f"{len(self.done)} file trasferiti"]
        if self.skipped:
            parts.append(f"{len(self.skipped)} già presenti")
        if self.errors:
            parts.append(f"{len(self.errors)} errori")
        if self.cancelled:
            parts.append("operazione annullata")
        result = ", ".join(parts)
        return result


def driver_available() -> bool:
    try:
        connection = socket.create_connection(USBMUXD_ADDRESS, timeout=1.0)
        connection.close()
        result = True
    except OSError:
        result = False
    return result


def _cancelled(cancel: Optional[threading.Event]) -> bool:
    result = cancel is not None and cancel.is_set()
    return result


def _run(coroutine):
    """Esegue un'operazione asincrona traducendo gli errori in IPhoneError."""
    try:
        result = asyncio.run(coroutine)
    except IPhoneError:
        raise
    except PhoneSyncError as exc:
        raise IPhoneError(f"Sincronizzazione con l'iPhone non riuscita: {exc}") from exc
    except PasswordRequiredError as exc:
        raise IPhoneError("L'iPhone è bloccato: sbloccalo e riprova.") from exc
    except (PairingDialogResponsePendingError, NotTrustedError) as exc:
        raise IPhoneError("Sull'iPhone tocca \"Autorizza\" e inserisci il codice, poi riprova.") from exc
    except UserDeniedPairingError as exc:
        raise IPhoneError("L'autorizzazione è stata negata sull'iPhone. Scollega e ricollega il cavo per riprovare.") from exc
    except (PyMobileDevice3Exception, ConnectionError, OSError, asyncio.TimeoutError) as exc:
        raise IPhoneError(f"Errore di comunicazione con l'iPhone: {exc}") from exc
    return result


async def _open_lockdown():
    if not driver_available():
        raise IPhoneError(DRIVER_MESSAGE)
    devices = await list_devices()
    usb_devices = [device for device in devices if device.is_usb]
    if not usb_devices:
        usb_devices = devices
    if not usb_devices:
        raise IPhoneError(NO_DEVICE_MESSAGE)
    lockdown = await create_using_usbmux(serial=usb_devices[0].serial, autopair=True,
                                         pair_timeout=PAIR_TIMEOUT)
    return lockdown


# --------------------------------------------------------------------------- operazioni asincrone

async def _device_info() -> DeviceInfo:
    lockdown = await _open_lockdown()
    try:
        info = lockdown.short_info
        result = DeviceInfo(
            name=info.get("DeviceName") or "iPhone",
            model=lockdown.display_name or info.get("ProductType") or "",
            ios_version=info.get("ProductVersion") or "?",
        )
    finally:
        await lockdown.close()
    return result


async def _list_music_app() -> list:
    """Scarica una copia del database dell'app Musica in una cartella temporanea e la legge."""
    folder = Path(tempfile.mkdtemp(prefix="myEasyMP3toIPhone_musica_"))
    lockdown = await _open_lockdown()
    try:
        async with AfcService(lockdown) as afc:
            for name in MUSIC_DATABASE_FILES:
                remote = posixpath.join(MUSIC_DATABASE_FOLDER, name)
                if await afc.exists(remote):
                    (folder / name).write_bytes(await afc.get_file_contents(remote))
        if not (folder / DATABASE_NAME).is_file():
            raise IPhoneError(NO_MUSIC_MESSAGE)
        try:
            result = read_music_database(folder / DATABASE_NAME)
        except PhoneLibraryError as exc:
            raise IPhoneError(f"Non riesco a leggere la musica dell'iPhone: {exc}. Riprova; se succede ancora, "
                              "la versione di iOS potrebbe usare un formato diverso.") from exc
    finally:
        await lockdown.close()
        shutil.rmtree(folder, ignore_errors=True)
    return result


async def _download_music(items: list, local_dir: Path, progress: Optional[ProgressFn],
                          cancel: Optional[threading.Event]) -> tuple:
    """Ogni brano (PhoneTrack) in local_dir/<pid>.<estensione>: nomi provvisori, chi chiama li sistema."""
    report = TransferReport(done=[], skipped=[], errors=[])
    downloaded = []
    lockdown = await _open_lockdown()
    try:
        async with AfcService(lockdown) as afc:
            index = 0
            while index < len(items) and not _cancelled(cancel):
                item = items[index]
                if progress is not None:
                    progress(index, len(items), item.tags.title or posixpath.basename(item.remote_path))
                local_path = local_dir / f"{item.pid}{posixpath.splitext(item.remote_path)[1].lower()}"
                try:
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    await afc.pull(item.remote_path, str(local_path), progress_bar=False)
                    downloaded.append((item, local_path))
                    report.done.append(item.remote_path)
                except (PyMobileDevice3Exception, OSError) as exc:
                    report.errors.append((item.tags.title or item.remote_path, str(exc)))
                index += 1
    finally:
        await lockdown.close()
    report.cancelled = _cancelled(cancel)
    result = (report, downloaded)
    return result


# --------------------------------------------------------------------------- API pubblica (bloccante)

def device_present():
    """True se un iPhone è collegato (USB o rete), False se no, None se manca il driver Apple. Veloce: non apre
    nessuna sessione con l'iPhone e non chiede l'autorizzazione."""
    if not driver_available():
        result = None
    else:
        try:
            result = bool(asyncio.run(list_devices()))
        except Exception:  # noqa: BLE001 - un servizio che non risponde equivale a nessun iPhone
            result = False
    return result


def get_device_info() -> DeviceInfo:
    result = _run(_device_info())
    return result


def list_music_app() -> list:
    """I brani dell'app Musica (phone_library.PhoneTrack) con un file sull'iPhone, con i tag che mostra l'app."""
    result = _run(_list_music_app())
    return result


async def _sync_registry(home: Path, sync_ids: set):
    from .provenance import synchronize
    lockdown = await _open_lockdown()
    try:
        async with AfcService(lockdown) as afc:
            result = await synchronize(afc, home, sync_ids)
    finally:
        await lockdown.close()
    return result


def sync_registry(home: Path, sync_ids: set):
    """Il registro della provenienza (provenance.Registry), unito a quello sull'iPhone e ripulito dei brani che non
    ci sono più."""
    result = _run(_sync_registry(home, sync_ids))
    return result


def download_music(items: list, local_dir: Path, progress: Optional[ProgressFn] = None,
                   cancel: Optional[threading.Event] = None) -> tuple:
    """Copia sul PC i file dei brani (PhoneTrack). Restituisce (TransferReport, [(PhoneTrack, file locale)])."""
    result = _run(_download_music(items, local_dir, progress, cancel))
    return result
