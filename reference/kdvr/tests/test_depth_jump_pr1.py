"""PR1: secret depth-jump new game (Ctrl+G)."""

from __future__ import annotations

import random
from pathlib import Path

import tcod.event
from tcod.ecs import Registry
from tcod.event import KeySym, Modifier, Scancode

from src.app import App, AppPhase
from src.components import EquipState, Fighter, Inventory, Player, PlayerProgression
from src.data.depth_jump_start_loader import DepthJumpStartConfig, parse_depth_jump_start_config
from src.data.floor_rune_registry import FloorRuneRegistry
from src.depth_entry import (
    DEPTH_ENTRY_INVALID,
    DepthEntryAction,
    DepthEntryState,
    handle_depth_entry_event,
    parse_depth_value,
)
from src.depth_jump_loadout import (
    apply_depth_jump_loadout,
    eligible_weapons,
    simulated_runes_for_floor,
)
from src.items.strength import pick_strongest, weapon_strength_key
from src.menu import is_ctrl_g
from src.past_runs.store import PastRunsStore
from src.settings_store import SettingsStore
from src.systems.digestion import GameOverEnding, GameOverState
from src.save.coordinator import SaveCoordinator
from src.save.store import SaveStore
from tests.item_test_helpers import (
    _armor_entry,
    _throwable_entry,
    _weapon_entry,
    default_test_wand_entry,
    install_item_registry,
    write_item_fixtures,
)

from src.data.item_loader import load_item_registry


def _key(sym: KeySym, *, mod: int = 0) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def _depth_jump_app(tmp_path: Path) -> App:
    return App(
        settings=_onboarded_settings(tmp_path),
        save_coordinator=SaveCoordinator(store=SaveStore(tmp_path / "save")),
    )


def _onboarded_settings(tmp_path: Path) -> SettingsStore:
    path = tmp_path / "settings.json"
    settings = SettingsStore(
        tutorial_prompt_answered=True,
        vore_prefs_onboarding_complete=True,
        path=path,
    )
    settings.save(path)
    return SettingsStore.load(path)


def _test_player() -> tuple[Registry, object]:
    world = Registry()
    player = world.new_entity()
    player.tags.add(Player)
    player.components[Inventory] = Inventory()
    player.components[EquipState] = EquipState()
    player.components[Fighter] = Fighter(
        hp=20,
        max_hp=20,
        accuracy=0.5,
        evade=1,
        ac=1,
        min_damage=1,
        max_damage=2,
    )
    player.components[PlayerProgression] = PlayerProgression()
    return world, player


def _fixture_registry(tmp_path: Path):
    write_item_fixtures(
        tmp_path,
        weapons=[
            _weapon_entry(
                "weak_blade",
                min_damage=3,
                max_damage=10,
                spawn_min_depth=1,
                spawn_max_depth=20,
            ),
            _weapon_entry(
                "strong_blade",
                min_damage=6,
                max_damage=8,
                spawn_min_depth=1,
                spawn_max_depth=20,
            ),
            _weapon_entry(
                "late_only",
                min_damage=20,
                max_damage=30,
                spawn_min_depth=15,
                spawn_max_depth=20,
            ),
        ],
        armor=[
            _armor_entry("thin", ac_bonus=2, spawn_min_depth=1, spawn_max_depth=20),
            _armor_entry("heavy", ac_bonus=5, spawn_min_depth=1, spawn_max_depth=20),
        ],
        throwables=[
            _throwable_entry(
                "dart",
                min_damage=2,
                max_damage=4,
                spawn_min_depth=1,
                spawn_max_depth=20,
            ),
            _throwable_entry(
                "javelin",
                min_damage=5,
                max_damage=8,
                spawn_min_depth=1,
                spawn_max_depth=20,
            ),
        ],
        potions=[
            {
                "id": "heal_a",
                "display_name": "heal a",
                "glyph": "!",
                "fg": [255, 0, 0],
                "examine": "heal",
                "effect": "heal",
                "heal_amount": 5,
                "spawn_weight": 1,
                "spawn_min_depth": 1,
                "spawn_max_depth": 20,
            }
        ],
        wands=[default_test_wand_entry()],
    )
    return load_item_registry(
        weapons_path=tmp_path / "weapons.json",
        armor_path=tmp_path / "armor.json",
        potions_path=tmp_path / "potions.json",
        wands_path=tmp_path / "wands.json",
        throwables_path=tmp_path / "throwables.json",
    )


def _test_config() -> DepthJumpStartConfig:
    return parse_depth_jump_start_config(
        {
            "schema_version": 1,
            "max_target_depth": 20,
            "throwable_stack_count": 5,
            "potion_count": 3,
            "wand_count": 3,
            "simulated_runes_min_numerator": 2,
            "simulated_runes_min_denominator": 3,
        }
    )


def test_weapon_strength_prefers_higher_min_damage() -> None:
    class _W:
        def __init__(self, min_d: int, max_d: int, acc: float) -> None:
            self.min_damage = min_d
            self.max_damage = max_d
            self.accuracy_bonus = acc

    items = [_W(3, 12, 0.2), _W(6, 8, 0.0)]
    picked = pick_strongest(items, key=weapon_strength_key, rng=random.Random(1))
    assert picked is not None
    assert picked.min_damage == 6


def test_simulated_runes_for_floor_uses_two_thirds_to_full() -> None:
    cfg = _test_config()
    rng = random.Random(0)
    counts = {
        simulated_runes_for_floor(runes_per_floor=3, config=cfg, rng=rng)
        for _ in range(50)
    }
    assert counts <= {2, 3}
    assert 2 in counts
    assert 3 in counts


def test_depth_entry_rejects_out_of_range_with_exact_message() -> None:
    state = DepthEntryState(buffer="0")
    action = handle_depth_entry_event(state, _key(KeySym.RETURN), max_depth=20)
    assert action is DepthEntryAction.NONE
    assert state.error_message == DEPTH_ENTRY_INVALID

    state.buffer = "21"
    action = handle_depth_entry_event(state, _key(KeySym.RETURN), max_depth=20)
    assert action is DepthEntryAction.NONE
    assert state.error_message == DEPTH_ENTRY_INVALID

    state.buffer = "10"
    action = handle_depth_entry_event(state, _key(KeySym.RETURN), max_depth=20)
    assert action is DepthEntryAction.CONFIRM
    assert parse_depth_value("10", max_depth=20) == 10


def test_loadout_uses_loot_depth_minus_one(tmp_path: Path) -> None:
    registry = _fixture_registry(tmp_path)
    install_item_registry(registry)
    _, player = _test_player()
    rng = random.Random(42)

    apply_depth_jump_loadout(
        player,
        target_depth=10,
        rng=rng,
        registry=registry,
        rune_registry=FloorRuneRegistry(schema_version=1, runes=(), runes_per_floor=0),
        runes_per_floor=3,
        rune_pieces_multiplier=1,
        config=_test_config(),
    )

    equip = player.components[EquipState]
    inventory = player.components[Inventory]
    assert inventory.slots["a"].item_id == "strong_blade"
    assert inventory.slots["b"].item_id == "heavy"
    assert inventory.slots["c"].item_id == "javelin"
    assert inventory.slots["c"].stack_count == 5
    assert equip.wielded_slot == "a"
    assert equip.worn_slot == "b"
    loot_pool = {weapon.id for weapon in eligible_weapons(registry, 9)}
    assert "late_only" not in loot_pool
    assert inventory.slots["a"].item_id == "strong_blade"


def test_level_warped_skips_past_runs(tmp_path: Path) -> None:
    store = PastRunsStore(tmp_path / "past_runs.json")
    state = GameOverState()
    ending = GameOverEnding(kind="digested", detail="wolf")

    state.open(
        player_name="Alex",
        ending=ending,
        monsters_defeated=1,
        runes_collected=2,
        depth=10,
        past_runs_store=store,
        level_warped=True,
    )

    assert store.load_runs() == []


def test_is_ctrl_g() -> None:
    assert is_ctrl_g(_key(KeySym.G, mod=Modifier.CTRL))
    assert not is_ctrl_g(_key(KeySym.G))


def test_ctrl_g_enters_name_then_depth(tmp_path: Path) -> None:
    from tests.ui_test_helpers import make_console

    console = make_console()
    app = _depth_jump_app(tmp_path)
    assert app.phase is AppPhase.MENU
    app.handle_event(_key(KeySym.G, mod=Modifier.CTRL))
    assert app.phase is AppPhase.NAME_ENTRY
    assert app.pending_depth_jump is True

    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.DEPTH_ENTRY

    app.handle_event(_key(KeySym.N1))
    app.handle_event(_key(KeySym.N0))
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.PLAY
    assert app.engine is not None
    assert app.engine.floor_depth == 10
    assert app.engine.level_warped is True


def test_depth_one_routes_to_normal_new_game(tmp_path: Path) -> None:
    from tests.ui_test_helpers import make_console

    console = make_console()
    app = _depth_jump_app(tmp_path)
    app.handle_event(_key(KeySym.G, mod=Modifier.CTRL))
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.DEPTH_ENTRY

    app.handle_event(_key(KeySym.N1))
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.PLAY
    assert app.engine is not None
    assert app.engine.floor_depth == 1
    assert app.engine.level_warped is False