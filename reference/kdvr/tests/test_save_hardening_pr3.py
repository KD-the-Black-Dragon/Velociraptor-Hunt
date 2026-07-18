"""PR3 engineering-maintainability: save migrate hook + additive defaults."""

from __future__ import annotations

import copy

import pytest

from src.components import Player, PlayerEffects, Position
from src.engine import GameEngine
from src.save.migrate import SaveMigrationError, migrate_run
from src.save.schema import SAVE_FORMAT_VERSION
from src.systems.player_effects import ensure_player_effects
from tests.map_test_helpers import isolate_other_ais


def test_migrate_run_v1_identity_sets_version() -> None:
    run = {"save_format_version": 1, "player_name": "X"}
    out = migrate_run(run)
    assert out["save_format_version"] == SAVE_FORMAT_VERSION
    assert out["player_name"] == "X"
    # Callers may mutate result without mutating input
    out["player_name"] = "Y"
    assert run["player_name"] == "X"


def test_migrate_run_rejects_future_version() -> None:
    with pytest.raises(SaveMigrationError, match="newer"):
        migrate_run({"save_format_version": 999}, from_version=999)


def test_migrate_run_rejects_pre_v1() -> None:
    with pytest.raises(SaveMigrationError, match="unsupported"):
        migrate_run({}, from_version=0)


def test_compact_round_trip_key_fields() -> None:
    engine = GameEngine(player_name="Compact", skip_new_game=False)
    isolate_other_ais(engine)
    engine.player_turn_count = 9
    engine.floor_depth = 3
    engine.last_come_here_turn = 4
    engine.close_door_pending = True
    assert engine.player is not None
    pos = engine.player.components[Position]
    engine.game_map.explored[pos.y, pos.x] = True
    engine.run_stats.monsters_defeated = 2
    engine.run_stats.runes_collected = 1

    snap = engine.build_run_snapshot()
    restored = GameEngine.from_run_snapshot(snap)

    assert restored.player_name == "Compact"
    assert restored.player_turn_count == 9
    assert restored.floor_depth == 3
    assert restored.last_come_here_turn == 4
    assert restored.close_door_pending is True
    assert restored.difficulty_id == engine.difficulty_id
    assert restored.player is not None
    assert restored.player.components[Position] == pos
    assert restored.game_map.explored[pos.y, pos.x]
    assert restored.run_stats.monsters_defeated == 2
    assert restored.run_stats.runes_collected == 1
    # PlayerEffects present after round-trip
    assert PlayerEffects in restored.player.components


def test_additive_defaults_when_optional_run_keys_missing() -> None:
    engine = GameEngine(player_name="Additive", skip_new_game=False)
    isolate_other_ais(engine)
    engine.player_turn_count = 5
    engine.last_come_here_turn = 2
    engine.close_door_pending = True
    engine.run_stats.monsters_defeated = 7
    assert engine.player is not None
    # Ensure effects exist so we can strip them from the record
    ensure_player_effects(engine.player)
    effects = engine.player.components[PlayerEffects]
    effects.haste_turns = 3

    snap = engine.build_run_snapshot()
    stripped = copy.deepcopy(snap)

    for key in (
        "last_come_here_turn",
        "close_door_pending",
        "run_stats",
        "macguffin_discovery",
        "message_log",
        "difficulty_id",
        "rng_state",
    ):
        stripped.pop(key, None)

    # Strip PlayerEffects from player entity record
    player_id = stripped["player_entity_id"]
    for record in stripped["entities"]:
        if int(record["id"]) == int(player_id):
            record.get("components", {}).pop("PlayerEffects", None)
            break

    # Map archetype optional
    stripped["game_map"].pop("layout_archetype", None)

    restored = GameEngine.from_run_snapshot(stripped)

    assert restored.player_name == "Additive"
    assert restored.player_turn_count == 5
    assert restored.last_come_here_turn == -1
    assert restored.close_door_pending is False
    assert restored.run_stats.monsters_defeated == 0
    assert restored.run_stats.runes_collected == 0
    assert restored.macguffin_discovery.active is False
    assert list(restored.message_log.entries()) == []
    assert restored.game_map.layout_archetype == ""
    assert restored.player is not None
    assert Player in restored.player.tags
    # Missing PlayerEffects → default inactive
    pe = restored.player.components[PlayerEffects]
    assert pe.haste_turns == 0
    assert pe.might_turns == 0
    assert pe.teleport_pending_turns is None


def test_apply_run_snapshot_calls_migrate() -> None:
    """Even without save_format_version on run body, apply still succeeds via migrate."""
    engine = GameEngine(player_name="Mig", skip_new_game=False)
    isolate_other_ais(engine)
    snap = engine.build_run_snapshot()
    # Envelope version is separate; run may still carry version from build
    assert snap.get("save_format_version") == SAVE_FORMAT_VERSION
    # Explicit migrate path used by apply — future version rejection still works
    with pytest.raises(SaveMigrationError):
        GameEngine.from_run_snapshot({**snap, "save_format_version": 99})
