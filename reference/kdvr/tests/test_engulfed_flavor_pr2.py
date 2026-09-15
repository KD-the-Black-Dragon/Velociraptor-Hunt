"""PR2: engulfed flavor emit cadence, type gate, save counter."""

from __future__ import annotations

import random

from src.components import Alignment, Position, Predator
from src.data.narrative_index import NarrativeIndex
from src.engine import GameEngine
from src.engine_turn import run_world_turn
from src.log_categories import MessageCategory
from src.systems.ai import spawn_test_npc
from src.systems.engulfed_flavor import (
    ENGULFED_FLAVOR_EVERY_N_WORLD_PHASES,
    maybe_emit_engulfed_flavor,
)
from src.systems.vore import engulf_player
from tests.map_test_helpers import ARENA_X, ARENA_Y, carve_floor_rect, isolate_other_ais


def _flavor_index(**pools: tuple[str, ...]) -> NarrativeIndex:
    engulfed: dict[tuple[str, str], tuple[str, ...]] = {}
    for key, lines in pools.items():
        # key like "wolf_OV"
        species, ntype = key.rsplit("_", 1)
        engulfed[(species, ntype)] = lines
    return NarrativeIndex(
        vore_variants={},
        digestion_complete={},
        digestion_player_modal={},
        npc_vore_hit={},
        npc_vore_miss={},
        offscreen_vore={},
        offscreen_digest={},
        engulfed_flavor=engulfed,
    )


def _engulf_setup(engine: GameEngine, *, narrative_type: str = "OV"):
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 1, ARENA_Y)
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
        hp=40,
    )
    engulf_player(
        engine.world,
        player,
        wolf,
        engine.message_log,
        narrative_type=narrative_type,
    )
    return player, wolf


def test_emit_silent_until_third_world_phase(monkeypatch) -> None:
    engine = GameEngine(skip_new_game=True)
    engine.new_game()
    player, wolf = _engulf_setup(engine)
    index = _flavor_index(wolf_OV=("belly squeeze",))
    monkeypatch.setattr(
        "src.systems.engulfed_flavor.get_narrative_index", lambda: index
    )

    for _ in range(2):
        maybe_emit_engulfed_flavor(
            engine.world, player, engine.message_log, random.Random(0)
        )
    assert wolf.components[Predator].engulfed_flavor_phases == 2
    assert not any("belly squeeze" in e.text for e in engine.message_log.entries())

    maybe_emit_engulfed_flavor(
        engine.world, player, engine.message_log, random.Random(0)
    )
    assert wolf.components[Predator].engulfed_flavor_phases == 3
    texts = [e.text for e in engine.message_log.entries()]
    assert any("belly squeeze" in t for t in texts)
    speech = [
        e for e in engine.message_log.entries() if "belly squeeze" in e.text
    ]
    assert speech[0].category is MessageCategory.SPEECH


def test_emit_again_on_sixth_phase(monkeypatch) -> None:
    engine = GameEngine(skip_new_game=True)
    engine.new_game()
    player, wolf = _engulf_setup(engine)
    index = _flavor_index(wolf_OV=("line one",))
    monkeypatch.setattr(
        "src.systems.engulfed_flavor.get_narrative_index", lambda: index
    )
    for _ in range(6):
        maybe_emit_engulfed_flavor(
            engine.world, player, engine.message_log, random.Random(0)
        )
    hits = [e for e in engine.message_log.entries() if "line one" in e.text]
    assert len(hits) == 2
    assert wolf.components[Predator].engulfed_flavor_phases == 6


def test_empty_pool_increments_but_never_logs(monkeypatch) -> None:
    engine = GameEngine(skip_new_game=True)
    engine.new_game()
    player, wolf = _engulf_setup(engine)
    index = _flavor_index()  # no pools
    monkeypatch.setattr(
        "src.systems.engulfed_flavor.get_narrative_index", lambda: index
    )
    before = len(engine.message_log.entries())
    for _ in range(ENGULFED_FLAVOR_EVERY_N_WORLD_PHASES):
        maybe_emit_engulfed_flavor(
            engine.world, player, engine.message_log, random.Random(0)
        )
    assert wolf.components[Predator].engulfed_flavor_phases == 3
    assert len(engine.message_log.entries()) == before


def test_cv_hold_ignores_ov_pool(monkeypatch) -> None:
    engine = GameEngine(skip_new_game=True)
    engine.new_game()
    player, wolf = _engulf_setup(engine, narrative_type="CV")
    index = _flavor_index(wolf_OV=("oral only",))
    monkeypatch.setattr(
        "src.systems.engulfed_flavor.get_narrative_index", lambda: index
    )
    before = len(engine.message_log.entries())
    for _ in range(3):
        maybe_emit_engulfed_flavor(
            engine.world, player, engine.message_log, random.Random(0)
        )
    assert len(engine.message_log.entries()) == before
    assert not any("oral only" in e.text for e in engine.message_log.entries())


def test_placeholder_substitution(monkeypatch) -> None:
    engine = GameEngine(skip_new_game=True)
    engine.new_game()
    player, wolf = _engulf_setup(engine)
    index = _flavor_index(wolf_OV=("{predator} crushes {prey}.",))
    monkeypatch.setattr(
        "src.systems.engulfed_flavor.get_narrative_index", lambda: index
    )
    for _ in range(3):
        maybe_emit_engulfed_flavor(
            engine.world, player, engine.message_log, random.Random(0)
        )
    texts = [e.text for e in engine.message_log.entries()]
    assert any("crushes" in t and t[0].isupper() for t in texts)
    assert not any("{predator}" in t or "{prey}" in t for t in texts)


def test_not_engulfed_is_noop(monkeypatch) -> None:
    engine = GameEngine(skip_new_game=True)
    engine.new_game()
    player = engine.player
    assert player is not None
    index = _flavor_index(wolf_OV=("should not appear",))
    monkeypatch.setattr(
        "src.systems.engulfed_flavor.get_narrative_index", lambda: index
    )
    maybe_emit_engulfed_flavor(
        engine.world, player, engine.message_log, random.Random(0)
    )
    assert not any("should not appear" in e.text for e in engine.message_log.entries())


def test_run_world_turn_hooks_emit(monkeypatch) -> None:
    engine = GameEngine(skip_new_game=True)
    engine.new_game()
    player, wolf = _engulf_setup(engine)
    index = _flavor_index(wolf_OV=("from world turn",))
    monkeypatch.setattr(
        "src.systems.engulfed_flavor.get_narrative_index", lambda: index
    )
    for _ in range(3):
        run_world_turn(engine)
    assert any("from world turn" in e.text for e in engine.message_log.entries())
    assert wolf.components[Predator].engulfed_flavor_phases == 3


def test_reengulf_resets_flavor_phase_counter(monkeypatch) -> None:
    engine = GameEngine(skip_new_game=True)
    engine.new_game()
    player, wolf = _engulf_setup(engine)
    wolf.components[Predator].engulfed_flavor_phases = 2
    # Re-assign Predator as engulf does
    engulf_player(
        engine.world,
        player,
        wolf,
        engine.message_log,
        narrative_type="OV",
    )
    assert wolf.components[Predator].engulfed_flavor_phases == 0
