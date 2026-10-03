import sys
from pathlib import Path


bundle_root = Path(
    getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])
)
APP_VERSION = (bundle_root / "VERSION").read_text(encoding="utf-8").strip()
