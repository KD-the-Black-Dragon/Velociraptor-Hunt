"""PR 1: vore foundation — formulas, content prefs, spawn tags, RNG, F2 debug."""

from __future__ import annotations

import random

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.components import (
    AI,
    Alignment,
    DisplayName,
    ExamineDescription,
    Fighter,
    NPCAlignment,
    VoreCapable,
    VoreNarratives,
)
from src.spawn import WOLF_EXAMINE_DESCRIPTION
from src.constants import (
    DEFAULT_VORE_CONTENT_PREFS,
    VORE_ESCAPE_BASE,
    VORE_ESCAPE_PER_FAIL,
    VORE_HIT_MAX,
    VORE_HIT_MIN,
    VORE_HP_THRESHOLD,
    VORE_STRUGGLE_DAMAGE,
    VoreContentPreferences,
)

from src.engine import GameEngine
from src.systems.vore import (
    enabled_narrative_types,
    get_narrative_phases,
    hp_fraction,
    is_vore_eligible,
    pick_narrative_type,
    vore_decision_chance,
    vore_hit_chance,
)


def _fighter(hp: int, max_hp: int = 30) -> Fighter:
    return Fighter(hp=hp, max_hp=max_hp, accuracy=10.0, evade=0, ac=1, min_damage=4, max_damage=4)


def test_hp_fraction_clamps() -> None:
    assert hp_fraction(_fighter(30)) == 1.0
    assert hp_fraction(_fighter(0)) == 0.0
    assert hp_fraction(_fighter(-5)) == 0.0


def test_is_vore_eligible_at_threshold() -> None:
    assert is_vore_eligible(_fighter(15)) is True
    assert is_vore_eligible(_fighter(16)) is False


def test_vore_decision_chance_boundaries() -> None:
    assert vore_decision_chance(1.0) == 0.0
    assert vore_decision_chance(0.53) == 0.0
    assert vore_decision_chance(VORE_HP_THRESHOLD) == 0.0
    assert vore_decision_chance(0.0) == 1.0
    assert abs(vore_decision_chance(0.47) - 0.06) < 0.001
    assert abs(vore_decision_chance(0.27) - 0.46) < 0.001
    assert abs(vore_decision_chance(0.03) - 0.94) < 0.001


def test_vore_hit_chance_boundaries() -> None:
    assert vore_hit_chance(1.0) == 0.0
    assert vore_hit_chance(0.53) == 0.0
    assert vore_hit_chance(0.0) == VORE_HIT_MAX
    assert abs(vore_hit_chance(VORE_HP_THRESHOLD) - VORE_HIT_MIN) < 0.001
    mid = vore_hit_chance(0.25)
    assert VORE_HIT_MIN < mid < VORE_HIT_MAX


def test_vore_escape_constants_defaults() -> None:
    assert VORE_ESCAPE_BASE == 0.15
    assert VORE_ESCAPE_PER_FAIL == 0.05
    assert VORE_STRUGGLE_DAMAGE == 2


def test_disabled_prefs_respect_enabled_set() -> None:
    prefs = VoreContentPreferences(enabled=frozenset({"AV"}))
    assert prefs.is_enabled("OV") is False
    assert prefs.is_enabled("CV") is False
    assert prefs.is_enabled("AV") is True
    assert enabled_narrative_types(("OV", "CV", "AV"), prefs) == ["AV"]


def test_default_prefs_enable_all_types() -> None:
    types = ("OV", "CV", "AV")
    assert set(enabled_narrative_types(types, DEFAULT_VORE_CONTENT_PREFS)) == set(types)


def test_pick_narrative_type_equal_weight() -> None:
    rng = random.Random(42)
    types = ("OV", "CV", "AV")
    counts = {"OV": 0, "CV": 0, "AV": 0}
    for _ in range(3000):
        picked = pick_narrative_type(types, DEFAULT_VORE_CONTENT_PREFS, rng)
        assert picked is not None
        counts[picked] += 1
    for count in counts.values():
        assert 800 < count < 1200


def test_get_narrative_phases_unknown_species_empty() -> None:
    """Do not pin stock wolf prose; unknown ids stay empty."""
    assert get_narrative_phases("___no_such_species___", "OV", "attempt") == []
    assert get_narrative_phases("___no_such_species___", "OV", "success") == []


def test_spawn_tags_wolf_vore_capable() -> None:
    engine = GameEngine()
    from tests.map_test_helpers import ensure_wolf

    monster = ensure_wolf(engine)
    assert monster.components[DisplayName].name == "wolf"
    assert monster.components[NPCAlignment].alignment == Alignment.EVIL
    assert monster.components[ExamineDescription].text == WOLF_EXAMINE_DESCRIPTION
    assert monster.components[VoreNarratives].types == ("OV", "CV", "AV")


def test_new_game_seeded_rng() -> None:
    a = GameEngine()
    a.new_game(seed=12345)
    b = GameEngine()
    b.new_game(seed=12345)
    a_monsters = sorted(
        (m.components[Fighter].hp for m in a.world.Q.all_of(components=[AI, Fighter])),
    )
    b_monsters = sorted(
        (m.components[Fighter].hp for m in b.world.Q.all_of(components=[AI, Fighter])),
    )
    assert a_monsters == b_monsters


def test_debug_hotkeys_disabled_by_default() -> None:
    engine = GameEngine()
    monsters = list(engine.world.Q.all_of(components=[AI, Fighter]))
    assert monsters
    for monster in monsters:
        assert monster.components[Fighter].hp == monster.components[Fighter].max_hp
    engine.handle_event(
        tcod.event.KeyDown(sym=KeySym.F2, scancode=Scancode.UNKNOWN, mod=Modifier.NONE),
    )
    assert all(m.components[Fighter].hp == m.components[Fighter].max_hp for m in monsters)
    assert not any("Debug:" in line for line in engine.message_log.lines())


def test_f2_debug_weakens_monsters(monkeypatch) -> None:
    monkeypatch.setattr("src.engine_input.DEBUG_GAMEPLAY_HOTKEYS_ENABLED", True)
    engine = GameEngine()
    monsters = list(engine.world.Q.all_of(components=[AI, Fighter]))
    assert monsters
    for monster in monsters:
        fighter = monster.components[Fighter]
        assert fighter.hp == fighter.max_hp
    engine.handle_event(
        tcod.event.KeyDown(sym=KeySym.F2, scancode=Scancode.UNKNOWN, mod=Modifier.NONE),
    )
    assert all(m.components[Fighter].hp == 1 for m in monsters)
    assert "Debug: all monsters weakened." in engine.message_log.lines()[-1]


def test_f2_before_inventory_routing(monkeypatch) -> None:
    """F2 must not be treated as inventory slot 'f' (not in INVENTORY_KEYS)."""
    monkeypatch.setattr("src.engine_input.DEBUG_GAMEPLAY_HOTKEYS_ENABLED", True)
    engine = GameEngine()
    engine.handle_event(
        tcod.event.KeyDown(sym=KeySym.F2, scancode=Scancode.UNKNOWN, mod=Modifier.NONE),
    )
    assert "Debug: all monsters weakened." in engine.message_log.lines()[-1]