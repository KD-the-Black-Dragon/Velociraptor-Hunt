"""PR7: rune progression rows in the status corner."""

from __future__ import annotations

from src.components import PlayerProgression
from src.data.floor_rune_registry import RuneEffect
from src.engine import GameEngine
from src.systems.floor_runes import apply_rune_effect
from src.ui.status_corner import (
    STATUS_ACCURACY_FG,
    STATUS_AC_FG,
    STATUS_DAMAGE_FG,
    STATUS_HP_FG,
    progression_extra_rows,
)

from tests.ui_test_helpers import render_engine_frame, status_corner_text


def test_progression_extra_rows_empty() -> None:
    assert progression_extra_rows(PlayerProgression()) == ()


def test_progression_extra_rows_hp_only() -> None:
    prog = PlayerProgression(bonus_max_hp=5)
    rows = progression_extra_rows(prog)
    assert len(rows) == 1
    assert rows[0].text == "HP +5"
    assert rows[0].fg == STATUS_HP_FG


def test_progression_extra_rows_accuracy_only() -> None:
    prog = PlayerProgression(bonus_accuracy=0.15)
    rows = progression_extra_rows(prog)
    assert len(rows) == 1
    assert rows[0].text == "Acc +0.15"


def test_progression_extra_rows_combat_on_separate_rows() -> None:
    prog = PlayerProgression(
        bonus_accuracy=0.2,
        bonus_min_damage=1,
        bonus_max_damage=1,
        bonus_ac=1,
    )
    rows = progression_extra_rows(prog)
    assert [row.text for row in rows] == ["Acc +0.2", "Dam +1", "AC +1"]
    assert [row.fg for row in rows] == [
        STATUS_ACCURACY_FG,
        STATUS_DAMAGE_FG,
        STATUS_AC_FG,
    ]


def test_progression_extra_rows_hp_and_combat() -> None:
    prog = PlayerProgression(bonus_max_hp=5, bonus_ac=1)
    rows = progression_extra_rows(prog)
    assert [row.text for row in rows] == ["HP +5", "AC +1"]


def test_progression_extra_rows_clips_to_max_width() -> None:
    prog = PlayerProgression(bonus_max_hp=12345)
    rows = progression_extra_rows(prog, max_width=10)
    assert rows[0].text == "HP +12345"[:10]


def test_engine_render_shows_rune_hp_bonus() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    apply_rune_effect(player, RuneEffect(type="max_hp", amount=5))
    console = render_engine_frame(engine)
    assert "HP +5" in status_corner_text(console, engine.ui_layout)


def test_engine_render_shows_combat_rune_bonuses() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    apply_rune_effect(
        player,
        RuneEffect(
            type="accuracy_damage",
            accuracy=0.2,
            min_damage=1,
            max_damage=1,
        ),
    )
    apply_rune_effect(player, RuneEffect(type="natural_ac", amount=1))
    console = render_engine_frame(engine)
    corner = status_corner_text(console, engine.ui_layout)
    assert "Acc +0.2" in corner
    assert "Dam +1" in corner
    assert "AC +1" in corner