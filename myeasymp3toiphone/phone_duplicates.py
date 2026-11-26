# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le copie della stessa canzone sull'iPhone, e quale tenere.

La stessa canzone (stesso artista e titolo, durata entro DUPLICATE_SECONDS) può stare sull'iPhone più volte:
- nello stesso album, anche scritto in un altro modo ("The Wall CD1" e "The Wall (Disc 1)", album_key): è un
  doppione, se ne tiene una sola (rank: prima i tag giusti, poi la qualità);
- in album diversi (l'album e una raccolta): è legittimo, si mostra e basta.
Due brani associati a file diversi della stessa cartella del PC, con la stessa estensione, sono canzoni diverse
anche con lo stesso titolo: sono tag sbagliati (un album con quindici "Comunque Vada"), non doppioni.

Anche all'invio: un brano del PC che sull'iPhone c'è già nello stesso album (o lo stesso file già mandato) non si
aggiunge, sostituisce la copia vecchia (send_plan)."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import PureWindowsPath

from .library import group_name
from .playlists import album_base

DUPLICATE_SECONDS = 5.0     # copie dello stesso album da rip diversi differiscono di qualche secondo
LOSSLESS = {".flac", ".wav", ".aif", ".aiff"}
# kbit/s stimati dalla dimensione (comprende tag e copertina): da TOP_KBPS un MP3 vale come un 320
TOP_KBPS = 300
QUALITY_STEPS = (TOP_KBPS, 240, 180)
BRACES = re.compile(r"\{[^}]*\}")       # "{]-Mizzy-[}" e simili, aggiunti da chi ha messo il disco in rete
# i campi che un brano dovrebbe avere: senza uno di questi i tag sono incompleti (non sbagliati)
EXPECTED_FIELDS = (("title", "titolo"), ("artist", "artista"), ("album", "album"), ("year", "anno"),
                   ("genre", "genere"), ("track_number", "numero"))
# i problemi che fanno dire "tag sbagliati": contano prima della qualità
GHOST_WEIGHT = 100
SUSPECT_WEIGHT = 10
STALE_WEIGHT = 5
MISFILED_WEIGHT = 5
JUNK_WEIGHT = 2
SAME_SIZE_SHARE = 0.05      # file entro il 5% della dimensione: grandi uguali (non decide un rip per pochi kB)


def song_key(tags) -> tuple:
    """(artista, titolo) senza maiuscole, accenti e spazi doppi."""
    result = (group_name(tags.artist or tags.album_artist or ""), group_name(tags.title or ""))
    return result


@lru_cache(maxsize=65536)
def album_key(album: str) -> str:
    """L'album senza disco ("CD1", "(Disc 2)"), parentesi e graffe: i modi diversi di scrivere lo stesso album."""
    result = album_base(BRACES.sub(" ", album or ""))
    return result


def _close(first: float, second: float) -> bool:
    """Durate entro DUPLICATE_SECONDS; una durata che non si conosce (0) non esclude niente."""
    result = not first or not second or abs(first - second) <= DUPLICATE_SECONDS
    return result


def path_key(path: str) -> str:
    """Un percorso di Windows da confrontare: barre e maiuscole non contano."""
    result = str(PureWindowsPath(path)).casefold()
    return result


def different_files_of_one_folder(first: str, second: str) -> bool:
    """Due file del PC diversi, nella stessa cartella e con la stessa estensione: canzoni diverse di un album."""
    result = False
    if first and second and path_key(first) != path_key(second):
        one = PureWindowsPath(first)
        other = PureWindowsPath(second)
        result = (str(one.parent).casefold() == str(other.parent).casefold()
                  and one.suffix.casefold() == other.suffix.casefold())
    return result


def kbps(item) -> int:
    """I kbit/s stimati di un brano dell'iPhone, dalla dimensione e dalla durata (0 se non si sa)."""
    result = 0
    if item.length > 0:
        result = int(round(item.size * 8 / item.length / 1000))
    return result


def suffix_of(item) -> str:
    result = PureWindowsPath(item.remote_path).suffix.lower()
    return result


def quality_text(item) -> str:
    """"FLAC", "MP3 ~320 kbit/s"."""
    name = suffix_of(item)[1:].upper() or "?"
    if suffix_of(item) in LOSSLESS:
        result = name
    else:
        result = f"{name} ~{kbps(item)} kbit/s"
    return result


def quality_key(item) -> tuple:
    """Più piccola = migliore: FLAC e MP3 a 320 kbit/s valgono uguale (gradino 0); sotto, conta il bitrate."""
    rate = kbps(item)
    if suffix_of(item) in LOSSLESS:
        step = 0
    else:
        step = 0
        while step < len(QUALITY_STEPS) and rate < QUALITY_STEPS[step]:
            step += 1
    result = (step, 0 if step == 0 else -rate)
    return result


def tag_problems(item, matches_pc, suspect: bool) -> tuple:
    """(peso dei tag sbagliati, [che cosa], [campi mancanti e altre mancanze]). matches_pc: True se i tag sono
    uguali a quelli del file del PC associato, False se diversi, None senza file associato."""
    weight = 0
    wrong = []
    if item.missing_file:
        weight += GHOST_WEIGHT
        wrong.append("senza file sull'iPhone")
    if suspect:
        weight += SUSPECT_WEIGHT
        wrong.append("titolo uguale a quello di altre canzoni dell'album")
    if matches_pc is False:
        weight += STALE_WEIGHT
        wrong.append("tag diversi dal file del PC")
    if item.misfiled:
        weight += MISFILED_WEIGHT
        wrong.append("nell'album sbagliato")
    if BRACES.search(item.tags.album or ""):
        weight += JUNK_WEIGHT
        wrong.append("aggiunte tra graffe nel nome dell'album")
    missing = []
    for name, label in EXPECTED_FIELDS:
        if not getattr(item.tags, name):
            missing.append(label)
    lacks = []
    if missing:
        lacks.append("senza " + ", ".join(missing))
    if item.album_without_cover:
        lacks.append("album senza immagine")
    result = (weight, wrong, lacks)
    return result


@dataclass
class DuplicateSet:
    """Le copie della stessa canzone nello stesso album: la prima è quella da tenere."""
    copies: list                                   # PhoneTrack, la migliore per prima
    reasons: dict = field(default_factory=dict)    # pid -> perché si tiene o si toglie

    @property
    def best(self):
        result = self.copies[0]
        return result

    @property
    def extra(self) -> list:
        result = self.copies[1:]
        return result


@dataclass
class Duplicates:
    sets: list = field(default_factory=list)            # DuplicateSet
    set_of: dict = field(default_factory=dict)          # pid -> DuplicateSet
    other_albums: dict = field(default_factory=dict)    # pid -> [PhoneTrack]: la stessa canzone in altri album
    suspect: set = field(default_factory=set)           # pid con un titolo che altre canzoni dell'album hanno

    def to_remove(self, items: list) -> list:
        """Le copie da togliere dei doppioni toccati da items (tutte tranne la migliore), solo quelle messe da un
        computer (le altre il computer non le può togliere)."""
        seen = set()
        result = []
        for item in items:
            chosen = self.set_of.get(item.pid)
            if chosen is not None and id(chosen) not in seen:
                seen.add(id(chosen))
                for other in chosen.extra:
                    if other.from_computer:
                        result.append(other)
        return result

    def others_of(self, item) -> list:
        """Tieni questa copia: le altre copie del suo doppione, solo quelle messe da un computer."""
        chosen = self.set_of.get(item.pid)
        result = []
        if chosen is not None:
            for other in chosen.copies:
                if other.pid != item.pid and other.from_computer:
                    result.append(other)
        return result


def _fits(item, cluster: list, sources: dict) -> bool:
    """item è la stessa canzone di tutti i brani del gruppo (durata vicina, non due file della stessa cartella)."""
    result = True
    for member in cluster:
        if not _close(member.length, item.length):
            result = False
        elif different_files_of_one_folder(sources.get(member.pid, ""), sources.get(item.pid, "")):
            result = False
    return result


def song_clusters(phone_tracks: list, sources: dict) -> list:
    """Le copie di ogni canzone: [[PhoneTrack]], anche di una copia sola. Brani senza titolo esclusi."""
    by_key = {}
    for item in phone_tracks:
        key = song_key(item.tags)
        if key[1]:
            by_key.setdefault(key, []).append(item)
    result = []
    for members in by_key.values():
        clusters = []
        for item in sorted(members, key=lambda track: (track.length, track.pid)):
            placed = False
            index = 0
            while not placed and index < len(clusters):
                if _fits(item, clusters[index], sources):
                    clusters[index].append(item)
                    placed = True
                index += 1
            if not placed:
                clusters.append([item])
        result += clusters
    return result


def _suspect_titles(clusters: list) -> set:
    """I brani il cui titolo, nello stesso album, ce l'hanno anche altre canzoni (durate diverse o file diversi della
    stessa cartella): un titolo copiato per sbaglio su più brani."""
    songs_of = {}
    for index, cluster in enumerate(clusters):
        for item in cluster:
            key = song_key(item.tags) + (album_key(item.tags.album),)
            songs_of.setdefault(key, set()).add(index)
    result = set()
    for cluster in clusters:
        for item in cluster:
            key = song_key(item.tags) + (album_key(item.tags.album),)
            if len(songs_of[key]) > 1:
                result.add(item.pid)
    return result


def _size_step(item) -> int:
    """La dimensione a gradini del SAME_SIZE_SHARE: due rip quasi uguali hanno lo stesso gradino."""
    result = 0
    if item.size > 0:
        result = int(math.log(item.size) / math.log(1 + SAME_SIZE_SHARE))
    return result


def _rank_key(item, matches: dict, suspect: set) -> tuple:
    """Più piccola = da tenere: tag sbagliati, qualità, tag incompleti, tag non confermati dal PC, playlist (più è
    meglio), messa da un computer, a parità di tutto l'MP3 a 320 prima del FLAC (sotto i 320 vince il FLAC, già
    con la qualità), file più piccolo (a gradini)."""
    weight, _wrong, lacks = tag_problems(item, matches.get(item.pid), item.pid in suspect)
    result = (weight, quality_key(item), len(lacks), 0 if matches.get(item.pid) is True else 1,
              -len(item.playlists), 0 if item.from_computer else 1, 1 if suffix_of(item) in LOSSLESS else 0,
              _size_step(item), item.pid)
    return result


def _keep_reason(item, matches: dict) -> str:
    parts = [quality_text(item)]
    if matches.get(item.pid) is True:
        parts.append("tag uguali al file del PC")
    if item.playlists:
        parts.append(f"in {len(item.playlists)} playlist")
    result = "Da tenere: " + ", ".join(parts)
    return result


def _drop_reason(item, best, matches: dict, suspect: set) -> str:
    """Perché questa copia è peggiore della migliore: il primo criterio di _rank_key in cui perde."""
    mine = _rank_key(item, matches, suspect)
    theirs = _rank_key(best, matches, suspect)
    _weight, wrong, lacks = tag_problems(item, matches.get(item.pid), item.pid in suspect)
    if mine[0] != theirs[0]:
        reason = "tag sbagliati (" + ", ".join(wrong) + ")"
    elif mine[1] != theirs[1]:
        reason = f"qualità più bassa ({quality_text(item)} contro {quality_text(best)})"
    elif mine[2] != theirs[2]:
        reason = "tag meno completi (" + ", ".join(lacks) + ")"
    elif mine[3] != theirs[3]:
        reason = "l'altra copia ha i tag uguali al file del PC"
    elif mine[4] != theirs[4]:
        reason = "l'altra copia è in più playlist"
    elif mine[5] != theirs[5]:
        reason = "l'altra copia è stata messa da un computer"
    elif mine[6] != theirs[6]:
        reason = f"a parità di tutto si preferisce {quality_text(best)} al FLAC"
    elif mine[7] != theirs[7]:
        reason = (f"stessa qualità, file più grande ({item.size / 1e6:.1f} MB contro "
                  f"{best.size / 1e6:.1f} MB)")
    else:
        reason = "copia equivalente, se ne tiene una"
    if not item.from_computer:
        reason += "; acquistata o scaricata sul telefono: un computer non la può togliere"
    result = "Da togliere: " + reason
    return result


def find(phone_tracks: list, sources: dict, matches: dict) -> Duplicates:
    """I doppioni dell'iPhone. sources: {pid: percorso del file del PC associato}; matches: {pid: True se i tag sono
    uguali a quelli del file del PC, False se diversi} (senza voce: nessun file associato)."""
    clusters = song_clusters(phone_tracks, sources)
    found = Duplicates(suspect=_suspect_titles(clusters))
    for cluster in clusters:
        by_album = {}
        for item in cluster:
            by_album.setdefault(album_key(item.tags.album), []).append(item)
        for members in by_album.values():
            if len(members) > 1:
                ordered = sorted(members, key=lambda track: _rank_key(track, matches, found.suspect))
                chosen = DuplicateSet(ordered)
                chosen.reasons[ordered[0].pid] = _keep_reason(ordered[0], matches)
                for other in ordered[1:]:
                    chosen.reasons[other.pid] = _drop_reason(other, ordered[0], matches, found.suspect)
                found.sets.append(chosen)
                for item in members:
                    found.set_of[item.pid] = chosen
        if len(by_album) > 1:
            for item in cluster:
                mine = album_key(item.tags.album)
                elsewhere = []
                for other in cluster:
                    if album_key(other.tags.album) != mine:
                        elsewhere.append(other)
                found.other_albums[item.pid] = elsewhere
    return found


# --------------------------------------------------------------------------- all'invio: sostituire, non aggiungere

@dataclass
class SendPlan:
    replaces: list = field(default_factory=list)   # (PhoneTrack, Track): la copia vecchia si sostituisce
    removes: list = field(default_factory=list)    # PhoneTrack: altre copie vecchie dello stesso album, da togliere
    kept_old: list = field(default_factory=list)   # (Track, PhoneTrack): c'è già, ma il computer non la può togliere
    sends: list = field(default_factory=list)      # Track: da copiare come brani nuovi


class PhoneIndex:
    """I brani dell'iPhone per canzone e album, e per file del PC associato: per cercarli a ogni brano inviato."""

    def __init__(self, phone_tracks: list, sources: dict) -> None:
        self.sources = sources
        self.by_song = {}
        self.by_path = {}
        for item in phone_tracks:
            key = song_key(item.tags) + (album_key(item.tags.album),)
            self.by_song.setdefault(key, []).append(item)
            source = sources.get(item.pid, "")
            if source:
                self.by_path.setdefault(path_key(source), []).append(item)

    def same_album_copies(self, track) -> list:
        """I brani dell'iPhone che sono la stessa canzone dello stesso album di track (un file del PC), o lo stesso
        file già mandato."""
        path = str(track.path)
        key = song_key(track.tags) + (album_key(track.tags.album),)
        length = getattr(track, "length", 0.0) or 0.0
        result = list(self.by_path.get(path_key(path), []))
        found = set()
        for item in result:
            found.add(item.pid)
        if key[1]:
            for item in self.by_song.get(key, []):
                source = self.sources.get(item.pid, "")
                if (item.pid not in found and _close(item.length, length)
                        and not different_files_of_one_folder(source, path)):
                    result.append(item)
                    found.add(item.pid)
        return result


def send_plan(sends: list, phone_tracks: list, sources: dict, busy: set) -> SendPlan:
    """Prima di un invio: i brani che sull'iPhone ci sono già nello stesso album sostituiscono la copia vecchia
    (quella in più playlist; le altre copie dello stesso album si tolgono). busy: pid dei brani dell'iPhone che hanno
    già un'azione (Elimina, Ricopia…): non si toccano due volte, quel brano si copia come nuovo."""
    plan = SendPlan()
    taken = set(busy)
    index = PhoneIndex(phone_tracks, sources)
    for track in sends:
        copies = []
        for item in index.same_album_copies(track):
            if item.pid not in taken:
                copies.append(item)
        writable = []
        for item in copies:
            if item.from_computer:
                writable.append(item)
        if writable:
            ordered = sorted(writable, key=lambda item: (-len(item.playlists), item.pid))
            plan.replaces.append((ordered[0], track))
            plan.removes += ordered[1:]
            for item in writable:
                taken.add(item.pid)
        else:
            plan.sends.append(track)
            if copies:
                plan.kept_old.append((track, copies[0]))
    return plan
