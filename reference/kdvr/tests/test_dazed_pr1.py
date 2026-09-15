"""PR1: NPC Dazed foundation (apply, AI skip, render bg, ignore player)."""

from __future__ import annotations

import random

from src.components import AI, Alignment, Dazed, Engulfed, Player, Position, Predator
from src.engine import GameEngine
from src.message_log import MessageCategory
from src.systems.ai import run_monster_turns, spawn_test_npc
from src.systems.dazed import apply_daze, tick_daze_on_ai_turn
from src.systems.fov import update_fov
from src.systems.render import DAZED_BG, PREDATOR_ENGULFED_BG, _predator_holding_prey
from tests.map_test_helpers import ARENA_X, ARENA_Y, carve_floor_rect


def _clear_npcs(engine: GameEngine) -> None:
    for entity in list(engine.world.Q.all_of(components=[AI])):
        if entity is engine.player:
            continue
        entity.clear()


def _place_visible_npc(engine: GameEngine) -> object:
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 2, ARENA_Y)
    player = engine.player
    assert player is not None
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    npc = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
        hp=20,
    )
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    return npc


def test_apply_daze_ignores_player() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    apply_daze(player, 5, engine.game_map, engine.message_log)
    assert player.components.get(Dazed) is None
    assert Player in player.tags


def test_apply_daze_sets_remaining_and_logs_when_visible() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    npc = _place_visible_npc(engine)
    apply_daze(npc, 3, engine.game_map, engine.message_log)
    assert npc.components[Dazed].remaining == 3
    texts = [e.text for e in engine.message_log.entries()]
    assert any(t.endswith("appears dazed.") and t[0].isupper() for t in texts)


def test_apply_daze_stacks_without_second_appears_message() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    npc = _place_visible_npc(engine)
    apply_daze(npc, 2, engine.game_map, engine.message_log)
    apply_daze(npc, 4, engine.game_map, engine.message_log)
    assert npc.components[Dazed].remaining == 6
    appears = [e.text for e in engine.message_log.entries() if "appears dazed" in e.text]
    assert len(appears) == 1


def test_tick_daze_skips_and_expires_with_message() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    npc = _place_visible_npc(engine)
    apply_daze(npc, 1, engine.game_map, engine.message_log)
    skipped = tick_daze_on_ai_turn(npc, engine.game_map, engine.message_log)
    assert skipped is True
    assert npc.components.get(Dazed) is None
    texts = [e.text for e in engine.message_log.entries()]
    assert any("no longer dazed" in t for t in texts)
    pos_cats = [
        e.category
        for e in engine.message_log.entries()
        if "no longer dazed" in e.text
    ]
    assert MessageCategory.POSITIVE in pos_cats


def test_run_monster_turns_decrements_daze_without_moving() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 3, ARENA_Y)
    player = engine.player
    assert player is not None
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X + 3,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
        hp=20,
    )
    start = wolf.components[Position]
    apply_daze(wolf, 2, engine.game_map, engine.message_log)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)

    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
    )
    assert wolf.components[Position] == start
    assert wolf.components[Dazed].remaining == 1

    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(1),
    )
    assert wolf.components.get(Dazed) is None


def test_dazed_bg_constant_distinct_from_holding() -> None:
    assert DAZED_BG != PREDATOR_ENGULFED_BG
    assert DAZED_BG[2] > DAZED_BG[0]  # bluish


def test_holding_bg_preferred_over_dazed_query() -> None:
    """Document priority: holding predator uses red BG path, not dazed."""
    engine = GameEngine()
    _clear_npcs(engine)
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    prey = spawn_test_npc(
        engine.world,
        x=ARENA_X,
        y=ARENA_Y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    prey.tags.add(Engulfed)
    wolf.components[Predator] = Predator(prey=prey, narrative_type="OV")
    wolf.components[Dazed] = Dazed(remaining=3)
    assert _predator_holding_prey(wolf) is True
