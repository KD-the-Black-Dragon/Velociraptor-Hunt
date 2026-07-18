from __future__ import annotations

import random
from functools import lru_cache
from typing import Any

from tcod.ecs import Entity, Registry

from src.components import (
    Abilities,
    AbilityState,
    AI,
    AIState,
    Alignment,
    BlocksMovement,
    DigestionStats,
    DisplayName,
    ExamineDescription,
    Fighter,
    Item,
    Mobility,
    NPCAlignment,
    NpcPrefix,
    Position,
    ProperName,
    Renderable,
    SpeciesId,
    VoreCapable,
    VoreNarratives,
)
from src.constants import MONSTER_SPAWN_MIN_DISTANCE
from src.data.ability_parser import collapse_and_parse_abilities, parse_abilities
from src.data.alignment_profiles import alignment_profile, digest_time_for, digestion_damage_for
from src.data.depth_scaling_config import (
    DepthBonuses,
    DepthScalingConfig,
    bonuses_for_spawn,
)
from src.data.depth_scaling_loader import (
    default_depth_scaling_config,
    reset_depth_scaling_cache,
)
from src.data.dungeon_spawn_config import DungeonSpawnConfig, compute_target_npc_count
from src.data.dungeon_spawn_loader import load_dungeon_spawn_config
from src.data.entity_loader import load_entity_registry
from src.data.entity_registry import EntityDefinition, EntityRegistry
from src.data.item_loader import load_item_registry
from src.components import ItemCategory
from src.data.item_registry import (
    ArmorDefinition,
    ItemRegistry,
    PotionDefinition,
    WandDefinition,
    WeaponDefinition,
)
from src.data.npc_prefix_loader import (
    default_npc_prefix_registry,
    reset_npc_prefix_registry_cache,
)
from src.data.npc_prefix_registry import NpcPrefixDefinition, NpcPrefixRegistry
from src.map_gen import GameMap, can_enter_tile, water_positions

@lru_cache(maxsize=1)
def _get_registry() -> EntityRegistry:
    return load_entity_registry()


def renderable_for(entity_id: str) -> Renderable:
    definition = _get_registry().get(entity_id)
    return Renderable(ch=ord(definition.glyph), fg=definition.fg)


_LAZY_ATTRS: dict[str, Any] = {
    "WOLF_EXAMINE_DESCRIPTION": lambda: _get_registry().get("wolf").examine or "",
    "KNIGHT_EXAMINE_DESCRIPTION": lambda: _get_registry().get("knight").examine or "",
    "RABBIT_EXAMINE_DESCRIPTION": lambda: _get_registry().get("rabbit").examine or "",
    "SHARK_EXAMINE_DESCRIPTION": lambda: _get_registry().get("shark").examine or "",
    "WOLF_RENDERABLE": lambda: renderable_for("wolf"),
    "KNIGHT_RENDERABLE": lambda: renderable_for("knight"),
    "RABBIT_RENDERABLE": lambda: renderable_for("rabbit"),
    "SHARK_RENDERABLE": lambda: renderable_for("shark"),
}


def __getattr__(name: str) -> Any:
    factory = _LAZY_ATTRS.get(name)
    if factory is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = factory()
    globals()[name] = value
    return value


def spawn_entity_by_id(
    world: Registry,
    entity_id: str,
    x: int,
    y: int,
    *,
    registry: EntityRegistry | None = None,
    floor_depth: int = 1,
    difficulty_id: str | None = None,
    depth_scaling: DepthScalingConfig | None = None,
) -> Entity:
    """Spawn one entity by registry id (tests, debug helpers, summons)."""
    reg = registry or load_entity_registry()
    return spawn_from_definition(
        world,
        reg.get(entity_id),
        x,
        y,
        floor_depth=floor_depth,
        difficulty_id=difficulty_id,
        depth_scaling=depth_scaling,
    )


def _bake_fighter_stats(
    definition: EntityDefinition,
    bonuses: DepthBonuses,
) -> tuple[int, int, float, float, int, int, int, float, int, int]:
    """Return combat fields after depth bonuses (max_hp, hp, acc, evade, ac, min, max, r_acc, r_min, r_max)."""
    max_hp = max(1, definition.max_hp + bonuses.max_hp)
    accuracy = definition.accuracy + bonuses.accuracy
    evade = max(0.0, float(definition.evade) + float(bonuses.evade))
    ac = max(0, definition.ac + bonuses.ac)
    min_damage = max(0, definition.min_damage + bonuses.min_damage)
    max_damage = max(0, definition.max_damage + bonuses.max_damage)
    if min_damage > max_damage:
        max_damage = min_damage

    ranged_accuracy = definition.ranged_accuracy
    ranged_min = definition.ranged_min_damage
    ranged_max = definition.ranged_max_damage
    if definition.ranged_min_damage > 0 and definition.ranged_max_damage > 0:
        ranged_accuracy = definition.ranged_accuracy + bonuses.accuracy
        ranged_min = max(0, definition.ranged_min_damage + bonuses.min_damage)
        ranged_max = max(0, definition.ranged_max_damage + bonuses.max_damage)
        if ranged_min > ranged_max:
            ranged_max = ranged_min

    return (
        max_hp,
        max_hp,
        accuracy,
        evade,
        ac,
        min_damage,
        max_damage,
        ranged_accuracy,
        ranged_min,
        ranged_max,
    )


def apply_prefix_definition(
    entity: Entity,
    definition: EntityDefinition,
    prefix: NpcPrefixDefinition,
) -> None:
    """Apply flat prefix bonuses and rename (after depth bake)."""
    bonuses = prefix.stat_bonuses
    fighter = entity.components[Fighter]
    max_hp = max(1, fighter.max_hp + bonuses.max_hp)
    min_damage = max(0, fighter.min_damage + bonuses.min_damage)
    max_damage = max(0, fighter.max_damage + bonuses.max_damage)
    if min_damage > max_damage:
        max_damage = min_damage
    ranged_acc = fighter.ranged_accuracy
    ranged_min = fighter.ranged_min_damage
    ranged_max = fighter.ranged_max_damage
    has_ranged = definition.ranged_min_damage > 0 and definition.ranged_max_damage > 0
    if has_ranged:
        ranged_acc = (
            fighter.ranged_accuracy + bonuses.accuracy + bonuses.ranged_accuracy
        )
        ranged_min = max(0, fighter.ranged_min_damage + bonuses.min_damage)
        ranged_max = max(0, fighter.ranged_max_damage + bonuses.max_damage)
        if ranged_min > ranged_max:
            ranged_max = ranged_min
    else:
        ranged_acc = fighter.ranged_accuracy

    entity.components[Fighter] = Fighter(
        hp=max_hp,
        max_hp=max_hp,
        accuracy=fighter.accuracy + bonuses.accuracy,
        evade=max(0.0, float(fighter.evade) + float(bonuses.evade)),
        ac=max(0, fighter.ac + bonuses.ac),
        min_damage=min_damage,
        max_damage=max_damage,
        ranged_accuracy=ranged_acc,
        ranged_min_damage=ranged_min,
        ranged_max_damage=ranged_max,
    )
    dig = entity.components.get(DigestionStats)
    if dig is not None and bonuses.digestion_damage_per_tick:
        entity.components[DigestionStats] = DigestionStats(
            damage_per_tick=max(0, dig.damage_per_tick + bonuses.digestion_damage_per_tick),
            digest_time=dig.digest_time,
        )
    entity.components[DisplayName] = DisplayName(
        name=f"{prefix.display_prefix}{definition.display_name}"
    )
    entity.components[NpcPrefix] = NpcPrefix(
        prefix_id=prefix.id,
        display_prefix=prefix.display_prefix,
    )
    if prefix.grant_abilities:
        merged = collapse_and_parse_abilities(
            [*definition.abilities, *prefix.grant_abilities]
        )
        entity.components[Abilities] = Abilities(parsed=merged)


def try_roll_prefix(
    entity: Entity,
    definition: EntityDefinition,
    *,
    floor_depth: int,
    difficulty_id: str | None,
    depth_scaling: DepthScalingConfig,
    rng: random.Random,
    prefix_registry: NpcPrefixRegistry | None = None,
) -> NpcPrefixDefinition | None:
    """Maybe roll and apply one prefix. Returns the prefix if applied."""
    profile = depth_scaling.profile_for(difficulty_id)
    chance = profile.prefix_spawn.chance_at_depth(floor_depth)
    if chance <= 0:
        return None
    if rng.randrange(100) >= chance:
        return None
    reg = prefix_registry if prefix_registry is not None else default_npc_prefix_registry()
    eligible = reg.eligible_for_entity(
        alignment=definition.alignment,
        floor_depth=floor_depth,
        definition=definition,
    )
    if not eligible:
        return None
    weights = [max(0, p.weight) for p in eligible]
    if sum(weights) <= 0:
        return None
    chosen = rng.choices(list(eligible), weights=weights, k=1)[0]
    apply_prefix_definition(entity, definition, chosen)
    return chosen


def spawn_from_definition(
    world: Registry,
    definition: EntityDefinition,
    x: int,
    y: int,
    *,
    floor_depth: int = 1,
    difficulty_id: str | None = None,
    depth_scaling: DepthScalingConfig | None = None,
    roll_prefix: bool = False,
    rng: random.Random | None = None,
    prefix_registry: NpcPrefixRegistry | None = None,
    player_x: int | None = None,
    player_y: int | None = None,
    arm_spawn_freeze: bool = False,
) -> Entity:
    """Materialize one NPC from a loaded entity definition.

    Depth bonuses bake into ``Fighter`` / digestion damage at spawn (once).
    Optional ``roll_prefix`` (floor population only) may add Elite-style modifiers.
    """
    profile = alignment_profile(definition.alignment)
    scaling = (
        depth_scaling
        if depth_scaling is not None
        else default_depth_scaling_config()
    )
    bonuses = bonuses_for_spawn(
        scaling,
        floor_depth=floor_depth,
        alignment=definition.alignment,
        difficulty_id=difficulty_id,
    )
    (
        max_hp,
        hp,
        accuracy,
        evade,
        ac,
        min_damage,
        max_damage,
        ranged_accuracy,
        ranged_min,
        ranged_max,
    ) = _bake_fighter_stats(definition, bonuses)

    entity = world[object()]
    entity.components[Position] = Position(x, y)
    entity.components[Renderable] = Renderable(
        ch=ord(definition.glyph),
        fg=definition.fg,
    )
    entity.components[Fighter] = Fighter(
        hp=hp,
        max_hp=max_hp,
        accuracy=accuracy,
        evade=evade,
        ac=ac,
        min_damage=min_damage,
        max_damage=max_damage,
        ranged_accuracy=ranged_accuracy,
        ranged_min_damage=ranged_min,
        ranged_max_damage=ranged_max,
    )
    entity.components[AI] = AI()
    entity.components[AIState] = AIState(ai_turn_salt=(x + y) & 1)
    # Spawn freeze is armed by callers that know player position (floor pop / summons).
    entity.components[AbilityState] = AbilityState()
    entity.components[SpeciesId] = SpeciesId(id=definition.id)
    entity.components[DisplayName] = DisplayName(name=definition.display_name)
    entity.components[NPCAlignment] = NPCAlignment(alignment=definition.alignment)
    entity.components[Mobility] = Mobility(kind=definition.mobility)

    if definition.examine:
        entity.components[ExamineDescription] = ExamineDescription(text=definition.examine)
    if definition.proper_name:
        entity.components[ProperName] = ProperName(name=definition.proper_name)

    if profile.blocks_movement:
        entity.tags.add(BlocksMovement)
    if profile.vore_capable:
        entity.tags.add(VoreCapable)
        narrative_types = (
            tuple(definition.vore_narratives.keys())
            if definition.vore_narratives
            else ("OV", "CV", "AV")
        )
        entity.components[VoreNarratives] = VoreNarratives(types=narrative_types)

    digestion_damage = digestion_damage_for(
        definition.alignment,
        definition.digestion_damage_per_tick,
    )
    if digestion_damage is not None:
        digest_time = digest_time_for(definition.alignment, definition.digest_time)
        assert digest_time is not None
        baked_dig_damage = max(0, digestion_damage + bonuses.digestion_damage_per_tick)
        entity.components[DigestionStats] = DigestionStats(
            damage_per_tick=baked_dig_damage,
            digest_time=digest_time,
        )

    if definition.abilities:
        parsed = parse_abilities(definition.abilities)
        if parsed:
            entity.components[Abilities] = Abilities(parsed=parsed)

    if roll_prefix:
        try_roll_prefix(
            entity,
            definition,
            floor_depth=floor_depth,
            difficulty_id=difficulty_id,
            depth_scaling=scaling,
            rng=rng or random.Random(),
            prefix_registry=prefix_registry,
        )

    if arm_spawn_freeze and player_x is not None and player_y is not None:
        from src.systems.ai.common import apply_spawn_ai_freeze_at_spawn

        apply_spawn_ai_freeze_at_spawn(
            entity,
            spawn_x=x,
            spawn_y=y,
            player_x=player_x,
            player_y=player_y,
            freeze_config=scaling.profile_for(difficulty_id).spawn_ai_freeze,
        )

    return entity


def _water_candidate_tiles(
    game_map: GameMap,
    player_x: int,
    player_y: int,
) -> list[tuple[int, int]]:
    tiles: list[tuple[int, int]] = []
    min_dist_sq = MONSTER_SPAWN_MIN_DISTANCE * MONSTER_SPAWN_MIN_DISTANCE
    from src.components import MobilityType

    for x, y in water_positions(game_map):
        if not can_enter_tile(game_map, x, y, MobilityType.AQUATIC):
            continue
        dx = x - player_x
        dy = y - player_y
        if dx * dx + dy * dy < min_dist_sq:
            continue
        tiles.append((x, y))
    return tiles


def _candidate_tiles(
    game_map: GameMap,
    player_x: int,
    player_y: int,
    *,
    mobility_kind,
) -> list[tuple[int, int]]:
    from src.components import MobilityType

    tiles: list[tuple[int, int]] = []
    min_dist_sq = MONSTER_SPAWN_MIN_DISTANCE * MONSTER_SPAWN_MIN_DISTANCE
    for y in range(game_map.height):
        for x in range(game_map.width):
            if not can_enter_tile(game_map, x, y, mobility_kind):
                continue
            dx = x - player_x
            dy = y - player_y
            if dx * dx + dy * dy < min_dist_sq:
                continue
            tiles.append((x, y))
    return tiles


def _eligible_definitions(
    registry: EntityRegistry,
    *,
    floor_depth: int,
    terrain: str,
    map_has_water: bool,
) -> list[EntityDefinition]:
    eligible: list[EntityDefinition] = []
    for definition in registry.entities:
        if not (definition.spawn.min_depth <= floor_depth <= definition.spawn.max_depth):
            continue
        if definition.spawn.terrain != terrain:
            continue
        if definition.spawn_requires_water and not map_has_water:
            continue
        eligible.append(definition)
    return eligible


@lru_cache(maxsize=1)
def default_spawn_config() -> DungeonSpawnConfig:
    return load_dungeon_spawn_config()


def reset_spawn_config_cache() -> None:
    default_spawn_config.cache_clear()
    reset_depth_scaling_cache()
    reset_npc_prefix_registry_cache()


def valid_spawn_tiles(
    game_map: GameMap,
    player_x: int,
    player_y: int,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """Return (land_candidates, water_candidates) for density and placement."""
    from src.components import MobilityType

    land = _candidate_tiles(
        game_map,
        player_x,
        player_y,
        mobility_kind=MobilityType.GROUND,
    )
    water = _water_candidate_tiles(game_map, player_x, player_y)
    return land, water


def count_valid_spawn_tiles(land: list[tuple[int, int]], water: list[tuple[int, int]]) -> int:
    return len(land) + len(water)


def good_aligned_weight_at_depth(
    registry: EntityRegistry,
    floor_depth: int,
    *,
    map_has_water: bool,
) -> int:
    """Species-agnostic cap for good-follower spawn budget reduction."""
    total = 0
    for terrain in ("land", "water"):
        for definition in _eligible_definitions(
            registry,
            floor_depth=floor_depth,
            terrain=terrain,
            map_has_water=map_has_water,
        ):
            if definition.alignment == Alignment.GOOD:
                total += max(0, int(definition.spawn.weight))
    return total


def _water_placement_pool(
    game_map: GameMap,
    water_cands: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    """Mutable placement pool: distance-filtered water, or all-water fallback."""
    from src.components import MobilityType

    if water_cands:
        return water_cands
    if not water_positions(game_map):
        return []
    return [
        (x, y)
        for x, y in water_positions(game_map)
        if can_enter_tile(game_map, x, y, MobilityType.AQUATIC)
    ]


def _filtered_eligible(
    land_defs: list[EntityDefinition],
    water_defs: list[EntityDefinition],
    *,
    land_cands: list[tuple[int, int]],
    water_place_pool: list[tuple[int, int]],
    map_has_water: bool,
) -> list[EntityDefinition]:
    eligible: list[EntityDefinition] = []
    if land_cands:
        eligible.extend(land_defs)
    if map_has_water and water_place_pool:
        eligible.extend(water_defs)
    return eligible


def _weighted_choice(definitions: list[EntityDefinition], rng: random.Random) -> EntityDefinition:
    weights = [max(0, int(definition.spawn.weight)) for definition in definitions]
    if not definitions or sum(weights) == 0:
        raise ValueError("empty weighted choice")
    return rng.choices(definitions, weights=weights, k=1)[0]


def spawn_floor_population(
    world: Registry,
    game_map: GameMap,
    player_x: int,
    player_y: int,
    floor_depth: int,
    *,
    rng: random.Random | None = None,
    good_follower_reduction: int = 0,
    registry: EntityRegistry | None = None,
    spawn_config: DungeonSpawnConfig | None = None,
    difficulty_id: str | None = None,
    depth_scaling: DepthScalingConfig | None = None,
    density_multiplier: float | None = None,
) -> list[Entity]:
    """Spawn NPCs via density-driven weighted draws from entity definitions."""
    rng = rng or random.Random()
    reg = registry or load_entity_registry()
    config = spawn_config or default_spawn_config()
    scaling = (
        depth_scaling
        if depth_scaling is not None
        else default_depth_scaling_config()
    )
    profile = scaling.profile_for(difficulty_id)
    dens_mult = (
        float(density_multiplier)
        if density_multiplier is not None
        else float(profile.density_multiplier)
    )

    land_cands, water_cands = valid_spawn_tiles(game_map, player_x, player_y)
    map_has_water = bool(water_positions(game_map))

    land_defs = _eligible_definitions(
        reg,
        floor_depth=floor_depth,
        terrain="land",
        map_has_water=map_has_water,
    )
    water_defs = _eligible_definitions(
        reg,
        floor_depth=floor_depth,
        terrain="water",
        map_has_water=map_has_water,
    )
    water_place_pool = _water_placement_pool(game_map, water_cands)

    valid_count = count_valid_spawn_tiles(land_cands, water_cands)
    target = compute_target_npc_count(
        valid_count,
        floor_depth,
        config,
        rng,
        density_multiplier=dens_mult,
    )
    effective_target = max(0, target - good_follower_reduction)

    placed: list[Entity] = []
    attempts = 0
    max_attempts = max(effective_target * 30, 50)

    while len(placed) < effective_target and attempts < max_attempts:
        attempts += 1
        eligible = _filtered_eligible(
            land_defs,
            water_defs,
            land_cands=land_cands,
            water_place_pool=water_place_pool,
            map_has_water=map_has_water,
        )
        if not eligible:
            break

        definition = _weighted_choice(eligible, rng)
        terrain = definition.spawn.terrain
        pool = land_cands if terrain == "land" else water_place_pool

        if not pool:
            continue

        x, y = rng.choice(pool)
        pool.remove((x, y))
        placed.append(
            spawn_from_definition(
                world,
                definition,
                x,
                y,
                floor_depth=floor_depth,
                difficulty_id=difficulty_id,
                depth_scaling=scaling,
                roll_prefix=True,
                rng=rng,
                player_x=player_x,
                player_y=player_y,
                arm_spawn_freeze=True,
            )
        )

    return placed


def _eligible_item_spawns(
    registry: ItemRegistry,
    *,
    floor_depth: int,
) -> list[tuple[ItemCategory, str]]:
    """Return (category, id) pairs eligible for this floor depth."""
    eligible: list[tuple[ItemCategory, str]] = []
    for weapon in registry.weapons:
        if weapon.spawn.min_depth <= floor_depth <= weapon.spawn.max_depth:
            eligible.append((ItemCategory.WEAPON, weapon.id))
    for armor in registry.armor:
        if armor.spawn.min_depth <= floor_depth <= armor.spawn.max_depth:
            eligible.append((ItemCategory.ARMOR, armor.id))
    for potion in registry.potions:
        if potion.spawn.min_depth <= floor_depth <= potion.spawn.max_depth:
            eligible.append((ItemCategory.POTION, potion.id))
    for wand in registry.wands:
        if wand.spawn.min_depth <= floor_depth <= wand.spawn.max_depth:
            eligible.append((ItemCategory.WAND, wand.id))
    for throwable in registry.throwables:
        if throwable.spawn.min_depth <= floor_depth <= throwable.spawn.max_depth:
            eligible.append((ItemCategory.THROWABLE, throwable.id))
    return eligible


def _build_item_weighted_pool(
    registry: ItemRegistry,
    *,
    floor_depth: int,
) -> list[tuple[ItemCategory, str]]:
    pool: list[tuple[ItemCategory, str]] = []
    for weapon in registry.weapons:
        if weapon.spawn.min_depth <= floor_depth <= weapon.spawn.max_depth:
            weight = int(weapon.spawn.weight)
            if weight > 0:
                pool.extend([(ItemCategory.WEAPON, weapon.id)] * weight)
    for armor_piece in registry.armor:
        if armor_piece.spawn.min_depth <= floor_depth <= armor_piece.spawn.max_depth:
            weight = int(armor_piece.spawn.weight)
            if weight > 0:
                pool.extend([(ItemCategory.ARMOR, armor_piece.id)] * weight)
    for potion in registry.potions:
        if potion.spawn.min_depth <= floor_depth <= potion.spawn.max_depth:
            weight = int(potion.spawn.weight)
            if weight > 0:
                pool.extend([(ItemCategory.POTION, potion.id)] * weight)
    for wand in registry.wands:
        if wand.spawn.min_depth <= floor_depth <= wand.spawn.max_depth:
            weight = int(wand.spawn.weight)
            if weight > 0:
                pool.extend([(ItemCategory.WAND, wand.id)] * weight)
    for throwable in registry.throwables:
        if throwable.spawn.min_depth <= floor_depth <= throwable.spawn.max_depth:
            weight = int(throwable.spawn.weight)
            if weight > 0:
                pool.extend([(ItemCategory.THROWABLE, throwable.id)] * weight)
    return pool


def _spawn_config_for(
    registry: ItemRegistry,
    category: ItemCategory,
    item_id: str,
) -> WeaponDefinition | ArmorDefinition | PotionDefinition | WandDefinition:
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


def spawn_item_entity(
    world: Registry,
    category: ItemCategory,
    item_id: str,
    x: int,
    y: int,
    *,
    registry: ItemRegistry | None = None,
    durability: int | None = None,
    charges: int | None = None,
    stack_count: int | None = None,
    rng: random.Random | None = None,
) -> Entity:
    """Place one floor item from registry data."""
    reg = registry or load_item_registry()
    definition = _spawn_config_for(reg, category, item_id)
    rng = rng or random.Random()

    entity = world[object()]
    entity.components[Position] = Position(x, y)
    entity.components[Renderable] = Renderable(
        ch=ord(definition.glyph),
        fg=definition.fg,
    )
    entity.components[ExamineDescription] = ExamineDescription(text=definition.examine)

    item_durability: int | None = None
    item_charges: int | None = None
    item_stack = 1
    if category == ItemCategory.WEAPON:
        weapon = reg.get_weapon(item_id)
        item_durability = durability if durability is not None else weapon.durability_max
    elif category == ItemCategory.ARMOR:
        armor_def = reg.get_armor(item_id)
        item_durability = durability if durability is not None else armor_def.durability_max
    elif category == ItemCategory.WAND:
        wand = reg.get_wand(item_id)
        item_charges = charges if charges is not None else wand.charges_start
    elif category == ItemCategory.THROWABLE:
        throwable = reg.get_throwable(item_id)
        if stack_count is not None:
            item_stack = max(1, int(stack_count))
        else:
            lo = max(1, int(throwable.spawn_stack_min))
            hi = max(lo, int(throwable.spawn_stack_max))
            item_stack = rng.randint(lo, hi)

    entity.components[Item] = Item(
        item_id=item_id,
        category=category,
        durability=item_durability,
        charges=item_charges,
        stack_count=item_stack,
    )
    return entity


def spawn_items(
    world: Registry,
    game_map: GameMap,
    player_x: int,
    player_y: int,
    floor_depth: int,
    *,
    rng: random.Random | None = None,
    registry: ItemRegistry | None = None,
) -> list[Entity]:
    """Spawn weighted floor items from item JSON for the current depth."""
    from src.components import MobilityType

    rng = rng or random.Random()
    reg = registry or load_item_registry()
    candidates = _candidate_tiles(
        game_map,
        player_x,
        player_y,
        mobility_kind=MobilityType.GROUND,
    )
    if not candidates:
        return []

    pool = _build_item_weighted_pool(reg, floor_depth=floor_depth)
    rng.shuffle(pool)
    rng.shuffle(candidates)
    spawned: list[Entity] = []
    from src.constants import MAX_FLOOR_ITEM_PLACEMENTS

    count = min(MAX_FLOOR_ITEM_PLACEMENTS, len(pool), len(candidates))

    for (x, y), (category, item_id) in zip(candidates[:count], pool[:count], strict=False):
        spawned.append(
            spawn_item_entity(world, category, item_id, x, y, registry=reg, rng=rng)
        )

    potion_counts: dict[str, int] = {}
    for entity in spawned:
        item = entity.components[Item]
        if item.category == ItemCategory.POTION:
            potion_counts[item.item_id] = potion_counts.get(item.item_id, 0) + 1

    remaining_candidates = list(candidates[count:])
    if not remaining_candidates:
        remaining_candidates = list(candidates)
    rng.shuffle(remaining_candidates)
    candidate_index = 0

    for potion in reg.potions:
        if not (potion.spawn.min_depth <= floor_depth <= potion.spawn.max_depth):
            continue
        needed = max(0, potion.spawn.spawn_min - potion_counts.get(potion.id, 0))
        for _ in range(needed):
            if candidate_index >= len(remaining_candidates):
                break
            x, y = remaining_candidates[candidate_index]
            candidate_index += 1
            spawned.append(
                spawn_item_entity(
                    world,
                    ItemCategory.POTION,
                    potion.id,
                    x,
                    y,
                    registry=reg,
                )
            )
            potion_counts[potion.id] = potion_counts.get(potion.id, 0) + 1

    return spawned