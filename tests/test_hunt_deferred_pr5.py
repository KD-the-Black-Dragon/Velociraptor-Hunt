"""PR5 (hunt-deferred): mud-only prints with per-print rain TTL."""

from __future__ import annotations

from tcod.event import KeySym

from src.hunt_map import HuntMap, HuntTerrain, is_mud
from src.hunt_weather import MudPrint, rain_level_at, reset_hunt_weather_cache
from src.hunt_session import handle_hunt_event
from tests.test_hunt_pr2 import _key, _open_square, _session


def _grass_square(size: int = 11) -> HuntMap:
    mmap = _open_square(size)
    mmap.tiles[4][5] = HuntTerrain.GRASS
    mmap.tiles[5][6] = HuntTerrain.BUSH
    return mmap


def _mud_square(size: int = 11) -> HuntMap:
    mmap = _open_square(size)
    for y in range(1, size - 1):
        for x in range(1, size - 1):
            mmap.tiles[y][x] = HuntTerrain.MUD
    return mmap


def test_mud_takes_prints_open_grassland_does_not() -> None:
    assert is_mud(HuntTerrain.MUD)
    assert not is_mud(HuntTerrain.OPEN)
    assert not is_mud(HuntTerrain.GRASS)
    assert not is_mud(HuntTerrain.BUSH)
    assert not is_mud(HuntTerrain.TREE)


def test_step_on_mud_always_leaves_a_print() -> None:
    session = _session(paddock=_mud_square(), x=5, y=5, facing=0)
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert any(p.x == 5 and p.y == 4 and p.owner == "hunter" for p in session.prints)


def test_step_on_open_grassland_leaves_no_print() -> None:
    session = _session(paddock=_open_square(), x=5, y=5, facing=0)
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.player_y == 4
    assert not any(p.x == 5 and p.y == 4 for p in session.prints)


def test_step_on_grass_or_bush_leaves_no_print() -> None:
    grass = _session(paddock=_grass_square(), x=5, y=5, facing=0)
    handle_hunt_event(grass, _key(KeySym.KP_8))
    assert grass.player_y == 4
    assert not any(p.x == 5 and p.y == 4 for p in grass.prints)
    bush = _session(paddock=_grass_square(), x=5, y=5, facing=2)
    handle_hunt_event(bush, _key(KeySym.KP_8))
    assert bush.player_x == 6
    assert not any(p.x == 6 and p.y == 5 for p in bush.prints)


def test_print_ttl_stamped_from_rain_at_placement() -> None:
    reset_hunt_weather_cache()
    session = _session(paddock=_mud_square(), x=5, y=5, facing=0)
    light_ttl = rain_level_at(0.0).print_ttl
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.prints
    assert session.prints[-1].ttl == light_ttl


def test_heavy_print_outlives_light_print_after_rain_changes() -> None:
    reset_hunt_weather_cache()
    light = rain_level_at(0.0)
    heavy = rain_level_at(20.0)
    assert heavy.print_ttl > light.print_ttl
    session = _session(paddock=_open_square(), x=5, y=5, facing=0)
    session.prints = [
        MudPrint(x=3, y=5, facing=0, owner="hunter", placed_aut=0.0, ttl=light.print_ttl),
        MudPrint(x=7, y=5, facing=0, owner="raptor", placed_aut=0.0, ttl=heavy.print_ttl),
    ]
    session.scheduler.world_aut = light.print_ttl + 1.0
    session._expire_clues()
    xs = {p.x for p in session.prints}
    assert 3 not in xs
    assert 7 in xs
