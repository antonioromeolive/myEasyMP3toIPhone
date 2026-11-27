# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""La linguetta Controlli senza interfaccia: i risultati di Verifica online come problemi, i risultati raggruppati per
album, da che parte sta ogni brano (PC e iPhone, solo PC, solo iPhone) e dove va ogni correzione scelta.

- Un brano **collegato** (c'è sul PC e sull'iPhone: registro della provenienza) si corregge da tutte e due le parti:
  sul PC (in sospeso e, se approvato, nei file) e sull'iPhone con Usa i tag da PC a iPhone, in attesa.
- Un brano **solo sul PC** si corregge solo sul PC.
- Un brano **solo sull'iPhone** si corregge solo sull'iPhone, con Cambia i tag (in attesa): solo i campi che l'iPhone
  sa cambiare (pending.EDIT_FIELDS) e solo per i brani messi da un computer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from . import cue
from .albumcheck import STATUS_ERROR, STATUS_NOT_FOUND, corrected_tags
from .pending import EDIT_FIELDS
from .scan import (
    FIX_TAGS, KIND_FEW_TRACKS, KIND_ONLINE, ORIGIN_ONLINE, SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_ORDER, Fix, Issue,
    tag_changes_of,
)
from .tags import OLD_TAG_FIELDS, OLD_TAG_NAMES, OLD_TAG_PRESENT, TAG_FIELDS

SIDE_BOTH = "lato_pc_iphone"
SIDE_PC = "lato_pc"
SIDE_PHONE = "lato_iphone"
SIDE_MIXED = "lato_misto"
# come si è scelto cosa controllare (scope_text)
HOW_SELECTED = "brani_selezionati"
HOW_ALBUMS = "album_scelti"
HOW_ARTISTS = "artisti_scelti"
HOW_ALL = "tutto_quanto"
SIDE_LABELS = {SIDE_BOTH: "PC e iPhone", SIDE_PC: "solo PC", SIDE_PHONE: "solo iPhone", SIDE_MIXED: "misto"}
OTHER_KEY = ("", "")              # i problemi senza un album (per esempio i brani solo sull'iPhone elencati per nome)
ONLINE_FIELDS = ("title", "artist", "album_artist", "album", "year", "track_number", "track_total", "disc_number",
                 "disc_total")
CUE_FIELDS = ("album_artist", "album", "year")     # per un'immagine CUE (tutto il disco in un file): solo l'album
FIELD_LABELS = dict(TAG_FIELDS + OLD_TAG_FIELDS)


# --------------------------------------------------------------------------- cosa si controlla

def scope_text(where: str, how: str, tracks: list, albums: list, opened: str = "") -> tuple:
    """(frase in HTML, nomi degli album) per il riquadro "Si controlla…". where: "PC" o "iPhone"; how: HOW_SELECTED
    (brani selezionati nella lista), HOW_ALBUMS, HOW_ARTISTS (scelti negli elenchi) o HOW_ALL; albums: le album_key."""
    from html import escape
    count = len(tracks)
    if not tracks:
        sentence = f"Niente da controllare: nella scheda {where} non ci sono brani."
    elif how == HOW_SELECTED:
        sentence = f"Si controlla: <b>{count} brani</b> selezionati nella lista della scheda {where}, da {len(albums)} album."
    elif how == HOW_ALBUMS and len(albums) == 1:
        sentence = (f"Si controlla l'album <b>{escape(albums[0][0])} — {escape(albums[0][1])}</b> scelto nella scheda {where} "
                    f"({count} brani).")
    elif how == HOW_ALBUMS:
        sentence = f"Si controlla: <b>{len(albums)} album</b> scelti nella scheda {where} ({count} brani)."
    elif how == HOW_ARTISTS:
        artists = []
        for key in albums:
            if key[0] not in artists:
                artists.append(key[0])
        if len(artists) == 1:
            sentence = (f"Si controlla l'artista <b>{escape(artists[0])}</b> scelto nella scheda {where}: {len(albums)} album, "
                        f"{count} brani.")
        else:
            sentence = f"Si controlla: <b>{len(artists)} artisti</b> scelti nella scheda {where}: {len(albums)} album, {count} brani."
    elif where == "PC":
        sentence = f"Si controlla: <b>tutti i brani della scheda PC</b> ({escape(opened)}): {len(albums)} album, {count} brani."
    else:
        sentence = f"Si controlla: <b>tutta la musica dell'iPhone</b>: {len(albums)} album, {count} brani."
    names = []
    for key in albums[:6]:
        names.append(f"{key[0]} — {key[1]}")
    shown = " · ".join(names)
    if len(albums) > 6:
        shown += f" · e altri {len(albums) - 6}"
    result = (sentence, shown if how != HOW_ALL else "")
    return result


def same_value(first, second) -> bool:
    """Due valori di un tag sono uguali, anche se diversi solo per le maiuscole ("uno" e "Uno"): nei Controlli una
    differenza così non è un problema e non si corregge."""
    if isinstance(first, str) and isinstance(second, str):
        result = first.casefold() == second.casefold()
    else:
        result = first == second
    return result


# --------------------------------------------------------------------------- Verifica online

def online_issues(result, number: int) -> list:
    """I problemi di un album verificato online (albumcheck.AlbumCheckResult): non trovato, brani che mancano
    rispetto all'edizione, tag diversi da quelli del catalogo (con la correzione). number: per i rule_id W*.N."""
    label = f"{result.artist} — {result.album}"
    files = []
    for track in result.local_tracks:
        files.append(track.path)
    issues = []
    if result.status in (STATUS_NOT_FOUND, STATUS_ERROR):
        tried = []
        for service, outcome in result.tried:
            tried.append(f"{service}: {outcome}")
        issues.append(Issue(KIND_ONLINE, SEVERITY_LOW, f"{label}: {result.status_text()}",
                            f"Nessun catalogo ha dato questo album: {'; '.join(tried)}.", files, origin=ORIGIN_ONLINE,
                            rule_id=f"W3.{number}"))
    else:
        edition = f"Edizione di {result.service_label}: {result.release.label()}."
        if result.ai_reason:
            edition += f" Scelta dall'AI ({result.ai_reason})."
        # FLAC + CUE: un file solo con tutte le tracce. Nessun brano "manca" e i campi della traccia (titolo,
        # numero) non si danno al file intero: solo quelli dell'album
        whole_disc = cue.all_images(result.local_tracks)
        fields = CUE_FIELDS if whole_disc else ONLINE_FIELDS
        if whole_disc:
            edition += " Il CUE ha tutte le tracce in un file solo: dal catalogo solo album, artista dell'album e anno."
        missing = [] if whole_disc else result.missing
        if missing:
            names = []
            for expected in missing[:15]:
                names.append(f"{expected.position_label()} {expected.title}")
            more = "…" if len(missing) > 15 else ""
            issues.append(Issue(KIND_FEW_TRACKS, SEVERITY_MEDIUM,
                                f"{label}: mancano {len(missing)} di {len(result.matches)} brani ({result.service_label})",
                                f"{edition} Mancano: {', '.join(names)}{more}.", files, origin=ORIGIN_ONLINE,
                                rule_id=f"W1.{number}"))
        changes = []
        changed = []
        for match in list(result.matches) + list(result.copies):      # anche le copie in un altro formato
            if match.local is not None:
                wanted = corrected_tags(match, result.release)
                values = {}
                for name in fields:
                    if not same_value(getattr(wanted, name), getattr(match.local.tags, name)):
                        values[name] = getattr(wanted, name)
                if values:
                    changes.append((match.local.path, values))
                    changed.append(match.local.path)
        if changes:
            issues.append(Issue(KIND_ONLINE, SEVERITY_LOW,
                                f"{label}: tag diversi da {result.service_label} su {len(changes)} brani",
                                edition, changed, Fix(FIX_TAGS, f"I tag di {result.service_label}", changes=changes),
                                origin=ORIGIN_ONLINE, rule_id=f"W2.{number}"))
    return issues


# --------------------------------------------------------------------------- per album

@dataclass(eq=False)
class Target:
    """Un brano dei risultati: scanned è il Track della scansione (i tag di "ora", l'album); pc il brano del PC,
    phone il brano dell'iPhone (phone_library.PhoneTrack), quelli che ci sono. Si confronta per identità: resolve
    restituisce sempre lo stesso Target per lo stesso file."""
    scanned: object
    pc: object = None
    phone: object = None

    @property
    def side(self) -> str:
        if self.pc is not None and self.phone is not None:
            result = SIDE_BOTH
        elif self.pc is not None:
            result = SIDE_PC
        else:
            result = SIDE_PHONE
        return result

    @property
    def name(self) -> str:
        tags = self.scanned.tags
        number = f"{tags.track_number:02d} " if tags.track_number else ""
        result = f"{number}{tags.title or self.scanned.path.name}"
        return result


@dataclass
class Row:
    """Una correzione: un campo di un brano (ora → diventa), dal problema numero issue del rapporto."""
    target: Target
    name: str
    old: object
    new: object
    issue: int


@dataclass
class AlbumProblem:
    index: int                     # il numero del problema nel rapporto
    issue: Issue
    rows: list = field(default_factory=list)
    files: list = field(default_factory=list)
    accepted: bool = False         # "va bene così" per questo album (mostrato solo a richiesta)


@dataclass
class AlbumEntry:
    key: tuple                     # (artista dell'album, album), OTHER_KEY per i problemi senza album
    problems: list = field(default_factory=list)
    targets: list = field(default_factory=list)   # i brani dell'album toccati dai problemi

    @property
    def title(self) -> str:
        if self.key == OTHER_KEY:
            result = "Altri problemi"
        else:
            result = f"{self.key[0]} — {self.key[1]}"
        return result

    @property
    def severity(self) -> str:
        result = SEVERITY_LOW
        for problem in self.problems:
            if SEVERITY_ORDER.get(problem.issue.severity, 3) < SEVERITY_ORDER.get(result, 3):
                result = problem.issue.severity
        return result

    @property
    def side(self) -> str:
        sides = set()
        for target in self.targets:
            sides.add(target.side)
        if len(sides) == 1:
            result = sides.pop()
        elif sides:
            result = SIDE_MIXED
        else:
            result = ""
        return result

    @property
    def year(self) -> str:
        result = ""
        for target in self.targets:
            if not result and target.scanned.tags.year:
                result = str(target.scanned.tags.year)[:4]
        return result

    def rows(self) -> list:
        result = []
        for problem in self.problems:
            result.extend(problem.rows)
        return result


def group_by_album(issues: list, resolve: Callable[[object], Optional[Target]]) -> list:
    """I problemi per album (AlbumEntry), dal più grave: un problema di più album compare sotto ognuno, con i soli
    file e le sole correzioni di quell'album. resolve(percorso) -> Target (None: un file che non è un brano, che va
    in "Altri problemi")."""
    entries = {}
    for index, issue in enumerate(issues):
        per_album = {}
        for path in issue.files:
            target = resolve(path)
            key = target.scanned.album_key if target is not None else OTHER_KEY
            per_album.setdefault(key, AlbumProblem(index, issue)).files.append(path)
            entry = entries.setdefault(key, AlbumEntry(key))
            if target is not None and target not in entry.targets:
                entry.targets.append(target)
        if issue.fix is not None:
            for path, values in tag_changes_of(issue.fix):
                target = resolve(path)
                if target is not None:
                    key = target.scanned.album_key
                    problem = per_album.setdefault(key, AlbumProblem(index, issue))
                    entry = entries.setdefault(key, AlbumEntry(key))
                    if target not in entry.targets:
                        entry.targets.append(target)
                    for name, value in values.items():
                        if name in OLD_TAG_NAMES:                # un vecchio tag (ID3v1, APE): c'è → tolto
                            old = OLD_TAG_PRESENT
                        else:
                            old = getattr(target.scanned.tags, name, None)
                        if not same_value(old, value):          # solo le maiuscole: niente da correggere
                            problem.rows.append(Row(target, name, old, value, index))
        for key, problem in per_album.items():
            entries[key].problems.append(problem)
    result = []
    for key in sorted(entries, key=lambda k: (k == OTHER_KEY, SEVERITY_ORDER.get(entries[k].severity, 3),
                                              k[0].lower(), k[1].lower())):
        result.append(entries[key])
    return result


def filter_accepted(entries: list, accepted, show: bool) -> tuple:
    """(album, quanti problemi vanno bene così): i problemi che vanno bene così per il loro album (accepted:
    accepted.Accepted) si tolgono, o con show restano segnati (AlbumProblem.accepted); un album senza altri problemi
    si toglie."""
    from .accepted import problem_type
    kept = []
    hidden = 0
    for entry in entries:
        problems = []
        for problem in entry.problems:
            ok = entry.key != OTHER_KEY and accepted.is_accepted(entry.key, problem_type(problem.issue))
            if ok:
                hidden += 1
                problem.accepted = True
            if show or not ok:
                problems.append(problem)
        if problems:
            entry.problems = problems
            kept.append(entry)
    result = (kept, hidden)
    return result


# --------------------------------------------------------------------------- dove va ogni correzione

@dataclass
class ApplyPlan:
    pc: list = field(default_factory=list)        # [(Track del PC, {campo: valore})]: brani collegati e solo PC
    linked: list = field(default_factory=list)    # [(PhoneTrack, Track)]: Usa i tag da PC a iPhone (collegati)
    phone: list = field(default_factory=list)     # [(PhoneTrack, {campo: valore})]: Cambia i tag (solo iPhone)
    blocked: list = field(default_factory=list)   # [(brano, motivo)]: correzioni che sull'iPhone non si possono fare
    old_tags: list = field(default_factory=list)  # [(Track del PC, [OLD_ID3V1, OLD_APE])]: vecchi tag da togliere
    #                                               dai file del PC (le copie per l'iPhone ne sono già senza)

    def count(self, side: str) -> int:
        if side == SIDE_PHONE:
            result = len(self.phone)
        elif side == SIDE_BOTH:
            result = len(self.linked)
        else:
            result = len(self.pc) - len(self.linked)
        return result


def _edit_value(name: str, value):
    """Un valore come lo vuole Cambia i tag sull'iPhone (anno e numeri come numeri, 0 = vuoto)."""
    if name in ("year", "track_number", "disc_number"):
        digits = str(value or "").strip()[:4]
        result = int(digits) if digits.isdigit() else 0
    elif name == "compilation":
        result = bool(value)
    else:
        result = "" if value is None else str(value)
    return result


def plan_apply(rows: list) -> ApplyPlan:
    """Le correzioni scelte (Row), unite per brano, divise per parte. Due correzioni dello stesso campo: vince
    l'ultima."""
    merged = []
    values_of = {}
    old_of = {}
    for row in rows:
        key = id(row.target)
        if key not in values_of:
            values_of[key] = {}
            old_of[key] = []
            merged.append(row.target)
        if row.name in OLD_TAG_NAMES:
            if row.name not in old_of[key]:
                old_of[key].append(row.name)
        else:
            values_of[key][row.name] = row.new
    plan = ApplyPlan()
    for target in merged:
        values = values_of[id(target)]
        side = target.side
        if old_of[id(target)] and target.pc is not None:        # solo i file del PC: sull'iPhone non c'è da fare
            plan.old_tags.append((target.pc, old_of[id(target)]))
        if not values:
            side = ""                                             # solo vecchi tag: nient'altro per questo brano
        if side in (SIDE_BOTH, SIDE_PC):
            plan.pc.append((target.pc, values))
        if side == SIDE_BOTH:
            plan.linked.append((target.phone, target.pc))
        if side == SIDE_PHONE:
            item = target.phone
            if not item.from_computer:
                plan.blocked.append((target.name, "non è stato messo da un computer: i suoi tag non si cambiano"))
            else:
                editable = {}
                refused = []
                for name, value in values.items():
                    if name in EDIT_FIELDS:
                        editable[name] = _edit_value(name, value)
                    else:
                        refused.append(FIELD_LABELS.get(name, name))
                if editable:
                    plan.phone.append((item, editable))
                if refused:
                    plan.blocked.append((target.name, f"sull'iPhone senza il file sul PC non si cambia: "
                                                       f"{', '.join(refused)}"))
    result = plan
    return result
