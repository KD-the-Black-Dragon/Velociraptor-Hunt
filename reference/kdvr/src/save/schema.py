"""Save document schema constants and envelope builder.

Field inventory and agent save-compat checklist:
``openspec/specs/save-load/spec.md`` and ``src/save/FIELDS.md``.
"""

from __future__ import annotations

import time
from typing import Any

SAVE_FORMAT_VERSION = 1

RunSnapshot = dict[str, Any]
SaveEnvelope = dict[str, Any]


def build_save_envelope(
    run: RunSnapshot,
    *,
    saved_at_unix: int | None = None,
    payload_sha256: str = "",
) -> SaveEnvelope:
    """Build the top-level save document (file I/O and hashing added in PR2)."""
    return {
        "save_format_version": SAVE_FORMAT_VERSION,
        "saved_at_unix": saved_at_unix if saved_at_unix is not None else int(time.time()),
        "payload_sha256": payload_sha256,
        "run": run,
    }