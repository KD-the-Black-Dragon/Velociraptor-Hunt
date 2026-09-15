"""PR 1: main menu shell, navigation, and app boot flow."""

from __future__ import annotations

import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.app import App, AppPhase
from src.constants import SCREEN_HEIGHT, SCREEN_WIDTH
from src.settings_store import SettingsStore
from src.constants import TITLE_LOGO_PATH
from src.menu import (
    MainMenuState,
    MenuAction,
    build_menu_options,
    handle_main_menu_event,
    is_ctrl_q,
    main_menu_options_start_y,
    render_main_menu,
)
from src.menu_title import (
    TITLE_LOGO_WIDTH_FRAC,
    load_title_logo,
    title_logo_dest_rect,
)


def _key(sym: KeySym, *, mod: Modifier = Modifier.NONE) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def test_menu_starts_with_new_game_highlighted() -> None:
    state = MainMenuState()
    assert state.highlight == 0
    assert state.highlighted_option == "New Game"


def test_menu_moves_highlight_down_and_wraps() -> None:
    state = MainMenuState()
    for _ in range(len(state.options) - 1):
        state.move_down()
    assert state.highlighted_option == "Exit"
    state.move_down()
    assert state.highlighted_option == "New Game"


def test_menu_moves_highlight_up_and_wraps() -> None:
    state = MainMenuState()
    state.move_up()
    assert state.highlighted_option == "Exit"


def test_enter_on_exit_requests_exit() -> None:
    state = MainMenuState()
    while state.highlighted_option != "Exit":
        state.move_down()
    action = handle_main_menu_event(state, _key(KeySym.RETURN))
    assert action is MenuAction.EXIT


def test_enter_on_new_game_requests_play() -> None:
    state = MainMenuState()
    action = handle_main_menu_event(state, _key(KeySym.RETURN))
    assert action is MenuAction.NEW_GAME


def test_enter_on_options_opens_options() -> None:
    state = MainMenuState()
    while state.highlighted_option != "Options":
        state.move_down()
    action = handle_main_menu_event(state, _key(KeySym.RETURN))
    assert action is MenuAction.OPTIONS


def test_enter_on_credits_opens_credits() -> None:
    state = MainMenuState()
    while state.highlighted_option != "Credits":
        state.move_down()
    action = handle_main_menu_event(state, _key(KeySym.RETURN))
    assert action is MenuAction.CREDITS


def test_credits_always_above_exit() -> None:
    options = build_menu_options(load_available=False, past_runs_available=False)
    assert options[-2:] == ("Credits", "Exit")
    options = build_menu_options(load_available=True, past_runs_available=True)
    assert options[-2:] == ("Credits", "Exit")


def test_enter_on_load_game_and_past_runs() -> None:
    state = MainMenuState(
        options=build_menu_options(load_available=True, past_runs_available=True),
    )
    while state.highlighted_option != "Load Game":
        state.move_down()
    assert handle_main_menu_event(state, _key(KeySym.RETURN)) is MenuAction.LOAD_GAME
    while state.highlighted_option != "Past Runs":
        state.move_down()
    assert handle_main_menu_event(state, _key(KeySym.RETURN)) is MenuAction.PAST_RUNS


def test_menu_without_load_omits_load_game_option() -> None:
    state = MainMenuState(options=build_menu_options(load_available=False))
    assert "Load Game" not in state.options
    state.move_down()
    assert state.highlighted_option == "Options"


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

    from src.save.coordinator import SaveCoordinator
    from src.save.store import SaveStore

    app = App(
        settings=_onboarded_settings(tmp_path),
        save_coordinator=SaveCoordinator(SaveStore(Path(tmp_path))),
    )
    assert not app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.NAME_ENTRY
    assert app.engine is None


def test_app_exit_from_menu_quits(tmp_path) -> None:
    app = App(settings=_onboarded_settings(tmp_path))
    while app.menu.highlighted_option != "Exit":
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


def test_title_logo_asset_exists_and_loads() -> None:
    assert TITLE_LOGO_PATH.is_file()
    image = load_title_logo()
    assert image.mode == "RGBA"
    assert image.size[0] > 0 and image.size[1] > 0


def test_title_logo_dest_rect_stays_above_options() -> None:
    dest_w, dest_h = 960, 720
    logo_w, logo_h = 1728, 1152
    options_y = main_menu_options_start_y(42, 5)
    x, y, w, h = title_logo_dest_rect(
        dest_x=0,
        dest_y=0,
        dest_w=dest_w,
        dest_h=dest_h,
        logo_w=logo_w,
        logo_h=logo_h,
        options_start_y=options_y,
        console_h=42,
    )
    assert w > 0 and h > 0
    assert abs(w / dest_w - TITLE_LOGO_WIDTH_FRAC) < 0.08 or w <= int(
        dest_w * TITLE_LOGO_WIDTH_FRAC
    )
    assert w <= int(dest_w * TITLE_LOGO_WIDTH_FRAC) + 1
    assert y >= 0
    assert y + h <= int(dest_h * (options_y / 42))
    assert abs((x + w / 2) - dest_w / 2) < 2


def test_render_main_menu_options_only_no_ascii_banner() -> None:
    console = tcod.console.Console(SCREEN_WIDTH, SCREEN_HEIGHT, order="F")
    state = MainMenuState()
    render_main_menu(console, state)

    options_y = main_menu_options_start_y(SCREEN_HEIGHT, len(state.options))
    # Upper area should be empty (logo is composited at present-time, not on console).
    assert _row_text(console, 2) == ""
    assert _row_text(console, options_y // 2) == ""
    assert _row_text(console, options_y) == "> New Game"


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
    options_y = main_menu_options_start_y(rows, len(state.options))
    assert options_y + len(state.options) - 1 < rows
    assert _row_text(console, options_y) == "> New Game"
    assert "Exit" in _row_text(console, options_y + len(state.options) - 1)