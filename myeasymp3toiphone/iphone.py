"""Comunicazione con l'iPhone tramite pymobiledevice3.

Richiede il servizio Apple Mobile Device (installato dall'app "Dispositivi Apple"
del Microsoft Store oppure da iTunes), che ascolta sulla porta locale 27015.

Cosa si può fare senza jailbreak:
  * leggere la libreria dell'app Musica (/iTunes_Control/Music) e copiarla sul PC;
  * leggere/scrivere i documenti delle app con "Condivisione file" (es. VLC),
    che vengono mostrati anche nell'app File dell'iPhone.
Scrivere nella libreria dell'app Musica non è possibile senza iTunes/Dispositivi
Apple: Apple non espone un protocollo pubblico per aggiornarne il database.

Tutte le funzioni pubbliche sono bloccanti: vanno chiamate da un thread di lavoro.
"""

import asyncio
import logging
import posixpath
import shutil
import tempfile
import socket
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from pymobiledevice3.exceptions import (
    AppNotInstalledError,
    NotTrustedError,
    PairingDialogResponsePendingError,
    PasswordRequiredError,
    PyMobileDevice3Exception,
    UserDeniedPairingError,
)
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.afc import AfcService
from pymobiledevice3.services.house_arrest import HouseArrestService
from pymobiledevice3.services.installation_proxy import InstallationProxyService
from pymobiledevice3.usbmux import list_devices

USBMUXD_ADDRESS = ("127.0.0.1", 27015)
MUSIC_ROOT = "/iTunes_Control/Music"
DOCUMENTS_ROOT = "/Documents"
PAIR_TIMEOUT = 60

# App consigliate per ascoltare la musica copiata dal PC
RECOMMENDED_APPS = {
    "org.videolan.vlc-ios": "VLC",
    "com.readdle.ReaddleDocsIPad": "Documents",
    "com.foobar2000.mobile": "foobar2000",
}

DRIVER_MESSAGE = (
    "Il servizio Apple per i dispositivi non è attivo.\n\n"
    "Installa l'app gratuita \"Dispositivi Apple\" dal Microsoft Store "
    "(oppure iTunes), poi ricollega l'iPhone."
)
NO_DEVICE_MESSAGE = "Nessun iPhone collegato. Collega l'iPhone con il cavo USB e sbloccalo."

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
class AppInfo:
    bundle_id: str
    name: str

    def label(self) -> str:
        if self.bundle_id in RECOMMENDED_APPS:
            result = f"{self.name} (consigliata per la musica)"
        else:
            result = self.name
        return result


@dataclass
class RemoteFile:
    path: str
    size: int = 0
    mtime: float = 0.0   # data di modifica (timestamp), 0 se non letta

MTIME_TOLERANCE = 2.0


@dataclass
class UploadItem:
    source: Path                 # il file sul PC: si legge soltanto
    relative: str                # dove va, dentro Documents (Musica/Artista/Album/NN - Titolo.ext)
    prepare: Optional[Callable[[Path], None]] = None   # modifica la COPIA temporanea prima dell'invio
    signature: str = ""          # le modifiche in sospeso applicate (overlay.TagOverlay.signature)


@dataclass
class TransferReport:
    done: list
    skipped: list
    errors: list      # (percorso, messaggio)
    cancelled: bool = False
    sent: list = field(default_factory=list)   # (percorso sull'iPhone, UploadItem, dimensione sull'iPhone)

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


LISTING_FILE = "iphone_files.json"


def save_listing(home: Path, bundle_id: str, app_name: str, files: list) -> None:
    """L'elenco dei file nell'app dell'iPhone, nella cartella dati: la colonna "iPhone" della Libreria lo usa anche
    con l'iPhone scollegato."""
    import json
    import os
    import time
    data = {"bundle_id": bundle_id, "app_name": app_name, "saved_at": time.strftime("%Y-%m-%d %H:%M"),
            "files": [[remote.path, remote.size, remote.mtime] for remote in files]}
    path = home / LISTING_FILE
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data), encoding="utf-8")
    os.replace(temporary, path)


def load_listing(home: Path) -> dict:
    """{"bundle_id", "app_name", "saved_at", "files": [RemoteFile]}; vuoto se manca o non è leggibile."""
    import json
    result = {}
    try:
        data = json.loads((home / LISTING_FILE).read_text(encoding="utf-8"))
        files = []
        for path, size, mtime in data.get("files", []):
            files.append(RemoteFile(path=str(path), size=int(size), mtime=float(mtime)))
        result = {"bundle_id": str(data.get("bundle_id", "")), "app_name": str(data.get("app_name", "")),
                  "saved_at": str(data.get("saved_at", "")), "files": files}
    except (OSError, ValueError, TypeError, AttributeError):
        result = {}
    return result


SENT_FILE = "iphone_inviati.json"


def load_sent(home: Path, bundle_id: str) -> dict:
    """Cosa è stato inviato a un'app: {percorso sull'iPhone in minuscolo: {source, size, mtime, signature,
    remote_size}}. Serve a riconoscere la versione sull'iPhone anche se la copia inviata ha tag diversi dal file."""
    import json
    result = {}
    try:
        data = json.loads((home / SENT_FILE).read_text(encoding="utf-8"))
        entries = data.get(bundle_id, {})
        if isinstance(entries, dict):
            result = entries
    except (OSError, ValueError, AttributeError):
        result = {}
    return result


def record_sent(home: Path, bundle_id: str, report: "TransferReport", key_of: Callable[[Path], str]) -> None:
    import json
    import os
    path = home / SENT_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError):
        data = {}
    entries = data.setdefault(bundle_id, {})
    for remote, item, remote_size in report.sent:
        local = item.source.stat()
        entries[remote.casefold()] = {"source": key_of(item.source), "size": local.st_size,
                                      "mtime": local.st_mtime, "signature": item.signature,
                                      "remote_size": remote_size}
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data), encoding="utf-8")
    os.replace(temporary, path)


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
    except PasswordRequiredError as exc:
        raise IPhoneError("L'iPhone è bloccato: sbloccalo e riprova.") from exc
    except (PairingDialogResponsePendingError, NotTrustedError) as exc:
        raise IPhoneError("Sull'iPhone tocca \"Autorizza\" e inserisci il codice, poi riprova.") from exc
    except UserDeniedPairingError as exc:
        raise IPhoneError("L'autorizzazione è stata negata sull'iPhone. Scollega e ricollega il cavo per riprovare.") from exc
    except AppNotInstalledError as exc:
        raise IPhoneError("L'app scelta non è installata sull'iPhone.") from exc
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


async def _list_files(afc: AfcService, root: str, with_size: bool) -> list:
    found = []
    if await afc.exists(root):
        async for directory, _subdirs, names in afc.walk(root):
            for name in sorted(names):
                path = posixpath.join(directory, name)
                size = 0
                mtime = 0.0
                if with_size:
                    info = await afc.stat(path)
                    size = int(info.get("st_size", 0))
                    modified = info.get("st_mtime")
                    if isinstance(modified, datetime):
                        mtime = modified.timestamp()
                found.append(RemoteFile(path=path, size=size, mtime=mtime))
    return found


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


async def _file_sharing_apps() -> list:
    lockdown = await _open_lockdown()
    try:
        async with InstallationProxyService(lockdown) as proxy:
            apps = await proxy.get_apps(application_type="User")
    finally:
        await lockdown.close()
    result = []
    for bundle_id, info in apps.items():
        if info.get("UIFileSharingEnabled"):
            name = info.get("CFBundleDisplayName") or info.get("CFBundleName") or bundle_id
            result.append(AppInfo(bundle_id=bundle_id, name=name))
    result.sort(key=lambda app: (app.bundle_id not in RECOMMENDED_APPS, app.name.lower()))
    return result


async def _list_app_files(bundle_id: str) -> list:
    lockdown = await _open_lockdown()
    try:
        async with await HouseArrestService.create(lockdown, bundle_id, documents_only=True) as afc:
            result = await _list_files(afc, DOCUMENTS_ROOT, with_size=True)
    finally:
        await lockdown.close()
    return result


async def _upload_to_app(bundle_id: str, items: list, progress: Optional[ProgressFn],
                         cancel: Optional[threading.Event]) -> TransferReport:
    """Ogni brano: copia temporanea, item.prepare sulla copia (tag modificati, pulizia), invio della copia; la copia
    sull'iPhone prende la data del file del PC. Il file del PC non si apre mai in scrittura."""
    report = TransferReport(done=[], skipped=[], errors=[])
    staging = Path(tempfile.mkdtemp(prefix="myEasyMP3toIPhone_invio_"))
    lockdown = await _open_lockdown()
    try:
        async with await HouseArrestService.create(lockdown, bundle_id, documents_only=True) as afc:
            created_dirs = set()
            index = 0
            while index < len(items) and not _cancelled(cancel):
                item = items[index]
                remote = posixpath.join(DOCUMENTS_ROOT, item.relative)
                if progress is not None:
                    progress(index, len(items), item.source.name)
                copy = staging / f"{index}{item.source.suffix.lower()}"
                try:
                    shutil.copyfile(str(item.source), str(copy))
                    if item.prepare is not None:
                        try:
                            item.prepare(copy)
                        except Exception as exc:  # noqa: BLE001 - un file strano si invia com'è, con un avviso
                            log.warning("Copia di %s inviata senza modifiche: %s", item.source, exc)
                            shutil.copyfile(str(item.source), str(copy))
                    parent = posixpath.dirname(remote)
                    if parent not in created_dirs:
                        await afc.makedirs(parent)
                        created_dirs.add(parent)
                    await afc.push(str(copy), remote, progress_bar=False)
                    await afc.set_file_time(remote, datetime.fromtimestamp(item.source.stat().st_mtime))
                    remote_size = int((await afc.stat(remote)).get("st_size", copy.stat().st_size))
                    report.done.append(remote)
                    report.sent.append((remote, item, remote_size))
                except (PyMobileDevice3Exception, OSError) as exc:
                    report.errors.append((str(item.source), str(exc)))
                finally:
                    if copy.exists():
                        copy.unlink()
                index += 1
    finally:
        await lockdown.close()
        shutil.rmtree(staging, ignore_errors=True)
    report.cancelled = _cancelled(cancel)
    return report


async def _delete_app_files(bundle_id: str, paths: list) -> TransferReport:
    report = TransferReport(done=[], skipped=[], errors=[])
    lockdown = await _open_lockdown()
    try:
        async with await HouseArrestService.create(lockdown, bundle_id, documents_only=True) as afc:
            for path in paths:
                failed = await afc.rm(path, force=True)
                if failed:
                    report.errors.append((path, "impossibile eliminare"))
                else:
                    report.done.append(path)
    finally:
        await lockdown.close()
    return report


async def _list_music_library() -> list:
    lockdown = await _open_lockdown()
    try:
        async with AfcService(lockdown) as afc:
            result = await _list_files(afc, MUSIC_ROOT, with_size=False)
    finally:
        await lockdown.close()
    return result


def _local_name(remote: str, from_music_library: bool) -> str:
    """Nome locale: i file della libreria Musica hanno nomi casuali (F12/ABCD.mp3)."""
    if from_music_library:
        folder = posixpath.basename(posixpath.dirname(remote))
        result = f"{folder}_{posixpath.basename(remote)}"
    else:
        result = posixpath.relpath(remote, DOCUMENTS_ROOT)
    return result


async def _download(bundle_id: Optional[str], remote_paths: list, local_dir: Path,
                    progress: Optional[ProgressFn], cancel: Optional[threading.Event]) -> tuple:
    report = TransferReport(done=[], skipped=[], errors=[])
    local_files = []
    lockdown = await _open_lockdown()
    try:
        if bundle_id is None:
            service = AfcService(lockdown)
        else:
            service = await HouseArrestService.create(lockdown, bundle_id, documents_only=True)
        async with service as afc:
            index = 0
            while index < len(remote_paths) and not _cancelled(cancel):
                remote = remote_paths[index]
                if progress is not None:
                    progress(index, len(remote_paths), posixpath.basename(remote))
                local_path = local_dir / _local_name(remote, bundle_id is None)
                try:
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    await afc.pull(remote, str(local_path), progress_bar=False)
                    local_files.append(local_path)
                    report.done.append(remote)
                except (PyMobileDevice3Exception, OSError) as exc:
                    report.errors.append((remote, str(exc)))
                index += 1
    finally:
        await lockdown.close()
    report.cancelled = _cancelled(cancel)
    result = (report, local_files)
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


def get_file_sharing_apps() -> list:
    result = _run(_file_sharing_apps())
    return result


def list_app_files(bundle_id: str) -> list:
    result = _run(_list_app_files(bundle_id))
    return result


def upload_to_app(bundle_id: str, items: list, progress: Optional[ProgressFn] = None,
                  cancel: Optional[threading.Event] = None) -> TransferReport:
    """items: lista di UploadItem. Si inviano tutti: chi chiama sceglie prima quali servono (device_status)."""
    result = _run(_upload_to_app(bundle_id, items, progress, cancel))
    return result


def delete_app_files(bundle_id: str, paths: list) -> TransferReport:
    result = _run(_delete_app_files(bundle_id, paths))
    return result


def list_music_library() -> list:
    result = _run(_list_music_library())
    return result


def download_files(bundle_id: Optional[str], remote_paths: list, local_dir: Path,
                   progress: Optional[ProgressFn] = None,
                   cancel: Optional[threading.Event] = None) -> tuple:
    """Scarica file dall'iPhone. bundle_id=None indica la libreria dell'app Musica.

    Restituisce (TransferReport, lista dei file locali scaricati).
    """
    result = _run(_download(bundle_id, remote_paths, local_dir, progress, cancel))
    return result
