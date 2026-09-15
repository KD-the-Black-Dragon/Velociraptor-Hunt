from __future__ import annotations

from pathlib import Path

import attrs

GAME_TITLE = "KD's Vore Roguelike"

# Root console width; height stays at legacy map+HUD until sidebar/status panels land.
# main.py uses runtime_console_dimensions() from src.ui.bootstrap for the real window.
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

MAP_WIDTH = 80
MAP_HEIGHT = 44

MAX_ROOMS = 30
ROOM_MIN_SIZE = 6
ROOM_MAX_SIZE = 10

FOV_RADIUS = 10

FLOOR_DEPTH_START = 1
FLOOR_DEPTH_MAX = 1000

# Map water generation — tune here; set WATER_TESTING_MODE True while playtesting aquatic content
WATER_FEATURE_CHANCE = 0.85
WATER_MIN_FEATURE_SIZE = 20
WATER_LAKE_ATTEMPTS = (1, 3)
WATER_RIVER_CHANCE = 0.70
WATER_PLACEMENT_RETRIES = 6
# Heavy water: always attempt features, smaller min size, more lakes/rivers, extra placement retries
WATER_TESTING_MODE = False
WATER_TESTING_FEATURE_CHANCE = 1.0
WATER_TESTING_MIN_FEATURE_SIZE = 12
WATER_TESTING_LAKE_ATTEMPTS = (3, 5)
WATER_TESTING_RIVER_CHANCE = 0.90
WATER_TESTING_PLACEMENT_RETRIES = 14

MIN_MONSTERS = 3
MAX_MONSTERS = 5
MONSTER_SPAWN_MIN_DISTANCE = 6
# New good allies: player-path steps from entrance (closed doors count as walkable).
GOOD_SPAWN_PATH_MIN = 10
GOOD_SPAWN_PATH_MAX = 15

# Per-instance buffs when a good ally follows the player downstairs (stacks each floor).
# Currently unused: apply call in engine_floor.descend_floor is commented out.
GOOD_FOLLOWER_DESCEND_MAX_HP = 5
GOOD_FOLLOWER_DESCEND_HP = 5
GOOD_FOLLOWER_DESCEND_MIN_DAMAGE = 1
GOOD_FOLLOWER_DESCEND_MAX_DAMAGE = 1
GOOD_FOLLOWER_DESCEND_RANGED_MIN_DAMAGE = 1
GOOD_FOLLOWER_DESCEND_RANGED_MAX_DAMAGE = 1
GOOD_FOLLOWER_DESCEND_ACCURACY = 0.03
GOOD_FOLLOWER_DESCEND_RANGED_ACCURACY = 0.03

# Map generation sanity (reject-and-retry thresholds)
MAX_GEN_ATTEMPTS = 50
MIN_SPAWN_CANDIDATE_COUNT = 30
MIN_LAND_TILE_COUNT = 400
MIN_PAIRWISE_SPREAD_BFS = 20

# Gameplay debug hotkeys (R/S/F2–F6 during PLAY) — False for release builds
DEBUG_GAMEPLAY_HOTKEYS_ENABLED = False

# Layout archetypes (PR1) — set LAYOUT_ARCHETYPE_FORCE for dev QA; F4 cycles at runtime
LAYOUT_ARCHETYPE_FORCE: str | None = None
LAYOUT_ARCHETYPE_BOXY_WEIGHT = 0.40
LAYOUT_ARCHETYPE_ORGANIC_WEIGHT = 0.40
LAYOUT_ARCHETYPE_HYBRID_WEIGHT = 0.20

# Doors (PR2)
DOOR_CORRIDOR_MOUTH_CHANCE = 0.55
DOOR_CHANCE_STDDEV = 0.10

RUNE_SPAWN_MIN_DISTANCE = 30
RUNES_PER_FLOOR = 3
RUNE_FLASH_RADIUS = 3

# Player / regen / vore / loot combat knobs live in data/global_tuning.json.
# Names below are provided via module __getattr__ (stock values unchanged at extraction).
# Hit check: accuracy - continuous_uniform(0, defender.evade) > 0.

HEALTH_POTION_HEAL = 10  # legacy unused; heal amounts come from potions.json

MESSAGE_LOG_CAPACITY = 100

# AI hot-path (fix-performance-ai-hotpath): memory sanitize at most every K player turns.
MEMORY_SANITIZE_INTERVAL = 2
# Distant AI throttle (PR2): Chebyshev radius R; busy floor when NPC count > N.
DISTANT_AI_RADIUS = 22
BUSY_FLOOR_NPC_THRESHOLD = 15

REST_UNTIL_MAX_TURNS = 100
REST_FRAME_SLEEP_SECONDS = 0.016

VORE_ENABLED = True
VORE_ADJACENCY_REQUIRED = True

VORE_NARRATIVE_TYPES_V1: tuple[str, ...] = ("OV", "CV", "AV")

# Lazy exports from data/global_tuning.json (import-time values match stock JSON).
_GLOBAL_TUNING_EXPORTS: dict[str, object] = {
    "PLAYER_MAX_HP": lambda t: t.player.max_hp,
    "PLAYER_ACCURACY": lambda t: t.player.accuracy,
    "PLAYER_EVADE": lambda t: t.player.evade,
    "PLAYER_AC": lambda t: t.player.ac,
    "PLAYER_MIN_DAMAGE": lambda t: t.player.min_damage,
    "PLAYER_MAX_DAMAGE": lambda t: t.player.max_damage,
    "MAX_FLOOR_ITEM_PLACEMENTS": lambda t: t.loot.max_floor_item_placements,
    "MIN_FLOOR_POTIONS": lambda t: t.loot.min_floor_potions,
    "NATURAL_REGEN_HP": lambda t: t.regen.hp,
    "NATURAL_REGEN_EVERY_N_PLAYER_TURNS": lambda t: t.regen.every_n_player_turns,
    "EVIL_NATURAL_REGEN_EVERY_N_PLAYER_TURNS": lambda t: t.regen.evil_every_n_player_turns,
    "VORE_HP_THRESHOLD": lambda t: t.vore.hp_threshold,
    "VORE_HIT_MIN": lambda t: t.vore.hit_min,
    "VORE_HIT_MAX": lambda t: t.vore.hit_max,
    "VORE_ESCAPE_BASE": lambda t: t.vore.escape_base,
    "VORE_ESCAPE_PER_FAIL": lambda t: t.vore.escape_per_fail,
    "VORE_STRUGGLE_DAMAGE": lambda t: t.vore.struggle_damage,
}


def __getattr__(name: str) -> object:
    getter = _GLOBAL_TUNING_EXPORTS.get(name)
    if getter is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from src.data.global_tuning_loader import default_global_tuning

    return getter(default_global_tuning())  # type: ignore[operator]


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_GLOBAL_TUNING_EXPORTS))


@attrs.define(frozen=True)
class VoreContentPreferences:
    """Global initiation filter (OV / CV / AV). Snapshotted per run; not used for digestion follow-through."""

    enabled: frozenset[str] = frozenset(VORE_NARRATIVE_TYPES_V1)

    def is_enabled(self, narrative_type: str) -> bool:
        return narrative_type in self.enabled


DEFAULT_VORE_CONTENT_PREFS = VoreContentPreferences()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TILESET_PATH = DATA_DIR / "Alloy_curses_12x12.png"
TITLE_LOGO_PATH = PROJECT_ROOT / "images" / "logo.png"