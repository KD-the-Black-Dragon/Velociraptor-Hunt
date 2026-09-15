"""Weapon attack delay and range-band (measure) effectiveness."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import attrs

from src.components import Position
from src.constants import DATA_DIR
from src.match_tactics import chebyshev

WEAPONS_PATH = DATA_DIR / "weapons.json"


@attrs.define(frozen=True)
class WeaponMeasureProfile:
    id: str
    attack_delay: float = 1.2
    # band -> mult (accuracy and damage share this mult for basics)
    band_mult: tuple[float, float, float, float, float] = (1.0, 0.85, 0.3, 0.15, 0.0)
    swappable: bool = True

    def mult_for_band(self, band: int) -> float:
        b = max(1, min(5, int(band)))
        return float(self.band_mult[b - 1])


_DEFAULT = WeaponMeasureProfile(id="default")


def range_band(attacker: Position, target: Position) -> int:
    """Chebyshev distance as range band (1 = adjacent, 5+ clamped to 5 for mult table)."""
    d = chebyshev(attacker, target)
    if d <= 0:
        return 1
    return min(5, int(d))


def is_knight_offset(dx: int, dy: int) -> bool:
    adx, ady = abs(dx), abs(dy)
    return (adx, ady) in ((1, 2), (2, 1))


def is_footwork_offset(dx: int, dy: int, *, max_chebyshev: int = 2) -> bool:
    """Legal footwork: any landing 1..max_chebyshev Chebyshev away (includes 1-tile).

    Prior design: max_chebyshev=2 means adjacent **or** two-step (incl. knight geometry
    within that radius). Self-tile (0,0) is never legal.
    """
    adx, ady = abs(int(dx)), abs(int(dy))
    dist = max(adx, ady)
    if dist <= 0:
        return False
    return dist <= int(max_chebyshev)


def all_footwork_offsets(*, max_chebyshev: int = 2) -> tuple[tuple[int, int], ...]:
    """Every legal footwork (dx, dy) offset from origin within max_chebyshev."""
    out: list[tuple[int, int]] = []
    r = int(max_chebyshev)
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if is_footwork_offset(dx, dy, max_chebyshev=r):
                out.append((dx, dy))
    return tuple(out)


def knight_reachable_band2(attacker: Position, target: Position) -> bool:
    """True if target is a knight-move away (counts as band-2 reachable for intents)."""
    return is_knight_offset(target.x - attacker.x, target.y - attacker.y)


def effective_band(attacker: Position, target: Position) -> int:
    """Band for measure resolution; knight-move foes treated as band 2."""
    if knight_reachable_band2(attacker, target):
        return 2
    return range_band(attacker, target)


def _parse_profile(raw: dict[str, Any]) -> WeaponMeasureProfile:
    mid = str(raw.get("id", "unknown"))
    delay = float(raw.get("attack_delay", 1.2))
    swappable = bool(raw.get("swappable", True))
    mraw = raw.get("measure") or {}
    bands = [1.0, 0.85, 0.3, 0.15, 0.0]
    if isinstance(mraw, dict):
        for i in range(1, 6):
            key = str(i)
            if key in mraw:
                bands[i - 1] = float(mraw[key])
            elif i in mraw:
                bands[i - 1] = float(mraw[i])
    return WeaponMeasureProfile(
        id=mid,
        attack_delay=delay,
        band_mult=(bands[0], bands[1], bands[2], bands[3], bands[4]),
        swappable=swappable,
    )


@lru_cache(maxsize=1)
def load_weapon_profiles(path: Path | None = None) -> dict[str, WeaponMeasureProfile]:
    p = path if path is not None else WEAPONS_PATH
    out: dict[str, WeaponMeasureProfile] = {"default": _DEFAULT}
    if not p.is_file():
        return out
    raw = json.loads(p.read_text(encoding="utf-8"))
    weapons = raw.get("weapons") if isinstance(raw, dict) else None
    if not isinstance(weapons, list):
        return out
    for row in weapons:
        if isinstance(row, dict) and row.get("id"):
            prof = _parse_profile(row)
            out[prof.id] = prof
    return out


def reset_weapon_measure_cache() -> None:
    load_weapon_profiles.cache_clear()


def get_weapon_profile(weapon_id: str | None) -> WeaponMeasureProfile:
    profiles = load_weapon_profiles()
    if weapon_id and weapon_id in profiles:
        return profiles[weapon_id]
    return profiles.get("short_sword", _DEFAULT)


def measure_mult(weapon_id: str | None, band: int) -> float:
    return get_weapon_profile(weapon_id).mult_for_band(band)


def attack_delay(weapon_id: str | None) -> float:
    return float(get_weapon_profile(weapon_id).attack_delay)


# Entity archetype → natural weapon defaults (no species layer; curated map)
ENTITY_DEFAULT_WEAPON: dict[str, str] = {
    "rat": "rat_teeth",
    "dire_rat": "rat_teeth",
    "wolf": "wolf_teeth",
    "dire_wolf": "wolf_teeth",
    "kobold": "dagger",
    "gnoll": "short_sword",
}


def default_weapon_for_entity(entity_id: str | None) -> str:
    if not entity_id:
        return "beast_claws"
    return ENTITY_DEFAULT_WEAPON.get(entity_id, "beast_claws")
