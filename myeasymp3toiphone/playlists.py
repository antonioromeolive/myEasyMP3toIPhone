# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Le playlist per artista e per compilation dell'iPhone: quali creare e quali cancellare (solo il piano; le scrive
phone_actions.rebuild_playlists, dopo la finestra che le elenca).

  * per artista: una playlist per artista dell'album (non l'artista dei singoli brani) con almeno MIN_ALBUMS album
    e MIN_TRACKS brani: tutti i suoi album, per anno, disco e numero di traccia;
  * per compilation: gli album di più artisti ("AA.VV.", "Artisti vari", la spunta compilation, o tanti artisti
    diversi e nessuno con metà dei brani). I volumi della stessa serie vanno in una playlist sola: quelli nella
    stessa cartella "radice" sul PC (una cartella per album, il nome della radice dentro il nome dell'album o della
    sua cartella), poi quelli con lo stesso nome a parte "Vol. N" e "CD N". Una serie con un album solo ha una
    playlist se ha almeno MIN_COMPILATION_TRACKS brani;
  * da cancellare: tutte le playlist messe da un computer (CopyTrans, iTunes, questo programma: sync_id diverso da
    0), comprese quelle fatte le volte prima. Quelle fatte sul telefono, le smart e le cartelle restano: il computer
    non le può toccare.
Solo i brani messi da un computer possono stare in una playlist mandata da un computer (sync_id)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath

from .albumcheck import normalize
from .library import album_folder, best_spelling, group_name

MARK = "♪ "                   # davanti al nome delle playlist fatte qui
MIN_ALBUMS = 2
MIN_TRACKS = 5
MIN_COMPILATION_TRACKS = 20
MIN_COMPILATION_ARTISTS = 4   # senza "AA.VV.": almeno tanti artisti diversi…
MAX_MAIN_SHARE = 0.5          # …e nessuno con questa parte dei brani o più
MIN_ROOT_NAME = 3
KIND_ARTIST = "artista"
KIND_COMPILATION = "compilation"
VARIOUS_KEYS = {"aavv", "artistivari", "variousartists", "various", "va", "autorivari", "vari", "variartisti"}
DISC_WORDS = r"(?:cd|disc|disco|disk|dvd)"
VOLUME_WORDS = r"(?:vol|volume|parte|part|pt)"
DISC_KEY = re.compile(rf"\b{DISC_WORDS}\s*\d+\b")
VOLUME_KEY = re.compile(rf"\b{VOLUME_WORDS}\s*\d+\b")
SHOWN_SUFFIX = re.compile(rf"[\s\-–,:]*[\(\[]?\s*(?:{DISC_WORDS}|{VOLUME_WORDS})\.?\s*\d+\s*[\)\]]?", re.IGNORECASE)


@dataclass
class PlannedPlaylist:
    name: str                 # con MARK davanti
    kind: str                 # KIND_ARTIST, KIND_COMPILATION
    tracks: list              # PhoneTrack, nell'ordine della playlist
    albums: list              # i nomi degli album, nell'ordine

    @property
    def members(self) -> list:
        result = []
        for item in self.tracks:
            result.append(item.sync_id)
        return result


@dataclass
class PlaylistPlan:
    create: list = field(default_factory=list)       # PlannedPlaylist
    delete: list = field(default_factory=list)       # phone_library.PhonePlaylist messe da un computer
    kept: list = field(default_factory=list)         # phone_library.PhonePlaylist fatte sul telefono
    left_out: int = 0                                 # brani non messi da un computer: in nessuna playlist


@dataclass
class _Album:
    key: tuple
    tracks: list = field(default_factory=list)
    compilation: bool = False
    owner: str = ""           # l'artista dell'album (group_name), se non è una compilation
    folder: str = ""          # la cartella dell'album sul PC ("" se non si sa)


def album_base(album: str) -> str:
    """L'album senza "CD 2", "Disc 1": i dischi di un album sono un album solo."""
    key = DISC_KEY.sub(" ", normalize(album or ""))
    result = re.sub(r"\s+", " ", key).strip()
    return result


def series_key(album: str) -> str:
    """La serie di una compilation: l'album senza disco e volume ("Raccolta Ottanta Vol. 3 CD 1" -> "raccolta ottanta")."""
    key = VOLUME_KEY.sub(" ", album_base(album))
    result = re.sub(r"\s+", " ", key).strip()
    return result


def series_name(album: str) -> str:
    """Il nome da mostrare della serie: l'album com'è scritto, senza "Vol. 3" e "CD 1"."""
    result = SHOWN_SUFFIX.sub("", album or "").strip(" -–,:")
    if not result:
        result = (album or "").strip()
    return result


def is_various(name: str) -> bool:
    """"AA.VV.", "Artisti vari", "Various Artists"…"""
    result = re.sub(r"[^a-z0-9]", "", group_name(name or "")) in VARIOUS_KEYS
    return result


def _natural(text: str) -> tuple:
    """Per ordinare "Vol. 2" prima di "Vol. 10"."""
    parts = []
    for piece in re.split(r"(\d+)", group_name(text or "")):
        if piece.isdigit():
            parts.append((0, int(piece), ""))
        elif piece:
            parts.append((1, 0, piece))
    result = tuple(parts)
    return result


def _track_order(item) -> tuple:
    tags = item.tags
    result = (tags.disc_number or 1, tags.track_number or 9999, group_name(tags.title or ""))
    return result


def _year(album: _Album) -> int:
    result = 9999
    for item in album.tracks:
        text = (item.tags.year or "")[:4]
        if text.isdigit():
            result = min(result, int(text))
    return result


def _album_folder(paths: list) -> str:
    """La cartella dell'album: quella comune ai suoi file, sopra "CD1"/"cd 2 - studio" se è divisa per dischi."""
    folders = set()
    for path in paths:
        folders.add(album_folder(path))
    result = _common_path(sorted(folders)) if folders else ""
    return result


def _common_path(folders: list) -> str:
    parts = list(PureWindowsPath(folders[0]).parts)
    for folder in folders[1:]:
        other = PureWindowsPath(folder).parts
        size = 0
        while size < len(parts) and size < len(other) and parts[size].lower() == other[size].lower():
            size += 1
        parts = parts[:size]
    result = str(PureWindowsPath(*parts)) if parts else ""
    return result


def _albums(tracks: list, sources: dict) -> list:
    """Gli album dei brani: (album senza disco, artista dell'album); se è una compilation e di chi è."""
    by_key = {}
    for item in tracks:
        key = (album_base(item.tags.album), group_name(item.tags.album_artist or ""))
        album = by_key.get(key)
        if album is None:
            album = _Album(key)
            by_key[key] = album
        album.tracks.append(item)
    result = []
    for album in by_key.values():
        artists = {}
        flagged = False
        paths = []
        for item in album.tracks:
            name = group_name(item.tags.artist or "")
            artists[name] = artists.get(name, 0) + 1
            flagged = flagged or item.tags.compilation
            if item.sync_id in sources:
                paths.append(sources[item.sync_id])
        album_artist = album.tracks[0].tags.album_artist or ""
        top = max(artists.values()) if artists else 0
        mixed = not album_artist and len(artists) >= MIN_COMPILATION_ARTISTS and top < MAX_MAIN_SHARE * len(album.tracks)
        album.compilation = flagged or is_various(album_artist) or mixed
        if not album.compilation:
            if album_artist:
                album.owner = group_name(album_artist)
            else:
                best = ""
                for name, count in artists.items():
                    if not best or count > artists[best]:
                        best = name
                album.owner = best
        album.folder = _album_folder(paths)
        result.append(album)
    return result


def _artist_playlists(albums: list) -> list:
    by_owner = {}
    for album in albums:
        if not album.compilation and album.owner:
            by_owner.setdefault(album.owner, []).append(album)
    result = []
    for owned in by_owner.values():
        count = 0
        spellings = []
        for album in owned:
            count += len(album.tracks)
            for item in album.tracks:
                spellings.append(item.tags.album_artist or item.tags.artist)
        if len(owned) >= MIN_ALBUMS and count >= MIN_TRACKS:
            owned.sort(key=lambda album: (_year(album), _natural(album.tracks[0].tags.album)))
            ordered = []
            names = []
            for album in owned:
                ordered += sorted(album.tracks, key=_track_order)
                names.append(album.tracks[0].tags.album)
            result.append(PlannedPlaylist(MARK + best_spelling(spellings), KIND_ARTIST, ordered, names))
    return result


def _root_groups(compilations: list) -> tuple:
    """([(nome della radice, [album])], album rimasti): nella stessa cartella radice, gli album che hanno il nome della
    radice nel loro nome (o in quello della loro cartella); almeno due."""
    by_root = {}
    names = {}
    for album in compilations:
        if album.folder:
            root = PureWindowsPath(album.folder).parent
            by_root.setdefault(str(root).lower(), []).append(album)
            names[str(root).lower()] = root.name
    groups = []
    grouped = set()
    for root, members in by_root.items():
        root_key = normalize(names[root])
        fitting = []
        for album in members:
            if root_key in normalize(album.tracks[0].tags.album or "") or                     root_key in normalize(PureWindowsPath(album.folder).name):
                fitting.append(album)
        if len(fitting) >= 2 and len(root_key) >= MIN_ROOT_NAME:
            groups.append((names[root], fitting))
            for album in fitting:
                grouped.add(id(album))
    rest = []
    for album in compilations:
        if id(album) not in grouped:
            rest.append(album)
    result = (groups, rest)
    return result


def _compilation_playlists(albums: list) -> list:
    compilations = []
    for album in albums:
        if album.compilation:
            compilations.append(album)
    groups, rest = _root_groups(compilations)
    by_series = {}
    for album in rest:
        by_series.setdefault(series_key(album.tracks[0].tags.album), []).append(album)
    for key, members in by_series.items():
        if key:
            shown = []
            for album in members:
                shown.append(series_name(album.tracks[0].tags.album))
            groups.append((best_spelling(shown), members))
    result = []
    for name, members in groups:
        count = 0
        for album in members:
            count += len(album.tracks)
        if len(members) >= 2 or count >= MIN_COMPILATION_TRACKS:
            members.sort(key=lambda album: _natural(album.tracks[0].tags.album))
            ordered = []
            album_names = []
            for album in members:
                ordered += sorted(album.tracks, key=_track_order)
                album_names.append(album.tracks[0].tags.album)
            result.append(PlannedPlaylist(MARK + name, KIND_COMPILATION, ordered, album_names))
    return result


def plan(phone_tracks: list, phone_playlists: list, sources: dict) -> PlaylistPlan:
    """Il piano: phone_tracks (PhoneTrack), phone_playlists (PhonePlaylist, quelle normali dell'iPhone), sources
    {sync_id: percorso del file sul PC} (registro della provenienza, solo questo PC)."""
    result = PlaylistPlan()
    usable = []
    for item in phone_tracks:
        if item.from_computer and not item.missing_file:
            usable.append(item)
        else:
            result.left_out += 1
    albums = _albums(usable, sources)
    created = _artist_playlists(albums) + _compilation_playlists(albums)
    used = set()
    for playlist in created:
        if group_name(playlist.name) in used:
            playlist.name += " (compilation)" if playlist.kind == KIND_COMPILATION else " (artista)"
        used.add(group_name(playlist.name))
    created.sort(key=lambda playlist: group_name(playlist.name))
    result.create = created
    for playlist in phone_playlists:
        if playlist.from_computer:
            result.delete.append(playlist)
        else:
            result.kept.append(playlist)
    return result


def source_paths(registry) -> dict:
    """{sync_id: percorso} dei brani la cui sorgente è su questo PC."""
    result = {}
    for link in registry.links.values():
        if link.here:
            result[link.sync_id] = str(Path(link.path))
    return result
