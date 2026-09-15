"""JSON deep-merge helpers for mod layering (objects recurse; arrays replace)."""

from __future__ import annotations

from typing import Any


def deep_merge_json(base: Any, overlay: Any) -> Any:
    """Merge ``overlay`` onto ``base`` without mutating either input.

    - Both values are objects (``dict``): recurse per key; keys only in base kept.
    - Otherwise (arrays, scalars, ``null``, or type mismatch): use ``overlay``.
    """
    if not isinstance(base, dict) or not isinstance(overlay, dict):
        return overlay
    out: dict[str, Any] = dict(base)
    for key, value in overlay.items():
        existing = out.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            out[key] = deep_merge_json(existing, value)
        else:
            out[key] = value
    return out
