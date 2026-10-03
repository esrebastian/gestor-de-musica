import os
from pathlib import Path
import hashlib

from mutagen import File
from .models import FileIssue, ScanResult, Song


SUPPORTED_EXTENSIONS = {
    ".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wav", ".wma", ".opus"
}


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


def read_song(path):
    audio = File(path, easy=True)

    song = Song(path=path)

    if audio:
        song.title = get_tag(audio, ["title"])
        song.artist = get_tag(audio, ["artist"])
        song.album = get_tag(audio, ["album"])
        song.genre = get_tag(audio, ["genre"])
        song.year = get_tag(audio, ["date"], "")

        if audio.info:
            song.duration = getattr(audio.info, "length", 0.0)

    song.file_hash = get_hash(path)
    return song


def scan_folder(folder):
    folder = Path(folder)
    if not folder.exists():
        raise FileNotFoundError(f"La carpeta no existe: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"La ruta no es una carpeta: {folder}")

    songs = []
    issues = []

    def record_walk_error(error):
        issues.append(
            FileIssue(
                path=Path(error.filename or folder),
                message=str(error),
            )
        )

    for directory, dirnames, filenames in os.walk(folder, onerror=record_walk_error):
        if Path(directory).resolve() == folder.resolve():
            dirnames[:] = [name for name in dirnames if name.casefold() != "repetidos"]
        for filename in filenames:
            path = Path(directory) / filename
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            try:
                songs.append(read_song(path))
            except Exception as error:
                issues.append(FileIssue(path=path, message=str(error)))

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
