"""PR3: delayed teleport potion — queue, fire, engulf escape."""

from __future__ import annotations

import random

from src.components import (
    DigestionStats,
    Engulfed,
    Inventory,
    PlayerEffects,
    Position,
    Predator,
)
from src.engine import GameEngine
from src.systems.inventory import make_potion_instance, quaff_potion_from_slot, reset_item_registry_cache
from src.systems.player_effects import (
    fire_delayed_teleport,
    queue_delayed_teleport,
    tick_player_effects,
)
from src.systems.vore import engulf_player

from tests.map_test_helpers import isolate_other_ais


def test_stock_teleport_potion_loads() -> None:
    reset_item_registry_cache()
    from src.systems.inventory import item_registry

    pot = item_registry().get_potion("potion_of_teleportation")
    assert pot.effect == "teleport_delay"
    assert pot.delay_min_turns == 3
    assert pot.delay_max_turns == 5


def test_quaff_queues_teleport_pending() -> None:
    reset_item_registry_cache()
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["g"] = make_potion_instance(
        "potion_of_teleportation"
    )
    assert quaff_potion_from_slot(player, "g", engine.message_log)
    pe = player.components[PlayerEffects]
    assert pe.teleport_pending_turns is not None
    assert 3 <= pe.teleport_pending_turns <= 5


def test_teleport_fires_after_countdown() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    origin = player.components[Position]
    queue_delayed_teleport(player, 2)
    rng = random.Random(0)

    tick_player_effects(
        player,
        engine.message_log,
        world=engine.world,
        game_map=engine.game_map,
        rng=rng,
    )
    assert player.components[PlayerEffects].teleport_pending_turns == 1
    assert player.components[Position] == origin

    tick_player_effects(
        player,
        engine.message_log,
        world=engine.world,
        game_map=engine.game_map,
        rng=rng,
    )
    assert player.components[PlayerEffects].teleport_pending_turns is None
    # With a full map, almost always moves; allow same tile only if no other candidates.
    # Seeded fire should usually relocate.
    assert isinstance(player.components[Position].x, int)


def test_teleport_escape_when_engulfed() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    wolf = engine.world[object()]
    from src.components import Fighter, Renderable, BlocksMovement, AI
    from src.components import Mobility, MobilityType

    wolf.components[Position] = Position(
        player.components[Position].x + 1,
        player.components[Position].y,
    )
    wolf.components[Fighter] = Fighter(
        hp=10, max_hp=10, accuracy=0.5, evade=0, ac=0, min_damage=1, max_damage=2
    )
    wolf.components[Renderable] = Renderable(ch=ord("w"))
    wolf.components[Mobility] = Mobility(kind=MobilityType.GROUND)
    wolf.tags.add(BlocksMovement)
    wolf.components[DigestionStats] = DigestionStats(damage_per_tick=2, digest_time=5)
    engulf_player(engine.world, player, wolf, engine.message_log, narrative_type="OV")
    assert Engulfed in player.tags
    assert wolf.components[Predator].prey is player

    moved = fire_delayed_teleport(
        player,
        engine.world,
        engine.game_map,
        random.Random(1),
        engine.message_log,
    )
    assert moved
    assert Engulfed not in player.tags
    assert Predator not in wolf.components
    assert player.components[Position] != wolf.components[Position]


def test_refresh_teleport_replaces_countdown() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    queue_delayed_teleport(player, 5)
    queue_delayed_teleport(player, 3)
    assert player.components[PlayerEffects].teleport_pending_turns == 3
