"""SmiteN (2–9) Smite-targeted attack and engagement AI."""

from __future__ import annotations

import random

import pytest

from src.components import Abilities, AbilityState, Alignment, Fighter, Position, Stunned
from src.data.abilities import filter_known_abilities
from src.data.ability_parser import parse_abilities
from src.data.entity_loader import load_entity_registry
from src.data.warnings import LoadWarnings
from src.engine import GameEngine
from src.systems.abilities import (
    is_stunned_prey,
    max_smite_range,
    pick_evil_smite_target,
    try_smite_engagement,
)
from src.systems.ai import pick_evil_target, run_monster_turns, spawn_test_npc
from src.systems.fov import update_fov
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_floor_rect,
    carve_horizontal_line,
    isolate_other_ais,
    spawn_wolf_with_abilities,
)


def _good_with_smite(engine: GameEngine, *, x: int, y: int, distance: int = 5):
    """Minimal good ally with SmiteN (no stock entity-id dependency)."""
    ally = spawn_test_npc(
        engine.world,
        x=x,
        y=y,
        species="test_cleric",
        alignment=Alignment.GOOD,
        hp=20,
        min_damage=1,
        max_damage=1,
    )
    fighter = ally.components[Fighter]
    ally.components[Fighter] = Fighter(
        hp=fighter.hp,
        max_hp=fighter.max_hp,
        accuracy=fighter.accuracy,
        evade=fighter.evade,
        ac=fighter.ac,
        min_damage=fighter.min_damage,
        max_damage=fighter.max_damage,
        ranged_accuracy=10.0,
        ranged_min_damage=3,
        ranged_max_damage=3,
    )
    ally.components[AbilityState] = AbilityState()
    parsed = parse_abilities([f"Smite{distance}"])
    ally.components[Abilities] = Abilities(parsed=parsed)
    from src.systems.ranged_magazine import ensure_ranged_magazine

    ensure_ranged_magazine(ally, maximum=2)
    return ally


def _wolf_with_smite(engine: GameEngine, distance: int):
    isolate_other_ais(engine)
    return spawn_wolf_with_abilities(
        engine.world,
        ARENA_X,
        ARENA_Y,
        [f"Smite{distance}"],
    )


@pytest.mark.parametrize("distance", [2, 3, 4, 5, 6, 7, 8, 9])
def test_filter_known_abilities_keeps_all_smite_tokens(distance: int) -> None:
    token = f"Smite{distance}"
    kept = filter_known_abilities("wolf", [token], LoadWarnings())
    assert kept == (token,)


@pytest.mark.parametrize("distance", [2, 3, 5, 9])
def test_spawned_wolf_max_smite_range_matches_token(distance: int) -> None:
    engine = GameEngine()
    wolf = _wolf_with_smite(engine, distance)
    assert max_smite_range(wolf) == distance


@pytest.mark.parametrize("distance", [2, 3, 5])
def test_wolf_smites_player_at_max_range(distance: int) -> None:
    engine = GameEngine()
    wolf = _wolf_with_smite(engine, distance)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, distance + 2)
    player.components[Position] = Position(ARENA_X + distance, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    engine.message_log = type(engine.message_log)()
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(42),
    )
    text = " ".join(entry.text for entry in engine.message_log.entries())
    assert "smites you" in text


@pytest.mark.parametrize("distance", [2, 3, 5])
def test_wolf_does_not_smite_player_beyond_max_range(distance: int) -> None:
    engine = GameEngine()
    wolf = _wolf_with_smite(engine, distance)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, distance + 3)
    player.components[Position] = Position(ARENA_X + distance + 1, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    engine.message_log = type(engine.message_log)()
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(42),
    )
    text = " ".join(entry.text for entry in engine.message_log.entries())
    assert "smites" not in text


def test_wolf_does_not_smite_adjacent_player() -> None:
    engine = GameEngine()
    wolf = _wolf_with_smite(engine, 2)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 3)
    wolf.components[Position] = Position(ARENA_X, ARENA_Y)
    player.components[Position] = Position(ARENA_X + 1, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    engine.message_log = type(engine.message_log)()
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(42),
    )
    text = " ".join(entry.text for entry in engine.message_log.entries())
    assert "smites" not in text


def test_no_smite_stunned_knight_in_range() -> None:
    engine = GameEngine()
    wolf = _wolf_with_smite(engine, 2)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 4)
    knight = spawn_test_npc(
        engine.world,
        x=ARENA_X + 2,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=0,
    )
    knight.tags.add(Stunned)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    assert is_stunned_prey(knight)
    assert not try_smite_engagement(
        wolf,
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        random.Random(0),
        alignment=Alignment.EVIL,
        entity_target=knight,
    )


def test_primary_at_three_preferred_over_neutral_at_two_for_smite_pick() -> None:
    """Primary at Chebyshev 3 beats closer neutral at 2 for Smite target pick."""
    engine = GameEngine()
    wolf = _wolf_with_smite(engine, 3)
    player = engine.player
    assert player is not None
    carve_floor_rect(engine, ARENA_X, ARENA_Y - 1, ARENA_X + 5, ARENA_Y + 3)
    wpos = Position(ARENA_X, ARENA_Y)
    wolf.components[Position] = wpos
    player.components[Position] = Position(ARENA_X + 10, ARENA_Y)
    knight = spawn_test_npc(
        engine.world,
        x=ARENA_X + 3,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    rabbit = spawn_test_npc(
        engine.world,
        x=ARENA_X,
        y=ARENA_Y + 2,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    isolate_other_ais(engine, keep=(wolf, knight, rabbit))
    update_fov(engine.game_map, wpos.x, wpos.y)
    chase_target, blocked = pick_evil_target(
        wolf,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
        player_engulfed=True,
    )
    assert blocked is None
    assert chase_target is knight
    smite_target = pick_evil_smite_target(
        wolf,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
        max_n=3,
        player_engulfed=True,
    )
    assert smite_target is knight

def test_good_smite_does_not_target_player_when_following() -> None:
    """Follow-mode chase target is the player; Smite must not fire at them."""
    engine = GameEngine()
    player = engine.player
    assert player is not None
    isolate_other_ais(engine)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    ally = _good_with_smite(engine, x=ARENA_X, y=ARENA_Y, distance=5)
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    player_hp_before = player.components[Fighter].hp
    engine.message_log = type(engine.message_log)()

    fired = try_smite_engagement(
        ally,
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        random.Random(0),
        alignment=Alignment.GOOD,
        entity_target=player,
    )
    assert fired is False
    assert player.components[Fighter].hp == player_hp_before
    text = " ".join(entry.text for entry in engine.message_log.entries())
    assert "smites you" not in text


def test_good_smite_hits_evil_not_player_when_both_in_range() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    isolate_other_ais(engine)
    carve_floor_rect(engine, ARENA_X, ARENA_Y - 1, ARENA_X + 6, ARENA_Y + 1)
    ally = _good_with_smite(engine, x=ARENA_X, y=ARENA_Y, distance=5)
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X + 4, ARENA_Y, [])
    isolate_other_ais(engine, keep=(ally, wolf))
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    player_hp_before = player.components[Fighter].hp
    wolf_hp_before = wolf.components[Fighter].hp
    engine.message_log = type(engine.message_log)()

    fired = try_smite_engagement(
        ally,
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        random.Random(0),
        alignment=Alignment.GOOD,
        entity_target=player,
    )
    assert fired is True
    assert player.components[Fighter].hp == player_hp_before
    assert wolf.components[Fighter].hp < wolf_hp_before
    text = " ".join(entry.text for entry in engine.message_log.entries())
    assert "smites you" not in text
    assert "smites" in text


def test_evil_smite_still_targets_player_via_chase_entity() -> None:
    """Regression: evil Smite may still use player as chase entity_target."""
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf = _wolf_with_smite(engine, 5)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    player_hp_before = player.components[Fighter].hp
    engine.message_log = type(engine.message_log)()

    fired = try_smite_engagement(
        wolf,
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        random.Random(0),
        alignment=Alignment.EVIL,
        entity_target=player,
    )
    assert fired is True
    text = " ".join(entry.text for entry in engine.message_log.entries())
    assert player.components[Fighter].hp < player_hp_before or "smites you" in text

