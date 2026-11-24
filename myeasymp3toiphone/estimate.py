# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Quanto dura un'azione sull'iPhone, da mostrare prima di chiedere conferma.

I numeri vengono da una misura su un iPhone vero via USB (24/11/2026, qualche migliaio di brani nella libreria): il
database della libreria (17 MB) si scarica in 0,8 s, 10 brani da 8 MB si inviano in 4,8 s (17 MB/s, preparazione
compresa), 10 brani si tolgono in 1,2 s. Qui sono un po' più prudenti: i file possono stare su un disco esterno
lento."""

from __future__ import annotations

import math
from pathlib import Path

BYTES_PER_SECOND = 12_000_000     # invio: copia sul PC, tag, impronta e trasferimento
SECONDS_PER_SENT_TRACK = 0.2      # preparazione di ogni brano, oltre ai byte
SECONDS_PER_SESSION = 3.0         # una sessione con l'iPhone: database scaricato, accordo, chiusura
SECONDS_PER_CHANGE = 0.05         # un brano tolto o un Cambia tag, dentro la sessione
SECONDS_TO_REREAD = 2.0           # alla fine si rilegge la musica dell'iPhone
SEND_BATCH = 25                   # phone_actions.BATCH_INSERTS
CHANGE_BATCH = 400                # phone_actions.BATCH_CHANGES
DEFAULT_SIZE = 8_000_000          # un file che non si legge: un MP3 di 4-5 minuti


def file_size(path) -> int:
    """La dimensione di un file del PC; DEFAULT_SIZE se non si legge."""
    try:
        result = Path(path).stat().st_size
    except OSError:
        result = DEFAULT_SIZE
    return result


def seconds(send_sizes: list, removes: int = 0, edits: int = 0) -> float:
    """send_sizes: i byte di ogni brano da inviare (anche quelli da rimpiazzare); removes: i brani da togliere (anche
    le versioni vecchie dei rimpiazzati); edits: i brani da aggiornare con Cambia tag."""
    total = 0.0
    if send_sizes:
        sessions = math.ceil(len(send_sizes) / SEND_BATCH)
        total += sessions * SECONDS_PER_SESSION + len(send_sizes) * SECONDS_PER_SENT_TRACK
        total += sum(send_sizes) / BYTES_PER_SECOND
    if removes:
        total += math.ceil(removes / CHANGE_BATCH) * SECONDS_PER_SESSION + removes * SECONDS_PER_CHANGE
    if edits:
        # un album nuovo si crea con un brano e gli altri lo raggiungono nella sessione dopo: una sessione in più
        total += (math.ceil(edits / CHANGE_BATCH) + 1) * SECONDS_PER_SESSION + edits * SECONDS_PER_CHANGE
    if total:
        total += SECONDS_TO_REREAD
    result = total
    return result


def describe(value: float) -> str:
    """"meno di un minuto", "circa 3 minuti", "circa 1 ora e 20 minuti" (per eccesso)."""
    minutes = math.ceil(value / 60)
    if value < 60:
        result = "meno di un minuto"
    elif minutes == 1:
        result = "circa un minuto"
    elif minutes < 60:
        result = f"circa {minutes} minuti"
    else:
        hours = minutes // 60
        rest = minutes % 60
        hour_text = "1 ora" if hours == 1 else f"{hours} ore"
        result = f"circa {hour_text}" if rest == 0 else f"circa {hour_text} e {rest} minuti"
    return result


def summary(count: int, value: float) -> str:
    """La riga per le finestre di conferma."""
    result = f"Brani: {count}. Tempo stimato: {describe(value)}."
    return result
