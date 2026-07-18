"""PR2: structured game-over endings."""

from __future__ import annotations

from src.game_over_ending import GameOverEnding, format_game_over_ending


def test_format_digested_ending() -> None:
    ending = GameOverEnding(kind="digested", detail="wolf")
    assert format_game_over_ending(ending) == "Digested by wolf"


def test_format_macguffin_ending_with_the_prefix() -> None:
    ending = GameOverEnding(kind="macguffin", detail="The Sword of Freedom")
    assert format_game_over_ending(ending) == "found The Sword of Freedom!"


def test_format_macguffin_ending_without_the_prefix() -> None:
    ending = GameOverEnding(kind="macguffin", detail="golden chalice")
    assert format_game_over_ending(ending) == "found the golden chalice!"


def test_format_boss_ending() -> None:
    ending = GameOverEnding(kind="boss")
    assert format_game_over_ending(ending) == "Defeated the boss"


def test_format_unknown_kind_falls_back_to_detail() -> None:
    ending = GameOverEnding(kind="custom", detail="Escaped the dungeon")
    assert format_game_over_ending(ending) == "Escaped the dungeon"