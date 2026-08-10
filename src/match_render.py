"""Arena map drawing for Gladiavore matches (no dungeon UI)."""

from __future__ import annotations

from collections.abc import Callable

import tcod.console
from tcod.ecs import Entity

from src.components import Position, Renderable
from src.game_map import GameMap, Tile
from src.match_vore import VorePhase

LIGHT_WALL = (120, 120, 120)
LIGHT_FLOOR = (160, 140, 90)  # sand
LIGHT_PILLAR = (100, 100, 100)

# Grapple / swallow danger tile tints (bright so tileset present path is readable)
BG_ALLY_IN_DANGER = (40, 180, 70)  # green — ally prey still visible
BG_PREDATOR_WRESTLING = (220, 200, 40)  # yellow — clinch / grapple phase
BG_PREDATOR_SWALLOWING = (230, 120, 30)  # orange — swallowing in progress
BG_PREDATOR_ENGULFED = (210, 45, 45)  # red — ally fully swallowed
# Soft PC-in-clinch (distinct from ally green)
BG_PC_IN_DANGER = (50, 140, 100)

# CP437 full block (0xDB) — solid cell; Unicode █ may not be mapped in the tileset
_FULL_BLOCK = chr(0xDB)


def _glyph(tile: int) -> tuple[str, tuple[int, int, int]]:
    if tile == Tile.WALL:
        return "#", LIGHT_WALL
    if tile == Tile.FLOOR:
        return ".", LIGHT_FLOOR
    if tile == Tile.DOOR_CLOSED:
        return "+", LIGHT_PILLAR
    if tile == Tile.DOOR_OPEN:
        return "/", LIGHT_FLOOR
    if tile == Tile.DEEP_WATER:
        return "~", (80, 140, 220)
    if tile == Tile.STAIRS_DOWN:
        return ">", (220, 200, 80)
    return " ", (0, 0, 0)


def render_map(console: tcod.console.Console, game_map: GameMap) -> None:
    """Draw full map (matches always reveal the sand pit)."""
    for y in range(game_map.height):
        for x in range(game_map.width):
            if y >= console.height or x >= console.width:
                continue
            ch, fg = _glyph(int(game_map.tiles[y, x]))
            console.print(x, y, ch, fg=fg)


def paint_tile_bg(
    console: tcod.console.Console,
    x: int,
    y: int,
    bg: tuple[int, int, int],
) -> None:
    """Paint a solid highlight cell (full block + bg). Entity glyphs redraw on top."""
    if not (0 <= x < console.width and 0 <= y < console.height):
        return
    # Full-block fg matches bg so the cell is a solid color under any later glyph.
    # Using both channels: some SDL tileset paths show fg more reliably than bg.
    console.print(x, y, _FULL_BLOCK, fg=bg, bg=bg)


def apply_grapple_tile_highlights(
    console: tcod.console.Console,
    *,
    grapple: object | None,
    is_ally: Callable[[Entity], bool],
) -> None:
    """Color tiles for active grapple/swallow scenes.

    - Green: ally prey in danger (still on the map / visible clinch)
    - Yellow: predator wrestling (GRAPPLE phase)
    - Orange: predator swallowing (SWALLOW phase)
    - Red: predator has fully engulfed prey (ENGULFED)
    """
    if grapple is None:
        return
    phase = grapple.phase  # type: ignore[attr-defined]
    predator = grapple.predator  # type: ignore[attr-defined]
    prey = grapple.prey  # type: ignore[attr-defined]
    if not isinstance(predator, Entity) or not isinstance(prey, Entity):
        return

    pred_pos = predator.components.get(Position)
    prey_pos = prey.components.get(Position)
    prey_is_ally = bool(is_ally(prey)) and not getattr(grapple, "prey_is_player", False)

    if phase is VorePhase.GRAPPLE:
        if pred_pos is not None:
            paint_tile_bg(console, pred_pos.x, pred_pos.y, BG_PREDATOR_WRESTLING)
        if prey_pos is not None and prey_is_ally:
            paint_tile_bg(console, prey_pos.x, prey_pos.y, BG_ALLY_IN_DANGER)
        elif prey_pos is not None and getattr(grapple, "prey_is_player", False):
            paint_tile_bg(console, prey_pos.x, prey_pos.y, BG_PC_IN_DANGER)
    elif phase is VorePhase.SWALLOW:
        if pred_pos is not None:
            paint_tile_bg(console, pred_pos.x, pred_pos.y, BG_PREDATOR_SWALLOWING)
        # Ally still co-located or adjacent: green on prey if separate tile
        if prey_pos is not None and prey_is_ally:
            if pred_pos is None or (prey_pos.x, prey_pos.y) != (pred_pos.x, pred_pos.y):
                paint_tile_bg(console, prey_pos.x, prey_pos.y, BG_ALLY_IN_DANGER)
    elif phase is VorePhase.ENGULFED:
        if pred_pos is not None:
            paint_tile_bg(console, pred_pos.x, pred_pos.y, BG_PREDATOR_ENGULFED)


def should_skip_prey_glyph(*, grapple: object | None, entity: Entity) -> bool:
    """Hide prey glyph when co-located during swallow/engulfed (predator owns the tile)."""
    if grapple is None:
        return False
    prey = grapple.prey  # type: ignore[attr-defined]
    predator = grapple.predator  # type: ignore[attr-defined]
    phase = grapple.phase  # type: ignore[attr-defined]
    if entity is not prey:
        return False
    if phase not in (VorePhase.SWALLOW, VorePhase.ENGULFED):
        return False
    if not isinstance(predator, Entity) or not isinstance(prey, Entity):
        return False
    pp = predator.components.get(Position)
    pr = prey.components.get(Position)
    if pp is None or pr is None:
        return False
    return pp.x == pr.x and pp.y == pr.y


def _highlight_for_entity(
    *,
    grapple: object | None,
    entity: Entity,
    is_ally: Callable[[Entity], bool],
) -> tuple[int, int, int] | None:
    """Return highlight color for this entity's tile, if any."""
    if grapple is None:
        return None
    phase = grapple.phase  # type: ignore[attr-defined]
    predator = grapple.predator  # type: ignore[attr-defined]
    prey = grapple.prey  # type: ignore[attr-defined]
    if entity is predator:
        if phase is VorePhase.GRAPPLE:
            return BG_PREDATOR_WRESTLING
        if phase is VorePhase.SWALLOW:
            return BG_PREDATOR_SWALLOWING
        if phase is VorePhase.ENGULFED:
            return BG_PREDATOR_ENGULFED
        return None
    if entity is prey:
        prey_is_ally = bool(is_ally(prey)) and not getattr(
            grapple, "prey_is_player", False
        )
        if phase is VorePhase.GRAPPLE:
            if prey_is_ally:
                return BG_ALLY_IN_DANGER
            if getattr(grapple, "prey_is_player", False):
                return BG_PC_IN_DANGER
        if phase is VorePhase.SWALLOW and prey_is_ally:
            # Only if still on a separate tile (normally co-located)
            return BG_ALLY_IN_DANGER
    return None


def draw_match_entities(
    console: tcod.console.Console,
    session: object,
) -> None:
    """Draw entity glyphs with grapple co-location rules and highlight underlay."""
    grapple = getattr(session, "grapple", None)
    world = session.world  # type: ignore[attr-defined]
    is_ally = getattr(session, "is_ally", lambda _e: False)
    for entity in world.Q.all_of(components=[Position, Renderable]):
        if should_skip_prey_glyph(grapple=grapple, entity=entity):
            continue
        pos = entity.components[Position]
        ren = entity.components[Renderable]
        if not (0 <= pos.x < console.width and 0 <= pos.y < console.height):
            continue
        hl = _highlight_for_entity(grapple=grapple, entity=entity, is_ally=is_ally)
        if hl is not None:
            # Solid underlay, then glyph with same bg so the cell stays tinted
            console.print(pos.x, pos.y, _FULL_BLOCK, fg=hl, bg=hl)
            console.print(pos.x, pos.y, chr(ren.ch), fg=ren.fg, bg=hl)
        else:
            bg = tuple(int(c) for c in console.rgb["bg"][pos.y, pos.x][:3])
            console.print(pos.x, pos.y, chr(ren.ch), fg=ren.fg, bg=bg)
