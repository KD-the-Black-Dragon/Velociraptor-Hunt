from __future__ import annotations

import attrs
import tcod.console

from src.ui.layout import RegionRect, UILayout

REGION_BACKGROUND = (20, 20, 30)
SIDEBAR_BACKGROUND = (18, 18, 28)
STATUS_CORNER_BACKGROUND = (16, 16, 26)

# Regions composited onto the root console during gameplay (sidebar blit last).
PLAY_BLIT_REGIONS: frozenset[str] = frozenset(
    {"map_viewport", "message_log", "sidebar", "status_corner"}
)
PLAY_BLIT_ORDER: tuple[str, ...] = (
    "map_viewport",
    "message_log",
    "sidebar",
    "status_corner",
)


def play_regions(layout: UILayout, root_width: int, root_height: int) -> dict[str, RegionRect]:
    """Root-console placement for camera viewport + message log region."""
    return {
        "map_viewport": layout.region("map_viewport"),
        "message_log": layout.region("message_log"),
        "sidebar": layout.region("sidebar"),
        "status_corner": layout.region("status_corner"),
    }


def blit_region(
    root: tcod.console.Console,
    rect: RegionRect,
    source: tcod.console.Console,
) -> None:
    """Copy a sub-console onto the root console at rect origin (clipped to both sizes)."""
    if rect.w <= 0 or rect.h <= 0:
        return
    width = min(rect.w, source.width, root.width - rect.x)
    height = min(rect.h, source.height, root.height - rect.y)
    if width <= 0 or height <= 0:
        return
    source.blit(root, dest_x=rect.x, dest_y=rect.y, width=width, height=height)


@attrs.define
class RegionBundle:
    """Sub-consoles for each layout region plus root placement."""

    layout: UILayout
    root_width: int
    root_height: int
    placements: dict[str, RegionRect]
    consoles: dict[str, tcod.console.Console]

    @classmethod
    def for_play(
        cls,
        layout: UILayout,
        root_width: int,
        root_height: int,
    ) -> RegionBundle:
        placements = play_regions(layout, root_width, root_height)
        log_rect = placements["message_log"]
        viewport = layout.map_viewport_tiles
        side = layout.region("sidebar")
        corner = layout.region("status_corner")

        consoles: dict[str, tcod.console.Console] = {
            "map_viewport": tcod.console.Console(viewport.w, viewport.h, order="F"),
            "message_log": tcod.console.Console(
                max(1, log_rect.w),
                max(1, log_rect.h),
                order="F",
            ),
            "sidebar": tcod.console.Console(side.w, side.h, order="F"),
            "status_corner": tcod.console.Console(corner.w, corner.h, order="F"),
        }
        return cls(
            layout=layout,
            root_width=root_width,
            root_height=root_height,
            placements=placements,
            consoles=consoles,
        )

    def console(self, name: str) -> tcod.console.Console:
        try:
            return self.consoles[name]
        except KeyError as exc:
            raise KeyError(f"unknown region console '{name}'") from exc

    def placement(self, name: str) -> RegionRect:
        return self.placements[name]

    def clear_region(self, name: str, *, bg: tuple[int, int, int] = REGION_BACKGROUND) -> None:
        sub = self.console(name)
        sub.clear(bg=bg)

    def blit_to_root(
        self,
        root: tcod.console.Console,
        *,
        names: frozenset[str] = PLAY_BLIT_REGIONS,
    ) -> None:
        ordered = [name for name in PLAY_BLIT_ORDER if name in names]
        for name in ordered:
            blit_region(root, self.placement(name), self.console(name))

    def blit_sidebar(self, root: tcod.console.Console) -> None:
        """Copy the sidebar sub-console onto the root (call after partial map re-blits)."""
        blit_region(root, self.placement("sidebar"), self.console("sidebar"))

    def blit_status_corner(self, root: tcod.console.Console) -> None:
        """Copy the status corner sub-console onto the root."""
        blit_region(root, self.placement("status_corner"), self.console("status_corner"))

    def blit_play_chrome(self, root: tcod.console.Console) -> None:
        """Re-blit sidebar + status corner after a partial map update."""
        self.blit_sidebar(root)
        self.blit_status_corner(root)