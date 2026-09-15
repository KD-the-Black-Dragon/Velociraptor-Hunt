"""Unit tests for JSON deep-merge helper (pinned values; no live data/)."""

from __future__ import annotations

from src.mods.json_merge import deep_merge_json


def test_deep_merge_nested_object_keeps_sibling_keys() -> None:
    base = {"id": "wolf", "spawn": {"weight": 3, "min_depth": 3, "max_depth": 10}}
    overlay = {"spawn": {"weight": 0}}
    merged = deep_merge_json(base, overlay)
    assert merged == {
        "id": "wolf",
        "spawn": {"weight": 0, "min_depth": 3, "max_depth": 10},
    }
    # Inputs not mutated
    assert base["spawn"]["weight"] == 3
    assert overlay == {"spawn": {"weight": 0}}


def test_deep_merge_arrays_replace() -> None:
    base = {"abilities": ["Pathfind"], "fg": [1, 2, 3]}
    overlay = {"abilities": [], "fg": [9, 9, 9]}
    merged = deep_merge_json(base, overlay)
    assert merged["abilities"] == []
    assert merged["fg"] == [9, 9, 9]


def test_deep_merge_scalar_and_null_replace() -> None:
    base = {"display_name": "wolf", "examine": "old", "proper_name": "Bob"}
    overlay = {"display_name": "Dire Wolf", "examine": None}
    merged = deep_merge_json(base, overlay)
    assert merged["display_name"] == "Dire Wolf"
    assert merged["examine"] is None
    assert merged["proper_name"] == "Bob"


def test_deep_merge_type_mismatch_replaces() -> None:
    base = {"spawn": {"weight": 1}, "abilities": ["A"]}
    overlay = {"spawn": 0, "abilities": {"nope": True}}
    merged = deep_merge_json(base, overlay)
    assert merged["spawn"] == 0
    assert merged["abilities"] == {"nope": True}


def test_deep_merge_non_dict_overlay_replaces_entire_value() -> None:
    assert deep_merge_json({"a": 1}, [1, 2, 3]) == [1, 2, 3]
    assert deep_merge_json([1], {"a": 1}) == {"a": 1}


def test_deep_merge_narrative_object_replaces_one_array_key() -> None:
    base = {
        "vore_narratives": {
            "OV": [{"attempt": ["old o"], "success": ["old os"]}],
            "CV": [{"attempt": ["old c"], "success": ["old cs"]}],
        }
    }
    overlay = {
        "vore_narratives": {
            "OV": [{"attempt": ["new o"], "success": ["new os"]}],
        }
    }
    merged = deep_merge_json(base, overlay)
    assert merged["vore_narratives"]["OV"][0]["attempt"] == ["new o"]
    assert merged["vore_narratives"]["CV"][0]["attempt"] == ["old c"]
