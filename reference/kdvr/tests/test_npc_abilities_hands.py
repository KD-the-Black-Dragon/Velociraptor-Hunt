"""PR3: Hands — bump closed doors open (no move); 20% break to floor."""

from __future__ import annotations

import random

import pytest

from src.components import AIState, Abilities, Alignment, Position
from src.data.ability_parser import FixedAbility, parse_abilities, parse_ability_token
from src.data.abilities import DOCUMENTED_ABILITIES, filter_known_abilities
from src.data.warnings import LoadWarnings
from src.engine import GameEngine
from src.log_categories import MessageCategory
from src.map_gen import Tile
from src.message_log import MessageLog
from src.systems.abilities import has_hands
from src.systems.ai.explore import entity_explore_can_traverse
from src.systems.ai.movement import _resolve_monster_move_direction
from src.systems.combat import try_action
from src.systems.fov import update_fov
from src.systems.movement import (
    HANDS_DOOR_BREAK_CHANCE,
    can_move_to,
    log_hands_door_break,
    log_hands_door_open,
    try_hands_closed_door,
    try_move,
)
from tests.map_test_helpers import carve_floor_tile, spawn_wolf_with_abilities


def test_parse_hands_token() -> None:
    assert parse_ability_token("Hands") == FixedAbility(ability_id="Hands")
    assert "Hands" in DOCUMENTED_ABILITIES


def test_filter_known_abilities_keeps_hands() -> None:
    kept = filter_known_abilities("kobold", ["Hands"], LoadWarnings())
    assert kept == ("Hands",)


def test_hands_can_traverse_closed_door_in_bfs() -> None:
    engine = GameEngine()
    carve_floor_tile(engine, 5, 5)
    carve_floor_tile(engine, 6, 5)
    wolf = spawn_wolf_with_abilities(engine.world, 5, 5, ["Hands"])
    engine.game_map.tiles[5, 6] = Tile.DOOR_CLOSED
    assert entity_explore_can_traverse(engine.game_map, 6, 5, wolf)


def test_hands_can_bump_closed_door_tile() -> None:
    engine = GameEngine()
    carve_floor_tile(engine, 5, 5)
    carve_floor_tile(engine, 6, 5)
    wolf = spawn_wolf_with_abilities(engine.world, 5, 5, ["Hands"])
    engine.game_map.tiles[5, 6] = Tile.DOOR_CLOSED
    assert can_move_to(engine.world, engine.game_map, wolf, Position(5, 5), (1, 0))


def test_hands_opens_door_without_moving() -> None:
    engine = GameEngine()
    carve_floor_tile(engine, 5, 5)
    carve_floor_tile(engine, 6, 5)
    wolf = spawn_wolf_with_abilities(engine.world, 5, 5, ["Hands"])
    engine.game_map.tiles[5, 6] = Tile.DOOR_CLOSED
    message_log = MessageLog()
    assert try_hands_closed_door(
        engine.world,
        engine.game_map,
        wolf,
        (1, 0),
        message_log,
        random.Random(0),
    )
    assert wolf.components[Position] == Position(5, 5)
    assert engine.game_map.tiles[5, 6] == Tile.DOOR_OPEN


def test_try_move_does_not_cross_closed_door() -> None:
    engine = GameEngine()
    carve_floor_tile(engine, 5, 5)
    carve_floor_tile(engine, 6, 5)
    wolf = spawn_wolf_with_abilities(engine.world, 5, 5, ["Hands"])
    engine.game_map.tiles[5, 6] = Tile.DOOR_CLOSED
    assert not try_move(engine.world, engine.game_map, wolf, (1, 0))
    assert wolf.components[Position] == Position(5, 5)


def test_hands_walks_through_open_door_after_bump() -> None:
    engine = GameEngine()
    carve_floor_tile(engine, 5, 5)
    carve_floor_tile(engine, 6, 5)
    carve_floor_tile(engine, 7, 5)
    wolf = spawn_wolf_with_abilities(engine.world, 5, 5, ["Hands"])
    engine.game_map.tiles[5, 6] = Tile.DOOR_OPEN
    assert try_move(engine.world, engine.game_map, wolf, (1, 0))
    assert wolf.components[Position] == Position(6, 5)


def test_without_hands_cannot_enter_closed_door() -> None:
    engine = GameEngine()
    carve_floor_tile(engine, 5, 5)
    wolf = spawn_wolf_with_abilities(engine.world, 5, 5, ["Range6"])
    engine.game_map.tiles[5, 6] = Tile.DOOR_CLOSED
    assert not has_hands(wolf)
    assert not can_move_to(engine.world, engine.game_map, wolf, Position(5, 5), (1, 0))


def test_hands_log_named_when_opener_visible() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    carve_floor_tile(engine, 10, 10)
    carve_floor_tile(engine, 11, 10)
    wolf = spawn_wolf_with_abilities(engine.world, 10, 10, ["Hands"])
    engine.game_map.tiles[10, 11] = Tile.DOOR_CLOSED
    update_fov(engine.game_map, 10, 10)
    message_log = MessageLog()
    log_hands_door_open(engine.game_map, wolf, 11, 10, message_log)
    assert message_log.lines() == ["The wolf opens the door."]


def test_hands_log_something_when_only_door_visible() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    carve_floor_tile(engine, 20, 20)
    carve_floor_tile(engine, 25, 20)
    wolf = spawn_wolf_with_abilities(engine.world, 25, 20, ["Hands"])
    door_x, door_y = 23, 20
    engine.game_map.tiles[door_y, door_x] = Tile.DOOR_CLOSED
    player.components[Position] = Position(20, 20)
    update_fov(engine.game_map, 20, 20)
    wolf_pos = wolf.components[Position]
    engine.game_map.visible[door_y, door_x] = True
    engine.game_map.visible[wolf_pos.y, wolf_pos.x] = False
    message_log = MessageLog()
    log_hands_door_open(engine.game_map, wolf, door_x, door_y, message_log)
    assert message_log.lines() == ["Something opens the door."]


def test_hands_break_log_is_caution_when_opener_visible() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    carve_floor_tile(engine, 12, 12)
    carve_floor_tile(engine, 13, 12)
    wolf = spawn_wolf_with_abilities(engine.world, 12, 12, ["Hands"])
    update_fov(engine.game_map, 12, 12)
    message_log = MessageLog()
    log_hands_door_break(engine.game_map, wolf, 13, 12, message_log)
    assert message_log.lines() == ["The wolf breaks down the door!"]
    assert message_log.entries()[0].category == MessageCategory.CAUTION


def test_hands_breaks_door_on_rng(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.systems.movement.HANDS_DOOR_BREAK_CHANCE",
        1.0,
    )
    engine = GameEngine()
    carve_floor_tile(engine, 5, 5)
    carve_floor_tile(engine, 6, 5)
    wolf = spawn_wolf_with_abilities(engine.world, 5, 5, ["Hands"])
    engine.game_map.tiles[5, 6] = Tile.DOOR_CLOSED
    message_log = MessageLog()
    assert try_hands_closed_door(
        engine.world,
        engine.game_map,
        wolf,
        (1, 0),
        message_log,
        random.Random(0),
    )
    assert wolf.components[Position] == Position(5, 5)
    assert engine.game_map.tiles[5, 6] == Tile.FLOOR


def test_hands_memory_pursuit_bumps_closed_door(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.map_test_helpers import isolate_other_ais

    monkeypatch.setattr("src.systems.movement.HANDS_DOOR_BREAK_CHANCE", 0.0)
    engine = GameEngine()
    # Horizontal corridor only — suite pollution / stray floor tiles can make
    # pathing prefer a diagonal and flake on direction == (1, 0).
    carve_floor_tile(engine, 5, 5)
    carve_floor_tile(engine, 6, 5)
    carve_floor_tile(engine, 7, 5)
    carve_floor_tile(engine, 8, 5)
    wolf = spawn_wolf_with_abilities(engine.world, 5, 5, ["Hands", "Range6"])
    isolate_other_ais(engine, keep=(wolf,))
    engine.game_map.tiles[5, 6] = Tile.DOOR_CLOSED
    player_pos = Position(8, 5)
    engine.player.components[Position] = player_pos
    state = wolf.components[AIState]
    state.last_known_primary = player_pos
    monster_pos = wolf.components[Position]

    direction, _phase = _resolve_monster_move_direction(
        wolf,
        engine.world,
        engine.game_map,
        engine.player,
        random.Random(99),
        state=state,
        alignment=Alignment.EVIL,
        blocked=frozenset(),
        player_engulfed=False,
        monster_pos=monster_pos,
    )
    assert direction == (1, 0)
    assert try_action(
        engine.world,
        engine.game_map,
        wolf,
        direction,
        engine.message_log,
        rng=random.Random(0),
    )
    assert state.door_spite_turns_left == 0
    assert engine.game_map.tiles[5, 6] == Tile.DOOR_OPEN
    assert wolf.components[Position] == Position(5, 5)


def test_try_action_hands_opens_door() -> None:
    engine = GameEngine()
    carve_floor_tile(engine, 5, 5)
    carve_floor_tile(engine, 6, 5)
    wolf = spawn_wolf_with_abilities(engine.world, 5, 5, ["Hands"])
    wolf.components[Abilities] = Abilities(parsed=parse_abilities(["Hands"]))
    engine.game_map.tiles[5, 6] = Tile.DOOR_CLOSED
    assert try_action(
        engine.world,
        engine.game_map,
        wolf,
        (1, 0),
        engine.message_log,
        rng=random.Random(0),
    )
    assert engine.game_map.tiles[5, 6] == Tile.DOOR_OPEN
    assert wolf.components[Position] == Position(5, 5)


def test_hands_break_chance_is_twenty_percent() -> None:
    assert HANDS_DOOR_BREAK_CHANCE == pytest.approx(0.20)