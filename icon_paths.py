from __future__ import annotations

import sys
from pathlib import Path


def get_assets_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "assets"
    return Path(__file__).resolve().parent / "assets"


def get_icon_png_path() -> Path:
    return get_assets_dir() / "SynkFolder.png"


def get_icon_ico_path() -> Path:
    return get_assets_dir() / "SynkFolder.ico"
