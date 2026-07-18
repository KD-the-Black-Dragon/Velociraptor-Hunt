"""PR1: first-run onboarding (prompt, tutorial, vore prefs)."""

from __future__ import annotations

import json

import tcod.event
from tcod.event import KeySym, Scancode

from src.app import App, AppPhase
from src.options_menu import TUTORIAL_ROW_INDEX, OptionsMenuState
from src.settings_store import SettingsStore
from src.tutorial_prompt import (
    TUTORIAL_DECLINED_NOTICE,
    TUTORIAL_OPTION_NO,
    TUTORIAL_OPTION_YES,
    TutorialPromptAction,
    TutorialPromptState,
    handle_tutorial_prompt_event,
)
from src.ui.onboarding_notice import (
    ONBOARDING_ALL_SET_LINES,
    OnboardingNoticeAction,
    handle_onboarding_notice_event,
)
from src.ui.tutorial_screen import (
    PAGE_COMMANDS,
    PAGE_CONTENT,
    PAGE_REMINDER,
    TutorialAction,
    TutorialScreenState,
    TUTORIAL_REMINDER_TEXT,
    handle_tutorial_event,
    tutorial_page_lines,
)
from src.ui.vore_prefs_onboarding import (
    CONFIRM_ROW_INDEX,
    VorePrefsOnboardingAction,
    VorePrefsOnboardingState,
    handle_vore_prefs_onboarding_event,
)


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def _onboarded_settings(tmp_path) -> SettingsStore:
    path = tmp_path / "settings.json"
    settings = SettingsStore(
        tutorial_prompt_answered=True,
        vore_prefs_onboarding_complete=True,
        path=path,
    )
    settings.save(path)
    return SettingsStore.load(path)


def test_prompt_no_selection_until_arrow() -> None:
    state = TutorialPromptState()
    assert handle_tutorial_prompt_event(state, _key(KeySym.RETURN)) is TutorialPromptAction.NONE
    state.move_down()
    assert handle_tutorial_prompt_event(state, _key(KeySym.RETURN)) is TutorialPromptAction.YES


def test_app_boots_to_tutorial_prompt(tmp_path) -> None:
    app = App(settings=SettingsStore(path=tmp_path / "settings.json"))
    assert app.phase is AppPhase.TUTORIAL_PROMPT
    assert app.tutorial_prompt is not None


def test_app_boots_to_vore_prefs_when_prompt_done(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = SettingsStore(tutorial_prompt_answered=True, path=path)
    settings.save(path)
    app = App(settings=SettingsStore.load(path))
    assert app.phase is AppPhase.VORE_PREFS_ONBOARDING


def test_app_boots_to_menu_when_onboarding_complete(tmp_path) -> None:
    app = App(settings=_onboarded_settings(tmp_path))
    assert app.phase is AppPhase.MENU


def test_no_path_shows_notice_then_vore_prefs(tmp_path) -> None:
    path = tmp_path / "settings.json"
    app = App(settings=SettingsStore(path=path))
    app.tutorial_prompt.move_down()
    app.tutorial_prompt.move_down()
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.ONBOARDING_NOTICE
    assert app.onboarding_notice_lines == (TUTORIAL_DECLINED_NOTICE,)
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.VORE_PREFS_ONBOARDING
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["tutorial_prompt_answered"] is True
    assert raw["vore_prefs_onboarding_complete"] is False


def test_yes_path_runs_tutorial_pages_then_vore_prefs(tmp_path) -> None:
    path = tmp_path / "settings.json"
    app = App(settings=SettingsStore(path=path))
    app.tutorial_prompt.move_down()
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.TUTORIAL
    assert app.tutorial_screen.page_index == PAGE_CONTENT
    app.handle_event(_key(KeySym.RETURN))
    assert app.tutorial_screen.page_index == PAGE_COMMANDS
    app.handle_event(_key(KeySym.RETURN))
    assert app.tutorial_screen.page_index == PAGE_REMINDER
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.VORE_PREFS_ONBOARDING


def test_vore_prefs_confirm_shows_all_set_then_menu(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = SettingsStore(tutorial_prompt_answered=True, path=path)
    settings.save(path)
    app = App(settings=SettingsStore.load(path))
    app.vore_prefs_onboarding.highlight = CONFIRM_ROW_INDEX
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.ONBOARDING_NOTICE
    assert app.onboarding_notice_lines == ONBOARDING_ALL_SET_LINES
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["vore_prefs_onboarding_complete"] is True
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.MENU


def test_vore_prefs_enter_no_op_without_selection(tmp_path) -> None:
    settings = SettingsStore(tutorial_prompt_answered=True, path=tmp_path / "s.json")
    state = VorePrefsOnboardingState()
    assert (
        handle_vore_prefs_onboarding_event(state, _key(KeySym.RETURN), settings=settings)
        is VorePrefsOnboardingAction.NONE
    )


def test_options_tutorial_two_pages_esc_back(tmp_path) -> None:
    app = App(settings=_onboarded_settings(tmp_path))
    app.phase = AppPhase.OPTIONS
    app._open_tutorial(include_reminder=False, from_options=True)
    assert app.tutorial_screen.last_page_index == PAGE_COMMANDS
    app.handle_event(_key(KeySym.RETURN))
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.OPTIONS
    app._open_tutorial(include_reminder=False, from_options=True)
    app.handle_event(_key(KeySym.ESCAPE))
    assert app.phase is AppPhase.OPTIONS


def test_tutorial_content_includes_key_topics() -> None:
    text = " ".join(
        line.text
        for page in (PAGE_CONTENT, PAGE_COMMANDS)
        for line in tutorial_page_lines(page)
        if line.text
    )
    assert "@ - you" in text
    assert "b - an enemy bat" in text
    assert "Y up, G left, J right, N down" in text
    assert "diagonally" in text
    assert "q to quaff potions" in text
    assert "Shift+. or > to descend stairs" in text
    assert "number row (above T)" in text
    assert "F1 or ? to list all commands" in text
    assert "turn-based" in text.lower()
    assert "permanent stat bonuses" in text
    assert "digested" in text.lower()
    assert TUTORIAL_REMINDER_TEXT in tutorial_page_lines(PAGE_REMINDER)[0].text


def test_onboarding_notice_advances_on_enter() -> None:
    assert handle_onboarding_notice_event(_key(KeySym.RETURN)) is OnboardingNoticeAction.CONTINUE
    assert handle_onboarding_notice_event(_key(KeySym.ESCAPE)) is OnboardingNoticeAction.NONE


def test_options_tutorial_row(tmp_path) -> None:
    app = App(settings=_onboarded_settings(tmp_path))
    app.phase = AppPhase.OPTIONS
    app.options = OptionsMenuState(highlight=TUTORIAL_ROW_INDEX)
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.TUTORIAL
    assert app.tutorial_screen.from_options is True