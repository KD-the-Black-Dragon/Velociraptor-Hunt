"""Depth-scaling schedules and difficulty profiles (data-driven NPC power curve)."""

from __future__ import annotations

from typing import Mapping

import attrs

from src.components import Alignment

# Stats that use dual-int schedules (float stats multiply by unit after).
INTEGER_STAT_KEYS = frozenset(
    {
        "max_hp",
        "ac",
        "min_damage",
        "max_damage",
        "digestion_damage_per_tick",
    }
)
FLOAT_STAT_KEYS = frozenset({"accuracy", "evade"})
ALL_STAT_KEYS = INTEGER_STAT_KEYS | FLOAT_STAT_KEYS

ALIGNMENT_BY_NAME: dict[str, Alignment] = {
    "good": Alignment.GOOD,
    "evil": Alignment.EVIL,
    "neutral": Alignment.NEUTRAL,
}


@attrs.define(frozen=True)
class StatSchedule:
    """Dual-integer depth schedule: per_floor * steps + floor(steps/n) * bank_amount."""

    per_floor: int = 0
    every_n_floors: int = 0
    bank_amount: int = 1
    start_depth: int = 1
    unit: float = 1.0  # float stats: multiply dual-int result by unit


@attrs.define(frozen=True)
class DepthBonuses:
    max_hp: int = 0
    ac: int = 0
    evade: float = 0.0
    accuracy: float = 0.0
    min_damage: int = 0
    max_damage: int = 0
    digestion_damage_per_tick: int = 0


@attrs.define(frozen=True)
class PrefixSpawnConfig:
    """Chance to roll an NPC prefix at floor spawn (stock: all zero = never)."""

    base_chance_pct: int = 0
    chance_pct_per_depth_step: int = 0
    max_chance_pct: int = 100
    start_depth: int = 1

    def chance_at_depth(self, floor_depth: int) -> int:
        steps = max(0, floor_depth - self.start_depth)
        raw = self.base_chance_pct + self.chance_pct_per_depth_step * steps
        return max(0, min(self.max_chance_pct, raw))


@attrs.define(frozen=True)
class SpawnAiFreezeConfig:
    """One-shot spawn freeze so far NPCs do not all rush the player at once.

    ``freeze_turns = min(max_turns, max(0, chebyshev - distance_offset) * turns_per_chebyshev)``
    Higher freeze values are gentler for the player. Disabled profiles use enabled=False.
    """

    enabled: bool = True
    turns_per_chebyshev: int = 2
    distance_offset: int = 6
    max_turns: int = 48
    proximity_unfreeze: int = 8

    def freeze_turns_for_chebyshev(self, chebyshev: int) -> int:
        if not self.enabled:
            return 0
        dist = max(0, int(chebyshev))
        raw = max(0, dist - self.distance_offset) * max(0, self.turns_per_chebyshev)
        return min(max(0, self.max_turns), raw)


@attrs.define(frozen=True)
class DifficultyProfile:
    id: str
    display_name: str
    apply_to_alignments: frozenset[Alignment]
    stats: Mapping[str, StatSchedule]
    density_multiplier: float = 1.0
    runes_per_floor_override: int | None = None
    rune_pieces_multiplier: int = 1
    prefix_spawn: PrefixSpawnConfig = attrs.field(factory=PrefixSpawnConfig)
    spawn_ai_freeze: SpawnAiFreezeConfig = attrs.field(factory=SpawnAiFreezeConfig)


@attrs.define(frozen=True)
class DepthScalingConfig:
    schema_version: int
    default_difficulty_id: str
    difficulties: Mapping[str, DifficultyProfile]

    def profile_for(self, difficulty_id: str | None) -> DifficultyProfile:
        """Resolve profile; unknown id falls back to default_difficulty_id."""
        if difficulty_id is not None and difficulty_id in self.difficulties:
            return self.difficulties[difficulty_id]
        return self.difficulties[self.default_difficulty_id]

    def list_difficulty_ids(self) -> tuple[str, ...]:
        """Stable file order for Options cycling."""
        return tuple(self.difficulties.keys())


def list_difficulty_ids(
    config: DepthScalingConfig | None = None,
) -> tuple[str, ...]:
    from src.data.depth_scaling_loader import default_depth_scaling_config

    cfg = config if config is not None else default_depth_scaling_config()
    return cfg.list_difficulty_ids()


def cycle_difficulty_id(
    current: str,
    *,
    step: int = 1,
    config: DepthScalingConfig | None = None,
) -> str:
    """Cycle difficulty id by step (+1 / -1). Unknown current → default."""
    from src.data.depth_scaling_loader import default_depth_scaling_config

    cfg = config if config is not None else default_depth_scaling_config()
    ids = list(cfg.list_difficulty_ids())
    if not ids:
        return cfg.default_difficulty_id
    if current == "easy":
        current = "easier"
    if current not in ids:
        current = cfg.default_difficulty_id
    index = ids.index(current)
    return ids[(index + step) % len(ids)]


def validate_difficulty_id(
    value: str | None,
    *,
    config: DepthScalingConfig | None = None,
) -> str:
    """Return a known difficulty id (fallback to default).

    Legacy settings used id ``easy``; soft-map to ``easier`` so old prefs load cleanly.
    """
    from src.data.depth_scaling_loader import default_depth_scaling_config

    cfg = config if config is not None else default_depth_scaling_config()
    if value == "easy":
        value = "easier"
    if value and value in cfg.difficulties:
        return value
    return cfg.default_difficulty_id


def dual_int_steps(depth: int, start_depth: int) -> int:
    return max(0, depth - start_depth)


def dual_int_bonus(schedule: StatSchedule, depth: int) -> int:
    """Integer dual-knob formula (before accuracy unit)."""
    steps = dual_int_steps(depth, schedule.start_depth)
    bank = 0
    if schedule.every_n_floors > 0:
        bank = (steps // schedule.every_n_floors) * schedule.bank_amount
    return schedule.per_floor * steps + bank


def resolve_bonuses(profile: DifficultyProfile, depth: int) -> DepthBonuses:
    """Compute depth bonuses for a profile at floor depth (alignment not checked)."""
    stats = profile.stats

    def int_stat(key: str) -> int:
        schedule = stats.get(key)
        if schedule is None:
            return 0
        return dual_int_bonus(schedule, depth)

    def float_stat(key: str) -> float:
        schedule = stats.get(key)
        if schedule is None:
            return 0.0
        return float(dual_int_bonus(schedule, depth)) * float(schedule.unit)

    return DepthBonuses(
        max_hp=int_stat("max_hp"),
        ac=int_stat("ac"),
        evade=float_stat("evade"),
        accuracy=float_stat("accuracy"),
        min_damage=int_stat("min_damage"),
        max_damage=int_stat("max_damage"),
        digestion_damage_per_tick=int_stat("digestion_damage_per_tick"),
    )


def bonuses_for_spawn(
    config: DepthScalingConfig,
    *,
    floor_depth: int,
    alignment: Alignment,
    difficulty_id: str | None = None,
) -> DepthBonuses:
    """Zero bonuses when alignment is not in the profile's apply set."""
    profile = config.profile_for(difficulty_id)
    if alignment not in profile.apply_to_alignments:
        return DepthBonuses()
    return resolve_bonuses(profile, floor_depth)
