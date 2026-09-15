"""Layer core game JSON with enabled mods (id catalogs + entities)."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from src.data.depth_scaling_config import DepthScalingConfig
from src.data.depth_scaling_loader import (
    DEPTH_SCALING_PATH,
    parse_depth_scaling_config,
)
from src.data.npc_prefix_loader import (
    NPC_PREFIXES_PATH,
    parse_npc_prefix_registry,
)
from src.data.npc_prefix_registry import NpcPrefixRegistry
from src.data.dungeon_spawn_config import DungeonSpawnConfig
from src.data.dungeon_spawn_loader import (
    DUNGEON_SPAWN_PATH,
    parse_dungeon_spawn_config,
)
from src.data.global_tuning_config import GlobalTuning
from src.data.global_tuning_loader import (
    GLOBAL_TUNING_PATH,
    parse_global_tuning,
)
from src.data.entity_loader import ENTITIES_PATH, EntityLoadError, parse_entity_registry
from src.data.entity_registry import EntityRegistry
from src.data.floor_rune_loader import FLOOR_RUNES_PATH, parse_floor_rune_registry
from src.data.floor_rune_registry import FloorRuneRegistry
from src.data.item_loader import (
    ItemLoadError,
    _parse_armor,
    _parse_potion,
    _parse_throwable,
    _parse_wand,
    _parse_weapon,
)
from src.data.item_loaders import (
    ARMOR_PATH,
    POTIONS_PATH,
    THROWABLES_PATH,
    WANDS_PATH,
    WEAPONS_PATH,
)
from src.data.item_registry import ItemRegistry
from src.data.macguffin_loader import MACGUFFINS_PATH, parse_macguffin_registry
from src.data.macguffin_registry import MacguffinRegistry
from src.data.names_loader import NAMES_PATH, NamesLoadError, parse_names_registry
from src.data.names_registry import NamesRegistry
from src.data.rescue_gratitude_loader import (
    RESCUE_GRATITUDE_PATH,
    parse_rescue_gratitude_registry,
)
from src.data.rescue_gratitude_registry import RescueGratitudeRegistry
from src.mods.discovery import enabled_mods_in_load_order
from src.mods.errors import ModLoadIssue, report_mod_data_errors
from src.mods.json_merge import deep_merge_json
from src.ui.layout import UI_LAYOUT_PATH, UILayout, parse_ui_layout

T = TypeVar("T")
EntryMergeMode = str  # "replace" | "deep"

ENTITIES_FILENAME = "entities.json"
WEAPONS_FILENAME = "weapons.json"
ARMOR_FILENAME = "armor.json"
POTIONS_FILENAME = "potions.json"
WANDS_FILENAME = "wands.json"
THROWABLES_FILENAME = "throwables.json"
FLOOR_RUNES_FILENAME = "floor_runes.json"
MACGUFFINS_FILENAME = "macguffins.json"
NAMES_FILENAME = "names.json"
DUNGEON_SPAWN_FILENAME = "dungeon_spawn.json"
DEPTH_SCALING_FILENAME = "depth_scaling.json"
GLOBAL_TUNING_FILENAME = "global_tuning.json"
NPC_PREFIXES_FILENAME = "npc_prefixes.json"
RESCUE_GRATITUDE_FILENAME = "rescue_gratitude.json"
UI_LAYOUT_FILENAME = "ui_layout.json"


def _load_json_object(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise ValueError(f"{path.name} must be a JSON object")
    return raw


def _merge_id_list(
    base_list: list[dict[str, Any]],
    overlay_list: list[Any],
    *,
    list_key: str,
    entry_merge: EntryMergeMode = "replace",
) -> list[dict[str, Any]]:
    """Merge catalog entries by ``id``. Preserve base order; append new ids.

    ``entry_merge``:
    - ``\"replace\"`` (default): overlay entry fully replaces the prior entry.
    - ``\"deep\"``: overlay deep-merges onto the prior entry (objects recurse;
      arrays/scalars replace). New ids are still inserted as the overlay object.
    """
    if entry_merge not in ("replace", "deep"):
        raise ValueError(f"unsupported entry_merge mode: {entry_merge!r}")

    by_id: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for index, entry in enumerate(base_list):
        if not isinstance(entry, dict):
            raise ValueError(f"{list_key}[{index}] must be an object")
        entity_id = entry.get("id")
        if not isinstance(entity_id, str) or not entity_id:
            raise ValueError(f"{list_key}[{index}]: missing or invalid string 'id'")
        if entity_id not in by_id:
            order.append(entity_id)
        by_id[entity_id] = entry

    for index, entry in enumerate(overlay_list):
        if not isinstance(entry, dict):
            raise ValueError(f"{list_key}[{index}] must be an object")
        entity_id = entry.get("id")
        if not isinstance(entity_id, str) or not entity_id:
            raise ValueError(f"{list_key}[{index}]: missing or invalid string 'id'")
        if entity_id not in by_id:
            order.append(entity_id)
            by_id[entity_id] = entry
        elif entry_merge == "deep":
            by_id[entity_id] = deep_merge_json(by_id[entity_id], entry)
        else:
            by_id[entity_id] = entry

    return [by_id[entity_id] for entity_id in order]


def _merge_names_map(
    base_names: dict[str, Any],
    overlay_names: dict[str, Any],
) -> dict[str, Any]:
    """Later mod replaces the name pool for the same entity id key."""
    merged = dict(base_names)
    for key, pool in overlay_names.items():
        if not isinstance(key, str) or not key:
            raise ValueError("names keys must be non-empty strings")
        merged[key] = pool
    return merged


def _reason_from_exc(exc: BaseException) -> str:
    if isinstance(exc, json.JSONDecodeError):
        return f"Invalid JSON near line {exc.lineno} column {exc.colno} — {exc.msg}"
    if isinstance(exc, OSError):
        return f"could not read file ({exc})"
    return str(exc)


def layer_id_list_catalog(
    *,
    core_path: Path,
    filename: str,
    list_key: str,
    parse: Callable[[dict[str, Any]], T],
    mods_root: Path | None = None,
    entry_merge: EntryMergeMode = "replace",
) -> tuple[T, tuple[ModLoadIssue, ...]]:
    """Core list-by-id catalog, then enabled mods; parse after each successful merge."""
    core_raw = _load_json_object(core_path)
    entries = core_raw.get(list_key)
    if not isinstance(entries, list):
        raise ValueError(f"{filename}: missing '{list_key}' array")
    schema_version = core_raw.get("schema_version")
    if not isinstance(schema_version, int):
        raise ValueError(f"{filename}: schema_version must be an integer")

    current_list = [e for e in entries if isinstance(e, dict)]
    # Keep non-dict detection on first parse of core
    current_raw: dict[str, Any] = {
        "schema_version": schema_version,
        list_key: list(entries),
    }
    result = parse(current_raw)
    current_list = list(current_raw[list_key])  # type: ignore[arg-type]

    issues: list[ModLoadIssue] = []
    for mod in enabled_mods_in_load_order(root=mods_root):
        mod_file = mod.path / filename
        if not mod_file.is_file():
            continue
        try:
            overlay_raw = _load_json_object(mod_file)
            overlay_list = overlay_raw.get(list_key)
            if not isinstance(overlay_list, list):
                raise ValueError(f"missing '{list_key}' array")
            merged_list = _merge_id_list(
                [e for e in current_list if isinstance(e, dict)],
                overlay_list,
                list_key=list_key,
                entry_merge=entry_merge,
            )
            merged_raw = {"schema_version": schema_version, list_key: merged_list}
            result = parse(merged_raw)
            current_list = merged_list
            current_raw = merged_raw
        except (json.JSONDecodeError, OSError, ValueError, TypeError, KeyError) as exc:
            issues.append(
                ModLoadIssue(mod_name=mod.name, filename=filename, reason=_reason_from_exc(exc))
            )

    return result, tuple(issues)


def layer_names_catalog(
    *,
    core_path: Path | None = None,
    mods_root: Path | None = None,
) -> tuple[NamesRegistry, tuple[ModLoadIssue, ...]]:
    data_path = core_path if core_path is not None else NAMES_PATH
    core_raw = _load_json_object(data_path)
    schema_version = core_raw.get("schema_version")
    if not isinstance(schema_version, int):
        raise NamesLoadError("names file: missing or invalid integer 'schema_version'")
    names_map = core_raw.get("names")
    if not isinstance(names_map, dict):
        raise NamesLoadError("names file: 'names' must be an object")

    current: dict[str, Any] = {
        "schema_version": schema_version,
        "names": dict(names_map),
    }
    registry = parse_names_registry(current)
    issues: list[ModLoadIssue] = []

    for mod in enabled_mods_in_load_order(root=mods_root):
        mod_file = mod.path / NAMES_FILENAME
        if not mod_file.is_file():
            continue
        try:
            overlay_raw = _load_json_object(mod_file)
            overlay_names = overlay_raw.get("names")
            if not isinstance(overlay_names, dict):
                raise NamesLoadError("names file: 'names' must be an object")
            merged_names = _merge_names_map(current["names"], overlay_names)
            merged = {"schema_version": schema_version, "names": merged_names}
            registry = parse_names_registry(merged)
            current = merged
        except (json.JSONDecodeError, OSError, NamesLoadError, ValueError, TypeError, KeyError) as exc:
            issues.append(
                ModLoadIssue(
                    mod_name=mod.name,
                    filename=NAMES_FILENAME,
                    reason=_reason_from_exc(exc),
                )
            )

    return registry, tuple(issues)


def load_entities_layered(
    *,
    core_path: Path | None = None,
    mods_root: Path | None = None,
    report: bool = True,
) -> tuple[EntityRegistry, tuple[ModLoadIssue, ...]]:
    """Load core ``entities.json``, then enabled mods in order; later fields win.

    Existing ids deep-merge (objects recurse; arrays replace). New ids must be
    complete entity objects.
    """
    data_path = core_path if core_path is not None else ENTITIES_PATH

    def _parse(raw: dict[str, Any]) -> EntityRegistry:
        return parse_entity_registry(raw)

    try:
        registry, issues = layer_id_list_catalog(
            core_path=data_path,
            filename=ENTITIES_FILENAME,
            list_key="entities",
            parse=_parse,
            mods_root=mods_root,
            entry_merge="deep",
        )
    except (json.JSONDecodeError, OSError, EntityLoadError, ValueError) as exc:
        # Core hard-fail: re-raise as EntityLoadError when possible
        if isinstance(exc, EntityLoadError):
            raise
        if isinstance(exc, json.JSONDecodeError):
            raise
        if isinstance(exc, OSError):
            raise
        raise EntityLoadError(str(exc)) from exc

    if report and issues:
        report_mod_data_errors(issues)
    return registry, issues


def _parse_item_collection(
    raw: dict[str, Any],
    *,
    list_key: str,
    parse_entry: Callable[..., Any],
) -> tuple[Any, ...]:
    entries = raw.get(list_key)
    if not isinstance(entries, list):
        raise ItemLoadError(f"missing '{list_key}' array")
    parsed = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ItemLoadError(f"{list_key}[{index}] must be an object")
        parsed.append(parse_entry(entry, context=f"{list_key}[{index}]"))
    return tuple(parsed)


def load_items_layered(
    *,
    weapons_path: Path | None = None,
    armor_path: Path | None = None,
    potions_path: Path | None = None,
    wands_path: Path | None = None,
    throwables_path: Path | None = None,
    mods_root: Path | None = None,
    report: bool = True,
) -> tuple[ItemRegistry, tuple[ModLoadIssue, ...]]:
    """Layer weapons/armor/potions/wands/throwables by id across enabled mods."""
    all_issues: list[ModLoadIssue] = []

    def weapons_parse(raw: dict[str, Any]) -> tuple[Any, ...]:
        return _parse_item_collection(raw, list_key="weapons", parse_entry=_parse_weapon)

    def armor_parse(raw: dict[str, Any]) -> tuple[Any, ...]:
        return _parse_item_collection(raw, list_key="armor", parse_entry=_parse_armor)

    def potions_parse(raw: dict[str, Any]) -> tuple[Any, ...]:
        return _parse_item_collection(raw, list_key="potions", parse_entry=_parse_potion)

    def wands_parse(raw: dict[str, Any]) -> tuple[Any, ...]:
        return _parse_item_collection(raw, list_key="wands", parse_entry=_parse_wand)

    def throwables_parse(raw: dict[str, Any]) -> tuple[Any, ...]:
        return _parse_item_collection(
            raw,
            list_key="throwables",
            parse_entry=_parse_throwable,
        )

    weapons, w_issues = layer_id_list_catalog(
        core_path=weapons_path or WEAPONS_PATH,
        filename=WEAPONS_FILENAME,
        list_key="weapons",
        parse=weapons_parse,
        mods_root=mods_root,
    )
    armor, a_issues = layer_id_list_catalog(
        core_path=armor_path or ARMOR_PATH,
        filename=ARMOR_FILENAME,
        list_key="armor",
        parse=armor_parse,
        mods_root=mods_root,
    )
    potions, p_issues = layer_id_list_catalog(
        core_path=potions_path or POTIONS_PATH,
        filename=POTIONS_FILENAME,
        list_key="potions",
        parse=potions_parse,
        mods_root=mods_root,
    )
    wands, d_issues = layer_id_list_catalog(
        core_path=wands_path or WANDS_PATH,
        filename=WANDS_FILENAME,
        list_key="wands",
        parse=wands_parse,
        mods_root=mods_root,
    )
    throwables, t_issues = layer_id_list_catalog(
        core_path=throwables_path or THROWABLES_PATH,
        filename=THROWABLES_FILENAME,
        list_key="throwables",
        parse=throwables_parse,
        mods_root=mods_root,
    )
    all_issues.extend(w_issues)
    all_issues.extend(a_issues)
    all_issues.extend(p_issues)
    all_issues.extend(d_issues)
    all_issues.extend(t_issues)

    registry = ItemRegistry(
        schema_version=1,
        weapons=weapons,
        armor=armor,
        potions=potions,
        wands=wands,
        throwables=throwables,
        warnings=(),
    )
    issue_tuple = tuple(all_issues)
    if report and issue_tuple:
        report_mod_data_errors(issue_tuple)
    return registry, issue_tuple


def load_floor_runes_layered(
    *,
    core_path: Path | None = None,
    mods_root: Path | None = None,
    report: bool = True,
) -> tuple[FloorRuneRegistry, tuple[ModLoadIssue, ...]]:
    registry, issues = layer_id_list_catalog(
        core_path=core_path or FLOOR_RUNES_PATH,
        filename=FLOOR_RUNES_FILENAME,
        list_key="runes",
        parse=parse_floor_rune_registry,
        mods_root=mods_root,
    )
    if report and issues:
        report_mod_data_errors(issues)
    return registry, issues


def load_macguffins_layered(
    *,
    core_path: Path | None = None,
    mods_root: Path | None = None,
    report: bool = True,
) -> tuple[MacguffinRegistry, tuple[ModLoadIssue, ...]]:
    registry, issues = layer_id_list_catalog(
        core_path=core_path or MACGUFFINS_PATH,
        filename=MACGUFFINS_FILENAME,
        list_key="macguffins",
        parse=parse_macguffin_registry,
        mods_root=mods_root,
    )
    if report and issues:
        report_mod_data_errors(issues)
    return registry, issues


def load_names_layered(
    *,
    core_path: Path | None = None,
    mods_root: Path | None = None,
    report: bool = True,
) -> tuple[NamesRegistry, tuple[ModLoadIssue, ...]]:
    registry, issues = layer_names_catalog(core_path=core_path, mods_root=mods_root)
    if report and issues:
        report_mod_data_errors(issues)
    return registry, issues


def layer_whole_file_catalog(
    *,
    core_path: Path,
    filename: str,
    parse: Callable[[dict[str, Any]], T],
    mods_root: Path | None = None,
) -> tuple[T, tuple[ModLoadIssue, ...]]:
    """Core file first; each enabled mod that provides *filename* fully replaces it.

    Overlay is applied only when it parses successfully; bad mods are skipped.
    """
    current_raw = _load_json_object(core_path)
    result = parse(current_raw)
    issues: list[ModLoadIssue] = []

    for mod in enabled_mods_in_load_order(root=mods_root):
        mod_file = mod.path / filename
        if not mod_file.is_file():
            continue
        try:
            overlay_raw = _load_json_object(mod_file)
            result = parse(overlay_raw)
            current_raw = overlay_raw
        except (json.JSONDecodeError, OSError, ValueError, TypeError, KeyError) as exc:
            issues.append(
                ModLoadIssue(mod_name=mod.name, filename=filename, reason=_reason_from_exc(exc))
            )

    return result, tuple(issues)


def layer_whole_file_document(
    *,
    core_path: Path,
    filename: str,
    validate: Callable[[dict[str, Any]], None],
    mods_root: Path | None = None,
) -> tuple[dict[str, Any], tuple[ModLoadIssue, ...]]:
    """Like :func:`layer_whole_file_catalog` but returns the winning raw document."""
    current_raw = _load_json_object(core_path)
    validate(current_raw)
    issues: list[ModLoadIssue] = []

    for mod in enabled_mods_in_load_order(root=mods_root):
        mod_file = mod.path / filename
        if not mod_file.is_file():
            continue
        try:
            overlay_raw = _load_json_object(mod_file)
            validate(overlay_raw)
            current_raw = overlay_raw
        except (json.JSONDecodeError, OSError, ValueError, TypeError, KeyError) as exc:
            issues.append(
                ModLoadIssue(mod_name=mod.name, filename=filename, reason=_reason_from_exc(exc))
            )

    return current_raw, tuple(issues)


def load_dungeon_spawn_layered(
    *,
    core_path: Path | None = None,
    mods_root: Path | None = None,
    report: bool = True,
) -> tuple[DungeonSpawnConfig, tuple[ModLoadIssue, ...]]:
    config, issues = layer_whole_file_catalog(
        core_path=core_path or DUNGEON_SPAWN_PATH,
        filename=DUNGEON_SPAWN_FILENAME,
        parse=parse_dungeon_spawn_config,
        mods_root=mods_root,
    )
    if report and issues:
        report_mod_data_errors(issues)
    return config, issues


def load_depth_scaling_layered(
    *,
    core_path: Path | None = None,
    mods_root: Path | None = None,
    report: bool = True,
) -> tuple[DepthScalingConfig, tuple[ModLoadIssue, ...]]:
    config, issues = layer_whole_file_catalog(
        core_path=core_path or DEPTH_SCALING_PATH,
        filename=DEPTH_SCALING_FILENAME,
        parse=parse_depth_scaling_config,
        mods_root=mods_root,
    )
    if report and issues:
        report_mod_data_errors(issues)
    return config, issues


def load_global_tuning_layered(
    *,
    core_path: Path | None = None,
    mods_root: Path | None = None,
    report: bool = True,
) -> tuple[GlobalTuning, tuple[ModLoadIssue, ...]]:
    config, issues = layer_whole_file_catalog(
        core_path=core_path or GLOBAL_TUNING_PATH,
        filename=GLOBAL_TUNING_FILENAME,
        parse=parse_global_tuning,
        mods_root=mods_root,
    )
    if report and issues:
        report_mod_data_errors(issues)
    return config, issues


def load_npc_prefixes_layered(
    *,
    core_path: Path | None = None,
    mods_root: Path | None = None,
    report: bool = True,
) -> tuple[NpcPrefixRegistry, tuple[ModLoadIssue, ...]]:
    registry, issues = layer_whole_file_catalog(
        core_path=core_path or NPC_PREFIXES_PATH,
        filename=NPC_PREFIXES_FILENAME,
        parse=parse_npc_prefix_registry,
        mods_root=mods_root,
    )
    if report and issues:
        report_mod_data_errors(issues)
    return registry, issues


def load_rescue_gratitude_layered(
    *,
    core_path: Path | None = None,
    mods_root: Path | None = None,
    report: bool = True,
) -> tuple[RescueGratitudeRegistry, tuple[ModLoadIssue, ...]]:
    registry, issues = layer_whole_file_catalog(
        core_path=core_path or RESCUE_GRATITUDE_PATH,
        filename=RESCUE_GRATITUDE_FILENAME,
        parse=parse_rescue_gratitude_registry,
        mods_root=mods_root,
    )
    if report and issues:
        report_mod_data_errors(issues)
    return registry, issues


def load_ui_layout_document_layered(
    *,
    core_path: Path | None = None,
    mods_root: Path | None = None,
    report: bool = True,
) -> tuple[dict[str, Any], tuple[ModLoadIssue, ...]]:
    """Effective ``ui_layout.json`` document after whole-file mod replaces."""

    def _validate(raw: dict[str, Any]) -> None:
        parse_ui_layout(raw)

    document, issues = layer_whole_file_document(
        core_path=core_path or UI_LAYOUT_PATH,
        filename=UI_LAYOUT_FILENAME,
        validate=_validate,
        mods_root=mods_root,
    )
    if report and issues:
        report_mod_data_errors(issues)
    return document, issues


def load_ui_layout_layered(
    *,
    preset: str | None = None,
    core_path: Path | None = None,
    mods_root: Path | None = None,
    report: bool = True,
) -> tuple[UILayout, tuple[ModLoadIssue, ...]]:
    document, issues = load_ui_layout_document_layered(
        core_path=core_path,
        mods_root=mods_root,
        report=False,
    )
    layout = parse_ui_layout(document, preset=preset)
    if report and issues:
        report_mod_data_errors(issues)
    return layout, issues


def load_all_layered(
    *,
    mods_root: Path | None = None,
    report: bool = True,
) -> tuple[ModLoadIssue, ...]:
    """Load all moddable JSON domains; install default caches; one combined report."""
    from src.data.depth_scaling_loader import reset_depth_scaling_cache
    from src.data.entity_loader import reset_entity_registry_cache
    from src.data.global_tuning_loader import reset_global_tuning_cache
    from src.data.names_loader import reset_names_registry
    from src.data.npc_prefix_loader import reset_npc_prefix_registry_cache
    from src.data.rescue_gratitude_loader import reset_rescue_gratitude_registry
    from src.systems.inventory import reset_item_registry_cache

    all_issues: list[ModLoadIssue] = []

    entities, ei = load_entities_layered(mods_root=mods_root, report=False)
    all_issues.extend(ei)
    items, ii = load_items_layered(mods_root=mods_root, report=False)
    all_issues.extend(ii)
    _runes, ri = load_floor_runes_layered(mods_root=mods_root, report=False)
    all_issues.extend(ri)
    _macs, mi = load_macguffins_layered(mods_root=mods_root, report=False)
    all_issues.extend(mi)
    names, ni = load_names_layered(mods_root=mods_root, report=False)
    all_issues.extend(ni)
    _spawn, si = load_dungeon_spawn_layered(mods_root=mods_root, report=False)
    all_issues.extend(si)
    _depth, di = load_depth_scaling_layered(mods_root=mods_root, report=False)
    all_issues.extend(di)
    _global, gi_tune = load_global_tuning_layered(mods_root=mods_root, report=False)
    all_issues.extend(gi_tune)
    _prefixes, pi = load_npc_prefixes_layered(mods_root=mods_root, report=False)
    all_issues.extend(pi)
    gratitude, gi = load_rescue_gratitude_layered(mods_root=mods_root, report=False)
    all_issues.extend(gi)
    _layout_doc, li = load_ui_layout_document_layered(mods_root=mods_root, report=False)
    all_issues.extend(li)

    # Install caches used by gameplay loaders
    reset_entity_registry_cache()
    import src.data.entity_loader as entity_loader_mod

    entity_loader_mod._default_registry = entities

    reset_item_registry_cache()
    import src.systems.inventory as inventory_mod

    inventory_mod._ITEM_REGISTRY = items

    reset_names_registry()
    import src.data.names_loader as names_mod

    names_mod._names_registry = names

    reset_rescue_gratitude_registry()
    import src.data.rescue_gratitude_loader as gratitude_mod

    gratitude_mod._rescue_gratitude_registry = gratitude

    reset_depth_scaling_cache()
    reset_global_tuning_cache()
    reset_npc_prefix_registry_cache()

    issue_tuple = tuple(all_issues)
    if report and issue_tuple:
        report_mod_data_errors(issue_tuple)
    return issue_tuple
