from __future__ import annotations

import re

import attrs

from src.log_categories import MessageCategory


@attrs.define(frozen=True)
class LogSegment:
    text: str
    fg: tuple[int, int, int]

_CATEGORY_ALIASES: dict[str, MessageCategory] = {
    "routine": MessageCategory.ROUTINE,
    "grey": MessageCategory.ROUTINE,
    "gray": MessageCategory.ROUTINE,
    "danger": MessageCategory.DANGER,
    "red": MessageCategory.DANGER,
    "caution": MessageCategory.CAUTION,
    "yellow": MessageCategory.CAUTION,
    "positive": MessageCategory.POSITIVE,
    "green": MessageCategory.POSITIVE,
    "magical": MessageCategory.MAGICAL,
    "cyan": MessageCategory.MAGICAL,
    "speech": MessageCategory.SPEECH,
    "white": MessageCategory.SPEECH,
    "rare": MessageCategory.RARE,
    "magenta": MessageCategory.RARE,
}

_MARKUP_TAG_RE = re.compile(r"\[\[([^\]]+)\]\]")


def category_from_log_name(name: str | None) -> MessageCategory | None:
    """Resolve a data-file log category name, or None when unknown or unset."""
    if name is None:
        return None
    normalized = name.strip().lower()
    if not normalized:
        return None
    return _CATEGORY_ALIASES.get(normalized)


def parse_log_category_field(raw: object, *, context: str) -> MessageCategory | None:
    """Parse optional entity JSON log category fields."""
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{context}: log category must be a non-empty string")
    category = category_from_log_name(raw)
    if category is None:
        raise ValueError(
            f"{context}: unknown log category '{raw}' "
            f"(known: {', '.join(sorted(_CATEGORY_ALIASES))})"
        )
    return category


def _fg_for_tag(tag: str, *, default_fg: tuple[int, int, int]) -> tuple[int, int, int] | None:
    normalized = tag.strip().lower()
    if normalized == "/":
        return default_fg
    category = _CATEGORY_ALIASES.get(normalized)
    if category is None:
        return None
    return category.fg


def _coalesce_segments(segments: list[LogSegment]) -> tuple[LogSegment, ...]:
    if not segments:
        return ()
    merged: list[LogSegment] = [segments[0]]
    for segment in segments[1:]:
        last = merged[-1]
        if last.fg == segment.fg:
            merged[-1] = LogSegment(text=last.text + segment.text, fg=last.fg)
        else:
            merged.append(segment)
    return tuple(merged)


def parse_log_markup(
    text: str,
    *,
    default_category: MessageCategory = MessageCategory.ROUTINE,
) -> tuple[str, tuple[LogSegment, ...]]:
    """Parse ``[[category]]...[[/]]`` markup into plain text and colored segments."""
    if not text:
        return "", ()

    default_fg = default_category.fg
    current_fg = default_fg
    segments: list[LogSegment] = []
    plain_parts: list[str] = []
    buffer = ""
    index = 0

    while index < len(text):
        if text.startswith("[[/]]", index):
            if buffer:
                segments.append(LogSegment(text=buffer, fg=current_fg))
                plain_parts.append(buffer)
                buffer = ""
            current_fg = default_fg
            index += 5
            continue

        if text.startswith("[[", index):
            close = text.find("]]", index + 2)
            if close == -1:
                buffer += text[index]
                index += 1
                continue
            tag = text[index + 2 : close]
            next_fg = _fg_for_tag(tag, default_fg=default_fg)
            if next_fg is None:
                literal = text[index : close + 2]
                buffer += literal
                index = close + 2
                continue
            if buffer:
                segments.append(LogSegment(text=buffer, fg=current_fg))
                plain_parts.append(buffer)
                buffer = ""
            current_fg = next_fg
            index = close + 2
            continue

        buffer += text[index]
        index += 1

    if buffer:
        segments.append(LogSegment(text=buffer, fg=current_fg))
        plain_parts.append(buffer)

    plain = "".join(plain_parts)
    if not segments:
        return plain, (LogSegment(text=plain, fg=default_fg),)
    return plain, _coalesce_segments(segments)


def wrap_log_segments(
    segments: tuple[LogSegment, ...],
    *,
    width: int,
) -> list[tuple[LogSegment, ...]]:
    """Word-wrap colored segments to ``width`` without splitting words."""
    if not segments or width <= 0:
        return [segments]
    rows: list[tuple[LogSegment, ...]] = []

    def flush_row(parts: list[tuple[str, tuple[int, int, int]]]) -> None:
        if not parts:
            return
        coalesced: list[LogSegment] = []
        for word, fg in parts:
            prefix = "" if not coalesced else " "
            piece = prefix + word
            if coalesced and coalesced[-1].fg == fg:
                last = coalesced[-1]
                coalesced[-1] = LogSegment(text=last.text + piece, fg=fg)
            else:
                coalesced.append(LogSegment(text=piece, fg=fg))
        rows.append(tuple(coalesced))

    logical_lines: list[list[tuple[str, tuple[int, int, int]]]] = [[]]
    for segment in segments:
        parts = segment.text.split("\n")
        for line_index, line in enumerate(parts):
            if line_index > 0:
                logical_lines.append([])
            for word in line.split():
                if word:
                    logical_lines[-1].append((word, segment.fg))

    for line_words in logical_lines:
        row_parts: list[tuple[str, tuple[int, int, int]]] = []
        row_len = 0
        for word, fg in line_words:
            extra = len(word) + (1 if row_parts else 0)
            if row_parts and row_len + extra > width:
                flush_row(row_parts)
                row_parts = [(word, fg)]
                row_len = len(word)
            else:
                row_parts.append((word, fg))
                row_len += extra
        flush_row(row_parts)

    return rows or [segments]