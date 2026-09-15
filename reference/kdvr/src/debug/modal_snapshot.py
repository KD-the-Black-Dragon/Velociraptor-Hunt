"""Active UI modal labels for crash reports (broader than ``modal_blocks_quit()``)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import App


def active_modal_label(app: App) -> str | None:
    """Return the highest-priority active modal label, or ``None`` for normal UI."""
    from src.app import AppPhase

    if app.new_game_confirm is not None:
        return "new_game_confirm"
    if app.mods_enter_confirm is not None:
        return "mods_enter_confirm"
    if app.quit_confirm is not None:
        return "quit_confirm"
    if app.phase is AppPhase.NAME_ENTRY:
        return "name_entry"
    if app.phase is AppPhase.MODS:
        return "mods"
    if app.phase is AppPhase.OPTIONS:
        return "options"
    if app.phase is AppPhase.PAST_RUNS:
        return "past_runs"
    if app.phase is AppPhase.CREDITS:
        return "credits"

    engine = app.engine
    if engine is None:
        return None

    if engine.game_over.active:
        return "game_over"
    if engine.digestion_modal.active:
        return "digestion_modal"
    if engine.vore_modal.active:
        return "vore_modal"
    if engine.ground_pickup_modal.active:
        return "ground_pickup_modal"
    if engine.inventory_modal.active:
        return "inventory_modal"
    if engine.macguffin_victory_confirm.active:
        return "macguffin_victory_confirm"
    if engine.help_overlay.active:
        return "help_overlay"
    if engine.log_overlay.active:
        return "log_overlay"
    if engine.examine_state.active or engine.examine_state.showing_description:
        return "examine"
    if engine.dismiss_state.active:
        return "dismiss"
    if engine.rest_in_progress():
        return "rest"
    if engine.autoexplore_in_progress():
        return "autoexplore"
    return None