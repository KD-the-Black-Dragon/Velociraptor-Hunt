"""CP437-safe text normalization for HUD and logs."""

from __future__ import annotations

from src.message_log import MessageLog
from src.text import cp437_safe


def test_cp437_safe_replaces_em_dash() -> None:
    assert cp437_safe("wolf - prey") == "wolf - prey"
    assert cp437_safe("wolf \u2014 prey") == "wolf  -  prey"


def test_message_log_stores_cp437_safe_text() -> None:
    log = MessageLog()
    log.add("The wolf burps triumphantly \u2014 the knight has been digested.")
    assert log.lines()[0] == "The wolf burps triumphantly  -  the knight has been digested."