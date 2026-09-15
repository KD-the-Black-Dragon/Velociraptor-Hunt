"""Helpers for layout-aware console and region rendering tests."""

from __future__ import annotations

import tcod.console

from src.constants import MAP_HEIGHT, MAP_WIDTH, SCREEN_HEIGHT, SCREEN_WIDTH
from src.engine import GameEngine
from src.ui.bootstrap import load_active_layout
from src.ui.camera import MapCamera
from src.ui.layout import UILayout
from src.ui.regions import RegionBundle


def default_layout() -> UILayout:
    return load_active_layout()


def message_log_y(layout: UILayout) -> int:
    return layout.region("message_log").y


def message_log_rect(layout: UILayout):
    return layout.region("message_log")


def hud_panel_y(layout: UILayout) -> int:
    """Alias for message_log_y (legacy test name)."""
    return message_log_y(layout)


def message_log_text(console: tcod.console.Console, layout: UILayout) -> str:
    """Concatenate printable text in the message_log region on a root console."""
    rect = message_log_rect(layout)
    return "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(rect.y, rect.y + rect.h)
        for x in range(rect.x, rect.x + rect.w)
    )


def sidebar_rect(layout: UILayout):
    return layout.region("sidebar")


def sidebar_text(console: tcod.console.Console, layout: UILayout) -> str:
    """Concatenate printable text in the sidebar region on a root console."""
    rect = sidebar_rect(layout)
    return "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(rect.y, rect.y + rect.h)
        for x in range(rect.x, rect.x + rect.w)
    )


def status_corner_rect(layout: UILayout):
    return layout.region("status_corner")


def status_corner_text(console: tcod.console.Console, layout: UILayout) -> str:
    """Concatenate printable text in the status_corner region on a root console."""
    rect = status_corner_rect(layout)
    return "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(rect.y, rect.y + rect.h)
        for x in range(rect.x, rect.x + rect.w)
    )


def make_console(
    width: int | None = None,
    height: int | None = None,
) -> tcod.console.Console:
    layout = default_layout()
    return tcod.console.Console(
        width or layout.root_cols,
        height or layout.root_rows,
        order="F",
    )


def make_region_bundle(
    layout: UILayout | None = None,
    *,
    root_width: int | None = None,
    root_height: int | None = None,
) -> RegionBundle:
    resolved = layout or default_layout()
    return RegionBundle.for_play(
        resolved,
        root_width or SCREEN_WIDTH,
        root_height or SCREEN_HEIGHT,
    )


def make_camera(
    layout: UILayout,
    player_x: int,
    player_y: int,
) -> MapCamera:
    return MapCamera.from_layout(
        layout,
        player_x,
        player_y,
        map_w=MAP_WIDTH,
        map_h=MAP_HEIGHT,
    )


def root_char_at_world(
    layout: UILayout,
    console: tcod.console.Console,
    camera: MapCamera,
    world_x: int,
    world_y: int,
) -> str:
    screen = camera.screen_xy(world_x, world_y)
    if screen is None:
        return " "
    map_r = layout.region("map_viewport")
    ch = int(console.rgba[map_r.x + screen[0], map_r.y + screen[1]]["ch"])
    return chr(ch) if ch else " "


def root_char_at_world_for_engine(
    engine: GameEngine,
    console: tcod.console.Console,
    world_x: int,
    world_y: int,
) -> str:
    from src.components import Position

    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    camera = make_camera(engine.ui_layout, player_pos.x, player_pos.y)
    return root_char_at_world(engine.ui_layout, console, camera, world_x, world_y)


def render_engine_frame(engine: GameEngine) -> tcod.console.Console:
    console = make_console()
    engine.render(console)
    return console