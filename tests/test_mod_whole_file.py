"""PR5: whole-file mod replace — dungeon_spawn, rescue_gratitude, ui_layout."""

from __future__ import annotations

import json
from pathlib import Path

from src.constants import DATA_DIR
from src.data.dungeon_spawn_loader import load_dungeon_spawn_config
from src.data.rescue_gratitude_loader import load_rescue_gratitude_registry
from src.mods.pipeline import (
    load_dungeon_spawn_layered,
    load_rescue_gratitude_layered,
    load_ui_layout_document_layered,
    load_ui_layout_layered,
)
from src.mods.state import write_mod_state
from src.ui.layout import list_ui_preset_ids, load_ui_layout


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _mod(root: Path, name: str, *, order: int = 1) -> Path:
    folder = root / name
    folder.mkdir(parents=True, exist_ok=True)
    write_mod_state(folder, enabled=True, order=order)
    return folder


def _minimal_spawn(**overrides: object) -> dict:
    base: dict = {
        "schema_version": 1,
        "defaults": {
            "density_pct": 0.01,
            "density_variance": 0.1,
            "min_npcs": 1,
            "max_npcs": 5,
        },
        "depth_bands": [],
    }
    base.update(overrides)
    return base


def test_dungeon_spawn_whole_file_replace(tmp_path: Path) -> None:
    core = tmp_path / "dungeon_spawn.json"
    _write_json(core, _minimal_spawn())
    mods = tmp_path / "mods"
    folder = _mod(mods, "Dense")
    _write_json(
        folder / "dungeon_spawn.json",
        _minimal_spawn(
            defaults={
                "density_pct": 0.5,
                "density_variance": 0.0,
                "min_npcs": 20,
                "max_npcs": 40,
            }
        ),
    )
    config, issues = load_dungeon_spawn_layered(
        core_path=core, mods_root=mods, report=False
    )
    assert issues == ()
    assert config.defaults.density_pct == 0.5
    assert config.defaults.min_npcs == 20


def test_dungeon_spawn_later_mod_wins(tmp_path: Path) -> None:
    core = tmp_path / "dungeon_spawn.json"
    _write_json(core, _minimal_spawn())
    mods = tmp_path / "mods"
    a = _mod(mods, "A", order=1)
    b = _mod(mods, "B", order=2)
    _write_json(
        a / "dungeon_spawn.json",
        _minimal_spawn(
            defaults={
                "density_pct": 0.2,
                "density_variance": 0.0,
                "min_npcs": 2,
                "max_npcs": 4,
            }
        ),
    )
    _write_json(
        b / "dungeon_spawn.json",
        _minimal_spawn(
            defaults={
                "density_pct": 0.9,
                "density_variance": 0.0,
                "min_npcs": 9,
                "max_npcs": 9,
            }
        ),
    )
    config, issues = load_dungeon_spawn_layered(
        core_path=core, mods_root=mods, report=False
    )
    assert issues == ()
    assert config.defaults.density_pct == 0.9


def test_bad_dungeon_spawn_skipped(tmp_path: Path) -> None:
    core = tmp_path / "dungeon_spawn.json"
    _write_json(core, _minimal_spawn())
    mods = tmp_path / "mods"
    folder = _mod(mods, "BrokenSpawn")
    (folder / "dungeon_spawn.json").write_text("{ no", encoding="utf-8")
    config, issues = load_dungeon_spawn_layered(
        core_path=core, mods_root=mods, report=False
    )
    assert len(issues) == 1
    assert issues[0].filename == "dungeon_spawn.json"
    assert issues[0].mod_name == "BrokenSpawn"
    assert config.defaults.density_pct == 0.01


def test_rescue_gratitude_whole_file_replace(tmp_path: Path) -> None:
    core = tmp_path / "rescue_gratitude.json"
    _write_json(core, {"schema_version": 1, "lines": ["core thanks"]})
    mods = tmp_path / "mods"
    folder = _mod(mods, "Thanks")
    _write_json(
        folder / "rescue_gratitude.json",
        {"schema_version": 1, "lines": ["mod thanks {name}"]},
    )
    reg, issues = load_rescue_gratitude_layered(
        core_path=core, mods_root=mods, report=False
    )
    assert issues == ()
    assert reg.lines == ("mod thanks {name}",)


def test_bad_rescue_gratitude_skipped(tmp_path: Path) -> None:
    core = tmp_path / "rescue_gratitude.json"
    _write_json(core, {"schema_version": 1, "lines": ["core line"]})
    mods = tmp_path / "mods"
    folder = _mod(mods, "BadThanks")
    _write_json(folder / "rescue_gratitude.json", {"schema_version": 1, "lines": []})
    reg, issues = load_rescue_gratitude_layered(
        core_path=core, mods_root=mods, report=False
    )
    assert len(issues) == 1
    assert reg.lines == ("core line",)


def test_ui_layout_whole_file_replace_default_preset(tmp_path: Path) -> None:
    stock = json.loads((DATA_DIR / "ui_layout.json").read_text(encoding="utf-8"))
    core = tmp_path / "ui_layout.json"
    _write_json(core, stock)
    assert stock["default_preset"] == "standard"

    modded = json.loads(json.dumps(stock))
    modded["default_preset"] = "wide_sidebar"
    mods = tmp_path / "mods"
    folder = _mod(mods, "WideDefault")
    _write_json(folder / "ui_layout.json", modded)

    doc, issues = load_ui_layout_document_layered(
        core_path=core, mods_root=mods, report=False
    )
    assert issues == ()
    assert doc["default_preset"] == "wide_sidebar"

    layout, _ = load_ui_layout_layered(
        core_path=core, mods_root=mods, report=False
    )
    assert layout.preset_id == "wide_sidebar"


def test_ui_layout_list_presets_uses_mods(tmp_path: Path, monkeypatch) -> None:
    stock = json.loads((DATA_DIR / "ui_layout.json").read_text(encoding="utf-8"))
    modded = json.loads(json.dumps(stock))
    # Rename is not allowed freely; keep stock presets but ensure list still works
    mods = tmp_path / "mods"
    folder = _mod(mods, "LayoutMod")
    _write_json(folder / "ui_layout.json", modded)
    monkeypatch.setattr("src.user_data.MODS_DIR", mods)

    ids = list_ui_preset_ids()
    assert "standard" in ids
    assert "wide_sidebar" in ids


def test_explicit_paths_ignore_mods(tmp_path: Path) -> None:
    core_spawn = tmp_path / "dungeon_spawn.json"
    _write_json(core_spawn, _minimal_spawn())
    mods = tmp_path / "mods"
    folder = _mod(mods, "Ignored")
    _write_json(
        folder / "dungeon_spawn.json",
        _minimal_spawn(
            defaults={
                "density_pct": 0.99,
                "density_variance": 0.0,
                "min_npcs": 99,
                "max_npcs": 99,
            }
        ),
    )
    config = load_dungeon_spawn_config(core_spawn)
    assert config.defaults.density_pct == 0.01

    core_g = tmp_path / "rescue_gratitude.json"
    _write_json(core_g, {"schema_version": 1, "lines": ["solo"]})
    _write_json(folder / "rescue_gratitude.json", {"schema_version": 1, "lines": ["mod"]})
    reg = load_rescue_gratitude_registry(core_g)
    assert reg.lines == ("solo",)

    stock = json.loads((DATA_DIR / "ui_layout.json").read_text(encoding="utf-8"))
    layout_path = tmp_path / "ui_layout.json"
    _write_json(layout_path, stock)
    layout = load_ui_layout(path=layout_path)
    assert layout.preset_id == stock["default_preset"]
