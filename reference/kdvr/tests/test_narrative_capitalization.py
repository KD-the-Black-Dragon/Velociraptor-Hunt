"""PR8: sentence capitalization on predator/prey template formatters."""

from __future__ import annotations

import random

from src.components import Alignment
from src.digestion_content import DIGESTION_COMPLETE_POOL
from src.engine import GameEngine
from src.systems.ai import spawn_test_npc
from src.systems.digestion import (
    _format_digestion_line,
    _format_player_digestion_phase,
    player_digestion_modal_phases,
)
from src.systems.vore import format_npc_vore_line
from src.text import enforce_sentence_capitalization

from tests.map_test_helpers import first_wolf


def test_enforce_sentence_capitalization_start() -> None:
    assert enforce_sentence_capitalization("the wolf") == "The wolf"


def test_enforce_sentence_capitalization_after_period() -> None:
    assert (
        enforce_sentence_capitalization("gone. the rabbit")
        == "gone. The rabbit"
    )


def test_enforce_sentence_capitalization_dash_not_boundary() -> None:
    assert enforce_sentence_capitalization("triumph - you") == "triumph - you"


def test_enforce_sentence_capitalization_after_question_and_exclamation() -> None:
    assert (
        enforce_sentence_capitalization("wait? the rabbit")
        == "wait? The rabbit"
    )
    assert (
        enforce_sentence_capitalization("gone! the rabbit")
        == "gone! The rabbit"
    )


def test_format_npc_vore_line_capitalizes_predator_at_start() -> None:
    engine = GameEngine()
    wolf = first_wolf(engine)
    knight = spawn_test_npc(
        engine.world,
        x=2,
        y=2,
        species="knight",
        alignment=Alignment.GOOD,
    )
    line = format_npc_vore_line(
        "{predator} swallows {prey} whole!",
        wolf,
        knight,
    )
    assert line.startswith("The wolf")


def test_format_digestion_line_capitalizes_after_dash_not_period() -> None:
    engine = GameEngine()
    wolf = first_wolf(engine)
    knight = spawn_test_npc(
        engine.world,
        x=2,
        y=2,
        species="knight",
        alignment=Alignment.GOOD,
    )
    template = DIGESTION_COMPLETE_POOL["OV"][0]
    line = _format_digestion_line(template, wolf, knight)
    assert line.startswith("The wolf burps triumphantly - the knight")


def test_player_digestion_modal_capitalizes_predator_at_start() -> None:
    engine = GameEngine()
    wolf = first_wolf(engine)
    line = _format_player_digestion_phase(
        "{predator} howls in triumph as it digests a great prize - you.",
        wolf,
    )
    assert line.startswith("The wolf")
    assert line.endswith(" - you.")


def test_player_digestion_modal_capitalizes_after_sentence_end() -> None:
    engine = GameEngine()
    wolf = first_wolf(engine)
    line = _format_player_digestion_phase(
        "You are lost. {predator} finishes the meal.",
        wolf,
    )
    assert line == "You are lost. The wolf finishes the meal."


def test_player_digestion_modal_phases_use_capitalization() -> None:
    """Capitalization of {predator} substitution — not stock phase wording."""
    engine = GameEngine()
    wolf = first_wolf(engine)
    phases = player_digestion_modal_phases(wolf, "OV", random.Random(0))
    assert phases
    assert all(phase[:1].isupper() for phase in phases if phase)