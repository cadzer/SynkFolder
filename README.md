# SynkFolder (AI)

A Windows-friendly Python tool that automatically organizes your `Downloads` folder into clean subfolders.

## Features

- Rule-based sorting for common file types (Documents, Images, Videos, etc.)
- AI-assisted classification for unknown file types (optional)
- Safe mode (`dry_run`) so you can preview moves before applying
- Continuous watch mode to organize new downloads automatically
- Duplicate-safe file naming

## Quick Start (Automatic Python Install on Windows)

### One-click launcher (recommended)

Use:

```bat
run_organizer.bat
```

or:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_organizer.ps1 -Watch
```

This launcher will:

1. Check if Python exists.
2. Automatically install Python via `winget` if missing.
3. Install project dependencies.
4. Start the organizer.

You can run one-time mode with:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_organizer.ps1 -Once
```

## Desktop UI

Launch GUI:

```bash
python main.py --ui
```

Packaged app behavior:

- The installed `.exe` opens the UI by default.
- In the UI, you can:
  - Edit Downloads path and settings
  - Toggle `dry_run` and AI usage
  - Run one cycle
  - Start/stop automatic watch mode
  - Close window and keep running in background (system tray)
  - Quit completely from UI or tray menu
  - See live logs

## Manual Quick Start

1. Install Python 3.10+.
2. Open terminal in this project folder.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. (Optional) Enable AI classification with an OpenAI-compatible key:

```powershell
setx OPENAI_API_KEY "your_key_here"
```

Restart terminal after setting env vars.

5. Run once:

```bash
python main.py --once
```

6. Run continuously (auto-organize new files):

```bash
python main.py --watch
```

## Build an EXE Installer

Generate a Windows installer (`SynkFolderSetup.exe`) with:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```

This build script will:

1. Install Python automatically if missing.
2. Install dependencies and `pyinstaller`.
3. Build `dist\SynkFolder.exe`.
4. Install Inno Setup automatically if missing.
5. Build installer in `dist_installer\SynkFolderSetup.exe`.

## Config

Edit `config.json`:

- `downloads_path`: folder to organize (default points to your Downloads)
- `dry_run`: `true` for preview-only, `false` to actually move files
- `watch_interval_seconds`: polling interval in watch mode
- `use_ai`: `true` to use AI for unknown extensions

## Folder Strategy

The app creates folders such as:

- `Documents`
- `Images`
- `Videos`
- `Audio`
- `Archives`
- `Code`
- `Installers`
- `Spreadsheets`
- `Presentations`
- `Unknown`

## Notes

- AI is only used when extension rules are not enough.
- No file content is uploaded by default; AI prompt uses filename + extension only.
- Keep `dry_run=true` first to verify behavior.
