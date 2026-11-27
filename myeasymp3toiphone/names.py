# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Quando due nomi sono "lo stesso" e quale grafia vince: un posto solo per tutti i controlli (checks_requirements.md,
REQ-14, D-1, D-2, D-3).

fold(testo, livello) toglie le differenze fino al livello dato, ognuno comprende i precedenti:

  * LEVEL_EXACT     niente: carattere per carattere;
  * LEVEL_SPACES    spazi all'inizio, alla fine e doppi; la stessa lettera accentata salvata in due modi (NFC);
  * LEVEL_CASE      maiuscole e minuscole;
  * LEVEL_ACCENTS   accenti ("Pérez" = "Perez"): così raggruppano gli elenchi del programma (library.group_name);
  * LEVEL_PUNCT     punteggiatura, "&" = "and" ("AC/DC" = "AC DC");
  * LEVEL_WORDS     "The" iniziale e ordine delle parole ("Battiato Franco" = "Franco Battiato").

choose_spelling sceglie la grafia da scrivere ovunque tra quelle dello stesso nome."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

LEVEL_EXACT = 0
LEVEL_SPACES = 1
LEVEL_CASE = 2
LEVEL_ACCENTS = 3
LEVEL_PUNCT = 4
LEVEL_WORDS = 5

POLICY_MOST = "la_più_usata"       # più brani; a parità più maiuscole, poi la prima
POLICY_FIRST = "la_prima"          # la prima nell'ordine dato
MIN_CAPITAL_WORD = 4              # le parole più corte ("e", "le", "di", "of", "the") non devono avere la maiuscola

_SPACES = re.compile(r"\s+")
_WORD = re.compile(r"[^\W\d_]+")


def clean_spaces(text: str) -> str:
    """Il testo senza spazi all'inizio, alla fine e doppi, con le lettere accentate in una forma sola (NFC)."""
    result = _SPACES.sub(" ", unicodedata.normalize("NFC", text or "")).strip()
    return result


def _without_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    kept = []
    for char in decomposed:
        if not unicodedata.combining(char):
            kept.append(char)
    result = "".join(kept)
    return result


def fold(text: str, level: int) -> str:
    """Il testo senza le differenze che contano fino a level (vedi sopra)."""
    result = text or ""
    if level >= LEVEL_SPACES:
        result = clean_spaces(result)
    if level >= LEVEL_CASE:
        result = result.casefold()
    if level >= LEVEL_ACCENTS:
        result = _SPACES.sub(" ", _without_accents(result)).strip()
    if level >= LEVEL_PUNCT:
        result = re.sub(r"[^a-z0-9]+", " ", result.replace("&", " and ")).strip()
    if level >= LEVEL_WORDS:
        words = result.split()
        if len(words) > 1 and words[0] == "the":
            words = words[1:]
        result = "".join(sorted(words))
    return result


def same(first: str, second: str, level: int) -> bool:
    result = fold(first, level) == fold(second, level)
    return result


def has_accents(text: str) -> bool:
    result = fold(text, LEVEL_CASE) != fold(text, LEVEL_ACCENTS)
    return result


def all_capitals(text: str) -> bool:
    """Tutto in maiuscolo ("AC/DC", "QUEEN"), con almeno una lettera."""
    letters = _WORD.findall(text or "")
    result = bool(letters) and (text or "").upper() == (text or "")
    return result


def capital_initials(text: str) -> bool:
    """Le iniziali maiuscole (D-1): la prima lettera e ogni parola di almeno MIN_CAPITAL_WORD lettere cominciano con la
    maiuscola, e il nome non è tutto in maiuscolo. "Franco Battiato", "Elio e le Storie Tese", "McCartney" sì;
    "franco battiato", "Franco battiato", "FRANCO BATTIATO" no."""
    words = _WORD.findall(text or "")
    result = bool(words) and words[0][0].isupper() and not all_capitals(text)
    index = 0
    while result and index < len(words):
        word = words[index]
        if len(word) >= MIN_CAPITAL_WORD and not word[0].isupper():
            result = False
        index += 1
    return result


def capital_rank(text: str) -> int:
    """0: iniziali maiuscole; 1: tutto maiuscolo; 2: il resto. Vince il numero più basso."""
    if capital_initials(text):
        result = 0
    elif all_capitals(text):
        result = 1
    else:
        result = 2
    return result


def _uppercase_count(text: str) -> int:
    count = 0
    for char in text:
        if char.isupper():
            count += 1
    return count


@dataclass
class Choice:
    spelling: str
    accents_differ: bool = False       # grafie con accenti diversi ("Perché"/"Perchè"): da controllare


def choose_spelling(spellings: list, counts: dict = None, policy: str = POLICY_MOST, capitals: bool = True) -> Choice:
    """La grafia che vince tra quelle dello stesso nome (spellings: in ordine, senza ripetizioni; counts: {grafia:
    brani}). Prima gli accenti (D-3): una grafia con l'accento vince su quella senza; con accenti diversi tra loro la
    scelta resta segnata come da controllare. Poi, con capitals, le iniziali maiuscole (D-1: capital_rank). Infine
    policy: POLICY_MOST la più usata (a parità, più maiuscole, poi la prima), POLICY_FIRST la prima."""
    counts = counts or {}
    candidates = []
    for spelling in spellings:
        if spelling and spelling not in candidates:
            candidates.append(spelling)
    accented = []
    for spelling in candidates:
        if has_accents(spelling):
            accented.append(spelling)
    if accented and len(accented) < len(candidates):
        candidates = accented
    forms = set()
    for spelling in candidates:
        forms.add(fold(spelling, LEVEL_CASE))
    accents_differ = bool(accented) and len(forms) > 1
    if capitals and candidates:
        best_rank = 3
        for spelling in candidates:
            best_rank = min(best_rank, capital_rank(spelling))
        ranked = []
        for spelling in candidates:
            if capital_rank(spelling) == best_rank:
                ranked.append(spelling)
        candidates = ranked
    chosen = candidates[0] if candidates else ""
    if policy == POLICY_MOST:
        best = None
        for position, spelling in enumerate(candidates):
            rank = (counts.get(spelling, 0), _uppercase_count(spelling), -position)
            if best is None or rank > best:
                best = rank
                chosen = spelling
    result = Choice(chosen, accents_differ)
    return result


# --------------------------------------------------------------------------- caratteri rovinati

REPLACEMENT_CHAR = "�"


def repaired_mojibake(text: str) -> str:
    """Il testo giusto di un testo UTF-8 letto come Windows-1252 o Latin-1 ("PerchÃ©" → "Perché"), "" se il testo
    non ha questo difetto."""
    result = ""
    if text and any(ord(char) > 127 for char in text):
        for codec in ("cp1252", "latin-1"):
            if not result:
                try:
                    candidate = text.encode(codec).decode("utf-8")
                except (UnicodeEncodeError, UnicodeDecodeError):
                    candidate = ""
                if candidate and candidate != text:
                    result = candidate
    return result
