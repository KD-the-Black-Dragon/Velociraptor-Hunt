"""PR2: Wander — mindless drift; no targeting or chase."""

from __future__ import annotations

import random
from unittest.mock import patch

from src.components import AIState, Alignment, Position
from src.data.ability_parser import FixedAbility, parse_ability_token
from src.data.abilities import DOCUMENTED_ABILITIES, filter_known_abilities
from src.data.warnings import LoadWarnings
from src.engine import GameEngine
from src.systems.abilities import has_wander
from src.systems.ai import spawn_test_npc
from src.systems.ai.movement import _resolve_monster_move_direction
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    isolate_other_ais,
    spawn_wolf_with_abilities,
)


def test_parse_wander_token() -> None:
    assert parse_ability_token("Wander") == FixedAbility(ability_id="Wander")
    assert "Wander" in DOCUMENTED_ABILITIES


def test_filter_known_abilities_keeps_wander() -> None:
    kept = filter_known_abilities("rabbit", ["Wander"], LoadWarnings())
    assert kept == ("Wander",)


def test_has_wander_on_spawned_entity() -> None:
    engine = GameEngine()
    rabbit = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["Wander"])
    assert has_wander(rabbit)


def test_resolve_move_wander_skips_evil_chase() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X + 4, ARENA_Y, ["Wander"])
    state = wolf.components[AIState]
    with patch("src.systems.ai.targeting.pick_evil_chase") as mock_chase:
        _resolve_monster_move_direction(
            wolf,
            engine.world,
            engine.game_map,
            player,
            random.Random(0),
            state=state,
            alignment=Alignment.EVIL,
            blocked=frozenset(),
            player_engulfed=False,
            monster_pos=wolf.components[Position],
        )
        mock_chase.assert_not_called()


def test_resolve_move_wander_skips_good_chase() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    knight = spawn_test_npc(
        engine.world,
        x=ARENA_X,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=20,
    )
    from src.components import Abilities
    from src.data.ability_parser import parse_abilities

    knight.components[Abilities] = Abilities(parsed=parse_abilities(["Wander"]))
    state = knight.components[AIState]
    with patch("src.systems.ai.targeting.pick_good_chase") as mock_chase:
        _resolve_monster_move_direction(
            knight,
            engine.world,
            engine.game_map,
            player,
            random.Random(0),
            state=state,
            alignment=Alignment.GOOD,
            blocked=frozenset(),
            player_engulfed=False,
            monster_pos=knight.components[Position],
        )
        mock_chase.assert_not_called()


