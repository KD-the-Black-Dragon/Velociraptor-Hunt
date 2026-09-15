"""PR4: Past Runs menu screen and gating."""

from __future__ import annotations

from pathlib import Path

import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.app import App, AppPhase
from src.menu import MenuAction, build_menu_options, handle_main_menu_event
from src.past_runs.schema import PastRunRecord
from src.past_runs.store import PastRunsStore, sorted_for_display
from src.save.coordinator import SaveCoordinator
from src.save.store import SaveStore
from src.ui.past_runs_screen import (
    PAST_RUNS_TITLE,
    PastRunsAction,
    PastRunsScreenState,
    build_past_runs_display_lines,
    format_past_run_stats_line,
    format_past_run_summary_line,
    handle_past_runs_event,
    past_runs_viewport_lines,
    render_past_runs_screen,
)


def _key(sym: KeySym, *, mod: Modifier = Modifier.NONE) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def _record(
    *,
    name: str = "Alex",
    depth: int = 5,
    date: str = "07/05/2026",
) -> PastRunRecord:
    return PastRunRecord(
        character_name=name,
        ending_kind="digested",
        ending_detail="wolf",
        monsters_defeated=3,
        runes_collected=1,
        depth=depth,
        date=date,
    )


def test_build_menu_options_omits_past_runs_when_empty() -> None:
    assert build_menu_options(load_available=False, past_runs_available=False) == (
        "New Game",
        "Options",
        "Credits",
        "Exit",
    )


def test_build_menu_options_includes_past_runs_when_available() -> None:
    options = build_menu_options(load_available=True, past_runs_available=True)
    assert options == (
        "New Game",
        "Load Game",
        "Past Runs",
        "Options",
        "Credits",
        "Exit",
    )


def test_menu_enter_on_past_runs_opens_screen(tmp_path: Path) -> None:
    store = PastRunsStore(tmp_path / "past_runs.json")
    store.append(_record(name="Morgan", depth=9))
    app = App(
        save_coordinator=SaveCoordinator(SaveStore(tmp_path / "saves")),
        past_runs_store=store,
    )
    assert "Past Runs" in app.menu.options

    while app.menu.highlighted_option != "Past Runs":
        app.menu.move_down()
    app.handle_event(_key(KeySym.RETURN))

    assert app.phase is AppPhase.PAST_RUNS
    assert len(app.past_runs_display) == 1
    assert app.past_runs_display[0].character_name == "Morgan"


def test_past_runs_escape_returns_to_menu(tmp_path: Path) -> None:
    store = PastRunsStore(tmp_path / "past_runs.json")
    store.append(_record())
    app = App(
        save_coordinator=SaveCoordinator(SaveStore(tmp_path / "saves")),
        past_runs_store=store,
    )
    while app.menu.highlighted_option != "Past Runs":
        app.menu.move_down()
    app.handle_event(_key(KeySym.RETURN))
    app.handle_event(_key(KeySym.ESCAPE))
    assert app.phase is AppPhase.MENU


def test_past_runs_screen_scrolls_with_arrow_keys() -> None:
    records = sorted_for_display(
        [_record(name=f"Run{i}", depth=i) for i in range(1, 12)],
    )
    state = PastRunsScreenState()
    console = tcod.console.Console(80, 8, order="F")
    line_count = len(build_past_runs_display_lines(records))
    viewport = past_runs_viewport_lines(console.height)
    assert line_count > viewport

    assert handle_past_runs_event(
        state,
        _key(KeySym.DOWN),
        line_count=line_count,
        viewport_lines=viewport,
    ) is PastRunsAction.NONE
    assert state.scroll_offset == 1

    for _ in range(20):
        handle_past_runs_event(
            state,
            _key(KeySym.PAGEDOWN),
            line_count=line_count,
            viewport_lines=viewport,
        )
    assert state.scroll_offset == line_count - viewport


def test_build_past_runs_display_lines_two_row_format() -> None:
    record = _record(name="Alex", depth=7, date="07/05/2026")
    lines = build_past_runs_display_lines([record])
    assert lines == [
        PAST_RUNS_TITLE,
        "",
        "Alex - Digested by wolf - 07/05/2026",
        "Depth 7 - 1 Runes - 3 Enemies Defeated",
    ]
    assert format_past_run_summary_line(record) == "Alex - Digested by wolf - 07/05/2026"
    assert format_past_run_stats_line(record) == "Depth 7 - 1 Runes - 3 Enemies Defeated"


def test_build_past_runs_display_lines_blank_between_runs() -> None:
    records = sorted_for_display(
        [_record(name="A", depth=2), _record(name="B", depth=5)],
    )
    lines = build_past_runs_display_lines(records)
    assert lines[0] == PAST_RUNS_TITLE
    assert lines[1] == ""
    assert "B - " in lines[2]
    assert "Depth 5" in lines[3]
    assert lines[4] == ""
    assert "A - " in lines[5]


def test_render_past_runs_screen_shows_two_row_entry() -> None:
    records = sorted_for_display([_record(name="Alex", depth=7)])
    console = tcod.console.Console(80, 24, order="F")
    render_past_runs_screen(console, records, PastRunsScreenState())

    body = ""
    for y in range(console.height - 1):
        for x in range(console.width):
            ch = int(console.rgba[x, y]["ch"])
            body += chr(ch) if ch else " "
    assert PAST_RUNS_TITLE in body
    assert "Alex - Digested by wolf - 07/05/2026" in body
    assert "Depth 7 - 1 Runes - 3 Enemies Defeated" in body
    assert "Name |" not in body


def test_handle_main_menu_past_runs_action() -> None:
    from src.menu import MainMenuState

    state = MainMenuState(
        options=build_menu_options(load_available=False, past_runs_available=True),
    )
    while state.highlighted_option != "Past Runs":
        state.move_down()
    assert handle_main_menu_event(state, _key(KeySym.RETURN)) is MenuAction.PAST_RUNS