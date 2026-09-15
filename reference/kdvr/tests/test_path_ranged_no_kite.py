"""RangeN (path) units stand ground and approach stunned prey for vore."""

from __future__ import annotations

import random

from tcod.ecs import Registry

from src.components import (
    AI,
    AIState,
    Abilities,
    AbilityState,
    Alignment,
    DisplayName,
    Fighter,
    NPCAlignment,
    Player,
    Position,
    SpeciesId,
    Stunned,
)
from src.data.ability_parser import parse_abilities
from src.map_gen import GameMap, Tile


def _choose_path_dir(*args, **kwargs):
    import src.systems.ai  # noqa: F401 — break abilities↔ai circular import
    from src.systems.abilities import choose_path_ranged_move_direction

    return choose_path_ranged_move_direction(*args, **kwargs)


def _open_map(width: int = 20, height: int = 20) -> GameMap:
    game_map = GameMap(width=width, height=height)
    game_map.tiles[:, :] = Tile.FLOOR
    return game_map


def _spawn_fox(world: Registry, x: int, y: int) -> object:
    e = world[object()]
    e.components[Position] = Position(x, y)
    e.components[AI] = AI()
    e.components[AIState] = AIState()
    e.components[AbilityState] = AbilityState()
    e.components[Abilities] = Abilities(parsed=parse_abilities(["Range5", "NoChase"]))
    from src.systems.ranged_magazine import ensure_ranged_magazine

    ensure_ranged_magazine(e, maximum=2)
    e.components[Fighter] = Fighter(
        hp=10,
        max_hp=10,
        accuracy=0.4,
        evade=2,
        ac=1,
        min_damage=1,
        max_damage=2,
        ranged_accuracy=1.0,
        ranged_min_damage=5,
        ranged_max_damage=7,
    )
    e.components[NPCAlignment] = NPCAlignment(alignment=Alignment.EVIL)
    e.components[DisplayName] = DisplayName(name="fox archer")
    e.components[SpeciesId] = SpeciesId(id="fox_archer")
    return e


def _spawn_player(world: Registry, x: int, y: int, *, stunned: bool = False) -> object:
    p = world[object()]
    p.tags.add(Player)
    p.components[Position] = Position(x, y)
    p.components[Fighter] = Fighter(
        hp=0 if stunned else 30,
        max_hp=30,
        accuracy=1.5,
        evade=1,
        ac=1,
        min_damage=1,
        max_damage=2,
    )
    if stunned:
        p.tags.add(Stunned)
    return p


def test_path_ranged_does_not_kite_when_closer_than_max_range() -> None:
    world = Registry()
    game_map = _open_map()
    fox = _spawn_fox(world, 5, 5)
    player = _spawn_player(world, 7, 5)
    rng = random.Random(0)
    direction = _choose_path_dir(
        fox,
        world,
        game_map,
        player,
        rng,
        alignment=Alignment.EVIL,
        entity_target=player,
        player_engulfed=False,
        blocked=frozenset(),
        monster_pos=Position(5, 5),
    )
    assert direction is None, "RangeN must stand ground, not kite away"


def test_path_ranged_closes_when_too_far() -> None:
    world = Registry()
    game_map = _open_map()
    fox = _spawn_fox(world, 2, 2)
    player = _spawn_player(world, 10, 2)
    rng = random.Random(0)
    direction = _choose_path_dir(
        fox,
        world,
        game_map,
        player,
        rng,
        alignment=Alignment.EVIL,
        entity_target=player,
        player_engulfed=False,
        blocked=frozenset(),
        monster_pos=Position(2, 2),
    )
    assert direction is not None
    assert direction[0] > 0


def test_path_ranged_approaches_stunned_player() -> None:
    world = Registry()
    game_map = _open_map()
    fox = _spawn_fox(world, 5, 5)
    player = _spawn_player(world, 8, 5, stunned=True)
    rng = random.Random(0)
    direction = _choose_path_dir(
        fox,
        world,
        game_map,
        player,
        rng,
        alignment=Alignment.EVIL,
        entity_target=player,
        player_engulfed=False,
        blocked=frozenset(),
        monster_pos=Position(5, 5),
    )
    assert direction is not None, "must approach stunned prey for vore"
    assert direction[0] > 0


def test_path_ranged_stunned_adjacent_holds_for_vore() -> None:
    world = Registry()
    game_map = _open_map()
    fox = _spawn_fox(world, 5, 5)
    player = _spawn_player(world, 6, 5, stunned=True)
    rng = random.Random(0)
    direction = _choose_path_dir(
        fox,
        world,
        game_map,
        player,
        rng,
        alignment=Alignment.EVIL,
        entity_target=player,
        player_engulfed=False,
        blocked=frozenset(),
        monster_pos=Position(5, 5),
    )
    assert direction is None
