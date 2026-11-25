# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Pezzi dell'interfaccia usati nelle due schede:

- FlowLayout: i widget uno dopo l'altro, e a capo quando la riga è piena (i filtri a pulsanti);
- ChipBar: i filtri a pulsanti ("chip") con il conteggio, uno solo scelto; si usa come una casella a tendina
  (currentIndex, setCurrentIndex, count, findText, itemText, currentIndexChanged), così fa anche da legenda;
- ActionBar: la riga delle azioni sopra la tabella dei brani, che cambia con la scelta: "N brani scelti", i pulsanti
  [(testo, attiva, funzione)] e una nota grigia a destra."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QLabel, QLayout, QMenu, QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from ..i18n import tr
from .icons import icon

ICON_COLOR = "#2f6fb3"          # le icone dei pulsanti neutri (su quelli verdi e rossi sono bianche)
# l'icona di ogni azione della barra (le chiavi di ActionBar)
ACTION_ICONS = {"copy": "plus", "replace": "swap", "tags": "tag", "delete": "trash", "edit": "pencil",
                "export": "export", "save": "save", "link": "link"}


class FlowLayout(QLayout):
    """I widget in fila, a capo quando non ci stanno (come le parole di un testo)."""

    def __init__(self, parent=None, spacing: int = 6) -> None:
        super().__init__(parent)
        self._items = []
        self._spacing = spacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item) -> None:
        self._items.append(item)

    def count(self) -> int:
        result = len(self._items)
        return result

    def itemAt(self, index: int):
        result = self._items[index] if 0 <= index < len(self._items) else None
        return result

    def takeAt(self, index: int):
        result = self._items.pop(index) if 0 <= index < len(self._items) else None
        return result

    def expandingDirections(self):
        result = Qt.Orientation(0)
        return result

    def hasHeightForWidth(self) -> bool:
        result = True
        return result

    def heightForWidth(self, width: int) -> int:
        result = self._place(QRect(0, 0, width, 0), False)
        return result

    def setGeometry(self, rect) -> None:
        super().setGeometry(rect)
        self._place(rect, True)

    def sizeHint(self) -> QSize:
        result = self.minimumSize()
        return result

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        result = size + QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return result

    def _place(self, rect, apply: bool) -> int:
        """Mette i widget nella riga (apply) e restituisce l'altezza che serve."""
        margins = self.contentsMargins()
        area = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        x = area.x()
        y = area.y()
        line_height = 0
        for item in self._items:
            hint = item.sizeHint()
            next_x = x + hint.width() + self._spacing
            if next_x - self._spacing > area.right() + 1 and line_height > 0:
                x = area.x()
                y = y + line_height + self._spacing
                next_x = x + hint.width() + self._spacing
                line_height = 0
            if apply:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x = next_x
            line_height = max(line_height, hint.height())
        result = y + line_height - rect.y() + margins.bottom()
        return result


class ChipBar(QWidget):
    """I filtri a pulsanti: (testo) con il conteggio a fianco, uno solo scelto. Si usa come una QComboBox."""

    currentIndexChanged = Signal(int)

    def __init__(self, texts: list, parent=None) -> None:
        super().__init__(parent)
        self._texts = list(texts)
        self._buttons = []
        self._counts = [None] * len(texts)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        layout = FlowLayout(self)
        for index, text in enumerate(self._texts):
            button = QPushButton(tr(text))
            button.setCheckable(True)
            button.setProperty("role", "chip")
            button.setCursor(Qt.PointingHandCursor)
            button.setFocusPolicy(Qt.TabFocus)
            self._group.addButton(button, index)
            layout.addWidget(button)
            self._buttons.append(button)
        self._buttons[0].setChecked(True)
        self._group.idToggled.connect(self._toggled)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

    def _toggled(self, index: int, checked: bool) -> None:
        if checked:
            self.currentIndexChanged.emit(index)

    def currentIndex(self) -> int:
        result = max(0, self._group.checkedId())
        return result

    def setCurrentIndex(self, index: int) -> None:
        if 0 <= index < len(self._buttons):
            self._buttons[index].setChecked(True)

    def count(self) -> int:
        result = len(self._buttons)
        return result

    def itemText(self, index: int) -> str:
        result = self._texts[index]
        return result

    def findText(self, text: str) -> int:
        result = self._texts.index(text) if text in self._texts else -1
        return result

    def set_counts(self, counts: list) -> None:
        """Il numero accanto a ogni filtro (None: senza numero); un filtro con 0 è più tenue."""
        self._counts = list(counts)
        for index, button in enumerate(self._buttons):
            count = self._counts[index] if index < len(self._counts) else None
            label = tr(self._texts[index])
            button.setText(label if count is None else f"{label}  {count}")
            button.setProperty("empty", count == 0)
            button.style().unpolish(button)
            button.style().polish(button)
        self.updateGeometry()

    def set_tips(self, tips: list) -> None:
        for button, tip in zip(self._buttons, tips):
            button.setToolTip(tip)


class ActionBar(QFrame):
    """La riga delle azioni sopra la tabella: "N brani scelti", i pulsanti (aggiornati con set_entries) e la nota.
    I pulsanti sono quelli dati a build (chiave, ruolo: "go", "danger" o ""); set_entries li riempie da
    {chiave: (testo, attiva, funzione)}; un pulsante senza voce si nasconde."""

    def __init__(self, keys: list, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("actionBar")
        self._who = QLabel()
        self._who.setObjectName("actionWho")
        self._note = QLabel()
        self._note.setObjectName("actionNote")
        self._note.setWordWrap(True)
        self._buttons = {}
        self._slots = {}
        row = FlowLayout(spacing=6)            # i pulsanti vanno a capo se la finestra è stretta
        row.addWidget(self._who)
        for key, role in keys:
            button = QPushButton()
            button.setProperty("role", role)
            if key in ACTION_ICONS:
                button.setIcon(icon(ACTION_ICONS[key], "white" if role in ("go", "danger") else ICON_COLOR))
            button.clicked.connect(lambda _checked=False, name=key: self._run(name))
            self._buttons[key] = button
            row.addWidget(button)
        self.menu_button = QPushButton("Strumenti")
        self.menu_button.setIcon(icon("tools", ICON_COLOR))
        self.menu_button.setVisible(False)
        row.addWidget(self.menu_button)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(4)
        layout.addLayout(row)
        layout.addWidget(self._note)             # la nota grigia sotto i pulsanti, su tutta la larghezza

    def set_menu(self, menu: QMenu, text: str = "Strumenti") -> None:
        self.menu_button.setText(text)
        self.menu_button.setMenu(menu)
        self.menu_button.setVisible(True)

    def _run(self, key: str) -> None:
        slot = self._slots.get(key)
        if slot is not None:
            slot()

    def set_entries(self, who: str, entries: dict, note: str = "") -> None:
        self._who.setText(who)
        self._note.setText(note)
        self._note.setVisible(bool(note))
        for key, button in self._buttons.items():
            entry = entries.get(key)
            button.setVisible(entry is not None)
            if entry is not None:
                text, enabled, slot = entry
                button.setText(text)
                button.setEnabled(enabled and slot is not None)
                self._slots[key] = slot

    def button(self, key: str) -> QPushButton:
        result = self._buttons[key]
        return result
