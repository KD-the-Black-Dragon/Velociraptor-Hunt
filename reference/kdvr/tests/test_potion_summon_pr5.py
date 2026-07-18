"""PR5: potion of alliance — summon depth-eligible good ally."""

from __future__ import annotations

import random

from src.components import Alignment, Inventory, NPCAlignment, Position, SpeciesId
from src.engine import GameEngine
from src.systems.inventory import (
    make_potion_instance,
    quaff_potion_from_slot,
    reset_item_registry_cache,
)
from src.systems.summon_ally import good_summon_pool, try_summon_ally

from tests.map_test_helpers import isolate_other_ais


def test_stock_alliance_loads() -> None:
    reset_item_registry_cache()
    from src.systems.inventory import item_registry

    pot = item_registry().get_potion("potion_of_alliance")
    assert pot.effect == "summon_ally"


def test_good_pool_includes_knight_at_depth_1() -> None:
    from src.data.entity_loader import load_entity_registry, reset_entity_registry_cache

    reset_entity_registry_cache()
    reg = load_entity_registry()
    pool = good_summon_pool(reg, floor_depth=1)
    ids = {d.id for d in pool}
    assert "knight" in ids
    assert all(d.alignment == Alignment.GOOD for d in pool)
    assert all(d.spawn.weight > 0 for d in pool)


def test_quaff_alliance_spawns_good_ally() -> None:
    reset_item_registry_cache()
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    before = sum(
        1
        for e in engine.world.Q.all_of(components=[NPCAlignment])
        if e.components[NPCAlignment].alignment == Alignment.GOOD
    )
    player.components[Inventory].slots["i"] = make_potion_instance(
        "potion_of_alliance"
    )
    assert quaff_potion_from_slot(
        player,
        "i",
        engine.message_log,
        game_map=engine.game_map,
        world=engine.world,
        floor_depth=engine.floor_depth,
        difficulty_id=engine.difficulty_id,
        rng=engine.rng,
    )
    after = [
        e
        for e in engine.world.Q.all_of(components=[NPCAlignment])
        if e.components[NPCAlignment].alignment == Alignment.GOOD
    ]
    assert len(after) >= before + 1
    # Nearest-ish: at least one good within a few tiles of player
    px, py = player.components[Position].x, player.components[Position].y
    assert any(
        max(
            abs(e.components[Position].x - px),
            abs(e.components[Position].y - py),
        )
        <= 8
        for e in after
        if e is not player
    )


def test_try_summon_places_adjacent_when_free() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    ally = try_summon_ally(
        player,
        engine.world,
        engine.game_map,
        floor_depth=1,
        rng=random.Random(0),
    )
    assert ally is not None
    assert ally.components[NPCAlignment].alignment == Alignment.GOOD
    assert SpeciesId in ally.components
    pp = player.components[Position]
    ap = ally.components[Position]
    assert max(abs(ap.x - pp.x), abs(ap.y - pp.y)) >= 1
