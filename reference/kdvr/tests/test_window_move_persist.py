"""Window position persistence on move and quit."""

from __future__ import annotations

from unittest.mock import MagicMock

import tcod.context

from src.settings_store import SettingsStore
from src.ui.window_controller import WindowController
from src.ui.window_state import WindowPreferences, sync_window_from_sdl


class _FakeWindow:
    def __init__(
        self,
        *,
        size: tuple[int, int] = (1600, 900),
        position: tuple[int, int] = (0, 0),
        fullscreen: bool = False,
        maximized: bool = False,
    ) -> None:
        self._size = size
        self._position = position
        self._fullscreen = fullscreen
        self._maximized = maximized

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    @property
    def position(self) -> tuple[int, int]:
        return self._position

    @position.setter
    def position(self, xy: tuple[int, int]) -> None:
        self._position = xy

    @property
    def fullscreen(self) -> bool:
        return self._fullscreen

    @property
    def flags(self):
        from tcod.sdl.video import WindowFlags

        flags = WindowFlags(0)
        if self._maximized:
            flags |= WindowFlags.MAXIMIZED
        return flags


def test_sync_window_from_sdl_updates_position_without_resize() -> None:
    prefs = WindowPreferences(client_width=1600, client_height=900, x=10, y=20)
    window = _FakeWindow(size=(1600, 900), position=(240, 180))
    updated = sync_window_from_sdl(prefs, window)  # type: ignore[arg-type]
    assert updated.x == 240
    assert updated.y == 180
    assert updated.client_width == 1600
    assert updated.client_height == 900


def test_persist_now_syncs_position_from_context() -> None:
    settings = SettingsStore(
        window=WindowPreferences(client_width=1600, client_height=900, x=0, y=0),
    )
    controller = WindowController(settings=settings)
    context = MagicMock(spec=tcod.context.Context)
    context.sdl_window = _FakeWindow(position=(300, 220))

    captured: list[dict[str, object]] = []

    def _enqueue(store: SettingsStore) -> None:
        captured.append(store.to_dict())

    from src.settings_coordinator import settings_coordinator

    original_enqueue = settings_coordinator.enqueue
    settings_coordinator.enqueue = _enqueue  # type: ignore[method-assign]
    try:
        controller.persist_now(context)
    finally:
        settings_coordinator.enqueue = original_enqueue  # type: ignore[method-assign]

    assert captured
    assert captured[-1]["window"]["x"] == 300
    assert captured[-1]["window"]["y"] == 220