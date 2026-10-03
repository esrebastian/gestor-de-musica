import os
from pathlib import Path
import hashlib
import base64
import binascii
from typing import Callable

from mutagen import File
from mutagen.flac import Picture
from .file_types import MUSIC_EXTENSIONS
from .models import FileIssue, ScanResult, Song
from .organizer import DUPLICATES_FOLDER, MUSIC_FOLDER


SUPPORTED_EXTENSIONS = MUSIC_EXTENSIONS
ProgressCallback = Callable[[str, int, int], None]
MAX_ARTWORK_BYTES = 512 * 1024


def get_tag(audio, names, default="Desconocido"):
    if not audio or not audio.tags:
        return default

    for name in names:
        value = audio.tags.get(name)
        if value:
            if isinstance(value, list):
                value = value[0]
            text = str(value).strip()
            if text:
                return text

    return default


def get_hash(path, chunk_size=1024 * 1024):
    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            sha256.update(chunk)

    return sha256.hexdigest()


def get_artwork(path):
    def valid_artwork(data):
        return data if data and len(data) <= MAX_ARTWORK_BYTES else None

    audio = File(path)
    if not audio:
        return None

    pictures = getattr(audio, "pictures", ())
    if pictures:
        return valid_artwork(pictures[0].data)

    tags = audio.tags
    if not tags:
        return None

    getall = getattr(tags, "getall", None)
    if getall:
        for frame in getall("APIC"):
            if frame.data:
                artwork = valid_artwork(frame.data)
                if artwork:
                    return artwork

    covers = tags.get("covr", ())
    if isinstance(covers, (bytes, bytearray)):
        covers = (covers,)
    for cover in covers:
        if cover:
            artwork = valid_artwork(bytes(cover))
            if artwork:
                return artwork

    encoded_pictures = tags.get("metadata_block_picture", ())
    if isinstance(encoded_pictures, (str, bytes)):
        encoded_pictures = (encoded_pictures,)
    for encoded in encoded_pictures:
        if isinstance(encoded, bytes):
            try:
                encoded = encoded.decode("ascii")
            except UnicodeDecodeError:
                continue
        try:
            picture = Picture(base64.b64decode(encoded))
        except (binascii.Error, ValueError):
            continue
        if picture.data:
            artwork = valid_artwork(picture.data)
            if artwork:
                return artwork

    for frame in tags.values():
        data = getattr(frame, "data", None)
        if data and getattr(frame, "mime", "").startswith("image/"):
            artwork = valid_artwork(data)
            if artwork:
                return artwork
    return None


def read_song(path):
    audio = File(path, easy=True)

    song = Song(path=path)

    if audio:
        song.title = get_tag(audio, ["title"])
        song.artist = get_tag(audio, ["artist"])
        song.album = get_tag(audio, ["album"])
        song.genre = get_tag(audio, ["genre"])
        song.year = get_tag(audio, ["date"], "")
        song.artwork = get_artwork(path)

        if audio.info:
            song.duration = getattr(audio.info, "length", 0.0)

    song.file_hash = get_hash(path)
    return song


def scan_folder(folder, progress_callback=None):
    folder = Path(folder)
    if not folder.exists():
        raise FileNotFoundError(f"La carpeta no existe: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"La ruta no es una carpeta: {folder}")

    songs = []
    issues = []
    audio_paths = []

    def record_walk_error(error):
        issues.append(
            FileIssue(
                path=Path(error.filename or folder),
                message=str(error),
            )
        )

    for directory, dirnames, filenames in os.walk(folder, onerror=record_walk_error):
        dirnames[:] = [
            name for name in dirnames
            if name.casefold() not in {"repetidos", DUPLICATES_FOLDER.casefold()}
        ]
        for filename in filenames:
            path = Path(directory) / filename
            if path.suffix.casefold() in SUPPORTED_EXTENSIONS:
                audio_paths.append(path)

        if progress_callback:
            progress_callback("listing", len(audio_paths), 0)

    total = len(audio_paths)
    if progress_callback:
        progress_callback("processing", 0, total)

    for completed, path in enumerate(audio_paths, start=1):
        try:
            songs.append(read_song(path))
        except Exception as error:
            issues.append(FileIssue(path=path, message=str(error)))
        if progress_callback:
            progress_callback("processing", completed, total)

    songs.sort(key=lambda song: (song.artist.lower(), song.title.lower()))
    return ScanResult(songs=songs, issues=issues)


def find_duplicates(songs):
    groups = {}

    for song in songs:
        groups.setdefault(song.file_hash, []).append(song)

    return [group for group in groups.values() if len(group) > 1]


def find_possible_duplicates(songs):
    groups = {}

    for song in songs:
        title = song.title.strip().casefold()
        artist = song.artist.strip().casefold()
        album = song.album.strip().casefold()
        if not title or not artist or not album:
            continue
        if {title, artist, album} & {"desconocido", "unknown"}:
            continue

        groups.setdefault((artist, title, album), []).append(song)

    possible_groups = []
    for group in groups.values():
        by_hash = {}
        for song in group:
            by_hash.setdefault(song.file_hash, song)
        if len(by_hash) > 1:
            possible_groups.append(list(by_hash.values()))

    return possible_groups
