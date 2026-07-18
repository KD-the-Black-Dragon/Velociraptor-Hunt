"""UI log helpers used by menus/overlays (map render: match_render / reference/kdvr)."""

from __future__ import annotations

import attrs
import tcod.console

from src.log_markup import LogSegment, wrap_log_segments
from src.message_log import LogEntry, MessageCategory
from src.text import cp437_safe

MESSAGE_LOG_BACKGROUND = (20, 20, 30)
HUD_MESSAGE_LINES = 8


@attrs.define(frozen=True)
class LogDisplayLine:
    """One wrapped row in the HUD message log."""

    segments: tuple[LogSegment, ...]

    @property
    def text(self) -> str:
        return "".join(segment.text for segment in self.segments)

    @property
    def fg(self) -> tuple[int, int, int]:
        if not self.segments:
            return MessageCategory.ROUTINE.fg
        return self.segments[0].fg


def _wrap_words(text: str, *, max_inner: int) -> list[str]:
    if max_inner <= 0:
        return [text]
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_inner:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def wrap_log_text(text: str, *, width: int) -> list[str]:
    if not text:
        return []
    if width <= 0:
        return [text]
    lines: list[str] = []
    segments = text.split("\n")
    for segment_index, segment in enumerate(segments):
        if segment_index > 0:
            lines.append("")
        stripped = segment.strip()
        if not stripped:
            continue
        lines.extend(_wrap_words(stripped, max_inner=width))
    return lines


def expand_log_entries_to_display_lines(
    messages: list[LogEntry] | list[str] | None,
    *,
    width_limit: int,
) -> list[LogDisplayLine]:
    if not messages:
        return []
    display: list[LogDisplayLine] = []
    for entry in messages:
        if isinstance(entry, str):
            safe = cp437_safe(entry)
            wrapped = wrap_log_text(safe, width=width_limit)
            for line in wrapped:
                display.append(
                    LogDisplayLine(
                        segments=(LogSegment(text=line, fg=MessageCategory.ROUTINE.fg),)
                    )
                )
            continue
        for row in wrap_log_segments(entry.display_segments(), width=width_limit):
            if row:
                display.append(LogDisplayLine(segments=row))
    return display


def render_message_log(
    console: tcod.console.Console,
    messages: list[LogEntry] | list[str] | None,
    *,
    start_y: int = 0,
    line_limit: int | None = None,
    max_lines: int = HUD_MESSAGE_LINES,
) -> None:
    if not messages:
        return
    width_limit = line_limit if line_limit is not None else console.width - 2
    display_lines = expand_log_entries_to_display_lines(
        messages,
        width_limit=width_limit,
    )
    visible_lines = display_lines[-max_lines:]
    for index, line in enumerate(visible_lines):
        row = start_y + index
        if row >= console.height:
            break
        x = 1
        for segment in line.segments:
            remaining = width_limit - (x - 1)
            if remaining <= 0:
                break
            clipped = segment.text[:remaining]
            if not clipped:
                continue
            console.print(x, row, clipped, fg=segment.fg)
            x += len(clipped)


def render_message_log_panel(
    console: tcod.console.Console,
    messages: list[LogEntry] | list[str] | None,
    *,
    max_lines: int,
) -> None:
    console.draw_rect(
        0,
        0,
        console.width,
        console.height,
        ch=0,
        fg=None,
        bg=MESSAGE_LOG_BACKGROUND,
    )
    render_message_log(
        console,
        messages,
        start_y=0,
        line_limit=console.width - 2,
        max_lines=max_lines,
    )
