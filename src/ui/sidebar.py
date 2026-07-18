from __future__ import annotations

import tcod.console
from tcod.ecs import Entity, Registry

from src.components import Alignment, Fighter, NPCAlignment, Player, Position
from src.map_gen import GameMap
from src.systems.fov import entity_visible_to_player
from src.systems.naming import entity_display_name
from src.systems.render import _hp_bar, npc_condition_bar
from src.text import cp437_safe
from src.ui.layout import SidebarLayout
from src.ui.regions import SIDEBAR_BACKGROUND
from src.ui.sidebar_npc_layout import (
    BandLayout,
    column_geometry,
    entry_slot,
    resolve_npc_bands,
)

SIDEBAR_PLAYER_FG = (255, 255, 255)
SIDEBAR_HP_FG = (255, 220, 120)
SIDEBAR_EVIL_FG = (240, 150, 140)
SIDEBAR_GOOD_FG = (150, 200, 230)
SIDEBAR_OVERFLOW_FG = (130, 130, 150)


def player_block_rows(sidebar: SidebarLayout) -> int:
    """Rows reserved for top pad, player name, HP line, and gap before evil band."""
    return sidebar.player_top_pad + 2 + sidebar.player_bottom_pad


def _chebyshev_distance(ax: int, ay: int, bx: int, by: int) -> int:
    return max(abs(ax - bx), abs(ay - by))


def _visible_sidebar_npcs(
    world: Registry,
    game_map: GameMap,
) -> tuple[list[tuple[int, Entity]], list[tuple[int, Entity]]]:
    evil: list[tuple[int, Entity]] = []
    good: list[tuple[int, Entity]] = []
    player = next(iter(world.Q.all_of(tags=[Player])), None)
    if player is None:
        return evil, good
    player_pos = player.components[Position]

    for entity in world.Q.all_of(components=[Fighter, Position, NPCAlignment]):
        if Player in entity.tags:
            continue
        if not entity_visible_to_player(game_map, entity):
            continue
        alignment = entity.components[NPCAlignment].alignment
        if alignment == Alignment.NEUTRAL:
            continue
        pos = entity.components[Position]
        distance = _chebyshev_distance(player_pos.x, player_pos.y, pos.x, pos.y)
        if alignment == Alignment.EVIL:
            evil.append((distance, entity))
        else:
            good.append((distance, entity))

    evil.sort(key=lambda item: item[0])
    good.sort(key=lambda item: item[0])
    return evil, good


def _draw_npc_entry(
    console: tcod.console.Console,
    *,
    x: int,
    base_row: int,
    entity: Entity,
    sidebar: SidebarLayout,
    line_limit: int,
    fg: tuple[int, int, int],
) -> None:
    fighter = entity.components[Fighter]
    name = cp437_safe(entity_display_name(entity))[:line_limit]
    bar = npc_condition_bar(fighter, sidebar.npc_hp_bar_width)
    console.print(x, base_row, name, fg=fg)
    console.print(x, base_row + 1, bar[:line_limit], fg=fg)


def _draw_evil_band(
    console: tcod.console.Console,
    *,
    evil: list[tuple[int, Entity]],
    evil_plan: BandLayout,
    player_rows: int,
    sidebar: SidebarLayout,
    good_band_top: int,
) -> None:
    if evil_plan.display_count <= 0 and evil_plan.overflow_count <= 0:
        return

    columns = column_geometry(console.width, evil_plan.column_count)
    entry_rows = sidebar.rows_per_npc
    last_entry_bottom = player_rows - 1

    for index in range(evil_plan.display_count):
        col_index, row_slot = entry_slot(
            index,
            col0_count=evil_plan.col0_count,
            interleaved_fill=evil_plan.interleaved_fill,
        )
        x, line_limit = columns[col_index]
        _, entity = evil[index]
        base_row = player_rows + row_slot * entry_rows
        if base_row + entry_rows > good_band_top:
            continue
        _draw_npc_entry(
            console,
            x=x,
            base_row=base_row,
            entity=entity,
            sidebar=sidebar,
            line_limit=line_limit,
            fg=SIDEBAR_EVIL_FG,
        )
        last_entry_bottom = max(last_entry_bottom, base_row + entry_rows - 1)

    if evil_plan.overflow_count > 0:
        overflow_row = min(good_band_top - 1, last_entry_bottom + 1)
        if overflow_row >= player_rows and overflow_row < good_band_top:
            line_limit = max(1, console.width - 2)
            console.print(
                1,
                overflow_row,
                f"+{evil_plan.overflow_count} evil"[:line_limit],
                fg=SIDEBAR_OVERFLOW_FG,
            )


def _draw_good_band(
    console: tcod.console.Console,
    *,
    good: list[tuple[int, Entity]],
    good_plan: BandLayout,
    sidebar: SidebarLayout,
    good_band_top: int,
) -> None:
    if good_plan.display_count <= 0 and good_plan.overflow_count <= 0:
        return

    height = console.height
    columns = column_geometry(console.width, good_plan.column_count)
    entry_rows = sidebar.rows_per_npc

    for index in range(good_plan.display_count):
        col_index, row_slot = entry_slot(
            index,
            col0_count=good_plan.col0_count,
            interleaved_fill=good_plan.interleaved_fill,
        )
        x, line_limit = columns[col_index]
        _, entity = good[index]
        base_row = height - sidebar.good_bottom_pad - entry_rows * (row_slot + 1)
        if base_row < good_band_top:
            continue
        _draw_npc_entry(
            console,
            x=x,
            base_row=base_row,
            entity=entity,
            sidebar=sidebar,
            line_limit=line_limit,
            fg=SIDEBAR_GOOD_FG,
        )

    if good_plan.overflow_count > 0:
        overflow_row = good_band_top
        if overflow_row < height - sidebar.good_bottom_pad:
            line_limit = max(1, console.width - 2)
            console.print(
                1,
                overflow_row,
                f"+{good_plan.overflow_count} good"[:line_limit],
                fg=SIDEBAR_OVERFLOW_FG,
            )


def render_sidebar_player(
    console: tcod.console.Console,
    *,
    player_name: str,
    fighter: Fighter | None = None,
    sidebar: SidebarLayout,
) -> None:
    """Draw sidebar background plus padded player name and HP bar."""
    console.draw_rect(
        0,
        0,
        console.width,
        console.height,
        ch=0,
        fg=None,
        bg=SIDEBAR_BACKGROUND,
    )
    line_limit = max(1, console.width - 2)
    name_row = sidebar.player_top_pad
    console.print(1, name_row, cp437_safe(player_name)[:line_limit], fg=SIDEBAR_PLAYER_FG)
    if fighter is None:
        return
    hp_row = name_row + 1
    hp_line = (
        f"HP {fighter.hp}/{fighter.max_hp} "
        f"{_hp_bar(fighter, sidebar.hp_bar_width)}"
    )
    console.print(1, hp_row, hp_line[:line_limit], fg=SIDEBAR_HP_FG)


def render_sidebar_npcs(
    console: tcod.console.Console,
    world: Registry,
    game_map: GameMap,
    *,
    sidebar: SidebarLayout,
) -> None:
    """Draw FOV-visible evil/good NPC entries (name + estimate bar + spacer)."""
    evil, good = _visible_sidebar_npcs(world, game_map)
    player_rows = player_block_rows(sidebar)
    evil_plan, good_plan, good_band_top = resolve_npc_bands(
        height=console.height,
        player_rows=player_rows,
        sidebar=sidebar,
        evil_count=len(evil),
        good_count=len(good),
    )
    _draw_evil_band(
        console,
        evil=evil,
        evil_plan=evil_plan,
        player_rows=player_rows,
        sidebar=sidebar,
        good_band_top=good_band_top,
    )
    _draw_good_band(
        console,
        good=good,
        good_plan=good_plan,
        sidebar=sidebar,
        good_band_top=good_band_top,
    )