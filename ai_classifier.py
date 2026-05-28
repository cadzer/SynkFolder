from __future__ import annotations

import os
from pathlib import Path

from openai import OpenAI

ALLOWED_CATEGORIES = [
    "Documents",
    "Spreadsheets",
    "Presentations",
    "Images",
    "Videos",
    "Audio",
    "Archives",
    "Code",
    "Installers",
    "Unknown",
]


def classify_with_ai(file_path: Path, model: str = "gpt-4o-mini") -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Unknown"

    client = OpenAI(api_key=api_key)
    prompt = (
        "You are classifying a file for Downloads organization.\n"
        f"Filename: {file_path.name}\n"
        f"Extension: {file_path.suffix.lower() or 'none'}\n\n"
        f"Pick exactly one category from: {', '.join(ALLOWED_CATEGORIES)}.\n"
        "Return only the category name."
    )

    try:
        response = client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=20,
        )
        text = (response.output_text or "").strip()
        if text in ALLOWED_CATEGORIES:
            return text
    except Exception:
        return "Unknown"

    return "Unknown"
