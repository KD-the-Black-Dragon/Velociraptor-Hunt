"""Runtime window mode controller (fullscreen session snapshot + persistence hooks)."""

from __future__ import annotations

import attrs
import tcod.context

from src.settings_coordinator import settings_coordinator
from src.settings_store import SettingsStore
from src.ui.layout import UILayout
from src.ui.window_state import (
    WindowPreferences,
    WindowSessionState,
    apply_startup_window,
    capture_session_state,
    centered_position,
    default_first_launch_client_size,
    ensure_four_k_size_seeded,
    enter_fullscreen,
    get_sdl_window,
    restore_after_fullscreen,
    sync_window_from_sdl,
)


@attrs.define
class WindowController:
    """Apply saved window state and handle fullscreen toggles."""

    settings: SettingsStore
    session_before_fullscreen: WindowSessionState | None = None

    def prepare_initial_preferences(self, layout: UILayout) -> WindowPreferences:
        """Resolve startup client size/position before opening the tcod context."""
        if self.settings.window_saved_on_disk:
            prefs = self.settings.window
            if self.settings.four_k_scaling:
                prefs = ensure_four_k_size_seeded(prefs)
                self.settings.window = prefs
            return prefs
        client_w, client_h = default_first_launch_client_size(layout)
        x, y = centered_position(client_w, client_h)
        prefs = WindowPreferences(
            client_width=client_w,
            client_height=client_h,
            x=x,
            y=y,
        )
        if self.settings.four_k_scaling:
            prefs = ensure_four_k_size_seeded(prefs)
        self.settings.window = prefs
        return prefs

    def apply_startup(self, context: tcod.context.Context, layout: UILayout) -> tuple[int, int]:
        """Restore saved mode after the window is created."""
        pixel_w, pixel_h = apply_startup_window(
            context,
            self.settings.window,
            layout,
            four_k_scaling=self.settings.four_k_scaling,
        )
        window = get_sdl_window(context)
        if window is not None and not window.fullscreen:
            self.settings.window = sync_window_from_sdl(
                self.settings.window,
                window,
                four_k_scaling=self.settings.four_k_scaling,
            )
        return pixel_w, pixel_h

    def sync_from_context(self, context: tcod.context.Context) -> None:
        """Refresh in-memory window prefs from the live SDL window."""
        window = get_sdl_window(context)
        if window is None:
            return
        self.settings.window = sync_window_from_sdl(
            self.settings.window,
            window,
            four_k_scaling=self.settings.four_k_scaling,
        )

    def on_window_changed(self, context: tcod.context.Context) -> None:
        """Persist latest window geometry after a move or resize."""
        self.sync_from_context(context)
        settings_coordinator.enqueue(self.settings)

    def persist_now(self, context: tcod.context.Context | None = None) -> None:
        """Enqueue the current settings snapshot (quit/shutdown)."""
        if context is not None:
            self.sync_from_context(context)
        settings_coordinator.enqueue(self.settings)

    def toggle_fullscreen(
        self,
        context: tcod.context.Context,
        layout: UILayout,
    ) -> tuple[int, int]:
        """Toggle fullscreen and return the resulting client size."""
        window = get_sdl_window(context)
        if window is None:
            self.settings.window = attrs.evolve(
                self.settings.window,
                fullscreen=not self.settings.window.fullscreen,
            )
            settings_coordinator.enqueue(self.settings)
            return self.settings.window.client_width, self.settings.window.client_height

        if window.fullscreen:
            updated, client_size = restore_after_fullscreen(
                context,
                layout,
                self.settings.window,
                self.session_before_fullscreen,
            )
            self.settings.window = updated
            self.session_before_fullscreen = None
            settings_coordinator.enqueue(self.settings)
            return client_size

        self.session_before_fullscreen, updated = enter_fullscreen(
            window,
            self.settings.window,
            self.session_before_fullscreen,
        )
        self.settings.window = updated
        settings_coordinator.enqueue(self.settings)
        return window.size