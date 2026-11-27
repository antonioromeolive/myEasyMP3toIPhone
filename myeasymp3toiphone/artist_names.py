# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le forme in cui è scritto un artista: "Franco Battiato", "Battiato Franco", "Battiato", "F. Battiato", accenti,
errori di battitura, duetti. Solo i nomi: i problemi e le correzioni li costruisce scan.

  * certo (regola): stesse parole, a parte maiuscole, accenti, punteggiatura, "The" iniziale e ordine
    ("Battiato Franco" = "Franco Battiato", "AC/DC" = "ACDC"): variant_key;
  * dubbio: solo il cognome, le iniziali, un errore di battitura (candidate_pairs, poi clusters): decide l'AI con il
    contesto (album e anni), e se è chiesto MusicBrainz (nome e alias dell'artista);
  * duetti: "A & B", "A feat. B", "A, B"…: se A c'è anche da solo, A resta artista e B va nel titolo (duet_proposal).

Vince sempre la forma più usata nella musica dell'utente (la sceglie scan)."""

from __future__ import annotations

import logging
import re
import threading
from difflib import SequenceMatcher
from typing import Callable, Optional

from .names import LEVEL_PUNCT, LEVEL_WORDS, fold

log = logging.getLogger(__name__)

DUET_SPLIT = re.compile(r"\s+(?:feat\.?|ft\.?|featuring|with|con|&|and|e|x|vs\.?)\s+|\s*[,;/+]\s*", re.IGNORECASE)
NOT_A_GUEST = {"jr", "sr", "ii", "iii", "iv"}     # "Grover Washington, Jr." non è un duetto
MIN_SURNAME = 4           # "Mina" sì, "Elio"… anche: decide comunque l'AI
TYPO_RATIO = 0.88
MIN_TYPO_LENGTH = 6
MAX_CLUSTER = 8
AI_BATCH = 20

ProgressFn = Callable[[int, int, str], None]


def plain_words(text: str) -> list:
    result = fold(text, LEVEL_PUNCT).split()
    return result


def variant_key(name: str) -> str:
    """La chiave delle varianti certe: parole senza maiuscole, accenti e punteggiatura, senza "the" iniziale, in
    ordine alfabetico, attaccate (names.LEVEL_WORDS)."""
    result = fold(name, LEVEL_WORDS)
    return result


def duet_parts(name: str) -> list:
    """I nomi di un duetto, nell'ordine ("A & B feat. C" -> [A, B, C]); un nome solo se non lo è."""
    parts = []
    for part in DUET_SPLIT.split(name or ""):
        cleaned = part.strip()
        if cleaned:
            parts.append(cleaned)
    if not parts:
        parts = [name]
    return parts


def duet_proposal(name: str, solos: dict) -> Optional[tuple]:
    """(artista principale, [ospiti]) se name è un duetto il cui primo nome c'è anche da solo (solos: {variant_key:
    grafia}); altrimenti None (un gruppo come "Simon & Garfunkel" resta com'è)."""
    parts = duet_parts(name)
    result = None
    if len(parts) > 1:
        guests = []
        real = True
        for part in parts[1:]:
            if variant_key(part) in NOT_A_GUEST:
                real = False
            guests.append(part)
        principal = solos.get(variant_key(parts[0]))
        if real and principal is not None and variant_key(principal) != variant_key(name):
            result = (principal, guests)
    return result


def with_guests(title: str, guests: list) -> str:
    """Il titolo con gli ospiti: "Titolo (feat. A & B)"; uguale se li nomina già."""
    lowered = (title or "").lower()
    if "feat" in lowered or not guests:
        result = title
    else:
        result = f"{title} (feat. {' & '.join(guests)})"
    return result


def _is_initial(word: str) -> bool:
    result = len(word) == 1 and word.isalpha()
    return result


def _initials_match(short: list, long: list) -> bool:
    """"f battiato" e "franco battiato": stesse parole, con iniziali al posto di qualche nome."""
    result = len(short) == len(long) and any(_is_initial(word) for word in short)
    index = 0
    while result and index < len(short):
        word = short[index]
        other = long[index]
        result = word == other or (_is_initial(word) and other.startswith(word) and len(other) > 1)
        index += 1
    return result


def candidate_pairs(names: dict) -> list:
    """Le coppie dubbie tra i gruppi certi: names {variant_key: grafia più usata}, senza i duetti. (chiave, chiave,
    perché): solo il cognome, iniziali, errore di battitura."""
    words = {}
    for key, display in names.items():
        words[key] = plain_words(display)
    by_word = {}
    for key, parts in words.items():
        if len(parts) > 1:
            for part in (parts[0], parts[-1]):
                by_word.setdefault(part, set()).add(key)
    found = {}
    for key, parts in words.items():
        if len(parts) == 1 and len(parts[0]) >= MIN_SURNAME:
            for other in by_word.get(parts[0], set()):
                found[tuple(sorted((key, other)))] = "solo il cognome"
    by_last = {}
    for key, parts in words.items():
        if len(parts) > 1:
            by_last.setdefault(parts[-1], []).append(key)
            by_last.setdefault(parts[0], []).append(key)
    for group in by_last.values():
        for first in group:
            for second in group:
                if first < second:
                    one, two = words[first], words[second]
                    matched = (_initials_match(one, two) or _initials_match(two, one)
                               or _initials_match(list(reversed(one)), two)
                               or _initials_match(list(reversed(two)), one))
                    if matched:
                        found[(first, second)] = "iniziali"
    by_letter = {}
    for key in names:
        if len(key) >= MIN_TYPO_LENGTH:
            by_letter.setdefault(key[0], []).append(key)
    for group in by_letter.values():
        group.sort()
        for index, first in enumerate(group):
            for second in group[index + 1:]:
                matcher = SequenceMatcher(None, first, second)
                if (abs(len(first) - len(second)) <= 2 and matcher.real_quick_ratio() >= TYPO_RATIO
                        and matcher.quick_ratio() >= TYPO_RATIO and matcher.ratio() >= TYPO_RATIO):
                    found.setdefault((first, second), "quasi uguali")
    result = []
    for (first, second), why in sorted(found.items()):
        result.append((first, second, why))
    return result


def clusters(pairs: list) -> list:
    """I gruppi dubbi (unione delle coppie), ognuno di al massimo MAX_CLUSTER nomi: [[chiave], {coppia: perché}]."""
    parent = {}

    def root(key):
        top = key
        while parent[top] != top:
            top = parent[top]
        return top

    reasons = {}
    for first, second, why in pairs:
        parent.setdefault(first, first)
        parent.setdefault(second, second)
        reasons[(first, second)] = why
        first_root, second_root = root(first), root(second)
        if first_root != second_root:
            parent[second_root] = first_root
    groups = {}
    for key in parent:
        groups.setdefault(root(key), []).append(key)
    result = []
    for members in groups.values():
        if 1 < len(members) <= MAX_CLUSTER:
            members.sort()
            why = {}
            for pair, text in reasons.items():
                if pair[0] in members:
                    why[pair] = text
            result.append((members, why))
    result.sort(key=lambda entry: entry[0][0])
    return result


AI_SYSTEM = """You help clean up the artist names of a personal music library. Each group lists artist names that \
might be written forms of the same artist (surname only, initials, typos), with how many tracks use each name and \
some of their albums and years. For every group answer which names are the SAME artist: give one or more sets of \
names (copy them exactly), leave out names that are a different artist. Two people with the same surname are \
different artists; a band and its singer are different artists. Write the reason in Italian, short and concrete."""

AI_SCHEMA = {
    "type": "object",
    "properties": {
        "groups": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "group": {"type": "string"},
                    "same": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}},
                    "reason": {"type": "string"},
                },
                "required": ["group", "same", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["groups"],
    "additionalProperties": False,
}


def ask_ai(provider, groups: list, names: dict, context: dict, progress: Optional[ProgressFn] = None,
           cancel: Optional[threading.Event] = None) -> tuple:
    """({indice del gruppo: ([[chiave]], motivo)}, errori). groups: clusters; context {chiave: (brani, "album
    (anno); …")}."""
    from .ai import AIError
    answers = {}
    errors = []
    start = 0
    while start < len(groups) and not (cancel is not None and cancel.is_set()) and not errors:
        batch = groups[start:start + AI_BATCH]
        if progress is not None:
            progress(start, len(groups), f"l'AI confronta {len(batch)} gruppi di nomi d'artista")
        lines = []
        for offset, (members, _why) in enumerate(batch):
            lines.append(f"G{start + offset + 1}")
            for key in members:
                count, albums = context.get(key, (0, ""))
                lines.append(f"   {names[key]} | {count} tracks | {albums}")
        try:
            reply = provider.ask_json(AI_SYSTEM, "GROUPS\n" + "\n".join(lines), AI_SCHEMA)
            for answer in reply.get("groups", []):
                label = str(answer.get("group", ""))
                if label.startswith("G") and label[1:].isdigit():
                    index = int(label[1:]) - 1
                    if start <= index < start + len(batch):
                        by_name = {}
                        for key in groups[index][0]:
                            by_name[names[key].casefold()] = key
                        sets = []
                        for chosen in answer.get("same", []):
                            keys = []
                            for written in chosen:
                                key = by_name.get(str(written).casefold())
                                if key is not None and key not in keys:
                                    keys.append(key)
                            if len(keys) > 1:
                                sets.append(keys)
                        answers[index] = (sets, str(answer.get("reason", "")).strip())
        except AIError as exc:
            errors.append(f"nomi degli artisti: {exc}")
            log.warning("Confronto dei nomi d'artista con l'AI non riuscito: %s", exc)
        start += AI_BATCH
    result = (answers, errors)
    return result


def musicbrainz_keys(client, name: str) -> set:
    """Le chiavi (variant_key) del nome, del nome per l'ordinamento e degli alias dell'artista che MusicBrainz trova
    per name (il primo risultato, se molto sicuro); vuoto se non lo trova."""
    result = set()
    for artist in client.search_artists(name):
        for written in artist:
            if written:
                result.add(variant_key(written))
    return result
