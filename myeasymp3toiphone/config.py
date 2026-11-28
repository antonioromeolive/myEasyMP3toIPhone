# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La cartella dati (~/.myEasyMP3toIPhone), le impostazioni, i profili AI e le loro chiavi.

Stesso meccanismo di myCalibreTools:
  * ai_profiles.json contiene i profili AI, senza chiavi e senza indirizzi privati;
  * una chiave o un indirizzo scritti in chiaro vanno nel credential store di Windows (keyring),
    oppure, senza credential store, in secrets.json nella cartella dati;
  * ogni campo che contiene una chiave o un indirizzo accetta $NOME: si salva solo il nome della
    variabile d'ambiente, il valore si legge all'avvio dal sistema.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sys
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from urllib.parse import urlsplit

log = logging.getLogger(__name__)

PRODUCT = "myEasyMP3toIPhone"
# Il nome con cui le chiavi API sono salvate nel credential store: cambiarlo fa perdere l'accesso alle chiavi salvate.
KEYRING_SERVICE = "myEasyMP3toIPhone"
DATA_DIR_NAME = ".myEasyMP3toIPhone"
HOME_ENV_VAR = "MYEASYMP3TOIPHONE_HOME"
# Il nome precedente del programma (fino al 21/11/2026): la sua cartella dati e le sue chiavi passano a questo
# (config_dir e startup.migrate_from_old_name)
OLD_PRODUCT = "myCopiaStiMP3"
OLD_DATA_DIR_NAME = ".myCopiaStiMP3"
OLD_KEYRING_SERVICE = "myCopiaStiMP3"
SETTINGS_FILE = "settings.json"
PROFILES_FILE = "ai_profiles.json"
SECRETS_FILE = "secrets.json"
VARIABLE_NAME = "[A-Za-z_][A-Za-z0-9_]*"

OLLAMA = "ollama"
AZURE = "azure"
OPENAI = "openai"
ANTHROPIC = "anthropic"
KINDS = ((OLLAMA, "Ollama"), (AZURE, "Azure OpenAI"), (OPENAI, "OpenAI"), (ANTHROPIC, "Anthropic (Claude)"))
OLLAMA_LOCAL_SERVER = "http://localhost:11434"
OPENAI_SERVER = "https://api.openai.com"
ANTHROPIC_SERVER = "https://api.anthropic.com"
PUBLIC_SERVERS = (OLLAMA_LOCAL_SERVER, OPENAI_SERVER, ANTHROPIC_SERVER)
SERVER_IN_STORE = "(nel credential store)"
DEFAULT_MODELS = {OLLAMA: "llama3.1:8b", AZURE: "", OPENAI: "gpt-4.1", ANTHROPIC: "claude-opus-5-5"}
# Le variabili d'ambiente (server, chiave) che un profilo nuovo nomina quando hanno un valore: gli stessi nomi dei
# profili di myCalibreTools (Ollama, Azure AI Foundry); per OpenAI e Anthropic, che myCalibreTools non usa, i nomi
# standard dei loro SDK. Un nome vuoto = quel tipo ha un server fisso.
PROFILE_VARIABLES = {
    OLLAMA: ("OLLAMA_API_BASE", "OLLAMA_API_KEY"),
    AZURE: ("AZURE_FOUNDRY_EP", "AZURE_FOUNDRY_KEY"),
    OPENAI: ("", "OPENAI_API_KEY"),
    ANTHROPIC: ("", "ANTHROPIC_API_KEY"),
}
DEFAULT_SCAN_PROFILE = "Ollama locale"  # creato al primo avvio (ai.ensure_default_profile): la scansione resta sul PC

CREDENTIAL_STORE = "Gestione credenziali di Windows" if sys.platform == "win32" else "il credential store del sistema"
SECRETS_FILE_TEXT = "secrets.json nella cartella dati"

# myCalibreTools: i suoi profili AI si possono importare (Impostazioni → Importa da myCalibreTools)
CALIBRE_TOOLS_DIR_NAME = ".myCalibreTools"
CALIBRE_TOOLS_HOME_ENV_VAR = "MYCALIBRETOOLS_HOME"
CALIBRE_TOOLS_KEYRING_SERVICE = "CalibreDuplicateRemover"
CALIBRE_TOOLS_SERVER_IN_STORE = "(in the credential store)"


# --------------------------------------------------------------------------- cartella dati

def _expanded(value: str) -> str:
    """Un percorso con %NOME%, $NOME e una ~ iniziale espansi."""
    result = os.path.expandvars(value).strip()
    if result.startswith(("~/", "~\\")):
        result = str(Path.home() / result[2:])
    return result


def _home_env_value() -> str:
    result = _expanded(os.environ.get(HOME_ENV_VAR, ""))
    return result


def home_env_ignored() -> bool:
    """MYEASYMP3TOIPHONE_HOME ha un valore che non è un percorso completo: viene ignorato."""
    value = _home_env_value()
    result = bool(value) and not os.path.isabs(value)
    return result


def home_folder() -> Path:
    """MYEASYMP3TOIPHONE_HOME quando è un percorso completo, altrimenti ~/.myEasyMP3toIPhone. Non la crea."""
    if _home_env_value() and not home_env_ignored():
        result = Path(_home_env_value())
    else:
        result = Path.home() / DATA_DIR_NAME
    return result


_old_home_in_use: set = set()   # la rinomina della cartella vecchia non è riuscita in questa esecuzione


def _rename_old_home(old: Path, new: Path) -> Path:
    """Rinomina la cartella dati del nome precedente; restituisce quella da usare. Se Windows rifiuta (un programma
    della versione precedente è ancora aperto) si usa la vecchia per tutta l'esecuzione e si riprova al prossimo
    avvio: mai una cartella nuova vuota, che nasconderebbe le impostazioni."""
    result = new
    if old in _old_home_in_use:
        result = old
    else:
        try:
            old.rename(new)
            log.info("Cartella dati %s rinominata in %s", old, new)
        except OSError as exc:
            if not new.exists():
                _old_home_in_use.add(old)
                result = old
                log.warning("Impossibile rinominare %s in %s, la uso così com'è: %s", old, new, exc)
    return result


def config_dir() -> Path:
    """La cartella dati, creata se manca. Solo la posizione predefinita prende la cartella del nome precedente
    (~/.myCopiaStiMP3); una cartella scelta con la variabile parte com'è."""
    result = home_folder()
    old = Path.home() / OLD_DATA_DIR_NAME
    if not result.exists() and result == Path.home() / DATA_DIR_NAME and old.is_dir():
        result = _rename_old_home(old, result)
    result.mkdir(parents=True, exist_ok=True)
    return result


def default_library_dir() -> Path:
    result = Path.home() / "Music" / PRODUCT
    return result


# --------------------------------------------------------------------------- $NOME

def is_variable_name(name) -> bool:
    result = isinstance(name, str) and re.fullmatch(VARIABLE_NAME, name) is not None
    return result


def variable_in(text) -> str:
    """NOME quando un campo è scritto $NOME, altrimenti ""."""
    match = None
    if isinstance(text, str):
        match = re.fullmatch(rf"\$({VARIABLE_NAME})", text.strip())
    if match:
        result = match.group(1)
    else:
        result = ""
    return result


def literal_text(text: str) -> str:
    """Un valore che inizia davvero con $ si scrive $$."""
    if text.startswith("$$"):
        result = text[1:]
    else:
        result = text
    return result


def as_written(value: str) -> str:
    if value.startswith("$"):
        result = f"${value}"
    else:
        result = value
    return result


def setting_value(text: str) -> str:
    """Il valore di un campo che può nominare una variabile: "" quando la variabile non ha valore."""
    name = variable_in(text)
    if name:
        result = os.environ.get(name, "")
    else:
        result = literal_text(text)
    return result


# --------------------------------------------------------------------------- JSON

def read_json(path: Path):
    """I dati del file; None se manca o non è leggibile."""
    result = None
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        result = None
    except (OSError, ValueError) as exc:
        log.warning("File illeggibile ignorato %s: %s", path, exc)
        result = None
    return result


def write_json(path: Path, data) -> None:
    """Scritto con un nome temporaneo e poi rinominato: nessuno legge mai mezzo file."""
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)


# --------------------------------------------------------------------------- segreti

def _secrets_path() -> Path:
    result = config_dir() / SECRETS_FILE
    return result


def _secret_in_credential_store(entry: str, service: str = KEYRING_SERVICE):
    """None quando il credential store manca o non contiene la voce."""
    try:
        import keyring
        result = keyring.get_password(service, entry)
    except Exception:  # noqa: BLE001 - keyring mancante o senza backend
        result = None
    return result


def _secret_in_file(entry: str) -> str:
    data = read_json(_secrets_path())
    result = ""
    if isinstance(data, dict):
        result = str(data.get(entry, ""))
    return result


def get_secret(entry: str) -> str:
    """La chiave salvata per un profilo: nel credential store, altrimenti in secrets.json."""
    result = _secret_in_credential_store(entry)
    if result is None:
        result = _secret_in_file(entry)
    return result


def secret_store(entry: str) -> str:
    """Dove si trova la chiave di un profilo, come detto all'utente: mai la chiave. "" se non c'è."""
    in_store = _secret_in_credential_store(entry)
    if in_store:
        result = CREDENTIAL_STORE
    elif in_store is None and _secret_in_file(entry):
        result = SECRETS_FILE_TEXT
    else:
        result = ""
    return result


def move_old_secret(entry: str) -> bool:
    """Una chiave salvata con il nome precedente del programma passa a quello nuovo (copiata, verificata, poi tolta
    dalla voce vecchia). Mai mostrata. True quando ce n'era una."""
    value = _secret_in_credential_store(entry, OLD_KEYRING_SERVICE)
    moved = False
    if value:
        if not _secret_in_credential_store(entry):
            set_secret(entry, value)
        if _secret_in_credential_store(entry) == value:
            try:
                import keyring
                keyring.delete_password(OLD_KEYRING_SERVICE, entry)
            except Exception:  # noqa: BLE001 - resta anche la copia vecchia: nessun danno
                pass
            moved = True
    return moved


def set_secret(entry: str, value: str) -> None:
    """Salva (o con value vuoto cancella) una chiave."""
    stored = False
    try:
        import keyring
        if value:
            keyring.set_password(KEYRING_SERVICE, entry, value)
        else:
            try:
                keyring.delete_password(KEYRING_SERVICE, entry)
            except Exception:  # noqa: BLE001 - non c'era
                pass
        stored = True
    except Exception as exc:  # noqa: BLE001
        log.warning("Credential store non disponibile (%s): la chiave va in %s", type(exc).__name__, _secrets_path())
    if not stored:
        data = read_json(_secrets_path())
        if not isinstance(data, dict):
            data = {}
        data[entry] = value
        write_json(_secrets_path(), data)


# --------------------------------------------------------------------------- profili AI

def _host_of(address: str) -> str:
    try:
        result = urlsplit(address).hostname or ""
    except ValueError:
        result = ""
    return result


def goes_in_store(address) -> bool:
    """Un indirizzo scritto in chiaro e non pubblico: lo tiene il credential store, non il file."""
    result = False
    if isinstance(address, str):
        written = address.strip()
        if written and written != SERVER_IN_STORE and not variable_in(written):
            result = written.rstrip("/") not in PUBLIC_SERVERS
    return result


def server_entry(profile_name: str) -> str:
    result = f"{profile_name} [server]"
    return result


@dataclass
class ProviderProfile:
    name: str
    kind: str = OLLAMA
    model: str = DEFAULT_MODELS[OLLAMA]
    # Ollama: l'indirizzo del server. Azure: l'endpoint della risorsa. OpenAI e Anthropic: fisso.
    base_url: str = OLLAMA_LOCAL_SERVER
    api_version: str = "2024-10-21"   # solo Azure; "v1" sceglie l'API /openai/v1
    temperature: float | None = 0.0   # None = non inviata (modelli di ragionamento; Anthropic non la invia mai)
    timeout: int = 300
    num_ctx: int = 16384              # solo Ollama
    api_key_variable: str = ""        # il nome della variabile con la chiave, quando il campo è $NOME
    # analisi AI degli album (Controlla la musica): al massimo tanti album e tanti brani per richiesta; un album non
    # si divide mai, quindi da solo può superare batch_tracks
    batch_albums: int = 10
    batch_tracks: int = 200
    max_failures: int = 3          # errori di fila in un controllo dopo cui l'AI smette (0 = mai)

    def key_from_variable(self) -> str:
        result = ""
        if is_variable_name(self.api_key_variable):
            result = os.environ.get(self.api_key_variable, "")
        return result

    @property
    def api_key(self) -> str:
        """La variabile nominata, altrimenti la chiave salvata nelle Impostazioni."""
        result = self.key_from_variable() or get_secret(self.name)
        return result

    @property
    def server(self) -> str:
        result = setting_value(self.base_url)
        return result

    @property
    def server_name(self) -> str:
        """Il server come lo dicono log e finestre: $NOME, un indirizzo pubblico, o nessun indirizzo."""
        written = self.base_url.strip()
        if goes_in_store(written):
            result = f"il server salvato per {self.name}"
        else:
            result = written
        return result

    def server_fingerprint(self) -> str:
        result = hashlib.sha256(self.server.encode("utf-8")).hexdigest()[:16]
        return result

    def without_server(self, text: str) -> str:
        """Un messaggio senza l'indirizzo privato (nominato da una variabile o nel credential store)."""
        result = text
        written = self.base_url.strip()
        if variable_in(written) or goes_in_store(written):
            address = self.server.strip().rstrip("/")
            for known in (address, _host_of(address)):
                if known:
                    result = result.replace(known, self.server_name)
        return result


def default_variables(kind: str) -> tuple:
    """(variabile del server, variabile della chiave) che un profilo nuovo di quel tipo nomina: quelle di
    PROFILE_VARIABLES che hanno un valore (dal file delle variabili o dal sistema), altrimenti ""."""
    server_name, key_name = PROFILE_VARIABLES.get(kind, ("", ""))
    server = server_name if server_name and os.environ.get(server_name) else ""
    key = key_name if key_name and os.environ.get(key_name) else ""
    result = (server, key)
    return result


def new_profile(name: str, kind: str = OLLAMA) -> ProviderProfile:
    """Un profilo appena aggiunto: nomina le variabili di PROFILE_VARIABLES che hanno un valore (si salva solo il nome),
    altrimenti l'indirizzo predefinito e nessuna chiave. Un profilo già salvato non cambia mai per queste."""
    server, key = default_variables(kind)
    fixed = {OLLAMA: OLLAMA_LOCAL_SERVER, AZURE: "https://<risorsa>.openai.azure.com", OPENAI: OPENAI_SERVER,
             ANTHROPIC: ANTHROPIC_SERVER}
    base_url = f"${server}" if server else fixed.get(kind, OLLAMA_LOCAL_SERVER)
    temperature = None if kind == ANTHROPIC else 0.0
    result = ProviderProfile(name=name, kind=kind, model=DEFAULT_MODELS.get(kind, ""), base_url=base_url,
                             temperature=temperature, api_key_variable=key)
    return result


def _profile_from(item: dict) -> ProviderProfile:
    known = {f.name for f in fields(ProviderProfile)}
    values = {}
    for key, value in item.items():
        if key in known:
            values[key] = value
    profile = ProviderProfile(**values)
    if profile.base_url == SERVER_IN_STORE:
        profile.base_url = get_secret(server_entry(profile.name))
        if not profile.base_url:
            log.warning("Profilo %r: il suo server non è più nel credential store", profile.name)
    return profile


def _profile_for_file(profile: ProviderProfile) -> dict:
    """Il profilo come lo contiene il file: un indirizzo privato va nel credential store. Se il credential store
    non lo restituisce, resta nel file (meglio un indirizzo in un file che nessun indirizzo)."""
    item = asdict(profile)
    entry = server_entry(profile.name)
    if goes_in_store(profile.base_url):
        set_secret(entry, profile.base_url)
        if get_secret(entry) == profile.base_url:
            item["base_url"] = SERVER_IN_STORE
        else:
            log.warning("Profilo %r: il credential store non ha tenuto il server, resta nel file", profile.name)
    elif get_secret(entry):
        set_secret(entry, "")
    return item


def load_profiles(folder: Path | None = None) -> list:
    """I profili AI salvati; nessuno quando il file manca o non è leggibile."""
    if folder is None:
        folder = config_dir()
    data = read_json(folder / PROFILES_FILE)
    result = []
    if isinstance(data, dict) and isinstance(data.get("profiles"), list):
        for item in data["profiles"]:
            if isinstance(item, dict) and isinstance(item.get("name"), str):
                result.append(_profile_from(item))
    return result


def save_profiles(profiles: list, folder: Path | None = None) -> None:
    """Prima il credential store, poi il file; poi il credential store dimentica i profili tolti."""
    if folder is None:
        folder = config_dir()
    before = load_profiles(folder)
    items = []
    for profile in profiles:
        items.append(_profile_for_file(profile))
    write_json(folder / PROFILES_FILE, {"profiles": items})
    names = {profile.name for profile in profiles}
    for old in before:
        if old.name not in names:
            set_secret(server_entry(old.name), "")
            set_secret(old.name, "")


def variables_named_in_settings(folder: Path) -> list:
    """Le variabili nominate dai server dei profili (quelle delle chiavi: environment.key_rows)."""
    result = []
    for profile in load_profiles(folder):
        name = variable_in(profile.base_url)
        if name and name not in result:
            result.append(name)
    return result


# --------------------------------------------------------------------------- importazione da myCalibreTools

def calibre_tools_folder() -> Path:
    value = _expanded(os.environ.get(CALIBRE_TOOLS_HOME_ENV_VAR, ""))
    if value and os.path.isabs(value):
        result = Path(value)
    else:
        result = Path.home() / CALIBRE_TOOLS_DIR_NAME
    return result


def calibre_tools_profiles() -> list:
    """I profili AI di myCalibreTools, con il server preso dal suo credential store; le chiavi restano dove sono
    finché non si importano (import_calibre_tools_key)."""
    data = read_json(calibre_tools_folder() / PROFILES_FILE)
    result = []
    known = {f.name for f in fields(ProviderProfile)}
    if isinstance(data, dict) and isinstance(data.get("profiles"), list):
        for item in data["profiles"]:
            if isinstance(item, dict) and isinstance(item.get("name"), str) and item.get("kind") in dict(KINDS):
                values = {}
                for key, value in item.items():
                    if key in known:
                        values[key] = value
                profile = ProviderProfile(**values)
                if profile.base_url == CALIBRE_TOOLS_SERVER_IN_STORE:
                    saved = _secret_in_credential_store(f"{profile.name} [servers]", CALIBRE_TOOLS_KEYRING_SERVICE)
                    try:
                        profile.base_url = str(json.loads(saved or "{}").get("base_url", ""))
                    except (ValueError, AttributeError):
                        profile.base_url = ""
                result.append(profile)
    return result


def import_calibre_tools_key(source_name: str, target_name: str) -> bool:
    """Copia la chiave salvata in myCalibreTools per un profilo nel credential store di questo programma, senza
    mostrarla. True quando c'era una chiave da copiare."""
    value = _secret_in_credential_store(source_name, CALIBRE_TOOLS_KEYRING_SERVICE)
    copied = bool(value)
    if copied:
        set_secret(target_name, value)
    return copied


# --------------------------------------------------------------------------- impostazioni del programma

def computer_name() -> str:
    """Il nome di questo computer (lo stesso del registro della provenienza): le cartelle della musica sono per
    computer, così con la cartella dati condivisa tra due PC ognuno ha le sue."""
    import socket
    result = socket.gethostname()
    return result


@dataclass
class AppSettings:
    library_dir: str = ""
    last_folder: str = ""           # dove si apre la finestra "Apri cartella"
    last_opened: str = ""           # l'ultima cartella mostrata, o * per le cartelle della musica: riaperta all'avvio
    last_import: str = ""
    last_export: str = ""
    scan_profile: str = ""          # il profilo AI della scansione; "" = senza AI
    scan_use_ai: bool = True
    scan_checks_off: list = field(default_factory=list)   # i controlli tolti in "Controlla la musica"
    scan_musicbrainz: bool = False  # i nomi d'artista dubbi anche su MusicBrainz (lento)
    scan_ai_flagged: bool = True    # Analisi AI solo sugli album dove le regole hanno trovato qualcosa
    scan_online: bool = False       # Verifica online tra i controlli (cataloghi: album_services)
    scan_online_flagged: bool = True   # Verifica online solo sugli album con problemi
    window_geometry: str = ""       # base64 di QMainWindow.saveGeometry
    language: str = "it"            # la lingua dell'interfaccia (i18n.LANGUAGES), dal prossimo avvio
    show_full_path: bool = False    # colonne Cartella (scheda PC) e Cartella della sorgente (iPhone): percorso completo
    album_services: list = field(default_factory=lambda: ["deezer", "apple"])   # Verifica album online, in ordine
    album_ai: bool = False          # Verifica album online: l'AI sceglie tra edizioni dubbie
    hidden_folders: list = field(default_factory=list)   # cartelle nascoste nella scheda PC (con le sottocartelle)
    preferred_folders: list = field(default_factory=list)  # con più copie di un brano, in ordine (library.preference)
    various_artists: list = field(default_factory=list)    # altri nomi che valgono come "AA.VV." (oltre a quelli fissi)
    ringtone_folder: str = ""       # la cartella delle suonerie (.m4r); "" = non ancora scelta
    ffmpeg_path: str = ""           # ffmpeg.exe (o la sua cartella) per Crea una suoneria; "" = quello nel PATH
    tagscan_path: str = ""          # Tagscan.exe (o la sua cartella) per Apri in TagScanner; "" = i posti soliti
    # le cartelle della musica di ogni computer: {nome del computer: {"folders": [cartelle], "library": cartella}}
    music_folders: dict = field(default_factory=dict)
    extra: dict = field(default_factory=dict)

    def _host_entry(self) -> dict:
        """Le cartelle della musica di questo computer ({} se non sono ancora state scelte)."""
        entry = self.music_folders.get(computer_name()) if isinstance(self.music_folders, dict) else None
        result = entry if isinstance(entry, dict) else {}
        return result

    def library_path(self) -> Path:
        """La Libreria (dove vanno Importa e Copia da iPhone a PC): quella segnata tra le cartelle della musica di
        questo computer; altrimenti library_dir; altrimenti la predefinita."""
        library = self._host_entry().get("library")
        if isinstance(library, str) and library:
            result = Path(_expanded(library))
        elif self.library_dir:
            result = Path(_expanded(self.library_dir))
        else:
            result = default_library_dir()
        return result

    def ringtone_path(self) -> Path | None:
        """La cartella delle suonerie (%NOME%, $NOME e ~ espansi); None se non è stata scelta."""
        text = _expanded(self.ringtone_folder) if self.ringtone_folder else ""
        result = Path(text) if text else None
        return result

    def music_dirs(self) -> list:
        """Le cartelle della musica di questo computer, in ordine (la prima vince tra copie uguali); senza un elenco,
        la Libreria sola."""
        folders = self._host_entry().get("folders")
        result = []
        if isinstance(folders, list):
            for folder in folders:
                if isinstance(folder, str) and folder.strip():
                    result.append(Path(_expanded(folder.strip())))
        if not result:
            result = [self.library_path()]
        return result

    def set_music_dirs(self, folders: list, library: str) -> None:
        """L'elenco delle cartelle della musica di questo computer e quale è la Libreria; library_dir la segue, così
        una versione precedente del programma trova ancora la Libreria."""
        if not isinstance(self.music_folders, dict):
            self.music_folders = {}
        self.music_folders[computer_name()] = {"folders": [str(folder) for folder in folders], "library": str(library)}
        self.library_dir = str(library)

    def other_computers(self) -> dict:
        """{nome del computer: [cartelle]} degli altri computer (si vedono in Impostazioni, non si usano qui)."""
        result = {}
        here = computer_name().lower()
        if isinstance(self.music_folders, dict):
            for name, entry in sorted(self.music_folders.items()):
                if name.lower() != here and isinstance(entry, dict) and isinstance(entry.get("folders"), list):
                    result[name] = list(entry["folders"])
        return result

    @classmethod
    def load(cls, folder: Path | None = None) -> "AppSettings":
        if folder is None:
            folder = config_dir()
        data = read_json(folder / SETTINGS_FILE)
        known = {f.name for f in fields(cls)}
        values = {}
        if isinstance(data, dict):
            for key, value in data.items():
                if key in known:
                    values[key] = value
        result = cls(**values)
        return result

    def save(self, folder: Path | None = None) -> None:
        if folder is None:
            folder = config_dir()
        try:
            write_json(folder / SETTINGS_FILE, asdict(self))
        except OSError as exc:
            log.warning("Impostazioni NON salvate in %s: %s", folder, exc)
