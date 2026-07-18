"""Structured endings for Past Runs / recap labels (Gladiavore product)."""

from __future__ import annotations

import attrs


@attrs.define(frozen=True)
class GameOverEnding:
    """Machine-readable ending; format for UI via ``format_game_over_ending``."""

    kind: str
    detail: str = ""


def format_game_over_ending(ending: GameOverEnding) -> str:
    """Render the recap line shown on game over and in Past Runs."""
    match ending.kind:
        case "digested":
            return f"Digested by {ending.detail}"
        case "macguffin":
            detail = ending.detail
            if detail.startswith("The "):
                return f"found {detail}!"
            return f"found the {detail}!"
        case "boss":
            return "Defeated the boss"
        case "career_end":
            return ending.detail or "Career ended"
        case _:
            return ending.detail or ending.kind
