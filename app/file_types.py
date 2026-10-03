from pathlib import Path


MUSIC_EXTENSIONS = frozenset(
    {".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wav", ".wma", ".opus"}
)
VIDEO_EXTENSIONS = frozenset(
    {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".webm", ".m4v"}
)
IMAGE_EXTENSIONS = frozenset(
    {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"}
)
DOCUMENT_EXTENSIONS = frozenset(
    {".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".xls", ".xlsx", ".ppt", ".pptx"}
)

PLANNED_FILE_CATEGORIES = {
    "video": VIDEO_EXTENSIONS,
    "image": IMAGE_EXTENSIONS,
    "document": DOCUMENT_EXTENSIONS,
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
