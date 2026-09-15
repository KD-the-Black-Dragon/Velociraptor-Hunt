"""PR3: Alternate CV struggle damage, escape daze, NPC CV digest daze."""

from __future__ import annotations

import random
from unittest.mock import patch

from src.components import (
    Alignment,
    Dazed,
    DigestionStats,
    DigestionStrikes,
    Engulfed,
    Fighter,
    Position,
    Predator,
    Stunned,
)
from src.data.depth_scaling_loader import default_depth_scaling_config
from src.engine import GameEngine
from src.systems.ai import spawn_test_npc
from src.systems.digestion import apply_digestion_tick, complete_npc_digestion
from src.systems.fov import update_fov
from src.systems.inventory import effective_fighter
from src.systems.vore import engulf_npc, engulf_player, try_struggle
from tests.map_test_helpers import ARENA_X, ARENA_Y, carve_floor_rect, isolate_other_ais


def _clear_ais(engine: GameEngine) -> None:
    isolate_other_ais(engine)


def _engulf_player(
    engine: GameEngine,
    *,
    narrative_type: str,
) -> tuple[object, object]:
    player = engine.player
    assert player is not None
    _clear_ais(engine)
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 2, ARENA_Y)
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
        hp=40,
    )
    wolf.components[DigestionStats] = DigestionStats(damage_per_tick=3, digest_time=6)
    engulf_player(
        engine.world,
        player,
        wolf,
        engine.message_log,
        narrative_type=narrative_type,
    )
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    return player, wolf


def _force_player_struggle_damage(player: object, amount: int = 6) -> None:
    from src.components import PlayerProgression

    progression = player.components.get(PlayerProgression) or PlayerProgression()
    player.components[PlayerProgression] = progression
    ef = effective_fighter(player)
    # Half of `amount` melee → struggle damage amount//2; set melee to amount*2? 
    # compute_struggle_damage = half melee. Want melee min=max=6 → struggle 3.
    target = amount
    progression.bonus_min_damage += target - ef.min_damage
    progression.bonus_max_damage += target - ef.max_damage


def test_alt_cv_off_cv_struggle_still_damages() -> None:
    engine = GameEngine(alternate_cv_mechanics=False)
    player, wolf = _engulf_player(engine, narrative_type="CV")
    _force_player_struggle_damage(player, 6)
    hp_before = wolf.components[Fighter].hp
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=1.0):
        try_struggle(
            engine.world,
            engine.game_map,
            player,
            (1, 0),
            engine.message_log,
            rng,
            alternate_cv_mechanics=False,
        )
    assert wolf.components[Fighter].hp == hp_before - 3
    assert Engulfed in player.tags


def test_alt_cv_on_cv_struggle_zero_damage_escape_chance_unchanged() -> None:
    engine = GameEngine(alternate_cv_mechanics=True)
    player, wolf = _engulf_player(engine, narrative_type="CV")
    _force_player_struggle_damage(player, 6)
    hp_before = wolf.components[Fighter].hp
    profile = default_depth_scaling_config().profile_for("normal")
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=1.0):
        try_struggle(
            engine.world,
            engine.game_map,
            player,
            (1, 0),
            engine.message_log,
            rng,
            alternate_cv_mechanics=True,
            difficulty_profile=profile,
        )
    assert wolf.components[Fighter].hp == hp_before
    assert Engulfed in player.tags
    assert wolf.components[Predator].failed_struggles == 1


def test_alt_cv_on_ov_struggle_still_damages_no_escape_daze() -> None:
    engine = GameEngine(alternate_cv_mechanics=True)
    player, wolf = _engulf_player(engine, narrative_type="OV")
    _force_player_struggle_damage(player, 6)
    hp_before = wolf.components[Fighter].hp
    profile = default_depth_scaling_config().profile_for("normal")
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=0.0):
        try_struggle(
            engine.world,
            engine.game_map,
            player,
            (1, 0),
            engine.message_log,
            rng,
            alternate_cv_mechanics=True,
            difficulty_profile=profile,
        )
    assert Engulfed not in player.tags
    assert wolf.components.get(Dazed) is None
    # Damage applied before escape (predator still had HP)
    # After escape predator exists; HP should have been reduced then release
    # Wait: damage happens then escape - so HP was reduced
    assert wolf.components[Fighter].hp == hp_before - 3


def test_alt_cv_on_cv_escape_applies_daze() -> None:
    engine = GameEngine(alternate_cv_mechanics=True)
    player, wolf = _engulf_player(engine, narrative_type="CV")
    profile = default_depth_scaling_config().profile_for("normal")
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=0.0):
        try_struggle(
            engine.world,
            engine.game_map,
            player,
            (1, 0),
            engine.message_log,
            rng,
            alternate_cv_mechanics=True,
            difficulty_profile=profile,
        )
    assert Engulfed not in player.tags
    assert wolf.components.get(Dazed) is not None
    assert wolf.components[Dazed].remaining == 5
    texts = [e.text for e in engine.message_log.entries()]
    assert any("appears dazed" in t for t in texts)


def test_alt_cv_on_cv_escape_stacks_daze() -> None:
    engine = GameEngine(alternate_cv_mechanics=True)
    player, wolf = _engulf_player(engine, narrative_type="CV")
    wolf.components[Dazed] = Dazed(remaining=2)
    profile = default_depth_scaling_config().profile_for("normal")
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=0.0):
        try_struggle(
            engine.world,
            engine.game_map,
            player,
            (1, 0),
            engine.message_log,
            rng,
            alternate_cv_mechanics=True,
            difficulty_profile=profile,
        )
    assert wolf.components[Dazed].remaining == 7


def test_alt_cv_on_npc_cv_digest_applies_daze() -> None:
    engine = GameEngine(alternate_cv_mechanics=True)
    _clear_ais(engine)
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 1, ARENA_Y)
    player = engine.player
    assert player is not None
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
        hp=30,
    )
    prey = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
        hp=1,
    )
    prey.components[Fighter].hp = 0
    prey.tags.add(Stunned)
    prey.components[DigestionStrikes] = DigestionStrikes(count=5)
    wolf.components[DigestionStats] = DigestionStats(damage_per_tick=3, digest_time=6)
    engulf_npc(engine.world, prey, wolf, narrative_type="CV")
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    profile = default_depth_scaling_config().profile_for("normal")
    digested = apply_digestion_tick(
        prey,
        wolf,
        engine.game_map,
        engine.message_log,
        random.Random(0),
        alternate_cv_mechanics=True,
        difficulty_profile=profile,
    )
    assert digested is True
    assert wolf.components.get(Predator) is None
    assert wolf.components.get(Dazed) is not None
    assert wolf.components[Dazed].remaining == 5


def test_alt_cv_on_npc_ov_digest_no_daze() -> None:
    engine = GameEngine(alternate_cv_mechanics=True)
    _clear_ais(engine)
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 1, ARENA_Y)
    player = engine.player
    assert player is not None
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
        hp=30,
    )
    prey = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
        hp=1,
    )
    prey.components[Fighter].hp = 0
    prey.tags.add(Stunned)
    prey.components[DigestionStrikes] = DigestionStrikes(count=5)
    wolf.components[DigestionStats] = DigestionStats(damage_per_tick=3, digest_time=6)
    engulf_npc(engine.world, prey, wolf, narrative_type="OV")
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    profile = default_depth_scaling_config().profile_for("normal")
    digested = apply_digestion_tick(
        prey,
        wolf,
        engine.game_map,
        engine.message_log,
        random.Random(0),
        alternate_cv_mechanics=True,
        difficulty_profile=profile,
    )
    assert digested is True
    assert wolf.components.get(Dazed) is None


def test_alt_cv_off_npc_cv_digest_no_daze() -> None:
    engine = GameEngine(alternate_cv_mechanics=False)
    _clear_ais(engine)
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 1, ARENA_Y)
    player = engine.player
    assert player is not None
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
        hp=30,
    )
    prey = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
        hp=1,
    )
    prey.components[Fighter].hp = 0
    prey.tags.add(Stunned)
    prey.components[DigestionStrikes] = DigestionStrikes(count=5)
    wolf.components[DigestionStats] = DigestionStats(damage_per_tick=3, digest_time=6)
    engulf_npc(engine.world, prey, wolf, narrative_type="CV")
    complete_npc_digestion(
        wolf,
        prey,
        engine.game_map,
        engine.message_log,
        random.Random(0),
        alternate_cv_mechanics=False,
    )
    assert wolf.components.get(Dazed) is None
