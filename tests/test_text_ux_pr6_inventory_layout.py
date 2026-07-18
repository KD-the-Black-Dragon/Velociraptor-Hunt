"""PR6: multi-column inventory layout + proportional list dialog."""

from __future__ import annotations

from pathlib import Path

import pytest
import tcod.console

from src.components import Inventory, InventoryItemInstance, ItemCategory
from src.constants import DATA_DIR
from src.engine import GameEngine
from src.systems.item_modals import (
    InventoryModalMode,
    InventoryModalState,
    begin_inspect,
    inventory_list_item_rows,
    inventory_modal_text,
)
from src.ui.inventory_list_layout import (
    choose_column_count,
    format_multi_column_block,
    join_list_modal,
)
from src.ui.layout import load_ui_layout
from src.ui.log_font import LOG_FONT_PATH, load_log_font_state
from src.ui.proportional_dialog import (
    LIST_MODAL_FOOTER,
    dialog_font_from_log_font,
    render_proportional_list_dialog_image,
)
from tests.map_test_helpers import isolate_other_ais


def _dagger() -> InventoryItemInstance:
    return InventoryItemInstance(
        item_id="dagger",
        category=ItemCategory.WEAPON,
        durability=100,
    )


def test_choose_column_count_short_always_one() -> None:
    assert choose_column_count(1, available_width=80) == 1
    assert choose_column_count(8, available_width=80) == 1


def test_choose_column_count_medium_up_to_two() -> None:
    assert choose_column_count(9, available_width=80) == 2
    assert choose_column_count(14, available_width=80) == 2
    assert choose_column_count(14, available_width=20) == 1


def test_choose_column_count_many_up_to_three() -> None:
    assert choose_column_count(15, available_width=80) == 3
    assert choose_column_count(26, available_width=80) == 3
    # min_col=14, gap=2 → 1 col when width < 30-ish; 2 when ~30–45; 3 when wider
    assert choose_column_count(26, available_width=20) == 1
    assert choose_column_count(26, available_width=32) == 2
    assert choose_column_count(26, available_width=50) == 3


def test_format_multi_column_fill_down() -> None:
    items = [f"{chr(ord('a') + i)}) item" for i in range(6)]
    # Force 2 columns: 6 items > 8? No - 6 is short → 1 col. Use 10 items.
    items = [f"{chr(ord('a') + i)}) item" for i in range(10)]
    block = format_multi_column_block(items, available_width=60)
    lines = [ln for ln in block.split("\n") if ln.strip()]
    # Fill down: first column has ceil(10/2)=5 items starting with a)
    assert lines[0].startswith("a)")
    assert "f)" in lines[0] or any("f)" in ln for ln in lines)
    # Row 0 should have a) in left and f) in right (column-major)
    assert "a)" in lines[0]
    assert "f)" in lines[0]


def test_multi_column_width_hugs_short_labels() -> None:
    """2-col daggers stay compact — not stretched to available_width."""
    items = [f"{chr(ord('a') + i)}) dagger" for i in range(10)]
    block = format_multi_column_block(items, available_width=72)
    lines = [ln for ln in block.split("\n") if ln.strip()]
    # Natural: "a) dagger" (9) + gap(2) + "f) dagger" (9) ≈ 20, not ~70
    assert max(len(ln) for ln in lines) <= 28
    assert max(len(ln) for ln in lines) < 40


def test_join_list_modal_includes_all_letters() -> None:
    items = [f"{chr(ord('a') + i)}) dagger" for i in range(26)]
    text = join_list_modal("Inventory", items, "Esc: close", available_width=72)
    for i in range(26):
        assert f"{chr(ord('a') + i)})" in text
    assert text.startswith("Inventory")
    assert "Esc: close" in text


def test_inspect_list_modal_multi_column_dense_rows() -> None:
    from src.systems.render import _modal_lines_from_text

    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=42)
    player = engine.player
    assert player is not None
    inv = player.components[Inventory]
    for letter in "abcdefghij":
        inv.slots[letter] = _dagger()
    text = inventory_modal_text(
        InventoryModalState(mode=InventoryModalMode.INSPECT_LIST),
        inv,
        available_width=72,
    )
    lines = _modal_lines_from_text(text, max_inner=72)
    # Multi-column: first item row contains a) and likely f)
    assert any("a)" in ln for ln in lines)
    # Dense: consecutive non-empty lines after Inventory
    idx = lines.index("Inventory")
    assert lines[idx + 1] == ""
    assert "a)" in lines[idx + 2]
    # Next line should be another item row, not blank
    assert lines[idx + 3] != ""


def test_engine_skips_cp437_inventory_when_flag_false() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=43)
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["a"] = _dagger()
    begin_inspect(player, engine.inventory_modal, engine.message_log)
    console = tcod.console.Console(80, 44, order="F")
    engine.render(console, draw_inventory_modal=False)
    text = "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(console.height)
        for x in range(console.width)
    )
    assert "Inventory" not in text

    engine.render(console, draw_inventory_modal=True)
    text2 = "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(console.height)
        for x in range(console.width)
    )
    assert "Inventory" in text2


@pytest.fixture
def log_font_or_skip():
    if not Path(LOG_FONT_PATH).is_file() and not (DATA_DIR / "fonts" / "SourceSans3-Regular.ttf").is_file():
        pytest.skip("log TTF not present")
    state = load_log_font_state(tile_px=12, tile_scale=2)
    if not state.enabled or state.font is None:
        pytest.skip("log font failed to load")
    return state


def test_proportional_list_dialog_image_smoke(log_font_or_skip) -> None:
    layout = load_ui_layout("standard")
    font = dialog_font_from_log_font(log_font_or_skip)
    assert font is not None
    items = [f"{chr(ord('a') + i)}) dagger" for i in range(26)]
    image = render_proportional_list_dialog_image(
        "Inventory",
        items,
        font=font,
        layout=layout,
        console_w=layout.root_cols,
        console_h=layout.root_rows,
        footer_text=LIST_MODAL_FOOTER,
    )
    assert image.size[0] >= 120
    assert image.size[1] >= 80
    # Non-background ink present
    pixels = image.load()
    w, h = image.size
    found = False
    for y in range(h):
        for x in range(w):
            if pixels[x, y][3] > 0 and pixels[x, y][:3] != (25, 20, 45):
                found = True
                break
        if found:
            break
    assert found


def test_proportional_list_short_names_not_full_window(log_font_or_skip) -> None:
    """Multi-column dagger list should not balloon to ~max panel width."""
    layout = load_ui_layout("standard")
    font = dialog_font_from_log_font(log_font_or_skip)
    assert font is not None
    root_w = layout.root_cols * layout.tile_px * layout.tile_scale
    max_panel_w = int(root_w * 0.88)
    items = [f"{chr(ord('a') + i)}) dagger" for i in range(12)]
    image = render_proportional_list_dialog_image(
        "Drop which item?",
        items,
        font=font,
        layout=layout,
        console_w=layout.root_cols,
        console_h=layout.root_rows,
    )
    # Content-hugging: well under max panel; 1-col vs 2-col jump stays modest
    assert image.size[0] < max_panel_w * 0.55
    one_col = render_proportional_list_dialog_image(
        "Inventory",
        items[:5],
        font=font,
        layout=layout,
        console_w=layout.root_cols,
        console_h=layout.root_rows,
    )
    two_col = image
    # 2-col wider than 1-col, but not a huge leap (≤ ~2.5×)
    assert two_col.size[0] > one_col.size[0]
    assert two_col.size[0] <= one_col.size[0] * 2.6


def test_inventory_list_item_rows_titles() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=44)
    player = engine.player
    assert player is not None
    inv = player.components[Inventory]
    inv.slots["a"] = _dagger()
    state = InventoryModalState(mode=InventoryModalMode.INSPECT_LIST)
    parts = inventory_list_item_rows(state, inv)
    assert parts is not None
    title, rows = parts
    assert title == "Inventory"
    assert any(r.startswith("a)") for r in rows)
