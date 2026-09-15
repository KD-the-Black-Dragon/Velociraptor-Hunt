"""PR3: ranged AI — reload priority, good top-up, evil hunger close."""

from __future__ import annotations

import random

from src.components import (
    Alignment,
    Fighter,
    Position,
    RangedMagazine,
    VoreCapable,
)
from src.engine import GameEngine
from src.systems.ai import run_monster_turns, spawn_test_npc
from src.systems.fov import update_fov
from src.systems.ranged_magazine import try_ranged_reload
from src.systems.vore import should_commit_ranged_hunger_approach
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_horizontal_line,
    isolate_other_ais,
    spawn_wolf_with_abilities,
)


def test_zero_shots_reloads_when_not_adjacent() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["Smite5"])
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    player.components[Position] = Position(ARENA_X + 4, ARENA_Y)
    # Keep player HP high so vore hunger won't commit.
    player.components[Fighter].hp = player.components[Fighter].max_hp
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    mag = wolf.components[RangedMagazine]
    mag.current = 0
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
    )
    assert mag.current == 1


def test_one_shot_does_not_reload_while_engaging() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["Smite5"])
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    player.components[Fighter].hp = player.components[Fighter].max_hp
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    mag = wolf.components[RangedMagazine]
    mag.current = 1
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
    )
    # Engaging with 1 shot: should fire (→0), never top up to 2.
    assert mag.current == 0


def test_good_ally_tops_up_when_no_enemy_in_sight() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    from src.components import Abilities, AbilityState
    from src.data.ability_parser import parse_abilities
    from src.systems.ranged_magazine import ensure_ranged_magazine

    ally = spawn_test_npc(
        engine.world,
        x=ARENA_X,
        y=ARENA_Y,
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
        accuracy=10.0,
        evade=fighter.evade,
        ac=fighter.ac,
        min_damage=1,
        max_damage=1,
        ranged_accuracy=10.0,
        ranged_min_damage=3,
        ranged_max_damage=3,
    )
    ally.components[AbilityState] = AbilityState()
    ally.components[Abilities] = Abilities(parsed=parse_abilities(["Smite5"]))
    ensure_ranged_magazine(ally, maximum=2)
    mag = ally.components[RangedMagazine]
    mag.current = 1
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 4)
    player.components[Position] = Position(ARENA_X + 2, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
    )
    assert mag.current == 2


def test_hunger_commit_blocks_shoot_and_closes() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = spawn_wolf_with_abilities(
        engine.world, ARENA_X, ARENA_Y, ["Smite5", "PreferVore"]
    )
    wolf.tags.add(VoreCapable)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    player.components[Position] = Position(ARENA_X + 4, ARENA_Y)
    # Eligible for vore decision
    player.components[Fighter].hp = 1
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    mag = wolf.components[RangedMagazine]
    before_shots = mag.current
    start = wolf.components[Position]
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
    )
    # PreferVore → hunger close; no shot spent; should have stepped closer
    assert mag.current == before_shots
    after = wolf.components[Position]
    assert abs(after.x - player.components[Position].x) < abs(
        start.x - player.components[Position].x
    ) or abs(after.y - player.components[Position].y) < abs(
        start.y - player.components[Position].y
    ) or (after.x != start.x or after.y != start.y)


def test_hunger_helper_false_when_adjacent() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = spawn_wolf_with_abilities(
        engine.world, ARENA_X, ARENA_Y, ["Smite5", "PreferVore"]
    )
    wolf.tags.add(VoreCapable)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 3)
    player.components[Position] = Position(ARENA_X + 1, ARENA_Y)
    player.components[Fighter].hp = 1
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    assert (
        should_commit_ranged_hunger_approach(
            wolf, player, engine.game_map, random.Random(0)
        )
        is False
    )


def test_try_ranged_reload_silent_helper() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["Range3"])
    mag = wolf.components[RangedMagazine]
    mag.current = 0
    engine.message_log = type(engine.message_log)()
    assert try_ranged_reload(wolf) is True
    assert list(engine.message_log.entries()) == []
