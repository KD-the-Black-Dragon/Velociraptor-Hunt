"""Path projectile cosmetic animation."""

from __future__ import annotations

from src.systems.projectile_anim import (
    PATH_PROJECTILE_FG,
    PATH_PROJECTILE_GLYPH,
    PROJECTILE_FRAMES_PER_TILE,
    SMITE_FRAMES_PER_STEP,
    SMITE_PROJECTILE_FG,
    SMITE_PROJECTILE_GLYPH,
    PathProjectileSpec,
    advance_projectile_frame,
    begin_projectile_session,
    build_npc_path_projectile_spec,
    build_smite_projectile_spec,
    render_projectile,
    reset_projectile_queue,
    take_queued_projectiles,
)
from tests.map_test_helpers import ARENA_X, ARENA_Y, spawn_wolf_with_abilities


def test_advance_projectile_frame_walks_beam_tiles() -> None:
    spec = PathProjectileSpec(
        tiles=((1, 0), (2, 0), (3, 0)),
        glyph=ord("*"),
        fg=(200, 200, 200),
    )
    session = begin_projectile_session([spec])
    assert session is not None

    for _ in range(PROJECTILE_FRAMES_PER_TILE * len(spec.tiles) - 1):
        result = advance_projectile_frame(session)
        assert result.screen_dirty
        assert not result.finished

    result = advance_projectile_frame(session)
    assert result.finished
    assert not session.active


def test_projectile_queue_reset_and_take() -> None:
    reset_projectile_queue()
    assert take_queued_projectiles() == []


def test_player_throw_defers_world_turn_until_projectile_finishes() -> None:
    from src.components import Position
    from src.engine import GameEngine
    from src.systems.projectile_anim import maybe_queue_player_path_projectile
    from tests.map_test_helpers import carve_horizontal_line, isolate_other_ais

    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X + 3, ARENA_Y, [])
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    engine._update_fov()
    wolf_pos_before = wolf.components[Position]
    maybe_queue_player_path_projectile(player, wolf, engine.game_map)

    engine._consume_player_turn()

    assert engine.pending_world_turn
    assert engine.projectile_in_progress()
    assert wolf.components[Position] == wolf_pos_before

    while engine.projectile_in_progress():
        engine.advance_projectile_animation()

    assert not engine.pending_world_turn


def test_smite_projectile_flashes_source_then_target() -> None:
    from src.components import Alignment, Position
    from src.engine import GameEngine
    from src.systems.ai import spawn_test_npc
    from tests.map_test_helpers import carve_horizontal_line, isolate_other_ais

    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 8)
    slime = spawn_test_npc(
        engine.world,
        x=ARENA_X + 4,
        y=ARENA_Y,
        species="slime",
        alignment=Alignment.EVIL,
    )
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    spec = build_smite_projectile_spec(slime, player)
    assert spec.trail is False
    assert spec.glyph == SMITE_PROJECTILE_GLYPH
    assert spec.fg == SMITE_PROJECTILE_FG
    assert spec.tiles == ((ARENA_X + 4, ARENA_Y), (ARENA_X, ARENA_Y))

    session = begin_projectile_session([spec])
    assert session is not None
    assert session.tile_index == 0

    for _ in range(SMITE_FRAMES_PER_STEP - 1):
        result = advance_projectile_frame(session)
        assert not result.finished
        assert session.tile_index == 0

    result = advance_projectile_frame(session)
    assert not result.finished
    assert session.tile_index == 1

    for _ in range(SMITE_FRAMES_PER_STEP - 1):
        advance_projectile_frame(session)

    result = advance_projectile_frame(session)
    assert result.finished


def test_render_smite_shows_only_current_flash_tile() -> None:
    import tcod.console

    from src.engine import GameEngine

    engine = GameEngine()
    spec = PathProjectileSpec(
        tiles=((10, 5), (20, 5)),
        glyph=SMITE_PROJECTILE_GLYPH,
        fg=SMITE_PROJECTILE_FG,
        trail=False,
        step_frames=SMITE_FRAMES_PER_STEP,
    )
    session = begin_projectile_session([spec])
    assert session is not None
    session.tile_index = 1

    console = tcod.console.Console(80, 44, order="F")
    render_projectile(
        console,
        session=session,
        game_map=engine.game_map,
        camera=None,
    )

    assert int(console.rgba[20, 5]["ch"]) == SMITE_PROJECTILE_GLYPH
    assert int(console.rgba[10, 5]["ch"]) != SMITE_PROJECTILE_GLYPH


def test_path_projectile_beam_spans_full_shot_distance() -> None:
    from src.components import Alignment, Position
    from src.engine import GameEngine
    from src.systems.ai import spawn_test_npc
    from tests.map_test_helpers import carve_horizontal_line, isolate_other_ais

    engine = GameEngine()
    isolate_other_ais(engine)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 20)
    player = engine.player
    assert player is not None
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X + 12,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    spec = build_npc_path_projectile_spec(player, wolf)
    assert len(spec.tiles) == 13
    assert spec.tiles[-1] == (ARENA_X + 12, ARENA_Y)


def test_render_projectile_draws_trail_through_current_tile() -> None:
    import tcod.console

    from src.components import Position
    from src.engine import GameEngine
    from src.systems.projectile_anim import render_projectile
    from tests.map_test_helpers import carve_horizontal_line, isolate_other_ais

    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 20)
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    engine._update_fov()
    spec = PathProjectileSpec(
        tiles=tuple((ARENA_X + offset, ARENA_Y) for offset in range(13)),
        glyph=PATH_PROJECTILE_GLYPH,
        fg=PATH_PROJECTILE_FG,
    )
    session = begin_projectile_session([spec])
    assert session is not None
    session.tile_index = 12

    console = tcod.console.Console(80, 44, order="F")
    render_projectile(
        console,
        session=session,
        game_map=engine.game_map,
        camera=None,
    )

    assert int(console.rgba[ARENA_X + 12, ARENA_Y]["ch"]) == PATH_PROJECTILE_GLYPH
    assert int(console.rgba[ARENA_X, ARENA_Y]["ch"]) == PATH_PROJECTILE_GLYPH


def test_path_projectile_uses_cyan_asterisk() -> None:
    from src.components import Position
    from src.engine import GameEngine

    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["Range2"])
    player = engine.player
    assert player is not None
    wolf_pos = wolf.components[Position]
    spec = build_npc_path_projectile_spec(wolf, player)
    assert spec.glyph == PATH_PROJECTILE_GLYPH
    assert spec.fg == PATH_PROJECTILE_FG
    assert spec.tiles[0] == (wolf_pos.x, wolf_pos.y)