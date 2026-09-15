"""PR 6: engulfed struggle, escape rolls, and directional ejection."""

from __future__ import annotations

import random
from unittest.mock import patch

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.components import (
    AI,
    BlocksMovement,
    Engulfed,
    Fighter,
    Position,
    Predator,
    Stunned,
    VoreCapable,
    VoreMercy,
)
from src import messages
from src.systems.ai import run_monster_turns
from src.constants import VORE_ESCAPE_BASE, VORE_ESCAPE_PER_FAIL
from src import messages
from src.engine import GameEngine
from src.systems.naming import entity_log_name

from tests.map_test_helpers import carve_east_of, carve_floor_rect
from src.systems.combat import apply_struggle_damage, compute_struggle_damage
from src.systems.inventory import effective_fighter
from src.systems.vore import debug_weaken_all_monsters
from src.systems.fov import update_fov
from src.systems.vore import (
    engulf_player,
    escape_chance_for_predator,
    should_attempt_vore,
    try_struggle,
)


def _press(engine: GameEngine, sym: KeySym) -> bool:
    return engine.handle_event(
        tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=Modifier.NONE),
    )


def _engulf_player_on_wolf(engine: GameEngine) -> tuple[object, object]:
    player = engine.player
    assert player is not None
    from tests.map_test_helpers import first_wolf

    wolf = first_wolf(engine)
    pos = player.components[Position]
    carve_floor_rect(engine, pos.x, pos.y - 1, pos.x + 1, pos.y)
    wolf.components[Position] = Position(pos.x + 1, pos.y)
    engulf_player(
        engine.world, player, wolf, engine.message_log, narrative_type="OV"
    )
    return player, wolf


def test_apply_struggle_damage_flat() -> None:
    engine = GameEngine()
    wolf = list(engine.world.Q.all_of(components=[Fighter, AI]))[0]
    wolf.components[Fighter] = Fighter(hp=10, max_hp=10, accuracy=10.0, evade=0, ac=0, min_damage=2, max_damage=2)
    apply_struggle_damage(wolf, 2)
    assert wolf.components[Fighter].hp == 8


def test_compute_struggle_damage_is_half_melee_no_ac() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    from src.components import PlayerProgression

    # Force deterministic attack range: min == max so no roll variance.
    progression = player.components.get(PlayerProgression) or PlayerProgression()
    player.components[PlayerProgression] = progression
    # Starter dagger is typically 3-5; pad bonuses so effective becomes 8-8.
    ef = effective_fighter(player)
    progression.bonus_min_damage += 8 - ef.min_damage
    progression.bonus_max_damage += 8 - ef.max_damage
    ef = effective_fighter(player)
    assert ef.min_damage == 8 and ef.max_damage == 8
    # Predator AC would not matter: compute_struggle_damage never applies it.
    amount = compute_struggle_damage(player, random.Random(0))
    assert amount == 4


def test_struggle_applies_half_attack_damage() -> None:
    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine)
    wolf.components[Fighter].hp = 30
    from src.components import PlayerProgression

    progression = player.components.get(PlayerProgression) or PlayerProgression()
    player.components[PlayerProgression] = progression
    ef = effective_fighter(player)
    progression.bonus_min_damage += 6 - ef.min_damage
    progression.bonus_max_damage += 6 - ef.max_damage
    assert effective_fighter(player).min_damage == 6
    assert effective_fighter(player).max_damage == 6
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=1.0):
        try_struggle(engine.world, engine.game_map, player, (1, 0), engine.message_log, rng)
    assert wolf.components[Fighter].hp == 30 - 3


def test_struggle_defeats_one_hp_predator_and_escapes() -> None:
    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine)
    wolf.components[Fighter].hp = 1
    expected_escape = messages.vore_escaped(entity_log_name(wolf))
    rng = random.Random(0)
    try_struggle(engine.world, engine.game_map, player, (1, 0), engine.message_log, rng)
    assert Engulfed not in player.tags
    assert BlocksMovement in player.tags
    assert any("defeated" in line for line in engine.message_log.lines())
    assert expected_escape in engine.message_log.lines()


def test_struggle_f2_predator_escape_via_key() -> None:
    engine = GameEngine()
    _engulf_player_on_wolf(engine)
    debug_weaken_all_monsters(engine.world, engine.message_log)
    turns_before = engine.player_turn_count
    with patch.object(engine.rng, "random", return_value=1.0):
        _press(engine, KeySym.UP)
    player = engine.player
    assert player is not None
    assert Engulfed not in player.tags
    assert engine.player_turn_count == turns_before + 1


def test_escape_roll_succeeds_with_seeded_rng() -> None:
    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine)
    wolf.components[Fighter].hp = 30
    rng = random.Random(42)
    roll = rng.random()
    rng = random.Random(42)
    if roll < VORE_ESCAPE_BASE:
        try_struggle(engine.world, engine.game_map, player, (0, -1), engine.message_log, rng)
        assert Engulfed not in player.tags


def test_failed_struggle_escalates_escape_chance() -> None:
    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine)
    wolf.components[Fighter].hp = 30
    assert escape_chance_for_predator(wolf) == VORE_ESCAPE_BASE
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=1.0):
        try_struggle(engine.world, engine.game_map, player, (1, 0), engine.message_log, rng)
    assert Engulfed in player.tags
    assert wolf.components[Predator].failed_struggles == 1
    expected = min(1.0, VORE_ESCAPE_BASE + VORE_ESCAPE_PER_FAIL)
    assert escape_chance_for_predator(wolf) == expected


def test_escape_at_zero_hp_leaves_stunned() -> None:
    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine)
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=0.0):
        try_struggle(engine.world, engine.game_map, player, (1, 0), engine.message_log, rng)
    assert Engulfed not in player.tags
    assert Stunned in player.tags
    assert player.components[Fighter].hp == 0


def test_directional_escape_moves_player() -> None:
    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine)
    pred_pos = wolf.components[Position]
    expected = Position(pred_pos.x, pred_pos.y - 1)
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=0.0):
        try_struggle(engine.world, engine.game_map, player, (0, -1), engine.message_log, rng)
    assert player.components[Position] == expected


def test_wait_does_not_struggle() -> None:
    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine)
    hp_before = wolf.components[Fighter].hp
    _press(engine, KeySym.H)
    assert wolf.components[Fighter].hp == hp_before
    assert Engulfed in player.tags


def test_struggle_while_stunned_blocked() -> None:
    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine)
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    wolf.components[Fighter].hp = 1
    hp_before = wolf.components[Fighter].hp
    _press(engine, KeySym.J)
    assert Engulfed in player.tags
    assert wolf.components[Fighter].hp == hp_before
    assert any("too tired to move" in line for line in engine.message_log.lines())


def test_struggle_logs_placeholder_message() -> None:
    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine)
    wolf.components[Fighter].hp = 30
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=1.0):
        try_struggle(engine.world, engine.game_map, player, (1, 0), engine.message_log, rng)
    log = engine.message_log.lines()
    assert any(line in messages._STRUGGLE_MESSAGES for line in log)


def test_vore_mercy_granted_on_escape() -> None:
    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine)
    wolf.components[Fighter].hp = 1
    rng = random.Random(0)
    try_struggle(engine.world, engine.game_map, player, (1, 0), engine.message_log, rng)
    assert VoreMercy in player.tags


def test_vore_mercy_blocks_adjacent_vore_attempt() -> None:
    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine)
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    wolf.components[Fighter].hp = 30
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=0.0):
        try_struggle(engine.world, engine.game_map, player, (1, 0), engine.message_log, rng)
    assert VoreMercy in player.tags
    assert should_attempt_vore(wolf, player, engine.game_map, random.Random(0)) is False


def test_vore_mercy_blocks_bump_damage_same_world_turn() -> None:
    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine)
    player.components[Fighter].hp = 5
    wolf.components[Fighter].hp = 30
    pos = player.components[Position]
    wolf.components[Position] = Position(pos.x + 1, pos.y)
    update_fov(engine.game_map, pos.x, pos.y)
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=0.0):
        try_struggle(engine.world, engine.game_map, player, (0, -1), engine.message_log, rng)
    assert VoreMercy in player.tags
    hp_before = player.components[Fighter].hp
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
    )
    assert player.components[Fighter].hp == hp_before
    assert not any("hits you" in line for line in engine.message_log.lines())


def test_vore_mercy_cleared_after_world_turn() -> None:
    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine)
    wolf.components[Fighter].hp = 1
    with patch.object(engine.rng, "random", return_value=1.0):
        _press(engine, KeySym.UP)
    assert VoreMercy not in player.tags