"""PR 3: floor depth, descent on Shift+`.`, good-ally follow, HUD depth."""

from __future__ import annotations

import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src import messages
from src.components import (
    AI,
    Alignment,
    Engulfed,
    Fighter,
    Inventory,
    NPCAlignment,
    Position,
    VoreCapable,
)
from src.constants import (
    FLOOR_DEPTH_MAX,
    FLOOR_DEPTH_START,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)

from src.engine import GameEngine
from src.map_gen import Tile, stairs_positions
from src.systems.ai import spawn_test_npc
from src.systems.fov import update_fov

from src.systems.vore import engulf_player

from tests.map_test_helpers import carve_east_of


def _press(engine: GameEngine, sym: KeySym, *, mod: Modifier = Modifier.NONE) -> bool:
    return engine.handle_event(
        tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod),
    )


def _press_descend(engine: GameEngine) -> bool:
    return _press(engine, KeySym.PERIOD, mod=Modifier.SHIFT)


def _press_descend_zero(engine: GameEngine, *, numpad: bool = False) -> bool:
    return _press(engine, KeySym.KP_0 if numpad else KeySym.N0)


def _place_player_on_stairs(engine: GameEngine) -> None:
    player = engine.player
    assert player is not None
    stairs = stairs_positions(engine.game_map)
    assert stairs
    x, y = stairs[0]
    player.components[Position] = Position(x, y)


def _good_npcs(engine: GameEngine) -> list:
    return [
        entity
        for entity in engine.world.Q.all_of(components=[AI, NPCAlignment])
        if entity.components[NPCAlignment].alignment == Alignment.GOOD
    ]


def test_new_game_starts_at_depth_one() -> None:
    engine = GameEngine()
    assert engine.floor_depth == FLOOR_DEPTH_START


def test_new_game_resets_depth() -> None:
    engine = GameEngine()
    engine.floor_depth = 7
    engine.new_game()
    assert engine.floor_depth == FLOOR_DEPTH_START


def test_unshifted_period_still_waits() -> None:
    engine = GameEngine()
    turns_before = engine.player_turn_count
    _press(engine, KeySym.PERIOD)
    assert engine.player_turn_count == turns_before + 1


def test_descend_not_on_stairs_no_turn() -> None:
    engine = GameEngine()
    turns_before = engine.player_turn_count
    depth_before = engine.floor_depth
    _press_descend(engine)
    assert engine.player_turn_count == turns_before
    assert engine.floor_depth == depth_before
    assert messages.no_stairs_here() in engine.message_log.lines()


def test_descend_engulfed_no_turn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    from tests.map_test_helpers import first_wolf

    wolf = first_wolf(engine)
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    wolf.components[Position] = Position(pos.x + 1, pos.y)
    engulf_player(engine.world, player, wolf, engine.message_log, narrative_type="OV")
    _place_player_on_stairs(engine)

    turns_before = engine.player_turn_count
    depth_before = engine.floor_depth
    _press_descend(engine)
    assert Engulfed in player.tags
    assert engine.player_turn_count == turns_before
    assert engine.floor_depth == depth_before
    assert messages.going_deeper_wont_help() in engine.message_log.lines()


def test_descend_with_zero_key_from_stairs() -> None:
    engine = GameEngine()
    _place_player_on_stairs(engine)
    depth_before = engine.floor_depth
    _press_descend_zero(engine, numpad=False)
    assert engine.floor_depth == depth_before + 1


def test_descend_with_numpad_zero_from_stairs() -> None:
    engine = GameEngine()
    _place_player_on_stairs(engine)
    depth_before = engine.floor_depth
    _press_descend_zero(engine, numpad=True)
    assert engine.floor_depth == depth_before + 1


def test_descend_from_stairs_advances_depth_and_regenerates_map() -> None:
    engine = GameEngine()
    engine.new_game(seed=42)
    old_tiles = engine.game_map.tiles.copy()
    _place_player_on_stairs(engine)

    _press_descend(engine)
    assert engine.floor_depth == FLOOR_DEPTH_START + 1
    assert not (engine.game_map.tiles == old_tiles).all()
    player = engine.player
    assert player is not None
    assert player.components[Position] == Position(*engine.game_map.enter_xy)


def test_descend_preserves_player_hp_and_inventory() -> None:
    engine = GameEngine()
    engine.new_game(seed=3)
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 11
    from src.systems.inventory import make_potion_instance

    potion = make_potion_instance()
    player.components[Inventory].slots["b"] = potion
    _place_player_on_stairs(engine)

    _press_descend(engine)
    assert player.components[Fighter].hp == 11
    saved = player.components[Inventory].slots.get("b")
    assert saved is not None
    assert saved.item_id == potion.item_id


def test_visible_knight_follows_on_descent() -> None:
    engine = GameEngine()
    engine.new_game(seed=9)
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    carve_east_of(engine, player_pos, 2)
    knight = spawn_test_npc(
        engine.world,
        x=player_pos.x + 1,
        y=player_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    knight_pos_before = knight.components[Position]
    _place_player_on_stairs(engine)
    stair_pos = player.components[Position]
    carve_east_of(engine, stair_pos, 2)
    knight.components[Position] = Position(stair_pos.x + 1, stair_pos.y)
    update_fov(engine.game_map, stair_pos.x, stair_pos.y)

    _press_descend(engine)

    assert knight in list(engine.world.Q.all_of(components=[AI]))
    assert knight.components[Position] != knight_pos_before


def test_hidden_knight_does_not_follow() -> None:
    engine = GameEngine()
    engine.new_game(seed=11)
    player = engine.player
    assert player is not None
    knight = spawn_test_npc(
        engine.world,
        x=1,
        y=1,
        species="knight",
        alignment=Alignment.GOOD,
    )
    update_fov(engine.game_map, player.components[Position].x, player.components[Position].y)
    _place_player_on_stairs(engine)

    _press_descend(engine)

    assert knight not in list(engine.world.Q.all_of(components=[AI]))


def test_followers_reduce_fresh_knight_spawns() -> None:
    from tests.map_test_helpers import carve_floor_tile, isolate_other_ais

    engine = GameEngine()
    engine.new_game(seed=13)
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    _place_player_on_stairs(engine)
    # Knight must have LOS to player *at descend* (stairs), not only at spawn tile.
    player_pos = player.components[Position]
    carve_floor_tile(engine, player_pos.x + 1, player_pos.y)
    spawn_test_npc(
        engine.world,
        x=player_pos.x + 1,
        y=player_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    update_fov(engine.game_map, player_pos.x, player_pos.y)

    _press_descend(engine)

    assert len(_good_npcs(engine)) >= 1
    assert len(list(engine.world.Q.all_of(components=[AI]))) > 0


def test_descend_respawns_monsters_and_items() -> None:
    engine = GameEngine()
    engine.new_game(seed=17)
    _place_player_on_stairs(engine)
    _press_descend(engine)

    assert len(list(engine.world.Q.all_of(components=[AI]))) > 0


def test_depth_caps_at_maximum() -> None:
    engine = GameEngine()
    engine.new_game(seed=19)
    engine.floor_depth = FLOOR_DEPTH_MAX
    _place_player_on_stairs(engine)
    _press_descend(engine)
    assert engine.floor_depth == FLOOR_DEPTH_MAX


def test_status_corner_shows_floor_depth() -> None:
    from tests.ui_test_helpers import render_engine_frame, status_corner_text

    engine = GameEngine()
    engine.floor_depth = 4
    console = render_engine_frame(engine)
    assert "Depth 4" in status_corner_text(console, engine.ui_layout)


def test_player_on_stairs_tile() -> None:
    engine = GameEngine()
    engine.new_game(seed=21)
    _place_player_on_stairs(engine)
    pos = engine.player.components[Position]
    assert engine.game_map.tiles[pos.y, pos.x] == Tile.STAIRS_DOWN