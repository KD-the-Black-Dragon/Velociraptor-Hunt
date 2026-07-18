"""PR7: proportional sentence confirms + game-over body."""

from __future__ import annotations

from pathlib import Path

import pytest
import tcod.console

from src.app import App, AppPhase
from src.constants import DATA_DIR
from src.engine import GameEngine
from src.game_over_ending import GameOverEnding
from src.quit_confirm import QUIT_PROMPT, QuitConfirmState
from src.systems.digestion import GameOverState
from src.systems.render import render_game_over
from src.ui.layout import load_ui_layout
from src.ui.log_font import LOG_FONT_PATH, load_log_font_state
from src.ui.proportional_dialog import (
    GAME_OVER_FOOTER,
    dialog_font_from_log_font,
    game_over_body_paragraphs,
    render_proportional_confirm_image,
)
from tests.map_test_helpers import isolate_other_ais


@pytest.fixture
def log_font_or_skip():
    if not Path(LOG_FONT_PATH).is_file() and not (
        DATA_DIR / "fonts" / "SourceSans3-Regular.ttf"
    ).is_file():
        pytest.skip("log TTF not present")
    state = load_log_font_state(tile_px=12, tile_scale=2)
    if not state.enabled or state.font is None:
        pytest.skip("log font failed to load")
    return state


def test_proportional_confirm_image_smoke(log_font_or_skip) -> None:
    layout = load_ui_layout("standard")
    font = dialog_font_from_log_font(log_font_or_skip)
    assert font is not None
    image = render_proportional_confirm_image(
        [QUIT_PROMPT],
        font=font,
        layout=layout,
        console_w=layout.root_cols,
        console_h=layout.root_rows,
        error_message="Please type capital 'Y' or lowercase 'n' only.",
    )
    assert image.size[0] >= 100
    assert image.size[1] >= 40


def test_game_over_body_paragraphs() -> None:
    from src.ui.proportional_dialog import GAME_OVER_TITLE

    lines = game_over_body_paragraphs(
        player_name="Hero",
        ending_line="Digested by wolf",
        monsters_defeated=3,
        runes_collected=1,
        depth=2,
    )
    assert lines[0] == GAME_OVER_TITLE
    assert "Hero" in lines
    assert "Digested by wolf" in lines
    assert any("Monsters defeated: 3" in ln for ln in lines)
    assert GAME_OVER_FOOTER


def test_render_game_over_title_only_skips_body() -> None:
    console = tcod.console.Console(80, 44, order="F")
    render_game_over(
        console,
        player_name="Hero",
        ending=GameOverEnding(kind="digested", detail="wolf"),
        monsters_defeated=1,
        runes_collected=0,
        depth=1,
        draw_body=False,
    )
    text = "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(console.height)
        for x in range(console.width)
    )
    assert "GAME OVER" in text
    assert "Hero" not in text
    assert "Digested" not in text


def test_engine_game_over_body_flag() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.game_over = GameOverState(
        player_name="Hero",
        ending=GameOverEnding(kind="boss"),
        monsters_defeated=0,
        runes_collected=0,
        depth=1,
    )
    console = tcod.console.Console(80, 44, order="F")
    engine.render(console, draw_game_over_body=False)
    text = "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(console.height)
        for x in range(console.width)
    )
    assert "GAME OVER" in text
    assert "Hero" not in text


def test_app_confirm_image_for_quit(log_font_or_skip) -> None:
    app = App()
    app.log_font = log_font_or_skip
    app.phase = AppPhase.PLAY
    app.engine = GameEngine()
    isolate_other_ais(app.engine)
    app.quit_confirm = QuitConfirmState()
    console = tcod.console.Console(80, 44, order="F")
    img = app._confirm_dialog_image(console)
    assert img is not None


def test_confirm_error_line_is_drawn(log_font_or_skip) -> None:
    """Invalid key must show the capital-Y reminder (not only grow the box)."""
    from src.quit_confirm import QUIT_INVALID_MESSAGE
    from src.ui.menu_dialog import MENU_DIALOG_ERROR_FG

    layout = load_ui_layout("standard")
    font = dialog_font_from_log_font(log_font_or_skip)
    assert font is not None
    image = render_proportional_confirm_image(
        [QUIT_PROMPT],
        font=font,
        layout=layout,
        console_w=layout.root_cols,
        console_h=layout.root_rows,
        error_message=QUIT_INVALID_MESSAGE,
    )
    pixels = image.load()
    w, h = image.size
    found = False
    for y in range(h):
        for x in range(w):
            p = pixels[x, y]
            if p[3] > 0 and abs(p[0] - MENU_DIALOG_ERROR_FG[0]) < 10 and abs(
                p[1] - MENU_DIALOG_ERROR_FG[1]
            ) < 40:
                found = True
                break
        if found:
            break
    assert found


def test_digestion_haze_alpha_ramps_to_max_at_five_strikes() -> None:
    from src.ui.log_present import (
        DIGESTION_HAZE_MAX_STRIKES,
        SCREEN_HAZE_MAX_ALPHA,
        digestion_haze_alpha,
    )

    assert DIGESTION_HAZE_MAX_STRIKES == 5
    assert digestion_haze_alpha(0) == 0
    assert digestion_haze_alpha(1) < digestion_haze_alpha(3) < digestion_haze_alpha(5)
    assert digestion_haze_alpha(5) == SCREEN_HAZE_MAX_ALPHA
    assert digestion_haze_alpha(9) == SCREEN_HAZE_MAX_ALPHA


def test_mods_enter_shows_all_prompt_lines(log_font_or_skip) -> None:
    """All three mods-enter paragraphs must fit (including Proceed? (Y/n))."""
    from src.mods.confirm import MODS_ENTER_PROMPT_LINES

    layout = load_ui_layout("standard")
    font = dialog_font_from_log_font(log_font_or_skip)
    assert font is not None
    image = render_proportional_confirm_image(
        list(MODS_ENTER_PROMPT_LINES),
        font=font,
        layout=layout,
        console_w=layout.root_cols,
        console_h=layout.root_rows,
    )
    # Tall enough for three paragraphs + spacing (not clipped short panel).
    assert image.size[1] >= 100
