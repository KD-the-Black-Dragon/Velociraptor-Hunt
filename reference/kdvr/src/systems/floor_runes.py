from __future__ import annotations

import random
from collections import deque
from functools import lru_cache

from tcod.ecs import Entity, Registry

from src.components import (
    BlocksMovement,
    ExamineDescription,
    Fighter,
    FloorRune,
    Player,
    PlayerProgression,
    Position,
    Renderable,
    ScreenFlashState,
)
from src.run_stats import RunStats
from src.constants import (
    MIN_PAIRWISE_SPREAD_BFS,
    PLAYER_MAX_HP,
    RUNE_SPAWN_MIN_DISTANCE,
    RUNES_PER_FLOOR,
)
from src.data.floor_rune_loader import load_floor_rune_registry
from src.data.floor_rune_registry import FloorRuneDefinition, FloorRuneRegistry, RuneEffect
from src.map_gen import GameMap, Tile
from src.message_log import MessageCategory, MessageLog


class RunePlacementError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def default_floor_rune_registry() -> FloorRuneRegistry:
    return load_floor_rune_registry()


def reset_floor_rune_registry_cache() -> None:
    default_floor_rune_registry.cache_clear()


def configured_runes_per_floor(
    registry: FloorRuneRegistry | None = None,
) -> int:
    """Global default rune count from floor_runes.json (or RUNES_PER_FLOOR fallback)."""
    reg = registry if registry is not None else default_floor_rune_registry()
    return max(0, int(reg.runes_per_floor))


def bfs_path_distance_from(
    game_map: GameMap,
    origin: tuple[int, int],
    *,
    tile_filter,
    cardinal_only: bool = True,
) -> dict[tuple[int, int], int]:
    """Shortest path distance from origin over tiles passing `tile_filter`."""
    ox, oy = origin
    if not game_map.in_bounds(ox, oy) or not tile_filter(ox, oy):
        return {}

    directions = (
        ((-1, 0), (1, 0), (0, -1), (0, 1))
        if cardinal_only
        else (
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        )
    )

    distances: dict[tuple[int, int], int] = {(ox, oy): 0}
    queue: deque[tuple[int, int]] = deque([(ox, oy)])

    while queue:
        x, y = queue.popleft()
        current = distances[(x, y)]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if not game_map.in_bounds(nx, ny):
                continue
            if not tile_filter(nx, ny):
                continue
            if (nx, ny) in distances:
                continue
            distances[(nx, ny)] = current + 1
            queue.append((nx, ny))

    return distances


def occupied_rune_blocked_tiles(world: Registry) -> set[tuple[int, int]]:
    """Tiles blocked for rune placement: NPCs only (floor items are walk-through)."""
    blocked: set[tuple[int, int]] = set()
    for entity in world.Q.all_of(tags=[BlocksMovement]):
        pos = entity.components.get(Position)
        if pos is not None:
            blocked.add((pos.x, pos.y))
    return blocked


def rune_candidates_with_path_distance(
    game_map: GameMap,
    world: Registry,
    enter_xy: tuple[int, int],
) -> list[tuple[int, int, int]]:
    """Return (x, y, path_distance) for every valid FLOOR placement tile."""
    distances = bfs_path_distance_from(
        game_map,
        enter_xy,
        tile_filter=lambda x, y: game_map.tiles[y, x] == Tile.FLOOR,
        cardinal_only=True,
    )
    blocked = occupied_rune_blocked_tiles(world)
    ex, ey = enter_xy
    candidates: list[tuple[int, int, int]] = []
    for (x, y), dist in distances.items():
        if (x, y) == (ex, ey):
            continue
        if (x, y) in blocked:
            continue
        candidates.append((x, y, dist))
    return candidates


def filter_candidates_by_pairwise_spread(
    candidates: list[tuple[int, int, int]],
    placed: list[tuple[int, int]],
    game_map: GameMap,
    *,
    minimum: int,
) -> list[tuple[int, int, int]]:
    """Keep candidates at least `minimum` BFS steps from every placed rune."""
    if not placed:
        return candidates

    distance_maps = [
        bfs_path_distance_from(
            game_map,
            position,
            tile_filter=lambda x, y: game_map.tiles[y, x] == Tile.FLOOR,
            cardinal_only=True,
        )
        for position in placed
    ]
    filtered: list[tuple[int, int, int]] = []
    for x, y, dist in candidates:
        if all(distances.get((x, y), -1) >= minimum for distances in distance_maps):
            filtered.append((x, y, dist))
    return filtered


def filter_candidates_by_entrance_distance(
    candidates: list[tuple[int, int, int]],
    *,
    minimum: int,
) -> list[tuple[int, int, int]]:
    """Keep candidates at least `minimum` BFS steps from the entrance."""
    return [(x, y, dist) for x, y, dist in candidates if dist >= minimum]


def choose_rune_placement(
    candidates: list[tuple[int, int, int]],
    *,
    min_distance: int,
    min_relax_to: int,
    rng: random.Random,
) -> tuple[int, int, int]:
    """Return (x, y, achieved_distance).

    Tries `min_distance` first, relaxing downward only to `min_relax_to`.
    """
    if not candidates:
        raise RunePlacementError("no valid rune tiles")

    start = max(min_distance, min_relax_to)
    for threshold in range(start, min_relax_to - 1, -1):
        pool = [(x, y, dist) for x, y, dist in candidates if dist >= threshold]
        if pool:
            x, y, achieved = rng.choice(pool)
            return x, y, achieved

    raise RunePlacementError("no rune tile satisfies entrance min distance")


def _weighted_rune_choice(
    definitions: tuple[FloorRuneDefinition, ...],
    rng: random.Random,
) -> FloorRuneDefinition:
    weights = [max(0, int(defn.weight)) for defn in definitions]
    if not definitions or sum(weights) == 0:
        raise RunePlacementError("no weighted rune definitions")
    return rng.choices(list(definitions), weights=weights, k=1)[0]


def spawn_rune_entity(
    world: Registry,
    definition: FloorRuneDefinition,
    x: int,
    y: int,
) -> Entity:
    entity = world[object()]
    entity.components[Position] = Position(x, y)
    entity.components[Renderable] = Renderable(
        ch=ord(definition.glyph),
        fg=definition.fg,
    )
    entity.components[ExamineDescription] = ExamineDescription(text=definition.examine)
    entity.components[FloorRune] = FloorRune(rune_id=definition.id)
    entity.tags.add(BlocksMovement)
    return entity


def spawn_floor_rune(
    world: Registry,
    game_map: GameMap,
    floor_depth: int,
    *,
    rng: random.Random | None = None,
    registry: FloorRuneRegistry | None = None,
    min_distance: int = RUNE_SPAWN_MIN_DISTANCE,
    min_pairwise: int = MIN_PAIRWISE_SPREAD_BFS,
    count: int | None = None,
) -> list[Entity]:
    """Place floor runes for this depth on distinct, spread tiles.

    ``count=None`` uses the registry's ``runes_per_floor`` (stock: 3).
    ``count=0`` places no runes (no eligibility check required).
    """
    rng = rng or random.Random()
    reg = registry or default_floor_rune_registry()
    if count is None:
        count = configured_runes_per_floor(reg)
    count = max(0, int(count))
    if count == 0:
        return []

    eligible = reg.eligible_at_depth(floor_depth)
    if not eligible:
        raise RunePlacementError(f"no runes eligible at depth {floor_depth}")

    placed: list[Entity] = []
    placed_positions: list[tuple[int, int]] = []
    for index in range(count):
        candidates = rune_candidates_with_path_distance(
            game_map,
            world,
            game_map.enter_xy,
        )
        candidates = [
            (x, y, dist)
            for x, y, dist in candidates
            if (x, y) not in placed_positions
        ]
        candidates = filter_candidates_by_entrance_distance(
            candidates,
            minimum=min_pairwise,
        )
        if not candidates:
            raise RunePlacementError("no valid rune tiles")

        definition = _weighted_rune_choice(eligible, rng)
        if index == 0:
            x, y, _achieved = choose_rune_placement(
                candidates,
                min_distance=min_distance,
                min_relax_to=min_pairwise,
                rng=rng,
            )
        else:
            spread_pool = filter_candidates_by_pairwise_spread(
                candidates,
                placed_positions,
                game_map,
                minimum=min_pairwise,
            )
            if not spread_pool:
                raise RunePlacementError("insufficient pairwise spread for rune placement")
            x, y, _achieved = rng.choice(spread_pool)

        placed_positions.append((x, y))
        placed.append(spawn_rune_entity(world, definition, x, y))

    return placed


def count_floor_runes(world: Registry) -> int:
    return len(list(world.Q.all_of(components=[FloorRune])))


def _player_progression(player: Entity) -> PlayerProgression:
    prog = player.components.get(PlayerProgression)
    if prog is None:
        prog = PlayerProgression()
        player.components[PlayerProgression] = prog
    return prog


def _effect_bonus_text(effect: RuneEffect) -> str:
    match effect.type:
        case "max_hp":
            return f"+{int(effect.amount)} max HP"
        case "accuracy":
            return f"+{effect.amount} accuracy"
        case "natural_ac":
            return f"+{int(effect.amount)} AC"
        case "natural_evade":
            amount = effect.amount or 0
            if float(amount) == int(amount):
                return f"+{int(amount)} evade"
            return f"+{float(amount):g} evade"
        case "accuracy_damage":
            parts: list[str] = []
            if effect.accuracy:
                parts.append(f"+{effect.accuracy} accuracy")
            if effect.min_damage:
                parts.append(f"+{effect.min_damage} min damage")
            if effect.max_damage:
                parts.append(f"+{effect.max_damage} max damage")
            return ", ".join(parts) if parts else "no bonus"
        case _:
            return effect.type


def _apply_max_hp_unit(player: Entity, amount: int) -> None:
    prog = _player_progression(player)
    fighter = player.components[Fighter]
    prog.bonus_max_hp += amount
    fighter.max_hp = PLAYER_MAX_HP + prog.bonus_max_hp
    fighter.hp = min(fighter.max_hp, fighter.hp + amount)


def _bank_fields(prog: PlayerProgression, bank: str) -> tuple[str, str, str]:
    """Return (pieces_attr, need_attr, frozen_attr) for a bank id."""
    mapping = {
        "max_hp": (
            "pieces_max_hp",
            "pieces_need_max_hp",
            "pieces_max_hp_need_frozen",
        ),
        "accuracy": (
            "pieces_accuracy",
            "pieces_need_accuracy",
            "pieces_accuracy_need_frozen",
        ),
        "ac": ("pieces_ac", "pieces_need_ac", "pieces_ac_need_frozen"),
        "evade": ("pieces_evade", "pieces_need_evade", "pieces_evade_need_frozen"),
        "min_damage": (
            "pieces_min_damage",
            "pieces_need_min_damage",
            "pieces_min_damage_need_frozen",
        ),
        "max_damage": (
            "pieces_max_damage",
            "pieces_need_max_damage",
            "pieces_max_damage_need_frozen",
        ),
    }
    if bank not in mapping:
        raise ValueError(f"unknown piece bank '{bank}'")
    return mapping[bank]


def _active_banks(effect: RuneEffect) -> list[tuple[str, object]]:
    """(bank_id, apply_one_unit callable taking player) for this effect."""
    from collections.abc import Callable

    banks: list[tuple[str, Callable[[Entity], None]]] = []
    match effect.type:
        case "max_hp":
            amount = int(effect.amount or 0)

            def apply_hp(player: Entity, *, _a: int = amount) -> None:
                _apply_max_hp_unit(player, _a)

            banks.append(("max_hp", apply_hp))
        case "accuracy":
            amount = float(effect.amount or 0.0)

            def apply_acc(player: Entity, *, _a: float = amount) -> None:
                _player_progression(player).bonus_accuracy += _a

            banks.append(("accuracy", apply_acc))
        case "natural_ac":
            amount = int(effect.amount or 0)

            def apply_ac(player: Entity, *, _a: int = amount) -> None:
                _player_progression(player).bonus_ac += _a

            banks.append(("ac", apply_ac))
        case "natural_evade":
            amount = float(effect.amount or 0.0)

            def apply_evade(player: Entity, *, _a: float = amount) -> None:
                _player_progression(player).bonus_evade += _a

            banks.append(("evade", apply_evade))
        case "accuracy_damage":
            acc = float(effect.accuracy or 0.0)
            min_d = int(effect.min_damage or 0)
            max_d = int(effect.max_damage or 0)
            if acc != 0.0:

                def apply_acc2(player: Entity, *, _a: float = acc) -> None:
                    _player_progression(player).bonus_accuracy += _a

                banks.append(("accuracy", apply_acc2))
            if min_d != 0:

                def apply_min(player: Entity, *, _a: int = min_d) -> None:
                    _player_progression(player).bonus_min_damage += _a

                banks.append(("min_damage", apply_min))
            if max_d != 0:

                def apply_max(player: Entity, *, _a: int = max_d) -> None:
                    _player_progression(player).bonus_max_damage += _a

                banks.append(("max_damage", apply_max))
        case _:
            raise ValueError(f"unsupported rune effect type '{effect.type}'")
    return banks  # type: ignore[return-value]


def _bank_label(bank: str) -> str:
    return {
        "max_hp": "HP",
        "accuracy": "Acc",
        "ac": "AC",
        "evade": "Evade",
        "min_damage": "Dam",
        "max_damage": "Dam",
    }.get(bank, bank)


def apply_rune_effect(
    player: Entity,
    effect: RuneEffect,
    *,
    rune_pieces_multiplier: int = 1,
) -> str:
    """Apply a permanent rune buff. Returns runtime outcome text for the log.

    Piece thresholds: ``need = pieces_per_bonus * rune_pieces_multiplier`` (sticky
    freeze on first grant to each bank). Partial pieces never affect combat.
    ``accuracy_damage`` splits pieces into active sub-field banks.
    """
    prog = _player_progression(player)
    multiplier = max(1, int(rune_pieces_multiplier))
    base_need = max(1, int(effect.pieces_per_bonus))
    grant = max(1, int(effect.pieces_granted))
    need_from_effect = max(1, base_need * multiplier)

    banks = _active_banks(effect)
    if not banks:
        return "no bonus"

    completed_labels: list[str] = []
    partial_labels: list[str] = []
    any_complete = False
    pure_legacy = base_need == 1 and multiplier == 1 and grant == 1

    for bank_id, apply_unit in banks:
        pieces_attr, need_attr, frozen_attr = _bank_fields(prog, bank_id)
        frozen = bool(getattr(prog, frozen_attr))
        if not frozen:
            setattr(prog, need_attr, need_from_effect)
            setattr(prog, frozen_attr, True)
        need = max(1, int(getattr(prog, need_attr)))
        pieces = int(getattr(prog, pieces_attr)) + grant
        completed = 0
        while pieces >= need:
            pieces -= need
            apply_unit(player)
            completed += 1
            any_complete = True
        setattr(prog, pieces_attr, pieces)
        if completed:
            # One-line summary per completed bank unit (last unit's text style)
            if bank_id == "max_hp":
                completed_labels.append(f"+{int(effect.amount or 0) * completed} max HP")
            elif bank_id == "accuracy":
                if effect.type == "accuracy":
                    completed_labels.append(
                        f"+{float(effect.amount or 0) * completed} accuracy"
                    )
                else:
                    completed_labels.append(
                        f"+{float(effect.accuracy or 0) * completed} accuracy"
                    )
            elif bank_id == "ac":
                completed_labels.append(f"+{int(effect.amount or 0) * completed} AC")
            elif bank_id == "min_damage":
                completed_labels.append(
                    f"+{int(effect.min_damage or 0) * completed} min damage"
                )
            elif bank_id == "max_damage":
                completed_labels.append(
                    f"+{int(effect.max_damage or 0) * completed} max damage"
                )
        if pieces > 0:
            partial_labels.append(f"{_bank_label(bank_id)} {pieces}/{need}")

    if pure_legacy and any_complete and not partial_labels:
        return _effect_bonus_text(effect)

    parts: list[str] = []
    if completed_labels:
        joined = ", ".join(completed_labels)
        if pure_legacy:
            parts.append(joined)
        else:
            parts.append(f"{joined}; complete" if not partial_labels else joined)
    if partial_labels:
        parts.append("; ".join(partial_labels))
    if not parts:
        return _effect_bonus_text(effect)
    return "; ".join(parts) if len(parts) > 1 and completed_labels and partial_labels else (
        parts[0] if len(parts) == 1 else "; ".join(parts)
    )


def try_activate_floor_rune(
    world: Registry,
    player: Entity,
    x: int,
    y: int,
    message_log: MessageLog,
    *,
    screen_flash: ScreenFlashState | None = None,
    registry: FloorRuneRegistry | None = None,
    run_stats: RunStats | None = None,
    rune_pieces_multiplier: int = 1,
) -> bool:
    """Step-on activation for floor runes. Returns True when a rune was consumed."""
    if Player not in player.tags:
        return False

    target = Position(x, y)
    rune_entities = list(world.Q.all_of(tags=[target], components=[FloorRune]))
    if not rune_entities:
        return False

    from src import messages

    reg = registry or default_floor_rune_registry()
    activated = False
    for entity in rune_entities:
        rune = entity.components[FloorRune]
        definition = reg.get(rune.rune_id)
        bonus = apply_rune_effect(
            player,
            definition.effect,
            rune_pieces_multiplier=rune_pieces_multiplier,
        )
        message_log.add(
            messages.rune_activated(definition.display_name, bonus),
            category=MessageCategory.MAGICAL,
        )
        if screen_flash is not None:
            screen_flash.pending = True
            screen_flash.color = definition.fg
        entity.clear()
        activated = True

    if activated and run_stats is not None:
        run_stats.record_rune_collected()
    return activated