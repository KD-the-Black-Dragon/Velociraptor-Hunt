"""PR1: dual window size sets, 4K toggle swap, and position clamp."""

from __future__ import annotations

from unittest.mock import MagicMock

import tcod.context

from src.settings_store import SettingsStore
from src.ui.bootstrap import load_active_layout
from src.ui.layout import load_ui_layout
from src.ui.window_controller import WindowController
from src.ui.window_state import (
    FOUR_K_TOGGLE_MIN_Y,
    WindowPreferences,
    WindowSessionState,
    apply_four_k_toggle_geometry,
    clamp_four_k_toggle_position,
    ensure_four_k_size_seeded,
    has_four_k_client_size,
    resolve_active_client_size,
    restore_after_fullscreen,
    sync_window_from_sdl,
    window_from_dict,
    window_to_dict,
)


class _FakeWindow:
    def __init__(
        self,
        *,
        size: tuple[int, int] = (1600, 900),
        position: tuple[int, int] = (40, 50),
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

    @size.setter
    def size(self, value: tuple[int, int]) -> None:
        self._size = value

    @property
    def position(self) -> tuple[int, int]:
        return self._position

    @position.setter
    def position(self, xy: tuple[int, int]) -> None:
        self._position = xy

    @property
    def fullscreen(self) -> bool:
        return self._fullscreen

    @fullscreen.setter
    def fullscreen(self, value: bool) -> None:
        self._fullscreen = bool(value)

    def maximize(self) -> None:
        self._maximized = True

    @property
    def flags(self):
        from tcod.sdl.video import WindowFlags

        flags = WindowFlags(0)
        if self._maximized:
            flags |= WindowFlags.MAXIMIZED
        return flags


def test_clamp_four_k_toggle_position() -> None:
    assert clamp_four_k_toggle_position(-10, -5) == (0, FOUR_K_TOGGLE_MIN_Y)
    assert clamp_four_k_toggle_position(100, 80) == (100, 80)
    assert clamp_four_k_toggle_position(0, 29) == (0, FOUR_K_TOGGLE_MIN_Y)


def test_window_dict_round_trip_optional_four_k_size() -> None:
    layout = load_ui_layout("standard")
    prefs = WindowPreferences(
        client_width=1600,
        client_height=900,
        x=10,
        y=20,
        four_k_client_width=3200,
        four_k_client_height=1800,
    )
    restored = window_from_dict(window_to_dict(prefs), layout)
    assert restored.client_width == 1600
    assert restored.four_k_client_width == 3200
    assert restored.four_k_client_height == 1800

    bare = window_from_dict(
        {"client_width": 1600, "client_height": 900, "x": 0, "y": 0},
        layout,
    )
    assert bare.four_k_client_width is None
    assert bare.four_k_client_height is None
    assert "four_k_client_width" not in window_to_dict(bare)


def test_sync_writes_only_active_size_set() -> None:
    prefs = WindowPreferences(
        client_width=1600,
        client_height=900,
        x=10,
        y=20,
        four_k_client_width=3000,
        four_k_client_height=1600,
    )
    window = _FakeWindow(size=(3100, 1700), position=(55, 66))

    under_four_k = sync_window_from_sdl(
        prefs,
        window,  # type: ignore[arg-type]
        four_k_scaling=True,
    )
    assert under_four_k.client_width == 1600
    assert under_four_k.client_height == 900
    assert under_four_k.four_k_client_width == 3100
    assert under_four_k.four_k_client_height == 1700
    assert under_four_k.x == 55
    assert under_four_k.y == 66

    window.size = (1700, 950)
    under_normal = sync_window_from_sdl(
        under_four_k,
        window,  # type: ignore[arg-type]
        four_k_scaling=False,
    )
    assert under_normal.client_width == 1700
    assert under_normal.client_height == 950
    assert under_normal.four_k_client_width == 3100
    assert under_normal.four_k_client_height == 1700


def test_first_enable_seeds_double_without_mutating_normal() -> None:
    layout = load_active_layout(SettingsStore(four_k_scaling=True))
    prefs = WindowPreferences(client_width=1600, client_height=900, x=-40, y=5)
    window = _FakeWindow(size=(1600, 900), position=(-40, 5))
    context = MagicMock(spec=tcod.context.Context)
    context.sdl_window = window

    updated, (w, h) = apply_four_k_toggle_geometry(
        context,
        prefs,
        layout,
        outgoing_four_k=False,
        incoming_four_k=True,
    )
    assert updated.client_width == 1600
    assert updated.client_height == 900
    assert updated.four_k_client_width == 3200
    assert updated.four_k_client_height == 1800
    assert (w, h) == (3200, 1800)
    assert window.size == (3200, 1800)
    assert updated.x == 0
    assert updated.y == FOUR_K_TOGGLE_MIN_Y
    assert window.position == (0, FOUR_K_TOGGLE_MIN_Y)


def test_toggle_off_restores_normal_size() -> None:
    layout = load_active_layout(SettingsStore(four_k_scaling=False))
    prefs = WindowPreferences(
        client_width=1600,
        client_height=900,
        x=80,
        y=90,
        four_k_client_width=3200,
        four_k_client_height=1800,
    )
    window = _FakeWindow(size=(3200, 1800), position=(80, 90))
    context = MagicMock(spec=tcod.context.Context)
    context.sdl_window = window

    updated, (w, h) = apply_four_k_toggle_geometry(
        context,
        prefs,
        layout,
        outgoing_four_k=True,
        incoming_four_k=False,
    )
    assert updated.client_width == 1600
    assert updated.client_height == 900
    assert updated.four_k_client_width == 3200
    assert updated.four_k_client_height == 1800
    assert (w, h) == (1600, 900)
    assert window.size == (1600, 900)


def test_second_enable_uses_remembered_four_k_size_not_redouble() -> None:
    layout = load_active_layout(SettingsStore(four_k_scaling=True))
    prefs = WindowPreferences(
        client_width=1600,
        client_height=900,
        x=80,
        y=90,
        four_k_client_width=2800,
        four_k_client_height=1600,
    )
    window = _FakeWindow(size=(1600, 900), position=(80, 90))
    context = MagicMock(spec=tcod.context.Context)
    context.sdl_window = window

    updated, (w, h) = apply_four_k_toggle_geometry(
        context,
        prefs,
        layout,
        outgoing_four_k=False,
        incoming_four_k=True,
    )
    assert (w, h) == (2800, 1600)
    assert updated.four_k_client_width == 2800
    assert updated.client_width == 1600


def test_maximized_skips_size_and_position_apply() -> None:
    layout = load_active_layout(SettingsStore(four_k_scaling=True))
    prefs = WindowPreferences(client_width=1600, client_height=900, x=-50, y=0)
    window = _FakeWindow(size=(3840, 2160), position=(-50, 0), maximized=True)
    context = MagicMock(spec=tcod.context.Context)
    context.sdl_window = window

    updated, (w, h) = apply_four_k_toggle_geometry(
        context,
        prefs,
        layout,
        outgoing_four_k=False,
        incoming_four_k=True,
    )
    assert (w, h) == (3840, 2160)
    assert window.size == (3840, 2160)
    assert window.position == (-50, 0)
    assert updated.x == -50
    assert not has_four_k_client_size(updated)


def test_fullscreen_skips_size_swap() -> None:
    layout = load_active_layout(SettingsStore(four_k_scaling=True))
    prefs = WindowPreferences(client_width=1600, client_height=900)
    window = _FakeWindow(size=(3840, 2160), fullscreen=True)
    context = MagicMock(spec=tcod.context.Context)
    context.sdl_window = window

    updated, (w, h) = apply_four_k_toggle_geometry(
        context,
        prefs,
        layout,
        outgoing_four_k=False,
        incoming_four_k=True,
    )
    assert (w, h) == (3840, 2160)
    assert updated.four_k_client_width is None
    assert updated.client_width == 1600


def test_startup_seeds_four_k_size_when_enabled(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = SettingsStore(
        path=path,
        four_k_scaling=True,
        window=WindowPreferences(client_width=1600, client_height=900),
        window_saved_on_disk=True,
    )
    controller = WindowController(settings=settings)
    layout = load_active_layout(settings)
    prefs = controller.prepare_initial_preferences(layout)
    assert prefs.four_k_client_width == 3200
    assert prefs.four_k_client_height == 1800
    assert resolve_active_client_size(prefs, four_k_scaling=True) == (3200, 1800)


def test_ensure_four_k_size_seeded_idempotent() -> None:
    prefs = WindowPreferences(
        client_width=1000,
        client_height=800,
        four_k_client_width=2500,
        four_k_client_height=1400,
    )
    assert ensure_four_k_size_seeded(prefs) is prefs


def test_exit_fullscreen_clamps_windowed_position() -> None:
    layout = load_ui_layout("standard")
    prefs = WindowPreferences(
        client_width=1600,
        client_height=900,
        x=-80,
        y=5,
        fullscreen=True,
    )
    snapshot = WindowSessionState(
        client_width=1600,
        client_height=900,
        x=-80,
        y=5,
        maximized=False,
    )
    window = _FakeWindow(size=(3840, 2160), position=(0, 0), fullscreen=True)
    context = MagicMock(spec=tcod.context.Context)
    context.sdl_window = window

    updated, _size = restore_after_fullscreen(context, layout, prefs, snapshot)
    assert window.fullscreen is False
    assert updated.x == 0
    assert updated.y == FOUR_K_TOGGLE_MIN_Y
    assert window.position == (0, FOUR_K_TOGGLE_MIN_Y)


def test_exit_fullscreen_maximized_skips_position_clamp() -> None:
    layout = load_ui_layout("standard")
    prefs = WindowPreferences(
        client_width=1600,
        client_height=900,
        x=-80,
        y=5,
        fullscreen=True,
    )
    snapshot = WindowSessionState(
        client_width=1600,
        client_height=900,
        x=-80,
        y=5,
        maximized=True,
    )
    window = _FakeWindow(size=(3840, 2160), position=(0, 0), fullscreen=True)
    context = MagicMock(spec=tcod.context.Context)
    context.sdl_window = window

    updated, _size = restore_after_fullscreen(context, layout, prefs, snapshot)
    assert updated.maximized is True
    assert updated.x == -80
    assert updated.y == 5
