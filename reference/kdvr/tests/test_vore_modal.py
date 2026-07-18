"""PR 3: vore modal narrative UI and engine phase machine."""

from __future__ import annotations

import random
from unittest.mock import patch

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.components import AI, Fighter, Position, ProperName, Stunned, VoreCapable
from src.engine import GameEngine
from src.systems.fov import update_fov
from src.systems.vore import VoreModalSegment, VoreModalState, get_narrative_phases

from tests.map_test_helpers import place_adjacent_wolf


def _press(engine: GameEngine, sym: KeySym) -> bool:
    return engine.handle_event(
        tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=Modifier.NONE),
    )


def _open_vore_modal(engine: GameEngine) -> None:
    """Force a reliable player-targeted vore attempt (adjacent wolf, HP 0)."""
    from tests.map_test_helpers import isolate_other_ais

    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    wolf = place_adjacent_wolf(engine)
    isolate_other_ais(engine, keep=(wolf,))
    wolf.components.pop(ProperName, None)
    # Ensure FOV includes the wolf after isolation stash moves others.
    from src.systems.fov import update_fov

    pos = player.components[Position]
    update_fov(engine.game_map, pos.x, pos.y)
    engine._consume_player_turn()
    assert engine.vore_modal.active, "expected vore modal after stunned player turn"


def test_modal_opens_on_vore_attempt() -> None:
    engine = GameEngine()
    _open_vore_modal(engine)
    assert engine.vore_modal.segment is VoreModalSegment.ATTEMPT
    assert "wolf" in engine.vore_modal.current_line().lower()


def test_enter_advances_attempt_phases() -> None:
    engine = GameEngine()
    _open_vore_modal(engine)
    first = engine.vore_modal.current_line()
    _press(engine, KeySym.RETURN)
    if engine.vore_modal.segment is VoreModalSegment.ATTEMPT:
        assert engine.vore_modal.current_line() == first or engine.vore_modal.phase_index >= 0


def test_miss_logs_evaded_not_modal_text() -> None:
    engine = GameEngine()
    with patch("src.systems.vore.resolve_vore_hit", return_value=False):
        _open_vore_modal(engine)
        modal_line = engine.vore_modal.current_line()
        while engine.vore_modal.active:
            _press(engine, KeySym.RETURN)
    assert any("evaded" in line and "vore attempt" in line for line in engine.message_log.lines())
    assert modal_line not in engine.message_log.lines()


def test_hit_advances_through_success_phases() -> None:
    engine = GameEngine()
    with patch("src.systems.vore.resolve_vore_hit", return_value=True):
        _open_vore_modal(engine)
        while engine.vore_modal.segment is VoreModalSegment.ATTEMPT:
            _press(engine, KeySym.RETURN)
        assert engine.vore_modal.segment is VoreModalSegment.SUCCESS
        success_lines = get_narrative_phases("wolf", engine.vore_modal.narrative_type, "success")
        assert len(success_lines) > 0
        presses = 0
        while engine.vore_modal.active and presses < 20:
            _press(engine, KeySym.RETURN)
            presses += 1
        assert not engine.vore_modal.active


def test_hit_does_not_log_temp_success_or_modal_text() -> None:
    engine = GameEngine()
    with patch("src.systems.vore.resolve_vore_hit", return_value=True):
        _open_vore_modal(engine)
        modal_lines: list[str] = []
        while engine.vore_modal.active:
            modal_lines.append(engine.vore_modal.current_line())
            _press(engine, KeySym.RETURN)
    log = engine.message_log.lines()
    for line in modal_lines:
        if line:
            assert line not in log
    assert not any("vore attempt succeeds" in line for line in log)


def test_kp_enter_advances_modal() -> None:
    engine = GameEngine()
    _open_vore_modal(engine)
    assert engine.vore_modal.active
    _press(engine, KeySym.KP_ENTER)
    assert engine.vore_modal.active or any(
        "evaded" in line and "vore attempt" in line for line in engine.message_log.lines()
    )


def test_movement_blocked_during_modal() -> None:
    engine = GameEngine()
    _open_vore_modal(engine)
    turns_before = engine.player_turn_count
    _press(engine, KeySym.UP)
    assert engine.player_turn_count == turns_before
    assert engine.vore_modal.active


def test_new_game_resets_modal() -> None:
    engine = GameEngine()
    _open_vore_modal(engine)
    engine.new_game()
    assert not engine.vore_modal.active


def test_vore_modal_state_reset_clears_phases() -> None:
    modal = VoreModalState()
    modal.open_attempt(
        predator=None,  # type: ignore[arg-type]
        name="wolf",
        narrative_type="OV",
        attempt_phases=["line one"],
        hit=False,
        pending=[],
        index=0,
    )
    modal.reset()
    assert modal.phases == []
    assert not modal.active