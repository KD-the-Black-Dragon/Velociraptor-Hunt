"""PR2: past runs persistence and sort order."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

from src.game_over_ending import GameOverEnding
from src.past_runs.schema import PastRunRecord
from src.past_runs.store import PastRunsStore, sorted_for_display, today_display_date
from src.systems.digestion import GameOverState

from tests.test_digestion import (
    _advance_digestion_modal,
    _engulf_player_on_wolf,
    _press,
)
from tcod.event import KeySym


def _record(
    *,
    name: str = "Alex",
    kind: str = "digested",
    detail: str = "wolf",
    monsters: int = 0,
    runes: int = 0,
    depth: int = 1,
    date: str = "01/15/2026",
) -> PastRunRecord:
    return PastRunRecord(
        character_name=name,
        ending_kind=kind,
        ending_detail=detail,
        monsters_defeated=monsters,
        runes_collected=runes,
        depth=depth,
        date=date,
    )


def test_probe_false_when_missing(tmp_path: Path) -> None:
    store = PastRunsStore(tmp_path / "past_runs.json")
    assert not store.probe()


def test_probe_true_after_append(tmp_path: Path) -> None:
    store = PastRunsStore(tmp_path / "past_runs.json")
    store.append(_record())
    assert store.probe()
    loaded = store.load_runs()
    assert len(loaded) == 1
    assert loaded[0].character_name == "Alex"
    assert loaded[0].ending_kind == "digested"
    assert loaded[0].ending_detail == "wolf"


def test_corrupt_file_treated_as_empty(tmp_path: Path) -> None:
    path = tmp_path / "past_runs.json"
    path.write_text("{not json", encoding="utf-8")
    store = PastRunsStore(path)
    assert not store.probe()
    assert store.load_runs() == []


def test_cap_evicts_oldest_entries(tmp_path: Path) -> None:
    store = PastRunsStore(tmp_path / "past_runs.json")
    with patch("src.past_runs.store.MAX_PAST_RUNS", 3):
        for index in range(4):
            store.append(_record(name=f"Run{index}", depth=index + 1))

    loaded = store.load_runs()
    assert len(loaded) == 3
    assert [run.character_name for run in loaded] == ["Run1", "Run2", "Run3"]


def test_sorted_for_display_order() -> None:
    runs = [
        _record(name="shallow", depth=2, runes=1, monsters=5, date="02/01/2026"),
        _record(name="deep", depth=5, runes=0, monsters=0, date="03/01/2026"),
        _record(name="deep-more-runes", depth=5, runes=3, monsters=0, date="01/01/2026"),
        _record(name="deep-tie-runes", depth=5, runes=3, monsters=2, date="02/01/2026"),
        _record(name="deep-tie-monsters", depth=5, runes=3, monsters=4, date="04/01/2026"),
        _record(name="deep-older-date", depth=5, runes=3, monsters=4, date="01/01/2026"),
    ]
    ordered = sorted_for_display(runs)
    assert [run.character_name for run in ordered] == [
        "deep-older-date",
        "deep-tie-monsters",
        "deep-tie-runes",
        "deep-more-runes",
        "deep",
        "shallow",
    ]


def test_game_over_open_appends_past_run(tmp_path: Path) -> None:
    store = PastRunsStore(tmp_path / "past_runs.json")
    state = GameOverState()
    ending = GameOverEnding(kind="digested", detail="shark")

    with patch("src.past_runs.store.today_display_date", return_value="07/05/2026"):
        state.open(
            player_name="Morgan",
            ending=ending,
            monsters_defeated=7,
            runes_collected=2,
            depth=9,
            past_runs_store=store,
        )

    assert state.active
    assert state.ending == ending
    assert state.monsters_defeated == 7
    assert state.runes_collected == 2
    assert state.depth == 9

    loaded = store.load_runs()
    assert len(loaded) == 1
    record = loaded[0]
    assert record.character_name == "Morgan"
    assert record.ending_kind == "digested"
    assert record.ending_detail == "shark"
    assert record.monsters_defeated == 7
    assert record.runes_collected == 2
    assert record.depth == 9
    assert record.date == "07/05/2026"


def test_game_over_via_engine_appends_with_isolated_store(tmp_path: Path) -> None:
    from src.engine import GameEngine
    from src.past_runs.store import PastRunsStore

    store = PastRunsStore(tmp_path / "past_runs.json")
    engine = GameEngine()
    engine.past_runs_store = store
    engine.run_stats.monsters_defeated = 3
    engine.run_stats.runes_collected = 1
    engine.floor_depth = 4

    _engulf_player_on_wolf(engine, player_hp=0)
    for _ in range(3):
        _press(engine, KeySym.PERIOD)
    _advance_digestion_modal(engine)

    assert engine.game_over.active
    loaded = store.load_runs()
    assert len(loaded) == 1
    assert loaded[0].character_name == "Player"
    assert loaded[0].ending_kind == "digested"
    assert loaded[0].ending_detail == "wolf"
    assert loaded[0].monsters_defeated == 3
    assert loaded[0].runes_collected == 1
    assert loaded[0].depth == 4


def test_today_display_date_format() -> None:
    with patch("src.past_runs.store.date") as mock_date:
        mock_date.today.return_value = date(2026, 7, 5)
        assert today_display_date() == "07/05/2026"