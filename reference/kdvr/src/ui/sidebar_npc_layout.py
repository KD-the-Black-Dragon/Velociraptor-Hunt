from __future__ import annotations

import attrs

from src.ui.layout import SidebarLayout

COLUMN_GAP = 1


@attrs.define(frozen=True)
class BandLayout:
    column_count: int
    display_count: int
    overflow_count: int
    rows_used: int
    truncate_names: bool
    col0_count: int
    col1_count: int
    interleaved_fill: bool = False


def column_first_split(
    count: int,
    *,
    column_count: int,
    per_column_max: int,
    row_slots: int,
) -> tuple[int, int]:
    """Split visible entries column-first; each column capped by count and row_slots."""
    if count <= 0 or row_slots <= 0:
        return 0, 0
    col0 = min(per_column_max, row_slots, count)
    remaining = count - col0
    col1 = 0
    if column_count > 1 and remaining > 0:
        col1 = min(per_column_max, row_slots, remaining)
    return col0, col1


def interleaved_split(
    display_count: int,
    *,
    per_column_max: int,
    row_slots: int,
) -> tuple[int, int]:
    """Split entries row-by-row across parallel columns (index 0→col0, 1→col1, 2→col0, …)."""
    if display_count <= 0 or row_slots <= 0:
        return 0, 0
    cap = min(row_slots, per_column_max)
    col0 = min(cap, (display_count + 1) // 2)
    col1 = min(cap, display_count // 2)
    return col0, col1


def vertical_rows_for_split(
    col0_count: int,
    col1_count: int,
    *,
    entry_rows: int,
) -> int:
    if col0_count <= 0 and col1_count <= 0:
        return 0
    return max(col0_count, col1_count) * entry_rows


def column_geometry(console_width: int, column_count: int) -> list[tuple[int, int]]:
    """Return (x, line_limit) for each column."""
    inner = max(1, console_width - 2)
    if column_count <= 1:
        return [(1, inner)]
    col_w = max(1, (inner - COLUMN_GAP) // 2)
    return [(1, col_w), (1 + col_w + COLUMN_GAP, col_w)]


def _shrink_split(
    col0_count: int,
    col1_count: int,
) -> tuple[int, int]:
    if col1_count > 0:
        return col0_count, col1_count - 1
    if col0_count > 0:
        return col0_count - 1, 0
    return 0, 0


def _make_band(
    columns: int,
    *,
    col0: int,
    col1: int,
    total_count: int,
    entry_rows: int,
    interleaved_fill: bool = False,
) -> BandLayout:
    display = col0 + col1
    overflow = total_count - display
    vert = vertical_rows_for_split(col0, col1, entry_rows=entry_rows)
    rows_used = vert + (1 if overflow > 0 else 0)
    use_two_columns = columns > 1 and col1 > 0
    return BandLayout(
        2 if use_two_columns else 1,
        display,
        overflow,
        rows_used,
        truncate_names=use_two_columns,
        col0_count=col0,
        col1_count=col1 if use_two_columns else 0,
        interleaved_fill=interleaved_fill and use_two_columns,
    )


def _fit_column_first(
    total_count: int,
    available_rows: int,
    *,
    columns: int,
    per_column_max: int,
    capped_total: int,
    entry_rows: int,
) -> BandLayout:
    row_slots = available_rows // entry_rows
    col0, col1 = column_first_split(
        capped_total,
        column_count=columns,
        per_column_max=per_column_max,
        row_slots=row_slots,
    )
    display = col0 + col1

    while display > 0:
        overflow = total_count - display
        vert = vertical_rows_for_split(col0, col1, entry_rows=entry_rows)
        rows_needed = vert + (1 if overflow > 0 else 0)
        if rows_needed <= available_rows:
            break
        col0, col1 = _shrink_split(col0, col1)
        display = col0 + col1

    return _make_band(
        columns,
        col0=col0,
        col1=col1,
        total_count=total_count,
        entry_rows=entry_rows,
        interleaved_fill=False,
    )


def _fit_interleaved(
    total_count: int,
    available_rows: int,
    *,
    per_column_max: int,
    capped_total: int,
    entry_rows: int,
) -> BandLayout:
    row_slots = available_rows // entry_rows
    display = min(capped_total, row_slots * 2, per_column_max * 2)

    while display > 0:
        col0, col1 = interleaved_split(
            display,
            per_column_max=per_column_max,
            row_slots=row_slots,
        )
        overflow = total_count - display
        vert = vertical_rows_for_split(col0, col1, entry_rows=entry_rows)
        rows_needed = vert + (1 if overflow > 0 else 0)
        if rows_needed <= available_rows:
            return _make_band(
                2,
                col0=col0,
                col1=col1,
                total_count=total_count,
                entry_rows=entry_rows,
                interleaved_fill=True,
            )
        display -= 1

    return BandLayout(1, 0, total_count, 0, False, 0, 0, False)


def _pick_split_plan(
    column_first: BandLayout,
    interleaved: BandLayout,
) -> BandLayout:
    if interleaved.col1_count == 0:
        return column_first
    if interleaved.display_count > column_first.display_count:
        return interleaved
    if column_first.display_count > interleaved.display_count:
        return column_first
    if column_first.col1_count == 0:
        return interleaved
    return column_first


def _fit_band(
    total_count: int,
    available_rows: int,
    *,
    columns: int,
    per_column_max: int,
    capped_total: int,
    entry_rows: int,
) -> BandLayout:
    column_first = _fit_column_first(
        total_count,
        available_rows,
        columns=columns,
        per_column_max=per_column_max,
        capped_total=capped_total,
        entry_rows=entry_rows,
    )
    if columns <= 1:
        return column_first

    interleaved = _fit_interleaved(
        total_count,
        available_rows,
        per_column_max=per_column_max,
        capped_total=capped_total,
        entry_rows=entry_rows,
    )
    return _pick_split_plan(column_first, interleaved)


def _pick_band_plan(
    single: BandLayout,
    two: BandLayout,
    *,
    capped_total: int,
    per_column_max: int,
) -> BandLayout:
    if two.col1_count == 0:
        return single
    if two.display_count > single.display_count:
        return two
    if single.display_count > two.display_count:
        return single
    if two.rows_used < single.rows_used:
        return two
    if capped_total > per_column_max:
        return two
    return single


def plan_band(
    total_count: int,
    available_rows: int,
    *,
    per_column_max: int,
    total_cap: int,
    entry_rows: int,
) -> BandLayout:
    """Plan one alignment band (evil or good) within a row budget."""
    if total_count <= 0:
        return BandLayout(1, 0, 0, 0, False, 0, 0)

    capped_total = min(total_count, total_cap)
    if available_rows <= 0:
        return BandLayout(1, 0, total_count, 0, False, 0, 0)

    row_slots = available_rows // entry_rows
    if row_slots <= 0:
        return BandLayout(1, 0, total_count, 1, False, 0, 0)

    single = _fit_band(
        total_count,
        available_rows,
        columns=1,
        per_column_max=per_column_max,
        capped_total=capped_total,
        entry_rows=entry_rows,
    )
    if single.overflow_count == 0 and single.display_count >= capped_total:
        return single

    two = _fit_band(
        total_count,
        available_rows,
        columns=2,
        per_column_max=per_column_max,
        capped_total=capped_total,
        entry_rows=entry_rows,
    )
    return _pick_band_plan(
        single,
        two,
        capped_total=capped_total,
        per_column_max=per_column_max,
    )


def resolve_npc_bands(
    *,
    height: int,
    player_rows: int,
    sidebar: SidebarLayout,
    evil_count: int,
    good_count: int,
) -> tuple[BandLayout, BandLayout, int]:
    """Return evil plan, good plan, and the first row of the good band."""
    middle_rows = max(0, height - player_rows - sidebar.good_bottom_pad)

    good_plan = plan_band(
        good_count,
        middle_rows,
        per_column_max=sidebar.good_per_column,
        total_cap=sidebar.max_good,
        entry_rows=sidebar.rows_per_npc,
    )
    evil_available = max(0, middle_rows - good_plan.rows_used)
    evil_plan = plan_band(
        evil_count,
        evil_available,
        per_column_max=sidebar.evil_per_column,
        total_cap=sidebar.max_evil,
        entry_rows=sidebar.rows_per_npc,
    )

    good_available = max(0, middle_rows - evil_plan.rows_used)
    if good_plan.rows_used > good_available:
        good_plan = plan_band(
            good_count,
            good_available,
            per_column_max=sidebar.good_per_column,
            total_cap=sidebar.max_good,
            entry_rows=sidebar.rows_per_npc,
        )

    good_band_top = height - sidebar.good_bottom_pad - good_plan.rows_used
    return evil_plan, good_plan, good_band_top


def entry_slot(
    index: int,
    *,
    col0_count: int,
    interleaved_fill: bool = False,
) -> tuple[int, int]:
    """Map display index to (column_index, row_slot_within_column)."""
    if interleaved_fill:
        return index % 2, index // 2
    if index < col0_count:
        return 0, index
    return 1, index - col0_count