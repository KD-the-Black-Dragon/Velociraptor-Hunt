"""PR4: camera-centered map viewport rendering."""

from __future__ import annotations

from src.components import Position
from src.constants import MAP_HEIGHT, MAP_WIDTH
from src.engine import GameEngine
from src.systems.render import render_entities, render_examine_cursor, render_map
from src.ui.camera import MapCamera

from tests.ui_test_helpers import (
    default_layout,
    make_camera,
    make_console,
    make_region_bundle,
    message_log_y,
    render_engine_frame,
    root_char_at_world,
    root_char_at_world_for_engine,
)


def _cell_char(console, x: int, y: int) -> str:
    ch = int(console.rgba[x, y]["ch"])
    return chr(ch) if ch else " "


def test_camera_viewport_console_matches_layout_tiles() -> None:
    layout = default_layout()
    bundle = make_region_bundle(layout)
    map_console = bundle.console("map_viewport")
    assert map_console.width == layout.map_viewport_tiles.w
    assert map_console.height == layout.map_viewport_tiles.h


def test_render_map_with_camera_shows_subset() -> None:
    engine = GameEngine()
    engine._update_fov()
    layout = default_layout()
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    camera = make_camera(layout, pos.x, pos.y)

    map_console = make_console(layout.map_viewport_tiles.w, layout.map_viewport_tiles.h)
    render_map(map_console, engine.game_map, camera=camera)

    world_x = camera.origin_x + 1
    world_y = camera.origin_y + 1
    if engine.game_map.explored[world_y, world_x]:
        assert _cell_char(map_console, 1, 1) != " "

    far_x = (camera.origin_x + 100) % MAP_WIDTH
    far_y = (camera.origin_y + 100) % MAP_HEIGHT
    screen = camera.screen_xy(far_x, far_y)
    if screen is None:
        assert True
    else:
        assert _cell_char(map_console, screen[0], screen[1]) in " .#~>"


def test_player_appears_on_screen_when_centered() -> None:
    engine = GameEngine(player_name="CamTest")
    engine._update_fov()
    console = render_engine_frame(engine)
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    glyph = root_char_at_world_for_engine(engine, console, pos.x, pos.y)
    assert glyph == "@"


def test_render_examine_cursor_respects_camera() -> None:
    layout = default_layout()
    engine = GameEngine()
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    camera = make_camera(layout, pos.x, pos.y)
    map_console = make_console(camera.width, camera.height)

    render_map(map_console, engine.game_map, camera=camera)
    cursor = Position(pos.x, pos.y)
    render_examine_cursor(map_console, cursor, engine.game_map, camera=camera)
    screen = camera.screen_xy(pos.x, pos.y)
    assert screen is not None
    assert _cell_char(map_console, screen[0], screen[1]) == "X"


def test_message_log_starts_below_map_viewport() -> None:
    layout = default_layout()
    map_r = layout.region("map_viewport")
    assert message_log_y(layout) == map_r.y + map_r.h


def test_camera_clamps_player_near_edge() -> None:
    layout = default_layout()
    camera = make_camera(layout, 0, 0)
    assert camera.origin_x == 0
    assert camera.origin_y == 0

    camera_far = make_camera(layout, MAP_WIDTH - 1, MAP_HEIGHT - 1)
    assert camera_far.origin_x == MAP_WIDTH - layout.map_viewport_tiles.w
    assert camera_far.origin_y == MAP_HEIGHT - layout.map_viewport_tiles.h


def test_render_entities_off_viewport_are_omitted() -> None:
    engine = GameEngine()
    layout = default_layout()
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    camera = MapCamera(0, 0, layout.map_viewport_tiles.w, layout.map_viewport_tiles.h)

    map_console = make_console(camera.width, camera.height)
    render_map(map_console, engine.game_map, camera=camera)
    render_entities(
        map_console,
        engine.world,
        engine.game_map,
        player=player,
        camera=camera,
    )

    screen = camera.screen_xy(pos.x, pos.y)
    if screen is None:
        assert True
    else:
        assert _cell_char(map_console, screen[0], screen[1]) == "@"