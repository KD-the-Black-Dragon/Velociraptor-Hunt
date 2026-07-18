"""Grapple HP → multi-phase swallow → digestion (JSON-driven)."""

from __future__ import annotations

import json
import random
from enum import Enum, auto
from functools import lru_cache
from pathlib import Path
from typing import Any

import attrs

from src.constants import DATA_DIR

MATCH_VORE_PATH = DATA_DIR / "match_vore.json"


class VorePhase(Enum):
    """Where a grab scene is in the pipeline."""

    GRAPPLE = auto()  # wrestling; grapple HP war
    SWALLOW = auto()  # multi-phase engulf in progress
    ENGULFED = auto()  # inside; digestion strikes


@attrs.define(frozen=True)
class VoreConfig:
    grab_aut_cost: float = 1.2
    grab_chance_base: float = 0.12
    grab_chance_per_missing_hp_fraction: float = 0.35
    grab_chance_if_downed: float = 0.9
    grab_balance_delta_predator: int = 1
    break_away_aut: float = 1.0
    break_away_base_chance: float = 0.35
    break_away_bonus_per_grapple_hp_fraction: float = 0.4
    counter_grapple_aut: float = 1.0
    counter_grapple_damage_min: int = 1
    counter_grapple_damage_max: int = 3
    counter_also_break_chance: float = 0.2
    predator_crush_aut: float = 1.2
    predator_crush_damage_min: int = 1
    predator_crush_damage_max: int = 3
    predator_secure_aut: float = 1.0
    predator_secure_grapple_damage: int = 2
    swallow_phases: int = 3
    swallow_phase_aut: float = 4.5
    digest_strike_aut: float = 3.0
    digest_strikes_to_end: int = 3
    ally_assist_release_damage_fraction: float = 0.2
    regurgitate_predator_hp_fraction: float = 0.2
    green_abort_before_digest: bool = True
    green_release_message: str = (
        "The exhibition ends — they must let go before things go too far."
    )
    flaunt_lines: tuple[str, ...] = ()


@attrs.define
class GrappleState:
    """Active grab scene between predator and prey."""

    predator: object  # Entity
    prey: object  # Entity
    grapple_hp: int
    grapple_hp_max: int
    phase: VorePhase = VorePhase.GRAPPLE
    swallow_phase_index: int = 0  # 0..swallow_phases-1 while SWALLOW
    digest_strikes: int = 0
    assist_damage_accumulated: float = 0.0
    prey_is_player: bool = True
    prey_ally_id: str | None = None


@lru_cache(maxsize=1)
def load_vore_config(path: Path | None = None) -> VoreConfig:
    p = path if path is not None else MATCH_VORE_PATH
    if not p.is_file():
        return VoreConfig(
            flaunt_lines=(
                "The predator belches contentedly, showing off for the crowd.",
            )
        )
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return VoreConfig()
    return _parse(raw)


def reset_vore_config_cache() -> None:
    load_vore_config.cache_clear()


def _parse(raw: dict[str, Any]) -> VoreConfig:
    flaunt = raw.get("flaunt_lines") or []
    if not isinstance(flaunt, list):
        flaunt = []
    return VoreConfig(
        grab_aut_cost=float(raw.get("grab_aut_cost", 1.2)),
        grab_chance_base=float(raw.get("grab_chance_base", 0.12)),
        grab_chance_per_missing_hp_fraction=float(
            raw.get("grab_chance_per_missing_hp_fraction", 0.35)
        ),
        grab_chance_if_downed=float(raw.get("grab_chance_if_downed", 0.9)),
        grab_balance_delta_predator=int(raw.get("grab_balance_delta_predator", 1)),
        break_away_aut=float(raw.get("break_away_aut", 1.0)),
        break_away_base_chance=float(raw.get("break_away_base_chance", 0.35)),
        break_away_bonus_per_grapple_hp_fraction=float(
            raw.get("break_away_bonus_per_grapple_hp_fraction", 0.4)
        ),
        counter_grapple_aut=float(raw.get("counter_grapple_aut", 1.0)),
        counter_grapple_damage_min=int(raw.get("counter_grapple_damage_min", 1)),
        counter_grapple_damage_max=int(raw.get("counter_grapple_damage_max", 3)),
        counter_also_break_chance=float(raw.get("counter_also_break_chance", 0.2)),
        predator_crush_aut=float(raw.get("predator_crush_aut", 1.2)),
        predator_crush_damage_min=int(raw.get("predator_crush_damage_min", 1)),
        predator_crush_damage_max=int(raw.get("predator_crush_damage_max", 3)),
        predator_secure_aut=float(raw.get("predator_secure_aut", 1.0)),
        predator_secure_grapple_damage=int(raw.get("predator_secure_grapple_damage", 2)),
        swallow_phases=max(1, int(raw.get("swallow_phases", 3))),
        swallow_phase_aut=float(raw.get("swallow_phase_aut", 4.5)),
        digest_strike_aut=float(raw.get("digest_strike_aut", 3.0)),
        digest_strikes_to_end=max(1, int(raw.get("digest_strikes_to_end", 3))),
        ally_assist_release_damage_fraction=float(
            raw.get("ally_assist_release_damage_fraction", 0.2)
        ),
        regurgitate_predator_hp_fraction=float(
            raw.get("regurgitate_predator_hp_fraction", 0.2)
        ),
        green_abort_before_digest=bool(raw.get("green_abort_before_digest", True)),
        green_release_message=str(
            raw.get(
                "green_release_message",
                "The exhibition ends — they must let go before things go too far.",
            )
        ),
        flaunt_lines=tuple(str(x) for x in flaunt),
    )


def grab_chance(
    *,
    prey_hp: int,
    prey_max_hp: int,
    prey_downed: bool,
    cfg: VoreConfig,
) -> float:
    if prey_downed or prey_hp <= 0:
        return min(1.0, cfg.grab_chance_if_downed)
    if prey_max_hp <= 0:
        return cfg.grab_chance_base
    missing = 1.0 - (prey_hp / prey_max_hp)
    return min(
        0.95,
        cfg.grab_chance_base + missing * cfg.grab_chance_per_missing_hp_fraction,
    )


def break_away_chance(*, grapple_hp: int, grapple_hp_max: int, cfg: VoreConfig) -> float:
    if grapple_hp_max <= 0:
        return cfg.break_away_base_chance
    frac = grapple_hp / grapple_hp_max
    return min(
        0.95,
        cfg.break_away_base_chance + frac * cfg.break_away_bonus_per_grapple_hp_fraction,
    )


def pick_flaunt(rng: random.Random, cfg: VoreConfig) -> str:
    if not cfg.flaunt_lines:
        return "The predator flaunts their victory."
    return rng.choice(list(cfg.flaunt_lines))
