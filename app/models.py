from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Song:
    path: Path
    title: str = "Desconocido"
    artist: str = "Desconocido"
    album: str = "Desconocido"
    genre: str = "Desconocido"
    year: str = ""
    duration: float = 0.0
    file_hash: str = ""
    artwork: bytes | None = field(default=None, compare=False, repr=False)

    @property
    def filename(self):
        return self.path.name

    @property
    def duration_text(self):
        minutes = int(self.duration // 60)
        seconds = int(self.duration % 60)
        return f"{minutes:02d}:{seconds:02d}"


@dataclass(frozen=True)
class FileIssue:
    path: Path
    message: str


@dataclass
class ScanResult:
    songs: list[Song]
    issues: list[FileIssue]


@dataclass
class OrganizationResult:
    moved: list[tuple[Path, Path]]
    issues: list[FileIssue]
    copied: list[tuple[Path, Path]] = field(default_factory=list)


@dataclass
class DuplicateActionResult:
    processed: list[Path]
    issues: list[FileIssue]
