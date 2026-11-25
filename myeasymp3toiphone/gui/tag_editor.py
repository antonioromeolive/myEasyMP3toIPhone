"""Pannello di modifica dei tag (singolo brano o più brani insieme). Le modifiche non toccano i file sul PC: restano
in sospeso e valgono per le copie inviate all'iPhone (vedi overlay.py)."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

from ..tags import BOOL_FIELDS, COVER_EXTENSIONS, INT_FIELDS, READ_ONLY_EXTENSIONS, TAG_FIELDS, read_cover, tag_kinds

MIXED = "(valori diversi)"
COVER_SIZE = 180
ALBUM_COVER_TRIES = 5     # un album scelto senza brani selezionati: la copertina del primo brano che ne ha una


def _as_text(value) -> str:
    if value is None:
        result = ""
    else:
        result = str(value)
    return result


class TagEditor(QWidget):
    # {campo: nuovo valore}, copertina (bytes o None)
    apply_requested = Signal(dict, object)
    renumber_requested = Signal()
    revert_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._tracks = []
        self.cover_provider = None   # track -> bytes della copertina da mostrare (anche quella in sospeso)
        self.edited_check = None     # track -> True se ha modifiche in sospeso
        self._dirty = set()
        self._new_cover: Optional[bytes] = None
        self._editors = {}

        self._header = QLabel("Seleziona uno o più brani")
        self._header.setWordWrap(True)
        self._header.setStyleSheet("font-weight: bold;")
        self._kinds = QLabel()
        self._kinds.setWordWrap(True)
        self._kinds.setStyleSheet("color: gray")

        form = QFormLayout()
        for name, label in TAG_FIELDS:
            if name in BOOL_FIELDS:
                # tre stati: sì, no e "valori diversi" quando i brani selezionati non sono uguali
                editor = QCheckBox("album di più artisti")
                editor.setToolTip("Compilation: l'artista dell'album è \"Artisti vari\", quello del brano è il "
                                  "suo. Senza, l'app Musica dell'iPhone divide l'album in un album per artista.")
                editor.clicked.connect(lambda _checked, field=name: self._bool_clicked(field))
            else:
                editor = QLineEdit()
                if name in INT_FIELDS:
                    editor.setValidator(QIntValidator(0, 999, editor))
                    editor.setMaximumWidth(80)
                editor.textEdited.connect(lambda _text, field=name: self._mark_dirty(field))
            self._editors[name] = editor
            form.addRow(label + ":", editor)
        tags_box = QGroupBox("Tag")
        tags_box.setLayout(form)

        self._cover_label = QLabel("Nessuna\ncopertina")
        self._cover_label.setAlignment(Qt.AlignCenter)
        self._cover_label.setFixedSize(COVER_SIZE, COVER_SIZE)
        self._cover_label.setStyleSheet("border: 1px solid palette(mid);")
        self._cover_button = QPushButton("Cambia copertina…")
        self._cover_button.clicked.connect(self._choose_cover)
        cover_layout = QVBoxLayout()
        cover_layout.addWidget(self._cover_label, alignment=Qt.AlignHCenter)
        cover_layout.addWidget(self._cover_button)
        cover_box = QGroupBox("Copertina")
        cover_box.setLayout(cover_layout)

        self._save_button = QPushButton("Salva modifiche")
        self._save_button.setToolTip("Salva le modifiche per l'iPhone: il file sul PC non cambia")
        self._save_button.setDefault(True)
        self._save_button.clicked.connect(self._apply)
        self._revert_button = QPushButton("Annulla")
        self._revert_button.clicked.connect(self._reload)
        self._renumber_button = QPushButton("Numera in ordine")
        self._renumber_button.setToolTip(
            "Assegna i numeri di traccia 1, 2, 3… ai brani selezionati, nell'ordine mostrato in tabella")
        self._renumber_button.clicked.connect(self.renumber_requested.emit)
        self._restore_button = QPushButton("Torna ai tag del file")
        self._restore_button.setToolTip("Annulla le modifiche in sospeso dei brani selezionati")
        self._restore_button.clicked.connect(self.revert_requested.emit)
        note = QLabel("I file sul PC sono in sola lettura: le modifiche restano in sospeso e valgono per le copie "
                      "inviate all'iPhone (ed esportate).")
        note.setWordWrap(True)
        note.setStyleSheet("color: gray")
        # spenta di serie, e di nuovo spenta dopo ogni salvataggio: l'iPhone cambia solo se lo chiedi
        self.also_phone = QCheckBox("Anche sull'iPhone: usa questi tag da PC a iPhone (va in attesa)")
        self.also_phone.setToolTip("Per i brani che sull'iPhone hanno la sorgente certa (registro): dopo il "
                                   "salvataggio i tag nuovi vanno in attesa per l'iPhone e partono con Applica. Spenta, "
                                   "l'iPhone resta com'è e la differenza si vede (⟳).")
        buttons = QHBoxLayout()
        buttons.addWidget(self._save_button)
        buttons.addWidget(self._revert_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self._header)
        layout.addWidget(self._kinds)
        layout.addWidget(tags_box)
        layout.addWidget(self.also_phone)
        layout.addLayout(buttons)
        layout.addWidget(self._renumber_button)
        layout.addWidget(self._restore_button)
        layout.addWidget(note)
        layout.addWidget(cover_box)
        layout.addStretch(1)
        self.set_tracks([])

    # ------------------------------------------------------------------ stato

    def set_tracks(self, tracks: list) -> None:
        self._tracks = list(tracks)
        self._reload()

    def show_album(self, tracks: list) -> None:
        """Nessun brano selezionato, ma un album scelto negli elenchi: la sua copertina e il suo nome, senza niente da
        modificare (la copertina del primo dei suoi brani che ne ha una, tra i primi ALBUM_COVER_TRIES)."""
        self.set_tracks([])
        cover = None
        index = 0
        while cover is None and index < len(tracks) and index < ALBUM_COVER_TRIES:
            cover = self._cover_of(tracks[index])
            index += 1
        self._show_cover(cover)
        if tracks:
            tags = tracks[0].tags
            artist = tags.album_artist or tags.artist
            self._header.setText(f"{artist} — {tags.album}\n{len(tracks)} brani: selezionali in tabella per "
                                 "modificarli")

    def focus_first_field(self) -> bool:
        """Il cursore nel primo campo (Titolo), con il testo selezionato, pronto da modificare (il tasto E della
        tabella). False se non c'è niente da modificare (nessun brano, o file in sola lettura)."""
        editor = self._editors[TAG_FIELDS[0][0]]
        result = editor.isEnabled()
        if result:
            editor.setFocus(Qt.ShortcutFocusReason)
            editor.selectAll()
        return result

    def has_unsaved_changes(self) -> bool:
        result = bool(self._dirty) or self._new_cover is not None
        return result

    def _reload(self) -> None:
        self._dirty = set()
        self._new_cover = None
        count = len(self._tracks)
        read_only = False
        for track in self._tracks:
            if track.path.suffix.lower() in READ_ONLY_EXTENSIONS:
                read_only = True
        enabled = count > 0 and not read_only
        for name, editor in self._editors.items():
            editor.setEnabled(enabled)
            values = set()
            for track in self._tracks:
                values.add(_as_text(getattr(track.tags, name)))
            if name in BOOL_FIELDS:
                editor.setTristate(len(values) > 1)
                if len(values) > 1:
                    editor.setCheckState(Qt.PartiallyChecked)
                else:
                    editor.setCheckState(Qt.Checked if values == {"True"} else Qt.Unchecked)
            elif len(values) == 1:
                editor.setText(values.pop())
                editor.setPlaceholderText("")
            else:
                editor.setText("")
                editor.setPlaceholderText(MIXED if count > 1 else "")
        if count == 0:
            self._header.setText("Seleziona uno o più brani")
        elif count == 1:
            self._header.setText(self._tracks[0].path.name)
        else:
            self._header.setText(f"{count} brani selezionati: i campi modificati verranno applicati a tutti")
        self._kinds.setText(self._kinds_text(read_only))
        self._kinds.setVisible(bool(self._kinds.text()))
        self._cover_button.setEnabled(enabled and self._cover_supported())
        self._renumber_button.setEnabled(count > 1)
        edited = False
        for track in self._tracks:
            if self.edited_check is not None and self.edited_check(track):
                edited = True
        self._restore_button.setEnabled(edited)
        self._update_buttons()
        self._show_cover(self._current_cover())

    def _kinds_text(self, read_only: bool) -> str:
        """Da quali tipi di tag vengono i valori (un brano), e se i tag si possono cambiare."""
        result = ""
        if len(self._tracks) == 1:
            kinds = tag_kinds(self._tracks[0].path)
            if not kinds:
                result = "Nessun tag nel file"
            elif len(kinds) == 1:
                result = f"Tag letti da: {kinds[0]}"
            else:
                joined = " + ".join(kinds)
                result = f"Tag letti da: {joined} (un campo vuoto si prende dal tipo seguente)"
        if read_only:
            note = "WMA, WAV e AIFF: i tag si leggono soltanto e i brani non si inviano all'iPhone"
            result = f"{result}\n{note}" if result else note
        return result

    def _bool_clicked(self, field: str) -> None:
        """Un clic sceglie sì o no per tutti: lo stato "valori diversi" non si sceglie a mano."""
        editor = self._editors[field]
        if editor.checkState() == Qt.PartiallyChecked:
            editor.setCheckState(Qt.Checked)
        editor.setTristate(False)
        self._mark_dirty(field)

    def _mark_dirty(self, field: str) -> None:
        self._dirty.add(field)
        self._update_buttons()

    def _update_buttons(self) -> None:
        changed = self.has_unsaved_changes()
        self._save_button.setEnabled(changed)
        self._revert_button.setEnabled(changed)

    def _cover_supported(self) -> bool:
        result = True
        for track in self._tracks:
            if track.path.suffix.lower() not in COVER_EXTENSIONS:
                result = False
        return result

    # ------------------------------------------------------------------ copertina

    def _cover_of(self, track) -> Optional[bytes]:
        if self.cover_provider is not None:
            result = self.cover_provider(track)
        else:
            result = read_cover(track.path)
        return result

    def _current_cover(self) -> Optional[bytes]:
        result = None
        if len(self._tracks) == 1:
            result = self._cover_of(self._tracks[0])
        elif len(self._tracks) > 1:
            result = self._cover_of(self._tracks[0])
            if result is not None:
                same_album = len({track.album_key for track in self._tracks}) == 1
                if not same_album:
                    result = None
        return result

    def _show_cover(self, data: Optional[bytes]) -> None:
        pixmap = QPixmap()
        if data is not None and pixmap.loadFromData(data):
            scaled = pixmap.scaled(COVER_SIZE, COVER_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._cover_label.setPixmap(scaled)
        else:
            self._cover_label.setPixmap(QPixmap())
            self._cover_label.setText("Nessuna\ncopertina")

    def _choose_cover(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(
            self, "Scegli l'immagine di copertina", "", "Immagini (*.jpg *.jpeg *.png)")
        if path:
            data = Path(path).read_bytes()
            pixmap = QPixmap()
            if pixmap.loadFromData(data):
                self._new_cover = data
                self._show_cover(data)
                self._update_buttons()
            else:
                QMessageBox.warning(self, "Copertina", "Il file scelto non è un'immagine valida.")

    # ------------------------------------------------------------------ salvataggio

    def _apply(self) -> None:
        changes = {}
        valid = True
        for name in sorted(self._dirty):
            if name in BOOL_FIELDS:
                changes[name] = self._editors[name].checkState() == Qt.Checked
            elif name in INT_FIELDS:
                text = self._editors[name].text().strip()
                if text == "":
                    changes[name] = None
                elif text.isdigit():
                    changes[name] = int(text)
                else:
                    valid = False
            else:
                changes[name] = self._editors[name].text().strip()
        if valid:
            self.apply_requested.emit(changes, self._new_cover)
        else:
            QMessageBox.warning(self, "Tag", "I campi numerici devono contenere solo numeri.")
