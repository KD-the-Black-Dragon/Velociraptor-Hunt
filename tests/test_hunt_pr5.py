"""PR5: F-then-confirm targeting, deterministic shots, tranq win."""

from __future__ import annotations

from tcod.event import KeySym

from src.hunt_combat import compute_damage, weapon_combat
from src.hunt_map import HuntTerrain
from src.hunt_raptor import HuntRaptor
from src.hunt_session import HuntAction, HuntMode, handle_hunt_event
from src.hunt_stance import AIM_NONE
from tests.test_hunt_pr2 import _key, _open_square, _session


def _aimed_shotgun(*, raptor_y: int = 4) -> object:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=raptor_y, facing=4, hp=100, max_hp=100)
    return _session(
        paddock=mmap, x=5, y=5, facing=0, raptor=raptor, weapon_id="shotgun",
        weapon_name="Shotgun",
    )


def test_rifle_unaimed_point_blank_is_graze_not_tranq() -> None:
    rifle = weapon_combat("rifle")
    dmg = compute_damage(
        rifle, range_chebyshev=1, aim_depth=AIM_NONE, hunter_running=False,
    )
    assert 0 < dmg < 100


def test_rifle_unaimed_long_range_in_rain_is_zero() -> None:
    rifle = weapon_combat("rifle")
    dmg = compute_damage(
        rifle,
        range_chebyshev=rifle.max_range,
        aim_depth=AIM_NONE,
        hunter_running=False,
        rain_id="heavy",
        raptor_moving=True,
        raptor_move_facing=2,
        shot_heading=0.0,
    )
    assert dmg == 0


def test_shotgun_unaimed_values_unchanged() -> None:
    shotgun = weapon_combat("shotgun")
    assert shotgun.unaimed_penalty == 10
    assert shotgun.unaimed_cap == 0
    assert shotgun.rain_heavy == 0
    dmg = compute_damage(
        shotgun, range_chebyshev=1, aim_depth=AIM_NONE, hunter_running=False,
        rain_id="heavy", raptor_moving=True,
    )
    assert dmg >= 100


def test_shotgun_close_unaimed_can_tranq() -> None:
    shotgun = weapon_combat("shotgun")
    dmg = compute_damage(
        shotgun, range_chebyshev=1, aim_depth=AIM_NONE, hunter_running=False,
    )
    assert dmg >= 100


def test_damage_is_deterministic() -> None:
    rifle = weapon_combat("rifle")
    a = compute_damage(rifle, range_chebyshev=8, aim_depth=2, hunter_running=True)
    b = compute_damage(rifle, range_chebyshev=8, aim_depth=2, hunter_running=True)
    assert a == b


def test_f_opens_targeting_on_visible_raptor() -> None:
    session = _aimed_shotgun()
    assert session.raptor_in_sight()
    handle_hunt_event(session, _key(KeySym.F))
    assert session.mode is HuntMode.TARGETING
    assert (session.cursor_x, session.cursor_y) == (session.raptor.x, session.raptor.y)
    preview, _ = session.targeting_preview()
    assert "range 3" in preview.factors or "range 1" in preview.factors
    assert "no aiming" in preview.factors


def test_esc_aborts_targeting_not_hunt() -> None:
    session = _aimed_shotgun()
    handle_hunt_event(session, _key(KeySym.F))
    assert handle_hunt_event(session, _key(KeySym.ESCAPE)) is HuntAction.NONE
    assert session.mode is HuntMode.PLAY


def _land(session) -> None:
    session.flush_projectile()


def test_shotgun_confirm_tranquilizes_and_bask() -> None:
    session = _aimed_shotgun(raptor_y=4)
    start_ammo = session.ammo
    handle_hunt_event(session, _key(KeySym.F))
    handle_hunt_event(session, _key(KeySym.RETURN))
    _land(session)
    assert session.raptor is not None
    assert session.raptor.hp <= 0
    assert session.mode is HuntMode.WIN_BASK
    assert session.ammo == start_ammo - 1
    assert handle_hunt_event(session, _key(KeySym.A)) is HuntAction.NONE
    assert session.mode is HuntMode.WIN_BASK
    assert handle_hunt_event(session, _key(KeySym.RETURN)) is HuntAction.NONE
    assert session.mode is HuntMode.WIN_RESULTS
    assert handle_hunt_event(session, _key(KeySym.A)) is HuntAction.NONE
    assert session.mode is HuntMode.WIN_RESULTS
    assert handle_hunt_event(session, _key(KeySym.RETURN)) is HuntAction.LEAVE


def test_tree_blocks_shot() -> None:
    mmap = _open_square()
    mmap.tiles[3][5] = HuntTerrain.TREE
    raptor = HuntRaptor(x=5, y=2, facing=4, hp=100, max_hp=100)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    assert not session.raptor_in_sight()
    hp = session.raptor.hp
    handle_hunt_event(session, _key(KeySym.F))
    session.cursor_x, session.cursor_y = 5, 2
    handle_hunt_event(session, _key(KeySym.RETURN))
    _land(session)
    assert session.raptor.hp == hp
    assert session.mode is HuntMode.PLAY
    assert "tree" in session.notice.lower() or "slams" in session.notice.lower()


def test_shot_continues_past_cursor_to_max_range() -> None:
    """Cursor 1 east of the hunter still hits a raptor 2 east on the same line."""
    mmap = _open_square()
    raptor = HuntRaptor(x=7, y=5, facing=6, hp=100, max_hp=100)
    session = _session(
        paddock=mmap, x=5, y=5, facing=2, raptor=raptor,
        weapon_id="shotgun", weapon_name="Shotgun",
    )
    handle_hunt_event(session, _key(KeySym.F))
    session.cursor_x, session.cursor_y = 6, 5
    handle_hunt_event(session, _key(KeySym.RETURN))
    _land(session)
    assert session.raptor is not None
    assert session.raptor.hp < 100


def test_blind_fire_hits_if_on_line() -> None:
    mmap = _open_square()
    mmap.tiles[4][5] = HuntTerrain.GRASS
    mmap.tiles[3][5] = HuntTerrain.GRASS
    mmap.tiles[2][5] = HuntTerrain.GRASS
    raptor = HuntRaptor(x=5, y=2, facing=4, hp=100, max_hp=100)
    session = _session(
        paddock=mmap, x=5, y=5, facing=0, raptor=raptor,
        weapon_id="shotgun", weapon_name="Shotgun",
    )
    assert not session.raptor_in_sight()
    handle_hunt_event(session, _key(KeySym.F))
    assert session.mode is HuntMode.TARGETING
    assert (session.cursor_x, session.cursor_y) != (raptor.x, raptor.y)
    session.cursor_x, session.cursor_y = raptor.x, raptor.y
    handle_hunt_event(session, _key(KeySym.RETURN))
    _land(session)
    assert session.raptor is not None
    assert session.raptor.hp < 100 or session.raptor.hp == 0
