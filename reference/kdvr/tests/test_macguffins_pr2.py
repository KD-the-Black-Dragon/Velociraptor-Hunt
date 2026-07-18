"""PR2: macguffin spawn, movement passthrough, save codec."""

from __future__ import annotations

import random

import pytest
from tcod.ecs import Registry

from src.components import BlocksMovement, Macguffin, Player, Position
from src.constants import MIN_PAIRWISE_SPREAD_BFS, RUNES_PER_FLOOR, RUNE_SPAWN_MIN_DISTANCE
from src.data.floor_rune_loader import parse_floor_rune_registry
from src.data.macguffin_loader import load_macguffin_registry
from src.data.macguffin_registry import MacguffinDefinition
from src.engine import GameEngine
from src.map_gen import GameMap, Tile
from src.save.codec import assign_entity_ids, encode_entity_record, restore_entities
from src.systems.floor_runes import (
    RunePlacementError,
    count_floor_runes,
    spawn_floor_rune,
)
from src.systems.macguffins import (
    count_floor_macguffins,
    spawn_macguffin_entity,
    spawn_macguffins,
)
from src.systems.movement import can_move_to
from tests.macguffin_test_helpers import (
    fixture_macguffin_definition,
    fixture_macguffin_registry,
    macguffin_placement_arena,
)
from tests.rune_test_helpers import minimal_floor_runes_payload, rune_placement_arena


def test_spawn_macguffins_empty_when_no_eligible_depth() -> None:
    world = Registry()
    game_map = macguffin_placement_arena()
    registry = fixture_macguffin_registry()
    placed = spawn_macguffins(
        world,
        game_map,
        floor_depth=50,
        registry=registry,
    )
    assert placed == []
    assert count_floor_macguffins(world) == 0


def test_spawn_one_macguffin_at_depth_one() -> None:
    world = Registry()
    game_map = rune_placement_arena(width=60, height=10)
    registry = fixture_macguffin_registry()
    placed = spawn_macguffins(
        world,
        game_map,
        floor_depth=1,
        rng=random.Random(2),
        registry=registry,
        min_distance=5,
        min_pairwise=5,
    )
    assert len(placed) == 1
    assert placed[0].components[Macguffin].macguffin_id == "early_relic"


def test_spawn_two_macguffins_at_shared_depth() -> None:
    """Fixture mid+late both eligible at depth 7."""
    world = Registry()
    game_map = macguffin_placement_arena(width=160, height=12)
    registry = fixture_macguffin_registry()
    placed = spawn_macguffins(
        world,
        game_map,
        floor_depth=7,
        rng=random.Random(11),
        registry=registry,
    )
    assert len(placed) == 2
    ids = {entity.components[Macguffin].macguffin_id for entity in placed}
    assert ids == {"mid_relic", "late_relic"}
    positions = {(e.components[Position].x, e.components[Position].y) for e in placed}
    assert len(positions) == 2


def test_spawn_runes_and_macguffins_share_map() -> None:
    world = Registry()
    game_map = macguffin_placement_arena(width=200, height=12)
    registry = fixture_macguffin_registry()
    rune_registry = parse_floor_rune_registry(
        minimal_floor_runes_payload(
            runes=[
                {
                    "id": f"rune_{index}",
                    "display_name": f"rune {index}",
                    "glyph": "0",
                    "fg": [100, 200, 100],
                    "examine": "test",
                    "weight": 1,
                    "min_depth": 1,
                    "max_depth": 20,
                    "effect": {"type": "max_hp", "amount": 1},
                }
                for index in range(3)
            ]
        )
    )
    runes = spawn_floor_rune(
        world,
        game_map,
        floor_depth=7,
        rng=random.Random(5),
        registry=rune_registry,
        min_distance=RUNE_SPAWN_MIN_DISTANCE,
        min_pairwise=MIN_PAIRWISE_SPREAD_BFS,
        count=RUNES_PER_FLOOR,
    )
    rune_positions = [
        (entity.components[Position].x, entity.components[Position].y) for entity in runes
    ]
    macguffins = spawn_macguffins(
        world,
        game_map,
        floor_depth=7,
        rng=random.Random(5),
        registry=registry,
        placed_positions=rune_positions,
    )
    assert len(runes) == RUNES_PER_FLOOR
    assert len(macguffins) == 2
    all_positions = rune_positions + [
        (entity.components[Position].x, entity.components[Position].y)
        for entity in macguffins
    ]
    assert len(set(all_positions)) == len(runes) + len(macguffins)


def test_macguffin_positions_distinct_from_runes() -> None:
    world = Registry()
    game_map = macguffin_placement_arena(width=180, height=12)
    registry = fixture_macguffin_registry()
    rune_registry = parse_floor_rune_registry(minimal_floor_runes_payload())
    runes = spawn_floor_rune(
        world,
        game_map,
        floor_depth=5,
        rng=random.Random(0),
        registry=rune_registry,
        min_distance=10,
        min_pairwise=10,
        count=1,
    )
    rune_pos = (runes[0].components[Position].x, runes[0].components[Position].y)
    macguffins = spawn_macguffins(
        world,
        game_map,
        floor_depth=5,
        rng=random.Random(0),
        registry=registry,
        placed_positions=[rune_pos],
        min_distance=10,
        min_pairwise=10,
    )
    assert macguffins
    for entity in macguffins:
        pos = entity.components[Position]
        assert (pos.x, pos.y) != rune_pos


def test_macguffin_has_blocks_movement_tag() -> None:
    world = Registry()
    definition = fixture_macguffin_definition(macguffin_id="blocks_test")
    entity = spawn_macguffin_entity(world, definition, 5, 5)
    assert BlocksMovement in entity.tags
    assert entity.components[Macguffin].macguffin_id == "blocks_test"


def test_player_can_step_onto_macguffin_npc_cannot() -> None:
    from src.systems.ai import spawn_test_npc
    from src.components import Alignment

    world = Registry()
    game_map = rune_placement_arena(width=45, height=10)
    definition = fixture_macguffin_definition()
    macguffin = spawn_macguffin_entity(world, definition, 20, 5)
    mac_pos = macguffin.components[Position]

    player = world[object()]
    player.tags.add(Player)
    player.tags.add(BlocksMovement)
    player.components[Position] = Position(mac_pos.x - 1, mac_pos.y)

    wolf = spawn_test_npc(
        world,
        x=mac_pos.x - 2,
        y=mac_pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )

    assert can_move_to(world, game_map, player, player.components[Position], (1, 0))
    assert not can_move_to(world, game_map, wolf, wolf.components[Position], (1, 0))


def test_macguffin_codec_round_trip() -> None:
    world = Registry()
    definition = MacguffinDefinition(
        id="test_macguffin",
        display_name="The Test Macguffin",
        glyph="!",
        fg=(200, 200, 200),
        examine="Codec test.",
        min_depth=1,
        max_depth=5,
        score=10,
    )
    entity = spawn_macguffin_entity(world, definition, 3, 4)
    id_map = assign_entity_ids([entity])
    record = encode_entity_record(entity, id_map[entity], id_map)

    restored_world = Registry()
    restore_entities(restored_world, [record])
    restored = restored_world[id_map[entity]]
    assert restored.components[Macguffin].macguffin_id == "test_macguffin"
    assert restored.components[Position] == Position(3, 4)


def test_new_game_spawns_macguffins_matching_eligible_count() -> None:
    """Integration smoke: floor-1 macguffin count matches live eligibility (not a fixed 1)."""
    engine = GameEngine()
    engine.new_game(seed=42)
    eligible = len(load_macguffin_registry().eligible_at_depth(1))
    assert count_floor_macguffins(engine.world) == eligible
    assert count_floor_runes(engine.world) == RUNES_PER_FLOOR


def test_descend_spawns_macguffins_matching_eligible_count() -> None:
    from tests.test_dungeon_pr3 import _place_player_on_stairs, _press_descend

    engine = GameEngine()
    engine.new_game(seed=17)
    _place_player_on_stairs(engine)
    _press_descend(engine)
    assert engine.floor_depth == 2
    eligible = len(load_macguffin_registry().eligible_at_depth(2))
    assert count_floor_macguffins(engine.world) == eligible


def test_spawn_macguffin_raises_when_no_tiles() -> None:
    world = Registry()
    game_map = GameMap(8, 8)
    game_map.tiles[:, :] = Tile.WALL
    game_map.tiles[4, 2:6] = Tile.FLOOR
    game_map.enter_xy = (2, 4)
    registry = fixture_macguffin_registry()
    with pytest.raises(RunePlacementError):
        spawn_macguffins(
            world,
            game_map,
            floor_depth=1,
            registry=registry,
            min_distance=20,
            min_pairwise=20,
        )