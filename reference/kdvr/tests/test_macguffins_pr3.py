"""PR3: macguffin step-on activation, victory modal, discovery state."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.app import App
from src.components import Macguffin, Position
from src.data.macguffin_loader import load_macguffin_registry
from src.engine import GameEngine
from src.macguffin_discovery import MacguffinDiscovery, decode_macguffin_discovery
from src.macguffin_discovery import encode_macguffin_discovery
from src.macguffin_victory_confirm import (
    MACGUFFIN_VICTORY_INVALID,
    MacguffinVictoryConfirmAction,
    MacguffinVictoryConfirmState,
    handle_macguffin_victory_confirm_event,
    victory_prompt,
)
from src.save.snapshot import apply_run_snapshot, build_run_snapshot
from src.systems.combat import try_action
from src.systems.floor_runes import try_activate_floor_rune
from src.systems.inventory import pickup_all_items_at
from src.systems.macguffins import (
    count_floor_macguffins,
    spawn_macguffin_entity,
    try_begin_macguffin_activation,
)
from tests.map_test_helpers import isolate_other_ais
from tests.rune_test_helpers import rune_placement_arena


def _key(sym: KeySym, *, mod: Modifier = Modifier.NONE) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def _press(engine: GameEngine, sym: KeySym, *, mod: Modifier = Modifier.NONE) -> None:
    engine.handle_event(_key(sym, mod=mod))


def _setup_macguffin_step_on(
    engine: GameEngine,
    *,
    mac_x: int = 20,
    mac_y: int = 5,
) -> None:
    game_map = rune_placement_arena(width=45, height=10)
    for entity in list(engine.world.Q.all_of(components=[Macguffin])):
        entity.clear()
    definition = load_macguffin_registry().get("sword_of_freedom")
    spawn_macguffin_entity(engine.world, definition, mac_x, mac_y)
    engine.game_map = game_map
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    player.components[Position] = Position(mac_x - 1, mac_y)


def _step_onto_macguffin(engine: GameEngine) -> None:
    player = engine.player
    assert player is not None
    assert try_action(
        engine.world,
        engine.game_map,
        player,
        (1, 0),
        engine.message_log,
    )
    pos = player.components[Position]
    pickup_all_items_at(engine.world, player, pos.x, pos.y, engine.message_log)
    try_activate_floor_rune(
        engine.world,
        player,
        pos.x,
        pos.y,
        engine.message_log,
        screen_flash=engine.screen_flash,
        run_stats=engine.run_stats,
    )
    try_begin_macguffin_activation(engine, player, pos.x, pos.y)


def test_try_begin_macguffin_activation_opens_modal_and_records_discovery() -> None:
    engine = GameEngine()
    _setup_macguffin_step_on(engine)
    player = engine.player
    assert player is not None
    pos = player.components[Position]

    assert try_begin_macguffin_activation(
        engine,
        player,
        pos.x + 1,
        pos.y,
    )
    assert engine.macguffin_victory_confirm.active
    assert engine.macguffin_victory_confirm.macguffin_id == "sword_of_freedom"
    assert (
        engine.macguffin_victory_confirm.display_name
        == "The Sword of Freedom"
    )
    assert engine.macguffin_discovery.active
    assert engine.macguffin_discovery.macguffin_id == "sword_of_freedom"
    assert engine.macguffin_discovery.score == 100


def test_try_begin_macguffin_activation_removes_entity() -> None:
    engine = GameEngine()
    _setup_macguffin_step_on(engine)
    player = engine.player
    assert player is not None
    pos = player.components[Position]

    assert count_floor_macguffins(engine.world) == 1
    try_begin_macguffin_activation(engine, player, pos.x + 1, pos.y)
    assert count_floor_macguffins(engine.world) == 0


def test_macguffin_victory_confirm_y_and_n_key_enforcement() -> None:
    state = MacguffinVictoryConfirmState(
        macguffin_id="sword_of_freedom",
        display_name="The Sword of Freedom",
        score=100,
    )
    assert (
        handle_macguffin_victory_confirm_event(state, _key(KeySym.Y, mod=Modifier.SHIFT))
        is MacguffinVictoryConfirmAction.CONFIRM
    )
    assert (
        handle_macguffin_victory_confirm_event(state, _key(KeySym.N))
        is MacguffinVictoryConfirmAction.CANCEL
    )


def test_macguffin_victory_confirm_rejects_invalid_keys() -> None:
    state = MacguffinVictoryConfirmState(
        macguffin_id="sword_of_freedom",
        display_name="The Sword of Freedom",
    )
    assert (
        handle_macguffin_victory_confirm_event(state, _key(KeySym.Y))
        is MacguffinVictoryConfirmAction.NONE
    )
    assert state.error_message == MACGUFFIN_VICTORY_INVALID
    assert (
        handle_macguffin_victory_confirm_event(state, _key(KeySym.N, mod=Modifier.SHIFT))
        is MacguffinVictoryConfirmAction.NONE
    )


def test_victory_prompt_includes_display_name_and_blank_line() -> None:
    prompt = victory_prompt("The Sword of Freedom")
    assert "The Sword of Freedom" in prompt
    assert "(Y/n)" in prompt
    assert "\n\n" in prompt


def test_engine_step_on_macguffin_opens_modal_without_consuming_turn() -> None:
    engine = GameEngine()
    _setup_macguffin_step_on(engine)
    turns_before = engine.player_turn_count

    _press(engine, KeySym.RIGHT)

    assert engine.macguffin_victory_confirm.active
    assert engine.macguffin_discovery.active
    assert count_floor_macguffins(engine.world) == 0
    assert engine.player_turn_count == turns_before


def test_decline_macguffin_victory_consumes_turn() -> None:
    engine = GameEngine()
    _setup_macguffin_step_on(engine)
    _press(engine, KeySym.RIGHT)
    turns_before = engine.player_turn_count

    _press(engine, KeySym.N)

    assert not engine.macguffin_victory_confirm.active
    assert engine.macguffin_discovery.active
    assert engine.player_turn_count == turns_before + 1


def test_confirm_macguffin_victory_opens_game_over() -> None:
    engine = GameEngine()
    _setup_macguffin_step_on(engine)
    _press(engine, KeySym.RIGHT)
    turns_before = engine.player_turn_count

    _press(engine, KeySym.Y, mod=Modifier.SHIFT)

    assert not engine.macguffin_victory_confirm.active
    assert engine.game_over.active
    assert engine.game_over.ending is not None
    assert engine.game_over.ending.kind == "macguffin"
    assert engine.game_over.ending.detail == "The Sword of Freedom"
    assert engine.player_turn_count == turns_before


def test_macguffin_modal_blocks_idle_command() -> None:
    engine = GameEngine()
    _setup_macguffin_step_on(engine)
    _press(engine, KeySym.RIGHT)

    assert not engine.can_issue_idle_command()


def test_ctrl_q_during_macguffin_modal_is_no_op(tmp_path) -> None:
    from pathlib import Path

    from src.save.coordinator import SaveCoordinator
    from src.save.store import SaveStore
    from tests.ui_test_helpers import make_console

    store = SaveStore(Path(tmp_path))
    app = App(save_coordinator=SaveCoordinator(store=store))
    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.engine is not None
    _setup_macguffin_step_on(app.engine)
    _press(app.engine, KeySym.RIGHT)

    app.handle_event(_key(KeySym.Q, mod=Modifier.CTRL))
    assert app.quit_confirm is None
    assert app.engine.macguffin_victory_confirm.active


def test_macguffin_discovery_encode_decode_round_trip() -> None:
    discovery = MacguffinDiscovery(
        macguffin_id="sword_of_freedom",
        display_name="The Sword of Freedom",
        score=100,
    )
    payload = encode_macguffin_discovery(discovery)
    restored = decode_macguffin_discovery(payload)
    assert restored == discovery


def test_macguffin_discovery_decode_empty() -> None:
    assert decode_macguffin_discovery({}) == MacguffinDiscovery()
    assert decode_macguffin_discovery(None) == MacguffinDiscovery()


def test_macguffin_discovery_snapshot_round_trip() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.macguffin_discovery.record(
        load_macguffin_registry().get("shield_of_justice"),
    )

    restored = GameEngine.from_run_snapshot(build_run_snapshot(engine))

    assert restored.macguffin_discovery.active
    assert restored.macguffin_discovery.macguffin_id == "shield_of_justice"
    assert restored.macguffin_discovery.display_name == "The Shield of Justice"
    assert restored.macguffin_discovery.score == 150
    assert not restored.macguffin_victory_confirm.active


def test_apply_run_snapshot_resets_modal_preserves_discovery() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.macguffin_discovery.record(
        load_macguffin_registry().get("cup_that_heals"),
    )
    engine.macguffin_victory_confirm.open(
        macguffin_id="cup_that_heals",
        display_name="The Cup that Heals",
        score=200,
    )

    snapshot = build_run_snapshot(engine)
    target = GameEngine(skip_new_game=True)
    apply_run_snapshot(target, snapshot)

    assert target.macguffin_discovery.macguffin_id == "cup_that_heals"
    assert not target.macguffin_victory_confirm.active


def test_mid_modal_snapshot_preserves_discovery_without_modal() -> None:
    engine = GameEngine()
    _setup_macguffin_step_on(engine)
    engine.player_turn_count = 9
    _step_onto_macguffin(engine)
    assert engine.macguffin_victory_confirm.active

    restored = GameEngine.from_run_snapshot(build_run_snapshot(engine))

    assert restored.player_turn_count == 9
    assert restored.macguffin_discovery.macguffin_id == "sword_of_freedom"
    assert not restored.macguffin_victory_confirm.active


def test_new_game_resets_discovery() -> None:
    engine = GameEngine()
    engine.macguffin_discovery.record(
        load_macguffin_registry().get("sword_of_freedom"),
    )
    engine.new_game(seed=1)
    assert not engine.macguffin_discovery.active


def test_descend_floor_preserves_discovery_resets_modal() -> None:
    from tests.test_dungeon_pr3 import _place_player_on_stairs

    engine = GameEngine()
    engine.macguffin_discovery.record(
        load_macguffin_registry().get("sword_of_freedom"),
    )
    engine.macguffin_victory_confirm.open(
        macguffin_id="sword_of_freedom",
        display_name="The Sword of Freedom",
        score=100,
    )
    _place_player_on_stairs(engine)
    engine.descend_floor()

    assert engine.macguffin_discovery.macguffin_id == "sword_of_freedom"
    assert not engine.macguffin_victory_confirm.active