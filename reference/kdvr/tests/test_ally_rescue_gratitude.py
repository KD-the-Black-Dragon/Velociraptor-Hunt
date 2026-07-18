"""PR3: gratitude when the player rescues good allies from engulfment."""

from __future__ import annotations

import random

from src import messages
from src.components import Alignment, Engulfed, Fighter, Position, ProperName, Stunned
from src.data.ally_content import format_rescue_gratitude, pick_rescue_gratitude_line
from src.data.rescue_gratitude_loader import load_rescue_gratitude_registry
from src.engine import GameEngine
from src.systems.ai import spawn_test_npc
from src.systems.combat import perform_wand_attack, try_action
from src.systems.fov import update_fov
from src.systems.vore import engulf_npc, release_prey_if_defeated_predator
from tests.map_test_helpers import (
    carve_east_of,
    ensure_adjacent_floor,
    first_wolf,
    iter_wolves,
)


def _wolf_holding_good_prey(engine: GameEngine) -> tuple[object, object]:
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    carve_east_of(engine, player_pos, 2)
    wolf = first_wolf(engine)
    knight = spawn_test_npc(
        engine.world,
        x=player_pos.x + 1,
        y=player_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        species_id="knight",
        hp=12,
        evade=0,
        ac=0,
    )
    knight.components[Fighter].hp = 0
    knight.tags.add(Stunned)
    wolf.components[Position] = Position(player_pos.x + 1, player_pos.y)
    engulf_npc(engine.world, knight, wolf, narrative_type="OV")
    update_fov(engine.game_map, player_pos.x, player_pos.y)
    return wolf, knight


def _wolf_holding_rabbit(engine: GameEngine) -> tuple[object, object]:
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    carve_east_of(engine, player_pos, 2)
    wolf = first_wolf(engine)
    rabbit = spawn_test_npc(
        engine.world,
        x=player_pos.x + 1,
        y=player_pos.y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
        hp=5,
        evade=0,
        ac=0,
        min_damage=0,
        max_damage=0,
    )
    rabbit.components[Fighter].hp = 0
    rabbit.tags.add(Stunned)
    wolf.components[Position] = Position(player_pos.x + 1, player_pos.y)
    engulf_npc(engine.world, rabbit, wolf, narrative_type="OV")
    update_fov(engine.game_map, player_pos.x, player_pos.y)
    return wolf, rabbit


def test_player_bump_rescue_emits_gratitude_for_good_prey() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf, knight = _wolf_holding_good_prey(engine)
    wolf.components[Fighter].hp = 1
    player.components[Position] = player.components[Position]
    rng = random.Random(0)
    expected_gratitude = format_rescue_gratitude(
        knight,
        pick_rescue_gratitude_line(load_rescue_gratitude_registry(), rng),
    )

    for _ in range(20):
        try_action(
            engine.world,
            engine.game_map,
            player,
            (1, 0),
            engine.message_log,
            rng=rng,
        )
        if wolf not in list(iter_wolves(engine)):
            break

    freed = messages.npc_freed_from_predator("The knight", "the wolf")
    assert freed in engine.message_log.lines()
    assert expected_gratitude in engine.message_log.lines()
    assert Engulfed not in knight.tags


def test_player_wand_rescue_emits_gratitude_for_good_prey() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf, knight = _wolf_holding_good_prey(engine)
    wolf.components[Fighter].hp = 1
    rng = random.Random(1)
    from src.components import Fighter as FighterComponent

    wand_fighter = FighterComponent(
        hp=1,
        max_hp=1,
        accuracy=100.0,
        evade=0,
        ac=0,
        min_damage=5,
        max_damage=5,
    )
    perform_wand_attack(
        player,
        wolf,
        wand_fighter,
        engine.message_log,
        world=engine.world,
        game_map=engine.game_map,
        rng=rng,
    )

    registry = load_rescue_gratitude_registry()
    possible = [format_rescue_gratitude(knight, template) for template in registry.lines]
    assert any(line in engine.message_log.lines() for line in possible)
    assert Engulfed not in knight.tags


def test_gratitude_uses_proper_name_when_set() -> None:
    engine = GameEngine()
    wolf, knight = _wolf_holding_good_prey(engine)
    knight.components[ProperName] = ProperName(name="Sir Test")
    rng = random.Random(2)
    release_prey_if_defeated_predator(
        engine.world,
        wolf,
        engine.game_map,
        engine.message_log,
        rng=rng,
        rescuer=engine.player,
    )
    lines = engine.message_log.lines()
    assert any("Sir Test" in line for line in lines)
    assert not any("the knight" in line for line in lines if "grateful" in line or "thanks" in line)


def test_knight_rescuer_no_gratitude() -> None:
    engine = GameEngine()
    wolf, knight = _wolf_holding_good_prey(engine)
    wolf.components[Fighter].hp = 1
    wolf_pos = wolf.components[Position]
    rescuer_pos = ensure_adjacent_floor(engine, wolf_pos, (-1, 0))
    rescuer = spawn_test_npc(
        engine.world,
        x=rescuer_pos.x,
        y=rescuer_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        species_id="knight",
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=5,
        max_damage=5,
    )
    try_action(
        engine.world,
        engine.game_map,
        rescuer,
        (1, 0),
        engine.message_log,
        rng=random.Random(0),
    )

    lines = engine.message_log.lines()
    assert messages.npc_freed_from_predator("The knight", "the wolf") in lines
    gratitude_markers = ("grateful", "thanks you profusely", "Thank you, says", "thanks you for the rescue")
    assert not any(any(marker in line for marker in gratitude_markers) for line in lines)


def test_neutral_prey_no_gratitude() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf, rabbit = _wolf_holding_rabbit(engine)
    wolf.components[Fighter].hp = 1
    rng = random.Random(0)
    for _ in range(20):
        try_action(
            engine.world,
            engine.game_map,
            player,
            (1, 0),
            engine.message_log,
            rng=rng,
        )
        if wolf not in list(iter_wolves(engine)):
            break

    lines = engine.message_log.lines()
    assert messages.npc_freed_from_predator("The rabbit", "the wolf") in lines
    gratitude_markers = ("grateful", "thanks you profusely", "Thank you, says")
    assert not any(any(marker in line for marker in gratitude_markers) for line in lines)