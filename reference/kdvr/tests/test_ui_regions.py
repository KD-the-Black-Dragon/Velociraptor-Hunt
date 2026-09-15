"""PR3–PR4: region sub-consoles and blit placement."""

from __future__ import annotations

from src.engine import GameEngine
from src.message_log import MessageLog
from src.systems.render import render_map
from src.ui.camera import MapCamera
from src.ui.regions import RegionBundle, blit_region, play_regions

from tests.ui_test_helpers import (
    default_layout,
    make_console,
    make_region_bundle,
    message_log_text,
    message_log_y,
    render_engine_frame,
)


def _cell_char(console, x: int, y: int) -> str:
    ch = int(console.rgba[x, y]["ch"])
    return chr(ch) if ch else " "


def test_play_regions_use_layout_viewport() -> None:
    layout = default_layout()
    regions = play_regions(layout, 80, 50)
    assert regions["map_viewport"].w == layout.map_viewport_tiles.w
    assert regions["map_viewport"].h == layout.map_viewport_tiles.h
    expected_log = layout.region("message_log")
    assert regions["message_log"] == expected_log


def test_region_bundle_map_console_matches_viewport() -> None:
    layout = default_layout()
    bundle = make_region_bundle(layout)
    map_console = bundle.console("map_viewport")
    assert map_console.width == layout.map_viewport_tiles.w
    assert map_console.height == layout.map_viewport_tiles.h


def test_blit_region_copies_map_tile_to_root() -> None:
    bundle = make_region_bundle()
    root = make_console()
    map_console = bundle.console("map_viewport")
    map_console.print(3, 4, "#", fg=(255, 255, 255))
    blit_region(root, bundle.placement("map_viewport"), map_console)
    assert _cell_char(root, 3, 4) == "#"


def test_engine_render_uses_region_pipeline() -> None:
    engine = GameEngine(player_name="Tester")
    engine.message_log = MessageLog()
    engine.message_log.add("region pipeline check")
    layout = engine.ui_layout
    console = render_engine_frame(engine)
    assert message_log_y(layout) == layout.region("map_viewport").y + layout.region("map_viewport").h
    assert "region pipeline check" in message_log_text(console, layout)


def test_render_map_camera_blit_matches_viewport_tile() -> None:
    engine = GameEngine()
    engine._update_fov()
    layout = default_layout()
    bundle = make_region_bundle(layout)
    root = make_console()
    map_console = bundle.console("map_viewport")
    player = engine.player
    assert player is not None
    from src.components import Position

    pos = player.components[Position]
    camera = MapCamera.from_layout(
        layout,
        pos.x,
        pos.y,
        map_w=engine.game_map.width,
        map_h=engine.game_map.height,
    )

    render_map(map_console, engine.game_map, camera=camera)
    blit_region(root, bundle.placement("map_viewport"), map_console)

    world_x = camera.origin_x + 2
    world_y = camera.origin_y + 2
    if engine.game_map.explored[world_y, world_x]:
        assert _cell_char(root, 2, 2) == _cell_char(map_console, 2, 2)