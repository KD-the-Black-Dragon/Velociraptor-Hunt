"""AI visit orchestration: intent pipeline, monster turns (PR10/PR11)."""
from __future__ import annotations

import random
from typing import Literal

from tcod.ecs import Entity, Registry

from src import messages
from src.debug_log import debug_print
from src.components import (
    AI,
    AbilityState,
    AIState,
    Alignment,
    BlocksMovement,
    DisplayName,
    Engulfed,
    Fighter,
    NPCAlignment,
    Player,
    Position,
    Predator,
    Renderable,
    SpeciesId,
    Stunned,
)
from src.constants import DEFAULT_VORE_CONTENT_PREFS, VoreContentPreferences
from src.map_gen import GameMap
from src.message_log import MessageLog
from src.systems.combat import try_action
from src.systems.abilities import (
    ActionStepKind,
    choose_path_ranged_move_direction,
    compute_action_plan,
    coward_flee_direction,
    erratic_pursuit_suppressed,
    has_path_ability,
    has_wander,
    try_path_engagement,
    try_smite_engagement,
    try_summon_on_first_sight,
)
from src.systems.digestion import apply_digestion_tick
from src.systems.naming import entity_log_name
from src.systems.vore import (
    VoreModalSegment,
    VoreModalState,
    find_predator_holding_prey,
    sync_engulfed_position,
    try_open_ranged_vore_modal,
    try_open_vore_modal,
    try_resolve_npc_ranged_vore,
    try_resolve_npc_vore,
)
from src.systems.ai.common import (
    _chebyshev,
    _distant_throttle_applies,
    _floor_is_busy,
    _forbidden_tiles,
    _get_ability_state,
    _get_ai_state,
    _half_turn_should_act,
    _has_los,
    _npc_alignment,
    _pick_nearest_tied,
    _sorted_monsters,
    spawn_ai_freeze_blocks_action,
)
from src.systems.ai.explore import (
    ExploreBfsCache,
    ExploreTerrainCache,
    _is_explore_step,
    _is_neutral_explore_step,
)
from src.systems.ai.targeting import (
    _monster_should_act,
    pick_evil_chase,
    pick_good_chase,
)
from src.systems.ai.chase import (
    _adjacent_attack_targets,
    _direction_toward,
    _prepare_chase_pursuit_turn,
    _print_evil_frustration_if_blocked,
    _resolve_chase_direction,
    _update_ai_memory,
)
from src.systems.ai.movement import (
    _choose_erratic_random_direction,
    _consume_door_spite_wait_turn,
    _resolve_monster_move_direction,
    _try_monster_move,
    _try_predator_holding_attack,
    resolve_wander_ability_move,
)

StepResult = Literal["next_step", "end_visit", "open_modal"]



def _execute_erratic_pursuit_step(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    message_log: MessageLog,
    rng: random.Random,
    *,
    alignment: Alignment,
    blocked: frozenset[Position],
    player_engulfed: bool,
    monster_pos: Position,
    state: AIState,
    skipped: set[Entity] | None,
    cache: ExploreBfsCache | None = None,
    player_turn_count: int = 0,
    distant_throttle: bool = False,
    floor_depth: int = 1,
    difficulty_id: str | None = None,
) -> tuple[StepResult, Position | None]:
    """Intentional first MOVE. Returns (result, tile left behind if moved)."""
    if try_summon_on_first_sight(
        monster,
        world,
        game_map,
        player,
        message_log,
        rng,
        alignment=alignment,
        player_engulfed=player_engulfed,
        floor_depth=floor_depth,
        difficulty_id=difficulty_id,
    ):
        return "end_visit", None

    coward_direction = coward_flee_direction(
        monster,
        world,
        game_map,
        player,
        rng,
        alignment=alignment,
        blocked_tiles=blocked,
        player_engulfed=player_engulfed,
    )
    if coward_direction is not None:
        try_action(
            world,
            game_map,
            monster,
            coward_direction,
            message_log,
            rng=rng,
            skip_turn_entities=skipped,
        )
        after = monster.components[Position]
        left = monster_pos if after != monster_pos else None
        return "end_visit", left

    if alignment == Alignment.EVIL:
        _print_evil_frustration_if_blocked(
            monster,
            world,
            game_map,
            player,
            rng,
            player_engulfed=player_engulfed,
            cache=cache,
            player_turn_count=player_turn_count,
            distant_throttle=distant_throttle,
        )

    # Optional only when already next to something worth attacking.
    if erratic_pursuit_suppressed(
        monster,
        world,
        game_map,
        player,
        alignment=alignment,
        player_engulfed=player_engulfed,
    ):
        return "next_step", None

    if has_wander(monster):
        if _consume_door_spite_wait_turn(
            monster,
            world,
            game_map,
            player,
            message_log,
            rng,
            state=state,
            monster_pos=monster_pos,
            skipped=skipped,
        ):
            return "next_step", None
        direction, pursuit_phase, explore_step = resolve_wander_ability_move(
            monster,
            world,
            game_map,
            player,
            rng,
            state=state,
            alignment=alignment,
            blocked=blocked,
            monster_pos=monster_pos,
            cache=cache,
            explore_allow_idle=False,
        )
        _try_monster_move(
            monster,
            world,
            game_map,
            direction,
            message_log,
            rng,
            origin=monster_pos,
            state=state,
            pursuit_phase=pursuit_phase,
            skipped=skipped,
            explore_step=explore_step,
            memory_target=None,
            player=player,
            cache=cache,
        )
        after = monster.components[Position]
        left = monster_pos if after != monster_pos else None
        return "next_step", left

    # Full intentional move (chase / memory / explore / flee) — no explore idle.
    # Mirror intent-pipeline move setup so explore progress and door spite stay correct.
    explore_step = False
    memory_target: Position | None = None
    if alignment == Alignment.EVIL:
        entity_target, pos_target, blocked_primary = pick_evil_chase(
            monster,
            world,
            game_map,
            player,
            rng,
            player_engulfed=player_engulfed,
            cache=cache,
            player_turn_count=player_turn_count,
            distant_throttle=distant_throttle,
        )
        if _consume_door_spite_wait_turn(
            monster,
            world,
            game_map,
            player,
            message_log,
            rng,
            state=state,
            monster_pos=monster_pos,
            skipped=skipped,
        ):
            return "next_step", None
        explore_step = _is_explore_step(
            Alignment.EVIL,
            state,
            entity_target,
            pos_target,
            "explore",
        )
        if blocked_primary is not None and entity_target is not None:
            debug_print(
                messages.evil_frustrated_by_blocker(
                    entity_log_name(monster, sentence_start=True),
                    entity_log_name(entity_target),
                    entity_log_name(blocked_primary),
                ),
                flush=True,
            )
        direction, pursuit_phase = _resolve_monster_move_direction(
            monster,
            world,
            game_map,
            player,
            rng,
            state=state,
            alignment=alignment,
            blocked=blocked,
            player_engulfed=player_engulfed,
            monster_pos=monster_pos,
            cache=cache,
            player_turn_count=player_turn_count,
            distant_throttle=distant_throttle,
            explore_allow_idle=False,
        )
        if pursuit_phase == "memory":
            memory_target = pos_target
    elif alignment == Alignment.GOOD:
        entity_target, pos_target, chase_mode = pick_good_chase(
            monster,
            world,
            game_map,
            player,
            rng,
            player_engulfed=player_engulfed,
            cache=cache,
            player_turn_count=player_turn_count,
            distant_throttle=distant_throttle,
        )
        if _consume_door_spite_wait_turn(
            monster,
            world,
            game_map,
            player,
            message_log,
            rng,
            state=state,
            monster_pos=monster_pos,
            skipped=skipped,
        ):
            return "next_step", None
        explore_step = _is_explore_step(
            Alignment.GOOD,
            state,
            entity_target,
            pos_target,
            chase_mode,
        )
        direction, pursuit_phase = _resolve_chase_direction(
            world,
            game_map,
            monster,
            monster_pos,
            target_entity=entity_target,
            target_position=pos_target,
            chase_mode=chase_mode,
            player=player,
            blocked=blocked,
            state=state,
            rng=rng,
            alignment=alignment,
            player_engulfed=player_engulfed,
            cache=cache,
            explore_allow_idle=False,
        )
        if pursuit_phase == "memory":
            memory_target = pos_target
    else:
        explore_step = _is_neutral_explore_step(monster, world, game_map)
        direction, pursuit_phase = _resolve_monster_move_direction(
            monster,
            world,
            game_map,
            player,
            rng,
            state=state,
            alignment=alignment,
            blocked=blocked,
            player_engulfed=player_engulfed,
            monster_pos=monster_pos,
            cache=cache,
            player_turn_count=player_turn_count,
            distant_throttle=distant_throttle,
            explore_allow_idle=False,
        )

    _try_monster_move(
        monster,
        world,
        game_map,
        direction,
        message_log,
        rng,
        origin=monster_pos,
        state=state,
        pursuit_phase=pursuit_phase,
        skipped=skipped,
        explore_step=explore_step,
        memory_target=memory_target,
        player=player,
        cache=cache,
    )
    after = monster.components[Position]
    left = monster_pos if after != monster_pos else None
    return "next_step", left


def _execute_erratic_attack_step(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    message_log: MessageLog,
    rng: random.Random,
    *,
    modal: VoreModalState | None,
    monsters: list[Entity],
    monster_index: int,
    vore_prefs: VoreContentPreferences,
    alignment: Alignment,
    player_engulfed: bool,
    monster_pos: Position,
    skipped: set[Entity] | None,
) -> StepResult:
    """Adjacent-only attack: vore modal, NPC vore, or melee bump. No ranged or distant chase."""
    targets = _adjacent_attack_targets(
        monster,
        world,
        game_map,
        player,
        alignment=alignment,
        player_engulfed=player_engulfed,
    )
    if not targets:
        return "next_step"

    if (
        modal is not None
        and player in targets
        and try_open_vore_modal(
            monster,
            player,
            game_map,
            modal,
            monsters,
            monster_index,
            rng,
            prefs=vore_prefs,
        )
    ):
        return "open_modal"

    if alignment == Alignment.EVIL and try_resolve_npc_vore(
        monster,
        world,
        game_map,
        message_log,
        rng,
        prefs=vore_prefs,
    ):
        return "end_visit"

    target = _pick_nearest_tied(monster_pos, targets, rng)
    direction = _direction_toward(monster_pos, target.components[Position])
    if direction is not None:
        try_action(
            world,
            game_map,
            monster,
            direction,
            message_log,
            rng=rng,
            skip_turn_entities=skipped,
        )
    return "next_step"


def _execute_erratic_random_step(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    message_log: MessageLog,
    rng: random.Random,
    *,
    monster_pos: Position,
    blocked: frozenset[Position],
    skipped: set[Entity] | None,
    forbid_return_to: Position | None = None,
) -> StepResult:
    """Mandatory random step: equal weight among legal dirs + stay; no reverse of first MOVE."""
    direction = _choose_erratic_random_direction(
        world,
        game_map,
        monster,
        monster_pos,
        rng,
        blocked_tiles=blocked,
        forbid_return_to=forbid_return_to,
    )
    if direction is not None and direction != (0, 0):
        try_action(
            world,
            game_map,
            monster,
            direction,
            message_log,
            rng=rng,
            skip_turn_entities=skipped,
        )
    return "next_step"


def _execute_intent_pipeline(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    message_log: MessageLog,
    rng: random.Random,
    *,
    modal: VoreModalState | None,
    monsters: list[Entity],
    monster_index: int,
    vore_prefs: VoreContentPreferences,
    state: AIState,
    alignment: Alignment,
    blocked: frozenset[Position],
    player_engulfed: bool,
    monster_pos: Position,
    skipped: set[Entity] | None,
    cache: ExploreBfsCache | None = None,
    player_turn_count: int = 0,
    distant_throttle: bool = False,
    floor_depth: int = 1,
    difficulty_id: str | None = None,
) -> StepResult:
    if try_summon_on_first_sight(
        monster,
        world,
        game_map,
        player,
        message_log,
        rng,
        alignment=alignment,
        player_engulfed=player_engulfed,
        floor_depth=floor_depth,
        difficulty_id=difficulty_id,
    ):
        return "end_visit"

    coward_direction = coward_flee_direction(
        monster,
        world,
        game_map,
        player,
        rng,
        alignment=alignment,
        blocked_tiles=blocked,
        player_engulfed=player_engulfed,
    )
    if coward_direction is not None:
        try_action(
            world,
            game_map,
            monster,
            coward_direction,
            message_log,
            rng=rng,
            skip_turn_entities=skipped,
        )
        return "end_visit"

    if modal is not None and try_open_vore_modal(
        monster,
        player,
        game_map,
        modal,
        monsters,
        monster_index,
        rng,
        prefs=vore_prefs,
    ):
        return "open_modal"

    if modal is not None and try_open_ranged_vore_modal(
        monster,
        player,
        game_map,
        modal,
        monsters,
        monster_index,
        rng,
        prefs=vore_prefs,
    ):
        return "open_modal"

    if alignment == Alignment.EVIL and try_resolve_npc_vore(
        monster,
        world,
        game_map,
        message_log,
        rng,
        prefs=vore_prefs,
    ):
        return "end_visit"

    if alignment == Alignment.EVIL and try_resolve_npc_ranged_vore(
        monster,
        world,
        game_map,
        message_log,
        rng,
        prefs=vore_prefs,
    ):
        return "end_visit"

    if has_wander(monster):
        if _consume_door_spite_wait_turn(
            monster,
            world,
            game_map,
            player,
            message_log,
            rng,
            state=state,
            monster_pos=monster_pos,
            skipped=skipped,
        ):
            return "next_step"
        direction, pursuit_phase, explore_step = resolve_wander_ability_move(
            monster,
            world,
            game_map,
            player,
            rng,
            state=state,
            alignment=alignment,
            blocked=blocked,
            monster_pos=monster_pos,
            cache=cache,
            explore_allow_idle=True,
        )
        _try_monster_move(
            monster,
            world,
            game_map,
            direction,
            message_log,
            rng,
            origin=monster_pos,
            state=state,
            pursuit_phase=pursuit_phase,
            skipped=skipped,
            explore_step=explore_step,
            memory_target=None,
            player=player,
            cache=cache,
        )
        return "next_step"

    explore_step = False
    memory_target: Position | None = None
    if alignment == Alignment.EVIL:
        entity_target, pos_target, blocked_primary = pick_evil_chase(
            monster,
            world,
            game_map,
            player,
            rng,
            player_engulfed=player_engulfed,
            cache=cache,
            player_turn_count=player_turn_count,
            distant_throttle=distant_throttle,
        )
        if _consume_door_spite_wait_turn(
            monster,
            world,
            game_map,
            player,
            message_log,
            rng,
            state=state,
            monster_pos=monster_pos,
            skipped=skipped,
        ):
            return "next_step"
        explore_step = _is_explore_step(
            Alignment.EVIL,
            state,
            entity_target,
            pos_target,
            "explore",
        )
        if blocked_primary is not None and entity_target is not None:
            debug_print(
                messages.evil_frustrated_by_blocker(
                    entity_log_name(monster, sentence_start=True),
                    entity_log_name(entity_target),
                    entity_log_name(blocked_primary),
                ),
                flush=True,
            )
        if try_path_engagement(
            monster,
            world,
            game_map,
            player,
            message_log,
            rng,
            alignment=alignment,
            entity_target=entity_target,
            player_engulfed=player_engulfed,
        ):
            return "end_visit"
        if try_smite_engagement(
            monster,
            world,
            game_map,
            player,
            message_log,
            rng,
            alignment=alignment,
            entity_target=entity_target,
            player_engulfed=player_engulfed,
        ):
            return "end_visit"
        if has_path_ability(monster):
            path_dir = choose_path_ranged_move_direction(
                monster,
                world,
                game_map,
                player,
                rng,
                alignment=alignment,
                entity_target=entity_target,
                player_engulfed=player_engulfed,
                blocked=blocked,
                monster_pos=monster_pos,
            )
            if path_dir is not None:
                try_action(
                    world,
                    game_map,
                    monster,
                    path_dir,
                    message_log,
                    rng=rng,
                    skip_turn_entities=skipped,
                )
                return "end_visit"
            # Stand ground while a non-adjacent quarry is in play (no kite, no
            # melee-close). Adjacent falls through so bump/vore can run.
            hold_quarry = entity_target
            if hold_quarry is None and not player_engulfed:
                player_pos = player.components[Position]
                if _has_los(game_map, monster_pos, player_pos):
                    hold_quarry = player
            if hold_quarry is not None:
                hold_pos = hold_quarry.components[Position]
                if _chebyshev(monster_pos, hold_pos) > 1:
                    return "end_visit"
        direction, pursuit_phase = _resolve_monster_move_direction(
            monster,
            world,
            game_map,
            player,
            rng,
            state=state,
            alignment=alignment,
            blocked=blocked,
            player_engulfed=player_engulfed,
            monster_pos=monster_pos,
            cache=cache,
            player_turn_count=player_turn_count,
            distant_throttle=distant_throttle,
        )
        if pursuit_phase == "memory":
            memory_target = pos_target
    elif alignment == Alignment.GOOD:
        entity_target, pos_target, chase_mode = pick_good_chase(
            monster,
            world,
            game_map,
            player,
            rng,
            player_engulfed=player_engulfed,
            cache=cache,
            player_turn_count=player_turn_count,
            distant_throttle=distant_throttle,
        )
        if _consume_door_spite_wait_turn(
            monster,
            world,
            game_map,
            player,
            message_log,
            rng,
            state=state,
            monster_pos=monster_pos,
            skipped=skipped,
        ):
            return "next_step"
        explore_step = _is_explore_step(
            Alignment.GOOD,
            state,
            entity_target,
            pos_target,
            chase_mode,
        )
        if try_path_engagement(
            monster,
            world,
            game_map,
            player,
            message_log,
            rng,
            alignment=alignment,
            entity_target=entity_target,
            player_engulfed=player_engulfed,
        ):
            return "end_visit"
        if try_smite_engagement(
            monster,
            world,
            game_map,
            player,
            message_log,
            rng,
            alignment=alignment,
            entity_target=entity_target,
            player_engulfed=player_engulfed,
        ):
            return "end_visit"
        if has_path_ability(monster):
            kite_dir = choose_path_ranged_move_direction(
                monster,
                world,
                game_map,
                player,
                rng,
                alignment=alignment,
                entity_target=entity_target,
                player_engulfed=player_engulfed,
                blocked=blocked,
                monster_pos=monster_pos,
            )
            if kite_dir is not None:
                try_action(
                    world,
                    game_map,
                    monster,
                    kite_dir,
                    message_log,
                    rng=rng,
                    skip_turn_entities=skipped,
                )
                return "end_visit"
        direction, pursuit_phase = _resolve_chase_direction(
            world,
            game_map,
            monster,
            monster_pos,
            target_entity=entity_target,
            target_position=pos_target,
            chase_mode=chase_mode,
            player=player,
            blocked=blocked,
            state=state,
            rng=rng,
            alignment=alignment,
            player_engulfed=player_engulfed,
            cache=cache,
        )
        if pursuit_phase == "memory":
            memory_target = pos_target
    else:
        explore_step = _is_neutral_explore_step(monster, world, game_map)
        direction, pursuit_phase = _resolve_monster_move_direction(
            monster,
            world,
            game_map,
            player,
            rng,
            state=state,
            alignment=alignment,
            blocked=blocked,
            player_engulfed=player_engulfed,
            monster_pos=monster_pos,
            cache=cache,
            player_turn_count=player_turn_count,
            distant_throttle=distant_throttle,
        )

    _try_monster_move(
        monster,
        world,
        game_map,
        direction,
        message_log,
        rng,
        origin=monster_pos,
        state=state,
        pursuit_phase=pursuit_phase,
        skipped=skipped,
        explore_step=explore_step,
        memory_target=memory_target,
        player=player,
        cache=cache,
    )
    return "next_step"


def _run_monster_visit(
    monster: Entity,
    monster_index: int,
    monsters: list[Entity],
    world: Registry,
    game_map: GameMap,
    player: Entity,
    message_log: MessageLog,
    rng: random.Random,
    *,
    modal: VoreModalState | None,
    vore_prefs: VoreContentPreferences,
    skipped: set[Entity] | None,
    player_engulfed: bool,
    player_turn_count: int,
    terrain_cache: ExploreTerrainCache | None = None,
    distant_throttle: bool = False,
    floor_depth: int = 1,
    difficulty_id: str | None = None,
) -> bool:
    """Execute one monster's action plan. Returns True when a vore modal opens."""
    monster_pos = monster.components[Position]
    alignment = _npc_alignment(monster)
    blocked = _forbidden_tiles(monster, player)
    state = _get_ai_state(monster)
    ability_state = _get_ability_state(monster)
    bfs_cache = ExploreBfsCache(
        terrain=terrain_cache if terrain_cache is not None else ExploreTerrainCache()
    )

    ability_state.plan_step_index = 0
    ability_state.erratic_index = 0
    plan = compute_action_plan(monster, player_turn_count)
    if len(plan.steps) == 1 and plan.steps[0].kind == ActionStepKind.SKIP:
        return False

    _update_ai_memory(
        monster,
        world,
        game_map,
        player,
        rng,
        player_engulfed=player_engulfed,
    )
    _prepare_chase_pursuit_turn(
        monster,
        world,
        game_map,
        player,
        rng,
        state,
        alignment=alignment,
        player_engulfed=player_engulfed,
        monster_pos=monster_pos,
    )

    # Tile left by intentional first MOVE — random MOVE may not step back onto it.
    erratic_forbid_return: Position | None = None

    for step_index, step in enumerate(plan.steps):
        if step_index < ability_state.plan_step_index:
            continue

        if step.kind == ActionStepKind.MOVE_OR_BUMP:
            result = _execute_intent_pipeline(
                monster,
                world,
                game_map,
                player,
                message_log,
                rng,
                modal=modal,
                monsters=monsters,
                monster_index=monster_index,
                vore_prefs=vore_prefs,
                state=state,
                alignment=alignment,
                blocked=blocked,
                player_engulfed=player_engulfed,
                monster_pos=monster_pos,
                skipped=skipped,
                cache=bfs_cache,
                player_turn_count=player_turn_count,
                distant_throttle=distant_throttle,
                floor_depth=floor_depth,
                difficulty_id=difficulty_id,
            )
        elif step.kind == ActionStepKind.MOVE:
            # Plan is MOVE, ATTACK, MOVE (optionally doubled for Fast).
            # Within each triple, index % 3 == 0 is intentional; == 2 is random.
            if step_index % 3 == 0:
                result, left_from = _execute_erratic_pursuit_step(
                    monster,
                    world,
                    game_map,
                    player,
                    message_log,
                    rng,
                    alignment=alignment,
                    blocked=blocked,
                    player_engulfed=player_engulfed,
                    monster_pos=monster_pos,
                    state=state,
                    skipped=skipped,
                    cache=bfs_cache,
                    player_turn_count=player_turn_count,
                    distant_throttle=distant_throttle,
                    floor_depth=floor_depth,
                    difficulty_id=difficulty_id,
                )
                if left_from is not None:
                    erratic_forbid_return = left_from
            else:
                result = _execute_erratic_random_step(
                    monster,
                    world,
                    game_map,
                    message_log,
                    rng,
                    monster_pos=monster_pos,
                    blocked=blocked,
                    skipped=skipped,
                    forbid_return_to=erratic_forbid_return,
                )
        elif step.kind == ActionStepKind.SKIP:
            return False
        elif step.kind == ActionStepKind.ATTACK:
            result = _execute_erratic_attack_step(
                monster,
                world,
                game_map,
                player,
                message_log,
                rng,
                modal=modal,
                monsters=monsters,
                monster_index=monster_index,
                vore_prefs=vore_prefs,
                alignment=alignment,
                player_engulfed=player_engulfed,
                monster_pos=monster_pos,
                skipped=skipped,
            )
        else:
            result = "next_step"

        if result == "open_modal":
            ability_state.plan_step_index = 0
            ability_state.erratic_index = 0
            return True
        if result == "end_visit":
            ability_state.plan_step_index = 0
            ability_state.erratic_index = 0
            return False

        ability_state.plan_step_index = step_index + 1
        monster_pos = monster.components[Position]

    ability_state.plan_step_index = 0
    ability_state.erratic_index = 0
    return False


def run_monster_turns(
    world: Registry,
    game_map: GameMap,
    player: Entity,
    message_log: MessageLog,
    *,
    rng: random.Random | None = None,
    modal: VoreModalState | None = None,
    vore_prefs: VoreContentPreferences = DEFAULT_VORE_CONTENT_PREFS,
    skipped: set[Entity] | None = None,
    player_turn_count: int = 0,
    floor_depth: int = 1,
    difficulty_id: str | None = None,
) -> bool:
    """Each monster acts once per world phase. Returns True when a vore modal opens."""
    rng = rng or random.Random()
    player_pos = player.components[Position]
    monsters = _sorted_monsters(world)
    terrain_cache = ExploreTerrainCache()
    busy = _floor_is_busy(len(monsters))
    if (
        modal is not None
        and modal.segment is VoreModalSegment.NONE
        and modal.pending_monsters
    ):
        start_index = modal.resume_monster_index
    else:
        start_index = 0

    player_engulfed = Engulfed in player.tags
    from src.data.depth_scaling_loader import default_depth_scaling_config

    freeze_cfg = default_depth_scaling_config().profile_for(difficulty_id).spawn_ai_freeze

    for index in range(start_index, len(monsters)):
        monster = monsters[index]
        if monster.components.get(AI) is None or monster.components.get(Position) is None:
            continue

        if skipped is not None and monster in skipped:
            continue

        if Engulfed in monster.tags:
            if Player not in monster.tags:
                predator = find_predator_holding_prey(world, monster)
                if predator is not None:
                    apply_digestion_tick(
                        monster,
                        predator,
                        game_map,
                        message_log,
                        rng,
                        skip_turn_entities=skipped,
                    )
            continue

        if Stunned in monster.tags:
            continue

        if monster.components.get(Predator) is not None:
            sync_engulfed_position(world, monster)
            _try_predator_holding_attack(
                world,
                game_map,
                monster,
                message_log,
                rng=rng,
                skipped=skipped,
            )
            continue

        if not _monster_should_act(monster):
            continue

        if spawn_ai_freeze_blocks_action(monster, player, freeze_cfg):
            continue

        distant_throttle = _distant_throttle_applies(monster, player, busy=busy)
        # D2: half-turn cadence when throttled — skip entire visit.
        if distant_throttle:
            state = _get_ai_state(monster)
            if not _half_turn_should_act(state, player_turn_count):
                continue

        if _run_monster_visit(
            monster,
            index,
            monsters,
            world,
            game_map,
            player,
            message_log,
            rng,
            modal=modal,
            vore_prefs=vore_prefs,
            skipped=skipped,
            player_engulfed=player_engulfed,
            player_turn_count=player_turn_count,
            terrain_cache=terrain_cache,
            distant_throttle=distant_throttle,
            floor_depth=floor_depth,
            difficulty_id=difficulty_id,
        ):
            return True

    return False


def spawn_test_npc(
    world: Registry,
    *,
    x: int,
    y: int,
    species: str,
    alignment: Alignment,
    species_id: str | None = None,
    hp: int = 10,
    accuracy: float = 10.0,
    evade: float = 0.0,
    ac: int = 0,
    min_damage: int = 2,
    max_damage: int = 2,
) -> Entity:
    """Test helper: spawn a minimal NPC with alignment (not used in production spawn)."""
    entity = world[object()]
    entity.components[Position] = Position(x, y)
    entity.components[Renderable] = Renderable(ch=ord("k"), fg=(120, 160, 220))
    entity.components[Fighter] = Fighter(
        hp=hp,
        max_hp=hp,
        accuracy=accuracy,
        evade=evade,
        ac=ac,
        min_damage=min_damage,
        max_damage=max_damage,
    )
    entity.components[AI] = AI()
    entity.components[AIState] = AIState(ai_turn_salt=(x + y) & 1)
    entity.components[AbilityState] = AbilityState()
    entity.components[DisplayName] = DisplayName(name=species)
    entity.components[SpeciesId] = SpeciesId(id=species_id or species)
    entity.components[NPCAlignment] = NPCAlignment(alignment=alignment)
    entity.tags.add(BlocksMovement)
    return entity
