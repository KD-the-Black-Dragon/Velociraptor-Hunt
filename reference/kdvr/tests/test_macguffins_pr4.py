"""PR4: macguffin victory game over, digestion override, past-run score."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.data.macguffin_loader import load_macguffin_registry
from src.engine import GameEngine
from src.game_over_ending import GameOverEnding, format_game_over_ending
from src.past_runs.store import PastRunsStore
from src.save.snapshot import build_run_snapshot
from src.systems.digestion import GameOverState
from tests.test_digestion import (
    _advance_digestion_modal,
    _engulf_player_on_wolf,
    _press,
)
from tests.test_macguffins_pr3 import _press as press_macguffin
from tests.test_macguffins_pr3 import _setup_macguffin_step_on


def _key(sym: KeySym, *, mod: Modifier = Modifier.NONE) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def test_confirm_macguffin_victory_formats_ending_with_article_rule() -> None:
    engine = GameEngine()
    _setup_macguffin_step_on(engine)
    press_macguffin(engine, KeySym.RIGHT)
    press_macguffin(engine, KeySym.Y, mod=Modifier.SHIFT)

    assert engine.game_over.ending is not None
    assert (
        format_game_over_ending(engine.game_over.ending)
        == "found The Sword of Freedom!"
    )


def test_confirm_macguffin_victory_appends_past_run_with_score(
    tmp_path: Path,
) -> None:
    store = PastRunsStore(tmp_path / "past_runs.json")
    engine = GameEngine()
    engine.past_runs_store = store
    engine.run_stats.monsters_defeated = 2
    engine.run_stats.runes_collected = 1
    engine.floor_depth = 6
    _setup_macguffin_step_on(engine)
    press_macguffin(engine, KeySym.RIGHT)

    with patch("src.past_runs.store.today_display_date", return_value="07/06/2026"):
        press_macguffin(engine, KeySym.Y, mod=Modifier.SHIFT)

    loaded = store.load_runs()
    assert len(loaded) == 1
    record = loaded[0]
    assert record.ending_kind == "macguffin"
    assert record.ending_detail == "The Sword of Freedom"
    assert record.macguffin_score == 100
    assert record.monsters_defeated == 2
    assert record.runes_collected == 1
    assert record.depth == 6


def test_digestion_override_uses_macguffin_ending_after_decline() -> None:
    engine = GameEngine()
    engine.macguffin_discovery.record(
        load_macguffin_registry().get("shield_of_justice"),
    )
    _engulf_player_on_wolf(engine, player_hp=0)
    for _ in range(3):
        _press(engine, KeySym.PERIOD)
    _advance_digestion_modal(engine)

    assert engine.game_over.active
    assert engine.game_over.ending is not None
    assert engine.game_over.ending.kind == "macguffin"
    assert engine.game_over.ending.detail == "The Shield of Justice"
    assert (
        format_game_over_ending(engine.game_over.ending)
        == "found The Shield of Justice!"
    )


def test_digestion_without_discovery_stays_digested() -> None:
    engine = GameEngine()
    _engulf_player_on_wolf(engine, player_hp=0)
    for _ in range(3):
        _press(engine, KeySym.PERIOD)
    _advance_digestion_modal(engine)

    assert engine.game_over.ending is not None
    assert engine.game_over.ending.kind == "digested"
    assert engine.game_over.ending.detail == "wolf"


def test_digestion_override_appends_macguffin_score(tmp_path: Path) -> None:
    store = PastRunsStore(tmp_path / "past_runs.json")
    engine = GameEngine()
    engine.past_runs_store = store
    engine.macguffin_discovery.record(
        load_macguffin_registry().get("cup_that_heals"),
    )
    _engulf_player_on_wolf(engine, player_hp=0)
    for _ in range(3):
        _press(engine, KeySym.PERIOD)
    _advance_digestion_modal(engine)

    loaded = store.load_runs()
    assert len(loaded) == 1
    assert loaded[0].ending_kind == "macguffin"
    assert loaded[0].macguffin_score == 200


def test_mid_modal_load_preserves_discovery_and_turn_count() -> None:
    engine = GameEngine()
    _setup_macguffin_step_on(engine)
    engine.player_turn_count = 12
    press_macguffin(engine, KeySym.RIGHT)
    assert engine.macguffin_victory_confirm.active

    restored = GameEngine.from_run_snapshot(build_run_snapshot(engine))

    assert restored.player_turn_count == 12
    assert restored.macguffin_discovery.macguffin_id == "sword_of_freedom"
    assert not restored.macguffin_victory_confirm.active


def test_game_over_open_accepts_macguffin_score(tmp_path: Path) -> None:
    store = PastRunsStore(tmp_path / "past_runs.json")
    state = GameOverState()
    ending = GameOverEnding(kind="macguffin", detail="The Sword of Freedom")

    state.open(
        player_name="Alex",
        ending=ending,
        monsters_defeated=1,
        runes_collected=0,
        depth=3,
        past_runs_store=store,
        macguffin_score=100,
    )

    loaded = store.load_runs()
    assert len(loaded) == 1
    assert loaded[0].macguffin_score == 100