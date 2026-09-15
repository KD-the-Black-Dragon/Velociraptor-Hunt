"""Load ``data/npc_prefixes.json`` (whole-file mod replace)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.components import Alignment
from src.constants import DATA_DIR
from src.data.ability_parser import (
    ABILITY_FAMILY_TOKENS,
    FIXED_ABILITY_IDS,
    FixedAbility,
    parse_ability_token,
)
from src.data.abilities import IMPLEMENTED_FIXED_IDS, IMPLEMENTED_KINDS
from src.data.depth_scaling_config import ALIGNMENT_BY_NAME
from src.data.npc_prefix_registry import (
    NpcPrefixDefinition,
    NpcPrefixRegistry,
    PrefixRequirements,
    PrefixStatBonuses,
)

NPC_PREFIXES_PATH = DATA_DIR / "npc_prefixes.json"
NPC_PREFIXES_SCHEMA_VERSION = 1
NPC_PREFIXES_FILENAME = "npc_prefixes.json"

_STAT_INT_KEYS = frozenset(
    {
        "max_hp",
        "ac",
        "evade",
        "min_damage",
        "max_damage",
        "digestion_damage_per_tick",
    }
)


class NpcPrefixLoadError(ValueError):
    pass


def load_npc_prefix_registry(
    path: Path | None = None,
    *,
    mods_root: Path | None = None,
    report_mod_errors: bool = True,
) -> NpcPrefixRegistry:
    if path is not None:
        if mods_root is not None:
            raise TypeError("mods_root is only valid when path is None (layered load)")
        with path.open(encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, dict):
            raise NpcPrefixLoadError("npc_prefixes file must be a JSON object")
        return parse_npc_prefix_registry(raw)

    from src.mods.pipeline import load_npc_prefixes_layered

    registry, _issues = load_npc_prefixes_layered(
        mods_root=mods_root,
        report=report_mod_errors,
    )
    return registry


@lru_cache(maxsize=1)
def default_npc_prefix_registry() -> NpcPrefixRegistry:
    return load_npc_prefix_registry()


def reset_npc_prefix_registry_cache() -> None:
    default_npc_prefix_registry.cache_clear()


def parse_npc_prefix_registry(raw: dict[str, Any]) -> NpcPrefixRegistry:
    schema_version = _require_int(raw, "schema_version", context="npc_prefixes file")
    if schema_version != NPC_PREFIXES_SCHEMA_VERSION:
        raise NpcPrefixLoadError(
            f"npc_prefixes file: unsupported schema_version {schema_version}"
        )

    prefixes_raw = raw.get("prefixes")
    if not isinstance(prefixes_raw, list):
        raise NpcPrefixLoadError("npc_prefixes file: 'prefixes' must be an array")

    prefixes: list[NpcPrefixDefinition] = []
    seen: set[str] = set()
    for index, entry in enumerate(prefixes_raw):
        if not isinstance(entry, dict):
            raise NpcPrefixLoadError(f"prefixes[{index}] must be an object")
        prefix = _parse_prefix(entry, index=index)
        if prefix.id in seen:
            raise NpcPrefixLoadError(f"duplicate prefix id '{prefix.id}'")
        seen.add(prefix.id)
        prefixes.append(prefix)

    for key in raw:
        if key in {"schema_version", "prefixes"}:
            continue
        raise NpcPrefixLoadError(f"npc_prefixes file: unknown top-level field '{key}'")

    return NpcPrefixRegistry(schema_version=schema_version, prefixes=tuple(prefixes))


def _parse_prefix(entry: dict[str, Any], *, index: int) -> NpcPrefixDefinition:
    context = f"prefixes[{index}]"
    prefix_id = _require_str(entry, "id", context=context)
    display_prefix = _require_str(entry, "display_prefix", context=context)

    alignments_raw = entry.get("apply_to_alignments")
    if not isinstance(alignments_raw, list) or not alignments_raw:
        raise NpcPrefixLoadError(
            f"{context}: 'apply_to_alignments' must be a non-empty array"
        )
    alignments: set[Alignment] = set()
    for i, name in enumerate(alignments_raw):
        if not isinstance(name, str):
            raise NpcPrefixLoadError(
                f"{context}: apply_to_alignments[{i}] must be a string"
            )
        alignment = ALIGNMENT_BY_NAME.get(name.lower())
        if alignment is None:
            raise NpcPrefixLoadError(
                f"{context}: unknown alignment '{name}'"
            )
        alignments.add(alignment)

    min_depth = _require_int(entry, "min_depth", context=context)
    max_depth = _require_int(entry, "max_depth", context=context)
    if min_depth > max_depth:
        raise NpcPrefixLoadError(f"{context}: min_depth must be <= max_depth")

    weight = entry.get("weight")
    if isinstance(weight, bool) or not isinstance(weight, int) or weight < 0:
        raise NpcPrefixLoadError(f"{context}: 'weight' must be an integer >= 0")

    bonuses_raw = entry.get("stat_bonuses", {})
    if bonuses_raw is None:
        bonuses_raw = {}
    if not isinstance(bonuses_raw, dict):
        raise NpcPrefixLoadError(f"{context}: 'stat_bonuses' must be an object")
    bonuses = _parse_stat_bonuses(bonuses_raw, context=f"{context}.stat_bonuses")
    grant_abilities = _parse_grant_abilities(
        entry.get("grant_abilities"), context=context
    )
    requirements = _parse_requirements(entry.get("requirements"), context=context)

    for key in entry:
        if key in {
            "id",
            "display_prefix",
            "apply_to_alignments",
            "min_depth",
            "max_depth",
            "weight",
            "stat_bonuses",
            "grant_abilities",
            "requirements",
        }:
            continue
        raise NpcPrefixLoadError(f"{context}: unknown field '{key}'")

    return NpcPrefixDefinition(
        id=prefix_id,
        display_prefix=display_prefix,
        apply_to_alignments=frozenset(alignments),
        min_depth=min_depth,
        max_depth=max_depth,
        weight=weight,
        stat_bonuses=bonuses,
        grant_abilities=grant_abilities,
        requirements=requirements,
    )


def _parse_stat_bonuses(raw: dict[str, Any], *, context: str) -> PrefixStatBonuses:
    values: dict[str, int | float] = {
        "max_hp": 0,
        "ac": 0,
        "evade": 0.0,
        "accuracy": 0.0,
        "ranged_accuracy": 0.0,
        "min_damage": 0,
        "max_damage": 0,
        "digestion_damage_per_tick": 0,
    }
    for key, value in raw.items():
        if key not in values:
            raise NpcPrefixLoadError(f"{context}: unknown stat '{key}'")
        if key in {"accuracy", "ranged_accuracy", "evade"}:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise NpcPrefixLoadError(f"{context}: '{key}' must be a number")
            values[key] = float(value)
        else:
            if isinstance(value, bool) or not isinstance(value, int):
                raise NpcPrefixLoadError(f"{context}: '{key}' must be an integer")
            values[key] = value
    return PrefixStatBonuses(
        max_hp=int(values["max_hp"]),
        ac=int(values["ac"]),
        evade=float(values["evade"]),
        accuracy=float(values["accuracy"]),
        ranged_accuracy=float(values["ranged_accuracy"]),
        min_damage=int(values["min_damage"]),
        max_damage=int(values["max_damage"]),
        digestion_damage_per_tick=int(values["digestion_damage_per_tick"]),
    )


def _parse_grant_abilities(
    raw: object | None,
    *,
    context: str,
) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise NpcPrefixLoadError(f"{context}: 'grant_abilities' must be an array")
    tokens: list[str] = []
    for index, token in enumerate(raw):
        if not isinstance(token, str) or not token:
            raise NpcPrefixLoadError(
                f"{context}: grant_abilities[{index}] must be a non-empty string"
            )
        parsed = parse_ability_token(token)
        if parsed is None:
            raise NpcPrefixLoadError(
                f"{context}: grant_abilities[{index}] unknown ability '{token}'"
            )
        if isinstance(parsed, FixedAbility):
            if parsed.ability_id not in IMPLEMENTED_FIXED_IDS:
                raise NpcPrefixLoadError(
                    f"{context}: grant_abilities[{index}] unimplemented ability '{token}'"
                )
        elif type(parsed) not in IMPLEMENTED_KINDS:
            raise NpcPrefixLoadError(
                f"{context}: grant_abilities[{index}] unimplemented ability '{token}'"
            )
        tokens.append(token)
    return tuple(tokens)


def _parse_requirements(
    raw: object | None,
    *,
    context: str,
) -> PrefixRequirements:
    if raw is None:
        return PrefixRequirements()
    if not isinstance(raw, dict):
        raise NpcPrefixLoadError(f"{context}: 'requirements' must be an object")
    allowed = {"ability_families"}
    for key in raw:
        if key not in allowed:
            raise NpcPrefixLoadError(f"{context}.requirements: unknown field '{key}'")
    families_raw = raw.get("ability_families")
    if families_raw is None:
        return PrefixRequirements()
    if not isinstance(families_raw, list) or not families_raw:
        raise NpcPrefixLoadError(
            f"{context}.requirements: 'ability_families' must be a non-empty array"
        )
    families: set[str] = set()
    allowed_families = ABILITY_FAMILY_TOKENS | FIXED_ABILITY_IDS
    for index, family in enumerate(families_raw):
        if not isinstance(family, str) or not family:
            raise NpcPrefixLoadError(
                f"{context}.requirements: ability_families[{index}] must be a non-empty string"
            )
        if family not in allowed_families:
            raise NpcPrefixLoadError(
                f"{context}.requirements: unknown ability family '{family}'"
            )
        families.add(family)
    return PrefixRequirements(ability_families=frozenset(families))


def _require_str(raw: dict[str, Any], key: str, *, context: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise NpcPrefixLoadError(f"{context}: '{key}' must be a non-empty string")
    return value


def _require_int(raw: dict[str, Any], key: str, *, context: str) -> int:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise NpcPrefixLoadError(f"{context}: '{key}' must be an integer")
    return value
