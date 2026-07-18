"""Offscreen NPC digestion complete message logging."""

from __future__ import annotations

import random

from src.components import (
    Alignment,
    DigestionStrikes,
    Fighter,
    Position,
    Predator,
    Stunned,
)
from src.engine import GameEngine
from src.spawn import spawn_entity_by_id
from src.systems.ai import spawn_test_npc
from src.systems.digestion import complete_npc_digestion
from src.systems.fov import update_fov
from src.systems.vore import engulf_npc

from tests.map_test_helpers import (
    carve_adjacent_line,
    carved_hidden_line,
    first_wolf,
    isolate_other_ais,
)


def _hidden_digestion_setup(engine: GameEngine, *, narrative_type: str = "OV"):
    hx, hy = carved_hidden_line(engine, 1)[0]
    wolf = spawn_entity_by_id(engine.world, "wolf", hx, hy)
    knight = spawn_test_npc(
        engine.world,
        x=hx,
        y=hy,
        species="knight",
        alignment=Alignment.GOOD,
        hp=5,
    )
    knight.components[Fighter].hp = 0
    knight.tags.add(Stunned)
    knight.components[DigestionStrikes] = DigestionStrikes(count=3)
    engulf_npc(engine.world, knight, wolf, narrative_type=narrative_type)
    return wolf, knight


def test_offscreen_digest_logs_entity_line() -> None:
    engine = GameEngine()
    wolf, knight = _hidden_digestion_setup(engine)
    lines_before = len(engine.message_log.lines())
    complete_npc_digestion(
        wolf,
        knight,
        engine.game_map,
        engine.message_log,
        random.Random(0),
    )
    new_lines = engine.message_log.lines()[lines_before:]
    assert len(new_lines) == 1
    assert new_lines[0].strip()
    # Do not pin live offscreen_digest phrase fragments.


def test_offscreen_digest_cv_logs() -> None:
    engine = GameEngine()
    wolf, knight = _hidden_digestion_setup(engine, narrative_type="CV")
    lines_before = len(engine.message_log.lines())
    complete_npc_digestion(
        wolf,
        knight,
        engine.game_map,
        engine.message_log,
        random.Random(0),
    )
    new_lines = engine.message_log.lines()[lines_before:]
    assert len(new_lines) == 1
    assert new_lines[0].strip()


def test_offscreen_digest_av_logs() -> None:
    engine = GameEngine()
    wolf, knight = _hidden_digestion_setup(engine, narrative_type="AV")
    lines_before = len(engine.message_log.lines())
    complete_npc_digestion(
        wolf,
        knight,
        engine.game_map,
        engine.message_log,
        random.Random(0),
    )
    new_lines = engine.message_log.lines()[lines_before:]
    assert len(new_lines) == 1
    assert new_lines[0].strip()


def test_offscreen_digest_silent_when_type_missing() -> None:
    engine = GameEngine()
    wolf, knight = _hidden_digestion_setup(engine, narrative_type="XX")
    lines_before = len(engine.message_log.lines())
    complete_npc_digestion(
        wolf,
        knight,
        engine.game_map,
        engine.message_log,
        random.Random(0),
    )
    assert len(engine.message_log.lines()) == lines_before


def test_visible_digest_uses_on_screen_pool() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    wolf_tile = carve_adjacent_line(engine, player_pos, 1)[0]
    wolf = first_wolf(engine)
    wolf.components[Position] = wolf_tile
    knight = spawn_test_npc(
        engine.world,
        x=wolf_tile.x,
        y=wolf_tile.y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=5,
    )
    knight.components[Fighter].hp = 0
    knight.tags.add(Stunned)
    knight.components[DigestionStrikes] = DigestionStrikes(count=3)
    engulf_npc(engine.world, knight, wolf, narrative_type="OV")
    update_fov(engine.game_map, player_pos.x, player_pos.y)
    lines_before = len(engine.message_log.lines())
    complete_npc_digestion(
        wolf,
        knight,
        engine.game_map,
        engine.message_log,
        random.Random(0),
    )
    new_lines = engine.message_log.lines()[lines_before:]
    assert len(new_lines) == 1
    assert new_lines[0].strip()