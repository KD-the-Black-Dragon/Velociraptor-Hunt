"""PR1: PreferVore — 100% vore attempt when otherwise legal."""

from __future__ import annotations

import random
from unittest.mock import patch

from src.components import Abilities, Alignment, Fighter, Position
from src.data.ability_parser import parse_abilities
from src.data.ability_parser import FixedAbility, parse_ability_token
from src.data.abilities import DOCUMENTED_ABILITIES, filter_known_abilities
from src.data.warnings import LoadWarnings
from src.engine import GameEngine
from src.systems.abilities import has_prefer_vore
from src.systems.ai import spawn_test_npc
from src.systems.fov import update_fov
from src.systems.vore import should_attempt_vore, try_resolve_npc_vore, vore_decision_chance
from tests.map_test_helpers import (
    carve_adjacent_line,
    place_adjacent_wolf,
    spawn_wolf_with_abilities,
)


def test_parse_prefer_vore_token() -> None:
    assert parse_ability_token("PreferVore") == FixedAbility(ability_id="PreferVore")
    assert "PreferVore" in DOCUMENTED_ABILITIES


def test_filter_known_abilities_keeps_prefer_vore() -> None:
    kept = filter_known_abilities("wolf", ["PreferVore"], LoadWarnings())
    assert kept == ("PreferVore",)


def test_has_prefer_vore_on_spawned_wolf() -> None:
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(engine.world, 5, 5, ["PreferVore"])
    assert has_prefer_vore(wolf)


def test_prefer_vore_skips_decision_roll_at_partial_hp() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 8
    player.components[Fighter].max_hp = 20
    assert vore_decision_chance(0.4) < 1.0
    wolf = place_adjacent_wolf(engine)
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=0.99):
        assert should_attempt_vore(wolf, player, engine.game_map, rng) is False
    wolf.components[Abilities] = Abilities(parsed=parse_abilities(["PreferVore"]))
    assert has_prefer_vore(wolf)
    with patch.object(rng, "random", return_value=0.99):
        assert should_attempt_vore(wolf, player, engine.game_map, rng) is True


def test_prefer_vore_does_not_bypass_eligibility_guards() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 16
    player.components[Fighter].max_hp = 20
    wolf = spawn_wolf_with_abilities(
        engine.world,
        player.components[Position].x + 1,
        player.components[Position].y,
        ["PreferVore"],
    )
    assert should_attempt_vore(wolf, player, engine.game_map, random.Random(0)) is False


def test_prefer_vore_npc_vore_attempt_when_decision_would_fail() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    wolf_tile, knight_tile = carve_adjacent_line(engine, player_pos, 2)
    wolf = spawn_wolf_with_abilities(
        engine.world,
        wolf_tile.x,
        wolf_tile.y,
        ["PreferVore"],
    )
    knight = spawn_test_npc(
        engine.world,
        x=knight_tile.x,
        y=knight_tile.y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=10,
    )
    knight.components[Fighter].max_hp = 24
    update_fov(engine.game_map, player_pos.x, player_pos.y)
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=0.99):
        with patch("src.systems.vore.resolve_vore_hit", return_value=False):
            assert try_resolve_npc_vore(
                wolf,
                engine.world,
                engine.game_map,
                engine.message_log,
                rng,
            )