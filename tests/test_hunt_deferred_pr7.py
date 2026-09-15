"""PR7 (hunt-deferred): aim off-center heading, pick, yaw, close-blind."""

from __future__ import annotations

import math

from tcod.event import KeySym, Modifier, Scancode

import tcod.event

from src.hunt_facing import (
    facing_name,
    heading_from_facing,
    heading_matches_facing,
    heading_toward,
    in_vision_cone,
    nearest_eight_facing,
    next_eight_facing,
    yaw_step_degrees,
)
from src.messages import hunt_fire_wrong_facing
from src.hunt_input import TankCommand, parse_tank_command
from src.hunt_map import load_paddock_config, vision_profile_for
from src.hunt_raptor import HuntRaptor
from src.hunt_save import hunt_from_snapshot, snapshot_hunt
from src.hunt_session import HuntMode, handle_hunt_event, render_hunt
from src.hunt_stance import AIM_DEEP, AIM_FOCUS, AIM_NONE, Gait
from tests.test_hunt_pr2 import _key, _open_square, _session
from tests.test_hunt_pr10 import _console_text
from tests.ui_test_helpers import make_console


def _ctrl(sym: KeySym, *, scancode: Scancode = Scancode.UNKNOWN) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=scancode, mod=Modifier.LCTRL)


def _far_raptor(*, x: int = 1, y: int = 9) -> HuntRaptor:
    """SW of a typical hunter, facing south so it neither sees nor is aimed-at."""
    return HuntRaptor(x=x, y=y, facing=4, hp=100, max_hp=100)


def _aimed(session) -> None:
    handle_hunt_event(session, _key(KeySym.A))
    handle_hunt_event(session, _key(KeySym.RETURN))


class _Pick:
    def __init__(self, index: int) -> None:
        self.index = index

    def choice(self, seq):
        return seq[self.index]


def test_ctrl_7_and_9_are_yaw_aim() -> None:
    assert parse_tank_command(_ctrl(KeySym.KP_7)) is TankCommand.YAW_AIM_LEFT
    assert parse_tank_command(_ctrl(KeySym.KP_9)) is TankCommand.YAW_AIM_RIGHT
    assert parse_tank_command(_key(KeySym.KP_7)) is TankCommand.ROTATE_45_LEFT
    assert parse_tank_command(_key(KeySym.KP_9)) is TankCommand.ROTATE_45_RIGHT


def test_heading_toward_cardinals() -> None:
    assert heading_toward(5, 5, 5, 2) == 0.0
    assert heading_toward(5, 5, 8, 5) == 90.0
    assert heading_toward(5, 5, 5, 8) == 180.0
    assert heading_toward(5, 5, 2, 5) == 270.0


def test_nearest_eight_facing_halfway_is_random() -> None:
    assert nearest_eight_facing(22.5, _Pick(0)) == 0
    assert nearest_eight_facing(22.5, _Pick(1)) == 1
    assert nearest_eight_facing(337.5, _Pick(0)) == 7
    assert nearest_eight_facing(337.5, _Pick(1)) == 0
    assert nearest_eight_facing(0.0) == 0
    assert nearest_eight_facing(44.0) == 1


def test_a_opens_aim_pick_on_a_visible_tile_only() -> None:
    session = _session(raptor=_far_raptor(), facing=0)
    visible = set(session.visible)
    handle_hunt_event(session, _key(KeySym.A))
    assert session.mode is HuntMode.AIM_PICK
    assert session.aim_depth == AIM_NONE
    assert (session.cursor_x, session.cursor_y) in visible
    assert (session.cursor_x, session.cursor_y) != (session.player_x, session.player_y)
    behind = (session.player_x, session.player_y + 1)
    assert behind not in visible
    handle_hunt_event(session, _key(KeySym.KP_2))
    assert (session.cursor_x, session.cursor_y) != behind
    assert (session.cursor_x, session.cursor_y) in session._aim_pick_tiles()


def test_aim_pick_cannot_leave_current_view() -> None:
    session = _session(raptor=_far_raptor(), facing=0)
    handle_hunt_event(session, _key(KeySym.A))
    tiles = session._aim_pick_tiles()
    for _ in range(8):
        handle_hunt_event(session, _key(KeySym.KP_4))
        handle_hunt_event(session, _key(KeySym.KP_6))
        handle_hunt_event(session, _key(KeySym.KP_8))
        handle_hunt_event(session, _key(KeySym.KP_2))
    assert (session.cursor_x, session.cursor_y) in tiles


def test_confirm_aim_centers_heading_on_picked_tile() -> None:
    session = _session(raptor=_far_raptor(), facing=0)
    handle_hunt_event(session, _key(KeySym.A))
    session.cursor_x = session.player_x + 1
    session.cursor_y = session.player_y - 2
    assert (session.cursor_x, session.cursor_y) in session._aim_pick_tiles()
    handle_hunt_event(session, _key(KeySym.RETURN))
    assert session.mode is HuntMode.PLAY
    assert session.aim_depth == AIM_FOCUS
    assert session.aim_heading_deg is not None
    expected = heading_toward(
        session.player_x, session.player_y, session.cursor_x, session.cursor_y,
    )
    assert abs((session.aim_heading_deg - expected + 180) % 360 - 180) < 1e-6


def test_aim_pick_escape_cancels_without_aiming() -> None:
    session = _session(raptor=_far_raptor())
    handle_hunt_event(session, _key(KeySym.A))
    handle_hunt_event(session, _key(KeySym.ESCAPE))
    assert session.mode is HuntMode.PLAY
    assert session.aim_depth == AIM_NONE
    assert session.aim_heading_deg is None


def test_gait_toggle_does_not_drop_aim() -> None:
    session = _session(raptor=_far_raptor(), x=5, y=8, facing=0)
    _aimed(session)
    handle_hunt_event(session, _key(KeySym.R))
    assert session.gait is Gait.RUN
    assert session.aim_depth == AIM_FOCUS
    handle_hunt_event(session, _key(KeySym.Q))
    assert session.gait is Gait.QUICK
    assert session.aim_depth == AIM_FOCUS
    handle_hunt_event(session, _key(KeySym.W))
    assert session.aim_depth == AIM_FOCUS


def test_run_and_quick_steps_drop_aim_walk_does_not() -> None:
    session = _session(raptor=_far_raptor(), x=5, y=8, facing=0)
    _aimed(session)
    handle_hunt_event(session, _key(KeySym.W))
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.aim_depth == AIM_FOCUS
    handle_hunt_event(session, _key(KeySym.R))
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.aim_depth == AIM_NONE
    session.raptor.x, session.raptor.y, session.raptor.facing = 1, 9, 4
    session.raptor.mind.fix_x = None
    session.raptor.mind.fix_y = None
    _aimed(session)
    handle_hunt_event(session, _key(KeySym.Q))
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.aim_depth == AIM_NONE


def test_drop_aim_snaps_facing_to_nearest_45() -> None:
    session = _session(raptor=_far_raptor(), facing=0)
    session.aim_depth = AIM_FOCUS
    session.aim_heading_deg = 20.0
    session.drop_aim()
    assert session.aim_depth == AIM_NONE
    assert session.facing == 0
    session.aim_depth = AIM_FOCUS
    session.aim_heading_deg = 50.0
    session.drop_aim()
    assert session.facing == 1


def test_drop_aim_halfway_picks_with_rng() -> None:
    session = _session(raptor=_far_raptor(), facing=0)
    session.rng = _Pick(1)  # type: ignore[assignment]
    session.aim_depth = AIM_FOCUS
    session.aim_heading_deg = 22.5
    session.drop_aim()
    assert session.facing == 1


def test_aim_level_1_blinds_adjacent_aim_2_blinds_two_rings() -> None:
    session = _session(
        raptor=_far_raptor(), x=5, y=5, facing=0,
        weapon_id="shotgun", weapon_name="Shotgun",
    )
    adj = (5, 4)
    ring2 = (5, 3)
    assert adj in session.visible
    assert ring2 in session.visible
    _aimed(session)
    assert session.aim_depth == AIM_FOCUS
    assert adj not in session.visible
    assert (5, 5) in session.visible
    assert ring2 in session.visible
    handle_hunt_event(session, _key(KeySym.A))
    assert session.aim_depth == AIM_DEEP
    assert adj not in session.visible
    assert ring2 not in session.visible
    assert (5, 5) in session.visible


def test_yaw_step_is_one_third_of_the_cone() -> None:
    cfg = load_paddock_config()
    profile = vision_profile_for(gait="walk", aim_depth=1, cfg=cfg)
    assert yaw_step_degrees(profile.cone_half_degrees) == (2.0 / 3.0) * profile.cone_half_degrees


def test_yaw_sweep_never_skips_a_tile_in_aimed_range() -> None:
    cfg = load_paddock_config()
    profile = vision_profile_for(gait="walk", aim_depth=1, cfg=cfg)
    half = profile.cone_half_degrees
    step = yaw_step_degrees(half)
    cone_range = profile.cone_range
    close_blind = 1
    headings = []
    heading = 0.0
    for _ in range(int(math.ceil(360.0 / step)) + 2):
        headings.append(heading)
        heading = (heading + step) % 360.0
    ox, oy = 20, 20
    missed: list[tuple[int, int]] = []
    for dy in range(-cone_range, cone_range + 1):
        for dx in range(-cone_range, cone_range + 1):
            dist = max(abs(dx), abs(dy))
            if dist == 0 or dist <= close_blind or dist > cone_range:
                continue
            tx, ty = ox + dx, oy + dy
            seen = False
            for h in headings:
                if in_vision_cone(
                    origin_x=ox,
                    origin_y=oy,
                    facing=0,
                    tile_x=tx,
                    tile_y=ty,
                    cone_range=cone_range,
                    half_degrees=half,
                    heading_deg=h,
                    close_blind=close_blind,
                ):
                    seen = True
                    break
            if not seen:
                missed.append((tx, ty))
    assert missed == []


def test_ctrl_yaw_changes_live_cone() -> None:
    session = _session(
        paddock=_open_square(21), x=10, y=10, facing=0, raptor=_far_raptor(x=1, y=19),
        weapon_id="shotgun", weapon_name="Shotgun",
    )
    _aimed(session)
    before = set(session.visible)
    heading = session.aim_heading_deg
    handle_hunt_event(session, _ctrl(KeySym.KP_9))
    assert session.aim_heading_deg is not None
    assert heading is not None
    assert abs((session.aim_heading_deg - heading + 180) % 360 - 180) > 1.0
    assert session.visible != before
    shared = before & session.visible
    lost = before - session.visible
    gained = session.visible - before
    assert lost and gained
    assert len(shared) > len(before) // 2
    assert session.aim_depth == AIM_FOCUS


def test_snapshot_keeps_aim_heading() -> None:
    session = _session(raptor=_far_raptor(), facing=0)
    _aimed(session)
    heading = session.aim_heading_deg
    snap = snapshot_hunt(session)
    restored = hunt_from_snapshot(snap)
    assert restored.aim_depth == AIM_FOCUS
    assert restored.aim_heading_deg == heading


def test_old_save_without_heading_derives_from_facing() -> None:
    session = _session(raptor=_far_raptor(), facing=2)
    snap = snapshot_hunt(session)
    snap["aim_depth"] = AIM_FOCUS
    snap.pop("aim_heading_deg", None)
    restored = hunt_from_snapshot(snap)
    assert restored.aim_heading_deg == heading_from_facing(2)


def test_aim_pick_draws_reticle() -> None:
    session = _session(paddock=_open_square(), x=5, y=5, facing=0, raptor=_far_raptor())
    handle_hunt_event(session, _key(KeySym.A))
    console = make_console()
    render_hunt(console, session)
    body = _console_text(console)
    assert "X" in body


def test_help_lists_yaw_and_aim_pick() -> None:
    from src.hunt_help import hunt_help_lines

    text = " ".join(line.text for line in hunt_help_lines())
    assert "Ctrl+7" in text
    assert "visible tile" in text
    assert "drop aim and turn" in text


def test_next_eight_facing_from_off_tick() -> None:
    assert next_eight_facing(20.0, 1) == 1
    assert next_eight_facing(20.0, -1) == 0
    assert next_eight_facing(20.0, 2) == 2
    assert next_eight_facing(20.0, -2) == 7
    assert next_eight_facing(0.0, 1) == 1
    assert next_eight_facing(0.0, -1) == 7
    assert next_eight_facing(355.0, 1) == 0
    assert next_eight_facing(355.0, -1) == 7


def test_unshifted_rotate_drops_aim_and_snaps_in_that_direction() -> None:
    session = _session(
        paddock=_open_square(21),
        x=10,
        y=10,
        facing=0,
        raptor=HuntRaptor(x=1, y=1, facing=0, hp=100, max_hp=100),
    )
    session.aim_depth = AIM_FOCUS
    session.aim_heading_deg = 20.0
    session.refresh_fov()
    handle_hunt_event(session, _key(KeySym.KP_9))
    assert session.aim_depth == AIM_NONE
    assert session.aim_heading_deg is None
    assert facing_name(session.facing) == "NE"

    session.aim_depth = AIM_FOCUS
    session.aim_heading_deg = 20.0
    session.facing = 0
    session.refresh_fov()
    handle_hunt_event(session, _key(KeySym.KP_7))
    assert session.aim_depth == AIM_NONE
    assert facing_name(session.facing) == "N"

    session.aim_depth = AIM_FOCUS
    session.aim_heading_deg = 20.0
    session.facing = 0
    handle_hunt_event(session, _key(KeySym.KP_6))
    assert session.aim_depth == AIM_NONE
    assert facing_name(session.facing) == "E"

    session.aim_depth = AIM_FOCUS
    session.aim_heading_deg = 20.0
    session.facing = 0
    handle_hunt_event(session, _key(KeySym.KP_4))
    assert session.aim_depth == AIM_NONE
    assert facing_name(session.facing) == "NW"


def test_ctrl_yaw_does_not_drop_aim() -> None:
    session = _session(raptor=_far_raptor(), facing=0)
    session.aim_depth = AIM_FOCUS
    session.aim_heading_deg = 20.0
    session.refresh_fov()
    handle_hunt_event(session, _ctrl(KeySym.KP_9))
    assert session.aim_depth == AIM_FOCUS
    assert session.aim_heading_deg is not None
    assert session.aim_heading_deg != 20.0
    assert session.facing == nearest_eight_facing(session.aim_heading_deg, session.rng)


def test_yaw_facing_tracks_nearest_tick_from_west_to_east() -> None:
    session = _session(
        paddock=_open_square(21),
        x=10,
        y=10,
        facing=6,
        raptor=HuntRaptor(x=1, y=1, facing=0, hp=100, max_hp=100),
        weapon_id="shotgun",
        weapon_name="Shotgun",
    )
    session.aim_depth = AIM_FOCUS
    session.aim_heading_deg = 270.0
    session.refresh_fov()
    seen = {session.facing}
    for _ in range(24):
        handle_hunt_event(session, _ctrl(KeySym.KP_9))
        seen.add(session.facing)
        assert session.aim_depth == AIM_FOCUS
        assert session.facing == nearest_eight_facing(
            session.aim_heading_deg, session.rng,
        )
        if abs((session.aim_heading_deg - 90.0 + 180) % 360 - 180) < 12.0:
            break
    assert 6 in seen
    assert 0 in seen
    assert 2 in seen


def test_cannot_fire_away_from_facing() -> None:
    session = _session(
        paddock=_open_square(), x=5, y=5, facing=0, raptor=_far_raptor(),
        weapon_id="shotgun", weapon_name="Shotgun",
    )
    handle_hunt_event(session, _key(KeySym.F))
    session.cursor_x, session.cursor_y = 5, 8
    ammo = session.ammo
    handle_hunt_event(session, _key(KeySym.RETURN))
    assert session.mode is HuntMode.TARGETING
    assert session.ammo == ammo
    assert session.notice == hunt_fire_wrong_facing()


def test_heading_matches_facing_slice() -> None:
    assert heading_matches_facing(0.0, 0)
    assert heading_matches_facing(22.5, 0)
    assert heading_matches_facing(337.5, 0)
    assert not heading_matches_facing(90.0, 0)
    assert heading_matches_facing(315.0, 7)
    assert not heading_matches_facing(180.0, 7)
