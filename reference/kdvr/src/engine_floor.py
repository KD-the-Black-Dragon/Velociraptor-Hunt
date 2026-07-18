"""Floor lifecycle for GameEngine: new game, descend, spawn, prefetch.

PR4 extract + PR7 facade cleanup. Call via ``GameEngine`` methods.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from tcod.ecs import Entity, Registry

from src import messages
from src.components import (
    BlocksMovement,
    EquipState,
    Fighter,
    Inventory,
    Mobility,
    MobilityType,
    Player,
    PlayerEffects,
    PlayerProgression,
    Position,
    Renderable,
)
from src.constants import (
    FLOOR_DEPTH_MAX,
    FLOOR_DEPTH_START,
    MAP_HEIGHT,
    MAP_WIDTH,
    MAX_GEN_ATTEMPTS,
    MAX_ROOMS,
    PLAYER_AC,
    PLAYER_ACCURACY,
    PLAYER_EVADE,
    PLAYER_MAX_DAMAGE,
    PLAYER_MAX_HP,
    PLAYER_MIN_DAMAGE,
    ROOM_MAX_SIZE,
    ROOM_MIN_SIZE,
)
from src.data.entity_loader import load_entity_registry
from src.debug.session_log import session_log
from src.debug_log import debug_print
from src.floor_prefetch import PrefetchParams
from src.map_gen import GameMap, generate_dungeon, water_positions
from src.spawn import good_aligned_weight_at_depth, spawn_floor_population, spawn_items
from src.systems.come_here import clear_all_come_here
from src.systems.descent import (
    clear_floor_entities,
    collect_descent_followers,
    place_descent_followers,
)
from src.systems.floor_runes import RunePlacementError, spawn_floor_rune
from src.systems.inventory import apply_starter_loadout
from src.systems.macguffins import spawn_macguffins

if TYPE_CHECKING:
    from src.engine import GameEngine


def new_game(
    engine: GameEngine,
    *,
    seed: int | None = None,
    log_session_milestones: bool = True,
    start_depth: int = 1,
    level_warped: bool = False,
) -> None:
    """Reset the ECS world and generate a fresh dungeon."""
    engine.level_warped = level_warped
    engine.depth_jump_start_depth = start_depth if start_depth > 1 else None
    engine.initialize_floor(
        seed=seed,
        mode="new",
        start_depth=start_depth,
        log_session_milestones=log_session_milestones,
    )
    engine.vore_modal.reset()
    engine.digestion_modal.reset()
    engine.game_over.reset()
    engine.run_stats.reset()
    engine.skipped_this_phase.clear()
    engine.examine_state.reset()
    engine.ground_pickup_modal.reset()
    engine.inventory_modal.reset()
    engine.macguffin_discovery.reset()
    engine.macguffin_victory_confirm.reset()
    engine.close_door_pending = False
    engine.last_come_here_turn = -1
    engine._debug_omniscient_vision = False
    engine.log_overlay.close()
    engine.help_overlay.close()
    engine._end_rest_session()
    engine._end_autoexplore_session()
    engine.message_log.clear()
    engine.message_log.add(messages.welcome())
    engine._update_fov()


def descend_floor(engine: GameEngine) -> None:
    """Generate a new floor, respawn entities, and preserve player + followers."""
    if engine.player is None:
        return

    followers = collect_descent_followers(
        engine.world,
        engine.game_map,
        engine.player,
    )
    clear_all_come_here(engine.world)
    engine.initialize_floor(mode="descend", followers=followers)
    engine.vore_modal.reset()
    engine.digestion_modal.reset()
    engine.skipped_this_phase.clear()
    engine.examine_state.reset()
    engine.ground_pickup_modal.reset()
    engine.inventory_modal.reset()
    engine.macguffin_victory_confirm.reset()
    engine.close_door_pending = False
    engine._update_fov()
    engine._notify_save_after_descent()


def spawn_player(engine: GameEngine) -> None:
    """Place the player at the dungeon entrance."""
    player = engine.world[object()]
    x, y = engine.game_map.enter_xy
    player.components[Position] = Position(x, y)
    player.components[Renderable] = Renderable(ch=ord("@"), fg=(255, 255, 255))
    player.components[Fighter] = Fighter(
        hp=PLAYER_MAX_HP,
        max_hp=PLAYER_MAX_HP,
        accuracy=PLAYER_ACCURACY,
        evade=PLAYER_EVADE,
        ac=PLAYER_AC,
        min_damage=PLAYER_MIN_DAMAGE,
        max_damage=PLAYER_MAX_DAMAGE,
    )
    player.components[Inventory] = Inventory()
    player.components[EquipState] = EquipState()
    player.components[PlayerProgression] = PlayerProgression()
    player.components[PlayerEffects] = PlayerEffects()
    player.components[Mobility] = Mobility(kind=MobilityType.GROUND)
    player.tags.add(Player)
    depth_jump_start_depth = getattr(engine, "depth_jump_start_depth", None)
    if depth_jump_start_depth is not None and depth_jump_start_depth > 1:
        from src.data.floor_rune_loader import load_floor_rune_registry
        from src.depth_jump_loadout import apply_depth_jump_loadout
        from src.systems.inventory import item_registry

        profile = engine.difficulty_profile()
        apply_depth_jump_loadout(
            player,
            target_depth=depth_jump_start_depth,
            rng=engine.rng,
            registry=item_registry(),
            rune_registry=load_floor_rune_registry(),
            runes_per_floor=engine.runes_per_floor(),
            rune_pieces_multiplier=profile.rune_pieces_multiplier,
            run_stats=engine.run_stats,
        )
    else:
        apply_starter_loadout(player)
    player.tags.add(BlocksMovement)
    engine.player = player


def dungeon_gen_kwargs(engine: GameEngine, *, seed: int | None = None) -> dict:
    return {
        "map_width": MAP_WIDTH,
        "map_height": MAP_HEIGHT,
        "max_rooms": MAX_ROOMS,
        "room_min_size": ROOM_MIN_SIZE,
        "room_max_size": ROOM_MAX_SIZE,
        "seed": seed,
        "water_testing": engine.water_testing_mode,
        "layout_archetype_force": engine.layout_archetype_force,
        "runes_per_floor": engine.runes_per_floor(),
    }


def difficulty_profile(engine: GameEngine):
    """Active difficulty profile for this run (from snapshot id)."""
    from src.data.depth_scaling_loader import default_depth_scaling_config

    return default_depth_scaling_config().profile_for(engine.difficulty_id)


def runes_per_floor(engine: GameEngine) -> int:
    """Rune count for this run (difficulty override, else floor_runes.json)."""
    from src.systems.floor_runes import configured_runes_per_floor

    override = engine.difficulty_profile().runes_per_floor_override
    if override is not None:
        return max(0, int(override))
    return configured_runes_per_floor()


def prefetch_params(
    engine: GameEngine,
    *,
    seed: int | None = None,
    depth: int | None = None,
) -> PrefetchParams:
    return PrefetchParams(
        map_width=MAP_WIDTH,
        map_height=MAP_HEIGHT,
        water_testing=engine.water_testing_mode,
        layout_archetype_force=engine.layout_archetype_force,
        seed=seed,
        depth=depth if depth is not None else engine.floor_depth,
        runes_per_floor=engine.runes_per_floor(),
    )


def take_or_generate_dungeon(
    engine: GameEngine,
    *,
    seed: int | None = None,
) -> GameMap:
    """Consume a prefetched map when params match; otherwise generate synchronously."""
    params = engine._prefetch_params(seed=seed)
    if engine.floor_prefetch is not None:
        cached = engine.floor_prefetch.take(params)
        if cached is not None:
            return cached
    debug_print("[prefetch] miss -> sync", flush=True)
    return generate_dungeon(**engine._dungeon_gen_kwargs(seed=seed))


def schedule_floor_prefetch(engine: GameEngine) -> None:
    if engine.floor_prefetch is None:
        return
    next_depth = (
        engine.floor_depth + 1
        if engine.floor_depth < FLOOR_DEPTH_MAX
        else engine.floor_depth
    )
    engine.floor_prefetch.schedule(
        engine._prefetch_params(seed=None, depth=next_depth),
    )


def invalidate_floor_prefetch(engine: GameEngine) -> None:
    if engine.floor_prefetch is None:
        return
    engine.floor_prefetch.cancel()
    engine._schedule_floor_prefetch()


def debug_log_floor_init_reject(attempt: int, reason: str) -> None:
    debug_print(f"[floor_init] rejected attempt {attempt}: {reason}", flush=True)


def spawn_floor_population_and_runes(
    engine: GameEngine,
    floor_depth: int,
    *,
    followers: list[Entity] | None = None,
) -> None:
    """Spawn NPCs, items, and runes. Raises RunePlacementError on rune failure."""
    if engine.player is None:
        raise RunePlacementError("no player")

    pos = engine.player.components[Position]
    good_reduction = 0
    if followers:
        reg = load_entity_registry()
        map_has_water = bool(water_positions(engine.game_map))
        good_reduction = min(
            len(followers),
            good_aligned_weight_at_depth(
                reg,
                floor_depth,
                map_has_water=map_has_water,
            ),
        )
    spawn_floor_population(
        engine.world,
        engine.game_map,
        pos.x,
        pos.y,
        floor_depth,
        rng=engine.rng,
        good_follower_reduction=good_reduction,
        difficulty_id=engine.difficulty_id,
    )
    spawn_items(
        engine.world,
        engine.game_map,
        pos.x,
        pos.y,
        floor_depth,
        rng=engine.rng,
    )
    runes = spawn_floor_rune(
        engine.world,
        engine.game_map,
        floor_depth,
        rng=engine.rng,
        count=engine.runes_per_floor(),
    )
    rune_positions = [
        (entity.components[Position].x, entity.components[Position].y)
        for entity in runes
    ]
    spawn_macguffins(
        engine.world,
        engine.game_map,
        floor_depth,
        rng=engine.rng,
        placed_positions=rune_positions,
    )


def initialize_floor(
    engine: GameEngine,
    *,
    seed: int | None = None,
    mode: str = "new",
    start_depth: int = 1,
    followers: list[Entity] | None = None,
    log_session_milestones: bool = True,
) -> None:
    """Generate a map, populate entities, and place runes with regen on failure."""
    if mode == "new":
        engine._initialize_floor_new(
            seed=seed,
            start_depth=start_depth,
            log_session_milestones=log_session_milestones,
        )
        return
    if mode == "descend":
        engine._initialize_floor_descend(
            followers=followers or [],
            log_session_milestones=log_session_milestones,
        )
        return
    raise ValueError(f"unsupported floor init mode: {mode}")


def log_session_floor_entered(
    engine: GameEngine,
    *,
    log_session_milestones: bool,
) -> None:
    if log_session_milestones:
        session_log.log(f"Entered floor {engine.floor_depth}")


def initialize_floor_new(
    engine: GameEngine,
    *,
    seed: int | None,
    start_depth: int = 1,
    log_session_milestones: bool = True,
) -> None:
    engine.player_turn_count = 0
    engine.floor_depth = max(FLOOR_DEPTH_START, int(start_depth))
    resolved_seed = seed if seed is not None else random.randint(0, 2_147_483_647)
    engine.run_seed = resolved_seed
    engine.rng = random.Random(resolved_seed)
    if log_session_milestones:
        session_log.log(f"Seed: {engine.run_seed}")

    for attempt in range(1, MAX_GEN_ATTEMPTS + 1):
        engine.world = Registry()
        engine.player = None
        engine.game_map = (
            engine._take_or_generate_dungeon(seed=seed)
            if attempt == 1
            else generate_dungeon(**engine._dungeon_gen_kwargs(seed=seed))
        )
        engine._spawn_player()
        try:
            engine._spawn_floor_population_and_runes(engine.floor_depth)
            engine._schedule_floor_prefetch()
            engine._log_session_floor_entered(
                log_session_milestones=log_session_milestones,
            )
            return
        except RunePlacementError:
            engine._debug_log_floor_init_reject(attempt, "rune_placement_failed")

    debug_print(
        "[floor_init] using best-effort rune placement after failed attempts",
        flush=True,
    )
    engine.world = Registry()
    engine.player = None
    engine.game_map = generate_dungeon(**engine._dungeon_gen_kwargs(seed=seed))
    engine._spawn_player()
    if engine.player is not None:
        try:
            engine._spawn_floor_population_and_runes(engine.floor_depth)
        except RunePlacementError:
            debug_print(
                "[floor_init] warning: incomplete rune placement on fallback",
                flush=True,
            )
    engine._schedule_floor_prefetch()
    engine._log_session_floor_entered(log_session_milestones=log_session_milestones)


def initialize_floor_isolation(
    engine: GameEngine,
    *,
    depth: int,
    seed: int,
    log_session_milestones: bool = False,
) -> None:
    """Bootstrap a single floor at ``depth`` for balance-sim isolation runs."""
    engine.player_turn_count = 0
    engine.floor_depth = depth
    engine.run_seed = seed
    engine.rng = random.Random(seed)
    if log_session_milestones:
        session_log.log(f"Seed: {engine.run_seed}")

    for attempt in range(1, MAX_GEN_ATTEMPTS + 1):
        engine.world = Registry()
        engine.player = None
        engine.game_map = (
            engine._take_or_generate_dungeon(seed=seed)
            if attempt == 1
            else generate_dungeon(**engine._dungeon_gen_kwargs(seed=seed))
        )
        engine._spawn_player()
        try:
            engine._spawn_floor_population_and_runes(engine.floor_depth)
            engine._schedule_floor_prefetch()
            engine._log_session_floor_entered(
                log_session_milestones=log_session_milestones,
            )
            return
        except RunePlacementError:
            engine._debug_log_floor_init_reject(attempt, "rune_placement_failed")

    debug_print(
        "[floor_init] using best-effort rune placement after failed attempts",
        flush=True,
    )
    engine.world = Registry()
    engine.player = None
    engine.game_map = generate_dungeon(**engine._dungeon_gen_kwargs(seed=seed))
    engine._spawn_player()
    if engine.player is not None:
        try:
            engine._spawn_floor_population_and_runes(engine.floor_depth)
        except RunePlacementError:
            debug_print(
                "[floor_init] warning: incomplete rune placement on fallback",
                flush=True,
            )
    engine._schedule_floor_prefetch()
    engine._log_session_floor_entered(log_session_milestones=log_session_milestones)


def initialize_floor_descend(
    engine: GameEngine,
    *,
    followers: list[Entity],
    log_session_milestones: bool = True,
) -> None:
    if engine.player is None:
        return

    keep = {engine.player, *followers}
    next_depth = (
        engine.floor_depth + 1
        if engine.floor_depth < FLOOR_DEPTH_MAX
        else engine.floor_depth
    )

    for attempt in range(1, MAX_GEN_ATTEMPTS + 1):
        engine.game_map = (
            engine._take_or_generate_dungeon()
            if attempt == 1
            else generate_dungeon(**engine._dungeon_gen_kwargs())
        )
        clear_floor_entities(engine.world, keep=keep)
        entrance_x, entrance_y = engine.game_map.enter_xy
        engine.player.components[Position] = Position(entrance_x, entrance_y)
        place_descent_followers(
            engine.game_map,
            followers,
            entrance_xy=engine.game_map.enter_xy,
            player=engine.player,
        )
        try:
            engine._spawn_floor_population_and_runes(
                next_depth,
                followers=followers,
            )
            engine.floor_depth = next_depth
            engine._schedule_floor_prefetch()
            engine._log_session_floor_entered(
                log_session_milestones=log_session_milestones,
            )
            return
        except RunePlacementError:
            engine._debug_log_floor_init_reject(attempt, "rune_placement_failed")

    debug_print(
        "[floor_init] using best-effort rune placement after failed attempts",
        flush=True,
    )
    engine.game_map = generate_dungeon(**engine._dungeon_gen_kwargs())
    clear_floor_entities(engine.world, keep=keep)
    entrance_x, entrance_y = engine.game_map.enter_xy
    engine.player.components[Position] = Position(entrance_x, entrance_y)
    place_descent_followers(
        engine.game_map,
        followers,
        entrance_xy=engine.game_map.enter_xy,
        player=engine.player,
    )
    engine.floor_depth = next_depth
    if engine.player is not None:
        try:
            engine._spawn_floor_population_and_runes(
                next_depth,
                followers=followers,
            )
        except RunePlacementError:
            debug_print(
                "[floor_init] warning: incomplete rune placement on fallback",
                flush=True,
            )
    engine._schedule_floor_prefetch()
    engine._log_session_floor_entered(log_session_milestones=log_session_milestones)
