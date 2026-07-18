"""PR1: secret 1v1 arena (Ctrl+B)."""

from __future__ import annotations

from pathlib import Path

import pytest
import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.app import App, AppPhase
from src.arena import format_arena_victory_message, initialize_arena
from src.arena_map import (
    ARENA_ENEMY_X,
    ARENA_PLAYER_X,
    ARENA_WALK_Y,
    build_arena_map,
)
from src.components import Fighter, Position, SpeciesId
from src.data.entity_loader import parse_entity_registry
from src.data.entity_registry import EntityRegistry
from src.engine import GameEngine
from src.entity_entry import (
    ENTITY_ENTRY_NOT_EVIL,
    ENTITY_ENTRY_UNKNOWN,
    EntityEntryAction,
    EntityEntryState,
    evil_entity_ids,
    handle_entity_entry_event,
    validate_entity_entry,
)
from src.events import fire_entity_defeated
from src.map_gen import Tile
from src.menu import is_ctrl_b
from src.past_runs.store import PastRunsStore
from src.save.coordinator import SaveCoordinator
from src.save.store import SaveNotFoundError, SaveStore
from src.settings_store import SettingsStore
from src.systems.digestion import GameOverEnding, GameOverState
from tests.entity_test_helpers import minimal_entity_payload, spawn_fixture_wolf


def _key(sym: KeySym, *, mod: int = 0) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def _onboarded_settings(tmp_path: Path) -> SettingsStore:
    path = tmp_path / "settings.json"
    settings = SettingsStore(
        tutorial_prompt_answered=True,
        vore_prefs_onboarding_complete=True,
        path=path,
    )
    settings.save(path)
    return SettingsStore.load(path)


def _arena_app(tmp_path: Path) -> App:
    return App(
        settings=_onboarded_settings(tmp_path),
        save_coordinator=SaveCoordinator(store=SaveStore(tmp_path / "save")),
    )


def _fixture_registry() -> EntityRegistry:
    return parse_entity_registry(
        {
            "schema_version": 1,
            "entities": [
                minimal_entity_payload(
                    "duel_rat",
                    display_name="rat",
                    spawn={"weight": 5, "min_depth": 2, "max_depth": 5, "terrain": "land"},
                ),
                minimal_entity_payload(
                    "retired_evil",
                    alignment="evil",
                    spawn={"weight": 0, "min_depth": 3, "max_depth": 10, "terrain": "land"},
                ),
                minimal_entity_payload(
                    "good_guy",
                    alignment="good",
                    digestion_damage_per_tick=None,
                    digest_time=None,
                    vore_narratives=None,
                    digestion_complete=None,
                    npc_vore_hit=None,
                    npc_vore_miss=None,
                    offscreen_vore=None,
                    offscreen_digest=None,
                ),
                minimal_entity_payload("pond_shark", alignment="evil", mobility="aquatic"),
            ],
        }
    )


def test_validate_entity_entry_messages() -> None:
    registry = _fixture_registry()
    assert validate_entity_entry("missing", registry) == (None, ENTITY_ENTRY_UNKNOWN)
    assert validate_entity_entry("good_guy", registry)[1] == ENTITY_ENTRY_NOT_EVIL
    definition, error = validate_entity_entry("duel_rat", registry)
    assert error == ""
    assert definition is not None
    assert definition.id == "duel_rat"


def test_evil_entity_ids_includes_weight_zero() -> None:
    registry = _fixture_registry()
    ids = evil_entity_ids(registry)
    assert "duel_rat" in ids
    assert "retired_evil" in ids
    assert "good_guy" not in ids


def test_build_arena_map_geometry() -> None:
    land_map = build_arena_map(aquatic_enemy=False)
    assert land_map.width == 10
    assert land_map.height == 3
    assert Tile(land_map.tiles[ARENA_WALK_Y, ARENA_PLAYER_X]) == Tile.FLOOR
    assert Tile(land_map.tiles[ARENA_WALK_Y, ARENA_ENEMY_X]) == Tile.FLOOR
    assert Tile(land_map.tiles[0, 0]) == Tile.WALL
    assert land_map.explored.all()

    water_map = build_arena_map(aquatic_enemy=True)
    assert Tile(water_map.tiles[ARENA_WALK_Y, ARENA_ENEMY_X]) == Tile.DEEP_WATER


def test_initialize_arena_spawns_player_and_enemy(tmp_path: Path) -> None:
    registry = _fixture_registry()
    engine = GameEngine(skip_new_game=True)
    enemy = initialize_arena(engine, "duel_rat", seed=42, registry=registry)

    assert engine.arena_mode is True
    assert engine.level_warped is True
    assert engine.floor_depth == 2
    assert engine.player is not None
    player_pos = engine.player.components[Position]
    enemy_pos = enemy.components[Position]
    assert (player_pos.x, player_pos.y) == (ARENA_PLAYER_X, ARENA_WALK_Y)
    assert (enemy_pos.x, enemy_pos.y) == (ARENA_ENEMY_X, ARENA_WALK_Y)
    assert enemy.components[SpeciesId].id == "duel_rat"


def test_initialize_arena_aquatic_enemy_gets_water_tile(tmp_path: Path) -> None:
    registry = _fixture_registry()
    engine = GameEngine(skip_new_game=True)
    initialize_arena(engine, "pond_shark", seed=7, registry=registry)
    assert Tile(engine.game_map.tiles[ARENA_WALK_Y, ARENA_ENEMY_X]) == Tile.DEEP_WATER


def test_arena_victory_on_enemy_defeated(tmp_path: Path) -> None:
    registry = _fixture_registry()
    engine = GameEngine(skip_new_game=True)
    enemy = initialize_arena(engine, "duel_rat", seed=1, registry=registry)
    enemy.components[Fighter].hp = 0
    fire_entity_defeated(enemy)
    assert engine.arena_victory_active is True
    assert engine.arena_victory_message == "You have defeated the rat!"


def test_format_arena_victory_message() -> None:
    from tcod.ecs import Registry

    world = Registry()
    enemy = spawn_fixture_wolf(world, 0, 0)
    assert format_arena_victory_message(enemy) == "You have defeated the wolf!"


def test_arena_save_now_is_noop_without_file(tmp_path: Path) -> None:
    store = SaveStore(tmp_path / "save")
    coordinator = SaveCoordinator(store=store)
    registry = _fixture_registry()
    engine = GameEngine(
        skip_new_game=True,
        save_coordinator=coordinator,
    )
    initialize_arena(engine, "duel_rat", seed=99, registry=registry)
    assert coordinator.save_now(engine) is True
    with pytest.raises(SaveNotFoundError):
        store.load_best()


def test_level_warped_skips_past_runs_for_arena_digest(tmp_path: Path) -> None:
    store = PastRunsStore(tmp_path / "past_runs.json")
    state = GameOverState()
    state.open(
        player_name="Player",
        ending=GameOverEnding(kind="digested", detail="rat"),
        monsters_defeated=0,
        runes_collected=0,
        depth=2,
        past_runs_store=store,
        level_warped=True,
    )
    assert store.load_runs() == []


def test_is_ctrl_b() -> None:
    assert is_ctrl_b(_key(KeySym.B, mod=Modifier.CTRL))
    assert not is_ctrl_b(_key(KeySym.B))


def test_ctrl_b_enters_entity_entry_and_starts_arena(tmp_path: Path) -> None:
    from unittest.mock import patch

    from tests.ui_test_helpers import make_console

    console = make_console()
    app = _arena_app(tmp_path)
    registry = _fixture_registry()

    with patch("src.entity_entry.load_entity_registry", return_value=registry), patch(
        "src.arena.load_entity_registry",
        return_value=registry,
    ), patch("src.data.entity_loader.load_entity_registry", return_value=registry):
        assert app.phase is AppPhase.MENU
        app.handle_event(_key(KeySym.B, mod=Modifier.CTRL))
        assert app.phase is AppPhase.ENTITY_ENTRY

        app.entity_entry.buffer = "duel_rat"
        app.handle_event(_key(KeySym.RETURN), console=console)

    assert app.phase is AppPhase.PLAY
    assert app.engine is not None
    assert app.engine.arena_mode is True
    assert app.engine.player_name == "Player"
    assert app.engine.floor_depth == 2


def test_entity_entry_rejects_unknown_id() -> None:
    registry = _fixture_registry()
    state = EntityEntryState(buffer="nope")
    action = handle_entity_entry_event(state, _key(KeySym.RETURN), registry=registry)
    assert action is EntityEntryAction.NONE
    assert state.error_message == ENTITY_ENTRY_UNKNOWN