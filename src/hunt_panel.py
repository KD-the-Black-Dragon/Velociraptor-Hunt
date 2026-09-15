"""Right-side hunt panel: clock, ring, raptor slot, hunter stats, weather."""

from __future__ import annotations

from src.hunt_clock import RingState
from src.hunt_combat import chebyshev
from src.hunt_facing import facing_name
from src.hunt_raptor import HuntRaptor
from src.hunt_stance import SPEED_LABEL, Gait
from src.text import cp437_safe

PANEL_WIDTH = 26
STATUS_ROWS = 2
RAPTOR_SLOT_LINES = 5

_CLOCK_FG = (200, 200, 160)
_RING_FG = {
    RingState.HUNTER_WINNING: (120, 255, 140),
    RingState.CLOSE: (220, 200, 80),
    RingState.RAPTOR_WINNING: (220, 80, 60),
}
_RAPTOR_FG = (200, 80, 60)
_LIME_FG = (50, 255, 80)
_RANGE_FG = (255, 255, 80)
_MUTED_FG = (140, 140, 140)
_RAIN_FG = {
    "light": (80, 150, 255),
    "medium": (110, 80, 210),
    "heavy": (180, 70, 220),
}
_GAIT_STATE = {
    Gait.WALK: "Walking",
    Gait.QUICK: "Quick",
    Gait.RUN: "Running",
    Gait.SNEAK: "Sneaking",
}
_WEAPON_SHORT = {
    "rifle": "Rifle",
    "shotgun": "Shotgun",
    "revolver": "Revolver",
}


def map_view_size(console_width: int, console_height: int) -> tuple[int, int]:
    """Map viewport excluding the right panel and two status rows."""
    view_h = max(1, console_height - STATUS_ROWS)
    view_w = max(1, console_width - PANEL_WIDTH)
    return view_w, view_h


def hunt_log_tile_rect(
    console_width: int,
    console_height: int,
    *,
    top: int | None = None,
) -> tuple[int, int, int, int]:
    """Lower-right panel region for the proportional thought log (tile cells)."""
    view_w, view_h = map_view_size(console_width, console_height)
    # Below clock/ring/raptor/hunter/weather/range (range sits at row 19).
    log_top = 21 if top is None else top
    log_top = min(log_top, max(8, view_h - 4))
    x = view_w + 1
    w = max(1, PANEL_WIDTH - 2)
    h = max(3, view_h - log_top - 1)
    return x, log_top, w, h


_HEALTH_BANDS: tuple[tuple[str, int, int], ...] = (
    ("Weary", 0, 24),
    ("Wavering", 25, 59),
    ("Rattled", 50, 79),
    ("Steady", 75, 99),
    ("Perfect", 100, 100),
)


def health_percent(hp: int, max_hp: int) -> int:
    if max_hp <= 0:
        return 0
    return max(0, min(100, int(round(100.0 * hp / max_hp))))


def fuzzy_health_label(percent: int, previous: str | None = None) -> str:
    """Overlapping bands; keep the last label while percent stays inside it."""
    pct = max(0, min(100, int(percent)))
    names = [name for name, lo, hi in _HEALTH_BANDS if lo <= pct <= hi]
    if previous in names:
        return previous
    if pct >= 100:
        return "Perfect"
    if pct >= 80:
        return "Steady"
    if pct >= 60:
        return "Rattled"
    if pct >= 25:
        return "Wavering"
    return "Weary"


def raptor_readout(
    raptor: HuntRaptor,
    hunter_x: int,
    hunter_y: int,
) -> tuple[str, ...]:
    dist = chebyshev(raptor.x, raptor.y, hunter_x, hunter_y)
    facing = facing_name(raptor.facing)
    if raptor.sees(hunter_x, hunter_y):
        facing = f"{facing}!"
    if raptor.last_move_facing is None:
        state = "Standing"
    else:
        mode = _GAIT_STATE.get(raptor.gait, "Walking")
        state = f"{mode} {facing_name(raptor.last_move_facing)}"
    pct = health_percent(raptor.hp, raptor.max_hp)
    health = fuzzy_health_label(pct, raptor.shown_health)
    raptor.shown_health = health
    return (
        "Velociraptor",
        f"Distance: {dist}",
        f"Facing: {facing}",
        f"State: {state}",
        f"Health: {health}",
    )


def hunter_stat_lines(
    *,
    facing: str,
    weapon_id: str,
    weapon_name: str,
    ammo: int,
    gait: Gait,
    aim_depth: int,
    fatigue: int,
) -> tuple[str, ...]:
    weapon = _WEAPON_SHORT.get(weapon_id, weapon_name)
    speed = SPEED_LABEL.get(gait, gait.value)
    return (
        f"Facing: {facing}",
        f"Weapon: {weapon}",
        f"Ammo: {ammo}",
        f"Speed: {speed}",
        f"Aim level: {aim_depth}",
        f"Fatigue: {fatigue}",
    )


def render_hunt_panel(
    console,
    *,
    clock_label: str,
    ring: RingState,
    raptor_lines: tuple[str, ...] = (),
    hunter_lines: tuple[str, ...] = (),
    weather_label: str = "",
    weather_id: str = "medium",
    targeting_range: int | None = None,
) -> None:
    view_w, view_h = map_view_size(console.width, console.height)
    inner = max(1, PANEL_WIDTH - 1)
    origin_x = view_w
    if origin_x < console.width:
        for y in range(view_h):
            console.print(origin_x, y, "|", fg=_MUTED_FG)
    tx = origin_x + 1 if origin_x + 1 < console.width else origin_x

    def put(row: int, text: str, fg: tuple[int, int, int]) -> None:
        if 0 <= row < view_h:
            console.print(tx, row, cp437_safe(text)[:inner], fg=fg)

    put(1, clock_label, _CLOCK_FG)
    put(2, ring.value, _RING_FG[ring])
    raptor_row = 4
    for i, line in enumerate(raptor_lines[:RAPTOR_SLOT_LINES]):
        put(raptor_row + i, line, _RAPTOR_FG)
    personal_row = 4 + RAPTOR_SLOT_LINES + 1
    for i, line in enumerate(hunter_lines):
        put(personal_row + i, line, _LIME_FG)
    weather_row = personal_row + len(hunter_lines) + 1
    rain_fg = _RAIN_FG.get(weather_id, _RAIN_FG["medium"])
    if weather_label:
        put(weather_row, weather_label, rain_fg)
    if targeting_range is not None:
        put(weather_row + 2, f"Range: {targeting_range}", _RANGE_FG)
    log_top = weather_row + (4 if targeting_range is not None else 2)
    lx, ly, lw, lh = hunt_log_tile_rect(console.width, console.height, top=log_top)
    for row in range(ly, ly + lh):
        if 0 <= row < view_h:
            console.print(lx, row, " " * lw, fg=_MUTED_FG)
