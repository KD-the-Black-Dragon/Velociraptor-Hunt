"""PR2: layered entities.json load (core then mods)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.components import MobilityType
from src.data.entity_loader import load_entity_registry, reset_entity_registry_cache
from src.mods.errors import format_mod_error_display, format_mod_load_issues
from src.mods.pipeline import load_entities_layered
from src.mods.reload import reload_game_data_caches
from src.mods.state import write_mod_state


def _minimal_entity(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "test_creature",
        "display_name": "test creature",
        "glyph": "x",
        "fg": [100, 100, 100],
        "alignment": "neutral",
        "mobility": "ground",
        "max_hp": 10,
        "evade": 1,
        "ac": 1,
        "accuracy": 1.0,
        "min_damage": 1,
        "max_damage": 2,
        "abilities": [],
        "spawn": {"weight": 1, "min_depth": 1, "max_depth": 10, "terrain": "land"},
    }
    base.update(overrides)
    return base


def _write_entities(path: Path, entities: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "entities": entities}
    path.write_text(json.dumps(payload), encoding="utf-8")


def _mod_with_entities(
    mods_root: Path,
    name: str,
    entities: list[dict[str, object]],
    *,
    order: int,
    enabled: bool = True,
) -> Path:
    folder = mods_root / name
    folder.mkdir(parents=True, exist_ok=True)
    write_mod_state(folder, enabled=enabled, order=order)
    _write_entities(folder / "entities.json", entities)
    return folder


def test_core_only_when_no_mods(tmp_path: Path) -> None:
    core = tmp_path / "core_entities.json"
    _write_entities(core, [_minimal_entity(id="alpha", display_name="Alpha")])
    mods_root = tmp_path / "mods"
    mods_root.mkdir()

    reg, issues = load_entities_layered(
        core_path=core, mods_root=mods_root, report=False
    )
    assert issues == ()
    assert list(reg.by_id()) == ["alpha"]
    assert reg.get("alpha").display_name == "Alpha"


def test_mod_adds_new_entity(tmp_path: Path) -> None:
    core = tmp_path / "core_entities.json"
    _write_entities(core, [_minimal_entity(id="alpha")])
    mods_root = tmp_path / "mods"
    _mod_with_entities(
        mods_root,
        "NewStuff",
        [_minimal_entity(id="dragon", display_name="Cool Dragon", glyph="D")],
        order=1,
    )

    reg, issues = load_entities_layered(
        core_path=core, mods_root=mods_root, report=False
    )
    assert issues == ()
    assert "dragon" in reg.by_id()
    assert reg.get("dragon").display_name == "Cool Dragon"
    assert "alpha" in reg.by_id()


def test_mod_overrides_core_id(tmp_path: Path) -> None:
    core = tmp_path / "core_entities.json"
    _write_entities(
        core,
        [_minimal_entity(id="wolf", display_name="Wolf", max_hp=20)],
    )
    mods_root = tmp_path / "mods"
    _mod_with_entities(
        mods_root,
        "HardWolves",
        [_minimal_entity(id="wolf", display_name="Dire Wolf", max_hp=99, glyph="W")],
        order=1,
    )

    reg, issues = load_entities_layered(
        core_path=core, mods_root=mods_root, report=False
    )
    assert issues == ()
    wolf = reg.get("wolf")
    assert wolf.display_name == "Dire Wolf"
    assert wolf.max_hp == 99
    assert wolf.glyph == "W"


def test_later_mod_wins_on_same_id(tmp_path: Path) -> None:
    core = tmp_path / "core_entities.json"
    _write_entities(core, [_minimal_entity(id="wolf", display_name="Core")])
    mods_root = tmp_path / "mods"
    _mod_with_entities(
        mods_root,
        "First",
        [_minimal_entity(id="wolf", display_name="First")],
        order=1,
    )
    _mod_with_entities(
        mods_root,
        "Second",
        [_minimal_entity(id="wolf", display_name="Second")],
        order=2,
    )

    reg, issues = load_entities_layered(
        core_path=core, mods_root=mods_root, report=False
    )
    assert issues == ()
    assert reg.get("wolf").display_name == "Second"


def test_disabled_mod_not_applied(tmp_path: Path) -> None:
    core = tmp_path / "core_entities.json"
    _write_entities(core, [_minimal_entity(id="wolf", display_name="Core")])
    mods_root = tmp_path / "mods"
    _mod_with_entities(
        mods_root,
        "OffMod",
        [_minimal_entity(id="wolf", display_name="ShouldNotAppear")],
        order=1,
        enabled=False,
    )

    reg, issues = load_entities_layered(
        core_path=core, mods_root=mods_root, report=False
    )
    assert issues == ()
    assert reg.get("wolf").display_name == "Core"


def test_bad_mod_json_skipped_with_issue(tmp_path: Path) -> None:
    core = tmp_path / "core_entities.json"
    _write_entities(core, [_minimal_entity(id="alpha")])
    mods_root = tmp_path / "mods"
    folder = mods_root / "Cool_Dragon_Mod"
    folder.mkdir(parents=True)
    write_mod_state(folder, enabled=True, order=1)
    (folder / "entities.json").write_text("{ not json", encoding="utf-8")

    reg, issues = load_entities_layered(
        core_path=core, mods_root=mods_root, report=False
    )
    assert "alpha" in reg.by_id()
    assert len(issues) == 1
    assert issues[0].mod_name == "Cool_Dragon_Mod"
    assert issues[0].filename == "entities.json"
    assert "Invalid JSON" in issues[0].reason

    display = format_mod_error_display(issues)
    assert "Cool_Dragon_Mod" in display
    assert "entities.json" in display
    assert "Mod data error" in display


def test_bad_mod_validation_skipped_keeps_prior_layer(tmp_path: Path) -> None:
    core = tmp_path / "core_entities.json"
    _write_entities(core, [_minimal_entity(id="wolf", display_name="Core")])
    mods_root = tmp_path / "mods"
    # Invalid after deep merge: bad mobility value (not merely missing fields)
    _mod_with_entities(
        mods_root,
        "Broken",
        [{"id": "wolf", "mobility": "banana"}],
        order=1,
    )

    reg, issues = load_entities_layered(
        core_path=core, mods_root=mods_root, report=False
    )
    assert reg.get("wolf").display_name == "Core"
    assert reg.get("wolf").mobility is MobilityType.GROUND
    assert len(issues) == 1
    assert issues[0].mod_name == "Broken"
    assert "entities.json" in issues[0].filename


def test_good_mod_after_bad_mod_still_applies(tmp_path: Path) -> None:
    core = tmp_path / "core_entities.json"
    _write_entities(core, [_minimal_entity(id="a", display_name="A")])
    mods_root = tmp_path / "mods"
    bad = mods_root / "Bad"
    bad.mkdir(parents=True)
    write_mod_state(bad, enabled=True, order=1)
    (bad / "entities.json").write_text("{", encoding="utf-8")
    _mod_with_entities(
        mods_root,
        "Good",
        [_minimal_entity(id="b", display_name="B")],
        order=2,
    )

    reg, issues = load_entities_layered(
        core_path=core, mods_root=mods_root, report=False
    )
    assert len(issues) == 1
    assert issues[0].mod_name == "Bad"
    assert "b" in reg.by_id()


def test_load_entity_registry_layers_with_mods_root(tmp_path: Path) -> None:
    # Use real core file + temp mods that override if wolf exists, or add id
    mods_root = tmp_path / "mods"
    _mod_with_entities(
        mods_root,
        "Extra",
        [_minimal_entity(id="pipeline_only_critter", display_name="Pipeline Critter")],
        order=1,
    )
    reset_entity_registry_cache()
    reg = load_entity_registry(mods_root=mods_root, report_mod_errors=False)
    assert "pipeline_only_critter" in reg.by_id()


def test_explicit_path_does_not_layer_mods(tmp_path: Path) -> None:
    core = tmp_path / "only.json"
    _write_entities(core, [_minimal_entity(id="solo")])
    mods_root = tmp_path / "mods"
    _mod_with_entities(
        mods_root,
        "Ignored",
        [_minimal_entity(id="solo", display_name="Modded")],
        order=1,
    )
    # Explicit path ignores mods entirely
    reg = load_entity_registry(core)
    assert reg.get("solo").display_name == "test creature"


def test_reload_clears_default_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mods_root = tmp_path / "mods"
    mods_root.mkdir()
    monkeypatch.setattr("src.user_data.MODS_DIR", mods_root)
    reset_entity_registry_cache()

    first = load_entity_registry(report_mod_errors=False)
    assert "reload_probe" not in first.by_id()

    _mod_with_entities(
        mods_root,
        "Probe",
        [_minimal_entity(id="reload_probe", display_name="After Reload")],
        order=1,
    )
    # Without reload, cached default would still omit the mod
    still_cached = load_entity_registry(report_mod_errors=False)
    assert "reload_probe" not in still_cached.by_id()

    reload_game_data_caches()
    after = load_entity_registry(report_mod_errors=False)
    assert after.get("reload_probe").display_name == "After Reload"


def test_format_mod_load_issues_lists_mod_and_file() -> None:
    from src.mods.errors import ModLoadIssue

    text = format_mod_load_issues(
        [
            ModLoadIssue("Cool_Dragon_Mod", "entities.json", "missing max_hp"),
        ]
    )
    assert "Cool_Dragon_Mod" in text
    assert "entities.json" in text
    assert "missing max_hp" in text


def _vore_block() -> dict[str, object]:
    return {
        "OV": [{"attempt": ["old ov attempt"], "success": ["old ov success"]}],
        "CV": [{"attempt": ["old cv attempt"], "success": ["old cv success"]}],
        "AV": [{"attempt": ["old av attempt"], "success": ["old av success"]}],
    }


def test_spawn_weight_zero_patch_inherits_other_fields(tmp_path: Path) -> None:
    core = tmp_path / "core_entities.json"
    _write_entities(
        core,
        [
            _minimal_entity(
                id="wolf",
                display_name="Wolf",
                max_hp=20,
                abilities=["Wander"],
                spawn={"weight": 3, "min_depth": 3, "max_depth": 10, "terrain": "land"},
            )
        ],
    )
    mods_root = tmp_path / "mods"
    _mod_with_entities(
        mods_root,
        "NoWolves",
        [{"id": "wolf", "spawn": {"weight": 0}}],
        order=1,
    )

    reg, issues = load_entities_layered(
        core_path=core, mods_root=mods_root, report=False
    )
    assert issues == ()
    wolf = reg.get("wolf")
    assert wolf.spawn.weight == 0
    assert wolf.spawn.min_depth == 3
    assert wolf.spawn.max_depth == 10
    assert wolf.spawn.terrain == "land"
    assert wolf.display_name == "Wolf"
    assert wolf.max_hp == 20
    assert wolf.abilities == ("Wander",)


def test_vore_narratives_ov_array_replace_keeps_cv_av(tmp_path: Path) -> None:
    core = tmp_path / "core_entities.json"
    _write_entities(
        core,
        [_minimal_entity(id="wolf", vore_narratives=_vore_block())],
    )
    mods_root = tmp_path / "mods"
    _mod_with_entities(
        mods_root,
        "RewriteOV",
        [
            {
                "id": "wolf",
                "vore_narratives": {
                    "OV": [
                        {
                            "attempt": ["new ov attempt"],
                            "success": ["new ov success"],
                        }
                    ]
                },
            }
        ],
        order=1,
    )

    reg, issues = load_entities_layered(
        core_path=core, mods_root=mods_root, report=False
    )
    assert issues == ()
    narratives = reg.get("wolf").vore_narratives
    assert narratives is not None
    assert narratives["OV"][0].attempt == ("new ov attempt",)
    assert narratives["OV"][0].success == ("new ov success",)
    assert narratives["CV"][0].attempt == ("old cv attempt",)
    assert narratives["AV"][0].attempt == ("old av attempt",)


def test_stacked_mods_deep_merge_fields(tmp_path: Path) -> None:
    core = tmp_path / "core_entities.json"
    _write_entities(
        core,
        [
            _minimal_entity(
                id="wolf",
                display_name="Core",
                spawn={"weight": 3, "min_depth": 3, "max_depth": 10, "terrain": "land"},
            )
        ],
    )
    mods_root = tmp_path / "mods"
    _mod_with_entities(
        mods_root,
        "First",
        [{"id": "wolf", "display_name": "Dire Wolf", "spawn": {"weight": 5}}],
        order=1,
    )
    _mod_with_entities(
        mods_root,
        "Second",
        [{"id": "wolf", "spawn": {"weight": 0}}],
        order=2,
    )

    reg, issues = load_entities_layered(
        core_path=core, mods_root=mods_root, report=False
    )
    assert issues == ()
    wolf = reg.get("wolf")
    assert wolf.display_name == "Dire Wolf"
    assert wolf.spawn.weight == 0
    assert wolf.spawn.min_depth == 3


def test_incomplete_new_id_skipped_with_issue(tmp_path: Path) -> None:
    core = tmp_path / "core_entities.json"
    _write_entities(core, [_minimal_entity(id="alpha")])
    mods_root = tmp_path / "mods"
    _mod_with_entities(
        mods_root,
        "StubDragon",
        [{"id": "cool_dragon", "display_name": "Cool Dragon"}],
        order=1,
    )

    reg, issues = load_entities_layered(
        core_path=core, mods_root=mods_root, report=False
    )
    assert "cool_dragon" not in reg.by_id()
    assert "alpha" in reg.by_id()
    assert len(issues) == 1
    assert issues[0].mod_name == "StubDragon"


def test_abilities_empty_array_clears_abilities(tmp_path: Path) -> None:
    core = tmp_path / "core_entities.json"
    _write_entities(
        core,
        [_minimal_entity(id="wolf", abilities=["Wander"])],
    )
    mods_root = tmp_path / "mods"
    _mod_with_entities(
        mods_root,
        "NoPath",
        [{"id": "wolf", "abilities": []}],
        order=1,
    )

    reg, issues = load_entities_layered(
        core_path=core, mods_root=mods_root, report=False
    )
    assert issues == ()
    assert reg.get("wolf").abilities == ()


def test_display_name_only_patch_inherits_rest(tmp_path: Path) -> None:
    core = tmp_path / "core_entities.json"
    _write_entities(
        core,
        [_minimal_entity(id="wolf", display_name="Core", max_hp=20)],
    )
    mods_root = tmp_path / "mods"
    _mod_with_entities(
        mods_root,
        "Rename",
        [{"id": "wolf", "display_name": "Nope"}],
        order=1,
    )

    reg, issues = load_entities_layered(
        core_path=core, mods_root=mods_root, report=False
    )
    assert issues == ()
    wolf = reg.get("wolf")
    assert wolf.display_name == "Nope"
    assert wolf.max_hp == 20
    assert wolf.glyph == "x"
