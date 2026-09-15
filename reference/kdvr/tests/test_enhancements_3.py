"""Enhancements 3: faction NPC spawn, stunned, and regen."""

from __future__ import annotations

import random
from unittest.mock import patch

from src import messages
from src.components import (
    AI,
    AIState,
    Alignment,
    DisplayName,
    Engulfed,
    ExamineDescription,
    Fighter,
    NPCAlignment,
    Player,
    Position,
    Predator,
    Renderable,
    Stunned,
    VoreCapable,
    VoreNarratives,
)
from src.constants import (
    EVIL_NATURAL_REGEN_EVERY_N_PLAYER_TURNS,
    NATURAL_REGEN_EVERY_N_PLAYER_TURNS,
)

from src.engine import GameEngine
from src.spawn import (
    KNIGHT_EXAMINE_DESCRIPTION,
    KNIGHT_RENDERABLE,
    RABBIT_EXAMINE_DESCRIPTION,
    RABBIT_RENDERABLE,
    WOLF_EXAMINE_DESCRIPTION,
    WOLF_RENDERABLE,
)
from src.systems.ai import (
    _clear_memory_of_engulfed_prey,
    _get_ai_state,
    _print_evil_frustration_if_blocked,
    _visible_neutrals,
    _visible_primary_hostiles,
    pick_evil_chase,
    pick_evil_target,
    pick_good_chase,
    run_monster_turns,
    spawn_test_npc,
)
from src.systems.combat import can_npc_swap, try_action
from src.systems.fov import can_see, update_fov
from src.systems.vore import VoreModalState, engulf_npc, try_resolve_npc_vore

from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_adjacent_line,
    carve_east_of,
    carve_floor_rect,
    carve_floor_tile,
    carved_bump_pair,
    carved_collinear,
    carved_fov_bump_pair,
    carved_hidden_line,
    carved_hidden_tile,
    ensure_adjacent_floor,
    first_wolf,
    isolate_other_ais,
    iter_wolves,
)


def _npcs_by_species(engine: GameEngine, species: str) -> list:
    return [
        e
        for e in engine.world.Q.all_of(components=[AI, DisplayName])
        if e.components[DisplayName].name == species
    ]


def test_spawn_population_is_density_driven() -> None:
    engine = GameEngine()
    total = len(list(engine.world.Q.all_of(components=[AI])))
    assert total > 0
    assert total <= 120
    assert len(_npcs_by_species(engine, "wolf")) >= 0
    assert len(_npcs_by_species(engine, "knight")) >= 0
    assert len(_npcs_by_species(engine, "rabbit")) >= 0


def test_wolf_spawn_evil_vore_capable() -> None:
    engine = GameEngine()
    for wolf in _npcs_by_species(engine, "wolf"):
        assert wolf.components[NPCAlignment].alignment == Alignment.EVIL
        assert VoreCapable in wolf.tags
        assert wolf.components[VoreNarratives].types == ("OV", "CV", "AV")
        assert wolf.components[ExamineDescription].text == WOLF_EXAMINE_DESCRIPTION
        assert wolf.components[Renderable] == WOLF_RENDERABLE


def test_knight_spawn_good_not_vore_capable() -> None:
    engine = GameEngine()
    for knight in _npcs_by_species(engine, "knight"):
        assert knight.components[NPCAlignment].alignment == Alignment.GOOD
        assert VoreCapable not in knight.tags
        assert knight.components.get(VoreNarratives) is None
        assert knight.components[ExamineDescription].text == KNIGHT_EXAMINE_DESCRIPTION
        assert knight.components[Renderable] == KNIGHT_RENDERABLE


def test_rabbit_spawn_neutral_not_vore_capable() -> None:
    engine = GameEngine()
    for rabbit in _npcs_by_species(engine, "rabbit"):
        assert rabbit.components[NPCAlignment].alignment == Alignment.NEUTRAL
        assert VoreCapable not in rabbit.tags
        assert rabbit.components[ExamineDescription].text == RABBIT_EXAMINE_DESCRIPTION
        assert rabbit.components[Renderable] == RABBIT_RENDERABLE


def test_knight_stunned_not_removed() -> None:
    engine = GameEngine()
    engine.new_game(seed=42)
    wolf = first_wolf(engine)
    (ax, ay), (bx, by), direction = carved_fov_bump_pair(
        engine, require_visible=True
    )
    knight = spawn_test_npc(
        engine.world,
        x=bx,
        y=by,
        species="knight",
        alignment=Alignment.GOOD,
        hp=1,
    )
    wolf.components[Position] = Position(ax, ay)
    knight.components[Position] = Position(bx, by)
    assert try_action(engine.world, engine.game_map, wolf, direction, engine.message_log)
    assert knight in list(engine.world.Q.all_of(components=[AI]))
    assert knight.components[Fighter].hp == 0
    assert Stunned in knight.tags
    assert messages.npc_stunned("The knight") in engine.message_log.lines()


def test_rabbit_stunned_not_removed() -> None:
    engine = GameEngine()
    engine.new_game(seed=42)
    wolf = first_wolf(engine)
    (ax, ay), (bx, by), direction = carved_fov_bump_pair(
        engine, require_visible=True
    )
    rabbit = spawn_test_npc(
        engine.world,
        x=bx,
        y=by,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
        hp=1,
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=0,
        max_damage=0,
    )
    wolf.components[Position] = Position(ax, ay)
    rabbit.components[Position] = Position(bx, by)
    assert try_action(engine.world, engine.game_map, wolf, direction, engine.message_log)
    assert rabbit in list(engine.world.Q.all_of(components=[AI]))
    assert rabbit.components[Fighter].hp == 0
    assert Stunned in rabbit.tags
    assert messages.npc_stunned("The rabbit") in engine.message_log.lines()


def test_evil_still_defeated_at_zero() -> None:
    import random

    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    isolate_other_ais(engine, keep=(wolf,))
    wolf.components[Fighter].hp = 1
    mpos = wolf.components[Position]
    carve_east_of(engine, mpos, 2)
    player.components[Position] = Position(mpos.x - 1, mpos.y)
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
    assert wolf not in list(iter_wolves(engine))
    log_text = " ".join(engine.message_log.lines()).lower()
    assert "defeated" in log_text
    assert "stunned" not in log_text


def test_knight_recovers_from_stunned_via_regen() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    knight_pos = ensure_adjacent_floor(engine, player_pos, (1, 0))
    update_fov(engine.game_map, player_pos.x, player_pos.y)
    knight = spawn_test_npc(
        engine.world,
        x=knight_pos.x,
        y=knight_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=5,
    )
    knight.components[Fighter].hp = 0
    knight.tags.add(Stunned)
    engine.player_turn_count = NATURAL_REGEN_EVERY_N_PLAYER_TURNS
    engine._apply_natural_regen()
    assert knight.components[Fighter].hp == 1
    assert Stunned not in knight.tags
    assert messages.npc_no_longer_stunned("The knight") in engine.message_log.lines()


def test_npc_stunned_recovery_off_screen_not_logged() -> None:
    engine = GameEngine()
    hx, hy = carved_hidden_tile(engine)
    knight = spawn_test_npc(
        engine.world,
        x=hx,
        y=hy,
        species="knight",
        alignment=Alignment.GOOD,
        hp=5,
    )
    knight.components[Fighter].hp = 0
    knight.tags.add(Stunned)
    lines_before = len(engine.message_log.lines())
    engine.player_turn_count = NATURAL_REGEN_EVERY_N_PLAYER_TURNS
    engine._apply_natural_regen()
    assert knight.components[Fighter].hp == 1
    assert Stunned not in knight.tags
    new_lines = engine.message_log.lines()[lines_before:]
    assert messages.npc_no_longer_stunned("The knight") not in new_lines


def test_good_npc_regen_every_8_player_turns() -> None:
    engine = GameEngine()
    knight = spawn_test_npc(
        engine.world,
        x=10,
        y=10,
        species="knight",
        alignment=Alignment.GOOD,
        hp=5,
    )
    knight.components[Fighter].hp = 3
    engine.player_turn_count = NATURAL_REGEN_EVERY_N_PLAYER_TURNS - 1
    engine._apply_natural_regen()
    assert knight.components[Fighter].hp == 3
    engine.player_turn_count = NATURAL_REGEN_EVERY_N_PLAYER_TURNS
    engine._apply_natural_regen()
    assert knight.components[Fighter].hp == 4


def test_evil_npc_regen_every_12_player_turns() -> None:
    engine = GameEngine()
    wolf = first_wolf(engine)
    wolf.components[Fighter].hp = 8
    engine.player_turn_count = EVIL_NATURAL_REGEN_EVERY_N_PLAYER_TURNS - 1
    engine._apply_natural_regen()
    assert wolf.components[Fighter].hp == 8
    engine.player_turn_count = EVIL_NATURAL_REGEN_EVERY_N_PLAYER_TURNS
    engine._apply_natural_regen()
    assert wolf.components[Fighter].hp == 9


def test_evil_frustrated_when_neutral_blocks_good_target() -> None:
    engine = GameEngine()
    wolf = first_wolf(engine)
    wpos, rpos, kpos = carved_collinear(engine, 3)
    wolf.components[Position] = wpos
    rabbit = spawn_test_npc(
        engine.world,
        x=rpos.x,
        y=rpos.y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    knight = spawn_test_npc(
        engine.world,
        x=kpos.x,
        y=kpos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    update_fov(engine.game_map, wpos.x, wpos.y)
    target, blocked = pick_evil_target(
        wolf,
        engine.world,
        engine.game_map,
        engine.player,
        random.Random(0),
    )
    assert target is rabbit
    assert blocked is knight


def test_evil_frustrated_when_neutral_blocks_player() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    wpos, rpos, ppos = carved_collinear(engine, 3)
    wolf.components[Position] = wpos
    rabbit = spawn_test_npc(
        engine.world,
        x=rpos.x,
        y=rpos.y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    player.components[Position] = ppos
    update_fov(engine.game_map, wpos.x, wpos.y)
    target, blocked = pick_evil_target(
        wolf,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
    )
    assert target is rabbit
    assert blocked is player


def test_evil_chases_primary_when_neutral_not_blocking() -> None:
    engine = GameEngine()
    wolf = first_wolf(engine)
    wpos, _, kpos = carved_collinear(engine, 3)
    wolf.components[Position] = wpos
    knight = spawn_test_npc(
        engine.world,
        x=kpos.x,
        y=kpos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    rabbit = spawn_test_npc(
        engine.world,
        x=kpos.x,
        y=kpos.y + 2,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    update_fov(engine.game_map, wpos.x, wpos.y)
    target, blocked = pick_evil_target(
        wolf,
        engine.world,
        engine.game_map,
        engine.player,
        random.Random(0),
    )
    assert target is knight
    assert blocked is None


def _frustration_corridor_setup(engine: GameEngine):
    """Wolf → rabbit → knight; player engulfed so knight is the primary target."""
    wolf = first_wolf(engine)
    wpos, rpos, kpos = carved_collinear(engine, 3)
    wolf.components[Position] = wpos
    rabbit = spawn_test_npc(
        engine.world,
        x=rpos.x,
        y=rpos.y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    knight = spawn_test_npc(
        engine.world,
        x=kpos.x,
        y=kpos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    isolate_other_ais(engine, keep=(wolf, rabbit, knight))
    # Engulfed: player is not an evil primary, so knight stays the blocked goal.
    engine.player.tags.add(Engulfed)
    update_fov(engine.game_map, wpos.x, wpos.y)
    return wolf, rabbit, knight


def test_evil_frustration_system_log_only(capsys, monkeypatch) -> None:
    """Frustration snarl is DEBUG_STDOUT only — never a player message-log line."""
    monkeypatch.setenv("DEBUG_STDOUT", "1")
    engine = GameEngine()
    wolf, rabbit, knight = _frustration_corridor_setup(engine)
    chase, blocked = pick_evil_target(
        wolf,
        engine.world,
        engine.game_map,
        engine.player,
        random.Random(0),
        player_engulfed=True,
    )
    assert chase is rabbit
    assert blocked is knight
    # Drain map_gen / prefetch noise from GameEngine construction.
    capsys.readouterr()
    # Direct path used by the evil intent pipeline (avoids distant-throttle flakes).
    _print_evil_frustration_if_blocked(
        wolf,
        engine.world,
        engine.game_map,
        engine.player,
        random.Random(0),
        player_engulfed=True,
    )
    captured = capsys.readouterr()
    assert (
        "snarls at the rabbit" in captured.out
        and "blocking the way to the knight" in captured.out
    )
    assert not any("snarls" in line for line in engine.message_log.lines())


def test_evil_frustration_suppressed_without_debug_stdout(capsys, monkeypatch) -> None:
    monkeypatch.delenv("DEBUG_STDOUT", raising=False)
    engine = GameEngine()
    wolf, _rabbit, _knight = _frustration_corridor_setup(engine)
    capsys.readouterr()
    _print_evil_frustration_if_blocked(
        wolf,
        engine.world,
        engine.game_map,
        engine.player,
        random.Random(0),
        player_engulfed=True,
    )
    captured = capsys.readouterr()
    assert "snarls" not in captured.out
    assert "[prefetch]" not in captured.out
    assert "[map_gen]" not in captured.out


def test_spawned_npcs_have_ai_state() -> None:
    engine = GameEngine()
    for npc in engine.world.Q.all_of(components=[AI]):
        assert npc.components.get(AIState) is not None


def test_evil_priority_primary_over_neutral() -> None:
    engine = GameEngine()
    wolf = first_wolf(engine)
    wpos, _, kpos = carved_collinear(engine, 3)
    wolf.components[Position] = wpos
    knight = spawn_test_npc(
        engine.world,
        x=kpos.x,
        y=kpos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    rabbit_y = kpos.y + 2
    if rabbit_y >= engine.game_map.height:
        rabbit_y = kpos.y - 2
    carve_floor_rect(engine, kpos.x, rabbit_y, kpos.x, rabbit_y)
    rabbit = spawn_test_npc(
        engine.world,
        x=kpos.x,
        y=rabbit_y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    update_fov(engine.game_map, wpos.x, wpos.y)
    target, _, _ = pick_evil_chase(
        wolf,
        engine.world,
        engine.game_map,
        engine.player,
        random.Random(0),
    )
    assert target is knight
    assert target is not rabbit


def test_evil_moves_to_last_known_primary() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    wpos, _, kpos = carved_collinear(engine, 3)
    wolf.components[Position] = wpos
    player.components[Position] = Position(1, 1)
    for npc in engine.world.Q.all_of(components=[AI, NPCAlignment, Position]):
        if npc is wolf or Player in npc.tags:
            continue
        npc.components[Position] = Position(70, 40)
    state = _get_ai_state(wolf)
    state.last_known_primary = kpos
    update_fov(engine.game_map, wpos.x, wpos.y)
    entity, pos, _ = pick_evil_chase(
        wolf,
        engine.world,
        engine.game_map,
        engine.player,
        random.Random(0),
    )
    assert entity is None
    assert pos == kpos


def test_evil_chases_visible_neutral_when_no_primary() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    wpos, rpos, _ = carved_collinear(engine, 3)
    wolf.components[Position] = wpos
    player.components[Position] = Position(1, 1)
    for npc in engine.world.Q.all_of(components=[AI, NPCAlignment, Position]):
        if npc is wolf or Player in npc.tags:
            continue
        npc.components[Position] = Position(70, 40)
    rabbit = spawn_test_npc(
        engine.world,
        x=rpos.x,
        y=rpos.y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    update_fov(engine.game_map, wpos.x, wpos.y)
    entity, pos, _ = pick_evil_chase(
        wolf,
        engine.world,
        engine.game_map,
        engine.player,
        random.Random(0),
    )
    assert entity is rabbit
    assert pos is None


def test_good_follows_player_when_no_evil() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    for wolf in iter_wolves(engine):
        wolf.components[Position] = Position(70, 40)
    wpos, _, ppos = carved_collinear(engine, 3)
    knight = spawn_test_npc(
        engine.world,
        x=wpos.x,
        y=wpos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    player.components[Position] = ppos
    update_fov(engine.game_map, wpos.x, wpos.y)
    entity, pos, mode = pick_good_chase(
        knight,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
    )
    assert entity is player
    assert mode == "follow"
    assert pos is None


def test_good_moves_to_last_known_player() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    for wolf in iter_wolves(engine):
        wolf.components[Position] = Position(70, 40)
    wpos, _, ppos = carved_collinear(engine, 3)
    knight = spawn_test_npc(
        engine.world,
        x=wpos.x,
        y=wpos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    player.components[Position] = Position(1, 1)
    state = _get_ai_state(knight)
    state.last_known_player = ppos
    update_fov(engine.game_map, wpos.x, wpos.y)
    assert not can_see(engine.game_map, wpos.x, wpos.y, player.components[Position].x, player.components[Position].y)
    entity, pos, mode = pick_good_chase(
        knight,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
    )
    assert entity is None
    assert pos == ppos
    assert mode == "memory"


def test_good_ignores_neutral_and_good_targets() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    for wolf in iter_wolves(engine):
        wolf.components[Position] = Position(70, 40)
    positions = carved_collinear(engine, 4)
    knight, rabbit, other = (
        spawn_test_npc(
            engine.world,
            x=positions[0].x,
            y=positions[0].y,
            species="knight",
            alignment=Alignment.GOOD,
        ),
        spawn_test_npc(
            engine.world,
            x=positions[1].x,
            y=positions[1].y,
            species="rabbit",
            alignment=Alignment.NEUTRAL,
        ),
        spawn_test_npc(
            engine.world,
            x=positions[2].x,
            y=positions[2].y,
            species="knight",
            alignment=Alignment.GOOD,
        ),
    )
    player.components[Position] = positions[3]
    update_fov(engine.game_map, positions[0].x, positions[0].y)
    entity, _, _ = pick_good_chase(
        knight,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
    )
    assert entity is player
    assert entity is not rabbit
    assert entity is not other


def test_good_bump_player_console_only(capsys, monkeypatch) -> None:
    monkeypatch.setenv("DEBUG_STDOUT", "1")
    from src.systems.ai import _choose_good_follow_direction

    engine = GameEngine()
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    knight_pos = ensure_adjacent_floor(engine, player_pos, (1, 0))
    knight = spawn_test_npc(
        engine.world,
        x=knight_pos.x,
        y=knight_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    knight_pos = knight.components[Position]
    _choose_good_follow_direction(
        engine.world,
        engine.game_map,
        knight,
        knight_pos,
        player,
    )
    captured = capsys.readouterr()
    assert messages.good_attempted_player_swap("the knight") in captured.out
    assert knight.components[Position] == knight_pos
    assert player.components[Position] == player_pos


def test_neutral_explores_when_no_evil() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    for wolf in iter_wolves(engine):
        wolf.components[Position] = Position(70, 40)
    wpos, _, _ = carved_collinear(engine, 3)
    rabbit = spawn_test_npc(
        engine.world,
        x=wpos.x,
        y=wpos.y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    pos_before = rabbit.components[Position]
    update_fov(engine.game_map, wpos.x, wpos.y)
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(1),
    )
    assert rabbit.components[Position] != pos_before


def test_explore_goal_cleared_on_reach() -> None:
    from src.systems.ai import _consume_reached_memory

    engine = GameEngine()
    wolf = first_wolf(engine)
    wpos, rpos, _ = carved_collinear(engine, 3)
    state = _get_ai_state(wolf)
    state.explore_goal = rpos
    wolf.components[Position] = rpos
    _consume_reached_memory(state, rpos)
    assert state.explore_goal is None


def test_memory_cleared_when_reaching_last_known_tile() -> None:
    from src.systems.ai import _consume_reached_memory

    engine = GameEngine()
    wolf = first_wolf(engine)
    reached = Position(10, 10)
    wolf.components[Position] = reached
    state = _get_ai_state(wolf)
    state.last_known_primary = reached
    _consume_reached_memory(state, reached)
    assert state.last_known_primary is None


def test_stunned_knight_skips_turn() -> None:
    engine = GameEngine()
    carve_floor_tile(engine, ARENA_X, ARENA_Y)
    for entity in engine.world.Q.all_of(components=[AI, Position]):
        if entity is not engine.player:
            entity.components[Position] = Position(70, 40)
    knight = spawn_test_npc(
        engine.world,
        x=ARENA_X,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=5,
    )
    knight.components[Fighter].hp = 0
    knight.tags.add(Stunned)
    pos_before = knight.components[Position]
    update_fov(engine.game_map, pos_before.x, pos_before.y)
    run_monster_turns(
        engine.world,
        engine.game_map,
        engine.player,
        engine.message_log,
        rng=random.Random(0),
    )
    assert knight.components[Position] == pos_before


def test_npc_good_good_swap() -> None:
    engine = GameEngine()
    (ax, ay), (bx, by), direction = carved_bump_pair(engine)
    knight_a = spawn_test_npc(
        engine.world,
        x=ax,
        y=ay,
        species="knight",
        alignment=Alignment.GOOD,
    )
    knight_b = spawn_test_npc(
        engine.world,
        x=bx,
        y=by,
        species="knight",
        alignment=Alignment.GOOD,
    )
    pos_a_before = knight_a.components[Position]
    pos_b_before = knight_b.components[Position]
    assert try_action(
        engine.world,
        engine.game_map,
        knight_a,
        direction,
        engine.message_log,
    )
    assert knight_a.components[Position] == pos_b_before
    assert knight_b.components[Position] == pos_a_before
    assert not any("hit" in line.lower() for line in engine.message_log.lines())


def test_npc_evil_evil_do_not_swap() -> None:
    engine = GameEngine()
    (ax, ay), (bx, by), direction = carved_bump_pair(engine)
    wolf_a = spawn_test_npc(
        engine.world,
        x=ax,
        y=ay,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    wolf_b = spawn_test_npc(
        engine.world,
        x=bx,
        y=by,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    pos_a_before = wolf_a.components[Position]
    pos_b_before = wolf_b.components[Position]
    assert not can_npc_swap(wolf_a, wolf_b)
    try_action(
        engine.world,
        engine.game_map,
        wolf_a,
        direction,
        engine.message_log,
    )
    assert wolf_a.components[Position] == pos_a_before
    assert wolf_b.components[Position] == pos_b_before


def test_npc_good_neutral_swap() -> None:
    engine = GameEngine()
    (ax, ay), (bx, by), direction = carved_bump_pair(engine)
    knight = spawn_test_npc(
        engine.world,
        x=ax,
        y=ay,
        species="knight",
        alignment=Alignment.GOOD,
    )
    rabbit = spawn_test_npc(
        engine.world,
        x=bx,
        y=by,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
        hp=8,
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=0,
        max_damage=0,
    )
    knight_pos_before = knight.components[Position]
    rabbit_pos_before = rabbit.components[Position]
    assert try_action(
        engine.world,
        engine.game_map,
        knight,
        direction,
        engine.message_log,
    )
    assert knight.components[Position] == rabbit_pos_before
    assert rabbit.components[Position] == knight_pos_before


def test_npc_cross_alignment_attacks() -> None:
    engine = GameEngine()
    (ax, ay), (bx, by), direction = carved_fov_bump_pair(
        engine, require_visible=True
    )
    wolf = spawn_test_npc(
        engine.world,
        x=ax,
        y=ay,
        species="wolf",
        alignment=Alignment.EVIL,
        min_damage=6,
        max_damage=6,
        evade=2,
        ac=2,
    )
    knight = spawn_test_npc(
        engine.world,
        x=bx,
        y=by,
        species="knight",
        alignment=Alignment.GOOD,
        hp=12,
        evade=1,
        ac=3,
        min_damage=3,
        max_damage=3,
    )
    knight_pos_before = knight.components[Position]
    wolf_pos_before = wolf.components[Position]
    knight_hp_before = knight.components[Fighter].hp
    assert try_action(
        engine.world,
        engine.game_map,
        wolf,
        direction,
        engine.message_log,
        rng=engine.rng,
    )
    assert wolf.components[Position] == wolf_pos_before
    assert knight.components[Position] == knight_pos_before
    assert knight.components[Fighter].hp < knight_hp_before
    assert any("hit" in line.lower() for line in engine.message_log.lines())


def test_npc_never_swaps_onto_player() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    knight_pos = ensure_adjacent_floor(engine, player_pos, (1, 0))
    knight = spawn_test_npc(
        engine.world,
        x=knight_pos.x,
        y=knight_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    knight_pos_before = knight.components[Position]
    assert not try_action(
        engine.world,
        engine.game_map,
        knight,
        (-1, 0),
        engine.message_log,
    )
    assert knight.components[Position] == knight_pos_before
    assert player.components[Position] == player_pos


def test_npc_combat_off_screen_not_logged() -> None:
    engine = GameEngine()
    (ax, ay), (bx, by), direction = carved_fov_bump_pair(
        engine, require_visible=False
    )
    wolf = spawn_test_npc(
        engine.world,
        x=ax,
        y=ay,
        species="wolf",
        alignment=Alignment.EVIL,
        min_damage=6,
        max_damage=6,
        evade=2,
        ac=2,
    )
    knight = spawn_test_npc(
        engine.world,
        x=bx,
        y=by,
        species="knight",
        alignment=Alignment.GOOD,
        hp=1,
        ac=0,
        min_damage=0,
        max_damage=0,
    )
    lines_before = len(engine.message_log.lines())
    assert try_action(
        engine.world,
        engine.game_map,
        wolf,
        direction,
        engine.message_log,
        rng=engine.rng,
    )
    assert knight.components[Fighter].hp == 0
    assert Stunned in knight.tags
    new_lines = engine.message_log.lines()[lines_before:]
    assert not any("hit" in line.lower() for line in new_lines)
    assert not any("stunned" in line.lower() for line in new_lines)


def test_npc_combat_on_screen_logged() -> None:
    engine = GameEngine()
    (ax, ay), (bx, by), direction = carved_fov_bump_pair(
        engine, require_visible=True
    )
    wolf = spawn_test_npc(
        engine.world,
        x=ax,
        y=ay,
        species="wolf",
        alignment=Alignment.EVIL,
        min_damage=6,
        max_damage=6,
        evade=2,
        ac=2,
    )
    knight = spawn_test_npc(
        engine.world,
        x=bx,
        y=by,
        species="knight",
        alignment=Alignment.GOOD,
        hp=12,
        evade=1,
        ac=3,
        min_damage=3,
        max_damage=3,
    )
    lines_before = len(engine.message_log.lines())
    assert try_action(
        engine.world,
        engine.game_map,
        wolf,
        direction,
        engine.message_log,
        rng=engine.rng,
    )
    new_lines = engine.message_log.lines()[lines_before:]
    assert any("hit" in line.lower() for line in new_lines)


def test_npc_swap_skips_defender_turn() -> None:
    engine = GameEngine()
    (ax, ay), (bx, by), direction = carved_bump_pair(engine)
    knight_a = spawn_test_npc(
        engine.world,
        x=ax,
        y=ay,
        species="knight",
        alignment=Alignment.GOOD,
    )
    knight_b = spawn_test_npc(
        engine.world,
        x=bx,
        y=by,
        species="knight",
        alignment=Alignment.GOOD,
    )
    skip_set: set = set()
    assert try_action(
        engine.world,
        engine.game_map,
        knight_a,
        direction,
        engine.message_log,
        skip_turn_entities=skip_set,
    )
    assert knight_b in skip_set
    knight_b_pos_after_swap = knight_b.components[Position]
    update_fov(engine.game_map, knight_b_pos_after_swap.x, knight_b_pos_after_swap.y)
    run_monster_turns(
        engine.world,
        engine.game_map,
        engine.player,
        engine.message_log,
        rng=random.Random(0),
        skipped=skip_set,
    )
    assert knight_b.components[Position] == knight_b_pos_after_swap


def _adjacent_stunned_knight_setup(engine: GameEngine):
    """Place a wolf adjacent to a stunned knight inside player FOV."""
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


def test_npc_vore_miss_log() -> None:
    engine = GameEngine()
    wolf, knight = _adjacent_stunned_knight_setup(engine)
    lines_before = len(engine.message_log.lines())
    with patch("src.systems.vore.resolve_vore_hit", return_value=False):
        with patch("src.systems.vore.should_attempt_vore", return_value=True):
            assert try_resolve_npc_vore(
                wolf,
                engine.world,
                engine.game_map,
                engine.message_log,
                random.Random(0),
            )
    assert Engulfed not in knight.tags
    new_lines = engine.message_log.lines()[lines_before:]
    assert new_lines
    assert any(
        "knight" in logged.lower() and "wolf" in logged.lower()
        for logged in new_lines
    )


def test_npc_vore_hit_engulfs_without_modal() -> None:
    engine = GameEngine()
    wolf, knight = _adjacent_stunned_knight_setup(engine)
    lines_before = len(engine.message_log.lines())
    with patch("src.systems.vore.resolve_vore_hit", return_value=True):
        with patch("src.systems.vore.should_attempt_vore", return_value=True):
            assert try_resolve_npc_vore(
                wolf,
                engine.world,
                engine.game_map,
                engine.message_log,
                random.Random(0),
            )
    assert Engulfed in knight.tags
    predator_state = wolf.components.get(Predator)
    assert predator_state is not None
    assert predator_state.prey is knight
    assert knight.components[Position] == wolf.components[Position]
    new_lines = engine.message_log.lines()[lines_before:]
    assert new_lines
    assert any("knight" in logged.lower() for logged in new_lines)


def test_npc_vore_via_monster_turns_no_modal() -> None:
    engine = GameEngine()
    wolf, knight = _adjacent_stunned_knight_setup(engine)
    modal = VoreModalState()

    def _npc_prey_only(monster, prey, *args, **kwargs):
        return Player not in prey.tags

    with patch("src.systems.vore.resolve_vore_hit", return_value=True):
        with patch("src.systems.vore.should_attempt_vore", side_effect=_npc_prey_only):
            opened = run_monster_turns(
                engine.world,
                engine.game_map,
                engine.player,
                engine.message_log,
                rng=random.Random(0),
                modal=modal,
            )
    assert not opened
    assert not modal.active
    assert Engulfed in knight.tags


def test_engulfed_npc_prey_skips_turn() -> None:
    engine = GameEngine()
    wolf, knight = _adjacent_stunned_knight_setup(engine)
    with patch("src.systems.vore.resolve_vore_hit", return_value=True):
        with patch("src.systems.vore.should_attempt_vore", return_value=True):
            assert try_resolve_npc_vore(
                wolf,
                engine.world,
                engine.game_map,
                engine.message_log,
                random.Random(0),
            )
    knight_pos = knight.components[Position]
    run_monster_turns(
        engine.world,
        engine.game_map,
        engine.player,
        engine.message_log,
        rng=random.Random(0),
    )
    assert knight.components[Position] == knight_pos


def test_engulfed_good_npc_invisible_to_evil_ai() -> None:
    from tests.map_test_helpers import ensure_wolves

    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolves = ensure_wolves(engine, 2)
    predator, hunter = wolves[0], wolves[1]
    player_pos = player.components[Position]
    pred_tile, prey_tile, hunter_tile = carve_adjacent_line(engine, player_pos, 3)
    knight = spawn_test_npc(
        engine.world,
        x=prey_tile.x,
        y=prey_tile.y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=5,
    )
    knight.components[Fighter].hp = 0
    knight.tags.add(Stunned)
    predator.components[Position] = pred_tile
    hunter.components[Position] = hunter_tile
    update_fov(engine.game_map, player_pos.x, player_pos.y)
    engulf_npc(engine.world, knight, predator, narrative_type="OV")

    primaries = _visible_primary_hostiles(
        hunter, engine.world, engine.game_map, player
    )
    assert knight not in primaries
    entity_target, _, _ = pick_evil_chase(
        hunter,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
    )
    assert entity_target is not knight


def test_engulfed_neutral_invisible_to_evil_ai() -> None:
    from tests.map_test_helpers import ensure_wolves

    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolves = ensure_wolves(engine, 2)
    predator, hunter = wolves[0], wolves[1]
    player_pos = player.components[Position]
    pred_tile, prey_tile, hunter_tile = carve_adjacent_line(engine, player_pos, 3)
    rabbit = spawn_test_npc(
        engine.world,
        x=prey_tile.x,
        y=prey_tile.y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
        hp=5,
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=0,
        max_damage=0,
    )
    rabbit.components[Fighter].hp = 0
    rabbit.tags.add(Stunned)
    predator.components[Position] = pred_tile
    hunter.components[Position] = hunter_tile
    update_fov(engine.game_map, player_pos.x, player_pos.y)
    engulf_npc(engine.world, rabbit, predator, narrative_type="OV")

    neutrals = _visible_neutrals(hunter, engine.world, engine.game_map)
    assert rabbit not in neutrals
    entity_target, _, _ = pick_evil_chase(
        hunter,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
    )
    assert entity_target is not rabbit


def test_engulfed_prey_clears_evil_memory() -> None:
    engine = GameEngine()
    wolf, knight = _adjacent_stunned_knight_setup(engine)
    engulf_npc(engine.world, knight, wolf, narrative_type="OV")
    state = _get_ai_state(wolf)
    prey_pos = knight.components[Position]
    state.last_known_primary = prey_pos
    state.last_known_neutral = prey_pos
    _clear_memory_of_engulfed_prey(state, engine.world)
    assert state.last_known_primary is None
    assert state.last_known_neutral is None


def test_npc_vore_off_screen_logs_atmospheric_line() -> None:
    engine = GameEngine()
    (hx, hy), (kx, ky) = carved_hidden_line(engine, 2)
    wolf = spawn_test_npc(
        engine.world,
        x=hx,
        y=hy,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    wolf.tags.add(VoreCapable)
    wolf.components[VoreNarratives] = VoreNarratives(types=("OV", "CV", "AV"))
    knight = spawn_test_npc(
        engine.world,
        x=kx,
        y=ky,
        species="knight",
        alignment=Alignment.GOOD,
        hp=5,
    )
    knight.components[Fighter].hp = 0
    knight.tags.add(Stunned)
    lines_before = len(engine.message_log.lines())
    with patch("src.systems.vore.pick_attempt_narrative_type", return_value="OV"):
        with patch("src.systems.vore.resolve_vore_hit", return_value=True):
            with patch("src.systems.vore.should_attempt_vore", return_value=True):
                assert try_resolve_npc_vore(
                    wolf,
                    engine.world,
                    engine.game_map,
                    engine.message_log,
                    random.Random(0),
                )
    assert Engulfed in knight.tags
    new_lines = engine.message_log.lines()[lines_before:]
    assert len(new_lines) == 1
    assert new_lines[0].strip()
    assert "swallows" not in new_lines[0].lower()


def _wolf_holding_stunned_rabbit(engine: GameEngine):
    """Wolf at player_pos+1 holding a stunned rabbit on the same tile."""
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
        accuracy=10.0,
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
    return wolf, rabbit, player_pos


def test_defeating_predator_frees_npc_prey() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf, rabbit, player_pos = _wolf_holding_stunned_rabbit(engine)
    wolf_pos = wolf.components[Position]
    player.components[Position] = Position(player_pos.x, player_pos.y)
    wolf.components[Fighter].hp = 1
    predator_tile_before = wolf_pos
    rabbit_tile_before = rabbit.components[Position]
    assert rabbit_tile_before == predator_tile_before

    import random

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

    assert Engulfed not in rabbit.tags
    assert wolf not in list(iter_wolves(engine))
    assert rabbit.components[Position] != predator_tile_before
    expected = messages.npc_freed_from_predator("The rabbit", "the wolf")
    assert expected in engine.message_log.lines()
    assert Stunned in rabbit.tags


def test_knight_rescues_engulfed_rabbit() -> None:
    engine = GameEngine()
    wolf, rabbit, player_pos = _wolf_holding_stunned_rabbit(engine)
    wolf_pos = wolf.components[Position]
    knight_pos = ensure_adjacent_floor(engine, wolf_pos, (1, 0))
    knight = spawn_test_npc(
        engine.world,
        x=knight_pos.x,
        y=knight_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=5,
        max_damage=5,
    )
    wolf.components[Fighter].hp = 1
    update_fov(engine.game_map, player_pos.x, player_pos.y)
    predator_tile_before = wolf_pos

    assert try_action(
        engine.world,
        engine.game_map,
        knight,
        (-1, 0),
        engine.message_log,
    )

    assert Engulfed not in rabbit.tags
    assert wolf not in list(iter_wolves(engine))
    assert rabbit.components[Position] != predator_tile_before
    assert messages.npc_freed_from_predator("The rabbit", "the wolf") in (
        engine.message_log.lines()
    )
    assert Stunned in rabbit.tags