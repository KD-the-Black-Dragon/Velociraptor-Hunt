"""PR4: potion of blinking — free-cursor, visible-only, cancel free."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym

from src.components import Inventory, Position
from src.engine import GameEngine
from src.systems.inventory import (
    make_potion_instance,
    reset_item_registry_cache,
)
from src.systems.item_modals import (
    InventoryModalMode,
    begin_blink_target,
    begin_quaff,
    handle_blink_target_modal_event,
    handle_inventory_modal_letter,
    is_valid_blink_tile,
)
from src.systems.movement import can_entity_enter_tile

from tests.map_test_helpers import isolate_other_ais


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=None, mod=0)


def test_stock_blink_loads() -> None:
    reset_item_registry_cache()
    from src.systems.inventory import item_registry

    pot = item_registry().get_potion("potion_of_blinking")
    assert pot.effect == "blink"


def test_begin_blink_does_not_consume_potion() -> None:
    reset_item_registry_cache()
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["h"] = make_potion_instance(
        "potion_of_blinking"
    )
    begin_quaff(player, engine.inventory_modal, engine.message_log)
    assert (
        handle_inventory_modal_letter(
            player,
            "h",
            engine.inventory_modal,
            engine.message_log,
            engine.world,
            game_map=engine.game_map,
        )
        is False
    )
    assert engine.inventory_modal.mode == InventoryModalMode.BLINK_TARGET
    assert player.components[Inventory].slots["h"] is not None


def test_blink_cancel_keeps_potion() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["h"] = make_potion_instance(
        "potion_of_blinking"
    )
    begin_blink_target(
        player, "h", engine.inventory_modal, engine.message_log, game_map=engine.game_map
    )
    turned = handle_blink_target_modal_event(
        _key(KeySym.ESCAPE),
        player,
        engine.inventory_modal,
        engine.world,
        engine.game_map,
        engine.message_log,
    )
    assert turned is False
    assert engine.inventory_modal.mode == InventoryModalMode.NONE
    assert player.components[Inventory].slots["h"] is not None


def test_blink_success_moves_and_consumes() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    engine._update_fov()
    origin = player.components[Position]
    # Find a valid adjacent visible blink tile
    dest = None
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)):
        x, y = origin.x + dx, origin.y + dy
        if is_valid_blink_tile(player, engine.world, engine.game_map, x, y):
            dest = Position(x, y)
            break
    if dest is None:
        # Force visibility on a walkable neighbor if FOV is tight
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            x, y = origin.x + dx, origin.y + dy
            if engine.game_map.in_bounds(x, y) and can_entity_enter_tile(
                engine.game_map, x, y, player
            ):
                engine.game_map.visible[y, x] = True
                if is_valid_blink_tile(player, engine.world, engine.game_map, x, y):
                    dest = Position(x, y)
                    break
    assert dest is not None

    player.components[Inventory].slots["h"] = make_potion_instance(
        "potion_of_blinking"
    )
    begin_blink_target(
        player, "h", engine.inventory_modal, engine.message_log, game_map=engine.game_map
    )
    engine.inventory_modal.blink_cursor = dest
    turned = handle_blink_target_modal_event(
        _key(KeySym.RETURN),
        player,
        engine.inventory_modal,
        engine.world,
        engine.game_map,
        engine.message_log,
    )
    assert turned is True
    assert player.components[Position] == dest
    assert player.components[Inventory].slots["h"] is None


def test_invalid_blink_does_not_consume() -> None:
    from src import messages
    from src.log_categories import MessageCategory

    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["h"] = make_potion_instance(
        "potion_of_blinking"
    )
    begin_blink_target(
        player, "h", engine.inventory_modal, engine.message_log, game_map=engine.game_map
    )
    # Point at an invisible or invalid tile (0,0 often wall)
    engine.inventory_modal.blink_cursor = Position(0, 0)
    engine.game_map.visible[0, 0] = False
    turned = handle_blink_target_modal_event(
        _key(KeySym.RETURN),
        player,
        engine.inventory_modal,
        engine.world,
        engine.game_map,
        engine.message_log,
    )
    assert turned is False
    assert engine.inventory_modal.mode == InventoryModalMode.BLINK_TARGET
    assert player.components[Inventory].slots["h"] is not None
    caution = [
        e.text
        for e in engine.message_log.entries()
        if e.category == MessageCategory.CAUTION
    ]
    assert messages.blink_invalid_out_of_sight() in caution


def test_blink_cursor_cannot_enter_unexplored() -> None:
    from src.systems.item_modals import _move_blink_cursor

    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    engine._update_fov()
    origin = player.components[Position]
    # Find a neighbor that is in bounds and mark it unexplored
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        x, y = origin.x + dx, origin.y + dy
        if not engine.game_map.in_bounds(x, y):
            continue
        engine.game_map.explored[y, x] = False
        stayed = _move_blink_cursor(origin, (dx, dy), engine.game_map)
        assert stayed == origin
        # Explored neighbor is allowed
        engine.game_map.explored[y, x] = True
        moved = _move_blink_cursor(origin, (dx, dy), engine.game_map)
        assert moved == Position(x, y)
        break


def test_blink_rejection_reasons() -> None:
    from src import messages
    from src.systems.item_modals import blink_rejection_message

    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    engine._update_fov()
    origin = player.components[Position]

    # Out of sight
    engine.game_map.visible[0, 0] = False
    assert (
        blink_rejection_message(player, engine.world, engine.game_map, 0, 0)
        == messages.blink_invalid_out_of_sight()
    )

    # Visible but not walkable (prefer a wall next to player if any)
    from src.map_gen import Tile

    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (0, 2)):
        x, y = origin.x + dx, origin.y + dy
        if not engine.game_map.in_bounds(x, y):
            continue
        if engine.game_map.tiles[y, x] == Tile.WALL:
            engine.game_map.visible[y, x] = True
            assert (
                blink_rejection_message(player, engine.world, engine.game_map, x, y)
                == messages.blink_invalid_not_walkable()
            )
            break

    # Occupied by a blocking entity on a walkable visible tile
    from src.components import BlocksMovement, Fighter, Mobility, MobilityType, Renderable

    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        x, y = origin.x + dx, origin.y + dy
        if not can_entity_enter_tile(engine.game_map, x, y, player):
            continue
        engine.game_map.visible[y, x] = True
        blocker = engine.world[object()]
        blocker.components[Position] = Position(x, y)
        blocker.components[Fighter] = Fighter(
            hp=5, max_hp=5, accuracy=0.5, evade=0, ac=0, min_damage=1, max_damage=1
        )
        blocker.components[Renderable] = Renderable(ch=ord("w"))
        blocker.components[Mobility] = Mobility(kind=MobilityType.GROUND)
        blocker.tags.add(BlocksMovement)
        assert (
            blink_rejection_message(player, engine.world, engine.game_map, x, y)
            == messages.blink_invalid_occupied()
        )
        break
