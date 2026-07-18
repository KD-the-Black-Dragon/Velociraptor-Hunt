"""FOV-gated cosmetic animation for Path beams and Smite flashes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import attrs
from tcod.ecs import Entity

from src.components import Position
from src.map_gen import GameMap
from src.systems.fov import entity_visible_to_player
from src.systems.ranged_path import path_tiles

if TYPE_CHECKING:
    from src.ui.layout import MapCamera


PATH_PROJECTILE_GLYPH = ord("*")
PATH_PROJECTILE_FG = (0, 255, 255)
SMITE_PROJECTILE_GLYPH = ord("*")
SMITE_PROJECTILE_FG = (255, 0, 255)
PROJECTILE_FRAMES_PER_TILE = 1
SMITE_FRAMES_PER_STEP = 2
PROJECTILE_FRAME_SLEEP_SECONDS = 0.024


@attrs.define(frozen=True)
class PathProjectileSpec:
    """Cosmetic ranged shot — Path beam trail or Smite source/target flash."""

    tiles: tuple[tuple[int, int], ...]
    glyph: int
    fg: tuple[int, int, int]
    trail: bool = True
    step_frames: int = PROJECTILE_FRAMES_PER_TILE


@attrs.define
class ProjectileAnimSession:
    specs: list[PathProjectileSpec]
    spec_index: int = 0
    tile_index: int = 0
    frames_left: int = 0
    active: bool = True

    def __attrs_post_init__(self) -> None:
        if self.frames_left <= 0:
            spec = self.current_spec
            self.frames_left = spec.step_frames if spec is not None else PROJECTILE_FRAMES_PER_TILE

    @property
    def current_spec(self) -> PathProjectileSpec | None:
        if self.spec_index >= len(self.specs):
            return None
        return self.specs[self.spec_index]


@attrs.define(frozen=True)
class ProjectileFrameResult:
    screen_dirty: bool
    finished: bool


_path_projectile_queue: list[PathProjectileSpec] = []


def reset_projectile_queue() -> None:
    _path_projectile_queue.clear()


def take_queued_projectiles() -> list[PathProjectileSpec]:
    queued = list(_path_projectile_queue)
    _path_projectile_queue.clear()
    return queued


def build_npc_path_projectile_spec(
    attacker: Entity,
    defender: Entity,
) -> PathProjectileSpec:
    origin = attacker.components[Position]
    target_pos = defender.components[Position]
    tiles = path_tiles(origin.x, origin.y, target_pos.x, target_pos.y)
    beam = tuple((int(x), int(y)) for x, y in tiles)
    return PathProjectileSpec(
        tiles=beam,
        glyph=PATH_PROJECTILE_GLYPH,
        fg=PATH_PROJECTILE_FG,
        trail=True,
        step_frames=PROJECTILE_FRAMES_PER_TILE,
    )


def build_smite_projectile_spec(
    attacker: Entity,
    defender: Entity,
) -> PathProjectileSpec:
    """Two-step flash: shooter tile, then target tile."""
    origin = attacker.components[Position]
    target_pos = defender.components[Position]
    return PathProjectileSpec(
        tiles=((origin.x, origin.y), (target_pos.x, target_pos.y)),
        glyph=SMITE_PROJECTILE_GLYPH,
        fg=SMITE_PROJECTILE_FG,
        trail=False,
        step_frames=SMITE_FRAMES_PER_STEP,
    )


def maybe_queue_player_path_projectile(
    attacker: Entity,
    defender: Entity,
    game_map: GameMap,
) -> None:
    """Queue a Path beam animation for a player throw."""
    maybe_queue_npc_path_projectile(attacker, defender, game_map)


def _combat_visible_to_player(
    game_map: GameMap,
    attacker: Entity,
    defender: Entity,
) -> bool:
    return entity_visible_to_player(game_map, attacker) or entity_visible_to_player(
        game_map, defender
    )


def maybe_queue_npc_path_projectile(
    attacker: Entity,
    defender: Entity,
    game_map: GameMap,
) -> None:
    """Queue a Path beam animation when the player can see the combat."""
    if not _combat_visible_to_player(game_map, attacker, defender):
        return
    spec = build_npc_path_projectile_spec(attacker, defender)
    if not spec.tiles:
        return
    _path_projectile_queue.append(spec)


def maybe_queue_smite_projectile(
    attacker: Entity,
    defender: Entity,
    game_map: GameMap,
) -> None:
    """Queue a Smite flash (source, then target) when the player can see the combat."""
    if not _combat_visible_to_player(game_map, attacker, defender):
        return
    _path_projectile_queue.append(build_smite_projectile_spec(attacker, defender))


def begin_projectile_session(specs: list[PathProjectileSpec]) -> ProjectileAnimSession | None:
    if not specs:
        return None
    return ProjectileAnimSession(specs=list(specs))


def advance_projectile_frame(session: ProjectileAnimSession) -> ProjectileFrameResult:
    if not session.active:
        return ProjectileFrameResult(screen_dirty=False, finished=True)

    spec = session.current_spec
    if spec is None or not spec.tiles:
        session.active = False
        return ProjectileFrameResult(screen_dirty=False, finished=True)

    session.frames_left -= 1
    if session.frames_left > 0:
        return ProjectileFrameResult(screen_dirty=True, finished=False)

    session.tile_index += 1
    if session.tile_index < len(spec.tiles):
        session.frames_left = spec.step_frames
        return ProjectileFrameResult(screen_dirty=True, finished=False)

    session.spec_index += 1
    session.tile_index = 0
    next_spec = session.current_spec
    if next_spec is not None:
        session.frames_left = next_spec.step_frames
    if session.spec_index >= len(session.specs):
        session.active = False
        return ProjectileFrameResult(screen_dirty=True, finished=True)

    return ProjectileFrameResult(screen_dirty=True, finished=False)


def _draw_projectile_glyph(
    console,
    *,
    x: int,
    y: int,
    game_map: GameMap,
    glyph: int,
    fg: tuple[int, int, int],
    camera: MapCamera | None,
) -> None:
    if not game_map.in_bounds(x, y):
        return
    if camera is not None:
        screen = camera.screen_xy(x, y)
        if screen is None:
            return
        draw_x, draw_y = screen
    else:
        draw_x, draw_y = x, y
    console.print(draw_x, draw_y, chr(glyph), fg=fg)


def render_projectile(
    console,
    *,
    session: ProjectileAnimSession,
    game_map: GameMap,
    camera: MapCamera | None = None,
) -> None:
    """Draw the beam trail through the current tile (FOV gate is at queue time)."""
    spec = session.current_spec
    if spec is None or not spec.tiles:
        return

    end_index = min(session.tile_index, len(spec.tiles) - 1)
    if spec.trail:
        draw_tiles = spec.tiles[: end_index + 1]
    else:
        draw_tiles = (spec.tiles[end_index],)
    for x, y in draw_tiles:
        _draw_projectile_glyph(
            console,
            x=x,
            y=y,
            game_map=game_map,
            glyph=spec.glyph,
            fg=spec.fg,
            camera=camera,
        )