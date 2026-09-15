"""PR1: Shift+D dismiss targeting — remove good allies without a turn or defeat."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Modifier

from src import messages
from src.components import Engulfed, Fighter, Position
from src.engine import GameEngine
from src.events import fire_entity_defeated, on_entity_defeated
from src.input_handlers import DISMISS_ALLY_KEY, DROP_ITEM_KEY
from src.spawn import spawn_entity_by_id
from src.systems.dismiss import try_confirm_dismiss
from src.systems.fov import update_fov
from src.systems.item_modals import InventoryModalMode
from tests.map_test_helpers import isolate_other_ais


def _key(sym: KeySym, *, mod: int = 0) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=None, mod=mod)


def _place_npc(engine: GameEngine, entity_id: str, dx: int = 1, dy: int = 0):
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    entity = spawn_entity_by_id(engine.world, entity_id, pos.x + dx, pos.y + dy)
    assert entity is not None
    update_fov(engine.game_map, pos.x, pos.y)
    return entity


def test_dismiss_key_is_shift_d_not_plain_d() -> None:
    assert DISMISS_ALLY_KEY is KeySym.D
    assert DROP_ITEM_KEY is KeySym.D


def test_shift_d_enters_dismiss_mode_plain_d_still_drops() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=21)
    player = engine.player
    assert player is not None

    engine.handle_event(_key(DISMISS_ALLY_KEY, mod=Modifier.SHIFT))
    assert engine.dismiss_state.active is True
    assert engine.dismiss_state.cursor == player.components[Position]

    engine.dismiss_state.reset()
    engine.handle_event(_key(DROP_ITEM_KEY))
    assert engine.dismiss_state.active is False
    assert engine.inventory_modal.active is True
    assert engine.inventory_modal.mode is InventoryModalMode.DROP


def test_confirm_dismisses_good_ally_without_turn_or_defeat() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=22)
    knight = _place_npc(engine, "knight")
    player = engine.player
    assert player is not None
    pos = knight.components[Position]

    defeated: list = []

    def _hook(entity) -> None:
        defeated.append(entity)

    on_entity_defeated.append(_hook)
    try:
        turns_before = engine.player_turn_count
        defeated_before = engine.run_stats.monsters_defeated

        engine.handle_event(_key(DISMISS_ALLY_KEY, mod=Modifier.SHIFT))
        assert engine.dismiss_state.active is True

        # Cursor starts on player; move onto the knight then confirm.
        engine.handle_event(_key(KeySym.RIGHT))
        assert engine.dismiss_state.cursor == pos
        engine.handle_event(_key(KeySym.RETURN))

        assert engine.dismiss_state.active is False
        assert Fighter not in knight.components
        assert any(
            messages.dismiss_exits_dungeon("The dog knight") in line
            or "exits the dungeon." in line
            for line in engine.message_log.lines()
        )
        assert engine.player_turn_count == turns_before
        assert engine.run_stats.monsters_defeated == defeated_before
        assert defeated == []
    finally:
        on_entity_defeated.remove(_hook)


def test_invalid_target_keeps_mode_and_logs() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=23)
    wolf = _place_npc(engine, "wolf")
    assert wolf is not None

    turns_before = engine.player_turn_count
    engine.handle_event(_key(DISMISS_ALLY_KEY, mod=Modifier.SHIFT))
    engine.handle_event(_key(KeySym.RIGHT))
    engine.handle_event(_key(KeySym.RETURN))

    assert engine.dismiss_state.active is True
    assert Fighter in wolf.components
    assert messages.dismiss_invalid_target() in engine.message_log.lines()
    assert engine.player_turn_count == turns_before


def test_empty_tile_invalid() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=24)
    player = engine.player
    assert player is not None
    pos = player.components[Position]

    # Confirm on player tile (player excluded) → invalid.
    ok = try_confirm_dismiss(
        engine.world,
        engine.message_log,
        x=pos.x,
        y=pos.y,
    )
    assert ok is False
    assert messages.dismiss_invalid_target() in engine.message_log.lines()


def test_esc_cancels_without_message_or_turn() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=25)
    turns_before = engine.player_turn_count
    lines_before = list(engine.message_log.lines())

    engine.handle_event(_key(DISMISS_ALLY_KEY, mod=Modifier.SHIFT))
    assert engine.dismiss_state.active is True
    engine.handle_event(_key(KeySym.ESCAPE))

    assert engine.dismiss_state.active is False
    assert engine.player_turn_count == turns_before
    assert engine.message_log.lines() == lines_before


def test_engulfed_good_is_invalid() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=26)
    knight = _place_npc(engine, "knight")
    knight.tags.add(Engulfed)
    pos = knight.components[Position]

    ok = try_confirm_dismiss(
        engine.world,
        engine.message_log,
        x=pos.x,
        y=pos.y,
    )
    assert ok is False
    assert Fighter in knight.components
    assert messages.dismiss_invalid_target() in engine.message_log.lines()


def test_try_confirm_does_not_fire_entity_defeated() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=27)
    knight = _place_npc(engine, "knight")
    pos = knight.components[Position]
    seen: list = []

    def _hook(entity) -> None:
        seen.append(entity)

    on_entity_defeated.append(_hook)
    try:
        assert try_confirm_dismiss(
            engine.world,
            engine.message_log,
            x=pos.x,
            y=pos.y,
        )
        assert seen == []
        # Sanity: defeat hook still works for real defeats.
        fire_entity_defeated(knight)
        assert seen == [knight]
    finally:
        on_entity_defeated.remove(_hook)
