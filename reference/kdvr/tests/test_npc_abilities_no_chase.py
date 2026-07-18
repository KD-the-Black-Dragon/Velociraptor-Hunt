"""PR2b: NoChase — pursue visible quarry only; no memory or momentum."""

from __future__ import annotations

import random
from unittest.mock import patch

from src.components import AIState, Alignment, Position
from src.data.ability_parser import FixedAbility, parse_ability_token
from src.data.abilities import DOCUMENTED_ABILITIES, filter_known_abilities
from src.data.warnings import LoadWarnings
from src.engine import GameEngine
from src.systems.abilities import has_no_chase
from src.systems.ai.targeting import pick_evil_chase
from src.systems.ai.chase import _update_ai_memory
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    isolate_other_ais,
    spawn_wolf_with_abilities,
)


def test_parse_no_chase_token() -> None:
    assert parse_ability_token("NoChase") == FixedAbility(ability_id="NoChase")
    assert "NoChase" in DOCUMENTED_ABILITIES


def test_filter_known_abilities_keeps_no_chase() -> None:
    kept = filter_known_abilities("wolf", ["NoChase"], LoadWarnings())
    assert kept == ("NoChase",)


def test_has_no_chase_on_spawned_wolf() -> None:
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["NoChase"])
    assert has_no_chase(wolf)


def test_no_chase_skips_last_known_primary_pursuit() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["NoChase"])
    state = wolf.components[AIState]
    memory_tile = Position(ARENA_X + 9, ARENA_Y + 9)
    state.last_known_primary = memory_tile
    with patch(
        "src.systems.ai.targeting._visible_primary_hostiles",
        return_value=[],
    ):
        with patch(
            "src.systems.ai.targeting._visible_neutrals",
            return_value=[],
        ):
            entity, pos_target, blocked = pick_evil_chase(
                wolf,
                engine.world,
                engine.game_map,
                player,
                random.Random(0),
            )
    assert entity is None
    assert blocked is None
    assert pos_target != memory_tile


def test_no_chase_still_chases_visible_primary() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    from tests.map_test_helpers import place_adjacent_wolf

    wolf = place_adjacent_wolf(engine)
    from src.components import Abilities
    from src.data.ability_parser import parse_abilities

    wolf.components[Abilities] = Abilities(parsed=parse_abilities(["NoChase"]))
    isolate_other_ais(engine, keep=(wolf,))
    entity, pos_target, blocked = pick_evil_chase(
        wolf,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
    )
    assert entity is player
    assert pos_target is None


def test_no_chase_clears_memory_when_quarry_not_visible() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X + 6, ARENA_Y, ["NoChase"])
    state = wolf.components[AIState]
    state.last_known_primary = Position(ARENA_X, ARENA_Y)
    state.chase_momentum_turns_left = 3
    with patch(
        "src.systems.ai.chase._visible_primary_hostiles",
        return_value=[],
    ):
        with patch(
            "src.systems.ai.chase._visible_neutrals",
            return_value=[],
        ):
            _update_ai_memory(
                wolf,
                engine.world,
                engine.game_map,
                player,
                random.Random(0),
                player_engulfed=False,
            )
    assert state.last_known_primary is None
    assert state.chase_momentum_turns_left == 0