"""PR3: inline log markup and rich message log rendering."""

from __future__ import annotations

from src.log_categories import MessageCategory
from src.log_markup import (
    LogSegment,
    category_from_log_name,
    parse_log_markup,
    wrap_log_segments,
)
from src.message_log import MessageLog
from src.systems.render import expand_log_entries_to_display_lines, render_message_log

from tests.ui_test_helpers import make_console


def _cell_fg(console, x: int, y: int) -> tuple[int, int, int]:
    return tuple(int(console.rgba[x, y]["fg"][index]) for index in range(3))


def test_parse_log_markup_colored_span() -> None:
    plain, segments = parse_log_markup(
        "The wolf [[magical]]glows[[/]] brightly.",
        default_category=MessageCategory.ROUTINE,
    )
    assert plain == "The wolf glows brightly."
    assert len(segments) == 3
    assert segments[0] == LogSegment("The wolf ", MessageCategory.ROUTINE.fg)
    assert segments[1] == LogSegment("glows", MessageCategory.MAGICAL.fg)
    assert segments[2] == LogSegment(" brightly.", MessageCategory.ROUTINE.fg)


def test_parse_log_markup_unknown_tag_stays_literal() -> None:
    plain, segments = parse_log_markup(
        "[[not_a_real_category]] stays",
        default_category=MessageCategory.ROUTINE,
    )
    assert "[[not_a_real_category]]" in plain
    assert len(segments) == 1


def test_message_log_add_parses_inline_markup() -> None:
    log = MessageLog()
    log.add(
        "Hello [[speech]]friend[[/]]!",
        category=MessageCategory.ROUTINE,
    )
    entry = log.entries()[0]
    assert entry.text == "Hello friend!"
    assert len(entry.segments) == 3
    assert entry.segments[1].fg == MessageCategory.SPEECH.fg


def test_wrap_log_segments_preserves_colors() -> None:
    _, segments = parse_log_markup(
        "one two [[danger]]three four[[/]] five",
        default_category=MessageCategory.ROUTINE,
    )
    rows = wrap_log_segments(segments, width=8)
    assert len(rows) >= 2
    danger_rows = [seg for row in rows for seg in row if seg.fg == MessageCategory.DANGER.fg]
    assert danger_rows
    assert "three" in danger_rows[0].text or "four" in danger_rows[0].text


def test_render_message_log_draws_multiple_colors_on_one_row() -> None:
    log = MessageLog()
    log.add(
        "Alpha [[positive]]healed[[/]] beta.",
        category=MessageCategory.ROUTINE,
    )
    console = make_console(30, 2)
    render_message_log(
        console,
        log.entries(),
        line_limit=28,
        max_lines=2,
    )
    assert _cell_fg(console, 1, 0) == MessageCategory.ROUTINE.fg
    healed_x = "Alpha healed beta.".index("healed") + 1
    assert _cell_fg(console, healed_x, 0) == MessageCategory.POSITIVE.fg


def test_expand_log_entries_wraps_rich_segments() -> None:
    log = MessageLog()
    log.add(
        "short [[magical]]longwordhighlight[[/]] tail",
        category=MessageCategory.ROUTINE,
    )
    rows = expand_log_entries_to_display_lines(log.entries(), width_limit=10)
    assert rows
    combined = "".join(seg.text for seg in rows[-1].segments)
    assert "tail" in combined or "longwordhighlight" in combined


def test_category_from_log_name_supports_speech_alias() -> None:
    assert category_from_log_name("speech") is MessageCategory.SPEECH
    assert category_from_log_name("white") is MessageCategory.SPEECH