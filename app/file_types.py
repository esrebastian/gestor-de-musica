from pathlib import Path


MUSIC_EXTENSIONS = frozenset(
    {".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wav", ".wma", ".opus"}
)
MUSIC_PLAYLIST_EXTENSIONS = frozenset({".m3u", ".m3u8", ".pls", ".wpl"})
MUSIC_PROJECT_EXTENSIONS = frozenset({".flp", ".als", ".aup3"})
INCOMPLETE_DOWNLOAD_EXTENSIONS = frozenset({".crdownload", ".part", ".tmp"})
VIDEO_EXTENSIONS = frozenset(
    {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".webm", ".m4v"}
)
SUBTITLE_EXTENSIONS = frozenset({".srt", ".vtt", ".ass"})
IMAGE_EXTENSIONS = frozenset(
    {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"}
)
DESIGN_EXTENSIONS = frozenset({".svg", ".psd", ".ai", ".fig"})
DOCUMENT_EXTENSIONS = frozenset(
    {
        ".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".log",
        ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".epub", ".mobi",
    }
)
ARCHIVE_EXTENSIONS = frozenset(
    {".zip", ".rar", ".7z", ".tar", ".gz", ".exe", ".msi", ".iso", ".apk"}
)
CODE_AND_DATA_EXTENSIONS = frozenset(
    {
        ".py", ".js", ".ts", ".cpp", ".cs", ".kt", ".html", ".css",
        ".sql", ".db", ".json", ".xml", ".yaml", ".yml",
    }
)

PLANNED_FILE_CATEGORIES = {
    "playlist": MUSIC_PLAYLIST_EXTENSIONS,
    "music_project": MUSIC_PROJECT_EXTENSIONS,
    "incomplete": INCOMPLETE_DOWNLOAD_EXTENSIONS,
    "video": VIDEO_EXTENSIONS,
    "subtitle": SUBTITLE_EXTENSIONS,
    "image": IMAGE_EXTENSIONS,
    "design": DESIGN_EXTENSIONS,
    "document": DOCUMENT_EXTENSIONS,
    "archive_or_installer": ARCHIVE_EXTENSIONS,
    "code_or_data": CODE_AND_DATA_EXTENSIONS,
    "unknown_or_unclassified": frozenset({".dat", ".bin"}),
}
ACTIVE_FILE_CATEGORIES = frozenset({"music"})


def category_for_extension(extension):
    normalized_extension = extension.casefold()
    if normalized_extension in MUSIC_EXTENSIONS:
        return "music"

    for category, extensions in PLANNED_FILE_CATEGORIES.items():
        if normalized_extension in extensions:
            return category

    return None


def category_for_path(path):
    return category_for_extension(Path(path).suffix)
