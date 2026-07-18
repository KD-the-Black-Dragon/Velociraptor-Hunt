from __future__ import annotations

import random
from enum import Enum, auto

import attrs
from tcod.ecs import Entity, Registry

from src import messages
from src.components import (
    Abilities,
    AbilityState,
    Alignment,
    BlocksMovement,
    Fighter,
    NPCAlignment,
    Player,
    Position,
    Stunned,
    VoreCapable,
)
from src.data.ability_parser import (
    FixedAbility,
    RangeAbility,
    RangedVoreAbility,
    SmiteAbility,
    SummonAbility,
)
from src.data.entity_loader import load_entity_registry
from src.map_gen import GameMap, can_enter_tile
from src.message_log import MessageCategory, MessageLog
from src.spawn import spawn_entity_by_id
from src.systems import ai as ai_module
from src.systems.ai.common import _closed_door_toward_target
from src.systems.combat import perform_npc_path_attack, perform_npc_smite_attack
from src.systems.ranged_path import PathShotStatus, resolve_path_shot
from src.systems.fov import entity_visible_to_player
from src.systems.movement import MOVEMENT_DIRECTIONS, is_stationary
from src.systems.naming import entity_log_name
class ActionStepKind(Enum):
    SKIP = auto()
    MOVE = auto()
    ATTACK = auto()
    MOVE_OR_BUMP = auto()


@attrs.define(frozen=True)
class ActionStep:
    kind: ActionStepKind


@attrs.define(frozen=True)
class ActionPlan:
    steps: tuple[ActionStep, ...]


def max_smite_range(entity: Entity) -> int | None:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return None
    best: int | None = None
    for parsed in abilities.parsed:
        if isinstance(parsed, SmiteAbility):
            best = parsed.distance if best is None else max(best, parsed.distance)
    return best


def has_smite_ability(entity: Entity) -> bool:
    return max_smite_range(entity) is not None


def max_path_range(entity: Entity) -> int | None:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return None
    best: int | None = None
    for parsed in abilities.parsed:
        if isinstance(parsed, RangeAbility):
            best = parsed.distance if best is None else max(best, parsed.distance)
    return best


def has_path_ability(entity: Entity) -> bool:
    return max_path_range(entity) is not None


def max_ranged_vore_range(entity: Entity) -> int | None:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return None
    best: int | None = None
    for parsed in abilities.parsed:
        if isinstance(parsed, RangedVoreAbility):
            best = parsed.distance if best is None else max(best, parsed.distance)
    return best


def has_ranged_vore_ability(entity: Entity) -> bool:
    return max_ranged_vore_range(entity) is not None


def has_coward(entity: Entity) -> bool:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return False
    return any(
        isinstance(parsed, FixedAbility) and parsed.ability_id == "Coward"
        for parsed in abilities.parsed
    )


def has_supercoward(entity: Entity) -> bool:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return False
    return any(
        isinstance(parsed, FixedAbility) and parsed.ability_id == "Supercoward"
        for parsed in abilities.parsed
    )


def has_coward_flee_ability(entity: Entity) -> bool:
    return has_coward(entity) or has_supercoward(entity)


def has_erratic(entity: Entity) -> bool:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return False
    return any(
        isinstance(parsed, FixedAbility) and parsed.ability_id == "Erratic"
        for parsed in abilities.parsed
    )


def has_slow(entity: Entity) -> bool:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return False
    return any(
        isinstance(parsed, FixedAbility) and parsed.ability_id == "Slow"
        for parsed in abilities.parsed
    )


def has_fast(entity: Entity) -> bool:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return False
    return any(
        isinstance(parsed, FixedAbility) and parsed.ability_id == "Fast"
        for parsed in abilities.parsed
    )


def has_knockback(entity: Entity) -> bool:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return False
    return any(
        isinstance(parsed, FixedAbility) and parsed.ability_id == "Knockback"
        for parsed in abilities.parsed
    )


def has_prefer_vore(entity: Entity) -> bool:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return False
    return any(
        isinstance(parsed, FixedAbility) and parsed.ability_id == "PreferVore"
        for parsed in abilities.parsed
    )


def has_wander(entity: Entity) -> bool:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return False
    return any(
        isinstance(parsed, FixedAbility) and parsed.ability_id == "Wander"
        for parsed in abilities.parsed
    )


def has_hands(entity: Entity) -> bool:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return False
    return any(
        isinstance(parsed, FixedAbility) and parsed.ability_id.lower() == "hands"
        for parsed in abilities.parsed
    )


def has_no_chase(entity: Entity) -> bool:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return False
    return any(
        isinstance(parsed, FixedAbility) and parsed.ability_id == "NoChase"
        for parsed in abilities.parsed
    )


def _knockback_step(attack_vector: tuple[int, int]) -> tuple[int, int]:
    dx, dy = attack_vector
    if dx == 0 and dy == 0:
        return (0, 0)
    step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
    step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
    return (step_x, step_y)


def try_apply_knockback(
    attacker: Entity,
    defender: Entity,
    world: Registry,
    game_map: GameMap,
    message_log: MessageLog,
    attack_vector: tuple[int, int],
) -> bool:
    """Push defender one tile along the attack vector. Returns True when moved."""
    if not has_knockback(attacker):
        return False

    step = _knockback_step(attack_vector)
    if step == (0, 0):
        return False

    from src.components import Player
    from src.systems.combat import _npc_combat_visible_to_player
    from src.systems.movement import can_move_to

    origin = defender.components[Position]
    if not can_move_to(world, game_map, defender, origin, step):
        return False

    defender.components[Position] = Position(origin.x + step[0], origin.y + step[1])
    if _npc_combat_visible_to_player(game_map, attacker, defender):
        if Player in defender.tags:
            message_log.add(
                messages.player_knocked_back(),
                category=MessageCategory.CAUTION,
            )
        else:
            message_log.add(
                messages.target_knocked_back(
                    entity_log_name(defender, sentence_start=True)
                ),
                category=MessageCategory.CAUTION,
            )
    return True


def has_lifedrain(entity: Entity) -> bool:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return False
    return any(
        isinstance(parsed, FixedAbility) and parsed.ability_id == "Lifedrain"
        for parsed in abilities.parsed
    )


def try_apply_lifedrain(
    attacker: Entity,
    defender: Entity,
    game_map: GameMap,
    message_log: MessageLog,
    damage: int,
) -> bool:
    """Heal attacker by damage dealt. Returns True when HP was restored."""
    if not has_lifedrain(attacker) or damage <= 0:
        return False

    from src.systems.combat import _npc_combat_visible_to_player, heal

    healed = heal(attacker, damage)
    if healed <= 0:
        return False
    if _npc_combat_visible_to_player(game_map, attacker, defender):
        message_log.add(
            messages.npc_appears_healthier(
                entity_log_name(attacker, sentence_start=True)
            ),
            category=MessageCategory.MAGICAL,
        )
    return True


def compute_action_plan(entity: Entity, player_turn_count: int = 0) -> ActionPlan:
    """Build the step list for one monster world-phase visit."""
    if has_slow(entity) and player_turn_count % 2 == 1:
        return ActionPlan(steps=(ActionStep(ActionStepKind.SKIP),))

    if has_erratic(entity):
        base: tuple[ActionStep, ...] = (
            ActionStep(ActionStepKind.MOVE),
            ActionStep(ActionStepKind.ATTACK),
            ActionStep(ActionStepKind.MOVE),
        )
    else:
        base = (ActionStep(ActionStepKind.MOVE_OR_BUMP),)

    if has_fast(entity):
        base = base + base
    return ActionPlan(steps=base)


def erratic_pursuit_suppressed(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    *,
    alignment: Alignment,
    player_engulfed: bool,
) -> bool:
    """Skip Erratic pursuit MOVE when already adjacent to an attack target."""
    return bool(
        ai_module._adjacent_attack_targets(
            monster,
            world,
            game_map,
            player,
            alignment=alignment,
            player_engulfed=player_engulfed,
        )
    )


def coward_should_flee(entity: Entity) -> bool:
    if not has_coward_flee_ability(entity):
        return False
    fighter = entity.components.get(Fighter)
    if fighter is None or fighter.hp <= 0:
        return False
    if has_supercoward(entity):
        return True
    return fighter.hp * 2 < fighter.max_hp


def _coward_threats(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    *,
    alignment: Alignment,
    player_engulfed: bool,
) -> list[Entity]:
    if alignment == Alignment.EVIL:
        return ai_module._visible_primary_hostiles(
            monster,
            world,
            game_map,
            player,
            player_engulfed=player_engulfed,
        )
    if alignment == Alignment.GOOD:
        return ai_module._visible_good_evils(monster, world, game_map)
    if alignment == Alignment.NEUTRAL:
        return ai_module._visible_evils(monster, world, game_map)
    return []


def coward_flee_direction(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    rng: random.Random,
    *,
    alignment: Alignment,
    blocked_tiles: frozenset[Position],
    player_engulfed: bool = False,
) -> tuple[int, int] | None:
    """Return a flee step when Coward/Supercoward rules and a visible threat allow retreat."""
    if is_stationary(monster) or not coward_should_flee(monster):
        return None
    threats = _coward_threats(
        monster,
        world,
        game_map,
        player,
        alignment=alignment,
        player_engulfed=player_engulfed,
    )
    if not threats:
        return None
    origin = monster.components[Position]
    threat_pos = ai_module._nearest_threat_position(threats, origin, rng)
    return ai_module._choose_flee_direction(
        world,
        game_map,
        monster,
        origin,
        threat_pos,
        rng,
        blocked_tiles=blocked_tiles,
    )


def _summon_abilities(entity: Entity) -> tuple[SummonAbility, ...]:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return ()
    return tuple(
        parsed for parsed in abilities.parsed if isinstance(parsed, SummonAbility)
    )


def _tile_free_for_summon(
    world: Registry,
    game_map: GameMap,
    x: int,
    y: int,
    *,
    mobility,
) -> bool:
    if not can_enter_tile(game_map, x, y, mobility):
        return False
    target = Position(x, y)
    return not any(world.Q.all_of(tags=[target, BlocksMovement]))


def _legal_adjacent_summon_tiles(
    world: Registry,
    game_map: GameMap,
    origin: Position,
    *,
    mobility,
) -> list[Position]:
    tiles: list[Position] = []
    for dx, dy in MOVEMENT_DIRECTIONS:
        dest = Position(origin.x + dx, origin.y + dy)
        if _tile_free_for_summon(world, game_map, dest.x, dest.y, mobility=mobility):
            tiles.append(dest)
    return tiles


def _summon_trigger_met(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    *,
    alignment: Alignment,
    player_engulfed: bool,
) -> bool:
    if alignment == Alignment.EVIL:
        return bool(
            ai_module._visible_primary_hostiles(
                monster,
                world,
                game_map,
                player,
                player_engulfed=player_engulfed,
            )
        )
    if alignment == Alignment.GOOD:
        return bool(ai_module._visible_good_evils(monster, world, game_map))
    if alignment == Alignment.NEUTRAL:
        return bool(ai_module._visible_evils(monster, world, game_map))
    return False


def try_summon_on_first_sight(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    message_log: MessageLog,
    rng: random.Random,
    *,
    alignment: Alignment,
    player_engulfed: bool = False,
    floor_depth: int = 1,
    difficulty_id: str | None = None,
) -> bool:
    """
    One-shot summon when alignment-appropriate hostiles enter LOS.
    Returns True when the summon ability fires (consumes the turn).
    """
    summons = _summon_abilities(monster)
    if not summons:
        return False

    state = monster.components.get(AbilityState)
    if state is None or state.summon_consumed:
        return False

    if not _summon_trigger_met(
        monster,
        world,
        game_map,
        player,
        alignment=alignment,
        player_engulfed=player_engulfed,
    ):
        return False

    state.summon_consumed = True
    origin = monster.components[Position]
    registry = load_entity_registry()

    for summon in summons:
        definition = registry.get(summon.entity_id)
        tiles = _legal_adjacent_summon_tiles(
            world,
            game_map,
            origin,
            mobility=definition.mobility,
        )
        rng.shuffle(tiles)
        for _ in range(summon.count):
            if not tiles:
                break
            dest = tiles.pop()
            spawn_entity_by_id(
                world,
                summon.entity_id,
                dest.x,
                dest.y,
                registry=registry,
                floor_depth=floor_depth,
                difficulty_id=difficulty_id,
            )

    if entity_visible_to_player(game_map, monster):
        message_log.add(
            messages.npc_summons_aid(entity_log_name(monster, sentence_start=True))
        )
    return True


def is_stunned_prey(entity: Entity) -> bool:
    fighter = entity.components.get(Fighter)
    if fighter is None or fighter.hp != 0:
        return False
    return Stunned in entity.tags or Player in entity.tags


def _chebyshev(a: Position, b: Position) -> int:
    return max(abs(a.x - b.x), abs(a.y - b.y))


def _can_smite_target(
    origin: Position,
    target: Entity,
    *,
    max_n: int,
    game_map: GameMap,
) -> bool:
    if is_stunned_prey(target):
        return False
    target_pos = target.components[Position]
    distance = _chebyshev(origin, target_pos)
    if distance < 2 or distance > max_n:
        return False
    return ai_module._has_los(game_map, origin, target_pos)


def pick_evil_smite_target(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    rng: random.Random,
    *,
    max_n: int,
    player_engulfed: bool = False,
) -> Entity | None:
    origin = monster.components[Position]
    primaries = ai_module._visible_primary_hostiles(
        monster,
        world,
        game_map,
        player,
        player_engulfed=player_engulfed,
    )
    in_range_primaries = [
        entity
        for entity in primaries
        if _can_smite_target(origin, entity, max_n=max_n, game_map=game_map)
    ]
    if in_range_primaries:
        return ai_module._pick_nearest_tied(origin, in_range_primaries, rng)

    neutrals = ai_module._visible_neutrals(monster, world, game_map)
    in_range_neutrals = [
        entity
        for entity in neutrals
        if _can_smite_target(origin, entity, max_n=max_n, game_map=game_map)
    ]
    if in_range_neutrals:
        return ai_module._pick_nearest_tied(origin, in_range_neutrals, rng)
    return None


def pick_good_smite_target(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    rng: random.Random,
    *,
    max_n: int,
) -> Entity | None:
    origin = monster.components[Position]
    evils = ai_module._visible_good_evils(monster, world, game_map)
    in_range = [
        entity
        for entity in evils
        if _can_smite_target(origin, entity, max_n=max_n, game_map=game_map)
    ]
    if not in_range:
        return None
    return ai_module._pick_nearest_tied(origin, in_range, rng)


def _engagement_target_for_chase(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    rng: random.Random,
    *,
    alignment: Alignment,
    max_n: int,
    player_engulfed: bool,
    entity_target: Entity | None,
) -> Entity | None:
    if entity_target is not None:
        return entity_target

    if alignment == Alignment.EVIL:
        return pick_evil_smite_target(
            monster,
            world,
            game_map,
            player,
            rng,
            max_n=max_n,
            player_engulfed=player_engulfed,
        )
    if alignment == Alignment.GOOD:
        return pick_good_smite_target(monster, world, game_map, rng, max_n=max_n)
    return None


def try_smite_engagement(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    message_log: MessageLog,
    rng: random.Random,
    *,
    alignment: Alignment,
    entity_target: Entity | None,
    player_engulfed: bool = False,
) -> bool:
    """
    Attempt a Smite-targeted shot when engagement rules allow.
    Returns True when a shot was attempted (hit or miss).
    """
    max_n = max_smite_range(monster)
    if max_n is None:
        return False

    origin = monster.components[Position]
    target = _engagement_target_for_chase(
        monster,
        world,
        game_map,
        player,
        rng,
        alignment=alignment,
        max_n=max_n,
        player_engulfed=player_engulfed,
        entity_target=entity_target,
    )
    if target is None:
        return False

    target_pos = target.components[Position]
    distance = _chebyshev(origin, target_pos)
    if distance == 1:
        return False
    if is_stunned_prey(target):
        return False
    if distance < 2 or distance > max_n:
        return False
    if not ai_module._has_los(game_map, origin, target_pos):
        return False

    perform_npc_smite_attack(
        monster,
        target,
        message_log,
        world=world,
        game_map=game_map,
        rng=rng,
    )
    return True


def _can_path_shoot_at(
    shooter: Entity,
    origin: Position,
    target: Entity,
    *,
    max_n: int,
    world: Registry,
    game_map: GameMap,
) -> bool:
    if is_stunned_prey(target):
        return False
    target_pos = target.components[Position]
    distance = _chebyshev(origin, target_pos)
    if distance < 2 or distance > max_n:
        return False
    if not ai_module._has_los(game_map, origin, target_pos):
        return False
    result = resolve_path_shot(world, game_map, shooter, target)
    return result.status is PathShotStatus.HIT


def pick_evil_path_target(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    rng: random.Random,
    *,
    max_n: int,
    player_engulfed: bool = False,
) -> Entity | None:
    origin = monster.components[Position]
    primaries = ai_module._visible_primary_hostiles(
        monster,
        world,
        game_map,
        player,
        player_engulfed=player_engulfed,
    )
    in_range_primaries = [
        entity
        for entity in primaries
        if _can_path_shoot_at(
            monster, origin, entity, max_n=max_n, world=world, game_map=game_map
        )
    ]
    if in_range_primaries:
        return ai_module._pick_nearest_tied(origin, in_range_primaries, rng)

    neutrals = ai_module._visible_neutrals(monster, world, game_map)
    in_range_neutrals = [
        entity
        for entity in neutrals
        if _can_path_shoot_at(
            monster, origin, entity, max_n=max_n, world=world, game_map=game_map
        )
    ]
    if in_range_neutrals:
        return ai_module._pick_nearest_tied(origin, in_range_neutrals, rng)
    return None


def pick_good_path_target(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    rng: random.Random,
    *,
    max_n: int,
) -> Entity | None:
    origin = monster.components[Position]
    evils = ai_module._visible_good_evils(monster, world, game_map)
    in_range = [
        entity
        for entity in evils
        if _can_path_shoot_at(
            monster, origin, entity, max_n=max_n, world=world, game_map=game_map
        )
    ]
    if not in_range:
        return None
    return ai_module._pick_nearest_tied(origin, in_range, rng)


def _engagement_target_for_path_chase(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    rng: random.Random,
    *,
    alignment: Alignment,
    max_n: int,
    player_engulfed: bool,
    entity_target: Entity | None,
) -> Entity | None:
    origin = monster.components[Position]
    if entity_target is not None and _can_path_shoot_at(
        monster,
        origin,
        entity_target,
        max_n=max_n,
        world=world,
        game_map=game_map,
    ):
        return entity_target

    if alignment == Alignment.EVIL:
        return pick_evil_path_target(
            monster,
            world,
            game_map,
            player,
            rng,
            max_n=max_n,
            player_engulfed=player_engulfed,
        )
    if alignment == Alignment.GOOD:
        return pick_good_path_target(monster, world, game_map, rng, max_n=max_n)
    return None


def try_path_engagement(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    message_log: MessageLog,
    rng: random.Random,
    *,
    alignment: Alignment,
    entity_target: Entity | None,
    player_engulfed: bool = False,
) -> bool:
    """
    Attempt a Path-targeted shot when engagement rules allow.
    Returns True when a shot was attempted (hit or miss).
    """
    max_n = max_path_range(monster)
    if max_n is None:
        return False

    origin = monster.components[Position]
    target = _engagement_target_for_path_chase(
        monster,
        world,
        game_map,
        player,
        rng,
        alignment=alignment,
        max_n=max_n,
        player_engulfed=player_engulfed,
        entity_target=entity_target,
    )
    if target is None:
        return False

    target_pos = target.components[Position]
    if has_hands(monster) and _closed_door_toward_target(game_map, origin, target_pos):
        return False
    distance = _chebyshev(origin, target_pos)
    if distance == 1:
        return False
    if is_stunned_prey(target):
        return False
    if distance < 2 or distance > max_n:
        return False
    if not ai_module._has_los(game_map, origin, target_pos):
        return False

    return perform_npc_path_attack(
        monster,
        target,
        message_log,
        world=world,
        game_map=game_map,
        rng=rng,
    )


def choose_path_ranged_move_direction(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    rng: random.Random,
    *,
    alignment: Alignment,
    entity_target: Entity | None,
    player_engulfed: bool,
    blocked: frozenset[Position],
    monster_pos: Position,
) -> tuple[int, int] | None:
    """Path (RangeN) reposition when not shooting this turn.

    Evil RangeN units **stand their ground** once the quarry is within max path
    range (no kiting). They only close distance when the quarry is too far to
    shoot, or when the quarry is **stunned** (must approach for adjacent vore).
    Coward / Supercoward flee is handled earlier in the visit pipeline.
    """
    from src.systems.ai.chase import _choose_chase_direction
    from src.systems.ai.movement import _choose_flee_direction

    if is_stationary(monster):
        return None

    max_n = max_path_range(monster)
    if max_n is None:
        return None

    if alignment == Alignment.EVIL:
        quarry = entity_target
        if quarry is None and not player_engulfed:
            player_pos = player.components[Position]
            if ai_module._has_los(game_map, monster_pos, player_pos):
                quarry = player
        if quarry is None:
            return None
        quarry_pos = quarry.components[Position]
        if has_hands(monster) and _closed_door_toward_target(
            game_map, monster_pos, quarry_pos
        ):
            return None
        distance = _chebyshev(monster_pos, quarry_pos)

        # Stunned prey: always close for adjacent vore (never kite or hold far).
        if is_stunned_prey(quarry):
            if distance <= 1:
                return None
            return _choose_chase_direction(
                world,
                game_map,
                monster,
                monster_pos,
                quarry_pos,
                blocked_tiles=blocked,
            )

        # Too far for a path shot: step into range.
        if distance > max_n:
            return _choose_chase_direction(
                world,
                game_map,
                monster,
                monster_pos,
                quarry_pos,
                blocked_tiles=blocked,
            )

        # In range (or closer): hold — do not kite away from the player.
        return None

    if alignment == Alignment.GOOD:
        player_pos = player.components[Position]
        if not ai_module._has_los(game_map, monster_pos, player_pos):
            return None
        distance_to_player = _chebyshev(monster_pos, player_pos)
        if distance_to_player > max_n:
            return None
        if distance_to_player > 2:
            return _choose_chase_direction(
                world,
                game_map,
                monster,
                monster_pos,
                player_pos,
                blocked_tiles=blocked,
            )
        if distance_to_player < 1:
            return _choose_flee_direction(
                world,
                game_map,
                monster,
                monster_pos,
                player_pos,
                rng,
                blocked_tiles=blocked,
            )
        if entity_target is not None:
            return _choose_chase_direction(
                world,
                game_map,
                monster,
                monster_pos,
                entity_target.components[Position],
                blocked_tiles=blocked,
            )
        return None

    return None