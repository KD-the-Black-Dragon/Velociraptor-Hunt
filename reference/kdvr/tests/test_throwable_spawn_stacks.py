"""Floor throwables spawn in data-driven packs (not always 1)."""

from __future__ import annotations

import random

from tcod.ecs import Registry

from src.components import Item, ItemCategory, Position
from src.data.item_loader import ItemLoadError, _parse_throwable
from src.spawn import spawn_item_entity
from src.systems.inventory import _instance_from_floor_item, item_registry


def test_throwable_parse_spawn_stack_range() -> None:
    raw = {
        "id": "test_rock",
        "display_name": "test rock",
        "glyph": ".",
        "fg": [1, 2, 3],
        "examine": "x",
        "min_damage": 1,
        "max_damage": 2,
        "accuracy_bonus": 0.0,
        "spawn_weight": 1,
        "spawn_min_depth": 1,
        "spawn_max_depth": 3,
        "spawn_stack_min": 3,
        "spawn_stack_max": 4,
    }
    t = _parse_throwable(raw, context="test")
    assert t.spawn_stack_min == 3
    assert t.spawn_stack_max == 4


def test_throwable_parse_rejects_inverted_stack() -> None:
    raw = {
        "id": "bad",
        "display_name": "bad",
        "glyph": ".",
        "fg": [1, 2, 3],
        "examine": "x",
        "min_damage": 1,
        "max_damage": 2,
        "accuracy_bonus": 0.0,
        "spawn_weight": 1,
        "spawn_min_depth": 1,
        "spawn_max_depth": 3,
        "spawn_stack_min": 5,
        "spawn_stack_max": 2,
    }
    try:
        _parse_throwable(raw, context="test")
    except ItemLoadError as exc:
        assert "spawn_stack" in str(exc)
    else:
        raise AssertionError("expected ItemLoadError")


def test_spawn_item_entity_throwable_stack_in_range() -> None:
    world = Registry()
    rng = random.Random(0)
    stacks: set[int] = set()
    for _ in range(30):
        ent = spawn_item_entity(
            world,
            ItemCategory.THROWABLE,
            "rock",
            1,
            1,
            rng=rng,
        )
        stacks.add(ent.components[Item].stack_count)
    assert stacks <= {3, 4}
    assert 3 in stacks or 4 in stacks
    # fixed count override
    ent = spawn_item_entity(
        world,
        ItemCategory.THROWABLE,
        "rock",
        2,
        2,
        stack_count=4,
        rng=rng,
    )
    assert ent.components[Item].stack_count == 4


def test_pickup_instance_preserves_floor_stack() -> None:
    floor = Item(
        item_id="rock",
        category=ItemCategory.THROWABLE,
        stack_count=4,
    )
    inst = _instance_from_floor_item(floor, item_registry())
    assert inst.stack_count == 4


def test_stock_throwables_have_pack_range() -> None:
    from src.systems.inventory import reset_item_registry_cache

    reset_item_registry_cache()
    reg = item_registry()
    for th in reg.throwables:
        assert th.spawn_stack_min == 3
        assert th.spawn_stack_max == 4
