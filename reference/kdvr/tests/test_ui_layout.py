"""PR1: ui_layout.json loader, region validation, and camera math."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from src.constants import MAP_HEIGHT, MAP_WIDTH
from src.ui.layout import (
    UI_LAYOUT_PATH,
    UILayoutLoadError,
    load_ui_layout,
    parse_ui_layout,
)


def _minimal_preset(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "root_cols": 80,
        "root_rows": 44,
        "regions": {
            "map_viewport": {"x": 0, "y": 0, "w": 57, "h": 34},
            "sidebar": {"x": 57, "y": 0, "w": 23, "h": 34},
            "message_log": {"x": 0, "y": 34, "w": 70, "h": 10},
            "status_corner": {"x": 70, "y": 34, "w": 10, "h": 10},
        },
        "map_viewport_tiles": {"w": 57, "h": 34},
        "message_log_lines": 8,
        "sidebar": {
            "hp_bar_width": 9,
            "npc_hp_bar_width": 6,
            "max_evil": 10,
            "max_good": 4,
            "evil_per_column": 5,
            "good_per_column": 2,
            "player_top_pad": 1,
            "player_bottom_pad": 1,
            "good_bottom_pad": 2,
            "rows_per_npc": 3,
        },
    }
    merged = copy.deepcopy(base)
    for key, value in overrides.items():
        if key == "regions" and isinstance(value, dict):
            merged_regions = copy.deepcopy(base["regions"])
            assert isinstance(merged_regions, dict)
            merged_regions.update(value)
            merged["regions"] = merged_regions
        else:
            merged[key] = value
    return merged


def _minimal_file(*, preset: str = "standard", preset_body: dict[str, object] | None = None) -> dict[str, object]:
    body = preset_body or _minimal_preset()
    return {
        "schema_version": 1,
        "tile_px": 12,
        "tile_scale": 2,
        "default_preset": preset,
        "presets": {preset: body},
    }


def test_load_default_ui_layout_json() -> None:
    layout = load_ui_layout()
    assert layout.preset_id == "standard"
    assert layout.tile_px == 12
    assert layout.tile_scale == 2
    assert layout.root_cols == 80
    assert layout.root_rows == 44
    assert layout.map_viewport_tiles.w == 57
    assert layout.map_viewport_tiles.h == 34
    assert layout.message_log_lines == 8
    assert layout.sidebar.max_evil == 10
    assert layout.sidebar.max_good == 4
    assert layout.sidebar.evil_per_column == 5
    assert layout.sidebar.good_per_column == 2
    assert layout.sidebar.hp_bar_width == 9
    assert layout.sidebar.npc_hp_bar_width == 6
    assert layout.region("status_corner").w == 10

    map_region = layout.region("map_viewport")
    assert map_region.w == 57 and map_region.h == 34
    assert layout.region("sidebar").x == 57
    assert layout.region("sidebar").w == 23
    assert layout.region("message_log").h == 10


def test_load_wide_sidebar_preset() -> None:
    layout = load_ui_layout("wide_sidebar")
    assert layout.preset_id == "wide_sidebar"
    assert layout.map_viewport_tiles.w == 44
    assert layout.region("sidebar").w == 36
    assert layout.sidebar.hp_bar_width == 18


def test_list_ui_preset_ids_includes_standard_and_wide() -> None:
    from src.ui.layout import list_ui_preset_ids

    preset_ids = list_ui_preset_ids()
    assert preset_ids == ("standard", "wide_sidebar")


def test_unknown_preset_raises() -> None:
    with pytest.raises(UILayoutLoadError, match="unknown preset"):
        load_ui_layout("nonexistent")


def test_map_viewport_must_match_tile_dims() -> None:
    raw = _minimal_file(
        preset_body=_minimal_preset(
            regions={"map_viewport": {"x": 0, "y": 0, "w": 40, "h": 34}},
        ),
    )
    with pytest.raises(UILayoutLoadError, match="must match map_viewport_tiles"):
        parse_ui_layout(raw)


def test_message_log_height_must_fit_lines() -> None:
    raw = _minimal_file(
        preset_body=_minimal_preset(
            regions={"message_log": {"x": 0, "y": 34, "w": 70, "h": 4}},
            message_log_lines=8,
        ),
    )
    with pytest.raises(UILayoutLoadError, match="message_log height"):
        parse_ui_layout(raw)


def test_region_tiling_rejects_gap() -> None:
    raw = _minimal_file(
        preset_body=_minimal_preset(
            regions={"status_corner": {"x": 70, "y": 34, "w": 9, "h": 8}},
        ),
    )
    with pytest.raises(UILayoutLoadError, match="tiling invalid"):
        parse_ui_layout(raw)


def test_region_tiling_rejects_overlap() -> None:
    raw = _minimal_file(
        preset_body=_minimal_preset(
            regions={"sidebar": {"x": 40, "y": 0, "w": 40, "h": 34}},
        ),
    )
    with pytest.raises(UILayoutLoadError, match="tiling invalid"):
        parse_ui_layout(raw)


def test_sidebar_too_narrow_for_hp_bar() -> None:
    raw = _minimal_file(
        preset_body=_minimal_preset(
            sidebar={
                "hp_bar_width": 29,
                "max_evil": 10,
                "max_good": 4,
                "evil_per_column": 5,
                "good_per_column": 2,
            },
        ),
    )
    with pytest.raises(UILayoutLoadError, match="too narrow"):
        parse_ui_layout(raw)


def test_camera_origin_centers_player() -> None:
    layout = load_ui_layout()
    cam_x, cam_y = layout.camera_origin(40, 22, map_w=MAP_WIDTH, map_h=MAP_HEIGHT)
    assert cam_x == 40 - layout.map_viewport_tiles.w // 2
    assert cam_y == 22 - layout.map_viewport_tiles.h // 2


def test_camera_origin_clamps_at_map_edges() -> None:
    layout = load_ui_layout()
    view_w = layout.map_viewport_tiles.w
    view_h = layout.map_viewport_tiles.h

    cam_x, cam_y = layout.camera_origin(0, 0, map_w=MAP_WIDTH, map_h=MAP_HEIGHT)
    assert cam_x == 0
    assert cam_y == 0

    cam_x, cam_y = layout.camera_origin(
        MAP_WIDTH - 1,
        MAP_HEIGHT - 1,
        map_w=MAP_WIDTH,
        map_h=MAP_HEIGHT,
    )
    assert cam_x == MAP_WIDTH - view_w
    assert cam_y == MAP_HEIGHT - view_h


def test_camera_origin_when_map_smaller_than_viewport() -> None:
    layout = load_ui_layout()
    cam_x, cam_y = layout.camera_origin(5, 5, map_w=30, map_h=20)
    assert cam_x == 0
    assert cam_y == 0


def test_missing_required_region_raises() -> None:
    body = _minimal_preset()
    regions = body["regions"]
    assert isinstance(regions, dict)
    del regions["status_corner"]
    raw = _minimal_file(preset_body=body)
    with pytest.raises(UILayoutLoadError, match="missing required region"):
        parse_ui_layout(raw)


def test_unknown_top_level_field_raises() -> None:
    raw = _minimal_file()
    raw["extra"] = True
    with pytest.raises(UILayoutLoadError, match="unknown top-level field"):
        parse_ui_layout(raw)


def test_load_from_custom_path(tmp_path: Path) -> None:
    import json

    path = tmp_path / "ui_layout.json"
    path.write_text(json.dumps(_minimal_file()), encoding="utf-8")
    layout = load_ui_layout(path=path)
    assert layout.preset_id == "standard"