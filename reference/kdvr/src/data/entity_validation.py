"""User-facing formatting for entities.json load failures."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.data.entity_loader import ENTITIES_PATH, EntityLoadError, load_entity_registry
from src.data.entity_registry import EntityRegistry

_ENTITY_DETAIL = re.compile(r"^entity '([^']+)': (.+)$")
_ENTITY_FIELD = re.compile(r"^entity '([^']+)'\.(.+)$")
_DUPLICATE_ID = re.compile(r"^duplicate entity id '([^']+)'$")
_ENTITIES_INDEX = re.compile(r"^entities\[(\d+)\] (.+)$")
_ENTITIES_FILE_PREFIX = re.compile(r"^entities file: (.+)$")


def format_entity_load_error(
    exc: EntityLoadError,
    *,
    path: Path = ENTITIES_PATH,
) -> str:
    """Map ``EntityLoadError.message`` to multi-line plain English (no traceback)."""
    message = str(exc)
    lines = [path.name, ""]

    match = _ENTITY_DETAIL.match(message)
    if match:
        lines.extend(
            [
                f"Entity: {match.group(1)}",
                "",
                "Problem:",
                match.group(2),
            ]
        )
        return "\n".join(lines)

    match = _ENTITY_FIELD.match(message)
    if match:
        lines.extend(
            [
                f"Entity: {match.group(1)}",
                "",
                "Problem:",
                f"{match.group(2)}",
            ]
        )
        return "\n".join(lines)

    match = _DUPLICATE_ID.match(message)
    if match:
        entity_id = match.group(1)
        lines.extend(
            [
                f"Entity: {entity_id}",
                "",
                "Problem:",
                f"duplicate entity id '{entity_id}'",
            ]
        )
        return "\n".join(lines)

    match = _ENTITIES_INDEX.match(message)
    if match:
        lines.extend(
            [
                "Problem:",
                f"entities[{match.group(1)}] {match.group(2)}",
            ]
        )
        return "\n".join(lines)

    match = _ENTITIES_FILE_PREFIX.match(message)
    if match:
        lines.extend(["Problem:", match.group(1)])
        return "\n".join(lines)

    if message.startswith("entities file must "):
        lines.extend(["Problem:", message.removeprefix("entities file ")])
        return "\n".join(lines)

    lines.extend(["Problem:", message])
    return "\n".join(lines)


def format_json_decode_error(
    exc: json.JSONDecodeError,
    *,
    path: Path,
    source: str | None = None,
) -> str:
    """Friendly JSON syntax error with line/column when available."""
    lines = [path.name, "", "Problem:"]
    if exc.lineno is not None and exc.colno is not None:
        detail = exc.msg or "invalid JSON"
        lines.append(
            f"Invalid JSON near line {exc.lineno} column {exc.colno} — {detail}"
        )
    else:
        lines.append(f"Invalid JSON — {exc.msg or 'could not parse file'}")
    return "\n".join(lines)


def load_entities_user_facing(
    path: Path | None = None,
    *,
    mods_root: Path | None = None,
) -> tuple[EntityRegistry | None, str | None]:
    """Load entities registry; return ``(registry, None)`` or ``(None, error_message)``.

    When *path* is None, loads core (this module's ``ENTITIES_PATH``) + enabled
    mods (hard-fail only on **core**). Mod file errors use the mod dialog and
    do not fail this call. Explicit *path* is single-file validation only.

    Tests may monkeypatch ``entity_validation.ENTITIES_PATH`` to override core.
    """
    if path is not None:
        data_path = path
        try:
            registry = load_entity_registry(data_path)
        except EntityLoadError as exc:
            return None, format_entity_load_error(exc, path=data_path)
        except json.JSONDecodeError as exc:
            return None, format_json_decode_error(exc, path=data_path)
        except OSError:
            return None, format_entity_load_error(
                EntityLoadError(f"could not read file '{data_path}'"),
                path=data_path,
            )
        return registry, None

    # Use this module's ENTITIES_PATH (monkeypatchable) as core for layered load.
    core_path = ENTITIES_PATH
    try:
        from src.mods.pipeline import load_entities_layered
        import src.data.entity_loader as entity_loader_mod

        registry, _issues = load_entities_layered(
            core_path=core_path,
            mods_root=mods_root,
            report=True,
        )
        entity_loader_mod._default_registry = registry
    except EntityLoadError as exc:
        return None, format_entity_load_error(exc, path=core_path)
    except json.JSONDecodeError as exc:
        return None, format_json_decode_error(exc, path=core_path)
    except OSError:
        return None, format_entity_load_error(
            EntityLoadError(f"could not read file '{core_path}'"),
            path=core_path,
        )
    return registry, None