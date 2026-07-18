"""PR2: good allies prioritize attacking predator engulfing the player."""

from __future__ import annotations

import random

from src.components import Alignment, Engulfed, Position
from src.engine import GameEngine
from src.map_gen import Tile
from src.systems.ai import pick_good_chase, spawn_test_npc
from src.systems.fov import update_fov
from src.systems.vore import engulf_player, release_engulfed
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_horizontal_line,
    ensure_wolf,
    ensure_wolves,
    isolate_other_ais,
)


def _engulfed_player_setup(engine: GameEngine) -> tuple[object, object, object, object]:
    """Knight west, other wolf adjacent, holding wolf east; player engulfed by holding wolf."""
    isolate_other_ais(engine)
    positions = carve_horizontal_line(engine, ARENA_X, ARENA_Y, 4)
    knight_pos, other_pos, holding_pos = positions[0], positions[1], positions[2]
    player = engine.player
    player.components[Position] = holding_pos

    # Density spawn can place 0–1 wolves; pin two for this scenario.
    wolves = ensure_wolves(engine, 2)
    holding_wolf = wolves[0]
    other_wolf = wolves[1]
    holding_wolf.components[Position] = holding_pos
    other_wolf.components[Position] = other_pos

    knight = spawn_test_npc(
        engine.world,
        x=knight_pos.x,
        y=knight_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        species_id="knight",
    )
    engulf_player(
        engine.world,
        player,
        holding_wolf,
        engine.message_log,
        narrative_type="OV",
    )
    update_fov(engine.game_map, knight_pos.x, knight_pos.y)
    return knight, holding_wolf, other_wolf, player


def test_good_prioritizes_engulfing_predator_over_closer_evil() -> None:
    engine = GameEngine()
    knight, holding_wolf, other_wolf, player = _engulfed_player_setup(engine)
    rng = random.Random(0)

    entity, pos, mode = pick_good_chase(
        knight,
        engine.world,
        engine.game_map,
        player,
        rng,
        player_engulfed=True,
    )

    assert entity is holding_wolf
    assert entity is not other_wolf
    assert pos is None
    assert mode == "attack"


def test_good_reverts_when_player_not_engulfed() -> None:
    engine = GameEngine()
    knight, holding_wolf, other_wolf, player = _engulfed_player_setup(engine)
    release_engulfed(
        engine.world,
        player,
        holding_wolf,
        engine.game_map,
        engine.message_log,
        escape_direction=None,
        rng=random.Random(0),
    )
    assert Engulfed not in player.tags
    update_fov(engine.game_map, knight.components[Position].x, knight.components[Position].y)

    entity, pos, mode = pick_good_chase(
        knight,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
        player_engulfed=False,
    )

    assert entity is other_wolf
    assert entity is not holding_wolf
    assert pos is None
    assert mode == "attack"


def test_good_ignores_predator_without_los() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    knight_pos = carve_horizontal_line(engine, ARENA_X, ARENA_Y, 1)[0]
    other_pos = Position(knight_pos.x, knight_pos.y + 2)
    holding_pos = Position(knight_pos.x + 3, knight_pos.y)
    carve_horizontal_line(engine, knight_pos.x, knight_pos.y, 4)
    for offset in range(1, 3):
        carve_horizontal_line(
            engine,
            knight_pos.x,
            knight_pos.y + offset,
            1,
        )
    carve_horizontal_line(engine, holding_pos.x, holding_pos.y, 1)
    for y in range(knight_pos.y - 1, knight_pos.y + 2):
        engine.game_map.tiles[y, knight_pos.x + 1] = Tile.WALL
        engine.game_map.tiles[y, knight_pos.x + 2] = Tile.WALL

    player = engine.player
    wolves = ensure_wolves(engine, 2)
    holding_wolf, other_wolf = wolves[0], wolves[1]
    holding_wolf.components[Position] = holding_pos
    other_wolf.components[Position] = other_pos
    player.components[Position] = holding_pos
    knight = spawn_test_npc(
        engine.world,
        x=knight_pos.x,
        y=knight_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        species_id="knight",
    )
    engulf_player(
        engine.world,
        player,
        holding_wolf,
        engine.message_log,
        narrative_type="OV",
    )
    update_fov(engine.game_map, knight_pos.x, knight_pos.y)

    from src.systems.fov import can_see

    assert not can_see(
        engine.game_map,
        knight_pos.x,
        knight_pos.y,
        holding_pos.x,
        holding_pos.y,
    )
    assert can_see(
        engine.game_map,
        knight_pos.x,
        knight_pos.y,
        other_pos.x,
        other_pos.y,
    )

    entity, pos, mode = pick_good_chase(
        knight,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
        player_engulfed=True,
    )

    assert entity is other_wolf
    assert mode == "attack"


def test_player_not_engulfed_unchanged_priority() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    positions = carve_horizontal_line(engine, ARENA_X, ARENA_Y, 3)
    knight_pos, wolf_pos, player_pos = positions
    wolf = ensure_wolf(engine)
    wolf.components[Position] = wolf_pos
    knight = spawn_test_npc(
        engine.world,
        x=knight_pos.x,
        y=knight_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        species_id="knight",
    )
    player = engine.player
    player.components[Position] = player_pos
    update_fov(engine.game_map, knight_pos.x, knight_pos.y)

    entity, pos, mode = pick_good_chase(
        knight,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
        player_engulfed=False,
    )

    assert entity is wolf
    assert mode == "attack"