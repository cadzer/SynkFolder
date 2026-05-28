from __future__ import annotations

from pathlib import Path


RULES_BY_FOLDER = {
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md"},
    "Spreadsheets": {".csv", ".xls", ".xlsx", ".ods"},
    "Presentations": {".ppt", ".pptx", ".key"},
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".heic"},
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "Code": {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cpp", ".cs", ".html", ".css", ".json", ".xml", ".yml", ".yaml"},
    "Installers": {".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm"},
}


def classify_by_extension(path: Path) -> str | None:
    ext = path.suffix.lower()
    for folder, exts in RULES_BY_FOLDER.items():
        if ext in exts:
            return folder
    return None
