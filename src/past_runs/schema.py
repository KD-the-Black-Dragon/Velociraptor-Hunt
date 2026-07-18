"""Past run record schema."""

from __future__ import annotations

from typing import Any

import attrs

PAST_RUNS_FORMAT_VERSION = 1
MAX_PAST_RUNS = 65535


@attrs.define(frozen=True)
class PastRunRecord:
    character_name: str
    ending_kind: str
    ending_detail: str
    monsters_defeated: int
    runes_collected: int
    depth: int
    date: str  # MM/DD/YYYY
    macguffin_score: int | None = None
    difficulty_id: str | None = None
    difficulty_display: str | None = None


def record_to_dict(record: PastRunRecord) -> dict[str, Any]:
    data: dict[str, Any] = {
        "character_name": record.character_name,
        "ending_kind": record.ending_kind,
        "ending_detail": record.ending_detail,
        "monsters_defeated": record.monsters_defeated,
        "runes_collected": record.runes_collected,
        "depth": record.depth,
        "date": record.date,
    }
    if record.macguffin_score is not None:
        data["macguffin_score"] = record.macguffin_score
    if record.difficulty_id is not None:
        data["difficulty_id"] = record.difficulty_id
    if record.difficulty_display is not None:
        data["difficulty_display"] = record.difficulty_display
    return data


def parse_record(raw: Any) -> PastRunRecord | None:
    if not isinstance(raw, dict):
        return None
    try:
        macguffin_score_raw = raw.get("macguffin_score")
        macguffin_score = (
            max(0, int(macguffin_score_raw))
            if macguffin_score_raw is not None
            else None
        )
        difficulty_id_raw = raw.get("difficulty_id")
        difficulty_id = (
            str(difficulty_id_raw) if difficulty_id_raw is not None else None
        )
        difficulty_display_raw = raw.get("difficulty_display")
        difficulty_display = (
            str(difficulty_display_raw)
            if difficulty_display_raw is not None
            else None
        )
        return PastRunRecord(
            character_name=str(raw["character_name"]),
            ending_kind=str(raw["ending_kind"]),
            ending_detail=str(raw.get("ending_detail", "")),
            monsters_defeated=max(0, int(raw["monsters_defeated"])),
            runes_collected=max(0, int(raw["runes_collected"])),
            depth=max(0, int(raw["depth"])),
            date=str(raw["date"]),
            macguffin_score=macguffin_score,
            difficulty_id=difficulty_id,
            difficulty_display=difficulty_display,
        )
    except (KeyError, TypeError, ValueError):
        return None


def parse_display_date(date: str) -> tuple[int, int, int]:
    """Parse MM/DD/YYYY for stable sorting (year, month, day)."""
    parts = date.split("/")
    if len(parts) != 3:
        return (0, 0, 0)
    try:
        month = int(parts[0])
        day = int(parts[1])
        year = int(parts[2])
    except ValueError:
        return (0, 0, 0)
    return (year, month, day)