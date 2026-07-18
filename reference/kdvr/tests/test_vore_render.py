"""PR 7: engulfed blindness rendering and HUD indicator."""

from __future__ import annotations

from unittest.mock import patch

import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.components import (
    AI,
    Alignment,
    Engulfed,
    Fighter,
    Position,
    Renderable,
    Stunned,
    VoreCapable,
)
from src.spawn import KNIGHT_RENDERABLE, WOLF_RENDERABLE
from src.systems.ai import spawn_test_npc
from src.constants import MAP_HEIGHT, SCREEN_HEIGHT, SCREEN_WIDTH
from src.engine import GameEngine
from tests.ui_test_helpers import (
    make_console,
    render_engine_frame,
    root_char_at_world_for_engine,
    status_corner_text,
)
from src.map_gen import Tile
from src.systems.fov import update_fov

from tests.map_test_helpers import carve_east_of, ensure_wolf, first_wolf
from src.systems.movement import MOVEMENT_DIRECTIONS
from src.systems.render import (
    ENGULFED_OVERLAY_FG,
    PREDATOR_ENGULFED_BG,
    render_engulfed_overlay,
    render_entities,
    render_map,
)
from src.systems.vore import engulf_npc, engulf_player


def _press(engine: GameEngine, sym: KeySym) -> bool:
    return engine.handle_event(
        tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=Modifier.NONE),
    )


def _advance_modal(engine: GameEngine) -> None:
    while engine.vore_modal.active:
        _press(engine, KeySym.RETURN)


def _engulf_via_successful_vore(engine: GameEngine) -> None:
    from tests.map_test_helpers import first_wolf

    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    pos = player.components[Position]
    wolf = first_wolf(engine)
    carve_east_of(engine, pos, 2)
    wolf.components[Position] = Position(pos.x + 1, pos.y)
    update_fov(engine.game_map, pos.x, pos.y)
    with patch("src.systems.vore.resolve_vore_hit", return_value=True):
        engine._consume_player_turn()
        _advance_modal(engine)
    assert Engulfed in player.tags


def _cell_char(console: tcod.console.Console, x: int, y: int) -> str:
    ch = int(console.rgba[x, y]["ch"])
    return chr(ch) if ch else " "


def _cell_bg(console: tcod.console.Console, x: int, y: int) -> tuple[int, int, int]:
    return tuple(console.rgba[x, y]["bg"][:3])


def _row_text(console: tcod.console.Console, y: int) -> str:
    return "".join(_cell_char(console, x, y) for x in range(SCREEN_WIDTH)).strip()


def _visible_floor_coords(engine: GameEngine) -> list[tuple[int, int]]:
    coords: list[tuple[int, int]] = []
    game_map = engine.game_map
    for y in range(game_map.height):
        for x in range(game_map.width):
            if game_map.explored[y, x] and game_map.visible[y, x]:
                if game_map.tiles[y, x] == Tile.FLOOR:
                    coords.append((x, y))
    return coords


def test_render_map_blind_skips_tiles() -> None:
    engine = GameEngine()
    engine._update_fov()
    coords = _visible_floor_coords(engine)
    assert coords

    console = make_console()
    console.clear()
    render_map(console, engine.game_map, blind=False)
    x, y = coords[0]
    assert _cell_char(console, x, y) == "."

    console.clear()
    render_map(console, engine.game_map, blind=True)
    assert _cell_char(console, x, y) == " "


def test_render_entities_blind_shows_only_player() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    engine._update_fov()
    pos = player.components[Position]
    wolf = ensure_wolf(engine)
    carve_east_of(engine, pos, 2)
    wolf.components[Position] = Position(pos.x + 1, pos.y)
    update_fov(engine.game_map, pos.x, pos.y)

    console = make_console()
    console.clear()
    render_map(console, engine.game_map)
    render_entities(console, engine.world, engine.game_map, blind=False)
    assert _cell_char(console, pos.x, pos.y) == "@"
    wolf_glyph = chr(wolf.components[Renderable].ch)
    assert _cell_char(console, pos.x + 1, pos.y) == wolf_glyph

    console.clear()
    render_map(console, engine.game_map, blind=True)
    render_entities(
        console,
        engine.world,
        engine.game_map,
        blind=True,
        player=player,
    )
    assert _cell_char(console, pos.x, pos.y) == "@"
    assert _cell_char(console, pos.x + 1, pos.y) == " "


def test_render_engulfed_overlay_draws_adjacent_hashes() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    console = make_console()

    render_engulfed_overlay(console, engine.game_map, pos)

    for dx, dy in MOVEMENT_DIRECTIONS:
        x, y = pos.x + dx, pos.y + dy
        if not engine.game_map.in_bounds(x, y):
            continue
        assert _cell_char(console, x, y) == "#"
    assert _cell_char(console, pos.x, pos.y) == " "
    assert tuple(console.rgba[pos.x + 1, pos.y + 1]["fg"][:3]) == ENGULFED_OVERLAY_FG


def test_status_corner_shows_engulfed_indicator() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.tags.add(Engulfed)
    console = render_engine_frame(engine)
    assert "ENGLF" in status_corner_text(console, engine.ui_layout)


def test_engine_render_blind_while_engulfed() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    _engulf_via_successful_vore(engine)
    engine._update_fov()
    pos = player.components[Position]

    console = make_console()
    engine.render(console)

    assert root_char_at_world_for_engine(engine, console, pos.x, pos.y) == "@"
    for dx, dy in MOVEMENT_DIRECTIONS:
        x, y = pos.x + dx, pos.y + dy
        if engine.game_map.in_bounds(x, y):
            assert root_char_at_world_for_engine(engine, console, x, y) == "#"

    assert "ENGLF" in status_corner_text(console, engine.ui_layout)


def test_render_skips_engulfed_npc_prey_glyph() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    wolf = ensure_wolf(engine)
    carve_east_of(engine, pos, 2)
    wolf.components[Position] = Position(pos.x + 1, pos.y)
    wolf.components[Renderable] = WOLF_RENDERABLE
    knight = spawn_test_npc(
        engine.world,
        x=pos.x + 1,
        y=pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    knight.components[Renderable] = KNIGHT_RENDERABLE
    engulf_npc(engine.world, knight, wolf, narrative_type="OV")
    update_fov(engine.game_map, pos.x, pos.y)

    console = make_console()
    render_map(console, engine.game_map)
    render_entities(console, engine.world, engine.game_map)

    tile_x, tile_y = pos.x + 1, pos.y
    wolf_glyph = chr(WOLF_RENDERABLE.ch)
    assert _cell_char(console, tile_x, tile_y) == wolf_glyph
    assert _cell_char(console, tile_x, tile_y) != chr(KNIGHT_RENDERABLE.ch)


def test_render_predator_holding_prey_uses_dark_red_background() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    wolf = ensure_wolf(engine)
    carve_east_of(engine, pos, 2)
    wolf.components[Position] = Position(pos.x + 1, pos.y)
    wolf.components[Renderable] = WOLF_RENDERABLE
    knight = spawn_test_npc(
        engine.world,
        x=pos.x + 1,
        y=pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    engulf_npc(engine.world, knight, wolf, narrative_type="OV")
    update_fov(engine.game_map, pos.x, pos.y)

    console = make_console()
    render_map(console, engine.game_map)
    render_entities(console, engine.world, engine.game_map)

    tile_x, tile_y = pos.x + 1, pos.y
    assert _cell_char(console, tile_x, tile_y) == chr(WOLF_RENDERABLE.ch)
    assert _cell_bg(console, tile_x, tile_y) == PREDATOR_ENGULFED_BG


def test_engine_render_normal_after_escape() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    wolf.components[Position] = Position(pos.x + 1, pos.y)
    engulf_player(
        engine.world, player, wolf, engine.message_log, narrative_type="OV"
    )
    engine._update_fov()

    console = make_console()
    engine.render(console)

    from src.systems.vore import release_engulfed

    release_engulfed(
        engine.world,
        player,
        wolf,
        engine.game_map,
        engine.message_log,
        escape_direction=(0, -1),
    )
    engine._update_fov()
    engine.render(console)

    assert root_char_at_world_for_engine(engine, console, pos.x + 1, pos.y) == chr(
        wolf.components[Renderable].ch
    )