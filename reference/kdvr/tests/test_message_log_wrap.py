"""PR1: message log word wrap."""

from __future__ import annotations

from src.message_log import LogEntry, MessageCategory
from src.systems.render import (
    expand_log_entries_to_display_lines,
    render_message_log,
    wrap_log_text,
)

from tests.ui_test_helpers import make_console


def _cell_char(console, x: int, y: int) -> str:
    ch = int(console.rgba[x, y]["ch"])
    return chr(ch) if ch else " "


def _cell_fg(console, x: int, y: int) -> tuple[int, int, int]:
    return tuple(int(console.rgba[x, y]["fg"][index]) for index in range(3))


def test_wrap_log_text_splits_long_line() -> None:
    text = "one two three four five six seven eight nine"
    lines = wrap_log_text(text, width=12)
    assert len(lines) >= 2
    assert all(len(line) <= 12 for line in lines if line)
    assert " ".join(lines).split() == text.split()


def test_wrap_log_text_preserves_intentional_newlines() -> None:
    lines = wrap_log_text("first line\nsecond line", width=20)
    assert "" in lines
    assert "first line" in lines
    assert "second line" in lines


def test_expand_log_entries_inherits_fg_on_wrapped_sub_lines() -> None:
    entry = LogEntry(
        "alpha bravo charlie delta echo foxtrot golf hotel",
        category=MessageCategory.DANGER,
    )
    display = expand_log_entries_to_display_lines([entry], width_limit=10)
    assert len(display) >= 2
    assert all(line.fg == MessageCategory.DANGER.fg for line in display)


def test_render_message_log_shows_wrapped_tail() -> None:
    width_limit = 20
    console = make_console(24, 4)
    long_text = (
        "You examine the ancient rune-covered door and wonder what lies beyond "
        "the threshold."
    )
    render_message_log(
        console,
        [LogEntry(long_text)],
        line_limit=width_limit,
        max_lines=4,
    )

    rows = [
        "".join(_cell_char(console, x, y) for x in range(console.width)).strip()
        for y in range(4)
    ]
    rendered = " ".join(part for part in rows if part)
    assert "threshold" in rendered
    assert "ancient" in rendered
    assert len(rendered) > width_limit


def test_render_message_log_prefers_recent_wrapped_lines() -> None:
    console = make_console(24, 3)
    render_message_log(
        console,
        [
            LogEntry("first short"),
            LogEntry(
                "second message wraps across many words in the log panel area here"
            ),
        ],
        line_limit=12,
        max_lines=3,
    )

    rows = [
        "".join(_cell_char(console, x, y) for x in range(console.width)).strip()
        for y in range(3)
    ]
    combined = "\n".join(rows)
    assert "first short" not in combined
    assert "panel area" in combined or "log panel" in combined