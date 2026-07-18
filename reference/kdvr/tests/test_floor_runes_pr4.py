"""PR4: rune activation, permanent progression, and screen flash."""

from __future__ import annotations

import random

from tcod.ecs import Registry

from src.components import (
    Fighter,
    Player,
    PlayerProgression,
    Position,
    ScreenFlashState,
)
from src.constants import RUNE_FLASH_RADIUS
from src.constants import PLAYER_AC, PLAYER_ACCURACY, PLAYER_MAX_HP, RUNES_PER_FLOOR
from src.data.floor_rune_registry import RuneEffect
from src.engine import GameEngine
from src.message_log import MessageLog
from src.spawn import spawn_entity_by_id
from src.systems.combat import try_action
from src.systems.floor_runes import (
    apply_rune_effect,
    count_floor_runes,
    spawn_floor_rune,

    try_activate_floor_rune,
)
from src.systems.inventory import effective_fighter

from src.data.floor_rune_loader import parse_floor_rune_registry
from tests.rune_test_helpers import minimal_floor_runes_payload, rune_placement_arena


def test_spawn_three_distinct_rune_tiles() -> None:
    world = Registry()
    game_map = rune_placement_arena(width=50, height=12)
    registry = parse_floor_rune_registry(minimal_floor_runes_payload())
    runes = spawn_floor_rune(
        world,
        game_map,
        floor_depth=1,
        rng=random.Random(9),
        registry=registry,
        min_distance=3,
        min_pairwise=3,
        count=RUNES_PER_FLOOR,
    )
    assert len(runes) == RUNES_PER_FLOOR
    positions = {(r.components[Position].x, r.components[Position].y) for r in runes}
    assert len(positions) == RUNES_PER_FLOOR


def test_apply_rune_effect_max_hp_syncs_fighter() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    assert fighter.max_hp == PLAYER_MAX_HP
    assert fighter.hp == PLAYER_MAX_HP

    bonus = apply_rune_effect(player, RuneEffect(type="max_hp", amount=5))
    assert bonus == "+5 max HP"
    prog = player.components[PlayerProgression]
    assert prog.bonus_max_hp == 5
    assert fighter.max_hp == PLAYER_MAX_HP + 5
    assert fighter.hp == PLAYER_MAX_HP + 5


def test_effective_fighter_includes_progression_bonuses() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    prog = player.components[PlayerProgression]
    baseline = effective_fighter(player)

    prog.bonus_accuracy = 0.15
    prog.bonus_ac = 2
    prog.bonus_min_damage = 1
    prog.bonus_max_damage = 1
    boosted = effective_fighter(player)

    assert boosted.accuracy == baseline.accuracy + 0.15
    assert boosted.ac == baseline.ac + 2
    assert boosted.min_damage == baseline.min_damage + 1
    assert boosted.max_damage == baseline.max_damage + 1


def test_try_activate_floor_rune_removes_entity_and_logs() -> None:
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

    log = MessageLog()
    flash = ScreenFlashState()
    assert try_activate_floor_rune(
        world,
        player,
        pos.x,
        pos.y,
        log,
        screen_flash=flash,
        registry=registry,
    )
    assert count_floor_runes(world) == 0
    assert any("+5 max HP" in line for line in log.lines())
    assert flash.pending
    assert player.components[PlayerProgression].bonus_max_hp == 5


def test_npc_cannot_activate_floor_rune() -> None:
    world = Registry()
    game_map = rune_placement_arena()
    registry = parse_floor_rune_registry(minimal_floor_runes_payload())
    rune = spawn_floor_rune(
        world,
        game_map,
        floor_depth=1,
        rng=random.Random(4),
        registry=registry,
        min_distance=2,
        count=1,
    )[0]
    pos = rune.components[Position]
    wolf = spawn_entity_by_id(world, "wolf", pos.x, pos.y)

    log = MessageLog()
    assert not try_activate_floor_rune(world, wolf, pos.x, pos.y, log, registry=registry)
    assert count_floor_runes(world) == 1


def test_engine_step_on_rune_activates_once() -> None:
    world = Registry()
    game_map = rune_placement_arena(width=30, height=10)
    registry = parse_floor_rune_registry(minimal_floor_runes_payload())
    rune = spawn_floor_rune(
        world,
        game_map,
        floor_depth=1,
        rng=random.Random(6),
        registry=registry,
        min_distance=2,
        count=1,
    )[0]
    rune_pos = rune.components[Position]

    engine = GameEngine()
    player = engine.player
    assert player is not None
    engine.world = world
    engine.game_map = game_map
    player.components[Position] = Position(rune_pos.x - 1, rune_pos.y)

    assert try_action(
        engine.world,
        engine.game_map,
        player,
        (1, 0),
        engine.message_log,
    )
    from src.systems.inventory import pickup_all_items_at

    pos = player.components[Position]
    pickup_all_items_at(engine.world, player, pos.x, pos.y, engine.message_log)
    try_activate_floor_rune(
        engine.world,
        player,
        pos.x,
        pos.y,
        engine.message_log,
        screen_flash=engine.screen_flash,
        registry=registry,
    )

    assert count_floor_runes(engine.world) == 0
    assert any("absorb" in line.lower() for line in engine.message_log.lines())
    assert engine.screen_flash.pending


def test_rune_bonuses_persist_after_descend() -> None:
    from tests.test_dungeon_pr3 import _place_player_on_stairs, _press_descend

    engine = GameEngine()
    engine.new_game(seed=99)
    player = engine.player
    assert player is not None
    apply_rune_effect(player, RuneEffect(type="max_hp", amount=7))
    fighter = player.components[Fighter]
    assert fighter.max_hp == PLAYER_MAX_HP + 7

    _place_player_on_stairs(engine)
    _press_descend(engine)

    assert player.components[PlayerProgression].bonus_max_hp == 7
    assert fighter.max_hp == PLAYER_MAX_HP + 7


def test_player_has_progression_on_spawn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    assert isinstance(player.components.get(PlayerProgression), PlayerProgression)


def test_screen_flash_does_not_repeat_while_standing_still() -> None:
    import tcod.console

    from src.systems.render import render_screen_flash

    flash = ScreenFlashState(pending=True, color=(80, 220, 120))
    console = tcod.console.Console(80, 50)

    render_screen_flash(console, state=flash, player_pos=Position(10, 5))
    for _ in range(5):
        render_screen_flash(console, state=flash, player_pos=Position(10, 5))
    assert not flash.pending


def test_screen_flash_is_one_shot_per_render() -> None:
    import tcod.console

    from src.systems.render import render_screen_flash

    flash = ScreenFlashState(pending=True, color=(80, 220, 120))
    console = tcod.console.Console(80, 50)

    render_screen_flash(console, state=flash, player_pos=Position(10, 5))
    assert not flash.pending

    render_screen_flash(console, state=flash, player_pos=Position(10, 5))
    assert not flash.pending


def test_screen_flash_only_tints_player_vicinity() -> None:
    import tcod.console

    from src.systems.render import render_screen_flash

    console = tcod.console.Console(40, 20)
    console.clear()
    base_bg = (10, 10, 10)
    player_pos = Position(20, 10)
    far_pos = Position(0, 0)
    console.print(far_pos.x, far_pos.y, ".", fg=(100, 100, 100), bg=base_bg)
    console.print(player_pos.x, player_pos.y, "@", fg=(255, 255, 255), bg=base_bg)

    flash_color = (80, 220, 120)
    render_screen_flash(
        console,
        state=ScreenFlashState(pending=True, color=flash_color),
        player_pos=player_pos,
    )

    def bg_rgb(x: int, y: int) -> tuple[int, int, int]:
        tile = console.rgba[y, x]
        return (int(tile["bg"][0]), int(tile["bg"][1]), int(tile["bg"][2]))

    assert bg_rgb(far_pos.x, far_pos.y) == base_bg
    assert bg_rgb(player_pos.x, player_pos.y) != base_bg

    tinted = 0
    for dy in range(-RUNE_FLASH_RADIUS, RUNE_FLASH_RADIUS + 1):
        for dx in range(-RUNE_FLASH_RADIUS, RUNE_FLASH_RADIUS + 1):
            if max(abs(dx), abs(dy)) > RUNE_FLASH_RADIUS:
                continue
            x, y = player_pos.x + dx, player_pos.y + dy
            if bg_rgb(x, y) != base_bg:
                tinted += 1
    assert tinted == (RUNE_FLASH_RADIUS * 2 + 1) ** 2