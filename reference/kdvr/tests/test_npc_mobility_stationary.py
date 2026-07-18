"""PR4: stationary mobility — no voluntary movement; attacks and ranged OK."""

from __future__ import annotations

import random

from tcod.ecs import Registry

from src.components import (
    AI,
    AIState,
    Alignment,
    Fighter,
    Mobility,
    MobilityType,
    NPCAlignment,
    Player,
    Position,
)
from src.data.entity_loader import parse_entity_registry
from src.engine import GameEngine
from src.map_gen import GameMap, Tile, can_enter_tile
from src.message_log import MessageLog
from src.systems.abilities import coward_flee_direction
from src.systems.ai import run_monster_turns, spawn_test_npc
from src.systems.ai.explore import _ensure_explore_goal
from src.systems.combat import try_action
from src.systems.movement import entity_mobility, is_stationary, try_move
from tests.map_test_helpers import carve_floor_tile, spawn_wolf_with_abilities


def _stationary_wolf(world, x: int, y: int, *, abilities: list[str] | None = None):
    wolf = spawn_wolf_with_abilities(world, x, y, abilities or [])
    wolf.components[Mobility] = Mobility(kind=MobilityType.STATIONARY)
    return wolf


def test_loader_accepts_stationary_mobility() -> None:
    raw = {
        "schema_version": 1,
        "entities": [
            {
                "id": "turret",
                "display_name": "turret",
                "glyph": "t",
                "fg": [100, 100, 100],
                "alignment": "evil",
                "mobility": "stationary",
                "max_hp": 8,
                "evade": 0,
                "ac": 2,
                "accuracy": 0.5,
                "min_damage": 2,
                "max_damage": 3,
                "spawn": {"weight": 1, "min_depth": 1, "max_depth": 10},
            }
        ],
    }
    registry = parse_entity_registry(raw)
    assert registry.get("turret").mobility == MobilityType.STATIONARY


def test_stationary_can_occupy_floor() -> None:
    game_map = GameMap(8, 8)
    game_map.tiles[:, :] = Tile.WALL
    game_map.tiles[4, 4] = Tile.FLOOR
    assert can_enter_tile(game_map, 4, 4, MobilityType.STATIONARY)


def test_stationary_try_move_blocked() -> None:
    engine = GameEngine()
    carve_floor_tile(engine, 5, 5)
    carve_floor_tile(engine, 6, 5)
    wolf = _stationary_wolf(engine.world, 5, 5)
    assert not try_move(engine.world, engine.game_map, wolf, (1, 0))
    assert wolf.components[Position] == Position(5, 5)


def test_stationary_attacks_adjacent_player() -> None:
    engine = GameEngine()
    carve_floor_tile(engine, 5, 5)
    carve_floor_tile(engine, 6, 5)
    wolf = _stationary_wolf(engine.world, 5, 5)
    player = engine.player
    assert player is not None
    player.components[Position] = Position(6, 5)
    hp_before = player.components[Fighter].hp
    assert try_action(
        engine.world,
        engine.game_map,
        wolf,
        (1, 0),
        MessageLog(),
        rng=random.Random(0),
    )
    assert player.components[Fighter].hp < hp_before
    assert wolf.components[Position] == Position(5, 5)


def test_stationary_does_not_chase_distant_player() -> None:
    engine = GameEngine()
    carve_floor_tile(engine, 5, 5)
    carve_floor_tile(engine, 8, 5)
    wolf = _stationary_wolf(engine.world, 5, 5)
    player = engine.player
    assert player is not None
    player.components[Position] = Position(8, 5)
    state = wolf.components[AIState]
    state.last_known_primary = Position(8, 5)

    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        MessageLog(),
        rng=random.Random(0),
        player_turn_count=1,
    )
    assert wolf.components[Position] == Position(5, 5)


def test_stationary_coward_does_not_flee() -> None:
    world = Registry()
    game_map = GameMap(10, 8)
    game_map.tiles[:, :] = Tile.WALL
    game_map.tiles[4, 3:7] = Tile.FLOOR
    turret = spawn_test_npc(
        world,
        x=4,
        y=4,
        species="turret",
        alignment=Alignment.EVIL,
    )
    turret.components[Mobility] = Mobility(kind=MobilityType.STATIONARY)
    from src.components import Abilities
    from src.data.ability_parser import parse_abilities

    turret.components[Abilities] = Abilities(parsed=parse_abilities(["Coward"]))
    turret.components[Fighter] = Fighter(
        hp=2,
        max_hp=10,
        accuracy=0.5,
        evade=0,
        ac=0,
        min_damage=2,
        max_damage=3,
    )
    player = world.new_entity()
    player.components[Position] = Position(6, 4)
    player.components[Fighter] = Fighter(
        hp=30,
        max_hp=30,
        accuracy=1.0,
        evade=0,
        ac=0,
        min_damage=2,
        max_damage=3,
    )
    player.tags.add(Player)
    assert coward_flee_direction(
        turret,
        world,
        game_map,
        player,
        random.Random(0),
        alignment=Alignment.EVIL,
        blocked_tiles=frozenset(),
    ) is None


def test_stationary_skips_explore_goal() -> None:
    engine = GameEngine()
    wolf = _stationary_wolf(engine.world, 5, 5)
    state = wolf.components[AIState]
    origin = wolf.components[Position]
    goal = _ensure_explore_goal(
        state,
        engine.game_map,
        origin,
        wolf,
        random.Random(0),
    )
    assert goal == origin
    assert state.explore_goal is None


def test_is_stationary_helper() -> None:
    engine = GameEngine()
    wolf = _stationary_wolf(engine.world, 5, 5)
    assert is_stationary(wolf)
    assert entity_mobility(wolf) == MobilityType.STATIONARY
    mover = spawn_wolf_with_abilities(engine.world, 6, 6, [])
    assert not is_stationary(mover)