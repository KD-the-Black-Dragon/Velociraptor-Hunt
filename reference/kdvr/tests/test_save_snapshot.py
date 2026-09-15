"""PR1: save snapshot round-trip restore."""

from __future__ import annotations

from collections import deque

from src.components import (
    AIState,
    Alignment,
    Dazed,
    DigestionStrikes,
    Engulfed,
    Inventory,
    Player,
    PlayerProgression,
    Position,
    Predator,
    Stunned,
)
from src.constants import VoreContentPreferences
from src.engine import GameEngine
from src.log_categories import MessageCategory
from src.map_gen import Tile
from src.systems.ai import spawn_test_npc
from src.systems.inventory import make_potion_instance

from tests.map_test_helpers import ARENA_X, ARENA_Y, carve_floor_tile, isolate_other_ais


def _round_trip(engine: GameEngine) -> GameEngine:
    snapshot = engine.build_run_snapshot()
    return GameEngine.from_run_snapshot(snapshot)


def test_round_trip_player_position_and_turn_count() -> None:
    engine = GameEngine(player_name="Aria", skip_new_game=False)
    isolate_other_ais(engine)
    engine.player_turn_count = 17
    player_pos = engine.player.components[Position]
    carve_floor_tile(engine, player_pos.x + 2, player_pos.y)
    engine.player.components[Position] = Position(player_pos.x + 2, player_pos.y)

    restored = _round_trip(engine)

    assert restored.player_name == "Aria"
    assert restored.player_turn_count == 17
    assert restored.player is not None
    assert restored.player.components[Position] == Position(player_pos.x + 2, player_pos.y)


def test_round_trip_map_explored() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.game_map.explored[ARENA_Y, ARENA_X] = True
    engine.game_map.explored[ARENA_Y, ARENA_X + 1] = True
    engine.game_map.tiles[ARENA_Y, ARENA_X] = Tile.FLOOR

    restored = _round_trip(engine)

    assert restored.game_map.explored[ARENA_Y, ARENA_X]
    assert restored.game_map.explored[ARENA_Y, ARENA_X + 1]
    assert restored.game_map.tiles[ARENA_Y, ARENA_X] == Tile.FLOOR


def test_round_trip_inventory_and_progression() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    assert engine.player is not None

    inventory = engine.player.components[Inventory]
    inventory.slots["c"] = make_potion_instance("healing_potion")
    progression = engine.player.components[PlayerProgression]
    progression.bonus_max_hp = 4
    progression.bonus_accuracy = 1.5
    progression.bonus_ac = 2

    restored = _round_trip(engine)
    assert restored.player is not None

    restored_inventory = restored.player.components[Inventory]
    potion = restored_inventory.slots["c"]
    assert potion is not None
    assert potion.item_id == "healing_potion"

    restored_progression = restored.player.components[PlayerProgression]
    assert restored_progression.bonus_max_hp == 4
    assert restored_progression.bonus_accuracy == 1.5
    assert restored_progression.bonus_ac == 2


def test_round_trip_npc_ai_state() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    npc = spawn_test_npc(
        engine.world,
        x=ARENA_X + 3,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = npc.components[AIState]
    state.last_known_player = Position(ARENA_X, ARENA_Y)
    state.explore_goal = Position(ARENA_X + 5, ARENA_Y)
    state.chase_frustration = 3
    state.chase_frustration_limit = 9
    state.explore_recent_positions = deque(
        (Position(ARENA_X + 1, ARENA_Y), Position(ARENA_X + 2, ARENA_Y)),
        maxlen=4,
    )
    state.explore_recent_goal_distances = deque((4, 3), maxlen=4)

    restored = _round_trip(engine)
    restored_npc = next(
        entity
        for entity in restored.world.Q.all_of(components=[AIState])
        if entity.components[Position] == Position(ARENA_X + 3, ARENA_Y)
    )
    restored_state = restored_npc.components[AIState]

    assert restored_state.last_known_player == Position(ARENA_X, ARENA_Y)
    assert restored_state.explore_goal == Position(ARENA_X + 5, ARENA_Y)
    assert restored_state.chase_frustration == 3
    assert restored_state.chase_frustration_limit == 9
    assert list(restored_state.explore_recent_positions) == [
        Position(ARENA_X + 1, ARENA_Y),
        Position(ARENA_X + 2, ARENA_Y),
    ]
    assert list(restored_state.explore_recent_goal_distances) == [4, 3]


def test_round_trip_dazed_remaining() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    wolf.components[Dazed] = Dazed(remaining=4)

    restored = _round_trip(engine)
    restored_wolf = next(
        entity
        for entity in restored.world.Q.all_of(components=[Dazed])
        if entity.components[Position] == Position(ARENA_X + 1, ARENA_Y)
    )
    assert restored_wolf.components[Dazed].remaining == 4


def test_round_trip_predator_prey_link() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    assert engine.player is not None

    predator = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    prey = engine.player
    prey.tags.add(Engulfed)
    prey.components[DigestionStrikes] = DigestionStrikes(count=2)
    predator.components[Predator] = Predator(
        prey=prey,
        narrative_type="OV",
        failed_struggles=1,
        engulfed_flavor_phases=5,
    )

    restored = _round_trip(engine)
    assert restored.player is not None
    assert Engulfed in restored.player.tags
    assert restored.player.components[DigestionStrikes].count == 2

    restored_predator = next(
        entity
        for entity in restored.world.Q.all_of(components=[Predator])
        if entity.components[Position] == Position(ARENA_X + 1, ARENA_Y)
    )
    predator_state = restored_predator.components[Predator]
    assert predator_state.prey is restored.player
    assert predator_state.narrative_type == "OV"
    assert predator_state.failed_struggles == 1
    assert predator_state.engulfed_flavor_phases == 5


def test_round_trip_message_log_and_metadata() -> None:
    prefs = VoreContentPreferences(enabled=frozenset({"OV", "AV"}))
    engine = GameEngine(vore_content_prefs=prefs)
    isolate_other_ais(engine)
    engine.message_log.clear()
    engine.message_log.add("Routine line.")
    engine.message_log.add("Danger!", category=MessageCategory.DANGER)
    engine.close_door_pending = True
    engine.floor_depth = 3
    engine.player.tags.add(Stunned)

    restored = _round_trip(engine)

    assert restored.vore_content_prefs.enabled == frozenset({"OV", "AV"})
    assert restored.ui_layout.preset_id == engine.ui_layout.preset_id
    assert restored.close_door_pending is True
    assert restored.floor_depth == 3
    assert restored.message_log.lines() == ["Routine line.", "Danger!"]
    assert restored.player is not None
    assert Stunned in restored.player.tags
    player_pos = restored.player.components[Position]
    assert restored.game_map.visible[player_pos.y, player_pos.x]