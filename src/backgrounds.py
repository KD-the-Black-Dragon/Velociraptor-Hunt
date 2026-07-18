"""Career background choice stub (JSON)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import attrs

from src.constants import DATA_DIR

BACKGROUNDS_PATH = DATA_DIR / "backgrounds.json"


@attrs.define(frozen=True)
class BackgroundDef:
    background_id: str
    name: str
    blurb: str
    starting_gold_bonus: int = 0
    starting_renown: int = 0
    note: str = ""


@attrs.define(frozen=True)
class BackgroundsConfig:
    backgrounds: tuple[BackgroundDef, ...] = ()
    by_id: dict[str, BackgroundDef] = attrs.field(factory=dict)


@lru_cache(maxsize=1)
def load_backgrounds(path: Path | None = None) -> BackgroundsConfig:
    p = path if path is not None else BACKGROUNDS_PATH
    if not p.is_file():
        return _fallback()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return _fallback()
    return _parse(raw)


def reset_backgrounds_cache() -> None:
    load_backgrounds.cache_clear()


def _fallback() -> BackgroundsConfig:
    b = BackgroundDef(
        "street_scrapper",
        "Street Scrapper",
        "You learned to fight for scraps.",
        0,
        0,
        "Stub.",
    )
    return BackgroundsConfig(backgrounds=(b,), by_id={b.background_id: b})


def _parse(raw: dict[str, Any]) -> BackgroundsConfig:
    items: list[BackgroundDef] = []
    for row in raw.get("backgrounds") or []:
        if not isinstance(row, dict):
            continue
        bid = str(row.get("id") or "")
        if not bid:
            continue
        items.append(
            BackgroundDef(
                background_id=bid,
                name=str(row.get("name") or bid),
                blurb=str(row.get("blurb") or ""),
                starting_gold_bonus=int(row.get("starting_gold_bonus", 0)),
                starting_renown=int(row.get("starting_renown", 0)),
                note=str(row.get("note") or ""),
            )
        )
    if not items:
        return _fallback()
    return BackgroundsConfig(
        backgrounds=tuple(items),
        by_id={b.background_id: b for b in items},
    )


def apply_background_to_career(career: Any, background_id: str) -> BackgroundDef | None:
    """Mutate career gold/renown/background fields. Returns the def used."""
    cfg = load_backgrounds()
    b = cfg.by_id.get(background_id) or (
        cfg.backgrounds[0] if cfg.backgrounds else None
    )
    if b is None:
        return None
    career.background_id = b.background_id
    career.gold = max(0, int(career.gold) + int(b.starting_gold_bonus))
    career.renown = max(0, int(career.renown) + int(b.starting_renown))
    return b
