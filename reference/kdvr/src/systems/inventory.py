from __future__ import annotations

import string

import attrs
from tcod.ecs import Entity, Registry

from src import messages
from src.debug.session_log import session_log
from src.components import (
    EquipState,
    Fighter,
    Inventory,
    InventoryItemInstance,
    Item,
    ItemCategory,
    Player,
    Position,
)
from src.constants import (
    PLAYER_AC,
    PLAYER_ACCURACY,
    PLAYER_MAX_DAMAGE,
    PLAYER_MIN_DAMAGE,
)
from src.data.item_loader import load_item_registry
from src.data.item_registry import (
    ArmorDefinition,
    ItemRegistry,
    PotionDefinition,
    ThrowableDefinition,
    WandDefinition,
    WeaponDefinition,
)
from src.events import fire_item_used
from src.message_log import MessageCategory, MessageLog
from src.systems.combat import heal

_ITEM_REGISTRY: ItemRegistry | None = None


def item_registry() -> ItemRegistry:
    global _ITEM_REGISTRY
    if _ITEM_REGISTRY is None:
        _ITEM_REGISTRY = load_item_registry()
    return _ITEM_REGISTRY


def reset_item_registry_cache() -> None:
    """Clear cached registry (tests)."""
    global _ITEM_REGISTRY
    _ITEM_REGISTRY = None


def first_empty_slot(inventory: Inventory) -> str | None:
    for letter in string.ascii_lowercase:
        if inventory.slots[letter] is None:
            return letter
    return None


def find_potion_stack_slot(inventory: Inventory, item_id: str) -> str | None:
    for letter in string.ascii_lowercase:
        instance = inventory.slots[letter]
        if (
            instance is not None
            and instance.category == ItemCategory.POTION
            and instance.item_id == item_id
        ):
            return letter
    return None


def find_throwable_stack_slot(inventory: Inventory, item_id: str) -> str | None:
    for letter in string.ascii_lowercase:
        instance = inventory.slots[letter]
        if (
            instance is not None
            and instance.category == ItemCategory.THROWABLE
            and instance.item_id == item_id
        ):
            return letter
    return None


def inventory_has_room_for(
    inventory: Inventory,
    *,
    item_id: str,
    category: ItemCategory,
) -> bool:
    if category == ItemCategory.POTION and find_potion_stack_slot(inventory, item_id) is not None:
        return True
    if (
        category == ItemCategory.THROWABLE
        and find_throwable_stack_slot(inventory, item_id) is not None
    ):
        return True
    return first_empty_slot(inventory) is not None


def _instance_from_floor_item(
    floor_item: Item,
    registry: ItemRegistry,
) -> InventoryItemInstance:
    return InventoryItemInstance(
        item_id=floor_item.item_id,
        category=floor_item.category,
        durability=floor_item.durability,
        charges=floor_item.charges,
        stack_count=max(1, int(floor_item.stack_count)),
    )


def _add_instance_to_inventory(
    inventory: Inventory,
    instance: InventoryItemInstance,
    registry: ItemRegistry,
    message_log: MessageLog,
) -> str | None:
    """
    Place instance into inventory. Returns slot letter used, or None if full.
    """
    if instance.category == ItemCategory.POTION:
        stack_slot = find_potion_stack_slot(inventory, instance.item_id)
        if stack_slot is not None:
            existing = inventory.slots[stack_slot]
            assert existing is not None
            existing.stack_count += instance.stack_count
            display = registry.display_name_for(instance.item_id, instance.category)
            message_log.add(messages.item_pickup_stacked(existing.stack_count, display, stack_slot))
            session_log.log(f"Collected {display}")
            return stack_slot

    if instance.category == ItemCategory.THROWABLE:
        stack_slot = find_throwable_stack_slot(inventory, instance.item_id)
        if stack_slot is not None:
            existing = inventory.slots[stack_slot]
            assert existing is not None
            existing.stack_count += instance.stack_count
            display = registry.display_name_for(instance.item_id, instance.category)
            message_log.add(messages.item_pickup_stacked(existing.stack_count, display, stack_slot))
            session_log.log(f"Collected {display}")
            return stack_slot

    slot = first_empty_slot(inventory)
    if slot is None:
        return None

    inventory.slots[slot] = instance
    display = registry.display_name_for(instance.item_id, instance.category)
    message_log.add(messages.item_pickup(display, slot))
    session_log.log(f"Collected {display}")
    return slot


def floor_items_at(world: Registry, x: int, y: int) -> list[Entity]:
    target = Position(x, y)
    items = list(world.Q.all_of(tags=[target], components=[Item]))
    items.sort(key=id)
    return items


def try_pickup_floor_entity(
    world: Registry,
    player: Entity,
    item_entity: Entity,
    message_log: MessageLog,
    *,
    registry: ItemRegistry | None = None,
) -> bool:
    """Pick up one floor item entity. Returns True on success."""
    if Player not in player.tags:
        return False

    floor_item = item_entity.components.get(Item)
    if floor_item is None:
        return False

    reg = registry or item_registry()
    inventory = player.components[Inventory]
    if not inventory_has_room_for(
        inventory,
        item_id=floor_item.item_id,
        category=floor_item.category,
    ):
        return False

    instance = _instance_from_floor_item(floor_item, reg)
    slot = _add_instance_to_inventory(inventory, instance, reg, message_log)
    if slot is None:
        return False

    item_entity.clear()
    return True


def pickup_all_items_at(
    world: Registry,
    player: Entity,
    x: int,
    y: int,
    message_log: MessageLog,
    *,
    registry: ItemRegistry | None = None,
) -> None:
    """Auto-pickup: take all floor items until inventory is full (one full message)."""
    if Player not in player.tags:
        return

    reg = registry or item_registry()
    inventory = player.components[Inventory]
    reported_full = False

    for item_entity in floor_items_at(world, x, y):
        floor_item = item_entity.components[Item]
        if not inventory_has_room_for(
            inventory,
            item_id=floor_item.item_id,
            category=floor_item.category,
        ):
            if not reported_full:
                message_log.add(messages.inventory_full())
                reported_full = True
            return

        if not try_pickup_floor_entity(
            world,
            player,
            item_entity,
            message_log,
            registry=reg,
        ):
            if not reported_full:
                message_log.add(messages.inventory_full())
                reported_full = True
            return


def pickup_items_at(
    world: Registry,
    player: Entity,
    x: int,
    y: int,
    message_log: MessageLog,
) -> None:
    """Backward-compatible alias for walkover auto-pickup."""
    pickup_all_items_at(world, player, x, y, message_log)


@attrs.define
class GroundPickupModalState:
    """Manual pickup modal when multiple items share a tile."""

    item_entities: list[Entity] = attrs.field(factory=list)

    @property
    def active(self) -> bool:
        return bool(self.item_entities)

    def open(self, entities: list[Entity]) -> None:
        self.item_entities = list(entities)

    def reset(self) -> None:
        self.item_entities = []

    def letter_for_index(self, index: int) -> str:
        return string.ascii_lowercase[index]

    def entity_for_letter(self, letter: str) -> Entity | None:
        for index, entity in enumerate(self.item_entities):
            if self.letter_for_index(index) == letter:
                return entity
        return None

    def remove_entity(self, entity: Entity) -> None:
        self.item_entities = [e for e in self.item_entities if e is not entity]


def begin_manual_pickup(
    world: Registry,
    player: Entity,
    message_log: MessageLog,
    modal: GroundPickupModalState,
    *,
    registry: ItemRegistry | None = None,
) -> bool:
    """
    Start manual pickup at player tile.
    Returns True if a modal was opened (caller should not consume a turn).
    """
    if Player not in player.tags:
        return False

    pos = player.components[Position]
    items = floor_items_at(world, pos.x, pos.y)
    if not items:
        message_log.add(messages.nothing_here_to_pickup())
        return False

    if len(items) == 1:
        reg = registry or item_registry()
        inventory = player.components[Inventory]
        floor_item = items[0].components[Item]
        if not inventory_has_room_for(
            inventory,
            item_id=floor_item.item_id,
            category=floor_item.category,
        ):
            message_log.add(messages.inventory_full())
            return False
        try_pickup_floor_entity(world, player, items[0], message_log, registry=reg)
        return False

    modal.open(items)
    return True


def handle_ground_pickup_modal_letter(
    world: Registry,
    player: Entity,
    letter: str,
    message_log: MessageLog,
    modal: GroundPickupModalState,
    *,
    registry: ItemRegistry | None = None,
) -> None:
    entity = modal.entity_for_letter(letter)
    if entity is None:
        return

    reg = registry or item_registry()
    inventory = player.components[Inventory]
    floor_item = entity.components[Item]
    if not inventory_has_room_for(
        inventory,
        item_id=floor_item.item_id,
        category=floor_item.category,
    ):
        message_log.add(messages.inventory_full())
        modal.reset()
        return

    if try_pickup_floor_entity(world, player, entity, message_log, registry=reg):
        modal.remove_entity(entity)
    if not modal.item_entities:
        modal.reset()


def consume_one_potion_charge(
    inventory: Inventory, slot: str, instance: InventoryItemInstance
) -> None:
    """Decrement stack or clear slot after a successful potion use."""
    instance.stack_count -= 1
    if instance.stack_count <= 0:
        inventory.slots[slot] = None


# Back-compat alias for internal call sites.
_consume_one_potion_charge = consume_one_potion_charge


def quaff_potion_from_slot(
    player: Entity,
    slot: str,
    message_log: MessageLog,
    *,
    registry: ItemRegistry | None = None,
    game_map: object | None = None,
    world: object | None = None,
    floor_depth: int = 1,
    difficulty_id: str | None = None,
    rng: object | None = None,
) -> bool:
    """
    Quaff the potion in a letter slot. Return True when a turn should advance.

    Instant and buff effects consume immediately. Blink opens a targeting modal
    without consuming here (handled by the quaff list path).
    """
    if Player not in player.tags:
        return False

    inventory = player.components[Inventory]
    instance = inventory.slots.get(slot)
    if instance is None:
        message_log.add(messages.slot_empty(slot))
        return False
    if instance.category != ItemCategory.POTION:
        message_log.add(messages.cant_drink_that())
        return False

    reg = registry or item_registry()
    potion = reg.get_potion(instance.item_id)
    display = reg.display_name_for(instance.item_id, instance.category)
    effect = potion.effect

    if effect == "heal":
        healed = heal(player, potion.heal_amount)
        _consume_one_potion_charge(inventory, slot, instance)
        fire_item_used(player, instance.item_id)
        if healed > 0:
            message_log.add(
                messages.potion_heal(display, healed),
                category=MessageCategory.POSITIVE,
            )
        else:
            message_log.add(messages.potion_no_effect(display))
        return True

    if effect == "magic_mapping":
        from src.map_gen import GameMap

        if not isinstance(game_map, GameMap):
            message_log.add(messages.cant_drink_that())
            return False
        game_map.explored[:] = True
        _consume_one_potion_charge(inventory, slot, instance)
        fire_item_used(player, instance.item_id)
        message_log.add(
            messages.potion_magic_mapping(display),
            category=MessageCategory.MAGICAL,
        )
        return True

    if effect == "haste":
        from src.systems.player_effects import apply_haste

        apply_haste(player, potion.duration_turns)
        _consume_one_potion_charge(inventory, slot, instance)
        fire_item_used(player, instance.item_id)
        message_log.add(
            messages.potion_haste(display),
            category=MessageCategory.MAGICAL,
        )
        return True

    if effect == "might":
        from src.systems.player_effects import apply_might

        apply_might(
            player,
            duration_turns=potion.duration_turns,
            accuracy_bonus=potion.accuracy_bonus,
            min_damage_bonus=potion.min_damage_bonus,
            max_damage_bonus=potion.max_damage_bonus,
        )
        _consume_one_potion_charge(inventory, slot, instance)
        fire_item_used(player, instance.item_id)
        message_log.add(
            messages.potion_might(display),
            category=MessageCategory.MAGICAL,
        )
        return True

    if effect == "digestion_ward":
        from src.systems.player_effects import apply_digestion_ward

        apply_digestion_ward(player, potion.duration_turns)
        _consume_one_potion_charge(inventory, slot, instance)
        fire_item_used(player, instance.item_id)
        message_log.add(
            messages.potion_antacid(display),
            category=MessageCategory.MAGICAL,
        )
        return True

    if effect == "teleport_delay":
        import random as _random

        from src.systems.player_effects import queue_delayed_teleport

        delay_min = max(1, potion.delay_min_turns)
        delay_max = max(delay_min, potion.delay_max_turns)
        if rng is not None and hasattr(rng, "randint"):
            delay = rng.randint(delay_min, delay_max)  # type: ignore[union-attr]
        else:
            delay = _random.randint(delay_min, delay_max)
        queue_delayed_teleport(player, delay)
        _consume_one_potion_charge(inventory, slot, instance)
        fire_item_used(player, instance.item_id)
        message_log.add(
            messages.potion_teleport_delay(display),
            category=MessageCategory.MAGICAL,
        )
        return True

    if effect == "summon_ally":
        from tcod.ecs import Registry

        from src.map_gen import GameMap
        from src.systems.summon_ally import try_summon_ally
        from src.systems.naming import entity_log_name_indefinite

        if not isinstance(game_map, GameMap) or not isinstance(world, Registry):
            message_log.add(messages.cant_drink_that())
            return False
        import random as _random

        use_rng = rng if isinstance(rng, _random.Random) else _random.Random()
        summoned = try_summon_ally(
            player,
            world,
            game_map,
            floor_depth=floor_depth,
            difficulty_id=difficulty_id,
            rng=use_rng,
        )
        _consume_one_potion_charge(inventory, slot, instance)
        fire_item_used(player, instance.item_id)
        if summoned is None:
            message_log.add(
                messages.potion_summon_failed(display),
                category=MessageCategory.CAUTION,
            )
        else:
            message_log.add(
                messages.potion_summon_success(
                    display,
                    entity_log_name_indefinite(summoned, sentence_start=True),
                ),
                category=MessageCategory.MAGICAL,
            )
        return True

    message_log.add(messages.cant_drink_that())
    return False


def use_inventory_slot(
    player: Entity,
    slot: str,
    message_log: MessageLog,
    *,
    game_map: object | None = None,
    world: object | None = None,
    floor_depth: int = 1,
    difficulty_id: str | None = None,
    rng: object | None = None,
) -> bool:
    """Backward-compatible alias for tests that quaff by slot directly."""
    return quaff_potion_from_slot(
        player,
        slot,
        message_log,
        game_map=game_map,
        world=world,
        floor_depth=floor_depth,
        difficulty_id=difficulty_id,
        rng=rng,
    )


def make_throwable_instance(
    item_id: str | None = None,
    *,
    stack_count: int = 1,
) -> InventoryItemInstance:
    """Test helper for placing throwables in inventory slots."""
    reg = item_registry()
    resolved_id = item_id or (
        "rock" if "rock" in reg.throwable_by_id() else reg.throwables[0].id
    )
    reg.get_throwable(resolved_id)
    return InventoryItemInstance(
        item_id=resolved_id,
        category=ItemCategory.THROWABLE,
        stack_count=stack_count,
    )


def make_potion_instance(
    item_id: str | None = None,
    *,
    stack_count: int = 1,
) -> InventoryItemInstance:
    """Test helper for placing potions in inventory slots."""
    reg = item_registry()
    resolved_id = item_id or reg.potions[0].id
    reg.get_potion(resolved_id)
    return InventoryItemInstance(
        item_id=resolved_id,
        category=ItemCategory.POTION,
        stack_count=stack_count,
    )


def make_weapon_instance(
    item_id: str | None = None,
    *,
    durability: int | None = None,
) -> InventoryItemInstance:
    """Test helper for placing weapons in inventory slots."""
    reg = item_registry()
    weapon_ids = {weapon.id for weapon in reg.weapons}
    resolved_id = item_id or (
        "dagger" if "dagger" in weapon_ids else reg.weapons[0].id
    )
    weapon = reg.get_weapon(resolved_id)
    return InventoryItemInstance(
        item_id=resolved_id,
        category=ItemCategory.WEAPON,
        durability=durability if durability is not None else weapon.durability_max,
    )


def make_wand_instance(
    item_id: str | None = None,
    *,
    charges: int | None = None,
) -> InventoryItemInstance:
    """Test helper for placing wands in inventory slots."""
    reg = item_registry()
    resolved_id = item_id or reg.wands[0].id
    wand = reg.get_wand(resolved_id)
    return InventoryItemInstance(
        item_id=resolved_id,
        category=ItemCategory.WAND,
        charges=charges if charges is not None else wand.charges_start,
    )


def make_armor_instance(
    item_id: str | None = None,
    *,
    durability: int | None = None,
) -> InventoryItemInstance:
    """Test helper for placing armor in inventory slots."""
    reg = item_registry()
    armor_ids = {piece.id for piece in reg.armor}
    resolved_id = item_id or (
        "leather_armor"
        if "leather_armor" in armor_ids
        else "robes"
        if "robes" in armor_ids
        else reg.armor[0].id
    )
    armor = reg.get_armor(resolved_id)
    return InventoryItemInstance(
        item_id=resolved_id,
        category=ItemCategory.ARMOR,
        durability=durability if durability is not None else armor.durability_max,
    )


STARTER_WEAPON_SLOT = "a"
STARTER_ARMOR_SLOT = "b"
STARTER_THROWABLE_SLOT = "c"
STARTER_ROCK_STACK_COUNT = 5


def apply_starter_loadout(player: Entity) -> None:
    """Place default wielded dagger, worn robes, and starter rocks on a new player."""
    if Player not in player.tags:
        return
    inventory = player.components[Inventory]
    equip = player.components.get(EquipState)
    if equip is None:
        equip = EquipState()
        player.components[EquipState] = equip

    inventory.slots[STARTER_WEAPON_SLOT] = make_weapon_instance("dagger")
    inventory.slots[STARTER_ARMOR_SLOT] = make_armor_instance("robes")
    inventory.slots[STARTER_THROWABLE_SLOT] = make_throwable_instance(
        "rock",
        stack_count=STARTER_ROCK_STACK_COUNT,
    )
    equip.wielded_slot = STARTER_WEAPON_SLOT
    equip.worn_slot = STARTER_ARMOR_SLOT


def slots_for_category(
    inventory: Inventory,
    category: ItemCategory,
) -> list[tuple[str, InventoryItemInstance]]:
    rows: list[tuple[str, InventoryItemInstance]] = []
    for letter in string.ascii_lowercase:
        instance = inventory.slots.get(letter)
        if instance is not None and instance.category == category:
            rows.append((letter, instance))
    return rows


def effective_fighter(player: Entity) -> Fighter:
    """Transient combat stats including gear, rune bonuses, and temporary might."""
    from src.components import PlayerEffects, PlayerProgression

    base = player.components[Fighter]
    inventory = player.components[Inventory]
    equip = player.components.get(EquipState)
    prog = player.components.get(PlayerProgression) or PlayerProgression()
    effects = player.components.get(PlayerEffects)
    reg = item_registry()

    min_damage = PLAYER_MIN_DAMAGE
    max_damage = PLAYER_MAX_DAMAGE
    accuracy = PLAYER_ACCURACY
    ac = PLAYER_AC

    if equip is not None and equip.wielded_slot is not None:
        instance = inventory.slots.get(equip.wielded_slot)
        if instance is not None and instance.category == ItemCategory.WEAPON:
            weapon = reg.get_weapon(instance.item_id)
            min_damage = weapon.min_damage
            max_damage = weapon.max_damage
            accuracy = PLAYER_ACCURACY + weapon.accuracy_bonus

    evade = base.evade
    if equip is not None and equip.worn_slot is not None:
        instance = inventory.slots.get(equip.worn_slot)
        if instance is not None and instance.category == ItemCategory.ARMOR:
            armor = reg.get_armor(instance.item_id)
            ac = PLAYER_AC + armor.ac_bonus
            evade = base.evade + armor.evade_bonus

    might_acc = 0.0
    might_min = 0
    might_max = 0
    if effects is not None and effects.might_turns > 0:
        might_acc = effects.might_accuracy_bonus
        might_min = effects.might_min_damage_bonus
        might_max = effects.might_max_damage_bonus

    return Fighter(
        hp=base.hp,
        max_hp=base.max_hp,
        accuracy=accuracy + prog.bonus_accuracy + might_acc,
        evade=evade + prog.bonus_evade,
        ac=ac + prog.bonus_ac,
        min_damage=min_damage + prog.bonus_min_damage + might_min,
        max_damage=max_damage + prog.bonus_max_damage + might_max,
    )


def clear_equip_slot(equip: EquipState, slot: str) -> None:
    if equip.wielded_slot == slot:
        equip.wielded_slot = None
    if equip.worn_slot == slot:
        equip.worn_slot = None


def destroy_item_in_slot(
    player: Entity,
    slot: str,
    message_log: MessageLog,
    *,
    registry: ItemRegistry | None = None,
) -> None:
    inventory = player.components[Inventory]
    instance = inventory.slots.get(slot)
    if instance is None:
        return

    reg = registry or item_registry()
    display = reg.display_name_for(instance.item_id, instance.category)
    inventory.slots[slot] = None
    equip = player.components.get(EquipState)
    if equip is not None:
        clear_equip_slot(equip, slot)
    message_log.add(
        messages.item_destroyed(display),
        category=MessageCategory.DANGER,
    )


def degrade_wielded_weapon_on_hit(player: Entity, message_log: MessageLog) -> None:
    equip = player.components.get(EquipState)
    if equip is None or equip.wielded_slot is None:
        return

    slot = equip.wielded_slot
    inventory = player.components[Inventory]
    instance = inventory.slots.get(slot)
    if instance is None or instance.category != ItemCategory.WEAPON:
        equip.wielded_slot = None
        return
    if instance.durability is None:
        return

    instance.durability -= 1
    if instance.durability <= 0:
        destroy_item_in_slot(player, slot, message_log)


def definition_for_spawn(
    registry: ItemRegistry,
    item_id: str,
    category: ItemCategory,
) -> WeaponDefinition | ArmorDefinition | PotionDefinition | WandDefinition | ThrowableDefinition:
    match category:
        case ItemCategory.WEAPON:
            return registry.get_weapon(item_id)
        case ItemCategory.ARMOR:
            return registry.get_armor(item_id)
        case ItemCategory.POTION:
            return registry.get_potion(item_id)
        case ItemCategory.WAND:
            return registry.get_wand(item_id)
        case ItemCategory.THROWABLE:
            return registry.get_throwable(item_id)