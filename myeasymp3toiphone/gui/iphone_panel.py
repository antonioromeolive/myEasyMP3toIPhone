"""Scheda iPhone: collegamento, invio di musica alle app e importazione dalla libreria Musica."""

import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .. import iphone, itunes
from ..config import config_dir
from ..library import copy_organized, load_tracks, scan_folder, target_relative_path
from ..overlay import path_key
from ..scan import DEVICE_SAME, device_status, remote_index
from ..tags import prepare_copy, protect_folder

REMOTE_MUSIC_FOLDER = "Musica"
DEVICE_POLL_MS = 3000   # ogni quanto si guarda se è stato collegato (o scollegato) un iPhone
IMPORT_TEMP_FOLDER = ".importazione_iphone"

INFO_TEXT = (
    "<b>Come funziona.</b> Due strade per mettere la musica sull'iPhone; i file del PC non cambiano mai, vanno "
    "sempre copie con i tag modificati.<br>"
    "• <b>Dal PC all'iPhone</b>: direttamente via cavo, dentro un'app con condivisione file, consigliata "
    "<b>VLC</b> (gratuita), in cartelle Artista/Album; i file si vedono anche in <i>File</i> → <i>Sul mio iPhone</i>.<br>"
    "• <b>App Musica dell'iPhone (tramite iTunes)</b>: le copie vanno in iTunes, che le sincronizza nell'app "
    "<i>Musica</i> (Apple lo permette solo così).<br>"
    "In senso inverso puoi <b>importare sul PC la musica dell'app Musica</b>; i brani protetti di Apple Music non sono "
    "copiabili."
)


def _format_size(size: int) -> str:
    if size >= 1024 * 1024:
        result = f"{size / (1024 * 1024):.1f} MB"
    else:
        result = f"{max(size, 0) // 1024} KB"
    return result


class IPhonePanel(QWidget):
    def __init__(self, window) -> None:
        super().__init__(window)
        self._window = window
        self._apps = []
        self._connected = False

        self._status = QLabel("iPhone non collegato")
        self._status.setStyleSheet("font-size: 15px; font-weight: bold;")
        self._connect_button = QPushButton("Collega iPhone")
        self._connect_button.clicked.connect(self.connect_device)
        top = QHBoxLayout()
        top.addWidget(self._status, 1)
        top.addWidget(self._connect_button)

        info = QLabel(INFO_TEXT)
        info.setWordWrap(True)
        info.setTextFormat(Qt.RichText)
        info.setStyleSheet("background: palette(alternate-base); padding: 8px; border-radius: 4px;")

        # --- PC -> iPhone
        self._app_combo = QComboBox()
        self._app_combo.currentIndexChanged.connect(self._app_changed)
        self._send_selection_button = QPushButton("Invia i brani selezionati nella Libreria")
        self._send_selection_button.clicked.connect(self._send_selection)
        self._send_folder_button = QPushButton("Invia una cartella…")
        self._send_folder_button.clicked.connect(self._send_folder)
        app_row = QHBoxLayout()
        app_row.addWidget(QLabel("App di destinazione:"))
        app_row.addWidget(self._app_combo, 1)
        send_row = QHBoxLayout()
        send_row.addWidget(self._send_selection_button)
        send_row.addWidget(self._send_folder_button)
        send_row.addStretch(1)
        send_box = QGroupBox("Dal PC all'iPhone")
        send_layout = QVBoxLayout(send_box)
        send_layout.addLayout(app_row)
        music_note = QLabel("L'app <b>Musica</b> di Apple non compare qui: per lei c'è il riquadro <i>App Musica "
                            "dell'iPhone (tramite iTunes)</i> qui sotto.")
        music_note.setWordWrap(True)
        music_note.setTextFormat(Qt.RichText)
        music_note.setStyleSheet("color: gray")
        send_layout.addWidget(music_note)
        send_layout.addLayout(send_row)

        # --- file presenti nell'app
        self._files_view = QTreeWidget()
        self._files_view.setHeaderLabels(["File nell'app", "Dimensione"])
        self._files_view.setRootIsDecorated(False)
        self._files_view.setSelectionMode(QTreeWidget.ExtendedSelection)
        self._files_view.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self._refresh_button = QPushButton("Aggiorna elenco")
        self._refresh_button.clicked.connect(self._refresh_files)
        self._download_button = QPushButton("Copia sul PC…")
        self._download_button.clicked.connect(self._download_selected)
        self._delete_button = QPushButton("Elimina dall'iPhone")
        self._delete_button.clicked.connect(self._delete_selected)
        files_buttons = QHBoxLayout()
        files_buttons.addWidget(self._refresh_button)
        files_buttons.addWidget(self._download_button)
        files_buttons.addStretch(1)
        files_buttons.addWidget(self._delete_button)
        files_box = QGroupBox("File presenti nell'app scelta")
        files_layout = QVBoxLayout(files_box)
        files_layout.addWidget(self._files_view)
        files_layout.addLayout(files_buttons)

        # --- app Musica -> PC
        self._import_button = QPushButton("Importa nella Libreria del PC la musica dell'app Musica")
        self._import_button.clicked.connect(self._import_music_library)
        import_box = QGroupBox("Dall'iPhone al PC")
        import_layout = QHBoxLayout(import_box)
        import_layout.addWidget(self._import_button)
        import_layout.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(info)
        layout.addWidget(send_box)
        layout.addWidget(self._build_itunes_box())
        layout.addWidget(files_box, 1)
        layout.addWidget(import_box)
        self._update_enabled()
        self._auto_tried = False      # già tentato il collegamento automatico per questo iPhone collegato
        self._driver_warned = False
        self._poll = QTimer(self)
        self._poll.setInterval(DEVICE_POLL_MS)
        self._poll.timeout.connect(self._check_device)
        self._poll.start()
        QTimer.singleShot(1500, self._check_device)

    # ------------------------------------------------------------------ rilevamento automatico

    def _check_device(self) -> None:
        """Ogni pochi secondi: un iPhone appena collegato si collega da solo (la prima volta l'iPhone chiede
        "Autorizza"), uno scollegato si segna come tale. Senza driver Apple lo dice una volta."""
        present = iphone.device_present()
        if present is None:
            if not self._driver_warned:
                self._driver_warned = True
                self._status.setText("Driver Apple mancante: installa l'app gratuita \"Dispositivi Apple\" dal "
                                     "Microsoft Store (oppure iTunes)")
        elif not present:
            self._auto_tried = False
            if self._connected:
                self._connected = False
                self._status.setText("iPhone scollegato")
                self._update_enabled()
                self._window.statusBar().showMessage("iPhone scollegato", 5000)
            elif self._driver_warned or self._status.text() == "iPhone non collegato":
                self._driver_warned = False
                self._status.setText("Collega l'iPhone con il cavo USB e sbloccalo")
        elif not self._connected and not self._auto_tried and not self._window.runner.is_busy:
            self._auto_tried = True
            self._status.setText("iPhone rilevato: collegamento… se l'iPhone lo chiede, tocca \"Autorizza\" e "
                                 "inserisci il codice")
            self._window.statusBar().showMessage("iPhone rilevato: collegamento in corso", 5000)
            self.connect_device(auto=True)

    # ------------------------------------------------------------------ stato

    # ------------------------------------------------------------------ app Musica tramite iTunes

    def _build_itunes_box(self):
        settings = self._window.app_settings
        self._itunes_send = QPushButton("Invia all'app Musica (tramite iTunes)")
        self._itunes_send.setToolTip("Le copie dei brani selezionati (o dell'artista/album scelto), con i tag "
                                     "modificati, vanno nella playlist \"myEasyMP3toIPhone\" di iTunes")
        self._itunes_send.clicked.connect(self._send_to_itunes)
        self._itunes_sync = QCheckBox("Poi sincronizza l'iPhone")
        self._itunes_sync.setChecked(settings.itunes_sync)
        self._itunes_sync.setToolTip("iTunes sincronizza l'iPhone collegato: la musica sul telefono diventa quella "
                                     "scelta nelle impostazioni di sincronizzazione di iTunes")
        self._itunes_sync.toggled.connect(self._itunes_sync_changed)
        self._ffmpeg_button = QPushButton("Installa ffmpeg")
        self._ffmpeg_button.setToolTip("Serve per i FLAC, che l'app Musica non legge: diventano ALAC (senza perdita "
                                       "di qualità). Installazione gratuita con winget, solo per il tuo utente")
        self._ffmpeg_button.clicked.connect(self._install_ffmpeg)
        self._itunes_note = QLabel()
        self._itunes_note.setWordWrap(True)
        self._itunes_note.setTextFormat(Qt.RichText)
        self._itunes_note.setStyleSheet("color: gray")
        row = QHBoxLayout()
        row.addWidget(self._itunes_send)
        row.addWidget(self._itunes_sync)
        row.addStretch(1)
        row.addWidget(self._ffmpeg_button)
        box = QGroupBox("App Musica dell'iPhone (tramite iTunes)")
        box_layout = QVBoxLayout(box)
        box_layout.addLayout(row)
        box_layout.addWidget(self._itunes_note)
        self._refresh_itunes_note()
        return box

    def _refresh_itunes_note(self) -> None:
        ffmpeg = itunes.find_ffmpeg()
        self._ffmpeg_button.setVisible(ffmpeg is None)
        ffmpeg_text = "ffmpeg presente: i FLAC diventano ALAC." if ffmpeg else ("<b>ffmpeg manca</b>: i FLAC "
                                                                               "verrebbero saltati.")
        self._itunes_note.setText(
            "iTunes si apre durante l'invio. I brani vanno nella playlist <b>myEasyMP3toIPhone</b>: se in iTunes "
            "sincronizzi solo alcune playlist, la prima volta aggiungi questa (iTunes → iPhone → Musica). Le copie "
            f"stanno in <code>{self._window.app_settings.itunes_path()}</code>: non cancellarle, iTunes le usa. "
            + ffmpeg_text)

    def _itunes_sync_changed(self, checked: bool) -> None:
        self._window.app_settings.itunes_sync = checked
        self._window.save_settings()

    def _install_ffmpeg(self) -> None:
        def work(progress, _cancel):
            progress(0, 0, "installazione di ffmpeg con winget")
            value = itunes.install_ffmpeg()
            return value

        def done(message):
            self._refresh_itunes_note()
            QMessageBox.information(self, "ffmpeg", message)

        self._window.runner.run("Installazione di ffmpeg", work, done)

    def _send_to_itunes(self) -> None:
        tracks = self._window.selected_tracks()
        if not tracks:
            QMessageBox.information(self, "App Musica", "Nella scheda Libreria seleziona i brani da inviare, oppure "
                                    "scegli un artista o un album negli elenchi in alto.")
        else:
            flac = 0
            for track in tracks:
                if track.path.suffix.lower() == ".flac":
                    flac += 1
            sync = self._itunes_sync.isChecked()
            root = self._window.app_settings.itunes_path()
            text = (f"Inviare {len(tracks)} brani all'app Musica tramite iTunes?\n\n"
                    f"• iTunes si apre; le copie vanno in {root}\n"
                    "• i file originali non cambiano\n")
            if flac and itunes.find_ffmpeg() is None:
                text += f"• {flac} FLAC verranno saltati: manca ffmpeg (pulsante \"Installa ffmpeg\")\n"
            elif flac:
                text += f"• {flac} FLAC diventano ALAC\n"
            if sync:
                text += "• poi iTunes sincronizza l'iPhone collegato\n"
            answer = QMessageBox.question(self, "App Musica", text)
            if answer == QMessageBox.Yes:
                overlay = self._window.overlay
                home = config_dir()

                def work(progress, cancel):
                    overlay.apply(tracks)
                    value = itunes.send_to_itunes(tracks, root, overlay, home, sync, progress, cancel)
                    return value

                self._window.runner.run("Invio a iTunes", work, self._after_itunes)

    def _after_itunes(self, report) -> None:
        message = report.summary() + "."
        if report.synced:
            message += "\n\nSincronizzazione avviata in iTunes per: " + ", ".join(report.synced)
        elif self._itunes_sync.isChecked():
            message += ("\n\nNessun iPhone collegato a iTunes: collegalo e sincronizza da iTunes (o rifai l'invio "
                        "con l'iPhone collegato).")
        if report.errors:
            details = []
            for path, error in report.errors[:10]:
                details.append(f"{Path(path).name}: {error}")
            message += "\n\nErrori:\n" + "\n".join(details)
        QMessageBox.information(self, "App Musica", message)

    def _update_enabled(self) -> None:
        has_app = self._connected and self._current_app() is not None
        self._app_combo.setEnabled(self._connected)
        self._send_selection_button.setEnabled(has_app)
        self._send_folder_button.setEnabled(has_app)
        self._refresh_button.setEnabled(has_app)
        self._download_button.setEnabled(has_app)
        self._delete_button.setEnabled(has_app)
        self._import_button.setEnabled(self._connected)

    def _current_app(self):
        index = self._app_combo.currentIndex()
        if 0 <= index < len(self._apps):
            result = self._apps[index]
        else:
            result = None
        return result

    def _show_error(self, message: str) -> None:
        self._connected = False
        self._status.setText("iPhone non collegato")
        self._update_enabled()
        QMessageBox.warning(self, "iPhone", message)

    # ------------------------------------------------------------------ collegamento

    def connect_device(self, auto: bool = False) -> None:
        def work(progress, _cancel):
            progress(0, 0, "se l'iPhone lo chiede, tocca Autorizza e inserisci il codice")
            info = iphone.get_device_info()
            progress(0, 0, "elenco delle app")
            apps = iphone.get_file_sharing_apps()
            value = (info, apps)
            return value

        if auto:
            on_error = self._show_auto_error
        else:
            on_error = self._show_error
        self._window.runner.run("Collegamento iPhone", work, self._connected_ok, on_error)

    def _show_auto_error(self, message: str) -> None:
        """Il collegamento automatico non riuscito non apre finestre: lo dice qui; "Collega iPhone" riprova."""
        self._connected = False
        self._status.setText(message.replace("\n\n", " "))
        self._update_enabled()

    def _connected_ok(self, value) -> None:
        info, apps = value
        self._connected = True
        self._status.setText("Collegato: " + info.label())
        self._window.statusBar().showMessage("iPhone collegato: " + info.label(), 8000)
        self._apps = apps
        last_bundle = self._window.app_settings.iphone_last_app
        self._app_combo.blockSignals(True)
        self._app_combo.clear()
        selected = 0
        for index, app in enumerate(apps):
            self._app_combo.addItem(app.label())
            if app.bundle_id == last_bundle:
                selected = index
        self._app_combo.setCurrentIndex(selected)
        self._app_combo.blockSignals(False)
        self._update_enabled()
        if not apps:
            QMessageBox.information(
                self, "iPhone",
                "Sull'iPhone non c'è nessuna app che accetta file dal computer.\n\n"
                "Installa VLC dall'App Store, poi premi di nuovo \"Collega iPhone\".")
        else:
            self._refresh_files()

    def _app_changed(self, _index: int) -> None:
        app = self._current_app()
        if app is not None:
            self._window.app_settings.iphone_last_app = app.bundle_id
            self._window.save_settings()
            self._refresh_files()
        self._update_enabled()

    # ------------------------------------------------------------------ file nell'app

    def _refresh_files(self) -> None:
        app = self._current_app()
        if app is not None and not self._window.runner.is_busy:
            bundle_id = app.bundle_id

            def work(_progress, _cancel):
                value = iphone.list_app_files(bundle_id)
                return value

            self._window.runner.run("Lettura file sull'iPhone", work, self._fill_files)

    def _fill_files(self, files: list) -> None:
        app = self._current_app()
        if app is not None:
            self._window.set_device_files(app, files)
        self._files_view.clear()
        for remote in files:
            shown = remote.path[len(iphone.DOCUMENTS_ROOT) + 1:]
            item = QTreeWidgetItem([shown, _format_size(remote.size)])
            item.setData(0, Qt.UserRole, remote.path)
            self._files_view.addTopLevelItem(item)

    def _selected_remote_paths(self) -> list:
        paths = []
        for item in self._files_view.selectedItems():
            paths.append(item.data(0, Qt.UserRole))
        return paths

    def _download_selected(self) -> None:
        app = self._current_app()
        paths = self._selected_remote_paths()
        if not paths:
            QMessageBox.information(self, "Copia sul PC", "Seleziona prima uno o più file nell'elenco.")
        else:
            folder = QFileDialog.getExistingDirectory(self, "Cartella in cui copiare i file")
            if folder:
                bundle_id = app.bundle_id

                def work(progress, cancel):
                    value = iphone.download_files(bundle_id, paths, Path(folder), progress, cancel)
                    return value

                self._window.runner.run("Copia dall'iPhone", work,
                                        lambda value: QMessageBox.information(
                                            self, "Copia sul PC", value[0].summary()))

    def _delete_selected(self) -> None:
        app = self._current_app()
        paths = self._selected_remote_paths()
        if paths:
            answer = QMessageBox.question(
                self, "Elimina dall'iPhone",
                f"Eliminare definitivamente {len(paths)} file dall'app {app.name}?")
            if answer == QMessageBox.Yes:
                bundle_id = app.bundle_id

                def work(_progress, _cancel):
                    value = iphone.delete_app_files(bundle_id, paths)
                    return value

                self._window.runner.run("Eliminazione", work, self._after_delete)

    def _after_delete(self, report) -> None:
        if report.errors:
            QMessageBox.warning(self, "Elimina", f"{len(report.errors)} file non eliminati.")
        self._refresh_files()

    # ------------------------------------------------------------------ per la scansione

    def connected_app(self):
        """L'app di destinazione scelta, se l'iPhone è collegato; altrimenti None."""
        if self._connected:
            result = self._current_app()
        else:
            result = None
        return result

    def upload_tracks(self, tracks: list) -> None:
        self._start_upload("Invio all'iPhone", lambda _progress, _cancel: tracks)

    def delete_remote(self, paths: list) -> None:
        app = self._current_app()
        if app is not None:
            bundle_id = app.bundle_id

            def work(_progress, _cancel):
                value = iphone.delete_app_files(bundle_id, paths)
                return value

            self._window.runner.run("Eliminazione dall'iPhone", work, self._after_delete)

    # ------------------------------------------------------------------ invio

    def _upload_items(self, tracks: list) -> list:
        """Ogni brano parte da una copia temporanea con le modifiche in sospeso: il file del PC non cambia."""
        overlay = self._window.overlay
        items = []
        for track in tracks:
            relative = REMOTE_MUSIC_FOLDER + "/" + target_relative_path(track).as_posix()

            def prepare(copy, track=track):
                prepare_copy(copy, track.tags, overlay.cover_for(track.path))

            items.append(iphone.UploadItem(source=track.path, relative=relative, prepare=prepare,
                                           signature=overlay.signature(track.path)))
        return items

    def _start_upload(self, title: str, collect_tracks) -> None:
        app = self._current_app()
        bundle_id = app.bundle_id
        overlay = self._window.overlay
        home = config_dir()

        def work(progress, cancel):
            tracks = collect_tracks(progress, cancel)
            overlay.apply(tracks)
            progress(0, 0, "confronto con l'iPhone")
            index = remote_index(iphone.list_app_files(bundle_id))
            sent = iphone.load_sent(home, bundle_id)
            needed = []
            already = []
            for track in tracks:
                if not track.error:
                    if device_status(track, index, sent, overlay.signature(track.path)) == DEVICE_SAME:
                        already.append(str(track.path))
                    else:
                        needed.append(track)
            report = iphone.upload_to_app(bundle_id, self._upload_items(needed), progress, cancel)
            report.skipped += already
            iphone.record_sent(home, bundle_id, report, path_key)
            return report

        self._window.runner.run(title, work, self._after_upload, self._show_error)

    def _after_upload(self, report) -> None:
        message = report.summary()
        if report.errors:
            details = []
            for path, error in report.errors[:10]:
                details.append(f"{Path(path).name}: {error}")
            message += "\n\n" + "\n".join(details)
        QMessageBox.information(self, "Invio all'iPhone", message)
        self._refresh_files()

    def _send_selection(self) -> None:
        tracks = self._window.selected_tracks()
        if not tracks:
            QMessageBox.information(
                self, "Invio all'iPhone",
                "Nella scheda Libreria seleziona i brani da inviare, oppure scegli un artista o un album negli elenchi in alto.")
        else:
            self._start_upload("Invio all'iPhone", lambda _progress, _cancel: tracks)

    def _send_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Cartella da inviare all'iPhone")
        if folder:
            protect_folder(Path(folder))
            self._start_upload("Invio cartella all'iPhone",
                               lambda progress, cancel: scan_folder(Path(folder), progress, cancel,
                                                                  self._window.tag_cache))

    # ------------------------------------------------------------------ importazione

    def _import_music_library(self) -> None:
        library = self._window.library_dir()
        answer = QMessageBox.question(
            self, "Importa dall'iPhone",
            "Copiare nella Libreria del PC tutta la musica dell'app Musica dell'iPhone?\n\n"
            f"Libreria: {library}\n\nI brani già presenti vengono saltati.")
        if answer == QMessageBox.Yes:
            temp_dir = library / IMPORT_TEMP_FOLDER

            def work(progress, cancel):
                progress(0, 0, "elenco dei brani")
                remote_files = iphone.list_music_library()
                remote_paths = [remote.path for remote in remote_files]
                try:
                    transfer, local_files = iphone.download_files(None, remote_paths, temp_dir, progress, cancel)
                    tracks = load_tracks(local_files, progress, cancel)
                    # dall'iPhone al PC: solo file nuovi, un file già presente sul PC non si sostituisce mai
                    copy_report = copy_organized(tracks, library, move=True, progress=progress, cancel=cancel,
                                                 overwrite=False)
                finally:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                value = (len(remote_paths), transfer, copy_report)
                return value

            self._window.runner.run("Importazione dall'iPhone", work, self._after_import, self._show_error)

    def _after_import(self, value) -> None:
        total, transfer, copy_report = value
        if total == 0:
            message = "Nell'app Musica dell'iPhone non ci sono brani copiabili."
        else:
            message = (f"Brani trovati sull'iPhone: {total}\n"
                       f"Scaricati: {len(transfer.done)}\n"
                       f"Aggiunti alla Libreria: {copy_report.summary()}")
            if transfer.errors:
                message += f"\nErrori di download: {len(transfer.errors)}"
        QMessageBox.information(self, "Importa dall'iPhone", message)
        self._window.open_library()
