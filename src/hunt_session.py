"""Hunt session: paddock, tank body, cone FOV, AUT."""

from __future__ import annotations

import random
from collections.abc import Callable
from enum import Enum, auto

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym

from src import messages as msg
from src.aut import AutScheduler
from src.hunt_aut import format_aut, load_hunt_aut_costs, tenths
from src.hunt_clock import (
    RingState,
    center_weight,
    load_hunt_clock,
    ring_state,
)
from src.hunt_combat import (
    chebyshev,
    load_hunt_combat,
    preview_shot,
    trace_projectile,
    weapon_combat,
)
from src.hunt_loss import (
    POST_SWALLOW_ENDOSOMA,
    HuntNarrativeDecks,
    attack_angle,
    load_hunt_loss,
    pick_post_belly_lines,
    pick_swallow_lines,
)
from src.hunt_facing import (
    FACING_DELTAS,
    angular_delta_deg,
    facing_delta,
    facing_name,
    facing_toward,
    heading_from_facing,
    heading_matches_facing,
    heading_toward,
    nearest_eight_facing,
    next_eight_facing,
    rotate_facing,
    tile_along_heading,
    yaw_step_degrees,
)
from src.hunt_modals import (
    MODAL_FOOTER,
    belly_fade_t,
    fill_loss_void,
    render_belly_overlay,
    render_centered_modal,
)
from src.hunt_fov import line_visible, visible_tiles
from src.hunt_help import help_toggle_event, render_hunt_help
from src.hunt_input import TankCommand, parse_tank_command
from src.hunt_panel import hunter_stat_lines, map_view_size, raptor_readout, render_hunt_panel
from src.hunt_projectile import (
    HuntDartAnim,
    PendingHuntShot,
    advance_dart,
    begin_dart,
    dart_draw_tiles,
    load_hunt_projectile,
)
from src.input_handlers import DIRECTION_KEYS, MODAL_ADVANCE_KEYS, is_help_open_key
from src.hunt_map import (
    HuntMap,
    HuntTerrain,
    generate_paddock,
    is_mud,
    load_paddock_config,
    nearest_walkable,
    vision_profile_for,
)
from src.hunt_stance import (
    AIM_FOCUS,
    AIM_NONE,
    Gait,
    raise_aim,
)
from src.hunt_training import (
    TRAINING_MENU_KEY,
    DummyScript,
    TrainingLayout,
    TrainingMenuState,
    dummy_act,
    generate_training_arena,
    handle_training_menu_event,
    render_training_menu,
    selectable_menu_indices,
    teleport_raptor,
    weapon_by_id,
)
from src.hunt_ai import RaptorSense, raptor_act
from src.message_log import MessageLog, MessageCategory
from src.hunt_difficulty import hunt_tuning
from src.hunt_fatigue import load_hunt_fatigue, vision_penalty as fatigue_vision
from src.hunt_raptor import (
    RAPTOR_ACTOR,
    HuntRaptor,
    pick_raptor_spawn,
)
from src.hunt_weather import (
    MudPrint,
    SoundMark,
    fade_audio,
    load_hunt_weather,
    move_sound_chance,
    rain_level_at,
)
from src.text import cp437_safe

HUNTER_ACTOR = "hunter"

_TERRAIN_GLYPH: dict[HuntTerrain, str] = {
    HuntTerrain.WALL: "#",
    HuntTerrain.OPEN: "'",
    HuntTerrain.MUD: ".",
    HuntTerrain.GRASS: ",",
    HuntTerrain.BUSH: ",",
    HuntTerrain.TREE: "T",
}

_TERRAIN_FG_SEEN: dict[HuntTerrain, tuple[int, int, int]] = {
    HuntTerrain.WALL: (70, 85, 70),
    HuntTerrain.OPEN: (90, 130, 55),
    HuntTerrain.MUD: (110, 80, 45),
    HuntTerrain.GRASS: (50, 120, 50),
    HuntTerrain.BUSH: (40, 100, 45),
    HuntTerrain.TREE: (30, 90, 35),
}

_TERRAIN_FG_KNOWN: dict[HuntTerrain, tuple[int, int, int]] = {
    HuntTerrain.WALL: (35, 42, 35),
    HuntTerrain.OPEN: (40, 55, 28),
    HuntTerrain.MUD: (50, 38, 24),
    HuntTerrain.GRASS: (24, 50, 24),
    HuntTerrain.BUSH: (20, 45, 22),
    HuntTerrain.TREE: (16, 40, 18),
}


class HuntAction(Enum):
    NONE = auto()
    LEAVE = auto()


class HuntMode(Enum):
    PLAY = auto()
    TARGETING = auto()
    AIM_PICK = auto()
    WIN_BASK = auto()
    WIN_RESULTS = auto()
    TIME_OVER = auto()
    SWALLOW = auto()
    BELLY = auto()
    DIGEST = auto()
    GAME_OVER = auto()


@attrs.define
class HuntSession:
    hunter_name: str
    weapon_id: str
    weapon_name: str
    difficulty_id: str = "normal"
    seed: int | None = None
    paddock: HuntMap | None = None
    player_x: int = 0
    player_y: int = 0
    facing: int = 0
    gait: Gait = Gait.WALK
    aim_depth: int = AIM_NONE
    aim_heading_deg: float | None = None
    raptor: HuntRaptor | None = None
    rng: random.Random | None = None
    ammo: int = 0
    mode: HuntMode = HuntMode.PLAY
    cursor_x: int = 0
    cursor_y: int = 0
    notice: str = ""
    win_lines: tuple[str, ...] = ()
    prints: list[MudPrint] = attrs.field(factory=list)
    sound_marks: list[SoundMark] = attrs.field(factory=list)
    raptor_heard_xy: tuple[int, int] | None = None
    raptor_gunshot_xy: tuple[int, int] | None = None
    raptor_under_fire: bool = False
    message_log: MessageLog = attrs.field(factory=MessageLog)
    rain_audio: float = 0.25
    hunter_ring: float = 0.0
    raptor_ring: float = 0.0
    time_over_win: bool = False
    swallow_angle: str = ""
    belly_turns: int = 0
    belly_cam_x: int | None = None
    belly_cam_y: int | None = None
    shots_fired: int = 0
    shots_landed: int = 0
    shots_perfect: int = 0
    shots_one_shot: int = 0
    outcome: str | None = None
    stats_recorded: bool = False
    help_open: bool = False
    restoring: bool = False
    post_swallow: Callable[[], str] | None = None
    narrative_decks: HuntNarrativeDecks | None = None
    scheduler: AutScheduler = attrs.field(factory=AutScheduler)
    visible: set[tuple[int, int]] = attrs.field(factory=set)
    last_known_x: int | None = None
    last_known_y: int | None = None
    run_fatigue: int = 0
    fatigue_recovery_streak: int = 0
    dart: HuntDartAnim | None = None
    pending_shot: PendingHuntShot | None = None
    training: bool = False
    training_layout: TrainingLayout | None = None
    dummy_script: DummyScript = DummyScript.NORMAL
    dummy_resume: DummyScript = DummyScript.NORMAL
    dummy_gait: Gait | None = None
    dummy_patrol_i: int = 0
    dummy_patrol_dir: int = 1
    training_menu: TrainingMenuState | None = None

    def __attrs_post_init__(self) -> None:
        if self.restoring:
            self.restoring = False
            if self.rng is None:
                self.rng = random.Random(self.seed)
            if self.aim_depth > AIM_NONE and self.aim_heading_deg is not None:
                self._sync_facing_to_aim()
            self.refresh_fov()
            self._refresh_raptor_fov()
            return
        if self.seed is None:
            self.seed = random.randrange(1, 2**31 - 1)
        if self.paddock is None:
            if self.training:
                self.paddock, layout = generate_training_arena()
                self.training_layout = layout
            else:
                self.paddock = generate_paddock(self.seed)
        cfg = load_paddock_config()
        if self.training and self.training_layout is not None:
            if self.player_x == 0 and self.player_y == 0:
                self.player_x, self.player_y = self.training_layout.hunter_xy
        elif self.player_x == 0 and self.player_y == 0:
            self.player_x, self.player_y = nearest_walkable(
                self.paddock,
                self.paddock.center_x,
                self.paddock.center_y,
            )
        if self.rng is None:
            self.rng = random.Random(self.seed)
        self.scheduler.register(HUNTER_ACTOR)
        combat = load_hunt_combat()
        if self.ammo <= 0:
            self.ammo = weapon_combat(self.weapon_id).ammo
        if self.raptor is None:
            if self.training and self.training_layout is not None:
                rx, ry = self.training_layout.raptor_xy
                rf = self.training_layout.raptor_facing
            else:
                rx, ry, rf = pick_raptor_spawn(
                    self.paddock, self.player_x, self.player_y, self.rng,
                )
            self.raptor = HuntRaptor(
                x=rx, y=ry, facing=rf,
                hp=combat.raptor_max_hp, max_hp=combat.raptor_max_hp,
            )
        self.scheduler.register(RAPTOR_ACTOR)
        self.rain_audio = rain_level_at(0.0).audio
        self.refresh_fov()
        self._refresh_raptor_fov()

    @property
    def map(self) -> HuntMap:
        assert self.paddock is not None
        return self.paddock

    @property
    def world_aut(self) -> float:
        return tenths(self.scheduler.world_aut)

    def rain(self):
        cycle = hunt_tuning(self.difficulty_id).rain_cycle_aut
        return rain_level_at(self.world_aut, cycle_aut=cycle)

    def refresh_fov(self) -> None:
        cfg = load_paddock_config()
        profile = vision_profile_for(
            gait=self.gait.value,
            aim_depth=self.aim_depth,
            cfg=cfg,
            weapon_id=self.weapon_id,
        )
        penalty = self.rain().hunter_vision_penalty + fatigue_vision(self.run_fatigue)
        cone = max(2, profile.cone_range - penalty)
        heading = self.aim_heading_deg if self.aim_depth > AIM_NONE else None
        close_blind = profile.close_blind if profile.close_blind > 0 else (
            self.aim_depth if self.aim_depth > AIM_NONE else 0
        )
        grass = self.rain().hunter_grass_see
        if profile.line and heading is not None:
            self.visible = line_visible(
                self.map,
                origin_x=self.player_x,
                origin_y=self.player_y,
                heading_deg=heading,
                cone_range=cone,
                close_blind=close_blind,
                grass_see_through=grass,
            )
        else:
            self.visible = visible_tiles(
                self.map,
                origin_x=self.player_x,
                origin_y=self.player_y,
                facing=self.facing,
                cone_range=cone,
                half_degrees=profile.cone_half_degrees,
                heading_deg=heading,
                close_blind=close_blind,
                grass_see_through=grass,
            )
        self._update_last_known()

    def _update_last_known(self) -> None:
        """Last hunter-seen raptor tile. Drop the mark if that tile is in FOV and empty."""
        if self.raptor is None:
            return
        if self.raptor_in_sight():
            self.last_known_x = self.raptor.x
            self.last_known_y = self.raptor.y
            return
        if self.last_known_x is None or self.last_known_y is None:
            return
        if (self.last_known_x, self.last_known_y) in self.visible:
            self.last_known_x = None
            self.last_known_y = None

    def _refresh_raptor_fov(self) -> None:
        if self.raptor is not None:
            self.raptor.refresh_fov(
                self.map,
                range_penalty=self.rain().raptor_vision_penalty,
                grass_see_through=self.rain().raptor_grass_see,
                cone_bonus=hunt_tuning(self.difficulty_id).raptor_cone_bonus,
            )

    def _set_gait(self, gait: Gait) -> None:
        self.gait = gait

    def _slow_if_running(self) -> None:
        """Sidestep/back while running drops to walk (does not clear aim — run already did)."""
        if self.gait is Gait.RUN:
            self.gait = Gait.WALK

    def clock_remaining(self) -> float:
        cfg = load_hunt_clock()
        return tenths(max(0.0, cfg.duration_aut - self.world_aut))

    def ring_hud(self) -> RingState:
        cfg = load_hunt_clock()
        return ring_state(self.hunter_ring, self.raptor_ring, cfg.definitely_margin)

    def _accrue_ring(self, dt: float) -> None:
        if dt <= 0.0:
            return
        self.hunter_ring += dt * center_weight(self.map, self.player_x, self.player_y)
        if self.raptor is not None:
            self.raptor_ring += dt * center_weight(self.map, self.raptor.x, self.raptor.y)

    def post_swallow_stance(self) -> str:
        from src.hunt_loss import normalize_post_swallow

        if self.post_swallow is None:
            return "digest"
        return normalize_post_swallow(self.post_swallow())

    def _decks(self) -> HuntNarrativeDecks:
        if self.narrative_decks is None:
            self.narrative_decks = HuntNarrativeDecks()
        return self.narrative_decks

    def _loss_rng(self) -> random.Random:
        return self.rng if self.rng is not None else random.Random(0)

    def begin_swallow(self) -> None:
        if self.raptor is None:
            return
        if self.mode not in (HuntMode.PLAY, HuntMode.TARGETING, HuntMode.AIM_PICK):
            return
        self.swallow_angle = attack_angle(
            self.player_x, self.player_y, self.facing,
            self.raptor.x, self.raptor.y,
        )
        self.win_lines = pick_swallow_lines(
            self.swallow_angle,
            stance=self.post_swallow_stance(),
            decks=self._decks(),
            rng=self._loss_rng(),
        )
        self.belly_turns = 0
        self.mode = HuntMode.SWALLOW
        self.notice = ""

    def enter_belly(self) -> None:
        """Hunter is inside; snap to the raptor tile so the ring sits on it."""
        if self.raptor is not None:
            self.player_x = self.raptor.x
            self.player_y = self.raptor.y
            self.belly_cam_x = self.raptor.x
            self.belly_cam_y = self.raptor.y
        else:
            self.belly_cam_x = self.player_x
            self.belly_cam_y = self.player_y
        self.mode = HuntMode.BELLY
        self.notice = ""

    def _belly_maybe_walk(self) -> None:
        """50% idle, 50% a random walkable step; hunter rides along."""
        if self.raptor is None or self.rng is None:
            return
        cfg = load_hunt_loss()
        if self.rng.random() >= cfg.belly_step_chance:
            return
        spots: list[tuple[int, int, int]] = []
        for i, (dx, dy) in enumerate(FACING_DELTAS):
            nx, ny = self.raptor.x + dx, self.raptor.y + dy
            if self.map.walkable(nx, ny):
                spots.append((nx, ny, i))
        if not spots:
            return
        nx, ny, facing = self.rng.choice(spots)
        ox, oy = self.raptor.x, self.raptor.y
        self.raptor.x, self.raptor.y = nx, ny
        self.raptor.facing = facing
        self.raptor.record_motion(ox, oy)
        self.player_x, self.player_y = nx, ny
        self._leave_print(nx, ny, facing, "raptor")

    def maybe_raptor_finish(self) -> bool:
        """True if Chebyshev 1 and the raptor currently sees the hunter."""
        if self.raptor is None or self.raptor.tranquilized:
            return False
        if self.mode not in (HuntMode.PLAY, HuntMode.TARGETING, HuntMode.AIM_PICK):
            return False
        if chebyshev(self.raptor.x, self.raptor.y, self.player_x, self.player_y) != 1:
            return False
        self._refresh_raptor_fov()
        if not self.raptor.sees(self.player_x, self.player_y):
            return False
        self.begin_swallow()
        return True

    def _check_clock(self) -> None:
        if self.mode is not HuntMode.PLAY:
            return
        if self.raptor is not None and self.raptor.tranquilized:
            return
        cfg = load_hunt_clock()
        if self.world_aut + 1e-9 < cfg.duration_aut:
            return
        won = self.ring_hud() is RingState.HUNTER_WINNING
        self.time_over_win = won
        self.outcome = "time_win" if won else "time_loss"
        self.mode = HuntMode.TIME_OVER
        if won:
            self.win_lines = (
                msg.hunt_you_win(),
                msg.hunt_time_win(),
                self.ring_hud().value,
            )
        else:
            self.win_lines = (
                msg.hunt_time_loss(),
                self.ring_hud().value,
            )

    def _add_run_fatigue(self) -> None:
        cfg = load_hunt_fatigue()
        self.run_fatigue = min(cfg.max_stack, self.run_fatigue + cfg.per_run_step)

    def _tick_fatigue(self, *, run_step: bool, quick_step: bool, recover: bool) -> None:
        if run_step:
            self._add_run_fatigue()
            self.fatigue_recovery_streak = 0
            return
        if quick_step:
            self.fatigue_recovery_streak = 0
            return
        if not recover or self.run_fatigue <= 0:
            return
        cfg = load_hunt_fatigue()
        need = max(1, cfg.recovery_turns)
        self.fatigue_recovery_streak += 1
        if self.fatigue_recovery_streak >= need:
            self.run_fatigue -= 1
            self.fatigue_recovery_streak = 0

    def _note(self, text: str) -> None:
        if text:
            self.notice = text
            self.message_log.add(text, category=MessageCategory.ROUTINE)

    def _spend(
        self,
        cost: float,
        *,
        run_step: bool = False,
        quick_step: bool = False,
        recover: bool = False,
    ) -> None:
        dt = tenths(cost * hunt_tuning(self.difficulty_id).hunter_aut_mult)
        self._tick_fatigue(
            run_step=run_step, quick_step=quick_step, recover=recover,
        )
        self.scheduler.commit_action(HUNTER_ACTOR, dt)
        self._pump_world()
        self._accrue_ring(dt)
        self._check_clock()

    def raptor_in_sight(self) -> bool:
        if self.raptor is None:
            return False
        return (self.raptor.x, self.raptor.y) in self.visible

    def try_step(self, dx: int, dy: int) -> bool:
        nx, ny = self.player_x + dx, self.player_y + dy
        if not self.map.walkable(nx, ny):
            return False
        if self.raptor is not None and nx == self.raptor.x and ny == self.raptor.y:
            return False
        ox, oy = self.player_x, self.player_y
        self.player_x = nx
        self.player_y = ny
        self._leave_print(nx, ny, self.facing, "hunter")
        self._emit_move_sound(ox, oy, source="hunter")
        return True

    def _leave_print(self, x: int, y: int, facing: int, owner: str) -> None:
        if not is_mud(self.map.terrain_at(x, y)):
            return
        ttl = self.rain().print_ttl
        self.prints.append(
            MudPrint(
                x=x, y=y, facing=facing, owner=owner,
                placed_aut=self.world_aut, ttl=ttl,
            )
        )

    def _emit_move_sound(self, x: int, y: int, *, source: str) -> None:
        """`x,y` is the tile left (FROM). Chance is gait then rain delta."""
        if self.rng is None:
            return
        level = self.rain()
        gait = self.gait.value if source == "hunter" else (
            self.raptor.gait.value if self.raptor is not None else "walk"
        )
        chance = move_sound_chance(gait, level.level_id)
        if chance <= 0.0 or self.rng.random() > chance:
            return
        if source == "hunter":
            if self.raptor is None:
                return
            if chebyshev(self.raptor.x, self.raptor.y, x, y) <= level.hear_range:
                self.raptor_heard_xy = (x, y)
            return
        if chebyshev(self.player_x, self.player_y, x, y) > level.hear_range:
            return
        self.sound_marks.append(
            SoundMark(x=x, y=y, false_alarm=False, expires_aut=self.world_aut + 2.0)
        )

    def _expire_clues(self) -> None:
        now = self.world_aut
        self.prints = [p for p in self.prints if now - p.placed_aut <= p.ttl]
        self.sound_marks = [s for s in self.sound_marks if s.expires_aut > now]

    def _maybe_false_alarm(self) -> None:
        if self.rng is None:
            return
        if self.notice.startswith("You fire"):
            return
        level = self.rain()
        if self.rng.random() >= level.false_alarm_chance:
            return
        walk = [
            (x, y)
            for y in range(self.map.height)
            for x in range(self.map.width)
            if self.map.walkable(x, y)
            and chebyshev(self.player_x, self.player_y, x, y) <= level.hear_range
            and (x, y) != (self.player_x, self.player_y)
        ]
        if not walk:
            return
        x, y = self.rng.choice(walk)
        self.sound_marks.append(
            SoundMark(x=x, y=y, false_alarm=True, expires_aut=self.world_aut + 2.0)
        )
        if self.raptor is not None:
            self.raptor_heard_xy = (x, y)

    def _tick_weather(self) -> None:
        cfg = load_hunt_weather()
        target = self.rain().audio
        self.rain_audio = fade_audio(self.rain_audio, target, cfg.audio_fade)
        self._expire_clues()

    def drop_aim(self) -> None:
        if self.aim_depth == AIM_NONE and self.aim_heading_deg is None:
            return
        heading = self.aim_heading_deg
        if heading is None:
            heading = heading_from_facing(self.facing)
        self.facing = nearest_eight_facing(heading, self.rng)
        self.aim_heading_deg = None
        self.aim_depth = AIM_NONE
        if self.mode is HuntMode.AIM_PICK:
            self.mode = HuntMode.PLAY

    def rotate_body(self, steps_clockwise: int) -> None:
        """8-tick tank rotate. Conventional turn while aimed drops aim and snaps."""
        if self.aim_depth > AIM_NONE or self.aim_heading_deg is not None:
            heading = self.aim_heading_deg
            if heading is None:
                heading = heading_from_facing(self.facing)
            self.facing = next_eight_facing(heading, steps_clockwise)
            self.aim_heading_deg = None
            self.aim_depth = AIM_NONE
            if self.mode is HuntMode.AIM_PICK:
                self.mode = HuntMode.PLAY
            return
        self.facing = rotate_facing(self.facing, steps_clockwise)

    def _aim_pick_tiles(self) -> set[tuple[int, int]]:
        return {
            xy for xy in self.visible
            if xy != (self.player_x, self.player_y)
        }

    def enter_aim_pick(self) -> None:
        self.refresh_fov()
        tiles = self._aim_pick_tiles()
        if not tiles:
            return
        self.mode = HuntMode.AIM_PICK
        self.notice = msg.hunt_aim_pick()
        self.cursor_x, self.cursor_y = self._preferred_aim_cursor(tiles)
        self._clamp_aim_cursor()

    def _preferred_aim_cursor(self, tiles: set[tuple[int, int]]) -> tuple[int, int]:
        if self.raptor is not None and (self.raptor.x, self.raptor.y) in tiles:
            return self.raptor.x, self.raptor.y
        facing_h = heading_from_facing(self.facing)

        def score(xy: tuple[int, int]) -> tuple[float, int]:
            ang = heading_toward(self.player_x, self.player_y, xy[0], xy[1])
            dist = chebyshev(self.player_x, self.player_y, xy[0], xy[1])
            return (angular_delta_deg(ang, facing_h), -dist)

        return min(tiles, key=score)

    def confirm_aim_pick(self) -> None:
        tiles = self._aim_pick_tiles()
        if (self.cursor_x, self.cursor_y) not in tiles:
            return
        self.aim_heading_deg = heading_toward(
            self.player_x, self.player_y, self.cursor_x, self.cursor_y,
        )
        self.aim_depth = AIM_FOCUS
        self._sync_facing_to_aim()
        self.mode = HuntMode.PLAY
        self.notice = ""
        self._spend(load_hunt_aut_costs().aim)
        self.refresh_fov()

    def _sync_facing_to_aim(self) -> None:
        if self.aim_heading_deg is None:
            return
        self.facing = nearest_eight_facing(self.aim_heading_deg, self.rng)

    def yaw_aim(self, *, clockwise: bool) -> None:
        if self.aim_depth <= AIM_NONE:
            return
        if self.aim_heading_deg is None:
            self.aim_heading_deg = heading_from_facing(self.facing)
        cfg = load_paddock_config()
        profile = vision_profile_for(
            gait=self.gait.value,
            aim_depth=self.aim_depth,
            cfg=cfg,
            weapon_id=self.weapon_id,
        )
        step = yaw_step_degrees(profile.cone_half_degrees)
        sign = 1.0 if clockwise else -1.0
        self.aim_heading_deg = (self.aim_heading_deg + sign * step) % 360.0
        self._sync_facing_to_aim()
        self.refresh_fov()

    def _clamp_aim_cursor(self) -> None:
        tiles = self._aim_pick_tiles()
        if (self.cursor_x, self.cursor_y) in tiles:
            return
        if not tiles:
            return
        best = min(
            tiles,
            key=lambda xy: chebyshev(self.cursor_x, self.cursor_y, xy[0], xy[1]),
        )
        self.cursor_x, self.cursor_y = best

    def enter_targeting(self) -> None:
        self.mode = HuntMode.TARGETING
        self.notice = ""
        if self.raptor is not None and self.raptor_in_sight():
            self.cursor_x, self.cursor_y = self.raptor.x, self.raptor.y
        else:
            heading = (
                self.aim_heading_deg
                if self.aim_depth > AIM_NONE and self.aim_heading_deg is not None
                else heading_from_facing(self.facing)
            )
            placed = False
            for dist in range(1, 9):
                tx, ty = tile_along_heading(
                    self.player_x, self.player_y, heading, dist,
                )
                if (tx, ty) != (self.player_x, self.player_y):
                    self.cursor_x, self.cursor_y = tx, ty
                    placed = True
                    break
            if not placed:
                dx, dy = facing_delta(self.facing)
                self.cursor_x = self.player_x + dx
                self.cursor_y = self.player_y + dy
        self._clamp_cursor()

    def _clamp_cursor(self) -> None:
        self.cursor_x = max(0, min(self.cursor_x, self.map.width - 1))
        self.cursor_y = max(0, min(self.cursor_y, self.map.height - 1))

    def targeting_preview(self):
        weapon = weapon_combat(self.weapon_id)
        raptor_xy = None if self.raptor is None else (self.raptor.x, self.raptor.y)
        trace = trace_projectile(
            self.map, self.player_x, self.player_y, self.cursor_x, self.cursor_y,
            raptor_xy=raptor_xy,
            max_range=weapon.max_range,
        )
        if trace.hit_raptor and self.raptor is not None:
            rng = chebyshev(self.player_x, self.player_y, self.raptor.x, self.raptor.y)
            shot_heading = heading_toward(
                self.player_x, self.player_y, self.raptor.x, self.raptor.y,
            )
        else:
            rng = chebyshev(self.player_x, self.player_y, self.cursor_x, self.cursor_y)
            shot_heading = heading_toward(
                self.player_x, self.player_y, self.cursor_x, self.cursor_y,
            )
        raptor = self.raptor
        return preview_shot(
            weapon,
            range_chebyshev=rng,
            aim_depth=self.aim_depth,
            hunter_running=False,
            hunter_fatigue=self.run_fatigue,
            raptor_visible=self.raptor_in_sight(),
            ammo=self.ammo,
            rain_id=self.rain().level_id,
            raptor_moving=raptor is not None and raptor.last_move_facing is not None,
            raptor_facing=None if raptor is None else raptor.facing,
            raptor_move_facing=None if raptor is None else raptor.last_move_facing,
            shot_heading=shot_heading,
        ), trace

    def confirm_shot(self) -> None:
        if self.ammo <= 0:
            self.notice = msg.hunt_no_ammo()
            return
        if self.cursor_x == self.player_x and self.cursor_y == self.player_y:
            self.notice = msg.hunt_shot_miss()
            return
        shot_heading = heading_toward(
            self.player_x, self.player_y, self.cursor_x, self.cursor_y,
        )
        if not heading_matches_facing(shot_heading, self.facing):
            self.notice = msg.hunt_fire_wrong_facing()
            return
        preview, trace = self.targeting_preview()
        self.ammo -= 1
        self.shots_fired += 1
        self.mode = HuntMode.PLAY
        self._note(msg.hunt_you_fire(self.weapon_name))
        self.raptor_gunshot_xy = (self.player_x, self.player_y)
        self.raptor_under_fire = bool(trace.hit_raptor)
        self.pending_shot = PendingHuntShot(
            blocked=trace.blocked,
            hit_raptor=trace.hit_raptor and preview.damage > 0,
            damage=preview.damage,
            would_tranq_full=preview.would_tranq_full,
        )
        cfg = load_hunt_projectile()
        self.dart = begin_dart(list(trace.path), frames_per_tile=cfg.frames_per_tile)
        if self.dart is None:
            self._apply_pending_shot()

    def projectile_in_progress(self) -> bool:
        return self.dart is not None and self.dart.active

    def advance_projectile(self) -> None:
        if self.dart is None or not self.dart.active:
            return
        cfg = load_hunt_projectile()
        if advance_dart(self.dart, frames_per_tile=cfg.frames_per_tile):
            self._apply_pending_shot()

    def flush_projectile(self) -> None:
        """Skip remaining dart frames and apply the already-computed shot."""
        if self.pending_shot is None and not self.projectile_in_progress():
            return
        if self.dart is not None:
            self.dart.active = False
        self._apply_pending_shot()

    def _apply_pending_shot(self) -> None:
        pending = self.pending_shot
        self.dart = None
        self.pending_shot = None
        if pending is None:
            return
        if pending.blocked:
            self.notice = f"{msg.hunt_you_fire(self.weapon_name)} {msg.hunt_shot_blocked()}"
            self._spend(load_hunt_aut_costs().fire)
            return
        if not pending.hit_raptor or self.raptor is None:
            self.notice = f"{msg.hunt_you_fire(self.weapon_name)} {msg.hunt_shot_miss()}"
            self._spend(load_hunt_aut_costs().fire)
            return
        damage = pending.damage
        self.shots_landed += 1
        if pending.would_tranq_full:
            self.shots_perfect += 1
        was_full = self.raptor.hp == self.raptor.max_hp
        self.raptor.hp -= damage
        if self.raptor.hp <= 0:
            self.raptor.hp = 0
            if was_full:
                self.shots_one_shot += 1
            self.outcome = "tranquilized"
            self.mode = HuntMode.WIN_BASK
            self.win_lines = (
                msg.hunt_you_win(),
                f"Weapon: {self.weapon_name}",
                f"Ammo left: {self.ammo}",
                f"AUT: {format_aut(self.world_aut)}",
            )
            return
        self.notice = f"{msg.hunt_you_fire(self.weapon_name)} {msg.hunt_shot_hit()}"
        self._spend(load_hunt_aut_costs().fire)

    def _raptor_turn(self) -> None:
        if self.raptor is None or self.rng is None:
            return
        if self.dummy_gait is not None:
            self.raptor.gait = self.dummy_gait
        if (
            self.training
            and self.training_layout is not None
            and self.dummy_script is not DummyScript.NORMAL
        ):
            self.dummy_patrol_i, self.dummy_patrol_dir = dummy_act(
                self.raptor,
                self.map,
                script=self.dummy_script,
                layout=self.training_layout,
                hunter_xy=(self.player_x, self.player_y),
                patrol_i=self.dummy_patrol_i,
                patrol_dir=self.dummy_patrol_dir,
            )
            return
        clock = load_hunt_clock()
        vis = vision_profile_for(
            gait=self.gait.value,
            aim_depth=self.aim_depth,
            cfg=load_paddock_config(),
            weapon_id=self.weapon_id,
        )
        rain = self.rain()
        hunter_cone = max(
            2,
            vis.cone_range - rain.hunter_vision_penalty - fatigue_vision(self.run_fatigue),
        )
        raptor_act(
            self.raptor,
            self.map,
            sense=RaptorSense(
                hunter_x=self.player_x,
                hunter_y=self.player_y,
                hunter_facing=self.facing,
                hunter_aim_depth=self.aim_depth,
                hunter_weapon_id=self.weapon_id,
                hunter_gait=self.gait.value,
                hunter_sees_raptor=self.raptor_in_sight(),
                ring=self.ring_hud(),
                hunter_ring=self.hunter_ring,
                raptor_ring=self.raptor_ring,
                clock_remaining=self.clock_remaining(),
                heard_xy=self.raptor_heard_xy,
                gunshot_xy=self.raptor_gunshot_xy,
                world_aut=self.world_aut,
                clock_duration=clock.duration_aut,
                definitely_margin=clock.definitely_margin,
                lock_gait=self.dummy_gait is not None,
                rain_id=rain.level_id,
                grass_see_through=rain.raptor_grass_see,
                under_fire=self.raptor_under_fire,
                hunter_cone_range=hunter_cone,
                hunter_cone_half=vis.cone_half_degrees,
                hunter_heading=self.aim_heading_deg if self.aim_depth > AIM_NONE else None,
                hunter_grass_see=rain.hunter_grass_see,
                hunter_close_blind=(
                    vis.close_blind if vis.close_blind > 0 else (
                        self.aim_depth if self.aim_depth > AIM_NONE else 0
                    )
                ),
                speed_mult=hunt_tuning(self.difficulty_id).raptor_speed_mult,
                los_hot_aut=hunt_tuning(self.difficulty_id).los_hot_aut,
                stalk_watch=hunt_tuning(self.difficulty_id).stalk_watch,
                rain_lead_aut=hunt_tuning(self.difficulty_id).rain_lead_aut,
                cycle_aut=hunt_tuning(self.difficulty_id).rain_cycle_aut,
                double_step_aut=2.0,
            ),
            rng=self.rng,
            prints=self.prints,
            range_penalty=self.rain().raptor_vision_penalty,
        )
        if self.raptor.mind.thought:
            self.message_log.add(
                self.raptor.mind.thought, category=MessageCategory.CAUTION,
            )

    def apply_training_command(self, command_id: str) -> None:
        if not self.training or self.raptor is None or self.training_layout is None:
            return
        layout = self.training_layout
        if command_id == "patrol":
            if self.dummy_script is not DummyScript.STOP:
                self.dummy_resume = DummyScript.PATROL
            self.dummy_script = DummyScript.PATROL
            self.dummy_patrol_i = 0
            self.dummy_patrol_dir = 1
            teleport_raptor(self.raptor, layout.patrol[0], layout.raptor_facing)
        elif command_id == "idle_grass":
            if self.dummy_script is not DummyScript.STOP:
                self.dummy_resume = DummyScript.IDLE_GRASS
            self.dummy_script = DummyScript.IDLE_GRASS
            teleport_raptor(self.raptor, layout.grass_still)
        elif command_id == "idle_open":
            if self.dummy_script is not DummyScript.STOP:
                self.dummy_resume = DummyScript.IDLE_OPEN
            self.dummy_script = DummyScript.IDLE_OPEN
            teleport_raptor(self.raptor, layout.open_still)
        elif command_id == "stop":
            if self.dummy_script is not DummyScript.STOP:
                self.dummy_resume = self.dummy_script
            self.dummy_script = DummyScript.STOP
        elif command_id == "cancel_stop":
            if self.dummy_script is DummyScript.STOP:
                self.dummy_script = self.dummy_resume
        elif command_id == "seek":
            if self.dummy_script is not DummyScript.STOP:
                self.dummy_resume = DummyScript.SEEK
            self.dummy_script = DummyScript.SEEK
        elif command_id == "gait_sneak":
            self.dummy_gait = Gait.SNEAK
            self.raptor.gait = Gait.SNEAK
        elif command_id == "gait_walk":
            self.dummy_gait = Gait.WALK
            self.raptor.gait = Gait.WALK
        elif command_id == "gait_run":
            self.dummy_gait = Gait.RUN
            self.raptor.gait = Gait.RUN
        elif command_id == "normal":
            self.dummy_script = DummyScript.NORMAL
            self.dummy_resume = DummyScript.NORMAL
        elif command_id.startswith("weapon_"):
            wid = command_id.removeprefix("weapon_")
            self.weapon_id, self.weapon_name, self.ammo = weapon_by_id(wid)
        if self.raptor.x == self.player_x and self.raptor.y == self.player_y:
            # Teleport must not land on the hunter.
            ox, oy = layout.raptor_xy
            if (ox, oy) != (self.player_x, self.player_y):
                teleport_raptor(self.raptor, (ox, oy))
        self._refresh_raptor_fov()
        self.refresh_fov()
        self.maybe_raptor_finish()

    def _pump_world(self) -> None:
        actors = [HUNTER_ACTOR, RAPTOR_ACTOR]
        while True:
            nxt = self.scheduler.next_actor(actors, player=HUNTER_ACTOR)
            if nxt is None or nxt == HUNTER_ACTOR:
                break
            if nxt == RAPTOR_ACTOR and self.raptor is not None and self.rng is not None:
                if self.raptor.tranquilized:
                    break
                if self.maybe_raptor_finish():
                    break
                ox, oy = self.raptor.x, self.raptor.y
                self._raptor_turn()
                if (self.raptor.x, self.raptor.y) != (ox, oy):
                    self._leave_print(
                        self.raptor.x, self.raptor.y, self.raptor.facing, "raptor",
                    )
                    self._emit_move_sound(ox, oy, source="raptor")
                if self.maybe_raptor_finish():
                    break
                costs = load_hunt_aut_costs()
                spent = costs.wait
                if self.raptor is not None:
                    spent = tenths(self.raptor.last_aut) if self.raptor.last_aut > 0 else costs.wait
                self.scheduler.commit_action(RAPTOR_ACTOR, tenths(spent))
        if self.mode is HuntMode.SWALLOW:
            return
        self.raptor_heard_xy = None
        self.raptor_gunshot_xy = None
        self.raptor_under_fire = False
        self._tick_weather()
        self._maybe_false_alarm()
        self._refresh_raptor_fov()
        self.refresh_fov()


_END_DISMISS = frozenset({KeySym.ESCAPE, KeySym.RETURN, KeySym.KP_ENTER})


def _is_end_dismiss(event: tcod.event.Event) -> bool:
    return isinstance(event, tcod.event.KeyDown) and event.sym in _END_DISMISS


def _handle_belly(session: HuntSession, event: tcod.event.Event) -> HuntAction:
    if not isinstance(event, tcod.event.KeyDown):
        return HuntAction.NONE
    cmd = parse_tank_command(event)
    wasted = cmd in {
        TankCommand.WAIT,
        TankCommand.FORWARD,
        TankCommand.BACK,
        TankCommand.SIDESTEP_LEFT,
        TankCommand.SIDESTEP_RIGHT,
        TankCommand.ROTATE_45_LEFT,
        TankCommand.ROTATE_45_RIGHT,
        TankCommand.ROTATE_90_LEFT,
        TankCommand.ROTATE_90_RIGHT,
    }
    if not wasted:
        return HuntAction.NONE
    session._belly_maybe_walk()
    session.belly_turns += 1
    if session.belly_turns >= load_hunt_loss().belly_turns:
        session.mode = HuntMode.DIGEST
        session.outcome = "digested"
        session.win_lines = pick_post_belly_lines(
            stance=session.post_swallow_stance(),
            decks=session._decks(),
            rng=session._loss_rng(),
        )
    return HuntAction.NONE


def _handle_targeting(session: HuntSession, event: tcod.event.Event) -> HuntAction:
    if not isinstance(event, tcod.event.KeyDown):
        return HuntAction.NONE
    if event.sym == KeySym.ESCAPE:
        session.mode = HuntMode.PLAY
        session.notice = ""
        return HuntAction.NONE
    if event.sym in MODAL_ADVANCE_KEYS or event.sym == KeySym.F:
        session.confirm_shot()
        return HuntAction.NONE
    delta = DIRECTION_KEYS.get(event.sym)
    if delta is not None:
        session.cursor_x += delta[0]
        session.cursor_y += delta[1]
        session._clamp_cursor()
    return HuntAction.NONE


def _handle_aim_pick(session: HuntSession, event: tcod.event.Event) -> HuntAction:
    if not isinstance(event, tcod.event.KeyDown):
        return HuntAction.NONE
    if event.sym == KeySym.ESCAPE or event.sym == KeySym.D:
        session.mode = HuntMode.PLAY
        session.notice = ""
        return HuntAction.NONE
    if event.sym in MODAL_ADVANCE_KEYS or event.sym == KeySym.A:
        session.confirm_aim_pick()
        return HuntAction.NONE
    delta = DIRECTION_KEYS.get(event.sym)
    if delta is not None:
        nx = session.cursor_x + delta[0]
        ny = session.cursor_y + delta[1]
        if (nx, ny) in session._aim_pick_tiles():
            session.cursor_x, session.cursor_y = nx, ny
    return HuntAction.NONE


def handle_hunt_event(session: HuntSession, event: tcod.event.Event) -> HuntAction:
    help_modes = (HuntMode.PLAY, HuntMode.TARGETING, HuntMode.AIM_PICK, HuntMode.BELLY)
    if session.help_open:
        toggle = help_toggle_event(event, help_open=True)
        if toggle is False:
            session.help_open = False
        return HuntAction.NONE
    if session.mode in help_modes and is_help_open_key(event):
        session.help_open = True
        return HuntAction.NONE
    if session.training_menu is not None:
        picked = handle_training_menu_event(session.training_menu, event)
        if picked == "":
            session.training_menu = None
        elif picked:
            session.apply_training_command(picked)
            session.training_menu = None
        return HuntAction.NONE
    if (
        session.training
        and session.mode is HuntMode.PLAY
        and isinstance(event, tcod.event.KeyDown)
        and event.sym == TRAINING_MENU_KEY
    ):
        menu = TrainingMenuState()
        sel = selectable_menu_indices()
        menu.highlight = sel[0] if sel else 0
        session.training_menu = menu
        return HuntAction.NONE
    if session.projectile_in_progress():
        cmd = parse_tank_command(event)
        if cmd is TankCommand.LEAVE:
            session.flush_projectile()
            return HuntAction.LEAVE
        return HuntAction.NONE
    if session.mode is HuntMode.WIN_BASK:
        if _is_end_dismiss(event):
            session.mode = HuntMode.WIN_RESULTS
        return HuntAction.NONE
    if session.mode is HuntMode.WIN_RESULTS:
        if _is_end_dismiss(event):
            return HuntAction.LEAVE
        return HuntAction.NONE
    if session.mode is HuntMode.TIME_OVER:
        if _is_end_dismiss(event):
            return HuntAction.LEAVE
        return HuntAction.NONE
    if session.mode is HuntMode.SWALLOW:
        if _is_end_dismiss(event):
            session.enter_belly()
        return HuntAction.NONE
    if session.mode is HuntMode.BELLY:
        return _handle_belly(session, event)
    if session.mode is HuntMode.DIGEST:
        if _is_end_dismiss(event):
            session.mode = HuntMode.GAME_OVER
            if session.post_swallow_stance() == POST_SWALLOW_ENDOSOMA:
                session.win_lines = (msg.hunt_game_over(), msg.hunt_endosoma_over())
            else:
                session.win_lines = (msg.hunt_game_over(), msg.hunt_digested_over())
        return HuntAction.NONE
    if session.mode is HuntMode.GAME_OVER:
        if _is_end_dismiss(event):
            return HuntAction.LEAVE
        return HuntAction.NONE
    if session.mode is HuntMode.TARGETING:
        return _handle_targeting(session, event)
    if session.mode is HuntMode.AIM_PICK:
        return _handle_aim_pick(session, event)
    cmd = parse_tank_command(event)
    if cmd is TankCommand.NONE:
        return HuntAction.NONE
    if cmd is TankCommand.LEAVE:
        return HuntAction.LEAVE
    if cmd is TankCommand.OPEN_TARGETING:
        session.enter_targeting()
        return HuntAction.NONE
    costs = load_hunt_aut_costs()
    if cmd is TankCommand.SET_QUICK:
        session._set_gait(Gait.QUICK)
        if costs.gait > 0.0:
            session._spend(costs.gait)
        session.refresh_fov()
        return HuntAction.NONE
    if cmd is TankCommand.SET_WALK:
        session._set_gait(Gait.WALK)
        if costs.gait > 0.0:
            session._spend(costs.gait)
        session.refresh_fov()
        return HuntAction.NONE
    if cmd is TankCommand.SET_RUN:
        session._set_gait(Gait.RUN)
        if costs.gait > 0.0:
            session._spend(costs.gait)
        session.refresh_fov()
        return HuntAction.NONE
    if cmd is TankCommand.SET_SNEAK:
        session._set_gait(Gait.SNEAK)
        if costs.gait > 0.0:
            session._spend(costs.gait)
        session.refresh_fov()
        return HuntAction.NONE
    if cmd is TankCommand.AIM:
        if session.aim_depth >= AIM_FOCUS:
            nxt = raise_aim(session.aim_depth)
            if nxt is None:
                return HuntAction.NONE
            session.aim_depth = nxt
            session._spend(costs.aim)
            session.refresh_fov()
            return HuntAction.NONE
        session.enter_aim_pick()
        return HuntAction.NONE
    if cmd is TankCommand.YAW_AIM_LEFT:
        if session.aim_depth <= AIM_NONE:
            return HuntAction.NONE
        session.yaw_aim(clockwise=False)
        session._spend(costs.rotate_45)
        session.refresh_fov()
        return HuntAction.NONE
    if cmd is TankCommand.YAW_AIM_RIGHT:
        if session.aim_depth <= AIM_NONE:
            return HuntAction.NONE
        session.yaw_aim(clockwise=True)
        session._spend(costs.rotate_45)
        session.refresh_fov()
        return HuntAction.NONE
    if cmd is TankCommand.STAND_DOWN:
        if session.aim_depth == AIM_NONE and session.aim_heading_deg is None:
            return HuntAction.NONE
        session.drop_aim()
        session._spend(costs.stand_down)
        session.refresh_fov()
        return HuntAction.NONE
    if cmd is TankCommand.WAIT:
        session._spend(costs.wait, recover=True)
        session.refresh_fov()
        return HuntAction.NONE
    if cmd is TankCommand.ROTATE_45_LEFT:
        session.rotate_body(-1)
        session._spend(costs.rotate_45)
        session.refresh_fov()
        return HuntAction.NONE
    if cmd is TankCommand.ROTATE_45_RIGHT:
        session.rotate_body(1)
        session._spend(costs.rotate_45)
        session.refresh_fov()
        return HuntAction.NONE
    if cmd is TankCommand.ROTATE_90_LEFT:
        session.rotate_body(-2)
        session._spend(costs.rotate_90)
        session.refresh_fov()
        return HuntAction.NONE
    if cmd is TankCommand.ROTATE_90_RIGHT:
        session.rotate_body(2)
        session._spend(costs.rotate_90)
        session.refresh_fov()
        return HuntAction.NONE
    if cmd is TankCommand.FORWARD:
        tired = session.gait in (Gait.RUN, Gait.QUICK)
        dx, dy = facing_delta(session.facing)
        if session.try_step(dx, dy):
            if tired:
                session.drop_aim()
            if session.maybe_raptor_finish():
                return HuntAction.NONE
            session._spend(
                costs.step_for(session.gait.value),
                run_step=session.gait is Gait.RUN,
                quick_step=session.gait is Gait.QUICK,
                recover=session.gait in (Gait.WALK, Gait.SNEAK),
            )
            session.refresh_fov()
        return HuntAction.NONE
    if cmd is TankCommand.BACK:
        tired = session.gait in (Gait.RUN, Gait.QUICK)
        slowed = session.gait is Gait.RUN
        session._slow_if_running()
        dx, dy = facing_delta(session.facing)
        moved = session.try_step(-dx, -dy)
        if moved:
            if tired:
                session.drop_aim()
            if session.maybe_raptor_finish():
                return HuntAction.NONE
            session._spend(
                costs.step_for(session.gait.value),
                recover=session.gait in (Gait.WALK, Gait.SNEAK),
            )
        if moved or slowed:
            session.refresh_fov()
        return HuntAction.NONE
    if cmd is TankCommand.SIDESTEP_LEFT:
        tired = session.gait in (Gait.RUN, Gait.QUICK)
        slowed = session.gait is Gait.RUN
        session._slow_if_running()
        dx, dy = facing_delta(rotate_facing(session.facing, -2))
        moved = session.try_step(dx, dy)
        if moved:
            if tired:
                session.drop_aim()
            if session.maybe_raptor_finish():
                return HuntAction.NONE
            session._spend(
                costs.step_for(session.gait.value),
                recover=session.gait in (Gait.WALK, Gait.SNEAK),
            )
        if moved or slowed:
            session.refresh_fov()
        return HuntAction.NONE
    if cmd is TankCommand.SIDESTEP_RIGHT:
        tired = session.gait in (Gait.RUN, Gait.QUICK)
        slowed = session.gait is Gait.RUN
        session._slow_if_running()
        dx, dy = facing_delta(rotate_facing(session.facing, 2))
        moved = session.try_step(dx, dy)
        if moved:
            if tired:
                session.drop_aim()
            if session.maybe_raptor_finish():
                return HuntAction.NONE
            session._spend(
                costs.step_for(session.gait.value),
                recover=session.gait in (Gait.WALK, Gait.SNEAK),
            )
        if moved or slowed:
            session.refresh_fov()
        return HuntAction.NONE
    return HuntAction.NONE


def render_hunt_stub(console: tcod.console.Console, session: HuntSession) -> None:
    """PR1 name kept; draws the paddock with camera, cone FOV, and tank hunter."""
    render_hunt(console, session)


def _belly_camera(session: HuntSession) -> tuple[int, int]:
    """Locked at swallow tile so a raptor step slides the ring on screen."""
    if session.belly_cam_x is not None and session.belly_cam_y is not None:
        return session.belly_cam_x, session.belly_cam_y
    if session.raptor is not None:
        return session.raptor.x, session.raptor.y
    return session.player_x, session.player_y


def _loss_fade_t(session: HuntSession) -> float:
    if session.post_swallow_stance() == POST_SWALLOW_ENDOSOMA:
        return 0.0
    total = max(1, load_hunt_loss().belly_turns)
    if session.mode in (HuntMode.DIGEST, HuntMode.GAME_OVER):
        return 1.0
    return belly_fade_t(turns=session.belly_turns, total=total)


def _render_belly(console: tcod.console.Console, session: HuntSession) -> None:
    fade = _loss_fade_t(session)
    fill_loss_void(console)
    mmap = session.map
    view_w, view_h = map_view_size(console.width, console.height)
    lock_x, lock_y = _belly_camera(session)
    cam_x = lock_x - view_w // 2
    cam_y = lock_y - view_h // 2
    cam_x = max(0, min(cam_x, max(0, mmap.width - view_w)))
    cam_y = max(0, min(cam_y, max(0, mmap.height - view_h)))
    ox, oy = session.player_x, session.player_y
    if session.raptor is not None:
        ox, oy = session.raptor.x, session.raptor.y
    render_belly_overlay(
        console,
        origin_sx=ox - cam_x,
        origin_sy=oy - cam_y,
        fade_t=fade,
    )
    console.print(
        1, console.height - 1, "Still or move — it does nothing.",
        fg=(140, 140, 140), bg=(0, 0, 0),
    )


def render_hunt(console: tcod.console.Console, session: HuntSession) -> None:
    if session.help_open:
        render_hunt_help(console, training=session.training)
        return
    if session.training_menu is not None:
        render_training_menu(console, session.training_menu)
        return
    if session.mode is HuntMode.BELLY:
        _render_belly(console, session)
        return
    if session.mode in (HuntMode.DIGEST, HuntMode.GAME_OVER):
        fill_loss_void(console)
        if session.mode is HuntMode.DIGEST:
            render_centered_modal(console, session.win_lines, footer=MODAL_FOOTER)
        else:
            body = session.win_lines
            title = msg.hunt_game_over()
            if body and body[0] == title:
                body = body[1:]
            render_centered_modal(console, body, title=title, footer=MODAL_FOOTER)
        return
    console.clear()
    mmap = session.map
    view_w, view_h = map_view_size(console.width, console.height)
    cam_x = session.player_x - view_w // 2
    cam_y = session.player_y - view_h // 2
    cam_x = max(0, min(cam_x, max(0, mmap.width - view_w)))
    cam_y = max(0, min(cam_y, max(0, mmap.height - view_h)))
    for sy in range(view_h):
        my = cam_y + sy
        if my < 0 or my >= mmap.height:
            continue
        for sx in range(view_w):
            mx = cam_x + sx
            if mx < 0 or mx >= mmap.width:
                continue
            terr = mmap.terrain_at(mx, my)
            glyph = _TERRAIN_GLYPH[terr]
            seen = (mx, my) in session.visible
            fg = _TERRAIN_FG_SEEN[terr] if seen else _TERRAIN_FG_KNOWN[terr]
            console.print(sx, sy, glyph, fg=fg)
            show_print = False
            for p in session.prints:
                if p.x == mx and p.y == my:
                    show_print = seen or session.rain().prints_outside_fov
                    break
            if show_print and (mx, my) != (session.player_x, session.player_y):
                console.print(sx, sy, '"', fg=(90, 70, 45) if seen else (50, 40, 28))
    px = session.player_x - cam_x
    py = session.player_y - cam_y
    live_raptor = session.raptor is not None and (
        session.raptor_in_sight() or session.mode in (HuntMode.WIN_BASK, HuntMode.WIN_RESULTS)
    )
    last_xy = (
        (session.last_known_x, session.last_known_y)
        if session.last_known_x is not None and session.last_known_y is not None
        else None
    )
    raptor_xy = None if session.raptor is None else (session.raptor.x, session.raptor.y)
    skip_sound: set[tuple[int, int]] = set()
    if live_raptor and raptor_xy is not None:
        skip_sound.add(raptor_xy)
    if (not live_raptor) and last_xy is not None and last_xy not in session.visible:
        skip_sound.add(last_xy)
    for mark in session.sound_marks:
        if (mark.x, mark.y) in skip_sound:
            continue
        sx = mark.x - cam_x
        sy = mark.y - cam_y
        if 0 <= sx < view_w and 0 <= sy < view_h:
            console.print(sx, sy, "?", fg=(200, 190, 80))
    if live_raptor and session.raptor is not None:
        rx = session.raptor.x - cam_x
        ry = session.raptor.y - cam_y
        if 0 <= rx < view_w and 0 <= ry < view_h:
            console.print(rx, ry, "r", fg=(200, 80, 60))
    elif last_xy is not None and last_xy not in session.visible:
        lx = last_xy[0] - cam_x
        ly = last_xy[1] - cam_y
        if 0 <= lx < view_w and 0 <= ly < view_h:
            console.print(lx, ly, "r", fg=(110, 50, 40))
    if session.mode in (HuntMode.TARGETING, HuntMode.AIM_PICK):
        cx = session.cursor_x - cam_x
        cy = session.cursor_y - cam_y
        if 0 <= cx < view_w and 0 <= cy < view_h:
            fg = (255, 220, 80) if session.mode is HuntMode.AIM_PICK else (180, 220, 255)
            console.print(cx, cy, "X", fg=fg)
    if 0 <= px < view_w and 0 <= py < view_h:
        console.print(px, py, "@", fg=(220, 220, 200))
    if session.dart is not None and session.dart.active:
        cfg = load_hunt_projectile()
        for mx, my in dart_draw_tiles(session.dart):
            dx = mx - cam_x
            dy = my - cam_y
            if 0 <= dx < view_w and 0 <= dy < view_h:
                console.print(dx, dy, cfg.glyph, fg=cfg.fg)
    raptor_lines: tuple[str, ...] = ()
    if session.raptor is not None and session.raptor_in_sight():
        session._refresh_raptor_fov()
        raptor_lines = raptor_readout(
            session.raptor, session.player_x, session.player_y,
        )
    targeting = session.mode is HuntMode.TARGETING
    targeting_range: int | None = None
    if targeting:
        preview, _trace = session.targeting_preview()
        targeting_range = preview.range_chebyshev
    rain = session.rain()
    render_hunt_panel(
        console,
        clock_label=f"Clock {format_aut(session.clock_remaining())}",
        ring=session.ring_hud(),
        raptor_lines=raptor_lines,
        hunter_lines=hunter_stat_lines(
            facing=facing_name(session.facing),
            weapon_id=session.weapon_id,
            weapon_name=session.weapon_name,
            ammo=session.ammo,
            gait=session.gait,
            aim_depth=session.aim_depth,
            fatigue=session.run_fatigue,
        ),
        weather_label=rain.label,
        weather_id=rain.level_id,
        targeting_range=targeting_range,
    )
    aut = format_aut(session.world_aut)
    if session.training:
        status = f"Training  |  AUT {aut}"
    elif session.hunter_name:
        status = f"{session.hunter_name}  |  AUT {aut}"
    else:
        status = f"AUT {aut}"
    console.print(1, console.height - 2, cp437_safe(status)[: console.width - 2], fg=(200, 200, 160))
    footer = ""
    if session.notice and session.mode in (
        HuntMode.PLAY, HuntMode.TARGETING, HuntMode.AIM_PICK,
    ):
        footer = session.notice
    if session.mode is HuntMode.WIN_BASK:
        console.print(2, 1, cp437_safe(msg.hunt_you_fire(session.weapon_name)), fg=(220, 220, 200))
        console.print(2, 2, cp437_safe(msg.hunt_raptor_tranquilized()), fg=(120, 255, 140))
        footer = "Enter or Esc to view the final results."
    if session.mode is HuntMode.SWALLOW:
        render_centered_modal(console, session.win_lines, footer=MODAL_FOOTER)
        return
    if session.mode in (HuntMode.WIN_RESULTS, HuntMode.TIME_OVER):
        body = session.win_lines
        title = msg.hunt_game_over()
        if body and body[0] == title:
            body = body[1:]
        render_centered_modal(console, body, title=title, footer=MODAL_FOOTER)
        return
    console.print(1, console.height - 1, footer[: console.width - 2], fg=(140, 140, 140))
