"""PR 1: main menu shell, navigation, and app boot flow."""

from __future__ import annotations

import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.app import App, AppPhase
from src.constants import SCREEN_HEIGHT, SCREEN_WIDTH
from src.settings_store import SettingsStore
from src.menu import (
    MainMenuState,
    MenuAction,
    build_menu_options,
    handle_main_menu_event,
    is_ctrl_q,
    render_main_menu,
)
from src.menu_title import (
    TITLE_BANNER_HEIGHT,
    TITLE_BANNER_LINE_X,
    TITLE_BANNER_LINES,
    TITLE_BANNER_WIDTH,
    TITLE_BANNER_X_OFFSETS,
    render_title_banner,
)


def _key(sym: KeySym, *, mod: Modifier = Modifier.NONE) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def test_menu_starts_with_new_game_highlighted() -> None:
    state = MainMenuState()
    assert state.highlight == 0
    assert state.highlighted_option == "New Hunt"


def test_menu_moves_highlight_down_and_wraps() -> None:
    state = MainMenuState()
    for _ in range(len(state.options) - 1):
        state.move_down()
    assert state.highlighted_option == "Quit"
    state.move_down()
    assert state.highlighted_option == "New Hunt"


def test_menu_moves_highlight_up_and_wraps() -> None:
    state = MainMenuState()
    state.move_up()
    assert state.highlighted_option == "Quit"


def test_enter_on_exit_requests_exit() -> None:
    state = MainMenuState()
    while state.highlighted_option != "Quit":
        state.move_down()
    action = handle_main_menu_event(state, _key(KeySym.RETURN))
    assert action is MenuAction.EXIT


def test_enter_on_new_game_requests_play() -> None:
    state = MainMenuState()
    action = handle_main_menu_event(state, _key(KeySym.RETURN))
    assert action is MenuAction.NEW_HUNT


def test_enter_on_options_opens_options() -> None:
    state = MainMenuState()
    while state.highlighted_option != "Options":
        state.move_down()
    action = handle_main_menu_event(state, _key(KeySym.RETURN))
    assert action is MenuAction.OPTIONS


def test_enter_on_stats() -> None:
    state = MainMenuState()
    while state.highlighted_option != "Stats":
        state.move_down()
    action = handle_main_menu_event(state, _key(KeySym.RETURN))
    assert action is MenuAction.STATS


def test_hunt_menu_options_are_fixed() -> None:
    options = build_menu_options()
    assert options == ("New Hunt", "Training Mode", "Stats", "Options", "Quit")
    assert build_menu_options(continue_available=True) == (
        "Continue Hunt", "New Hunt", "Training Mode", "Stats", "Options", "Quit",
    )


def test_ctrl_q_on_menu_is_no_op() -> None:
    state = MainMenuState()
    action = handle_main_menu_event(
        state,
        _key(KeySym.Q, mod=Modifier.CTRL),
    )
    assert action is MenuAction.NONE
    assert is_ctrl_q(_key(KeySym.Q, mod=Modifier.CTRL))


def _onboarded_settings(tmp_path) -> SettingsStore:
    path = tmp_path / "settings.json"
    settings = SettingsStore(
        tutorial_prompt_answered=True,
        vore_prefs_onboarding_complete=True,
        path=path,
    )
    settings.save(path)
    return SettingsStore.load(path)


def test_app_boots_to_menu_without_engine(tmp_path) -> None:
    app = App(settings=_onboarded_settings(tmp_path))
    assert app.phase is AppPhase.MENU
    assert app.engine is None


def test_app_new_game_opens_name_entry(tmp_path) -> None:
    from pathlib import Path

    from src.career_store import CareerStore
    from src.save.coordinator import SaveCoordinator
    from src.save.store import SaveStore

    app = App(
        settings=_onboarded_settings(tmp_path),
        save_coordinator=SaveCoordinator(SaveStore(Path(tmp_path))),
        career_store=CareerStore(Path(tmp_path) / "career"),
    )
    assert not app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.WEAPON_SELECT
    assert app.engine is None


def test_app_exit_from_menu_quits(tmp_path) -> None:
    app = App(settings=_onboarded_settings(tmp_path))
    while app.menu.highlighted_option != "Quit":
        app.menu.move_down()
    assert app.handle_event(_key(KeySym.RETURN))


def test_app_window_quit_exits(tmp_path) -> None:
    app = App(settings=_onboarded_settings(tmp_path))
    assert app.handle_event(tcod.event.Quit())


def test_app_ctrl_q_on_menu_does_not_exit(tmp_path) -> None:
    app = App(settings=_onboarded_settings(tmp_path))
    assert not app.handle_event(_key(KeySym.Q, mod=Modifier.CTRL))
    assert app.phase is AppPhase.MENU


def _row_text(console: tcod.console.Console, y: int) -> str:
    chars: list[str] = []
    for x in range(SCREEN_WIDTH):
        ch = int(console.rgba[x, y]["ch"])
        chars.append(chr(ch) if ch else " ")
    return "".join(chars).strip()


def test_title_banner_row_offsets() -> None:
    assert len(TITLE_BANNER_X_OFFSETS) == TITLE_BANNER_HEIGHT
    assert TITLE_BANNER_HEIGHT == 5
    assert all(isinstance(x, int) for x in TITLE_BANNER_X_OFFSETS)


def test_render_main_menu_clears_to_title_and_options() -> None:
    console = tcod.console.Console(SCREEN_WIDTH, SCREEN_HEIGHT, order="F")
    state = MainMenuState()
    render_main_menu(console, state)

    options_y = SCREEN_HEIGHT - len(state.options) - 3
    title_y = max(2, (options_y - TITLE_BANNER_HEIGHT - 2) // 2)
    banner_top = _row_text(console, title_y)
    assert "____" in banner_top
    banner_mid = _row_text(console, title_y + 2)
    assert "GLADIAVORE" not in banner_mid
    assert "_" in banner_mid or "|" in banner_mid or "\\" in banner_mid
    banner_bottom = _row_text(console, title_y + TITLE_BANNER_HEIGHT - 1)
    assert "_" in banner_bottom or "\\" in banner_bottom

    assert _row_text(console, options_y) == "> New Hunt"


def _banner_print_x(width: int, row_offset: int) -> int:
    anchor = max(0, (width - TITLE_BANNER_WIDTH) // 2)
    return max(0, anchor + TITLE_BANNER_LINE_X[row_offset])


def test_title_banner_rows_share_block_anchor_across_widths() -> None:
    """Banner rows must not drift relative to each other when the window width changes."""
    text_rows = [
        row_offset
        for row_offset, line in enumerate(TITLE_BANNER_LINES)
        if line.rstrip()
    ]
    reference_deltas = [
        _banner_print_x(80, row_offset) - _banner_print_x(80, text_rows[0])
        for row_offset in text_rows
    ]

    for width in range(56, 100):
        deltas = [
            _banner_print_x(width, row_offset) - _banner_print_x(width, text_rows[0])
            for row_offset in text_rows
        ]
        assert deltas == reference_deltas

    for width in range(56, 99):
        shift = _banner_print_x(width + 1, text_rows[0]) - _banner_print_x(width, text_rows[0])
        for row_offset in text_rows:
            row_shift = _banner_print_x(width + 1, row_offset) - _banner_print_x(
                width, row_offset
            )
            assert row_shift == shift


def test_menu_options_share_x_across_widths() -> None:
    from src.menu import MENU_LINE_WIDTH

    for width in range(56, 100):
        console = tcod.console.Console(width, 42, order="F")
        render_main_menu(console, MainMenuState())
        state = MainMenuState()
        options_y = console.height - len(state.options) - 3
        menu_x = max(0, (width - MENU_LINE_WIDTH) // 2)
        for index, option in enumerate(state.options):
            row_y = options_y + index
            assert chr(int(console.rgba[menu_x, row_y]["ch"])) in "> "
            assert chr(int(console.rgba[menu_x + 1, row_y]["ch"])) == " "
            assert chr(int(console.rgba[menu_x + 2, row_y]["ch"])) == option[0]


def test_render_main_menu_options_fit_layout_console_height() -> None:
    """Options anchor to console.height (42-row layout), not legacy SCREEN_HEIGHT."""
    from src.ui.bootstrap import runtime_console_dimensions
    from src.ui.layout import load_ui_layout

    layout = load_ui_layout()
    cols, rows = runtime_console_dimensions(layout)
    console = tcod.console.Console(cols, rows, order="F")
    render_main_menu(console, MainMenuState())

    state = MainMenuState()
    options_y = rows - len(state.options) - 3
    assert options_y + len(state.options) - 1 < rows
    assert _row_text(console, options_y) == "> New Hunt"
    assert "Quit" in _row_text(console, options_y + len(state.options) - 1)