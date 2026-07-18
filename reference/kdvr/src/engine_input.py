"""Input handling for GameEngine: events, modals, gameplay keys, debug toggles.

PR6 extract + PR7 cleanup (public names; EngineEventResult lives here).
Call via ``GameEngine`` methods so existing patches/tests keep working.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod.event
from tcod.event import KeySym, Modifier

from src import messages
from src.components import BlocksMovement, Engulfed, Fighter, Position, Stunned
from src.debug.session_log import session_log
from src.input_handlers import (
    AUTOEXPLORE_KEY,
    COME_HERE_KEY,
    CLOSE_DOOR_KEY,
    DESCEND_KEY,
    DIRECTION_KEYS,
    is_ctrl_direction,
    DROP_ITEM_KEY,
    EVOKE_WAND_KEY,
    EXAMINE_KEY,
    THROW_PICK_KEY,
    THROW_QUICK_KEY,
    INSPECT_INVENTORY_KEY,
    INVENTORY_KEYS,
    MODAL_ADVANCE_KEYS,
    QUAFF_POTION_KEY,
    REST_UNTIL_KEY,
    WAIT_KEYS,
    WEAR_ARMOR_KEY,
    WIELD_WEAPON_KEY,
)
from src.map_gen import Tile
from src.message_log import MessageCategory
from src.macguffin_victory_confirm import (
    MacguffinVictoryConfirmAction,
    handle_macguffin_victory_confirm_event,
)
from src.systems.come_here import ComeHereResult, try_come_here_shout
from src.systems.combat import heal, sync_stunned_state, try_action, try_force_attack
from src.systems.examine import description_for_tile, move_examine_cursor
from src.systems.floor_runes import try_activate_floor_rune
from src.systems.inventory import (
    begin_manual_pickup,
    floor_items_at,
    handle_ground_pickup_modal_letter,
    pickup_all_items_at,
)
from src.systems.item_modals import (
    InventoryModalMode,
    begin_drop,
    begin_evoke,
    begin_inspect,
    begin_quick_throw,
    begin_throw_pick,
    begin_quaff,
    begin_wear,
    begin_wield,
    handle_evoke_target_modal_event,
    handle_throw_target_modal_event,
    handle_inventory_modal_escape,
    handle_inventory_modal_letter,
)
from src.systems.macguffins import try_begin_macguffin_activation
from src.systems.vore import debug_weaken_all_monsters, try_struggle
from src.ui.help_overlay import handle_help_overlay_event
from src.ui.log_overlay import (
    build_overlay_display_lines,
    handle_log_overlay_event,
    overlay_viewport_lines,
)

from enum import Enum, auto

if TYPE_CHECKING:
    from src.engine import GameEngine


class EngineEventResult(Enum):
    """Outcome of engine input handling for the app shell."""

    CONTINUE = auto()
    RECAP_DISMISSED = auto()

def pack_blocked_while_engulfed(engine: GameEngine) -> bool:
    if engine.player is not None and Engulfed in engine.player.tags:
        engine.message_log.add(
            messages.engulfed_pack_blocked(),
            category=MessageCategory.DANGER,
        )
        return True
    return False

def player_on_stairs(engine: GameEngine) -> bool:
    if engine.player is None:
        return False
    pos = engine.player.components[Position]
    if not engine.game_map.in_bounds(pos.x, pos.y):
        return False
    return engine.game_map.tiles[pos.y, pos.x] == Tile.STAIRS_DOWN

def try_descend(engine: GameEngine) -> bool:
    """
    Handle Shift+`.` (`>`). Return True when a turn was consumed.
    """
    if engine.player is None:
        return False

    if Engulfed in engine.player.tags:
        engine.message_log.add(
            messages.going_deeper_wont_help(),
            category=MessageCategory.DANGER,
        )
        return False

    if not engine._player_on_stairs():
        engine.message_log.add(messages.no_stairs_here())
        return False

    engine.descend_floor()
    return True

def toggle_debug_omniscient_vision(engine: GameEngine) -> None:
    engine._debug_omniscient_vision = not engine._debug_omniscient_vision
    engine._update_fov()
    if engine._debug_omniscient_vision:
        engine.message_log.add(messages.debug_omniscient_vision_enabled())
    else:
        engine.message_log.add(messages.debug_omniscient_vision_disabled())

def handle_inventory_modal_event(engine: GameEngine, event: tcod.event.Event) -> EngineEventResult:
    if not isinstance(event, tcod.event.KeyDown):
        return EngineEventResult.CONTINUE
    if engine.inventory_modal.mode == InventoryModalMode.EVOKE_TARGET:
        if engine.player is not None and handle_evoke_target_modal_event(
            event,
            engine.player,
            engine.inventory_modal,
            engine.world,
            engine.game_map,
            engine.message_log,
            rng=engine.rng,
            run_stats=engine.run_stats,
        ):
            engine._consume_player_turn()
        return EngineEventResult.CONTINUE
    if engine.inventory_modal.mode == InventoryModalMode.THROW_TARGET:
        if engine.player is not None and handle_throw_target_modal_event(
            event,
            engine.player,
            engine.inventory_modal,
            engine.world,
            engine.game_map,
            engine.message_log,
            rng=engine.rng,
            run_stats=engine.run_stats,
        ):
            engine._consume_player_turn()
        return EngineEventResult.CONTINUE
    if engine.inventory_modal.mode == InventoryModalMode.BLINK_TARGET:
        from src.systems.item_modals import handle_blink_target_modal_event

        if engine.player is not None and handle_blink_target_modal_event(
            event,
            engine.player,
            engine.inventory_modal,
            engine.world,
            engine.game_map,
            engine.message_log,
        ):
            engine._update_fov()
            engine._consume_player_turn()
        return EngineEventResult.CONTINUE
    if event.sym == KeySym.ESCAPE:
        handle_inventory_modal_escape(engine.inventory_modal)
        return EngineEventResult.CONTINUE
    if event.sym in INVENTORY_KEYS and engine.player is not None:
        if handle_inventory_modal_letter(
            engine.player,
            INVENTORY_KEYS[event.sym],
            engine.inventory_modal,
            engine.message_log,
            engine.world,
            game_map=engine.game_map,
            floor_depth=engine.floor_depth,
            difficulty_id=engine.difficulty_id,
            rng=engine.rng,
        ):
            engine._consume_player_turn()
    return EngineEventResult.CONTINUE

def handle_ground_pickup_modal_event(engine: GameEngine, event: tcod.event.Event) -> EngineEventResult:
    if not isinstance(event, tcod.event.KeyDown):
        return EngineEventResult.CONTINUE
    if event.sym == KeySym.ESCAPE:
        engine.ground_pickup_modal.reset()
        return EngineEventResult.CONTINUE
    if event.sym in INVENTORY_KEYS and engine.player is not None:
        handle_ground_pickup_modal_letter(
            engine.world,
            engine.player,
            INVENTORY_KEYS[event.sym],
            engine.message_log,
            engine.ground_pickup_modal,
        )
    return EngineEventResult.CONTINUE

def handle_examine_description_event(engine: GameEngine, event: tcod.event.Event) -> EngineEventResult:
    if isinstance(event, tcod.event.KeyDown) and event.sym == KeySym.ESCAPE:
        engine.examine_state.showing_description = False
        engine.examine_state.description_text = ""
    return EngineEventResult.CONTINUE

def handle_examine_cursor_event(engine: GameEngine, event: tcod.event.Event) -> EngineEventResult:
    if not isinstance(event, tcod.event.KeyDown):
        return EngineEventResult.CONTINUE
    if event.sym == KeySym.ESCAPE:
        engine.examine_state.reset()
        return EngineEventResult.CONTINUE
    if event.sym in DIRECTION_KEYS:
        engine.examine_state.cursor = move_examine_cursor(
            engine.examine_state.cursor,
            DIRECTION_KEYS[event.sym],
            engine.game_map,
        )
        return EngineEventResult.CONTINUE
    if event.sym in MODAL_ADVANCE_KEYS:
        cursor = engine.examine_state.cursor
        engine.examine_state.description_text = description_for_tile(
            engine.world,
            cursor.x,
            cursor.y,
        )
        engine.examine_state.showing_description = True
    return EngineEventResult.CONTINUE

def handle_gameplay_event(engine: GameEngine, event: tcod.event.Event) -> EngineEventResult:
    match event:
        case tcod.event.KeyDown(sym=KeySym.R):
            engine.new_game(log_session_milestones=False)
            session_log.log("Dungeon regenerated")
            engine.message_log.add(messages.dungeon_regenerated())
        case tcod.event.KeyDown(sym=sym, mod=mod) if (
            sym == DESCEND_KEY and mod & Modifier.SHIFT
        ):
            if engine._try_descend():
                engine._consume_player_turn()
        case tcod.event.KeyDown(sym=KeySym.S):
            engine._toggle_stunned_debug()
        case tcod.event.KeyDown(sym=KeySym.F2):
            debug_weaken_all_monsters(engine.world, engine.message_log)
        case tcod.event.KeyDown(sym=KeySym.F3):
            engine._toggle_water_testing_mode()
        case tcod.event.KeyDown(sym=KeySym.F4):
            engine._cycle_layout_archetype_force()
        case tcod.event.KeyDown(sym=KeySym.F5):
            engine._toggle_debug_omniscient_vision()
        case tcod.event.KeyDown(sym=KeySym.F6):
            from src.debug.force_crash import trigger_force_crash

            trigger_force_crash()
        case tcod.event.KeyDown(sym=KeySym.COMMA):
            if engine.player is not None and not engine._pack_blocked_while_engulfed():
                begin_manual_pickup(
                    engine.world,
                    engine.player,
                    engine.message_log,
                    engine.ground_pickup_modal,
                )
        case tcod.event.KeyDown(sym=sym) if sym == INSPECT_INVENTORY_KEY:
            if engine.player is not None and not engine._pack_blocked_while_engulfed():
                begin_inspect(engine.player, engine.inventory_modal, engine.message_log)
        case tcod.event.KeyDown(sym=sym) if sym == DROP_ITEM_KEY:
            if engine.player is not None and not engine._pack_blocked_while_engulfed():
                begin_drop(engine.player, engine.inventory_modal, engine.message_log)
        case tcod.event.KeyDown(sym=sym, mod=mod) if (
            sym == WIELD_WEAPON_KEY and not (mod & Modifier.SHIFT)
        ):
            if engine.player is not None and not engine._pack_blocked_while_engulfed():
                begin_wield(engine.player, engine.inventory_modal, engine.message_log)
        case tcod.event.KeyDown(sym=sym, mod=mod) if (
            sym == WEAR_ARMOR_KEY and (mod & Modifier.SHIFT)
        ):
            if engine.player is not None and not engine._pack_blocked_while_engulfed():
                begin_wear(engine.player, engine.inventory_modal, engine.message_log)
        case tcod.event.KeyDown(sym=sym) if sym == QUAFF_POTION_KEY:
            if engine.player is not None and not engine._pack_blocked_while_engulfed():
                begin_quaff(engine.player, engine.inventory_modal, engine.message_log)
        case tcod.event.KeyDown(sym=sym) if sym == EVOKE_WAND_KEY:
            if engine.player is not None and not engine._pack_blocked_while_engulfed():
                begin_evoke(engine.player, engine.inventory_modal, engine.message_log)
        case tcod.event.KeyDown(sym=sym, mod=mod) if (
            sym == THROW_QUICK_KEY and not (mod & Modifier.SHIFT)
        ):
            if engine.player is not None and not engine._pack_blocked_while_engulfed():
                begin_quick_throw(
                    engine.player,
                    engine.inventory_modal,
                    engine.message_log,
                    engine.world,
                    game_map=engine.game_map,
                )
        case tcod.event.KeyDown(sym=sym, mod=mod) if (
            sym == THROW_PICK_KEY and (mod & Modifier.SHIFT)
        ):
            if engine.player is not None and not engine._pack_blocked_while_engulfed():
                begin_throw_pick(
                    engine.player,
                    engine.inventory_modal,
                    engine.message_log,
                )
        case tcod.event.KeyDown(sym=sym) if sym == EXAMINE_KEY:
            if engine.player is not None:
                if Engulfed in engine.player.tags:
                    engine.message_log.add(
                        messages.examine_engulfed_cant_see(),
                        category=MessageCategory.DANGER,
                    )
                else:
                    engine.examine_state.enter(engine.player.components[Position])
        case tcod.event.KeyDown(sym=sym) if sym == CLOSE_DOOR_KEY:
            if engine.player is not None:
                if Engulfed in engine.player.tags:
                    pass
                elif Stunned in engine.player.tags:
                    engine.message_log.add(
                        messages.stunned_too_tired_to_move(),
                        category=MessageCategory.DANGER,
                    )
                else:
                    engine.close_door_pending = True
                    engine.message_log.add(messages.close_door_choose_direction())
        case tcod.event.KeyDown(sym=sym) if sym == AUTOEXPLORE_KEY:
            if engine.player is not None:
                engine.close_door_pending = False
                engine.begin_autoexplore()
        case tcod.event.KeyDown(sym=sym) if sym == REST_UNTIL_KEY:
            if engine.player is not None:
                engine.close_door_pending = False
                engine.begin_rest()
        case tcod.event.KeyDown(sym=sym) if sym == COME_HERE_KEY:
            if engine.player is not None:
                engine.close_door_pending = False
                result, engine.last_come_here_turn = try_come_here_shout(
                    engine.world,
                    engine.game_map,
                    engine.player,
                    engine.message_log,
                    player_turn_count=engine.player_turn_count,
                    last_come_here_turn=engine.last_come_here_turn,
                )
                if result in (
                    ComeHereResult.SHOUTED,
                    ComeHereResult.ENGULFED_FIZZLE,
                ):
                    engine._consume_player_turn()
        case tcod.event.KeyDown(sym=sym) if sym in WAIT_KEYS:
            if engine.player is not None:
                engine.close_door_pending = False
                if Stunned in engine.player.tags:
                    engine.message_log.add(
                        messages.stunned_too_tired_to_move(),
                        category=MessageCategory.DANGER,
                    )
                engine._consume_player_turn()
        case tcod.event.KeyDown() if (
            engine.player is not None
            and (direction := is_ctrl_direction(event)) is not None
        ):
            engine.close_door_pending = False
            if Engulfed in engine.player.tags:
                if Stunned in engine.player.tags:
                    engine.message_log.add(
                        messages.stunned_too_tired_to_move(),
                        category=MessageCategory.DANGER,
                    )
                else:
                    try_struggle(
                        engine.world,
                        engine.game_map,
                        engine.player,
                        direction,
                        engine.message_log,
                        engine.rng,
                        run_stats=engine.run_stats,
                    )
                engine._consume_player_turn()
            elif try_force_attack(
                engine.world,
                engine.game_map,
                engine.player,
                direction,
                engine.message_log,
                rng=engine.rng,
                run_stats=engine.run_stats,
            ):
                engine._consume_player_turn()
        case tcod.event.KeyDown(sym=sym) if sym in DIRECTION_KEYS:
            if engine.player is not None:
                if engine.close_door_pending:
                    engine.close_door_pending = False
                    if engine._try_close_door(DIRECTION_KEYS[sym]):
                        engine._consume_player_turn()
                    return EngineEventResult.CONTINUE
                if Engulfed in engine.player.tags:
                    if Stunned in engine.player.tags:
                        engine.message_log.add(
                        messages.stunned_too_tired_to_move(),
                        category=MessageCategory.DANGER,
                    )
                    else:
                        try_struggle(
                            engine.world,
                            engine.game_map,
                            engine.player,
                            DIRECTION_KEYS[sym],
                            engine.message_log,
                            engine.rng,
                            run_stats=engine.run_stats,
                        )
                    engine._consume_player_turn()
                elif Stunned in engine.player.tags:
                    engine.message_log.add(
                        messages.stunned_too_tired_to_move(),
                        category=MessageCategory.DANGER,
                    )
                    engine._consume_player_turn()
                elif try_action(
                    engine.world,
                    engine.game_map,
                    engine.player,
                    DIRECTION_KEYS[sym],
                    engine.message_log,
                    rng=engine.rng,
                    skip_turn_entities=engine.skipped_this_phase,
                    run_stats=engine.run_stats,
                ):
                    pos = engine.player.components[Position]
                    pickup_all_items_at(
                        engine.world,
                        engine.player,
                        pos.x,
                        pos.y,
                        engine.message_log,
                    )
                    try_activate_floor_rune(
                        engine.world,
                        engine.player,
                        pos.x,
                        pos.y,
                        engine.message_log,
                        screen_flash=engine.screen_flash,
                        run_stats=engine.run_stats,
                        rune_pieces_multiplier=engine.difficulty_profile().rune_pieces_multiplier,
                    )
                    if try_begin_macguffin_activation(
                        engine,
                        engine.player,
                        pos.x,
                        pos.y,
                    ):
                        pass
                    else:
                        engine._consume_player_turn()
    return EngineEventResult.CONTINUE

def modal_blocks_quit(engine: GameEngine) -> bool:
    """True while a modal requires Enter-only input (no quit-to-menu)."""
    return (
        engine.vore_modal.active
        or engine.digestion_modal.active
        or engine.game_over.active
        or engine.ground_pickup_modal.active
        or engine.inventory_modal.active
        or engine.macguffin_victory_confirm.active
        or engine.arena_victory_active
    )

def log_overlay_metrics(engine: GameEngine) -> tuple[int, int]:
    viewport_lines = overlay_viewport_lines(engine.ui_layout)
    line_count = len(
        build_overlay_display_lines(
            engine.message_log.entries(),
            layout=engine.ui_layout,
        )
    )
    return line_count, viewport_lines

def handle_meta_overlay_events(engine: GameEngine, event: tcod.event.Event) -> bool:
    line_count, viewport_lines = engine._log_overlay_metrics()
    if handle_help_overlay_event(
        engine.help_overlay,
        engine.log_overlay,
        event,
        log_line_count=line_count,
        log_viewport_lines=viewport_lines,
    ):
        return True
    return handle_log_overlay_event(
        engine.log_overlay,
        event,
        line_count=line_count,
        viewport_lines=viewport_lines,
    )

def handle_event(engine: GameEngine, event: tcod.event.Event) -> EngineEventResult:
    """Process gameplay input. Ctrl+Q is handled by the app shell."""
    if isinstance(event, tcod.event.Quit):
        return EngineEventResult.CONTINUE

    if engine._handle_meta_overlay_events(event):
        return EngineEventResult.CONTINUE

    if engine.arena_victory_active:
        return EngineEventResult.CONTINUE

    if engine.game_over.active:
        if (
            isinstance(event, tcod.event.KeyDown)
            and event.sym in MODAL_ADVANCE_KEYS
        ):
            return EngineEventResult.RECAP_DISMISSED
        return EngineEventResult.CONTINUE

    if engine.digestion_modal.active:
        if (
            isinstance(event, tcod.event.KeyDown)
            and event.sym in MODAL_ADVANCE_KEYS
        ):
            engine._advance_digestion_modal()
        return EngineEventResult.CONTINUE

    if engine.vore_modal.active:
        if (
            isinstance(event, tcod.event.KeyDown)
            and event.sym in MODAL_ADVANCE_KEYS
        ):
            engine._advance_vore_modal()
        return EngineEventResult.CONTINUE

    if engine.inventory_modal.active:
        return engine._handle_inventory_modal_event(event)

    if engine.ground_pickup_modal.active:
        return engine._handle_ground_pickup_modal_event(event)

    if engine.macguffin_victory_confirm.active:
        action = handle_macguffin_victory_confirm_event(
            engine.macguffin_victory_confirm,
            event,
        )
        if action is MacguffinVictoryConfirmAction.CONFIRM:
            engine._complete_macguffin_victory()
        elif action is MacguffinVictoryConfirmAction.CANCEL:
            engine.macguffin_victory_confirm.reset()
            engine._consume_player_turn()
        return EngineEventResult.CONTINUE

    if engine.examine_state.showing_description:
        return engine._handle_examine_description_event(event)

    if engine.examine_state.active:
        return engine._handle_examine_cursor_event(event)

    return engine._handle_gameplay_event(event)

def toggle_water_testing_mode(engine: GameEngine) -> None:
    """Debug helper: heavier water on the next generated floor (press R to regen)."""
    engine.water_testing_mode = not engine.water_testing_mode
    if engine.water_testing_mode:
        engine.message_log.add(messages.water_testing_mode_enabled())
    else:
        engine.message_log.add(messages.water_testing_mode_disabled())
    engine._invalidate_floor_prefetch()

def try_close_door(engine: GameEngine, direction: tuple[int, int]) -> bool:
    """Close an adjacent open door. Return True when a turn was consumed."""
    if engine.player is None:
        return False
    if Engulfed in engine.player.tags or Stunned in engine.player.tags:
        if Stunned in engine.player.tags:
            engine.message_log.add(
                messages.stunned_too_tired_to_move(),
                category=MessageCategory.DANGER,
            )
        return False

    pos = engine.player.components[Position]
    dx, dy = direction
    target_x = pos.x + dx
    target_y = pos.y + dy
    if not engine.game_map.in_bounds(target_x, target_y):
        engine.message_log.add(messages.no_open_door_there())
        return False
    if engine.game_map.tiles[target_y, target_x] != Tile.DOOR_OPEN:
        engine.message_log.add(messages.no_open_door_there())
        return False
    if engine._door_tile_blocked(target_x, target_y):
        engine.message_log.add(messages.something_in_the_way())
        return False
    engine.game_map.tiles[target_y, target_x] = Tile.DOOR_CLOSED
    engine.message_log.add(messages.door_closed())
    return True

def door_tile_blocked(engine: GameEngine, x: int, y: int) -> bool:
    """Return True when an entity or floor item occupies the door tile."""
    target = Position(x, y)
    for entity in engine.world.Q.all_of(tags=[target, BlocksMovement]):
        return True
    return bool(floor_items_at(engine.world, x, y))

def cycle_layout_archetype_force(engine: GameEngine) -> None:
    """Debug helper: cycle forced layout archetype (press R to regen)."""
    match engine.layout_archetype_force:
        case None:
            engine.layout_archetype_force = "boxy"
            engine.message_log.add(messages.layout_archetype_force_boxy())
        case "boxy":
            engine.layout_archetype_force = "organic"
            engine.message_log.add(messages.layout_archetype_force_organic())
        case "organic":
            engine.layout_archetype_force = "hybrid"
            engine.message_log.add(messages.layout_archetype_force_hybrid())
        case _:
            engine.layout_archetype_force = None
            engine.message_log.add(messages.layout_archetype_force_cleared())
    engine._invalidate_floor_prefetch()

def toggle_stunned_debug(engine: GameEngine) -> None:
    """Debug helper: toggle stunned state to verify movement gate."""
    if engine.player is None:
        return
    fighter = engine.player.components.get(Fighter)
    if Stunned in engine.player.tags:
        if fighter is not None:
            heal(engine.player, fighter.max_hp)
        sync_stunned_state(engine.player)
        engine.message_log.add(messages.stunned_cleared_debug())
    else:
        if fighter is not None:
            fighter.hp = 0
        sync_stunned_state(engine.player)
        engine.message_log.add(
            messages.player_stunned(),
            category=MessageCategory.DANGER,
        )
