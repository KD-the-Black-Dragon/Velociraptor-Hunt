"""PR 3: vore narratives from data; remove hardcoded wolf fallback."""

from __future__ import annotations

from pathlib import Path

from tcod.ecs import Registry

from src.components import Alignment, DigestionStats, VoreCapable, VoreNarratives
from src.data.alignment_profiles import alignment_profile
from src.data.narrative_index import reset_narrative_index
from src.systems.vore import get_narrative_phases


def test_vore_content_module_removed() -> None:
    assert not Path("src/vore_content.py").exists()


def test_narrative_phases_from_fixture_index() -> None:
    """Index lookup uses entity id + type — not stock phrase content."""
    from src.data.entity_registry import VoreNarrativeVariant
    from src.data.narrative_index import NarrativeIndex

    reset_narrative_index()
    index = NarrativeIndex(
        vore_variants={
            ("fixture_predator", "OV"): (
                VoreNarrativeVariant(
                    attempt=("Fixture jaws open!",),
                    success=("Fixture swallow one.", "Fixture swallow two."),
                ),
            ),
        },
        digestion_complete={},
        digestion_player_modal={},
        npc_vore_hit={},
        npc_vore_miss={},
        offscreen_vore={},
        offscreen_digest={},
        engulfed_flavor={},
    )
    attempt = index.narrative_phases("fixture_predator", "OV", "attempt")
    success = index.narrative_phases("fixture_predator", "OV", "success")
    assert attempt == ("Fixture jaws open!",)
    assert success == ("Fixture swallow one.", "Fixture swallow two.")
    assert index.narrative_phases("missing", "OV", "attempt") == ()


def test_non_vore_species_returns_empty_phases() -> None:
    reset_narrative_index()
    # Unknown / non-vorish ids yield empty phases even if stock files change.
    assert get_narrative_phases("___no_such_species___", "OV", "attempt") == []


def test_evil_alignment_applies_vore_without_ability_flags() -> None:
    from src.systems.ai import spawn_test_npc

    world = Registry()
    wolf = spawn_test_npc(
        world,
        x=1,
        y=1,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    wolf.tags.add(VoreCapable)
    wolf.components[VoreNarratives] = VoreNarratives(types=("OV", "CV", "AV"))
    profile = alignment_profile(Alignment.EVIL)
    assert profile.vore_capable
    assert VoreCapable in wolf.tags
    assert wolf.components[VoreNarratives].types == ("OV", "CV", "AV")


def test_good_alignment_never_vore_capable() -> None:
    from src.systems.ai import spawn_test_npc

    world = Registry()
    knight = spawn_test_npc(
        world,
        x=2,
        y=2,
        species="knight",
        alignment=Alignment.GOOD,
    )
    assert VoreCapable not in knight.tags
    assert knight.components.get(VoreNarratives) is None
    assert knight.components.get(DigestionStats) is None
