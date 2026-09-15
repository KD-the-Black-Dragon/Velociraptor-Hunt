"""PR11 (hunt-deferred): rain layer crossfades and seamless self-loops."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from src.hunt_rain_audio import (
    HuntRainMixer,
    LAYER_IDS,
    approach_volume,
    layer_targets,
    loop_overlap_due,
    make_seamless_loop,
    rain_sound_path,
)
from src.hunt_weather import load_hunt_weather, reset_hunt_weather_cache


def test_layer_targets_are_exclusive() -> None:
    assert layer_targets("light") == {"light": 1.0, "medium": 0.0, "heavy": 0.0}
    assert layer_targets("medium") == {"light": 0.0, "medium": 1.0, "heavy": 0.0}
    assert layer_targets("heavy") == {"light": 0.0, "medium": 0.0, "heavy": 1.0}


def test_approach_volume_reaches_target_in_about_the_fade_time() -> None:
    value = 0.0
    dt = 0.05
    seconds = 1.0
    steps = 0
    while abs(value - 1.0) > 1e-9 and steps < 50:
        value = approach_volume(value, 1.0, dt, seconds)
        steps += 1
    assert abs(value - 1.0) < 1e-9
    assert 18 <= steps <= 22


def test_seamless_loop_hides_the_wrap() -> None:
    n = 1000
    xfade = 100
    # A ramp that would click hard if looped raw (end=1, start=0).
    samples = np.linspace(0.0, 1.0, n, dtype=np.float64)
    looped = make_seamless_loop(samples, xfade)
    assert looped.shape[0] == n - xfade
    # Last sample of the loop matches the sample just before the loop start.
    assert abs(float(looped[-1]) - float(samples[xfade - 1])) < 1e-6
    assert abs(float(looped[0]) - float(samples[xfade])) < 1e-9


def test_loop_overlap_window() -> None:
    assert loop_overlap_due(594.0, 600.0, 6.0)
    assert not loop_overlap_due(10.0, 600.0, 6.0)
    assert not loop_overlap_due(5.0, 8.0, 6.0)


def test_missing_files_do_not_crash(tmp_path: Path) -> None:
    mixer = HuntRainMixer()
    mixer.start("medium", sounds_dir=tmp_path)
    mixer.tick(level_id="heavy")
    mixer.stop()
    assert mixer.missing == LAYER_IDS or not mixer.enabled


def test_start_fades_in_from_silence(tmp_path: Path) -> None:
    mixer = HuntRainMixer()
    mixer.start("heavy", sounds_dir=tmp_path)
    assert mixer.volumes == {"light": 0.0, "medium": 0.0, "heavy": 0.0}
    mixer._last_tick = time.monotonic() - 3.0
    mixer.tick(level_id="heavy")
    assert mixer.volumes["heavy"] == 1.0
    assert mixer.volumes["light"] == 0.0
    mixer.stop()


def test_stop_does_not_wait_on_device_teardown() -> None:
    mixer = HuntRainMixer()

    class _FakeDevice:
        running = True

        def stop(self) -> None:
            time.sleep(0.3)
            self.running = False

    mixer._device = _FakeDevice()
    mixer._playing = True
    t0 = time.monotonic()
    mixer.stop()
    elapsed = time.monotonic() - t0
    assert elapsed < 0.05
    assert mixer._device.running is True
    assert mixer._playing is False


def test_start_does_not_block_on_decode(tmp_path: Path) -> None:
    mixer = HuntRainMixer()
    t0 = time.monotonic()
    mixer.start("light", sounds_dir=tmp_path)
    elapsed = time.monotonic() - t0
    assert elapsed < 0.25
    mixer.stop()


def test_opening_real_mp3s_is_not_a_full_decode() -> None:
    """Regression: fully decoding the 10-minute beds froze the window."""
    mixer = HuntRainMixer()
    t0 = time.monotonic()
    mixer._sounds_dir = None
    mixer._probe_files()
    if not mixer._paths:
        mixer.stop()
        return
    mixer._open_primary_voices()
    elapsed = time.monotonic() - t0
    mixer._reset_voices()
    assert elapsed < 0.5
    assert mixer._lengths.get("medium", 0.0) > 60.0


def test_sound_paths_point_at_the_dropped_mp3s() -> None:
    assert rain_sound_path("light").name == "LightRain.mp3"
    assert rain_sound_path("medium").name == "MediumRain.mp3"
    assert rain_sound_path("heavy").name == "HeavyRain.mp3"
    # Assets are in-tree for this PR; tests must not require decoding them.
    assert rain_sound_path("light").is_file()
    assert rain_sound_path("medium").is_file()
    assert rain_sound_path("heavy").is_file()


def test_weather_json_has_crossfade_seconds() -> None:
    reset_hunt_weather_cache()
    cfg = load_hunt_weather()
    assert cfg.layer_crossfade_seconds > 0.0
    assert cfg.loop_crossfade_seconds > 0.0
