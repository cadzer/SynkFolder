from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def get_user_config_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path.home() / ".config"
    config_dir = base / "SynkFolder"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_user_config_path() -> Path:
    return get_user_config_dir() / "config.json"


def get_bundled_config_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "config.json"
    return Path(__file__).resolve().parent / "config.json"


def get_project_config_path() -> Path:
    return Path(__file__).resolve().parent / "config.json"


def _default_config_data() -> dict:
    return {
        "downloads_path": str(Path.home() / "Downloads"),
        "dry_run": True,
        "watch_interval_seconds": 5,
        "use_ai": True,
        "ai_model": "gpt-4o-mini",
    }


def ensure_config_file(config_path: Path) -> None:
    if config_path.exists():
        return

    config_path.parent.mkdir(parents=True, exist_ok=True)

    for source in (get_bundled_config_path(), get_project_config_path()):
        if source.exists():
            shutil.copy2(source, config_path)
            return

    config_path.write_text(json.dumps(_default_config_data(), indent=2), encoding="utf-8")


def resolve_config_path(cli_path: str | Path | None = None) -> Path:
    if cli_path is not None:
        explicit = Path(cli_path).expanduser()
        if explicit.is_absolute() or explicit.parent != Path("."):
            ensure_config_file(explicit)
            return explicit

    if getattr(sys, "frozen", False):
        user_path = get_user_config_path()
        ensure_config_file(user_path)
        return user_path

    project_path = get_project_config_path()
    if project_path.exists():
        return project_path

    user_path = get_user_config_path()
    ensure_config_file(user_path)
    return user_path
