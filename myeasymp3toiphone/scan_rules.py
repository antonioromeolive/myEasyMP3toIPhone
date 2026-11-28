# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le regole dei Controlli aggiunte con checks_requirements.md (R18-R31), più RuleView: i brani come li vedono le
regole, con le correzioni delle regole già passate.

Le regole girano a livelli (checks_requirements.md, sezione 6): file, campi del brano, nomi, coerenza dell'album,
completezza, doppioni. Ogni livello vede le correzioni proposte da quelli prima come già fatte (RuleView.apply), così
due regole non propongono due correzioni diverse dello stesso campo. Le regole sui nomi e sugli album guardano tutta
la musica (RuleView.all), ma segnalano solo quello che tocca i brani controllati (RuleView.selected)."""

from __future__ import annotations

import re
from dataclasses import replace

from . import cue
from .library import UNKNOWN_ALBUM, assign_groups, group_by_album, is_various_artists, phone_group_key
from .names import (
    LEVEL_ACCENTS, LEVEL_CASE, LEVEL_PUNCT, POLICY_FIRST, POLICY_MOST, REPLACEMENT_CHAR, choose_spelling,
    clean_spaces, fold, repaired_mojibake,
)
from .scan import (
    FIX_TAGS, KIND_DUPLICATE, KIND_FEW_TRACKS, KIND_FORMAT, KIND_MISSING_TAGS, KIND_NAMES, KIND_SPLIT,
    KIND_UNREADABLE, SEVERITY_HIGH, SEVERITY_LOW, SEVERITY_MEDIUM, Fix, Issue, _tracks_text,
)
from .tags import OLD_TAG_NAMES

SUPPORTED_MUSIC = (".mp3", ".flac", ".m4a")          # D-7 (con M4A, D-9): gli altri si segnalano
MAX_PATH = 260                                        # Windows: oltre, molti programmi non aprono il file
NEAR_MAX_PATH = 240
NAME_FIELDS = ("title", "artist", "album_artist", "album")
ARTIST_FIELDS = ("artist", "album_artist")
NUMBERED_TITLE = re.compile(r"^\s*0*(\d{1,3})\s*[-–._]\s+(\S.*)$")
FILE_NUMBER = re.compile(r"^\s*(?:(\d{1,2})-)?(\d{1,3})(?=[\s._-])")    # "05 - …", "05. …", "1-05 - …" (disco 1)
MANY = 15                                             # quanti nomi o brani si elencano nel dettaglio


# --------------------------------------------------------------------------- i brani visti dalle regole

class RuleView:
    """Copie dei brani: selected quelli controllati, all anche il resto della musica (context), quando si controlla
    una parte. Le regole lavorano su queste copie; apply ci scrive le correzioni proposte, così le regole dopo le
    vedono come già fatte. I brani veri non cambiano."""

    def __init__(self, tracks: list, context: list = None) -> None:
        self.by_path = {}
        self.selected = []
        self.all = []
        for track in tracks:
            copy = self._copy(track)
            self.by_path[str(track.path)] = copy
            self.selected.append(copy)
            self.all.append(copy)
        for track in context or []:
            if str(track.path) not in self.by_path:
                copy = self._copy(track)
                self.by_path[str(track.path)] = copy
                self.all.append(copy)
        self.partial = len(self.all) > len(self.selected)
        assign_groups(self.all)

    @staticmethod
    def _copy(track):
        result = replace(track, tags=track.tags.copy(), group_key=None)
        return result

    def apply(self, issues: list) -> None:
        """Le correzioni dei tag dei problemi, sulle copie; poi gli album si raggruppano di nuovo."""
        changed = False
        for issue in issues:
            if issue.fix is not None and issue.fix.action == FIX_TAGS:
                for path, values in issue.fix.changes:
                    track = self.by_path.get(str(path))
                    if track is not None:
                        for name, value in values.items():
                            if name not in OLD_TAG_NAMES:
                                setattr(track.tags, name, value)
                                changed = True
        if changed:
            assign_groups(self.all)

    def selected_paths(self) -> set:
        result = set()
        for track in self.selected:
            result.add(str(track.path))
        return result

    def selected_albums(self) -> dict:
        """{album_key: tutti i brani dell'album (anche quelli non controllati)} degli album dei brani controllati."""
        wanted = set()
        for track in self.selected:
            wanted.add(track.album_key)
        groups = group_by_album(self.all)
        result = {}
        for key, album_tracks in groups.items():
            if key in wanted:
                result[key] = album_tracks
        return result


def _changes_list(wanted: dict) -> list:
    """{percorso: {campo: valore}} -> [(percorso, valori)], nell'ordine in cui sono arrivati."""
    result = []
    for path, values in wanted.items():
        if values:
            result.append((path, values))
    return result


def _set(wanted: dict, track, name: str, value) -> None:
    if getattr(track.tags, name) != value:
        wanted.setdefault(track.path, {})[name] = value


def _names_line(names: list) -> str:
    quoted = []
    for name in names[:MANY]:
        quoted.append(f"\"{name}\"")
    result = ", ".join(quoted)
    if len(names) > MANY:
        result += f" e altri {len(names) - MANY}"
    return result


# --------------------------------------------------------------------------- livello 1: file

def detect_unsupported_formats(tracks: list) -> list:
    """R18: i file musicali che non sono MP3, FLAC o M4A (D-7)."""
    by_format = {}
    for track in tracks:
        suffix = track.path.suffix.lower()
        if suffix not in SUPPORTED_MUSIC:
            by_format.setdefault(suffix.lstrip(".").upper(), []).append(track.path)
    issues = []
    if by_format:
        files = []
        parts = []
        for name in sorted(by_format):
            files += by_format[name]
            parts.append(f"{name} {len(by_format[name])}")
        issues.append(Issue(
            KIND_FORMAT, SEVERITY_MEDIUM, f"{_tracks_text(len(files))} in un formato non supportato ({', '.join(parts)})",
            "Il programma lavora con MP3, FLAC e M4A. Gli altri formati non si inviano all'iPhone come si deve: l'app "
            "Musica non suona OGG, Opus e WMA, e in WAV e AIFF i tag (titolo, artista, album) non arrivano.",
            files, rule_id="R18"))
    return issues


def long_path_files(tracks: list) -> tuple:
    """(percorsi troppo lunghi, percorsi vicini al limite)."""
    too_long = []
    near = []
    for track in tracks:
        length = len(str(track.path))
        if length >= MAX_PATH:
            too_long.append(track.path)
        elif length >= NEAR_MAX_PATH:
            near.append(track.path)
    result = (too_long, near)
    return result


def detect_long_paths(tracks: list) -> list:
    """R19: percorsi oltre il limite di Windows (260 caratteri: molti programmi non aprono il file, e il programma
    lo vede illeggibile) o vicini (240)."""
    too_long, near = long_path_files(tracks)
    issues = []
    if too_long:
        issues.append(Issue(
            KIND_UNREADABLE, SEVERITY_HIGH, f"{_tracks_text(len(too_long))} con il percorso troppo lungo",
            f"Il percorso completo (cartelle + nome del file) supera i {MAX_PATH} caratteri, il limite di Windows: "
            "molti programmi non aprono questi file, e copiarli o inviarli può non riuscire.", too_long,
            rule_id="R19.1"))
    if near:
        issues.append(Issue(
            KIND_UNREADABLE, SEVERITY_LOW, f"{_tracks_text(len(near))} con il percorso vicino al limite",
            f"Il percorso completo supera i {NEAR_MAX_PATH} caratteri: un nome di cartella un po' più lungo lo porta "
            f"oltre il limite di Windows ({MAX_PATH}).", near, rule_id="R19.2"))
    return issues


# --------------------------------------------------------------------------- livello 2: campi del brano

def _title_without_prefix(track) -> str:
    """Il titolo senza il numero di traccia ("05 - Titolo", con 5 il numero del brano) o senza l'artista davanti
    ("Artista - Titolo"); "" se non c'è niente da togliere."""
    title = track.tags.title or ""
    result = ""
    match = NUMBERED_TITLE.match(title)
    if match and track.tags.track_number and int(match.group(1)) == track.tags.track_number:
        result = match.group(2).strip()
    artist = track.tags.artist or ""
    prefix = f"{artist} - "
    if not result and artist and len(title) > len(prefix) and fold(title[:len(prefix)], LEVEL_CASE) == \
            fold(prefix, LEVEL_CASE):
        result = title[len(prefix):].strip()
    return result


def detect_title_prefixes(tracks: list) -> list:
    """R20: titoli con davanti il numero di traccia o l'artista."""
    changes = []
    for track in tracks:
        if not track.error:
            title = _title_without_prefix(track)
            if title:
                changes.append((track.path, {"title": title}))
    issues = []
    if changes:
        files = []
        for path, _values in changes:
            files.append(path)
        issues.append(Issue(
            KIND_MISSING_TAGS, SEVERITY_LOW, f"{_tracks_text(len(changes))} con il numero o l'artista nel titolo",
            "Il titolo comincia con il numero di traccia (\"05 - Titolo\") o con il nome dell'artista (\"Artista - "
            "Titolo\"): sull'iPhone si vede due volte. La correzione lascia solo il titolo.", files,
            Fix(FIX_TAGS, "Togli numero e artista dal titolo", changes=changes), rule_id="R20"))
    return issues


def detect_spaces(tracks: list) -> list:
    """R21: spazi all'inizio, alla fine o doppi, e lettere accentate salvate in due modi diversi (D-3)."""
    changes = []
    for track in tracks:
        if not track.error:
            wanted = {}
            for name in NAME_FIELDS:
                value = getattr(track.tags, name) or ""
                cleaned = clean_spaces(value)
                if cleaned != value:
                    wanted[name] = cleaned
            if wanted:
                changes.append((track.path, wanted))
    issues = []
    if changes:
        files = []
        for path, _values in changes:
            files.append(path)
        issues.append(Issue(
            KIND_MISSING_TAGS, SEVERITY_LOW, f"{_tracks_text(len(changes))} con spazi in più nei tag",
            "Titolo, artista, artista dell'album o album hanno spazi all'inizio, alla fine o doppi (o una lettera "
            "accentata salvata in un modo diverso dal solito, che a schermo non si vede). Il programma li considera "
            "uguali agli altri, ma l'iPhone tiene la grafia del primo brano che riceve: meglio che sia pulita.",
            files, Fix(FIX_TAGS, "Togli gli spazi in più", changes=changes), rule_id="R21"))
    return issues


def detect_mojibake(tracks: list) -> list:
    """R22: caratteri rovinati da una codifica sbagliata ("PerchÃ©"): con la correzione quando il testo giusto è
    certo, a mano quando c'è il carattere "�" (l'originale è perso)."""
    changes = []
    lost = []
    for track in tracks:
        if not track.error:
            wanted = {}
            broken = False
            for name in NAME_FIELDS:
                value = getattr(track.tags, name) or ""
                repaired = repaired_mojibake(value)
                if repaired:
                    wanted[name] = repaired
                elif REPLACEMENT_CHAR in value:
                    broken = True
            if wanted:
                changes.append((track.path, wanted))
            if broken:
                lost.append(track.path)
    issues = []
    if changes:
        files = []
        for path, _values in changes:
            files.append(path)
        issues.append(Issue(
            KIND_MISSING_TAGS, SEVERITY_MEDIUM, f"{_tracks_text(len(changes))} con lettere accentate rovinate",
            "Testi come \"PerchÃ©\" invece di \"Perché\": il tag è stato scritto con una codifica e letto con un'altra. "
            "Sull'iPhone diventano un artista o un album in più. La correzione rimette le lettere giuste.", files,
            Fix(FIX_TAGS, "Rimetti le lettere accentate", changes=changes), rule_id="R22.1"))
    if lost:
        issues.append(Issue(
            KIND_MISSING_TAGS, SEVERITY_MEDIUM, f"{_tracks_text(len(lost))} con il carattere \"{REPLACEMENT_CHAR}\" nei tag",
            f"Al posto di qualche lettera (di solito accentata) c'è \"{REPLACEMENT_CHAR}\": la lettera giusta è persa e "
            "il programma non la può indovinare.", lost, rule_id="R22.2"))
    return issues


# --------------------------------------------------------------------------- livello 3: nomi

def _name_usage(tracks: list, key_of) -> dict:
    """{chiave: ([grafie in ordine], {grafia: brani}, {percorso dei brani})} per i nomi di artista e artista
    dell'album; ogni brano conta una volta per grafia."""
    result = {}
    for track in tracks:
        seen = set()
        for name in ARTIST_FIELDS:
            value = getattr(track.tags, name) or ""
            if value and value not in seen:
                seen.add(value)
                key = key_of(value)
                if key:
                    spellings, counts, paths = result.setdefault(key, ([], {}, set()))
                    if value not in counts:
                        spellings.append(value)
                        counts[value] = 0
                    counts[value] += 1
                    paths.add(str(track.path))
    return result


def _rename_changes(tracks: list, spellings: set, chosen: str) -> list:
    """Le correzioni che scrivono chosen al posto di ognuna delle grafie, in artista e artista dell'album."""
    wanted = {}
    for track in tracks:
        for name in ARTIST_FIELDS:
            value = getattr(track.tags, name) or ""
            if value in spellings and value != chosen:
                wanted.setdefault(track.path, {})[name] = chosen
    result = _changes_list(wanted)
    return result


def detect_spelling_variants(view: RuleView) -> list:
    """R23: lo stesso nome d'artista scritto con maiuscole, accenti o spazi diversi, in tutta la musica (D-1, D-2,
    D-3). Vince la grafia con le iniziali maiuscole più usata; con accenti diversi ("Perché"/"Perchè") il problema
    dice di controllare."""
    usage = _name_usage(view.all, lambda value: fold(value, LEVEL_ACCENTS))
    selected = view.selected_paths()
    issues = []
    number = 0
    for key in sorted(usage):
        spellings, counts, paths = usage[key]
        if len(spellings) > 1 and paths & selected:
            number += 1
            choice = choose_spelling(spellings, counts, POLICY_MOST)
            chosen = choice.spelling
            others = []
            for spelling in spellings:
                if spelling != chosen:
                    others.append(spelling)
            changes = _rename_changes(view.all, set(spellings), chosen)
            files = []
            for path, _values in changes:
                files.append(path)
            lines = []
            for spelling in spellings:
                lines.append(f"\"{spelling}\" ({_tracks_text(counts[spelling])})")
            detail = (f"Lo stesso nome compare come {', '.join(lines)}. Il programma li mostra insieme, ma l'iPhone "
                      "tiene la grafia del primo brano che riceve e non la cambia più: meglio una grafia sola. Vince "
                      "quella con le iniziali maiuscole, la più usata.")
            title = f"\"{chosen}\" scritto anche come {_names_line(others)}"
            severity = SEVERITY_MEDIUM
            if choice.accents_differ:
                title = f"Accenti diversi: {title}"
                detail += (" Attenzione: le grafie hanno accenti diversi e il programma non sa quale è giusto: ha "
                           f"scelto \"{chosen}\". Controlla prima di applicare.")
                severity = SEVERITY_LOW
            issues.append(Issue(KIND_NAMES, severity, title, detail, files,
                                Fix(FIX_TAGS, f"Scrivi ovunque \"{chosen}\"", changes=changes),
                                rule_id=f"R23.{number}"))
    return issues


# --------------------------------------------------------------------------- livello 4: coerenza dell'album

def _album_label(key: tuple) -> str:
    result = f"{key[0]} — {key[1]}"
    return result


def _distinct(values: list) -> list:
    result = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def detect_album_name_spellings(view: RuleView) -> list:
    """R24: il nome dell'album scritto in modi diversi (maiuscole, accenti, spazi) nello stesso album: vince il più
    usato, a parità il primo nell'ordine dei brani (D-9)."""
    issues = []
    number = 0
    albums = view.selected_albums()
    for key in sorted(albums, key=lambda k: (k[0].casefold(), k[1].casefold())):
        album_tracks = albums[key]
        values = []
        counts = {}
        for track in album_tracks:
            value = track.tags.album or ""
            if value:
                values.append(value)
                counts[value] = counts.get(value, 0) + 1
        spellings = _distinct(values)
        if len(spellings) > 1:
            number += 1
            chosen = choose_spelling(spellings, counts, POLICY_MOST, capitals=False).spelling
            wanted = {}
            for track in album_tracks:
                if track.tags.album and track.tags.album != chosen:
                    _set(wanted, track, "album", chosen)
            changes = _changes_list(wanted)
            others = []
            for spelling in spellings:
                if spelling != chosen:
                    others.append(spelling)
            issues.append(Issue(
                KIND_SPLIT, SEVERITY_MEDIUM, f"{_album_label(key)}: il nome dell'album scritto anche come "
                f"{_names_line(others)}",
                "I brani dello stesso album hanno il nome scritto con maiuscole, accenti o spazi diversi. L'iPhone tiene "
                "la grafia del primo brano che riceve: meglio una sola. Vince la più usata nell'album.",
                [track.path for track in album_tracks],
                Fix(FIX_TAGS, f"Album \"{chosen}\" su tutti i brani", changes=changes), rule_id=f"R24.{number}"))
    return issues


def detect_album_artist_spellings(view: RuleView) -> list:
    """R25 (D-1): l'artista dell'album identico su tutti i brani dell'album, anche fra le grafie di "artisti vari"
    ("AA.VV." e "Artisti Vari") e sui brani dove è vuoto. Vince la grafia con le iniziali maiuscole, a parità la
    prima nell'ordine dei brani."""
    issues = []
    number = 0
    albums = view.selected_albums()
    for key in sorted(albums, key=lambda k: (k[0].casefold(), k[1].casefold())):
        album_tracks = albums[key]
        values = []
        empty = 0
        for track in album_tracks:
            if track.tags.album_artist:
                values.append(track.tags.album_artist)
            else:
                empty += 1
        spellings = _distinct(values)
        if len(spellings) > 1 or (spellings and empty):
            number += 1
            chosen = choose_spelling(spellings, policy=POLICY_FIRST).spelling
            wanted = {}
            for track in album_tracks:
                _set(wanted, track, "album_artist", chosen)
            changes = _changes_list(wanted)
            parts = []
            if len(spellings) > 1:
                parts.append("scritto in modi diversi: " + _names_line(spellings))
            if empty:
                parts.append(f"vuoto su {_tracks_text(empty)}")
            issues.append(Issue(
                KIND_SPLIT, SEVERITY_HIGH if len(spellings) > 1 else SEVERITY_MEDIUM,
                f"{_album_label(key)}: artista dell'album {'; '.join(parts)}",
                "L'artista dell'album deve essere identico su tutti i brani dell'album, anche nelle maiuscole: con "
                "grafie diverse (per esempio \"AA.VV.\" e \"Artisti Vari\") l'iPhone divide l'album in due. Vince la "
                "grafia con le iniziali maiuscole; i brani senza artista dell'album lo ricevono.",
                [track.path for track in album_tracks],
                Fix(FIX_TAGS, f"Artista dell'album \"{chosen}\" su tutti i brani", changes=changes),
                rule_id=f"R25.{number}"))
    return issues


def _single_artist(album_tracks: list) -> str:
    """L'artista dei brani, se è lo stesso (identico) su tutti; "" altrimenti."""
    artists = set()
    for track in album_tracks:
        artists.add(track.tags.artist or "")
    result = ""
    if len(artists) == 1:
        result = artists.pop()
    return result


def detect_album_artist_from_artist(view: RuleView) -> list:
    """R26 (D-1, D-9): un album con tutti i brani dello stesso artista prende quell'artista come artista dell'album,
    quando l'artista dell'album è vuoto, o è "artisti vari" (una compilation segnata per sbaglio: si toglie anche la
    spunta compilation)."""
    issues = []
    number = 0
    albums = view.selected_albums()
    for key in sorted(albums, key=lambda k: (k[0].casefold(), k[1].casefold())):
        album_tracks = albums[key]
        artist = _single_artist(album_tracks)
        album_artists = set()
        for track in album_tracks:
            album_artists.add(track.tags.album_artist or "")
        empty = album_artists == {""}
        various = len(album_artists) == 1 and is_various_artists(next(iter(album_artists))) and len(album_tracks) > 1
        if artist and key[1] != UNKNOWN_ALBUM and (empty or various):
            number += 1
            wanted = {}
            for track in album_tracks:
                _set(wanted, track, "album_artist", artist)
                if various:
                    _set(wanted, track, "compilation", False)
            if various:
                title = f"{_album_label(key)}: \"artisti vari\" ma i brani sono tutti di {artist}"
                detail = ("L'artista dell'album dice che è una compilation, ma tutti i brani sono dello stesso artista: "
                          "sull'iPhone l'album finisce tra le compilation invece che sotto l'artista. La correzione "
                          f"mette \"{artist}\" come artista dell'album e toglie la spunta Compilation.")
                severity = SEVERITY_MEDIUM
            else:
                title = f"{_album_label(key)}: senza artista dell'album"
                detail = ("Nessun brano ha l'artista dell'album e sono tutti dello stesso artista: la correzione lo "
                          "scrive anche come artista dell'album, così l'album resta intero anche se un brano un "
                          "giorno avrà un ospite.")
                severity = SEVERITY_LOW
            issues.append(Issue(
                KIND_SPLIT, severity, title, detail, [track.path for track in album_tracks],
                Fix(FIX_TAGS, f"Artista dell'album \"{artist}\"", changes=_changes_list(wanted)),
                rule_id=f"R26.{number}"))
    return issues


def detect_compilation_flags(view: RuleView) -> list:
    """R27: la spunta Compilation uguale su tutti i brani dell'album e d'accordo con l'artista dell'album: accesa
    con "artisti vari", spenta se i brani sono tutti dello stesso artista, altrimenti come la maggior parte dei brani."""
    issues = []
    number = 0
    albums = view.selected_albums()
    for key in sorted(albums, key=lambda k: (k[0].casefold(), k[1].casefold())):
        album_tracks = albums[key]
        flags = []
        album_artist = ""
        for track in album_tracks:
            flags.append(bool(track.tags.compilation))
            if not album_artist and track.tags.album_artist:
                album_artist = track.tags.album_artist
        various = bool(album_artist) and is_various_artists(album_artist)
        single = bool(_single_artist(album_tracks))
        on = flags.count(True)
        if various:
            target = True
            why = f"l'artista dell'album è \"{album_artist}\": è una compilation"
        elif single:
            target = False
            why = "i brani sono tutti dello stesso artista: non è una compilation"
        else:
            target = on * 2 >= len(flags)
            why = "vale quello che ha la maggior parte dei brani"
        wanted = {}
        for track in album_tracks:
            _set(wanted, track, "compilation", target)
        changes = _changes_list(wanted)
        if changes and key[1] != UNKNOWN_ALBUM:
            number += 1
            mixed = 0 < on < len(flags)
            if mixed:
                title = f"{_album_label(key)}: la spunta Compilation c'è su {on} brani su {len(flags)}"
            elif target:
                title = f"{_album_label(key)}: manca la spunta Compilation"
            else:
                title = f"{_album_label(key)}: spunta Compilation su un album di un solo artista"
            if target:
                action = f"La correzione la accende su tutti i brani ({why})."
                described = "Compilation accesa su tutti i brani"
            else:
                action = f"La correzione la spegne su tutti i brani ({why})."
                described = "Compilation spenta su tutti i brani"
            issues.append(Issue(
                KIND_SPLIT, SEVERITY_MEDIUM if mixed or target else SEVERITY_LOW, title,
                "Sull'iPhone la spunta Compilation decide se l'album sta tra le compilation; diversa tra i brani, "
                f"l'album può dividersi. {action}", [track.path for track in album_tracks],
                Fix(FIX_TAGS, described, changes=changes), rule_id=f"R27.{number}"))
    return issues


def detect_phone_merges(view: RuleView) -> list:
    """R28: album diversi sul PC che l'iPhone unisce, perché per lui gli zeri davanti ai numeri non contano
    ("Raccolta 01" = "Raccolta 1", library.phone_group_key): l'album sull'iPhone prende il nome arrivato prima. La
    correzione scrive su tutti il nome più usato."""
    groups = group_by_album(view.all)
    by_phone = {}
    for key in groups:
        if key[1] != UNKNOWN_ALBUM:
            phone_key = (phone_group_key(key[0]), phone_group_key(key[1]))
            by_phone.setdefault(phone_key, []).append(key)
    selected = view.selected_paths()
    issues = []
    number = 0
    for phone_key in sorted(by_phone):
        keys = by_phone[phone_key]
        album_tracks = []
        for key in keys:
            album_tracks += groups[key]
        touched = False
        for track in album_tracks:
            if str(track.path) in selected:
                touched = True
        if len(keys) > 1 and touched:
            number += 1
            counts = {}
            spellings = []
            for track in album_tracks:
                value = track.tags.album or ""
                if value not in counts:
                    spellings.append(value)
                    counts[value] = 0
                counts[value] += 1
            chosen = choose_spelling(spellings, counts, POLICY_MOST, capitals=False).spelling
            wanted = {}
            for track in album_tracks:
                _set(wanted, track, "album", chosen)
            names = []
            for key in keys:
                names.append(_album_label(key))
            issues.append(Issue(
                KIND_SPLIT, SEVERITY_HIGH, f"\"{chosen}\": {len(keys)} album che sull'iPhone diventano uno",
                f"Sul PC sono album diversi ({'; '.join(names)}), ma l'iPhone non conta gli zeri davanti ai numeri "
                "(\"01\" = \"1\") e li mette in un album solo, con il nome arrivato per primo. Se sono lo stesso album, "
                f"la correzione scrive \"{chosen}\" su tutti.", [track.path for track in album_tracks],
                Fix(FIX_TAGS, f"Album \"{chosen}\" su tutti i brani", changes=_changes_list(wanted)),
                rule_id=f"R28.{number}"))
    return issues


def _by_format(album_tracks: list) -> dict:
    result = {}
    for track in album_tracks:
        result.setdefault(track.path.suffix.casefold(), []).append(track)
    return result


def _most_common_number(values: list) -> int:
    """Il valore più frequente tra quelli non vuoti; a parità il più alto; 0 se non ce ne sono."""
    counts = {}
    for value in values:
        if value:
            counts[value] = counts.get(value, 0) + 1
    result = 0
    best = None
    for value, count in counts.items():
        rank = (count, value)
        if best is None or rank > best:
            best = rank
            result = value
    return result


def detect_track_numbers(view: RuleView) -> list:
    """R30 (a mano): in un album di più dischi brani senza numero del disco; numero di traccia più alto del totale,
    numero del disco più alto del numero di dischi. R31 (correzione): il totale delle tracce diverso tra i brani dello
    stesso disco, il numero di dischi diverso tra i brani dell'album."""
    issues = []
    number = 0
    albums = view.selected_albums()
    for key in sorted(albums, key=lambda k: (k[0].casefold(), k[1].casefold())):
        if key[1] != UNKNOWN_ALBUM and not cue.all_images(albums[key]):
            for suffix, copy in sorted(_by_format(albums[key]).items()):
                manual, changes = _numbers_of_copy(copy)
                files = [track.path for track in copy]
                label = _album_label(key) + (f" ({suffix.lstrip('.')})" if len(_by_format(albums[key])) > 1 else "")
                if manual:
                    number += 1
                    issues.append(Issue(
                        KIND_FEW_TRACKS, SEVERITY_MEDIUM, f"{label}: numeri di traccia o di disco sbagliati",
                        " ".join(manual), files, rule_id=f"R30.{number}"))
                if changes:
                    number += 1
                    issues.append(Issue(
                        KIND_FEW_TRACKS, SEVERITY_LOW, f"{label}: totale delle tracce o dei dischi diverso tra i brani",
                        "Il totale delle tracce (o il numero di dischi) cambia da un brano all'altro dello stesso disco: "
                        "la correzione scrive su tutti il valore più frequente.", files,
                        Fix(FIX_TAGS, "Lo stesso totale su tutti i brani", changes=changes), rule_id=f"R31.{number}"))
    return issues


def _numbers_of_copy(copy: list) -> tuple:
    """(frasi dei problemi da correggere a mano, correzioni dei totali) di una copia dell'album (un formato)."""
    manual = []
    discs = set()
    no_disc = 0
    for track in copy:
        if track.tags.disc_number:
            discs.add(track.tags.disc_number)
        else:
            no_disc += 1
    if no_disc and any(disc > 1 for disc in discs):
        manual.append(f"L'album ha più dischi, ma {_tracks_text(no_disc)} non ha il numero del disco: sull'iPhone "
                      "finiscono nel disco 1, mescolati.")
    over = []
    for track in copy:
        tags = track.tags
        if tags.track_number and tags.track_total and tags.track_number > tags.track_total:
            over.append(f"{tags.title or track.path.name} (traccia {tags.track_number} di {tags.track_total})")
        elif tags.disc_number and tags.disc_total and tags.disc_number > tags.disc_total:
            over.append(f"{tags.title or track.path.name} (disco {tags.disc_number} di {tags.disc_total})")
    if over:
        shown = "; ".join(over[:MANY]) + ("…" if len(over) > MANY else "")
        manual.append(f"Numero più alto del totale: {shown}.")
    wanted = {}
    by_disc = {}
    for track in copy:
        by_disc.setdefault(track.tags.disc_number or 1, []).append(track)
    for disc_tracks in by_disc.values():
        totals = []
        for track in disc_tracks:
            totals.append(track.tags.track_total)
        total = _most_common_number(totals)
        if total and len(set(totals)) > 1:
            for track in disc_tracks:
                _set(wanted, track, "track_total", total)
    disc_totals = []
    for track in copy:
        disc_totals.append(track.tags.disc_total)
    disc_total = _most_common_number(disc_totals)
    if disc_total and len(set(disc_totals)) > 1:
        for track in copy:
            _set(wanted, track, "disc_total", disc_total)
    result = (manual, _changes_list(wanted))
    return result


def numbers_from_file_names(copy: list) -> dict:
    """{brano: (disco o None, numero)} dai nomi dei file ("05 - Titolo.mp3"), se ogni file ha il suo numero e non ce
    ne sono due uguali (per disco); {} altrimenti."""
    found = {}
    places = set()
    usable = True
    for track in copy:
        match = FILE_NUMBER.match(track.path.stem)
        if match is None:
            usable = False
        else:
            disc = int(match.group(1)) if match.group(1) else None
            place = (disc or track.tags.disc_number or 1, int(match.group(2)))
            if place in places or place[1] == 0:
                usable = False
            places.add(place)
            found[id(track)] = (disc, int(match.group(2)))
    result = found if usable else {}
    return result


def _numbers_fix(copy: list, numbers: dict) -> list:
    """Le correzioni che scrivono i numeri presi dai nomi dei file (e il totale, se è più basso del numero più alto)."""
    highest = 0
    for _disc, value in numbers.values():
        highest = max(highest, value)
    wanted = {}
    for track in copy:
        disc, value = numbers[id(track)]
        _set(wanted, track, "track_number", value)
        if disc is not None:
            _set(wanted, track, "disc_number", disc)
        if track.tags.track_total and track.tags.track_total < highest:
            _set(wanted, track, "track_total", highest)
    result = _changes_list(wanted)
    return result


def detect_number_clashes(view: RuleView) -> list:
    """R29: nello stesso album e formato, lo stesso disco e numero di traccia con titoli diversi: numeri sbagliati
    (per esempio quelli degli album originali in una raccolta) o due album veri sotto lo stesso nome (due "Greatest
    Hits", due edizioni). Se i nomi dei file hanno un numero diverso per ogni brano, la correzione prende quello. Gira
    prima del conto dei brani mancanti (R9), che così conta sui numeri giusti. Con lo stesso titolo è R8."""
    issues = []
    number = 0
    albums = view.selected_albums()
    for key in sorted(albums, key=lambda k: (k[0].casefold(), k[1].casefold())):
        if key[1] != UNKNOWN_ALBUM:
            clashes = []
            files = []
            folders = set()
            changes = []
            for _suffix, copy in sorted(_by_format(albums[key]).items()):
                copy_clashes = 0
                by_number = {}
                for track in copy:
                    if not track.error and track.tags.track_number:
                        place = (track.tags.disc_number or 1, track.tags.track_number)
                        by_number.setdefault(place, []).append(track)
                for place in sorted(by_number):
                    same_place = by_number[place]
                    titles = set()
                    for track in same_place:
                        titles.add(fold(track.tags.title, LEVEL_PUNCT))
                    if len(titles) > 1:
                        names = []
                        for track in same_place:
                            names.append(f"«{track.tags.title}»")
                            files.append(track.path)
                            folders.add(track.path.parent)
                        prefix = f"{place[0]}-{place[1]}" if place[0] > 1 else str(place[1])
                        clashes.append(f"{prefix}: {', '.join(names)}")
                        copy_clashes += 1
                if copy_clashes:
                    from_names = numbers_from_file_names(copy)
                    if from_names:
                        changes += _numbers_fix(copy, from_names)
            if clashes:
                number += 1
                shown = "; ".join(clashes[:MANY]) + ("…" if len(clashes) > MANY else "")
                hint = (f" I brani sono in {len(folders)} cartelle: è probabile che siano due album con lo stesso nome."
                        if len(folders) > 1 else "")
                detail = (f"Nello stesso album lo stesso numero di traccia (e disco) ha titoli diversi: {shown}.{hint} "
                          "Sull'iPhone l'album ha i brani mescolati, e i brani che mancano non si possono contare.")
                fix = None
                if changes:
                    detail += (" I nomi dei file hanno invece un numero diverso per ogni brano (\"05 - …\"): la "
                               "correzione scrive quello come numero di traccia.")
                    fix = Fix(FIX_TAGS, "Numero di traccia dal nome del file", changes=changes)
                issues.append(Issue(
                    KIND_FEW_TRACKS, SEVERITY_MEDIUM,
                    f"{_album_label(key)}: {len(clashes)} numeri di traccia usati da brani diversi", detail, files, fix,
                    rule_id=f"R29.{number}"))
    return issues
