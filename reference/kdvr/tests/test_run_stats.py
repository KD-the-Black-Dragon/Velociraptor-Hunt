"""PR1: per-run statistics and save round-trip."""

from __future__ import annotations

import random

from src.components import AI, Alignment, Fighter, Position
from src.engine import GameEngine
from src.run_stats import RunStats, decode_run_stats
from src.systems.ai import spawn_test_npc
from src.systems.combat import _perform_attack, perform_wand_attack, try_action
from src.systems.vore import engulf_player, try_struggle

from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_floor_tile,
    first_wolf,
    isolate_other_ais,
)
from tests.test_floor_runes_pr4 import (
    minimal_floor_runes_payload,
    rune_placement_arena,
)
from src.data.floor_rune_loader import parse_floor_rune_registry
from src.components import Player, PlayerProgression, ScreenFlashState
from src.constants import (
    PLAYER_ACCURACY,
    PLAYER_MAX_HP,
)
from src.message_log import MessageLog
from src.systems.floor_runes import spawn_floor_rune, try_activate_floor_rune
from tcod.ecs import Registry


def _round_trip(engine: GameEngine) -> GameEngine:
    snapshot = engine.build_run_snapshot()
    return GameEngine.from_run_snapshot(snapshot)


def test_new_game_resets_run_stats() -> None:
    engine = GameEngine()
    engine.run_stats.monsters_defeated = 4
    engine.run_stats.runes_collected = 2
    engine.new_game()
    assert engine.run_stats.monsters_defeated == 0
    assert engine.run_stats.runes_collected == 0


def test_decode_run_stats_defaults_when_missing() -> None:
    stats = decode_run_stats(None)
    assert stats.monsters_defeated == 0
    assert stats.runes_collected == 0


def test_round_trip_run_stats() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.run_stats.monsters_defeated = 9
    engine.run_stats.runes_collected = 3

    restored = _round_trip(engine)

    assert restored.run_stats.monsters_defeated == 9
    assert restored.run_stats.runes_collected == 3


def test_round_trip_run_stats_defaults_for_legacy_snapshot() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    snapshot = engine.build_run_snapshot()
    snapshot.pop("run_stats", None)

    restored = GameEngine.from_run_snapshot(snapshot)

    assert restored.run_stats.monsters_defeated == 0
    assert restored.run_stats.runes_collected == 0


def test_player_melee_defeat_increments_monsters_defeated() -> None:
    engine = GameEngine()
    monster = first_wolf(engine)
    isolate_other_ais(engine, keep=(monster,))
    monster.components[Fighter].hp = 1
    mpos = monster.components[Position]
    engine.player.components[Position] = Position(mpos.x - 1, mpos.y)
    carve_floor_tile(engine, mpos.x - 1, mpos.y)
    carve_floor_tile(engine, mpos.x, mpos.y)

    rng = random.Random(0)
    for _ in range(20):
        try_action(
            engine.world,
            engine.game_map,
            engine.player,
            (1, 0),
            engine.message_log,
            rng=rng,
            run_stats=engine.run_stats,
        )
        if monster not in list(engine.world.Q.all_of(components=[AI, Fighter])):
            break

    assert engine.run_stats.monsters_defeated == 1


def test_npc_melee_defeat_does_not_increment_run_stats() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    attacker = spawn_test_npc(
        engine.world,
        x=ARENA_X,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    defender = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    carve_floor_tile(engine, ARENA_X, ARENA_Y)
    carve_floor_tile(engine, ARENA_X + 1, ARENA_Y)
    defender.components[Fighter].hp = 1
    stats = RunStats()

    _perform_attack(
        attacker,
        defender,
        engine.message_log,
        world=engine.world,
        game_map=engine.game_map,
        rng=random.Random(0),
        run_stats=stats,
    )

    assert stats.monsters_defeated == 0


def test_wand_defeat_increments_monsters_defeated() -> None:
    engine = GameEngine()
    monster = first_wolf(engine)
    isolate_other_ais(engine, keep=(monster,))
    monster.components[Fighter].hp = 1
    stats = RunStats()
    wand_fighter = Fighter(
        hp=1,
        max_hp=1,
        accuracy=100.0,
        evade=0,
        ac=0,
        min_damage=5,
        max_damage=5,
    )

    perform_wand_attack(
        engine.player,
        monster,
        wand_fighter,
        engine.message_log,
        world=engine.world,
        game_map=engine.game_map,
        rng=random.Random(1),
        run_stats=stats,
    )

    assert stats.monsters_defeated == 1


def test_struggle_defeat_increments_monsters_defeated() -> None:
    engine = GameEngine()
    player = engine.player
    wolf = first_wolf(engine)
    pos = player.components[Position]
    carve_floor_tile(engine, pos.x, pos.y)
    carve_floor_tile(engine, pos.x + 1, pos.y)
    wolf.components[Position] = Position(pos.x + 1, pos.y)
    wolf.components[Fighter].hp = 1
    engulf_player(engine.world, player, wolf, engine.message_log, narrative_type="OV")
    stats = RunStats()

    try_struggle(
        engine.world,
        engine.game_map,
        player,
        (1, 0),
        engine.message_log,
        random.Random(0),
        run_stats=stats,
    )

    assert stats.monsters_defeated == 1


def test_floor_rune_activation_increments_runes_collected() -> None:
    world = Registry()
    game_map = rune_placement_arena()
    registry = parse_floor_rune_registry(minimal_floor_runes_payload())
    rune = spawn_floor_rune(
        world,
        game_map,
        floor_depth=1,
        rng=random.Random(2),
        registry=registry,
        min_distance=2,
        count=1,
    )[0]
    pos = rune.components[Position]

    player = world[object()]
    player.tags.add(Player)
    player.components[Fighter] = Fighter(
        hp=PLAYER_MAX_HP,
        max_hp=PLAYER_MAX_HP,
        accuracy=PLAYER_ACCURACY,
        evade=0,
        ac=1,
        min_damage=1,
        max_damage=2,
    )
    player.components[PlayerProgression] = PlayerProgression()

    stats = RunStats()
    assert try_activate_floor_rune(
        world,
        player,
        pos.x,
        pos.y,
        MessageLog(),
        screen_flash=ScreenFlashState(),
        registry=registry,
        run_stats=stats,
    )
    assert stats.runes_collected == 1