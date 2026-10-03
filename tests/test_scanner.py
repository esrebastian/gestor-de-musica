import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app import scanner
from app.file_types import (
    ACTIVE_FILE_CATEGORIES,
    category_for_extension,
    category_for_path,
)
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

    def test_embedded_cover_art_is_read_for_grid_previews(self):
        picture = SimpleNamespace(data=b"cover image bytes")
        audio = SimpleNamespace(pictures=[picture], tags={})

        with patch.object(scanner, "File", return_value=audio):
            artwork = scanner.get_artwork(Path("track.flac"))

        self.assertEqual(artwork, b"cover image bytes")

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

    def test_music_duplicates_folder_is_not_scanned_again(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            duplicate = root / "Musica_y_Audio" / "Duplicados" / "copy.mp3"
            duplicate.parent.mkdir(parents=True)
            duplicate.touch()

            with patch.object(scanner, "read_song") as read_song:
                result = scanner.scan_folder(root)

        self.assertEqual(result.songs, [])
        read_song.assert_not_called()

    def test_music_is_active_and_other_file_categories_are_prepared(self):
        self.assertEqual(ACTIVE_FILE_CATEGORIES, frozenset({"music"}))
        self.assertEqual(category_for_extension(".mp3"), "music")
        self.assertEqual(category_for_extension(".m3u"), "playlist")
        self.assertEqual(category_for_extension(".flp"), "music_project")
        self.assertEqual(category_for_extension(".MP4"), "video")
        self.assertEqual(category_for_path(Path("photo.PNG")), "image")
        self.assertEqual(category_for_extension(".pdf"), "document")
        self.assertEqual(category_for_extension(".crdownload"), "incomplete")
        self.assertEqual(category_for_extension(".zip"), "archive_or_installer")
        self.assertEqual(
            category_for_extension(".unknown-extension"), None
        )

    def test_scan_reports_determinate_progress_for_music_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = root / "one.mp3"
            second = root / "subfolder" / "two.flac"
            second.parent.mkdir()
            first.touch()
            second.touch()
            progress = []

            with patch.object(
                scanner,
                "read_song",
                side_effect=lambda path: Song(path=path),
            ):
                result = scanner.scan_folder(
                    root,
                    progress_callback=lambda phase, done, total: progress.append(
                        (phase, done, total)
                    ),
                )

        processing_progress = [item[1:] for item in progress if item[0] == "processing"]
        self.assertEqual(len(result.songs), 2)
        self.assertEqual(
            processing_progress,
            [(0, 2), (1, 2), (2, 2)],
        )

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