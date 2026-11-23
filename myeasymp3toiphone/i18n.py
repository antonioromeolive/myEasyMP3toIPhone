# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La lingua dell'interfaccia: italiano (com'è scritto il programma) o inglese.

Il codice resta scritto in italiano. In inglese i testi si traducono quando arrivano allo schermo: tr() cerca il
testo nel catalogo (i18n_en.CATALOG, un modello per ogni testo del codice, con {0}, {1}… per le parti variabili) e
traduce anche le parti variabili che sono a loro volta testi del catalogo; un testo composto si traduce riga per
riga, o pezzo per pezzo nell'HTML. install_qt_hooks() fa passare da tr() i testi di finestre, pulsanti, menu,
messaggi e barra di stato; i dati (titoli, artisti, album) restano come sono. In italiano non cambia niente.

La lingua si sceglie in Impostazioni e vale dal prossimo avvio (set_language prima di aprire l'interfaccia)."""

from __future__ import annotations

import re
from functools import lru_cache

LANGUAGES = {"it": "Italiano", "en": "English"}
DEFAULT_LANGUAGE = "it"
PLACEHOLDER = re.compile(r"(?<!\{)\{(\d+)\}(?!\})")
MIN_FRAGMENT = 12          # i pezzi di testo tradotti dentro un testo più lungo: almeno questi caratteri
MIN_PIECE = 4              # i testi tra i tag di una voce HTML del catalogo: almeno questi caratteri fissi
MAX_DEPTH = 2              # le parti variabili si traducono fin qui ("consigliato — {0}" → "AI ({0}): {1}" → "alta")
TAG = re.compile(r"<[^<>]+>")
GROUP = re.compile(r"\(\?P<g\d+>\.\*\?\)")     # le parti variabili nella regex di un modello
LETTER = re.compile(r"[A-Za-zÀ-ÿ]")

_state = {"language": DEFAULT_LANGUAGE, "tables": None}


def set_language(code: str) -> None:
    _state["language"] = code if code in LANGUAGES else DEFAULT_LANGUAGE
    _translate.cache_clear()


def language() -> str:
    result = _state["language"]
    return result


def english() -> bool:
    result = _state["language"] == "en"
    return result


def _unescape(text: str) -> str:
    result = text.replace("{{", "{").replace("}}", "}")
    return result


def _html_pieces(catalog: dict) -> dict:
    """I testi tra i tag delle voci HTML del catalogo, ognuno con il suo pezzo inglese (se i pezzi sono tanti quanti):
    un testo HTML composto da più voci ("<b>…</b>" + "<br>Scegli…") si traduce così pezzo per pezzo (_html)."""
    result = {}
    for italian, translated in catalog.items():
        if TAG.search(italian):
            italian_pieces = TAG.split(italian)
            english_pieces = TAG.split(translated)
            if len(italian_pieces) == len(english_pieces):
                for index, piece in enumerate(italian_pieces):
                    plain = PLACEHOLDER.sub("", piece).strip()
                    if len(plain) >= MIN_PIECE and LETTER.search(plain) and piece.strip() not in catalog:
                        result[piece.strip()] = english_pieces[index].strip()
    return result


def _tables() -> tuple:
    """(testi fissi {italiano: inglese}, modelli [(lunghezza del testo fisso, pezzo più lungo, regex, inglese)])."""
    if _state["tables"] is None:
        from .i18n_en import CATALOG
        exact = {}
        patterns = []
        entries = dict(_html_pieces(CATALOG))
        entries.update(CATALOG)
        for italian, translated in entries.items():
            if PLACEHOLDER.search(italian):
                pieces = PLACEHOLDER.split(italian)
                expression = "^"
                literal = 0
                longest = ""
                for index, piece in enumerate(pieces):
                    if index % 2 == 0:
                        plain = _unescape(piece)
                        expression += re.escape(plain)
                        literal += len(plain.strip())
                        if len(plain.strip()) > len(longest):
                            longest = plain.strip()
                    else:
                        expression += f"(?P<g{piece}>.*?)"
                expression += "$"
                if longest:
                    patterns.append((literal, longest, re.compile(expression, re.DOTALL), translated))
            else:
                exact[_unescape(italian)] = _unescape(translated)
        patterns.sort(key=lambda entry: -entry[0])
        _state["tables"] = (exact, patterns)
    result = _state["tables"]
    return result


def _part(text: str, depth: int) -> str:
    """Una parte variabile: tradotta se è a sua volta un testo del catalogo, altrimenti com'è (un titolo, un numero)."""
    exact, _patterns = _tables()
    result = exact.get(text)
    if result is None:
        result = _whole(text, depth)
    if result is None:
        result = text
    return result


def _whole(text: str, depth: int = 0) -> str | None:
    """Il testo intero come uno dei modelli; None se nessuno corrisponde. Le parti variabili si traducono a loro
    volta fino a MAX_DEPTH livelli."""
    exact, patterns = _tables()
    result = exact.get(text)
    index = 0
    while result is None and index < len(patterns):
        _literal, longest, expression, translated = patterns[index]
        if longest in text:
            match = expression.match(text)
            if match is not None and not TAG.search(GROUP.sub("", expression.pattern)) and \
                    TAG.search("".join(match.groups())):
                match = None        # un modello senza HTML non prende pezzi di HTML: si traduce tra i tag (_html)
            if match is not None:
                values = {}
                for name, value in match.groupdict().items():
                    values[name[1:]] = _part(value, depth + 1) if depth < MAX_DEPTH else value
                result = PLACEHOLDER.sub(lambda found: "\x00" + found.group(1) + "\x00", translated)
                result = _unescape(result)
                for number, value in values.items():
                    result = result.replace("\x00" + number + "\x00", value)
        index += 1
    return result


def _fragments(text: str) -> str:
    """Dentro un testo composto: i pezzi lunghi che sono testi del catalogo."""
    exact, _patterns = _tables()
    result = text
    candidates = []
    for italian in exact:
        if len(italian) >= MIN_FRAGMENT and italian in result and exact[italian] != italian:
            candidates.append(italian)
    candidates.sort(key=len, reverse=True)
    for italian in candidates:
        result = result.replace(italian, exact[italian])
    return result


def _multiline(text: str) -> str:
    """I testi del catalogo su più righe dentro un testo composto (prima di tradurlo riga per riga)."""
    exact, _patterns = _tables()
    result = text
    for italian, translated in exact.items():
        if "\n" in italian.strip() and italian in result:
            result = result.replace(italian, translated)
    return result


def _html(text: str) -> str:
    """L'HTML pezzo per pezzo: i testi tra i tag."""
    result = re.sub(r">([^<>]+)<", lambda found: ">" + _translate(found.group(1)) + "<", text)
    return result


@lru_cache(maxsize=8192)
def _translate(text: str) -> str:
    stripped = text.strip()
    result = None
    if stripped:
        result = _whole(text)
        if result is None and stripped != text:
            inner = _whole(stripped)
            if inner is not None:
                result = text.replace(stripped, inner)
        if result is None and "\n" in text:
            lines = []
            for line in _multiline(text).split("\n"):
                lines.append(_translate(line) if line.strip() else line)
            result = "\n".join(lines)
        if result is None and "<" in text and ">" in text:
            result = _html("<_>" + text + "</_>")[3:-4]
        if result is None and ": " in text:
            head, tail = text.split(": ", 1)
            head_text, tail_text = _whole(head), _whole(tail)
            if head_text is not None or tail_text is not None:
                result = (head_text or head) + ": " + (tail_text or _fragments(tail))
        if result is None:
            result = _fragments(text)
    else:
        result = text
    return result


def tr(text):
    """Il testo nella lingua dell'interfaccia (in italiano com'è)."""
    if english() and isinstance(text, str) and text:
        result = _translate(text)
    else:
        result = text
    return result


def tr_exact(text):
    """Solo un testo fisso del catalogo (veloce: per le celle degli elenchi, che sono quasi sempre dati)."""
    result = text
    if english() and isinstance(text, str) and text:
        result = _tables()[0].get(text, text)
    return result


def prompt(system: str) -> str:
    """Il prompt dell'AI: le spiegazioni (motivi) nella lingua dell'interfaccia."""
    result = system.replace("in Italian", "in English") if english() else system
    return result


# --------------------------------------------------------------------------- Qt

def _translated_args(args: tuple, positions) -> list:
    values = list(args)
    for position in positions:
        if position < len(values) and isinstance(values[position], str):
            values[position] = tr(values[position])
    return values


def _wrap(cls, name: str, positions=(0,), all_strings: bool = False, static: bool = False) -> None:
    original = getattr(cls, name)

    def method(*args, **kwargs):
        if all_strings:
            values = []
            for value in args:
                values.append(tr(value) if isinstance(value, str) else value)
        else:
            shift = 0 if static else 1
            values = list(args[:shift]) + _translated_args(args[shift:], positions)
        result = original(*values, **kwargs)
        return result

    setattr(cls, name, staticmethod(method) if static else method)


def _subclass(module, name: str, positions=(0,), all_strings: bool = False, exact_lists: bool = False) -> None:
    """Sostituisce la classe nel modulo di PySide6 con una che traduce i testi passati al costruttore: va fatto prima
    di importare l'interfaccia (che la importa per nome)."""
    base = getattr(module, name)

    def init(self, *args, **kwargs):
        values = []
        for index, value in enumerate(args):
            if isinstance(value, str) and (all_strings or index in positions):
                value = tr(value)
            elif exact_lists and isinstance(value, list):
                value = [tr_exact(item) for item in value]
            values.append(value)
        base.__init__(self, *values, **kwargs)

    replacement = type(name, (base,), {"__init__": init})
    setattr(module, name, replacement)


def install_qt_hooks() -> None:
    """In inglese: i testi mostrati da Qt passano da tr(). Da chiamare una volta, prima di importare gui."""
    from PySide6 import QtGui, QtWidgets
    widgets = QtWidgets
    for cls, names in ((widgets.QWidget, ("setWindowTitle", "setToolTip", "setStatusTip")),
                       (widgets.QLabel, ("setText",)), (widgets.QAbstractButton, ("setText",)),
                       (widgets.QGroupBox, ("setTitle",)), (widgets.QLineEdit, ("setPlaceholderText",)),
                       (QtGui.QAction, ("setText", "setToolTip", "setStatusTip")),
                       (widgets.QStatusBar, ("showMessage",)), (widgets.QTextEdit, ("setHtml",)),
                       (widgets.QMessageBox, ("setText", "setInformativeText"))):
        for name in names:
            _wrap(cls, name)
    # le caselle a tendina no: il loro testo è spesso un valore (un profilo, un modello); chi le riempie usa tr()
    _wrap(widgets.QFormLayout, "addRow", positions=(0,))
    _wrap(widgets.QTabWidget, "addTab", all_strings=True)
    _wrap(widgets.QTabWidget, "setTabText", positions=(1,))
    _wrap(widgets.QTabWidget, "setTabToolTip", positions=(1,))
    _wrap(widgets.QMenu, "addAction", all_strings=True)
    _wrap(widgets.QMenu, "addMenu", all_strings=True)
    _wrap(widgets.QDialogButtonBox, "addButton", positions=(0,))
    original_headers = widgets.QTreeWidget.setHeaderLabels

    def header_labels(self, labels):
        original_headers(self, [tr(label) for label in labels])

    widgets.QTreeWidget.setHeaderLabels = header_labels
    for name in ("question", "information", "warning", "critical"):
        _wrap(widgets.QMessageBox, name, positions=(1, 2), static=True)
    for name in ("getOpenFileName", "getSaveFileName"):
        _wrap(widgets.QFileDialog, name, positions=(1, 3), static=True)
    _wrap(widgets.QFileDialog, "getExistingDirectory", positions=(1,), static=True)
    _wrap(widgets.QToolTip, "showText", positions=(1,), static=True)
    for name in ("QLabel", "QPushButton", "QCheckBox", "QRadioButton", "QGroupBox"):
        _subclass(widgets, name)
    _subclass(widgets, "QMenu", all_strings=True)
    _subclass(QtGui, "QAction", all_strings=True)
    _subclass(widgets, "QTreeWidgetItem", positions=(), exact_lists=True)
    original_item_text = widgets.QTreeWidgetItem.setText
    original_item_tip = widgets.QTreeWidgetItem.setToolTip

    def item_text(self, column, text):
        original_item_text(self, column, tr_exact(text))

    def item_tip(self, column, text):
        original_item_tip(self, column, tr(text))

    widgets.QTreeWidgetItem.setText = item_text
    widgets.QTreeWidgetItem.setToolTip = item_tip
