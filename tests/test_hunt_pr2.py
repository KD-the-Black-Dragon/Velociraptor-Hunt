"""PR2: circular paddock, tank facing, cone FOV, AUT tenths."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.hunt_aut import format_aut, load_hunt_aut_costs, tenths
from src.hunt_facing import facing_delta, facing_name, in_vision_cone, rotate_facing
from src.hunt_fov import has_line_of_sight, visible_tiles
from src.hunt_input import TankCommand, parse_tank_command
from src.hunt_map import HuntMap, HuntTerrain, generate_paddock, nearest_walkable
from src.hunt_raptor import HuntRaptor
from src.hunt_session import HuntAction, HuntSession, handle_hunt_event


def _key(sym: KeySym, *, ctrl: bool = False) -> tcod.event.KeyDown:
    mod = Modifier.LCTRL if ctrl else Modifier.NONE
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def _open_square(size: int = 11) -> HuntMap:
    tiles = [[HuntTerrain.OPEN for _ in range(size)] for _ in range(size)]
    for i in range(size):
        tiles[0][i] = HuntTerrain.WALL
        tiles[size - 1][i] = HuntTerrain.WALL
        tiles[i][0] = HuntTerrain.WALL
        tiles[i][size - 1] = HuntTerrain.WALL
    return HuntMap(
        width=size,
        height=size,
        tiles=tiles,
        radius=float(size),
        center_x=size // 2,
        center_y=size // 2,
    )


def _session(*, paddock: HuntMap | None = None, x: int = 5, y: int = 5, facing: int = 0, weapon_id: str = "rifle", weapon_name: str = "Bolt-action rifle", **kwargs) -> HuntSession:
    kwargs.setdefault("raptor", HuntRaptor(x=1, y=1, facing=6, hp=100, max_hp=100))
    return HuntSession(
        hunter_name="Muldoon",
        weapon_id=weapon_id,
        weapon_name=weapon_name,
        seed=1,
        paddock=paddock if paddock is not None else _open_square(),
        player_x=x,
        player_y=y,
        facing=facing,
        **kwargs,
    )


def test_aut_costs_are_tenths() -> None:
    costs = load_hunt_aut_costs()
    for value in (
        costs.wait, costs.step, costs.walk, costs.quick, costs.run, costs.sneak,
        costs.rotate_45, costs.rotate_90, costs.sidestep,
    ):
        assert value == tenths(value)


def test_generated_paddock_is_circular_with_jungle() -> None:
    mmap = generate_paddock(7)
    assert mmap.terrain_at(0, 0) is HuntTerrain.WALL
    assert mmap.terrain_at(mmap.width - 1, mmap.height - 1) is HuntTerrain.WALL
    assert mmap.inside_circle(mmap.center_x, mmap.center_y)
    assert mmap.walkable(*nearest_walkable(mmap, mmap.center_x, mmap.center_y))
    kinds = {mmap.terrain_at(x, y) for y in range(mmap.height) for x in range(mmap.width)}
    assert HuntTerrain.TREE in kinds
    assert HuntTerrain.GRASS in kinds
    assert HuntTerrain.OPEN in kinds
    assert HuntTerrain.MUD in kinds


def test_tank_keys_map_to_commands() -> None:
    assert parse_tank_command(_key(KeySym.KP_8)) is TankCommand.FORWARD
    assert parse_tank_command(_key(KeySym.Y)) is TankCommand.FORWARD
    assert parse_tank_command(_key(KeySym.UP)) is TankCommand.FORWARD
    assert parse_tank_command(_key(KeySym.KP_2)) is TankCommand.BACK
    assert parse_tank_command(_key(KeySym.KP_7)) is TankCommand.ROTATE_45_LEFT
    assert parse_tank_command(_key(KeySym.KP_4)) is TankCommand.ROTATE_90_LEFT
    assert parse_tank_command(_key(KeySym.KP_4, ctrl=True)) is TankCommand.SIDESTEP_LEFT
    assert parse_tank_command(_key(KeySym.G, ctrl=True)) is TankCommand.SIDESTEP_LEFT
    assert parse_tank_command(_key(KeySym.PERIOD)) is TankCommand.WAIT
    assert parse_tank_command(_key(KeySym.ESCAPE)) is TankCommand.LEAVE


def test_rotate_does_not_move_and_costs_aut() -> None:
    session = _session()
    x, y = session.player_x, session.player_y
    assert handle_hunt_event(session, _key(KeySym.KP_6)) is HuntAction.NONE
    assert (session.player_x, session.player_y) == (x, y)
    assert facing_name(session.facing) == "E"
    assert session.world_aut == load_hunt_aut_costs().rotate_90


def test_forward_moves_along_facing() -> None:
    session = _session(facing=0)
    x, y = session.player_x, session.player_y
    handle_hunt_event(session, _key(KeySym.KP_8))
    dx, dy = facing_delta(0)
    assert session.player_x == x + dx
    assert session.player_y == y + dy
    assert session.facing == 0


def test_blocked_step_spends_no_aut() -> None:
    mmap = _open_square()
    mmap.tiles[4][5] = HuntTerrain.TREE
    session = _session(paddock=mmap, x=5, y=5, facing=0)
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.player_y == 5
    assert session.world_aut == 0.0


def test_sidestep_left_while_facing_north() -> None:
    session = _session(facing=0)
    x, y = session.player_x, session.player_y
    handle_hunt_event(session, _key(KeySym.KP_4, ctrl=True))
    assert session.facing == 0
    assert session.player_x == x - 1
    assert session.player_y == y


def test_wait_advances_aut_tenths() -> None:
    session = _session()
    handle_hunt_event(session, _key(KeySym.H))
    assert format_aut(session.world_aut) == format_aut(load_hunt_aut_costs().wait)


def test_cone_excludes_behind_includes_ahead() -> None:
    assert in_vision_cone(
        origin_x=5, origin_y=5, facing=0, tile_x=5, tile_y=3,
        cone_range=8, half_degrees=55,
    )
    assert not in_vision_cone(
        origin_x=5, origin_y=5, facing=0, tile_x=5, tile_y=7,
        cone_range=8, half_degrees=55,
    )


def test_tree_blocks_los() -> None:
    mmap = _open_square()
    mmap.tiles[4][5] = HuntTerrain.TREE
    assert not has_line_of_sight(mmap, 5, 5, 5, 3)
    assert has_line_of_sight(mmap, 5, 5, 5, 4)


def test_fov_respects_facing() -> None:
    session = _session(facing=0)
    assert (session.player_x, session.player_y - 1) in session.visible
    assert (session.player_x, session.player_y + 2) not in session.visible
    handle_hunt_event(session, _key(KeySym.KP_6))
    session.refresh_fov()
    assert (session.player_x + 1, session.player_y) in session.visible


def test_rotate_facing_wraps() -> None:
    assert rotate_facing(0, -1) == 7
    assert rotate_facing(7, 1) == 0


def test_visible_tiles_uses_cone_and_los() -> None:
    mmap = _open_square()
    seen = visible_tiles(
        mmap, origin_x=5, origin_y=5, facing=2, cone_range=8, half_degrees=55,
    )
    assert (6, 5) in seen
    assert (4, 5) not in seen
