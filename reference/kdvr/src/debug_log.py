from __future__ import annotations

import os

DEBUG_STDOUT_ENV = "DEBUG_STDOUT"


def debug_stdout_enabled() -> bool:
    """True when development stdout logging is enabled via environment."""
    value = os.environ.get(DEBUG_STDOUT_ENV, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def debug_print(*args: object, **kwargs: object) -> None:
    """Print to stdout only when ``DEBUG_STDOUT`` is set (see ``debug_stdout_enabled``)."""
    if not debug_stdout_enabled():
        return
    print(*args, **kwargs)  # type: ignore[arg-type]