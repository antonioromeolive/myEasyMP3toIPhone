# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le Impostazioni: la cartella della Libreria, l'AI della scansione e i profili AI (come in myCalibreTools: ogni
chiave o indirizzo accetta $NOME; scritti in chiaro vanno nella Gestione credenziali di Windows)."""

from __future__ import annotations

import copy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)

from .. import environment
from ..i18n import DEFAULT_LANGUAGE, LANGUAGES, tr
from ..ai import AIError, connection_test, make_provider
from ..config import (
    ANTHROPIC, ANTHROPIC_SERVER, AZURE, DEFAULT_MODELS, KINDS, OLLAMA, OLLAMA_LOCAL_SERVER, OPENAI, OPENAI_SERVER,
    PROFILE_VARIABLES, AppSettings, as_written, calibre_tools_folder, calibre_tools_profiles, default_variables,
    get_secret, import_calibre_tools_key, literal_text, load_profiles, new_profile, save_profiles, set_secret,
    variable_in,
)
from .theme import mark_danger

NO_AI = "(nessuna: solo le regole)"
VARIABLE_TIP = ("$NOME legge il valore dalla variabile d'ambiente NOME: si salva solo il nome. La variabile si imposta "
                "nel file\n%USERPROFILE%\\.myEasyMP3toIPhone\\myEasyMP3toIPhone.env (vince sul sistema) o nelle variabili di "
                "Windows.\nRiavvia il programma dopo averla cambiata.")


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Impostazioni")
        self.resize(900, 600)
        self.settings = settings
        self.profiles = load_profiles()
        self.keys = {}
        for profile in self.profiles:
            self.keys[profile.name] = get_secret(profile.name)
        self.removed = []
        self._current = None
        self._loading = False

        tabs = QTabWidget()
        tabs.addTab(self._build_general_tab(), "Generale")
        tabs.addTab(self._build_profiles_tab(), "Profili AI")
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)
        self._refresh_list()
        if self.profiles:
            self.list.setCurrentRow(0)
        self._fill_scan_profiles()

    # ------------------------------------------------------------------ generale

    def _build_general_tab(self) -> QWidget:
        self.g_library = QLineEdit(str(self.settings.library_path()))
        browse = QPushButton("Sfoglia…")
        browse.clicked.connect(self._browse_library)
        library_row = QHBoxLayout()
        library_row.addWidget(self.g_library, 1)
        library_row.addWidget(browse)
        self.g_scan_profile = QComboBox()
        self.g_language = QComboBox()
        for code, label in LANGUAGES.items():
            self.g_language.addItem(label, code)
        self.g_language.setCurrentIndex(max(0, self.g_language.findData(self.settings.language)))
        self.g_language.setToolTip("Vale dal prossimo avvio del programma. Il README resta in italiano.")
        note = QLabel("La scansione usa sempre le regole locali (gratuite). Con un profilo AI, l'AI riceve una tabella "
                      "degli album (artisti, titoli, numeri di traccia, nomi delle cartelle) e propone altri problemi e "
                      "le correzioni. Con un'AI nel cloud questi dati escono dal computer; con Ollama restano qui.")
        note.setWordWrap(True)
        note.setStyleSheet("color: gray")
        form = QFormLayout()
        form.addRow("Cartella della Libreria", library_row)
        form.addRow("AI della scansione", self.g_scan_profile)
        form.addRow("Lingua dell'interfaccia", self.g_language)
        form.addRow(note)
        widget = QWidget()
        widget.setLayout(form)
        return widget

    def _browse_library(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Cartella della Libreria", self.g_library.text())
        if folder:
            self.g_library.setText(folder)

    def _fill_scan_profiles(self) -> None:
        chosen = self.g_scan_profile.currentText() or self.settings.scan_profile
        self.g_scan_profile.clear()
        self.g_scan_profile.addItem(tr(NO_AI))
        for profile in self.profiles:
            self.g_scan_profile.addItem(profile.name)
        index = self.g_scan_profile.findText(chosen)
        self.g_scan_profile.setCurrentIndex(max(0, index))

    # ------------------------------------------------------------------ profili

    def _build_profiles_tab(self) -> QWidget:
        self.list = QListWidget()
        self.list.currentRowChanged.connect(self._select_profile)
        add = QPushButton("Aggiungi")
        duplicate = QPushButton("Duplica")
        remove = QPushButton("Elimina")
        mark_danger(remove)
        import_button = QPushButton("Importa da myCalibreTools…")
        import_button.setToolTip(f"Copia i profili AI di myCalibreTools ({calibre_tools_folder()}), con le chiavi "
                                 "salvate nella Gestione credenziali")
        add.clicked.connect(self._add_profile)
        duplicate.clicked.connect(self._duplicate_profile)
        remove.clicked.connect(self._remove_profile)
        import_button.clicked.connect(self._import_calibre_tools)
        row = QHBoxLayout()
        for button in (add, duplicate, remove):
            row.addWidget(button)
        left = QVBoxLayout()
        left.addWidget(self.list)
        left.addLayout(row)
        left.addWidget(import_button)

        self.f_name = QLineEdit()
        self.f_kind = QComboBox()
        for kind, label in KINDS:
            self.f_kind.addItem(label, kind)
        self.f_kind.currentIndexChanged.connect(self._kind_changed)
        self.l_url = QLabel()
        self.f_url = QLineEdit()
        self.f_url.setToolTip(VARIABLE_TIP + "\nUn indirizzo scritto qui va nella Gestione credenziali di Windows, "
                              "non in un file.")
        self.l_model = QLabel()
        self.f_model = QComboBox()
        self.f_model.setEditable(True)
        self.b_models = QPushButton("Aggiorna modelli")
        self.b_models.clicked.connect(self._refresh_models)
        model_row = QHBoxLayout()
        model_row.addWidget(self.f_model, 1)
        model_row.addWidget(self.b_models)
        self.f_key = QLineEdit()
        self.f_key.setEchoMode(QLineEdit.Password)
        self.f_key.setToolTip(VARIABLE_TIP + "\nUna chiave scritta qui va nella Gestione credenziali di Windows; se "
                              "inizia davvero con $, scrivi $$.")
        self.f_key.textChanged.connect(self._key_typed)
        self.f_version = QLineEdit()
        self.f_temp_on = QCheckBox("Invia la temperatura")
        self.f_temp = QDoubleSpinBox()
        self.f_temp.setRange(0, 2)
        self.f_temp.setSingleStep(0.1)
        self.f_temp_on.toggled.connect(self.f_temp.setEnabled)
        temp_row = QHBoxLayout()
        temp_row.addWidget(self.f_temp_on)
        temp_row.addWidget(self.f_temp, 1)
        self.f_timeout = QSpinBox()
        self.f_timeout.setRange(10, 3600)
        self.f_timeout.setSuffix(" s")
        self.f_ctx = QSpinBox()
        self.f_ctx.setRange(2048, 1_048_576)
        self.f_ctx.setSingleStep(2048)
        self.test_button = QPushButton("Prova la connessione")
        self.test_button.clicked.connect(self._test)
        self.hint = QLabel()
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet("color: gray")

        form = QFormLayout()
        form.addRow("Nome", self.f_name)
        form.addRow("Tipo", self.f_kind)
        form.addRow(self.l_url, self.f_url)
        form.addRow(self.l_model, model_row)
        form.addRow("Chiave API", self.f_key)
        form.addRow("Versione API", self.f_version)
        form.addRow("Temperatura", temp_row)
        form.addRow("Timeout", self.f_timeout)
        form.addRow("Contesto (Ollama)", self.f_ctx)
        self.fields = QWidget()
        self.fields.setLayout(form)
        right = QVBoxLayout()
        right.addWidget(self.fields)
        right.addWidget(self.test_button)
        right.addWidget(self.hint)
        right.addStretch(1)
        columns = QHBoxLayout()
        columns.addLayout(left, 1)
        columns.addLayout(right, 2)
        widget = QWidget()
        widget.setLayout(columns)
        return widget

    def _refresh_list(self) -> None:
        self.list.blockSignals(True)
        self.list.clear()
        for profile in self.profiles:
            self.list.addItem(profile.name)
        self.list.blockSignals(False)
        has = bool(self.profiles)
        self.fields.setEnabled(has)
        self.test_button.setEnabled(has)

    def _select_profile(self, row: int) -> None:
        self._store_current()
        if 0 <= row < len(self.profiles):
            self._current = self.profiles[row]
        else:
            self._current = None
        profile = self._current
        if profile is not None:
            self._loading = True
            self.f_name.setText(profile.name)
            self.f_kind.setCurrentIndex(max(0, self.f_kind.findData(profile.kind)))
            self.f_url.setText(profile.base_url)
            self.f_model.clear()
            self.f_model.setEditText(profile.model)
            if profile.api_key_variable:
                self.f_key.setText(f"${profile.api_key_variable}")
            else:
                self.f_key.setText(as_written(self.keys.get(profile.name, "")))
            self.f_version.setText(profile.api_version)
            self.f_temp_on.setChecked(profile.temperature is not None)
            self.f_temp.setValue(profile.temperature or 0.0)
            self.f_temp.setEnabled(profile.temperature is not None)
            self.f_timeout.setValue(profile.timeout)
            self.f_ctx.setValue(profile.num_ctx)
            # ancora in caricamento: un profilo salvato si mostra com'è; i valori predefiniti del tipo (server,
            # $NOME della chiave) valgono solo quando l'utente cambia il tipo
            self._kind_changed()
            self._loading = False

    def _key_typed(self, text: str) -> None:
        """Un nome si vede, una chiave no."""
        if variable_in(text):
            self.f_key.setEchoMode(QLineEdit.Normal)
        else:
            self.f_key.setEchoMode(QLineEdit.Password)

    def _store_current(self) -> None:
        profile = self._current
        if profile is not None and not self._loading:
            old_name = profile.name
            new_name = self.f_name.text().strip() or old_name
            if new_name != old_name and new_name in {p.name for p in self.profiles}:
                new_name = old_name
            profile.name = new_name
            profile.kind = self.f_kind.currentData()
            profile.base_url = self.f_url.text().strip()
            profile.model = self.f_model.currentText().strip()
            profile.api_key_variable = variable_in(self.f_key.text())
            profile.api_version = self.f_version.text().strip()
            if self.f_temp_on.isChecked() and profile.kind != ANTHROPIC:
                profile.temperature = self.f_temp.value()
            else:
                profile.temperature = None
            profile.timeout = self.f_timeout.value()
            profile.num_ctx = self.f_ctx.value()
            if old_name != profile.name:
                self.keys[profile.name] = self.keys.get(old_name, "")
                self.keys[old_name] = ""
                self.removed.append(old_name)
            if not profile.api_key_variable:
                self.keys[profile.name] = literal_text(self.f_key.text())
            row = self.profiles.index(profile)
            if self.list.item(row) is not None:
                self.list.item(row).setText(profile.name)

    def _kind_changed(self) -> None:
        kind = self.f_kind.currentData()
        azure = kind == AZURE
        local = kind == OLLAMA
        fixed = kind in (OPENAI, ANTHROPIC)
        self.l_url.setText("Endpoint" if azure or fixed else "Server")
        self.l_model.setText("Deployment" if azure else "Modello")
        self.f_url.setEnabled(not fixed)
        self.f_version.setEnabled(azure)
        self.f_ctx.setEnabled(local)
        self.b_models.setEnabled(local)
        self.f_temp_on.setEnabled(kind != ANTHROPIC)
        if local:
            self.f_key.setPlaceholderText("nessuna: solo per un server che la chiede, es. $OLLAMA_API_KEY")
        else:
            self.f_key.setPlaceholderText("la chiave, oppure $NOME di una variabile d'ambiente")
        if not self._loading and self._current is not None:
            # i $NOME predefiniti di un altro tipo (PROFILE_VARIABLES) lasciano il posto a quelli di questo tipo
            other_servers = set()
            other_keys = set()
            for other_kind, (server_name, key_name) in PROFILE_VARIABLES.items():
                if other_kind != kind:
                    other_servers.add(server_name)
                    other_keys.add(key_name)
            if variable_in(self.f_url.text()) in other_servers - {""}:
                self.f_url.setText("")
            if variable_in(self.f_key.text()) in other_keys - {""}:
                self.f_key.setText("")
            server_variable, key_variable = default_variables(kind)
            if kind == OPENAI:
                self.f_url.setText(OPENAI_SERVER)
            elif kind == ANTHROPIC:
                self.f_url.setText(ANTHROPIC_SERVER)
                self.f_temp_on.setChecked(False)
            elif server_variable and not variable_in(self.f_url.text()):
                self.f_url.setText(f"${server_variable}")
            elif azure and "openai.azure" not in self.f_url.text() and not variable_in(self.f_url.text()):
                self.f_url.setText("https://<risorsa>.openai.azure.com")
            elif kind == OLLAMA and not self.f_url.text().strip():
                self.f_url.setText(OLLAMA_LOCAL_SERVER)
            if key_variable and not self.f_key.text().strip():
                self.f_key.setText(f"${key_variable}")
            if not self.f_model.currentText().strip():
                self.f_model.setEditText(DEFAULT_MODELS.get(kind, ""))
        hints = {
            OLLAMA: "Ollama: l'indirizzo del server (predefinito http://localhost:11434) o $OLLAMA_API_BASE. "
                    "\"Aggiorna modelli\" elenca i modelli installati. Con Ollama i dati restano sul computer.",
            AZURE: "Azure OpenAI: l'endpoint della risorsa ($AZURE_FOUNDRY_EP) e il nome del deployment, la chiave "
                   "$AZURE_FOUNDRY_KEY (gli stessi nomi di myCalibreTools); versione API per esempio "
                   "2024-10-21, oppure v1. Togli \"Invia la temperatura\" per i modelli di ragionamento.",
            OPENAI: "OpenAI: il nome del modello e la chiave. L'endpoint è api.openai.com.",
            ANTHROPIC: "Anthropic (Claude): il nome del modello (predefinito claude-opus-5-5) e la chiave. La "
                       "temperatura non si invia: i modelli attuali non la accettano.",
        }
        self.hint.setText(hints.get(kind, ""))

    def _refresh_models(self) -> None:
        self._store_current()
        if self._current is not None:
            try:
                models = make_provider(self._current).list_models()
                current = self.f_model.currentText()
                self.f_model.clear()
                self.f_model.addItems(models)
                self.f_model.setEditText(current or (models[0] if models else ""))
            except AIError as exc:
                QMessageBox.warning(self, "Modelli", str(exc))

    def _test(self) -> None:
        self._store_current()
        profile = self._current
        if profile is not None:
            set_secret(profile.name, self.keys.get(profile.name, ""))
            self.setCursor(Qt.WaitCursor)
            self.test_button.setText("Prova in corso…")
            self.test_button.setEnabled(False)
            QApplication.processEvents()
            try:
                good, message = connection_test(profile)
            finally:
                self.unsetCursor()
                self.test_button.setText("Prova la connessione")
                self.test_button.setEnabled(True)
            if environment.uses_a_key(profile):
                message += f"\n\nChiave usata: {environment.key_source(profile)}."
            if good:
                QMessageBox.information(self, f"Prova: {profile.name}", message)
            else:
                QMessageBox.warning(self, f"Prova: {profile.name}", message)

    def _unique_name(self, base: str) -> str:
        names = {profile.name for profile in self.profiles}
        name = base
        number = 2
        while name in names:
            name = f"{base} {number}"
            number += 1
        return name

    def _add_profile(self) -> None:
        self._store_current()
        self.profiles.append(new_profile(self._unique_name("Nuovo profilo")))
        self._refresh_list()
        self.list.setCurrentRow(len(self.profiles) - 1)
        self._fill_scan_profiles()

    def _duplicate_profile(self) -> None:
        self._store_current()
        if self._current is not None:
            profile = copy.deepcopy(self._current)
            name = self._unique_name(profile.name)
            self.keys[name] = self.keys.get(profile.name, "")
            profile.name = name
            self.profiles.append(profile)
            self._refresh_list()
            self.list.setCurrentRow(len(self.profiles) - 1)
            self._fill_scan_profiles()

    def _remove_profile(self) -> None:
        row = self.list.currentRow()
        if 0 <= row < len(self.profiles):
            self._current = None
            removed = self.profiles.pop(row)
            self.keys[removed.name] = ""
            self._refresh_list()
            if self.profiles:
                self.list.setCurrentRow(min(row, len(self.profiles) - 1))
            self._fill_scan_profiles()

    def _import_calibre_tools(self) -> None:
        self._store_current()
        found = calibre_tools_profiles()
        if not found:
            QMessageBox.information(self, "Importa da myCalibreTools",
                                    f"Nessun profilo AI trovato in {calibre_tools_folder()}.")
        else:
            imported = []
            with_key = 0
            for profile in found:
                source_name = profile.name
                profile.name = self._unique_name(profile.name)
                if not profile.api_key_variable and import_calibre_tools_key(source_name, profile.name):
                    self.keys[profile.name] = get_secret(profile.name)
                    with_key += 1
                if profile.kind == ANTHROPIC:
                    profile.temperature = None
                self.profiles.append(profile)
                imported.append(profile.name)
            self._refresh_list()
            self.list.setCurrentRow(len(self.profiles) - 1)
            self._fill_scan_profiles()
            QMessageBox.information(self, "Importa da myCalibreTools",
                                    f"Importati {len(imported)} profili: {', '.join(imported)}.\n"
                                    f"Chiavi copiate nella Gestione credenziali: {with_key}.\n"
                                    "I profili che leggono una chiave da $NOME continuano a leggerla da lì.")

    # ------------------------------------------------------------------ salvataggio

    def accept(self) -> None:
        self._store_current()
        save_profiles(self.profiles)
        names = {profile.name for profile in self.profiles}
        for name, value in self.keys.items():
            if name in names:
                set_secret(name, value)
            else:
                set_secret(name, "")
        library = self.g_library.text().strip()
        self.settings.library_dir = library
        self.settings.language = self.g_language.currentData() or DEFAULT_LANGUAGE
        chosen = self.g_scan_profile.currentText()
        if chosen == tr(NO_AI):
            self.settings.scan_profile = ""
        else:
            self.settings.scan_profile = chosen
        self.settings.save()
        super().accept()
