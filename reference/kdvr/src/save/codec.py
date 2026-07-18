"""Component and metadata encode/decode helpers for run snapshots."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from typing import Any

from tcod.ecs import Entity, Registry

from src.components import (
    AI,
    AIState,
    Abilities,
    AbilityState,
    Alignment,
    BlocksMovement,
    DigestionStats,
    DigestionStrikes,
    DisplayName,
    Engulfed,
    EquipState,
    ExamineDescription,
    Fighter,
    FloorRune,
    Macguffin,
    Inventory,
    InventoryItemInstance,
    Item,
    ItemCategory,
    Mobility,
    MobilityType,
    NPCAlignment,
    NpcPrefix,
    Player,
    PlayerEffects,
    PlayerProgression,
    Position,
    Predator,
    ProperName,
    Renderable,
    SpeciesId,
    Stunned,
    VoreCapable,
    VoreMercy,
    VoreNarratives,
)
from src.constants import VoreContentPreferences
from src.data.ability_parser import (
    FixedAbility,
    ParsedAbility,
    RangeAbility,
    RangedVoreAbility,
    SmiteAbility,
    SummonAbility,
    parse_abilities,
)
from src.log_categories import MessageCategory
from src.log_markup import LogSegment
from src.message_log import LogEntry, MessageLog

PERSISTED_TAGS: frozenset[str] = frozenset(
    {
        Player,
        Stunned,
        BlocksMovement,
        VoreCapable,
        Engulfed,
        VoreMercy,
    }
)

EntityIdMap = dict[Entity, int]


def encode_vore_content_prefs(prefs: VoreContentPreferences) -> dict[str, list[str]]:
    return {"enabled": sorted(prefs.enabled)}


def decode_vore_content_prefs(data: dict[str, Any]) -> VoreContentPreferences:
    enabled = frozenset(data.get("enabled", ()))
    return VoreContentPreferences(enabled=enabled)


def encode_rng_state(state: tuple[Any, ...]) -> list[Any]:
    version, internal, gauss = state
    return [version, list(internal), gauss]


def decode_rng_state(data: list[Any]) -> tuple[Any, ...]:
    version, internal, gauss = data
    return (version, tuple(internal), gauss)


def _encode_position(pos: Position | None) -> dict[str, int] | None:
    if pos is None:
        return None
    return {"x": pos.x, "y": pos.y}


def _decode_position(data: dict[str, int] | None) -> Position | None:
    if data is None:
        return None
    return Position(x=int(data["x"]), y=int(data["y"]))


def _encode_item_category(category: ItemCategory) -> str:
    return category.name


def _decode_item_category(name: str) -> ItemCategory:
    return ItemCategory[name]


def _encode_inventory_item(instance: InventoryItemInstance) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "item_id": instance.item_id,
        "category": _encode_item_category(instance.category),
        "stack_count": instance.stack_count,
    }
    if instance.durability is not None:
        payload["durability"] = instance.durability
    if instance.charges is not None:
        payload["charges"] = instance.charges
    return payload


def _decode_inventory_item(data: dict[str, Any]) -> InventoryItemInstance:
    return InventoryItemInstance(
        item_id=str(data["item_id"]),
        category=_decode_item_category(str(data["category"])),
        durability=data.get("durability"),
        charges=data.get("charges"),
        stack_count=int(data.get("stack_count", 1)),
    )


def _ability_to_token(ability: ParsedAbility) -> str:
    if isinstance(ability, SmiteAbility):
        return f"Smite{ability.distance}"
    if isinstance(ability, RangeAbility):
        return f"Range{ability.distance}"
    if isinstance(ability, RangedVoreAbility):
        return f"RangedVore{ability.distance}"
    if isinstance(ability, SummonAbility):
        return f"Summon{ability.count} {ability.entity_id}"
    if isinstance(ability, FixedAbility):
        return ability.ability_id
    raise TypeError(f"unsupported ability type: {type(ability)!r}")


def _encode_components(entity: Entity, id_map: EntityIdMap) -> dict[str, Any]:
    components: dict[str, Any] = {}

    if Position in entity.components:
        pos = entity.components[Position]
        components["Position"] = {"x": pos.x, "y": pos.y}

    if Renderable in entity.components:
        renderable = entity.components[Renderable]
        components["Renderable"] = {
            "ch": renderable.ch,
            "fg": list(renderable.fg),
        }

    if Fighter in entity.components:
        fighter = entity.components[Fighter]
        payload: dict[str, Any] = {
            "hp": fighter.hp,
            "max_hp": fighter.max_hp,
            "accuracy": fighter.accuracy,
            "evade": fighter.evade,
            "ac": fighter.ac,
            "min_damage": fighter.min_damage,
            "max_damage": fighter.max_damage,
        }
        if fighter.ranged_accuracy is not None:
            payload["ranged_accuracy"] = fighter.ranged_accuracy
        if fighter.ranged_min_damage is not None:
            payload["ranged_min_damage"] = fighter.ranged_min_damage
        if fighter.ranged_max_damage is not None:
            payload["ranged_max_damage"] = fighter.ranged_max_damage
        components["Fighter"] = payload

    if AI in entity.components:
        components["AI"] = {}

    if AIState in entity.components:
        state = entity.components[AIState]
        components["AIState"] = {
            "last_known_primary": _encode_position(state.last_known_primary),
            "last_known_neutral": _encode_position(state.last_known_neutral),
            "last_known_evil": _encode_position(state.last_known_evil),
            "last_known_player": _encode_position(state.last_known_player),
            "explore_goal": _encode_position(state.explore_goal),
            "chase_momentum_direction": (
                list(state.chase_momentum_direction)
                if state.chase_momentum_direction is not None
                else None
            ),
            "chase_momentum_turns_left": state.chase_momentum_turns_left,
            "chase_frustration": state.chase_frustration,
            "chase_frustration_limit": state.chase_frustration_limit,
            "explore_frustration": state.explore_frustration,
            "explore_frustration_limit": state.explore_frustration_limit,
            "door_spite_turns_left": state.door_spite_turns_left,
            "memory_blind_turns": state.memory_blind_turns,
            "memory_blind_limit": state.memory_blind_limit,
            "explore_force_farthest_on_repick": state.explore_force_farthest_on_repick,
            "ai_turn_salt": int(state.ai_turn_salt) & 1,
            "spawn_freeze_remaining": int(state.spawn_freeze_remaining),
            "spawn_freeze_consumed": bool(state.spawn_freeze_consumed),
            "come_here": bool(state.come_here),
            "explore_recent_positions": [
                {"x": pos.x, "y": pos.y} for pos in state.explore_recent_positions
            ],
            "explore_recent_goal_distances": list(state.explore_recent_goal_distances),
        }

    if AbilityState in entity.components:
        ability_state = entity.components[AbilityState]
        components["AbilityState"] = {
            "summon_consumed": ability_state.summon_consumed,
            "erratic_index": ability_state.erratic_index,
            "plan_step_index": ability_state.plan_step_index,
        }

    if Abilities in entity.components:
        tokens = [_ability_to_token(ability) for ability in entity.components[Abilities].parsed]
        components["Abilities"] = {"tokens": tokens}

    if Item in entity.components:
        item = entity.components[Item]
        payload = {
            "item_id": item.item_id,
            "category": _encode_item_category(item.category),
        }
        if item.durability is not None:
            payload["durability"] = item.durability
        if item.charges is not None:
            payload["charges"] = item.charges
        if item.stack_count != 1:
            payload["stack_count"] = int(item.stack_count)
        components["Item"] = payload

    if Inventory in entity.components:
        inventory = entity.components[Inventory]
        components["Inventory"] = {
            slot: _encode_inventory_item(instance) if instance is not None else None
            for slot, instance in inventory.slots.items()
        }

    if EquipState in entity.components:
        equip = entity.components[EquipState]
        components["EquipState"] = {
            "wielded_slot": equip.wielded_slot,
            "worn_slot": equip.worn_slot,
        }

    if DisplayName in entity.components:
        components["DisplayName"] = {"name": entity.components[DisplayName].name}

    if SpeciesId in entity.components:
        components["SpeciesId"] = {"id": entity.components[SpeciesId].id}

    if NpcPrefix in entity.components:
        prefix = entity.components[NpcPrefix]
        components["NpcPrefix"] = {
            "prefix_id": prefix.prefix_id,
            "display_prefix": prefix.display_prefix,
        }

    if Mobility in entity.components:
        kind = entity.components[Mobility].kind
        components["Mobility"] = {"kind": kind.name}

    if NPCAlignment in entity.components:
        alignment = entity.components[NPCAlignment].alignment
        components["NPCAlignment"] = {"alignment": alignment.name}

    if ProperName in entity.components:
        components["ProperName"] = {"name": entity.components[ProperName].name}

    if ExamineDescription in entity.components:
        components["ExamineDescription"] = {
            "text": entity.components[ExamineDescription].text
        }

    if FloorRune in entity.components:
        components["FloorRune"] = {"rune_id": entity.components[FloorRune].rune_id}

    if Macguffin in entity.components:
        components["Macguffin"] = {
            "macguffin_id": entity.components[Macguffin].macguffin_id,
        }

    if PlayerProgression in entity.components:
        progression = entity.components[PlayerProgression]
        components["PlayerProgression"] = {
            "bonus_max_hp": progression.bonus_max_hp,
            "bonus_accuracy": progression.bonus_accuracy,
            "bonus_min_damage": progression.bonus_min_damage,
            "bonus_max_damage": progression.bonus_max_damage,
            "bonus_ac": progression.bonus_ac,
            "bonus_evade": progression.bonus_evade,
            "pieces_max_hp": progression.pieces_max_hp,
            "pieces_need_max_hp": progression.pieces_need_max_hp,
            "pieces_max_hp_need_frozen": progression.pieces_max_hp_need_frozen,
            "pieces_accuracy": progression.pieces_accuracy,
            "pieces_need_accuracy": progression.pieces_need_accuracy,
            "pieces_accuracy_need_frozen": progression.pieces_accuracy_need_frozen,
            "pieces_ac": progression.pieces_ac,
            "pieces_need_ac": progression.pieces_need_ac,
            "pieces_ac_need_frozen": progression.pieces_ac_need_frozen,
            "pieces_evade": progression.pieces_evade,
            "pieces_need_evade": progression.pieces_need_evade,
            "pieces_evade_need_frozen": progression.pieces_evade_need_frozen,
            "pieces_min_damage": progression.pieces_min_damage,
            "pieces_need_min_damage": progression.pieces_need_min_damage,
            "pieces_min_damage_need_frozen": progression.pieces_min_damage_need_frozen,
            "pieces_max_damage": progression.pieces_max_damage,
            "pieces_need_max_damage": progression.pieces_need_max_damage,
            "pieces_max_damage_need_frozen": progression.pieces_max_damage_need_frozen,
        }

    if PlayerEffects in entity.components:
        pe = entity.components[PlayerEffects]
        components["PlayerEffects"] = {
            "haste_turns": pe.haste_turns,
            "might_turns": pe.might_turns,
            "might_accuracy_bonus": pe.might_accuracy_bonus,
            "might_min_damage_bonus": pe.might_min_damage_bonus,
            "might_max_damage_bonus": pe.might_max_damage_bonus,
            "digestion_ward_turns": pe.digestion_ward_turns,
            "teleport_pending_turns": pe.teleport_pending_turns,
        }

    if VoreNarratives in entity.components:
        components["VoreNarratives"] = {
            "types": list(entity.components[VoreNarratives].types)
        }

    if DigestionStats in entity.components:
        stats = entity.components[DigestionStats]
        components["DigestionStats"] = {
            "damage_per_tick": stats.damage_per_tick,
            "digest_time": stats.digest_time,
        }

    if DigestionStrikes in entity.components:
        components["DigestionStrikes"] = {
            "count": entity.components[DigestionStrikes].count
        }

    if Predator in entity.components:
        predator = entity.components[Predator]
        prey = predator.prey
        if prey not in id_map:
            raise ValueError("Predator.prey is missing from entity id map")
        components["Predator"] = {
            "prey_id": id_map[prey],
            "narrative_type": predator.narrative_type,
            "failed_struggles": predator.failed_struggles,
        }

    return components


def _decode_components(
    entity: Entity,
    components: dict[str, Any],
    id_to_entity: dict[int, Entity],
) -> None:
    if "Position" in components:
        pos = components["Position"]
        entity.components[Position] = Position(x=int(pos["x"]), y=int(pos["y"]))

    if "Renderable" in components:
        renderable = components["Renderable"]
        entity.components[Renderable] = Renderable(
            ch=int(renderable["ch"]),
            fg=tuple(renderable["fg"]),
        )

    if "Fighter" in components:
        fighter = components["Fighter"]
        entity.components[Fighter] = Fighter(
            hp=int(fighter["hp"]),
            max_hp=int(fighter["max_hp"]),
            accuracy=float(fighter["accuracy"]),
            evade=float(fighter["evade"]),
            ac=int(fighter["ac"]),
            min_damage=int(fighter["min_damage"]),
            max_damage=int(fighter["max_damage"]),
            ranged_accuracy=fighter.get("ranged_accuracy"),
            ranged_min_damage=fighter.get("ranged_min_damage"),
            ranged_max_damage=fighter.get("ranged_max_damage"),
        )

    if "AI" in components:
        entity.components[AI] = AI()

    if "AIState" in components:
        state = components["AIState"]
        entity.components[AIState] = AIState(
            last_known_primary=_decode_position(state.get("last_known_primary")),
            last_known_neutral=_decode_position(state.get("last_known_neutral")),
            last_known_evil=_decode_position(state.get("last_known_evil")),
            last_known_player=_decode_position(state.get("last_known_player")),
            explore_goal=_decode_position(state.get("explore_goal")),
            chase_momentum_direction=(
                tuple(state["chase_momentum_direction"])
                if state.get("chase_momentum_direction") is not None
                else None
            ),
            chase_momentum_turns_left=int(state.get("chase_momentum_turns_left", 0)),
            chase_frustration=int(state.get("chase_frustration", 0)),
            chase_frustration_limit=int(state.get("chase_frustration_limit", 0)),
            explore_frustration=int(state.get("explore_frustration", 0)),
            explore_frustration_limit=int(state.get("explore_frustration_limit", 0)),
            door_spite_turns_left=int(state.get("door_spite_turns_left", 0)),
            memory_blind_turns=int(state.get("memory_blind_turns", 0)),
            memory_blind_limit=int(state.get("memory_blind_limit", 0)),
            explore_force_farthest_on_repick=bool(
                state.get("explore_force_farthest_on_repick", False)
            ),
            ai_turn_salt=int(state.get("ai_turn_salt", 0)) & 1,
            spawn_freeze_remaining=max(0, int(state.get("spawn_freeze_remaining", 0))),
            spawn_freeze_consumed=bool(state.get("spawn_freeze_consumed", False)),
            come_here=bool(state.get("come_here", False)),
            explore_recent_positions=deque(
                (
                    Position(x=int(pos["x"]), y=int(pos["y"]))
                    for pos in state.get("explore_recent_positions", ())
                ),
                maxlen=4,
            ),
            explore_recent_goal_distances=deque(
                (int(value) for value in state.get("explore_recent_goal_distances", ())),
                maxlen=4,
            ),
        )

    if "AbilityState" in components:
        ability_state = components["AbilityState"]
        entity.components[AbilityState] = AbilityState(
            summon_consumed=bool(ability_state.get("summon_consumed", False)),
            erratic_index=int(ability_state.get("erratic_index", 0)),
            plan_step_index=int(ability_state.get("plan_step_index", 0)),
        )

    if "Abilities" in components:
        tokens = tuple(components["Abilities"].get("tokens", ()))
        parsed = parse_abilities(tokens)
        if parsed:
            entity.components[Abilities] = Abilities(parsed=parsed)

    if "Item" in components:
        item = components["Item"]
        entity.components[Item] = Item(
            item_id=str(item["item_id"]),
            category=_decode_item_category(str(item["category"])),
            durability=item.get("durability"),
            charges=item.get("charges"),
            stack_count=max(1, int(item.get("stack_count", 1))),
        )

    if "Inventory" in components:
        slots = {
            slot: (
                _decode_inventory_item(instance) if instance is not None else None
            )
            for slot, instance in components["Inventory"].items()
        }
        entity.components[Inventory] = Inventory(slots=slots)

    if "EquipState" in components:
        equip = components["EquipState"]
        entity.components[EquipState] = EquipState(
            wielded_slot=equip.get("wielded_slot"),
            worn_slot=equip.get("worn_slot"),
        )

    if "DisplayName" in components:
        entity.components[DisplayName] = DisplayName(name=str(components["DisplayName"]["name"]))

    if "SpeciesId" in components:
        entity.components[SpeciesId] = SpeciesId(id=str(components["SpeciesId"]["id"]))

    if "NpcPrefix" in components:
        prefix = components["NpcPrefix"]
        entity.components[NpcPrefix] = NpcPrefix(
            prefix_id=str(prefix.get("prefix_id", "")),
            display_prefix=str(prefix.get("display_prefix", "")),
        )

    if "Mobility" in components:
        entity.components[Mobility] = Mobility(kind=MobilityType[components["Mobility"]["kind"]])

    if "NPCAlignment" in components:
        entity.components[NPCAlignment] = NPCAlignment(
            alignment=Alignment[components["NPCAlignment"]["alignment"]]
        )

    if "ProperName" in components:
        entity.components[ProperName] = ProperName(name=str(components["ProperName"]["name"]))

    if "ExamineDescription" in components:
        entity.components[ExamineDescription] = ExamineDescription(
            text=str(components["ExamineDescription"]["text"])
        )

    if "FloorRune" in components:
        entity.components[FloorRune] = FloorRune(
            rune_id=str(components["FloorRune"]["rune_id"])
        )

    if "Macguffin" in components:
        entity.components[Macguffin] = Macguffin(
            macguffin_id=str(components["Macguffin"]["macguffin_id"]),
        )

    if "PlayerProgression" in components:
        progression = components["PlayerProgression"]

        def _pi(key: str, default: int = 0) -> int:
            try:
                return max(0, int(progression.get(key, default)))
            except (TypeError, ValueError):
                return default

        def _pb(key: str) -> bool:
            return bool(progression.get(key, False))

        entity.components[PlayerProgression] = PlayerProgression(
            bonus_max_hp=_pi("bonus_max_hp"),
            bonus_accuracy=float(progression.get("bonus_accuracy", 0.0)),
            bonus_min_damage=_pi("bonus_min_damage"),
            bonus_max_damage=_pi("bonus_max_damage"),
            bonus_ac=_pi("bonus_ac"),
            bonus_evade=max(0.0, float(progression.get("bonus_evade", 0.0) or 0.0)),
            pieces_max_hp=_pi("pieces_max_hp"),
            pieces_need_max_hp=max(1, _pi("pieces_need_max_hp", 1)),
            pieces_max_hp_need_frozen=_pb("pieces_max_hp_need_frozen"),
            pieces_accuracy=_pi("pieces_accuracy"),
            pieces_need_accuracy=max(1, _pi("pieces_need_accuracy", 1)),
            pieces_accuracy_need_frozen=_pb("pieces_accuracy_need_frozen"),
            pieces_ac=_pi("pieces_ac"),
            pieces_need_ac=max(1, _pi("pieces_need_ac", 1)),
            pieces_ac_need_frozen=_pb("pieces_ac_need_frozen"),
            pieces_evade=_pi("pieces_evade"),
            pieces_need_evade=max(1, _pi("pieces_need_evade", 1)),
            pieces_evade_need_frozen=_pb("pieces_evade_need_frozen"),
            pieces_min_damage=_pi("pieces_min_damage"),
            pieces_need_min_damage=max(1, _pi("pieces_need_min_damage", 1)),
            pieces_min_damage_need_frozen=_pb("pieces_min_damage_need_frozen"),
            pieces_max_damage=_pi("pieces_max_damage"),
            pieces_need_max_damage=max(1, _pi("pieces_need_max_damage", 1)),
            pieces_max_damage_need_frozen=_pb("pieces_max_damage_need_frozen"),
        )

    if "PlayerEffects" in components:
        raw_pe = components["PlayerEffects"]
        if not isinstance(raw_pe, dict):
            raw_pe = {}

        def _pe_i(key: str, default: int = 0) -> int:
            try:
                return max(0, int(raw_pe.get(key, default)))
            except (TypeError, ValueError):
                return default

        tele_raw = raw_pe.get("teleport_pending_turns", None)
        tele: int | None
        if tele_raw is None:
            tele = None
        else:
            try:
                tele = max(1, int(tele_raw))
            except (TypeError, ValueError):
                tele = None
        try:
            might_acc = float(raw_pe.get("might_accuracy_bonus", 0.0))
        except (TypeError, ValueError):
            might_acc = 0.0
        entity.components[PlayerEffects] = PlayerEffects(
            haste_turns=_pe_i("haste_turns"),
            might_turns=_pe_i("might_turns"),
            might_accuracy_bonus=might_acc,
            might_min_damage_bonus=_pe_i("might_min_damage_bonus"),
            might_max_damage_bonus=_pe_i("might_max_damage_bonus"),
            digestion_ward_turns=_pe_i("digestion_ward_turns"),
            teleport_pending_turns=tele,
        )

    if "VoreNarratives" in components:
        entity.components[VoreNarratives] = VoreNarratives(
            types=tuple(components["VoreNarratives"].get("types", ()))
        )

    if "DigestionStats" in components:
        stats = components["DigestionStats"]
        entity.components[DigestionStats] = DigestionStats(
            damage_per_tick=int(stats["damage_per_tick"]),
            digest_time=int(stats["digest_time"]),
        )

    if "DigestionStrikes" in components:
        entity.components[DigestionStrikes] = DigestionStrikes(
            count=int(components["DigestionStrikes"]["count"])
        )

    if "Predator" in components:
        predator = components["Predator"]
        prey_id = int(predator["prey_id"])
        prey = id_to_entity[prey_id]
        entity.components[Predator] = Predator(
            prey=prey,
            narrative_type=str(predator["narrative_type"]),
            failed_struggles=int(predator.get("failed_struggles", 0)),
        )


def encode_entity_tags(entity: Entity) -> list[str]:
    return sorted(tag for tag in entity.tags if tag in PERSISTED_TAGS)


def decode_entity_tags(entity: Entity, tags: list[str]) -> None:
    for tag in tags:
        if tag in PERSISTED_TAGS:
            entity.tags.add(tag)


def encode_message_log(message_log: MessageLog) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for entry in message_log.entries():
        payload: dict[str, Any] = {
            "text": entry.text,
            "category": entry.category.name,
        }
        if entry.segments:
            payload["segments"] = [
                {"text": segment.text, "fg": list(segment.fg)} for segment in entry.segments
            ]
        entries.append(payload)
    return entries


def decode_message_log(message_log: MessageLog, entries: list[dict[str, Any]]) -> None:
    message_log.clear()
    for entry in entries:
        category = MessageCategory[entry["category"]]
        segments_data = entry.get("segments")
        if segments_data:
            segments = tuple(
                LogSegment(text=str(segment["text"]), fg=tuple(segment["fg"]))
                for segment in segments_data
            )
            message_log._messages.append(
                LogEntry(
                    text=str(entry["text"]),
                    category=category,
                    segments=segments,
                )
            )
        else:
            message_log.add(str(entry["text"]), category=category)


def assign_entity_ids(entities: list[Entity]) -> EntityIdMap:
    """Assign stable 1-based ids sorted by map position."""
    ordered = sorted(
        entities,
        key=lambda entity: (
            entity.components[Position].y,
            entity.components[Position].x,
            id(entity),
        ),
    )
    return {entity: index + 1 for index, entity in enumerate(ordered)}


def encode_entity_record(entity: Entity, entity_id: int, id_map: EntityIdMap) -> dict[str, Any]:
    return {
        "id": entity_id,
        "tags": encode_entity_tags(entity),
        "components": _encode_components(entity, id_map),
    }


def restore_entities(world: Registry, entity_records: list[dict[str, Any]]) -> dict[int, Entity]:
    id_to_entity: dict[int, Entity] = {}
    deferred_predators: list[tuple[Entity, dict[str, Any]]] = []

    for record in entity_records:
        entity_id = int(record["id"])
        entity = world[entity_id]
        id_to_entity[entity_id] = entity
        components = record.get("components", {})
        if "Predator" in components:
            deferred_predators.append((entity, record))
            components = {key: value for key, value in components.items() if key != "Predator"}
        _decode_components(entity, components, id_to_entity)
        decode_entity_tags(entity, record.get("tags", []))

    for entity, record in deferred_predators:
        _decode_components(entity, record["components"], id_to_entity)

    return id_to_entity