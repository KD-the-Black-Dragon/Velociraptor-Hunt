"""PR3: GENERIC prefs-immune fallback when capability ∩ prefs is empty."""

from __future__ import annotations

import random

from tcod.ecs import Registry

from src.components import (
    AI,
    Alignment,
    DisplayName,
    Fighter,
    NPCAlignment,
    Position,
    Predator,
    SpeciesId,
    VoreCapable,
    VoreNarratives,
)
from src.constants import VoreContentPreferences
from src.map_gen import GameMap, Tile
from src.message_log import MessageLog
from src.systems.digestion import (
    complete_npc_digestion,
    player_digestion_modal_phases,
)
from src.systems.vore import (
    format_npc_vore_line,
    get_narrative_phases,
    pick_attempt_narrative_type,
    pick_offscreen_vore_line_for,
    pick_visible_npc_vore_message,
    pick_vore_narrative_variant,
    should_attempt_vore,
)
from src.systems.vore_fallback import (
    GENERIC_DIGESTION_COMPLETE,
    GENERIC_NPC_VORE_HIT,
    GENERIC_OFFSCREEN_DIGEST,
    GENERIC_OFFSCREEN_VORE,
    GENERIC_PLAYER_ATTEMPT,
    GENERIC_PLAYER_DIGESTION_MODAL,
    GENERIC_PLAYER_SUCCESS,
    GENERIC_VORE_TYPE,
)
from tests.spawn_test_helpers import fixture_entity_definition, fixture_entity_registry


def _prefs(*enabled: str) -> VoreContentPreferences:
    return VoreContentPreferences(enabled=frozenset(enabled))


def _open_map() -> GameMap:
    game_map = GameMap(20, 20)
    game_map.tiles[:, :] = Tile.FLOOR
    return game_map


def _cv_only_registry():
    return fixture_entity_registry(
        fixture_entity_definition(
            entity_id="cv_only",
            requires_vore_types=frozenset({"CV"}),
        )
    )


def _make_predator(world: Registry, *, x: int = 5, y: int = 5):
    entity = world.new_entity()
    entity.components[SpeciesId] = SpeciesId(id="cv_only")
    entity.components[VoreNarratives] = VoreNarratives(types=("OV", "CV", "AV"))
    entity.components[DisplayName] = DisplayName(name="python")
    entity.components[Position] = Position(x, y)
    entity.components[AI] = AI()
    entity.components[NPCAlignment] = NPCAlignment(alignment=Alignment.EVIL)
    entity.components[Fighter] = Fighter(
        hp=20, max_hp=20, accuracy=10.0, evade=0, ac=1, min_damage=2, max_damage=4
    )
    entity.tags.add(VoreCapable)
    return entity


def _make_player(world: Registry, *, x: int = 6, y: int = 5):
    from src.components import Player

    player = world.new_entity()
    player.tags.add(Player)
    player.components[Position] = Position(x, y)
    player.components[Fighter] = Fighter(
        hp=0, max_hp=30, accuracy=10.0, evade=0, ac=1, min_damage=2, max_damage=4
    )
    player.components[DisplayName] = DisplayName(name="you")
    return player


def test_pick_attempt_uses_generic_when_pool_empty() -> None:
    world = Registry()
    predator = _make_predator(world)
    registry = _cv_only_registry()
    assert (
        pick_attempt_narrative_type(
            predator, _prefs("OV"), random.Random(0), registry=registry
        )
        == GENERIC_VORE_TYPE
    )


def test_generic_not_in_vore_prefs_v1() -> None:
    from src.constants import VORE_NARRATIVE_TYPES_V1

    assert GENERIC_VORE_TYPE not in VORE_NARRATIVE_TYPES_V1
    assert not _prefs("OV", "CV", "AV").is_enabled(GENERIC_VORE_TYPE)


def test_pick_vore_narrative_variant_generic() -> None:
    world = Registry()
    predator = _make_predator(world)
    attempt, success = pick_vore_narrative_variant(
        predator, GENERIC_VORE_TYPE, random.Random(0)
    )
    assert attempt == list(GENERIC_PLAYER_ATTEMPT)
    assert success == list(GENERIC_PLAYER_SUCCESS)


def test_get_narrative_phases_generic() -> None:
    assert get_narrative_phases("any", GENERIC_VORE_TYPE, "attempt") == list(
        GENERIC_PLAYER_ATTEMPT
    )
    assert get_narrative_phases("any", GENERIC_VORE_TYPE, "success") == list(
        GENERIC_PLAYER_SUCCESS
    )


def test_player_digestion_modal_generic() -> None:
    world = Registry()
    predator = _make_predator(world)
    phases = player_digestion_modal_phases(
        predator, GENERIC_VORE_TYPE, random.Random(0)
    )
    assert len(phases) == len(GENERIC_PLAYER_DIGESTION_MODAL)
    assert "digest" in phases[0].lower()


def test_npc_visible_hit_miss_generic() -> None:
    world = Registry()
    predator = _make_predator(world)
    prey = world.new_entity()
    prey.components[DisplayName] = DisplayName(name="rabbit")
    prey.components[NPCAlignment] = NPCAlignment(alignment=Alignment.GOOD)
    hit = pick_visible_npc_vore_message(
        predator, prey, GENERIC_VORE_TYPE, hit=True, rng=random.Random(0)
    )
    miss = pick_visible_npc_vore_message(
        predator, prey, GENERIC_VORE_TYPE, hit=False, rng=random.Random(0)
    )
    assert hit is not None
    assert miss is not None
    assert "swallow" in hit.lower()
    assert "fail" in miss.lower()
    assert GENERIC_NPC_VORE_HIT == ("{predator} swallows {prey}.",)


def test_offscreen_vore_generic() -> None:
    world = Registry()
    predator = _make_predator(world)
    line = pick_offscreen_vore_line_for(
        predator, GENERIC_VORE_TYPE, random.Random(0)
    )
    assert line in GENERIC_OFFSCREEN_VORE


def test_npc_digest_complete_generic_on_screen() -> None:
    world = Registry()
    game_map = _open_map()
    game_map.visible[:, :] = True
    predator = _make_predator(world, x=5, y=5)
    prey = world.new_entity()
    prey.components[DisplayName] = DisplayName(name="rabbit")
    prey.components[Position] = Position(5, 5)
    prey.components[NPCAlignment] = NPCAlignment(alignment=Alignment.GOOD)
    prey.components[Fighter] = Fighter(
        hp=0, max_hp=5, accuracy=1.0, evade=0, ac=0, min_damage=1, max_damage=1
    )
    predator.components[Predator] = Predator(prey=prey, narrative_type=GENERIC_VORE_TYPE)
    log = MessageLog()
    complete_npc_digestion(
        predator, prey, game_map, log, random.Random(0), alternate_cv_mechanics=True
    )
    lines = log.lines()
    assert lines
    assert "digest" in lines[-1].lower()
    assert GENERIC_DIGESTION_COMPLETE == ("{predator} digests {prey}.",)
    assert GENERIC_OFFSCREEN_DIGEST


def test_should_attempt_still_true_when_pool_empty() -> None:
    """GENERIC makes empty capability∩prefs still eligible to attempt."""
    world = Registry()
    game_map = _open_map()
    predator = _make_predator(world, x=5, y=5)
    player = _make_player(world, x=6, y=5)
    registry = _cv_only_registry()
    # Force registry used by attemptable via species lookup in should_attempt path:
    # should_attempt → _vore_base_eligible no longer checks pool; pick uses registry.
    from unittest.mock import patch

    with patch("src.systems.vore.get_entity_registry", return_value=registry):
        assert should_attempt_vore(
            predator, player, game_map, random.Random(0), prefs=_prefs("OV")
        )
        assert (
            pick_attempt_narrative_type(predator, _prefs("OV"), random.Random(0))
            == GENERIC_VORE_TYPE
        )


def test_format_generic_offscreen_line() -> None:
    world = Registry()
    predator = _make_predator(world)
    prey = world.new_entity()
    prey.components[DisplayName] = DisplayName(name="rabbit")
    line = format_npc_vore_line(GENERIC_OFFSCREEN_VORE[0], predator, prey)
    assert "python" in line.lower() or "rabbit" in line.lower()
