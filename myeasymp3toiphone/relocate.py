# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le sorgenti sparite: ritrovare sul PC i file spostati (o rinominati) dei brani dell'iPhone associati, prima di
chiedere all'utente cosa fare. Si cerca tra i brani della cartella aperta, dal più sicuro al meno sicuro:

  1. lo stesso nome e la stessa dimensione del file sparito; se il registro ha l'impronta, la si ricalcola sul
     candidato (si leggono solo pezzi del file) e deve essere la stessa;
  2. lo stesso audio con un altro nome (rinominato): un file con l'impronta che il registro ricorda (la cache dei tag
     ha quelle già calcolate); tra più copie, quella nella cartella con il nome più simile;
  3. per gli altri, l'album intero in una cartella e le regole: le stesse proposte di quelle in rosso
     (adoption.automatic_proposals: nome della cartella, numeri, titoli, durata).

Niente cambia qui: il risultato sono proposte, che l'utente conferma (si scrive solo il registro)."""

from __future__ import annotations

from pathlib import Path

from . import adoption, provenance
from .albumcheck import similarity
from .overlay import path_key

REASON_SAME_AUDIO = "stesso audio (impronta), spostato"
REASON_SAME_FILE = "stesso nome e stessa dimensione del file, spostato"
REASON_SAME_FILE_AUDIO = "stesso nome, dimensione e audio (impronta), spostato"


def _size(path: Path) -> int:
    try:
        result = path.stat().st_size
    except OSError:
        result = -1
    return result


def _by_fingerprint(link, tracks_by_key: dict, index: dict, tag_cache, used: set):
    """Il brano del PC con lo stesso audio del file sparito, o None. Con più copie dello stesso audio (la stessa
    canzone in due raccolte) vince quella nella cartella con il nome più simile a quella di prima."""
    old_folder = Path(link.path).parent.name
    result = None
    best = -1.0
    for key in index.get(link.fingerprint, []) if link.fingerprint else []:
        track = tracks_by_key.get(key)
        if track is not None and key not in used and tag_cache.fingerprint(track.path) == link.fingerprint:
            score = similarity(old_folder, track.path.parent.name)
            if score > best:
                best = score
                result = track
    return result


def _by_name(link, by_name: dict, used: set, printer):
    """(brano del PC con lo stesso nome e la stessa dimensione, motivo) o (None, ""). Con più candidati vince quello
    nella cartella con lo stesso nome di quella di prima. Se il registro ha l'impronta, deve coincidere."""
    old = Path(link.path)
    candidates = []
    for track in by_name.get(old.name.lower(), []):
        if path_key(track.path) not in used and (not link.size or _size(track.path) == link.size):
            candidates.append(track)
    chosen = None
    for track in candidates:
        if chosen is None or (track.path.parent.name.lower() == old.parent.name.lower()
                              and chosen.path.parent.name.lower() != old.parent.name.lower()):
            chosen = track
    reason = REASON_SAME_FILE
    if chosen is not None and link.fingerprint:
        if printer(chosen.path) == link.fingerprint:
            reason = REASON_SAME_FILE_AUDIO
        else:
            chosen = None              # stesso nome e dimensione, ma un altro audio
    result = (chosen, reason if chosen is not None else "")
    return result


def relocate(missing: list, pc_tracks: list, tag_cache, preferred: tuple = (), taken=frozenset(),
             printer=None) -> dict:
    """missing: [(PhoneTrack, provenance.Link)] delle sorgenti sparite; pc_tracks: i brani della cartella aperta.
    {pid: adoption.Proposal} per quelli ritrovati. Un file del PC va a un brano solo, mai a uno già associato a un
    altro brano (taken: le path_key dei file nel registro). printer(path) -> impronta (provenance.file_fingerprints,
    sostituibile nei test)."""
    if printer is None:
        def printer(path):
            value = provenance.file_fingerprints([path]).get(path, "")
            return value
    tracks_by_key = {}
    by_name = {}
    for track in pc_tracks:
        if not track.error:
            tracks_by_key[path_key(track.path)] = track
            by_name.setdefault(track.path.name.lower(), []).append(track)
    index = tag_cache.fingerprint_index() if tag_cache is not None else {}
    used = set(taken)
    result = {}
    rest = []
    for item, link in missing:
        # prima lo stesso file (nome e dimensione, l'audio verificato), poi lo stesso audio con un altro nome: così
        # una copia della stessa canzone in un'altra raccolta non passa davanti al file spostato
        found, reason = _by_name(link, by_name, used, printer)
        how = provenance.HOW_FINGERPRINT
        level = adoption.LEVEL_CERTAIN
        if found is not None and reason == REASON_SAME_FILE:
            how = provenance.HOW_RULES
            level = adoption.LEVEL_VERY_LIKELY
        if found is None:
            found = _by_fingerprint(link, tracks_by_key, index, tag_cache, used)
            reason = REASON_SAME_AUDIO
        if found is not None:
            used.add(path_key(found.path))
            result[item.pid] = adoption.Proposal(item, found, how, reason, level=level)
        else:
            rest.append(item)
    if rest:
        result.update(adoption.automatic_proposals(rest, pc_tracks, preferred, used))
    return result
