from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Callable, Iterable

from ai_classifier import classify_with_ai
from file_rules import classify_by_extension


@dataclass
class OrganizerConfig:
    downloads_path: Path
    dry_run: bool
    watch_interval_seconds: int
    use_ai: bool
    ai_model: str


def load_config(config_path: Path) -> OrganizerConfig:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return OrganizerConfig(
        downloads_path=Path(data["downloads_path"]).expanduser(),
        dry_run=bool(data.get("dry_run", True)),
        watch_interval_seconds=int(data.get("watch_interval_seconds", 5)),
        use_ai=bool(data.get("use_ai", True)),
        ai_model=str(data.get("ai_model", "gpt-4o-mini")),
    )


def iter_files(downloads_path: Path) -> Iterable[Path]:
    for item in downloads_path.iterdir():
        if item.is_file():
            yield item


def pick_target_folder(file_path: Path, config: OrganizerConfig) -> str:
    by_extension = classify_by_extension(file_path)
    if by_extension:
        return by_extension
    if config.use_ai:
        return classify_with_ai(file_path, model=config.ai_model)
    return "Unknown"


def resolve_unique_path(target_dir: Path, file_name: str) -> Path:
    candidate = target_dir / file_name
    if not candidate.exists():
        return candidate

    stem = Path(file_name).stem
    suffix = Path(file_name).suffix
    counter = 1
    while True:
        new_name = f"{stem} ({counter}){suffix}"
        candidate = target_dir / new_name
        if not candidate.exists():
            return candidate
        counter += 1


def _default_logger(message: str) -> None:
    print(message)


def organize_once(config: OrganizerConfig, logger: Callable[[str], None] | None = None) -> int:
    log = logger or _default_logger
    moved_count = 0
    downloads_path = config.downloads_path
    downloads_path.mkdir(parents=True, exist_ok=True)

    for file_path in iter_files(downloads_path):
        folder_name = pick_target_folder(file_path, config)
        target_dir = downloads_path / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = resolve_unique_path(target_dir, file_path.name)

        if file_path == target_path:
            continue

        if config.dry_run:
            log(f"[DRY RUN] {file_path.name} -> {folder_name}/{target_path.name}")
            moved_count += 1
            continue

        shutil.move(str(file_path), str(target_path))
        log(f"[MOVED] {file_path.name} -> {folder_name}/{target_path.name}")
        moved_count += 1

    return moved_count


def watch_and_organize(
    config: OrganizerConfig,
    logger: Callable[[str], None] | None = None,
    stop_event: Event | None = None,
) -> None:
    log = logger or _default_logger
    stopper = stop_event or Event()
    log(f"Watching: {config.downloads_path}")
    log(f"Dry run: {config.dry_run}")
    log(f"AI enabled: {config.use_ai}")
    log("Press Stop to end.\n")

    seen = set()
    while not stopper.is_set():
        try:
            current = {p.resolve() for p in iter_files(config.downloads_path)}
            if current != seen:
                changed = len(current.symmetric_difference(seen))
                if changed > 0:
                    moved = organize_once(config, logger=log)
                    if moved:
                        log(f"Cycle complete: {moved} file(s) organized.\n")
                seen = {p.resolve() for p in iter_files(config.downloads_path)}
            time.sleep(config.watch_interval_seconds)
        except KeyboardInterrupt:
            break
    log("\nStopped.")
