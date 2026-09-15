"""Player-facing reporting for bad mod data files (never silent)."""

from __future__ import annotations

import os
import sys
from datetime import datetime

import attrs

from src.debug import paths as debug_paths
from src.debug.startup_error import (
    append_startup_error_log,
    format_startup_error_timestamp,
    show_startup_error_dialog,
)

MOD_DATA_ERROR_HEADING = "Mod data error"

_SKIP_DIALOG_ENV = "KDS_SKIP_STARTUP_DIALOG"
_SKIP_MOD_DIALOG_ENV = "KDS_SKIP_MOD_DIALOG"


@attrs.define(frozen=True)
class ModLoadIssue:
    """One skipped mod file during layered load."""

    mod_name: str
    filename: str
    reason: str


def format_mod_load_issues(issues: list[ModLoadIssue] | tuple[ModLoadIssue, ...]) -> str:
    """Multi-block detail text listing every failed mod/file."""
    if not issues:
        return ""
    blocks: list[str] = []
    for issue in issues:
        blocks.append(
            "\n".join(
                [
                    f"Mod: {issue.mod_name}",
                    f"File: {issue.filename}",
                    f"Problem: {issue.reason}",
                    "",
                    "That file was skipped. Other game data still loaded.",
                ]
            )
        )
    return "\n\n".join(blocks)


def format_mod_error_display(issues: list[ModLoadIssue] | tuple[ModLoadIssue, ...]) -> str:
    detail = format_mod_load_issues(issues).strip()
    if not detail:
        return MOD_DATA_ERROR_HEADING
    return f"{MOD_DATA_ERROR_HEADING}\n\n{detail}"


def _skip_dialog() -> bool:
    for env_name in (_SKIP_MOD_DIALOG_ENV, _SKIP_DIALOG_ENV):
        if os.environ.get(env_name, "").strip().lower() in {"1", "true", "yes", "on"}:
            return True
    return False


def show_mod_error_dialog(display_text: str) -> None:
    """Show a modal dialog for mod data errors. Never raises."""
    if _skip_dialog():
        return
    # Reuse startup dialog chrome; inject heading via display_text body.
    # show_startup_error_dialog always labels window "Startup Error" — use a
    # local twin so the title matches mod failures.
    try:
        import tkinter as tk
        from tkinter import scrolledtext

        root = tk.Tk()
        root.withdraw()
        root.title(MOD_DATA_ERROR_HEADING)

        window = tk.Toplevel(root)
        window.title(MOD_DATA_ERROR_HEADING)
        window.geometry("520x360")
        window.resizable(True, True)

        frame = tk.Frame(window, padx=12, pady=12)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame,
            text=MOD_DATA_ERROR_HEADING,
            wraplength=480,
            justify=tk.LEFT,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=tk.W)

        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=14, font=("Consolas", 10))
        text.pack(fill=tk.BOTH, expand=True, pady=(8, 8))
        detail = display_text
        if detail.startswith(MOD_DATA_ERROR_HEADING):
            detail = detail.removeprefix(MOD_DATA_ERROR_HEADING).lstrip("\n")
        text.insert(tk.END, detail)
        text.configure(state=tk.DISABLED)

        tk.Button(frame, text="OK", width=10, command=window.destroy).pack(anchor=tk.E)
        window.protocol("WM_DELETE_WINDOW", window.destroy)
        window.grab_set()
        window.focus_force()
        root.wait_window(window)
        root.destroy()
    except Exception:
        # Fallback: try startup dialog path
        try:
            show_startup_error_dialog(display_text)
        except Exception:
            pass


def report_mod_data_errors(issues: list[ModLoadIssue] | tuple[ModLoadIssue, ...]) -> None:
    """stderr + startup_error.log + dialog for skipped bad mod files. Never raises."""
    if not issues:
        return
    display = format_mod_error_display(issues)
    try:
        print(display, file=sys.stderr)
    except OSError:
        pass
    # Log under the same trail as other data errors so players can re-read after OK.
    try:
        append_startup_error_log(display)
    except Exception:
        try:
            debug_paths.LOGS_DIR.mkdir(parents=True, exist_ok=True)
            stamp = format_startup_error_timestamp(at=datetime.now().astimezone())
            with debug_paths.startup_error_log_path().open("a", encoding="utf-8") as handle:
                handle.write(f"{stamp}\n{display}\n\n")
        except OSError:
            pass
    show_mod_error_dialog(display)
