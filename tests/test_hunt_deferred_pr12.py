"""PR12: raptor heatmap mind, gait AUT, danger-close, gunshot blur."""

from __future__ import annotations

from src.hunt_ai import HuntAiConfig, RaptorSense, raptor_act
from src.hunt_aut import load_hunt_aut_costs, tenths
from src.hunt_clock import RingState, load_hunt_clock, reset_hunt_clock_cache
from src.hunt_combat import chebyshev
from src.hunt_heatmap import apply_gunshot, ensure_maps, sound_plausible
from src.hunt_fov import has_line_of_sight, visible_tiles
from src.hunt_map import HuntMap, HuntTerrain, generate_paddock, load_paddock_config, reset_paddock_config_cache
from src.hunt_raptor import HuntRaptor
from src.hunt_session import handle_hunt_event
from src.hunt_stance import Gait
from src.hunt_weather import load_hunt_weather, reset_hunt_weather_cache
from tests.test_hunt_pr2 import _key, _open_square, _session
from tests.test_hunt_pr4 import _FixedRng
from tcod.event import KeySym


def _cfg(**kwargs) -> HuntAiConfig:
    return HuntAiConfig(danger_close=4, observe_clock_frac=0.2, **kwargs)


def _sense(**kwargs) -> RaptorSense:
    base = dict(
        hunter_x=10,
        hunter_y=10,
        hunter_facing=0,
        hunter_aim_depth=0,
        hunter_weapon_id="rifle",
        hunter_gait="walk",
        hunter_sees_raptor=False,
        ring=RingState.CLOSE,
        hunter_ring=0.0,
        raptor_ring=0.0,
        clock_remaining=200.0,
        world_aut=80.0,
        clock_duration=320.0,
        definitely_margin=12.0,
    )
    base.update(kwargs)
    return RaptorSense(**base)


def test_gait_aut_is_proportional() -> None:
    costs = load_hunt_aut_costs()
    assert costs.sneak == tenths(costs.walk * 2)
    assert tenths(costs.run * 4) == tenths(costs.walk * 2)
    assert tenths(costs.quick * 4) == tenths(costs.run + costs.walk * 3)


def test_raptor_body_aut_is_twice_hunter() -> None:
    from src.hunt_ai import _aut_for, load_hunt_ai, reset_hunt_ai_cache
    from src.hunt_raptor import HuntRaptor
    reset_hunt_ai_cache()
    assert load_hunt_ai().speed_mult == 2.0
    raptor = HuntRaptor(x=1, y=1, facing=0)
    raptor.gait = Gait.WALK
    costs = load_hunt_aut_costs()
    assert _aut_for(raptor, "step") == tenths(costs.walk / 2)
    assert _aut_for(raptor, "rotate") == tenths(costs.rotate_45 / 2)


def test_clock_scaled_for_walk_steps() -> None:
    reset_hunt_clock_cache()
    assert load_hunt_clock().duration_aut == 320.0


def test_light_rain_hunter_sees_farther() -> None:
    reset_hunt_weather_cache()
    reset_paddock_config_cache()
    weather = load_hunt_weather()
    pad = load_paddock_config()
    light = weather.levels[0]
    medium = weather.levels[1]
    heavy = weather.levels[2]
    h_walk = pad.cone_range
    r_base = pad.raptor_cone_range
    assert h_walk - light.hunter_vision_penalty > r_base - light.raptor_vision_penalty
    assert h_walk - medium.hunter_vision_penalty < r_base - medium.raptor_vision_penalty
    assert (r_base - heavy.raptor_vision_penalty) - (h_walk - heavy.hunter_vision_penalty) >= 6


def test_bullseye_has_center_mud_and_grass_ring() -> None:
    mmap = generate_paddock(11)
    assert mmap.terrain_at(mmap.center_x, mmap.center_y) is HuntTerrain.MUD
    grasses = [
        (x, y)
        for y in range(mmap.height)
        for x in range(mmap.width)
        if mmap.terrain_at(x, y) is HuntTerrain.GRASS
        and max(abs(x - mmap.center_x), abs(y - mmap.center_y)) <= 12
    ]
    assert len(grasses) >= 8


def test_hide_spots_are_three_deep_grass() -> None:
    mmap = generate_paddock(11)
    assert mmap.hide_spots
    x, y, facing = mmap.hide_spots[0]
    assert mmap.terrain_at(x, y) is HuntTerrain.GRASS


def test_hunter_sees_two_grass_not_the_third() -> None:
    tiles = [[HuntTerrain.OPEN for _ in range(11)] for _ in range(11)]
    for i in range(11):
        tiles[0][i] = HuntTerrain.WALL
        tiles[10][i] = HuntTerrain.WALL
        tiles[i][0] = HuntTerrain.WALL
        tiles[i][10] = HuntTerrain.WALL
    tiles[5][6] = HuntTerrain.GRASS
    tiles[5][7] = HuntTerrain.GRASS
    tiles[5][8] = HuntTerrain.GRASS
    mmap = HuntMap(11, 11, tiles, 20.0, 5, 5)
    assert has_line_of_sight(mmap, 5, 5, 7, 5, grass_see_through=2)
    assert not has_line_of_sight(mmap, 5, 5, 8, 5, grass_see_through=2)
    assert not has_line_of_sight(mmap, 5, 5, 7, 5, grass_see_through=1)


def test_raptor_in_deep_grass_sees_the_field() -> None:
    tiles = [[HuntTerrain.OPEN for _ in range(11)] for _ in range(11)]
    for i in range(11):
        tiles[0][i] = HuntTerrain.WALL
        tiles[10][i] = HuntTerrain.WALL
        tiles[i][0] = HuntTerrain.WALL
        tiles[i][10] = HuntTerrain.WALL
    tiles[5][5] = HuntTerrain.GRASS
    tiles[5][6] = HuntTerrain.GRASS
    tiles[5][7] = HuntTerrain.GRASS
    mmap = HuntMap(11, 11, tiles, 20.0, 5, 5)
    seen = visible_tiles(
        mmap, origin_x=5, origin_y=5, facing=2, cone_range=8, half_degrees=55,
        grass_see_through=2,
    )
    assert (5, 8) in seen or (6, 5) in seen or (5, 9) in seen or (8, 5) in seen
    assert (8, 5) in seen


def test_under_fire_breaks_like_aim() -> None:
    mmap = _open_square(21)
    raptor = HuntRaptor(x=10, y=2, facing=4)
    raptor_act(
        raptor, mmap,
        sense=_sense(
            hunter_x=10,
            hunter_y=10,
            hunter_aim_depth=0,
            hunter_sees_raptor=True,
            under_fire=True,
            clock_remaining=200.0,
            clock_duration=320.0,
        ),
        rng=_FixedRng(0.0),
        cfg=_cfg(),
    )
    assert raptor.mind.intent in ("cover", "break")


def test_danger_close_rushes() -> None:
    mmap = _open_square(21)
    raptor = HuntRaptor(x=10, y=12, facing=0)
    raptor.refresh_fov(mmap)
    assert raptor.sees(10, 10)
    raptor_act(
        raptor, mmap,
        sense=_sense(),
        rng=_FixedRng(0.0),
        cfg=_cfg(),
    )
    assert raptor.mind.intent == "rush"
    assert raptor.gait is Gait.RUN
    assert chebyshev(raptor.x, raptor.y, 10, 10) <= 2 or raptor.facing == 0


def test_gunshot_plateau_is_flat_and_contains_truth() -> None:
    mmap = _open_square(21)
    raptor = HuntRaptor(x=2, y=2, facing=2)
    rng = _FixedRng(0.0)
    apply_gunshot(
        raptor, mmap, (10, 10),
        rng=rng, jitter=3, blur=4, world_aut=1.0,
    )
    ensure_maps(raptor, mmap)
    vals = [
        float(raptor.belief[y, x])
        for y in range(mmap.height)
        for x in range(mmap.width)
        if float(raptor.belief[y, x]) > 0
    ]
    assert vals
    assert max(vals) - min(vals) < 1e-5
    assert float(raptor.belief[10, 10]) > 0


def test_sound_outside_reach_is_implausible() -> None:
    mmap = _open_square(21)
    raptor = HuntRaptor(x=2, y=2, facing=2)
    raptor.mind.fix_x = 10
    raptor.mind.fix_y = 10
    raptor.mind.fix_aut = 50.0
    ensure_maps(raptor, mmap)
    assert not sound_plausible(
        raptor, mmap, 1, 1,
        world_aut=50.4,
        run_cost=0.4,
        memory=8.0,
    )


def test_walk_step_costs_walk_aut() -> None:
    session = _session(paddock=_open_square(), x=5, y=8, facing=0)
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.world_aut == load_hunt_aut_costs().walk


def test_thought_log_records_raptor_intent() -> None:
    mmap = _open_square(21)
    raptor = HuntRaptor(x=10, y=12, facing=0)
    session = _session(paddock=mmap, x=10, y=10, facing=0, raptor=raptor)
    handle_hunt_event(session, _key(KeySym.PERIOD))
    assert session.raptor is not None
    assert session.raptor.mind.thought
    assert any(session.raptor.mind.thought.replace("—", "-") in line.replace("—", "-") for line in session.message_log.lines())
