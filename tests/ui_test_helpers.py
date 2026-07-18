"""Helpers for layout-aware console tests (Gladiavore product)."""

from __future__ import annotations

import tcod.console

from src.constants import MAP_HEIGHT, MAP_WIDTH, SCREEN_HEIGHT, SCREEN_WIDTH
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
    return message_log_y(layout)


def message_log_text(console: tcod.console.Console, layout: UILayout) -> str:
    rect = message_log_rect(layout)
    return "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(rect.y, rect.y + rect.h)
        for x in range(rect.x, rect.x + rect.w)
    )


def sidebar_rect(layout: UILayout):
    return layout.region("sidebar")


def sidebar_text(console: tcod.console.Console, layout: UILayout) -> str:
    rect = sidebar_rect(layout)
    return "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(rect.y, rect.y + rect.h)
        for x in range(rect.x, rect.x + rect.w)
    )


def status_corner_rect(layout: UILayout):
    return layout.region("status_corner")


def status_corner_text(console: tcod.console.Console, layout: UILayout) -> str:
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
