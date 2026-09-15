"""PR10 / PR11: modals and menu screens at layout console size."""

from __future__ import annotations

import tcod.console

from src.engine import GameEngine
from src.name_entry import NameEntryState, render_name_entry
from src.quit_confirm import QuitConfirmState, render_quit_confirm
from src.systems.render import render_modal
from src.ui.bootstrap import runtime_console_dimensions
from src.ui.layout import load_ui_layout

from tests.test_vore_modal import _open_vore_modal
from tests.ui_test_helpers import default_layout, render_engine_frame

MODAL_BACKGROUND = (25, 20, 45)


def _modal_cells(console: tcod.console.Console) -> list[tuple[int, int]]:
    cells: list[tuple[int, int]] = []
    for y in range(console.height):
        for x in range(console.width):
            bg = tuple(console.rgba[x, y]["bg"][:3])
            if bg == MODAL_BACKGROUND:
                cells.append((x, y))
    return cells


def test_render_modal_centered_on_root_console() -> None:
    layout = default_layout()
    console = tcod.console.Console(layout.root_cols, layout.root_rows, order="F")
    render_modal(
        console,
        text="Inventory\na) sword\nb) potion\n\nEsc: close",
    )
    cells = _modal_cells(console)
    assert cells
    xs, ys = zip(*cells)
    center_x = (min(xs) + max(xs)) // 2
    center_y = (min(ys) + max(ys)) // 2
    assert abs(center_x - layout.root_cols // 2) <= layout.root_cols // 4
    assert abs(center_y - layout.root_rows // 2) <= layout.root_rows // 4


def test_vore_modal_drawn_on_root_console_over_sidebar() -> None:
    engine = GameEngine()
    _open_vore_modal(engine)
    console = render_engine_frame(engine)
    layout = engine.ui_layout
    side_r = layout.region("sidebar")
    assert any(
        tuple(console.rgba[x, y]["bg"][:3]) == MODAL_BACKGROUND
        for y in range(side_r.y, side_r.y + side_r.h)
        for x in range(side_r.x, side_r.x + side_r.w)
    )


def test_name_entry_uses_console_height() -> None:
    layout = load_ui_layout()
    cols, rows = runtime_console_dimensions(layout)
    console = tcod.console.Console(cols, rows, order="F")
    render_name_entry(console, NameEntryState(buffer="Alex"))
    prompt_y = rows // 2 - 2
    row_text = "".join(
        chr(int(console.rgba[x, prompt_y + 2]["ch"])) if int(console.rgba[x, prompt_y + 2]["ch"]) else " "
        for x in range(cols)
    ).strip()
    assert "> Alex_" in row_text


def test_quit_confirm_centered_on_root_console() -> None:
    layout = default_layout()
    cols, rows = runtime_console_dimensions(layout)
    console = tcod.console.Console(cols, rows, order="F")
    render_quit_confirm(console, QuitConfirmState())
    # Shared dialog chrome centers the panel; scan full console for the prompt.
    text = "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(rows)
        for x in range(cols)
    )
    assert "quit" in text.lower()
    # Roughly centered: prompt should not sit only in the top/bottom 2 rows.
    found_y = None
    for y in range(rows):
        row = "".join(
            chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
            for x in range(cols)
        )
        if "quit" in row.lower():
            found_y = y
            break
    assert found_y is not None
    assert 2 < found_y < rows - 2