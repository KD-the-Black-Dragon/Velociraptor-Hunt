"""Ensure only one interactive game process runs at a time."""

from __future__ import annotations

import atexit
import multiprocessing as mp
import os
import sys
from dataclasses import dataclass
from typing import IO, Callable

from src.constants import GAME_TITLE

_SKIP_ENV = "KDS_SKIP_SINGLE_INSTANCE"
_ALREADY_RUNNING_HEADING = f"{GAME_TITLE} is already running."
_ALREADY_RUNNING_DETAIL = "Close the existing window before starting another copy."


@dataclass
class _InstanceGuard:
    release_fn: Callable[[], None]
    lock_file: IO[str] | None = None


_guard: _InstanceGuard | None = None


def _skip_requested() -> bool:
    return os.environ.get(_SKIP_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def _should_enforce() -> bool:
    if _skip_requested():
        return False
    return mp.current_process().name == "MainProcess"


def _try_acquire_windows() -> bool:
    import ctypes
    from ctypes import wintypes

    error_already_exists = 183
    kernel32 = ctypes.windll.kernel32
    mutex_name = "Local\\KDsVoreRoguelikeSingleInstance"
    handle = kernel32.CreateMutexW(None, wintypes.BOOL(True), mutex_name)
    if not handle:
        return True
    if kernel32.GetLastError() == error_already_exists:
        kernel32.CloseHandle(handle)
        return False

    def release() -> None:
        kernel32.ReleaseMutex(handle)
        kernel32.CloseHandle(handle)

    global _guard
    _guard = _InstanceGuard(release_fn=release)
    return True


def _try_acquire_posix() -> bool:
    import fcntl

    from src.user_data import USER_DATA_DIR

    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = USER_DATA_DIR / "instance.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    lock_file = os.fdopen(fd, "r+", encoding="utf-8")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_file.close()
        return False

    lock_file.seek(0)
    lock_file.write(str(os.getpid()))
    lock_file.truncate()
    lock_file.flush()

    def release() -> None:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        try:
            lock_file.close()
        except OSError:
            pass

    global _guard
    _guard = _InstanceGuard(release_fn=release, lock_file=lock_file)
    return True


def try_acquire_single_instance() -> bool:
    """Return False when another main game process already holds the lock."""
    global _guard
    if not _should_enforce():
        return True
    if _guard is not None:
        return True
    if sys.platform == "win32":
        return _try_acquire_windows()
    return _try_acquire_posix()


def release_single_instance() -> None:
    """Release the process lock when the game exits."""
    global _guard
    if _guard is None:
        return
    _guard.release_fn()
    _guard = None


def _register_release_on_exit() -> None:
    atexit.register(release_single_instance)


def show_already_running_dialog() -> None:
    """Show a modal dialog when a second copy is blocked. Never raises."""
    if _skip_requested():
        return
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        window = tk.Toplevel(root)
        window.title(GAME_TITLE)
        window.geometry("420x160")
        window.resizable(False, False)

        frame = tk.Frame(window, padx=16, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame,
            text=_ALREADY_RUNNING_HEADING,
            wraplength=360,
            justify=tk.LEFT,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=tk.W)

        tk.Label(
            frame,
            text=_ALREADY_RUNNING_DETAIL,
            wraplength=360,
            justify=tk.LEFT,
            font=("Segoe UI", 10),
        ).pack(anchor=tk.W, pady=(8, 12))

        tk.Button(frame, text="OK", width=10, command=window.destroy).pack(anchor=tk.E)
        window.protocol("WM_DELETE_WINDOW", window.destroy)
        window.grab_set()
        window.focus_force()
        root.wait_window(window)
        root.destroy()
    except Exception:
        pass


def block_second_instance() -> bool:
    """Acquire the lock or show a dialog and return False."""
    if try_acquire_single_instance():
        _register_release_on_exit()
        return True
    show_already_running_dialog()
    return False