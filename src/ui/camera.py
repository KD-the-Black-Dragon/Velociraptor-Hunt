from __future__ import annotations

import attrs

from src.ui.layout import UILayout


@attrs.define(frozen=True)
class MapCamera:
    """Top-left world tile of the visible map viewport."""

    origin_x: int
    origin_y: int
    width: int
    height: int

    @classmethod
    def from_layout(
        cls,
        layout: UILayout,
        player_x: int,
        player_y: int,
        *,
        map_w: int,
        map_h: int,
    ) -> MapCamera:
        cam_x, cam_y = layout.camera_origin(
            player_x,
            player_y,
            map_w=map_w,
            map_h=map_h,
        )
        tiles = layout.map_viewport_tiles
        return cls(cam_x, cam_y, tiles.w, tiles.h)

    def screen_xy(self, world_x: int, world_y: int) -> tuple[int, int] | None:
        screen_x = world_x - self.origin_x
        screen_y = world_y - self.origin_y
        if 0 <= screen_x < self.width and 0 <= screen_y < self.height:
            return screen_x, screen_y
        return None