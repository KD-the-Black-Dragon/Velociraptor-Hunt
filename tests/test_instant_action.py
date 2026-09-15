"""Instant action (Ctrl+B): kind pick + match card id + solo practice match."""

from __future__ import annotations

from pathlib import Path

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.app import App, AppPhase
from src.instant_action import (
    InstantActionResult,
    InstantActionState,
    InstantStep,
    cards_for_kind,
    filter_cards,
    handle_instant_action_event,
    resolve_card_id,
    start_instant_match,
)
from src.match_session import MatchEndKind, MatchPhase
from src.menu import is_ctrl_b
from src.save.coordinator import SaveCoordinator
from src.save.store import SaveStore
from src.settings_store import SettingsStore


def _key(sym: KeySym, *, mod: int = 0) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def _onboarded_settings(tmp_path: Path) -> SettingsStore:
    path = tmp_path / "settings.json"
    settings = SettingsStore(
        tutorial_prompt_answered=True,
        vore_prefs_onboarding_complete=True,
        path=path,
    )
    settings.save(path)
    return SettingsStore.load(path)


def _app(tmp_path: Path) -> App:
    return App(
        settings=_onboarded_settings(tmp_path),
        save_coordinator=SaveCoordinator(store=SaveStore(tmp_path / "save")),
    )


def test_is_ctrl_b() -> None:
    assert is_ctrl_b(_key(KeySym.B, mod=int(Modifier.CTRL)))
    assert not is_ctrl_b(_key(KeySym.B))


def test_cards_for_kind_filters() -> None:
    red = cards_for_kind("red")
    green = cards_for_kind("green")
    # Solo-only list: multi packs like r1_wolves excluded
    assert not any(c.card_id == "r1_wolves" for c in red)
    assert any(c.card_id == "d1_wolf" for c in red)
    assert any(c.card_id == "r1_green_spar" for c in green)
    assert not any(c.card_id == "r1_wolves" for c in green)


def test_filter_cards_by_buffer() -> None:
    all_red = filter_cards("red", "")
    wolves = filter_cards("red", "wol")
    assert len(wolves) <= len(all_red)
    assert any(c.card_id == "d1_wolf" for c in wolves)


def test_resolve_card_id() -> None:
    card, err = resolve_card_id("red", "d1_wolf")
    assert err == ""
    assert card is not None
    assert card.kind == "red"
    assert card.max_allies == 0
    assert card.enemies
    _, err2 = resolve_card_id("red", "r1_green_spar")
    assert err2
    _, err3 = resolve_card_id("red", "not_a_card")
    assert err3
    _, err4 = resolve_card_id("red", "r1_wolves")
    assert err4  # multi-opponent not allowed in solo instant action


def test_kind_then_card_flow() -> None:
    st = InstantActionState()
    assert handle_instant_action_event(st, _key(KeySym.N1)) is InstantActionResult.NONE
    assert st.kind == "green"
    assert st.step is InstantStep.CARD
    assert handle_instant_action_event(st, _key(KeySym.ESCAPE)) is InstantActionResult.BACK_TO_KIND
    assert st.step is InstantStep.KIND
    handle_instant_action_event(st, _key(KeySym.N2))
    st.buffer = "d1_wolf"
    r = handle_instant_action_event(st, _key(KeySym.RETURN))
    assert r is InstantActionResult.START_MATCH
    assert st.selected_card is not None
    assert st.selected_card.card_id == "d1_wolf"


def test_start_instant_match_solo() -> None:
    card, err = resolve_card_id("red", "d1_wolf")
    assert not err and card is not None
    session = start_instant_match(card, difficulty_id="normal", seed=42)
    assert session.instant_action
    assert session.card.max_allies == 0
    assert not session.living_allies()
    assert len(session.living_enemies()) == 1
    assert session.career.player_name == "Sparrer"


def test_instant_win_recap_menu_footer() -> None:
    card, _ = resolve_card_id("green", "r1_green_spar")
    assert card is not None
    session = start_instant_match(card, difficulty_id="normal", seed=1)
    # Defeat all enemies
    for e in list(session.living_enemies()):
        from src.components import Fighter

        e.components[Fighter].hp = 0
    session._finish_win()
    assert session.phase is MatchPhase.RECAP
    assert session.end_kind is MatchEndKind.WIN
    assert any("main menu" in line.lower() for line in session.recap_lines)
    assert session.career.round_index == 1  # not advanced


def test_app_ctrl_b_opens_instant(tmp_path: Path) -> None:
    app = _app(tmp_path)
    assert app.phase is AppPhase.MENU
    app.phase = AppPhase.INSTANT_ACTION
    app.instant_action.reset()
    assert app.phase is AppPhase.INSTANT_ACTION
    assert app.instant_action.step is InstantStep.KIND


def test_app_instant_start_match(tmp_path: Path) -> None:
    app = _app(tmp_path)
    app.phase = AppPhase.INSTANT_ACTION
    app.instant_action.reset()
    app.handle_event(_key(KeySym.N2), console=None)
    app.instant_action.buffer = "d1_wolf"
    app.handle_event(_key(KeySym.RETURN), console=None)
    assert app.phase is AppPhase.MATCH
    assert app.match_session is not None
    assert app.match_session.instant_action
    assert len(app.match_session.living_enemies()) == 1
    # Finish win → menu
    for e in list(app.match_session.living_enemies()):
        from src.components import Fighter

        e.components[Fighter].hp = 0
    app.match_session._finish_win()
    # Simulate recap dismiss
    assert app.match_session.handle_event(_key(KeySym.RETURN))
    app._finish_match_to_hub()
    assert app.phase is AppPhase.MENU
    assert app.match_session is None
