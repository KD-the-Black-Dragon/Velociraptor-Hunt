from __future__ import annotations

import random
from enum import Enum, auto

import attrs
from tcod.ecs import Entity, Registry

from src import messages
from src.components import (
    AI,
    Alignment,
    BlocksMovement,
    DigestionStrikes,
    Engulfed,
    Fighter,
    NPCAlignment,
    Position,
    Predator,
    VoreCapable,
    VoreMercy,
    VoreNarratives,
)
from src.map_gen import Tile, can_enter_tile
from src.systems.combat import apply_struggle_damage
from src.data.ally_content import format_rescue_gratitude, pick_rescue_gratitude_line
from src.data.narrative_index import get_narrative_index
from src.data.rescue_gratitude_loader import get_rescue_gratitude_registry
from src.systems.naming import entity_display_name, entity_log_name, entity_type_id
from src.text import enforce_sentence_capitalization
from src.systems.movement import MOVEMENT_DIRECTIONS, entity_mobility
from src.constants import (
    DEFAULT_VORE_CONTENT_PREFS,
    VORE_ENABLED,
    VORE_ESCAPE_BASE,
    VORE_ESCAPE_PER_FAIL,
    VORE_HIT_MAX,
    VORE_HIT_MIN,
    VORE_HP_THRESHOLD,
    VORE_STRUGGLE_DAMAGE,
    VoreContentPreferences,
)
from src.components import Player
from src.run_stats import RunStats
from src.events import (
    fire_entity_defeated,
    fire_player_engulfed,
    fire_player_escaped_engulf,
    fire_vore_attempt,
)
from src.map_gen import GameMap
from src.message_log import MessageCategory, MessageLog
from src.systems.fov import can_see, entity_visible_to_player
from src.vore_npc_content import NPC_VORE_HIT_POOL, NPC_VORE_MISS_POOL


class VoreModalSegment(Enum):
    NONE = auto()
    ATTEMPT = auto()
    SUCCESS = auto()


@attrs.define
class VoreModalState:
    segment: VoreModalSegment = VoreModalSegment.NONE
    phases: list[str] = attrs.field(factory=list)
    phase_index: int = 0
    predator: Entity | None = None
    predator_name: str = ""
    hit: bool = False
    narrative_type: str = ""
    success_phases: list[str] = attrs.field(factory=list)
    resume_monster_index: int = 0
    pending_monsters: list[Entity] = attrs.field(factory=list)

    @property
    def active(self) -> bool:
        return self.segment is not VoreModalSegment.NONE

    def current_line(self) -> str:
        if not self.phases:
            return ""
        return self.phases[self.phase_index]

    def open_attempt(
        self,
        predator: Entity,
        name: str,
        narrative_type: str,
        attempt_phases: list[str],
        hit: bool,
        pending: list[Entity],
        index: int,
        *,
        success_phases: list[str] | None = None,
    ) -> None:
        self.segment = VoreModalSegment.ATTEMPT
        self.predator = predator
        self.predator_name = name
        self.narrative_type = narrative_type
        self.phases = list(attempt_phases)
        self.success_phases = list(success_phases or [])
        self.phase_index = 0
        self.hit = hit
        self.pending_monsters = pending
        self.resume_monster_index = index

    def reset(self) -> None:
        self.segment = VoreModalSegment.NONE
        self.phases = []
        self.phase_index = 0
        self.predator = None
        self.predator_name = ""
        self.hit = False
        self.narrative_type = ""
        self.success_phases = []
        self.resume_monster_index = 0
        self.pending_monsters = []


def hp_fraction(fighter: Fighter) -> float:
    if fighter.max_hp <= 0:
        return 0.0
    return max(0.0, min(1.0, fighter.hp / fighter.max_hp))


def is_vore_eligible(fighter: Fighter) -> bool:
    return hp_fraction(fighter) <= VORE_HP_THRESHOLD


def vore_decision_chance(hp_frac: float) -> float:
    if hp_frac > VORE_HP_THRESHOLD:
        return 0.0
    if hp_frac <= 0.0:
        return 1.0
    return (VORE_HP_THRESHOLD - hp_frac) / VORE_HP_THRESHOLD


def vore_hit_chance(hp_frac: float) -> float:
    if hp_frac > VORE_HP_THRESHOLD:
        return 0.0
    if hp_frac <= 0.0:
        return 1.0
    t = (VORE_HP_THRESHOLD - hp_frac) / VORE_HP_THRESHOLD
    return VORE_HIT_MIN + t * (VORE_HIT_MAX - VORE_HIT_MIN)


def enabled_narrative_types(
    monster_types: tuple[str, ...],
    prefs: VoreContentPreferences,
) -> list[str]:
    return [t for t in monster_types if prefs.is_enabled(t)]


def pick_narrative_type(
    monster_types: tuple[str, ...],
    prefs: VoreContentPreferences,
    rng: random.Random,
) -> str | None:
    pool = enabled_narrative_types(monster_types, prefs)
    if not pool:
        return None
    return rng.choice(pool)


def get_narrative_phases(entity_id: str, narrative_type: str, segment: str) -> list[str]:
    """Lookup narrative phases from data index keyed by entity id."""
    return list(
        get_narrative_index().narrative_phases(entity_id, narrative_type, segment)
    )


def pick_vore_narrative_variant(
    monster: Entity,
    narrative_type: str,
    rng: random.Random,
) -> tuple[list[str], list[str]] | None:
    """Return (attempt phases, success phases) from data, or None if unavailable."""
    variant = get_narrative_index().pick_vore_variant(
        entity_type_id(monster),
        narrative_type,
        rng,
    )
    if variant is None:
        return None
    return list(variant.attempt), list(variant.success)


def monster_narrative_types(monster: Entity) -> tuple[str, ...]:
    narratives = monster.components.get(VoreNarratives)
    return narratives.types if narratives is not None else ()


def chebyshev_distance(a: Position, b: Position) -> int:
    return max(abs(a.x - b.x), abs(a.y - b.y))


def is_adjacent(a: Position, b: Position) -> bool:
    return chebyshev_distance(a, b) == 1


def _is_npc_vore_prey(prey: Entity) -> bool:
    alignment = prey.components.get(NPCAlignment)
    if alignment is None:
        return False
    return alignment.alignment in (Alignment.GOOD, Alignment.NEUTRAL)


def _vore_base_eligible(
    monster: Entity,
    prey: Entity,
    game_map: GameMap,
    *,
    prefs: VoreContentPreferences = DEFAULT_VORE_CONTENT_PREFS,
) -> bool:
    if not VORE_ENABLED:
        return False
    if VoreCapable not in monster.tags:
        return False
    predator_alignment = monster.components.get(NPCAlignment)
    if predator_alignment is not None and predator_alignment.alignment in (
        Alignment.GOOD,
        Alignment.NEUTRAL,
    ):
        return False
    if monster.components.get(AI) is None or monster.components.get(Position) is None:
        return False
    if Engulfed in prey.tags:
        return False
    if VoreMercy in prey.tags:
        return False
    if Player not in prey.tags and not _is_npc_vore_prey(prey):
        return False
    prey_fighter = prey.components.get(Fighter)
    if prey_fighter is None or not is_vore_eligible(prey_fighter):
        return False
    monster_pos = monster.components[Position]
    prey_pos = prey.components[Position]
    if not can_see(game_map, monster_pos.x, monster_pos.y, prey_pos.x, prey_pos.y):
        return False
    types = monster_narrative_types(monster)
    if not enabled_narrative_types(types, prefs):
        return False
    return True


def _vore_decision_committed(
    monster: Entity,
    prey_fighter: Fighter,
    rng: random.Random,
) -> bool:
    from src.systems.abilities import has_prefer_vore

    if has_prefer_vore(monster):
        return True
    frac = hp_fraction(prey_fighter)
    return rng.random() < vore_decision_chance(frac)


def should_attempt_vore(
    monster: Entity,
    prey: Entity,
    game_map: GameMap,
    rng: random.Random,
    *,
    prefs: VoreContentPreferences = DEFAULT_VORE_CONTENT_PREFS,
) -> bool:
    if not _vore_base_eligible(monster, prey, game_map, prefs=prefs):
        return False
    monster_pos = monster.components[Position]
    prey_pos = prey.components[Position]
    if not is_adjacent(monster_pos, prey_pos):
        return False
    prey_fighter = prey.components[Fighter]
    return _vore_decision_committed(monster, prey_fighter, rng)


def should_attempt_ranged_vore(
    monster: Entity,
    prey: Entity,
    game_map: GameMap,
    rng: random.Random,
    *,
    max_n: int,
    prefs: VoreContentPreferences = DEFAULT_VORE_CONTENT_PREFS,
) -> bool:
    if not _vore_base_eligible(monster, prey, game_map, prefs=prefs):
        return False
    monster_pos = monster.components[Position]
    prey_pos = prey.components[Position]
    distance = chebyshev_distance(monster_pos, prey_pos)
    if distance < 2 or distance > max_n:
        return False
    prey_fighter = prey.components[Fighter]
    return _vore_decision_committed(monster, prey_fighter, rng)


def resolve_vore_hit(prey: Entity, rng: random.Random) -> bool:
    fighter = prey.components.get(Fighter)
    if fighter is None:
        return False
    return rng.random() < vore_hit_chance(hp_fraction(fighter))


def format_npc_vore_line(template: str, predator: Entity, prey: Entity) -> str:
    from src.text import format_narrative_template

    predator_name = entity_log_name(predator)
    prey_name = entity_log_name(prey)
    return enforce_sentence_capitalization(
        format_narrative_template(template, predator=predator_name, prey=prey_name)
    )


def format_player_vore_phase(template: str, predator: Entity) -> str:
    """Format NPC→player vore modal phase; only ``{predator}`` is substituted."""
    from src.text import format_narrative_template

    predator_name = entity_log_name(predator)
    return enforce_sentence_capitalization(
        format_narrative_template(template, predator=predator_name)
    )


def pick_visible_npc_vore_message(
    predator: Entity,
    prey: Entity,
    narrative_type: str,
    *,
    hit: bool,
    rng: random.Random,
) -> str | None:
    """On-screen NPC vore log: entity data first, then global pool fallback."""
    entity_id = entity_type_id(predator)
    index = get_narrative_index()
    if hit:
        templates = index.npc_vore_hit_lines(entity_id, narrative_type)
        if not templates:
            templates = NPC_VORE_HIT_POOL.get(narrative_type, ())
    else:
        templates = index.npc_vore_miss_lines(entity_id, narrative_type)
        if not templates:
            templates = NPC_VORE_MISS_POOL.get(narrative_type, ())
    if not templates:
        return None
    return format_npc_vore_line(rng.choice(templates), predator, prey)


def _vore_npc_prey_in_range(
    predator: Entity,
    world: Registry,
    game_map: GameMap,
    *,
    min_distance: int,
    max_distance: int,
) -> list[Entity]:
    predator_pos = predator.components[Position]
    candidates: list[Entity] = []
    for entity in world.Q.all_of(components=[Fighter, NPCAlignment, Position, AI]):
        if Player in entity.tags:
            continue
        if Engulfed in entity.tags:
            continue
        if not _is_npc_vore_prey(entity):
            continue
        prey_pos = entity.components[Position]
        distance = chebyshev_distance(predator_pos, prey_pos)
        if distance < min_distance or distance > max_distance:
            continue
        if not can_see(
            game_map,
            predator_pos.x,
            predator_pos.y,
            prey_pos.x,
            prey_pos.y,
        ):
            continue
        if not is_vore_eligible(entity.components[Fighter]):
            continue
        candidates.append(entity)
    return candidates


def adjacent_vore_npc_prey(
    predator: Entity,
    world: Registry,
    game_map: GameMap,
) -> list[Entity]:
    """Adjacent good/neutral NPCs weakened enough for vore."""
    return _vore_npc_prey_in_range(
        predator, world, game_map, min_distance=1, max_distance=1
    )


def ranged_vore_npc_prey(
    predator: Entity,
    world: Registry,
    game_map: GameMap,
    max_n: int,
) -> list[Entity]:
    """Good/neutral NPC prey at Chebyshev distance [2, max_n] with LOS."""
    return _vore_npc_prey_in_range(
        predator, world, game_map, min_distance=2, max_distance=max_n
    )


def try_resolve_npc_vore(
    predator: Entity,
    world: Registry,
    game_map: GameMap,
    message_log: MessageLog,
    rng: random.Random,
    *,
    prefs: VoreContentPreferences = DEFAULT_VORE_CONTENT_PREFS,
) -> bool:
    """
    Log-only NPC vore attempt against adjacent good/neutral prey.
    Returns True when the predator's turn was spent on an attempt.
    """
    if predator.components.get(Predator) is not None:
        return False
    prey_options = adjacent_vore_npc_prey(predator, world, game_map)
    if not prey_options:
        return False
    prey = rng.choice(prey_options)
    if not should_attempt_vore(predator, prey, game_map, rng, prefs=prefs):
        return False
    narrative_type = pick_narrative_type(monster_narrative_types(predator), prefs, rng)
    if narrative_type is None:
        return False
    hit = resolve_vore_hit(prey, rng)
    log_visible = entity_visible_to_player(game_map, predator) or entity_visible_to_player(
        game_map, prey
    )
    if log_visible:
        line = pick_visible_npc_vore_message(
            predator,
            prey,
            narrative_type,
            hit=hit,
            rng=rng,
        )
        if line is not None:
            # Witnessed successful swallow: caution yellow by default (not miss).
            category = (
                MessageCategory.CAUTION if hit else MessageCategory.ROUTINE
            )
            message_log.add(line, category=category)
    elif hit:
        template = get_narrative_index().pick_offscreen_vore_line(
            entity_type_id(predator),
            narrative_type,
            rng,
        )
        if template is not None:
            # Offscreen success: heard only — keep routine default.
            message_log.add(format_npc_vore_line(template, predator, prey))
    if hit:
        engulf_npc(world, prey, predator, narrative_type=narrative_type)
    fire_vore_attempt(predator, prey, hit=hit)
    return True


def try_resolve_npc_ranged_vore(
    predator: Entity,
    world: Registry,
    game_map: GameMap,
    message_log: MessageLog,
    rng: random.Random,
    *,
    prefs: VoreContentPreferences = DEFAULT_VORE_CONTENT_PREFS,
) -> bool:
    """
    Log-only NPC vore attempt against ranged good/neutral prey.
    Returns True when the predator's turn was spent on an attempt.
    """
    from src.systems.abilities import max_ranged_vore_range

    max_n = max_ranged_vore_range(predator)
    if max_n is None:
        return False
    if predator.components.get(Predator) is not None:
        return False
    prey_options = ranged_vore_npc_prey(predator, world, game_map, max_n)
    if not prey_options:
        return False
    prey = rng.choice(prey_options)
    if not should_attempt_ranged_vore(
        predator, prey, game_map, rng, max_n=max_n, prefs=prefs
    ):
        return False
    narrative_type = pick_narrative_type(monster_narrative_types(predator), prefs, rng)
    if narrative_type is None:
        return False
    hit = resolve_vore_hit(prey, rng)
    log_visible = entity_visible_to_player(game_map, predator) or entity_visible_to_player(
        game_map, prey
    )
    if log_visible:
        line = pick_visible_npc_vore_message(
            predator,
            prey,
            narrative_type,
            hit=hit,
            rng=rng,
        )
        if line is not None:
            category = (
                MessageCategory.CAUTION if hit else MessageCategory.ROUTINE
            )
            message_log.add(line, category=category)
    elif hit:
        template = get_narrative_index().pick_offscreen_vore_line(
            entity_type_id(predator),
            narrative_type,
            rng,
        )
        if template is not None:
            message_log.add(format_npc_vore_line(template, predator, prey))
    if hit:
        engulf_npc(world, prey, predator, narrative_type=narrative_type)
    fire_vore_attempt(predator, prey, hit=hit)
    return True


def try_open_vore_modal(
    monster: Entity,
    player: Entity,
    game_map: GameMap,
    modal: VoreModalState,
    pending_monsters: list[Entity],
    monster_index: int,
    rng: random.Random,
    *,
    prefs: VoreContentPreferences = DEFAULT_VORE_CONTENT_PREFS,
) -> bool:
    """Open a vore narrative modal if eligible. Returns True when the predator's turn was spent."""
    if monster.components.get(Predator) is not None:
        return False
    if not should_attempt_vore(monster, player, game_map, rng, prefs=prefs):
        return False
    name = entity_display_name(monster)
    narrative_type = pick_narrative_type(monster_narrative_types(monster), prefs, rng)
    if narrative_type is None:
        return False
    picked = pick_vore_narrative_variant(monster, narrative_type, rng)
    if picked is None:
        return False
    attempt_phases, success_phases = picked
    if not attempt_phases:
        return False
    # Substitute {predator} (and leave unknown keys literal) before display.
    attempt_phases = [format_player_vore_phase(phase, monster) for phase in attempt_phases]
    success_phases = [format_player_vore_phase(phase, monster) for phase in success_phases]
    hit = resolve_vore_hit(player, rng)
    modal.open_attempt(
        monster,
        name,
        narrative_type,
        attempt_phases,
        hit,
        pending_monsters,
        monster_index,
        success_phases=success_phases,
    )
    return True


def try_open_ranged_vore_modal(
    monster: Entity,
    player: Entity,
    game_map: GameMap,
    modal: VoreModalState,
    pending_monsters: list[Entity],
    monster_index: int,
    rng: random.Random,
    *,
    prefs: VoreContentPreferences = DEFAULT_VORE_CONTENT_PREFS,
) -> bool:
    """Open a vore narrative modal for ranged prey when eligible."""
    from src.systems.abilities import max_ranged_vore_range

    max_n = max_ranged_vore_range(monster)
    if max_n is None:
        return False
    if monster.components.get(Predator) is not None:
        return False
    if not should_attempt_ranged_vore(
        monster, player, game_map, rng, max_n=max_n, prefs=prefs
    ):
        return False
    name = entity_display_name(monster)
    narrative_type = pick_narrative_type(monster_narrative_types(monster), prefs, rng)
    if narrative_type is None:
        return False
    picked = pick_vore_narrative_variant(monster, narrative_type, rng)
    if picked is None:
        return False
    attempt_phases, success_phases = picked
    if not attempt_phases:
        return False
    attempt_phases = [format_player_vore_phase(phase, monster) for phase in attempt_phases]
    success_phases = [format_player_vore_phase(phase, monster) for phase in success_phases]
    hit = resolve_vore_hit(player, rng)
    modal.open_attempt(
        monster,
        name,
        narrative_type,
        attempt_phases,
        hit,
        pending_monsters,
        monster_index,
        success_phases=success_phases,
    )
    return True


def _is_walkable_tile(game_map: GameMap, x: int, y: int) -> bool:
    return game_map.in_bounds(x, y) and game_map.is_walkable(x, y)


def _blocks_movement_at(
    world: Registry,
    x: int,
    y: int,
    *,
    exclude: set[Entity],
) -> bool:
    target = Position(x, y)
    for entity in world.Q.all_of(tags=[target, BlocksMovement]):
        if entity not in exclude:
            return True
    return False


def _is_valid_escape_tile(
    game_map: GameMap,
    world: Registry,
    pos: Position,
    *,
    exclude: set[Entity],
    prey: Entity | None = None,
) -> bool:
    if not game_map.in_bounds(pos.x, pos.y):
        return False
    if prey is not None:
        if not can_enter_tile(game_map, pos.x, pos.y, entity_mobility(prey)):
            return False
    elif not _is_walkable_tile(game_map, pos.x, pos.y):
        return False
    return not _blocks_movement_at(world, pos.x, pos.y, exclude=exclude)


def _tile_in_direction(origin: Position, direction: tuple[int, int] | None) -> Position | None:
    if direction is None:
        return None
    return origin + direction


def find_adjacent_free_tile(
    game_map: GameMap,
    world: Registry,
    origin: Position,
    *,
    exclude: set[Entity],
    rng: random.Random,
    prey: Entity | None = None,
) -> Position | None:
    candidates: list[Position] = []
    for direction in MOVEMENT_DIRECTIONS:
        dest = origin + direction
        if _is_valid_escape_tile(
            game_map, world, dest, exclude=exclude, prey=prey
        ):
            candidates.append(dest)
    if not candidates:
        return None
    return rng.choice(candidates)


def find_nearest_free_tile(
    game_map: GameMap,
    world: Registry,
    origin: Position,
    *,
    exclude: set[Entity],
    rng: random.Random,
    max_radius: int = 20,
    prey: Entity | None = None,
) -> Position | None:
    for radius in range(1, max_radius + 1):
        ring: list[Position] = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if max(abs(dx), abs(dy)) != radius:
                    continue
                dest = Position(origin.x + dx, origin.y + dy)
                if _is_valid_escape_tile(
                    game_map, world, dest, exclude=exclude, prey=prey
                ):
                    ring.append(dest)
        if ring:
            return rng.choice(ring)
    return None


def pick_random_direction_tile(
    game_map: GameMap,
    world: Registry,
    origin: Position,
    *,
    rng: random.Random,
    prey: Entity | None = None,
    exclude: set[Entity] | None = None,
) -> Position | None:
    blocked = exclude if exclude is not None else set()
    directions = list(MOVEMENT_DIRECTIONS)
    rng.shuffle(directions)
    for direction in directions:
        dest = origin + direction
        if _is_valid_escape_tile(
            game_map, world, dest, exclude=blocked, prey=prey
        ):
            return dest
    return None


def teleport_to_random_floor_tile(
    entity: Entity,
    game_map: GameMap,
    world: Registry,
    rng: random.Random,
) -> None:
    floors: list[tuple[int, int]] = []
    for y in range(game_map.height):
        for x in range(game_map.width):
            if game_map.tiles[y, x] != Tile.FLOOR:
                continue
            if _blocks_movement_at(world, x, y, exclude={entity}):
                continue
            floors.append((x, y))
    if not floors:
        return
    x, y = rng.choice(floors)
    entity.components[Position] = Position(x, y)


def engulf_npc(
    world: Registry,
    prey: Entity,
    predator: Entity,
    *,
    narrative_type: str,
) -> None:
    """Headless engulf for NPC prey: co-located, no modal or HUD changes."""
    prey.tags.add(Engulfed)
    prey.tags.discard(BlocksMovement)
    predator.components[Predator] = Predator(prey=prey, narrative_type=narrative_type)
    predator_pos = predator.components[Position]
    prey.components[Position] = predator_pos


def engulf_player(
    world: Registry,
    player: Entity,
    predator: Entity,
    message_log: MessageLog,
    *,
    narrative_type: str,
) -> None:
    engulf_npc(world, player, predator, narrative_type=narrative_type)
    fire_player_engulfed(player, predator)


def sync_engulfed_position(world: Registry, predator: Entity) -> None:
    predator_state = predator.components.get(Predator)
    if predator_state is None:
        return
    prey = predator_state.prey
    if Engulfed not in prey.tags:
        return
    predator_pos = predator.components[Position]
    prey.components[Position] = predator_pos


def release_prey_if_defeated_predator(
    world: Registry,
    predator: Entity,
    game_map: GameMap,
    message_log: MessageLog,
    *,
    rng: random.Random | None = None,
    rescuer: Entity | None = None,
) -> None:
    """If a holding predator is defeated, eject prey before the entity is cleared."""
    predator_state = predator.components.get(Predator)
    if predator_state is None:
        return
    prey = predator_state.prey
    if Engulfed not in prey.tags:
        return
    if Player in prey.tags:
        release_engulfed(
            world,
            prey,
            predator,
            game_map,
            message_log,
            escape_direction=None,
            rng=rng,
        )
    else:
        release_npc_engulfed(
            world,
            prey,
            predator,
            game_map,
            message_log,
            rng=rng,
            rescuer=rescuer,
        )


def _is_good_prey(prey: Entity) -> bool:
    alignment = prey.components.get(NPCAlignment)
    return alignment is not None and alignment.alignment == Alignment.GOOD


def release_npc_engulfed(
    world: Registry,
    prey: Entity,
    predator: Entity,
    game_map: GameMap,
    message_log: MessageLog,
    *,
    rng: random.Random | None = None,
    rescuer: Entity | None = None,
) -> None:
    """Eject an engulfed NPC prey when its predator is defeated."""
    rng = rng or random.Random()
    prey.tags.discard(Engulfed)
    predator_state = predator.components.get(Predator)
    if predator_state is not None:
        predator_state.failed_struggles = 0
    predator.components.pop(Predator, None)
    prey.tags.add(BlocksMovement)

    predator_pos = predator.components[Position]
    exclude = {prey, predator}
    dest = find_adjacent_free_tile(
        game_map, world, predator_pos, exclude=exclude, rng=rng, prey=prey
    )
    if dest is None:
        dest = find_nearest_free_tile(
            game_map, world, predator_pos, exclude=exclude, rng=rng, prey=prey
        )
    if dest is not None:
        prey.components[Position] = dest

    prey.tags.add(VoreMercy)
    prey.components.pop(DigestionStrikes, None)

    if entity_visible_to_player(game_map, prey) or entity_visible_to_player(
        game_map, predator
    ):
        prey_name = entity_log_name(prey, sentence_start=True)
        predator_name = entity_log_name(predator)
        message_log.add(
            messages.npc_freed_from_predator(prey_name, predator_name),
            category=MessageCategory.POSITIVE,
        )
        if (
            rescuer is not None
            and Player in rescuer.tags
            and _is_good_prey(prey)
        ):
            template = pick_rescue_gratitude_line(get_rescue_gratitude_registry(), rng)
            message_log.add(
                format_rescue_gratitude(prey, template),
                category=MessageCategory.POSITIVE,
            )


def release_engulfed(
    world: Registry,
    player: Entity,
    predator: Entity,
    game_map: GameMap,
    message_log: MessageLog,
    *,
    escape_direction: tuple[int, int] | None = None,
    rng: random.Random | None = None,
) -> None:
    rng = rng or random.Random()
    player.tags.discard(Engulfed)
    predator_state = predator.components.get(Predator)
    if predator_state is not None:
        predator_state.failed_struggles = 0
    predator.components.pop(Predator, None)
    player.tags.add(BlocksMovement)

    predator_pos = predator.components[Position]
    exclude = {player, predator}
    dest = _tile_in_direction(predator_pos, escape_direction)
    if dest is None or not _is_valid_escape_tile(
        game_map, world, dest, exclude=exclude, prey=player
    ):
        picked = find_adjacent_free_tile(
            game_map,
            world,
            predator_pos,
            exclude=exclude,
            rng=rng,
            prey=player,
        )
        dest = picked
    if dest is None:
        picked = pick_random_direction_tile(
            game_map,
            world,
            predator_pos,
            rng=rng,
            prey=player,
            exclude=exclude,
        )
        if picked is not None:
            target = Position(picked.x, picked.y)
            for occupant in world.Q.all_of(tags=[target], components=[Position]):
                if occupant is player or occupant is predator:
                    continue
                teleport_to_random_floor_tile(occupant, game_map, world, rng)
            dest = picked
    if dest is None:
        dest = find_nearest_free_tile(
            game_map,
            world,
            predator_pos,
            exclude=exclude,
            rng=rng,
            prey=player,
        )
    if dest is not None:
        player.components[Position] = dest

    player.components.pop(DigestionStrikes, None)
    player.tags.add(VoreMercy)
    message_log.add(
        messages.vore_escaped(entity_log_name(predator)),
        category=MessageCategory.POSITIVE,
    )
    fire_player_escaped_engulf(player, predator)


def find_predator_holding_prey(world: Registry, prey: Entity) -> Entity | None:
    for entity in world.Q.all_of(components=[Predator]):
        if entity.components[Predator].prey is prey:
            return entity
    return None


def escape_chance_for_predator(predator: Entity) -> float:
    predator_state = predator.components.get(Predator)
    if predator_state is None:
        return VORE_ESCAPE_BASE
    bonus = predator_state.failed_struggles * VORE_ESCAPE_PER_FAIL
    return min(1.0, VORE_ESCAPE_BASE + bonus)


def try_struggle(
    world: Registry,
    game_map: GameMap,
    player: Entity,
    direction: tuple[int, int],
    message_log: MessageLog,
    rng: random.Random,
    *,
    run_stats: RunStats | None = None,
) -> bool:
    """Struggle while engulfed. Always consumes a player turn when invoked."""
    predator = find_predator_holding_prey(world, player)
    if predator is None:
        return True

    message_log.add(
        messages.pick_struggle_message(rng),
        category=MessageCategory.CAUTION,
    )
    apply_struggle_damage(predator, VORE_STRUGGLE_DAMAGE)
    fighter = predator.components.get(Fighter)
    if fighter is not None and fighter.hp <= 0:
        release_engulfed(
            world,
            player,
            predator,
            game_map,
            message_log,
            escape_direction=direction,
            rng=rng,
        )
        defeated = entity_log_name(predator, sentence_start=True)
        message_log.add(messages.target_defeated(defeated))
        fire_entity_defeated(predator)
        if run_stats is not None:
            run_stats.record_monster_defeated(defeated_entity=predator)
        predator.clear()
        return True

    predator_state = predator.components.get(Predator)
    chance = escape_chance_for_predator(predator)
    if rng.random() < chance:
        release_engulfed(
            world,
            player,
            predator,
            game_map,
            message_log,
            escape_direction=direction,
            rng=rng,
        )
    elif predator_state is not None:
        predator_state.failed_struggles += 1
    return True


def debug_weaken_all_monsters(world: Registry, message_log: MessageLog) -> None:
    """Set every monster Fighter HP to 1 (F2 debug helper)."""
    for entity in world.Q.all_of(components=[AI, Fighter]):
        fighter = entity.components[Fighter]
        fighter.hp = 1
    message_log.add(messages.debug_all_monsters_weakened())