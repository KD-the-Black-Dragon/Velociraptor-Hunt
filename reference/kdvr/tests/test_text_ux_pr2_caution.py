"""PR2: witnessed NPC swallow/digest logs default to caution color."""

from __future__ import annotations

import random
from unittest.mock import patch

from src.components import Engulfed, Position
from src.engine import GameEngine
from src.log_categories import MessageCategory
from src.systems.digestion import complete_npc_digestion
from src.systems.fov import entity_visible_to_player
from src.systems.vore import try_resolve_npc_vore
from tests.map_test_helpers import relocate_player
from tests.test_enhancements_3 import _adjacent_stunned_knight_setup


def test_on_screen_npc_vore_hit_is_caution() -> None:
    engine = GameEngine()
    wolf, knight = _adjacent_stunned_knight_setup(engine)
    with patch("src.systems.vore.resolve_vore_hit", return_value=True):
        with patch("src.systems.vore.should_attempt_vore", return_value=True):
            assert try_resolve_npc_vore(
                wolf,
                engine.world,
                engine.game_map,
                engine.message_log,
                random.Random(0),
            )
    assert Engulfed in knight.tags
    entries = engine.message_log.entries()
    assert entries
    assert entries[-1].category is MessageCategory.CAUTION


def test_on_screen_npc_vore_miss_is_routine() -> None:
    engine = GameEngine()
    wolf, knight = _adjacent_stunned_knight_setup(engine)
    with patch("src.systems.vore.resolve_vore_hit", return_value=False):
        with patch("src.systems.vore.should_attempt_vore", return_value=True):
            assert try_resolve_npc_vore(
                wolf,
                engine.world,
                engine.game_map,
                engine.message_log,
                random.Random(0),
            )
    assert Engulfed not in knight.tags
    entries = engine.message_log.entries()
    assert entries
    assert entries[-1].category is MessageCategory.ROUTINE


def test_offscreen_npc_vore_hit_is_routine() -> None:
    engine = GameEngine()
    wolf, knight = _adjacent_stunned_knight_setup(engine)
    relocate_player(engine, 2, 2)
    engine._update_fov()
    assert not entity_visible_to_player(engine.game_map, wolf)
    assert not entity_visible_to_player(engine.game_map, knight)

    engine.message_log = type(engine.message_log)()
    with patch("src.systems.vore.resolve_vore_hit", return_value=True):
        with patch("src.systems.vore.should_attempt_vore", return_value=True):
            assert try_resolve_npc_vore(
                wolf,
                engine.world,
                engine.game_map,
                engine.message_log,
                random.Random(0),
            )
    assert Engulfed in knight.tags
    entries = engine.message_log.entries()
    # Offscreen atmospheric line if any — never caution.
    for entry in entries:
        assert entry.category is MessageCategory.ROUTINE


def test_on_screen_npc_digest_complete_is_caution() -> None:
    engine = GameEngine()
    wolf, knight = _adjacent_stunned_knight_setup(engine)
    with patch("src.systems.vore.resolve_vore_hit", return_value=True):
        with patch("src.systems.vore.should_attempt_vore", return_value=True):
            try_resolve_npc_vore(
                wolf,
                engine.world,
                engine.game_map,
                engine.message_log,
                random.Random(0),
            )
    assert Engulfed in knight.tags
    engine.message_log = type(engine.message_log)()
    complete_npc_digestion(
        wolf,
        knight,
        engine.game_map,
        engine.message_log,
        random.Random(0),
    )
    entries = engine.message_log.entries()
    assert entries
    assert entries[-1].category is MessageCategory.CAUTION


def test_offscreen_npc_digest_complete_is_routine() -> None:
    engine = GameEngine()
    wolf, knight = _adjacent_stunned_knight_setup(engine)
    with patch("src.systems.vore.resolve_vore_hit", return_value=True):
        with patch("src.systems.vore.should_attempt_vore", return_value=True):
            try_resolve_npc_vore(
                wolf,
                engine.world,
                engine.game_map,
                engine.message_log,
                random.Random(0),
            )
    relocate_player(engine, 2, 2)
    engine._update_fov()
    assert not entity_visible_to_player(engine.game_map, wolf)
    assert not entity_visible_to_player(engine.game_map, knight)

    engine.message_log = type(engine.message_log)()
    complete_npc_digestion(
        wolf,
        knight,
        engine.game_map,
        engine.message_log,
        random.Random(0),
    )
    for entry in engine.message_log.entries():
        assert entry.category is MessageCategory.ROUTINE
