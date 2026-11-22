"""Lettura e scrittura dei tag audio.

Supporta MP3 (ID3), M4A (MP4/iTunes), FLAC e OGG/Opus (Vorbis comment).
Le copertine sono supportate per MP3, M4A e FLAC.
"""

import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional

import mutagen
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, ID3, ID3NoHeaderError
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".flac", ".ogg", ".opus"}
COVER_EXTENSIONS = {".mp3", ".m4a", ".flac"}

# Campi modificabili: (attributo, etichetta mostrata nell'interfaccia)
TAG_FIELDS = [
    ("title", "Titolo"),
    ("artist", "Artista"),
    ("album_artist", "Artista album"),
    ("album", "Album"),
    ("track_number", "N. traccia"),
    ("track_total", "Tracce totali"),
    ("disc_number", "N. disco"),
    ("disc_total", "Dischi totali"),
    ("year", "Anno"),
    ("genre", "Genere"),
    ("compilation", "Compilation"),
]
INT_FIELDS = {"track_number", "track_total", "disc_number", "disc_total"}
# sì/no: un album di più artisti (l'artista dell'album è "Artisti vari", quello del brano è il suo); l'app Musica
# tiene insieme l'album solo con questa spunta
BOOL_FIELDS = {"compilation"}


class TagError(Exception):
    """Errore nella lettura o scrittura dei tag."""


# Le cartelle aperte nel programma sono in sola lettura: nessun file dentro di esse viene mai modificato. Le modifiche
# dei tag restano in sospeso (overlay) e si applicano solo alle copie (invio all'iPhone, esportazione, importazione).
_protected_roots: set = set()


def protect_folder(folder: Path) -> None:
    _protected_roots.add(os.path.normcase(os.path.abspath(str(folder))))


def is_protected(path: Path) -> bool:
    target = os.path.normcase(os.path.abspath(str(path)))
    result = False
    for root in _protected_roots:
        if target == root or target.startswith(root.rstrip("\\/") + os.sep):
            result = True
    return result


def _check_writable(path: Path, new_copy: bool) -> None:
    if is_protected(path) and not new_copy:
        raise TagError(f"{path.name}: la cartella è in sola lettura, il file sul PC non si modifica")


@dataclass
class TrackTags:
    title: str = ""
    artist: str = ""
    album_artist: str = ""
    album: str = ""
    track_number: Optional[int] = None
    track_total: Optional[int] = None
    disc_number: Optional[int] = None
    disc_total: Optional[int] = None
    year: str = ""
    genre: str = ""
    compilation: bool = False

    def copy(self) -> "TrackTags":
        result = replace(self)
        return result


def is_audio_file(path: Path) -> bool:
    result = path.suffix.lower() in AUDIO_EXTENSIONS
    return result


def _to_int(text: str) -> Optional[int]:
    """Legge le cifre iniziali: '07' -> 7, '3 of 12' -> 3, 'abc' -> None."""
    stripped = text.strip()
    index = 0
    while index < len(stripped) and stripped[index].isdigit():
        index += 1
    if index > 0:
        result = int(stripped[:index])
    else:
        result = None
    return result


def _split_pair(text: str) -> tuple:
    """'3/12' -> (3, 12); '3' -> (3, None); '' -> (None, None)."""
    if "/" in text:
        first, second = text.split("/", 1)
        result = (_to_int(first), _to_int(second))
    else:
        result = (_to_int(text), None)
    return result


def _join_pair(number: Optional[int], total: Optional[int]) -> str:
    if number is None:
        result = ""
    elif total is None:
        result = str(number)
    else:
        result = f"{number}/{total}"
    return result


def _first(tags, key: str) -> str:
    result = ""
    try:
        values = tags[key]
    except (KeyError, ValueError):
        values = []
    if values:
        result = str(values[0]).strip()
    return result


def _set(tags, key: str, value: str) -> None:
    if value:
        tags[key] = [value]
    else:
        try:
            del tags[key]
        except (KeyError, ValueError):
            pass


def _is_vorbis(audio) -> bool:
    result = isinstance(audio, (FLAC, OggVorbis, OggOpus))
    return result


def _open_easy(path: Path):
    try:
        audio = mutagen.File(str(path), easy=True)
    except mutagen.MutagenError as exc:
        raise TagError(f"Impossibile leggere {path.name}: {exc}") from exc
    if audio is None:
        raise TagError(f"Formato non supportato: {path.name}")
    return audio


def read_tags(path: Path) -> tuple:
    """Restituisce (TrackTags, durata in secondi)."""
    audio = _open_easy(path)
    tags = TrackTags()
    if audio.tags is not None:
        source = audio.tags
        tags.title = _first(source, "title")
        tags.artist = _first(source, "artist")
        tags.album_artist = _first(source, "albumartist")
        tags.album = _first(source, "album")
        tags.genre = _first(source, "genre")
        tags.year = _first(source, "date")[:4]
        tags.track_number, tags.track_total = _split_pair(_first(source, "tracknumber"))
        tags.disc_number, tags.disc_total = _split_pair(_first(source, "discnumber"))
        tags.compilation = _flag(_first(source, "compilation")) if "compilation" in _easy_keys(audio) else False
        if _is_vorbis(audio):
            if tags.track_total is None:
                tags.track_total = _to_int(_first(source, "tracktotal") or _first(source, "totaltracks"))
            if tags.disc_total is None:
                tags.disc_total = _to_int(_first(source, "disctotal") or _first(source, "totaldiscs"))
    if path.suffix.lower() in MP4_EXTENSIONS:
        tags.compilation = _read_mp4_compilation(path)
    length = 0.0
    if audio.info is not None:
        length = float(getattr(audio.info, "length", 0.0) or 0.0)
    result = (tags, length)
    return result


MP4_EXTENSIONS = {".m4a", ".m4b", ".mp4"}


def _flag(text: str) -> bool:
    result = text.strip().lower() in ("1", "true", "yes", "sì", "si")
    return result


def _easy_keys(audio) -> set:
    """Le chiavi che l'interfaccia "facile" di mutagen conosce per questo file (le Vorbis le accettano tutte)."""
    if _is_vorbis(audio):
        result = {"compilation"}
    else:
        result = set(getattr(audio.tags, "valid_keys", {}) or {})
    return result


def _read_mp4_compilation(path: Path) -> bool:
    """EasyMP4 non conosce la spunta compilation (cpil): si legge dal tag MP4 vero."""
    result = False
    try:
        audio = MP4(str(path))
        if audio.tags is not None:
            result = bool(audio.tags.get("cpil", False))
    except mutagen.MutagenError:
        result = False
    return result


def _write_mp4_compilation(path: Path, value: bool) -> None:
    audio = MP4(str(path))
    if audio.tags is None:
        audio.add_tags()
    if value:
        audio.tags["cpil"] = True
    else:
        audio.tags.pop("cpil", None)
    audio.save()


def write_tags(path: Path, tags: TrackTags, new_copy: bool = False) -> None:
    """Scrive i tag. new_copy=True solo per una copia appena creata dal programma (esportazione, importazione)."""
    _check_writable(path, new_copy)
    audio = _open_easy(path)
    if audio.tags is None:
        audio.add_tags()
    target = audio.tags
    _set(target, "title", tags.title)
    _set(target, "artist", tags.artist)
    _set(target, "albumartist", tags.album_artist)
    _set(target, "album", tags.album)
    _set(target, "genre", tags.genre)
    _set(target, "date", tags.year)
    if "compilation" in _easy_keys(audio):
        _set(target, "compilation", "1" if tags.compilation else "")
    if _is_vorbis(audio):
        _set(target, "tracknumber", _join_pair(tags.track_number, None))
        _set(target, "tracktotal", _join_pair(tags.track_total, None))
        _set(target, "discnumber", _join_pair(tags.disc_number, None))
        _set(target, "disctotal", _join_pair(tags.disc_total, None))
    else:
        _set(target, "tracknumber", _join_pair(tags.track_number, tags.track_total))
        _set(target, "discnumber", _join_pair(tags.disc_number, tags.disc_total))
    try:
        audio.save()
        if path.suffix.lower() in MP4_EXTENSIONS:
            _write_mp4_compilation(path, tags.compilation)
        if path.suffix.lower() == ".mp3":
            save_as_id3v23(path, new_copy)
    except mutagen.MutagenError as exc:
        raise TagError(f"Impossibile salvare {path.name}: {exc}") from exc


def save_as_id3v23(path: Path, new_copy: bool = False) -> None:
    """Riscrive il tag ID3 in versione 2.3, la più letta da Windows, autoradio e app dell'iPhone. mutagen converte i
    frame (per esempio l'anno TDRC -> TYER) solo con update_to_v23: un save(v2_version=3) da solo lascia frame 2.4
    che molti lettori ignorano. Un tag ID3v1 già presente viene aggiornato insieme (v1=1)."""
    _check_writable(path, new_copy)
    id3 = ID3(str(path))
    id3.update_to_v23()
    id3.save(str(path), v1=1, v2_version=3)


def prepare_copy(path: Path, tags: TrackTags, cover: Optional[bytes] = None) -> None:
    """Una copia pronta per l'iPhone (o esportata): i tag (con le modifiche in sospeso), la copertina nuova e, per gli
    MP3, niente tag ID3v1 né APE (alcuni lettori leggono quelli e mostrano valori vecchi) e ID3 v2.3. Solo su copie:
    mai sul file originale."""
    write_tags(path, tags, new_copy=True)
    if cover is not None and path.suffix.lower() in COVER_EXTENSIONS:
        write_cover(path, cover, new_copy=True)
    if path.suffix.lower() == ".mp3":
        from mutagen.apev2 import delete as delete_ape
        from mutagen.id3 import delete as delete_id3
        try:
            delete_ape(str(path))
        except mutagen.MutagenError:
            pass  # nessun tag APE
        delete_id3(str(path), delete_v1=True, delete_v2=False)


def read_cover(path: Path) -> Optional[bytes]:
    """Restituisce i byte dell'immagine di copertina, o None."""
    result = None
    suffix = path.suffix.lower()
    try:
        if suffix == ".mp3":
            frames = ID3(str(path)).getall("APIC")
            if frames:
                result = frames[0].data
        elif suffix == ".m4a":
            covers = (MP4(str(path)).tags or {}).get("covr", [])
            if covers:
                result = bytes(covers[0])
        elif suffix == ".flac":
            pictures = FLAC(str(path)).pictures
            if pictures:
                result = pictures[0].data
    except Exception:  # noqa: BLE001 - una copertina illeggibile è solo una copertina che non si mostra
        result = None
    return result


def _image_mime(data: bytes) -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        result = "image/png"
    else:
        result = "image/jpeg"
    return result


def write_cover(path: Path, data: bytes, new_copy: bool = False) -> None:
    """Sostituisce la copertina incorporata nel file."""
    _check_writable(path, new_copy)
    suffix = path.suffix.lower()
    mime = _image_mime(data)
    try:
        if suffix == ".mp3":
            try:
                id3 = ID3(str(path))
            except ID3NoHeaderError:
                id3 = ID3()
            id3.delall("APIC")
            id3.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=data))
            id3.update_to_v23()
            id3.save(str(path), v1=1, v2_version=3)
        elif suffix == ".m4a":
            mp4 = MP4(str(path))
            if mp4.tags is None:
                mp4.add_tags()
            image_format = MP4Cover.FORMAT_PNG if mime == "image/png" else MP4Cover.FORMAT_JPEG
            mp4.tags["covr"] = [MP4Cover(data, imageformat=image_format)]
            mp4.save()
        elif suffix == ".flac":
            flac = FLAC(str(path))
            picture = Picture()
            picture.type = 3
            picture.mime = mime
            picture.data = data
            flac.clear_pictures()
            flac.add_picture(picture)
            flac.save()
        else:
            raise TagError(f"Copertina non supportata per i file {suffix}")
    except mutagen.MutagenError as exc:
        raise TagError(f"Impossibile salvare la copertina di {path.name}: {exc}") from exc
