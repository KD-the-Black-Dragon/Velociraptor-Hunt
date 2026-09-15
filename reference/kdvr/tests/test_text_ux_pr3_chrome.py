"""PR3: shared dialog chrome for confirms and menu notices."""

from __future__ import annotations

import tcod.console

from src.macguffin_victory_confirm import (
    MacguffinVictoryConfirmState,
    render_macguffin_victory_confirm,
)
from src.mods.confirm import ModsEnterConfirmState, render_mods_enter_confirm
from src.new_game_confirm import NewGameConfirmState, render_new_game_confirm
from src.quit_confirm import QuitConfirmState, render_quit_confirm
from src.ui.menu_dialog import DIALOG_BG, render_confirm_dialog


def _has_dialog_bg(console: tcod.console.Console) -> bool:
    """True if any cell uses the dialog panel background."""
    for y in range(console.height):
        for x in range(console.width):
            bg = tuple(int(console.rgba[x, y]["bg"][i]) for i in range(3))
            if bg == DIALOG_BG:
                return True
    return False


def test_render_confirm_dialog_draws_panel_bg() -> None:
    console = tcod.console.Console(80, 40, order="F")
    render_confirm_dialog(console, ["Hello dialog world"], band="center")
    assert _has_dialog_bg(console)


def test_new_game_confirm_has_chrome() -> None:
    console = tcod.console.Console(80, 40, order="F")
    render_new_game_confirm(console, NewGameConfirmState())
    assert _has_dialog_bg(console)


def test_quit_confirm_has_chrome() -> None:
    console = tcod.console.Console(80, 40, order="F")
    render_quit_confirm(console, QuitConfirmState())
    assert _has_dialog_bg(console)


def test_mods_enter_confirm_has_chrome() -> None:
    console = tcod.console.Console(80, 40, order="F")
    render_mods_enter_confirm(console, ModsEnterConfirmState())
    assert _has_dialog_bg(console)


def test_macguffin_victory_confirm_has_chrome() -> None:
    console = tcod.console.Console(80, 40, order="F")
    state = MacguffinVictoryConfirmState()
    state.open(macguffin_id="sword", display_name="The Sword of Freedom", score=10)
    render_macguffin_victory_confirm(console, state)
    assert _has_dialog_bg(console)
    text = "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(console.height)
        for x in range(console.width)
    )
    assert "Sword" in text or "found" in text.lower()


def test_narrow_console_confirm_stays_on_screen() -> None:
    console = tcod.console.Console(40, 20, order="F")
    render_confirm_dialog(
        console,
        ["A saved game exists and will be overwritten. Proceed? (Y/n)"],
        band="lower",
    )
    assert _has_dialog_bg(console)
