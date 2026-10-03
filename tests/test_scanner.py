import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import scanner
from app.models import Song


class ScanFolderTests(unittest.TestCase):
    def test_missing_folder_raises_clear_error(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_folder = Path(temporary_directory) / "missing"

            with self.assertRaises(FileNotFoundError):
                scanner.scan_folder(missing_folder)

    def test_unreadable_song_is_returned_as_an_issue(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            audio_path = Path(temporary_directory) / "track.mp3"
            audio_path.touch()

            with patch.object(scanner, "read_song", side_effect=PermissionError("access denied")):
                result = scanner.scan_folder(temporary_directory)

        self.assertEqual(result.songs, [])
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].path, audio_path)
        self.assertIn("access denied", result.issues[0].message)

    def test_repetidos_folder_is_not_scanned_again(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            repeated_audio = root / "Repetidos" / "copy.mp3"
            repeated_audio.parent.mkdir()
            repeated_audio.touch()

            with patch.object(scanner, "read_song") as read_song:
                result = scanner.scan_folder(root)

        self.assertEqual(result.songs, [])
        read_song.assert_not_called()

    def test_possible_duplicates_require_matching_metadata_and_different_hash(self):
        songs = [
            Song(
                path=Path("one.mp3"),
                title="Numb",
                artist="Linkin Park",
                album="Meteora",
                file_hash="hash-one",
            ),
            Song(
                path=Path("two.flac"),
                title=" numb ",
                artist="LINKIN PARK",
                album="Meteora",
                file_hash="hash-two",
            ),
            Song(
                path=Path("three.mp3"),
                title="Numb",
                artist="Linkin Park",
                album="Meteora",
                file_hash="hash-one",
            ),
        ]

        groups = scanner.find_possible_duplicates(songs)

        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]), 2)
        self.assertNotIn(songs[2], groups[0])


if __name__ == "__main__":
    unittest.main()