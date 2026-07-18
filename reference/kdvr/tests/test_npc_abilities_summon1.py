"""PR4: Summon1 entity spawn on first hostile LOS."""

from __future__ import annotations

import random

import pytest

from src.components import AbilityState, Position, SpeciesId
from src.data.entity_loader import EntityLoadError, parse_entity_registry
from src.engine import GameEngine
from src import messages
from src.spawn import spawn_from_definition
from src.data.entity_loader import load_entity_registry
from src.systems.ai import run_monster_turns
from src.systems.fov import update_fov
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_adjacent_line,
    carve_horizontal_line,
    isolate_other_ais,
    relocate_player,
    spawn_wolf_with_abilities,
)
from tests.test_npc_data_pr1 import _minimal_entity


def _rabbits(engine: GameEngine) -> list:
    return [
        entity
        for entity in engine.world.Q.all_of(components=[SpeciesId])
        if entity.components[SpeciesId].id == "rabbit"
    ]


def _adjacent_rabbit_ids(engine: GameEngine, wolf) -> set[int]:
    from src.components import Position, SpeciesId

    wpos = wolf.components[Position]
    adjacent: set[int] = set()
    for rabbit in engine.world.Q.all_of(components=[SpeciesId]):
        if rabbit.components[SpeciesId].id != "rabbit":
            continue
        rpos = rabbit.components[Position]
        if max(abs(wpos.x - rpos.x), abs(wpos.y - rpos.y)) == 1:
            adjacent.add(id(rabbit))
    return adjacent


def _summon1_wolf(engine: GameEngine):
    wolf = spawn_wolf_with_abilities(
        engine.world,
        ARENA_X,
        ARENA_Y,
        ["Summon1 rabbit"],
    )
    isolate_other_ais(engine, keep=(wolf,))
    return wolf


def test_invalid_summon_entity_id_raises() -> None:
    payload = {
        "schema_version": 1,
        "entities": [_minimal_entity(id="wolf", abilities=["Summon1 phoenix"])],
    }
    with pytest.raises(EntityLoadError, match="phoenix"):
        parse_entity_registry(payload)


def test_summon_on_first_los_spawns_adjacent_rabbit() -> None:
    engine = GameEngine()
    wolf = _summon1_wolf(engine)
    player = engine.player
    assert player is not None
    carve_adjacent_line(engine, wolf.components[Position], 2)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    update_fov(engine.game_map, ARENA_X + 3, ARENA_Y)
    before_adjacent = _adjacent_rabbit_ids(engine, wolf)
    engine.message_log = type(engine.message_log)()
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(42),
    )
    assert len(_adjacent_rabbit_ids(engine, wolf) - before_adjacent) == 1
    assert wolf.components[AbilityState].summon_consumed is True


def test_summon_consumed_skips_second_activation() -> None:
    engine = GameEngine()
    wolf = _summon1_wolf(engine)
    player = engine.player
    assert player is not None
    carve_adjacent_line(engine, wolf.components[Position], 2)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    update_fov(engine.game_map, ARENA_X + 3, ARENA_Y)
    engine.message_log = type(engine.message_log)()
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(42),
    )
    rabbits_after_first = {id(rabbit) for rabbit in _rabbits(engine)}
    assert wolf.components[AbilityState].summon_consumed is True
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(42),
    )
    assert {id(rabbit) for rabbit in _rabbits(engine)} == rabbits_after_first


def test_summon_log_when_wolf_in_player_fov() -> None:
    engine = GameEngine()
    wolf = _summon1_wolf(engine)
    player = engine.player
    assert player is not None
    carve_adjacent_line(engine, wolf.components[Position], 2)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    update_fov(engine.game_map, ARENA_X + 3, ARENA_Y)
    engine.message_log = type(engine.message_log)()
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(42),
    )
    assert messages.npc_summons_aid("The wolf") in engine.message_log.lines()


def test_summon_silent_when_wolf_outside_player_fov() -> None:
    """Summon fires when wolf sees a knight; log suppressed if player cannot see wolf.

    Setup: Summon1 wolf, open adjacent tiles, good target in wolf LOS, player far
    enough that the wolf tile is outside player FOV.
    """
    from src.systems.ai import spawn_test_npc
    from src.components import Alignment

    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(
        engine.world,
        ARENA_X,
        ARENA_Y,
        ["Summon1 rabbit"],
    )
    isolate_other_ais(engine, keep=(wolf,))
    carve_adjacent_line(engine, wolf.components[Position], 2)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    knight = spawn_test_npc(
        engine.world,
        x=ARENA_X + 3,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    isolate_other_ais(engine, keep=(wolf, knight))
    # Player in a distant corner so wolf is outside FOV (radius 10).
    relocate_player(engine, 2, 2)
    player = engine.player
    assert player is not None
    update_fov(engine.game_map, 2, 2)
    wpos = wolf.components[Position]
    assert not engine.game_map.visible[wpos.y, wpos.x]
    before = len(_rabbits(engine))
    engine.message_log = type(engine.message_log)()
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(42),
    )
    assert not any("summons aid" in line for line in engine.message_log.lines())
    assert len(_rabbits(engine)) >= before + 1
    assert wolf.components[AbilityState].summon_consumed is True