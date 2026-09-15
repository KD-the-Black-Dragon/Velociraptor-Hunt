"""Per-instance combat buffs when good NPCs follow downstairs."""

from __future__ import annotations

from src.components import Alignment, Fighter
from src.constants import (
    GOOD_FOLLOWER_DESCEND_ACCURACY,
    GOOD_FOLLOWER_DESCEND_HP,
    GOOD_FOLLOWER_DESCEND_MAX_DAMAGE,
    GOOD_FOLLOWER_DESCEND_MAX_HP,
    GOOD_FOLLOWER_DESCEND_MIN_DAMAGE,
    GOOD_FOLLOWER_DESCEND_RANGED_ACCURACY,
    GOOD_FOLLOWER_DESCEND_RANGED_MAX_DAMAGE,
    GOOD_FOLLOWER_DESCEND_RANGED_MIN_DAMAGE,
)
from src.systems.descent import (
    apply_good_follower_descent_buff,
    apply_good_follower_descent_buffs,
)
from src.systems.ai import spawn_test_npc
from tcod.ecs import Registry


def test_apply_buff_melee_only_ranged_fallback() -> None:
    fighter = Fighter(
        hp=10,
        max_hp=10,
        accuracy=1.0,
        evade=0.0,
        ac=0,
        min_damage=5,
        max_damage=5,
    )
    apply_good_follower_descent_buff(fighter)
    assert fighter.max_hp == 10 + GOOD_FOLLOWER_DESCEND_MAX_HP
    assert fighter.hp == 10 + GOOD_FOLLOWER_DESCEND_HP
    assert fighter.min_damage == 5 + GOOD_FOLLOWER_DESCEND_MIN_DAMAGE
    assert fighter.max_damage == 5 + GOOD_FOLLOWER_DESCEND_MAX_DAMAGE
    assert fighter.accuracy == 1.0 + GOOD_FOLLOWER_DESCEND_ACCURACY
    assert fighter.ranged_min_damage == 5 + GOOD_FOLLOWER_DESCEND_RANGED_MIN_DAMAGE
    assert fighter.ranged_max_damage == 5 + GOOD_FOLLOWER_DESCEND_RANGED_MAX_DAMAGE
    assert fighter.ranged_accuracy == 1.0 + GOOD_FOLLOWER_DESCEND_RANGED_ACCURACY
    # Melee and ranged each +1 from pre-buff baseline (not double-counted).
    assert fighter.effective_ranged_min_damage() == 6
    assert fighter.min_damage == 6
    assert fighter.effective_ranged_accuracy() == 1.0 + GOOD_FOLLOWER_DESCEND_RANGED_ACCURACY


def test_apply_buff_explicit_ranged_independent() -> None:
    fighter = Fighter(
        hp=8,
        max_hp=10,
        accuracy=1.2,
        evade=0.0,
        ac=0,
        min_damage=4,
        max_damage=6,
        ranged_min_damage=2,
        ranged_max_damage=3,
        ranged_accuracy=0.9,
    )
    apply_good_follower_descent_buff(fighter)
    assert fighter.min_damage == 5
    assert fighter.max_damage == 7
    assert fighter.ranged_min_damage == 2 + GOOD_FOLLOWER_DESCEND_RANGED_MIN_DAMAGE
    assert fighter.ranged_max_damage == 3 + GOOD_FOLLOWER_DESCEND_RANGED_MAX_DAMAGE
    assert fighter.accuracy == 1.2 + GOOD_FOLLOWER_DESCEND_ACCURACY
    assert fighter.ranged_accuracy == 0.9 + GOOD_FOLLOWER_DESCEND_RANGED_ACCURACY
    assert fighter.hp == min(fighter.max_hp, 8 + GOOD_FOLLOWER_DESCEND_HP)
    assert fighter.max_hp == 10 + GOOD_FOLLOWER_DESCEND_MAX_HP


def test_buff_stacks_on_repeated_apply() -> None:
    fighter = Fighter(
        hp=10,
        max_hp=10,
        accuracy=1.0,
        evade=0.0,
        ac=0,
        min_damage=3,
        max_damage=3,
    )
    apply_good_follower_descent_buff(fighter)
    apply_good_follower_descent_buff(fighter)
    assert fighter.max_hp == 10 + 2 * GOOD_FOLLOWER_DESCEND_MAX_HP
    assert fighter.min_damage == 3 + 2 * GOOD_FOLLOWER_DESCEND_MIN_DAMAGE
    assert fighter.accuracy == 1.0 + 2 * GOOD_FOLLOWER_DESCEND_ACCURACY
    assert fighter.ranged_min_damage == 3 + 2 * GOOD_FOLLOWER_DESCEND_RANGED_MIN_DAMAGE


def test_hp_buff_does_not_exceed_new_max() -> None:
    fighter = Fighter(
        hp=10,
        max_hp=10,
        accuracy=1.0,
        evade=0.0,
        ac=0,
        min_damage=1,
        max_damage=1,
    )
    apply_good_follower_descent_buff(fighter)
    assert fighter.hp == fighter.max_hp == 15


def test_apply_buffs_to_follower_entities() -> None:
    world = Registry()
    ally = spawn_test_npc(
        world,
        x=1,
        y=1,
        species="squire",
        alignment=Alignment.GOOD,
        hp=12,
        min_damage=2,
        max_damage=4,
        accuracy=1.0,
    )
    before = ally.components[Fighter]
    base_max = before.max_hp
    apply_good_follower_descent_buffs([ally])
    after = ally.components[Fighter]
    assert after.max_hp == base_max + GOOD_FOLLOWER_DESCEND_MAX_HP
    assert after.min_damage == 2 + GOOD_FOLLOWER_DESCEND_MIN_DAMAGE
