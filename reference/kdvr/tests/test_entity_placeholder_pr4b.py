"""PR4b: optional entity placeholder flag (content marker only)."""

from __future__ import annotations

from src.components import Alignment
from src.data.entity_loader import EntityLoadError, parse_entity_registry
from src.data.entity_loader import load_entity_registry, reset_entity_registry_cache


def _minimal_entity(**overrides: object) -> dict:
    base: dict = {
        "id": "stub_rat",
        "display_name": "stub rat",
        "glyph": "r",
        "fg": [100, 100, 100],
        "alignment": "evil",
        "mobility": "ground",
        "max_hp": 5,
        "evade": 0,
        "ac": 0,
        "accuracy": 0.5,
        "min_damage": 1,
        "max_damage": 2,
        "spawn": {"weight": 0, "min_depth": 1, "max_depth": 10},
        "examine": "[placeholder] A test stub.",
        "placeholder": True,
        "digestion_damage_per_tick": 2,
        "digest_time": 5,
        "vore_narratives": {
            "OV": [
                {
                    "attempt": ["[placeholder] attempt"],
                    "success": ["[placeholder] success"],
                }
            ]
        },
        "digestion_complete": {"OV": ["[placeholder] done"]},
        "npc_vore_hit": {"OV": ["[placeholder] hit"]},
        "npc_vore_miss": {"OV": ["[placeholder] miss"]},
        "offscreen_vore": {"OV": ["[placeholder] off vore"]},
        "offscreen_digest": {"OV": ["[placeholder] off dig"]},
    }
    base.update(overrides)
    return base


class TestPlaceholderFlag:
    def test_placeholder_true_parses(self) -> None:
        reg = parse_entity_registry(
            {"schema_version": 1, "entities": [_minimal_entity()]}
        )
        entity = reg.get("stub_rat")
        assert entity.placeholder is True
        assert entity.alignment == Alignment.EVIL
        # No unknown-trait noise for the known field
        assert not any("placeholder" in w.lower() for w in reg.warnings)

    def test_placeholder_default_false(self) -> None:
        raw = _minimal_entity()
        del raw["placeholder"]
        reg = parse_entity_registry({"schema_version": 1, "entities": [raw]})
        assert reg.get("stub_rat").placeholder is False

    def test_placeholder_must_be_bool(self) -> None:
        raw = _minimal_entity(placeholder="yes")
        try:
            parse_entity_registry({"schema_version": 1, "entities": [raw]})
            raise AssertionError("expected load error")
        except EntityLoadError as exc:
            assert "placeholder" in str(exc)

    def test_finished_stock_species_not_placeholders(self) -> None:
        """Core finished species stay unmarked; PR5 fillers may set placeholder true."""
        reset_entity_registry_cache()
        reg = load_entity_registry()
        finished = {"bat", "wolf", "knight", "rabbit", "shark"}
        for entity in reg.entities:
            if entity.id in finished:
                assert entity.placeholder is False
