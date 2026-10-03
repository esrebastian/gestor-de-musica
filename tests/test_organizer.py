import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.models import Song
from app.organizer import (
    build_destination,
    organize,
    process_duplicates,
    preview_organization,
    validate_organization,
)


class OrganizerTests(unittest.TestCase):
    def test_default_destination_follows_music_artist_album_tree(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "Mi Música"
            song = Song(
                path=root / "Numb.mp3",
                title="Numb",
                artist="Linkin Park",
                album="Meteora",
            )

            destination = build_destination(root, song)

        self.assertEqual(
            destination,
            root / "Musica_y_Audio" / "Artistas" / "Linkin Park" / "Meteora" / "Numb.mp3",
        )

    def test_missing_album_songs_go_to_artist_loose_songs_folder(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            song = Song(
                path=root / "single.mp3",
                title="Single",
                artist="Artist",
                album="Unknown",
            )

            destination = build_destination(root, song)

        self.assertEqual(
            destination,
            root / "Musica_y_Audio" / "Artistas" / "Artist"
            / "Canciones_Sueltas" / "Single.mp3",
        )

    def test_unknown_artists_use_unknown_artist_tree_folder(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            song = Song(path=root / "untagged.mp3", title="Untagged")

            destination = build_destination(root, song)

        self.assertEqual(
            destination,
            root / "Musica_y_Audio" / "Artistas" / "Artistas_Desconocidos"
            / "Canciones_Sueltas" / "Untagged.mp3",
        )

    def test_genre_can_be_added_before_artist_and_album(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            song = Song(
                path=root / "Numb.mp3",
                title="Numb",
                artist="Linkin Park",
                album="Meteora",
                genre="Rock",
            )

            destination = build_destination(root, song, organize_genre=True)

        self.assertEqual(
            destination,
            root / "Musica_y_Audio" / "Rock" / "Artistas" / "Linkin Park"
            / "Meteora" / "Numb.mp3",
        )

    def test_missing_tags_use_fallback_folders_and_preserve_filename(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            song = Song(path=root / "untagged track.mp3")

            destination = build_destination(root, song)

        self.assertEqual(
            destination,
            root / "Musica_y_Audio" / "Artistas" / "Artistas_Desconocidos"
            / "Canciones_Sueltas" / "untagged track.mp3",
        )

    def test_preview_reserves_unique_destinations_when_titles_collide(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_directory = root / "Incoming"
            source_directory.mkdir()
            first_source = source_directory / "first.mp3"
            second_source = source_directory / "second.mp3"
            first_source.touch()
            second_source.touch()
            first = Song(
                path=first_source,
                title="Track",
                artist="Artist",
                album="Album",
            )
            second = Song(
                path=second_source,
                title="Track",
                artist="Artist",
                album="Album",
            )

            operations = preview_organization(root, [first, second])

        destinations = [destination for _, destination in operations]
        self.assertEqual(len(destinations), 2)
        self.assertEqual(len(set(destinations)), 2)
        base = root / "Musica_y_Audio" / "Artistas" / "Artist" / "Album"
        self.assertEqual(destinations[0], base / "Track.mp3")
        self.assertEqual(destinations[1], base / "Track (1).mp3")

    def test_missing_source_is_reported_before_moving(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            song = Song(path=root / "missing.mp3", title="Track", artist="Artist", album="Album")

            issues = validate_organization(root, [song])

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].path, song.path)

    def test_move_failure_is_reported_without_claiming_success(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "track.mp3"
            source.touch()
            song = Song(path=source, title="Track", artist="Artist", album="Album")

            with patch("app.organizer.shutil.move", side_effect=PermissionError("access denied")):
                result = organize(root, [song])

        self.assertEqual(result.moved, [])
        self.assertEqual(len(result.issues), 1)
        self.assertIn("access denied", result.issues[0].message)

    def test_duplicate_move_preserves_one_copy_and_moves_extras(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first_path = root / "Numb.mp3"
            second_path = root / "Numb (1).mp3"
            first_path.touch()
            second_path.touch()
            group = [Song(path=first_path), Song(path=second_path)]

            result = process_duplicates(root, [group], "move")

            self.assertTrue(first_path.exists())
            self.assertTrue(
                (
                    root / "Musica_y_Audio" / "Duplicados"
                    / second_path.name
                ).exists()
            )

        self.assertEqual(result.processed, [second_path])
        self.assertEqual(result.issues, [])

    def test_duplicate_trash_action_uses_recycle_bin(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first_path = root / "Numb.mp3"
            duplicate_path = root / "Numb (1).mp3"
            first_path.touch()
            duplicate_path.touch()
            group = [Song(path=first_path), Song(path=duplicate_path)]

            with patch("app.organizer.send2trash") as trash:
                result = process_duplicates(root, [group], "trash")

        trash.assert_called_once_with(str(duplicate_path))
        self.assertEqual(result.processed, [duplicate_path])
        self.assertEqual(result.issues, [])


if __name__ == "__main__":
    unittest.main()