import os
from pathlib import Path
import shutil

from send2trash import send2trash

from .models import DuplicateActionResult, FileIssue, OrganizationResult


def safe_name(text):
    invalid = '<>:"/\\|?*'
    result = str(text).strip()

    for character in invalid:
        result = result.replace(character, "_")

    return result or "Desconocido"


def metadata_name(value, fallback):
    text = str(value).strip()
    if not text or text.casefold() in {"desconocido", "unknown"}:
        return fallback
    return safe_name(text)


def build_destination(
    root,
    song,
    organize_artist=True,
    organize_album=True,
    organize_genre=False,
):
    folders = []
    if organize_genre:
        folders.append(metadata_name(song.genre, "Otros"))
    if organize_artist:
        folders.append(metadata_name(song.artist, "Otros"))
    if organize_album:
        folders.append(metadata_name(song.album, "Sin álbum"))

    title = str(song.title).strip()
    if not title or title.casefold() in {"desconocido", "unknown"}:
        filename = safe_name(song.path.stem)
    else:
        filename = safe_name(title)
    extension = song.path.suffix

    return Path(root).joinpath(*folders, f"{filename}{extension}")


def preview_organization(
    root,
    songs,
    organize_artist=True,
    organize_album=True,
    organize_genre=False,
):
    operations = []
    reserved_destinations = set()

    for song in songs:
        destination = build_destination(
            root,
            song,
            organize_artist=organize_artist,
            organize_album=organize_album,
            organize_genre=organize_genre,
        )

        if song.path.resolve() != destination.resolve():
            candidate = destination
            counter = 1
            while (
                candidate.exists()
                or os.path.normcase(str(candidate.resolve())) in reserved_destinations
            ):
                candidate = destination.with_name(
                    f"{destination.stem} ({counter}){destination.suffix}"
                )
                counter += 1

            reserved_destinations.add(os.path.normcase(str(candidate.resolve())))
            destination = candidate
            operations.append((song.path, destination))

    return operations


def validate_organization(
    root,
    songs,
    organize_artist=True,
    organize_album=True,
    organize_genre=False,
):
    issues = []

    for source, destination in preview_organization(
        root,
        songs,
        organize_artist=organize_artist,
        organize_album=organize_album,
        organize_genre=organize_genre,
    ):
        if not source.is_file():
            issues.append(FileIssue(source, "El archivo ya no existe o no es accesible."))
            continue

        if not os.access(source, os.R_OK):
            issues.append(FileIssue(source, "No hay permiso de lectura sobre el archivo."))
        if not os.access(source.parent, os.W_OK | os.X_OK):
            issues.append(FileIssue(source, "No hay permiso para retirar el archivo de su carpeta."))

        destination_parent = destination.parent
        while not destination_parent.exists():
            parent = destination_parent.parent
            if parent == destination_parent:
                break
            destination_parent = parent

        if not os.access(destination_parent, os.W_OK | os.X_OK):
            issues.append(
                FileIssue(
                    destination,
                    f"No hay permiso para crear o escribir en {destination.parent}.",
                )
            )

    return issues


def organize(
    root,
    songs,
    organize_artist=True,
    organize_album=True,
    organize_genre=False,
):
    operations = preview_organization(
        root,
        songs,
        organize_artist=organize_artist,
        organize_album=organize_album,
        organize_genre=organize_genre,
    )
    moved = []
    issues = []

    for source, destination in operations:
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)

            final_destination = destination
            counter = 1

            while final_destination.exists():
                final_destination = destination.with_name(
                    f"{destination.stem} ({counter}){destination.suffix}"
                )
                counter += 1

            shutil.move(str(source), str(final_destination))
            moved.append((source, final_destination))
        except OSError as error:
            issues.append(FileIssue(path=source, message=str(error)))

    return OrganizationResult(moved=moved, issues=issues)


def process_duplicates(root, groups, action):
    processed = []
    issues = []
    duplicates = [song for group in groups for song in group[1:]]

    for song in duplicates:
        source = song.path
        try:
            if not source.is_file() or not os.access(source, os.R_OK | os.W_OK):
                raise PermissionError("El archivo no existe o no hay permisos suficientes.")

            if action == "move":
                if not os.access(root, os.W_OK | os.X_OK):
                    raise PermissionError("No hay permiso para escribir en la carpeta elegida.")

                destination_directory = Path(root) / "Repetidos"
                destination_directory.mkdir(parents=True, exist_ok=True)
                destination = destination_directory / source.name
                counter = 1
                while destination.exists():
                    destination = destination_directory / (
                        f"{source.stem} ({counter}){source.suffix}"
                    )
                    counter += 1
                shutil.move(str(source), str(destination))
            elif action == "trash":
                send2trash(str(source))
            else:
                raise ValueError(f"Acción de repetidos no válida: {action}")

            processed.append(source)
        except (OSError, ValueError) as error:
            issues.append(FileIssue(path=source, message=str(error)))

    return DuplicateActionResult(processed=processed, issues=issues)
