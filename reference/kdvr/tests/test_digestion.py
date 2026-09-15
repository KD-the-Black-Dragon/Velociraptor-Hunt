"""Digestion: foundation, NPC ticks, and player game over."""

from __future__ import annotations

import random
from unittest.mock import patch

import pytest
import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.components import (
    AI,
    Alignment,
    DigestionStats,
    DigestionStrikes,
    DisplayName,
    Engulfed,
    Fighter,
    Position,
    Predator,
    Stunned,
    VoreCapable,
    VoreMercy,
)
from src import messages
from src.constants import (
    NATURAL_REGEN_EVERY_N_PLAYER_TURNS,
)
from src.systems.inventory import effective_fighter
from src.components import EquipState
from src.systems.combat import try_action
from src.digestion_content import DIGESTION_COMPLETE_POOL
from src.systems.digestion import (
    apply_digestion_tick,
    apply_player_digestion_tick,
    player_digestion_modal_line,
)
from src.systems.vore import engulf_player, try_struggle
from src.engine import GameEngine
from src.data.entity_loader import EntityLoadError, parse_entity_registry
from src.spawn import spawn_entity_by_id
from src.systems.ai import run_monster_turns, spawn_test_npc
from src.systems.combat import try_action
from src.systems.fov import update_fov
from src.systems.vore import (
    engulf_npc,
    release_npc_engulfed,
    should_attempt_vore,
    try_resolve_npc_vore,
)

from tests.digest_test_helpers import (
    expected_default_digest_time,
    minimal_evil_entity_payload,
    pin_predator_digest_stats,
    spawn_evil_from_fixture,
)
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_adjacent_line,
    carve_east_of,
    carve_floor_rect,
    ensure_adjacent_floor,
    first_wolf,
    iter_wolves,
)


def _adjacent_stunned_knight_setup(engine: GameEngine):
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    wolf_tile, knight_tile = carve_adjacent_line(engine, player_pos, 2)
    wolf = first_wolf(engine)
    knight = spawn_test_npc(
        engine.world,
        x=knight_tile.x,
        y=knight_tile.y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=5,
    )
    knight.components[Fighter].hp = 0
    knight.tags.add(Stunned)
    wolf.components[Position] = wolf_tile
    update_fov(engine.game_map, player_pos.x, player_pos.y)
    return wolf, knight


def test_evil_spawn_has_digestion_stats() -> None:
    engine = GameEngine()
    wolf = first_wolf(engine)
    stats = wolf.components.get(DigestionStats)
    assert stats is not None
    assert stats.damage_per_tick >= 1
    assert stats.digest_time >= 1


def test_engulf_stores_narrative_type_on_predator() -> None:
    engine = GameEngine()
    wolf, knight = _adjacent_stunned_knight_setup(engine)
    with patch("src.systems.vore.pick_attempt_narrative_type", return_value="AV"):
        with patch("src.systems.vore.resolve_vore_hit", return_value=True):
            with patch("src.systems.vore.should_attempt_vore", return_value=True):
                assert try_resolve_npc_vore(
                    wolf,
                    engine.world,
                    engine.game_map,
                    engine.message_log,
                    random.Random(0),
                )
    predator_state = wolf.components.get(Predator)
    assert predator_state is not None
    assert predator_state.narrative_type == "AV"


def test_npc_release_grants_vore_mercy() -> None:
    engine = GameEngine()
    wolf, knight = _adjacent_stunned_knight_setup(engine)
    engulf_npc(engine.world, knight, wolf, narrative_type="CV")
    release_npc_engulfed(
        engine.world,
        knight,
        wolf,
        engine.game_map,
        engine.message_log,
        rng=random.Random(0),
    )
    assert VoreMercy in knight.tags
    assert Engulfed not in knight.tags
    assert wolf.components.get(Predator) is None


def test_vore_mercy_blocks_npc_re_engulf() -> None:
    engine = GameEngine()
    wolf, knight = _adjacent_stunned_knight_setup(engine)
    engulf_npc(engine.world, knight, wolf, narrative_type="OV")
    release_npc_engulfed(
        engine.world,
        knight,
        wolf,
        engine.game_map,
        engine.message_log,
        rng=random.Random(0),
    )
    assert VoreMercy in knight.tags
    assert should_attempt_vore(wolf, knight, engine.game_map, random.Random(0)) is False


def test_vore_mercy_blocks_npc_combat_damage() -> None:
    engine = GameEngine()
    wolf, knight = _adjacent_stunned_knight_setup(engine)
    engulf_npc(engine.world, knight, wolf, narrative_type="OV")
    release_npc_engulfed(
        engine.world,
        knight,
        wolf,
        engine.game_map,
        engine.message_log,
        rng=random.Random(0),
    )
    knight.components[Fighter].hp = 5
    knight.components[Position] = Position(
        wolf.components[Position].x + 1,
        wolf.components[Position].y,
    )
    hp_before = knight.components[Fighter].hp
    try_action(
        engine.world,
        engine.game_map,
        wolf,
        (1, 0),
        engine.message_log,
    )
    assert knight.components[Fighter].hp == hp_before


def _clear_npcs(engine: GameEngine) -> None:
    for entity in list(engine.world.Q.all_of(components=[AI])):
        if entity is engine.player:
            continue
        entity.clear()


def _adjacent_walkable_pair(engine: GameEngine) -> tuple[Position, Position]:
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 1, ARENA_Y)
    return Position(ARENA_X, ARENA_Y), Position(ARENA_X + 1, ARENA_Y)


def _place_player_with_los_to(engine: GameEngine, target: Position) -> None:
    player = engine.player
    assert player is not None
    dest = ensure_adjacent_floor(engine, target, (-1, 0))
    player.components[Position] = dest
    update_fov(engine.game_map, dest.x, dest.y)


def test_predator_attack_only_while_holding() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    wolf_pos, knight_pos = _adjacent_walkable_pair(engine)
    player.components[Position] = Position(0, 0)
    wolf = spawn_entity_by_id(engine.world, "wolf", wolf_pos.x, wolf_pos.y)

    prey = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
        hp=1,
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=0,
        max_damage=0,
    )
    prey.components[Fighter].hp = 0
    prey.tags.add(Stunned)
    engulf_npc(engine.world, prey, wolf, narrative_type="OV")

    target = spawn_test_npc(
        engine.world,
        x=knight_pos.x,
        y=knight_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=10,
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=0,
        max_damage=0,
    )
    target_hp_before = target.components[Fighter].hp
    wolf_pos_before = wolf.components[Position]

    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
    )

    assert wolf.components[Position] == wolf_pos_before
    assert target.components[Fighter].hp < target_hp_before


def test_holding_predator_does_not_attack_adjacent_evil() -> None:
    """Evil holding prey must never melee another evil (player or NPC prey)."""
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 2, ARENA_Y)
    wolf_pos = Position(ARENA_X + 1, ARENA_Y)
    other_pos = Position(ARENA_X, ARENA_Y)
    player.components[Position] = Position(0, 0)

    wolf = spawn_entity_by_id(engine.world, "wolf", wolf_pos.x, wolf_pos.y)
    other = spawn_entity_by_id(engine.world, "wolf", other_pos.x, other_pos.y)
    prey = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
        hp=1,
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=0,
        max_damage=0,
    )
    engulf_npc(engine.world, prey, wolf, narrative_type="OV")

    other_hp_before = other.components[Fighter].hp
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
    )
    assert other.components[Fighter].hp == other_hp_before


def test_holding_predator_skips_evil_to_hit_adjacent_good() -> None:
    """When an evil neighbor is scanned first, still punch a valid good target."""
    from src.systems.ai import _try_predator_holding_attack

    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    # West = evil (MOVEMENT_DIRECTIONS typically tries W before E), east = good
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 2, ARENA_Y)
    wolf_pos = Position(ARENA_X + 1, ARENA_Y)
    evil_pos = Position(ARENA_X, ARENA_Y)
    good_pos = Position(ARENA_X + 2, ARENA_Y)
    player.components[Position] = Position(0, 0)

    wolf = spawn_entity_by_id(engine.world, "wolf", wolf_pos.x, wolf_pos.y)
    packmate = spawn_entity_by_id(engine.world, "wolf", evil_pos.x, evil_pos.y)
    knight = spawn_test_npc(
        engine.world,
        x=good_pos.x,
        y=good_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=20,
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=0,
        max_damage=0,
    )
    prey = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
        hp=1,
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=0,
        max_damage=0,
    )
    engulf_npc(engine.world, prey, wolf, narrative_type="OV")

    pack_hp = packmate.components[Fighter].hp
    knight_hp = knight.components[Fighter].hp
    _try_predator_holding_attack(
        engine.world,
        engine.game_map,
        wolf,
        engine.message_log,
        rng=random.Random(0),
    )
    assert packmate.components[Fighter].hp == pack_hp
    assert knight.components[Fighter].hp < knight_hp


def test_try_action_evil_does_not_melee_evil() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 1, ARENA_Y)
    a = spawn_entity_by_id(engine.world, "wolf", ARENA_X, ARENA_Y)
    b = spawn_entity_by_id(engine.world, "wolf", ARENA_X + 1, ARENA_Y)
    hp_before = b.components[Fighter].hp
    asserted = try_action(
        engine.world,
        engine.game_map,
        a,
        (1, 0),
        engine.message_log,
        rng=random.Random(0),
    )
    assert asserted is False
    assert b.components[Fighter].hp == hp_before


def test_predator_cannot_move_while_holding() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    wolf_tile = ensure_adjacent_floor(engine, player_pos, (1, 0))
    wolf = spawn_entity_by_id(engine.world, "wolf", wolf_tile.x, wolf_tile.y)

    prey = spawn_test_npc(
        engine.world,
        x=wolf_tile.x,
        y=wolf_tile.y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
        hp=1,
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=0,
        max_damage=0,
    )
    prey.components[Fighter].hp = 0
    prey.tags.add(Stunned)
    engulf_npc(engine.world, prey, wolf, narrative_type="OV")
    wolf_pos_before = wolf.components[Position]

    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
    )

    assert wolf.components[Position] == wolf_pos_before
    assert wolf.components.get(Predator) is not None


def test_holding_predator_cannot_initiate_vore() -> None:
    engine = GameEngine()
    wolf, knight = _adjacent_stunned_knight_setup(engine)
    rabbit = spawn_test_npc(
        engine.world,
        x=wolf.components[Position].x,
        y=wolf.components[Position].y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
        hp=1,
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=0,
        max_damage=0,
    )
    rabbit.components[Fighter].hp = 0
    rabbit.tags.add(Stunned)
    engulf_npc(engine.world, rabbit, wolf, narrative_type="OV")

    with patch("src.systems.vore.resolve_vore_hit", return_value=True):
        with patch("src.systems.vore.should_attempt_vore", return_value=True):
            assert not try_resolve_npc_vore(
                wolf,
                engine.world,
                engine.game_map,
                engine.message_log,
                random.Random(0),
            )
    assert Engulfed not in knight.tags


def _isolated_engulfed_knight(
    engine: GameEngine,
    *,
    knight_hp: int,
    narrative_type: str = "OV",
    digest_time: int = 3,
) -> tuple[object, object]:
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    wolf_pos, _ = _adjacent_walkable_pair(engine)
    wolf = spawn_entity_by_id(engine.world, "wolf", wolf_pos.x, wolf_pos.y)
    _place_player_with_los_to(engine, wolf_pos)
    knight = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=10,
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=0,
        max_damage=0,
    )
    knight.components[Fighter].hp = knight_hp
    if knight_hp <= 0:
        knight.tags.add(Stunned)
    pin_predator_digest_stats(wolf, digest_time=digest_time)
    engulf_npc(engine.world, knight, wolf, narrative_type=narrative_type)
    return wolf, knight


def _run_world_phase(engine: GameEngine, *, seed: int = 0) -> None:
    player = engine.player
    assert player is not None
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(seed),
    )


def test_digestion_reduces_hp_before_strikes() -> None:
    engine = GameEngine()
    wolf, knight = _isolated_engulfed_knight(engine, knight_hp=5)
    _run_world_phase(engine)
    assert knight.components[Fighter].hp == 2
    assert knight.components.get(DigestionStrikes) is None


def test_no_strike_on_same_tick_as_hp_to_zero() -> None:
    engine = GameEngine()
    wolf, knight = _isolated_engulfed_knight(engine, knight_hp=3)
    _run_world_phase(engine)
    assert knight.components[Fighter].hp == 0
    assert Stunned in knight.tags
    assert knight.components.get(DigestionStrikes) is None


def test_digest_time_strikes_digests_npc() -> None:
    engine = GameEngine()
    wolf, knight = _isolated_engulfed_knight(engine, knight_hp=0)
    for seed in range(3):
        _run_world_phase(engine, seed=seed)
    assert wolf.components.get(Predator) is None
    living_knights = [
        e
        for e in engine.world.Q.all_of(components=[DisplayName])
        if e.components[DisplayName].name == "knight"
    ]
    assert not living_knights


def test_digestion_resets_strikes_on_freedom() -> None:
    engine = GameEngine()
    wolf, knight = _isolated_engulfed_knight(engine, knight_hp=0)
    knight.components[DigestionStrikes] = DigestionStrikes(count=2)
    release_npc_engulfed(
        engine.world,
        knight,
        wolf,
        engine.game_map,
        engine.message_log,
        rng=random.Random(0),
    )
    assert knight.components.get(DigestionStrikes) is None


def test_regen_blocked_when_strikes_ge_1() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    knight = spawn_test_npc(
        engine.world,
        x=player.components[Position].x + 1,
        y=player.components[Position].y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=5,
    )
    knight.components[Fighter].hp = 0
    knight.tags.add(Stunned)
    knight.components[DigestionStrikes] = DigestionStrikes(count=1)
    engine.player_turn_count = NATURAL_REGEN_EVERY_N_PLAYER_TURNS
    engine._apply_natural_regen()
    assert knight.components[Fighter].hp == 0
    assert Stunned in knight.tags


def test_good_plea_message_probabilistic() -> None:
    engine = GameEngine()
    wolf, knight = _isolated_engulfed_knight(engine, knight_hp=0)
    lines_before = len(engine.message_log.lines())
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=0.0):
        apply_digestion_tick(
            knight,
            wolf,
            engine.game_map,
            engine.message_log,
            rng,
        )
    new_lines = engine.message_log.lines()[lines_before:]
    assert new_lines
    assert any(
        any(phrase in line for phrase in ("begs for rescue", "grunts helplessly"))
        for line in new_lines
    )


def test_neutral_silent_on_digestion_tick() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    wolf_pos, _ = _adjacent_walkable_pair(engine)
    wolf = spawn_entity_by_id(engine.world, "wolf", wolf_pos.x, wolf_pos.y)
    _place_player_with_los_to(engine, wolf_pos)
    rabbit = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
        hp=1,
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=0,
        max_damage=0,
    )
    rabbit.components[Fighter].hp = 0
    rabbit.tags.add(Stunned)
    engulf_npc(engine.world, rabbit, wolf, narrative_type="OV")
    lines_before = len(engine.message_log.lines())
    apply_digestion_tick(
        rabbit,
        wolf,
        engine.game_map,
        engine.message_log,
        random.Random(0),
    )
    new_lines = engine.message_log.lines()[lines_before:]
    assert not new_lines


def test_completion_message_uses_narrative_type() -> None:
    engine = GameEngine()
    wolf, knight = _isolated_engulfed_knight(engine, knight_hp=0, narrative_type="CV")
    knight.components[DigestionStrikes] = DigestionStrikes(count=2)
    lines_before = len(engine.message_log.lines())
    apply_digestion_tick(
        knight,
        wolf,
        engine.game_map,
        engine.message_log,
        random.Random(0),
    )
    new_lines = engine.message_log.lines()[lines_before:]
    assert new_lines
    assert any(line.strip() for line in new_lines)


def test_predator_unbound_after_digest_next_turn() -> None:
    engine = GameEngine()
    wolf, _knight = _isolated_engulfed_knight(engine, knight_hp=0)
    for seed in range(3):
        _run_world_phase(engine, seed=seed)
    assert wolf.components.get(Predator) is None
    _run_world_phase(engine, seed=99)
    assert wolf.components.get(Predator) is None


def _press(engine: GameEngine, sym: KeySym) -> bool:
    return engine.handle_event(
        tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=Modifier.NONE),
    )


def _engulf_player_on_wolf(
    engine: GameEngine,
    *,
    narrative_type: str = "OV",
    player_hp: int | None = None,
    digest_time: int = 3,
) -> tuple[object, object]:
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    wolf.components[Position] = Position(pos.x + 1, pos.y)
    pin_predator_digest_stats(wolf, digest_time=digest_time)
    engulf_player(
        engine.world,
        player,
        wolf,
        engine.message_log,
        narrative_type=narrative_type,
    )
    if player_hp is not None:
        player.components[Fighter].hp = player_hp
        if player_hp <= 0:
            player.tags.add(Stunned)
    return player, wolf


def test_player_digestion_strike_cadence() -> None:
    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine, player_hp=0)
    first = apply_player_digestion_tick(player, wolf)
    assert first.open_modal is False
    assert first.strike_added is True
    assert player.components[DigestionStrikes].count == 1
    second = apply_player_digestion_tick(player, wolf)
    assert second.open_modal is False
    assert second.strike_added is True
    assert player.components[DigestionStrikes].count == 2
    third = apply_player_digestion_tick(player, wolf)
    assert third.open_modal is True
    assert third.strike_added is True


def test_player_digestion_reduces_hp_before_strikes() -> None:
    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine, player_hp=5)
    equip = player.components.get(EquipState)
    if equip is not None:
        equip.worn_slot = None
    raw_tick = wolf.components[DigestionStats].damage_per_tick
    apply_player_digestion_tick(player, wolf)
    assert player.components[Fighter].hp == 5 - raw_tick
    assert player.components.get(DigestionStrikes) is None


def test_player_third_strike_opens_modal() -> None:
    engine = GameEngine()
    _engulf_player_on_wolf(engine, player_hp=0, narrative_type="AV")
    for _ in range(2):
        _press(engine, KeySym.PERIOD)
    assert not engine.digestion_modal.active
    _press(engine, KeySym.PERIOD)
    assert engine.digestion_modal.active
    assert engine.digestion_modal.line.strip()


def _advance_digestion_modal(engine: GameEngine) -> None:
    while engine.digestion_modal.active:
        _press(engine, KeySym.RETURN)


def test_game_over_screen_shows_digested_by() -> None:
    from tests.ui_test_helpers import render_engine_frame

    engine = GameEngine()
    engine.run_stats.monsters_defeated = 4
    engine.run_stats.runes_collected = 2
    _engulf_player_on_wolf(engine, player_hp=0)
    for _ in range(3):
        _press(engine, KeySym.PERIOD)
    _advance_digestion_modal(engine)
    assert engine.game_over.active
    assert engine.game_over.player_name == "Player"
    assert engine.game_over.ending is not None
    assert engine.game_over.ending.kind == "digested"
    assert engine.game_over.ending.detail == "wolf"
    assert engine.game_over.monsters_defeated == 4
    assert engine.game_over.runes_collected == 2
    assert engine.game_over.depth == engine.floor_depth
    assert Engulfed not in engine.player.tags

    console = render_engine_frame(engine)
    rendered = ""
    for y in range(console.height):
        rendered += "".join(
            chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
            for x in range(console.width)
        )
    assert "Monsters defeated: 4" in rendered
    assert "Runes collected: 2" in rendered
    assert f"Depth: {engine.floor_depth}" in rendered


def test_game_over_enter_dismisses_recap() -> None:
    from src.engine import EngineEventResult

    engine = GameEngine()
    _engulf_player_on_wolf(engine, player_hp=0)
    for _ in range(3):
        _press(engine, KeySym.PERIOD)
    _advance_digestion_modal(engine)
    assert _press(engine, KeySym.RETURN) is EngineEventResult.RECAP_DISMISSED


def test_engulfed_player_immune_to_combat_damage() -> None:
    from tests.map_test_helpers import ensure_wolves

    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine, player_hp=10)
    wolves = ensure_wolves(engine, 2)
    hunter = next(e for e in wolves if e is not wolf)
    hunter.components[Position] = Position(
        wolf.components[Position].x + 1,
        wolf.components[Position].y,
    )
    hp_before = player.components[Fighter].hp
    try_action(
        engine.world,
        engine.game_map,
        hunter,
        (-1, 0),
        engine.message_log,
    )
    assert player.components[Fighter].hp == hp_before
    assert not any("hits you" in line for line in engine.message_log.lines())


def test_player_strike_increments_log_digestion_message() -> None:
    engine = GameEngine()
    _engulf_player_on_wolf(engine, player_hp=0)
    _press(engine, KeySym.PERIOD)
    assert messages.player_being_digested() in engine.message_log.lines()


def test_engulfed_player_no_regen_clears_stunned_on_strike_turn() -> None:
    engine = GameEngine()
    player, _wolf = _engulf_player_on_wolf(engine, player_hp=0)
    engine.player_turn_count = NATURAL_REGEN_EVERY_N_PLAYER_TURNS
    _press(engine, KeySym.PERIOD)
    assert player.components[Fighter].hp == 0
    assert Stunned in player.tags
    assert messages.no_longer_stunned() not in engine.message_log.lines()


def test_struggle_and_digestion_same_turn() -> None:
    engine = GameEngine()
    player, wolf = _engulf_player_on_wolf(engine, player_hp=6)
    wolf.components[Fighter].hp = 30
    equip = player.components.get(EquipState)
    if equip is not None:
        equip.worn_slot = None
    raw_tick = wolf.components[DigestionStats].damage_per_tick
    # Deterministic half-melee struggle damage (min == max).
    from src.components import PlayerProgression

    progression = player.components.get(PlayerProgression) or PlayerProgression()
    player.components[PlayerProgression] = progression
    ef = effective_fighter(player)
    progression.bonus_min_damage += 4 - ef.min_damage
    progression.bonus_max_damage += 4 - ef.max_damage
    with patch.object(engine.rng, "random", return_value=1.0):
        _press(engine, KeySym.UP)
    assert Engulfed in player.tags
    assert player.components[Fighter].hp == 6 - raw_tick
    assert wolf.components[Fighter].hp == 30 - 2  # half of 4
    assert player.components.get(DigestionStrikes) is None


def test_custom_digest_time_requires_n_strikes() -> None:
    engine = GameEngine()
    wolf, knight = _isolated_engulfed_knight(engine, knight_hp=0, digest_time=5)
    for seed in range(4):
        _run_world_phase(engine, seed=seed)
    assert wolf.components.get(Predator) is not None
    living_knights = [
        e
        for e in engine.world.Q.all_of(components=[DisplayName])
        if e.components[DisplayName].name == "knight"
    ]
    assert living_knights
    _run_world_phase(engine, seed=99)
    assert wolf.components.get(Predator) is None
    living_knights = [
        e
        for e in engine.world.Q.all_of(components=[DisplayName])
        if e.components[DisplayName].name == "knight"
    ]
    assert not living_knights


def test_digest_time_default_when_omitted() -> None:
    from tcod.ecs import Registry

    payload = {
        "schema_version": 1,
        "entities": [minimal_evil_entity_payload("slow_predator", digest_time=None)],
    }
    definition = parse_entity_registry(payload).get("slow_predator")
    assert definition.digest_time is None
    world = Registry()
    predator = spawn_evil_from_fixture(world, entity_id="slow_predator")
    stats = predator.components[DigestionStats]
    assert stats.digest_time == expected_default_digest_time()


def test_digest_time_load_error_on_good_entity() -> None:
    payload = {
        "schema_version": 1,
        "entities": [
            minimal_evil_entity_payload(
                "knight",
                alignment="good",
                digest_time=3,
            )
        ],
    }
    with pytest.raises(EntityLoadError, match="digest_time is only valid for evil"):
        parse_entity_registry(payload)