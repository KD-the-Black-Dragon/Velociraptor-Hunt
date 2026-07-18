"""PR2 engineering-maintainability: remaining message-log catalog coverage."""

from __future__ import annotations

from src import messages
from src.save.sanitize import SanitizeReport


def test_unknown_difficulty_wording() -> None:
    text = messages.unknown_difficulty_using_fallback("bogus", "Normal")
    assert text == "Unknown difficulty 'bogus'; using Normal."


def test_sanitize_summary_uses_messages_catalog() -> None:
    report = SanitizeReport(
        dropped_item_ids=["ghost_sword"],
        dropped_entity_ids=["ghost_wolf"],
        dropped_prefix_ids=["ghost_elite"],
    )
    text = report.summary_message()
    assert text == messages.save_sanitize_dropped(
        "; ".join(
            [
                messages.save_sanitize_detail_items("ghost_sword"),
                messages.save_sanitize_detail_creatures("ghost_wolf"),
                messages.save_sanitize_detail_prefixes("ghost_elite"),
            ]
        )
    )
    assert "no longer in the game" in text
    assert "ghost_sword" in text


def test_sanitize_summary_empty_parts_fallback() -> None:
    # any_dropped is false when lists empty; summary still well-formed if called
    report = SanitizeReport()
    text = report.summary_message()
    assert text == messages.save_sanitize_dropped(
        messages.save_sanitize_detail_fallback()
    )
