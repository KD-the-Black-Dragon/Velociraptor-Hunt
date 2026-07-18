"""Pre-window JSON validation errors: dialog, log file, and stderr."""

from __future__ import annotations

import os
import sys
from datetime import datetime

from src.debug import paths as debug_paths

STARTUP_JSON_ERROR_HEADING = "Unable to start the game due to JSON error."

_SKIP_DIALOG_ENV = "KDS_SKIP_STARTUP_DIALOG"


def format_startup_error_timestamp(*, at: datetime | None = None) -> str:
    """Local time like ``7/6/2026 9:56 AM`` (no leading zeros on month/day/hour)."""
    moment = at if at is not None else datetime.now().astimezone()
    hour = moment.strftime("%I").lstrip("0") or "12"
    return f"{moment.month}/{moment.day}/{moment.year} {hour}:{moment.minute:02d} {moment.strftime('%p')}"


def format_startup_error_display(detail_message: str) -> str:
    """Full player-facing text: fixed heading plus formatted validation detail."""
    detail = detail_message.strip()
    if not detail:
        return STARTUP_JSON_ERROR_HEADING
    return f"{STARTUP_JSON_ERROR_HEADING}\n\n{detail}"


def format_startup_error_log_entry(
    detail_message: str,
    *,
    at: datetime | None = None,
) -> str:
    """One append block for ``startup_error.log``."""
    display = format_startup_error_display(detail_message)
    stamp = format_startup_error_timestamp(at=at)
    return f"{stamp}\n{display}\n\n"


def append_startup_error_log(detail_message: str, *, at: datetime | None = None) -> None:
    """Append a timestamped entry to ``logs/startup_error.log``. Never raises."""
    try:
        debug_paths.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        entry = format_startup_error_log_entry(detail_message, at=at)
        with debug_paths.startup_error_log_path().open("a", encoding="utf-8") as handle:
            handle.write(entry)
    except OSError:
        pass


def show_startup_error_dialog(display_text: str) -> None:
    """Show a modal dialog with the full startup error text. Never raises."""
    if os.environ.get(_SKIP_DIALOG_ENV, "").strip().lower() in {"1", "true", "yes", "on"}:
        return
    try:
        import tkinter as tk
        from tkinter import scrolledtext

        root = tk.Tk()
        root.withdraw()
        root.title("Startup Error")

        window = tk.Toplevel(root)
        window.title("Startup Error")
        window.geometry("520x360")
        window.resizable(True, True)

        frame = tk.Frame(window, padx=12, pady=12)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame,
            text=STARTUP_JSON_ERROR_HEADING,
            wraplength=480,
            justify=tk.LEFT,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=tk.W)

        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=14, font=("Consolas", 10))
        text.pack(fill=tk.BOTH, expand=True, pady=(8, 8))
        detail = display_text
        if detail.startswith(STARTUP_JSON_ERROR_HEADING):
            detail = detail.removeprefix(STARTUP_JSON_ERROR_HEADING).lstrip("\n")
        text.insert(tk.END, detail)
        text.configure(state=tk.DISABLED)

        tk.Button(frame, text="OK", width=10, command=window.destroy).pack(anchor=tk.E)
        window.protocol("WM_DELETE_WINDOW", window.destroy)
        window.grab_set()
        window.focus_force()
        root.wait_window(window)
        root.destroy()
    except Exception:
        pass


def report_startup_json_error(detail_message: str) -> None:
    """Emit startup JSON failure to stderr, ``startup_error.log``, and dialog."""
    display = format_startup_error_display(detail_message)
    try:
        print(display, file=sys.stderr)
    except OSError:
        pass
    append_startup_error_log(detail_message)
    show_startup_error_dialog(display)