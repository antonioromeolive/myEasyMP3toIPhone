# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""I colori del programma: barre dei titoli (intestazioni delle colonne, riquadri, scheda scelta) in blu, pulsanti
colorati quando si possono premere e grigi quando no, rossi quelli che cancellano qualcosa
(QPushButton con la proprietà role="danger": mark_danger).

Lo stile Fusion serve perché lo stile nativo di Windows ignora in parte i colori dei pulsanti. I grigi sono
semitrasparenti e il testo sul blu è bianco: si leggono sia con il tema chiaro sia con quello scuro di Windows."""

from __future__ import annotations

BLUE = "#2f6fb3"
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

STYLE_SHEET = f"""
QPushButton {{
    background-color: {BLUE}; color: white;
    border: 1px solid {BLUE_DARK}; border-radius: 4px; padding: 5px 14px;
}}
QPushButton:hover {{ background-color: {BLUE_LIGHT}; }}
QPushButton:pressed {{ background-color: {BLUE_DARK}; }}
QPushButton:default {{ border: 2px solid {BLUE_DARK}; }}
QPushButton[role="go"] {{ background-color: {GREEN}; border-color: {GREEN_DARK}; }}
QPushButton[role="go"]:hover {{ background-color: {GREEN_LIGHT}; }}
QPushButton[role="go"]:pressed {{ background-color: {GREEN_DARK}; }}
QPushButton[role="danger"] {{ background-color: {RED}; border-color: {RED_DARK}; }}
QPushButton[role="danger"]:hover {{ background-color: {RED_LIGHT}; }}
QPushButton[role="danger"]:pressed {{ background-color: {RED_DARK}; }}
QPushButton:disabled, QPushButton[role="danger"]:disabled, QPushButton[role="go"]:disabled {{
    background-color: {GRAY_BACK}; color: {GRAY_TEXT}; border: 1px solid {GRAY_BORDER};
}}

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

QToolBar {{ background-color: rgba(47, 111, 179, 0.10); border: none; spacing: 4px; }}
QToolButton {{ border-radius: 4px; padding: 3px; }}
QToolButton:hover {{ background-color: rgba(47, 111, 179, 0.25); }}
QToolButton:pressed {{ background-color: rgba(47, 111, 179, 0.40); }}
QToolButton:disabled {{ color: {GRAY_TEXT}; }}
"""


def apply_theme(app) -> None:
    """Da chiamare una volta, subito dopo aver creato la QApplication."""
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE_SHEET)


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
    """Il colore di un pulsante: "go" verde (avvia), "danger" rosso (cancella o interrompe), "" il blu normale."""
    button.setProperty("role", role)
    button.style().unpolish(button)
    button.style().polish(button)


def mark_danger(button) -> None:
    """Un pulsante che cancella qualcosa: rosso finché si può premere."""
    button.setProperty("role", "danger")
    button.style().unpolish(button)
    button.style().polish(button)
