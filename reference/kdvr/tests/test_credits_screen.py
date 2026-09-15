"""PR1: credits screen module (static content, render, Esc back)."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.ui.credits_screen import (
    CREDITS_LINES,
    CREDITS_TITLE,
    CreditsAction,
    credits_display_lines,
    handle_credits_event,
    render_credits_screen,
)
from tests.ui_test_helpers import make_console


def _keydown(sym: KeySym, *, mod: Modifier = Modifier.NONE) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def test_credits_display_line_count() -> None:
    assert len(credits_display_lines()) == 21


def test_credits_content_includes_title_and_roles() -> None:
    text = "\n".join(CREDITS_LINES)
    assert CREDITS_TITLE in text
    assert "K.D." in text
    assert "Curator of Voracious Beasts" in text


def test_credits_content_includes_links() -> None:
    text = "\n".join(CREDITS_LINES)
    assert "patreon.com/KD_Dragon" in text
    assert "furaffinity.net/user/kd" in text


def test_credits_content_includes_font_attribution() -> None:
    text = "\n".join(CREDITS_LINES)
    assert "Source Sans 3" in text
    assert "SIL Open Font License 1.1" in text
    assert "CP437 tile font via libtcod" in text


def test_credits_content_includes_library_attribution() -> None:
    text = "\n".join(CREDITS_LINES)
    assert "Python 3.11+ — PSF License Agreement" in text
    assert "libtcod / tcod (>=16.0) — BSD 3-Clause License" in text
    assert "tcod-ecs (>=5.0) — MIT License" in text
    assert "numpy (>=1.26) — BSD License" in text
    assert "Pillow (>=10.0) — HPND License" in text
    assert "attrs — MIT License (transitive dependency)" in text


def test_credits_sections_in_order() -> None:
    lines = [line.text for line in credits_display_lines() if line.text]
    title_index = lines.index(CREDITS_TITLE)
    credits_index = lines.index("Credits")
    links_index = lines.index("Links")
    fonts_index = lines.index("Fonts")
    libraries_index = lines.index("Libraries")
    assert title_index < credits_index < links_index < fonts_index < libraries_index


def test_escape_returns_back() -> None:
    assert handle_credits_event(_keydown(KeySym.ESCAPE)) is CreditsAction.BACK


def test_other_keys_are_no_op() -> None:
    assert handle_credits_event(_keydown(KeySym.RETURN)) is CreditsAction.NONE
    assert handle_credits_event(_keydown(KeySym.UP)) is CreditsAction.NONE


def test_render_credits_screen_draws_title_and_footer() -> None:
    console = make_console()
    render_credits_screen(console)
    overlay_text = "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(console.height - 1)
        for x in range(console.width)
    )
    assert CREDITS_TITLE in overlay_text
    assert "patreon.com/KD_Dragon" in overlay_text

    footer_row = console.height - 1
    footer_text = "".join(
        chr(int(console.rgba[x, footer_row]["ch"]))
        if int(console.rgba[x, footer_row]["ch"])
        else " "
        for x in range(console.width)
    )
    assert "Esc: close" in footer_text