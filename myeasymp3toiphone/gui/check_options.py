# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La linguetta Controlli, in alto: su cosa (PC o iPhone, con la selezione della sua scheda: i brani selezionati, gli
album o gli artisti scelti negli elenchi, o tutto), cosa controllare (le regole, l'Analisi AI e la Verifica online,
queste due anche solo sugli album con problemi), Solo AI e Avvia il controllo."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QRadioButton, QVBoxLayout,
    QWidget,
)

from ..check_flow import HOW_ALL, SIDE_PC, SIDE_PHONE
from ..albumcheck import DISCOGS_TOKEN_VAR, SERVICE_DISCOGS, SERVICE_ORDER
from ..scan import CHECK_VARIANTS, CHECKS
from .album_check_dialog import SERVICE_LABEL



def _note(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet("color: gray")
    return label


class CheckOptions(QWidget):
    """Le scelte del controllo. scope() dice su cosa; checks() le regole; ai_on(), online_services() il resto.
    start_requested: Avvia il controllo (o Solo AI)."""

    start_requested = Signal()

    def __init__(self, window) -> None:
        super().__init__(window)
        self._window = window
        self._ignore_selection = False          # Tutto il PC / Tutto l'iPhone: la selezione della scheda non conta
        settings = window.app_settings

        self.pc_side = QRadioButton("PC (i brani della scheda PC)")
        self.phone_side = QRadioButton("iPhone (la musica dell'app Musica)")
        self.pc_side.setChecked(True)
        sides = QButtonGroup(self)
        sides.addButton(self.pc_side)
        sides.addButton(self.phone_side)
        self.pc_side.toggled.connect(lambda _checked: self._side_changed())
        side_row = QHBoxLayout()
        side_row.addWidget(QLabel("<b>Su cosa:</b>"))
        side_row.addWidget(self.pc_side)
        side_row.addWidget(self.phone_side)
        side_row.addStretch(1)

        self.scope_label = QLabel()
        self.scope_label.setWordWrap(True)
        self.scope_label.setTextFormat(Qt.RichText)
        self.scope_names = _note("")
        self.edit_button = QPushButton()
        self.edit_button.clicked.connect(self._go_to_tab)
        self.all_button = QPushButton()
        self.all_button.clicked.connect(self._toggle_selection)
        self.rule_label = _note("")
        buttons = QHBoxLayout()
        buttons.addWidget(self.edit_button)
        buttons.addWidget(self.all_button)
        buttons.addStretch(1)
        scope_box = QFrame()
        scope_box.setObjectName("scopeBox")
        scope_box.setStyleSheet("QFrame#scopeBox { border: 2px solid palette(highlight); border-radius: 6px; }")
        scope_layout = QVBoxLayout(scope_box)
        scope_layout.addWidget(self.scope_label)
        scope_layout.addWidget(self.scope_names)
        scope_layout.addLayout(buttons)
        scope_layout.addWidget(self.rule_label)

        off = set(settings.scan_checks_off)
        self.boxes = {}
        grid = QGridLayout()
        for row, (check_id, label, note) in enumerate(CHECKS):
            box = QCheckBox(label)
            box.setChecked(check_id not in off)
            box.toggled.connect(lambda _checked: self._update())
            grid.addWidget(box, row, 0, Qt.AlignTop)
            grid.addWidget(_note(note), row, 1)
            self.boxes[check_id] = box
        self.musicbrainz = QCheckBox("…e i nomi dubbi anche su MusicBrainz (nomi e alias dell'artista; lento: un "
                                     "artista al secondo, serve internet)")
        self.musicbrainz.setChecked(settings.scan_musicbrainz)
        grid.addWidget(self.musicbrainz, len(CHECKS), 0, 1, 2)
        grid.setColumnStretch(1, 1)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: gray")
        grid.addWidget(line, len(CHECKS) + 1, 0, 1, 2)

        self.ai_box = QCheckBox()
        self.ai_box.setChecked(settings.scan_use_ai)
        self.ai_box.toggled.connect(lambda _checked: self._update())
        self.ai_flagged = QCheckBox("solo sugli album con problemi (gli altri si saltano)")
        self.ai_flagged.setChecked(settings.scan_ai_flagged)
        ai_row = len(CHECKS) + 2
        grid.addWidget(self.ai_box, ai_row, 0, Qt.AlignTop)
        grid.addWidget(_note("l'AI guarda la tabella degli album: conferma o scarta i problemi delle regole, ne trova "
                             "altri e propone le correzioni; con la Verifica online sceglie tra edizioni dubbie"),
                       ai_row, 1)
        grid.addWidget(self.ai_flagged, ai_row + 1, 0, 1, 2)

        self.online_box = QCheckBox("Verifica online")
        self.online_box.setChecked(settings.scan_online)
        self.online_box.toggled.connect(lambda _checked: self._update())
        self.online_flagged = QCheckBox("solo sugli album con problemi (spenta: tutti gli album, è lento)")
        self.online_flagged.setChecked(settings.scan_online_flagged)
        grid.addWidget(self.online_box, ai_row + 2, 0, Qt.AlignTop)
        grid.addWidget(_note("confronta gli album con i cataloghi su internet: brani che mancano anche se i numeri "
                             "tornano, i tag giusti"), ai_row + 2, 1)
        grid.addWidget(self.online_flagged, ai_row + 3, 0, 1, 2)
        services = QHBoxLayout()
        self._services_label = QLabel("Cataloghi, in quest'ordine finché uno dà l'album completo:")
        self._services_label.setStyleSheet("margin-left: 24px")
        services.addWidget(self._services_label)
        self.service_boxes = {}
        for service in SERVICE_ORDER:
            box = QCheckBox(SERVICE_LABEL[service])
            box.setChecked(service in settings.album_services)
            box.toggled.connect(lambda _checked: self._update())
            self.service_boxes[service] = box
            services.addWidget(box)
        services.addStretch(1)
        grid.addLayout(services, ai_row + 4, 0, 1, 2)
        for widget in (self.ai_flagged, self.online_flagged):
            widget.setStyleSheet("margin-left: 24px")

        self.solo_note = QLabel("Senza regole nessun album ha \"problemi\": l'AI e la Verifica online guardano tutti "
                                "gli album di quello che si controlla.")
        self.solo_note.setWordWrap(True)
        self.solo_note.setStyleSheet("color: palette(highlight)")
        all_button = QPushButton("Tutti")
        all_button.clicked.connect(lambda: self._set_all(True))
        none_button = QPushButton("Nessuno")
        none_button.clicked.connect(lambda: self._set_all(False))
        self.solo_ai_button = QPushButton("Solo AI")
        self.solo_ai_button.setToolTip("Spegne gli altri controlli, accende l'Analisi AI su tutto quello che si "
                                       "controlla e parte")
        self.solo_ai_button.clicked.connect(self._solo_ai)
        self.start_button = QPushButton("Avvia il controllo")
        self.start_button.setProperty("role", "go")
        self.start_button.clicked.connect(self.start_requested.emit)
        bottom = QHBoxLayout()
        bottom.addWidget(QLabel("<b>Cosa controllare</b>"))
        bottom.addWidget(all_button)
        bottom.addWidget(none_button)
        bottom.addWidget(self.solo_ai_button)
        bottom.addStretch(1)
        bottom.addWidget(self.start_button)

        left = QVBoxLayout()
        left.addLayout(side_row)
        left.addWidget(scope_box)
        left.addStretch(1)
        right = QVBoxLayout()
        right.addLayout(grid)
        right.addWidget(self.solo_note)
        right.addStretch(1)
        columns = QHBoxLayout()
        columns.addLayout(left, 2)
        columns.addLayout(right, 3)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(columns, 1)
        layout.addLayout(bottom)
        self.refresh()

    # ------------------------------------------------------------------ su cosa

    @property
    def side(self) -> str:
        result = SIDE_PHONE if self.phone_side.isChecked() else SIDE_PC
        return result

    def set_side(self, side: str) -> None:
        """PC o iPhone (l'iPhone solo se la sua musica è stata letta), con la riga "Si controlla" rifatta."""
        self.phone_side.setEnabled(bool(self._window.phone_tracks))
        if side == SIDE_PHONE and self.phone_side.isEnabled():
            self.phone_side.setChecked(True)
        else:
            self.pc_side.setChecked(True)
        self.refresh()

    def scope(self) -> tuple:
        """(parte, brani, frase, nomi): i brani del PC (Track) o dell'iPhone (PhoneTrack) da controllare."""
        from ..check_flow import scope_text
        window = self._window
        if self.side == SIDE_PHONE:
            if self._ignore_selection:
                items = list(window.phone_tracks)
                albums = []
                for item in items:
                    key = (item.tags.album_artist or item.display_artist, item.tags.album)
                    if key not in albums:
                        albums.append(key)
                text = scope_text("iPhone", HOW_ALL, items, albums)
            else:
                items, text = window.iphone_panel.check_scope()
        elif self._ignore_selection:
            items = window.format_tracks()
            albums = []
            for track in items:
                if track.album_key not in albums:
                    albums.append(track.album_key)
            text = scope_text("PC", HOW_ALL, items, albums, window.open_description())
        else:
            items, text = window.check_scope()
        result = (self.side, items, text[0], text[1])
        return result

    def _side_changed(self) -> None:
        self._ignore_selection = False
        self.refresh()

    def _go_to_tab(self) -> None:
        self._window.show_side_tab(self.side)

    def _toggle_selection(self) -> None:
        self._ignore_selection = not self._ignore_selection
        self.refresh()

    def refresh(self) -> None:
        """Le scelte che dipendono da cosa è aperto: la musica dell'iPhone, la selezione delle schede, il profilo AI,
        il token di Discogs."""
        window = self._window
        self.phone_side.setEnabled(bool(window.phone_tracks))
        if self.side == SIDE_PHONE and not window.phone_tracks:
            self.pc_side.setChecked(True)
        tab = "iPhone" if self.side == SIDE_PHONE else "PC"
        _side, items, sentence, names = self.scope()
        self.scope_label.setText(sentence)
        self.scope_names.setText(names)
        self.scope_names.setVisible(bool(names))
        self.edit_button.setText(f"Modifica la selezione nella scheda {tab}")
        if self._ignore_selection:
            self.all_button.setText(f"Usa la selezione della scheda {tab}")
        else:
            self.all_button.setText("Tutto il PC" if tab == "PC" else "Tutto l'iPhone")
        self.rule_label.setText(f"Come la barra delle azioni: i brani selezionati nella lista della scheda {tab}; se non "
                                "ce ne sono, gli artisti o gli album scelti negli elenchi; se non c'è niente, tutto.")
        self._items = items
        name = window.scan_launcher.profile_name()
        self.ai_box.setText(f"Analisi AI ({name})" if name else "Analisi AI (scegli un profilo in Impostazioni → "
                            "Generale)")
        self.ai_box.setEnabled(bool(name))
        discogs = self.service_boxes[SERVICE_DISCOGS]
        ready = window.album_discogs_ready()
        discogs.setEnabled(ready)
        discogs.setToolTip("" if ready else f"Imposta la variabile {DISCOGS_TOKEN_VAR} (nel file delle variabili o in "
                           "Windows) con un token personale di Discogs, poi riavvia")
        self._update()

    # ------------------------------------------------------------------ cosa controllare

    def checks(self) -> frozenset:
        chosen = set()
        for check_id, box in self.boxes.items():
            if box.isChecked():
                chosen.add(check_id)
        result = frozenset(chosen)
        return result

    def checks_off(self) -> list:
        result = []
        for check_id, box in self.boxes.items():
            if not box.isChecked():
                result.append(check_id)
        return result

    def ai_on(self) -> bool:
        result = self.ai_box.isChecked() and self.ai_box.isEnabled()
        return result

    def online_services(self) -> list:
        """I cataloghi scelti, in ordine; [] se la Verifica online è spenta."""
        result = []
        if self.online_box.isChecked():
            for service in SERVICE_ORDER:
                box = self.service_boxes[service]
                if box.isChecked() and box.isEnabled():
                    result.append(service)
        return result

    def ai_flagged_only(self) -> bool:
        """L'AI solo sugli album con problemi: vale solo se c'è almeno una regola."""
        result = self.ai_flagged.isChecked() and bool(self.checks())
        return result

    def online_flagged_only(self) -> bool:
        result = self.online_flagged.isChecked() and bool(self.checks())
        return result

    def _set_all(self, checked: bool) -> None:
        for box in self.boxes.values():
            box.setChecked(checked)
        self.ai_box.setChecked(checked)
        if not checked:
            self.online_box.setChecked(False)
        self._update()

    def _solo_ai(self) -> None:
        """Solo AI: le regole e la Verifica online spente, l'AI accesa su tutto quello che si controlla; e parte."""
        for box in self.boxes.values():
            box.setChecked(False)
        self.online_box.setChecked(False)
        self.ai_box.setChecked(True)
        self._update()
        if self.start_button.isEnabled():
            self.start_requested.emit()

    def _update(self) -> None:
        rules = bool(self.checks())
        self.musicbrainz.setEnabled(self.boxes[CHECK_VARIANTS].isChecked())
        self.ai_flagged.setEnabled(self.ai_on() and rules)
        online = self.online_box.isChecked()
        self.online_flagged.setEnabled(online and rules)
        self._services_label.setVisible(online)
        for box in self.service_boxes.values():
            box.setVisible(online)
        self.solo_note.setVisible((self.ai_on() or online) and not rules)
        self.solo_ai_button.setEnabled(self.ai_box.isEnabled())
        something = rules or self.ai_on() or bool(self.online_services())
        self.start_button.setEnabled(bool(getattr(self, "_items", [])) and something)
