"""Il riquadro a destra della scheda iPhone, fatto come l'editor dei tag della scheda PC: i tag dei brani scelti come li
mostra l'app Musica e la copertina del file associato sul PC. Cambia i tag va in attesa e parte con Applica; la casella
"Anche sul PC" (spenta, e di nuovo spenta dopo ogni volta) mette gli stessi tag sui file del PC associati come
modifiche in sospeso: i file non cambiano."""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from ..phone_actions import EDITABLE_FIELDS
from ..tags import BOOL_FIELDS, INT_FIELDS, TAG_FIELDS
from .tag_editor import COVER_SIZE, MIXED

NUMBER_FIELDS = ("year", "track_number", "disc_number")    # quelli dell'iPhone che vogliono un numero (0 svuota)
FIXED_TIP = ("Non si cambia qui: sull'iPhone l'artista si rinominerebbe per tutti i suoi brani. Cambialo nella scheda "
             "PC, poi usa Ricopia da PC a iPhone.")
ONE_AT_A_TIME = "(si cambia un brano alla volta)"


def _shown(value) -> str:
    if value is None or value == "":
        result = ""
    else:
        result = str(value)
    return result


class PhoneTagPanel(QWidget):
    # i brani dell'iPhone da cambiare, {campo: nuovo valore}, anche sul PC
    queue_requested = Signal(list, dict, bool)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._tracks = []
        self._editable = []          # i brani messi da un computer: solo questi si cambiano
        self._original = {}
        self._original_compilation = Qt.Unchecked
        self.values = {}
        self.also_pc = False
        self.fields = {}

        self._header = QLabel("Seleziona uno o più brani")
        self._header.setWordWrap(True)
        self._header.setStyleSheet("font-weight: bold;")
        self._kinds = QLabel()
        self._kinds.setWordWrap(True)
        self._kinds.setStyleSheet("color: gray")

        form = QFormLayout()
        self.compilation = QCheckBox("album di più artisti")
        self.compilation.setToolTip("Compilation: l'artista dell'album è \"Artisti vari\", quello del brano è il "
                                    "suo. Senza, l'app Musica dell'iPhone divide l'album in un album per artista.")
        self.compilation.clicked.connect(self._compilation_clicked)
        for name, label in TAG_FIELDS:
            if name in BOOL_FIELDS:
                form.addRow(label + ":", self.compilation)
            else:
                edit = QLineEdit()
                if name in INT_FIELDS or name == "year":
                    edit.setMaximumWidth(80)
                if name not in EDITABLE_FIELDS:
                    edit.setReadOnly(True)
                    edit.setToolTip(FIXED_TIP if "artist" in name else "Non si cambia sull'iPhone: cambialo nella "
                                    "scheda PC, poi usa Ricopia da PC a iPhone.")
                edit.textEdited.connect(lambda _text: self._update_buttons())
                self.fields[name] = edit
                form.addRow(label + ":", edit)
        tags_box = QGroupBox("Tag")
        tags_box.setLayout(form)

        self._cover_label = QLabel("Nessuna\ncopertina")
        self._cover_label.setAlignment(Qt.AlignCenter)
        self._cover_label.setFixedSize(COVER_SIZE, COVER_SIZE)
        self._cover_label.setStyleSheet("border: 1px solid palette(mid);")
        self._cover_note = QLabel()
        self._cover_note.setWordWrap(True)
        self._cover_note.setStyleSheet("color: gray")
        cover_layout = QVBoxLayout()
        cover_layout.addWidget(self._cover_label, alignment=Qt.AlignHCenter)
        cover_layout.addWidget(self._cover_note)
        cover_box = QGroupBox("Copertina")
        cover_box.setLayout(cover_layout)

        self._save_button = QPushButton("Metti in attesa")
        self._save_button.setToolTip("L'iPhone cambia con Applica (la barra blu in alto)")
        self._save_button.setDefault(True)
        self._save_button.clicked.connect(self._check)
        self._revert_button = QPushButton("Annulla")
        self._revert_button.clicked.connect(self._reload)
        # spenta di serie, e di nuovo spenta dopo ogni volta: il PC cambia solo se lo chiedi
        self._also_pc = QCheckBox("Anche sul PC")
        self._also_pc.setToolTip("Spenta, il PC resta com'è e la differenza si vede (⟳). Per scrivere i tag nei file "
                                 "del PC c'è Usa i tag da iPhone a PC.")
        # la spiegazione va a capo in una riga a parte: una casella non va a capo, e un testo lungo allargava il
        # riquadro oltre lo spazio della scheda (se ne vedeva solo un pezzo)
        self._also_pc_note = QLabel()
        self._also_pc_note.setWordWrap(True)
        self._also_pc_note.setStyleSheet("color: gray")
        note = QLabel("Si cambiano titolo (un brano alla volta), album, numeri, anno, genere e Compilation: vanno in "
                      "attesa e l'iPhone cambia con Applica. Un campo vuoto non cambia; anno o numero 0 lo svuota. "
                      "Artista e artista dell'album si cambiano nella scheda PC, poi Ricopia da PC a iPhone.")
        note.setWordWrap(True)
        note.setStyleSheet("color: gray")
        buttons = QHBoxLayout()
        buttons.addWidget(self._save_button)
        buttons.addWidget(self._revert_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self._header)
        layout.addWidget(self._kinds)
        layout.addWidget(tags_box)
        layout.addWidget(self._also_pc)
        layout.addWidget(self._also_pc_note)
        layout.addLayout(buttons)
        layout.addWidget(note)
        layout.addWidget(cover_box)
        layout.addStretch(1)
        self.set_tracks([])

    # ------------------------------------------------------------------ stato

    def set_tracks(self, phone_tracks: list, linked: int = 0, cover: Optional[bytes] = None,
                   cover_note: str = "") -> None:
        """I brani scelti (PhoneTrack); linked: quanti hanno il file associato su questo PC (Anche sul PC); la
        copertina da mostrare e la riga che dice da dove viene."""
        self._tracks = list(phone_tracks)
        editable = []
        for item in self._tracks:
            if item.from_computer:
                editable.append(item)
        self._editable = editable
        self._also_pc_note.setText(f"Gli stessi tag per i {linked} brani con il file su questo PC, come modifiche in "
                                   "sospeso (i file non cambiano)")
        self._also_pc.setEnabled(linked > 0 and bool(editable))
        if not self._also_pc.isEnabled():
            self._also_pc.setChecked(False)
        self._show_cover(cover)
        self._cover_note.setText(cover_note)
        self._cover_note.setVisible(bool(cover_note))
        self._reload()

    def show_album(self, phone_tracks: list, cover: Optional[bytes] = None, cover_note: str = "") -> None:
        """Nessun brano selezionato, ma un album scelto negli elenchi: la sua copertina (dal file associato sul PC) e
        il suo nome, senza niente da cambiare (come nella scheda PC)."""
        self.set_tracks([], 0, cover, cover_note)
        if phone_tracks:
            tags = phone_tracks[0].tags
            artist = tags.album_artist or tags.artist
            self._header.setText(f"{artist} — {tags.album}\n{len(phone_tracks)} brani: selezionali per cambiarli")

    def _reload(self) -> None:
        count = len(self._tracks)
        enabled = bool(self._editable)
        for name, edit in self.fields.items():
            values = set()
            for item in self._tracks:
                values.add(_shown(getattr(item.tags, name)))
            if len(values) == 1:
                edit.setText(values.pop())
                edit.setPlaceholderText("")
            else:
                edit.setText("")
                edit.setPlaceholderText(MIXED if count > 1 else "")
            if name == "title" and count > 1:
                edit.setText("")
                edit.setPlaceholderText(ONE_AT_A_TIME)
                edit.setEnabled(False)
            elif name in EDITABLE_FIELDS:
                edit.setEnabled(enabled)
            else:
                edit.setEnabled(count > 0)
        self._original = {}
        for name, edit in self.fields.items():
            self._original[name] = edit.text()
        flags = set()
        for item in self._tracks:
            flags.add(bool(item.tags.compilation))
        self.compilation.setTristate(len(flags) > 1)
        if len(flags) > 1:
            self.compilation.setCheckState(Qt.PartiallyChecked)
        else:
            self.compilation.setCheckState(Qt.Checked if True in flags else Qt.Unchecked)
        self.compilation.setEnabled(enabled)
        self._original_compilation = self.compilation.checkState()
        if count == 0:
            self._header.setText("Seleziona uno o più brani")
        elif count == 1:
            self._header.setText(self._tracks[0].tags.title or self._tracks[0].remote_path)
        else:
            self._header.setText(f"{count} brani selezionati: i campi cambiati valgono per tutti")
        self._kinds.setText(self._kinds_text())
        self._kinds.setVisible(bool(self._kinds.text()))
        self._update_buttons()

    def _kinds_text(self) -> str:
        """Perché alcuni brani scelti non si cambiano (non messi da un computer)."""
        others = len(self._tracks) - len(self._editable)
        if others and not self._editable:
            result = ("Non messi sull'iPhone da un computer (acquistati, scaricati o di un altro programma): i tag "
                      "si vedono ma non si cambiano")
        elif others:
            result = f"{others} dei brani scelti non sono stati messi da un computer: i loro tag non cambiano"
        else:
            result = ""
        return result

    def focus_first_field(self) -> bool:
        """Il cursore nel primo campo che si può cambiare (Titolo, o Album con più brani), con il testo selezionato.
        False se non c'è niente da cambiare."""
        chosen = None
        for name, edit in self.fields.items():
            if chosen is None and name in EDITABLE_FIELDS and edit.isEnabled():
                chosen = edit
        result = chosen is not None
        if result:
            chosen.setFocus(Qt.ShortcutFocusReason)
            chosen.selectAll()
        return result

    def _compilation_clicked(self) -> None:
        """Un clic sceglie sì o no per tutti: lo stato "valori diversi" non si sceglie a mano."""
        if self.compilation.checkState() == Qt.PartiallyChecked:
            self.compilation.setCheckState(Qt.Checked)
        self.compilation.setTristate(False)
        self._update_buttons()

    def has_unsaved_changes(self) -> bool:
        result = self.compilation.checkState() != self._original_compilation
        for name, edit in self.fields.items():
            if name in EDITABLE_FIELDS and edit.isEnabled() and edit.text().strip() != self._original.get(name, ""):
                result = True
        return result

    def _update_buttons(self) -> None:
        changed = bool(self._editable) and self.has_unsaved_changes()
        self._save_button.setEnabled(changed)
        self._revert_button.setEnabled(changed)

    def _show_cover(self, data: Optional[bytes]) -> None:
        pixmap = QPixmap()
        if data is not None and pixmap.loadFromData(data):
            scaled = pixmap.scaled(COVER_SIZE, COVER_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._cover_label.setPixmap(scaled)
        else:
            self._cover_label.setPixmap(QPixmap())
            self._cover_label.setText("Nessuna\ncopertina")

    # ------------------------------------------------------------------ in attesa

    def _check(self) -> None:
        """I campi cambiati, controllati: un campo vuoto non cambia; anno e numeri solo cifre (0 svuota)."""
        values = {}
        problem = ""
        for name, edit in self.fields.items():
            text = edit.text().strip()
            if name in EDITABLE_FIELDS and edit.isEnabled() and text and text != self._original.get(name, ""):
                if name in NUMBER_FIELDS:
                    if text.isascii() and text.isdigit() and int(text) <= 9999:   # "²" è isdigit ma non un int
                        values[name] = int(text)
                    else:
                        problem = f"{name.replace('_', ' ')}: serve un numero"
                else:
                    values[name] = text
        state = self.compilation.checkState()
        if state != self._original_compilation and state != Qt.PartiallyChecked:
            values["compilation"] = state == Qt.Checked
        if problem:
            QMessageBox.warning(self, "Cambia i tag", problem)
        elif not values:
            QMessageBox.information(self, "Cambia i tag", "Non hai cambiato niente.")
        elif self._editable:
            self.values = values
            self.also_pc = self._also_pc.isChecked()
            self._also_pc.setChecked(False)
            # i campi restano come scritti: l'iPhone li prende con Applica
            for name, edit in self.fields.items():
                self._original[name] = edit.text().strip()
            self._original_compilation = self.compilation.checkState()
            self._update_buttons()
            self.queue_requested.emit(list(self._editable), values, self.also_pc)
