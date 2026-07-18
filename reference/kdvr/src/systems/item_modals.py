from __future__ import annotations

import random
import string
from enum import Enum, auto

import attrs
import tcod.event
from tcod.ecs import Entity, Registry
from tcod.event import KeySym

from src import messages
from src.components import EquipState, Inventory, InventoryItemInstance, Item, ItemCategory, Player, Position
from src.data.item_registry import ItemRegistry
from src.input_handlers import DIRECTION_KEYS, MODAL_ADVANCE_KEYS
from src.map_gen import GameMap
from src.message_log import MessageLog
from src.spawn import spawn_item_entity
from src.systems.inventory import (
    clear_equip_slot,
    item_registry,
    quaff_potion_from_slot,
    slots_for_category,
)
from src.run_stats import RunStats
from src.systems.player_throw import (
    THROW_TARGET_BACK_KEYS,
    any_evil_throw_target_in_los,
    build_throw_target_tiles,
    confirm_player_throw,
    cycle_throw_target_index,
    default_throw_target_index,
    pick_best_throwable_slot,
    slots_for_throwables_with_stack,
    throw_target_position,
)
from src.systems.wand_evoke import (
    build_evoke_targets,
    confirm_wand_evoke,
    cycle_evoke_target_index,
    default_evoke_target_index,
    evil_targets_in_range,
    is_valid_wand_target,
    slots_for_wands_with_charges,
    wand_charges,
)


class InventoryModalMode(Enum):
    NONE = auto()
    INSPECT_LIST = auto()
    INSPECT_DETAIL = auto()
    DROP = auto()
    WIELD = auto()
    WEAR = auto()
    QUAFF = auto()
    EVOKE_PICK = auto()
    EVOKE_TARGET = auto()
    THROW_PICK = auto()
    THROW_TARGET = auto()
    BLINK_TARGET = auto()


@attrs.define
class InventoryModalState:
    mode: InventoryModalMode = InventoryModalMode.NONE
    selected_slot: str | None = None
    evoke_wand_slot: str | None = None
    evoke_targets: list[Entity] = attrs.field(factory=list)
    evoke_target_index: int = 0
    throw_slot: str | None = None
    throw_target_tiles: list[Position] = attrs.field(factory=list)
    throw_target_index: int = 0
    blink_slot: str | None = None
    blink_cursor: Position | None = None

    @property
    def active(self) -> bool:
        return self.mode != InventoryModalMode.NONE

    def reset(self) -> None:
        self.mode = InventoryModalMode.NONE
        self.selected_slot = None
        self.evoke_wand_slot = None
        self.evoke_targets = []
        self.evoke_target_index = 0
        self.throw_slot = None
        self.throw_target_tiles = []
        self.throw_target_index = 0
        self.blink_slot = None
        self.blink_cursor = None


def occupied_slots(inventory: Inventory) -> list[tuple[str, InventoryItemInstance]]:
    rows: list[tuple[str, InventoryItemInstance]] = []
    for letter in string.ascii_lowercase:
        instance = inventory.slots.get(letter)
        if instance is not None:
            rows.append((letter, instance))
    return rows


def _plural_display_name(display_name: str, count: int) -> str:
    if count == 1:
        return display_name
    if display_name.endswith("s"):
        return display_name
    return f"{display_name}s"


def _stack_label(instance: InventoryItemInstance, display_name: str) -> str:
    if (
        instance.category in (ItemCategory.POTION, ItemCategory.THROWABLE)
        and instance.stack_count > 1
    ):
        plural = _plural_display_name(display_name, instance.stack_count)
        return f"{instance.stack_count} {plural}"
    return display_name


def _join_modal_blocks(*blocks: str) -> str:
    """Separate modal sections with a blank line between each block."""
    return "\n\n".join(block for block in blocks if block)


def _equip_suffix(letter: str, equip: EquipState | None) -> str:
    if equip is None:
        return ""
    if letter == equip.wielded_slot:
        return " (wielded)"
    if letter == equip.worn_slot:
        return " (worn)"
    return ""


def _list_row(
    letter: str,
    instance: InventoryItemInstance,
    display: str,
    *,
    equip: EquipState | None = None,
) -> str:
    label = _stack_label(instance, display) + _equip_suffix(letter, equip)
    return f"{letter}) {label}"


def format_item_detail_text(
    instance: InventoryItemInstance,
    registry: ItemRegistry,
    *,
    wielded_slot: str | None = None,
    worn_slot: str | None = None,
    slot_letter: str | None = None,
) -> str:
    """Full gameplay stat reveal for an inventory or floor item."""
    display = registry.display_name_for(instance.item_id, instance.category)
    lines: list[str] = []

    title = display
    if slot_letter == wielded_slot:
        title = f"{display} (wielded)"
    elif slot_letter == worn_slot:
        title = f"{display} (worn)"
    lines.append(title)

    match instance.category:
        case ItemCategory.WEAPON:
            weapon = registry.get_weapon(instance.item_id)
            lines.append(weapon.examine)
            lines.append(f"Damage: {weapon.min_damage}-{weapon.max_damage}")
            lines.append(f"Accuracy bonus: +{weapon.accuracy_bonus:g}")
            if instance.durability is not None:
                lines.append(f"Durability: {instance.durability}/{weapon.durability_max}")
        case ItemCategory.ARMOR:
            armor = registry.get_armor(instance.item_id)
            lines.append(armor.examine)
            lines.append(f"AC bonus: +{armor.ac_bonus}")
            eb = armor.evade_bonus
            if float(eb) == int(eb):
                lines.append(f"Evade bonus: +{int(eb)}")
            else:
                lines.append(f"Evade bonus: +{eb:g}")
            lines.append(f"Digestion AC: +{armor.digestion_ac}")
            if instance.durability is not None:
                lines.append(f"Durability: {instance.durability}/{armor.durability_max}")
        case ItemCategory.POTION:
            potion = registry.get_potion(instance.item_id)
            lines.append(potion.examine)
            if instance.stack_count > 1:
                lines.append(f"Quantity: {instance.stack_count}")
            if potion.effect == "heal":
                lines.append(f"Heals {potion.heal_amount} HP")
            # Other effects: examine text only (no numeric spoilers).
        case ItemCategory.WAND:
            wand = registry.get_wand(instance.item_id)
            lines.append(wand.examine)
            lines.append(f"Effect: {wand.effect}")
            lines.append(f"Damage: {wand.min_damage}-{wand.max_damage}")
            lines.append(f"Accuracy: {wand.accuracy:g}")
            lines.append(f"Range: {wand.range}")
            charges = instance.charges if instance.charges is not None else wand.charges_start
            lines.append(f"Charges: {charges}/{wand.charges_max}")
        case ItemCategory.THROWABLE:
            throwable = registry.get_throwable(instance.item_id)
            lines.append(throwable.examine)
            lines.append(f"Damage: {throwable.min_damage}-{throwable.max_damage}")
            lines.append(f"Accuracy bonus: +{throwable.accuracy_bonus:g}")
            if instance.stack_count > 1:
                lines.append(f"Quantity: {instance.stack_count}")

    # Single newlines: compact stat rows (double spacing looked like 2+ line gaps).
    return "\n".join(lines)


def format_floor_item_detail_text(floor_item: Item, registry: ItemRegistry | None = None) -> str:
    reg = registry or item_registry()
    instance = InventoryItemInstance(
        item_id=floor_item.item_id,
        category=floor_item.category,
        durability=floor_item.durability,
        charges=floor_item.charges,
        stack_count=1,
    )
    return format_item_detail_text(instance, reg)


def _list_modal_text(
    title: str,
    item_lines: list[str],
    *,
    footer: str = "Esc: close",
    available_width: int = 56,
) -> str:
    from src.ui.inventory_list_layout import join_list_modal

    return join_list_modal(title, item_lines, footer, available_width=available_width)


def inspect_list_modal_text(
    inventory: Inventory,
    registry: ItemRegistry | None = None,
    *,
    equip: EquipState | None = None,
    available_width: int = 56,
) -> str:
    reg = registry or item_registry()
    item_lines = []
    for letter, instance in occupied_slots(inventory):
        display = reg.display_name_for(instance.item_id, instance.category)
        item_lines.append(_list_row(letter, instance, display, equip=equip))
    return _list_modal_text("Inventory", item_lines, available_width=available_width)


def drop_list_modal_text(
    inventory: Inventory,
    registry: ItemRegistry | None = None,
    *,
    equip: EquipState | None = None,
    available_width: int = 56,
) -> str:
    reg = registry or item_registry()
    item_lines = []
    for letter, instance in occupied_slots(inventory):
        display = reg.display_name_for(instance.item_id, instance.category)
        item_lines.append(_list_row(letter, instance, display, equip=equip))
    return _list_modal_text(
        "Drop which item?", item_lines, available_width=available_width
    )


def wield_list_modal_text(
    inventory: Inventory,
    registry: ItemRegistry | None = None,
    *,
    equip: EquipState | None = None,
    available_width: int = 56,
) -> str:
    reg = registry or item_registry()
    item_lines = []
    for letter, instance in slots_for_category(inventory, ItemCategory.WEAPON):
        display = reg.display_name_for(instance.item_id, instance.category)
        item_lines.append(_list_row(letter, instance, display, equip=equip))
    return _list_modal_text(
        "Wield which weapon?", item_lines, available_width=available_width
    )


def wear_list_modal_text(
    inventory: Inventory,
    registry: ItemRegistry | None = None,
    *,
    equip: EquipState | None = None,
    available_width: int = 56,
) -> str:
    reg = registry or item_registry()
    item_lines = []
    for letter, instance in slots_for_category(inventory, ItemCategory.ARMOR):
        display = reg.display_name_for(instance.item_id, instance.category)
        item_lines.append(_list_row(letter, instance, display, equip=equip))
    return _list_modal_text(
        "Wear which armor?", item_lines, available_width=available_width
    )


def throw_list_modal_text(
    inventory: Inventory,
    registry: ItemRegistry | None = None,
    *,
    equip: EquipState | None = None,
    available_width: int = 56,
) -> str:
    reg = registry or item_registry()
    item_lines = []
    for letter, instance in slots_for_throwables_with_stack(inventory):
        display = reg.display_name_for(instance.item_id, instance.category)
        item_lines.append(_list_row(letter, instance, display, equip=equip))
    return _list_modal_text(
        "Throw which item?", item_lines, available_width=available_width
    )


def evoke_list_modal_text(
    inventory: Inventory,
    registry: ItemRegistry | None = None,
    *,
    equip: EquipState | None = None,
    available_width: int = 56,
) -> str:
    reg = registry or item_registry()
    item_lines = []
    for letter, instance in slots_for_wands_with_charges(inventory, registry=reg):
        display = reg.display_name_for(instance.item_id, instance.category)
        item_lines.append(_list_row(letter, instance, display, equip=equip))
    return _list_modal_text(
        "Evoke which wand?", item_lines, available_width=available_width
    )


def quaff_list_modal_text(
    inventory: Inventory,
    registry: ItemRegistry | None = None,
    *,
    equip: EquipState | None = None,
    available_width: int = 56,
) -> str:
    reg = registry or item_registry()
    item_lines = []
    for letter, instance in slots_for_category(inventory, ItemCategory.POTION):
        display = reg.display_name_for(instance.item_id, instance.category)
        item_lines.append(_list_row(letter, instance, display, equip=equip))
    return _list_modal_text(
        "Quaff which potion?", item_lines, available_width=available_width
    )


def inventory_list_item_rows(
    state: InventoryModalState,
    inventory: Inventory,
    registry: ItemRegistry | None = None,
    *,
    equip: EquipState | None = None,
) -> tuple[str, list[str]] | None:
    """Title + item label rows for multi-column list modes; None for detail/target/none."""
    reg = registry or item_registry()
    if state.mode == InventoryModalMode.INSPECT_LIST:
        rows = [
            _list_row(
                letter,
                instance,
                reg.display_name_for(instance.item_id, instance.category),
                equip=equip,
            )
            for letter, instance in occupied_slots(inventory)
        ]
        return "Inventory", rows
    if state.mode == InventoryModalMode.DROP:
        rows = [
            _list_row(
                letter,
                instance,
                reg.display_name_for(instance.item_id, instance.category),
                equip=equip,
            )
            for letter, instance in occupied_slots(inventory)
        ]
        return "Drop which item?", rows
    if state.mode == InventoryModalMode.WIELD:
        rows = [
            _list_row(
                letter,
                instance,
                reg.display_name_for(instance.item_id, instance.category),
                equip=equip,
            )
            for letter, instance in slots_for_category(inventory, ItemCategory.WEAPON)
        ]
        return "Wield which weapon?", rows
    if state.mode == InventoryModalMode.WEAR:
        rows = [
            _list_row(
                letter,
                instance,
                reg.display_name_for(instance.item_id, instance.category),
                equip=equip,
            )
            for letter, instance in slots_for_category(inventory, ItemCategory.ARMOR)
        ]
        return "Wear which armor?", rows
    if state.mode == InventoryModalMode.QUAFF:
        rows = [
            _list_row(
                letter,
                instance,
                reg.display_name_for(instance.item_id, instance.category),
                equip=equip,
            )
            for letter, instance in slots_for_category(inventory, ItemCategory.POTION)
        ]
        return "Quaff which potion?", rows
    if state.mode == InventoryModalMode.EVOKE_PICK:
        rows = [
            _list_row(
                letter,
                instance,
                reg.display_name_for(instance.item_id, instance.category),
                equip=equip,
            )
            for letter, instance in slots_for_wands_with_charges(inventory, registry=reg)
        ]
        return "Evoke which wand?", rows
    if state.mode == InventoryModalMode.THROW_PICK:
        rows = [
            _list_row(
                letter,
                instance,
                reg.display_name_for(instance.item_id, instance.category),
                equip=equip,
            )
            for letter, instance in slots_for_throwables_with_stack(inventory)
        ]
        return "Throw which item?", rows
    return None


def inventory_modal_text(
    state: InventoryModalState,
    inventory: Inventory,
    registry: ItemRegistry | None = None,
    *,
    equip: EquipState | None = None,
    player: Entity | None = None,
    available_width: int = 56,
) -> str:
    reg = registry or item_registry()
    if state.mode == InventoryModalMode.EVOKE_TARGET:
        return ""
    if state.mode == InventoryModalMode.THROW_TARGET:
        return ""
    if state.mode == InventoryModalMode.BLINK_TARGET:
        return ""
    if state.mode == InventoryModalMode.INSPECT_DETAIL and state.selected_slot is not None:
        instance = inventory.slots.get(state.selected_slot)
        if instance is None:
            return inspect_list_modal_text(
                inventory, reg, equip=equip, available_width=available_width
            )
        detail = format_item_detail_text(
            instance,
            reg,
            slot_letter=state.selected_slot,
            wielded_slot=equip.wielded_slot if equip else None,
            worn_slot=equip.worn_slot if equip else None,
        )
        return _join_modal_blocks(detail, "Esc: back")
    list_parts = inventory_list_item_rows(state, inventory, reg, equip=equip)
    if list_parts is not None:
        title, item_lines = list_parts
        return _list_modal_text(title, item_lines, available_width=available_width)
    return ""


def begin_inspect(
    player: Entity,
    modal: InventoryModalState,
    message_log: MessageLog,
) -> bool:
    if Player not in player.tags:
        return False
    inventory = player.components[Inventory]
    if not occupied_slots(inventory):
        message_log.add(messages.inventory_empty())
        return False
    modal.mode = InventoryModalMode.INSPECT_LIST
    modal.selected_slot = None
    return True


def begin_drop(
    player: Entity,
    modal: InventoryModalState,
    message_log: MessageLog,
) -> bool:
    if Player not in player.tags:
        return False
    inventory = player.components[Inventory]
    if not occupied_slots(inventory):
        message_log.add(messages.nothing_to_drop())
        return False
    modal.mode = InventoryModalMode.DROP
    modal.selected_slot = None
    return True


def begin_wield(
    player: Entity,
    modal: InventoryModalState,
    message_log: MessageLog,
) -> bool:
    if Player not in player.tags:
        return False
    inventory = player.components[Inventory]
    if not slots_for_category(inventory, ItemCategory.WEAPON):
        message_log.add(messages.no_weapons())
        return False
    modal.mode = InventoryModalMode.WIELD
    modal.selected_slot = None
    return True


def begin_wear(
    player: Entity,
    modal: InventoryModalState,
    message_log: MessageLog,
) -> bool:
    if Player not in player.tags:
        return False
    inventory = player.components[Inventory]
    if not slots_for_category(inventory, ItemCategory.ARMOR):
        message_log.add(messages.no_armor())
        return False
    modal.mode = InventoryModalMode.WEAR
    modal.selected_slot = None
    return True


def begin_quaff(
    player: Entity,
    modal: InventoryModalState,
    message_log: MessageLog,
) -> bool:
    if Player not in player.tags:
        return False
    inventory = player.components[Inventory]
    if not slots_for_category(inventory, ItemCategory.POTION):
        message_log.add(messages.no_potions())
        return False
    modal.mode = InventoryModalMode.QUAFF
    modal.selected_slot = None
    return True


def begin_quick_throw(
    player: Entity,
    modal: InventoryModalState,
    message_log: MessageLog,
    world: Registry,
    *,
    game_map: GameMap | None,
) -> bool:
    if Player not in player.tags:
        return False
    inventory = player.components[Inventory]
    slot = pick_best_throwable_slot(inventory)
    if slot is None:
        message_log.add(messages.nothing_to_throw())
        return False
    return _begin_throw_target(
        player,
        slot,
        modal,
        world,
        message_log,
        game_map=game_map,
    )


def begin_throw_pick(
    player: Entity,
    modal: InventoryModalState,
    message_log: MessageLog,
) -> bool:
    if Player not in player.tags:
        return False
    inventory = player.components[Inventory]
    if not slots_for_throwables_with_stack(inventory):
        message_log.add(messages.nothing_to_throw())
        return False
    modal.mode = InventoryModalMode.THROW_PICK
    modal.selected_slot = None
    modal.throw_slot = None
    modal.throw_target_tiles = []
    modal.throw_target_index = 0
    return True


def begin_evoke(
    player: Entity,
    modal: InventoryModalState,
    message_log: MessageLog,
) -> bool:
    if Player not in player.tags:
        return False
    inventory = player.components[Inventory]
    if not slots_for_wands_with_charges(inventory):
        message_log.add(messages.no_wands())
        return False
    modal.mode = InventoryModalMode.EVOKE_PICK
    modal.selected_slot = None
    modal.evoke_wand_slot = None
    modal.evoke_targets = []
    modal.evoke_target_index = 0
    return True


def drop_item_from_slot(
    world: Registry,
    player: Entity,
    slot: str,
    message_log: MessageLog,
    *,
    registry: ItemRegistry | None = None,
) -> bool:
    if Player not in player.tags:
        return False

    inventory = player.components[Inventory]
    instance = inventory.slots.get(slot)
    if instance is None:
        return False

    reg = registry or item_registry()
    pos = player.components[Position]
    spawn_item_entity(
        world,
        instance.category,
        instance.item_id,
        pos.x,
        pos.y,
        registry=reg,
        durability=instance.durability,
        charges=instance.charges,
    )

    display = reg.display_name_for(instance.item_id, instance.category)
    if instance.category == ItemCategory.POTION and instance.stack_count > 1:
        instance.stack_count -= 1
    else:
        inventory.slots[slot] = None
        equip = player.components.get(EquipState)
        if equip is not None:
            clear_equip_slot(equip, slot)

    message_log.add(messages.item_dropped(display))
    return True


def _wield_from_slot(
    player: Entity,
    slot: str,
    message_log: MessageLog,
    modal: InventoryModalState,
) -> bool:
    inventory = player.components[Inventory]
    instance = inventory.slots.get(slot)
    if instance is None or instance.category != ItemCategory.WEAPON:
        return False

    equip = player.components.setdefault(EquipState, EquipState())
    if equip.wielded_slot == slot:
        message_log.add(messages.already_wielding())
        modal.reset()
        return False

    reg = item_registry()
    display = reg.display_name_for(instance.item_id, instance.category)
    equip.wielded_slot = slot
    message_log.add(messages.wield_item(display))
    modal.reset()
    return True


def _wear_from_slot(
    player: Entity,
    slot: str,
    message_log: MessageLog,
    modal: InventoryModalState,
) -> bool:
    inventory = player.components[Inventory]
    instance = inventory.slots.get(slot)
    if instance is None or instance.category != ItemCategory.ARMOR:
        return False

    equip = player.components.setdefault(EquipState, EquipState())
    if equip.worn_slot == slot:
        message_log.add(messages.already_wearing())
        modal.reset()
        return False

    reg = item_registry()
    display = reg.display_name_for(instance.item_id, instance.category)
    equip.worn_slot = slot
    message_log.add(messages.wear_item(display))
    modal.reset()
    return True


def handle_inventory_modal_letter(
    player: Entity,
    letter: str,
    modal: InventoryModalState,
    message_log: MessageLog,
    world: Registry,
    *,
    game_map: GameMap | None = None,
    floor_depth: int = 1,
    difficulty_id: str | None = None,
    rng: random.Random | None = None,
) -> bool:
    """
    Handle a letter key in an inventory modal.
    Returns True when the player turn should be consumed.
    """
    inventory = player.components[Inventory]

    if modal.mode == InventoryModalMode.INSPECT_LIST:
        instance = inventory.slots.get(letter)
        if instance is None:
            return False
        modal.selected_slot = letter
        modal.mode = InventoryModalMode.INSPECT_DETAIL
        return False

    if modal.mode == InventoryModalMode.DROP:
        if inventory.slots.get(letter) is None:
            return False
        drop_item_from_slot(world, player, letter, message_log)
        if not occupied_slots(inventory):
            modal.reset()
        return False

    if modal.mode == InventoryModalMode.WIELD:
        if inventory.slots.get(letter) is None:
            return False
        return _wield_from_slot(player, letter, message_log, modal)

    if modal.mode == InventoryModalMode.WEAR:
        if inventory.slots.get(letter) is None:
            return False
        return _wear_from_slot(player, letter, message_log, modal)

    if modal.mode == InventoryModalMode.QUAFF:
        if inventory.slots.get(letter) is None:
            return False
        instance = inventory.slots.get(letter)
        if instance is not None and instance.category == ItemCategory.POTION:
            pot = item_registry().get_potion(instance.item_id)
            if pot.effect == "blink":
                return begin_blink_target(
                    player, letter, modal, message_log, game_map=game_map
                )
        if quaff_potion_from_slot(
            player,
            letter,
            message_log,
            game_map=game_map,
            world=world,
            floor_depth=floor_depth,
            difficulty_id=difficulty_id,
            rng=rng,
        ):
            modal.reset()
            return True
        return False

    if modal.mode == InventoryModalMode.EVOKE_PICK:
        instance = inventory.slots.get(letter)
        if instance is None or instance.category != ItemCategory.WAND:
            return False
        reg = item_registry()
        wand = reg.get_wand(instance.item_id)
        if wand_charges(instance, wand) <= 0:
            message_log.add(messages.cant_evoke_that())
            modal.reset()
            return False
        return _begin_evoke_target(
            player,
            letter,
            modal,
            world,
            message_log,
            game_map=game_map,
        )

    if modal.mode == InventoryModalMode.THROW_PICK:
        instance = inventory.slots.get(letter)
        if instance is None or instance.category != ItemCategory.THROWABLE:
            return False
        if instance.stack_count <= 0:
            return False
        return _begin_throw_target(
            player,
            letter,
            modal,
            world,
            message_log,
            game_map=game_map,
        )

    return False


def _begin_evoke_target(
    player: Entity,
    wand_slot: str,
    modal: InventoryModalState,
    world: Registry,
    message_log: MessageLog,
    *,
    game_map: GameMap | None,
) -> bool:
    if game_map is None:
        return False
    reg = item_registry()
    instance = player.components[Inventory].slots.get(wand_slot)
    if instance is None:
        return False
    wand = reg.get_wand(instance.item_id)
    targets = build_evoke_targets(world, game_map, player, wand.range)
    if not evil_targets_in_range(targets, player):
        message_log.add(messages.no_valid_targets_in_range())
        modal.reset()
        return False
    modal.evoke_wand_slot = wand_slot
    modal.evoke_targets = targets
    modal.evoke_target_index = default_evoke_target_index(targets, player)
    modal.mode = InventoryModalMode.EVOKE_TARGET
    return False


def _begin_throw_target(
    player: Entity,
    throwable_slot: str,
    modal: InventoryModalState,
    world: Registry,
    message_log: MessageLog,
    *,
    game_map: GameMap | None,
) -> bool:
    if game_map is None:
        return False
    instance = player.components[Inventory].slots.get(throwable_slot)
    if instance is None or instance.stack_count <= 0:
        return False
    if not any_evil_throw_target_in_los(world, game_map, player):
        message_log.add(messages.no_valid_targets_in_range())
        modal.reset()
        return False
    tiles = build_throw_target_tiles(world, game_map, player)
    if not tiles:
        message_log.add(messages.no_valid_targets_in_range())
        modal.reset()
        return False
    reg = item_registry()
    display_name = reg.display_name_for(instance.item_id, instance.category)
    modal.throw_slot = throwable_slot
    modal.throw_target_tiles = tiles
    modal.throw_target_index = default_throw_target_index(tiles)
    modal.mode = InventoryModalMode.THROW_TARGET
    message_log.add(messages.throw_at_which_target(display_name))
    return False


def handle_throw_target_modal_event(
    event: tcod.event.Event,
    player: Entity,
    modal: InventoryModalState,
    world: Registry,
    game_map: GameMap,
    message_log: MessageLog,
    *,
    rng: random.Random | None = None,
    run_stats: RunStats | None = None,
) -> bool:
    """Handle target-pick input for throwable fire. Returns True to consume a turn."""
    if not isinstance(event, tcod.event.KeyDown):
        return False
    if event.sym == KeySym.ESCAPE:
        modal.reset()
        return False
    if event.sym in DIRECTION_KEYS:
        modal.throw_target_index = cycle_throw_target_index(
            modal.throw_target_index,
            len(modal.throw_target_tiles),
            forward=event.sym not in THROW_TARGET_BACK_KEYS,
        )
        return False
    if event.sym in MODAL_ADVANCE_KEYS:
        throwable_slot = modal.throw_slot
        target_tile = throw_target_position(
            modal.throw_target_tiles,
            modal.throw_target_index,
        )
        if throwable_slot is None or target_tile is None:
            modal.reset()
            return False
        if confirm_player_throw(
            world,
            game_map,
            player,
            throwable_slot,
            target_tile,
            message_log,
            rng=rng,
            run_stats=run_stats,
        ):
            modal.reset()
            return True
        modal.reset()
    return False


def handle_evoke_target_modal_event(
    event: tcod.event.Event,
    player: Entity,
    modal: InventoryModalState,
    world: Registry,
    game_map: GameMap,
    message_log: MessageLog,
    *,
    rng: random.Random | None = None,
    run_stats: RunStats | None = None,
) -> bool:
    """Handle target-pick input for wand evoke. Returns True to consume a turn."""
    if not isinstance(event, tcod.event.KeyDown):
        return False
    if event.sym == KeySym.ESCAPE:
        modal.reset()
        return False
    if event.sym in DIRECTION_KEYS:
        modal.evoke_target_index = cycle_evoke_target_index(
            modal.evoke_target_index,
            len(modal.evoke_targets),
        )
        return False
    if event.sym in MODAL_ADVANCE_KEYS:
        wand_slot = modal.evoke_wand_slot
        if wand_slot is None or not modal.evoke_targets:
            modal.reset()
            return False
        target = modal.evoke_targets[modal.evoke_target_index]
        if not is_valid_wand_target(target, player):
            message_log.add(messages.not_the_best_target())
            modal.reset()
            return False
        if confirm_wand_evoke(
            world,
            game_map,
            player,
            wand_slot,
            target,
            message_log,
            rng=rng,
            run_stats=run_stats,
        ):
            modal.reset()
            return True
        modal.reset()
    return False


def blink_rejection_message(
    player: Entity,
    world: Registry,
    game_map: GameMap,
    x: int,
    y: int,
) -> str | None:
    """
    Return a caution-ready rejection string, or None if the tile is a valid blink.

    Priority: out of sight → not walkable → occupied.
    """
    if not game_map.in_bounds(x, y) or not game_map.visible[y, x]:
        return messages.blink_invalid_out_of_sight()
    from src.systems.movement import can_entity_enter_tile, is_blocked_for_mover

    if not can_entity_enter_tile(game_map, x, y, player):
        return messages.blink_invalid_not_walkable()
    if is_blocked_for_mover(world, x, y, player):
        return messages.blink_invalid_occupied()
    return None


def is_valid_blink_tile(
    player: Entity,
    world: Registry,
    game_map: GameMap,
    x: int,
    y: int,
) -> bool:
    """True when the tile is currently visible, walkable, and unoccupied."""
    return blink_rejection_message(player, world, game_map, x, y) is None


def begin_blink_target(
    player: Entity,
    potion_slot: str,
    modal: InventoryModalState,
    message_log: MessageLog,
    *,
    game_map: GameMap | None,
) -> bool:
    """Enter free-cursor blink targeting; does not consume potion or turn."""
    if game_map is None or Player not in player.tags:
        message_log.add(messages.cant_drink_that())
        return False
    instance = player.components[Inventory].slots.get(potion_slot)
    if instance is None or instance.category != ItemCategory.POTION:
        return False
    pos = player.components[Position]
    modal.blink_slot = potion_slot
    modal.blink_cursor = Position(pos.x, pos.y)
    modal.mode = InventoryModalMode.BLINK_TARGET
    message_log.add(messages.blink_where())
    return False


def _move_blink_cursor(
    cursor: Position,
    direction: tuple[int, int],
    game_map: GameMap,
) -> Position:
    """One-step blink reticle move; stay put if dest is OOB or never explored."""
    dest = cursor + direction
    if not game_map.in_bounds(dest.x, dest.y):
        return cursor
    if not game_map.explored[dest.y, dest.x]:
        return cursor
    return dest


def handle_blink_target_modal_event(
    event: tcod.event.Event,
    player: Entity,
    modal: InventoryModalState,
    world: Registry,
    game_map: GameMap,
    message_log: MessageLog,
) -> bool:
    """Handle map-cursor blink. Returns True when blink succeeds (consume turn)."""
    from src.systems.inventory import consume_one_potion_charge
    from src.events import fire_item_used
    from src.log_categories import MessageCategory

    if not isinstance(event, tcod.event.KeyDown):
        return False
    if event.sym == KeySym.ESCAPE:
        modal.reset()
        return False
    if event.sym in DIRECTION_KEYS:
        if modal.blink_cursor is None:
            return False
        # Do not enter never-seen (black) tiles — reticle would vanish under shroud.
        modal.blink_cursor = _move_blink_cursor(
            modal.blink_cursor,
            DIRECTION_KEYS[event.sym],
            game_map,
        )
        return False
    if event.sym in MODAL_ADVANCE_KEYS:
        cursor = modal.blink_cursor
        slot = modal.blink_slot
        if cursor is None or slot is None:
            modal.reset()
            return False
        reject = blink_rejection_message(
            player, world, game_map, cursor.x, cursor.y
        )
        if reject is not None:
            # Prohibit invalid attempt — no consume, stay in targeting.
            message_log.add(reject, category=MessageCategory.CAUTION)
            return False
        inventory = player.components[Inventory]
        instance = inventory.slots.get(slot)
        if instance is None or instance.category != ItemCategory.POTION:
            modal.reset()
            return False
        reg = item_registry()
        display = reg.display_name_for(instance.item_id, instance.category)
        item_id = instance.item_id
        player.components[Position] = Position(cursor.x, cursor.y)
        consume_one_potion_charge(inventory, slot, instance)
        fire_item_used(player, item_id)
        message_log.add(
            messages.blink_success(display),
            category=MessageCategory.MAGICAL,
        )
        modal.reset()
        return True
    return False


def handle_inventory_modal_escape(modal: InventoryModalState) -> None:
    if modal.mode == InventoryModalMode.INSPECT_DETAIL:
        modal.mode = InventoryModalMode.INSPECT_LIST
        modal.selected_slot = None
        return
    modal.reset()