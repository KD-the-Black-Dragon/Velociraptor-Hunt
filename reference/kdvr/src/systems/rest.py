from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from tcod.ecs import Entity, Registry

from src import messages
from src.components import Engulfed, Fighter, Position, Stunned
from src.constants import REST_UNTIL_MAX_TURNS
from src.map_gen import GameMap
from src.message_log import MessageCategory, MessageLog
from src.systems.ai.targeting import _visible_good_evils  # test patch target
from src.systems.danger_interrupts import (
    DangerInterruptReason,
    attach_attack_interrupt_listener,
    detach_attack_interrupt_listener,
    evaluate_danger_interrupt,
    find_good_ally_alarm_shouter,
)
from src.systems.fov import entity_visible_to_player, player_has_visible_evil

REST_MAX_SILENT_TURNS_PER_FRAME = 16


class RestEndReason(Enum):
    BLOCKED = "blocked"
    ATTACK = "attack"
    DANGER = "danger"
    ALLY_ALARM = "ally_alarm"
    HEALED = "healed"
    CAP = "cap"


@dataclass(frozen=True)
class RestResult:
    consumed_turns: int
    end_reason: RestEndReason | None


@dataclass
class RestSession:
    active: bool = True
    consumed: int = 0
    max_turns: int = REST_UNTIL_MAX_TURNS
    attack_interrupt: bool = False

    def clear_attack_interrupt(self) -> None:
        self.attack_interrupt = False


@dataclass(frozen=True)
class RestFrameResult:
    screen_dirty: bool
    finished: bool


def rest_visible_fingerprint(
    *,
    player: Entity,
    game_map: GameMap,
    world: Registry,
    message_log: MessageLog,
) -> tuple[int, bool, tuple[tuple[int, int, int], ...], int]:
    """Snapshot of player-visible state for rest frame dirty detection."""
    fighter = player.components.get(Fighter)
    hp = fighter.hp if fighter is not None else 0
    stunned = Stunned in player.tags
    visible_positions: list[tuple[int, int, int]] = []
    for entity in world.Q.all_of(components=[Position]):
        if entity is not player and not entity_visible_to_player(game_map, entity):
            continue
        pos = entity.components[Position]
        visible_positions.append((id(entity), pos.x, pos.y))
    return (
        hp,
        stunned,
        tuple(sorted(visible_positions)),
        len(message_log.entries()),
    )


def begin_rest_until_healed_or_danger(
    *,
    player: Entity,
    game_map: GameMap,
    world: Registry,
    message_log: MessageLog,
    max_turns: int = REST_UNTIL_MAX_TURNS,
) -> RestSession | None:
    """Pre-checks and start message. Returns None when rest is blocked."""
    if Engulfed in player.tags:
        message_log.add(
            messages.rest_engulfed_no_time(),
            category=MessageCategory.DANGER,
        )
        return None

    fighter = player.components.get(Fighter)
    if fighter is None:
        return None

    if fighter.hp >= fighter.max_hp:
        message_log.add(messages.rest_already_full_health())
        return None

    if player_has_visible_evil(game_map, world):
        message_log.add(
            messages.rest_too_dangerous_now(),
            category=MessageCategory.DANGER,
        )
        return None

    message_log.add(messages.rest_start())
    return RestSession(max_turns=max_turns)


def _danger_to_rest_end(reason: DangerInterruptReason) -> RestEndReason:
    return RestEndReason(reason.value)


def _evaluate_rest_stop(
    *,
    player: Entity,
    game_map: GameMap,
    world: Registry,
    message_log: MessageLog,
    session: RestSession,
) -> RestEndReason | None:
    danger = evaluate_danger_interrupt(
        player=player,
        game_map=game_map,
        world=world,
        message_log=message_log,
        attack_interrupt=session.attack_interrupt,
    )
    if danger is not None:
        return _danger_to_rest_end(danger)

    fighter = player.components.get(Fighter)
    if fighter is not None and fighter.hp >= fighter.max_hp:
        message_log.add(
            messages.rest_fully_healed(),
            category=MessageCategory.POSITIVE,
        )
        return RestEndReason.HEALED

    if session.consumed >= session.max_turns:
        message_log.add(messages.rest_finish())
        return RestEndReason.CAP

    return None


def advance_rest_turn(
    *,
    player: Entity,
    game_map: GameMap,
    world: Registry,
    message_log: MessageLog,
    session: RestSession,
    consume_turn: Callable[[], None],
) -> RestEndReason | None:
    """Consume one rest turn and return a stop reason when rest should end."""
    if not session.active:
        return RestEndReason.BLOCKED

    session.clear_attack_interrupt()
    consume_turn()
    session.consumed += 1
    return _evaluate_rest_stop(
        player=player,
        game_map=game_map,
        world=world,
        message_log=message_log,
        session=session,
    )


def advance_rest_frame(
    *,
    player: Entity,
    game_map: GameMap,
    world: Registry,
    message_log: MessageLog,
    session: RestSession,
    consume_turn: Callable[[], None],
) -> RestFrameResult:
    """Advance up to REST_MAX_SILENT_TURNS_PER_FRAME turns; re-render only when visible state changes."""
    if not session.active:
        return RestFrameResult(screen_dirty=False, finished=True)

    before = rest_visible_fingerprint(
        player=player,
        game_map=game_map,
        world=world,
        message_log=message_log,
    )
    for _ in range(REST_MAX_SILENT_TURNS_PER_FRAME):
        end_reason = advance_rest_turn(
            player=player,
            game_map=game_map,
            world=world,
            message_log=message_log,
            session=session,
            consume_turn=consume_turn,
        )
        if end_reason is not None:
            session.active = False
            after = rest_visible_fingerprint(
                player=player,
                game_map=game_map,
                world=world,
                message_log=message_log,
            )
            return RestFrameResult(screen_dirty=before != after, finished=True)

        after = rest_visible_fingerprint(
            player=player,
            game_map=game_map,
            world=world,
            message_log=message_log,
        )
        if before != after:
            return RestFrameResult(screen_dirty=True, finished=False)

    return RestFrameResult(screen_dirty=False, finished=False)


def try_rest_until_healed_or_danger(
    *,
    player: Entity,
    game_map: GameMap,
    world: Registry,
    message_log: MessageLog,
    consume_turn: Callable[[], None],
    max_turns: int = REST_UNTIL_MAX_TURNS,
) -> RestResult:
    """Synchronous rest loop for tests and tooling."""
    session = begin_rest_until_healed_or_danger(
        player=player,
        game_map=game_map,
        world=world,
        message_log=message_log,
        max_turns=max_turns,
    )
    if session is None:
        return RestResult(consumed_turns=0, end_reason=RestEndReason.BLOCKED)

    marker = attach_rest_attack_listener(session)
    end_reason: RestEndReason | None = None
    try:
        while session.active:
            end_reason = advance_rest_turn(
                player=player,
                game_map=game_map,
                world=world,
                message_log=message_log,
                session=session,
                consume_turn=consume_turn,
            )
            if end_reason is not None:
                session.active = False
    finally:
        detach_rest_attack_listener(marker)

    return RestResult(consumed_turns=session.consumed, end_reason=end_reason)


def attach_rest_attack_listener(session: RestSession) -> Callable[[], None]:
    return attach_attack_interrupt_listener(session)


def detach_rest_attack_listener(marker: Callable[[], None]) -> None:
    detach_attack_interrupt_listener(marker)