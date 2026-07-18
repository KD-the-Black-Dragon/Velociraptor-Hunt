"""PR4: proportional digestion modal trial (image rasterization)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.constants import DATA_DIR
from src.ui.layout import load_ui_layout
from src.ui.log_font import LOG_FONT_PATH, load_log_font_state
from src.ui.proportional_dialog import (
    DIGESTION_MODAL_FOOTER,
    render_proportional_dialog_image,
)


@pytest.fixture
def log_font_or_skip():
    if not Path(LOG_FONT_PATH).is_file() and not (DATA_DIR / "fonts" / "SourceSans3-Regular.ttf").is_file():
        pytest.skip("log TTF not present")
    state = load_log_font_state(tile_px=12, tile_scale=2)
    if not state.enabled or state.font is None:
        pytest.skip("log font failed to load")
    return state


def test_proportional_digestion_dialog_image_has_body_and_footer(log_font_or_skip) -> None:
    layout = load_ui_layout("standard")
    body = (
        "Between the heat of the wolf's furry coat and your dwindling strength, "
        "you soon lack the means to attempt fighting your way back out."
    )
    image = render_proportional_dialog_image(
        body,
        font=log_font_or_skip.font,
        layout=layout,
        console_w=layout.root_cols,
        console_h=layout.root_rows,
    )
    assert image.size[0] >= 100
    assert image.size[1] >= 40
    # Footer glyph ink should exist in lower third (rough smoke)
    pixels = image.load()
    w, h = image.size
    found_non_bg = False
    for y in range(h * 2 // 3, h):
        for x in range(w):
            if pixels[x, y][3] > 0 and pixels[x, y][:3] != (25, 20, 45):
                found_non_bg = True
                break
        if found_non_bg:
            break
    assert found_non_bg


def test_engine_skips_cp437_digestion_when_flag_false() -> None:
    import tcod.console

    from src.engine import GameEngine
    from src.systems.digestion import DigestionModalState
    from tests.map_test_helpers import isolate_other_ais

    engine = GameEngine()
    isolate_other_ais(engine)
    engine.digestion_modal = DigestionModalState()
    engine.digestion_modal.open(
        engine.player,  # type: ignore[arg-type]
        ["UniqueDigestionPhaseTokenXYZ"],
    )
    # predator can be player for render-only smoke
    console = tcod.console.Console(80, 44, order="F")
    engine.render(console, draw_digestion_modal=False)
    text = "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(console.height)
        for x in range(console.width)
    )
    assert "UniqueDigestionPhaseTokenXYZ" not in text

    engine.render(console, draw_digestion_modal=True)
    text2 = "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(console.height)
        for x in range(console.width)
    )
    assert "UniqueDigestionPhaseTokenXYZ" in text2


def test_digestion_modal_footer_constant() -> None:
    assert "Enter" in DIGESTION_MODAL_FOOTER
