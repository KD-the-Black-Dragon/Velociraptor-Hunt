"""Full-screen scrollable Past Runs table (main menu)."""

from __future__ import annotations

from enum import Enum, auto

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym

from src.game_over_ending import GameOverEnding, format_game_over_ending
from src.input_handlers import (
    LOG_OVERLAY_LINE_DOWN_KEYS,
    LOG_OVERLAY_LINE_UP_KEYS,
    LOG_OVERLAY_PAGE_DOWN_KEYS,
    LOG_OVERLAY_PAGE_UP_KEYS,
)
from src.past_runs.schema import PastRunRecord
from src.systems.render import MESSAGE_LOG_BACKGROUND
from src.text import cp437_safe
from src.ui.log_overlay import (
    apply_line_scroll,
    apply_page_scroll,
    clamp_scroll_offset,
)

PAST_RUNS_TITLE = "PAST RUNS"
PAST_RUNS_FOOTER = "Esc: back | Arrows: line | PgUp/PgDn: page"
PAST_RUNS_TITLE_FG = (255, 220, 120)
PAST_RUNS_ROW_FG = (220, 220, 210)
PAST_RUNS_FOOTER_FG = (160, 160, 170)


class PastRunsAction(Enum):
    """Outcome of Past Runs screen input."""

    NONE = auto()
    BACK = auto()


@attrs.define
class PastRunsScreenState:
    """Scroll state for the Past Runs table."""

    scroll_offset: int = 0

    def reset(self) -> None:
        self.scroll_offset = 0


def format_past_run_summary_line(record: PastRunRecord) -> str:
    ending = GameOverEnding(kind=record.ending_kind, detail=record.ending_detail)
    ending_text = format_game_over_ending(ending)
    return f"{record.character_name} - {ending_text} - {record.date}"


def format_past_run_stats_line(record: PastRunRecord) -> str:
    difficulty = record.difficulty_display or record.difficulty_id
    if difficulty:
        return (
            f"{difficulty} - Depth {record.depth} - {record.runes_collected} Runes - "
            f"{record.monsters_defeated} Enemies Defeated"
        )
    return (
        f"Depth {record.depth} - {record.runes_collected} Runes - "
        f"{record.monsters_defeated} Enemies Defeated"
    )


def build_past_runs_display_lines(records: list[PastRunRecord]) -> list[str]:
    """Title, blank line, then two lines per run separated by blanks (pre-sorted)."""
    lines: list[str] = [PAST_RUNS_TITLE]
    if not records:
        return lines
    lines.append("")
    for index, record in enumerate(records):
        lines.append(format_past_run_summary_line(record))
        lines.append(format_past_run_stats_line(record))
        if index < len(records) - 1:
            lines.append("")
    return lines


def truncate_line(line: str, *, width: int) -> str:
    if width <= 0:
        return ""
    safe = cp437_safe(line)
    if len(safe) <= width:
        return safe
    if width <= 1:
        return safe[:width]
    return safe[: width - 1] + "…"


def past_runs_viewport_lines(console_height: int) -> int:
    """Visible lines excluding the footer row."""
    return max(1, console_height - 1)


def handle_past_runs_event(
    state: PastRunsScreenState,
    event: tcod.event.Event,
    *,
    line_count: int,
    viewport_lines: int,
) -> PastRunsAction:
    """Handle Past Runs input."""
    if not isinstance(event, tcod.event.KeyDown):
        return PastRunsAction.NONE

    sym = event.sym
    if sym == KeySym.ESCAPE:
        return PastRunsAction.BACK
    if sym in LOG_OVERLAY_LINE_UP_KEYS:
        state.scroll_offset = apply_line_scroll(
            state.scroll_offset,
            -1,
            line_count=line_count,
            viewport_lines=viewport_lines,
        )
        return PastRunsAction.NONE
    if sym in LOG_OVERLAY_LINE_DOWN_KEYS:
        state.scroll_offset = apply_line_scroll(
            state.scroll_offset,
            1,
            line_count=line_count,
            viewport_lines=viewport_lines,
        )
        return PastRunsAction.NONE
    if sym in LOG_OVERLAY_PAGE_UP_KEYS:
        state.scroll_offset = apply_page_scroll(
            state.scroll_offset,
            -1,
            line_count=line_count,
            viewport_lines=viewport_lines,
        )
        return PastRunsAction.NONE
    if sym in LOG_OVERLAY_PAGE_DOWN_KEYS:
        state.scroll_offset = apply_page_scroll(
            state.scroll_offset,
            1,
            line_count=line_count,
            viewport_lines=viewport_lines,
        )
        return PastRunsAction.NONE
    return PastRunsAction.NONE


def render_past_runs_screen(
    console: tcod.console.Console,
    records: list[PastRunRecord],
    state: PastRunsScreenState,
) -> None:
    """Draw the scrollable Past Runs table on the root console."""
    console.clear(bg=MESSAGE_LOG_BACKGROUND)
    display_lines = build_past_runs_display_lines(records)
    line_count = len(display_lines)
    viewport_lines = past_runs_viewport_lines(console.height)
    state.scroll_offset = clamp_scroll_offset(
        state.scroll_offset,
        line_count=line_count,
        viewport_lines=viewport_lines,
    )
    visible = display_lines[
        state.scroll_offset : state.scroll_offset + viewport_lines
    ]
    text_width = max(1, console.width - 2)
    for row_index, line in enumerate(visible):
        clipped = truncate_line(line, width=text_width)
        if line == PAST_RUNS_TITLE:
            fg = PAST_RUNS_TITLE_FG
        else:
            fg = PAST_RUNS_ROW_FG
        console.print(1, row_index, clipped, fg=fg)

    footer = cp437_safe(PAST_RUNS_FOOTER)
    footer_x = max(1, (console.width - len(footer)) // 2)
    console.print(
        footer_x,
        console.height - 1,
        footer[: console.width - 2],
        fg=PAST_RUNS_FOOTER_FG,
    )