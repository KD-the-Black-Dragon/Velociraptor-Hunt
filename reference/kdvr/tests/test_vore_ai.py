"""PR 2: headless vore decision and hit resolution in monster AI."""

from __future__ import annotations

import random
from unittest.mock import patch

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src import messages
from src.components import AI, Fighter, Position, ProperName, Stunned, VoreCapable
from src.systems.naming import entity_log_possessive
from src.engine import GameEngine
from src.systems.ai import _sorted_monsters, run_monster_turns
from src.systems.fov import update_fov
from src.systems.vore import (
    VoreModalState,
    is_adjacent,
    resolve_vore_hit,
    should_attempt_vore,
    vore_decision_chance,
    vore_hit_chance,
)

from tests.map_test_helpers import first_wolf, place_adjacent_wolf


def _press(engine: GameEngine, sym: KeySym) -> bool:
    return engine.handle_event(
        tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=Modifier.NONE),
    )


def _advance_modal(engine: GameEngine) -> None:
    while engine.vore_modal.active:
        _press(engine, KeySym.RETURN)





def test_is_adjacent_chebyshev() -> None:
    assert is_adjacent(Position(0, 0), Position(1, 0)) is True
    assert is_adjacent(Position(0, 0), Position(1, 1)) is True
    assert is_adjacent(Position(0, 0), Position(2, 0)) is False


def test_should_attempt_vore_ineligible_above_half_hp() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 16
    place_adjacent_wolf(engine)
    wolf = first_wolf(engine)
    assert should_attempt_vore(wolf, player, engine.game_map, random.Random(0)) is False


def test_should_attempt_vore_false_when_not_adjacent() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    wolf = first_wolf(engine)
    assert should_attempt_vore(wolf, player, engine.game_map, random.Random(0)) is False


def test_should_attempt_vore_true_at_zero_hp_adjacent() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    wolf = place_adjacent_wolf(engine)
    assert vore_decision_chance(0.0) == 1.0
    assert should_attempt_vore(wolf, player, engine.game_map, random.Random(0)) is True


def test_should_attempt_vore_respects_vore_enabled() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    place_adjacent_wolf(engine)
    wolf = first_wolf(engine)
    with patch("src.systems.vore.VORE_ENABLED", False):
        assert should_attempt_vore(wolf, player, engine.game_map, random.Random(0)) is False


def test_resolve_vore_hit_always_true_at_zero_hp() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    assert vore_hit_chance(0.0) == 1.0
    assert resolve_vore_hit(player, random.Random(0)) is True


def test_resolve_vore_hit_floor_at_threshold() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 15
    threshold_chance = vore_hit_chance(0.5)
    rng = random.Random()
    rng.seed(999)
    roll = rng.random()
    expected = roll < threshold_chance
    rng.seed(999)
    assert resolve_vore_hit(player, rng) == expected


def test_sorted_monsters_deterministic_order() -> None:
    engine = GameEngine()
    first = _sorted_monsters(engine.world)
    second = _sorted_monsters(engine.world)
    assert [id(m) for m in first] == [id(m) for m in second]
    positions = [(m.components[Position].y, m.components[Position].x) for m in first]
    assert positions == sorted(positions)


def test_run_monster_turns_opens_modal_on_vore() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    place_adjacent_wolf(engine)
    modal = VoreModalState()
    opened = run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
        modal=modal,
    )
    assert opened is True
    assert modal.active


def test_run_monster_turns_vore_miss_logs_evaded_after_enter() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    wolf = place_adjacent_wolf(engine)
    with patch("src.systems.vore.resolve_vore_hit", return_value=False):
        engine._consume_player_turn()
    _advance_modal(engine)
    expected = messages.vore_attempt_evaded(entity_log_possessive(wolf))
    assert expected in engine.message_log.lines()


def test_vore_miss_logs_named_predator_without_article() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    wolf = place_adjacent_wolf(engine)
    wolf.components[ProperName] = ProperName(name="Fang")
    with patch("src.systems.vore.resolve_vore_hit", return_value=False):
        engine._consume_player_turn()
    _advance_modal(engine)
    expected = "You evaded Fang's vore attempt."
    assert expected in engine.message_log.lines()
    assert "the Fang" not in " ".join(engine.message_log.lines())


def test_run_monster_turns_vore_hit_no_log_until_resolved() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    place_adjacent_wolf(engine)
    with patch("src.systems.vore.resolve_vore_hit", return_value=True):
        engine._consume_player_turn()
    assert engine.vore_modal.active
    assert not any("vore attempt succeeds" in line for line in engine.message_log.lines())
    _advance_modal(engine)
    assert not engine.vore_modal.active


def test_adjacent_zero_hp_prefers_vore_over_bump() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    place_adjacent_wolf(engine)
    engine._consume_player_turn()
    assert player.components[Fighter].hp == 0
    assert engine.vore_modal.active


def test_vore_event_hook_fires_on_modal_resolve() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    place_adjacent_wolf(engine)
    fired: list[bool] = []

    def _hook(predator, prey, hit: bool) -> None:
        fired.append(hit)

    from src.events import on_vore_attempt

    on_vore_attempt.append(_hook)
    try:
        with patch("src.systems.vore.resolve_vore_hit", return_value=False):
            engine._consume_player_turn()
        assert len(fired) == 0
        _advance_modal(engine)
        assert len(fired) == 1
        assert fired[0] is False
    finally:
        on_vore_attempt.remove(_hook)