from __future__ import annotations

import multiprocessing as mp
import sys
import time
from typing import TYPE_CHECKING

import tcod.console
import tcod.context
import tcod.event
import tcod.tileset

from src.constants import GAME_TITLE, REST_FRAME_SLEEP_SECONDS, TILESET_PATH

# Legacy dungeon animation sleep (unused on career path; keep constant for loop)
PROJECTILE_FRAME_SLEEP_SECONDS = 0.0

if TYPE_CHECKING:
    from src.app import App
from src.settings_coordinator import settings_coordinator
from src.settings_store import SettingsStore
from src.ui.log_font import load_log_font_state
from src.ui.bootstrap import load_active_layout

from src.ui.window_controller import WindowController
from src.ui.window_limits import enforce_minimum_window_size
from src.ui.window_state import resize_app_console


def load_tileset() -> tcod.tileset.Tileset:
    """Load the CP437 tileset used for ASCII rendering."""
    tileset = tcod.tileset.load_tilesheet(
        str(TILESET_PATH),
        columns=16,
        rows=16,
        charmap=tcod.tileset.CHARMAP_CP437,
    )
    tcod.tileset.procedural_block_elements(tileset=tileset)
    return tileset


def _active_baseline(app: App):
    """Always derive the preset template from current settings."""
    return load_active_layout(app.settings)


def _resize_console(
    *,
    app: App,
    pixel_w: int,
    pixel_h: int,
) -> tcod.console.Console:
    return resize_app_console(app, pixel_w, pixel_h)


def _apply_pending_console(
    app: App,
    console: tcod.console.Console,
) -> tcod.console.Console:
    if app.pending_console_replace is not None:
        console = app.pending_console_replace
        app.pending_console_replace = None
    return console


def _handle_loop_event(
    event: tcod.event.Event,
    *,
    app: App,
    console: tcod.console.Console,
    context: tcod.context.Context,
) -> tuple[tcod.console.Console, bool]:
    """Process one window event. Returns (console, should_exit)."""
    if isinstance(event, tcod.event.WindowResized):
        baseline = _active_baseline(app)
        pixel_w, pixel_h = enforce_minimum_window_size(
            context,
            baseline,
            requested_w=event.width,
            requested_h=event.height,
        )
        if app.window_controller is not None:
            app.window_controller.on_window_changed(context)
        return _resize_console(app=app, pixel_w=pixel_w, pixel_h=pixel_h), False
    if isinstance(event, tcod.event.WindowMoved):
        if app.window_controller is not None:
            app.window_controller.on_window_changed(context)
        return console, False
    if app.handle_event(event, console=console, context=context):
        if app.window_controller is not None:
            app.window_controller.persist_now(context)
        return console, True
    console = _apply_pending_console(app, console)
    return console, False


def run_loop(
    console: tcod.console.Console,
    context: tcod.context.Context,
    app: App,
) -> None:
    """Event loop: render until quit."""
    while True:
        if app.rest_in_progress() or app.autoexplore_in_progress():
            assert app.engine is not None
            for event in tcod.event.get():
                console, should_exit = _handle_loop_event(
                    event,
                    app=app,
                    console=console,
                    context=context,
                )
                if should_exit:
                    raise SystemExit()
                app.render(console)
                app.present(console, context)
                break

            if not app.rest_in_progress() and not app.autoexplore_in_progress():
                continue

            if app.rest_in_progress():
                frame = app.engine.advance_rest_animation()
                if frame.screen_dirty:
                    app.render(console)
                app.present(console, context)
                time.sleep(REST_FRAME_SLEEP_SECONDS)
            else:
                frame = app.engine.advance_autoexplore_animation()
                # One dungeon step per present(); keeps animation and the OS message pump alive.
                app.render(console)
                app.present(console, context)
            continue

        if app.projectile_in_progress():
            assert app.engine is not None
            for event in tcod.event.get():
                console, should_exit = _handle_loop_event(
                    event,
                    app=app,
                    console=console,
                    context=context,
                )
                if should_exit:
                    raise SystemExit()
                app.render(console)
                app.present(console, context)
                break

            if not app.projectile_in_progress():
                continue

            app.render(console)
            app.present(console, context)
            app.engine.advance_projectile_animation()
            time.sleep(PROJECTILE_FRAME_SLEEP_SECONDS)
            continue

        app.render(console)
        app.present(console, context)

        for event in tcod.event.wait():
            console, should_exit = _handle_loop_event(
                event,
                app=app,
                console=console,
                context=context,
            )
            if should_exit:
                raise SystemExit()


def _initialize_multiprocessing_for_frozen_app() -> None:
    """Enable process-based workers inside PyInstaller bundles on Windows."""
    if getattr(sys, "frozen", False):
        mp.freeze_support()


def main() -> None:
    """Open the game window and run until the player quits."""
    _initialize_multiprocessing_for_frozen_app()
    from src.debug.crash_report import install_crash_handler, register_app, register_ui
    from src.debug.session_log import (
        session_log,
        should_log_quit_milestone,
        skip_quit_milestone,
    )

    session_log.start_session()
    install_crash_handler()
    app: App | None = None
    try:
        from src.data.entity_validation import load_entities_user_facing

        _, validation_error = load_entities_user_facing()
        if validation_error is not None:
            from src.debug.startup_error import report_startup_json_error

            report_startup_json_error(validation_error)
            skip_quit_milestone(reason="startup_validation")
            sys.exit(1)

        from src.app import App

        settings = SettingsStore.load()
        baseline = load_active_layout(settings)
        window_controller = WindowController(settings=settings)
        startup_prefs = window_controller.prepare_initial_preferences(baseline)
        pixel_w, pixel_h = startup_prefs.client_width, startup_prefs.client_height

        tileset = load_tileset()
        app = App(
            settings=settings,
            window_controller=window_controller,
            baseline_layout=baseline,
            ui_layout=baseline,
        )
        register_app(app)
        console = tcod.console.Console(baseline.root_cols, baseline.root_rows, order="F")

        with tcod.context.new(
            console=console,
            tileset=tileset,
            title=GAME_TITLE,
            width=pixel_w,
            height=pixel_h,
        ) as context:
            register_ui(console, context)
            pixel_w, pixel_h = window_controller.apply_startup(context, baseline)
            console = _resize_console(app=app, pixel_w=pixel_w, pixel_h=pixel_h)
            enforce_minimum_window_size(context, baseline)
            app.log_font = load_log_font_state(
                tile_px=baseline.tile_px,
                tile_scale=baseline.tile_scale,
            )
            try:
                run_loop(console, context, app)
            except BaseException:
                skip_quit_milestone(reason="crash")
                raise
    finally:
        if app is not None and app.window_controller is not None:
            app.window_controller.persist_now()
        settings_coordinator.flush()
        settings_coordinator.close()
        if should_log_quit_milestone():
            session_log.log("Quit")
        session_log.close()


if __name__ == "__main__":
    main()