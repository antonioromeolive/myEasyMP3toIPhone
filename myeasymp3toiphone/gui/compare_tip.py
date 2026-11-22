# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Il suggerimento di ✔ e ⟳: una tabella con il brano abbinato, come è stato abbinato e i tag sul PC e sull'iPhone
affiancati, i valori diversi evidenziati. Si calcola quando il mouse si ferma sulla cella (show_on_tooltip), non
per tutte le righe a ogni riempimento della tabella."""

from __future__ import annotations

from html import escape

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QToolTip

DIFFERENT = "#e8a33d"
CERTAIN = "#3fae5a"


def comparison_html(title: str, matched: str, how: str, certain: bool, rows: list) -> str:
    """rows: (campo, valore sul PC, valore sull'iPhone, diverso), da phone_library.comparison."""
    how_color = CERTAIN if certain else DIFFERENT
    lines = ["<table cellspacing='0' cellpadding='3'>",
             f"<tr><td colspan='3'><b>{escape(title)}</b><br>"
             f"<span style='white-space:pre'>{escape(matched)}</span><br>"
             f"<span style='color:{how_color}'>{escape(how)}</span></td></tr>",
             "<tr><th align='left'>Campo</th><th align='left'>Sul PC</th><th align='left'>Sull'iPhone</th></tr>"]
    for label, pc_value, phone_value, differs in rows:
        style = f" style='color:{DIFFERENT}; font-weight:bold'" if differs else ""
        lines.append(f"<tr{style}><td>{escape(label)}</td><td>{escape(pc_value) or '—'}</td>"
                     f"<td>{escape(phone_value) or '—'}</td></tr>")
    lines.append("</table>")
    result = "".join(lines)
    return result


def show_on_tooltip(event, view, text_for) -> bool:
    """In un eventFilter sul viewport: per un QEvent.ToolTip chiede text_for(posizione) e mostra il testo.
    True se l'evento è stato gestito."""
    handled = False
    if event.type() == QEvent.ToolTip:
        text = text_for(event.pos())
        if text:
            QToolTip.showText(event.globalPos(), text, view)
        else:
            QToolTip.hideText()
        handled = True
    return handled
