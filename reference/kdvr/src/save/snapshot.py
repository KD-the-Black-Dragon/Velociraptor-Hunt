"""Build and apply in-memory run snapshots for save/load."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from tcod.ecs import Registry

from src.components import Player, Position
from src.map_gen import GameMap
from src.message_log import MessageLog
from src.save.codec import (
    assign_entity_ids,
    decode_message_log,
    decode_rng_state,
    decode_vore_content_prefs,
    encode_entity_record,
    encode_message_log,
    encode_rng_state,
    encode_vore_content_prefs,
    restore_entities,
)
from src.macguffin_discovery import (
    decode_macguffin_discovery,
    encode_macguffin_discovery,
)
from src.run_stats import decode_run_stats, encode_run_stats
from src.save.schema import SAVE_FORMAT_VERSION

if TYPE_CHECKING:
    from src.engine import GameEngine


def build_run_snapshot(engine: GameEngine) -> dict[str, Any]:
    """Capture full run state from a live engine."""
    from src.mods.fingerprint import encode_mods_fingerprint

    entities = list(engine.world.Q.all_of(components=[Position]))
    id_map = assign_entity_ids(entities)

    player_entity_id: int | None = None
    entity_records: list[dict[str, Any]] = []
    for entity in sorted(id_map, key=lambda item: id_map[item]):
        entity_id = id_map[entity]
        if Player in entity.tags:
            player_entity_id = entity_id
        entity_records.append(encode_entity_record(entity, entity_id, id_map))

    if player_entity_id is None:
        raise ValueError("snapshot requires a player entity")

    game_map = engine.game_map
    return {
        "save_format_version": SAVE_FORMAT_VERSION,
        "player_name": engine.player_name,
        "player_turn_count": engine.player_turn_count,
        "last_come_here_turn": engine.last_come_here_turn,
        "floor_depth": engine.floor_depth,
        "level_warped": bool(engine.level_warped),
        "difficulty_id": engine.difficulty_id,
        "vore_content_prefs": encode_vore_content_prefs(engine.vore_content_prefs),
        "ui_preset": engine.ui_layout.preset_id,
        "rng_state": encode_rng_state(engine.rng.getstate()),
        "close_door_pending": engine.close_door_pending,
        "player_entity_id": player_entity_id,
        "game_map": {
            "width": game_map.width,
            "height": game_map.height,
            "tiles": game_map.tiles.tolist(),
            "explored": game_map.explored.tolist(),
            "enter_xy": list(game_map.enter_xy),
            "layout_archetype": game_map.layout_archetype,
        },
        "message_log": encode_message_log(engine.message_log),
        "entities": entity_records,
        "run_stats": encode_run_stats(engine.run_stats),
        "macguffin_discovery": encode_macguffin_discovery(
            engine.macguffin_discovery,
        ),
        "mods": encode_mods_fingerprint(),
    }


def apply_run_snapshot(engine: GameEngine, run: dict[str, Any]) -> None:
    """Restore run state onto an engine created with ``skip_new_game=True``."""
    from src.data.depth_scaling_config import validate_difficulty_id
    from src.data.depth_scaling_loader import default_depth_scaling_config
    from src.save.migrate import migrate_run

    run = migrate_run(run)

    engine.player_name = str(run["player_name"])
    engine.player_turn_count = int(run["player_turn_count"])
    engine.last_come_here_turn = int(run.get("last_come_here_turn", -1))
    engine.floor_depth = int(run["floor_depth"])
    engine.level_warped = bool(run.get("level_warped", False))
    engine.depth_jump_start_depth = None
    raw_difficulty = run.get("difficulty_id")
    validated = validate_difficulty_id(
        str(raw_difficulty) if raw_difficulty is not None else None
    )
    engine.difficulty_id = validated
    engine.vore_content_prefs = decode_vore_content_prefs(run["vore_content_prefs"])
    engine.close_door_pending = bool(run.get("close_door_pending", False))
    engine.run_stats = decode_run_stats(run.get("run_stats"))

    rng_state = run.get("rng_state")
    if rng_state is not None:
        engine.rng.setstate(decode_rng_state(rng_state))

    map_data = run["game_map"]
    game_map = GameMap(int(map_data["width"]), int(map_data["height"]))
    game_map.tiles = np.array(map_data["tiles"], dtype=np.int8)
    game_map.explored = np.array(map_data["explored"], dtype=bool)
    game_map.enter_xy = tuple(map_data["enter_xy"])
    game_map.layout_archetype = str(map_data.get("layout_archetype", ""))
    engine.game_map = game_map

    engine.world = Registry()
    id_to_entity = restore_entities(engine.world, run["entities"])

    player_entity_id = int(run["player_entity_id"])
    player = id_to_entity.get(player_entity_id)
    if player is None or Player not in player.tags:
        raise ValueError("snapshot player_entity_id is invalid")
    engine.player = player
    # Old saves lack PlayerEffects; additive default.
    from src.components import PlayerEffects
    from src.systems.player_effects import ensure_player_effects

    if PlayerEffects not in player.components:
        ensure_player_effects(player)

    message_log = MessageLog()
    decode_message_log(message_log, run.get("message_log", []))
    engine.message_log = message_log

    if raw_difficulty is not None and str(raw_difficulty) != validated:
        from src import messages

        fallback_name = default_depth_scaling_config().profile_for(
            validated
        ).display_name
        engine.message_log.add(
            messages.unknown_difficulty_using_fallback(
                str(raw_difficulty),
                fallback_name,
            )
        )

    from src.save.sanitize import apply_sanitize_notice, sanitize_loaded_world

    report = sanitize_loaded_world(engine.world)
    apply_sanitize_notice(engine.message_log, report)

    engine.vore_modal.reset()
    engine.digestion_modal.reset()
    engine.game_over.reset()
    engine.skipped_this_phase.clear()
    engine.examine_state.reset()
    engine.ground_pickup_modal.reset()
    engine.inventory_modal.reset()
    engine.macguffin_discovery = decode_macguffin_discovery(
        run.get("macguffin_discovery"),
    )
    engine.macguffin_victory_confirm.reset()
    engine.screen_flash.pending = False
    engine.log_overlay.close()
    engine.help_overlay.close()
    engine._end_rest_session()
    engine._end_autoexplore_session()
    engine.projectile_session = None
    engine.pending_world_turn = False