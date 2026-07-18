"""Save format migration hooks.

Current wire version is v1. Call ``migrate_run`` after envelope integrity checks
and before applying a snapshot so future format bumps have a single landing spot.

Rules for agents (see also ``openspec/specs/save-load/spec.md``):

- Prefer **additive** fields with defaults on load — no version bump.
- Removed content ids → soft-drop (``sanitize``), not corrupt.
- True layout breaks → bump ``SAVE_FORMAT_VERSION``, add a step here, consult designer.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.save.schema import SAVE_FORMAT_VERSION, RunSnapshot


class SaveMigrationError(ValueError):
    """Run payload cannot be migrated to the current format."""


def migrate_run(
    run: RunSnapshot,
    *,
    from_version: int | None = None,
) -> RunSnapshot:
    """Return a run dict suitable for ``apply_run_snapshot``.

    **v1:** identity (shallow structural copy; nested values shared until mutated).
    When ``from_version`` is omitted, uses ``run["save_format_version"]`` if present,
    otherwise assumes the current ``SAVE_FORMAT_VERSION``.
    """
    if not isinstance(run, dict):
        raise SaveMigrationError("run payload must be an object")

    version = from_version
    if version is None:
        raw = run.get("save_format_version", SAVE_FORMAT_VERSION)
        try:
            version = int(raw)
        except (TypeError, ValueError) as exc:
            raise SaveMigrationError(
                f"invalid save_format_version in run: {raw!r}"
            ) from exc

    if version > SAVE_FORMAT_VERSION:
        raise SaveMigrationError(
            f"save format {version} is newer than this game "
            f"(supports {SAVE_FORMAT_VERSION})"
        )
    if version < 1:
        raise SaveMigrationError(f"unsupported save format version: {version}")

    # Future: if version < SAVE_FORMAT_VERSION, chain step functions here.
    # v1 → v1 is a no-op copy so callers can always mutate the result safely.
    migrated: RunSnapshot = deepcopy(run)
    migrated["save_format_version"] = SAVE_FORMAT_VERSION
    return migrated
