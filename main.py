from __future__ import annotations

import argparse
from pathlib import Path

from config_paths import resolve_config_path
from organizer import load_config, organize_once, watch_and_organize
from ui import run_ui


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SynkFolder")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    parser.add_argument("--once", action="store_true", help="Run organization one time")
    parser.add_argument("--watch", action="store_true", help="Run in continuous watch mode")
    parser.add_argument("--ui", action="store_true", help="Open desktop user interface")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = resolve_config_path(args.config)
    if args.ui:
        run_ui(config_path)
        return

    config = load_config(config_path)

    if args.watch:
        watch_and_organize(config)
        return

    moved = organize_once(config)
    print(f"Done. Organized {moved} file(s).")


if __name__ == "__main__":
    main()
