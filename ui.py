from __future__ import annotations

import json
import queue
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw, ImageTk

from icon_paths import get_icon_ico_path, get_icon_png_path
from organizer import OrganizerConfig, load_config, organize_once, watch_and_organize
from windows_branding import apply_windows_window_icon, configure_windows_app_identity


# Modern dark palette
COLORS = {
    "bg": "#0d1117",
    "surface": "#161b22",
    "surface_alt": "#21262d",
    "border": "#30363d",
    "text": "#e6edf3",
    "text_muted": "#8b949e",
    "accent": "#58a6ff",
    "accent_hover": "#79b8ff",
    "success": "#3fb950",
    "success_hover": "#56d364",
    "warning": "#d29922",
    "warning_hover": "#e3b341",
    "danger": "#f85149",
    "danger_hover": "#ff7b72",
    "purple": "#a371f7",
    "purple_hover": "#bc8cff",
    "log_bg": "#0d1117",
    "log_fg": "#c9d1d9",
}


class OrganizerUI:
    def __init__(self, root: ctk.CTk, config_path: Path) -> None:
        self.root = root
        self.root.title("SynkFolder")
        self.root.geometry("900x620")
        self.root.minsize(760, 520)
        self.root.configure(fg_color=COLORS["bg"])

        self.config_path = config_path
        self.config = load_config(config_path)

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.tray_icon: pystray.Icon | None = None
        self.tray_thread: threading.Thread | None = None
        self._watch_running = False
        self._window_icon: ImageTk.PhotoImage | None = None

        self._apply_window_icon()
        self._build_layout()
        self._sync_form_from_config()
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self.root.after(150, self._drain_logs)

    def _btn(
        self,
        parent,
        text: str,
        command,
        color: str,
        hover: str,
        width: int = 130,
        height: int = 38,
        **kwargs,
    ) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=height,
            corner_radius=12,
            fg_color=color,
            hover_color=hover,
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            border_width=0,
            **kwargs,
        )

    def _build_layout(self) -> None:
        # Header
        header = ctk.CTkFrame(self.root, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 8))

        title_block = ctk.CTkFrame(header, fg_color="transparent")
        title_block.pack(side="left")

        ctk.CTkLabel(
            title_block,
            text="SynkFolder",
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_block,
            text="AI-powered folder sorting",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(2, 0))

        self.status_frame = ctk.CTkFrame(
            header, fg_color=COLORS["surface_alt"], corner_radius=20, height=36
        )
        self.status_frame.pack(side="right", padx=(0, 4))
        self.status_dot = ctk.CTkLabel(
            self.status_frame, text="●", font=ctk.CTkFont(size=14), text_color=COLORS["text_muted"]
        )
        self.status_dot.pack(side="left", padx=(14, 4), pady=8)
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Idle",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLORS["text_muted"],
        )
        self.status_label.pack(side="left", padx=(0, 14), pady=8)

        # Settings card
        cfg_outer = ctk.CTkFrame(self.root, fg_color=COLORS["surface"], corner_radius=16)
        cfg_outer.pack(fill="x", padx=24, pady=(8, 12))

        cfg_inner = ctk.CTkFrame(cfg_outer, fg_color="transparent")
        cfg_inner.pack(fill="x", padx=20, pady=18)

        ctk.CTkLabel(
            cfg_inner,
            text="Settings",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["accent"],
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 14))

        ctk.CTkLabel(
            cfg_inner,
            text="Choose a folder to organize your files",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"],
        ).grid(row=1, column=0, sticky="w")

        path_row = ctk.CTkFrame(cfg_inner, fg_color="transparent")
        path_row.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(4, 12))
        path_row.columnconfigure(0, weight=1)

        self.path_var = ctk.StringVar()
        self.path_entry = ctk.CTkEntry(
            path_row,
            textvariable=self.path_var,
            height=40,
            corner_radius=10,
            fg_color=COLORS["surface_alt"],
            border_color=COLORS["border"],
            border_width=1,
            text_color=COLORS["text"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self._btn(
            path_row,
            "Browse",
            self.select_downloads_folder,
            COLORS["accent"],
            COLORS["accent_hover"],
            width=100,
            height=40,
        ).grid(row=0, column=1)

        opts = ctk.CTkFrame(cfg_inner, fg_color="transparent")
        opts.grid(row=3, column=0, columnspan=3, sticky="ew")
        opts.columnconfigure(1, weight=1)

        self.dry_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opts,
            text="Dry run (preview only — no file moves)",
            variable=self.dry_var,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text"],
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            border_color=COLORS["border"],
            corner_radius=6,
        ).grid(row=0, column=0, sticky="w", pady=4)

        self.ai_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opts,
            text="Use AI for unknown file types",
            variable=self.ai_var,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text"],
            fg_color=COLORS["purple"],
            hover_color=COLORS["purple_hover"],
            border_color=COLORS["border"],
            corner_radius=6,
        ).grid(row=1, column=0, sticky="w", pady=4)

        interval_row = ctk.CTkFrame(opts, fg_color="transparent")
        interval_row.grid(row=2, column=0, sticky="w", pady=4)

        ctk.CTkLabel(
            interval_row,
            text="Watch interval (sec)",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"],
        ).pack(side="left", padx=(0, 10))

        self.interval_var = ctk.StringVar()
        ctk.CTkEntry(
            interval_row,
            textvariable=self.interval_var,
            width=70,
            height=36,
            corner_radius=10,
            fg_color=COLORS["surface_alt"],
            border_color=COLORS["border"],
            border_width=1,
            text_color=COLORS["text"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
        ).pack(side="left")

        self.background_on_close_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opts,
            text="Keep running in background when window is closed",
            variable=self.background_on_close_var,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text"],
            fg_color=COLORS["warning"],
            hover_color=COLORS["warning_hover"],
            border_color=COLORS["border"],
            corner_radius=6,
        ).grid(row=3, column=0, sticky="w", pady=4)

        cfg_inner.columnconfigure(0, weight=1)

        # Action buttons
        actions = ctk.CTkFrame(self.root, fg_color="transparent")
        actions.pack(fill="x", padx=24, pady=(0, 12))

        left_actions = ctk.CTkFrame(actions, fg_color="transparent")
        left_actions.pack(side="left")

        self.run_once_btn = self._btn(
            left_actions,
            "Run Once",
            self.run_once,
            COLORS["accent"],
            COLORS["accent_hover"],
        )
        self.run_once_btn.pack(side="left", padx=(0, 8))

        self.start_watch_btn = self._btn(
            left_actions,
            "Start Auto Watch",
            self.start_watch,
            COLORS["success"],
            COLORS["success_hover"],
            width=150,
        )
        self.start_watch_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = self._btn(
            left_actions,
            "Stop",
            self.stop_watch,
            COLORS["warning"],
            COLORS["warning_hover"],
            width=100,
            state="disabled",
        )
        self.stop_btn.pack(side="left", padx=(0, 8))

        self._btn(
            left_actions,
            "Quit",
            self.quit_completely,
            COLORS["danger"],
            COLORS["danger_hover"],
            width=90,
        ).pack(side="left")

        self._btn(
            actions,
            "Save Settings",
            self.save_settings,
            COLORS["purple"],
            COLORS["purple_hover"],
            width=130,
        ).pack(side="right")

        # Log panel
        log_outer = ctk.CTkFrame(self.root, fg_color=COLORS["surface"], corner_radius=16)
        log_outer.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        log_header = ctk.CTkFrame(log_outer, fg_color="transparent")
        log_header.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            log_header,
            text="Live Log",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(side="left")

        self.log_text = ctk.CTkTextbox(
            log_outer,
            wrap="word",
            state="disabled",
            fg_color=COLORS["log_bg"],
            text_color=COLORS["log_fg"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=12,
            font=ctk.CTkFont(family="Consolas", size=12),
        )
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def _set_status(self, running: bool) -> None:
        self._watch_running = running
        if running:
            self.status_dot.configure(text_color=COLORS["success"])
            self.status_label.configure(text="Watching", text_color=COLORS["success"])
        else:
            self.status_dot.configure(text_color=COLORS["text_muted"])
            self.status_label.configure(text="Idle", text_color=COLORS["text_muted"])

    def _sync_form_from_config(self) -> None:
        self.path_var.set(str(self.config.downloads_path))
        self.dry_var.set(self.config.dry_run)
        self.ai_var.set(self.config.use_ai)
        self.interval_var.set(str(self.config.watch_interval_seconds))

    def _build_config_from_form(self) -> OrganizerConfig:
        interval = int(self.interval_var.get().strip() or "5")
        if interval < 1:
            interval = 1
        return OrganizerConfig(
            downloads_path=Path(self.path_var.get().strip()),
            dry_run=bool(self.dry_var.get()),
            watch_interval_seconds=interval,
            use_ai=bool(self.ai_var.get()),
            ai_model=self.config.ai_model or "gpt-4o-mini",
        )

    def _load_icon_image(self, size: int = 64) -> Image.Image:
        png_path = get_icon_png_path()
        if png_path.exists():
            image = Image.open(png_path).convert("RGBA")
            return image.resize((size, size), Image.Resampling.LANCZOS)
        image = Image.new("RGBA", (size, size), color=(13, 17, 23, 255))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((8, 8, size - 8, size - 8), radius=10, outline=(88, 166, 255), width=3)
        draw.rounded_rectangle((size // 3, size // 3, size - size // 3, size - size // 3), radius=6, fill=(63, 185, 80))
        return image

    def _apply_window_icon(self) -> None:
        ico_path = get_icon_ico_path()
        apply_windows_window_icon(self.root, ico_path)
        try:
            self._window_icon = ImageTk.PhotoImage(self._load_icon_image(64))
            self.root.iconphoto(True, self._window_icon)
        except Exception:
            pass

    def _create_tray_image(self) -> Image.Image:
        return self._load_icon_image(64)

    def _ensure_tray_icon(self) -> None:
        if self.tray_icon is not None:
            return

        menu = pystray.Menu(
            pystray.MenuItem("Open", lambda: self.root.after(0, self.show_window)),
            pystray.MenuItem("Quit Completely", lambda: self.root.after(0, self.quit_completely)),
        )
        self.tray_icon = pystray.Icon(
            name="SynkFolder",
            title="SynkFolder",
            icon=self._create_tray_image(),
            menu=menu,
        )
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()

    def _stop_tray_icon(self) -> None:
        if self.tray_icon is not None:
            self.tray_icon.stop()
            self.tray_icon = None

    def show_window(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def select_downloads_folder(self) -> None:
        selected = filedialog.askdirectory(
            title="Select Downloads Folder",
            initialdir=self.path_var.get().strip() or str(Path.home()),
        )
        if selected:
            self.path_var.set(selected)

    def _log(self, message: str) -> None:
        self.log_queue.put(message)

    def _append_log(self, msg: str) -> None:
        self.log_text.configure(state="normal")
        if msg.startswith("[MOVED]"):
            line_color = COLORS["success"]
        elif msg.startswith("[DRY RUN]"):
            line_color = COLORS["warning"]
        elif msg.startswith("[INFO]"):
            line_color = COLORS["accent"]
        else:
            line_color = COLORS["log_fg"]

        self.log_text.insert("end", msg + "\n")
        # Color last line via tag emulation: CTkTextbox uses underlying tk.Text
        try:
            inner = self.log_text._textbox
            start = inner.index("end-2l linestart")
            end = inner.index("end-1c")
            tag = f"tag_{id(msg)}"
            inner.tag_add(tag, start, end)
            inner.tag_config(tag, foreground=line_color)
        except Exception:
            pass

        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _drain_logs(self) -> None:
        while not self.log_queue.empty():
            self._append_log(self.log_queue.get_nowait())
        self.root.after(150, self._drain_logs)

    def save_settings(self) -> None:
        try:
            self.config = self._build_config_from_form()
            data = {
                "downloads_path": str(self.config.downloads_path),
                "dry_run": self.config.dry_run,
                "watch_interval_seconds": self.config.watch_interval_seconds,
                "use_ai": self.config.use_ai,
                "ai_model": self.config.ai_model,
            }
            self.config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            self._log(f"[INFO] Settings saved to {self.config_path}")
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))

    def run_once(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showwarning("Busy", "A task is already running.")
            return
        try:
            self.config = self._build_config_from_form()
        except Exception as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return

        def task() -> None:
            self._log("[INFO] Running one cycle...")
            moved = organize_once(self.config, logger=self._log)
            self._log(f"[INFO] Done. Organized {moved} file(s).")

        self.worker_thread = threading.Thread(target=task, daemon=True)
        self.worker_thread.start()

    def start_watch(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showwarning("Busy", "Watch is already running.")
            return
        try:
            self.config = self._build_config_from_form()
        except Exception as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return

        self.stop_event.clear()
        self._set_watch_state(running=True)

        def task() -> None:
            watch_and_organize(self.config, logger=self._log, stop_event=self.stop_event)
            self.root.after(0, lambda: self._set_watch_state(running=False))

        self.worker_thread = threading.Thread(target=task, daemon=True)
        self.worker_thread.start()
        self._log("[INFO] Auto watch started.")

    def stop_watch(self) -> None:
        self.stop_event.set()
        self._log("[INFO] Stop requested...")

    def hide_to_background(self) -> None:
        if not (self.worker_thread and self.worker_thread.is_alive()):
            self.start_watch()
        self._ensure_tray_icon()
        self.root.withdraw()
        self._log("[INFO] Running in background. Use tray icon to reopen or quit.")

    def on_window_close(self) -> None:
        if self.background_on_close_var.get():
            self.hide_to_background()
            return
        self.quit_completely()

    def quit_completely(self) -> None:
        self.stop_event.set()
        self._stop_tray_icon()
        self.root.after(200, self.root.destroy)

    def _set_watch_state(self, running: bool) -> None:
        self._set_status(running)
        if running:
            self.start_watch_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.run_once_btn.configure(state="disabled")
        else:
            self.start_watch_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.run_once_btn.configure(state="normal")


def run_ui(config_path: str | Path = "config.json") -> None:
    from config_paths import resolve_config_path
    from single_instance import ensure_single_instance

    guard = ensure_single_instance()
    if guard is None:
        return

    configure_windows_app_identity()
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root = ctk.CTk()
    app = OrganizerUI(root, resolve_config_path(config_path))
    guard.start_listener(app.show_window, schedule=lambda fn: root.after(0, fn))
    try:
        root.mainloop()
    finally:
        guard.stop()
