"""PR1 improve-text-ux: narrative placeholders, safe format, menu dialog layout."""

from __future__ import annotations

import tcod.console
import tcod.ecs

from src.components import DisplayName, Position
from src.systems.naming import entity_log_name
from src.systems.vore import format_player_vore_phase
from src.text import format_narrative_template
from src.ui.menu_dialog import (
    MENU_DIALOG_BAND_OFFSET,
    menu_dialog_max_width,
    menu_dialog_start_y,
    wrap_dialog_text,
    wrap_text_words,
)
from src.new_game_confirm import (
    NEW_GAME_OVERWRITE_PROMPT,
    NewGameConfirmState,
    render_new_game_confirm,
)


def test_format_narrative_template_substitutes_known_keys() -> None:
    assert (
        format_narrative_template("{predator} lunges.", predator="the wolf")
        == "the wolf lunges."
    )


def test_format_narrative_template_leaves_unknown_keys_literal() -> None:
    assert (
        format_narrative_template("{predtaor} lunges.", predator="the wolf")
        == "{predtaor} lunges."
    )


def test_format_player_vore_phase_substitutes_predator() -> None:
    world = tcod.ecs.Registry()
    predator = world.new_entity()
    predator.components[DisplayName] = DisplayName(name="wolf")
    predator.components[Position] = Position(1, 1)
    # entity_log_name may add article
    name = entity_log_name(predator)
    line = format_player_vore_phase("{predator} tries to swallow you.", predator)
    assert "{predator}" not in line
    assert name.split()[-1] in line or "wolf" in line.lower()


def test_format_player_vore_phase_unknown_key_stays() -> None:
    world = tcod.ecs.Registry()
    predator = world.new_entity()
    predator.components[DisplayName] = DisplayName(name="wolf")
    line = format_player_vore_phase("{predtaor} howls.", predator)
    assert "{predtaor}" in line


def test_wrap_text_fits_max_width() -> None:
    lines = wrap_text_words(
        "A saved hunt exists and will be abandoned. Proceed? (Y/n)",
        max_width=30,
    )
    assert all(len(line) <= 30 for line in lines)
    assert len(lines) >= 2


def test_menu_dialog_start_y_is_lower_band() -> None:
    # At typical height, preferred mid+6 should be used
    y = menu_dialog_start_y(44, 2)
    assert y == 44 // 2 + MENU_DIALOG_BAND_OFFSET


def test_menu_dialog_start_y_clamps_on_short_console() -> None:
    y = menu_dialog_start_y(10, 5)
    assert y >= 1
    assert y + 5 <= 10


def test_render_new_game_confirm_draws_wrapped_text() -> None:
    console = tcod.console.Console(40, 24, order="F")
    render_new_game_confirm(console, NewGameConfirmState())
    # At least some non-space glyphs from the prompt appear
    text = "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(console.height)
        for x in range(console.width)
    )
    assert "saved" in text.lower() or "Proceed" in text or "overwritten" in text.lower()


def test_new_game_prompt_wraps_for_narrow_console() -> None:
    max_w = menu_dialog_max_width(40)
    lines = wrap_dialog_text(NEW_GAME_OVERWRITE_PROMPT, max_width=max_w)
    assert all(len(line) <= max_w for line in lines)
    assert len(lines) >= 1
