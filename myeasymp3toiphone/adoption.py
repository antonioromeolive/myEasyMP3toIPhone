# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""L'adozione: collegare i brani già sull'iPhone (messi da CopyTrans, da un altro computer…) ai file del PC, per
riempire il registro della provenienza. Dal più veloce, e per ogni brano finché uno non lo trova:

  1. cartella: una cartella il cui nome contiene il nome dell'album (senza maiuscole, accenti e punteggiatura) e dentro
     un file con lo stesso titolo, la stessa durata (entro DURATION_TOLERANCE) e lo stesso numero di traccia: molto
     probabile, proposto già spuntato; senza il numero, probabile; con il titolo solo simile, da controllare. Non
     legge l'audio: è il passo veloce.
  2. impronta dell'audio (se scelta): stesso audio = stesso brano, qualunque siano titolo, album, artista (le
     compilation, i brani "sciolti"); con più copie sul PC si sceglie quella con i tag più simili. Certo.
  3. regole: durata entro DURATION_TOLERANCE e titolo e artista somiglianti, con un candidato chiaramente migliore.
     Molto probabile: proposto già spuntato.
  4. AI (se scelta): per i dubbi veri, al più MAX_CANDIDATES candidati per brano con la cartella del PC come contesto;
     risponde quale (o nessuno), con la sicurezza e il motivo. Proposto, spuntato solo se l'AI è sicura.
Quello che resta non ha un file sul PC: è un brano "estraneo", che il programma non tocca mai da solo. Tutto si
mostra prima di scrivere, con le spunte: un brano senza spunta resta com'è.

Bloccante: va chiamato da un thread di lavoro. Le impronte dell'iPhone si ricordano (provenance.PhoneFingerprints):
la prima volta servono ~0,25 s a brano, poi solo per i brani nuovi.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from . import iphone, provenance
from .albumcheck import normalize, similarity
from .phone_library import differences

log = logging.getLogger(__name__)

DURATION_TOLERANCE = 2.0      # secondi
MAX_CANDIDATES = 5
RULE_SCORE = 0.9              # titolo e artista quasi uguali…
RULE_MARGIN = 0.15            # …e nessun altro candidato vicino
MIN_TITLE = 0.5               # sotto, un candidato non vale la pena di mostrarlo
FOLDER_TITLE = 0.9            # cartella: titolo uguale (a parte punteggiatura e parentesi)…
FOLDER_TITLE_DOUBT = 0.75     # …o almeno simile: da controllare
MIN_ALBUM_NAME = 3            # un album più corto ("A") si troverebbe in troppe cartelle
AI_BATCH = 25
SAVE_EVERY = 100

ProgressFn = Callable[[int, int, str], None]


@dataclass
class Proposal:
    phone: object             # phone_library.PhoneTrack
    pc: object                # library.Track
    how: str                  # provenance.HOW_*
    reason: str = ""
    checked: bool = True
    level: str = ""           # la certezza mostrata: certo, molto probabile, probabile, da controllare, a mano


@dataclass
class AdoptionResult:
    certain: list = field(default_factory=list)      # Proposal con l'impronta: collegati senza chiedere
    proposals: list = field(default_factory=list)    # regole e AI: da confermare
    foreign: list = field(default_factory=list)      # PhoneTrack senza un file sul PC
    already: int = 0                                 # brani già nel registro
    by_folder: int = 0                               # trovati dal nome della cartella, senza leggere l'audio
    not_from_computer: int = 0                       # acquistati o scaricati sul telefono: niente da collegare
    ai_errors: list = field(default_factory=list)
    cancelled: bool = False


def _cancelled(cancel: Optional[threading.Event]) -> bool:
    result = cancel is not None and cancel.is_set()
    return result


# --------------------------------------------------------------------------- impronte

def phone_fingerprints(phone_tracks: list, home: Path, progress: Optional[ProgressFn] = None,
                       cancel: Optional[threading.Event] = None) -> dict:
    """{sync_id: impronta} dei brani dell'iPhone; legge dal telefono solo quelle che non conosce già."""
    from pymobiledevice3.services.afc import AfcService

    known = provenance.PhoneFingerprints(home)
    result = {}
    missing = []
    for item in phone_tracks:
        value = known.get(item.remote_path, item.size)
        if value:
            result[item.sync_id] = value
        else:
            missing.append(item)

    async def work():
        lockdown = await iphone._open_lockdown()
        try:
            async with AfcService(lockdown) as afc:
                index = 0
                while index < len(missing) and not _cancelled(cancel):
                    item = missing[index]
                    try:
                        value = await provenance.phone_fingerprint(afc, item.remote_path, item.size,
                                                                   Path(item.remote_path).suffix)
                    except Exception as exc:  # noqa: BLE001 - un file che non si legge non ferma gli altri
                        log.warning("Impronta non letta dall'iPhone per %s: %s", item.remote_path, exc)
                        value = ""
                    if value:
                        known.put(item.remote_path, item.size, value)
                        result[item.sync_id] = value
                    index += 1
                    if index % SAVE_EVERY == 0:
                        known.save()       # se si annulla o si interrompe, si riprende da qui
                    if progress is not None and index % 10 == 0:
                        progress(index, len(missing), f"impronte dei brani dell'iPhone: {index} di {len(missing)}")
        finally:
            await lockdown.close()

    if missing:
        try:
            iphone._run(work())
        finally:
            known.save()
    return result


def pc_fingerprints(tracks: list, tag_cache, progress: Optional[ProgressFn] = None,
                    cancel: Optional[threading.Event] = None) -> dict:
    """{percorso: impronta} dei file del PC; quelle nuove si ricordano nella cache dei tag."""
    result = {}
    missing = []
    for track in tracks:
        value = tag_cache.fingerprint(track.path) if tag_cache is not None else ""
        if value:
            result[str(track.path)] = value
        elif not track.error:
            missing.append(str(track.path))
    if missing:
        computed = provenance.file_fingerprints(missing, progress, cancel)
        for path, value in computed.items():
            if value:
                result[path] = value
                if tag_cache is not None:
                    tag_cache.store_fingerprint(Path(path), value)
        if tag_cache is not None:
            tag_cache.save()
    return result


# --------------------------------------------------------------------------- regole

def _closest_copy(phone_track, copies: list):
    """Tra più copie dello stesso audio sul PC, quella con meno tag diversi (a parità, il percorso più corto)."""
    best = None
    best_key = None
    for track in copies:
        key = (len(differences(track.tags, phone_track.tags)), len(str(track.path)), str(track.path).lower())
        if best_key is None or key < best_key:
            best = track
            best_key = key
    return best


def _artist_of(tags) -> str:
    result = tags.artist or tags.album_artist
    return result


def _score(phone_track, track) -> float:
    title = similarity(phone_track.tags.title, track.tags.title or track.path.stem)
    artist = max(similarity(_artist_of(phone_track.tags), track.tags.artist),
                 similarity(_artist_of(phone_track.tags), track.tags.album_artist or ""))
    result = 0.6 * title + 0.4 * artist
    return result


def candidates(phone_track, by_length: list) -> list:
    """[(punteggio, Track)] in ordine, i più simili, con durata entro DURATION_TOLERANCE."""
    import bisect
    lengths = [length for length, _index, _track in by_length]
    start = bisect.bisect_left(lengths, phone_track.length - DURATION_TOLERANCE)
    end = bisect.bisect_right(lengths, phone_track.length + DURATION_TOLERANCE)
    scored = []
    for _length, _index, track in by_length[start:end]:
        if similarity(phone_track.tags.title, track.tags.title or track.path.stem) >= MIN_TITLE:
            scored.append((_score(phone_track, track), track))
    scored.sort(key=lambda pair: (-pair[0], str(pair[1].path).lower()))
    result = scored[:MAX_CANDIDATES]
    return result


# --------------------------------------------------------------------------- AI

AI_SYSTEM = """You match songs on an iPhone with the music files on the owner's PC. For each iPhone track you get up to \
five candidate PC files with a similar duration. The tags may differ (spelling, featured artists, compilations, \
remasters, live versions); the PC folder name tells the album or compilation a file belongs to, and tracks of the \
same iPhone album usually come from the same PC folder.

For every track answer with the id of the candidate that is the same recording, or "" when none is. A different \
recording (live, remix, another version, a cover) is NOT the same. Confidence: "high" only when title, artist and \
duration agree; "medium" when one detail differs but it is surely the same recording; "low" otherwise. Write the \
reason in Italian, short and concrete. Use only the ids given."""

AI_SCHEMA = {
    "type": "object",
    "properties": {
        "matches": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "track": {"type": "string"},
                    "candidate": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "reason": {"type": "string"},
                },
                "required": ["track", "candidate", "confidence", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["matches"],
    "additionalProperties": False,
}


def _duration(seconds: float) -> str:
    total = int(round(seconds))
    result = f"{total // 60}:{total % 60:02d}"
    return result


def ai_lines(batch: list) -> tuple:
    """(testo per l'AI, {id brano: (PhoneTrack, {id candidato: Track})})."""
    lines = []
    ids = {}
    for number, (phone_track, scored) in enumerate(batch, start=1):
        tags = phone_track.tags
        track_id = f"T{number}"
        lines.append(f"{track_id} | {tags.title} | artist: {tags.artist} | album artist: {tags.album_artist or '-'} | "
                     f"album: {tags.album} | {_duration(phone_track.length)}")
        options = {}
        for index, (_score_value, track) in enumerate(scored, start=1):
            candidate_id = f"{track_id}.C{index}"
            folder = "/".join(track.path.parent.parts[-2:])
            pc_tags = track.tags
            lines.append(f"   {candidate_id} | {pc_tags.title or track.path.stem} | artist: {pc_tags.artist} | "
                         f"album artist: {pc_tags.album_artist or '-'} | album: {pc_tags.album} | "
                         f"{_duration(track.length)} | folder: {folder}")
            options[candidate_id] = track
        ids[track_id] = (phone_track, options)
    result = ("\n".join(lines), ids)
    return result


def ask_ai(provider, doubtful: list, progress: Optional[ProgressFn], cancel, outcome: AdoptionResult) -> list:
    """Le proposte dell'AI per i brani dubbi [(PhoneTrack, [(punteggio, Track)])]. Chi non ha risposta resta dubbio."""
    from .ai import AIError

    proposals = []
    answered = set()
    start = 0
    while start < len(doubtful) and not _cancelled(cancel):
        batch = doubtful[start:start + AI_BATCH]
        if progress is not None:
            progress(start, len(doubtful), f"l'AI confronta {len(batch)} brani dubbi")
        text, ids = ai_lines(batch)
        try:
            reply = provider.ask_json(AI_SYSTEM, "TRACKS\n" + text, AI_SCHEMA)
            for match in reply.get("matches", []):
                entry = ids.get(str(match.get("track", "")))
                if entry is not None and entry[0].sync_id not in answered:
                    phone_track, options = entry
                    answered.add(phone_track.sync_id)
                    chosen = options.get(str(match.get("candidate", "")))
                    if chosen is not None:
                        confidence = str(match.get("confidence", "low"))
                        proposals.append(Proposal(phone_track, chosen, provenance.HOW_AI,
                                                  f"AI ({confidence}): {str(match.get('reason', '')).strip()}",
                                                  checked=confidence == "high",
                                                  level=LEVEL_LIKELY if confidence == "high" else LEVEL_CHECK))
        except AIError as exc:
            outcome.ai_errors.append(str(exc))
            log.warning("Abbinamento con l'AI non riuscito: %s", exc)
        start += AI_BATCH
    return proposals


# --------------------------------------------------------------------------- tutto insieme

LEVEL_CERTAIN = "certo"
LEVEL_VERY_LIKELY = "molto probabile"
LEVEL_LIKELY = "probabile"
LEVEL_CHECK = "da controllare"
LEVEL_MANUAL = "a mano"


def _folder_text(track) -> str:
    """Il nome della cartella del file e di quella sopra, semplificati (per cercarci il nome dell'album)."""
    parent = track.path.parent
    result = f" {normalize(parent.name)} {normalize(parent.parent.name)} "
    return result


def folder_proposals(phone_tracks: list, pc_tracks: list) -> dict:
    """{sync_id: Proposal} dal nome delle cartelle: il nome dell'album nel nome della cartella del file (o di quella
    sopra) e dentro un file con titolo e durata uguali. Veloce: non legge l'audio."""
    by_folder = {}
    texts = {}
    for track in pc_tracks:
        if not track.error and track.length > 0:
            folder = str(track.path.parent)
            by_folder.setdefault(folder, []).append(track)
            if folder not in texts:
                texts[folder] = _folder_text(track)
    folders_of_album = {}
    result = {}
    for item in phone_tracks:
        album = normalize(item.tags.album or "")
        if len(album) >= MIN_ALBUM_NAME:
            if album not in folders_of_album:
                found = []
                for folder, text in texts.items():
                    if f" {album} " in text or (len(album) >= 6 and album in text):
                        found.append(folder)
                folders_of_album[album] = found
            best = None
            best_key = None
            for folder in folders_of_album[album]:
                for track in by_folder[folder]:
                    title = similarity(item.tags.title, track.tags.title or track.path.stem)
                    same_length = abs(track.length - item.length) <= DURATION_TOLERANCE
                    same_number = bool(item.tags.track_number) and item.tags.track_number == track.tags.track_number
                    key = (title >= FOLDER_TITLE, same_length, same_number, title)
                    if title >= FOLDER_TITLE_DOUBT and same_length and (best_key is None or key > best_key):
                        best = track
                        best_key = key
            if best is not None:
                folder_name = best.path.parent.name
                if best_key[0] and best_key[2]:
                    proposal = Proposal(item, best, provenance.HOW_FOLDER,
                                        f"cartella \"{folder_name}\": stesso titolo, numero e durata",
                                        checked=True, level=LEVEL_VERY_LIKELY)
                elif best_key[0]:
                    proposal = Proposal(item, best, provenance.HOW_FOLDER,
                                        f"cartella \"{folder_name}\": stesso titolo e durata",
                                        checked=True, level=LEVEL_LIKELY)
                else:
                    proposal = Proposal(item, best, provenance.HOW_FOLDER,
                                        f"cartella \"{folder_name}\": titolo simile, stessa durata",
                                        checked=False, level=LEVEL_CHECK)
                result[item.sync_id] = proposal
    return result


def _near_in_length(pc_tracks: list, phone_tracks: list) -> list:
    """I file del PC con una durata vicina a quella di almeno un brano: solo di questi serve l'impronta."""
    lengths = []
    for item in phone_tracks:
        lengths.append(item.length)
    lengths.sort()
    import bisect
    result = []
    for track in pc_tracks:
        start = bisect.bisect_left(lengths, track.length - DURATION_TOLERANCE)
        if start < len(lengths) and lengths[start] <= track.length + DURATION_TOLERANCE:
            result.append(track)
    return result


def adopt(phone_tracks: list, pc_tracks: list, registry, home: Path, tag_cache=None, provider=None,
          progress: Optional[ProgressFn] = None, cancel: Optional[threading.Event] = None,
          use_fingerprint: bool = True, read_phone: bool = True, replace_known: bool = False) -> AdoptionResult:
    """Le sorgenti dei brani dell'iPhone tra i file pc_tracks. use_fingerprint: anche l'impronta dell'audio (lenta la
    prima volta); read_phone: le impronte che mancano si leggono dall'iPhone (connesso), altrimenti solo quelle
    ricordate. replace_known: anche i brani che hanno già una sorgente (scelti a mano)."""
    outcome = AdoptionResult()
    unknown = []
    for item in phone_tracks:
        if not item.from_computer:
            outcome.not_from_computer += 1
        elif registry.get(item.sync_id) is not None and not replace_known:
            outcome.already += 1
        else:
            unknown.append(item)
    usable = []
    for track in pc_tracks:
        if not track.error:
            usable.append(track)
    if unknown and usable:
        if progress is not None:
            progress(0, 0, "nomi delle cartelle")
        by_folder = folder_proposals(unknown, usable)
        remaining = []
        for item in unknown:
            proposal = by_folder.get(item.sync_id)
            if proposal is not None and proposal.level == LEVEL_VERY_LIKELY:
                outcome.proposals.append(proposal)
                outcome.by_folder += 1
            else:
                remaining.append(item)
        _adopt_remaining(remaining, usable, by_folder, home, tag_cache, provider, progress, cancel, use_fingerprint,
                         read_phone, outcome)
    elif unknown:
        outcome.foreign += unknown          # nessun file sul PC con cui confrontare
    outcome.cancelled = _cancelled(cancel)
    if outcome.cancelled:
        # annullato: niente proposte a metà (i brani senza impronta sembrerebbero dubbi); le impronte lette restano
        outcome.certain = []
        outcome.proposals = []
        outcome.foreign = []
    return outcome


def _adopt_remaining(unknown: list, usable: list, by_folder: dict, home: Path, tag_cache, provider, progress, cancel,
                     use_fingerprint: bool, read_phone: bool, outcome: AdoptionResult) -> None:
    """Impronta, regole e AI per i brani che il nome della cartella non ha trovato con sicurezza."""
    pc_prints = {}
    phone_prints = {}
    if unknown and use_fingerprint and not _cancelled(cancel):
        if progress is not None:
            progress(0, 0, "impronte dei file del PC")
        pc_prints = pc_fingerprints(_near_in_length(usable, unknown), tag_cache, progress, cancel)
        if not _cancelled(cancel) and read_phone:
            phone_prints = phone_fingerprints(unknown, home, progress, cancel)
        elif not _cancelled(cancel):
            known = provenance.PhoneFingerprints(home)
            for item in unknown:
                value = known.get(item.remote_path, item.size)
                if value:
                    phone_prints[item.sync_id] = value
    if unknown and not _cancelled(cancel):
        by_print = {}
        for track in usable:
            value = pc_prints.get(str(track.path))
            if value:
                by_print.setdefault(value, []).append(track)
        by_length = _by_length(usable)
        doubtful = []
        for item in unknown:
            copies = by_print.get(phone_prints.get(item.sync_id, ""), [])
            folder = by_folder.get(item.sync_id)
            if copies:
                chosen = _closest_copy(item, copies)
                note = "stesso audio" if len(copies) == 1 else f"stesso audio (la più simile di {len(copies)} copie)"
                outcome.certain.append(Proposal(item, chosen, provenance.HOW_FINGERPRINT, note, level=LEVEL_CERTAIN))
            elif folder is not None:
                outcome.proposals.append(folder)
                outcome.by_folder += 1
            else:
                scored = candidates(item, by_length)
                if not scored:
                    outcome.foreign.append(item)
                elif scored[0][0] >= RULE_SCORE and (len(scored) == 1 or scored[1][0] <= scored[0][0] - RULE_MARGIN):
                    outcome.proposals.append(Proposal(item, scored[0][1], provenance.HOW_RULES,
                                                      "stessa durata, titolo e artista quasi uguali (audio diverso: "
                                                      "forse un'altra codifica)", level=LEVEL_VERY_LIKELY))
                else:
                    doubtful.append((item, scored))
        if doubtful and provider is not None and not _cancelled(cancel):
            ai_proposals = ask_ai(provider, doubtful, progress, cancel, outcome)
            outcome.proposals += ai_proposals
            decided = set()
            for proposal in ai_proposals:
                decided.add(proposal.phone.sync_id)
            remaining = []
            for item, scored in doubtful:
                if item.sync_id not in decided:
                    remaining.append((item, scored))
            doubtful = remaining
        for item, scored in doubtful:
            # senza AI, o senza risposta: il candidato migliore, non spuntato
            outcome.proposals.append(Proposal(item, scored[0][1], provenance.HOW_RULES,
                                              f"il più simile di {len(scored)} candidati: controlla", checked=False,
                                              level=LEVEL_CHECK))


# --------------------------------------------------------------------------- Associa sorgente (uno o una cartella)

def _phone_print(phone_track, home: Path, read_phone: bool) -> str:
    """L'impronta di un brano dell'iPhone: dalla memoria, o letta dal telefono se read_phone (iPhone connesso)."""
    result = provenance.PhoneFingerprints(home).get(phone_track.remote_path, phone_track.size)
    if not result and read_phone and phone_track.sync_id:
        try:
            result = phone_fingerprints([phone_track], home).get(phone_track.sync_id, "")
        except Exception as exc:  # noqa: BLE001 - senza impronta si va avanti con titolo e durata
            log.warning("Impronta non letta dall'iPhone: %s", exc)
            result = ""
    return result


def _by_length(tracks: list) -> list:
    result = []
    for index, track in enumerate(tracks):
        if track.length > 0 and not track.error:
            result.append((track.length, index, track))
    result.sort(key=lambda entry: (entry[0], entry[1]))
    return result


def rank_sources(phone_track, pc_tracks: list, home: Path, tag_cache=None, provider=None,
                 read_phone: bool = True) -> list:
    """I file del PC che possono essere la sorgente del brano, il più probabile per primo (Proposal):
      1. stesso audio (impronta), tra tutti i file con durata entro DURATION_TOLERANCE, senza filtro sul titolo
         (le compilation con titoli diversi): certo;
      2. titolo, artista e durata (candidates);
      3. se non c'è un'impronta uguale e i primi candidati sono vicini, l'AI sceglie (se c'è un fornitore)."""
    proposals = []
    near = []
    for track in pc_tracks:
        if not track.error and track.length > 0 and abs(track.length - phone_track.length) <= DURATION_TOLERANCE:
            near.append(track)
    printed = _phone_print(phone_track, home, read_phone) if near else ""
    exact = []
    if printed:
        prints = pc_fingerprints(near, tag_cache)
        for track in near:
            if prints.get(str(track.path)) == printed:
                exact.append(track)
    exact.sort(key=lambda track: (len(differences(track.tags, phone_track.tags)), str(track.path).lower()))
    for track in exact:
        proposals.append(Proposal(phone_track, track, provenance.HOW_FINGERPRINT, "stesso audio (impronta): certo"))
    exact_ids = set()
    for track in exact:
        exact_ids.add(id(track))
    scored = []
    for score, track in candidates(phone_track, _by_length(pc_tracks)):
        if id(track) not in exact_ids:
            scored.append((score, track))
    close = len(scored) > 1 and scored[1][0] > scored[0][0] - RULE_MARGIN
    if not exact and provider is not None and scored and (close or scored[0][0] < RULE_SCORE):
        outcome = AdoptionResult()
        chosen = ask_ai(provider, [(phone_track, scored)], None, None, outcome)
        if chosen:
            proposals.append(Proposal(phone_track, chosen[0].pc, provenance.HOW_AI, chosen[0].reason))
            remaining = []
            for score, track in scored:
                if track is not chosen[0].pc:
                    remaining.append((score, track))
            scored = remaining
    for score, track in scored:
        proposals.append(Proposal(phone_track, track, provenance.HOW_RULES,
                                  f"titolo, artista e durata simili ({score:.0%})"))
    return proposals


def link_for(proposal: Proposal, overlay=None, fingerprint: str = ""):
    """La riga del registro per una proposta confermata."""
    path = proposal.pc.path
    try:
        info = path.stat()
        size, mtime = info.st_size, info.st_mtime
    except OSError:
        size, mtime = 0, 0.0
    result = provenance.Link(sync_id=proposal.phone.sync_id, pc=provenance.computer_name(), path=str(path),
                             size=size, mtime=mtime, signature=overlay.signature(path) if overlay is not None else "",
                             fingerprint=fingerprint, how=proposal.how)
    return result
