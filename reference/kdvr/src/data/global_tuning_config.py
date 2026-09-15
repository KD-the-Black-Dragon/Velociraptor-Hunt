"""Parsed shapes for ``data/global_tuning.json`` (player / regen / vore / loot)."""

from __future__ import annotations

import attrs


@attrs.define(frozen=True)
class PlayerTuning:
    max_hp: int
    accuracy: float
    evade: float
    ac: int
    min_damage: int
    max_damage: int


@attrs.define(frozen=True)
class RegenTuning:
    hp: int
    every_n_player_turns: int
    evil_every_n_player_turns: int


@attrs.define(frozen=True)
class VoreTuning:
    hp_threshold: float
    hit_min: float
    hit_max: float
    escape_base: float
    escape_per_fail: float
    struggle_damage: int


@attrs.define(frozen=True)
class LootTuning:
    max_floor_item_placements: int
    min_floor_potions: int


@attrs.define(frozen=True)
class GlobalTuning:
    schema_version: int
    player: PlayerTuning
    regen: RegenTuning
    vore: VoreTuning
    loot: LootTuning
