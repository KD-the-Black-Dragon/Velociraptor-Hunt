"""Parse / load tests for data/global_tuning.json (fixture numbers only)."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from src.data.global_tuning_loader import (
    GlobalTuningLoadError,
    default_global_tuning,
    parse_global_tuning,
    reset_global_tuning_cache,
)


def _stock_like() -> dict:
    return {
        "schema_version": 1,
        "player": {
            "max_hp": 30,
            "accuracy": 1.5,
            "evade": 0,
            "ac": 1,
            "min_damage": 1,
            "max_damage": 2,
        },
        "regen": {
            "hp": 1,
            "every_n_player_turns": 8,
            "evil_every_n_player_turns": 12,
        },
        "vore": {
            "hp_threshold": 0.5,
            "hit_min": 0.25,
            "hit_max": 1.0,
            "escape_base": 0.15,
            "escape_per_fail": 0.05,
            "struggle_damage": 2,
        },
        "loot": {
            "max_floor_item_placements": 5,
            "min_floor_potions": 1,
        },
    }


def test_parse_stock_like_fixture() -> None:
    config = parse_global_tuning(_stock_like())
    assert config.player.max_hp == 30
    assert config.player.accuracy == 1.5
    assert config.regen.every_n_player_turns == 8
    assert config.vore.struggle_damage == 2
    assert config.loot.max_floor_item_placements == 5


def test_reject_bad_schema() -> None:
    raw = _stock_like()
    raw["schema_version"] = 99
    with pytest.raises(GlobalTuningLoadError, match="schema_version"):
        parse_global_tuning(raw)


def test_reject_min_damage_gt_max() -> None:
    raw = _stock_like()
    raw["player"]["min_damage"] = 5
    raw["player"]["max_damage"] = 1
    with pytest.raises(GlobalTuningLoadError, match="min_damage"):
        parse_global_tuning(raw)


def test_reject_unknown_top_level() -> None:
    raw = _stock_like()
    raw["extra"] = 1
    with pytest.raises(GlobalTuningLoadError, match="unknown top-level"):
        parse_global_tuning(raw)


def test_reject_hp_threshold_out_of_range() -> None:
    raw = _stock_like()
    raw["vore"]["hp_threshold"] = 0.0
    with pytest.raises(GlobalTuningLoadError, match="hp_threshold"):
        parse_global_tuning(raw)


def test_default_stock_file_loads() -> None:
    reset_global_tuning_cache()
    config = default_global_tuning()
    assert config.schema_version == 1
    assert config.player.max_hp >= 1
    reset_global_tuning_cache()


def test_constants_aliases_match_default() -> None:
    reset_global_tuning_cache()
    from src import constants
    from src.data.global_tuning_loader import default_global_tuning as load

    tuning = load()
    assert constants.PLAYER_MAX_HP == tuning.player.max_hp
    assert constants.PLAYER_ACCURACY == tuning.player.accuracy
    assert constants.NATURAL_REGEN_EVERY_N_PLAYER_TURNS == tuning.regen.every_n_player_turns
    assert constants.VORE_STRUGGLE_DAMAGE == tuning.vore.struggle_damage
    assert constants.MAX_FLOOR_ITEM_PLACEMENTS == tuning.loot.max_floor_item_placements
    reset_global_tuning_cache()


def test_mod_whole_file_replace(tmp_path: Path) -> None:
    from src.mods.pipeline import load_global_tuning_layered

    core = tmp_path / "core"
    core.mkdir()
    core_file = core / "global_tuning.json"
    core_raw = _stock_like()
    import json

    core_file.write_text(json.dumps(core_raw), encoding="utf-8")

    mods = tmp_path / "mods"
    mod = mods / "harder_player"
    mod.mkdir(parents=True)
    (mod / "mod.state").write_text("E 1\n", encoding="utf-8")
    overlay = copy.deepcopy(core_raw)
    overlay["player"]["max_hp"] = 99
    (mod / "global_tuning.json").write_text(json.dumps(overlay), encoding="utf-8")

    config, issues = load_global_tuning_layered(
        core_path=core_file,
        mods_root=mods,
        report=False,
    )
    assert not issues
    assert config.player.max_hp == 99
