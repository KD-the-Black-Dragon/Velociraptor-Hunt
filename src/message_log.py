from __future__ import annotations

from collections import deque

import attrs

from src.constants import MESSAGE_LOG_CAPACITY
from src.log_categories import (
    ALERT_MESSAGE_FG,
    DEFAULT_MESSAGE_FG,
    MessageCategory,
)
from src.log_markup import LogSegment, parse_log_markup
from src.text import cp437_safe

__all__ = [
    "ALERT_MESSAGE_FG",
    "DEFAULT_MESSAGE_FG",
    "LogEntry",
    "LogSegment",
    "MessageCategory",
    "MessageLog",
]


@attrs.define(frozen=True)
class LogEntry:
    text: str
    category: MessageCategory = MessageCategory.ROUTINE
    segments: tuple[LogSegment, ...] = ()

    @property
    def fg(self) -> tuple[int, int, int]:
        return self.category.fg

    def display_segments(self) -> tuple[LogSegment, ...]:
        if self.segments:
            return self.segments
        return (LogSegment(text=self.text, fg=self.category.fg),)


class MessageLog:
    """Fixed-size scrolling log for HUD messages."""

    def __init__(self, max_messages: int = MESSAGE_LOG_CAPACITY) -> None:
        self._messages: deque[LogEntry] = deque(maxlen=max_messages)

    def add(
        self,
        text: str,
        *,
        category: MessageCategory = MessageCategory.ROUTINE,
    ) -> None:
        if text:
            safe = cp437_safe(text)
            plain, segments = parse_log_markup(safe, default_category=category)
            self._messages.append(
                LogEntry(text=plain, category=category, segments=segments)
            )

    def lines(self) -> list[str]:
        return [entry.text for entry in self._messages]

    def entries(self) -> list[LogEntry]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()