"""Soft-drop unknown content after load so removed data does not brick runs."""

from __future__ import annotations

from dataclasses import dataclass, field

from tcod.ecs import Entity, Registry

from src.components import (
    DisplayName,
    EquipState,
    Inventory,
    Item,
    Player,
    Predator,
    SpeciesId,
    NpcPrefix,
)
from src import messages
from src.data.entity_loader import get_entity_registry
from src.data.item_registry import ItemRegistry
from src.message_log import MessageCategory, MessageLog
from src.systems.inventory import item_registry
from src.systems.naming import entity_type_id


@dataclass
class SanitizeReport:
    dropped_item_ids: list[str] = field(default_factory=list)
    dropped_entity_ids: list[str] = field(default_factory=list)
    dropped_prefix_ids: list[str] = field(default_factory=list)

    @property
    def any_dropped(self) -> bool:
        return bool(
            self.dropped_item_ids
            or self.dropped_entity_ids
            or self.dropped_prefix_ids
        )

    def summary_message(self) -> str:
        parts: list[str] = []
        if self.dropped_item_ids:
            uniq = sorted(set(self.dropped_item_ids))
            shown = ", ".join(uniq[:5])
            if len(uniq) > 5:
                shown += ", …"
            parts.append(messages.save_sanitize_detail_items(shown))
        if self.dropped_entity_ids:
            uniq = sorted(set(self.dropped_entity_ids))
            shown = ", ".join(uniq[:5])
            if len(uniq) > 5:
                shown += ", …"
            parts.append(messages.save_sanitize_detail_creatures(shown))
        if self.dropped_prefix_ids:
            uniq = sorted(set(self.dropped_prefix_ids))
            shown = ", ".join(uniq[:5])
            if len(uniq) > 5:
                shown += ", …"
            parts.append(messages.save_sanitize_detail_prefixes(shown))
        detail = (
            "; ".join(parts) if parts else messages.save_sanitize_detail_fallback()
        )
        return messages.save_sanitize_dropped(detail)


def _item_known(item_id: str, category, registry: ItemRegistry) -> bool:
    try:
        registry.display_name_for(item_id, category)
        return True
    except KeyError:
        return False


def _clear_inventory_unknowns(
    entity: Entity,
    registry: ItemRegistry,
    report: SanitizeReport,
) -> None:
    inventory = entity.components.get(Inventory)
    if inventory is None:
        return
    equip = entity.components.get(EquipState)
    for letter, instance in list(inventory.slots.items()):
        if instance is None:
            continue
        if _item_known(instance.item_id, instance.category, registry):
            continue
        report.dropped_item_ids.append(instance.item_id)
        inventory.slots[letter] = None
        if equip is not None:
            if equip.wielded_slot == letter:
                equip.wielded_slot = None
            if equip.worn_slot == letter:
                equip.worn_slot = None


def _despawn_unknown_floor_items(
    world: Registry,
    registry: ItemRegistry,
    report: SanitizeReport,
) -> None:
    for entity in list(world.Q.all_of(components=[Item])):
        if Player in entity.tags:
            continue
        item = entity.components[Item]
        if _item_known(item.item_id, item.category, registry):
            continue
        report.dropped_item_ids.append(item.item_id)
        entity.clear()


def _despawn_unknown_npcs(world: Registry, report: SanitizeReport) -> None:
    reg = get_entity_registry()
    known = set(reg.by_id())
    doomed: list[Entity] = []
    for entity in list(world.Q.all_of(components=[SpeciesId])):
        if Player in entity.tags:
            continue
        species = entity.components[SpeciesId].id
        if species in known:
            continue
        report.dropped_entity_ids.append(species)
        doomed.append(entity)

    doomed_set = set(doomed)
    # Break predator links that pointed at removed prey.
    for entity in list(world.Q.all_of(components=[Predator])):
        predator = entity.components[Predator]
        if predator.prey in doomed_set:
            entity.components.pop(Predator, None)

    for entity in doomed:
        entity.clear()


def _soft_drop_unknown_prefixes(world: Registry, report: SanitizeReport) -> None:
    """Clear unknown NpcPrefix; restore base DisplayName from species when possible."""
    from src.data.npc_prefix_loader import default_npc_prefix_registry

    known = set(default_npc_prefix_registry().by_id())
    reg = get_entity_registry()
    for entity in list(world.Q.all_of(components=[NpcPrefix])):
        if Player in entity.tags:
            continue
        prefix_id = entity.components[NpcPrefix].prefix_id
        if prefix_id in known:
            continue
        report.dropped_prefix_ids.append(prefix_id)
        entity.components.pop(NpcPrefix, None)
        species = entity.components.get(SpeciesId)
        if species is not None:
            try:
                base_name = reg.get(species.id).display_name
            except KeyError:
                continue
            entity.components[DisplayName] = DisplayName(name=base_name)


def sanitize_loaded_world(
    world: Registry,
    *,
    registry: ItemRegistry | None = None,
) -> SanitizeReport:
    """Drop unknown items/entities after snapshot restore. Does not touch the player entity itself."""
    report = SanitizeReport()
    items = registry or item_registry()
    for entity in world.Q.all_of(components=[Inventory]):
        _clear_inventory_unknowns(entity, items, report)
    _despawn_unknown_floor_items(world, items, report)
    _despawn_unknown_npcs(world, report)
    _soft_drop_unknown_prefixes(world, report)
    return report


def apply_sanitize_notice(message_log: MessageLog, report: SanitizeReport) -> None:
    if not report.any_dropped:
        return
    message_log.add(
        report.summary_message(),
        category=MessageCategory.CAUTION,
    )
