from __future__ import annotations

import attrs

from src.components import ItemCategory


@attrs.define(frozen=True)
class ItemSpawnConfig:
    weight: float
    min_depth: int
    max_depth: int
    spawn_min: int = 0


@attrs.define(frozen=True)
class WeaponDefinition:
    id: str
    display_name: str
    glyph: str
    fg: tuple[int, int, int]
    examine: str
    min_damage: int
    max_damage: int
    accuracy_bonus: float
    durability_max: int
    spawn: ItemSpawnConfig


@attrs.define(frozen=True)
class ArmorDefinition:
    id: str
    display_name: str
    glyph: str
    fg: tuple[int, int, int]
    examine: str
    ac_bonus: int
    digestion_ac: int
    durability_max: int
    spawn: ItemSpawnConfig
    evade_bonus: float = 0.0


@attrs.define(frozen=True)
class PotionDefinition:
    id: str
    display_name: str
    glyph: str
    fg: tuple[int, int, int]
    examine: str
    effect: str
    spawn: ItemSpawnConfig
    heal_amount: int = 0
    duration_turns: int = 0
    accuracy_bonus: float = 0.0
    min_damage_bonus: int = 0
    max_damage_bonus: int = 0
    delay_min_turns: int = 0
    delay_max_turns: int = 0


@attrs.define(frozen=True)
class ThrowableDefinition:
    id: str
    display_name: str
    glyph: str
    fg: tuple[int, int, int]
    examine: str
    min_damage: int
    max_damage: int
    accuracy_bonus: float
    spawn: ItemSpawnConfig
    # Floor spawn stack size (inclusive range); stock packs of 3–4.
    spawn_stack_min: int = 1
    spawn_stack_max: int = 1


@attrs.define(frozen=True)
class WandDefinition:
    id: str
    display_name: str
    glyph: str
    fg: tuple[int, int, int]
    examine: str
    effect: str
    charges_max: int
    charges_start: int
    range: int
    min_damage: int
    max_damage: int
    accuracy: float
    spawn: ItemSpawnConfig


@attrs.define(frozen=True)
class ItemRegistry:
    schema_version: int
    weapons: tuple[WeaponDefinition, ...]
    armor: tuple[ArmorDefinition, ...]
    potions: tuple[PotionDefinition, ...]
    wands: tuple[WandDefinition, ...]
    throwables: tuple[ThrowableDefinition, ...] = ()
    warnings: tuple[str, ...] = ()

    def weapon_by_id(self) -> dict[str, WeaponDefinition]:
        return {item.id: item for item in self.weapons}

    def armor_by_id(self) -> dict[str, ArmorDefinition]:
        return {item.id: item for item in self.armor}

    def potion_by_id(self) -> dict[str, PotionDefinition]:
        return {item.id: item for item in self.potions}

    def wand_by_id(self) -> dict[str, WandDefinition]:
        return {item.id: item for item in self.wands}

    def throwable_by_id(self) -> dict[str, ThrowableDefinition]:
        return {item.id: item for item in self.throwables}

    def get_weapon(self, item_id: str) -> WeaponDefinition:
        return self.weapon_by_id()[item_id]

    def get_armor(self, item_id: str) -> ArmorDefinition:
        return self.armor_by_id()[item_id]

    def get_potion(self, item_id: str) -> PotionDefinition:
        return self.potion_by_id()[item_id]

    def get_wand(self, item_id: str) -> WandDefinition:
        return self.wand_by_id()[item_id]

    def get_throwable(self, item_id: str) -> ThrowableDefinition:
        return self.throwable_by_id()[item_id]

    def category_for(self, item_id: str) -> ItemCategory:
        if item_id in self.weapon_by_id():
            return ItemCategory.WEAPON
        if item_id in self.armor_by_id():
            return ItemCategory.ARMOR
        if item_id in self.potion_by_id():
            return ItemCategory.POTION
        if item_id in self.wand_by_id():
            return ItemCategory.WAND
        if item_id in self.throwable_by_id():
            return ItemCategory.THROWABLE
        raise KeyError(item_id)

    def display_name_for(self, item_id: str, category: ItemCategory) -> str:
        match category:
            case ItemCategory.WEAPON:
                return self.get_weapon(item_id).display_name
            case ItemCategory.ARMOR:
                return self.get_armor(item_id).display_name
            case ItemCategory.POTION:
                return self.get_potion(item_id).display_name
            case ItemCategory.WAND:
                return self.get_wand(item_id).display_name
            case ItemCategory.THROWABLE:
                return self.get_throwable(item_id).display_name

    def glyph_for(self, item_id: str, category: ItemCategory) -> str:
        match category:
            case ItemCategory.WEAPON:
                return self.get_weapon(item_id).glyph
            case ItemCategory.ARMOR:
                return self.get_armor(item_id).glyph
            case ItemCategory.POTION:
                return self.get_potion(item_id).glyph
            case ItemCategory.WAND:
                return self.get_wand(item_id).glyph
            case ItemCategory.THROWABLE:
                return self.get_throwable(item_id).glyph