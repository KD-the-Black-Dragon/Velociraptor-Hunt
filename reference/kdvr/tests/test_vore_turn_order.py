"""PR 4: mid-monster-phase resume and turn-order correctness."""

from __future__ import annotations

import random
from unittest.mock import patch

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.components import AI, Fighter, Position, Stunned, VoreCapable
from src.engine import GameEngine
from src.systems.ai import _sorted_monsters, run_monster_turns

from tests.map_test_helpers import (
    carve_east_of,
    carve_floor_tile,
    clear_wolf_abilities,
    ensure_wolves,
    isolate_other_ais,
    iter_wolves,
    place_wolf_at,
)
from src.systems.fov import update_fov
from src.systems.vore import VoreModalSegment


def _press(engine: GameEngine, sym: KeySym) -> bool:
    return engine.handle_event(
        tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=Modifier.NONE),
    )


def _advance_modal(engine: GameEngine) -> None:
    while engine.vore_modal.active:
        _press(engine, KeySym.RETURN)


def _stun_player(engine: GameEngine) -> None:
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)


def _sorted_wolves(engine: GameEngine) -> list[object]:
    from tests.map_test_helpers import ensure_wolves

    # F1 is rat-only; spawn wolves when the floor has none.
    ensure_wolves(engine, 2)
    wolves = [m for m in iter_wolves(engine) if Position in m.components]
    return sorted(
        wolves,
        key=lambda wolf: (
            wolf.components[Position].y,
            wolf.components[Position].x,
            id(wolf),
        ),
    )


def _move_non_wolves_away(engine: GameEngine) -> None:
    """Keep knights/rabbits out of wolf-only vore turn-order scenarios."""
    player_pos = engine.player.components[Position]
    assert player_pos is not None
    x = min(player_pos.x + 25, 78)
    y = min(player_pos.y + 15, 41)
    for entity in engine.world.Q.all_of(components=[AI, Position]):
        if VoreCapable not in entity.tags:
            entity.components[Position] = Position(x, y)
            y = min(y + 1, 42)


def _monster_index(engine: GameEngine, entity: object) -> int:
    return _sorted_monsters(engine.world).index(entity)  # type: ignore[arg-type]


def _resolve_miss_modal(engine: GameEngine) -> None:
    with patch("src.systems.vore.resolve_vore_hit", return_value=False):
        _advance_modal(engine)


def test_miss_resumes_at_next_monster_index() -> None:
    engine = GameEngine()
    engine.new_game(seed=42)
    _move_non_wolves_away(engine)
    ensure_wolves(engine, 2)
    clear_wolf_abilities(engine)
    monsters = _sorted_wolves(engine)
    _stun_player(engine)
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    carve_east_of(engine, player_pos, 5)
    monsters = _sorted_wolves(engine)
    assert len(monsters) >= 2

    for index, wolf in enumerate(monsters):
        if index == 0:
            place_wolf_at(engine, wolf, player_pos.x + 1, player_pos.y)
        elif index == 1:
            place_wolf_at(engine, wolf, player_pos.x + 3, player_pos.y)
        else:
            place_wolf_at(engine, wolf, player_pos.x + 20, player_pos.y + 20)
    opener = monsters[0]
    runner_up = monsters[1]
    isolate_other_ais(engine, keep=(opener, runner_up))
    update_fov(engine.game_map, player_pos.x, player_pos.y)

    acted: list[object] = []
    original = run_monster_turns.__globals__["try_action"]

    def _track_try_action(world, game_map, actor, direction, message_log, **kwargs):
        acted.append(actor)
        return original(world, game_map, actor, direction, message_log, **kwargs)
    with patch("src.systems.ai.visit.try_action", side_effect=_track_try_action), patch("src.systems.ai.movement.try_action", side_effect=_track_try_action):
        with patch("src.systems.vore.resolve_vore_hit", return_value=False):
            engine._consume_player_turn()
            assert engine.vore_modal.active
            assert engine.vore_modal.resume_monster_index == _monster_index(engine, opener)
            assert engine.vore_modal.predator is opener
            _resolve_miss_modal(engine)

    assert opener not in acted
    assert runner_up in acted
    assert not engine.vore_modal.active


def test_hit_skips_remaining_monsters_in_world_phase() -> None:
    engine = GameEngine()
    engine.new_game(seed=42)
    _move_non_wolves_away(engine)
    ensure_wolves(engine, 2)
    clear_wolf_abilities(engine)
    _stun_player(engine)
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    carve_east_of(engine, player_pos, 5)
    monsters = _sorted_wolves(engine)
    assert len(monsters) >= 2

    first, second = monsters[0], monsters[1]
    place_wolf_at(engine, first, player_pos.x + 1, player_pos.y)
    place_wolf_at(engine, second, player_pos.x + 3, player_pos.y)
    update_fov(engine.game_map, player_pos.x, player_pos.y)

    acted: list[object] = []

    def _track_try_action(world, game_map, actor, direction, message_log, **kwargs):
        acted.append(actor)
        from src.systems.combat import try_action as real_try_action

        return real_try_action(world, game_map, actor, direction, message_log, **kwargs)

    with patch("src.systems.ai.visit.try_action", side_effect=_track_try_action), patch("src.systems.ai.movement.try_action", side_effect=_track_try_action):
        with patch("src.systems.vore.resolve_vore_hit", return_value=True):
            engine._consume_player_turn()
            _advance_modal(engine)

    assert second not in acted
    assert not engine.vore_modal.active


def test_after_miss_complete_next_player_turn_starts_from_zero() -> None:
    engine = GameEngine()
    engine.new_game(seed=42)
    _move_non_wolves_away(engine)
    ensure_wolves(engine, 1)
    clear_wolf_abilities(engine)
    _stun_player(engine)
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    carve_east_of(engine, player_pos, 3)
    monsters = _sorted_wolves(engine)
    assert len(monsters) >= 1
    first = monsters[0]
    place_wolf_at(engine, first, player_pos.x + 1, player_pos.y)
    update_fov(engine.game_map, player_pos.x, player_pos.y)

    with patch("src.systems.vore.resolve_vore_hit", return_value=False):
        engine._consume_player_turn()
        _resolve_miss_modal(engine)

    assert not engine.vore_modal.active
    assert engine.vore_modal.pending_monsters == []

    call_log: list[int] = []

    def _fake_run_monster_turns(*args, **kwargs):
        modal = kwargs.get("modal")
        if modal is not None and modal.pending_monsters:
            call_log.append(modal.resume_monster_index)
        else:
            call_log.append(0)
        return False

    with patch("src.engine_turn.run_monster_turns", side_effect=_fake_run_monster_turns):
        engine._consume_player_turn()

    assert call_log == [0]


def test_chained_modal_after_miss_does_not_resume_further_until_resolved() -> None:
    engine = GameEngine()
    _move_non_wolves_away(engine)
    clear_wolf_abilities(engine)
    _stun_player(engine)
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    carve_east_of(engine, player_pos, 2)
    carve_floor_tile(engine, player_pos.x, player_pos.y + 1)
    ensure_wolves(engine, 2)
    clear_wolf_abilities(engine)
    monsters = _sorted_wolves(engine)
    assert len(monsters) >= 2

    first, second = monsters[0], monsters[1]
    place_wolf_at(engine, first, player_pos.x + 1, player_pos.y)
    place_wolf_at(engine, second, player_pos.x, player_pos.y + 1)
    update_fov(engine.game_map, player_pos.x, player_pos.y)

    acted: list[object] = []

    def _track_try_action(world, game_map, actor, direction, message_log, **kwargs):
        acted.append(actor)
        from src.systems.combat import try_action as real_try_action

        return real_try_action(world, game_map, actor, direction, message_log, **kwargs)

    with patch("src.systems.ai.visit.try_action", side_effect=_track_try_action), patch("src.systems.ai.movement.try_action", side_effect=_track_try_action):
        with patch("src.systems.vore.resolve_vore_hit", return_value=False):
            engine._consume_player_turn()
            assert engine.vore_modal.predator is first
            _press(engine, KeySym.RETURN)

    assert engine.vore_modal.active
    assert engine.vore_modal.predator is second
    assert first not in acted
    assert second not in acted
    assert len([line for line in engine.message_log.lines() if "evaded" in line]) == 1

    _advance_modal(engine)
    assert not engine.vore_modal.active


def test_open_attempt_stores_monster_index_for_resume() -> None:
    engine = GameEngine()
    _move_non_wolves_away(engine)
    clear_wolf_abilities(engine)
    _stun_player(engine)
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    carve_east_of(engine, player_pos, 3)
    monsters = _sorted_wolves(engine)
    for index, wolf in enumerate(monsters):
        if index == 0:
            place_wolf_at(engine, wolf, player_pos.x + 1, player_pos.y)
        else:
            place_wolf_at(engine, wolf, player_pos.x + 20, player_pos.y + 20)
    update_fov(engine.game_map, player_pos.x, player_pos.y)

    opener = monsters[0]
    engine._consume_player_turn()
    assert engine.vore_modal.active
    assert engine.vore_modal.predator is opener
    # Resume index is into the phase snapshot (pending_monsters), not a
    # re-sorted world query after earlier NPCs may have moved.
    assert engine.vore_modal.resume_monster_index == engine.vore_modal.pending_monsters.index(
        opener
    )
    assert engine.vore_modal.segment is VoreModalSegment.ATTEMPT