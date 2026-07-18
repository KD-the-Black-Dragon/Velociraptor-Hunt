"""Sidebar NPC band planning: columns, overflow, and height budgeting."""

from __future__ import annotations

from src.ui.layout import SidebarLayout
from src.ui.sidebar_npc_layout import (
    column_first_split,
    entry_slot,
    interleaved_split,
    plan_band,
    resolve_npc_bands,
    vertical_rows_for_split,
)


def _sidebar(**overrides: int) -> SidebarLayout:
    defaults = {
        "hp_bar_width": 9,
        "npc_hp_bar_width": 6,
        "max_evil": 10,
        "max_good": 4,
        "evil_per_column": 5,
        "good_per_column": 2,
        "player_top_pad": 1,
        "player_bottom_pad": 1,
        "good_bottom_pad": 2,
        "rows_per_npc": 3,
    }
    defaults.update(overrides)
    return SidebarLayout(**defaults)


def test_plan_band_single_column_when_five_or_fewer() -> None:
    plan = plan_band(
        3,
        30,
        per_column_max=5,
        total_cap=10,
        entry_rows=3,
    )
    assert plan.column_count == 1
    assert plan.display_count == 3
    assert plan.overflow_count == 0
    assert plan.col0_count == 3
    assert plan.col1_count == 0
    assert not plan.truncate_names


def test_plan_band_second_column_when_more_than_five() -> None:
    plan = plan_band(
        7,
        30,
        per_column_max=5,
        total_cap=10,
        entry_rows=3,
    )
    assert plan.column_count == 2
    assert plan.display_count == 7
    assert plan.overflow_count == 0
    assert plan.col0_count == 5
    assert plan.col1_count == 2
    assert plan.truncate_names


def test_plan_band_overflow_when_more_than_two_columns_can_show() -> None:
    plan = plan_band(
        12,
        30,
        per_column_max=5,
        total_cap=10,
        entry_rows=3,
    )
    assert plan.display_count == 10
    assert plan.overflow_count == 2


def test_column_first_split_uses_parallel_columns_when_vertically_tight() -> None:
    col0, col1 = column_first_split(
        5,
        column_count=2,
        per_column_max=2,
        row_slots=1,
    )
    assert col0 == 1
    assert col1 == 1
    assert vertical_rows_for_split(col0, col1, entry_rows=3) == 3


def test_plan_band_two_columns_parallel_row_uses_both_columns() -> None:
    plan = plan_band(
        5,
        4,
        per_column_max=2,
        total_cap=4,
        entry_rows=3,
    )
    assert plan.column_count == 2
    assert plan.display_count == 2
    assert plan.overflow_count == 3
    assert plan.col0_count == 1
    assert plan.col1_count == 1


def test_plan_band_keeps_overflow_row_when_height_is_tight() -> None:
    plan = plan_band(
        10,
        7,
        per_column_max=5,
        total_cap=10,
        entry_rows=3,
    )
    assert plan.display_count == 4
    assert plan.overflow_count == 6
    assert plan.rows_used == 7
    assert plan.col0_count == 2
    assert plan.col1_count == 2


def test_resolve_npc_bands_overflow_survives_short_sidebar() -> None:
    sidebar = _sidebar()
    player_rows = sidebar.player_top_pad + 2 + sidebar.player_bottom_pad
    height = player_rows + 7 + sidebar.good_bottom_pad
    evil_plan, good_plan, good_band_top = resolve_npc_bands(
        height=height,
        player_rows=player_rows,
        sidebar=sidebar,
        evil_count=10,
        good_count=0,
    )
    assert evil_plan.display_count == 4
    assert evil_plan.overflow_count == 6
    assert good_band_top == player_rows + evil_plan.rows_used


def test_plan_band_never_reserves_empty_second_column_across_heights() -> None:
    for available_rows in range(4, 25):
        plan = plan_band(
            8,
            available_rows,
            per_column_max=5,
            total_cap=10,
            entry_rows=3,
        )
        if plan.column_count == 2:
            assert plan.col1_count > 0


def test_plan_band_prefers_two_columns_when_parallel_shows_more_entries() -> None:
    plan = plan_band(
        6,
        7,
        per_column_max=5,
        total_cap=10,
        entry_rows=3,
    )
    assert plan.column_count == 2
    assert plan.col1_count > 0
    assert plan.display_count == 4


def test_interleaved_split_balances_parallel_columns() -> None:
    col0, col1 = interleaved_split(6, per_column_max=5, row_slots=3)
    assert col0 == 3
    assert col1 == 3


def test_entry_slot_interleaved_alternates_columns_by_row() -> None:
    assert entry_slot(0, col0_count=3, interleaved_fill=True) == (0, 0)
    assert entry_slot(1, col0_count=3, interleaved_fill=True) == (1, 0)
    assert entry_slot(2, col0_count=3, interleaved_fill=True) == (0, 1)
    assert entry_slot(5, col0_count=3, interleaved_fill=True) == (1, 2)


def test_resolve_npc_bands_uses_both_columns_at_dead_band_heights() -> None:
    """Regression: pixel heights 816–839 and 888–911 must not collapse to one column."""
    sidebar = _sidebar()
    player_rows = sidebar.player_top_pad + 2 + sidebar.player_bottom_pad
    cell_px = 24

    for pixel_h in range(816, 840):
        side_h = pixel_h // cell_px - 10
        evil_plan, _, _ = resolve_npc_bands(
            height=side_h,
            player_rows=player_rows,
            sidebar=sidebar,
            evil_count=9,
            good_count=2,
        )
        assert evil_plan.column_count == 2
        assert evil_plan.col1_count > 0
        assert evil_plan.display_count == 6

    for pixel_h in range(888, 912):
        side_h = pixel_h // cell_px - 10
        evil_plan, _, _ = resolve_npc_bands(
            height=side_h,
            player_rows=player_rows,
            sidebar=sidebar,
            evil_count=11,
            good_count=2,
        )
        assert evil_plan.column_count == 2
        assert evil_plan.col1_count > 0
        assert evil_plan.display_count == 8


def test_resolve_npc_bands_evil_and_good_do_not_share_vertical_space() -> None:
    sidebar = _sidebar()
    player_rows = sidebar.player_top_pad + 2 + sidebar.player_bottom_pad
    height = player_rows + 12 + sidebar.good_bottom_pad
    evil_plan, good_plan, good_band_top = resolve_npc_bands(
        height=height,
        player_rows=player_rows,
        sidebar=sidebar,
        evil_count=6,
        good_count=4,
    )
    assert evil_plan.rows_used + good_plan.rows_used <= height - player_rows - sidebar.good_bottom_pad
    assert good_band_top >= player_rows + evil_plan.rows_used