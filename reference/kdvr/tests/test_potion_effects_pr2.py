"""PR2: potion effect dispatch — heal, mapping, haste, might, antacid."""

from __future__ import annotations

import pytest

from src.components import (
    DigestionStats,
    DigestionStrikes,
    Engulfed,
    Fighter,
    Inventory,
    PlayerEffects,
    Predator,
)
from src.data.item_loader import _parse_potion
from src.data.item_loaders import ItemLoadError
from src.engine import GameEngine
from src.systems.combat import sync_stunned_state
from src.systems.digestion import apply_player_digestion_tick
from src.systems.inventory import (
    effective_fighter,
    make_potion_instance,
    quaff_potion_from_slot,
)
from src.systems.player_effects import apply_digestion_ward

from tests.map_test_helpers import isolate_other_ais


def test_stock_potion_effects_load() -> None:
    from src.systems.inventory import item_registry, reset_item_registry_cache

    reset_item_registry_cache()
    reg = item_registry()
    assert reg.get_potion("potion_of_discovery").effect == "magic_mapping"
    assert reg.get_potion("potion_of_haste").duration_turns == 20
    might = reg.get_potion("potion_of_might")
    assert might.min_damage_bonus == 5
    assert might.max_damage_bonus == 5
    assert might.accuracy_bonus == pytest.approx(0.15)
    assert reg.get_potion("potion_of_antacid").effect == "digestion_ward"


def test_magic_mapping_sets_explored_not_visible() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    engine.game_map.explored[:] = False
    engine.game_map.visible[:] = False
    player.components[Inventory].slots["c"] = make_potion_instance(
        "potion_of_discovery"
    )

    assert quaff_potion_from_slot(
        player, "c", engine.message_log, game_map=engine.game_map
    )
    assert engine.game_map.explored.all()
    assert not engine.game_map.visible.any()
    assert player.components[Inventory].slots["c"] is None


def test_haste_potion_applies_duration() -> None:
    from src.systems.inventory import reset_item_registry_cache

    reset_item_registry_cache()
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    # Slot c — avoid overwriting starter dagger in a / robes in b.
    player.components[Inventory].slots["c"] = make_potion_instance("potion_of_haste")
    assert quaff_potion_from_slot(player, "c", engine.message_log)
    assert player.components[PlayerEffects].haste_turns == 20


def test_might_potion_boosts_effective_fighter() -> None:
    from src.systems.inventory import item_registry, reset_item_registry_cache

    reset_item_registry_cache()
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    pot = item_registry().get_potion("potion_of_might")
    assert pot.min_damage_bonus == 5
    before = effective_fighter(player)
    player.components[Inventory].slots["c"] = make_potion_instance("potion_of_might")
    assert quaff_potion_from_slot(player, "c", engine.message_log)
    pe = player.components[PlayerEffects]
    assert pe.might_turns == 10
    assert pe.might_min_damage_bonus == 5
    assert pe.might_max_damage_bonus == 5
    after = effective_fighter(player)
    assert after.min_damage == before.min_damage + 5
    assert after.max_damage == before.max_damage + 5
    assert after.accuracy == pytest.approx(before.accuracy + 0.15)


def test_antacid_blocks_digestion_damage_and_strikes() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    apply_digestion_ward(player, 20)

    wolf = engine.world[object()]
    wolf.components[DigestionStats] = DigestionStats(damage_per_tick=5, digest_time=3)
    wolf.components[Predator] = Predator(prey=player, narrative_type="OV")
    player.tags.add(Engulfed)
    player.components[Fighter].hp = 0
    sync_stunned_state(player)

    result = apply_player_digestion_tick(player, wolf, engine.message_log)
    assert result.strike_added is False
    assert result.open_modal is False
    assert player.components.get(DigestionStrikes) is None

    player.components[Fighter].hp = 10
    apply_player_digestion_tick(player, wolf, engine.message_log)
    assert player.components[Fighter].hp == 10


def test_heal_still_works() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 5
    player.components[Inventory].slots["c"] = make_potion_instance("healing_potion")
    assert quaff_potion_from_slot(player, "c", engine.message_log)
    assert player.components[Fighter].hp > 5


def test_unsupported_effect_fails_load() -> None:
    with pytest.raises(ItemLoadError, match="unsupported potion effect"):
        _parse_potion(
            {
                "id": "bad",
                "display_name": "bad",
                "glyph": "!",
                "fg": [1, 2, 3],
                "examine": "x",
                "effect": "not_a_real_effect",
                "spawn_weight": 1,
                "spawn_min_depth": 1,
                "spawn_max_depth": 10,
            },
            context="test",
        )
