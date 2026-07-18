"""PR1: macguffin data catalog loader and registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.data.macguffin_loader import (
    MACGUFFINS_PATH,
    MacguffinLoadError,
    load_macguffin_registry,
    parse_macguffin_registry,
)


def _minimal_macguffins_payload(
    *,
    macguffins: list[dict] | None = None,
) -> dict:
    if macguffins is None:
        macguffins = [
            {
                "id": "test_item",
                "display_name": "The Test Item",
                "glyph": "*",
                "fg": [200, 200, 200],
                "examine": "A test macguffin.",
                "min_depth": 1,
                "max_depth": 10,
                "score": 50,
            }
        ]
    return {"schema_version": 1, "macguffins": macguffins}


def test_load_default_macguffins_json_smoke() -> None:
    """Live file must parse; ids/depths/scores are free to retune."""
    registry = load_macguffin_registry(MACGUFFINS_PATH)
    assert registry.schema_version == 1
    assert len(registry.macguffins) >= 1
    for macguffin in registry.macguffins:
        assert macguffin.id
        assert macguffin.min_depth <= macguffin.max_depth


def test_eligible_at_depth_uses_fixture_bands() -> None:
    from tests.macguffin_test_helpers import fixture_macguffin_registry

    registry = fixture_macguffin_registry()
    assert [m.id for m in registry.eligible_at_depth(1)] == ["early_relic"]
    assert {m.id for m in registry.eligible_at_depth(4)} == {"early_relic", "mid_relic"}
    assert {m.id for m in registry.eligible_at_depth(7)} == {
        "mid_relic",
        "late_relic",
    }
    assert [m.id for m in registry.eligible_at_depth(20)] == []


def test_registry_get() -> None:
    from tests.macguffin_test_helpers import fixture_macguffin_registry

    registry = fixture_macguffin_registry()
    late = registry.get("late_relic")
    assert late.score == 30
    assert late.glyph == '"'
    with pytest.raises(KeyError):
        registry.get("missing")


def test_forbidden_wall_glyph_rejected() -> None:
    payload = _minimal_macguffins_payload(
        macguffins=[
            {
                "id": "bad",
                "display_name": "Bad",
                "glyph": "#",
                "fg": [1, 1, 1],
                "examine": "bad",
                "min_depth": 1,
                "max_depth": 5,
                "score": 1,
            }
        ]
    )
    with pytest.raises(MacguffinLoadError, match="reserved"):
        parse_macguffin_registry(payload)


def test_negative_score_rejected() -> None:
    payload = _minimal_macguffins_payload(
        macguffins=[
            {
                "id": "bad",
                "display_name": "Bad",
                "glyph": "!",
                "fg": [1, 1, 1],
                "examine": "bad",
                "min_depth": 1,
                "max_depth": 5,
                "score": -1,
            }
        ]
    )
    with pytest.raises(MacguffinLoadError, match="score"):
        parse_macguffin_registry(payload)


def test_duplicate_id_rejected() -> None:
    entry = _minimal_macguffins_payload()["macguffins"][0]
    payload = _minimal_macguffins_payload(macguffins=[entry, dict(entry)])
    with pytest.raises(MacguffinLoadError, match="duplicate"):
        parse_macguffin_registry(payload)


def test_min_depth_greater_than_max_rejected() -> None:
    payload = _minimal_macguffins_payload(
        macguffins=[
            {
                "id": "bad",
                "display_name": "Bad",
                "glyph": "!",
                "fg": [1, 1, 1],
                "examine": "bad",
                "min_depth": 10,
                "max_depth": 2,
                "score": 0,
            }
        ]
    )
    with pytest.raises(MacguffinLoadError, match="min_depth"):
        parse_macguffin_registry(payload)


def test_load_from_temp_file(tmp_path: Path) -> None:
    path = tmp_path / "macguffins.json"
    path.write_text(json.dumps(_minimal_macguffins_payload()), encoding="utf-8")
    registry = load_macguffin_registry(path)
    assert len(registry.macguffins) == 1
    assert registry.macguffins[0].id == "test_item"