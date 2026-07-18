"""Per-floor outcome snapshots for balance analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tcod.ecs import Entity


@dataclass
class LoadoutProfile:
    """Median loadout at floor entry (isolation injection, PR6)."""

    weapon_damage_sum: int = 8
    armor_ac: int = 1
    heal_potions: int = 0
    might_potions: int = 0
    haste_potions: int = 0
    teleport_potions: int = 0
    wand_charges: int = 0


@dataclass
class LoadoutAtEntry:
    """Player gear/consumables at floor entry (filled in later PRs)."""

    weapon_damage_sum: int = 0
    weapon_accuracy: int = 0
    armor_ac: int = 0
    heal_potions: int = 0
    might_potions: int = 0
    haste_potions: int = 0
    teleport_potions: int = 0
    wand_charges: int = 0


@dataclass
class FloorOutcomeSnapshot:
    """One floor visit outcome (descend or digest on this floor)."""

    floor: int
    seed: int
    digested: bool
    descended: bool
    rune_quota: int = 3
    runes_this_floor: int = 0
    bail_for_survival: bool = False
    consumable_heal: int = 0
    consumable_might: int = 0
    consumable_haste: int = 0
    consumable_teleport: int = 0
    wand_evokes: int = 0
    weapon_improved: bool = False
    armor_improved: bool = False
    upgrade_weapon_spawned: bool = False
    upgrade_weapon_taken: bool = False
    upgrade_armor_spawned: bool = False
    upgrade_armor_taken: bool = False
    stunned_events: int = 0
    event_score: float = 0.0
    entry_loadout: LoadoutAtEntry = field(default_factory=LoadoutAtEntry)


@dataclass
class FloorVisitTracker:
    """Tracks per-floor counters between entry and exit."""

    floor: int
    seed: int
    entry: LoadoutAtEntry = field(default_factory=LoadoutAtEntry)
    runes_at_start: int = 0
    bail_for_survival: bool = False
    consumable_heal: int = 0
    consumable_might: int = 0
    consumable_haste: int = 0
    consumable_teleport: int = 0
    wand_evokes: int = 0
    upgrade_weapon_spawned: bool = False
    upgrade_weapon_taken: bool = False
    upgrade_armor_spawned: bool = False
    upgrade_armor_taken: bool = False
    stunned_events: int = 0
    _stunned_last_turn: bool = False

    def snapshot(
        self,
        *,
        digested: bool,
        descended: bool,
        runes_collected: int,
        rune_quota: int,
        player: Entity | None = None,
    ) -> FloorOutcomeSnapshot:
        from src.sim.inventory_policy import (
            capture_loadout_at_entry,
            loadout_armor_improved,
            loadout_weapon_improved,
        )

        from src.sim.scoring import event_score as compute_event_score

        runes_this_floor = max(0, runes_collected - self.runes_at_start)
        exit_entry = (
            capture_loadout_at_entry(player) if player is not None else LoadoutAtEntry()
        )
        outcome = FloorOutcomeSnapshot(
            floor=self.floor,
            seed=self.seed,
            digested=digested,
            descended=descended,
            rune_quota=rune_quota,
            runes_this_floor=runes_this_floor,
            bail_for_survival=self.bail_for_survival,
            consumable_heal=self.consumable_heal,
            consumable_might=self.consumable_might,
            consumable_haste=self.consumable_haste,
            consumable_teleport=self.consumable_teleport,
            wand_evokes=self.wand_evokes,
            weapon_improved=loadout_weapon_improved(self.entry, exit_entry),
            armor_improved=loadout_armor_improved(self.entry, exit_entry),
            upgrade_weapon_spawned=self.upgrade_weapon_spawned,
            upgrade_weapon_taken=self.upgrade_weapon_taken,
            upgrade_armor_spawned=self.upgrade_armor_spawned,
            upgrade_armor_taken=self.upgrade_armor_taken,
            stunned_events=self.stunned_events,
            entry_loadout=self.entry,
        )
        outcome.event_score = compute_event_score(outcome)
        return outcome


@dataclass
class FloorTrackingState:
    """Active floor visit; emits snapshots on descend or digest."""

    visit: FloorVisitTracker | None = None

    def begin_floor(
        self,
        *,
        floor: int,
        seed: int,
        runes_collected: int,
        player: Entity | None = None,
    ) -> None:
        from src.sim.inventory_policy import capture_loadout_at_entry

        entry = capture_loadout_at_entry(player) if player is not None else LoadoutAtEntry()
        self.visit = FloorVisitTracker(
            floor=floor,
            seed=seed,
            runes_at_start=runes_collected,
            entry=entry,
        )

    def finish_visit(
        self,
        *,
        digested: bool,
        descended: bool,
        runes_collected: int,
        rune_quota: int,
        player: Entity | None = None,
    ) -> FloorOutcomeSnapshot | None:
        if self.visit is None:
            return None
        snapshot = self.visit.snapshot(
            digested=digested,
            descended=descended,
            runes_collected=runes_collected,
            rune_quota=rune_quota,
            player=player,
        )
        self.visit = None
        return snapshot