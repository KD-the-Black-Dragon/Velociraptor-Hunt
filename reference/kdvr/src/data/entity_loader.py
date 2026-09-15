from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.components import Alignment, MobilityType
from src.constants import DATA_DIR, VORE_NARRATIVE_TYPES_V1
from src.data.abilities import filter_known_abilities
from src.data.ability_parser import SummonAbility, parse_ability_token
from src.data.entity_registry import (
    EntityDefinition,
    EntityRegistry,
    SpawnConfig,
    VoreNarrativeVariant,
)
from src.data.warnings import LoadWarnings
from src.log_categories import MessageCategory
from src.log_markup import parse_log_category_field

ENTITIES_PATH = DATA_DIR / "entities.json"

_default_registry: EntityRegistry | None = None
_path_registry_cache: dict[Path, EntityRegistry] = {}

_ENTITY_TRAITS: frozenset[str] = frozenset(
    {
        "id",
        "display_name",
        "glyph",
        "fg",
        "alignment",
        "mobility",
        "examine",
        "proper_name",
        "max_hp",
        "evade",
        "ac",
        "accuracy",
        "min_damage",
        "max_damage",
        "ranged_accuracy",
        "ranged_min_damage",
        "ranged_max_damage",
        "digestion_damage_per_tick",
        "digest_time",
        "experience_points",
        "abilities",
        "spawn",
        "spawn_requires_water",
        "vore_narratives",
        "digestion_complete",
        "digestion_player_modal",
        "npc_vore_hit",
        "npc_vore_miss",
        "offscreen_vore",
        "offscreen_digest",
        "engulfed_flavor",
        "introduction",
        "introduction_log_category",
        "placeholder",
    }
)

_DEPRECATED_OFFSCREEN_KEYS: dict[str, str] = {
    "offscreen_ov": "offscreen_vore",
    "offscreen_cv": "offscreen_vore",
    "offscreen_av": "offscreen_vore",
    "offscreen_ov_digest": "offscreen_digest",
    "offscreen_cv_digest": "offscreen_digest",
    "offscreen_av_digest": "offscreen_digest",
}

_RESERVED_ENTITY_TRAITS: frozenset[str] = frozenset(
    {
        "experience_value",
        "hd",
        "scale_with_depth",
        "loot_table",
        "drop_chance",
        "gold_min",
        "gold_max",
        "guaranteed_drops",
        "spawn_chance",
        "speed",
        "attacks_per_turn",
        "ai_profile",
        "vore_narrative_types",
    }
)

_SPAWN_TRAITS: frozenset[str] = frozenset(
    {"weight", "min_depth", "max_depth", "terrain", "requires_vore_types"}
)
_RECOGNIZED_VORE_TYPES: frozenset[str] = frozenset(VORE_NARRATIVE_TYPES_V1)

_RESERVED_SPAWN_TRAITS: frozenset[str] = frozenset({"min_distance", "group_size"})

_ALIGNMENT_MAP = {
    "good": Alignment.GOOD,
    "evil": Alignment.EVIL,
    "neutral": Alignment.NEUTRAL,
}

_MOBILITY_MAP = {
    "ground": MobilityType.GROUND,
    "walker": MobilityType.GROUND,
    "fly": MobilityType.FLY,
    "flyer": MobilityType.FLY,
    "aquatic": MobilityType.AQUATIC,
    "stationary": MobilityType.STATIONARY,
}


class EntityLoadError(ValueError):
    pass


def _read_entity_registry(path: Path) -> EntityRegistry:
    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)
    return parse_entity_registry(raw)


def load_entity_registry(
    path: Path | None = None,
    *,
    mods_root: Path | None = None,
    report_mod_errors: bool = True,
) -> EntityRegistry:
    """Load entities from one file, or core + enabled mods when *path* is None.

    Default load (``path is None``) applies the mod pipeline: install
    ``data/entities.json`` first, then each enabled mod's ``entities.json``
    (later id wins). Explicit *path* is single-file only (tests / tools).

    *mods_root* overrides ``{user_data}/mods`` for the layered path (tests).
    """
    if path is not None:
        data_path = path
        # Explicit path: never layer mods (deterministic single-file load).
        if mods_root is not None:
            raise TypeError("mods_root is only valid when path is None (layered load)")
        cached = _path_registry_cache.get(data_path)
        if cached is not None:
            return cached
        registry = _read_entity_registry(data_path)
        _path_registry_cache[data_path] = registry
        return registry

    # Layered default registry (core + mods).
    if mods_root is not None:
        from src.mods.pipeline import load_entities_layered

        registry, _issues = load_entities_layered(
            mods_root=mods_root,
            report=report_mod_errors,
        )
        return registry

    global _default_registry
    if _default_registry is None:
        from src.mods.pipeline import load_entities_layered

        _default_registry, _issues = load_entities_layered(report=report_mod_errors)
    return _default_registry


def get_entity_registry() -> EntityRegistry:
    """Return the cached default entity registry (core + enabled mods)."""
    return load_entity_registry()


def reset_entity_registry_cache() -> None:
    """Clear cached registries (tests or mod reload)."""
    global _default_registry
    _default_registry = None
    _path_registry_cache.clear()
    from src.data.narrative_index import reset_narrative_index

    reset_narrative_index()


def parse_entity_registry(raw: dict[str, Any]) -> EntityRegistry:
    warnings = LoadWarnings()
    schema_version = _require_int(raw, "schema_version", context="entities file")
    entities_raw = raw.get("entities")
    if not isinstance(entities_raw, list):
        raise EntityLoadError("entities file must contain an 'entities' array")

    for key in raw:
        if key in {"schema_version", "entities"}:
            continue
        warnings.warn_unknown_trait(key, "entities file")

    known_ids: set[str] = set()
    for index, entry in enumerate(entities_raw):
        if not isinstance(entry, dict):
            raise EntityLoadError(f"entities[{index}] must be an object")
        entity_id = entry.get("id")
        if isinstance(entity_id, str) and entity_id:
            known_ids.add(entity_id)

    entities: list[EntityDefinition] = []
    seen_ids: set[str] = set()
    for index, entry in enumerate(entities_raw):
        if not isinstance(entry, dict):
            raise EntityLoadError(f"entities[{index}] must be an object")
        entity = _parse_entity(entry, warnings, known_ids=known_ids)
        if entity.id in seen_ids:
            raise EntityLoadError(f"duplicate entity id '{entity.id}'")
        seen_ids.add(entity.id)
        entities.append(entity)

    registry = EntityRegistry(
        schema_version=schema_version,
        entities=tuple(entities),
        warnings=warnings.messages,
    )
    from src.data.narrative_index import reset_narrative_index

    reset_narrative_index()
    return registry


def _parse_entity(
    raw: dict[str, Any],
    warnings: LoadWarnings,
    *,
    known_ids: frozenset[str] | set[str],
) -> EntityDefinition:
    entity_id = _require_str(raw, "id")
    _reject_deprecated_offscreen_keys(raw, entity_id)
    _scan_unknown_traits(raw, entity_id, warnings)

    alignment = _parse_alignment(_require_str(raw, "alignment"), entity_id)
    mobility = _parse_mobility(_require_str(raw, "mobility"), entity_id)
    glyph = _require_str(raw, "glyph")
    if len(glyph) != 1:
        raise EntityLoadError(f"entity '{entity_id}': glyph must be exactly one character")

    min_damage = _require_int(raw, "min_damage", entity_id=entity_id)
    max_damage = _require_int(raw, "max_damage", entity_id=entity_id)
    if min_damage > max_damage:
        raise EntityLoadError(
            f"entity '{entity_id}': min_damage ({min_damage}) cannot exceed max_damage ({max_damage})"
        )

    spawn_raw = raw.get("spawn")
    if not isinstance(spawn_raw, dict):
        raise EntityLoadError(f"entity '{entity_id}': missing required object 'spawn'")

    abilities_raw = raw.get("abilities", [])
    if not isinstance(abilities_raw, list) or not all(
        isinstance(item, str) for item in abilities_raw
    ):
        raise EntityLoadError(f"entity '{entity_id}': abilities must be a string array")
    abilities = filter_known_abilities(entity_id, abilities_raw, warnings)
    for ability in abilities:
        parsed = parse_ability_token(ability)
        if isinstance(parsed, SummonAbility) and parsed.entity_id not in known_ids:
            raise EntityLoadError(
                f"entity '{entity_id}': summon target '{parsed.entity_id}' "
                "is not a known entity id"
            )
    if any(
        ability.startswith("Smite") or ability.startswith("Range") for ability in abilities
    ):
        if (
            raw.get("ranged_accuracy") is None
            or raw.get("ranged_min_damage") is None
            or raw.get("ranged_max_damage") is None
        ):
            warnings.warn_ranged_stats_defaulted(entity_id)

    accuracy = _require_number(raw, "accuracy", entity_id=entity_id)
    ranged_accuracy = (
        accuracy
        if raw.get("ranged_accuracy") is None
        else _require_number(raw, "ranged_accuracy", entity_id=entity_id)
    )
    ranged_min_damage = (
        min_damage
        if raw.get("ranged_min_damage") is None
        else _require_int(raw, "ranged_min_damage", entity_id=entity_id)
    )
    ranged_max_damage = (
        max_damage
        if raw.get("ranged_max_damage") is None
        else _require_int(raw, "ranged_max_damage", entity_id=entity_id)
    )
    if ranged_min_damage > ranged_max_damage:
        raise EntityLoadError(
            f"entity '{entity_id}': ranged_min_damage ({ranged_min_damage}) "
            f"cannot exceed ranged_max_damage ({ranged_max_damage})"
        )

    digestion = raw.get("digestion_damage_per_tick")
    if digestion is not None and not isinstance(digestion, int):
        raise EntityLoadError(
            f"entity '{entity_id}': digestion_damage_per_tick must be an integer"
        )

    digest_time = raw.get("digest_time")
    if digest_time is not None:
        if not isinstance(digest_time, int):
            raise EntityLoadError(f"entity '{entity_id}': digest_time must be an integer")
        if digest_time < 1:
            raise EntityLoadError(
                f"entity '{entity_id}': digest_time must be an integer >= 1"
            )
        if alignment != Alignment.EVIL:
            raise EntityLoadError(
                f"entity '{entity_id}': digest_time is only valid for evil entities"
            )

    experience_points = raw.get("experience_points")
    if experience_points is not None and not isinstance(experience_points, int):
        raise EntityLoadError(f"entity '{entity_id}': experience_points must be an integer")

    proper_name = raw.get("proper_name")
    if proper_name is not None and not isinstance(proper_name, str):
        raise EntityLoadError(f"entity '{entity_id}': proper_name must be a string or null")

    examine = raw.get("examine")
    if examine is not None and not isinstance(examine, str):
        raise EntityLoadError(f"entity '{entity_id}': examine must be a string")

    spawn_requires_water = raw.get("spawn_requires_water", False)
    if not isinstance(spawn_requires_water, bool):
        raise EntityLoadError(f"entity '{entity_id}': spawn_requires_water must be a boolean")

    placeholder = raw.get("placeholder", False)
    if not isinstance(placeholder, bool):
        raise EntityLoadError(f"entity '{entity_id}': placeholder must be a boolean")

    return EntityDefinition(
        id=entity_id,
        display_name=_require_str(raw, "display_name"),
        glyph=glyph,
        fg=_parse_rgb(raw.get("fg"), entity_id),
        alignment=alignment,
        mobility=mobility,
        max_hp=_require_int(raw, "max_hp", entity_id=entity_id),
        evade=_require_number(raw, "evade", entity_id=entity_id),
        ac=_require_int(raw, "ac", entity_id=entity_id),
        accuracy=accuracy,
        min_damage=min_damage,
        max_damage=max_damage,
        ranged_accuracy=ranged_accuracy,
        ranged_min_damage=ranged_min_damage,
        ranged_max_damage=ranged_max_damage,
        spawn=_parse_spawn(spawn_raw, entity_id, warnings),
        examine=examine,
        proper_name=proper_name,
        spawn_requires_water=spawn_requires_water,
        digestion_damage_per_tick=digestion,
        digest_time=digest_time,
        experience_points=experience_points,
        vore_narratives=_parse_vore_narratives(raw.get("vore_narratives"), entity_id),
        digestion_complete=_parse_narrative_type_lines(
            raw.get("digestion_complete"), entity_id, "digestion_complete"
        ),
        digestion_player_modal=_parse_digestion_player_modal(
            raw.get("digestion_player_modal"), entity_id
        ),
        npc_vore_hit=_parse_narrative_type_lines(
            raw.get("npc_vore_hit"), entity_id, "npc_vore_hit"
        ),
        npc_vore_miss=_parse_narrative_type_lines(
            raw.get("npc_vore_miss"), entity_id, "npc_vore_miss"
        ),
        offscreen_vore=_parse_narrative_type_lines(
            raw.get("offscreen_vore"), entity_id, "offscreen_vore"
        ),
        offscreen_digest=_parse_narrative_type_lines(
            raw.get("offscreen_digest"), entity_id, "offscreen_digest"
        ),
        engulfed_flavor=_parse_engulfed_flavor(
            raw.get("engulfed_flavor"), entity_id
        ),
        introduction=_parse_introduction(raw.get("introduction"), entity_id),
        introduction_log_category=_parse_introduction_log_category(
            raw.get("introduction_log_category"),
            entity_id,
        ),
        abilities=abilities,
        placeholder=placeholder,
    )


def _reject_deprecated_offscreen_keys(raw: dict[str, Any], entity_id: str) -> None:
    for key, replacement in _DEPRECATED_OFFSCREEN_KEYS.items():
        if key in raw:
            raise EntityLoadError(
                f"entity '{entity_id}': '{key}' is deprecated; "
                f"use '{replacement}' object keyed by OV/CV/AV"
            )


def _scan_unknown_traits(raw: dict[str, Any], entity_id: str, warnings: LoadWarnings) -> None:
    for key in raw:
        if key in _ENTITY_TRAITS:
            continue
        if key in _RESERVED_ENTITY_TRAITS:
            warnings.warn_reserved_trait(key, entity_id)
        else:
            warnings.warn_unknown_trait(key, entity_id)


def _parse_spawn(
    raw: dict[str, Any],
    entity_id: str,
    warnings: LoadWarnings,
) -> SpawnConfig:
    for key in raw:
        if key in _SPAWN_TRAITS:
            continue
        if key in _RESERVED_SPAWN_TRAITS:
            warnings.warn_reserved_trait(f"spawn.{key}", entity_id)
        else:
            warnings.warn_unknown_trait(f"spawn.{key}", entity_id)

    weight = _require_number(raw, "weight", entity_id=entity_id)
    # 0 = deprecated / never spawn (definition kept for old saves and lookups).
    if weight < 0:
        raise EntityLoadError(
            f"entity '{entity_id}': spawn.weight must be >= 0 (0 means never spawn)"
        )

    min_depth = _require_int(raw, "min_depth", entity_id=entity_id)
    max_depth = _require_int(raw, "max_depth", entity_id=entity_id)
    if min_depth > max_depth:
        raise EntityLoadError(
            f"entity '{entity_id}': spawn.min_depth cannot exceed spawn.max_depth"
        )

    terrain = raw.get("terrain", "land")
    if terrain not in {"land", "water"}:
        raise EntityLoadError(
            f"entity '{entity_id}': spawn.terrain must be 'land' or 'water'"
        )

    requires_vore_types = _parse_requires_vore_types(
        raw.get("requires_vore_types"),
        entity_id,
    )

    return SpawnConfig(
        weight=float(weight),
        min_depth=min_depth,
        max_depth=max_depth,
        terrain=terrain,
        requires_vore_types=requires_vore_types,
    )


def _parse_requires_vore_types(raw: Any, entity_id: str) -> frozenset[str]:
    """Parse spawn.requires_vore_types; omit/null/[] → empty; ignore unrecognized entries."""
    if raw is None:
        return frozenset()
    if not isinstance(raw, list):
        raise EntityLoadError(
            f"entity '{entity_id}': spawn.requires_vore_types must be an array or null"
        )
    recognized: set[str] = set()
    for item in raw:
        if isinstance(item, str) and item in _RECOGNIZED_VORE_TYPES:
            recognized.add(item)
    return frozenset(recognized)


def _parse_vore_variant(raw: Any, entity_id: str, path: str) -> VoreNarrativeVariant:
    if not isinstance(raw, dict):
        raise EntityLoadError(f"entity '{entity_id}': {path} must be an object")
    attempt = raw.get("attempt", [])
    success = raw.get("success", [])
    if not isinstance(attempt, list) or not all(isinstance(line, str) for line in attempt):
        raise EntityLoadError(f"entity '{entity_id}': {path}.attempt must be a string array")
    if not isinstance(success, list) or not all(isinstance(line, str) for line in success):
        raise EntityLoadError(f"entity '{entity_id}': {path}.success must be a string array")
    if not attempt:
        raise EntityLoadError(f"entity '{entity_id}': {path}.attempt must not be empty")
    if not success:
        raise EntityLoadError(f"entity '{entity_id}': {path}.success must not be empty")
    return VoreNarrativeVariant(attempt=tuple(attempt), success=tuple(success))


def _parse_vore_narratives(
    raw: Any,
    entity_id: str,
) -> dict[str, tuple[VoreNarrativeVariant, ...]] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise EntityLoadError(f"entity '{entity_id}': vore_narratives must be an object")

    parsed: dict[str, tuple[VoreNarrativeVariant, ...]] = {}
    for narrative_type, entry in raw.items():
        if not isinstance(narrative_type, str):
            raise EntityLoadError(
                f"entity '{entity_id}': invalid vore_narratives entry '{narrative_type}'"
            )
        variants: list[VoreNarrativeVariant] = []
        if isinstance(entry, dict) and "attempt" in entry:
            variants.append(
                _parse_vore_variant(entry, entity_id, f"vore_narratives.{narrative_type}")
            )
        elif isinstance(entry, list):
            for index, variant_raw in enumerate(entry):
                variants.append(
                    _parse_vore_variant(
                        variant_raw,
                        entity_id,
                        f"vore_narratives.{narrative_type}[{index}]",
                    )
                )
        else:
            raise EntityLoadError(
                f"entity '{entity_id}': vore_narratives.{narrative_type} must be "
                "an object or variant array"
            )
        if not variants:
            raise EntityLoadError(
                f"entity '{entity_id}': vore_narratives.{narrative_type} must not be empty"
            )
        parsed[narrative_type] = tuple(variants)
    return parsed


def _parse_narrative_type_lines(
    raw: Any,
    entity_id: str,
    field_name: str,
) -> dict[str, tuple[str, ...]] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise EntityLoadError(f"entity '{entity_id}': {field_name} must be an object")
    parsed: dict[str, tuple[str, ...]] = {}
    for narrative_type, lines in raw.items():
        if not isinstance(narrative_type, str) or not isinstance(lines, list):
            raise EntityLoadError(
                f"entity '{entity_id}': invalid {field_name} entry '{narrative_type}'"
            )
        if not all(isinstance(line, str) for line in lines) or not lines:
            raise EntityLoadError(
                f"entity '{entity_id}': {field_name}.{narrative_type} must be a "
                "non-empty string array"
            )
        parsed[narrative_type] = tuple(lines)
    return parsed


def _parse_engulfed_flavor(
    raw: Any,
    entity_id: str,
) -> dict[str, tuple[str, ...]] | None:
    """Optional per-type flavor arrays; empty arrays / omit keys are allowed (no-op pools)."""
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise EntityLoadError(f"entity '{entity_id}': engulfed_flavor must be an object")
    parsed: dict[str, tuple[str, ...]] = {}
    for narrative_type, lines in raw.items():
        if not isinstance(narrative_type, str) or not isinstance(lines, list):
            raise EntityLoadError(
                f"entity '{entity_id}': invalid engulfed_flavor entry '{narrative_type}'"
            )
        if not all(isinstance(line, str) for line in lines):
            raise EntityLoadError(
                f"entity '{entity_id}': engulfed_flavor.{narrative_type} must be a "
                "string array"
            )
        if not lines:
            continue
        parsed[narrative_type] = tuple(lines)
    return parsed or None


def _parse_introduction(raw: Any, entity_id: str) -> tuple[str, ...] | None:
    if raw is None:
        return None
    return _parse_phase_lines(raw, entity_id, "introduction")


def _parse_introduction_log_category(
    raw: Any,
    entity_id: str,
) -> MessageCategory | None:
    if raw is None:
        return None
    try:
        return parse_log_category_field(
            raw,
            context=f"entity '{entity_id}'.introduction_log_category",
        )
    except ValueError as exc:
        raise EntityLoadError(str(exc)) from exc


def _parse_phase_lines(raw: Any, entity_id: str, path: str) -> tuple[str, ...]:
    if not isinstance(raw, list) or not raw:
        raise EntityLoadError(f"entity '{entity_id}': {path} must be a non-empty string array")
    if not all(isinstance(line, str) and line for line in raw):
        raise EntityLoadError(f"entity '{entity_id}': {path} must contain non-empty strings")
    return tuple(raw)


def _parse_digestion_modal_variants(
    raw: Any,
    entity_id: str,
    path: str,
) -> tuple[tuple[str, ...], ...]:
    if isinstance(raw, str):
        if not raw:
            raise EntityLoadError(f"entity '{entity_id}': {path} must not be empty")
        return ((raw,),)
    if isinstance(raw, dict) and "phases" in raw:
        return (_parse_phase_lines(raw["phases"], entity_id, f"{path}.phases"),)
    if isinstance(raw, list):
        if all(isinstance(item, str) for item in raw):
            return (_parse_phase_lines(raw, entity_id, path),)
        variants: list[tuple[str, ...]] = []
        for index, entry in enumerate(raw):
            variant_path = f"{path}[{index}]"
            if isinstance(entry, dict) and "phases" in entry:
                variants.append(
                    _parse_phase_lines(entry["phases"], entity_id, f"{variant_path}.phases")
                )
            elif isinstance(entry, str) and entry:
                variants.append((entry,))
            else:
                raise EntityLoadError(
                    f"entity '{entity_id}': {variant_path} must be a string or "
                    "object with phases"
                )
        if not variants:
            raise EntityLoadError(f"entity '{entity_id}': {path} must not be empty")
        return tuple(variants)
    raise EntityLoadError(
        f"entity '{entity_id}': {path} must be a string, phase array, or variant array"
    )


def _parse_digestion_player_modal(
    raw: Any,
    entity_id: str,
) -> dict[str, tuple[tuple[str, ...], ...]] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise EntityLoadError(f"entity '{entity_id}': digestion_player_modal must be an object")
    parsed: dict[str, tuple[tuple[str, ...], ...]] = {}
    for narrative_type, entry in raw.items():
        if not isinstance(narrative_type, str):
            raise EntityLoadError(
                f"entity '{entity_id}': invalid digestion_player_modal entry '{narrative_type}'"
            )
        parsed[narrative_type] = _parse_digestion_modal_variants(
            entry,
            entity_id,
            f"digestion_player_modal.{narrative_type}",
        )
    return parsed


def _parse_alignment(value: str, entity_id: str) -> Alignment:
    try:
        return _ALIGNMENT_MAP[value]
    except KeyError as exc:
        raise EntityLoadError(
            f"entity '{entity_id}': alignment must be good, evil, or neutral"
        ) from exc


def _parse_mobility(value: str, entity_id: str) -> MobilityType:
    try:
        return _MOBILITY_MAP[value]
    except KeyError as exc:
        raise EntityLoadError(
            f"entity '{entity_id}': mobility must be ground, fly, aquatic, or stationary"
        ) from exc


def _parse_rgb(value: Any, entity_id: str) -> tuple[int, int, int]:
    if not isinstance(value, list) or len(value) != 3:
        raise EntityLoadError(f"entity '{entity_id}': fg must be [r, g, b]")
    components: list[int] = []
    for channel in value:
        if not isinstance(channel, int) or not 0 <= channel <= 255:
            raise EntityLoadError(f"entity '{entity_id}': fg values must be integers 0-255")
        components.append(channel)
    return (components[0], components[1], components[2])


def _require_str(raw: dict[str, Any], key: str, *, entity_id: str | None = None) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        label = f"entity '{entity_id}'" if entity_id else "entities file"
        raise EntityLoadError(f"{label}: missing or invalid string '{key}'")
    return value


def _require_int(
    raw: dict[str, Any],
    key: str,
    *,
    entity_id: str | None = None,
    context: str | None = None,
) -> int:
    value = raw.get(key)
    if not isinstance(value, int):
        if context:
            raise EntityLoadError(f"{context}: missing or invalid integer '{key}'")
        label = f"entity '{entity_id}'" if entity_id else "entities file"
        raise EntityLoadError(f"{label}: missing or invalid integer '{key}'")
    return value


def _require_number(
    raw: dict[str, Any],
    key: str,
    *,
    entity_id: str | None = None,
) -> float:
    value = raw.get(key)
    if not isinstance(value, (int, float)):
        label = f"entity '{entity_id}'" if entity_id else "entities file"
        raise EntityLoadError(f"{label}: missing or invalid number '{key}'")
    return float(value)