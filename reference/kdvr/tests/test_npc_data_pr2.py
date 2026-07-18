"""PR 2: combat range formulas and weight-based generic spawn."""

from __future__ import annotations

import random

from tcod.ecs import Registry

from src.components import AI, Alignment, DisplayName, Fighter, NPCAlignment, Position, SpeciesId
from src.data.entity_loader import load_entity_registry
from src.map_gen import GameMap, Tile, generate_dungeon
from src.spawn import spawn_floor_population, spawn_from_definition
from src.systems.combat import resolve_attack
from src.constants import PLAYER_ACCURACY, PLAYER_MAX_DAMAGE, PLAYER_MIN_DAMAGE
from tests.fight_helpers import fighter_inert, fighter_player
from tests.spawn_test_helpers import expected_spawn_count, fixed_spawn_config, valid_spawn_tile_count


def test_spawn_from_definition_uses_json_combat_stats() -> None:
    world = Registry()
    wolf = load_entity_registry().get("wolf")
    entity = spawn_from_definition(world, wolf, 10, 10)
    fighter = entity.components[Fighter]
    assert fighter.accuracy == wolf.accuracy
    assert fighter.evade == wolf.evade
    assert fighter.ac == wolf.ac
    assert fighter.min_damage == wolf.min_damage
    assert fighter.max_damage == wolf.max_damage
    assert entity.components[SpeciesId].id == "wolf"
    assert entity.components[NPCAlignment].alignment == Alignment.EVIL


class _FixedRollRng:
    """Returns a fixed value for both continuous evade rolls and int damage rolls."""

    def __init__(self, value: float) -> None:
        self._value = value

    def randint(self, _a: int, _b: int) -> int:
        return int(self._value)

    def uniform(self, _a: float, _b: float) -> float:
        return float(self._value)


def test_resolve_attack_miss_when_evade_roll_meets_accuracy() -> None:
    attacker = fighter_player()
    defender = Fighter(hp=10, max_hp=10, accuracy=10.0, evade=10.0, ac=0, min_damage=4, max_damage=4)
    # Continuous roll equals accuracy → hit_value <= 0 → miss
    hit, damage = resolve_attack(attacker, defender, _FixedRollRng(PLAYER_ACCURACY))
    assert hit is False
    assert damage == 0


def test_resolve_attack_hit_when_evade_roll_below_accuracy() -> None:
    attacker = fighter_player()
    defender = fighter_inert()
    rng = random.Random(0)
    hit, damage = resolve_attack(attacker, defender, rng)
    assert hit is True
    assert PLAYER_MIN_DAMAGE <= damage <= PLAYER_MAX_DAMAGE


def test_resolve_attack_damage_floors_at_zero() -> None:
    attacker = Fighter(hp=10, max_hp=10, accuracy=10.0, evade=0.0, ac=0, min_damage=1, max_damage=1)
    defender = Fighter(hp=10, max_hp=10, accuracy=0.0, evade=0.0, ac=5, min_damage=0, max_damage=0)
    rng = random.Random(0)
    hit, damage = resolve_attack(attacker, defender, rng)
    assert hit is True
    assert damage == 0


def test_player_misses_evade_two_defender_about_one_quarter() -> None:
    """Continuous: P(hit)=acc/E for 0<acc<E. PLAYER_ACCURACY/2 → ~25% miss."""
    player = fighter_player()
    defender = Fighter(
        hp=10,
        max_hp=10,
        accuracy=1.0,
        evade=2.0,
        ac=0,
        min_damage=1,
        max_damage=1,
    )
    rng = random.Random(99)
    misses = 0
    for _ in range(3000):
        hit, _ = resolve_attack(player, defender, rng)
        if not hit:
            misses += 1
    # E[misses] ≈ 3000 * (1 - PLAYER_ACCURACY/2) = 750 at stock acc 1.5
    assert 550 < misses < 1000


def test_continuous_evade_fractional_scales_hit_rate() -> None:
    """Fractional evade steps change hit chance smoothly (not discrete bands)."""
    attacker = Fighter(
        hp=10, max_hp=10, accuracy=2.0, evade=0.0, ac=0, min_damage=1, max_damage=1
    )
    low_e = Fighter(
        hp=50, max_hp=50, accuracy=0.0, evade=2.5, ac=0, min_damage=0, max_damage=0
    )
    high_e = Fighter(
        hp=50, max_hp=50, accuracy=0.0, evade=4.0, ac=0, min_damage=0, max_damage=0
    )
    n = 4000
    hits_low = sum(
        1 for i in range(n) if resolve_attack(attacker, low_e, random.Random(i))[0]
    )
    hits_high = sum(
        1 for i in range(n) if resolve_attack(attacker, high_e, random.Random(i))[0]
    )
    # P ≈ 2/2.5=0.80 vs 2/4=0.50
    assert hits_low > hits_high
    assert 0.70 * n < hits_low < 0.90 * n
    assert 0.40 * n < hits_high < 0.60 * n


def test_lower_accuracy_misses_more_than_player() -> None:
    """Synthetic accuracy ordering — not live entity accuracy fields."""
    low = Fighter(hp=10, max_hp=10, accuracy=0.5, evade=0.0, ac=0, min_damage=1, max_damage=1)
    high = fighter_player()
    target = Fighter(hp=50, max_hp=50, accuracy=0.0, evade=5.0, ac=0, min_damage=0, max_damage=0)
    rng_low = random.Random(1)
    rng_high = random.Random(1)
    low_hits = sum(1 for _ in range(500) if resolve_attack(low, target, rng_low)[0])
    high_hits = sum(1 for _ in range(500) if resolve_attack(high, target, rng_high)[0])
    assert low.accuracy < PLAYER_ACCURACY
    assert low_hits < high_hits


def test_resolve_attack_fixed_damage_when_min_equals_max() -> None:
    attacker = Fighter(
        hp=10,
        max_hp=10,
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=6,
        max_damage=6,
    )
    target = fighter_inert()
    hit, damage = resolve_attack(attacker, target, random.Random(99))
    assert hit is True
    assert damage == 6


def _open_spawn_map(*, with_water: bool = False) -> GameMap:
    """Large floor arena with enough tiles outside MONSTER_SPAWN_MIN_DISTANCE."""
    game_map = GameMap(60, 60)
    game_map.tiles[:, :] = Tile.FLOOR
    if with_water:
        game_map.tiles[10:20, 10:20] = Tile.DEEP_WATER
    game_map.enter_xy = (30, 30)
    return game_map


def test_spawn_floor_population_land_only_matches_effective_target() -> None:
    world = Registry()
    game_map = _open_spawn_map()
    config = fixed_spawn_config(density_pct=0.15, density_variance=0.0)
    expected = expected_spawn_count(game_map, 30, 30, floor_depth=1, config=config, rng_seed=42)
    spawned = spawn_floor_population(
        world,
        game_map,
        player_x=30,
        player_y=30,
        floor_depth=1,
        rng=random.Random(42),
        spawn_config=config,
    )
    assert len(spawned) == expected
    assert "shark" not in [e.components[DisplayName].name for e in spawned]


def test_spawn_floor_population_water_floor_uses_unified_target() -> None:
    world = Registry()
    game_map = _open_spawn_map(with_water=True)
    config = fixed_spawn_config(density_pct=0.2, density_variance=0.0)
    expected = expected_spawn_count(game_map, 30, 30, floor_depth=1, config=config, rng_seed=7)
    spawned = spawn_floor_population(
        world,
        game_map,
        player_x=30,
        player_y=30,
        floor_depth=1,
        rng=random.Random(7),
        spawn_config=config,
    )
    assert len(spawned) == expected
    for entity in spawned:
        if entity.components[DisplayName].name == "shark":
            pos = entity.components[Position]
            assert game_map.tiles[pos.y, pos.x] == Tile.DEEP_WATER


def test_good_follower_reduction_lowers_spawn_total() -> None:
    world = Registry()
    game_map = _open_spawn_map()
    config = fixed_spawn_config(density_pct=0.2, density_variance=0.0)
    baseline = expected_spawn_count(game_map, 30, 30, floor_depth=1, config=config, rng_seed=3)
    spawned = spawn_floor_population(
        world,
        game_map,
        player_x=30,
        player_y=30,
        floor_depth=1,
        rng=random.Random(3),
        spawn_config=config,
        good_follower_reduction=1,
    )
    assert len(spawned) == max(0, baseline - 1)


def test_generated_dungeon_spawns_ai_entities() -> None:
    game_map = generate_dungeon(80, 44, seed=21)
    world = Registry()
    spawned = spawn_floor_population(
        world,
        game_map,
        player_x=game_map.enter_xy[0],
        player_y=game_map.enter_xy[1],
        floor_depth=1,
        rng=random.Random(21),
    )
    assert len(spawned) == len(list(world.Q.all_of(components=[AI])))
    assert len(spawned) > 0
    enter_x, enter_y = game_map.enter_xy
    assert len(spawned) <= valid_spawn_tile_count(game_map, enter_x, enter_y)