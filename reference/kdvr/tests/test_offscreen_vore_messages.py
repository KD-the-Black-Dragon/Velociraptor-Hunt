"""Offscreen NPC vore hit message logging."""

from __future__ import annotations

import random
from unittest.mock import patch

from src.components import (
    Alignment,
    Fighter,
    Position,
    Stunned,
    VoreCapable,
    VoreNarratives,
)
from src.engine import GameEngine
from src.log_markup import parse_log_markup
from src.systems.ai import spawn_test_npc
from src.systems.fov import update_fov
from src.data.entity_loader import load_entity_registry
from src.systems.vore import format_npc_vore_line, try_resolve_npc_vore

from tests.map_test_helpers import (
    carve_adjacent_line,
    carved_hidden_line,
    first_wolf,
    isolate_other_ais,
)


def _hidden_wolf_knight_setup(engine: GameEngine):
    (hx, hy), (kx, ky) = carved_hidden_line(engine, 2)
    wolf = spawn_test_npc(
        engine.world,
        x=hx,
        y=hy,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    wolf.tags.add(VoreCapable)
    wolf.components[VoreNarratives] = VoreNarratives(types=("OV", "CV", "AV"))
    knight = spawn_test_npc(
        engine.world,
        x=kx,
        y=ky,
        species="knight",
        alignment=Alignment.GOOD,
        hp=5,
    )
    knight.components[Fighter].hp = 0
    knight.tags.add(Stunned)
    return wolf, knight


def test_offscreen_vore_hit_logs_entity_line() -> None:
    engine = GameEngine()
    wolf, knight = _hidden_wolf_knight_setup(engine)
    lines_before = len(engine.message_log.lines())
    with patch("src.systems.vore.pick_narrative_type", return_value="OV"):
        with patch("src.systems.vore.resolve_vore_hit", return_value=True):
            with patch("src.systems.vore.should_attempt_vore", return_value=True):
                assert try_resolve_npc_vore(
                    wolf,
                    engine.world,
                    engine.game_map,
                    engine.message_log,
                    random.Random(0),
                )
    new_lines = engine.message_log.lines()[lines_before:]
    assert len(new_lines) == 1
    assert new_lines[0].strip()
    # Offscreen pool is atmospheric; do not pin live phrase fragments.
    assert "swallows" not in new_lines[0].lower()


def test_offscreen_vore_miss_is_silent() -> None:
    engine = GameEngine()
    wolf, _knight = _hidden_wolf_knight_setup(engine)
    lines_before = len(engine.message_log.lines())
    with patch("src.systems.vore.resolve_vore_hit", return_value=False):
        with patch("src.systems.vore.should_attempt_vore", return_value=True):
            assert try_resolve_npc_vore(
                wolf,
                engine.world,
                engine.game_map,
                engine.message_log,
                random.Random(0),
            )
    assert len(engine.message_log.lines()) == lines_before


def test_offscreen_vore_hit_cv_logs() -> None:
    engine = GameEngine()
    wolf, _knight = _hidden_wolf_knight_setup(engine)
    lines_before = len(engine.message_log.lines())
    with patch("src.systems.vore.pick_narrative_type", return_value="CV"):
        with patch("src.systems.vore.resolve_vore_hit", return_value=True):
            with patch("src.systems.vore.should_attempt_vore", return_value=True):
                assert try_resolve_npc_vore(
                    wolf,
                    engine.world,
                    engine.game_map,
                    engine.message_log,
                    random.Random(0),
                )
    new_lines = engine.message_log.lines()[lines_before:]
    assert len(new_lines) == 1
    assert new_lines[0].strip()


def test_offscreen_vore_hit_av_logs() -> None:
    engine = GameEngine()
    wolf, _knight = _hidden_wolf_knight_setup(engine)
    lines_before = len(engine.message_log.lines())
    with patch("src.systems.vore.pick_narrative_type", return_value="AV"):
        with patch("src.systems.vore.resolve_vore_hit", return_value=True):
            with patch("src.systems.vore.should_attempt_vore", return_value=True):
                assert try_resolve_npc_vore(
                    wolf,
                    engine.world,
                    engine.game_map,
                    engine.message_log,
                    random.Random(0),
                )
    new_lines = engine.message_log.lines()[lines_before:]
    assert len(new_lines) == 1
    assert new_lines[0].strip()


def test_offscreen_vore_hit_silent_when_type_missing() -> None:
    engine = GameEngine()
    wolf, _knight = _hidden_wolf_knight_setup(engine)
    lines_before = len(engine.message_log.lines())
    with patch("src.systems.vore.pick_narrative_type", return_value="XX"):
        with patch("src.systems.vore.resolve_vore_hit", return_value=True):
            with patch("src.systems.vore.should_attempt_vore", return_value=True):
                assert try_resolve_npc_vore(
                    wolf,
                    engine.world,
                    engine.game_map,
                    engine.message_log,
                    random.Random(0),
                )
    assert len(engine.message_log.lines()) == lines_before


def _visible_wolf_knight_setup(engine: GameEngine):
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    wolf_tile, knight_tile = carve_adjacent_line(engine, player_pos, 2)
    wolf = first_wolf(engine)
    knight = spawn_test_npc(
        engine.world,
        x=knight_tile.x,
        y=knight_tile.y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=5,
    )
    knight.components[Fighter].hp = 0
    knight.tags.add(Stunned)
    wolf.components[Position] = wolf_tile
    update_fov(engine.game_map, player_pos.x, player_pos.y)
    return wolf, knight


def test_visible_vore_hit_uses_entity_lines() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf, knight = _visible_wolf_knight_setup(engine)
    lines_before = len(engine.message_log.lines())
    with patch("src.systems.vore.pick_narrative_type", return_value="OV"):
        with patch("src.systems.vore.resolve_vore_hit", return_value=True):
            with patch("src.systems.vore.should_attempt_vore", return_value=True):
                assert try_resolve_npc_vore(
                    wolf,
                    engine.world,
                    engine.game_map,
                    engine.message_log,
                    random.Random(0),
                )
    new_lines = engine.message_log.lines()[lines_before:]
    assert len(new_lines) == 1
    wolf_def = load_entity_registry().get("wolf")
    assert wolf_def.npc_vore_hit is not None
    expected = {
        parse_log_markup(format_npc_vore_line(line, wolf, knight))[0]
        for line in wolf_def.npc_vore_hit["OV"]
    }
    assert new_lines[0] in expected