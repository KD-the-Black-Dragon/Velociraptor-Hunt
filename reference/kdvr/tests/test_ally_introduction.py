"""PR1: good ally name introductions."""

from __future__ import annotations

import random

from src.components import (
    Alignment,
    Engulfed,
    Position,
    ProperName,
    Stunned,
)
from src.data.entity_loader import load_entity_registry
from src.data.names_loader import load_names_registry
from src.engine import GameEngine
from src.log_categories import MessageCategory
from src.systems.ally_introduction import try_good_introductions
from src.systems.ai import spawn_test_npc
from src.systems.fov import update_fov
from src.systems.naming import entity_log_name
from src.systems.vore import engulf_player
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    ensure_adjacent_floor,
    isolate_other_ais,
    iter_wolves,
    relocate_player,
)


def _introduce(
    engine: GameEngine,
    *,
    seed: int = 0,
) -> None:
    update_fov(
        engine.game_map,
        engine.player.components[Position].x,
        engine.player.components[Position].y,
    )
    try_good_introductions(
        engine.world,
        engine.game_map,
        engine.player,
        engine.message_log,
        rng=random.Random(seed),
        entity_registry=load_entity_registry(),
        names_registry=load_names_registry(),
    )


def _setup_adjacent_knight(engine: GameEngine) -> object:
    isolate_other_ais(engine)
    player_pos = relocate_player(engine, ARENA_X, ARENA_Y)
    knight_pos = ensure_adjacent_floor(engine, player_pos, (1, 0))
    knight = spawn_test_npc(
        engine.world,
        x=knight_pos.x,
        y=knight_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        species_id="knight",
    )
    return knight


def test_knight_introduces_when_adjacent_and_coast_clear() -> None:
    engine = GameEngine()
    knight = _setup_adjacent_knight(engine)
    _introduce(engine, seed=0)

    proper = knight.components.get(ProperName)
    assert proper is not None
    assert proper.name in load_names_registry().pool_for("knight")
    assert any(
        proper.name in line for line in engine.message_log.lines()
    )
    intro_entries = [
        entry
        for entry in engine.message_log.entries()
        if proper.name in entry.text
    ]
    assert intro_entries
    assert intro_entries[-1].category is MessageCategory.SPEECH
    assert entity_log_name(knight) == proper.name


def test_introduction_once_per_entity() -> None:
    engine = GameEngine()
    knight = _setup_adjacent_knight(engine)
    _introduce(engine, seed=0)
    first_name = knight.components[ProperName].name
    line_count = len(engine.message_log.lines())

    _introduce(engine, seed=1)
    assert knight.components[ProperName].name == first_name
    assert len(engine.message_log.lines()) == line_count


def test_stunned_knight_does_not_introduce() -> None:
    engine = GameEngine()
    knight = _setup_adjacent_knight(engine)
    knight.tags.add(Stunned)
    _introduce(engine)

    assert knight.components.get(ProperName) is None
    assert not any("I am " in line for line in engine.message_log.lines())


def test_non_adjacent_knight_does_not_introduce() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    relocate_player(engine, ARENA_X, ARENA_Y)
    spawn_test_npc(
        engine.world,
        x=ARENA_X + 3,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
        species_id="knight",
    )
    _introduce(engine)

    assert not any("I am " in line for line in engine.message_log.lines())


def test_wolf_visible_to_player_blocks_introduction() -> None:
    engine = GameEngine()
    knight = _setup_adjacent_knight(engine)
    wolf = next(iter_wolves(engine))
    wolf_pos = ensure_adjacent_floor(engine, knight.components[Position], (1, 0))
    wolf.components[Position] = wolf_pos
    _introduce(engine)

    assert knight.components.get(ProperName) is None


def test_wolf_visible_to_knight_blocks_introduction() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player_pos = relocate_player(engine, ARENA_X, ARENA_Y)
    knight_pos = ensure_adjacent_floor(engine, player_pos, (1, 0))
    knight = spawn_test_npc(
        engine.world,
        x=knight_pos.x,
        y=knight_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        species_id="knight",
    )
    wolf = next(iter_wolves(engine))
    wolf_pos = ensure_adjacent_floor(engine, knight_pos, (0, -1))
    wolf.components[Position] = wolf_pos
    _introduce(engine)

    assert knight.components.get(ProperName) is None


def test_player_engulfed_blocks_introduction() -> None:
    engine = GameEngine()
    knight = _setup_adjacent_knight(engine)
    player = engine.player
    wolf = next(iter_wolves(engine))
    wolf_pos = ensure_adjacent_floor(engine, player.components[Position], (-1, 0))
    wolf.components[Position] = wolf_pos
    from src.systems.vore import engulf_player

    engulf_player(engine.world, player, wolf, engine.message_log, narrative_type="OV")
    _introduce(engine)

    assert knight.components.get(ProperName) is None


def test_engine_hook_introduces_on_consumed_turn() -> None:
    engine = GameEngine()
    knight = _setup_adjacent_knight(engine)
    engine._consume_player_turn()

    proper = knight.components.get(ProperName)
    assert proper is not None
    assert any(proper.name in line for line in engine.message_log.lines())


def test_introduction_hidden_when_not_in_player_fov() -> None:
    engine = GameEngine()
    knight = _setup_adjacent_knight(engine)
    update_fov(
        engine.game_map,
        engine.player.components[Position].x,
        engine.player.components[Position].y,
    )
    kpos = knight.components[Position]
    engine.game_map.visible[kpos.y, kpos.x] = False
    try_good_introductions(
        engine.world,
        engine.game_map,
        engine.player,
        engine.message_log,
        rng=random.Random(0),
        entity_registry=load_entity_registry(),
        names_registry=load_names_registry(),
    )

    assert knight.components.get(ProperName) is not None
    assert not any("I am " in line for line in engine.message_log.lines())