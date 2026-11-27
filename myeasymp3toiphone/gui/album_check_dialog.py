"""Verifica online, i dettagli di un album (Dettagli della verifica online nei risultati dei Controlli): le tracce
dell'edizione scelta e i file del PC; un'altra edizione, i tag corretti, la copertina."""

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QBrush, QColor, QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QSplitter, QStyle, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .pc_write import ALSO_PC, ask_where, offer_pc_write
from ..albumcheck import (
    SERVICE_APPLE, SERVICE_DEEZER, SERVICE_DISCOGS, SERVICE_MUSICBRAINZ,
    STATUS_COMPLETE, STATUS_ERROR, STATUS_INCOMPLETE, check_album, corrected_tags,
)

SERVICE_LABEL = {SERVICE_DEEZER: "Deezer", SERVICE_APPLE: "Apple Music", SERVICE_DISCOGS: "Discogs",
                 SERVICE_MUSICBRAINZ: "MusicBrainz"}


GREEN = QColor(30, 140, 60)
RED = QColor(200, 40, 40)
GREY = QColor(130, 130, 130)


def status_icon(widget: QWidget, status: str):
    style = widget.style()
    if status == STATUS_COMPLETE:
        result = style.standardIcon(QStyle.SP_DialogApplyButton)
    elif status == STATUS_INCOMPLETE:
        result = style.standardIcon(QStyle.SP_MessageBoxWarning)
    else:
        result = style.standardIcon(QStyle.SP_MessageBoxQuestion)
    return result


class AlbumCheckDialog(QDialog):
    """I risultati di Verifica album online; embedded: dentro la linguetta Controlli, senza "Chiudi"."""

    def __init__(self, results: list, window, embedded: bool = False) -> None:
        super().__init__(window)
        self.setWindowTitle("Verifica album online: i risultati")
        if embedded:
            self.setWindowFlags(Qt.Widget)
        else:
            self.resize(1100, 650)
        self._window = window
        self._results = list(results)
        self._updating_combo = False

        self._only_incomplete = QCheckBox("Mostra solo gli album da sistemare")
        self._only_incomplete.toggled.connect(self._fill_album_list)
        self._album_list = QListWidget()
        self._album_list.currentRowChanged.connect(self._show_current)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self._only_incomplete)
        left_layout.addWidget(self._album_list)

        self._status_label = QLabel()
        self._status_label.setWordWrap(True)
        self._status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self._tried_label = QLabel()
        self._tried_label.setWordWrap(True)
        self._tried_label.setStyleSheet("color: gray")
        self._edition_combo = QComboBox()
        self._edition_combo.currentIndexChanged.connect(self._edition_changed)
        self._edition_label = QLabel("Edizione:")
        edition_row = QHBoxLayout()
        edition_row.addWidget(self._edition_label)
        edition_row.addWidget(self._edition_combo, 1)

        self._tracks_view = QTreeWidget()
        self._tracks_view.setHeaderLabels(["Traccia", "Titolo nel catalogo", "File sul PC", "Stato"])
        self._tracks_view.setRootIsDecorated(False)
        self._tracks_view.header().setSectionResizeMode(QHeaderView.Interactive)
        self._tracks_view.setColumnWidth(0, 70)
        self._tracks_view.setColumnWidth(1, 300)
        self._tracks_view.setColumnWidth(2, 300)

        self._with_cover = QCheckBox("scarica anche la copertina")
        self._with_cover.setChecked(True)
        self._fix_button = QPushButton("Correggi i tag con questi dati")
        self._fix_button.setToolTip("Imposta titolo, numero traccia/disco, album, artista album e anno "
                                    "dei brani riconosciuti secondo il catalogo (in sospeso: i file non cambiano)")
        self._fix_button.clicked.connect(self._fix_tags)
        self._open_button = QPushButton("Apri nel catalogo")
        self._open_button.clicked.connect(self._open_release)
        self._retry_button = QPushButton("Riprova la verifica")
        self._retry_button.clicked.connect(self._retry)
        actions = QHBoxLayout()
        actions.addWidget(self._fix_button)
        actions.addWidget(self._with_cover)
        actions.addStretch(1)
        actions.addWidget(self._retry_button)
        actions.addWidget(self._open_button)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        intro = QLabel("Per ogni album: le tracce dell'edizione trovata e i tuoi file (le mancanti in rosso). Puoi "
                       "scegliere un'altra edizione e correggere i tag con i suoi dati: restano in sospeso e valgono "
                       "per le copie (iPhone, esportazione), i file del PC non cambiano.")
        intro.setWordWrap(True)
        intro.setStyleSheet("color: gray")
        right_layout.addWidget(intro)
        right_layout.addWidget(self._status_label)
        right_layout.addWidget(self._tried_label)
        right_layout.addLayout(edition_row)
        right_layout.addWidget(self._tracks_view, 1)
        right_layout.addLayout(actions)

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([320, 780])

        bottom = QHBoxLayout()
        bottom.addWidget(QLabel(self._summary()))
        bottom.addStretch(1)
        if not embedded:
            close_button = QPushButton("Chiudi")
            close_button.clicked.connect(self.accept)
            bottom.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(splitter, 1)
        layout.addLayout(bottom)
        self._fill_album_list()

    # ------------------------------------------------------------------ elenco album

    def _summary(self) -> str:
        complete = 0
        incomplete = 0
        for result in self._results:
            if result.status == STATUS_COMPLETE:
                complete += 1
            elif result.status == STATUS_INCOMPLETE:
                incomplete += 1
        other = len(self._results) - complete - incomplete
        text = f"{len(self._results)} album verificati: {complete} completi, {incomplete} incompleti"
        if other:
            text += f", {other} non trovati o con errori"
        return text

    def _visible_results(self) -> list:
        visible = []
        for result in self._results:
            if not self._only_incomplete.isChecked() or result.status != STATUS_COMPLETE:
                visible.append(result)
        return visible

    def _fill_album_list(self) -> None:
        self._album_list.clear()
        for result in self._visible_results():
            item = QListWidgetItem(status_icon(self, result.status), f"{result.artist} — {result.album}")
            item.setToolTip(result.status_text())
            self._album_list.addItem(item)
        if self._album_list.count() > 0:
            self._album_list.setCurrentRow(0)
        else:
            self._show_result(None)

    def _current_result(self):
        row = self._album_list.currentRow()
        visible = self._visible_results()
        if 0 <= row < len(visible):
            result = visible[row]
        else:
            result = None
        return result

    def _show_current(self, _row: int) -> None:
        self._show_result(self._current_result())

    # ------------------------------------------------------------------ dettaglio

    def _show_result(self, result) -> None:
        self._tracks_view.clear()
        self._updating_combo = True
        self._edition_combo.clear()
        if result is None:
            self._status_label.setText("")
            self._tried_label.setText("")
        else:
            self._status_label.setText(result.status_text())
            details = []
            if len(result.tried) > 1:
                tried = []
                for label, outcome in result.tried:
                    tried.append(f"{label}: {outcome}")
                details.append("Provati in ordine: " + "; ".join(tried))
            if result.ai_reason:
                details.append(f"Edizione scelta dall'AI. {result.ai_reason}")
            self._tried_label.setText("\n".join(details))
            self._edition_label.setText(f"Edizione su {result.service_label}:")
            self._open_button.setText(f"Apri su {result.service_label}")
            for candidate in result.candidates:
                self._edition_combo.addItem(candidate.label())
            if result.release is not None:
                ids = [candidate.id for candidate in result.candidates]
                if result.release.id in ids:
                    self._edition_combo.setCurrentIndex(ids.index(result.release.id))
            self._fill_tracks(result)
        self._updating_combo = False
        has_release = result is not None and result.release is not None
        self._fix_button.setEnabled(has_release)
        self._open_button.setEnabled(has_release)
        self._retry_button.setVisible(result is not None and result.status == STATUS_ERROR)
        self._edition_combo.setEnabled(result is not None and len(result.candidates) > 1)

    def _fill_tracks(self, result) -> None:
        for match in result.matches:
            item = QTreeWidgetItem()
            item.setText(0, match.expected.position_label())
            item.setText(1, match.expected.title)
            if match.local is None:
                item.setText(3, "MANCANTE")
                item.setForeground(3, QBrush(RED))
                item.setForeground(1, QBrush(RED))
            else:
                item.setText(2, match.local.path.name)
                item.setText(3, "presente")
                item.setForeground(3, QBrush(GREEN))
            self._tracks_view.addTopLevelItem(item)
        for track in result.extra:
            item = QTreeWidgetItem(["", "", track.path.name, "non riconosciuta"])
            item.setForeground(3, QBrush(GREY))
            item.setToolTip(3, "Il brano non corrisponde a nessuna traccia di questa edizione")
            self._tracks_view.addTopLevelItem(item)

    def _replace_result(self, old, new) -> None:
        index = self._results.index(old)
        self._results[index] = new
        self._window.store_check_result(new)
        row = self._album_list.currentRow()
        self._fill_album_list()
        if 0 <= row < self._album_list.count():
            self._album_list.setCurrentRow(row)

    # ------------------------------------------------------------------ azioni

    def _edition_changed(self, index: int) -> None:
        result = self._current_result()
        valid = (not self._updating_combo and result is not None
                 and 0 <= index < len(result.candidates))
        if valid:
            chosen = result.candidates[index]
            client = self._client(result)

            def work(_progress, _cancel):
                value = check_album(client, result.local_tracks, result.candidates, chosen)
                return value

            self._window.runner.run("Verifica edizione", work,
                                    lambda new: self._replace_result(result, new))

    def _retry(self) -> None:
        result = self._current_result()
        if result is not None:
            client = self._client(result)

            def work(_progress, _cancel):
                value = check_album(client, result.local_tracks)
                return value

            self._window.runner.run("Verifica album online", work,
                                    lambda new: self._replace_result(result, new))

    def _open_release(self) -> None:
        result = self._current_result()
        if result is not None and result.release is not None:
            QDesktopServices.openUrl(QUrl(self._client(result).release_url(result.release)))

    def _client(self, result):
        """Il client del catalogo da cui viene il risultato."""
        result_client = self._window.album_clients[result.service]
        return result_client

    def _fix_tags(self) -> None:
        result = self._current_result()
        if result is not None and result.release is not None:
            matched = [match for match in result.matches if match.local is not None]
            where = ask_where(self, "Correggi tag", f"Aggiornare i tag di {len(matched)} brani con i dati di "
                              f"{result.service_label}?\n\n{result.release.label()}")
            if where:
                self._run_fix(result, matched, where == ALSO_PC)

    def _run_fix(self, result, matched: list, also_pc: bool = False) -> None:
        """I tag corretti (e la copertina) restano in sospeso per le copie dell'iPhone; con also_pc poi l'elenco dei
        file del PC da modificare (pc_write), che si scrivono solo se l'utente lo approva. La copertina resta solo per
        le copie. In background solo lo scaricamento della copertina."""
        client = self._client(result)
        release = result.release
        with_cover = self._with_cover.isChecked()

        def work(progress, _cancel):
            cover = None
            if with_cover:
                progress(0, 0, "download copertina")
                cover = client.fetch_cover(release)
            return cover

        def done(cover):
            pairs = []
            for match in matched:
                pairs.append((match.local, corrected_tags(match, release)))
            self._window.apply_tag_changes(pairs, cover)
            if also_pc:
                if with_cover and cover is None:
                    self._window.statusBar().showMessage("Nessuna copertina disponibile per questa edizione", 8000)
                offer_pc_write(self._window, self, [match.local for match in matched], "Correggi tag",
                               f"si scrivono nel file i tag di {result.service_label} dei campi scelti (la copertina "
                               "va solo sulle copie per l'iPhone)")
            else:
                message = (f"Tag corretti su {len(pairs)} brani, salvati per l'iPhone: i file sul PC non cambiano. "
                           "Inviali all'iPhone per applicarli.")
                if with_cover and cover is None:
                    message += "\nNessuna copertina disponibile per questa edizione."
                QMessageBox.information(self, "Correggi tag", message)

        self._window.runner.run("Correzione tag", work, done)
