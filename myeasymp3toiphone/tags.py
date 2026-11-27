"""Lettura e scrittura dei tag audio.

Supporta MP3 (ID3), M4A (MP4/iTunes), FLAC e OGG/Opus (Vorbis comment). Si leggono tutti i tipi di tag, come i
programmi dei tag (TagScanner, Mp3tag): negli MP3 ID3v2, poi APEv2, poi ID3v1, campo per campo (un campo vuoto si
prende dal tipo seguente). WMA, WAV e AIFF si leggono soltanto (ASF, ID3, RIFF INFO): i loro tag non si scrivono e
all'iPhone non si inviano. Le copertine sono supportate per MP3, M4A e FLAC.
"""

import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional

import mutagen
from mutagen.apev2 import APENoHeaderError, APEv2
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, ID3, TCON, ID3NoHeaderError
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis

from .i18n import tr

# tag solo in lettura: non si scrivono (nemmeno sulle copie) e all'iPhone non si inviano
READ_ONLY_EXTENSIONS = {".wma", ".wav", ".aif", ".aiff"}
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".flac", ".ogg", ".opus"} | READ_ONLY_EXTENSIONS
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
# I vecchi tag di un MP3 (ID3v1 in fondo al file, APEv2): non sono campi ma "togli questo tag" nelle correzioni dei
# Controlli (R2, R3) e nell'elenco da approvare di gui.pc_write. Prima di toglierli i loro valori passano nell'ID3v2
OLD_ID3V1 = "vecchio_id3v1"
OLD_APE = "vecchio_ape"
OLD_TAG_FIELDS = [(OLD_ID3V1, "Tag ID3v1"), (OLD_APE, "Tag APE")]
OLD_TAG_NAMES = {OLD_ID3V1, OLD_APE}
OLD_TAG_PRESENT = "c'è"
OLD_TAG_REMOVED = "tolto"
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


def _easy_read(audio, path: Path) -> TrackTags:
    """I tag letti da mutagen in modo "easy" (ID3, MP4, Vorbis)."""
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
    return tags


MERGED_FIELDS = ("title", "artist", "album_artist", "album", "track_number", "track_total", "disc_number",
                 "disc_total", "year", "genre")


def _merge(target: TrackTags, other: Optional[TrackTags]) -> None:
    """I campi vuoti di target presi da other (un altro tipo di tag dello stesso file)."""
    if other is not None:
        for name in MERGED_FIELDS:
            if getattr(target, name) in (None, "") and getattr(other, name) not in (None, ""):
                setattr(target, name, getattr(other, name))
        if not target.compilation and other.compilation:
            target.compilation = True


def _id3_kind(id3) -> str:
    version = getattr(id3, "version", (2, 4, 0))
    if version[0] == 1:
        result = "ID3v1"
    else:
        result = f"ID3v2.{version[1]}"
    return result


def _id3_text(id3, frame_id: str) -> str:
    result = ""
    frames = id3.getall(frame_id)
    if frames and getattr(frames[0], "text", None):
        result = str(frames[0].text[0]).strip()
    return result


ID3_FRAMES = {"title": "TIT2", "artist": "TPE1", "album_artist": "TPE2", "album": "TALB", "year": "TDRC",
              "old_year": "TYER", "genre": "TCON", "track": "TRCK", "disc": "TPOS", "compilation": "TCMP"}


def _from_id3(id3) -> TrackTags:
    """I tag di un ID3 letto senza "easy" (WAV, AIFF)."""
    tags = TrackTags()
    for name in ("title", "artist", "album_artist", "album"):
        setattr(tags, name, _id3_text(id3, ID3_FRAMES[name]))
    tags.year = (_id3_text(id3, ID3_FRAMES["year"]) or _id3_text(id3, ID3_FRAMES["old_year"]))[:4]
    genres = id3.getall(ID3_FRAMES["genre"])
    if genres and genres[0].genres:
        tags.genre = str(genres[0].genres[0]).strip()
    tags.track_number, tags.track_total = _split_pair(_id3_text(id3, ID3_FRAMES["track"]))
    tags.disc_number, tags.disc_total = _split_pair(_id3_text(id3, ID3_FRAMES["disc"]))
    tags.compilation = _flag(_id3_text(id3, ID3_FRAMES["compilation"]))
    return tags


APE_KEYS = (("title", "Title"), ("artist", "Artist"), ("album_artist", "Album Artist"),
            ("album_artist", "AlbumArtist"), ("album", "Album"), ("year", "Year"), ("genre", "Genre"))
APE_NUMBER_KEYS = (("track", "Track"), ("disc", "Disc"))
APE_COMPILATION_KEYS = ("Compilation",)


def _ape_tags(path: Path) -> Optional[TrackTags]:
    """Il tag APEv2 del file (MP3), o None se non c'è."""
    try:
        ape = APEv2(str(path))
    except (APENoHeaderError, mutagen.MutagenError, OSError):
        ape = None
    result = None
    if ape is not None:
        result = TrackTags()
        for name, key in APE_KEYS:
            value = str(ape[key]).strip() if key in ape else ""
            if value and not getattr(result, name):
                setattr(result, name, value)
        result.year = result.year[:4]
        for name, key in APE_NUMBER_KEYS:
            if key in ape:
                pair = _split_pair(str(ape[key]))
                setattr(result, name + "_number", pair[0])
                setattr(result, name + "_total", pair[1])
        if APE_COMPILATION_KEYS[0] in ape:
            result.compilation = _flag(str(ape[APE_COMPILATION_KEYS[0]]))
    return result


def _v1_text(block: bytes) -> str:
    result = block.split(b"\x00")[0].decode("latin-1").strip()
    return result


def id3v1_tags(path: Path) -> Optional[TrackTags]:
    """Il vecchio tag ID3v1 (gli ultimi 128 byte del file), o None se non c'è."""
    block = b""
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            if handle.tell() >= 128:
                handle.seek(-128, os.SEEK_END)
                block = handle.read(128)
    except OSError:
        block = b""
    result = None
    if block[:3] == b"TAG":
        result = TrackTags(title=_v1_text(block[3:33]), artist=_v1_text(block[33:63]),
                           album=_v1_text(block[63:93]), year=_v1_text(block[93:97]))
        if block[125] == 0 and block[126] != 0:      # ID3v1.1: il numero di traccia
            result.track_number = block[126]
        genre = block[127]
        if genre < len(TCON.GENRES):
            result.genre = TCON.GENRES[genre]
    return result


RIFF_INFO = {b"INAM": "title", b"IART": "artist", b"IPRD": "album", b"ICRD": "year", b"IGNR": "genre"}


def _riff_text(data: bytes) -> str:
    raw = data.split(b"\x00")[0]
    try:
        result = raw.decode("utf-8").strip()
    except UnicodeDecodeError:
        result = raw.decode("cp1252", errors="replace").strip()
    return result


def _riff_list(data: bytes, tags: Optional[TrackTags]) -> Optional[TrackTags]:
    """Le voci di un blocco LIST INFO aggiunte a tags (creato se None)."""
    result = tags
    position = 0
    while position + 8 <= len(data):
        sub_id = data[position:position + 4]
        size = int.from_bytes(data[position + 4:position + 8], "little")
        text = _riff_text(data[position + 8:position + 8 + size])
        if result is None:
            result = TrackTags()
        name = RIFF_INFO.get(sub_id)
        if name is not None and text:
            setattr(result, name, text[:4] if name == "year" else text)
        elif sub_id in (b"ITRK", b"IPRT") and text:
            result.track_number, result.track_total = _split_pair(text)
        position += 8 + size + size % 2
    return result


def riff_info_tags(path: Path) -> Optional[TrackTags]:
    """I tag RIFF INFO di un WAV (LIST INFO: INAM, IART, IPRD, ICRD, IGNR, ITRK), o None se non ci sono."""
    result = None
    try:
        with path.open("rb") as handle:
            header = handle.read(12)
            valid = header[:4] == b"RIFF" and header[8:12] == b"WAVE"
            while valid:
                chunk = handle.read(8)
                valid = len(chunk) == 8
                if valid:
                    chunk_id = chunk[:4]
                    size = int.from_bytes(chunk[4:8], "little")
                    if chunk_id == b"LIST":
                        data = handle.read(size + size % 2)
                        if data[:4] == b"INFO":
                            result = _riff_list(data[4:size], result)
                    else:
                        handle.seek(size + size % 2, os.SEEK_CUR)   # l'audio non si legge
    except OSError:
        result = None
    return result


ASF_KEYS = (("title", "Title"), ("artist", "Author"), ("album_artist", "WM/AlbumArtist"),
            ("album", "WM/AlbumTitle"), ("genre", "WM/Genre"))
ASF_OTHER_KEYS = {"year": "WM/Year", "old_year": "WM/OriginalReleaseYear", "track": "WM/TrackNumber",
                  "old_track": "WM/Track", "disc": "WM/PartOfSet", "compilation": "WM/IsCompilation"}


def _asf_value(tags, key: str) -> str:
    values = tags.get(key, []) if tags is not None else []
    result = ""
    if values:
        first = values[0]
        result = str(getattr(first, "value", first)).strip()
    return result


def _from_asf(audio) -> TrackTags:
    """I tag di un WMA (ASF)."""
    tags = TrackTags()
    source = audio.tags
    for name, key in ASF_KEYS:
        setattr(tags, name, _asf_value(source, key))
    tags.year = (_asf_value(source, ASF_OTHER_KEYS["year"]) or _asf_value(source, ASF_OTHER_KEYS["old_year"]))[:4]
    tags.track_number, tags.track_total = _split_pair(_asf_value(source, ASF_OTHER_KEYS["track"])
                                                      or _asf_value(source, ASF_OTHER_KEYS["old_track"]))
    tags.disc_number, tags.disc_total = _split_pair(_asf_value(source, ASF_OTHER_KEYS["disc"]))
    tags.compilation = _flag(_asf_value(source, ASF_OTHER_KEYS["compilation"]))
    return tags


def _read_read_only(path: Path) -> tuple:
    """(TrackTags, durata, tipi di tag) di un WMA, WAV o AIFF."""
    try:
        audio = mutagen.File(str(path))
    except mutagen.MutagenError as exc:
        raise TagError(f"Impossibile leggere {path.name}: {exc}") from exc
    if audio is None:
        raise TagError(f"Formato non supportato: {path.name}")
    suffix = path.suffix.lower()
    tags = TrackTags()
    kinds = []
    if suffix == ".wma":
        tags = _from_asf(audio)
        if audio.tags:
            kinds.append("ASF (WMA)")
    elif audio.tags is not None:
        tags = _from_id3(audio.tags)
        kinds.append(_id3_kind(audio.tags))
    if suffix == ".wav":
        info = riff_info_tags(path)
        if info is not None:
            _merge(tags, info)
            kinds.append("RIFF INFO")
    length = 0.0
    if audio.info is not None:
        length = float(getattr(audio.info, "length", 0.0) or 0.0)
    result = (tags, length, kinds)
    return result


def read_all_tags(path: Path) -> tuple:
    """(TrackTags, durata in secondi, tipi di tag trovati nel file in ordine di precedenza, es. ["ID3v2.3", "APEv2"]).
    Negli MP3 i campi vuoti del tag principale si prendono da APEv2, poi da ID3v1 (come TagScanner e Mp3tag)."""
    if path.suffix.lower() in READ_ONLY_EXTENSIONS:
        result = _read_read_only(path)
    else:
        audio = _open_easy(path)
        tags = _easy_read(audio, path)
        kinds = []
        id3 = getattr(audio.tags, "_EasyID3__id3", None) if audio.tags is not None else None
        if id3 is not None:
            kinds.append(_id3_kind(id3))
        elif audio.tags is not None:
            kinds.append(TAG_KIND_NAMES.get(type(audio).__name__, type(audio).__name__))
        if path.suffix.lower() == ".mp3":
            ape = _ape_tags(path)
            if ape is not None and kinds == ["ID3v1"]:
                # senza ID3v2 mutagen dà l'ID3v1 come tag principale: APEv2 viene prima
                _merge(ape, tags)
                tags = ape
                kinds = ["APEv2", "ID3v1"]
            elif ape is not None:
                _merge(tags, ape)
                kinds.append("APEv2")
            if "ID3v1" not in kinds:
                v1 = id3v1_tags(path)
                if v1 is not None:
                    _merge(tags, v1)
                    kinds.append("ID3v1")
        length = 0.0
        if audio.info is not None:
            length = float(getattr(audio.info, "length", 0.0) or 0.0)
        result = (tags, length, kinds)
    return result


TAG_KIND_NAMES = {"EasyMP4": "MP4 (iTunes)", "FLAC": "Vorbis comment", "OggVorbis": "Vorbis comment",
                  "OggOpus": "Vorbis comment"}


def read_tags(path: Path) -> tuple:
    """Restituisce (TrackTags, durata in secondi): tutti i tipi di tag del file, uniti (read_all_tags)."""
    tags, length, _kinds = read_all_tags(path)
    result = (tags, length)
    return result


def tag_kinds(path: Path) -> list:
    """I tipi di tag del file, in ordine di precedenza ([] se non si legge)."""
    try:
        result = read_all_tags(path)[2]
    except TagError:
        result = []
    return result


UNCOMPRESSED_EXTENSIONS = {".wav", ".aif", ".aiff"}
BITRATE_MODES = {"CBR": "costante", "VBR": "variabile", "ABR": "media"}


def _codec_name(info) -> str:
    """Il codec, quando il contenitore ne può avere più d'uno (M4A, WMA, OGG): "AAC", "ALAC", "Vorbis"…"""
    description = str(getattr(info, "codec_description", "") or getattr(info, "codec_name", "") or "")
    class_name = type(info).__name__
    if "alac" in description.lower() or str(getattr(info, "codec", "")).lower() == "alac":
        result = "ALAC"
    elif "aac" in description.lower() or str(getattr(info, "codec", "")).lower().startswith("mp4a"):
        result = "AAC"
    elif "lossless" in description.lower():
        result = "WMA Lossless"
    elif class_name.startswith("OggVorbis"):
        result = "Vorbis"
    elif class_name.startswith("OggOpus"):
        result = "Opus"
    else:
        result = ""
    return result


def audio_format(path: Path) -> str:
    """Formato, codec e compressione del file, in breve: "MP3 · 320 kbit/s costante", "FLAC · senza perdita · 912
    kbit/s", "M4A · AAC · 256 kbit/s", "WAV · non compresso". Vuoto se il file non si legge."""
    path = Path(path)
    extension = path.suffix[1:].upper()
    try:
        audio = mutagen.File(str(path))
    except (mutagen.MutagenError, OSError):
        audio = None
    if audio is None or getattr(audio, "info", None) is None:
        result = ""
    else:
        info = audio.info
        parts = [extension]
        codec = _codec_name(info)
        if codec and codec.upper() != extension:
            parts.append(codec)
        kbits = int(round((getattr(info, "bitrate", 0) or 0) / 1000))
        if path.suffix.lower() in UNCOMPRESSED_EXTENSIONS:
            parts.append(tr("non compresso"))
        else:
            if path.suffix.lower() == ".flac" or codec in ("ALAC", "WMA Lossless"):
                parts.append(tr("senza perdita"))
            if kbits:
                mode = tr(BITRATE_MODES.get(str(getattr(info, "bitrate_mode", "")).rsplit(".", 1)[-1], ""))
                parts.append(f"{kbits} kbit/s {mode}".strip())
        result = " · ".join(parts)
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
    if path.suffix.lower() in READ_ONLY_EXTENSIONS:
        raise TagError(f"{path.name}: i tag dei file {path.suffix.lower()} si leggono soltanto")
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


def write_tags_approved(path: Path, tags: TrackTags) -> None:
    """Scrive i tag nel file ORIGINALE del PC, anche dentro una cartella aperta. Solo da gui.pc_write, dopo che
    l'utente ha visto e approvato l'elenco dei file e dei campi che cambiano: Usa i tag da iPhone a PC (vale l'iPhone)
    e "Anche nei file del PC" delle correzioni (Correggi tag, Applica la correzione). Ogni altra modifica dei tag resta
    in sospeso e va solo sulle copie."""
    write_tags(path, tags, new_copy=True)


def remove_old_tags_approved(path: Path, tags: TrackTags, names: list) -> None:
    """Toglie dal file ORIGINALE del PC i vecchi tag scelti (OLD_ID3V1, OLD_APE). Solo da gui.pc_write, dopo
    l'elenco approvato. Prima scrive tags (i valori letti, che comprendono quelli presi dall'APE o dall'ID3v1 per i
    campi vuoti dell'ID3v2) nel tag ID3v2: così niente si perde."""
    if path.suffix.lower() == ".mp3" and names:
        write_tags(path, tags, new_copy=True)
        if OLD_APE in names:
            from mutagen.apev2 import delete as delete_ape
            try:
                delete_ape(str(path))
            except mutagen.MutagenError:
                pass  # nessun tag APE
        if OLD_ID3V1 in names:
            from mutagen.id3 import delete as delete_id3
            delete_id3(str(path), delete_v1=True, delete_v2=False)


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
