# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

import json
import logging
import os
import re
import zipfile
from pathlib import Path

from myeasymp3toiphone import config, env_file, environment, home_backup, startup
from myeasymp3toiphone.config import (
    ANTHROPIC, KEYRING_SERVICE, SERVER_IN_STORE, ProviderProfile, load_profiles, save_profiles, set_secret,
)


def test_private_server_and_key_never_in_file(isolated):
    profile = ProviderProfile(name="Locale", base_url="http://192.168.1.50:11434")
    save_profiles([profile])
    set_secret("Locale", "chiave-finta-123")
    text = (config.home_folder() / config.PROFILES_FILE).read_text(encoding="utf-8")
    assert "192.168.1.50" not in text and "chiave-finta-123" not in text
    assert SERVER_IN_STORE in text
    loaded = load_profiles()
    assert loaded[0].server == "http://192.168.1.50:11434"
    assert loaded[0].api_key == "chiave-finta-123"
    assert isolated.store[(KEYRING_SERVICE, "Locale")] == "chiave-finta-123"


def test_variable_names_are_saved_not_values(monkeypatch):
    monkeypatch.setenv("MY_TEST_SERVER", "http://10.0.0.9:11434")
    monkeypatch.setenv("MY_TEST_KEY", "k-finta")
    profile = ProviderProfile(name="Var", base_url="$MY_TEST_SERVER", api_key_variable="MY_TEST_KEY")
    save_profiles([profile])
    text = (config.home_folder() / config.PROFILES_FILE).read_text(encoding="utf-8")
    assert "$MY_TEST_SERVER" in text and "10.0.0.9" not in text and "k-finta" not in text
    loaded = load_profiles()[0]
    assert loaded.server == "http://10.0.0.9:11434"
    assert loaded.api_key == "k-finta"
    assert loaded.without_server("errore su http://10.0.0.9:11434/api") == "errore su $MY_TEST_SERVER/api"


def test_removed_profile_forgets_its_secrets(isolated):
    save_profiles([ProviderProfile(name="Via", base_url="http://10.1.1.1")])
    set_secret("Via", "x")
    save_profiles([])
    assert (KEYRING_SERVICE, "Via") not in isolated.store
    assert (KEYRING_SERVICE, "Via [server]") not in isolated.store


def test_import_from_calibre_tools(isolated):
    folder = config.calibre_tools_folder()
    folder.mkdir(parents=True)
    items = [{"name": "Claude", "kind": ANTHROPIC, "model": "claude-opus-5-5", "base_url": config.ANTHROPIC_SERVER,
              "extra_params": [], "requests_at_once": 1},
             {"name": "Gpu", "kind": "ollama", "model": "m", "base_url": config.CALIBRE_TOOLS_SERVER_IN_STORE}]
    (folder / config.PROFILES_FILE).write_text(json.dumps({"profiles": items}), encoding="utf-8")
    isolated.store[(config.CALIBRE_TOOLS_KEYRING_SERVICE, "Claude")] = "chiave-di-calibre"
    isolated.store[(config.CALIBRE_TOOLS_KEYRING_SERVICE, "Gpu [servers]")] = json.dumps({"base_url": "http://10.2.2.2"})
    found = config.calibre_tools_profiles()
    assert [p.name for p in found] == ["Claude", "Gpu"]
    assert found[1].base_url == "http://10.2.2.2"
    assert config.import_calibre_tools_key("Claude", "Claude importato")
    assert isolated.store[(KEYRING_SERVICE, "Claude importato")] == "chiave-di-calibre"


def test_environment_report_never_shows_values(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-finta-segreta")
    text = environment.report_text()
    assert "sk-finta-segreta" not in text
    assert re.search(r"ANTHROPIC_API_KEY\s+= impostata \(sistema\)", text)


def test_variables_list_matches_code():
    """Ogni os.environ.get("NOME") del codice è in environment.VARIABLES (o è del build)."""
    package = Path(environment.__file__).parent
    names = set()
    for path in package.rglob("*.py"):
        names.update(re.findall(r"os\.environ\.get\(\"([A-Z_][A-Z0-9_]*)\"", path.read_text(encoding="utf-8")))
    assert names <= set(environment.VARIABLES) | set(environment.BUILD_VARIABLES)


def test_first_start_creates_env_file_and_record(isolated):
    startup.prepare()
    home = config.home_folder()
    assert (home / env_file.ENV_FILE_NAME).is_file()
    assert home_backup.read_record(home)["data_format"] == str(home_backup.DATA_FORMAT)
    assert not (home / home_backup.BACKUP_FOLDER).exists()


def test_env_file_is_loaded_before_logging_reads_it(isolated):
    """L'ordine: il file delle variabili prima di chi legge una variabile (il livello del log)."""
    home = config.config_dir()
    (home / env_file.ENV_FILE_NAME).write_text("MYEASYMP3TOIPHONE_LOG_LEVEL=WARNING\n", encoding="utf-8")
    startup.prepare()
    assert environment.log_level() == logging.WARNING
    assert env_file.source("MYEASYMP3TOIPHONE_LOG_LEVEL") == "file"


def test_names_in_use_are_added_to_env_file(isolated):
    save_profiles([ProviderProfile(name="C", kind=ANTHROPIC, api_key_variable="MY_TEST_CLAUDE_KEY",
                                   base_url=config.ANTHROPIC_SERVER)])
    startup.prepare()
    text = (config.home_folder() / env_file.ENV_FILE_NAME).read_text(encoding="utf-8")
    assert "MY_TEST_CLAUDE_KEY=\n" in text


def test_backup_when_data_format_rises(isolated, monkeypatch):
    home = config.config_dir()
    home_backup.write_record(home, "0.1.3")
    (home / env_file.ENV_FILE_NAME).write_text("MY_TEST_A=1\n", encoding="utf-8")
    (home / "Backup").mkdir()
    (home / "Backup" / "vecchio.zip").write_bytes(b"x")
    (home / "sub" / "Backup").mkdir(parents=True)
    (home / "sub" / "Backup" / "dentro.txt").write_text("y", encoding="utf-8")
    monkeypatch.setattr(home_backup, "DATA_FORMAT", home_backup.DATA_FORMAT + 1)
    target = home_backup.backup_if_needed(home, "0.2.0")
    assert target is not None and target.name.startswith("myEasyMP3toIPhone-home-for-0.1.3-")
    with zipfile.ZipFile(target) as zipped:
        names = set(zipped.namelist())
        record = zipped.read(home_backup.RECORD_FILE_NAME).decode("utf-8")
    assert env_file.ENV_FILE_NAME in names
    assert "sub/Backup/dentro.txt" in names
    assert not any(name.startswith("Backup/") for name in names)
    assert "version=0.1.3" in record
    assert home_backup.backup_if_needed(home, "0.2.0") is None
    assert not list((home / "Backup").glob("*.tmp"))


def test_no_backup_for_new_home(isolated):
    home = config.config_dir()
    assert home_backup.backup_if_needed(home, "0.1.0") is None


def test_old_registry_settings_are_migrated(isolated, monkeypatch):
    from PySide6.QtCore import QSettings
    monkeypatch.setattr(startup, "OLD_QSETTINGS", ("CopiaStiMP3Test", "CopiaStiMP3Test"))
    old = QSettings("CopiaStiMP3Test", "CopiaStiMP3Test")
    old.setValue("library_dir", "C:\\Musica\\Prova")
    old.sync()
    try:
        assert startup.migrate_old_settings(config.config_dir())
        assert config.AppSettings.load().library_dir == "C:\\Musica\\Prova"
    finally:
        old.clear()
        old.sync()
    assert os.environ.get("MYEASYMP3TOIPHONE_HOME")


def test_default_scan_profile_is_local_ollama(isolated, monkeypatch):
    from myeasymp3toiphone import ai
    monkeypatch.setattr(ai, "local_ollama_models", lambda *a, **k: ["llama3.2:latest", "gemma4:e4b"])
    startup.prepare()
    profiles = load_profiles()
    assert [(p.name, p.kind, p.base_url, p.model) for p in profiles] == [
        (config.DEFAULT_SCAN_PROFILE, "ollama", config.OLLAMA_LOCAL_SERVER, "gemma4:e4b")]
    assert config.AppSettings.load().scan_profile == config.DEFAULT_SCAN_PROFILE


def test_default_profile_never_overrides_choices(isolated):
    from myeasymp3toiphone import ai
    home = config.config_dir()
    save_profiles([ProviderProfile(name="Mio", kind=ANTHROPIC, base_url=config.ANTHROPIC_SERVER)])
    settings = config.AppSettings(scan_profile="Mio")
    settings.save()
    assert not ai.ensure_default_profile(home)
    assert [p.name for p in load_profiles()] == ["Mio"]
    save_profiles([])  # tutti i profili tolti: non torna
    assert not ai.ensure_default_profile(home)


def test_choose_local_model():
    from myeasymp3toiphone import ai
    assert ai.choose_local_model(["x:1", "qwen3.5:4b"]) == "qwen3.5:4b"
    assert ai.choose_local_model(["x:1"]) == "x:1"
    assert ai.choose_local_model([]) == config.DEFAULT_MODELS["ollama"]


def test_new_profiles_name_the_same_variables_as_mycalibretools(monkeypatch):
    plain = {kind: config.new_profile("p", kind) for kind, _label in config.KINDS}
    assert plain["ollama"].base_url == config.OLLAMA_LOCAL_SERVER and plain["ollama"].api_key_variable == ""
    assert plain["azure"].api_key_variable == "" and not plain["azure"].base_url.startswith("$")
    for name in ("OLLAMA_API_BASE", "OLLAMA_API_KEY", "AZURE_FOUNDRY_EP", "AZURE_FOUNDRY_KEY", "OPENAI_API_KEY",
                 "ANTHROPIC_API_KEY"):
        monkeypatch.setenv(name, "valore-finto")
    named = {kind: config.new_profile("p", kind) for kind, _label in config.KINDS}
    assert (named["ollama"].base_url, named["ollama"].api_key_variable) == ("$OLLAMA_API_BASE", "OLLAMA_API_KEY")
    assert (named["azure"].base_url, named["azure"].api_key_variable) == ("$AZURE_FOUNDRY_EP", "AZURE_FOUNDRY_KEY")
    assert (named["openai"].base_url, named["openai"].api_key_variable) == (config.OPENAI_SERVER, "OPENAI_API_KEY")
    assert named["anthropic"].api_key_variable == "ANTHROPIC_API_KEY" and named["anthropic"].temperature is None


def test_profile_variables_are_listed_and_in_template():
    values, _bad = env_file.parse_lines(env_file.TEMPLATE_PATH.read_text(encoding="utf-8-sig").splitlines())
    for server_name, key_name in config.PROFILE_VARIABLES.values():
        for name in (server_name, key_name):
            if name:
                assert name in environment.VARIABLES
                assert name in values
    assert "OLLAMA_FALLBACK_API_BASE" in values


def test_settings_kind_change_swaps_default_variables(monkeypatch):
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui.settings_dialog import SettingsDialog
    for name in ("OLLAMA_API_KEY", "AZURE_FOUNDRY_EP", "AZURE_FOUNDRY_KEY"):
        monkeypatch.setenv(name, "valore-finto")
    _app = QApplication.instance() or QApplication([])
    dialog = SettingsDialog(config.AppSettings())
    dialog._add_profile()
    assert dialog.f_key.text() == "$OLLAMA_API_KEY"
    dialog.f_kind.setCurrentIndex(dialog.f_kind.findData("azure"))
    assert (dialog.f_url.text(), dialog.f_key.text()) == ("$AZURE_FOUNDRY_EP", "$AZURE_FOUNDRY_KEY")
    dialog.f_kind.setCurrentIndex(dialog.f_kind.findData("anthropic"))
    assert (dialog.f_url.text(), dialog.f_key.text()) == (config.ANTHROPIC_SERVER, "")
    dialog.reject()


def test_migration_from_old_name(tmp_path, monkeypatch, isolated):
    """Da myCopiaStiMP3 a myEasyMP3toIPhone: cartella dati, copia di sicurezza, .env, impostazioni, chiavi."""
    import json
    from pathlib import Path
    fake_home = tmp_path / "utente"
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    monkeypatch.delenv("MYEASYMP3TOIPHONE_HOME", raising=False)
    old = fake_home / ".myCopiaStiMP3"
    old.mkdir(parents=True)
    (old / "myCopiaStiMP3.home.txt").write_text("version=0.1.1-dev\ndata_format=1\n", encoding="utf-8")
    (old / "myCopiaStiMP3.env").write_text("MYCOPIASTIMP3_LOG_LEVEL=WARNING\n", encoding="utf-8")
    (old / "ai_profiles.json").write_text(json.dumps({"profiles": [{"name": "Claude", "kind": "anthropic",
                                                                    "base_url": config.ANTHROPIC_SERVER}]}),
                                          encoding="utf-8")
    (old / "settings.json").write_text(json.dumps({"last_opened": "X:/musica"}), encoding="utf-8")
    isolated.store[(config.OLD_KEYRING_SERVICE, "Claude")] = "chiave-finta-vecchia"
    startup.prepare()
    new = fake_home / ".myEasyMP3toIPhone"
    assert new.is_dir() and not old.exists()
    backups = list((new / "Backup").glob("myEasyMP3toIPhone-home-for-0.1.1-dev-*.zip"))
    assert len(backups) == 1
    with zipfile.ZipFile(backups[0]) as zipped:
        assert "myCopiaStiMP3.env" in zipped.namelist()   # la copia ha i file come erano
    env_text = (new / "myEasyMP3toIPhone.env").read_text(encoding="utf-8")
    assert env_text.startswith("MYEASYMP3TOIPHONE_LOG_LEVEL=WARNING") and not (new / "myCopiaStiMP3.env").exists()
    assert environment.log_level() == logging.WARNING
    saved = config.AppSettings.load(new)
    assert saved.last_opened == "X:/musica"
    assert isolated.store[(config.KEYRING_SERVICE, "Claude")] == "chiave-finta-vecchia"
    assert (config.OLD_KEYRING_SERVICE, "Claude") not in isolated.store
    assert home_backup.read_record(new)["data_format"] == str(home_backup.DATA_FORMAT)
    startup.prepare()   # la seconda volta non fa niente di nuovo
    assert len(list((new / "Backup").glob("*.zip"))) == 1


def test_settings_show_saved_profile_unchanged(monkeypatch):
    """Selezionare un profilo salvato non gli aggiunge i valori predefiniti del tipo (es. $OLLAMA_API_KEY)."""
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from myeasymp3toiphone.gui.settings_dialog import SettingsDialog
    monkeypatch.setenv("OLLAMA_API_KEY", "valore-finto")
    monkeypatch.setenv("OLLAMA_API_BASE", "http://server-finto:11434")
    save_profiles([ProviderProfile(name="Locale", base_url=config.OLLAMA_LOCAL_SERVER)])
    _app = QApplication.instance() or QApplication([])
    dialog = SettingsDialog(config.AppSettings())
    assert dialog.f_key.text() == "" and dialog.f_url.text() == config.OLLAMA_LOCAL_SERVER
    dialog.accept()
    saved = load_profiles()[0]
    assert saved.api_key_variable == "" and saved.base_url == config.OLLAMA_LOCAL_SERVER
