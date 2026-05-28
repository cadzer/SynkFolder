from __future__ import annotations

import sys
from pathlib import Path

APP_USER_MODEL_ID = "SynkFolder.Application.1.0"


def configure_windows_app_identity() -> None:
    """Ensure Windows taskbar uses this app's icon instead of a generic Python icon."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass


def apply_windows_window_icon(root, ico_path: Path) -> None:
    if sys.platform != "win32" or not ico_path.exists():
        return
    resolved = str(ico_path.resolve())
    try:
        root.iconbitmap(default=resolved)
        root.iconbitmap(resolved)
    except Exception:
        pass
    try:
        root.wm_iconbitmap(default=resolved)
    except Exception:
        pass
