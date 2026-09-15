"""Rain cycle, mud prints, and movement-sound clues."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import attrs

from src.constants import DATA_DIR
from src.hunt_aut import tenths

HUNT_WEATHER_PATH = DATA_DIR / "hunt_weather.json"

GAIT_SOUND_CHANCE: dict[str, float] = {
    "run": 1.00,
    "quick": 0.67,
    "walk": 0.33,
    "sneak": 0.00,
}
RAIN_SOUND_DELTA: dict[str, float] = {
    "light": 0.0,
    "medium": -0.10,
    "heavy": -0.20,
}


def move_sound_chance(gait: str, rain_id: str) -> float:
    """Chance a step makes a sound. Sneak stays silent in every rain."""
    base = GAIT_SOUND_CHANCE.get((gait or "walk").lower(), 0.33)
    if base <= 0.0:
        return 0.0
    return max(0.0, min(1.0, base + RAIN_SOUND_DELTA.get(rain_id, 0.0)))

# light -> medium -> heavy -> medium -> ...
_CYCLE = (0, 1, 2, 1)


@attrs.define(frozen=True)
class RainLevel:
    level_id: str
    label: str
    hunter_vision_penalty: int
    raptor_vision_penalty: int
    hear_range: int
    hide_sound_chance: float
    false_alarm_chance: float
    prints_outside_fov: bool
    print_ttl: float
    audio: float
    hunter_grass_see: int = 2
    raptor_grass_see: int = 2


@attrs.define(frozen=True)
class HuntWeatherConfig:
    cycle_aut: float
    audio_fade: float
    layer_crossfade_seconds: float
    loop_crossfade_seconds: float
    levels: tuple[RainLevel, ...]
    gait_hide_adjust: dict[str, float]


@attrs.define
class MudPrint:
    x: int
    y: int
    facing: int
    owner: str
    placed_aut: float
    ttl: float = 16.0


@attrs.define
class SoundMark:
    x: int
    y: int
    false_alarm: bool
    expires_aut: float


def _parse_level(raw: dict) -> RainLevel:
    return RainLevel(
        level_id=str(raw.get("id", "rain")),
        label=str(raw.get("label", "rain")),
        hunter_vision_penalty=int(raw.get("hunter_vision_penalty", 0)),
        raptor_vision_penalty=int(raw.get("raptor_vision_penalty", 0)),
        hear_range=int(raw.get("hear_range", 8)),
        hide_sound_chance=float(raw.get("hide_sound_chance", 0.3)),
        false_alarm_chance=float(raw.get("false_alarm_chance", 0.1)),
        prints_outside_fov=bool(raw.get("prints_outside_fov", False)),
        print_ttl=float(raw.get("print_ttl", 16.0)),
        audio=float(raw.get("audio", 0.5)),
        hunter_grass_see=int(raw.get("hunter_grass_see", 2)),
        raptor_grass_see=int(raw.get("raptor_grass_see", 2)),
    )


@lru_cache(maxsize=1)
def load_hunt_weather(path: Path | None = None) -> HuntWeatherConfig:
    p = path if path is not None else HUNT_WEATHER_PATH
    raw = json.loads(p.read_text(encoding="utf-8"))
    levels = tuple(
        _parse_level(item)
        for item in raw.get("levels", [])
        if isinstance(item, dict)
    )
    if not levels:
        levels = (_parse_level({"id": "medium", "label": "rain"}),)
    gait = raw.get("gait_hide_adjust", {})
    gait_adj = {str(k): float(v) for k, v in gait.items()} if isinstance(gait, dict) else {}
    return HuntWeatherConfig(
        cycle_aut=tenths(raw.get("cycle_aut", 10.0)),
        audio_fade=float(raw.get("audio_fade", 0.3)),
        layer_crossfade_seconds=float(raw.get("layer_crossfade_seconds", 3.0)),
        loop_crossfade_seconds=float(raw.get("loop_crossfade_seconds", 6.0)),
        levels=levels,
        gait_hide_adjust=gait_adj,
    )


def reset_hunt_weather_cache() -> None:
    load_hunt_weather.cache_clear()


def rain_index_at(
    world_aut: float,
    cfg: HuntWeatherConfig | None = None,
    *,
    cycle_aut: float | None = None,
) -> int:
    cfg = cfg if cfg is not None else load_hunt_weather()
    cycle = max(0.1, float(cycle_aut) if cycle_aut is not None else cfg.cycle_aut)
    step = int(world_aut / cycle) % len(_CYCLE)
    return _CYCLE[step]


def rain_level_at(
    world_aut: float,
    cfg: HuntWeatherConfig | None = None,
    *,
    cycle_aut: float | None = None,
) -> RainLevel:
    cfg = cfg if cfg is not None else load_hunt_weather()
    idx = rain_index_at(world_aut, cfg, cycle_aut=cycle_aut)
    return cfg.levels[idx % len(cfg.levels)]


def aut_until_light(world_aut: float, *, cycle_aut: float) -> float:
    """AUT until the next light-rain phase (0 if already light)."""
    cycle = max(0.1, cycle_aut)
    step = int(world_aut / cycle) % len(_CYCLE)
    if _CYCLE[step] == 0:
        return 0.0
    for i in range(1, 8):
        nxt = (step + i) % len(_CYCLE)
        if _CYCLE[nxt] == 0:
            boundary = (int(world_aut / cycle) + i) * cycle
            return max(0.0, boundary - world_aut)
    return cycle * 4.0


def fade_audio(current: float, target: float, fade: float) -> float:
    return current + (target - current) * fade
