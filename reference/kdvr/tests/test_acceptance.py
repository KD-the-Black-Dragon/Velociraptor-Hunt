"""Automated checks for core-roguelike acceptance criteria (no GUI required)."""

from __future__ import annotations

import random
import string

from src import messages
from src.components import (
    AI,
    Fighter,
    Inventory,
    Item,
    Player,
    Position,
    Stunned,
    VoreCapable,
)
from src.components import InventoryItemInstance, ItemCategory
from src.constants import GAME_TITLE
from src.engine import GameEngine
from src.input_handlers import DIRECTION_KEYS, INVENTORY_KEYS
from src.map_gen import Tile, generate_dungeon
from src.systems.combat import try_action
from src.systems.fov import can_see, update_fov
from src.systems.inventory import make_potion_instance, pickup_items_at, use_inventory_slot
from src.systems.movement import MOVEMENT_DIRECTIONS, can_move_to, try_move


def test_ac1_window_title_and_dungeon() -> None:
    assert GAME_TITLE == "KD's Vore Roguelike"
    dungeon = generate_dungeon(80, 44, seed=1)
    assert (dungeon.tiles == Tile.FLOOR).any()
    assert dungeon.is_walkable(*dungeon.enter_xy)


def test_ac2_eight_direction_movement_and_walls() -> None:
    assert len(MOVEMENT_DIRECTIONS) == 8
    assert len(DIRECTION_KEYS) >= 12  # arrows, diagonals, and numpad cover 8 directions
    assert len({v for v in DIRECTION_KEYS.values()}) == 8
    engine = GameEngine()
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    # Wall blocks movement.
    for direction in MOVEMENT_DIRECTIONS:
        dx, dy = direction
        nx, ny = pos.x + dx, pos.y + dy
        if not engine.game_map.is_walkable(nx, ny):
            assert not try_move(engine.world, engine.game_map, player, direction)
    # Corner cut allowed when destination walkable.
    for y in range(1, engine.game_map.height - 1):
        for x in range(1, engine.game_map.width - 1):
            if engine.game_map.tiles[y, x] != Tile.FLOOR:
                continue
            for dx, dy in ((-1, 1), (1, -1)):
                nx, ny = x + dx, y + dy
                if engine.game_map.is_walkable(nx, ny):
                    engine.player.components[Position] = Position(x, y)
                    if can_move_to(engine.world, engine.game_map, player, Position(x, y), (dx, dy)):
                        return
    raise AssertionError("No corner-cut scenario found in generated map")


def test_ac3_fov_and_explored_memory() -> None:
    engine = GameEngine()
    explored_before = engine.game_map.explored.sum()
    visible_before = engine.game_map.visible.sum()
    assert explored_before > 0
    assert visible_before > 0
    try_move(engine.world, engine.game_map, engine.player, (1, 0))
    engine._run_world_turn()
    assert engine.game_map.explored.sum() >= explored_before
    # Explored can exceed visible after leaving tiles.
    pos = engine.player.components[Position]
    update_fov(engine.game_map, pos.x, pos.y)
    assert engine.game_map.explored.sum() >= engine.game_map.visible.sum()


def test_ac4_monster_spawn_and_chase() -> None:
    engine = GameEngine()
    monsters = list(engine.world.Q.all_of(components=[AI, Position]))
    assert len(monsters) > 0
    player_pos = engine.player.components[Position]
    for monster in monsters:
        mpos = monster.components[Position]
        assert (mpos.x, mpos.y) != (player_pos.x, player_pos.y)


def test_ac5_bump_combat_defeated_terminology() -> None:
    engine = GameEngine()
    from tests.map_test_helpers import first_wolf, isolate_other_ais

    monster = first_wolf(engine)
    isolate_other_ais(engine, keep=(monster,))
    monster.components[Fighter].hp = 1
    mpos = monster.components[Position]
    engine.player.components[Position] = Position(mpos.x - 1, mpos.y)
    rng = random.Random(0)
    for _ in range(20):
        try_action(
            engine.world,
            engine.game_map,
            engine.player,
            (1, 0),
            engine.message_log,
            rng=rng,
        )
        if monster not in list(engine.world.Q.all_of(components=[AI, Fighter])):
            break
    assert monster not in list(engine.world.Q.all_of(components=[AI]))
    log_text = " ".join(engine.message_log.lines()).lower()
    assert "defeated" in log_text
    assert "wolf" in log_text
    assert "monster" not in log_text
    assert "kill" not in log_text
    assert "die" not in log_text


def test_ac6_stunned_and_potion_while_stunned() -> None:
    engine = GameEngine()
    player = engine.player
    fighter = player.components[Fighter]
    fighter.hp = 0
    player.tags.add(Stunned)
    assert not try_action(engine.world, engine.game_map, player, (1, 0), engine.message_log)
    player.components[Inventory].slots["a"] = make_potion_instance()
    assert use_inventory_slot(player, "a", engine.message_log)
    assert fighter.hp > 0
    assert Stunned not in player.tags
    log_text = " ".join(engine.message_log.lines()).lower()
    assert "digested" not in log_text


def test_ac7_inventory_slots_and_full_rejection() -> None:
    engine = GameEngine()
    inventory = engine.player.components[Inventory]
    assert len(inventory.slots) == 26
    assert set(inventory.slots) == set(string.ascii_lowercase)
    assert len(INVENTORY_KEYS) == 26
    for letter in string.ascii_lowercase:
        inventory.slots[letter] = InventoryItemInstance(
            item_id="dagger",
            category=ItemCategory.WEAPON,
            durability=100,
        )
    item = engine.world[object()]
    pos = engine.player.components[Position]
    item.components[Position] = pos
    item.components[Item] = Item(item_id="dagger", category=ItemCategory.WEAPON, durability=100)
    pickup_items_at(engine.world, engine.player, pos.x, pos.y, engine.message_log)
    assert Item in item.components
    assert messages.inventory_full() in engine.message_log.lines()


def test_ac8_no_top_level_vore_package() -> None:
    """Core AC8: no top-level `src.vore` package (systems/vore.py submodule is allowed)."""
    import src

    assert not hasattr(src, "vore")
    import pkgutil

    assert not any(m.name.endswith("vore") for m in pkgutil.iter_modules(src.__path__, src.__name__ + "."))


def test_core_systems_no_vore_import() -> None:
    """Core modular boundary: movement/inventory must not load vore at import time."""
    import subprocess
    import sys

    script = """
import importlib
import sys
for name in ("src.systems.movement", "src.systems.inventory"):
    importlib.import_module(name)
assert "src.systems.vore" not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1]),
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_vore_smoke_engulf_struggle_escape() -> None:
    """Vore domain smoke: engulf, struggle message, defeat predator, escape."""
    from unittest.mock import patch

    import tcod.event
    from tcod.event import KeySym, Modifier, Scancode

    from src.components import Engulfed, Fighter, Position
    from src.constants import VORE_ENABLED
    from src.engine import GameEngine
    from src.systems.vore import engulf_player
    from tests.map_test_helpers import carve_east_of

    assert VORE_ENABLED is True
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf = next(iter(engine.world.Q.all_of(components=[AI, Fighter, Position])))
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    wolf.components[Position] = Position(pos.x + 1, pos.y)
    wolf.components[Fighter].hp = 1
    engulf_player(
        engine.world, player, wolf, engine.message_log, narrative_type="OV"
    )
    assert Engulfed in player.tags
    with patch.object(engine.rng, "random", return_value=1.0):
        engine.handle_event(
            tcod.event.KeyDown(sym=KeySym.UP, scancode=Scancode.UNKNOWN, mod=Modifier.NONE),
        )
    assert Engulfed not in player.tags
    log = " ".join(engine.message_log.lines()).lower()
    assert "break free" in log or "fight to break free" in log
    assert "escape from" in log


def test_event_hooks_exist() -> None:
    from src import events

    assert callable(events.fire_entity_defeated)
    assert callable(events.fire_player_stunned)
    assert callable(events.fire_item_used)
    assert callable(events.fire_player_turn_consumed)


def test_items_spawn_on_new_game() -> None:
    engine = GameEngine()
    items = list(engine.world.Q.all_of(components=[Item]))
    assert len(items) >= 1


def test_ac_quit_ctrl_q(tmp_path) -> None:
    """Ctrl+Q during play opens quit confirm; engine alone does not exit."""
    import tcod.event
    from tcod.event import KeySym, Modifier, Scancode

    from src.app import App, AppPhase
    from src.engine import EngineEventResult

    engine = GameEngine()
    assert (
        engine.handle_event(
            tcod.event.KeyDown(sym=KeySym.Q, scancode=Scancode.UNKNOWN, mod=Modifier.CTRL),
        )
        is EngineEventResult.CONTINUE
    )

    from tests.ui_test_helpers import make_console

    from tests.save_test_helpers import app_with_isolated_save

    app = app_with_isolated_save(tmp_path)
    console = make_console()
    app.handle_event(
        tcod.event.KeyDown(sym=KeySym.RETURN, scancode=Scancode.UNKNOWN, mod=Modifier.NONE),
        console=console,
    )
    app.handle_event(
        tcod.event.KeyDown(sym=KeySym.RETURN, scancode=Scancode.UNKNOWN, mod=Modifier.NONE),
        console=console,
    )
    assert app.phase is AppPhase.PLAY
    app.handle_event(
        tcod.event.KeyDown(sym=KeySym.Q, scancode=Scancode.UNKNOWN, mod=Modifier.CTRL),
    )
    assert app.quit_confirm is not None