"""Enhancements 2: identity, combat messaging, faction AI."""

from __future__ import annotations

import random

from src import messages
from src.components import (
    AI,
    Alignment,
    DisplayName,
    ExamineDescription,
    Fighter,
    Item,
    NPCAlignment,
    Position,
    ProperName,
    Stunned,
    VoreCapable,
    VoreNarratives,
)
from src.engine import GameEngine
from src.spawn import WOLF_EXAMINE_DESCRIPTION

from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_east_of,
    carve_floor_rect,
    ensure_adjacent_floor,
    first_wolf,
    isolate_other_ais,
    iter_wolves,
)
from src.systems.ai import (
    pick_hostile_target,
    run_monster_turns,
    spawn_test_npc,
    _choose_chase_direction,
    _forbidden_tiles,
)
from src.systems.combat import try_action
from src.systems.fov import update_fov
from src.systems.vore import VoreModalState, should_attempt_vore
from src.systems.naming import (
    DEFAULT_SPECIES,
    entity_display_name,
    entity_log_name,
    entity_log_possessive,
    entity_species,
)


def _make_wolf_engine(*, seed: int = 42) -> GameEngine:
    engine = GameEngine()
    engine.new_game(seed=seed)
    return engine


def test_entity_species_from_display_name() -> None:
    engine = _make_wolf_engine()
    assert entity_species(first_wolf(engine)) == "wolf"


def test_entity_species_fallback() -> None:
    engine = _make_wolf_engine()
    wolf = first_wolf(engine)
    wolf.components.pop(DisplayName, None)
    assert entity_species(wolf) == DEFAULT_SPECIES


def test_entity_log_name_species_mid_sentence() -> None:
    engine = _make_wolf_engine()
    assert entity_log_name(first_wolf(engine)) == "the wolf"


def test_entity_log_name_species_sentence_start() -> None:
    engine = _make_wolf_engine()
    assert entity_log_name(first_wolf(engine), sentence_start=True) == "The wolf"


def test_entity_log_name_proper_name() -> None:
    engine = _make_wolf_engine()
    wolf = first_wolf(engine)
    wolf.components[ProperName] = ProperName(name="Bob")
    assert entity_log_name(wolf) == "Bob"


def test_entity_log_possessive_species() -> None:
    engine = _make_wolf_engine()
    assert entity_log_possessive(first_wolf(engine)) == "the wolf's"


def test_entity_log_possessive_proper_name() -> None:
    engine = _make_wolf_engine()
    wolf = first_wolf(engine)
    wolf.components[ProperName] = ProperName(name="Fang")
    assert entity_log_possessive(wolf) == "Fang's"


def test_vore_log_messages_no_the_before_proper_name() -> None:
    assert (
        messages.vore_attempt_evaded("Fang's")
        == "You evaded Fang's vore attempt."
    )
    assert messages.vore_escaped("Fang") == "You escape from Fang."
    assert "the Fang" not in messages.vore_attempt_evaded("Fang's")
    assert "the Fang" not in messages.vore_escaped("Fang")


def test_vore_log_messages_article_for_species() -> None:
    assert (
        messages.vore_attempt_evaded("the wolf's")
        == "You evaded the wolf's vore attempt."
    )
    assert messages.vore_escaped("the wolf") == "You escape from the wolf."


def _vore_capable_test_npc(
    engine: GameEngine,
    *,
    x: int,
    y: int,
    species: str,
    alignment: Alignment,
):
    npc = spawn_test_npc(
        engine.world,
        x=x,
        y=y,
        species=species,
        alignment=alignment,
    )
    npc.tags.add(VoreCapable)
    npc.components[VoreNarratives] = VoreNarratives(types=("OV", "CV", "AV"))
    return npc


def test_good_npc_never_attempts_vore() -> None:
    engine = _make_wolf_engine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    pos = player.components[Position]
    npc_pos = ensure_adjacent_floor(engine, pos, (1, 0))
    knight = _vore_capable_test_npc(
        engine,
        x=npc_pos.x,
        y=npc_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    update_fov(engine.game_map, pos.x, pos.y)
    assert (
        should_attempt_vore(knight, player, engine.game_map, random.Random(0)) is False
    )


def test_neutral_npc_never_attempts_vore() -> None:
    engine = _make_wolf_engine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    pos = player.components[Position]
    npc_pos = ensure_adjacent_floor(engine, pos, (1, 0))
    villager = _vore_capable_test_npc(
        engine,
        x=npc_pos.x,
        y=npc_pos.y,
        species="villager",
        alignment=Alignment.NEUTRAL,
    )
    update_fov(engine.game_map, pos.x, pos.y)
    assert (
        should_attempt_vore(villager, player, engine.game_map, random.Random(0))
        is False
    )


def test_good_npc_does_not_open_vore_modal() -> None:
    engine = _make_wolf_engine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    pos = player.components[Position]
    npc_pos = ensure_adjacent_floor(engine, pos, (1, 0))
    _vore_capable_test_npc(
        engine,
        x=npc_pos.x,
        y=npc_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    update_fov(engine.game_map, pos.x, pos.y)
    modal = VoreModalState()
    opened = run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
        modal=modal,
    )
    assert opened is False
    assert not modal.active


def test_entity_display_name_species_only() -> None:
    engine = _make_wolf_engine()
    assert entity_display_name(first_wolf(engine)) == "wolf"


def test_wolves_spawn_evil_alignment() -> None:
    engine = _make_wolf_engine()
    for monster in engine.world.Q.all_of(tags=[VoreCapable], components=[AI]):
        alignment = monster.components.get(NPCAlignment)
        assert alignment is not None
        assert alignment.alignment == Alignment.EVIL


def test_no_proper_names_on_spawn() -> None:
    engine = _make_wolf_engine()
    named = [
        m
        for m in engine.world.Q.all_of(tags=[VoreCapable])
        if m.components.get(ProperName) is not None
    ]
    assert named == []


def test_wolf_has_examine_description() -> None:
    engine = _make_wolf_engine()
    for monster in iter_wolves(engine):
        desc = monster.components.get(ExamineDescription)
        assert desc is not None
        assert desc.text == WOLF_EXAMINE_DESCRIPTION


def test_potion_has_examine_description() -> None:
    from src.components import ItemCategory

    engine = _make_wolf_engine()
    potions = [
        item
        for item in engine.world.Q.all_of(components=[Item])
        if item.components[Item].category == ItemCategory.POTION
    ]
    assert potions
    for item in potions:
        desc = item.components.get(ExamineDescription)
        assert desc is not None
        assert desc.text.strip()


def test_player_hit_wolf_uses_species_name() -> None:
    import random

    engine = _make_wolf_engine()
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    mpos = wolf.components[Position]
    player.components[Position] = Position(mpos.x - 1, mpos.y)
    rng = random.Random(0)
    for _ in range(20):
        try_action(
            engine.world,
            engine.game_map,
            player,
            (1, 0),
            engine.message_log,
            rng=rng,
        )
        if any("You hit the wolf for" in line for line in engine.message_log.lines()):
            break
    assert any("You hit the wolf for" in line for line in engine.message_log.lines())


def test_wolf_hit_player_uses_species_name() -> None:
    import random

    engine = _make_wolf_engine()
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    pos = player.components[Position]
    wolf.components[Position] = Position(pos.x - 1, pos.y)
    # Seeded + retry: high stock player evade can miss unseeded single bump.
    rng = random.Random(0)
    for _ in range(20):
        try_action(
            engine.world,
            engine.game_map,
            wolf,
            (1, 0),
            engine.message_log,
            rng=rng,
        )
        if any("The wolf hits you for" in line for line in engine.message_log.lines()):
            break
    assert any("The wolf hits you for" in line for line in engine.message_log.lines())


def test_combat_log_never_says_monster() -> None:
    engine = _make_wolf_engine()
    player = engine.player
    assert player is not None
    for wolf in iter_wolves(engine):
        mpos = wolf.components[Position]
        player.components[Position] = Position(mpos.x - 1, mpos.y)
        for _ in range(6):
            try_action(engine.world, engine.game_map, player, (1, 0), engine.message_log)
            if wolf not in list(engine.world.Q.all_of(components=[Fighter])):
                break
    log_text = " ".join(engine.message_log.lines()).lower()
    assert "monster" not in log_text


def test_message_templates_actor_hits_target() -> None:
    assert messages.actor_hits_target("Bob", "you", 2) == "Bob hits you for 2 damage."
    assert messages.actor_hits_target("You", "the wolf", 3) == "You hit the wolf for 3 damage."
    assert (
        messages.actor_hits_target_no_damage("You", "the wolf")
        == "You hit the wolf but deal no damage."
    )
    assert messages.actor_misses_target("You", "the wolf") == "You miss the wolf."
    assert messages.actor_misses_target("The wolf", "you") == "The wolf misses you."
    assert messages.target_defeated("The wolf") == "The wolf was defeated."


def test_message_templates_smite_and_shoot() -> None:
    assert (
        messages.npc_smites_target("The wolf", "you", 4)
        == "The wolf smites you for 4 damage."
    )
    assert (
        messages.npc_smites_at_target_miss("The wolf", "you")
        == "The wolf smites you but misses."
    )
    assert (
        messages.player_smites_target("the wolf", 3)
        == "You smite the wolf for 3 damage."
    )
    assert (
        messages.player_smites_at_target_miss("the wolf")
        == "You smite the wolf but miss."
    )
    assert (
        messages.npc_shoots_target("The fox archer", "you", 2)
        == "The fox archer shoots you for 2 damage."
    )


def test_evil_prefers_nearest_hostile() -> None:
    engine = _make_wolf_engine(seed=42)
    carve_floor_rect(engine, 9, 10, 14, 10)
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    origin = Position(10, 10)
    wolf.components[Position] = origin
    player.components[Position] = Position(14, 10)
    knight = spawn_test_npc(
        engine.world,
        x=12,
        y=10,
        species="knight",
        alignment=Alignment.GOOD,
    )
    update_fov(engine.game_map, origin.x, origin.y)
    target = pick_hostile_target(
        wolf, engine.world, engine.game_map, player, random.Random(0)
    )
    assert target is knight


def test_evil_random_tie_among_equidistant_hostiles() -> None:
    engine = _make_wolf_engine(seed=1)
    carve_floor_rect(engine, 8, 10, 12, 10)
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    origin = Position(10, 10)
    wolf.components[Position] = origin
    player.components[Position] = Position(11, 10)
    knight = spawn_test_npc(
        engine.world, x=9, y=10, species="knight", alignment=Alignment.GOOD
    )
    update_fov(engine.game_map, origin.x, origin.y)
    picks = {
        pick_hostile_target(
            wolf, engine.world, engine.game_map, player, random.Random(seed)
        )
        for seed in range(20)
    }
    assert player in picks
    assert knight in picks


def test_good_chases_evil_not_player() -> None:
    engine = _make_wolf_engine(seed=5)
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    isolate_other_ais(engine, keep=(wolf,))
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 10, ARENA_Y + 2)
    player.components[Position] = Position(ARENA_X + 2, ARENA_Y)
    knight = spawn_test_npc(
        engine.world,
        x=ARENA_X + 2,
        y=ARENA_Y + 2,
        species="knight",
        alignment=Alignment.GOOD,
    )
    wolf.components[Position] = Position(ARENA_X + 5, ARENA_Y + 2)
    update_fov(engine.game_map, knight.components[Position].x, knight.components[Position].y)
    knight_pos_before = knight.components[Position]
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
    )
    assert knight.components[Position] != knight_pos_before
    assert player.components[Position] == Position(ARENA_X + 2, ARENA_Y)


def test_good_does_not_step_on_player_tile() -> None:
    engine = _make_wolf_engine()
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    knight_pos = ensure_adjacent_floor(engine, pos, (1, 0))
    knight = spawn_test_npc(
        engine.world,
        x=knight_pos.x,
        y=knight_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    blocked = _forbidden_tiles(knight, player)
    direction = _choose_chase_direction(
        engine.world,
        engine.game_map,
        knight,
        knight.components[Position],
        player.components[Position],
        blocked_tiles=blocked,
    )
    if direction is not None:
        dest = knight.components[Position] + direction
        assert dest != player.components[Position]


def test_neutral_flees_from_visible_evil() -> None:
    engine = _make_wolf_engine(seed=7)
    player = engine.player
    assert player is not None
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 4, ARENA_Y)
    wolf = first_wolf(engine)
    wolf.components[Position] = Position(ARENA_X + 1, ARENA_Y)
    wolf_pos = wolf.components[Position]
    neutral = spawn_test_npc(
        engine.world,
        x=ARENA_X + 2,
        y=ARENA_Y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    neutral_pos_before = neutral.components[Position]
    player.components[Position] = Position(ARENA_X, ARENA_Y)

    def _chebyshev(a: Position, b: Position) -> int:
        return max(abs(a.x - b.x), abs(a.y - b.y))

    update_fov(engine.game_map, neutral_pos_before.x, neutral_pos_before.y)
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
    )
    assert neutral.components[Position] != neutral_pos_before
    assert _chebyshev(neutral.components[Position], wolf_pos) > _chebyshev(
        neutral_pos_before, wolf_pos
    )


def test_neutral_does_not_attack_player() -> None:
    engine = _make_wolf_engine(seed=11)
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    npc_pos = ensure_adjacent_floor(engine, pos, (1, 0))
    spawn_test_npc(
        engine.world,
        x=npc_pos.x,
        y=npc_pos.y,
        species="villager",
        alignment=Alignment.NEUTRAL,
    )
    hp_before = player.components[Fighter].hp
    update_fov(engine.game_map, pos.x, pos.y)
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
    )
    assert player.components[Fighter].hp == hp_before
    assert not any("hits you" in line for line in engine.message_log.lines())


def test_player_swap_with_good_npc() -> None:
    engine = _make_wolf_engine()
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    swap_pos = ensure_adjacent_floor(engine, pos, (1, 0))
    knight = spawn_test_npc(
        engine.world,
        x=swap_pos.x,
        y=swap_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    knight_pos = knight.components[Position]
    player_pos_before = Position(pos.x, pos.y)
    skip_set: set = set()
    assert try_action(
        engine.world,
        engine.game_map,
        player,
        (1, 0),
        engine.message_log,
        skip_turn_entities=skip_set,
    )
    assert player.components[Position] == knight_pos
    assert knight.components[Position] == player_pos_before
    assert knight in skip_set
    assert messages.player_swap_places("the knight") in engine.message_log.lines()
    log_text = " ".join(engine.message_log.lines()).lower()
    assert "hit" not in log_text


def test_player_swap_with_neutral_npc() -> None:
    engine = _make_wolf_engine()
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    swap_pos = ensure_adjacent_floor(engine, pos, (1, 0))
    villager = spawn_test_npc(
        engine.world,
        x=swap_pos.x,
        y=swap_pos.y,
        species="villager",
        alignment=Alignment.NEUTRAL,
    )
    villager_pos = villager.components[Position]
    player_pos_before = Position(pos.x, pos.y)
    skip_set: set = set()
    assert try_action(
        engine.world,
        engine.game_map,
        player,
        (1, 0),
        engine.message_log,
        skip_turn_entities=skip_set,
    )
    assert player.components[Position] == villager_pos
    assert villager.components[Position] == player_pos_before
    assert villager in skip_set
    assert messages.player_swap_places("the villager") in engine.message_log.lines()


def test_player_swap_uses_proper_name() -> None:
    engine = _make_wolf_engine()
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    swap_pos = ensure_adjacent_floor(engine, pos, (1, 0))
    knight = spawn_test_npc(
        engine.world,
        x=swap_pos.x,
        y=swap_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    knight.components[ProperName] = ProperName(name="Sir Aldric")
    try_action(engine.world, engine.game_map, player, (1, 0), engine.message_log)
    assert messages.player_swap_places("Sir Aldric") in engine.message_log.lines()


def test_player_still_attacks_evil_wolf() -> None:
    import random

    engine = _make_wolf_engine()
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    mpos = wolf.components[Position]
    carve_east_of(engine, mpos, 2)
    player.components[Position] = Position(mpos.x - 1, mpos.y)
    skip_set: set = set()
    rng = random.Random(0)
    hit_logged = False
    for _ in range(20):
        assert try_action(
            engine.world,
            engine.game_map,
            player,
            (1, 0),
            engine.message_log,
            skip_turn_entities=skip_set,
            rng=rng,
        )
        if any("You hit the wolf" in line for line in engine.message_log.lines()):
            hit_logged = True
            break
    assert skip_set == set()
    assert hit_logged


def test_swap_skips_npc_turn_this_phase() -> None:
    engine = _make_wolf_engine(seed=5)
    carve_floor_rect(engine, 8, 10, 12, 10)
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    player.components[Position] = Position(9, 10)
    wolf.components[Position] = Position(12, 10)
    knight = spawn_test_npc(
        engine.world,
        x=10,
        y=10,
        species="knight",
        alignment=Alignment.GOOD,
    )
    skip_set: set = set()
    try_action(
        engine.world,
        engine.game_map,
        player,
        (1, 0),
        engine.message_log,
        skip_turn_entities=skip_set,
    )
    assert knight in skip_set
    knight_pos_after_swap = knight.components[Position]
    update_fov(engine.game_map, knight_pos_after_swap.x, knight_pos_after_swap.y)
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
        skipped=skip_set,
    )
    assert knight.components[Position] == knight_pos_after_swap


def test_stunned_player_cannot_swap() -> None:
    engine = _make_wolf_engine()
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    knight_pos = ensure_adjacent_floor(engine, pos, (1, 0))
    knight = spawn_test_npc(
        engine.world,
        x=knight_pos.x,
        y=knight_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    knight_pos_before = knight.components[Position]
    player_pos_before = Position(pos.x, pos.y)
    player.tags.add(Stunned)
    skip_set: set = set()
    assert not try_action(
        engine.world,
        engine.game_map,
        player,
        (1, 0),
        engine.message_log,
        skip_turn_entities=skip_set,
    )
    assert skip_set == set()
    assert player.components[Position] == player_pos_before
    assert knight.components[Position] == knight_pos_before