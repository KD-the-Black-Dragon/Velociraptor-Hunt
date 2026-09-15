"""PR8: status corner panel (depth + ailments)."""

from __future__ import annotations

from src.components import Engulfed, Fighter, Stunned
from src.engine import GameEngine
from src.ui.regions import PLAY_BLIT_REGIONS, STATUS_CORNER_BACKGROUND
from src.ui.status_corner import (
    STATUS_AC_FG,
    PlayerStatusEffects,
    StatusBonusRow,
    render_status_corner,
)

from tests.ui_test_helpers import (
    default_layout,
    make_region_bundle,
    render_engine_frame,
    status_corner_text,
)


def _cell_char(console, x: int, y: int) -> str:
    ch = int(console.rgba[x, y]["ch"])
    return chr(ch) if ch else " "


def _row_text(console, y: int) -> str:
    return "".join(_cell_char(console, x, y) for x in range(console.width)).strip()


def test_status_corner_in_play_blit_regions() -> None:
    assert "status_corner" in PLAY_BLIT_REGIONS


def test_render_status_corner_shows_depth() -> None:
    layout = default_layout()
    bundle = make_region_bundle(layout)
    corner = bundle.console("status_corner")
    render_status_corner(corner, PlayerStatusEffects(floor_depth=4))
    assert _row_text(corner, 0) == "Depth 4"


def test_render_status_corner_shows_stun_and_engulfed() -> None:
    layout = default_layout()
    bundle = make_region_bundle(layout)
    corner = bundle.console("status_corner")
    render_status_corner(
        corner,
        PlayerStatusEffects(floor_depth=2, stunned=True, engulfed=True),
    )
    assert _row_text(corner, 0) == "Depth 2"
    assert _row_text(corner, 1) == "STUN"
    assert _row_text(corner, 2) == "ENGLF"


def test_render_status_corner_supports_extra_rows() -> None:
    layout = default_layout()
    bundle = make_region_bundle(layout)
    corner = bundle.console("status_corner")
    render_status_corner(
        corner,
        PlayerStatusEffects(
            floor_depth=1,
            extra_rows=(StatusBonusRow("BUFF", STATUS_AC_FG),),
        ),
    )
    assert _row_text(corner, 1) == "BUFF"


def test_render_status_corner_fills_background() -> None:
    layout = default_layout()
    bundle = make_region_bundle(layout)
    corner = bundle.console("status_corner")
    render_status_corner(corner, PlayerStatusEffects(floor_depth=1))
    bg = tuple(corner.rgba[0, 0]["bg"][:3])
    assert bg == STATUS_CORNER_BACKGROUND


def test_engine_render_shows_depth_in_status_corner() -> None:
    engine = GameEngine()
    engine.floor_depth = 7
    console = render_engine_frame(engine)
    corner_text = status_corner_text(console, engine.ui_layout)
    assert "Depth 7" in corner_text


def test_engine_render_shows_engulfed_in_status_corner() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.tags.add(Engulfed)
    console = render_engine_frame(engine)
    assert "ENGLF" in status_corner_text(console, engine.ui_layout)


def test_engine_render_shows_stun_in_status_corner() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.tags.add(Stunned)
    console = render_engine_frame(engine)
    assert "STUN" in status_corner_text(console, engine.ui_layout)