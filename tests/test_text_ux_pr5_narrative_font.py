"""PR5: proportional narrative modals — vore + examine (digestion model)."""

from __future__ import annotations

import tcod.console

from src.app import App, EXAMINE_DESCRIPTION_FOOTER
from src.engine import GameEngine
from src.systems.digestion import DigestionModalState
from src.systems.vore import VoreModalSegment, VoreModalState
from src.ui.proportional_dialog import DIGESTION_MODAL_FOOTER
from tests.map_test_helpers import isolate_other_ais


def _console_has_text(console: tcod.console.Console, needle: str) -> bool:
    text = "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(console.height)
        for x in range(console.width)
    )
    return needle in text


def _open_vore_line(modal: VoreModalState, line: str) -> None:
    modal.segment = VoreModalSegment.ATTEMPT
    modal.phases = [line]
    modal.phase_index = 0


def test_engine_skips_cp437_vore_when_flag_false() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.vore_modal = VoreModalState()
    _open_vore_line(engine.vore_modal, "UniqueVorePhaseTokenXYZ")
    console = tcod.console.Console(80, 44, order="F")
    assert engine.vore_modal.active
    engine.render(console, draw_vore_modal=False)
    assert not _console_has_text(console, "UniqueVorePhaseTokenXYZ")

    engine.render(console, draw_vore_modal=True)
    assert _console_has_text(console, "UniqueVorePhaseTokenXYZ")


def test_engine_skips_cp437_examine_description_when_flag_false() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.examine_state.showing_description = True
    engine.examine_state.description_text = "UniqueExamineDescTokenXYZ"
    console = tcod.console.Console(80, 44, order="F")
    engine.render(console, draw_examine_description=False)
    assert not _console_has_text(console, "UniqueExamineDescTokenXYZ")

    engine.render(console, draw_examine_description=True)
    assert _console_has_text(console, "UniqueExamineDescTokenXYZ")


def test_app_narrative_payload_priority() -> None:
    app = App()
    app.engine = GameEngine()
    isolate_other_ais(app.engine)
    assert app._narrative_dialog_payload() is None

    app.engine.examine_state.showing_description = True
    app.engine.examine_state.description_text = "look here"
    payload = app._narrative_dialog_payload()
    assert payload is not None
    assert payload[0] == "look here"
    assert payload[1] == EXAMINE_DESCRIPTION_FOOTER

    app.engine.vore_modal = VoreModalState()
    _open_vore_line(app.engine.vore_modal, "vore line")
    payload = app._narrative_dialog_payload()
    assert payload is not None
    assert payload[0] == "vore line"
    assert payload[1] == DIGESTION_MODAL_FOOTER

    app.engine.digestion_modal = DigestionModalState()
    app.engine.digestion_modal.open(app.engine.player, ["digest line"])  # type: ignore[arg-type]
    payload = app._narrative_dialog_payload()
    assert payload is not None
    assert payload[0] == "digest line"
    assert payload[1] == DIGESTION_MODAL_FOOTER


def test_examine_footer_constant() -> None:
    assert "Esc" in EXAMINE_DESCRIPTION_FOOTER


def test_starter_loadout_not_full_pack() -> None:
    """TEMP full-pack debug loadout removed after PR6 sign-off."""
    from src.components import Inventory

    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=99)
    player = engine.player
    assert player is not None
    inv = player.components[Inventory]
    occupied = sum(1 for v in inv.slots.values() if v is not None)
    assert occupied == 3


def test_wrap_log_text_pixels_single_newline_is_tight(log_font_or_skip=None) -> None:
    """Single \\n must not inject a blank row (was causing huge item-detail gaps)."""
    from pathlib import Path

    import pytest

    from src.constants import DATA_DIR
    from src.ui.log_font import LOG_FONT_PATH, load_log_font_state
    from src.ui.proportional_log import wrap_log_text_pixels

    if not Path(LOG_FONT_PATH).is_file() and not (
        DATA_DIR / "fonts" / "SourceSans3-Regular.ttf"
    ).is_file():
        pytest.skip("log TTF not present")
    state = load_log_font_state(tile_px=12, tile_scale=2)
    if not state.enabled or state.font is None:
        pytest.skip("log font failed to load")
    lines = wrap_log_text_pixels(
        "dagger (wielded)\nA short blade.\nDamage: 3-5",
        font=state.font,
        max_width_px=400,
    )
    assert lines == ["dagger (wielded)", "A short blade.", "Damage: 3-5"]
    para = wrap_log_text_pixels(
        "Title\n\nBody after blank",
        font=state.font,
        max_width_px=400,
    )
    assert para == ["Title", "", "Body after blank"]
