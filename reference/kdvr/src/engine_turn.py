"""Turn pipeline for GameEngine: consume turn, world phase, regen, digestion, rest.

PR5 extract + PR7 facade cleanup. Call via ``GameEngine`` methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tcod.ecs import Entity

from src import messages
from src.components import (
    AI,
    Alignment,
    DigestionStrikes,
    Engulfed,
    Fighter,
    NPCAlignment,
    Predator,
    Stunned,
    VoreMercy,
)
from src.constants import (
    EVIL_NATURAL_REGEN_EVERY_N_PLAYER_TURNS,
    NATURAL_REGEN_EVERY_N_PLAYER_TURNS,
    NATURAL_REGEN_HP,
)
from src.data.entity_loader import get_entity_registry
from src.data.names_loader import get_names_registry
from src.events import fire_player_turn_consumed, fire_vore_attempt
from src.game_over_ending import GameOverEnding
from src.message_log import MessageCategory
from src.systems.ai import run_monster_turns
from src.systems.ally_introduction import try_good_introductions
from src.systems.combat import heal
from src.systems.digestion import (
    apply_player_digestion_tick,
    complete_player_digestion,
    player_digestion_modal_phases,
)
from src.systems.fov import entity_visible_to_player
from src.systems.naming import entity_log_name, entity_log_possessive, entity_type_id
from src.systems.projectile_anim import (
    ProjectileFrameResult,
    advance_projectile_frame,
    begin_projectile_session,
    reset_projectile_queue,
    take_queued_projectiles,
)
from src.systems.autoexplore import (
    AutoexploreFrameResult,
    advance_autoexplore_frame,
    attach_autoexplore_attack_listener,
    begin_autoexplore,
    detach_autoexplore_attack_listener,
)
from src.systems.rest import (
    RestFrameResult,
    advance_rest_frame,
    attach_rest_attack_listener,
    begin_rest_until_healed_or_danger,
    detach_rest_attack_listener,
)
from src.systems.vore import (
    VoreModalSegment,
    engulf_player,
    find_predator_holding_prey,
    get_narrative_phases,
)

if TYPE_CHECKING:
    from src.engine import GameEngine


def begin_projectile_session_from_queue(engine: GameEngine) -> None:
    """Start a cosmetic Path beam session when the queue has specs."""
    queued = take_queued_projectiles()
    if queued:
        engine.projectile_session = begin_projectile_session(queued)


def run_world_turn(engine: GameEngine) -> None:
    """World phase after a player action consumes a turn (monsters, FOV, etc.)."""
    reset_projectile_queue()
    if engine.player is not None:
        run_monster_turns(
            engine.world,
            engine.game_map,
            engine.player,
            engine.message_log,
            rng=engine.rng,
            modal=engine.vore_modal,
            vore_prefs=engine.vore_content_prefs,
            skipped=engine.skipped_this_phase,
            player_turn_count=engine.player_turn_count,
            floor_depth=engine.floor_depth,
            difficulty_id=engine.difficulty_id,
        )
    engine.skipped_this_phase.clear()
    engine._update_fov()
    begin_projectile_session_from_queue(engine)
    for entity in list(engine.world.Q.all_of(tags=[VoreMercy])):
        entity.tags.discard(VoreMercy)


def advance_vore_modal(engine: GameEngine) -> None:
    modal = engine.vore_modal
    player = engine.player
    if player is None or modal.predator is None:
        modal.reset()
        return

    if modal.segment is VoreModalSegment.ATTEMPT:
        if modal.phase_index < len(modal.phases) - 1:
            modal.phase_index += 1
            return
        if not modal.hit:
            engine.message_log.add(
                messages.vore_attempt_evaded(
                    entity_log_possessive(modal.predator)
                )
            )
            fire_vore_attempt(modal.predator, player, hit=False)
            modal.segment = VoreModalSegment.NONE
            modal.resume_monster_index += 1
            reset_projectile_queue()
            if run_monster_turns(
                engine.world,
                engine.game_map,
                player,
                engine.message_log,
                rng=engine.rng,
                modal=modal,
                vore_prefs=engine.vore_content_prefs,
                skipped=engine.skipped_this_phase,
                player_turn_count=engine.player_turn_count,
                floor_depth=engine.floor_depth,
                difficulty_id=engine.difficulty_id,
            ):
                return
            modal.reset()
            engine._update_fov()
            begin_projectile_session_from_queue(engine)
            return
        success_phases = modal.success_phases
        if not success_phases and modal.predator is not None:
            from src.systems.vore import format_player_vore_phase

            success_phases = [
                format_player_vore_phase(phase, modal.predator)
                for phase in get_narrative_phases(
                    entity_type_id(modal.predator),
                    modal.narrative_type,
                    "success",
                )
            ]
        modal.phases = success_phases
        modal.phase_index = 0
        modal.segment = VoreModalSegment.SUCCESS
        return

    if modal.segment is VoreModalSegment.SUCCESS:
        if modal.phase_index < len(modal.phases) - 1:
            modal.phase_index += 1
            return
        engulf_player(
            engine.world,
            player,
            modal.predator,
            engine.message_log,
            narrative_type=modal.narrative_type,
        )
        fire_vore_attempt(modal.predator, player, hit=True)
        modal.reset()
        engine._update_fov()


def regen_blocked_by_digestion(entity: Entity) -> bool:
    strikes = entity.components.get(DigestionStrikes)
    return strikes is not None and strikes.count >= 1


def apply_natural_regen(engine: GameEngine) -> None:
    if engine.player is None:
        return
    if engine.player_turn_count % NATURAL_REGEN_EVERY_N_PLAYER_TURNS == 0:
        fighter = engine.player.components.get(Fighter)
        if (
            fighter is not None
            and Engulfed not in engine.player.tags
            and fighter.hp < fighter.max_hp
            and not engine._regen_blocked_by_digestion(engine.player)
        ):
            was_stunned = Stunned in engine.player.tags
            healed = heal(engine.player, NATURAL_REGEN_HP)
            if healed > 0 and was_stunned and Stunned not in engine.player.tags:
                engine.message_log.add(
                    messages.no_longer_stunned(),
                    category=MessageCategory.POSITIVE,
                )
    engine._apply_npc_natural_regen()


def apply_npc_natural_regen(engine: GameEngine) -> None:
    for entity in engine.world.Q.all_of(components=[AI, Fighter, NPCAlignment]):
        alignment = entity.components[NPCAlignment].alignment
        if alignment in (Alignment.GOOD, Alignment.NEUTRAL):
            if engine.player_turn_count % NATURAL_REGEN_EVERY_N_PLAYER_TURNS != 0:
                continue
        elif alignment == Alignment.EVIL:
            if engine.player_turn_count % EVIL_NATURAL_REGEN_EVERY_N_PLAYER_TURNS != 0:
                continue
        else:
            continue
        fighter = entity.components[Fighter]
        if fighter.hp >= fighter.max_hp:
            continue
        if engine._regen_blocked_by_digestion(entity):
            continue
        was_stunned = Stunned in entity.tags
        healed = heal(entity, NATURAL_REGEN_HP)
        if healed <= 0:
            continue
        if was_stunned and Stunned not in entity.tags:
            if entity_visible_to_player(engine.game_map, entity):
                name = entity_log_name(entity, sentence_start=True)
                engine.message_log.add(
                    messages.npc_no_longer_stunned(name),
                    category=MessageCategory.POSITIVE,
                )


def maybe_apply_player_digestion(engine: GameEngine) -> bool:
    """Digestion tick while engulfed. Returns True when the world phase should wait."""
    player = engine.player
    if player is None or Engulfed not in player.tags:
        return False
    predator = find_predator_holding_prey(engine.world, player)
    if predator is None:
        return False
    result = apply_player_digestion_tick(player, predator, engine.message_log)
    if result.strike_added:
        engine.message_log.add(
            messages.player_being_digested(),
            category=MessageCategory.DANGER,
        )
    if not result.open_modal:
        return False
    predator_state = predator.components.get(Predator)
    narrative_type = (
        predator_state.narrative_type if predator_state is not None else "OV"
    )
    phases = player_digestion_modal_phases(predator, narrative_type, engine.rng)
    engine.digestion_modal.open(predator, phases)
    return True


def advance_digestion_modal(engine: GameEngine) -> None:
    predator = engine.digestion_modal.predator
    player = engine.player
    if predator is None or player is None:
        engine.digestion_modal.reset()
        return
    if not engine.digestion_modal.advance():
        return
    digested_by = complete_player_digestion(player, predator)
    engine.digestion_modal.reset()
    save_store = None
    if engine.save_coordinator is not None and not engine.arena_mode:
        engine.save_coordinator.prepare_for_game_over_wipe()
        save_store = engine.save_coordinator.store
    if engine.macguffin_discovery.active:
        ending = GameOverEnding(
            kind="macguffin",
            detail=engine.macguffin_discovery.display_name,
        )
        macguffin_score = engine.macguffin_discovery.score
    else:
        ending = GameOverEnding(kind="digested", detail=digested_by)
        macguffin_score = None
    profile = engine.difficulty_profile()
    engine.game_over.open(
        player_name=engine.player_name,
        ending=ending,
        monsters_defeated=engine.run_stats.monsters_defeated,
        runes_collected=engine.run_stats.runes_collected,
        depth=engine.floor_depth,
        save_store=save_store,
        past_runs_store=engine.past_runs_store,
        macguffin_score=macguffin_score,
        difficulty_id=profile.id,
        difficulty_display=profile.display_name,
        level_warped=engine.level_warped,
    )


def complete_macguffin_victory(engine: GameEngine) -> None:
    confirm = engine.macguffin_victory_confirm
    display_name = confirm.display_name
    score = confirm.score
    engine.macguffin_victory_confirm.reset()
    save_store = None
    if engine.save_coordinator is not None:
        engine.save_coordinator.prepare_for_game_over_wipe()
        save_store = engine.save_coordinator.store
    profile = engine.difficulty_profile()
    engine.game_over.open(
        player_name=engine.player_name,
        ending=GameOverEnding(kind="macguffin", detail=display_name),
        monsters_defeated=engine.run_stats.monsters_defeated,
        runes_collected=engine.run_stats.runes_collected,
        depth=engine.floor_depth,
        save_store=save_store,
        past_runs_store=engine.past_runs_store,
        macguffin_score=score,
        difficulty_id=profile.id,
        difficulty_display=profile.display_name,
        level_warped=engine.level_warped,
    )


def end_rest_session(engine: GameEngine) -> None:
    if engine._rest_attack_listener is not None:
        detach_rest_attack_listener(engine._rest_attack_listener)
        engine._rest_attack_listener = None
    engine.rest_session = None


def cancel_rest(engine: GameEngine) -> None:
    """Stop an in-progress rest without logging an automatic end reason."""
    engine._end_rest_session()


def rest_in_progress(engine: GameEngine) -> bool:
    return engine.rest_session is not None and engine.rest_session.active


def projectile_in_progress(engine: GameEngine) -> bool:
    return (
        engine.projectile_session is not None and engine.projectile_session.active
    )


def advance_projectile_animation(engine: GameEngine) -> ProjectileFrameResult:
    session = engine.projectile_session
    if session is None:
        return ProjectileFrameResult(screen_dirty=False, finished=True)
    result = advance_projectile_frame(session)
    if result.finished:
        engine.projectile_session = None
        if engine.pending_world_turn:
            engine.pending_world_turn = False
            run_world_turn(engine)
    return result


def end_autoexplore_session(engine: GameEngine) -> None:
    if engine._autoexplore_attack_listener is not None:
        detach_autoexplore_attack_listener(engine._autoexplore_attack_listener)
        engine._autoexplore_attack_listener = None
    engine.autoexplore_session = None


def cancel_autoexplore(engine: GameEngine) -> None:
    """Stop in-progress autoexplore without logging an automatic end reason."""
    engine._end_autoexplore_session()


def autoexplore_in_progress(engine: GameEngine) -> bool:
    return (
        engine.autoexplore_session is not None
        and engine.autoexplore_session.active
    )


def begin_autoexplore_session(engine: GameEngine) -> bool:
    """Start incremental autoexplore if pre-checks pass."""
    if engine.player is None or engine.autoexplore_in_progress():
        return False
    if engine.rest_in_progress():
        return False
    session = begin_autoexplore(
        player=engine.player,
        game_map=engine.game_map,
        world=engine.world,
        message_log=engine.message_log,
    )
    if session is None:
        return False
    engine.autoexplore_session = session
    engine._autoexplore_attack_listener = attach_autoexplore_attack_listener(session)
    return True


def advance_autoexplore_animation(engine: GameEngine) -> AutoexploreFrameResult:
    """Advance one autoexplore animation frame (batched steps allowed)."""
    if engine.player is None or engine.autoexplore_session is None:
        return AutoexploreFrameResult(screen_dirty=False, finished=True)
    result = advance_autoexplore_frame(
        engine=engine,
        session=engine.autoexplore_session,
        consume_turn=engine._consume_player_turn,
    )
    if result.finished:
        engine._end_autoexplore_session()
    return result


def begin_rest(engine: GameEngine) -> bool:
    """Start incremental rest if pre-checks pass."""
    if engine.player is None or engine.rest_in_progress():
        return False
    if engine.autoexplore_in_progress():
        return False
    session = begin_rest_until_healed_or_danger(
        player=engine.player,
        game_map=engine.game_map,
        world=engine.world,
        message_log=engine.message_log,
    )
    if session is None:
        return False
    engine.rest_session = session
    engine._rest_attack_listener = attach_rest_attack_listener(session)
    return True


def advance_rest_animation(engine: GameEngine) -> RestFrameResult:
    """Advance one rest animation frame (batched silent turns allowed)."""
    if engine.player is None or engine.rest_session is None:
        return RestFrameResult(screen_dirty=False, finished=True)
    result = advance_rest_frame(
        player=engine.player,
        game_map=engine.game_map,
        world=engine.world,
        message_log=engine.message_log,
        session=engine.rest_session,
        consume_turn=engine._consume_player_turn,
    )
    if result.finished:
        engine._end_rest_session()
    return result


def consume_player_turn(engine: GameEngine) -> None:
    """Advance player turn counter, apply natural regen, fire hook, run world phase."""
    if engine.player is None:
        return
    from src.systems.player_effects import haste_skips_world_phase, tick_player_effects

    engine.player_turn_count += 1
    skip_world = engine._maybe_apply_player_digestion()
    engine._apply_natural_regen()
    engine._update_fov()
    try_good_introductions(
        engine.world,
        engine.game_map,
        engine.player,
        engine.message_log,
        rng=engine.rng,
        entity_registry=get_entity_registry(),
        names_registry=get_names_registry(),
    )
    fire_player_turn_consumed(engine.player)
    tick_player_effects(
        engine.player,
        engine.message_log,
        world=engine.world,
        game_map=engine.game_map,
        rng=engine.rng,
    )
    # Teleport may have moved the player; refresh FOV before world phase.
    engine._update_fov()
    # Haste: 2 player actions per 1 monster phase while Fast remains.
    if haste_skips_world_phase(engine.player):
        skip_world = True
    begin_projectile_session_from_queue(engine)
    if not skip_world:
        if projectile_in_progress(engine):
            engine.pending_world_turn = True
        else:
            engine._run_world_turn()
    engine._notify_save_after_player_turn()
