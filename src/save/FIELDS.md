# Save field inventory (format v1)

Authoritative agent checklist lives in `openspec/specs/save-load/spec.md`.  
This file is a quick map of the **in-memory run snapshot** (`build_run_snapshot` / `apply_run_snapshot`).

Envelope (file only): `save_format_version`, `saved_at_unix`, `payload_sha256`, `run`.

## Top-level `run` keys

| Key | Required on write | Missing on load → |
|-----|-------------------|-------------------|
| `save_format_version` | yes (1) | assumed current; migrate sets to current |
| `player_name` | yes | hard fail (required) |
| `player_turn_count` | yes | hard fail |
| `floor_depth` | yes | hard fail |
| `player_entity_id` | yes | hard fail if missing/invalid |
| `vore_content_prefs` | yes | hard fail |
| `game_map` | yes | hard fail |
| `entities` | yes | hard fail |
| `last_come_here_turn` | yes | **-1** |
| `difficulty_id` | yes | default difficulty via `validate_difficulty_id` |
| `ui_preset` | yes (encode) | active layout if omitted at `from_run_snapshot` |
| `rng_state` | yes | leave engine RNG as constructed |
| `close_door_pending` | yes | **False** |
| `message_log` | yes | **[]** |
| `run_stats` | yes | empty `RunStats` |
| `macguffin_discovery` | yes | empty discovery |
| `mods` | yes (fingerprint) | not re-applied mid-load here (fingerprint gate is store/menu) |

## `game_map`

| Key | Missing → |
|-----|-----------|
| `width`, `height`, `tiles`, `explored`, `enter_xy` | hard fail |
| `layout_archetype` | `""` |

## Entity record

| Key | Missing → |
|-----|-----------|
| `id` | hard fail |
| `tags` | **[]** (only `PERSISTED_TAGS` re-applied) |
| `components` | **{}** |

### Component defaults (selected)

| Component / field | Missing → |
|-------------------|-----------|
| `PlayerEffects` (whole) | `ensure_player_effects` after restore |
| `PlayerEffects.*` fields | 0 / None as in codec |
| `AIState.come_here` | **False** |
| `AIState.spawn_freeze_remaining` | **0** |
| `AIState.spawn_freeze_consumed` | **False** (legacy mid-floor NPCs clear on first tick) |
| `AIState.memory_blind_turns` / `memory_blind_limit` | **0** |
| `AIState` numeric fields | **0** / empty deques |
| `AbilityState.*` | False / 0 |
| `Inventory` item `stack_count` | **1** |
| `NpcPrefix` strings | `""` |
| `Predator.failed_struggles` | **0** |
| `PlayerProgression` bonuses/pieces | **0** / need floors default 1 (incl. `bonus_evade` / `pieces_evade*`) |

Unknown **item_id** / **SpeciesId** / prefix ids: soft-drop in `sanitize` after load (not corrupt).

## Ephemeral (never in snapshot)

Modals, overlays, rest session, FOV `visible`, debug toggles, macguffin victory confirm.

## Agent checklist (when touching persistence)

1. New **optional** state → encode if present; **default on load** if missing; test stripped snapshot.
2. New content only → no save change.
3. Removed/renamed **id** → soft-drop or dual-read; do not hard-fail load.
4. True wire break → bump `SAVE_FORMAT_VERSION` + step in `migrate.py` + **designer consult**.
