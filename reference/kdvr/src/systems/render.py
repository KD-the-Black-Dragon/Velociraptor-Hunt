from __future__ import annotations

import attrs
import tcod.console
from tcod import libtcodpy
from tcod.ecs import Entity, Registry

from src.components import (
    Engulfed,
    EquipState,
    Fighter,
    Inventory,
    Item,
    Player,
    Position,
    Predator,
    Renderable,
    ScreenFlashState,
)
from src.game_over_ending import GameOverEnding, format_game_over_ending
from src.log_markup import LogSegment, wrap_log_segments
from src.message_log import LogEntry, MessageCategory
from src.systems.inventory import GroundPickupModalState, item_registry
from src.systems.item_modals import InventoryModalMode, InventoryModalState, inventory_modal_text
from src.systems.player_throw import throw_target_position
from src.systems.wand_evoke import evoke_target_position
from src.constants import MAP_HEIGHT, MAP_WIDTH, RUNE_FLASH_RADIUS
from src.ui.camera import MapCamera
from src.text import cp437_safe
from src.map_gen import GameMap, Tile
from src.systems.movement import MOVEMENT_DIRECTIONS

# Tile colors: bright when visible, dim when explored-only.
LIGHT_WALL = (120, 120, 120)
DARK_WALL = (0, 0, 100)
LIGHT_FLOOR = (72, 72, 72)
DARK_FLOOR = (50, 50, 150)
LIGHT_WATER = (80, 140, 220)
DARK_WATER = (30, 60, 120)
LIGHT_STAIRS = (220, 200, 80)
DARK_STAIRS = (90, 80, 40)
LIGHT_DOOR = (120, 120, 120)
DARK_DOOR = (70, 50, 30)

HUD_MESSAGE_LINES = 5
HP_BAR_WIDTH = 18
ENGULFED_OVERLAY_FG = (100, 20, 20)
PREDATOR_ENGULFED_BG = (80, 10, 10)

def _tile_glyph_and_fg(tile: int, visible: bool) -> tuple[str, tuple[int, int, int]]:
    if tile == Tile.WALL:
        return "#", LIGHT_WALL if visible else DARK_WALL
    if tile == Tile.DEEP_WATER:
        return "~", LIGHT_WATER if visible else DARK_WATER
    if tile == Tile.STAIRS_DOWN:
        return ">", LIGHT_STAIRS if visible else DARK_STAIRS
    if tile == Tile.DOOR_CLOSED:
        return "+", LIGHT_DOOR if visible else DARK_DOOR
    if tile == Tile.DOOR_OPEN:
        return "-", LIGHT_DOOR if visible else DARK_DOOR
    return ".", LIGHT_FLOOR if visible else DARK_FLOOR


def render_map(
    console: tcod.console.Console,
    game_map: GameMap,
    *,
    blind: bool = False,
    camera: MapCamera | None = None,
) -> None:
    """Draw map tiles with explored-memory dimming."""
    if blind:
        return
    if camera is None:
        for world_y in range(game_map.height):
            for world_x in range(game_map.width):
                if not game_map.explored[world_y, world_x]:
                    continue
                tile = game_map.tiles[world_y, world_x]
                char, fg = _tile_glyph_and_fg(tile, game_map.visible[world_y, world_x])
                console.print(world_x, world_y, char, fg=fg)
        return

    for screen_y in range(camera.height):
        for screen_x in range(camera.width):
            world_x = camera.origin_x + screen_x
            world_y = camera.origin_y + screen_y
            if not game_map.in_bounds(world_x, world_y):
                continue
            if not game_map.explored[world_y, world_x]:
                continue
            tile = game_map.tiles[world_y, world_x]
            char, fg = _tile_glyph_and_fg(tile, game_map.visible[world_y, world_x])
            console.print(screen_x, screen_y, char, fg=fg)


def _predator_holding_prey(entity: Entity) -> bool:
    predator_state = entity.components.get(Predator)
    if predator_state is None:
        return False
    return Engulfed in predator_state.prey.tags


def render_entities(
    console: tcod.console.Console,
    world: Registry,
    game_map: GameMap,
    *,
    blind: bool = False,
    player: Entity | None = None,
    camera: MapCamera | None = None,
) -> None:
    """Draw entities with Position and Renderable on visible tiles."""
    entities = list(world.Q.all_of(components=[Position, Renderable]))
    floor_items = [
        entity
        for entity in entities
        if Player not in entity.tags
        and entity.components.get(Item) is not None
        and entity.components.get(Fighter) is None
    ]
    npcs = [
        entity
        for entity in entities
        if Player not in entity.tags
        and entity.components.get(Fighter) is not None
    ]
    others = [
        entity
        for entity in entities
        if Player not in entity.tags and entity not in floor_items and entity not in npcs
    ]
    players = [entity for entity in entities if Player in entity.tags]
    for entity in floor_items + others + npcs + players:
        if Engulfed in entity.tags:
            # Engulfed prey is hidden; the player still sees themselves while blind.
            if not (blind and player is not None and entity is player):
                continue
        if blind and (player is None or entity is not player):
            continue
        pos = entity.components[Position]
        if not game_map.in_bounds(pos.x, pos.y):
            continue
        if not game_map.visible[pos.y, pos.x]:
            continue
        if camera is not None:
            screen = camera.screen_xy(pos.x, pos.y)
            if screen is None:
                continue
            draw_x, draw_y = screen
        else:
            draw_x, draw_y = pos.x, pos.y
        renderable = entity.components[Renderable]
        bg = PREDATOR_ENGULFED_BG if _predator_holding_prey(entity) else None
        console.print(draw_x, draw_y, chr(renderable.ch), fg=renderable.fg, bg=bg)


def _tile_in_flash_radius(dx: int, dy: int, *, radius: int) -> bool:
    return max(abs(dx), abs(dy)) <= radius


def render_screen_flash(
    console: tcod.console.Console,
    *,
    state: ScreenFlashState,
    player_pos: Position | None = None,
    camera: MapCamera | None = None,
) -> None:
    """Draw a one-frame tint around the player, then clear pending."""
    if not state.pending:
        return
    state.pending = False
    if player_pos is None:
        return

    px, py = player_pos.x, player_pos.y
    for dy in range(-RUNE_FLASH_RADIUS, RUNE_FLASH_RADIUS + 1):
        for dx in range(-RUNE_FLASH_RADIUS, RUNE_FLASH_RADIUS + 1):
            if not _tile_in_flash_radius(dx, dy, radius=RUNE_FLASH_RADIUS):
                continue
            world_x, world_y = px + dx, py + dy
            if camera is not None:
                screen = camera.screen_xy(world_x, world_y)
                if screen is None:
                    continue
                draw_x, draw_y = screen
            else:
                if not (0 <= world_x < MAP_WIDTH and 0 <= world_y < MAP_HEIGHT):
                    continue
                draw_x, draw_y = world_x, world_y
            console.draw_rect(
                draw_x,
                draw_y,
                1,
                1,
                ch=0,
                bg=state.color,
                bg_blend=libtcodpy.BKGND_SCREEN,
            )


def render_engulfed_overlay(
    console: tcod.console.Console,
    game_map: GameMap,
    player_pos: Position,
    *,
    camera: MapCamera | None = None,
) -> None:
    """Draw decorative dark-red walls around the player while engulfed."""
    for dx, dy in MOVEMENT_DIRECTIONS:
        world_x = player_pos.x + dx
        world_y = player_pos.y + dy
        if not game_map.in_bounds(world_x, world_y):
            continue
        if camera is not None:
            screen = camera.screen_xy(world_x, world_y)
            if screen is None:
                continue
            draw_x, draw_y = screen
        else:
            draw_x, draw_y = world_x, world_y
        console.print(draw_x, draw_y, "#", fg=ENGULFED_OVERLAY_FG)


def _hp_bar(fighter: Fighter, width: int = HP_BAR_WIDTH) -> str:
    if fighter.max_hp <= 0:
        return "[" + "-" * width + "]"
    filled = round(width * fighter.hp / fighter.max_hp)
    filled = max(0, min(width, filled))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def npc_condition_bar(fighter: Fighter, width: int = 6) -> str:
    """Coarse NPC condition estimate: fill count 0…width via equal ratio spacing."""
    if fighter.max_hp <= 0 or fighter.hp <= 0:
        filled = 0
    else:
        filled = min(width, round(width * fighter.hp / fighter.max_hp))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


MESSAGE_LOG_BACKGROUND = (20, 20, 30)


@attrs.define(frozen=True)
class LogDisplayLine:
    """One wrapped row in the HUD message log."""

    segments: tuple[LogSegment, ...]

    @property
    def text(self) -> str:
        return "".join(segment.text for segment in self.segments)

    @property
    def fg(self) -> tuple[int, int, int]:
        if not self.segments:
            return MessageCategory.ROUTINE.fg
        return self.segments[0].fg


def wrap_log_text(text: str, *, width: int) -> list[str]:
    """Word-wrap log text to ``width`` characters; preserves intentional newlines."""
    if not text:
        return []
    if width <= 0:
        return [text]
    lines: list[str] = []
    segments = text.split("\n")
    for segment_index, segment in enumerate(segments):
        if segment_index > 0:
            lines.append("")
        stripped = segment.strip()
        if not stripped:
            continue
        lines.extend(_wrap_words(stripped, max_inner=width))
    return lines


def expand_log_entries_to_display_lines(
    messages: list[LogEntry] | list[str] | None,
    *,
    width_limit: int,
) -> list[LogDisplayLine]:
    """Expand logical log entries into wrapped display lines with inherited colors."""
    if not messages:
        return []
    display: list[LogDisplayLine] = []
    for entry in messages:
        if isinstance(entry, str):
            safe = cp437_safe(entry)
            wrapped = wrap_log_text(safe, width=width_limit)
            for line in wrapped:
                display.append(
                    LogDisplayLine(
                        segments=(LogSegment(text=line, fg=MessageCategory.ROUTINE.fg),)
                    )
                )
            continue
        for row in wrap_log_segments(entry.display_segments(), width=width_limit):
            if row:
                display.append(LogDisplayLine(segments=row))
    return display


def render_message_log(
    console: tcod.console.Console,
    messages: list[LogEntry] | list[str] | None,
    *,
    start_y: int = 0,
    line_limit: int | None = None,
    max_lines: int = HUD_MESSAGE_LINES,
) -> None:
    """Draw scrolling message log rows into a region-local console."""
    if not messages:
        return
    width_limit = line_limit if line_limit is not None else console.width - 2
    display_lines = expand_log_entries_to_display_lines(
        messages,
        width_limit=width_limit,
    )
    visible_lines = display_lines[-max_lines:]
    for index, line in enumerate(visible_lines):
        row = start_y + index
        if row >= console.height:
            break
        x = 1
        for segment in line.segments:
            remaining = width_limit - (x - 1)
            if remaining <= 0:
                break
            clipped = segment.text[:remaining]
            if not clipped:
                continue
            console.print(x, row, clipped, fg=segment.fg)
            x += len(clipped)


def render_message_log_panel(
    console: tcod.console.Console,
    messages: list[LogEntry] | list[str] | None,
    *,
    max_lines: int,
) -> None:
    """Draw message log background + lines into the message_log sub-console."""
    console.draw_rect(
        0,
        0,
        console.width,
        console.height,
        ch=0,
        fg=None,
        bg=MESSAGE_LOG_BACKGROUND,
    )
    render_message_log(
        console,
        messages,
        start_y=0,
        line_limit=console.width - 2,
        max_lines=max_lines,
    )


def _wrap_words(text: str, *, max_inner: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_inner:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _modal_lines_from_text(text: str, *, max_inner: int) -> list[str]:
    """Preserve intentional newlines; word-wrap only within each logical line.

    Blank lines only come from ``\\n\\n`` section breaks (or empty logical lines),
    so multi-column item rows stay dense.
    """
    lines: list[str] = []
    paragraphs = text.split("\n\n")
    for paragraph_index, paragraph in enumerate(paragraphs):
        if paragraph_index > 0:
            lines.append("")
        logical_lines = paragraph.split("\n") if paragraph else [""]
        for raw_line in logical_lines:
            stripped = raw_line.strip()
            if not stripped:
                lines.append("")
                continue
            lines.extend(_wrap_words(stripped, max_inner=max_inner))
    return lines


def _modal_rows_with_alignment(text: str, *, max_inner: int) -> list[tuple[str, str]]:
    """Build modal rows as (line, 'center'|'left'). First and Esc: blocks are centered.

    Consecutive non-empty lines within a paragraph stay adjacent (multi-column dense).
    """
    rows: list[tuple[str, str]] = []
    paragraphs = cp437_safe(text).split("\n\n")
    for paragraph_index, paragraph in enumerate(paragraphs):
        if paragraph_index > 0:
            rows.append(("", "center"))
        if paragraph_index == 0 or paragraph.strip().startswith("Esc:"):
            align = "center"
        else:
            align = "left"
        logical_lines = paragraph.split("\n") if paragraph else [""]
        for raw_line in logical_lines:
            stripped = raw_line.strip()
            if not stripped:
                rows.append(("", align))
                continue
            for wrapped in _wrap_words(stripped, max_inner=max_inner):
                rows.append((wrapped, align))
    return rows


def render_modal(console: tcod.console.Console, *, text: str) -> None:
    """Draw a modal centered in ``console`` (typically the map viewport sub-console)."""
    if not text:
        return

    # Width from console (not height); leave margin for padding/border.
    max_inner = min(72, max(12, console.width - 6))
    rows = _modal_rows_with_alignment(text, max_inner=max_inner)
    inner_width = max((len(line) for line, _ in rows), default=0)
    inner_width = min(inner_width, max_inner)
    box_width = inner_width + 4
    box_height = len(rows) + 4
    x = max(1, (console.width - box_width) // 2)
    y = max(1, (console.height - box_height) // 2)

    console.draw_rect(x, y, box_width, box_height, ch=ord(" "), fg=(220, 210, 200), bg=(25, 20, 45))
    for row_offset, (line, align) in enumerate(rows):
        clipped = line[:inner_width]
        padded = clipped.center(inner_width) if align == "center" else clipped.ljust(inner_width)
        console.print(x + 2, y + 2 + row_offset, padded, fg=(255, 240, 210))


def render_centered_modal(console: tcod.console.Console, *, text: str) -> None:
    """Draw a modal box (inventory-aware alignment via render_modal)."""
    render_modal(console, text=text)


def render_inventory_modal(
    console: tcod.console.Console,
    *,
    state: InventoryModalState,
    inventory: Inventory | None,
    equip: EquipState | None = None,
    player: Entity | None = None,
    game_map: GameMap | None = None,
    camera: MapCamera | None = None,
) -> None:
    if inventory is None:
        return
    if state.mode == InventoryModalMode.EVOKE_TARGET:
        if game_map is not None:
            cursor = evoke_target_position(state.evoke_targets, state.evoke_target_index)
            if cursor is not None:
                render_examine_cursor(
                    console,
                    cursor,
                    game_map,
                    camera=camera,
                )
        return
    if state.mode == InventoryModalMode.THROW_TARGET:
        if game_map is not None:
            cursor = throw_target_position(
                state.throw_target_tiles,
                state.throw_target_index,
            )
            if cursor is not None:
                render_examine_cursor(
                    console,
                    cursor,
                    game_map,
                    camera=camera,
                )
        return
    if state.mode == InventoryModalMode.BLINK_TARGET:
        if game_map is not None and state.blink_cursor is not None:
            render_examine_cursor(
                console,
                state.blink_cursor,
                game_map,
                camera=camera,
                draw_on_unexplored=True,
            )
        return
    available_width = min(72, max(12, console.width - 6))
    text = inventory_modal_text(
        state,
        inventory,
        equip=equip,
        player=player,
        available_width=available_width,
    )
    if text:
        render_modal(console, text=text)


def render_ground_pickup_modal(
    console: tcod.console.Console,
    *,
    state: GroundPickupModalState,
) -> None:
    """List floor items available for manual pickup."""
    reg = item_registry()
    from src.ui.inventory_list_layout import join_list_modal

    item_lines = []
    for index, entity in enumerate(state.item_entities):
        letter = state.letter_for_index(index)
        floor_item = entity.components[Item]
        name = reg.display_name_for(floor_item.item_id, floor_item.category)
        item_lines.append(f"{letter}) {name}")
    available_width = min(72, max(12, console.width - 6))
    render_modal(
        console,
        text=join_list_modal(
            "Pick up which item?",
            item_lines,
            "Esc: close",
            available_width=available_width,
        ),
    )


def render_vore_modal(console: tcod.console.Console, *, text: str) -> None:
    """Draw a centered narrative box over the map region."""
    render_centered_modal(console, text=text)


def render_digestion_modal(console: tcod.console.Console, *, text: str) -> None:
    """Draw the player digestion completion narrative."""
    render_centered_modal(console, text=text)


def render_game_over(
    console: tcod.console.Console,
    *,
    player_name: str,
    ending: GameOverEnding,
    monsters_defeated: int,
    runes_collected: int,
    depth: int,
    draw_body: bool = True,
) -> None:
    """Game over summary after a completed run.

    *draw_body*: when False, only the fixed-width ``GAME OVER`` title is drawn
    so present can composite a proportional body (design: title tile, body log font).
    """
    if draw_body:
        lines = [
            "GAME OVER",
            "",
            player_name,
            format_game_over_ending(ending),
            "",
            f"Monsters defeated: {monsters_defeated}",
            f"Runes collected: {runes_collected}",
            f"Depth: {depth}",
            "",
            "Press Enter to return to menu",
        ]
    else:
        # Title only (fixed-width); proportional body composites below in present.
        lines = ["GAME OVER"]
    inner_width = min(max((len(line) for line in lines), default=0), 56)
    box_width = inner_width + 4
    box_height = len(lines) + 4
    x = max(1, (console.width - box_width) // 2)
    if draw_body:
        y = max(1, (console.height - box_height) // 2)
    else:
        # Upper band so the proportional body panel can sit under the title.
        y = max(1, console.height // 5 - box_height // 2)
    # Match proportional dialog chrome (dark fill + golden border).
    from src.ui.menu_dialog import DIALOG_BG, _draw_dialog_chrome

    _draw_dialog_chrome(console, x, y, box_width, box_height)
    for row_offset, line in enumerate(lines):
        padded = cp437_safe(line)[:inner_width].center(inner_width)
        console.print(
            x + 2,
            y + 2 + row_offset,
            padded,
            fg=(255, 240, 210),
            bg=DIALOG_BG,
        )


def render_examine_cursor(
    console: tcod.console.Console,
    cursor: Position,
    game_map: GameMap,
    *,
    camera: MapCamera | None = None,
    draw_on_unexplored: bool = False,
) -> None:
    """Highlight the examine/blink cursor (normally only on explored tiles)."""
    if not game_map.in_bounds(cursor.x, cursor.y):
        return
    if not draw_on_unexplored and not game_map.explored[cursor.y, cursor.x]:
        return
    if camera is not None:
        screen = camera.screen_xy(cursor.x, cursor.y)
        if screen is None:
            return
        draw_x, draw_y = screen
    else:
        draw_x, draw_y = cursor.x, cursor.y
    console.print(draw_x, draw_y, "X", fg=(120, 220, 255))