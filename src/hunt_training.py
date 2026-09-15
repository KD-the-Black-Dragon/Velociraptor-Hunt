"""Training Mode: fixed arena, dummy scripts, F2 command menu."""

from __future__ import annotations

from enum import Enum

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym

from src.hunt_aut import load_hunt_aut_costs
from src.hunt_facing import facing_delta, facing_toward, rotate_facing
from src.hunt_map import HuntMap, HuntTerrain, collect_hide_spots
from src.hunt_raptor import HuntRaptor, raptor_try_step
from src.input_handlers import MODAL_ADVANCE_KEYS
from src.text import cp437_safe
from src.hunt_combat import weapon_combat
from src.weapon_select import load_hunt_weapons

# Training F2 is this mode only (live hunt does not bind it).
TRAINING_MENU_KEY = KeySym.F2

_NAV_UP = frozenset({KeySym.UP, KeySym.KP_8})
_NAV_DOWN = frozenset({KeySym.DOWN, KeySym.KP_2})


class DummyScript(Enum):
    NORMAL = "normal"
    PATROL = "patrol"
    IDLE_GRASS = "idle_grass"
    IDLE_OPEN = "idle_open"
    STOP = "stop"
    SEEK = "seek"


@attrs.define(frozen=True)
class TrainingLayout:
    hunter_xy: tuple[int, int]
    raptor_xy: tuple[int, int]
    raptor_facing: int
    open_still: tuple[int, int]
    grass_still: tuple[int, int]
    patrol: tuple[tuple[int, int], ...]


@attrs.define
class TrainingMenuState:
    highlight: int = 0

    def move(self, delta: int, n: int) -> None:
        if n <= 0:
            return
        self.highlight = (self.highlight + delta) % n


def generate_training_arena() -> tuple[HuntMap, TrainingLayout]:
    """Identical handmade paddock: open west, long grass east, patrol across both."""
    w, h = 31, 15
    tiles = [[HuntTerrain.WALL for _ in range(w)] for _ in range(h)]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            tiles[y][x] = HuntTerrain.GRASS if x >= 15 else HuntTerrain.OPEN
    for x in range(2, 9):
        tiles[12][x] = HuntTerrain.MUD
    tiles[2][2] = HuntTerrain.TREE
    tiles[2][28] = HuntTerrain.TREE
    mmap = HuntMap(
        width=w,
        height=h,
        tiles=tiles,
        radius=20.0,
        center_x=w // 2,
        center_y=h // 2,
        hide_spots=(),
    )
    mmap.hide_spots = collect_hide_spots(mmap)
    patrol = tuple((x, 5) for x in range(4, 25))
    layout = TrainingLayout(
        hunter_xy=(5, 10),
        raptor_xy=(20, 5),
        raptor_facing=6,
        open_still=(5, 8),
        grass_still=(20, 8),
        patrol=patrol,
    )
    return mmap, layout


def training_menu_rows() -> tuple[tuple[str, str], ...]:
    """(command_id, label) including section headers with empty id."""
    return (
        ("", "Dummy"),
        ("patrol", "Walk back and forth (open <-> grass)"),
        ("idle_grass", "Stand still in long grass"),
        ("idle_open", "Stand still in open ground"),
        ("stop", "Stop moving"),
        ("cancel_stop", "Cancel stop moving"),
        ("seek", "Seek and chase ASAP"),
        ("gait_sneak", "Gait: sneak"),
        ("gait_walk", "Gait: walk"),
        ("gait_run", "Gait: run"),
        ("normal", "Normal behavior"),
        ("", "Loadout"),
        ("weapon_rifle", "Weapon: Rifle"),
        ("weapon_shotgun", "Weapon: Shotgun"),
        ("weapon_revolver", "Weapon: Revolver"),
    )


def selectable_menu_indices() -> tuple[int, ...]:
    return tuple(i for i, (cid, _) in enumerate(training_menu_rows()) if cid)


def render_training_menu(console: tcod.console.Console, menu: TrainingMenuState) -> None:
    console.clear()
    console.print(2, 1, "Training Mode", fg=(255, 220, 120))
    rows = training_menu_rows()
    y = 3
    for i, (cid, label) in enumerate(rows):
        if not cid:
            console.print(2, y, label, fg=(180, 160, 80))
        else:
            mark = ">" if i == menu.highlight else " "
            fg = (220, 220, 200) if i == menu.highlight else (160, 160, 150)
            console.print(2, y, f"{mark} {label}", fg=fg)
        y += 1
        if y >= console.height - 2:
            break
    console.print(
        2,
        console.height - 1,
        "Enter: apply   Esc: close",
        fg=(140, 140, 140),
    )


def handle_training_menu_event(
    menu: TrainingMenuState,
    event: tcod.event.Event,
) -> str | None:
    """None = stay open; '' = close; other = command id to apply."""
    if not isinstance(event, tcod.event.KeyDown):
        return None
    rows = training_menu_rows()
    selectable = selectable_menu_indices()
    if event.sym == KeySym.ESCAPE:
        return ""
    if event.sym in _NAV_UP:
        _move_highlight(menu, -1, selectable)
        return None
    if event.sym in _NAV_DOWN:
        _move_highlight(menu, 1, selectable)
        return None
    if event.sym in MODAL_ADVANCE_KEYS:
        i = menu.highlight
        if 0 <= i < len(rows) and rows[i][0]:
            return rows[i][0]
    return None


def _move_highlight(menu: TrainingMenuState, delta: int, selectable: tuple[int, ...]) -> None:
    if not selectable:
        return
    if menu.highlight not in selectable:
        menu.highlight = selectable[0]
        return
    pos = selectable.index(menu.highlight)
    menu.highlight = selectable[(pos + delta) % len(selectable)]


def _tank_toward(raptor: HuntRaptor, mmap: HuntMap, tx: int, ty: int, blocked: set[tuple[int, int]]) -> None:
    if raptor.x == tx and raptor.y == ty:
        return
    desired = facing_toward(raptor.x, raptor.y, tx, ty)
    if raptor.facing != desired:
        step = 1 if (desired - raptor.facing) % 8 <= 4 else -1
        raptor.facing = rotate_facing(raptor.facing, step)
        return
    dx, dy = facing_delta(raptor.facing)
    raptor_try_step(raptor, mmap, dx, dy, blocked=blocked)


def dummy_act(
    raptor: HuntRaptor,
    mmap: HuntMap,
    *,
    script: DummyScript,
    layout: TrainingLayout,
    hunter_xy: tuple[int, int],
    patrol_i: int,
    patrol_dir: int,
) -> tuple[int, int]:
    """One dummy turn. Returns updated (patrol_i, patrol_dir)."""
    blocked = {hunter_xy}
    costs = load_hunt_aut_costs()
    raptor.last_aut = costs.step_for(raptor.gait.value)
    if script is DummyScript.STOP or script in (DummyScript.IDLE_GRASS, DummyScript.IDLE_OPEN):
        raptor.last_aut = costs.wait
        return patrol_i, patrol_dir
    if script is DummyScript.SEEK:
        _tank_toward(raptor, mmap, hunter_xy[0], hunter_xy[1], blocked)
        return patrol_i, patrol_dir
    if script is DummyScript.PATROL:
        path = layout.patrol
        if not path:
            return patrol_i, patrol_dir
        i = max(0, min(patrol_i, len(path) - 1))
        tx, ty = path[i]
        if (raptor.x, raptor.y) == (tx, ty):
            nxt = i + patrol_dir
            if nxt >= len(path) or nxt < 0:
                patrol_dir = -patrol_dir
                nxt = i + patrol_dir
            i = max(0, min(nxt, len(path) - 1))
            tx, ty = path[i]
        _tank_toward(raptor, mmap, tx, ty, blocked)
        return i, patrol_dir
    return patrol_i, patrol_dir


def teleport_raptor(raptor: HuntRaptor, xy: tuple[int, int], facing: int | None = None) -> None:
    raptor.x, raptor.y = xy
    if facing is not None:
        raptor.facing = facing


def weapon_by_id(weapon_id: str) -> tuple[str, str, int]:
    """weapon_id, display name, ammo."""
    ammo = weapon_combat(weapon_id).ammo
    for w in load_hunt_weapons():
        if w.weapon_id == weapon_id:
            return w.weapon_id, w.name, ammo
    w = load_hunt_weapons()[0]
    return w.weapon_id, w.name, weapon_combat(w.weapon_id).ammo
