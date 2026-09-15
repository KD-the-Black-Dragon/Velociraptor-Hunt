"""PR1: ally ranged damage JSON + difficulty good/evil_ranged_shots knobs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.data.depth_scaling_loader import (
    DepthScalingLoadError,
    default_depth_scaling_config,
    parse_depth_scaling_config,
    reset_depth_scaling_cache,
)
from src.data.entity_loader import load_entity_registry, reset_entity_registry_cache

ROOT = Path(__file__).resolve().parents[1]


def test_stock_good_ally_ranged_damage_halved() -> None:
    reset_entity_registry_cache()
    registry = load_entity_registry()
    ram = registry.by_id()["ram_crossbow"]
    sheep = registry.by_id()["sheep_cleric"]
    assert ram.ranged_min_damage == 4
    assert ram.ranged_max_damage == 5
    assert sheep.ranged_min_damage == 5
    assert sheep.ranged_max_damage == 6


def test_stock_depth_scaling_ranged_shots() -> None:
    reset_depth_scaling_cache()
    cfg = default_depth_scaling_config()
    for did in ("easier", "normal", "hard"):
        profile = cfg.profile_for(did)
        assert profile.good_ranged_shots == 2
        assert profile.evil_ranged_shots == 2
    nightmare = cfg.profile_for("nightmare")
    assert nightmare.good_ranged_shots == 2
    assert nightmare.evil_ranged_shots == 3


def test_depth_scaling_omitted_ranged_shots_defaults() -> None:
    raw = {
        "schema_version": 1,
        "default_difficulty_id": "normal",
        "difficulties": {
            "normal": {
                "display_name": "Normal",
                "apply_to_alignments": ["evil"],
                "stats": {},
            }
        },
    }
    cfg = parse_depth_scaling_config(raw)
    profile = cfg.profile_for("normal")
    assert profile.good_ranged_shots == 2
    assert profile.evil_ranged_shots == 2


@pytest.mark.parametrize("field", ["good_ranged_shots", "evil_ranged_shots"])
def test_depth_scaling_rejects_ranged_shots_below_one(field: str) -> None:
    raw = {
        "schema_version": 1,
        "default_difficulty_id": "normal",
        "difficulties": {
            "normal": {
                "display_name": "Normal",
                "apply_to_alignments": ["evil"],
                "stats": {},
                field: 0,
            }
        },
    }
    with pytest.raises(DepthScalingLoadError) as exc:
        parse_depth_scaling_config(raw)
    assert field in str(exc.value)


def test_stock_json_files_contain_ranged_shot_keys() -> None:
    """Sanity: authored keys exist in the on-disk stock file."""
    data = json.loads((ROOT / "data" / "depth_scaling.json").read_text(encoding="utf-8"))
    for did, profile in data["difficulties"].items():
        assert "good_ranged_shots" in profile, did
        assert "evil_ranged_shots" in profile, did
