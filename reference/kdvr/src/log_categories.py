from __future__ import annotations

from enum import Enum


class MessageCategory(Enum):
    """Log message color categories (stock RGB per fix-deferred-bugfixes design)."""

    ROUTINE = (192, 192, 192)
    DANGER = (255, 80, 80)
    CAUTION = (255, 220, 80)
    POSITIVE = (80, 220, 120)
    MAGICAL = (100, 220, 255)
    SPEECH = (255, 255, 255)
    RARE = (255, 100, 255)

    @property
    def fg(self) -> tuple[int, int, int]:
        return self.value


DEFAULT_MESSAGE_FG: tuple[int, int, int] = MessageCategory.ROUTINE.fg
ALERT_MESSAGE_FG: tuple[int, int, int] = MessageCategory.DANGER.fg