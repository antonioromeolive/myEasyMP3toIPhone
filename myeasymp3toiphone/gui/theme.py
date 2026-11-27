# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""I colori del programma: barre dei titoli (intestazioni delle colonne, riquadri, scheda scelta) in blu; i pulsanti
con una gerarchia: neutri di serie (bordo blu al passaggio del mouse), **verdi** per l'azione principale (role="go":
Applica, Copia da PC a iPhone, Avvia…), **rossi** per quelli che cancellano o interrompono (role="danger":
mark_danger), grigi quando non si possono premere. I filtri a pulsanti (role="chip") sono pillole, blu quando
scelte. Le icone sono in icons.py.

Lo stile Fusion serve perché lo stile nativo di Windows ignora in parte i colori dei pulsanti. I grigi sono
semitrasparenti e il testo sul blu è bianco: si leggono sia con il tema chiaro sia con quello scuro di Windows.

La selezione negli elenchi e nelle tabelle è blu pieno con il testo bianco, uguale anche quando l'elenco non ha il
fuoco (Qt la mostrerebbe grigia: con due elenchi affiancati non si vedeva cosa era scelto). Nelle tabelle dei brani
gli album si distinguono dallo sfondo (album_band): due tinte che si alternano da un album all'altro, ognuna chiara e
scura a righe alterne dentro l'album; le tinte sono semitrasparenti, per il tema chiaro e quello scuro."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette

BLUE = "#2f6fb3"
SELECTION = "#1f6fd6"          # lo sfondo della selezione, con il testo bianco
# (chiara, scura) per album: azzurro, poi ambra, poi di nuovo azzurro…
ALBUM_BANDS = ((QColor(47, 111, 179, 34), QColor(47, 111, 179, 70)),
               (QColor(225, 150, 30, 30), QColor(225, 150, 30, 66)))
BLUE_LIGHT = "#3d82cc"
BLUE_DARK = "#245a93"
GREEN = "#2e8b57"
GREEN_LIGHT = "#3aa56a"
GREEN_DARK = "#226b43"
RED = "#c0392b"
RED_LIGHT = "#d64a3b"
RED_DARK = "#962d22"
GRAY_BACK = "rgba(128, 128, 128, 0.22)"
GRAY_TEXT = "rgba(128, 128, 128, 0.95)"
GRAY_BORDER = "rgba(128, 128, 128, 0.35)"
AMBER_TEXT = "#b36b00"         # gli avvisi (non sincronizzare con iTunes): si legge sul chiaro e sullo scuro

STYLE_SHEET = f"""
QPushButton {{
    background-color: rgba(128, 128, 128, 0.10); color: palette(button-text);
    border: 1px solid {GRAY_BORDER}; border-radius: 6px; padding: 5px 12px;
}}
QPushButton:hover {{ background-color: rgba(47, 111, 179, 0.14); border-color: {BLUE}; }}
QPushButton:pressed {{ background-color: rgba(47, 111, 179, 0.28); }}
QPushButton:checked {{ background-color: rgba(47, 111, 179, 0.45); border: 2px solid {BLUE}; font-weight: 600; }}
QPushButton:default {{ border: 1px solid {BLUE}; }}
QPushButton[role="go"] {{ background-color: {GREEN}; color: white; border-color: {GREEN_DARK}; font-weight: 600; }}
QPushButton[role="go"]:hover {{ background-color: {GREEN_LIGHT}; }}
QPushButton[role="go"]:pressed {{ background-color: {GREEN_DARK}; }}
QPushButton[role="danger"] {{ background-color: {RED}; color: white; border-color: {RED_DARK}; font-weight: 600; }}
QPushButton[role="danger"]:hover {{ background-color: {RED_LIGHT}; }}
QPushButton[role="danger"]:pressed {{ background-color: {RED_DARK}; }}
QPushButton:disabled, QPushButton[role="danger"]:disabled, QPushButton[role="go"]:disabled {{
    background-color: {GRAY_BACK}; color: {GRAY_TEXT}; border: 1px solid {GRAY_BORDER}; font-weight: normal;
}}
QPushButton::menu-indicator {{ subcontrol-position: right center; right: 6px; }}

QHeaderView::section {{
    background-color: {BLUE}; color: white; font-weight: bold;
    padding: 4px 6px; border: none; border-right: 1px solid {BLUE_LIGHT};
}}
QHeaderView::section:hover {{ background-color: {BLUE_LIGHT}; }}

QGroupBox {{
    border: 1px solid {BLUE}; border-radius: 5px; margin-top: 16px; padding-top: 10px;
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left; left: 8px;
    padding: 2px 10px; background-color: {BLUE}; color: white; border-radius: 3px;
}}

QTabBar::tab {{
    padding: 6px 16px; margin-right: 2px;
    border: 1px solid {GRAY_BORDER}; border-bottom: none;
    border-top-left-radius: 4px; border-top-right-radius: 4px;
    background-color: {GRAY_BACK};
}}
QTabBar::tab:selected {{ background-color: {BLUE}; color: white; border-color: {BLUE_DARK}; }}
QTabBar::tab:hover:!selected {{ background-color: rgba(47, 111, 179, 0.30); }}

QToolBar {{
    background-color: rgba(47, 111, 179, 0.06); border: none; border-bottom: 1px solid rgba(47, 111, 179, 0.25);
    spacing: 2px; padding: 4px 8px;
}}
QToolBar::separator {{ background-color: {GRAY_BORDER}; width: 1px; margin: 6px 8px; }}
QToolButton {{ border-radius: 6px; padding: 4px 10px; }}
QToolButton:hover {{ background-color: rgba(47, 111, 179, 0.25); }}
QToolButton:pressed {{ background-color: rgba(47, 111, 179, 0.40); }}
QToolButton:disabled {{ color: {GRAY_TEXT}; }}

QAbstractItemView {{ selection-background-color: {SELECTION}; selection-color: white; }}

QPushButton[role="chip"] {{
    background-color: transparent; color: palette(text); font-weight: 600;
    border: 1px solid {GRAY_BORDER}; border-radius: 13px; padding: 3px 12px;
}}
QPushButton[role="chip"]:hover {{ background-color: rgba(47, 111, 179, 0.15); }}
QPushButton[role="chip"]:checked {{ background-color: {BLUE}; color: white; border-color: {BLUE_DARK}; }}
QPushButton[role="chip"][empty="true"] {{ color: {GRAY_TEXT}; }}
QPushButton[role="chip"][empty="true"]:checked {{ color: white; }}

QFrame#actionBar {{
    background-color: rgba(47, 111, 179, 0.07); border: 1px solid rgba(47, 111, 179, 0.25); border-radius: 6px;
}}
QLabel#actionWho {{ font-weight: bold; }}
QLabel#actionNote {{ color: {GRAY_TEXT}; }}
QFrame#deviceCard {{
    background-color: rgba(47, 111, 179, 0.06); border: 1px solid rgba(47, 111, 179, 0.35); border-radius: 8px;
}}
QFrame#checkCard {{
    background-color: rgba(47, 111, 179, 0.04); border: 1px solid rgba(47, 111, 179, 0.30); border-radius: 8px;
}}
QLabel#cardTitle {{ font-size: 15px; font-weight: bold; }}
QLabel#deviceName {{ font-size: 15px; font-weight: bold; }}
QLabel#deviceInfo {{ color: {GRAY_TEXT}; }}
QLabel#warningLine {{ color: {AMBER_TEXT}; }}
QLabel#chipNote {{ color: {AMBER_TEXT}; font-weight: 600; margin-left: 8px; }}
QLabel#helpText {{ background: palette(alternate-base); padding: 8px; border-radius: 4px; }}
QLabel#panelTitle {{ font-weight: bold; }}
"""


def apply_theme(app) -> None:
    """Da chiamare una volta, subito dopo aver creato la QApplication."""
    app.setStyle("Fusion")
    palette = app.palette()
    for group in (QPalette.Active, QPalette.Inactive):     # anche senza fuoco: non grigio su grigio
        palette.setColor(group, QPalette.Highlight, QColor(SELECTION))
        palette.setColor(group, QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    app.setStyleSheet(STYLE_SHEET)


def album_bands(keys: list) -> list:
    """Per ogni riga (la chiave del suo album, nell'ordine mostrato) l'indice in ALBUM_BANDS e 0/1 (chiara/scura):
    la tinta cambia quando cambia l'album rispetto alla riga prima, la chiara e la scura si alternano dentro l'album."""
    result = []
    band = 0
    shade = 0
    previous = None
    for position, key in enumerate(keys):
        if position > 0 and key != previous:
            band = 1 - band
            shade = 0
        elif position > 0:
            shade = 1 - shade
        result.append((band, shade))
        previous = key
    return result


def album_band(band: int, shade: int) -> QColor:
    result = ALBUM_BANDS[band][shade]
    return result


def install_italian(app) -> bool:
    """I pulsanti standard di Qt in italiano (OK, Annulla, Sì, No…): la traduzione di Qt stessa, se c'è."""
    from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
    translator = QTranslator(app)     # figlio dell'applicazione: resta vivo quanto lei
    loaded = translator.load(QLocale(QLocale.Italian, QLocale.Italy), "qtbase", "_",
                             QLibraryInfo.path(QLibraryInfo.TranslationsPath))
    if loaded:
        app.installTranslator(translator)
    result = loaded
    return result


def set_role(button, role: str) -> None:
    """Il colore di un pulsante: "go" verde (avvia), "danger" rosso (cancella o interrompe), "" neutro."""
    button.setProperty("role", role)
    button.style().unpolish(button)
    button.style().polish(button)


def mark_danger(button) -> None:
    """Un pulsante che cancella qualcosa: rosso finché si può premere."""
    button.setProperty("role", "danger")
    button.style().unpolish(button)
    button.style().polish(button)
