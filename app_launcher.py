from __future__ import annotations

import argparse
from pathlib import Path

from config_paths import resolve_config_path
from organizer import load_config, organize_once, watch_and_organize
from ui import run_ui
from windows_branding import configure_windows_app_identity


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SynkFolder")
    parser.add_argument("--once", action="store_true", help="Run one organize cycle and exit")
    parser.add_argument("--watch", action="store_true", help="Watch downloads continuously")
    parser.add_argument("--ui", action="store_true", help="Open desktop user interface")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    return parser.parse_args()


def main() -> None:
    configure_windows_app_identity()
    args = parse_args()
    config_path = resolve_config_path(args.config)
    if args.ui:
        run_ui(config_path)
        return

    config = load_config(config_path)
    if args.once:
        moved = organize_once(config)
        print(f"Done. Organized {moved} file(s).")
        return

    if args.watch:
        watch_and_organize(config)
        return

    # Default behavior for installed app: UI mode.
    run_ui(config_path)


if __name__ == "__main__":
    main()
