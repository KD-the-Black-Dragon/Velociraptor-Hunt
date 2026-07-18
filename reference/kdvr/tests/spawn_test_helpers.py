"""Isolated dungeon spawn fixtures for mechanics tests — not stock JSON counts.

When to use which helper
------------------------
- **``fixed_spawn_config`` / density helpers** — floor population *counts* and tile
  eligibility, not individual NPC combat stats.
- **``spawn_fixture_at`` / ``fixture_*`` depth scaling** — mechanics and depth-bake
  tests. Pin entity defs and difficulty schedules in the test; never assert live
  ``data/`` balance numbers.
- **``spawn_species_at``** — place a registry species (stock or injected) at fixed
  coords with explicit ``floor_depth`` / ``difficulty_id`` / optional
  ``depth_scaling``. Prefer an injected ``registry`` + fixture scaling for
  asserts; stock ids are fine only for structural checks (components present).
- **``set_engine_depth``** — set ``engine.floor_depth`` and ``engine.difficulty_id``
  for tests that exercise engine-level code paths (descent, spawn population).
- **``spawn_test_npc`` (``src.systems.ai``)** — minimal AI/combat shell with no
  species data, abilities, or depth bake. Use when alignment + Fighter is enough.
- **``digest_test_helpers.spawn_evil_from_fixture``** — digestion-focused evil
  predator with pinned digest fields; not a general depth/difficulty helper.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from tcod.ecs import Entity, Registry

from src.components import Alignment, Fighter, MobilityType, Position, SpeciesId
from src.data.depth_scaling_config import (
    DepthScalingConfig,
    DifficultyProfile,
    StatSchedule,
)
from src.data.dungeon_spawn_config import (
    DensityDefaults,
    DepthBand,
    DungeonSpawnConfig,
    compute_target_npc_count,
)
from src.data.entity_loader import parse_entity_registry
from src.data.entity_registry import EntityDefinition, EntityRegistry, SpawnConfig
from src.map_gen import GameMap
from src.spawn import (
    count_valid_spawn_tiles,
    spawn_entity_by_id,
    spawn_from_definition,
    valid_spawn_tiles,
)

if TYPE_CHECKING:
    from src.engine import GameEngine


def fixed_spawn_config(
    *,
    density_pct: float = 0.5,
    density_variance: float = 0.0,
    min_npcs: int = 0,
    max_npcs: int | None = 120,
) -> DungeonSpawnConfig:
    """Deterministic spawn config for isolated spawn mechanics tests."""
    defaults = DensityDefaults(
        density_pct=density_pct,
        density_variance=density_variance,
        min_npcs=min_npcs,
        max_npcs=max_npcs,
    )
    return DungeonSpawnConfig(
        schema_version=1,
        defaults=defaults,
        depth_bands=(
            DepthBand(
                min_depth=1,
                max_depth=1000,
                density_pct=density_pct,
                density_variance=density_variance,
                min_npcs=min_npcs,
                max_npcs=max_npcs,
            ),
        ),
    )


def valid_spawn_tile_count(
    game_map: GameMap,
    player_x: int,
    player_y: int,
) -> int:
    land, water = valid_spawn_tiles(game_map, player_x, player_y)
    return count_valid_spawn_tiles(land, water)


def effective_spawn_target(
    game_map: GameMap,
    player_x: int,
    player_y: int,
    floor_depth: int,
    config: DungeonSpawnConfig,
    rng: random.Random,
    *,
    good_follower_reduction: int = 0,
) -> int:
    valid_count = valid_spawn_tile_count(game_map, player_x, player_y)
    target = compute_target_npc_count(valid_count, floor_depth, config, rng)
    return max(0, target - good_follower_reduction)


def expected_spawn_count(
    game_map: GameMap,
    player_x: int,
    player_y: int,
    floor_depth: int,
    config: DungeonSpawnConfig,
    rng_seed: int,
    *,
    good_follower_reduction: int = 0,
) -> int:
    return effective_spawn_target(
        game_map,
        player_x,
        player_y,
        floor_depth,
        config,
        random.Random(rng_seed),
        good_follower_reduction=good_follower_reduction,
    )


# ---------------------------------------------------------------------------
# Depth scaling fixtures (not stock data/depth_scaling.json)
# ---------------------------------------------------------------------------


def fixture_stat_schedule(
    *,
    per_floor: int = 0,
    every_n_floors: int = 0,
    bank_amount: int = 1,
    start_depth: int = 1,
    unit: float = 1.0,
) -> StatSchedule:
    """Pinned dual-int schedule for tests (do not load stock JSON)."""
    return StatSchedule(
        per_floor=per_floor,
        every_n_floors=every_n_floors,
        bank_amount=bank_amount,
        start_depth=start_depth,
        unit=unit,
    )


def fixture_difficulty_profile(
    *,
    difficulty_id: str = "test",
    display_name: str = "Test",
    apply_to_alignments: frozenset[Alignment] | None = None,
    stats: dict[str, StatSchedule] | None = None,
) -> DifficultyProfile:
    return DifficultyProfile(
        id=difficulty_id,
        display_name=display_name,
        apply_to_alignments=apply_to_alignments
        if apply_to_alignments is not None
        else frozenset({Alignment.EVIL}),
        stats=stats or {},
    )


def fixture_depth_scaling_config(
    profile: DifficultyProfile | None = None,
    *,
    default_difficulty_id: str | None = None,
    extra_profiles: dict[str, DifficultyProfile] | None = None,
) -> DepthScalingConfig:
    """One or more difficulty profiles for isolated depth-bake tests."""
    primary = profile or fixture_difficulty_profile()
    difficulties: dict[str, DifficultyProfile] = {primary.id: primary}
    if extra_profiles:
        difficulties.update(extra_profiles)
    default_id = default_difficulty_id or primary.id
    if default_id not in difficulties:
        raise ValueError(
            f"default_difficulty_id {default_id!r} not in difficulties "
            f"{sorted(difficulties)}"
        )
    return DepthScalingConfig(
        schema_version=1,
        default_difficulty_id=default_id,
        difficulties=difficulties,
    )


def fixture_entity_definition(
    entity_id: str = "fixture_critter",
    *,
    display_name: str | None = None,
    alignment: Alignment = Alignment.EVIL,
    mobility: MobilityType = MobilityType.GROUND,
    max_hp: int = 10,
    evade: int = 0,
    ac: int = 1,
    accuracy: float = 0.5,
    min_damage: int = 2,
    max_damage: int = 3,
    ranged_accuracy: float = 0.0,
    ranged_min_damage: int = 0,
    ranged_max_damage: int = 0,
    digestion_damage_per_tick: int | None = 3,
    digest_time: int | None = 6,
    abilities: tuple[str, ...] = (),
    spawn_weight: int = 1,
    min_depth: int = 1,
    max_depth: int = 1000,
) -> EntityDefinition:
    """Pinned EntityDefinition — not loaded from data/entities.json."""
    return EntityDefinition(
        id=entity_id,
        display_name=display_name or entity_id.replace("_", " "),
        glyph="c",
        fg=(100, 100, 100),
        alignment=alignment,
        mobility=mobility,
        max_hp=max_hp,
        evade=evade,
        ac=ac,
        accuracy=accuracy,
        min_damage=min_damage,
        max_damage=max_damage,
        ranged_accuracy=ranged_accuracy,
        ranged_min_damage=ranged_min_damage,
        ranged_max_damage=ranged_max_damage,
        spawn=SpawnConfig(
            weight=spawn_weight,
            min_depth=min_depth,
            max_depth=max_depth,
        ),
        abilities=abilities,
        digestion_damage_per_tick=digestion_damage_per_tick,
        digest_time=digest_time,
    )


def fixture_entity_registry(
    *definitions: EntityDefinition,
) -> EntityRegistry:
    """Build a mini registry from pinned definitions."""
    if not definitions:
        definitions = (fixture_entity_definition(),)
    return EntityRegistry(schema_version=1, entities=tuple(definitions))


def fixture_entity_registry_from_payload(payload: dict[str, Any]) -> EntityRegistry:
    """Parse a minimal entities JSON-shaped dict (schema_version + entities list)."""
    return parse_entity_registry(payload)


# ---------------------------------------------------------------------------
# Spawn at depth / difficulty
# ---------------------------------------------------------------------------


def set_engine_depth(
    engine: GameEngine,
    *,
    floor_depth: int | None = None,
    difficulty_id: str | None = None,
) -> GameEngine:
    """Set run depth/difficulty on a live engine (mutates; returns engine)."""
    if floor_depth is not None:
        engine.floor_depth = floor_depth
    if difficulty_id is not None:
        from src.data.depth_scaling_config import validate_difficulty_id

        engine.difficulty_id = validate_difficulty_id(difficulty_id)
    return engine


def spawn_fixture_at(
    world: Registry,
    definition: EntityDefinition,
    x: int,
    y: int,
    *,
    floor_depth: int = 1,
    difficulty_id: str | None = "test",
    depth_scaling: DepthScalingConfig | None = None,
    roll_prefix: bool = False,
    rng: random.Random | None = None,
) -> Entity:
    """Spawn a pinned definition with optional fixture depth scaling.

    Prefer this for any test that asserts combat stats after depth bake.
    """
    scaling = depth_scaling if depth_scaling is not None else fixture_depth_scaling_config()
    return spawn_from_definition(
        world,
        definition,
        x,
        y,
        floor_depth=floor_depth,
        difficulty_id=difficulty_id,
        depth_scaling=scaling,
        roll_prefix=roll_prefix,
        rng=rng,
    )


def spawn_species_at(
    world: Registry,
    species_id: str,
    x: int,
    y: int,
    *,
    floor_depth: int = 1,
    difficulty_id: str | None = None,
    depth_scaling: DepthScalingConfig | None = None,
    registry: EntityRegistry | None = None,
    roll_prefix: bool = False,
    rng: random.Random | None = None,
) -> Entity:
    """Place one species by id at (x, y) with depth/difficulty bake.

    Pass a fixture ``registry`` and ``depth_scaling`` when asserting stats.
    Stock registry + stock scaling is OK only for structural checks (e.g.
    ``SpeciesId`` present) — do not pin live balance numbers in asserts.
    """
    if registry is not None:
        return spawn_from_definition(
            world,
            registry.get(species_id),
            x,
            y,
            floor_depth=floor_depth,
            difficulty_id=difficulty_id,
            depth_scaling=depth_scaling,
            roll_prefix=roll_prefix,
            rng=rng,
        )
    return spawn_entity_by_id(
        world,
        species_id,
        x,
        y,
        registry=None,
        floor_depth=floor_depth,
        difficulty_id=difficulty_id,
        depth_scaling=depth_scaling,
    )


def spawn_species_on_engine(
    engine: GameEngine,
    species_id: str,
    x: int,
    y: int,
    *,
    floor_depth: int | None = None,
    difficulty_id: str | None = None,
    depth_scaling: DepthScalingConfig | None = None,
    registry: EntityRegistry | None = None,
    carve: bool = True,
    roll_prefix: bool = False,
    rng: random.Random | None = None,
) -> Entity:
    """Spawn on an engine's world; defaults depth/difficulty from the engine.

    When ``carve`` is True, ensures a floor tile at (x, y) via map helpers.
    """
    depth = engine.floor_depth if floor_depth is None else floor_depth
    diff = engine.difficulty_id if difficulty_id is None else difficulty_id
    if carve:
        from tests.map_test_helpers import carve_floor_tile

        carve_floor_tile(engine, x, y)
    return spawn_species_at(
        engine.world,
        species_id,
        x,
        y,
        floor_depth=depth,
        difficulty_id=diff,
        depth_scaling=depth_scaling,
        registry=registry,
        roll_prefix=roll_prefix,
        rng=rng,
    )


def fighter_of(entity: Entity) -> Fighter:
    """Convenience for tests asserting baked combat stats."""
    return entity.components[Fighter]


def species_id_of(entity: Entity) -> str:
    sid = entity.components.get(SpeciesId)
    if sid is None:
        raise AssertionError("entity has no SpeciesId")
    return sid.id


def position_of(entity: Entity) -> Position:
    return entity.components[Position]
