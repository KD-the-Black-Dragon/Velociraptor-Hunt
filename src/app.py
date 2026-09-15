from __future__ import annotations

from typing import Any

# Dungeon types live under reference/kdvr; lightweight stubs keep career App importable.


class GameEngine:  # noqa: D101
    pass


class EngineEventResult:  # noqa: D101
    pass


class DepthEntryState:  # noqa: D101
    pass


class InventoryModalMode:  # noqa: D101
    pass

from enum import Enum, auto

import attrs
import tcod.console
import tcod.context
import tcod.event

from src import messages
from src.debug.session_log import session_log
from src.floor_prefetch import FloorPrefetch, menu_prefetch_params
from src.log_categories import MessageCategory
from src.menu import (
    MainMenuState,
    MenuAction,
    build_menu_options,
    handle_main_menu_event,
    is_ctrl_b,
    is_ctrl_g,
    is_ctrl_q,
    is_ctrl_s,
    render_main_menu,
)
from src.name_entry import (
    NameEntryAction,
    NameEntryState,
    handle_name_entry_event,
    render_name_entry,
    resolve_display_name,
)
from src.new_game_confirm import (
    NewGameConfirmAction,
    NewGameConfirmState,
    handle_new_game_confirm_event,
    render_new_game_confirm,
)
from src.mods.confirm import (
    ModsEnterConfirmAction,
    ModsEnterConfirmState,
    handle_mods_enter_confirm_event,
    render_mods_enter_confirm,
)
from src.mods.fingerprint import LOAD_MODS_MISMATCH_MESSAGE, save_mods_compatible
from src.mods.menu import (
    ModsMenuAction,
    ModsMenuState,
    handle_mods_menu_event,
    render_mods_menu,
)
from src.mods.reload import reload_all_game_data
from src.options_menu import (
    OptionsAction,
    OptionsMenuState,
    handle_options_event,
    render_options_menu,
)
from src.quit_confirm import (
    QuitConfirmAction,
    QuitConfirmState,
    handle_quit_confirm_event,
    render_quit_confirm,
)
from src.past_runs.store import PastRunsStore, sorted_for_display
from src.save.coordinator import SaveCoordinator
from src.save.store import SaveNotFoundError
from src.settings_store import SettingsStore
from src.ui.past_runs_screen import (
    PastRunsAction,
    PastRunsScreenState,
    build_past_runs_display_lines,
    handle_past_runs_event,
    past_runs_viewport_lines,
    render_past_runs_screen,
)
from src.ui.bootstrap import load_active_layout
from src.ui.window_controller import WindowController
from src.ui.window_state import resize_app_console
from src.ui.dynamic_layout import resolve_dynamic_layout
from src.ui.layout import UILayout, load_ui_layout
from src.ui.log_font import LogFontState
from src.ui.log_overlay import overlay_viewport_lines
from src.ui.credits_screen import CreditsAction, handle_credits_event, render_credits_screen
from src.tutorial_prompt import (
    TUTORIAL_DECLINED_NOTICE,
    TutorialPromptAction,
    TutorialPromptState,
    handle_tutorial_prompt_event,
    render_tutorial_prompt,
)
from src.ui.onboarding_notice import (
    ONBOARDING_ALL_SET_LINES,
    OnboardingNoticeAction,
    handle_onboarding_notice_event,
    render_onboarding_notice,
)
from src.ui.tutorial_screen import (
    TutorialAction,
    TutorialScreenState,
    handle_tutorial_event,
    render_tutorial_screen,
)
from src.ui.vore_prefs_onboarding import (
    VorePrefsOnboardingAction,
    VorePrefsOnboardingState,
    handle_vore_prefs_onboarding_event,
    render_vore_prefs_onboarding,
)
from src.components import DigestionStrikes, EquipState, Inventory, Item
from src.ui.log_present import (
    SCREEN_HAZE_MAX_ALPHA,
    digestion_haze_alpha,
    present_credits_frame,
    present_downtime_frame,
    present_frame,
    present_match_frame,
    present_help_overlay_frame,
    present_log_overlay_frame,
    present_onboarding_notice_frame,
    present_play_with_dialog_overlay,
    present_play_with_digestion_dialog,
    present_tutorial_page_frame,
    present_tutorial_prompt_frame,
    present_vore_prefs_onboarding_frame,
    present_with_dialog_overlay,
)
from src.ui.proportional_dialog import (
    DIGESTION_MODAL_FOOTER,
    GAME_OVER_FOOTER,
    LIST_MODAL_FOOTER,
    dialog_font_from_log_font,
    game_over_body_paragraphs,
    render_proportional_confirm_image,
    render_proportional_dialog_image,
    render_proportional_list_dialog_image,
)
from src.quit_confirm import QUIT_PROMPT
from src.new_game_confirm import NEW_GAME_OVERWRITE_PROMPT
from src.mods.confirm import MODS_ENTER_PROMPT_LINES
from src.career import CareerState, new_career
from src.career_store import CareerNotFoundError, CareerStore
from src.downtime_hub import (
    DowntimeHubState,
    HubAction,
    downtime_display_lines,
    handle_downtime_event,
    hub_footer_text,
    render_downtime_hub,
)
from src.background_pick import (
    BackgroundPickAction,
    BackgroundPickState,
    background_pick_footer,
    background_pick_lines,
    handle_background_pick_event,
)
from src.weapon_select import (
    WeaponSelectAction,
    WeaponSelectState,
    handle_weapon_select_event,
    weapon_select_footer,
    weapon_select_lines,
)
from src.hunt_session import (
    HuntAction,
    HuntMode,
    HuntSession,
    handle_hunt_event,
    render_hunt_stub,
)
from src.hunt_log import present_hunt_with_log
from src.hunt_stats import (
    HuntStatsAction,
    HuntStatsScreenState,
    HuntStatsStore,
    handle_hunt_stats_event,
    hunt_stats_footer,
    hunt_stats_lines,
    render_hunt_stats,
)
from src.backgrounds import apply_background_to_career
from src.match_session import MatchEndKind, MatchSession, render_match, start_match
from src.instant_action import (
    InstantActionResult,
    InstantActionState,
    handle_instant_action_event,
    render_instant_action,
    start_instant_match,
)
from src import messages as msg

EXAMINE_DESCRIPTION_FOOTER = "Esc: close"


class AppPhase(Enum):
    """Top-level application states."""

    TUTORIAL_PROMPT = auto()
    ONBOARDING_NOTICE = auto()
    TUTORIAL = auto()
    VORE_PREFS_ONBOARDING = auto()
    MENU = auto()
    NAME_ENTRY = auto()
    WEAPON_SELECT = auto()
    HUNT = auto()
    STATS = auto()
    BACKGROUND_PICK = auto()
    DEPTH_ENTRY = auto()
    INSTANT_ACTION = auto()
    OPTIONS = auto()
    MODS = auto()
    PAST_RUNS = auto()
    CREDITS = auto()
    DOWNTIME = auto()
    MATCH = auto()
    PLAY = auto()


@attrs.define
class App:
    """Owns menu vs gameplay phases and routes input/render."""

    settings: SettingsStore = attrs.Factory(SettingsStore.load)
    window_controller: WindowController | None = None
    pending_console_replace: tcod.console.Console | None = None
    baseline_layout: UILayout | None = None
    ui_layout: UILayout | None = None
    phase: AppPhase = AppPhase.MENU
    tutorial_prompt: TutorialPromptState | None = None
    onboarding_notice_lines: tuple[str, ...] | None = None
    tutorial_screen: TutorialScreenState = attrs.field(factory=TutorialScreenState)
    vore_prefs_onboarding: VorePrefsOnboardingState = attrs.field(
        factory=VorePrefsOnboardingState,
    )
    menu: MainMenuState = attrs.Factory(MainMenuState)
    name_entry: NameEntryState = attrs.Factory(NameEntryState)
    weapon_select: WeaponSelectState = attrs.field(factory=WeaponSelectState)
    hunt: HuntSession | None = None
    background_pick: BackgroundPickState = attrs.field(factory=BackgroundPickState)
    depth_entry: DepthEntryState = attrs.Factory(DepthEntryState)
    instant_action: InstantActionState = attrs.field(factory=InstantActionState)
    pending_depth_jump: bool = False
    pending_display_name: str = ""
    options: OptionsMenuState = attrs.Factory(OptionsMenuState)
    mods_menu: ModsMenuState | None = None
    mods_enter_confirm: ModsEnterConfirmState | None = None
    mods_return_to_menu: bool = False
    load_game_error: str | None = None
    quit_confirm: QuitConfirmState | None = None
    new_game_confirm: NewGameConfirmState | None = None
    pending_new_game_overwrite: bool = False
    engine: GameEngine | None = None
    career: CareerState | None = None
    career_store: CareerStore = attrs.field(factory=CareerStore)
    downtime_hub: DowntimeHubState = attrs.field(factory=DowntimeHubState)
    match_session: MatchSession | None = None
    floor_prefetch: FloorPrefetch = attrs.field(factory=FloorPrefetch)
    log_font: LogFontState = attrs.Factory(LogFontState)
    save_coordinator: SaveCoordinator = attrs.field(factory=SaveCoordinator)
    past_runs_store: PastRunsStore = attrs.field(factory=PastRunsStore)
    past_runs_screen: PastRunsScreenState = attrs.field(factory=PastRunsScreenState)
    past_runs_display: tuple = attrs.field(factory=tuple)
    hunt_stats_store: HuntStatsStore = attrs.field(factory=HuntStatsStore)
    stats_screen: HuntStatsScreenState = attrs.field(factory=HuntStatsScreenState)

    def __attrs_post_init__(self) -> None:
        if self.window_controller is None:
            self.window_controller = WindowController(settings=self.settings)
        self._boot_onboarding()

    def _boot_onboarding(self) -> None:
        """Route first launch through tutorial prompt and vore prefs."""
        if not self.settings.tutorial_prompt_answered:
            self.phase = AppPhase.TUTORIAL_PROMPT
            self.tutorial_prompt = TutorialPromptState()
            return
        if not self.settings.vore_prefs_onboarding_complete:
            self.phase = AppPhase.VORE_PREFS_ONBOARDING
            self.vore_prefs_onboarding = VorePrefsOnboardingState()
            return
        self.phase = AppPhase.MENU
        self._on_menu_enter()

    def _open_tutorial(
        self,
        *,
        include_reminder: bool,
        from_options: bool,
    ) -> None:
        self.tutorial_screen.reset(
            include_reminder=include_reminder,
            from_options=from_options,
        )
        self.phase = AppPhase.TUTORIAL

    def _advance_tutorial(self) -> None:
        if self.tutorial_screen.page_index < self.tutorial_screen.last_page_index:
            self.tutorial_screen.page_index += 1
            return
        if self.tutorial_screen.from_options:
            self.phase = AppPhase.OPTIONS
            return
        self._maybe_enter_vore_prefs_or_menu()

    def _show_onboarding_notice(self, lines: tuple[str, ...]) -> None:
        self.onboarding_notice_lines = lines
        self.phase = AppPhase.ONBOARDING_NOTICE

    def _maybe_enter_vore_prefs_or_menu(self) -> None:
        if not self.settings.vore_prefs_onboarding_complete:
            self.phase = AppPhase.VORE_PREFS_ONBOARDING
            self.vore_prefs_onboarding = VorePrefsOnboardingState()
            return
        self.phase = AppPhase.MENU
        self._on_menu_enter()

    def _open_past_runs(self) -> None:
        self.past_runs_display = tuple(
            sorted_for_display(self.past_runs_store.load_runs()),
        )
        self.past_runs_screen.reset()
        self.phase = AppPhase.PAST_RUNS

    def _has_continuable_save(self) -> bool:
        """Career hub save and/or legacy dungeon autosave."""
        return self.career_store.probe() or self.save_coordinator.store.probe()

    def _wipe_all_saves(self) -> None:
        self.save_coordinator.store.delete_all()
        self.career_store.delete()

    def _on_menu_enter(self) -> None:
        self.floor_prefetch.cancel()
        self.floor_prefetch.schedule(menu_prefetch_params(seed=None))
        self.menu = MainMenuState(
            options=build_menu_options(
                continue_available=self.save_coordinator.has_hunt_save(),
            ),
        )
        self.new_game_confirm = None
        self.pending_new_game_overwrite = False
        self.hunt = None

    def _commit_or_save_hunt(self) -> None:
        hunt = self.hunt
        if hunt is None:
            return
        if getattr(hunt, "training", False):
            return
        if hunt.outcome:
            try:
                self.hunt_stats_store.record_session(hunt)
            except OSError:
                pass
            self.save_coordinator.wipe_saves()
            return
        self.save_coordinator.save_hunt(hunt)

    def _abandon_saved_hunt(self) -> None:
        session = self.save_coordinator.load_hunt()
        if session is not None:
            if not session.outcome:
                session.outcome = "abandoned"
            try:
                self.hunt_stats_store.record_session(session)
            except OSError:
                pass
        self.save_coordinator.wipe_saves()

    def _autosave_open_hunt(self) -> None:
        if self.phase is AppPhase.HUNT and self.hunt is not None and not self.hunt.outcome:
            if getattr(self.hunt, "training", False):
                return
            if self.hunt.projectile_in_progress():
                return
            self.save_coordinator.save_hunt(self.hunt)

    def _return_to_menu(self) -> None:
        session_log.log("Quit to menu")
        self._commit_or_save_hunt()
        if self.career is not None:
            try:
                self.career_store.save(self.career)
            except OSError:
                pass
        if self.engine is not None:
            self.floor_prefetch.cancel()
        self.engine = None
        self.career = None
        self.match_session = None
        self._stop_hunt_rain()
        self.hunt = None
        self.downtime_hub = DowntimeHubState()
        self.quit_confirm = None
        self.mods_menu = None
        self.mods_enter_confirm = None
        self.mods_return_to_menu = False
        self.phase = AppPhase.MENU
        self._on_menu_enter()

    def _enter_downtime(self, career: CareerState) -> None:
        """Product path: career hub between matches."""
        self.career = career
        self.engine = None
        self.match_session = None
        self.downtime_hub = DowntimeHubState()
        self.downtime_hub.ensure_starter_gate(career)
        self.phase = AppPhase.DOWNTIME
        try:
            self.career_store.save(career)
        except OSError:
            pass
        session_log.log(
            f"Entered downtime (round {career.round_index}, gold {career.gold})",
        )

    def _start_match_from_hub(self) -> None:
        """Begin arena match from downtime card selection."""
        assert self.career is not None
        card = self.downtime_hub.pending_match_card
        if card is None:
            return
        self.downtime_hub.pending_match_card = None
        self.downtime_hub.reset_to_root()
        session_log.log(f"Started match {card.card_id} ({card.kind})")
        self.match_session = start_match(self.career, card)
        self.phase = AppPhase.MATCH

    def _finish_match_to_hub(self) -> None:
        """After recap, save career and return to downtime (or end career if digested).

        Instant action: discard ephemeral career and return to main menu (no store write).
        """
        ms = self.match_session
        instant = ms is not None and ms.instant_action
        digested = ms is not None and ms.end_kind is MatchEndKind.DIGESTED
        self.match_session = None
        if instant:
            session_log.log("Instant action ended — return to menu")
            self.career = None
            self.downtime_hub = DowntimeHubState()
            self.instant_action.reset()
            self.phase = AppPhase.MENU
            self._on_menu_enter()
            return
        if digested:
            session_log.log("Career ended — PC digested")
            self.career = None
            self.downtime_hub = DowntimeHubState()
            try:
                self.career_store.delete()
            except OSError:
                pass
            self.phase = AppPhase.MENU
            self._on_menu_enter()
            return
        assert self.career is not None
        try:
            self.career_store.save(self.career)
        except OSError:
            pass
        self.downtime_hub = DowntimeHubState()
        self.phase = AppPhase.DOWNTIME
        session_log.log(
            f"Returned to downtime (round {self.career.round_index}, gold {self.career.gold})",
        )

    def _start_instant_match_from_ui(self) -> None:
        """Begin solo practice match from Instant Action card pick."""
        card = self.instant_action.selected_card
        if card is None:
            return
        session_log.log(
            f"Instant action {card.card_id} ({card.kind})",
        )
        self.match_session = start_instant_match(
            card,
            difficulty_id=self.settings.difficulty_id,
        )
        self.career = self.match_session.career
        self.phase = AppPhase.MATCH

    def _start_new_career(
        self,
        display_name: str,
        *,
        background_id: str | None = None,
    ) -> None:
        if self.pending_new_game_overwrite:
            self._wipe_all_saves()
            self.pending_new_game_overwrite = False
        session_log.log("Started new career")
        career = new_career(
            player_name=display_name,
            difficulty_id=self.settings.difficulty_id,
        )
        if background_id:
            apply_background_to_career(career, background_id)
        self._enter_downtime(career)

    def _start_new_hunt(self, weapon: WeaponSelectState) -> None:
        sel = weapon.selected
        if sel is None:
            return
        session_log.log(f"Started hunt ({sel.weapon_id})")
        self.hunt = HuntSession(
            hunter_name="",
            weapon_id=sel.weapon_id,
            weapon_name=sel.name,
            difficulty_id=self.settings.difficulty_id,
        )
        self.engine = None
        self.career = None
        self.match_session = None
        self.phase = AppPhase.HUNT
        self.save_coordinator.save_hunt(self.hunt)
        self._start_hunt_rain()

    def _start_training(self) -> None:
        session_log.log("Started training mode")
        self.hunt = HuntSession(
            hunter_name="",
            weapon_id="rifle",
            weapon_name="Bolt-action rifle",
            difficulty_id=self.settings.difficulty_id,
            training=True,
        )
        self.engine = None
        self.career = None
        self.match_session = None
        self.phase = AppPhase.HUNT
        self._start_hunt_rain()

    def _start_hunt_rain(self) -> None:
        if self.hunt is None:
            return
        from src.hunt_rain_audio import start_hunt_rain

        start_hunt_rain(self.hunt.rain().level_id)

    def _stop_hunt_rain(self) -> None:
        from src.hunt_rain_audio import stop_hunt_rain

        stop_hunt_rain()

    def tick_hunt_rain(self) -> None:
        if self.phase is not AppPhase.HUNT or self.hunt is None:
            return
        from src.hunt_rain_audio import tick_hunt_rain

        tick_hunt_rain(self.hunt.rain().level_id)

    def hunt_rain_ticking(self) -> bool:
        from src.hunt_rain_audio import hunt_rain_active

        return self.phase is AppPhase.HUNT and self.hunt is not None and hunt_rain_active()

    def _load_career_or_dungeon(self, console: tcod.console.Console) -> None:
        """Prefer Gladiavore career; fall back to legacy dungeon autosave."""
        if self.career_store.probe():
            try:
                career = self.career_store.load()
            except (CareerNotFoundError, OSError, ValueError):
                self.load_game_error = "Could not load career save."
                self.phase = AppPhase.MENU
                self._on_menu_enter()
                return
            self.load_game_error = None
            self._enter_downtime(career)
            return
        self._load_saved_game(console)

    def _try_open_mods(self) -> None:
        """Open Mods, or show capital-Y save wipe gate when a save exists."""
        has_save = self._has_continuable_save()
        if has_save:
            self.mods_enter_confirm = ModsEnterConfirmState()
            return
        self._enter_mods(
            ended_run=self.phase is AppPhase.PLAY or self.phase is AppPhase.DOWNTIME,
        )

    def _enter_mods(self, *, ended_run: bool) -> None:
        """Enter the Mods submenu after any required save wipe / run end."""
        self.mods_enter_confirm = None
        self.mods_return_to_menu = ended_run
        if ended_run and self.engine is not None:
            self.floor_prefetch.cancel()
            self.engine = None
        if ended_run:
            self.career = None
        self.mods_menu = ModsMenuState()
        self.mods_menu.refresh()
        self.phase = AppPhase.MODS

    def _confirm_enter_mods(self) -> None:
        """Delete saves (if any), end PLAY/DOWNTIME if active, then open Mods."""
        self._wipe_all_saves()
        was_active = (
            self.phase is AppPhase.PLAY
            or self.phase is AppPhase.DOWNTIME
            or self.engine is not None
            or self.career is not None
        )
        if was_active and self.engine is not None:
            session_log.log("Ended run for Mods menu")
        if was_active and self.career is not None:
            session_log.log("Ended career for Mods menu")
        self._enter_mods(ended_run=was_active or self.mods_return_to_menu)

    def _leave_mods(self) -> None:
        """Reload all JSON data, then return to Options or main menu."""
        reload_all_game_data()
        # Refresh layout template so Options preset list reflects ui_layout mods.
        self.reload_baseline_from_settings()
        self.ui_layout = None
        self.mods_menu = None
        self.mods_enter_confirm = None
        if self.mods_return_to_menu:
            self.mods_return_to_menu = False
            self.phase = AppPhase.MENU
            self._on_menu_enter()
            return
        self.phase = AppPhase.OPTIONS

    def _enter_play(self, engine: GameEngine) -> None:
        """Attach engine, switch to PLAY, and write the initial autosave."""
        self.engine = engine
        self.engine.past_runs_store = self.past_runs_store
        self.phase = AppPhase.PLAY
        if not engine.arena_mode:
            self.save_coordinator.on_play_enter(engine)

    def _layout_for_run(
        self,
        console: tcod.console.Console,
        *,
        ui_preset: str | None = None,
    ) -> UILayout:
        if ui_preset:
            self.baseline_layout = load_ui_layout(ui_preset)
        else:
            self.reload_baseline_from_settings()
        assert self.baseline_layout is not None
        layout = resolve_dynamic_layout(
            self.baseline_layout,
            console.width,
            console.height,
        )
        self.apply_ui_layout(layout)
        return layout

    def _start_new_game(
        self,
        display_name: str,
        *,
        console: tcod.console.Console,
    ) -> None:
        """Legacy dungeon New Game (depth-jump floor 1, tools). Product path is career."""
        if self.pending_new_game_overwrite:
            self._wipe_all_saves()
            self.pending_new_game_overwrite = False
        session_log.log("Started new game (legacy dungeon)")
        layout = self._layout_for_run(console, ui_preset=self.settings.ui_preset)
        self._enter_play(
            GameEngine(
                player_name=display_name,
                vore_content_prefs=self.settings.vore_content,
                difficulty_id=self.settings.difficulty_id,
                ui_layout=layout,
                floor_prefetch=self.floor_prefetch,
                save_coordinator=self.save_coordinator,
            )
        )

    def _start_arena_game(
        self,
        entity_id: str,
        *,
        console: tcod.console.Console,
    ) -> None:
        session_log.log(f"Started arena battle vs {entity_id}")
        layout = self._layout_for_run(console, ui_preset=self.settings.ui_preset)
        engine = GameEngine(
            player_name="Player",
            vore_content_prefs=self.settings.vore_content,
            difficulty_id=self.settings.difficulty_id,
            ui_layout=layout,
            floor_prefetch=self.floor_prefetch,
            save_coordinator=self.save_coordinator,
            skip_new_game=True,
        )
        initialize_arena(engine, entity_id)
        self._enter_play(engine)

    def _start_depth_jump_game(
        self,
        display_name: str,
        target_depth: int,
        *,
        console: tcod.console.Console,
    ) -> None:
        if self.pending_new_game_overwrite:
            self._wipe_all_saves()
            self.pending_new_game_overwrite = False
        session_log.log(f"Started depth-jump game at floor {target_depth}")
        layout = self._layout_for_run(console, ui_preset=self.settings.ui_preset)
        engine = GameEngine(
            player_name=display_name,
            vore_content_prefs=self.settings.vore_content,
            difficulty_id=self.settings.difficulty_id,
            ui_layout=layout,
            floor_prefetch=self.floor_prefetch,
            save_coordinator=self.save_coordinator,
            skip_new_game=True,
        )
        engine.new_game(start_depth=target_depth, level_warped=True)
        self._enter_play(engine)

    def _load_saved_game(self, console: tcod.console.Console) -> None:
        try:
            run = self.save_coordinator.store.load_best()
        except SaveNotFoundError:
            self._on_menu_enter()
            return
        if not save_mods_compatible(run):
            # Keep the save on disk; player may restore mods via Explorer or start New Game.
            self.phase = AppPhase.MENU
            self._on_menu_enter()
            self.load_game_error = LOAD_MODS_MISMATCH_MESSAGE
            return
        self.load_game_error = None
        layout = self._layout_for_run(console, ui_preset=self.settings.ui_preset)
        engine = GameEngine.from_run_snapshot(
            run,
            floor_prefetch=self.floor_prefetch,
        )
        engine.ui_layout = layout
        engine.save_coordinator = self.save_coordinator
        engine._schedule_floor_prefetch()
        self._enter_play(engine)
        session_log.log("Loaded game")

    def active_layout(self) -> UILayout:
        if self.ui_layout is not None:
            return self.ui_layout
        return load_active_layout(self.settings)

    def apply_ui_layout(self, layout: UILayout) -> None:
        self.ui_layout = layout
        if self.engine is not None:
            self.engine.ui_layout = layout

    def reload_baseline_from_settings(self) -> None:
        """Refresh the preset template after Options changes ui_preset."""
        self.baseline_layout = load_active_layout(self.settings)

    def sync_layout_for_console(self, console: tcod.console.Console) -> UILayout:
        """Reload the active preset from settings and resolve at console size."""
        return self._layout_for_run(console)

    def layout_for_new_game(self, console: tcod.console.Console) -> UILayout:
        """Resolve the active preset at the current window size for a new run."""
        return self._layout_for_run(console)

    def rest_in_progress(self) -> bool:
        return (
            self.phase is AppPhase.PLAY
            and self.engine is not None
            and self.engine.rest_in_progress()
        )

    def autoexplore_in_progress(self) -> bool:
        return (
            self.phase is AppPhase.PLAY
            and self.engine is not None
            and self.engine.autoexplore_in_progress()
        )

    def projectile_in_progress(self) -> bool:
        if self.phase is AppPhase.HUNT and self.hunt is not None:
            return self.hunt.projectile_in_progress()
        return (
            self.phase is AppPhase.PLAY
            and self.engine is not None
            and self.engine.projectile_in_progress()
        )

    def advance_projectile_animation(self) -> None:
        if self.phase is AppPhase.HUNT and self.hunt is not None:
            flying = self.hunt.projectile_in_progress()
            self.hunt.advance_projectile()
            if flying and not self.hunt.projectile_in_progress():
                self._autosave_open_hunt()
            return
        if self.engine is not None:
            self.engine.advance_projectile_animation()

    def projectile_frame_sleep_seconds(self) -> float:
        if self.phase is AppPhase.HUNT and self.hunt is not None:
            from src.hunt_projectile import load_hunt_projectile

            return load_hunt_projectile().frame_sleep_seconds
        return 0.0

    def _font_ready(self) -> bool:
        return self.log_font.enabled and self.log_font.font is not None

    def _digestion_strike_haze_alpha(self) -> int:
        """Progressive veil while DigestionStrikes accumulate (0 HP / stunned phase)."""
        if self.engine is None or self.engine.player is None:
            return 0
        strikes = self.engine.player.components.get(DigestionStrikes)
        if strikes is None:
            return 0
        return digestion_haze_alpha(strikes.count)

    def render(self, console: tcod.console.Console) -> None:
        font_ready = self._font_ready()
        if self.phase is AppPhase.TUTORIAL_PROMPT and self.tutorial_prompt is not None:
            render_tutorial_prompt(console, self.tutorial_prompt)
            return
        if self.phase is AppPhase.ONBOARDING_NOTICE and self.onboarding_notice_lines:
            render_onboarding_notice(console, self.onboarding_notice_lines)
            return
        if self.phase is AppPhase.TUTORIAL:
            render_tutorial_screen(console, self.tutorial_screen)
            return
        if self.phase is AppPhase.VORE_PREFS_ONBOARDING:
            render_vore_prefs_onboarding(
                console,
                self.vore_prefs_onboarding,
                settings=self.settings,
            )
            return
        if self.phase is AppPhase.MENU:
            render_main_menu(console, self.menu)
            if self.new_game_confirm is not None:
                if not font_ready:
                    render_new_game_confirm(console, self.new_game_confirm)
            elif self.load_game_error is not None:
                if not font_ready:
                    _render_menu_notice(console, self.load_game_error)
            return
        if self.phase is AppPhase.NAME_ENTRY:
            render_name_entry(console, self.name_entry)
            return
        if self.phase is AppPhase.WEAPON_SELECT:
            if not self._font_ready():
                console.clear()
                y = 1
                for line in weapon_select_lines(self.weapon_select):
                    if y >= console.height - 2:
                        break
                    console.print(2, y, line.text[: console.width - 4], fg=line.fg)
                    y += 1
                console.print(
                    2,
                    console.height - 1,
                    weapon_select_footer()[: console.width - 4],
                    fg=(140, 140, 140),
                )
            return
        if self.phase is AppPhase.STATS:
            if not self._font_ready():
                did = self.stats_screen.difficulty_id
                render_hunt_stats(
                    console,
                    self.hunt_stats_store.load(did),
                    difficulty_id=did,
                )
            return
        if self.phase is AppPhase.HUNT and self.hunt is not None:
            render_hunt_stub(console, self.hunt)
            if self.quit_confirm is not None and not font_ready:
                render_quit_confirm(console, self.quit_confirm)
            return
        if self.phase is AppPhase.BACKGROUND_PICK:
            # Full-screen text; proportional path uses present_downtime_frame.
            if not self._font_ready():
                console.clear()
                y = 1
                for line in background_pick_lines(self.background_pick):
                    if y >= console.height - 2:
                        break
                    console.print(2, y, line.text[: console.width - 4], fg=line.fg)
                    y += 1
                console.print(
                    2,
                    console.height - 1,
                    background_pick_footer()[: console.width - 4],
                    fg=(140, 140, 140),
                )
            return
        if self.phase is AppPhase.DEPTH_ENTRY:
            render_depth_entry(console, self.depth_entry)
            return
        if self.phase is AppPhase.INSTANT_ACTION:
            render_instant_action(console, self.instant_action)
            return
        if self.phase is AppPhase.OPTIONS:
            render_options_menu(console, self.options, settings=self.settings)
            if self.mods_enter_confirm is not None and not font_ready:
                render_mods_enter_confirm(console, self.mods_enter_confirm)
            return
        if self.phase is AppPhase.MODS:
            if self.mods_menu is not None:
                render_mods_menu(console, self.mods_menu)
            return
        if self.phase is AppPhase.PAST_RUNS:
            render_past_runs_screen(
                console,
                list(self.past_runs_display),
                self.past_runs_screen,
            )
            return
        if self.phase is AppPhase.CREDITS:
            render_credits_screen(console)
            return
        if self.phase is AppPhase.DOWNTIME and self.career is not None:
            render_downtime_hub(console, self.career, self.downtime_hub)
            if self.quit_confirm is not None and not font_ready:
                render_quit_confirm(console, self.quit_confirm)
            return
        if self.phase is AppPhase.MATCH and self.match_session is not None:
            render_match(console, self.match_session)
            if self.quit_confirm is not None and not font_ready:
                render_quit_confirm(console, self.quit_confirm)
            return
        if self.engine is not None:
            use_log_ttf = self.phase is AppPhase.PLAY and self.log_font.enabled
            play_font = use_log_ttf and self.log_font.font is not None
            # Proportional dialogs composite in present(); skip CP437 text.
            draw_digest = not (play_font and self.engine.digestion_modal.active)
            draw_vore = not (play_font and self.engine.vore_modal.active)
            draw_examine = not (
                play_font and self.engine.examine_state.showing_description
            )
            inv = self.engine.inventory_modal
            draw_inv = not (
                play_font
                and inv.active
                and inv.mode
                not in (
                    InventoryModalMode.EVOKE_TARGET,
                    InventoryModalMode.THROW_TARGET,
                    InventoryModalMode.BLINK_TARGET,
                )
            )
            draw_pickup = not (play_font and self.engine.ground_pickup_modal.active)
            draw_macguffin = not (
                play_font and self.engine.macguffin_victory_confirm.active
            )
            # Full game-over panel is proportional (+ haze); skip all CP437 recap.
            skip_go_cp437 = play_font and self.engine.game_over.active
            self.engine.render(
                console,
                blit_message_log=not use_log_ttf,
                draw_digestion_modal=draw_digest,
                draw_vore_modal=draw_vore,
                draw_examine_description=draw_examine,
                draw_inventory_modal=draw_inv,
                draw_ground_pickup_modal=draw_pickup,
                draw_macguffin_victory=draw_macguffin,
                draw_game_over=not skip_go_cp437,
                draw_game_over_body=not skip_go_cp437,
            )
        if self.quit_confirm is not None and not self._font_ready():
            render_quit_confirm(console, self.quit_confirm)

    def _narrative_dialog_payload(self) -> tuple[str, str] | None:
        """Body + footer for digestion/vore/examine proportional dialogs."""
        if self.engine is None:
            return None
        if self.engine.digestion_modal.active:
            return self.engine.digestion_modal.line, DIGESTION_MODAL_FOOTER
        if self.engine.vore_modal.active:
            return self.engine.vore_modal.current_line(), DIGESTION_MODAL_FOOTER
        if self.engine.examine_state.showing_description:
            return self.engine.examine_state.description_text, EXAMINE_DESCRIPTION_FOOTER
        return None

    def _confirm_dialog_image(self, console: tcod.console.Console):
        """Build proportional Y/n or notice dialog, or None."""
        if not self._font_ready():
            return None
        dialog_font = dialog_font_from_log_font(self.log_font)
        if dialog_font is None:
            return None
        layout = self.active_layout()

        if self.quit_confirm is not None:
            return render_proportional_confirm_image(
                [QUIT_PROMPT],
                font=dialog_font,
                layout=layout,
                console_w=console.width,
                console_h=console.height,
                error_message=self.quit_confirm.error_message,
            )
        if self.phase is AppPhase.MENU and self.new_game_confirm is not None:
            return render_proportional_confirm_image(
                [NEW_GAME_OVERWRITE_PROMPT],
                font=dialog_font,
                layout=layout,
                console_w=console.width,
                console_h=console.height,
                error_message=self.new_game_confirm.error_message,
            )
        if self.phase is AppPhase.MENU and self.load_game_error is not None:
            return render_proportional_confirm_image(
                [self.load_game_error],
                font=dialog_font,
                layout=layout,
                console_w=console.width,
                console_h=console.height,
                footer_text="(Press any key)",
            )
        if self.phase is AppPhase.OPTIONS and self.mods_enter_confirm is not None:
            return render_proportional_confirm_image(
                list(MODS_ENTER_PROMPT_LINES),
                font=dialog_font,
                layout=layout,
                console_w=console.width,
                console_h=console.height,
                error_message=self.mods_enter_confirm.error_message,
            )
        if (
            self.engine is not None
            and self.engine.macguffin_victory_confirm.active
        ):
            first, second = victory_prompt_lines(
                self.engine.macguffin_victory_confirm.display_name
            )
            return render_proportional_confirm_image(
                [first, second],
                font=dialog_font,
                layout=layout,
                console_w=console.width,
                console_h=console.height,
                error_message=self.engine.macguffin_victory_confirm.error_message,
            )
        if self.engine is not None and self.engine.arena_victory_active:
            return render_proportional_confirm_image(
                [self.engine.arena_victory_message],
                font=dialog_font,
                layout=layout,
                console_w=console.width,
                console_h=console.height,
                footer_text="(Enter)",
            )
        return None

    def _game_over_dialog_image(self, console: tcod.console.Console):
        if self.engine is None or not self.engine.game_over.active:
            return None
        if not self._font_ready():
            return None
        dialog_font = dialog_font_from_log_font(self.log_font)
        if dialog_font is None:
            return None
        go = self.engine.game_over
        assert go.ending is not None
        paragraphs = game_over_body_paragraphs(
            player_name=go.player_name,
            ending_line=format_game_over_ending(go.ending),
            monsters_defeated=go.monsters_defeated,
            runes_collected=go.runes_collected,
            depth=go.depth,
        )
        return render_proportional_confirm_image(
            paragraphs,
            font=dialog_font,
            layout=self.active_layout(),
            console_w=console.width,
            console_h=console.height,
            footer_text=GAME_OVER_FOOTER,
        )

    def _confirm_band(self) -> str:
        if self.phase is AppPhase.MENU and (
            self.new_game_confirm is not None or self.load_game_error is not None
        ):
            return "lower"
        return "center"

    def _uses_proportional_list_dialog(self) -> bool:
        """True when inventory list/detail or ground pickup should composite TTF."""
        if self.engine is None:
            return False
        if self.engine.ground_pickup_modal.active:
            return True
        inv = self.engine.inventory_modal
        return inv.active and inv.mode not in (
            InventoryModalMode.EVOKE_TARGET,
            InventoryModalMode.THROW_TARGET,
            InventoryModalMode.BLINK_TARGET,
        )

    def _inventory_or_pickup_dialog_image(self, console: tcod.console.Console):
        """Build proportional inventory/pickup dialog image, or None if unavailable."""
        if self.engine is None or self.log_font.font is None:
            return None

        dialog_font = dialog_font_from_log_font(self.log_font)
        if dialog_font is None:
            return None
        layout = self.active_layout()
        engine = self.engine
        inv_modal = engine.inventory_modal
        if inv_modal.active and inv_modal.mode not in (
            InventoryModalMode.EVOKE_TARGET,
            InventoryModalMode.THROW_TARGET,
            InventoryModalMode.BLINK_TARGET,
        ):
            player = engine.player
            if player is None:
                return None
            inventory = player.components.get(Inventory)
            if inventory is None:
                return None
            equip = player.components.get(EquipState)
            list_parts = inventory_list_item_rows(inv_modal, inventory, equip=equip)
            if list_parts is not None:
                title, rows = list_parts
                return render_proportional_list_dialog_image(
                    title,
                    rows,
                    font=dialog_font,
                    layout=layout,
                    console_w=console.width,
                    console_h=console.height,
                    footer_text=LIST_MODAL_FOOTER,
                )
            # Inspect detail: single-column narrative panel (same font).
            text = inventory_modal_text(inv_modal, inventory, equip=equip)
            if not text:
                return None
            body = text
            footer = "Esc: back"
            if "\n\nEsc:" in text:
                body, _, rest = text.rpartition("\n\n")
                footer = rest.strip() or footer
            return render_proportional_dialog_image(
                body,
                font=dialog_font,
                layout=layout,
                console_w=console.width,
                console_h=console.height,
                footer_text=footer,
            )
        if engine.ground_pickup_modal.active:
            reg = item_registry()
            state = engine.ground_pickup_modal
            rows = []
            for index, entity in enumerate(state.item_entities):
                letter = state.letter_for_index(index)
                floor_item = entity.components[Item]
                name = reg.display_name_for(floor_item.item_id, floor_item.category)
                rows.append(f"{letter}) {name}")
            return render_proportional_list_dialog_image(
                "Pick up which item?",
                rows,
                font=dialog_font,
                layout=layout,
                console_w=console.width,
                console_h=console.height,
                footer_text=LIST_MODAL_FOOTER,
            )
        return None

    def present(self, console: tcod.console.Console, context: tcod.context.Context) -> None:
        """Present the rendered console, compositing the proportional log during play."""
        if self.phase is AppPhase.TUTORIAL_PROMPT and self.tutorial_prompt is not None:
            present_tutorial_prompt_frame(
                context,
                console,
                layout=self.active_layout(),
                prompt_state=self.tutorial_prompt,
                log_font=self.log_font,
                integer_scaling=True,
                align=(0, 0),
            )
            return
        if self.phase is AppPhase.ONBOARDING_NOTICE and self.onboarding_notice_lines:
            present_onboarding_notice_frame(
                context,
                console,
                layout=self.active_layout(),
                messages=self.onboarding_notice_lines,
                log_font=self.log_font,
                integer_scaling=True,
                align=(0, 0),
            )
            return
        if self.phase is AppPhase.TUTORIAL:
            present_tutorial_page_frame(
                context,
                console,
                layout=self.active_layout(),
                state=self.tutorial_screen,
                log_font=self.log_font,
                integer_scaling=True,
                align=(0, 0),
            )
            return
        if self.phase is AppPhase.VORE_PREFS_ONBOARDING:
            present_vore_prefs_onboarding_frame(
                context,
                console,
                layout=self.active_layout(),
                state=self.vore_prefs_onboarding,
                settings=self.settings,
                log_font=self.log_font,
                integer_scaling=True,
                align=(0, 0),
            )
            return
        if (
            self.phase is AppPhase.PLAY
            and self.engine is not None
            and (
                self.engine.help_overlay.active
                or self.engine.log_overlay.active
            )
        ):
            if self.engine.help_overlay.active:
                present_help_overlay_frame(
                    context,
                    console,
                    layout=self.active_layout(),
                    log_font=self.log_font,
                    integer_scaling=True,
                    align=(0, 0),
                )
                return
            present_log_overlay_frame(
                context,
                console,
                layout=self.active_layout(),
                log_entries=self.engine.message_log.entries(),
                log_overlay=self.engine.log_overlay,
                log_font=self.log_font,
                viewport_lines=overlay_viewport_lines(self.active_layout()),
                integer_scaling=True,
                align=(0, 0),
            )
            return
        if self.phase is AppPhase.CREDITS:
            present_credits_frame(
                context,
                console,
                layout=self.active_layout(),
                log_font=self.log_font,
                integer_scaling=True,
                align=(0, 0),
            )
            return
        if self.phase is AppPhase.WEAPON_SELECT:
            present_downtime_frame(
                context,
                console,
                layout=self.active_layout(),
                lines=weapon_select_lines(self.weapon_select),
                footer_text=weapon_select_footer(),
                log_font=self.log_font,
                dialog_img=None,
                integer_scaling=True,
                align=(0, 0),
            )
            return
        if self.phase is AppPhase.STATS:
            present_downtime_frame(
                context,
                console,
                layout=self.active_layout(),
                lines=hunt_stats_lines(
                    self.hunt_stats_store.load(self.stats_screen.difficulty_id),
                    difficulty_id=self.stats_screen.difficulty_id,
                ),
                footer_text=hunt_stats_footer(),
                log_font=self.log_font,
                dialog_img=None,
                integer_scaling=True,
                align=(0, 0),
            )
            return
        if self.phase is AppPhase.BACKGROUND_PICK:
            present_downtime_frame(
                context,
                console,
                layout=self.active_layout(),
                lines=background_pick_lines(self.background_pick),
                footer_text=background_pick_footer(),
                log_font=self.log_font,
                dialog_img=None,
                integer_scaling=True,
                align=(0, 0),
            )
            return
        if self.phase is AppPhase.DOWNTIME and self.career is not None:
            dialog_img = (
                self._confirm_dialog_image(console) if self._font_ready() else None
            )
            present_downtime_frame(
                context,
                console,
                layout=self.active_layout(),
                lines=downtime_display_lines(self.career, self.downtime_hub),
                footer_text=hub_footer_text(self.downtime_hub),
                log_font=self.log_font,
                dialog_img=dialog_img,
                integer_scaling=True,
                align=(0, 0),
            )
            return
        if self.phase is AppPhase.MATCH and self.match_session is not None:
            dialog_img = (
                self._confirm_dialog_image(console) if self._font_ready() else None
            )
            present_match_frame(
                context,
                console,
                layout=self.active_layout(),
                session=self.match_session,
                log_font=self.log_font,
                dialog_img=dialog_img,
                integer_scaling=True,
                align=(0, 0),
            )
            return
        strike_haze = (
            self._digestion_strike_haze_alpha()
            if self.phase is AppPhase.PLAY
            else 0
        )
        if self._font_ready():
            confirm_img = self._confirm_dialog_image(console)
            if confirm_img is not None:
                band = self._confirm_band()
                if self.phase is AppPhase.PLAY and self.engine is not None:
                    present_play_with_dialog_overlay(
                        context,
                        console,
                        layout=self.active_layout(),
                        log_entries=self.engine.message_log.entries(),
                        log_font=self.log_font,
                        max_lines=self.active_layout().message_log_lines,
                        dialog_img=confirm_img,
                        band=band,
                        haze_alpha=strike_haze,
                        integer_scaling=True,
                        align=(0, 0),
                    )
                else:
                    present_with_dialog_overlay(
                        context,
                        console,
                        layout=self.active_layout(),
                        dialog_img=confirm_img,
                        band=band,
                        integer_scaling=True,
                        align=(0, 0),
                    )
                return
            go_img = self._game_over_dialog_image(console)
            if go_img is not None and self.engine is not None:
                present_play_with_dialog_overlay(
                    context,
                    console,
                    layout=self.active_layout(),
                    log_entries=self.engine.message_log.entries(),
                    log_font=self.log_font,
                    max_lines=self.active_layout().message_log_lines,
                    dialog_img=go_img,
                    band="center",
                    haze_alpha=SCREEN_HAZE_MAX_ALPHA,
                    integer_scaling=True,
                    align=(0, 0),
                )
                return
            narrative = self._narrative_dialog_payload()
            if (
                self.phase is AppPhase.PLAY
                and self.engine is not None
                and narrative is not None
            ):
                dialog_text, footer_text = narrative
                # Full veil for digestion completion; strike ramp otherwise (vore/examine).
                haze = (
                    SCREEN_HAZE_MAX_ALPHA
                    if self.engine.digestion_modal.active
                    else strike_haze
                )
                present_play_with_digestion_dialog(
                    context,
                    console,
                    layout=self.active_layout(),
                    log_entries=self.engine.message_log.entries(),
                    log_font=self.log_font,
                    max_lines=self.active_layout().message_log_lines,
                    dialog_text=dialog_text,
                    footer_text=footer_text,
                    haze_alpha=haze,
                    integer_scaling=True,
                    align=(0, 0),
                )
                return
            if (
                self.phase is AppPhase.PLAY
                and self.engine is not None
                and self._uses_proportional_list_dialog()
            ):
                dialog_img = self._inventory_or_pickup_dialog_image(console)
                if dialog_img is not None:
                    present_play_with_dialog_overlay(
                        context,
                        console,
                        layout=self.active_layout(),
                        log_entries=self.engine.message_log.entries(),
                        log_font=self.log_font,
                        max_lines=self.active_layout().message_log_lines,
                        dialog_img=dialog_img,
                        haze_alpha=strike_haze,
                        integer_scaling=True,
                        align=(0, 0),
                    )
                    return
        if self.phase is AppPhase.PLAY and self.engine is not None and self.log_font.enabled:
            present_frame(
                context,
                console,
                layout=self.active_layout(),
                log_entries=self.engine.message_log.entries(),
                log_font=self.log_font,
                max_lines=self.active_layout().message_log_lines,
                haze_alpha=strike_haze,
                integer_scaling=True,
                align=(0, 0),
            )
            return
        if self.phase is AppPhase.PLAY and strike_haze > 0:
            present_frame(
                context,
                console,
                layout=self.active_layout(),
                haze_alpha=strike_haze,
                integer_scaling=True,
                align=(0, 0),
            )
            return
        if (
            self.phase is AppPhase.HUNT
            and self.hunt is not None
            and self.log_font.enabled
            and self.log_font.font is not None
            and not self.hunt.help_open
            and self.hunt.training_menu is None
            and self.hunt.mode
            not in (
                HuntMode.SWALLOW,
                HuntMode.BELLY,
                HuntMode.DIGEST,
                HuntMode.GAME_OVER,
            )
        ):
            present_hunt_with_log(
                context,
                console,
                log_entries=self.hunt.message_log.entries(),
                font=self.log_font.font,
                layout=self.active_layout(),
            )
            return
        present_frame(context, console, integer_scaling=True, align=(0, 0))

    def handle_event(
        self,
        event: tcod.event.Event,
        *,
        console: tcod.console.Console | None = None,
        context: tcod.context.Context | None = None,
    ) -> bool:
        """Return True when the application should exit."""
        if isinstance(event, tcod.event.Quit):
            if self.phase is AppPhase.HUNT and self.hunt is not None:
                if getattr(self.hunt, "training", False):
                    pass
                elif self.hunt.outcome:
                    try:
                        self.hunt_stats_store.record_session(self.hunt)
                    except OSError:
                        pass
                    self.save_coordinator.wipe_saves()
                else:
                    self.hunt.flush_projectile()
                    self.save_coordinator.save_hunt(self.hunt)
            return True

        if self.phase is AppPhase.TUTORIAL_PROMPT and self.tutorial_prompt is not None:
            if is_ctrl_q(event):
                return False
            action = handle_tutorial_prompt_event(self.tutorial_prompt, event)
            if action is TutorialPromptAction.YES:
                self.settings.mark_tutorial_prompt_answered()
                self.tutorial_prompt = None
                self._open_tutorial(include_reminder=True, from_options=False)
            elif action is TutorialPromptAction.NO:
                self.settings.mark_tutorial_prompt_answered()
                self.tutorial_prompt = None
                self._show_onboarding_notice((TUTORIAL_DECLINED_NOTICE,))
            return False

        if self.phase is AppPhase.ONBOARDING_NOTICE:
            if is_ctrl_q(event):
                return False
            if handle_onboarding_notice_event(event) is OnboardingNoticeAction.CONTINUE:
                self.onboarding_notice_lines = None
                self._maybe_enter_vore_prefs_or_menu()
            return False

        if self.phase is AppPhase.TUTORIAL:
            if is_ctrl_q(event):
                return False
            action = handle_tutorial_event(self.tutorial_screen, event)
            if action is TutorialAction.BACK:
                self.phase = AppPhase.OPTIONS
            elif action is TutorialAction.ADVANCE:
                self._advance_tutorial()
            return False

        if self.phase is AppPhase.VORE_PREFS_ONBOARDING:
            if is_ctrl_q(event):
                return False
            action = handle_vore_prefs_onboarding_event(
                self.vore_prefs_onboarding,
                event,
                settings=self.settings,
            )
            if action is VorePrefsOnboardingAction.CONFIRMED:
                self.settings.mark_vore_prefs_onboarding_complete()
                self._show_onboarding_notice(ONBOARDING_ALL_SET_LINES)
            return False

        if self.phase is AppPhase.MENU:
            if is_ctrl_q(event):
                return False
            if self.new_game_confirm is not None:
                action = handle_new_game_confirm_event(self.new_game_confirm, event)
                if action is NewGameConfirmAction.CONFIRM:
                    self.new_game_confirm = None
                    self.load_game_error = None
                    self._abandon_saved_hunt()
                    self.pending_new_game_overwrite = False
                    self.weapon_select = WeaponSelectState()
                    self.phase = AppPhase.WEAPON_SELECT
                elif action is NewGameConfirmAction.CANCEL:
                    self.new_game_confirm = None
                return False
            if self.load_game_error is not None and isinstance(event, tcod.event.KeyDown):
                # Any key dismisses the notice; menu stays ready for New Game / Options.
                self.load_game_error = None
                return False
            if is_ctrl_g(event) or is_ctrl_b(event):
                return False
            action = handle_main_menu_event(self.menu, event)
            if action is MenuAction.EXIT:
                return True
            if action is MenuAction.CONTINUE_HUNT:
                loaded = self.save_coordinator.load_hunt()
                if loaded is None:
                    self.load_game_error = "Could not load the saved hunt."
                else:
                    self.hunt = loaded
                    self.phase = AppPhase.HUNT
                    self._start_hunt_rain()
            elif action is MenuAction.NEW_HUNT:
                self.pending_depth_jump = False
                self.load_game_error = None
                if self.save_coordinator.has_hunt_save():
                    self.new_game_confirm = NewGameConfirmState()
                else:
                    self.weapon_select = WeaponSelectState()
                    self.phase = AppPhase.WEAPON_SELECT
            elif action is MenuAction.TRAINING:
                self.load_game_error = None
                self._start_training()
            elif action is MenuAction.STATS:
                self.load_game_error = None
                self.stats_screen = HuntStatsScreenState(
                    difficulty_id=self.settings.difficulty_id,
                )
                self.phase = AppPhase.STATS
            elif action is MenuAction.OPTIONS:
                self.load_game_error = None
                self.options = OptionsMenuState()
                self.phase = AppPhase.OPTIONS
            return False

        if self.phase is AppPhase.NAME_ENTRY:
            if is_ctrl_q(event):
                return False
            action = handle_name_entry_event(self.name_entry, event)
            if action is NameEntryAction.CANCEL:
                self.pending_depth_jump = False
                self.pending_new_game_overwrite = False
                self.phase = AppPhase.MENU
                self._on_menu_enter()
            elif action is NameEntryAction.CONFIRM:
                self.pending_display_name = resolve_display_name(self.name_entry.buffer)
                self.weapon_select = WeaponSelectState()
                self.phase = AppPhase.WEAPON_SELECT
            return False

        if self.phase is AppPhase.WEAPON_SELECT:
            if is_ctrl_q(event):
                return False
            action = handle_weapon_select_event(self.weapon_select, event)
            if action is WeaponSelectAction.BACK:
                self.phase = AppPhase.MENU
                self._on_menu_enter()
            elif action is WeaponSelectAction.CONFIRM:
                self._start_new_hunt(self.weapon_select)
            return False

        if self.phase is AppPhase.STATS:
            if is_ctrl_q(event):
                return False
            if handle_hunt_stats_event(event, self.stats_screen) is HuntStatsAction.BACK:
                self.phase = AppPhase.MENU
                self._on_menu_enter()
            return False

        if self.phase is AppPhase.HUNT:
            if self.quit_confirm is not None:
                action = handle_quit_confirm_event(self.quit_confirm, event)
                if action is QuitConfirmAction.CONFIRM:
                    self.quit_confirm = None
                    self._return_to_menu()
                elif action is QuitConfirmAction.CANCEL:
                    self.quit_confirm = None
                return False
            if is_ctrl_q(event):
                if self.hunt is not None:
                    self.hunt.flush_projectile()
                self._autosave_open_hunt()
                self.quit_confirm = QuitConfirmState()
                return False
            if self.hunt is not None and handle_hunt_event(self.hunt, event) is HuntAction.LEAVE:
                self._return_to_menu()
                return False
            self._autosave_open_hunt()
            return False

        if self.phase is AppPhase.BACKGROUND_PICK:
            if is_ctrl_q(event):
                return False
            action = handle_background_pick_event(self.background_pick, event)
            if action is BackgroundPickAction.BACK:
                self.phase = AppPhase.NAME_ENTRY
            elif action is BackgroundPickAction.CONFIRM:
                sel = self.background_pick.selected
                bid = sel.background_id if sel is not None else None
                self._start_new_career(
                    self.pending_display_name,
                    background_id=bid,
                )
            return False

        if self.phase is AppPhase.DEPTH_ENTRY:
            if is_ctrl_q(event):
                return False
            from src.data.depth_jump_start_loader import default_depth_jump_start_config

            max_depth = default_depth_jump_start_config().max_target_depth
            action = handle_depth_entry_event(
                self.depth_entry,
                event,
                max_depth=max_depth,
            )
            if action is DepthEntryAction.CANCEL:
                self.pending_depth_jump = False
                self.pending_new_game_overwrite = False
                self.phase = AppPhase.MENU
                self._on_menu_enter()
            elif action is DepthEntryAction.CONFIRM:
                depth = parse_depth_value(self.depth_entry.buffer, max_depth=max_depth)
                assert depth is not None
                assert console is not None
                self.pending_depth_jump = False
                display_name = self.pending_display_name
                if depth == 1:
                    self._start_new_game(display_name, console=console)
                else:
                    self._start_depth_jump_game(
                        display_name,
                        depth,
                        console=console,
                    )
            return False

        if self.phase is AppPhase.INSTANT_ACTION:
            if is_ctrl_q(event):
                return False
            result = handle_instant_action_event(self.instant_action, event)
            if result is InstantActionResult.CANCEL_TO_MENU:
                self.instant_action.reset()
                self.phase = AppPhase.MENU
                self._on_menu_enter()
            elif result is InstantActionResult.START_MATCH:
                self._start_instant_match_from_ui()
            return False

        if self.phase is AppPhase.OPTIONS:
            if is_ctrl_q(event):
                return False
            if self.mods_enter_confirm is not None:
                confirm_action = handle_mods_enter_confirm_event(
                    self.mods_enter_confirm,
                    event,
                )
                if confirm_action is ModsEnterConfirmAction.CONFIRM:
                    self._confirm_enter_mods()
                elif confirm_action is ModsEnterConfirmAction.CANCEL:
                    self.mods_enter_confirm = None
                return False
            preset_before = self.settings.ui_preset
            layout = self.active_layout()

            def _toggle_fullscreen() -> None:
                assert self.window_controller is not None
                assert context is not None
                pixel_w, pixel_h = self.window_controller.toggle_fullscreen(context, layout)
                if console is not None:
                    self.pending_console_replace = resize_app_console(
                        self,
                        pixel_w,
                        pixel_h,
                    )

            action = handle_options_event(
                self.options,
                event,
                settings=self.settings,
                toggle_fullscreen=_toggle_fullscreen if context is not None else None,
            )
            if self.settings.ui_preset != preset_before:
                self.reload_baseline_from_settings()
                if console is not None and context is not None:
                    from src.ui.window_limits import client_pixels_from_context

                    baseline = self.baseline_layout or load_active_layout(self.settings)
                    pixel_w, pixel_h = client_pixels_from_context(context, baseline)
                    self.pending_console_replace = resize_app_console(
                        self,
                        pixel_w,
                        pixel_h,
                    )
                elif console is not None:
                    self.sync_layout_for_console(console)
            if action is OptionsAction.OPEN_TUTORIAL:
                self._open_tutorial(include_reminder=False, from_options=True)
            elif action is OptionsAction.OPEN_MODS:
                self._try_open_mods()
            elif action is OptionsAction.BACK:
                self.phase = AppPhase.MENU
                self._on_menu_enter()
            return False

        if self.phase is AppPhase.MODS:
            if is_ctrl_q(event):
                return False
            if self.mods_menu is None:
                self._leave_mods()
                return False
            mods_action = handle_mods_menu_event(self.mods_menu, event)
            if mods_action is ModsMenuAction.BACK:
                self._leave_mods()
            return False

        if self.phase is AppPhase.PAST_RUNS:
            if is_ctrl_q(event):
                return False
            line_count = len(
                build_past_runs_display_lines(list(self.past_runs_display)),
            )
            viewport_lines = past_runs_viewport_lines(
                console.height if console is not None else 44,
            )
            if (
                handle_past_runs_event(
                    self.past_runs_screen,
                    event,
                    line_count=line_count,
                    viewport_lines=viewport_lines,
                )
                is PastRunsAction.BACK
            ):
                self.phase = AppPhase.MENU
                self._on_menu_enter()
            return False

        if self.phase is AppPhase.CREDITS:
            if is_ctrl_q(event):
                return False
            if handle_credits_event(event) is CreditsAction.BACK:
                self.phase = AppPhase.MENU
                self._on_menu_enter()
            return False

        if self.phase is AppPhase.DOWNTIME and self.career is not None:
            if self.quit_confirm is not None:
                action = handle_quit_confirm_event(self.quit_confirm, event)
                if action is QuitConfirmAction.CONFIRM:
                    self._return_to_menu()
                elif action is QuitConfirmAction.CANCEL:
                    self.quit_confirm = None
                return False
            if is_ctrl_q(event):
                self.quit_confirm = QuitConfirmState()
                return False
            hub_action = handle_downtime_event(self.downtime_hub, self.career, event)
            if hub_action is HubAction.REQUEST_LEAVE_MENU:
                self.quit_confirm = QuitConfirmState()
            elif hub_action is HubAction.START_MATCH:
                self._start_match_from_hub()
            elif hub_action is HubAction.CAREER_DIRTY:
                try:
                    self.career_store.save(self.career)
                except OSError:
                    pass
            return False

        if self.phase is AppPhase.MATCH and self.match_session is not None:
            if self.quit_confirm is not None:
                action = handle_quit_confirm_event(self.quit_confirm, event)
                if action is QuitConfirmAction.CONFIRM:
                    self.quit_confirm = None
                    instant = self.match_session.instant_action
                    self.match_session = None
                    if instant:
                        self.career = None
                        self.instant_action.reset()
                        self.phase = AppPhase.MENU
                        self._on_menu_enter()
                    else:
                        # Abandon match without settlement — return to hub as-is.
                        self.phase = AppPhase.DOWNTIME
                        if self.career is not None:
                            try:
                                self.career_store.save(self.career)
                            except OSError:
                                pass
                elif action is QuitConfirmAction.CANCEL:
                    self.quit_confirm = None
                return False
            if is_ctrl_q(event):
                self.quit_confirm = QuitConfirmState()
                return False
            if is_ctrl_s(event) and self.match_session.instant_action:
                self.match_session.message_log.add(
                    msg.instant_action_not_saved(),
                    category=MessageCategory.CAUTION,
                )
                return False
            if self.match_session.handle_event(event):
                self._finish_match_to_hub()
            return False

        if self.phase is AppPhase.PLAY and self.engine is not None:
            if self.engine.arena_victory_active:
                from src.input_handlers import MODAL_ADVANCE_KEYS

                if (
                    isinstance(event, tcod.event.KeyDown)
                    and event.sym in MODAL_ADVANCE_KEYS
                ):
                    clear_arena_state(self.engine)
                    self._return_to_menu()
                return False

            if isinstance(event, tcod.event.KeyDown):
                if self.engine.rest_in_progress():
                    self.engine.cancel_rest()
                if self.engine.autoexplore_in_progress():
                    self.engine.cancel_autoexplore()

            if self.quit_confirm is not None:
                action = handle_quit_confirm_event(self.quit_confirm, event)
                if action is QuitConfirmAction.CONFIRM:
                    self._return_to_menu()
                elif action is QuitConfirmAction.CANCEL:
                    self.quit_confirm = None
                    self.save_coordinator.poll_save_failure(self.engine)
                return False

            if is_ctrl_q(event) and self.engine.can_issue_idle_command():
                self.save_coordinator.queue_background_save(self.engine)
                self.quit_confirm = QuitConfirmState()
                return False

            if is_ctrl_s(event) and self.engine.can_issue_idle_command():
                if self.engine.arena_mode:
                    self.engine.message_log.add(
                        messages.game_saved(),
                        category=MessageCategory.POSITIVE,
                    )
                elif self.save_coordinator.save_now(self.engine):
                    self.engine.message_log.add(
                        messages.game_saved(),
                        category=MessageCategory.POSITIVE,
                    )
                else:
                    self.engine.message_log.add(
                        messages.save_failed(),
                        category=MessageCategory.DANGER,
                    )
                return False

            result = self.engine.handle_event(event)
            if result is EngineEventResult.RECAP_DISMISSED:
                self._return_to_menu()
            self.save_coordinator.poll_save_failure(self.engine)
            return False

        return False


def _render_menu_notice(console: tcod.console.Console, message: str) -> None:
    """Multi-line notice on the main menu (e.g. load/mod mismatch) with chrome."""
    from src.ui.menu_dialog import (
        menu_dialog_max_width,
        render_menu_dialog_lines,
        wrap_dialog_text,
    )

    max_width = menu_dialog_max_width(console.width)
    lines = wrap_dialog_text(message, max_width=max_width)
    lines.append("(Press any key)")
    render_menu_dialog_lines(
        console,
        lines,
        body_fg=(255, 160, 120),
        hint_line_index=len(lines) - 1,
        band="lower",
    )