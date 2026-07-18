from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from tcod.ecs import Entity, Registry

from src import messages
from src.components import (
    Engulfed,
    Fighter,
    FloorRune,
    Inventory,
    Item,
    Macguffin,
    Player,
    Position,
    Stunned,
)
from src.map_gen import GameMap
from src.message_log import MessageCategory, MessageLog
from src.systems.combat import try_action
from src.systems.danger_interrupts import (
    DangerInterruptReason,
    attach_attack_interrupt_listener,
    detach_attack_interrupt_listener,
    evaluate_danger_interrupt,
)
from src.systems.floor_runes import try_activate_floor_rune
from src.systems.fov import player_has_visible_evil
from src.systems.inventory import floor_items_at, inventory_has_room_for, pickup_all_items_at
from src.systems.macguffins import try_begin_macguffin_activation
from src.systems.player_navigation import (
    explore_frontier_tiles,
    first_step_toward,
    nearest_goal_deterministic,
    player_walk_distances,
    player_walk_distances_with_blockers,
)


if TYPE_CHECKING:
    from src.engine import GameEngine


class AutoexploreEndReason(Enum):
    BLOCKED = "blocked"
    ATTACK = "attack"
    DANGER = "danger"
    ALLY_ALARM = "ally_alarm"
    COMPLETE = "complete"
    MODAL = "modal"


@dataclass(frozen=True)
class AutoexploreResult:
    consumed_turns: int
    end_reason: AutoexploreEndReason | None


@dataclass
class AutoexploreSession:
    active: bool = True
    consumed: int = 0
    attack_interrupt: bool = False

    def clear_attack_interrupt(self) -> None:
        self.attack_interrupt = False


@dataclass(frozen=True)
class AutoexploreFrameResult:
    screen_dirty: bool
    finished: bool


def _danger_to_autoexplore_end(reason: DangerInterruptReason) -> AutoexploreEndReason:
    return AutoexploreEndReason(reason.value)


def _player_below_half_hp(player: Entity) -> bool:
    fighter = player.components.get(Fighter)
    if fighter is None or fighter.max_hp <= 0:
        return True
    return fighter.hp * 2 < fighter.max_hp


def _tile_has_pickup_goal(
    world: Registry,
    game_map: GameMap,
    player: Entity,
    x: int,
    y: int,
) -> bool:
    if not game_map.in_bounds(x, y) or not game_map.explored[y, x]:
        return False

    target = Position(x, y)
    for entity in world.Q.all_of(tags=[target]):
        if entity.components.get(FloorRune) is not None:
            return True
        if entity.components.get(Macguffin) is not None:
            return True

    inventory = player.components.get(Inventory)
    if inventory is None:
        return False

    for item_entity in floor_items_at(world, x, y):
        item = item_entity.components[Item]
        if inventory_has_room_for(
            inventory,
            item_id=item.item_id,
            category=item.category,
        ):
            return True
    return False


def known_pickup_goals(
    world: Registry,
    game_map: GameMap,
    player: Entity,
) -> list[tuple[int, int]]:
    goals: set[tuple[int, int]] = set()
    for entity in world.Q.all_of(components=[Position]):
        pos = entity.components[Position]
        if _tile_has_pickup_goal(world, game_map, player, pos.x, pos.y):
            goals.add((pos.x, pos.y))
    return list(goals)


def pick_autoexplore_step(
    *,
    world: Registry,
    game_map: GameMap,
    player: Entity,
) -> tuple[int, int] | None:
    pos = player.components[Position]
    origin = (pos.x, pos.y)
    distances = player_walk_distances_with_blockers(
        world,
        game_map,
        origin,
        player,
        cardinal_only=False,
    )

    pickup_goals = known_pickup_goals(world, game_map, player)
    goal = nearest_goal_deterministic(pickup_goals, distances)
    if goal is not None:
        if goal == origin:
            return (0, 0)
        goal_distances = player_walk_distances(game_map, goal, cardinal_only=False)
        return first_step_toward(
            origin,
            goal,
            goal_distances,
            cardinal_only=False,
        )

    frontier = explore_frontier_tiles(game_map, cardinal_only=False)
    goal = nearest_goal_deterministic(frontier, distances)
    if goal is None:
        return None
    goal_distances = player_walk_distances(game_map, goal, cardinal_only=False)
    return first_step_toward(
        origin,
        goal,
        goal_distances,
        cardinal_only=False,
    )


def _apply_tile_step_hooks(engine: GameEngine) -> bool:
    """Run post-move pickup/rune/macguffin hooks. True when automation must stop."""
    player = engine.player
    if player is None:
        return False
    pos = player.components[Position]
    pickup_all_items_at(
        engine.world,
        player,
        pos.x,
        pos.y,
        engine.message_log,
    )
    try_activate_floor_rune(
        engine.world,
        player,
        pos.x,
        pos.y,
        engine.message_log,
        screen_flash=engine.screen_flash,
        run_stats=engine.run_stats,
        rune_pieces_multiplier=engine.difficulty_profile().rune_pieces_multiplier,
    )
    if try_begin_macguffin_activation(engine, player, pos.x, pos.y):
        return True
    return False


def begin_autoexplore(
    *,
    player: Entity,
    game_map: GameMap,
    world: Registry,
    message_log: MessageLog,
) -> AutoexploreSession | None:
    """Pre-checks and start message. Returns None when autoexplore is blocked."""
    if Engulfed in player.tags:
        message_log.add(
            messages.autoexplore_engulfed(),
            category=MessageCategory.DANGER,
        )
        return None

    if _player_below_half_hp(player):
        message_log.add(
            messages.autoexplore_too_injured(),
            category=MessageCategory.DANGER,
        )
        return None

    if Stunned in player.tags:
        message_log.add(
            messages.stunned_too_tired_to_move(),
            category=MessageCategory.DANGER,
        )
        return None

    if player_has_visible_evil(game_map, world):
        message_log.add(
            messages.autoexplore_enemy_in_sight(),
            category=MessageCategory.DANGER,
        )
        return None

    message_log.add(messages.autoexplore_start())
    return AutoexploreSession()


def advance_autoexplore_turn(
    *,
    engine: GameEngine,
    session: AutoexploreSession,
    consume_turn: Callable[[], None],
) -> AutoexploreEndReason | None:
    """Consume one autoexplore turn when possible; return stop reason when done."""
    if not session.active:
        return AutoexploreEndReason.BLOCKED

    player = engine.player
    if player is None:
        return AutoexploreEndReason.BLOCKED

    session.clear_attack_interrupt()
    direction = pick_autoexplore_step(
        world=engine.world,
        game_map=engine.game_map,
        player=player,
    )
    if direction is None:
        message_log = engine.message_log
        message_log.add(messages.autoexplore_complete())
        return AutoexploreEndReason.COMPLETE

    if direction == (0, 0):
        if _apply_tile_step_hooks(engine):
            return AutoexploreEndReason.MODAL
        consume_turn()
        session.consumed += 1
    elif try_action(
        engine.world,
        engine.game_map,
        player,
        direction,
        engine.message_log,
        rng=engine.rng,
        skip_turn_entities=engine.skipped_this_phase,
        run_stats=engine.run_stats,
    ):
        if _apply_tile_step_hooks(engine):
            return AutoexploreEndReason.MODAL
        consume_turn()
        session.consumed += 1
    else:
        return None

    danger = evaluate_danger_interrupt(
        player=player,
        game_map=engine.game_map,
        world=engine.world,
        message_log=engine.message_log,
        attack_interrupt=session.attack_interrupt,
    )
    if danger is not None:
        return _danger_to_autoexplore_end(danger)
    return None


def advance_autoexplore_frame(
    *,
    engine: GameEngine,
    session: AutoexploreSession,
    consume_turn: Callable[[], None],
) -> AutoexploreFrameResult:
    """Advance one step per call so main can render/present between world turns."""
    if engine.player is None or not session.active:
        return AutoexploreFrameResult(screen_dirty=False, finished=True)

    consumed_before = session.consumed
    end_reason = advance_autoexplore_turn(
        engine=engine,
        session=session,
        consume_turn=consume_turn,
    )
    if end_reason is not None:
        session.active = False
        return AutoexploreFrameResult(screen_dirty=True, finished=True)

    progressed = session.consumed > consumed_before
    return AutoexploreFrameResult(screen_dirty=progressed, finished=False)


def try_autoexplore(
    *,
    engine: GameEngine,
    consume_turn: Callable[[], None],
) -> AutoexploreResult:
    """Synchronous autoexplore loop for tests and tooling."""
    player = engine.player
    if player is None:
        return AutoexploreResult(consumed_turns=0, end_reason=AutoexploreEndReason.BLOCKED)

    session = begin_autoexplore(
        player=player,
        game_map=engine.game_map,
        world=engine.world,
        message_log=engine.message_log,
    )
    if session is None:
        return AutoexploreResult(consumed_turns=0, end_reason=AutoexploreEndReason.BLOCKED)

    marker = attach_autoexplore_attack_listener(session)
    end_reason: AutoexploreEndReason | None = None
    idle_steps = 0
    try:
        while session.active:
            consumed_before = session.consumed
            end_reason = advance_autoexplore_turn(
                engine=engine,
                session=session,
                consume_turn=consume_turn,
            )
            if end_reason is not None:
                session.active = False
                break
            if session.consumed == consumed_before:
                idle_steps += 1
                if idle_steps >= 8:
                    engine.message_log.add(messages.autoexplore_complete())
                    end_reason = AutoexploreEndReason.COMPLETE
                    session.active = False
                    break
            else:
                idle_steps = 0
    finally:
        detach_autoexplore_attack_listener(marker)

    return AutoexploreResult(consumed_turns=session.consumed, end_reason=end_reason)


def attach_autoexplore_attack_listener(
    session: AutoexploreSession,
) -> Callable[[], None]:
    return attach_attack_interrupt_listener(session)


def detach_autoexplore_attack_listener(marker: Callable[[], None]) -> None:
    detach_attack_interrupt_listener(marker)