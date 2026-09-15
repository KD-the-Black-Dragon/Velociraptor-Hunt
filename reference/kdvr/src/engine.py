from __future__ import annotations

import random
from collections.abc import Callable
from typing import TYPE_CHECKING

import tcod.console
import tcod.event
from tcod.ecs import Entity, Registry

from src.components import (
    Engulfed,
    EquipState,
    Fighter,
    Inventory,
    PlayerEffects,
    PlayerProgression,
    Position,
    ScreenFlashState,
    Stunned,
)
from src.constants import (
    DEFAULT_VORE_CONTENT_PREFS,
    FLOOR_DEPTH_START,
    MAP_HEIGHT,
    MAP_WIDTH,
    LAYOUT_ARCHETYPE_FORCE,
    WATER_TESTING_MODE,
    VoreContentPreferences,
)
from src.floor_prefetch import FloorPrefetch, PrefetchParams
from src.map_gen import GameMap
from src import engine_floor, engine_input, engine_turn
from src.engine_input import EngineEventResult
from src.message_log import MessageLog
from src.past_runs.store import PastRunsStore
from src.run_stats import RunStats
from src.macguffin_discovery import MacguffinDiscovery
from src.macguffin_victory_confirm import (
    MacguffinVictoryConfirmState,
    render_macguffin_victory_confirm,
)
from src.systems.fov import update_fov
from src.systems.projectile_anim import ProjectileAnimSession, ProjectileFrameResult
from src.systems.autoexplore import AutoexploreFrameResult, AutoexploreSession
from src.systems.rest import RestFrameResult, RestSession
from src.systems.inventory import GroundPickupModalState
from src.systems.item_modals import InventoryModalState, InventoryModalMode
from src.systems.dismiss import DismissState
from src.systems.examine import ExamineState
from src.systems.digestion import DigestionModalState, GameOverState
from src.systems.render import (
    MESSAGE_LOG_BACKGROUND,
    render_centered_modal,
    render_digestion_modal,
    render_engulfed_overlay,
    render_entities,
    render_examine_cursor,
    render_game_over,
    render_ground_pickup_modal,
    render_message_log_panel,
    render_inventory_modal,
    render_map,
    render_screen_flash,
    render_vore_modal,
)
from src.ui.bootstrap import load_active_layout
from src.ui.sidebar import render_sidebar_npcs, render_sidebar_player
from src.ui.status_corner import (
    PlayerStatusEffects,
    player_effects_extra_rows,
    progression_extra_rows,
    render_status_corner,
)

from src.ui.camera import MapCamera
from src.ui.layout import UILayout
from src.ui.help_overlay import HelpOverlayState, render_help_overlay
from src.ui.log_overlay import LogOverlayState, render_log_overlay
from src.ui.regions import PLAY_BLIT_REGIONS, RegionBundle

if TYPE_CHECKING:
    from src.save.coordinator import SaveCoordinator
from src.systems.vore import VoreModalState


class GameEngine:
    """Owns world state, the ECS registry, and the main loop helpers.

    **Public surface** (stable for app, save, and most tests):

    - Construction: ``__init__``, ``from_run_snapshot``, ``build_run_snapshot``
    - Run lifecycle: ``new_game``, ``descend_floor``, ``initialize_floor``
    - Difficulty: ``difficulty_profile``, ``runes_per_floor``
    - Input: ``handle_event``, ``modal_blocks_quit``, ``can_issue_idle_command``
    - Rest: ``begin_rest``, ``cancel_rest``, ``rest_in_progress``, ``advance_rest_animation``
    - Autoexplore: ``begin_autoexplore``, ``cancel_autoexplore``, ``autoexplore_in_progress``, ``advance_autoexplore_animation``
    - Projectile: ``projectile_in_progress``, ``advance_projectile_animation``
    - Render: ``render``, ``play_log_console``

    **Internal** (prefixed ``_``; tests may still call these): floor/turn helpers,
    modal handlers, debug toggles. Implementation lives in ``engine_floor``,
    ``engine_turn``, and ``engine_input``.
    """

    def __init__(
        self,
        *,
        player_name: str = "Player",
        vore_content_prefs: VoreContentPreferences = DEFAULT_VORE_CONTENT_PREFS,
        difficulty_id: str | None = None,
        alternate_cv_mechanics: bool = False,
        ui_layout: UILayout | None = None,
        floor_prefetch: FloorPrefetch | None = None,
        skip_new_game: bool = False,
        save_coordinator: SaveCoordinator | None = None,
    ) -> None:
        self.player_name = player_name
        self.ui_layout = ui_layout or load_active_layout()
        self.world: Registry = Registry()
        self.game_map: GameMap = GameMap(MAP_WIDTH, MAP_HEIGHT)
        self.message_log = MessageLog()
        self._play_log_console: tcod.console.Console | None = None
        self.player: Entity | None = None
        self.player_turn_count = 0
        # player_turn_count when last successful/fizzle Come here! landed; -1 = never.
        self.last_come_here_turn = -1
        self.run_stats = RunStats()
        self.run_seed: int | None = None
        self.rng = random.Random()
        # Snapshot at new game: initiation filter only (not digestion follow-through).
        self.vore_content_prefs = vore_content_prefs
        # Run difficulty snapshot (Options value at New Game; immutable mid-run).
        from src.data.depth_scaling_config import validate_difficulty_id

        self.difficulty_id = validate_difficulty_id(difficulty_id)
        # Alternate CV rules snapshot (Options at New Game; immutable mid-run).
        self.alternate_cv_mechanics = bool(alternate_cv_mechanics)
        self.vore_modal = VoreModalState()
        self.digestion_modal = DigestionModalState()
        self.game_over = GameOverState()
        self.skipped_this_phase: set[Entity] = set()
        self.examine_state = ExamineState()
        self.dismiss_state = DismissState()
        self.ground_pickup_modal = GroundPickupModalState()
        self.inventory_modal = InventoryModalState()
        self.macguffin_discovery = MacguffinDiscovery()
        self.macguffin_victory_confirm = MacguffinVictoryConfirmState()
        self.screen_flash = ScreenFlashState()
        self.floor_depth = FLOOR_DEPTH_START
        self.level_warped = False
        self.depth_jump_start_depth: int | None = None
        self.arena_mode = False
        self.arena_enemy_id: str | None = None
        self.arena_enemy_entity: Entity | None = None
        self.arena_victory_active = False
        self.arena_victory_message = ""
        self._arena_victory_handler = None
        self.water_testing_mode = WATER_TESTING_MODE
        self.layout_archetype_force: str | None = LAYOUT_ARCHETYPE_FORCE
        self._debug_omniscient_vision = False
        self.close_door_pending = False
        self.floor_prefetch = floor_prefetch
        self.rest_session: RestSession | None = None
        self.autoexplore_session: AutoexploreSession | None = None
        self.projectile_session: ProjectileAnimSession | None = None
        self.pending_world_turn = False
        self._rest_attack_listener: Callable[[], None] | None = None
        self._autoexplore_attack_listener: Callable[[], None] | None = None
        self.log_overlay = LogOverlayState()
        self.help_overlay = HelpOverlayState()
        self.save_coordinator = save_coordinator
        self.past_runs_store: PastRunsStore | None = None
        if not skip_new_game:
            self.new_game()

    @classmethod
    def from_run_snapshot(
        cls,
        run: dict,
        *,
        floor_prefetch: FloorPrefetch | None = None,
    ) -> GameEngine:
        """Restore a run from an in-memory snapshot (PR1); file load uses PR2 store."""
        from src.save.codec import decode_vore_content_prefs
        from src.save.snapshot import apply_run_snapshot
        from src.ui.bootstrap import load_active_layout

        # Display layout comes from live settings (incl. 4K); App._load_saved_game
        # also re-resolves via _layout_for_run before PLAY.
        ui_layout = load_active_layout()
        engine = cls(
            player_name=str(run.get("player_name", "Player")),
            vore_content_prefs=decode_vore_content_prefs(
                run.get("vore_content_prefs", {"enabled": []})
            ),
            alternate_cv_mechanics=bool(run.get("alternate_cv_mechanics", False)),
            ui_layout=ui_layout,
            floor_prefetch=floor_prefetch,
            skip_new_game=True,
        )
        apply_run_snapshot(engine, run)
        engine._update_fov()
        return engine

    def build_run_snapshot(self) -> dict:
        """Capture full run state for save/load."""
        from src.save.snapshot import build_run_snapshot

        return build_run_snapshot(self)

    def new_game(
        self,
        *,
        seed: int | None = None,
        log_session_milestones: bool = True,
        start_depth: int = 1,
        level_warped: bool = False,
    ) -> None:
        """Reset the ECS world and generate a fresh dungeon."""
        engine_floor.new_game(
            self,
            seed=seed,
            log_session_milestones=log_session_milestones,
            start_depth=start_depth,
            level_warped=level_warped,
        )

    def _pack_blocked_while_engulfed(self) -> bool:
        return engine_input.pack_blocked_while_engulfed(self)

    def _player_on_stairs(self) -> bool:
        return engine_input.player_on_stairs(self)

    def descend_floor(self) -> None:
        """Generate a new floor, respawn entities, and preserve player + followers."""
        engine_floor.descend_floor(self)

    def _try_descend(self) -> bool:
        return engine_input.try_descend(self)

    def _spawn_player(self) -> None:
        """Place the player at the dungeon entrance."""
        engine_floor.spawn_player(self)

    def _dungeon_gen_kwargs(self, *, seed: int | None = None) -> dict:
        return engine_floor.dungeon_gen_kwargs(self, seed=seed)

    def difficulty_profile(self):
        """Active difficulty profile for this run (from snapshot id)."""
        return engine_floor.difficulty_profile(self)

    def runes_per_floor(self) -> int:
        """Rune count for this run (difficulty override, else floor_runes.json)."""
        return engine_floor.runes_per_floor(self)

    def _prefetch_params(
        self,
        *,
        seed: int | None = None,
        depth: int | None = None,
    ) -> PrefetchParams:
        return engine_floor.prefetch_params(self, seed=seed, depth=depth)

    def _take_or_generate_dungeon(self, *, seed: int | None = None) -> GameMap:
        """Consume a prefetched map when params match; otherwise generate synchronously."""
        return engine_floor.take_or_generate_dungeon(self, seed=seed)

    def _schedule_floor_prefetch(self) -> None:
        engine_floor.schedule_floor_prefetch(self)

    def _invalidate_floor_prefetch(self) -> None:
        engine_floor.invalidate_floor_prefetch(self)

    def _debug_log_floor_init_reject(self, attempt: int, reason: str) -> None:
        engine_floor.debug_log_floor_init_reject(attempt, reason)

    def _spawn_floor_population_and_runes(
        self,
        floor_depth: int,
        *,
        followers: list[Entity] | None = None,
    ) -> None:
        """Spawn NPCs, items, and runes. Raises RunePlacementError on rune failure."""
        engine_floor.spawn_floor_population_and_runes(
            self,
            floor_depth,
            followers=followers,
        )

    def initialize_floor(
        self,
        *,
        seed: int | None = None,
        mode: str = "new",
        start_depth: int = 1,
        followers: list[Entity] | None = None,
        log_session_milestones: bool = True,
    ) -> None:
        """Generate a map, populate entities, and place runes with regen on failure."""
        engine_floor.initialize_floor(
            self,
            seed=seed,
            mode=mode,
            start_depth=start_depth,
            followers=followers,
            log_session_milestones=log_session_milestones,
        )

    def _log_session_floor_entered(self, *, log_session_milestones: bool) -> None:
        engine_floor.log_session_floor_entered(
            self, log_session_milestones=log_session_milestones
        )

    def _initialize_floor_new(
        self,
        *,
        seed: int | None,
        start_depth: int = 1,
        log_session_milestones: bool = True,
    ) -> None:
        engine_floor.initialize_floor_new(
            self,
            seed=seed,
            start_depth=start_depth,
            log_session_milestones=log_session_milestones,
        )

    def _initialize_floor_descend(
        self,
        *,
        followers: list[Entity],
        log_session_milestones: bool = True,
    ) -> None:
        engine_floor.initialize_floor_descend(
            self,
            followers=followers,
            log_session_milestones=log_session_milestones,
        )

    def initialize_isolation_floor(
        self,
        *,
        depth: int,
        seed: int,
        log_session_milestones: bool = False,
    ) -> None:
        """Sim-only: generate one floor at ``depth`` without a full new-game flow."""
        engine_floor.initialize_floor_isolation(
            self,
            depth=depth,
            seed=seed,
            log_session_milestones=log_session_milestones,
        )

    def _update_fov(self) -> None:
        if self.player is None:
            return
        if self._debug_omniscient_vision:
            self.game_map.explored[:] = True
            self.game_map.visible[:] = True
            return
        pos = self.player.components[Position]
        update_fov(self.game_map, pos.x, pos.y)

    def _toggle_debug_omniscient_vision(self) -> None:
        engine_input.toggle_debug_omniscient_vision(self)

    def _run_world_turn(self) -> None:
        """World phase after a player action consumes a turn (monsters, FOV, etc.)."""
        engine_turn.run_world_turn(self)

    def _advance_vore_modal(self) -> None:
        engine_turn.advance_vore_modal(self)

    def _regen_blocked_by_digestion(self, entity: Entity) -> bool:
        return engine_turn.regen_blocked_by_digestion(entity)

    def _apply_natural_regen(self) -> None:
        engine_turn.apply_natural_regen(self)

    def _apply_npc_natural_regen(self) -> None:
        engine_turn.apply_npc_natural_regen(self)

    def _maybe_apply_player_digestion(self) -> bool:
        """Digestion tick while engulfed. Returns True when the world phase should wait."""
        return engine_turn.maybe_apply_player_digestion(self)

    def _advance_digestion_modal(self) -> None:
        engine_turn.advance_digestion_modal(self)

    def _complete_macguffin_victory(self) -> None:
        engine_turn.complete_macguffin_victory(self)

    def _end_rest_session(self) -> None:
        engine_turn.end_rest_session(self)

    def _end_autoexplore_session(self) -> None:
        engine_turn.end_autoexplore_session(self)

    def cancel_rest(self) -> None:
        """Stop an in-progress rest without logging an automatic end reason."""
        engine_turn.cancel_rest(self)

    def cancel_autoexplore(self) -> None:
        """Stop in-progress autoexplore without logging an automatic end reason."""
        engine_turn.cancel_autoexplore(self)

    def rest_in_progress(self) -> bool:
        return engine_turn.rest_in_progress(self)

    def autoexplore_in_progress(self) -> bool:
        return engine_turn.autoexplore_in_progress(self)

    def begin_rest(self) -> bool:
        """Start incremental rest if pre-checks pass."""
        return engine_turn.begin_rest(self)

    def begin_autoexplore(self) -> bool:
        """Start incremental autoexplore if pre-checks pass."""
        return engine_turn.begin_autoexplore_session(self)

    def advance_rest_animation(self) -> RestFrameResult:
        """Advance one rest animation frame (batched silent turns allowed)."""
        return engine_turn.advance_rest_animation(self)

    def advance_autoexplore_animation(self) -> AutoexploreFrameResult:
        """Advance one autoexplore animation frame (batched steps allowed)."""
        return engine_turn.advance_autoexplore_animation(self)

    def projectile_in_progress(self) -> bool:
        return engine_turn.projectile_in_progress(self)

    def advance_projectile_animation(self) -> ProjectileFrameResult:
        """Advance one Path projectile cosmetic frame."""
        return engine_turn.advance_projectile_animation(self)

    def _consume_player_turn(self) -> None:
        """Advance player turn counter, apply natural regen, fire hook, run world phase."""
        engine_turn.consume_player_turn(self)

    def can_issue_idle_command(self) -> bool:
        """True when quit/save/autosave are allowed (no blocking modals or automation)."""
        return (
            not self.modal_blocks_quit()
            and not self.rest_in_progress()
            and not self.autoexplore_in_progress()
            and not self.projectile_in_progress()
        )

    def _notify_save_after_player_turn(self) -> None:
        if self.save_coordinator is not None:
            self.save_coordinator.on_player_turn_end(self)

    def _notify_save_after_descent(self) -> None:
        if self.save_coordinator is not None:
            self.save_coordinator.on_descend_floor(self)

    def _handle_inventory_modal_event(self, event: tcod.event.Event) -> EngineEventResult:
        return engine_input.handle_inventory_modal_event(self, event)

    def _handle_ground_pickup_modal_event(self, event: tcod.event.Event) -> EngineEventResult:
        return engine_input.handle_ground_pickup_modal_event(self, event)

    def _handle_examine_description_event(self, event: tcod.event.Event) -> EngineEventResult:
        return engine_input.handle_examine_description_event(self, event)

    def _handle_examine_cursor_event(self, event: tcod.event.Event) -> EngineEventResult:
        return engine_input.handle_examine_cursor_event(self, event)

    def _handle_dismiss_cursor_event(self, event: tcod.event.Event) -> EngineEventResult:
        return engine_input.handle_dismiss_cursor_event(self, event)

    def _handle_gameplay_event(self, event: tcod.event.Event) -> EngineEventResult:
        return engine_input.handle_gameplay_event(self, event)

    def modal_blocks_quit(self) -> bool:
        return engine_input.modal_blocks_quit(self)

    def _log_overlay_metrics(self) -> tuple[int, int]:
        return engine_input.log_overlay_metrics(self)

    def _handle_meta_overlay_events(self, event: tcod.event.Event) -> bool:
        return engine_input.handle_meta_overlay_events(self, event)

    def handle_event(self, event: tcod.event.Event) -> EngineEventResult:
        """Process gameplay input. Ctrl+Q is handled by the app shell."""
        return engine_input.handle_event(self, event)

    def _toggle_water_testing_mode(self) -> None:
        engine_input.toggle_water_testing_mode(self)

    def _try_close_door(self, direction: tuple[int, int]) -> bool:
        return engine_input.try_close_door(self, direction)

    def _door_tile_blocked(self, x: int, y: int) -> bool:
        return engine_input.door_tile_blocked(self, x, y)

    def _cycle_layout_archetype_force(self) -> None:
        engine_input.cycle_layout_archetype_force(self)

    def _toggle_stunned_debug(self) -> None:
        engine_input.toggle_stunned_debug(self)

    @property
    def play_log_console(self) -> tcod.console.Console | None:
        """Message log sub-console from the latest play render (for TTF composite)."""
        return self._play_log_console

    def render(
        self,
        console: tcod.console.Console,
        *,
        blit_message_log: bool = True,
        draw_digestion_modal: bool = True,
        draw_vore_modal: bool = True,
        draw_examine_description: bool = True,
        draw_inventory_modal: bool = True,
        draw_ground_pickup_modal: bool = True,
        draw_macguffin_victory: bool = True,
        draw_game_over_body: bool = True,
        draw_game_over: bool = True,
    ) -> None:
        """Draw the current frame.

        ``draw_*`` flags: when False, skip CP437 modal text so present
        can composite proportional UI.
        """
        console.clear()
        if self.help_overlay.active:
            render_help_overlay(console, self.help_overlay)
            return

        if self.log_overlay.active:
            render_log_overlay(
                console,
                self.message_log.entries(),
                self.log_overlay,
                layout=self.ui_layout,
            )
            return

        regions = RegionBundle.for_play(
            self.ui_layout,
            console.width,
            console.height,
        )
        map_console = regions.console("map_viewport")
        map_console.clear()
        log_console = regions.console("message_log")
        log_console.clear()
        side_console = regions.console("sidebar")
        side_console.clear()
        corner_console = regions.console("status_corner")
        corner_console.clear()

        player_pos = (
            self.player.components[Position]
            if self.player is not None
            else None
        )
        if player_pos is not None:
            camera = MapCamera.from_layout(
                self.ui_layout,
                player_pos.x,
                player_pos.y,
                map_w=MAP_WIDTH,
                map_h=MAP_HEIGHT,
            )
        else:
            tiles = self.ui_layout.map_viewport_tiles
            camera = MapCamera(0, 0, tiles.w, tiles.h)

        engulfed = self.player is not None and Engulfed in self.player.tags
        render_map(map_console, self.game_map, blind=engulfed, camera=camera)
        render_entities(
            map_console,
            self.world,
            self.game_map,
            blind=engulfed,
            player=self.player,
            camera=camera,
        )
        if self.projectile_session is not None and self.projectile_session.active:
            from src.systems.projectile_anim import render_projectile

            render_projectile(
                map_console,
                session=self.projectile_session,
                game_map=self.game_map,
                camera=camera,
            )
        if engulfed and self.player is not None:
            render_engulfed_overlay(
                map_console,
                self.game_map,
                player_pos,
                camera=camera,
            )
        render_screen_flash(
            map_console,
            state=self.screen_flash,
            player_pos=player_pos,
            camera=camera,
        )

        fighter: Fighter | None = None
        inventory: Inventory | None = None
        equip: EquipState | None = None
        stunned = False
        if self.player is not None:
            fighter = self.player.components.get(Fighter)
            inventory = self.player.components.get(Inventory)
            equip = self.player.components.get(EquipState)
            stunned = Stunned in self.player.tags

        render_sidebar_player(
            side_console,
            player_name=self.player_name,
            fighter=fighter,
            sidebar=self.ui_layout.sidebar,
        )
        render_sidebar_npcs(
            side_console,
            self.world,
            self.game_map,
            sidebar=self.ui_layout.sidebar,
        )
        render_message_log_panel(
            log_console,
            self.message_log.entries(),
            max_lines=self.ui_layout.message_log_lines,
        )
        self._play_log_console = log_console
        player = self.player
        prog = (
            player.components.get(PlayerProgression)
            if player is not None
            else None
        )
        effect_rows = ()
        if player is not None:
            pe = player.components.get(PlayerEffects)
            if pe is not None:
                effect_rows = player_effects_extra_rows(
                    pe,
                    max_width=corner_console.width,
                )
        extra_rows = effect_rows + progression_extra_rows(
            prog or PlayerProgression(),
            max_width=corner_console.width,
        )
        render_status_corner(
            corner_console,
            PlayerStatusEffects(
                floor_depth=self.floor_depth,
                stunned=stunned,
                engulfed=engulfed,
                extra_rows=extra_rows,
            ),
        )

        blit_regions = PLAY_BLIT_REGIONS
        if not blit_message_log:
            blit_regions = PLAY_BLIT_REGIONS - frozenset({"message_log"})
            log_rect = regions.placement("message_log")
            console.draw_rect(
                log_rect.x,
                log_rect.y,
                log_rect.w,
                log_rect.h,
                ch=0,
                fg=None,
                bg=MESSAGE_LOG_BACKGROUND,
            )
        regions.blit_to_root(console, names=blit_regions)
        if self.examine_state.active and not self.examine_state.showing_description:
            render_examine_cursor(
                map_console,
                self.examine_state.cursor,
                self.game_map,
                camera=camera,
            )
            regions.blit_to_root(console, names=frozenset({"map_viewport"}))
            regions.blit_play_chrome(console)
        elif self.dismiss_state.active:
            render_examine_cursor(
                map_console,
                self.dismiss_state.cursor,
                self.game_map,
                camera=camera,
            )
            regions.blit_to_root(console, names=frozenset({"map_viewport"}))
            regions.blit_play_chrome(console)
        if self.game_over.active and draw_game_over:
            assert self.game_over.ending is not None
            render_game_over(
                console,
                player_name=self.game_over.player_name,
                ending=self.game_over.ending,
                monsters_defeated=self.game_over.monsters_defeated,
                runes_collected=self.game_over.runes_collected,
                depth=self.game_over.depth,
                draw_body=draw_game_over_body,
            )
        elif self.digestion_modal.active and draw_digestion_modal:
            render_digestion_modal(console, text=self.digestion_modal.line)
        elif self.vore_modal.active and draw_vore_modal:
            render_vore_modal(console, text=self.vore_modal.current_line())
        elif self.inventory_modal.active:
            if self.inventory_modal.mode in (
                InventoryModalMode.EVOKE_TARGET,
                InventoryModalMode.THROW_TARGET,
                InventoryModalMode.BLINK_TARGET,
            ):
                render_inventory_modal(
                    map_console,
                    state=self.inventory_modal,
                    inventory=inventory,
                    equip=equip,
                    player=self.player,
                    game_map=self.game_map,
                    camera=camera,
                )
                regions.blit_to_root(console, names=frozenset({"map_viewport"}))
                regions.blit_play_chrome(console)
            elif draw_inventory_modal:
                render_inventory_modal(
                    console,
                    state=self.inventory_modal,
                    inventory=inventory,
                    equip=equip,
                    player=self.player,
                    game_map=self.game_map,
                )
        elif self.ground_pickup_modal.active and draw_ground_pickup_modal:
            render_ground_pickup_modal(console, state=self.ground_pickup_modal)
        elif self.macguffin_victory_confirm.active and draw_macguffin_victory:
            render_macguffin_victory_confirm(
                console,
                self.macguffin_victory_confirm,
            )
        elif self.examine_state.showing_description and draw_examine_description:
            render_centered_modal(console, text=self.examine_state.description_text)

__all__ = ["EngineEventResult", "GameEngine"]
