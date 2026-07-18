"""PR6–PR7 / PR11: sidebar player block and NPC list."""

from __future__ import annotations

from src.components import Alignment, Engulfed, Fighter, Position, Stunned
from src.engine import GameEngine
from src.systems.ai import spawn_test_npc
from src.systems.render import npc_condition_bar

from src.ui.regions import PLAY_BLIT_REGIONS, SIDEBAR_BACKGROUND
from src.ui.sidebar import player_block_rows, render_sidebar_npcs, render_sidebar_player

from tests.map_test_helpers import carve_east_of, isolate_other_ais
from tests.ui_test_helpers import (
    default_layout,
    make_region_bundle,
    render_engine_frame,
    sidebar_text,
)


def _cell_char(console, x: int, y: int) -> str:
    ch = int(console.rgba[x, y]["ch"])
    return chr(ch) if ch else " "


def _row_text(console, y: int) -> str:
    return "".join(_cell_char(console, x, y) for x in range(console.width)).strip()


def test_sidebar_blitted_after_map_and_log() -> None:
    assert PLAY_BLIT_REGIONS == frozenset(
        {"map_viewport", "message_log", "sidebar", "status_corner"}
    )


def test_blit_sidebar_copies_player_block_to_root() -> None:
    layout = default_layout()
    bundle = make_region_bundle(layout)
    from tests.ui_test_helpers import make_console

    root = make_console()
    side_console = bundle.console("sidebar")
    fighter = Fighter(
        hp=24,
        max_hp=30,
        accuracy=10.0,
        evade=0,
        ac=1,
        min_damage=1,
        max_damage=1,
    )
    render_sidebar_player(
        side_console,
        player_name="Alex",
        fighter=fighter,
        sidebar=layout.sidebar,
    )
    bundle.blit_sidebar(root)
    rect = layout.region("sidebar")
    name_row = rect.y + layout.sidebar.player_top_pad
    row_text = "".join(
        _cell_char(root, x, name_row) for x in range(rect.x, rect.x + rect.w)
    ).strip()
    assert "Alex" in row_text


def test_render_sidebar_player_shows_name_and_hp_on_separate_rows() -> None:
    layout = default_layout()
    bundle = make_region_bundle(layout)
    side_console = bundle.console("sidebar")
    fighter = Fighter(
        hp=24,
        max_hp=30,
        accuracy=10.0,
        evade=0,
        ac=1,
        min_damage=1,
        max_damage=1,
    )
    render_sidebar_player(
        side_console,
        player_name="Alex",
        fighter=fighter,
        sidebar=layout.sidebar,
    )
    assert _row_text(side_console, layout.sidebar.player_top_pad) == "Alex"
    hp_row = layout.sidebar.player_top_pad + 1
    assert "HP 24/30" in _row_text(side_console, hp_row)
    assert "[" in _row_text(side_console, hp_row)


def test_render_sidebar_player_omits_ailment_flags() -> None:
    layout = default_layout()
    bundle = make_region_bundle(layout)
    side_console = bundle.console("sidebar")
    fighter = Fighter(
        hp=10,
        max_hp=20,
        accuracy=10.0,
        evade=0,
        ac=1,
        min_damage=1,
        max_damage=1,
    )
    render_sidebar_player(
        side_console,
        player_name="Player",
        fighter=fighter,
        sidebar=layout.sidebar,
    )
    text = " ".join(
        _row_text(side_console, y)
        for y in range(player_block_rows(layout.sidebar) + 1)
    )
    assert "STUNNED" not in text
    assert "ENGULFED" not in text
    assert "Depth" not in text


def test_render_sidebar_player_fills_background() -> None:
    layout = default_layout()
    bundle = make_region_bundle(layout)
    side_console = bundle.console("sidebar")
    render_sidebar_player(
        side_console,
        player_name="Alex",
        fighter=None,
        sidebar=layout.sidebar,
    )
    bg = tuple(side_console.rgba[0, 0]["bg"][:3])
    assert bg == SIDEBAR_BACKGROUND


def test_engine_render_shows_player_in_sidebar() -> None:
    engine = GameEngine(player_name="SidebarTest")
    layout = engine.ui_layout
    console = render_engine_frame(engine)
    side_text = sidebar_text(console, layout)
    assert "SidebarTest" in side_text
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    assert f"HP {fighter.hp}/{fighter.max_hp}" in side_text


def test_engine_render_sidebar_omits_engulfed_flag() -> None:
    engine = GameEngine(player_name="Engulfed")
    player = engine.player
    assert player is not None
    player.tags.add(Engulfed)
    player.tags.add(Stunned)
    console = render_engine_frame(engine)
    side_text = sidebar_text(console, engine.ui_layout)
    assert "ENGULFED" not in side_text
    assert "STUNNED" not in side_text


def _render_sidebar(engine: GameEngine):
    layout = engine.ui_layout
    bundle = make_region_bundle(layout)
    side_console = bundle.console("sidebar")
    player = engine.player
    assert player is not None
    fighter = player.components.get(Fighter)
    render_sidebar_player(
        side_console,
        player_name=engine.player_name,
        fighter=fighter,
        sidebar=layout.sidebar,
    )
    render_sidebar_npcs(
        side_console,
        engine.world,
        engine.game_map,
        sidebar=layout.sidebar,
    )
    return side_console, layout


def test_npc_condition_bar_covers_all_fill_counts() -> None:
    fighter = Fighter(
        hp=1,
        max_hp=6,
        accuracy=10.0,
        evade=0,
        ac=1,
        min_damage=1,
        max_damage=1,
    )
    seen: set[int] = set()
    for hp in range(7):
        fighter.hp = hp
        bar = npc_condition_bar(fighter, 6)
        fill = bar.count("#")
        seen.add(fill)
    assert seen == {0, 1, 2, 3, 4, 5, 6}


def test_sidebar_shows_visible_evil_below_player() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    isolate_other_ais(engine)
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    spawn_test_npc(
        engine.world,
        x=pos.x + 1,
        y=pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    engine._update_fov()

    side_console, layout = _render_sidebar(engine)
    evil_row = player_block_rows(layout.sidebar)
    assert "wolf" in _row_text(side_console, evil_row)
    assert "[" in _row_text(side_console, evil_row + 1)


def test_sidebar_shows_visible_good_at_bottom() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    isolate_other_ais(engine)
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    spawn_test_npc(
        engine.world,
        x=pos.x + 1,
        y=pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    engine._update_fov()

    side_console, layout = _render_sidebar(engine)
    height = layout.region("sidebar").h
    name_row = height - layout.sidebar.good_bottom_pad - layout.sidebar.rows_per_npc
    assert "knight" in _row_text(side_console, name_row)


def test_sidebar_omits_neutral_and_out_of_fov_npcs() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    isolate_other_ais(engine)
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    spawn_test_npc(
        engine.world,
        x=pos.x + 1,
        y=pos.y,
        species="villager",
        alignment=Alignment.NEUTRAL,
    )
    spawn_test_npc(
        engine.world,
        x=pos.x + 1,
        y=pos.y + 20,
        species="lurker",
        alignment=Alignment.EVIL,
    )
    engine._update_fov()

    side_console, layout = _render_sidebar(engine)
    start = player_block_rows(layout.sidebar)
    npc_rows = [_row_text(side_console, y) for y in range(start, side_console.height)]
    assert all("villager" not in row for row in npc_rows)
    assert all("lurker" not in row for row in npc_rows)


def test_sidebar_evil_sorted_nearest_first() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    isolate_other_ais(engine)
    pos = player.components[Position]
    carve_east_of(engine, pos, 4)
    spawn_test_npc(
        engine.world,
        x=pos.x + 3,
        y=pos.y,
        species="far",
        alignment=Alignment.EVIL,
    )
    spawn_test_npc(
        engine.world,
        x=pos.x + 1,
        y=pos.y,
        species="near",
        alignment=Alignment.EVIL,
    )
    engine._update_fov()

    side_console, layout = _render_sidebar(engine)
    base = player_block_rows(layout.sidebar)
    step = layout.sidebar.rows_per_npc
    assert "near" in _row_text(side_console, base)
    assert "far" in _row_text(side_console, base + step)


def _short_sidebar_console(engine: GameEngine, *, height: int):
    from tests.ui_test_helpers import make_console

    layout = engine.ui_layout
    side_console = make_console(layout.region("sidebar").w, height)
    player = engine.player
    assert player is not None
    fighter = player.components.get(Fighter)
    render_sidebar_player(
        side_console,
        player_name=engine.player_name,
        fighter=fighter,
        sidebar=layout.sidebar,
    )
    render_sidebar_npcs(
        side_console,
        engine.world,
        engine.game_map,
        sidebar=layout.sidebar,
    )
    return side_console, layout


def test_sidebar_evil_overflow_summary_when_height_is_tight() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    isolate_other_ais(engine)
    pos = player.components[Position]
    carve_east_of(engine, pos, 12)
    for index in range(10):
        spawn_test_npc(
            engine.world,
            x=pos.x + 1 + (index % 3),
            y=pos.y,
            species=f"wolf{index}",
            alignment=Alignment.EVIL,
        )
    engine._update_fov()

    height = player_block_rows(engine.ui_layout.sidebar) + 7 + engine.ui_layout.sidebar.good_bottom_pad
    side_console, layout = _short_sidebar_console(engine, height=height)
    npc_text = " ".join(
        _row_text(side_console, y)
        for y in range(player_block_rows(layout.sidebar), side_console.height)
    )
    assert "+6 evil" in npc_text
    shown = sum(1 for token in npc_text.split() if token.startswith("wolf"))
    assert 0 < shown < 10


def test_sidebar_good_overflow_summary() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    isolate_other_ais(engine)
    pos = player.components[Position]
    carve_east_of(engine, pos, 6)
    for index in range(5):
        spawn_test_npc(
            engine.world,
            x=pos.x + 1 + index,
            y=pos.y,
            species=f"knight{index}",
            alignment=Alignment.GOOD,
        )
    engine._update_fov()

    height = player_block_rows(engine.ui_layout.sidebar) + 4 + engine.ui_layout.sidebar.good_bottom_pad
    side_console, layout = _short_sidebar_console(engine, height=height)
    npc_text = " ".join(
        _row_text(side_console, y)
        for y in range(player_block_rows(layout.sidebar), side_console.height)
    )
    assert "+3 good" in npc_text
    shown = sum(1 for token in npc_text.split() if token.startswith("knight"))
    assert 0 < shown < 5


def test_sidebar_good_nearest_at_bottom_edge() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    isolate_other_ais(engine)
    pos = player.components[Position]
    carve_east_of(engine, pos, 4)
    spawn_test_npc(
        engine.world,
        x=pos.x + 3,
        y=pos.y,
        species="far",
        alignment=Alignment.GOOD,
    )
    spawn_test_npc(
        engine.world,
        x=pos.x + 1,
        y=pos.y,
        species="near",
        alignment=Alignment.GOOD,
    )
    engine._update_fov()

    side_console, layout = _render_sidebar(engine)
    height = layout.region("sidebar").h
    pad = layout.sidebar.good_bottom_pad
    step = layout.sidebar.rows_per_npc
    near_row = height - pad - step
    far_row = height - pad - step * 2
    assert "near" in _row_text(side_console, near_row)
    assert "far" in _row_text(side_console, far_row)