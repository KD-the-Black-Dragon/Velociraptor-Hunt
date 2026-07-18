from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import attrs

from src.constants import DATA_DIR

UI_LAYOUT_PATH = DATA_DIR / "ui_layout.json"
UI_LAYOUT_SCHEMA_VERSION = 1

REQUIRED_REGIONS: tuple[str, ...] = (
    "map_viewport",
    "sidebar",
    "message_log",
    "status_corner",
)


class UILayoutLoadError(ValueError):
    pass


@attrs.define(frozen=True)
class RegionRect:
    x: int
    y: int
    w: int
    h: int


@attrs.define(frozen=True)
class MapViewportTiles:
    w: int
    h: int


@attrs.define(frozen=True)
class SidebarLayout:
    hp_bar_width: int
    npc_hp_bar_width: int
    max_evil: int
    max_good: int
    evil_per_column: int
    good_per_column: int
    player_top_pad: int
    player_bottom_pad: int
    good_bottom_pad: int
    rows_per_npc: int


@attrs.define(frozen=True)
class UILayout:
    """Resolved layout preset for one root console."""

    preset_id: str
    tile_px: int
    tile_scale: int
    root_cols: int
    root_rows: int
    regions: dict[str, RegionRect]
    map_viewport_tiles: MapViewportTiles
    message_log_lines: int
    sidebar: SidebarLayout

    @property
    def root_width(self) -> int:
        return self.root_cols

    @property
    def root_height(self) -> int:
        return self.root_rows

    def region(self, name: str) -> RegionRect:
        try:
            return self.regions[name]
        except KeyError as exc:
            raise KeyError(f"unknown layout region '{name}'") from exc

    def camera_origin(
        self,
        player_x: int,
        player_y: int,
        *,
        map_w: int,
        map_h: int,
    ) -> tuple[int, int]:
        """Return top-left world tile shown in the map viewport, clamped to map bounds."""
        view_w = self.map_viewport_tiles.w
        view_h = self.map_viewport_tiles.h

        if map_w <= view_w:
            cam_x = 0
        else:
            cam_x = player_x - view_w // 2
            cam_x = max(0, min(cam_x, map_w - view_w))

        if map_h <= view_h:
            cam_y = 0
        else:
            cam_y = player_y - view_h // 2
            cam_y = max(0, min(cam_y, map_h - view_h))

        return cam_x, cam_y


def load_ui_layout(
    preset: str | None = None,
    *,
    path: Path | None = None,
    mods_root: Path | None = None,
    report_mod_errors: bool = True,
) -> UILayout:
    """Load a layout preset; default path layers whole-file mod replaces."""
    if path is not None:
        if mods_root is not None:
            raise TypeError("mods_root is only valid when path is None (layered load)")
        with path.open(encoding="utf-8") as handle:
            raw = json.load(handle)
        return parse_ui_layout(raw, preset=preset)

    from src.mods.pipeline import load_ui_layout_layered

    layout, _issues = load_ui_layout_layered(
        preset=preset,
        mods_root=mods_root,
        report=report_mod_errors,
    )
    return layout


def parse_ui_layout(raw: dict[str, Any], *, preset: str | None = None) -> UILayout:
    schema_version = _require_int(raw, "schema_version", context="ui_layout file")
    if schema_version != UI_LAYOUT_SCHEMA_VERSION:
        raise UILayoutLoadError(
            f"ui_layout file: unsupported schema_version {schema_version}"
        )

    tile_px = _require_int(raw, "tile_px", context="ui_layout file")
    if tile_px <= 0:
        raise UILayoutLoadError("ui_layout file: tile_px must be positive")

    tile_scale = _require_int(raw, "tile_scale", context="ui_layout file")
    if tile_scale <= 0:
        raise UILayoutLoadError("ui_layout file: tile_scale must be positive")

    default_preset = _require_str(raw, "default_preset", context="ui_layout file")

    presets_raw = raw.get("presets")
    if not isinstance(presets_raw, dict) or not presets_raw:
        raise UILayoutLoadError("ui_layout file: 'presets' must be a non-empty object")

    preset_id = preset or default_preset
    if preset_id not in presets_raw:
        known = ", ".join(sorted(presets_raw))
        raise UILayoutLoadError(
            f"ui_layout file: unknown preset '{preset_id}' (known: {known})"
        )

    preset_raw = presets_raw[preset_id]
    if not isinstance(preset_raw, dict):
        raise UILayoutLoadError(f"ui_layout presets['{preset_id}'] must be an object")

    layout = _parse_preset(
        preset_id,
        preset_raw,
        tile_px=tile_px,
        tile_scale=tile_scale,
    )
    _validate_region_tiling(layout)

    allowed_top = {"schema_version", "tile_px", "tile_scale", "default_preset", "presets"}
    for key in raw:
        if key not in allowed_top:
            raise UILayoutLoadError(f"ui_layout file: unknown top-level field '{key}'")

    return layout


def _parse_preset(
    preset_id: str,
    raw: dict[str, Any],
    *,
    tile_px: int,
    tile_scale: int,
) -> UILayout:
    root_cols = _require_int(raw, "root_cols", context=f"presets['{preset_id}']")
    root_rows = _require_int(raw, "root_rows", context=f"presets['{preset_id}']")
    if root_cols <= 0 or root_rows <= 0:
        raise UILayoutLoadError(
            f"presets['{preset_id}']: root_cols and root_rows must be positive"
        )

    regions_raw = raw.get("regions")
    if not isinstance(regions_raw, dict):
        raise UILayoutLoadError(f"presets['{preset_id}']: 'regions' must be an object")

    regions: dict[str, RegionRect] = {}
    for name in REQUIRED_REGIONS:
        if name not in regions_raw:
            raise UILayoutLoadError(
                f"presets['{preset_id}']: missing required region '{name}'"
            )
        entry = regions_raw[name]
        if not isinstance(entry, dict):
            raise UILayoutLoadError(
                f"presets['{preset_id}'].regions['{name}'] must be an object"
            )
        regions[name] = _parse_region(entry, context=f"presets['{preset_id}'].regions['{name}']")

    for key in regions_raw:
        if key not in REQUIRED_REGIONS:
            raise UILayoutLoadError(
                f"presets['{preset_id}']: unknown region '{key}'"
            )

    viewport_raw = raw.get("map_viewport_tiles")
    if not isinstance(viewport_raw, dict):
        raise UILayoutLoadError(
            f"presets['{preset_id}']: 'map_viewport_tiles' must be an object"
        )
    viewport = MapViewportTiles(
        w=_require_int(viewport_raw, "w", context=f"presets['{preset_id}'].map_viewport_tiles"),
        h=_require_int(viewport_raw, "h", context=f"presets['{preset_id}'].map_viewport_tiles"),
    )
    if viewport.w <= 0 or viewport.h <= 0:
        raise UILayoutLoadError(
            f"presets['{preset_id}']: map_viewport_tiles w/h must be positive"
        )

    map_region = regions["map_viewport"]
    if map_region.w != viewport.w or map_region.h != viewport.h:
        raise UILayoutLoadError(
            f"presets['{preset_id}']: map_viewport size must match map_viewport_tiles "
            f"({map_region.w}x{map_region.h} != {viewport.w}x{viewport.h})"
        )

    message_log_lines = _require_int(
        raw,
        "message_log_lines",
        context=f"presets['{preset_id}']",
    )
    if message_log_lines <= 0:
        raise UILayoutLoadError(
            f"presets['{preset_id}']: message_log_lines must be positive"
        )

    log_region = regions["message_log"]
    if log_region.h < message_log_lines:
        raise UILayoutLoadError(
            f"presets['{preset_id}']: message_log height {log_region.h} "
            f"< message_log_lines {message_log_lines}"
        )

    sidebar_raw = raw.get("sidebar")
    if not isinstance(sidebar_raw, dict):
        raise UILayoutLoadError(f"presets['{preset_id}']: 'sidebar' must be an object")

    sidebar = SidebarLayout(
        hp_bar_width=_require_int(
            sidebar_raw,
            "hp_bar_width",
            context=f"presets['{preset_id}'].sidebar",
        ),
        npc_hp_bar_width=_sidebar_int(
            sidebar_raw,
            "npc_hp_bar_width",
            default=6,
            context=f"presets['{preset_id}'].sidebar",
        ),
        max_evil=_require_int(
            sidebar_raw,
            "max_evil",
            context=f"presets['{preset_id}'].sidebar",
        ),
        max_good=_require_int(
            sidebar_raw,
            "max_good",
            context=f"presets['{preset_id}'].sidebar",
        ),
        evil_per_column=_sidebar_int(
            sidebar_raw,
            "evil_per_column",
            default=5,
            context=f"presets['{preset_id}'].sidebar",
        ),
        good_per_column=_sidebar_int(
            sidebar_raw,
            "good_per_column",
            default=2,
            context=f"presets['{preset_id}'].sidebar",
        ),
        player_top_pad=_sidebar_int(
            sidebar_raw,
            "player_top_pad",
            default=1,
            context=f"presets['{preset_id}'].sidebar",
        ),
        player_bottom_pad=_sidebar_int(
            sidebar_raw,
            "player_bottom_pad",
            default=1,
            context=f"presets['{preset_id}'].sidebar",
        ),
        good_bottom_pad=_sidebar_int(
            sidebar_raw,
            "good_bottom_pad",
            default=2,
            context=f"presets['{preset_id}'].sidebar",
        ),
        rows_per_npc=_sidebar_int(
            sidebar_raw,
            "rows_per_npc",
            default=3,
            context=f"presets['{preset_id}'].sidebar",
        ),
    )
    if sidebar.hp_bar_width <= 0 or sidebar.npc_hp_bar_width <= 0:
        raise UILayoutLoadError(
            f"presets['{preset_id}'].sidebar: hp_bar_width and npc_hp_bar_width must be positive"
        )
    if sidebar.max_evil < 0 or sidebar.max_good < 0:
        raise UILayoutLoadError(
            f"presets['{preset_id}'].sidebar: max_evil and max_good must be >= 0"
        )
    if sidebar.evil_per_column <= 0 or sidebar.good_per_column <= 0:
        raise UILayoutLoadError(
            f"presets['{preset_id}'].sidebar: evil_per_column and good_per_column must be positive"
        )
    if sidebar.max_evil < sidebar.evil_per_column:
        raise UILayoutLoadError(
            f"presets['{preset_id}'].sidebar: max_evil must be >= evil_per_column"
        )
    if sidebar.max_good < sidebar.good_per_column:
        raise UILayoutLoadError(
            f"presets['{preset_id}'].sidebar: max_good must be >= good_per_column"
        )
    if sidebar.rows_per_npc < 2:
        raise UILayoutLoadError(
            f"presets['{preset_id}'].sidebar: rows_per_npc must be >= 2"
        )

    side_region = regions["sidebar"]
    if side_region.w < sidebar.hp_bar_width + 10:
        raise UILayoutLoadError(
            f"presets['{preset_id}']: sidebar width {side_region.w} "
            f"too narrow for hp_bar_width {sidebar.hp_bar_width}"
        )
    if side_region.w < sidebar.npc_hp_bar_width + 4:
        raise UILayoutLoadError(
            f"presets['{preset_id}']: sidebar width {side_region.w} "
            f"too narrow for npc_hp_bar_width {sidebar.npc_hp_bar_width}"
        )

    allowed_preset = {
        "root_cols",
        "root_rows",
        "regions",
        "map_viewport_tiles",
        "message_log_lines",
        "sidebar",
    }
    for key in raw:
        if key not in allowed_preset:
            raise UILayoutLoadError(
                f"presets['{preset_id}']: unknown field '{key}'"
            )

    return UILayout(
        preset_id=preset_id,
        tile_px=tile_px,
        tile_scale=tile_scale,
        root_cols=root_cols,
        root_rows=root_rows,
        regions=regions,
        map_viewport_tiles=viewport,
        message_log_lines=message_log_lines,
        sidebar=sidebar,
    )


def _parse_region(raw: dict[str, Any], *, context: str) -> RegionRect:
    return RegionRect(
        x=_require_int(raw, "x", context=context),
        y=_require_int(raw, "y", context=context),
        w=_require_int(raw, "w", context=context),
        h=_require_int(raw, "h", context=context),
    )


def _validate_region_tiling(layout: UILayout) -> None:
    coverage = [[0 for _ in range(layout.root_cols)] for _ in range(layout.root_rows)]

    for name, rect in layout.regions.items():
        if rect.w <= 0 or rect.h <= 0:
            raise UILayoutLoadError(
                f"presets['{layout.preset_id}'].regions['{name}']: w/h must be positive"
            )
        if rect.x < 0 or rect.y < 0:
            raise UILayoutLoadError(
                f"presets['{layout.preset_id}'].regions['{name}']: x/y must be >= 0"
            )
        if rect.x + rect.w > layout.root_cols or rect.y + rect.h > layout.root_rows:
            raise UILayoutLoadError(
                f"presets['{layout.preset_id}'].regions['{name}']: region exceeds root bounds"
            )
        for row in range(rect.y, rect.y + rect.h):
            for col in range(rect.x, rect.x + rect.w):
                coverage[row][col] += 1

    for row in range(layout.root_rows):
        for col in range(layout.root_cols):
            count = coverage[row][col]
            if count != 1:
                raise UILayoutLoadError(
                    f"presets['{layout.preset_id}']: region tiling invalid at "
                    f"({col}, {row}) — expected 1 region, got {count}"
                )


def _require_str(raw: dict[str, Any], key: str, *, context: str) -> str:
    if key not in raw:
        raise UILayoutLoadError(f"{context}: missing required field '{key}'")
    value = raw[key]
    if not isinstance(value, str) or not value.strip():
        raise UILayoutLoadError(f"{context}: '{key}' must be a non-empty string")
    return value


def _sidebar_int(
    raw: dict[str, Any],
    key: str,
    *,
    default: int,
    context: str,
) -> int:
    if key not in raw:
        return default
    return _require_int(raw, key, context=context)


def _require_int(raw: dict[str, Any], key: str, *, context: str) -> int:
    if key not in raw:
        raise UILayoutLoadError(f"{context}: missing required field '{key}'")
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise UILayoutLoadError(f"{context}: '{key}' must be an integer")
    return value


_UI_PRESET_LABELS: dict[str, str] = {
    "standard": "Standard",
    "wide_sidebar": "Wide",
}


def list_ui_preset_ids(
    *,
    path: Path | None = None,
    mods_root: Path | None = None,
) -> tuple[str, ...]:
    """Return preset ids from effective ui_layout (core + mods) in sorted order."""
    if path is not None:
        with path.open(encoding="utf-8") as handle:
            raw = json.load(handle)
    else:
        from src.mods.pipeline import load_ui_layout_document_layered

        raw, _issues = load_ui_layout_document_layered(
            mods_root=mods_root,
            report=False,
        )
    presets_raw = raw.get("presets")
    if not isinstance(presets_raw, dict) or not presets_raw:
        raise UILayoutLoadError("ui_layout file: 'presets' must be a non-empty object")
    return tuple(sorted(presets_raw))


def ui_preset_display_label(preset_id: str) -> str:
    """Human-readable label for an options-menu preset id."""
    return _UI_PRESET_LABELS.get(preset_id, preset_id.replace("_", " ").title())


def cycle_ui_preset(
    current: str,
    *,
    step: int = 1,
    path: Path | None = None,
) -> str:
    """Return the next or previous preset id, wrapping at list ends."""
    preset_ids = list_ui_preset_ids(path=path)
    if not preset_ids:
        return current
    try:
        index = preset_ids.index(current)
    except ValueError:
        index = 0
    return preset_ids[(index + step) % len(preset_ids)]