"""Concurrent rain beds with weather crossfades and seamless self-loops.

Beds are *streamed* (not fully decoded). pygame.mixer.Sound of a 10-minute
MP3 materializes ~100 MB of PCM per file and freezes the UI; miniaudio
decodes a few milliseconds of audio at a time on the playback thread.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

import numpy as np

from src.constants import PROJECT_ROOT
from src.hunt_weather import load_hunt_weather

SOUNDS_DIR = PROJECT_ROOT / "Sounds"
RAIN_FILES: dict[str, str] = {
    "light": "LightRain.mp3",
    "medium": "MediumRain.mp3",
    "heavy": "HeavyRain.mp3",
}
LAYER_IDS: tuple[str, ...] = ("light", "medium", "heavy")
SAMPLE_RATE = 44100
CHANNELS = 2


def rain_sound_path(level_id: str, *, sounds_dir: Path | None = None) -> Path:
    folder = sounds_dir if sounds_dir is not None else SOUNDS_DIR
    name = RAIN_FILES.get(level_id, f"{level_id}.mp3")
    return folder / name


def layer_targets(level_id: str) -> dict[str, float]:
    """One layer at full volume; the others silent."""
    key = level_id if level_id in RAIN_FILES else "medium"
    return {lid: (1.0 if lid == key else 0.0) for lid in LAYER_IDS}


def approach_volume(current: float, target: float, dt: float, seconds: float) -> float:
    """Linear ramp so a weather swap takes `seconds` of wall-clock time."""
    if seconds <= 0.0:
        return target
    step = max(0.0, dt) / seconds
    delta = target - current
    if abs(delta) <= step:
        return target
    return current + (step if delta > 0.0 else -step)


def loop_overlap_due(elapsed: float, length: float, xfade: float) -> bool:
    """True when the playing voice is inside the tail window that should overlap."""
    if length <= xfade * 2.0 or elapsed < 0.0:
        return False
    remaining = length - elapsed
    return 0.0 < remaining <= xfade


def make_seamless_loop(samples: np.ndarray, xfade: int) -> np.ndarray:
    """Overlap the tail into the head so a loop does not click (offline helper)."""
    n = int(samples.shape[0])
    xfade = int(xfade)
    if xfade < 2 or n < xfade * 3:
        return samples
    data = samples.astype(np.float64, copy=False)
    t = np.linspace(0.0, 1.0, xfade, dtype=np.float64)
    fade_out = np.cos(t * (np.pi / 2.0))
    fade_in = np.sin(t * (np.pi / 2.0))
    if data.ndim == 2:
        fade_out = fade_out[:, None]
        fade_in = fade_in[:, None]
    out = np.array(data[xfade:], copy=True)
    out[-xfade:] = data[-xfade:] * fade_out + data[:xfade] * fade_in
    peak = np.max(np.abs(out))
    if peak > 32767.0:
        out *= 32767.0 / peak
    return out.astype(samples.dtype, copy=False)


class _LayerVoice:
    stream: Any = None
    frames: int = 0
    gain: float = 0.0


class HuntRainMixer:
    """Three looping beds; volumes follow the current rain id."""

    def __init__(self) -> None:
        self.volumes: dict[str, float] = {lid: 0.0 for lid in LAYER_IDS}
        self.target_id: str = "medium"
        self.enabled: bool = False
        self.missing: tuple[str, ...] = ()
        self._lock = threading.Lock()
        self._paths: dict[str, Path] = {}
        self._lengths: dict[str, float] = {}
        self._voices: dict[str, list[_LayerVoice]] = {
            lid: [_LayerVoice(), _LayerVoice()] for lid in LAYER_IDS
        }
        self._active: dict[str, int] = {lid: 0 for lid in LAYER_IDS}
        self._playing: bool = False
        self._last_tick: float | None = None
        self._device: Any = None
        self._device_failed: bool = False
        self._preload_started: bool = False
        self._sounds_dir: Path | None = None
        self._loop_s: float = 6.0

    def preload(self, *, sounds_dir: Path | None = None) -> None:
        """Open the audio device and probe file lengths. Safe to call more than once."""
        with self._lock:
            if sounds_dir is not None:
                self._sounds_dir = sounds_dir
            if self._preload_started:
                return
            self._preload_started = True
        self._ensure_device()
        self._probe_files()
        self._ensure_playback_running()

    def _ensure_device(self) -> bool:
        if self._device is not None:
            return True
        if self._device_failed:
            return False
        try:
            import miniaudio

            self._device = miniaudio.PlaybackDevice(
                output_format=miniaudio.SampleFormat.SIGNED16,
                nchannels=CHANNELS,
                sample_rate=SAMPLE_RATE,
                buffersize_msec=100,
                app_name="Velociraptor Hunt",
            )
            return True
        except Exception:
            self._device_failed = True
            self._device = None
            return False

    def _probe_files(self) -> None:
        folder = self._sounds_dir
        paths: dict[str, Path] = {}
        lengths: dict[str, float] = {}
        missing: list[str] = []
        info_fn = None
        try:
            import miniaudio

            info_fn = miniaudio.get_file_info
        except Exception:
            info_fn = None
        for lid in LAYER_IDS:
            path = rain_sound_path(lid, sounds_dir=folder)
            if not path.is_file():
                missing.append(lid)
                continue
            duration = 0.0
            if info_fn is not None:
                try:
                    duration = float(info_fn(str(path)).duration)
                except Exception:
                    duration = 0.0
            paths[lid] = path
            lengths[lid] = max(0.0, duration)
        with self._lock:
            self._paths = paths
            self._lengths = lengths
            self.missing = tuple(missing)
            self.enabled = bool(paths)

    def _open_stream(self, path: Path) -> Any:
        import miniaudio

        return miniaudio.stream_file(
            str(path),
            output_format=miniaudio.SampleFormat.SIGNED16,
            nchannels=CHANNELS,
            sample_rate=SAMPLE_RATE,
        )

    def _reset_voices(self) -> None:
        for lid in LAYER_IDS:
            for voice in self._voices[lid]:
                voice.stream = None
                voice.frames = 0
                voice.gain = 0.0
            self._active[lid] = 0

    def _open_primary_voices(self) -> None:
        self._reset_voices()
        with self._lock:
            paths = dict(self._paths)
        for lid, path in paths.items():
            try:
                stream = self._open_stream(path)
            except Exception:
                continue
            primary = self._voices[lid][0]
            primary.stream = stream
            primary.frames = 0
            primary.gain = 1.0

    def start(self, level_id: str, *, sounds_dir: Path | None = None) -> None:
        if sounds_dir is not None:
            self._sounds_dir = sounds_dir
        self.target_id = level_id if level_id in RAIN_FILES else "medium"
        cfg = load_hunt_weather()
        self._loop_s = max(0.05, cfg.loop_crossfade_seconds)
        self._probe_files()
        opened: dict[str, Any] = {}
        for lid, path in dict(self._paths).items():
            try:
                opened[lid] = self._open_stream(path)
            except Exception:
                continue
        with self._lock:
            self._reset_voices()
            for lid, stream in opened.items():
                primary = self._voices[lid][0]
                primary.stream = stream
                primary.frames = 0
                primary.gain = 1.0
            self.volumes = {lid: 0.0 for lid in LAYER_IDS}
            self._playing = True
            self._last_tick = time.monotonic()
        self._ensure_playback_running()

    def _ensure_playback_running(self) -> None:
        """Keep the device spinning so stop/start never waits on WASAPI teardown."""
        if not self._ensure_device():
            return
        device = self._device
        if device is None or getattr(device, "running", False):
            return
        gen = self._playback_generator()
        try:
            next(gen)
            device.start(gen)
        except Exception:
            pass

    def _playback_generator(self) -> Any:
        nframes = yield b""
        while True:
            mixed = self._render(int(nframes) if nframes else 1024)
            nframes = yield mixed

    def _read_voice(self, voice: _LayerVoice, nframes: int) -> np.ndarray:
        silence = np.zeros((nframes, CHANNELS), dtype=np.float32)
        stream = voice.stream
        if stream is None:
            return silence
        try:
            samples = stream.send(nframes)
        except StopIteration:
            voice.stream = None
            return silence
        except Exception:
            voice.stream = None
            return silence
        arr = np.asarray(samples, dtype=np.int16).ravel()
        need = nframes * CHANNELS
        if arr.size < need:
            padded = np.zeros(need, dtype=np.int16)
            padded[: arr.size] = arr
            arr = padded
            voice.stream = None
        stereo = arr[:need].reshape(nframes, CHANNELS).astype(np.float32)
        voice.frames += nframes
        return stereo

    def _maybe_overlap(self, lid: str, nframes: int) -> None:
        length = self._lengths.get(lid, 0.0)
        path = self._paths.get(lid)
        if path is None:
            return
        xfade = self._loop_s
        voices = self._voices[lid]
        active = self._active[lid]
        primary = voices[active]
        other = voices[1 - active]
        if primary.stream is None:
            try:
                primary.stream = self._open_stream(path)
            except Exception:
                return
            primary.frames = 0
            primary.gain = 1.0
            other.stream = None
            other.gain = 0.0
            return
        elapsed = primary.frames / float(SAMPLE_RATE)
        if other.stream is None and loop_overlap_due(elapsed, length, xfade):
            try:
                other.stream = self._open_stream(path)
            except Exception:
                other.stream = None
            else:
                other.frames = 0
                other.gain = 0.0
        if other.stream is not None:
            t = min(1.0, max(0.0, other.frames / max(1.0, xfade * SAMPLE_RATE)))
            primary.gain = 1.0 - t
            other.gain = t
            if t >= 1.0:
                primary.stream = None
                primary.gain = 0.0
                primary.frames = 0
                self._active[lid] = 1 - active

    def _render(self, nframes: int) -> np.ndarray:
        nframes = max(1, min(int(nframes), 16384))
        mixed = np.zeros((nframes, CHANNELS), dtype=np.float32)
        with self._lock:
            if not self._playing:
                return mixed.astype(np.int16)
            volumes = dict(self.volumes)
        # Decode outside the lock: the audio callback must not hold it while
        # the decoder releases the GIL, or Esc deadlocks against stop().
        for lid in LAYER_IDS:
            layer = volumes.get(lid, 0.0)
            self._maybe_overlap(lid, nframes)
            for voice in self._voices[lid]:
                if voice.stream is None and voice.gain <= 0.0:
                    continue
                chunk = self._read_voice(voice, nframes)
                gain = layer * voice.gain
                if gain <= 0.0:
                    continue
                mixed += chunk * gain
        return np.clip(mixed, -32767.0, 32767.0).astype(np.int16)

    def set_target(self, level_id: str) -> None:
        if level_id in RAIN_FILES:
            self.target_id = level_id

    def tick(self, *, level_id: str | None = None) -> None:
        if not self._playing:
            return
        now = time.monotonic()
        dt = 0.0 if self._last_tick is None else max(0.0, now - self._last_tick)
        self._last_tick = now
        if level_id is not None:
            self.set_target(level_id)
        cfg = load_hunt_weather()
        weather_s = max(0.05, cfg.layer_crossfade_seconds)
        self._loop_s = max(0.05, cfg.loop_crossfade_seconds)
        targets = layer_targets(self.target_id)
        with self._lock:
            for lid in LAYER_IDS:
                self.volumes[lid] = approach_volume(
                    self.volumes[lid], targets[lid], dt, weather_s,
                )

    def stop(self) -> None:
        """Mute immediately. Leave the audio device running so Esc is not a hitch."""
        with self._lock:
            self._playing = False
            self.volumes = {lid: 0.0 for lid in LAYER_IDS}
            self._reset_voices()
            self._last_tick = None


_mixer: HuntRainMixer | None = None


def hunt_rain_mixer() -> HuntRainMixer:
    global _mixer
    if _mixer is None:
        _mixer = HuntRainMixer()
    return _mixer


def preload_hunt_rain() -> None:
    hunt_rain_mixer().preload()


def start_hunt_rain(level_id: str) -> None:
    hunt_rain_mixer().start(level_id)


def stop_hunt_rain() -> None:
    hunt_rain_mixer().stop()


def tick_hunt_rain(level_id: str) -> None:
    hunt_rain_mixer().tick(level_id=level_id)


def hunt_rain_active() -> bool:
    return hunt_rain_mixer()._playing
