from __future__ import annotations

import string
from collections import deque
from enum import Enum, auto
from typing import Final, Self

import attrs
import tcod.ecs.callbacks
from tcod.ecs import Entity

# Tag sentinels for tcod-ecs queries.
Player: Final = "Player"
Stunned: Final = "Stunned"
BlocksMovement: Final = "BlocksMovement"
VoreCapable: Final = "VoreCapable"
Engulfed: Final = "Engulfed"
VoreMercy: Final = "VoreMercy"


class ItemCategory(Enum):
    WEAPON = auto()
    ARMOR = auto()
    POTION = auto()
    WAND = auto()
    THROWABLE = auto()


def empty_inventory_slots() -> dict[str, InventoryItemInstance | None]:
    return {letter: None for letter in string.ascii_lowercase}


@attrs.define
class InventoryItemInstance:
    item_id: str
    category: ItemCategory
    durability: int | None = None
    charges: int | None = None
    stack_count: int = 1


@attrs.define(frozen=True)
class Position:
    x: int
    y: int

    def __add__(self, direction: tuple[int, int]) -> Self:
        dx, dy = direction
        return self.__class__(self.x + dx, self.y + dy)


@tcod.ecs.callbacks.register_component_changed(component=Position)
def on_position_changed(entity: Entity, old: Position | None, new: Position | None) -> None:
    """Mirror position components as tags for fast spatial queries."""
    if old == new:
        return
    if old is not None:
        entity.tags.discard(old)
    if new is not None:
        entity.tags.add(new)


@attrs.define(frozen=True)
class Renderable:
    ch: int = ord("?")
    fg: tuple[int, int, int] = (255, 255, 255)


@attrs.define
class Fighter:
    hp: int
    max_hp: int
    accuracy: float
    evade: float
    ac: int
    min_damage: int
    max_damage: int
    ranged_accuracy: float | None = None
    ranged_min_damage: int | None = None
    ranged_max_damage: int | None = None

    def effective_ranged_accuracy(self) -> float:
        return self.accuracy if self.ranged_accuracy is None else self.ranged_accuracy

    def effective_ranged_min_damage(self) -> int:
        return self.min_damage if self.ranged_min_damage is None else self.ranged_min_damage

    def effective_ranged_max_damage(self) -> int:
        return self.max_damage if self.ranged_max_damage is None else self.ranged_max_damage


@attrs.define(frozen=True)
class Abilities:
    """Parsed ability modifiers from entity definition."""

    parsed: tuple[object, ...]


@attrs.define
class AbilityState:
    """Mutable per-instance ability state."""

    summon_consumed: bool = False
    erratic_index: int = 0
    plan_step_index: int = 0


@attrs.define
class AI:
    """Chase-AI placeholder; behavior lives in systems/ai.py."""

    pass


@attrs.define
class AIState:
    """Per-NPC AI memory and exploration goals."""

    last_known_primary: Position | None = None
    last_known_neutral: Position | None = None
    last_known_evil: Position | None = None
    last_known_player: Position | None = None
    explore_goal: Position | None = None
    chase_momentum_direction: tuple[int, int] | None = None
    chase_momentum_turns_left: int = 0
    chase_frustration: int = 0
    chase_frustration_limit: int = 0
    explore_frustration: int = 0
    explore_frustration_limit: int = 0
    door_spite_turns_left: int = 0
    # Turns without LOS while holding last-known; trail goes cold at limit.
    memory_blind_turns: int = 0
    memory_blind_limit: int = 0
    explore_force_farthest_on_repick: bool = False
    # Fixed 0/1 stagger for distant half-turn cadence (D2); set at spawn, saved.
    ai_turn_salt: int = 0
    # One-shot spawn freeze (anti-swarm): remaining world-phase skips; once cleared, never again.
    spawn_freeze_remaining: int = 0
    spawn_freeze_consumed: bool = False
    # Temporary "Come here!" order (add-come-here); AI behavior in PR2.
    come_here: bool = False
    explore_recent_positions: deque[Position] = attrs.field(factory=lambda: deque(maxlen=4))
    explore_recent_goal_distances: deque[int] = attrs.field(factory=lambda: deque(maxlen=4))
    # Ephemeral per-episode BFS cache (not persisted in saves).
    explore_goal_distance_map: dict[Position, int] | None = attrs.field(
        default=None,
        repr=False,
        eq=False,
    )
    # Ephemeral BFS cache for last-known memory pursuit (not persisted).
    memory_pursuit_distance_map: dict[Position, int] | None = attrs.field(
        default=None,
        repr=False,
        eq=False,
    )
    memory_pursuit_map_target: Position | None = attrs.field(
        default=None,
        repr=False,
        eq=False,
    )
    # Ephemeral: last player_turn_count when memory sanitize BFS ran (-1 = never).
    memory_sanitize_at_turn: int = attrs.field(default=-1, repr=False, eq=False)


@attrs.define(frozen=True)
class Item:
    item_id: str
    category: ItemCategory
    durability: int | None = None
    charges: int | None = None
    stack_count: int = 1


@attrs.define
class Inventory:
    slots: dict[str, InventoryItemInstance | None] = attrs.field(factory=empty_inventory_slots)


@attrs.define
class EquipState:
    wielded_slot: str | None = None
    worn_slot: str | None = None


@attrs.define(frozen=True)
class DisplayName:
    """Species or type label (e.g. wolf, knight). Used when no ProperName is set."""

    name: str


@attrs.define(frozen=True)
class SpeciesId:
    """Data-file entity id for narratives and digestion lookup."""

    id: str


@attrs.define(frozen=True)
class NpcPrefix:
    """Dynamic name/stat modifier (e.g. Elite) — not a separate species id."""

    prefix_id: str
    display_prefix: str


class MobilityType(Enum):
    """How an entity traverses map tiles."""

    GROUND = auto()
    FLY = auto()
    AQUATIC = auto()
    STATIONARY = auto()


@attrs.define(frozen=True)
class Mobility:
    kind: MobilityType


class Alignment(Enum):
    GOOD = auto()
    EVIL = auto()
    NEUTRAL = auto()


@attrs.define(frozen=True)
class NPCAlignment:
    alignment: Alignment


@attrs.define(frozen=True)
class ProperName:
    name: str


@attrs.define(frozen=True)
class ExamineDescription:
    text: str


@attrs.define(frozen=True)
class FloorRune:
    rune_id: str


@attrs.define(frozen=True)
class Macguffin:
    macguffin_id: str


@attrs.define
class PlayerProgression:
    """Authoritative permanent rune bonuses for this run."""

    # Completed bonuses (enter combat via effective_fighter)
    bonus_max_hp: int = 0
    bonus_accuracy: float = 0.0
    bonus_min_damage: int = 0
    bonus_max_damage: int = 0
    bonus_ac: int = 0
    bonus_evade: float = 0.0
    # Piece banks: partial progress never affects combat until threshold
    pieces_max_hp: int = 0
    pieces_need_max_hp: int = 1
    pieces_max_hp_need_frozen: bool = False
    pieces_accuracy: int = 0
    pieces_need_accuracy: int = 1
    pieces_accuracy_need_frozen: bool = False
    pieces_ac: int = 0
    pieces_need_ac: int = 1
    pieces_ac_need_frozen: bool = False
    pieces_evade: int = 0
    pieces_need_evade: int = 1
    pieces_evade_need_frozen: bool = False
    pieces_min_damage: int = 0
    pieces_need_min_damage: int = 1
    pieces_min_damage_need_frozen: bool = False
    pieces_max_damage: int = 0
    pieces_need_max_damage: int = 1
    pieces_max_damage_need_frozen: bool = False


@attrs.define
class PlayerEffects:
    """Temporary potion buffs and pending delayed teleport (player only)."""

    haste_turns: int = 0
    might_turns: int = 0
    might_accuracy_bonus: float = 0.0
    might_min_damage_bonus: int = 0
    might_max_damage_bonus: int = 0
    digestion_ward_turns: int = 0
    # None = no pending teleport; int = turns remaining until fire (PR3).
    teleport_pending_turns: int | None = None


@attrs.define
class ScreenFlashState:
    """One-shot flash: set pending on activation, consumed on the next render."""

    pending: bool = False
    color: tuple[int, int, int] = (40, 80, 40)


@attrs.define(frozen=True)
class VoreNarratives:
    """Extensible narrative type ID list (strings). v1 uses OV/CV/AV; must include OV."""

    types: tuple[str, ...]


@attrs.define
class DigestionStrikes:
    count: int = 0


@attrs.define(frozen=True)
class DigestionStats:
    damage_per_tick: int
    digest_time: int


@attrs.define
class Predator:
    prey: Entity
    narrative_type: str
    failed_struggles: int = 0
    # Completed world phases while this hold is active (engulfed flavor cadence).
    engulfed_flavor_phases: int = 0


@attrs.define
class Dazed:
    """NPC-only timed skip status. ``remaining`` = AI turns still to skip."""

    remaining: int


@attrs.define
class RangedMagazine:
    """Path/Smite ammo for RangeN/SmiteN NPCs. ``current`` in ``[0, maximum]``."""

    current: int
    maximum: int