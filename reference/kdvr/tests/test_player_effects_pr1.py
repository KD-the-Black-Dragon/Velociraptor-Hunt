"""PR1: PlayerEffects tick, haste world-skip, save roundtrip, status rows."""

from __future__ import annotations

from unittest.mock import patch

from src.components import Player, PlayerEffects, PlayerProgression
from src.engine import GameEngine
from src.save.snapshot import apply_run_snapshot, build_run_snapshot
from src.systems.player_effects import (
    apply_digestion_ward,
    apply_haste,
    apply_might,
    ensure_player_effects,
    haste_skips_world_phase,
    queue_delayed_teleport,
    tick_player_effects,
)
from src.ui.status_corner import player_effects_extra_rows

from tests.map_test_helpers import isolate_other_ais


def test_tick_decrements_buffs() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    apply_haste(player, 3)
    apply_might(
        player,
        duration_turns=2,
        accuracy_bonus=0.15,
        min_damage_bonus=5,
        max_damage_bonus=5,
    )
    apply_digestion_ward(player, 20)
    queue_delayed_teleport(player, 4)

    tick_player_effects(player, engine.message_log)
    pe = player.components[PlayerEffects]
    assert pe.haste_turns == 2
    assert pe.might_turns == 1
    assert pe.digestion_ward_turns == 19
    assert pe.teleport_pending_turns == 3

    tick_player_effects(player, engine.message_log)
    pe = player.components[PlayerEffects]
    assert pe.might_turns == 0
    assert pe.might_accuracy_bonus == 0.0
    assert pe.might_min_damage_bonus == 0


def test_buff_expiry_logs_caution() -> None:
    from src.log_categories import MessageCategory
    from src import messages

    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    apply_haste(player, 1)
    apply_might(
        player,
        duration_turns=1,
        accuracy_bonus=0.15,
        min_damage_bonus=5,
        max_damage_bonus=5,
    )
    apply_digestion_ward(player, 1)

    tick_player_effects(player, engine.message_log)
    entries = engine.message_log.entries()
    caution_texts = [
        e.text for e in entries if e.category == MessageCategory.CAUTION
    ]
    assert messages.effect_haste_wore_off() in caution_texts
    assert messages.effect_might_wore_off() in caution_texts
    assert messages.effect_antacid_wore_off() in caution_texts


def test_teleport_pending_clears_at_zero_without_fire() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    queue_delayed_teleport(player, 1)
    tick_player_effects(player)
    assert player.components[PlayerEffects].teleport_pending_turns is None


def test_haste_skips_monster_phase() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    # 2 player actions : 1 monster phase while hasted (not freeze forever).
    # Duration 4: skip, run, skip, run.
    apply_haste(player, 4)
    world_calls = {"n": 0}

    def counting_world(self: GameEngine) -> None:
        world_calls["n"] += 1

    with patch.object(GameEngine, "_run_world_turn", counting_world):
        engine._consume_player_turn()  # 4→3 odd → skip
        assert world_calls["n"] == 0
        assert player.components[PlayerEffects].haste_turns == 3
        assert haste_skips_world_phase(player)

        engine._consume_player_turn()  # 3→2 even → monsters
        assert world_calls["n"] == 1
        assert player.components[PlayerEffects].haste_turns == 2
        assert not haste_skips_world_phase(player)

        engine._consume_player_turn()  # 2→1 odd → skip
        assert world_calls["n"] == 1
        assert player.components[PlayerEffects].haste_turns == 1

        engine._consume_player_turn()  # 1→0 → monsters
        assert world_calls["n"] == 2
        assert player.components[PlayerEffects].haste_turns == 0

        engine._consume_player_turn()  # no haste → monsters
        assert world_calls["n"] == 3


def test_new_player_has_player_effects() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    assert engine.player is not None
    assert PlayerEffects in engine.player.components


def test_save_load_player_effects_roundtrip() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    apply_haste(player, 7)
    apply_might(
        player,
        duration_turns=5,
        accuracy_bonus=0.15,
        min_damage_bonus=5,
        max_damage_bonus=5,
    )
    apply_digestion_ward(player, 20)
    queue_delayed_teleport(player, 3)

    snap = build_run_snapshot(engine)
    loaded = GameEngine(skip_new_game=True)
    apply_run_snapshot(loaded, snap)
    assert loaded.player is not None
    pe = loaded.player.components[PlayerEffects]
    assert pe.haste_turns == 7
    assert pe.might_turns == 5
    assert pe.might_accuracy_bonus == 0.15
    assert pe.might_min_damage_bonus == 5
    assert pe.might_max_damage_bonus == 5
    assert pe.digestion_ward_turns == 20
    assert pe.teleport_pending_turns == 3


def test_old_save_missing_player_effects_defaults() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    snap = build_run_snapshot(engine)
    for ent in snap["entities"]:
        ent.get("components", {}).pop("PlayerEffects", None)

    loaded = GameEngine(skip_new_game=True)
    apply_run_snapshot(loaded, snap)
    assert loaded.player is not None
    pe = ensure_player_effects(loaded.player)
    assert pe.haste_turns == 0
    assert pe.teleport_pending_turns is None


def test_status_rows_include_active_effects() -> None:
    pe = PlayerEffects(
        haste_turns=4,
        might_turns=3,
        digestion_ward_turns=20,
        teleport_pending_turns=2,
    )
    rows = player_effects_extra_rows(pe, max_width=12)
    texts = [r.text for r in rows]
    assert any(t.startswith("Fast") for t in texts)
    assert any(t.startswith("Might") for t in texts)
    assert any("Antac" in t for t in texts)
    assert any(t.startswith("Tele?") for t in texts)
