# Design: Save / Load System

**Note (post-archive):** Saves now live under `{user_data}/saves/` via `src/user_data.py` (not `data/saves/` in the project tree).

## Design philosophy

Saves exist so players can **pause and resume** a permadeath run — not to cheat defeat. One autosave chain, written safely in the background, restored with **no intentional state loss** at the last stable checkpoint. Crash or power loss may lose a few turns of progress; that is acceptable.

---

## Resolved decisions

| # | Decision |
|---|----------|
| 1 | **One save slot** — single active run; no slot picker |
| 2 | **Save directory** — `{user_data}/saves/` (via `src/user_data.py`) |
| 3 | **File set** — `autosave.json` (primary) + `autosave.bak1.json` … `autosave.bak3.json` (3 backups) |
| 4 | **Format** — versioned JSON (`save_format_version: 1`); UTF-8; pretty-print optional (compact on disk) |
| 5 | **Integrity** — each file includes `payload_sha256` over canonical JSON payload; corrupt files skipped on load |
| 6 | **Atomic write** — worker writes `autosave.tmp` → fsync → rotate chain → `os.replace` into primary |
| 7 | **Background saves** — dedicated worker thread (`threading.Thread` or `ThreadPoolExecutor(max_workers=1)`); main thread builds immutable snapshot, worker serializes + rotates |
| 8 | **Coalescing** — if a save is in flight, newer snapshots replace the queued one; only latest matters |
| 9 | **Idle command gate** — `can_issue_idle_command()` ≡ same conditions as today’s quit prompt (`modal_blocks_quit()` is **False**). When **True**, normal commands (move, Ctrl+Q, Ctrl+S) are allowed. When **False**, Ctrl+Q and Ctrl+S are **no-op** (no quit prompt, **no save**) |
| 10 | **Autosave cadence** — every **15 player turns** OR **30 seconds** since last successful save (whichever first), only when idle gate passes at player turn end |
| 11 | **Extra autosave triggers** — after successful `descend_floor()`; **every player turn end while player is `Engulfed`** (danger save; background) |
| 11b | **Ctrl+Q + save** — when idle gate passes, Ctrl+Q opens quit confirm **and** queues background save in the same moment; save runs even if user later presses **n**. If Ctrl+Q is no-op (modal blocks quit), **no save** |
| 11c | **Ctrl+S manual save** — when idle gate passes, **main-thread** synchronous save; message log **"Game saved."** on success. Blocked by same modals as Ctrl+Q. No-op when gate fails |
| 11d | **First save** — write autosave **immediately** when entering `PLAY` (new game after engine create; load game after successful restore updates slot in place) |
| 12 | **Load order** — try primary → bak1 → bak2 → bak3; first file that parses + validates wins |
| 13 | **Menu probe** — `SaveStore.probe()` runs on menu enter **before** rendering options. If no save: **Load Game omitted** from Up/Down cycle (Option B — not shown/selectable) |
| 14 | **New Game overwrite** — if probe finds valid save, New Game opens confirm modal: *"A saved game exists and will be overwritten. Proceed? (Y/n)"* — capital **Y** only; **n** or Escape → menu; save **not** deleted until name entry confirms and `GameEngine` is created |
| 15 | **Name entry cancel** — Escape from name entry returns to menu; existing saves remain |
| 16 | **Game Over wipe** — `GameOverState.open()` (digestion defeat) immediately deletes all autosave files (sync, best-effort) |
| 17 | **Quit to menu** — Ctrl+Q **Y** returns to menu (run remains resumable via Load Game); save was triggered on Ctrl+Q keypress |
| 18 | **Run prefs** — save includes `vore_content_prefs` + `ui_preset` id frozen at run start; Load restores these, not live `settings.json` |
| 19 | **Entity refs** — snapshot assigns stable integer `entity_id`; `Predator.prey`, modal lists, evoke targets use ids; remapped on load |
| 20 | **Ephemeral UI** — do not persist `log_overlay`, `help_overlay`, `quit_confirm`, `screen_flash.pending`, `skipped_this_phase`, `rest_session`; reset on load |
| 21 | **Mid-modal resume** — not guaranteed; load last stable checkpoint (acceptable loss). **Engulfed** state **is** persisted (strikes, predator, tags) |
| 25 | **Rest** — never persisted; any player command (including Ctrl+Q / Ctrl+S) cancels rest before save snapshot |
| 26 | **`{user_data}/saves/`** — per-user; manual backup allowed |
| 22 | **Content version** — save records `content_hash` optional metadata (entities.json mtime or version string) for diagnostics; load does not hard-fail in v1 |
| 23 | **Window close (X)** — out of scope for v1 unless trivial; Ctrl+Q is the supported quit-and-save path |
| 24 | **Cadence defaults approved** — 15 turns / 30s autosave; 3 rotating backups; mid-modal crash loads last checkpoint; window **X** not required in v1 |

---

## Save file layout

```text
{user_data}/saves/
  autosave.json       # primary (newest successful write)
  autosave.bak1.json  # previous primary
  autosave.bak2.json
  autosave.bak3.json  # oldest retained
  autosave.tmp        # transient write target (deleted after success)
```

### Rotation algorithm (on successful write)

```text
1. Validate serialized bytes + parse round-trip (optional quick decode)
2. Write bytes to autosave.tmp; fsync
3. Delete autosave.bak3.json (if exists)
4. Rename bak2 → bak3, bak1 → bak2, primary → bak1
5. Replace autosave.tmp → autosave.json (atomic where OS allows)
```

On Windows, use `os.replace` for same-volume atomic rename.

### Document envelope

```json
{
  "save_format_version": 1,
  "saved_at_unix": 1730000000,
  "payload_sha256": "…",
  "run": { … }
}
```

`run` holds the full game snapshot (see below).

---

## Snapshot contents (`run` payload)

Everything required to resume **exactly** where the player left off at the last stable checkpoint.

### Run metadata

| Field | Source |
|-------|--------|
| `player_name` | `GameEngine.player_name` |
| `player_turn_count` | `GameEngine.player_turn_count` |
| `floor_depth` | `GameEngine.floor_depth` |
| `vore_content_prefs` | `GameEngine.vore_content_prefs` (snapshot) |
| `ui_preset` | preset id from frozen `UILayout` / layout metadata |
| `rng_state` | `random.getstate()` |
| `close_door_pending` | `GameEngine.close_door_pending` |

### Map (`game_map`)

| Field | Notes |
|-------|-------|
| `width`, `height` | |
| `tiles` | int grid as nested list or flat array |
| `explored` | bool grid — **required** (vision progress) |
| `enter_xy` | downstairs/upstairs anchor |
| `layout_archetype` | procedural archetype id |

`visible` is **not** saved — recompute via `_update_fov()` on load.

### Message log

Serialize `message_log.entries()` — text, category, markup segments (same structure `LogEntry` uses today).

### Entities (ECS)

Array of records:

```json
{
  "id": 1,
  "tags": ["Player", "BlocksMovement", …],
  "components": {
    "Position": {"x": 10, "y": 20},
    "Fighter": { … },
    "AIState": { … deques as lists … },
    …
  }
}
```

**Include all entity types on the current floor:**

- Player: `Inventory`, `EquipState`, `PlayerProgression`, `Fighter`, `Mobility`, tags (`Engulfed`, `Stunned`, …), `DigestionStrikes` if engulfed
- NPCs: full `AIState` (deques → lists), `AbilityState`, `Fighter`, alignment, species, optional `ProperName`, `Predator` with `prey_id` + `narrative_type`, `VoreNarratives`, `DigestionStats`, etc.
- Floor items: `Item`, `Position`, `Renderable`, `ExamineDescription`
- Floor runes (unpicked): `FloorRune`, `Position`, …

**Exclude:** debug flags (`_debug_omniscient_vision`, `water_testing_mode`, `layout_archetype_force`).

### Modal / session state

At save checkpoints, blocking modals are **inactive** (idle gate). **v1:** do not persist `vore_modal`, `digestion_modal`, `game_over`, inventory/ground pickup modals, or `rest_session` — load assumes all closed. **Do** persist player **Engulfed** / `DigestionStrikes` / predator `Predator` component on NPC.

### Player pointer

`player_entity_id` — which entity id has the `Player` tag.

---

## Architecture

```text
src/save/
  schema.py          # version constants, envelope types
  snapshot.py        # GameEngine → SaveSnapshot (immutable dataclass / dict)
  restore.py         # SaveSnapshot → GameEngine.from_snapshot()
  store.py           # SaveStore: probe, load, save_bytes, rotate, delete_all
  coordinator.py     # SaveCoordinator: background thread, schedule, coalesce

src/app.py           # menu probe, load path, new-game confirm, quit save hook
src/menu.py          # Load Game disabled styling + input guard
src/engine.py        # checkpoint hooks after player turn / descent
```

```text
                    ┌─────────────────┐
  player turn end   │  GameEngine     │
  (stable)          │  build_snapshot │
        ──────────► └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ SaveCoordinator │◄── Ctrl+Q (with modal), autosave, engulfed
                    │  worker thread  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐     Ctrl+S (idle) ──► SaveStore (sync, main thread)
                    │ SaveStore.rotate│
                    │  {user_data}/saves/*   │
                    └─────────────────┘
```

### Idle command gate (`can_issue_idle_command`)

Shared by **Ctrl+Q**, **Ctrl+S**, and periodic autosave eligibility at turn end.

**No-op** (no quit, no save) when `modal_blocks_quit()` is **True**:

- `vore_modal` active
- `digestion_modal` active
- `game_over.active`
- `inventory_modal` / `ground_pickup_modal` open

Matches DCSS norm: quit/save only from idle command state.

**Additional autosave rule:** while player has `Engulfed` tag, queue background save **every player turn end** (even if 15-turn/30s throttle not met). Still requires idle gate at turn end (engulfed exploration between turns is idle).

**Rest:** not saved; player input cancels rest before snapshot is taken.

### Load path

```text
MENU --Load Game--> SaveStore.load_best()
  → GameEngine.from_snapshot(snapshot, floor_prefetch=…)
  → PLAY (skip name entry)
```

Cancel floor prefetch; reschedule from loaded `floor_depth` + `rng_state`.

### New Game path (save exists)

```text
MENU --New Game--> NEW_GAME_CONFIRM overlay
  Y → NAME_ENTRY → confirm name → delete_all_saves() → GameEngine(new) → PLAY
  n / Esc → MENU (saves intact)
```

### Game Over path

```text
digestion complete → game_over.open() → SaveStore.delete_all() (sync)
recap → menu (no save remains)
```

---

## Menu UX

### Load Game absent when no save

- Probe runs in `App._on_menu_enter()` → builds **visible menu options** list
- If no valid save: menu shows **four** options (New Game, High Scores, Options, Exit) — **Load Game omitted**; Up/Down never selects it
- If save exists: full five options including Load Game

### New Game confirm

Reuse quit-confirm pattern: overlay on menu, capital **Y** / lowercase **n**, error message on invalid key.

---

## PR plan

| PR | Scope |
|----|-------|
| **PR1** | Save schema v1; `snapshot` + `restore`; round-trip unit tests (memory only, no files) |
| **PR2** | `SaveStore` file I/O, rotation, SHA256 validate, load fallback chain, `delete_all` |
| **PR3** | `SaveCoordinator` background thread; idle gate; turn + timer + engulfed + descent triggers; initial save on PLAY |
| **PR4** | Menu probe (skip Load if absent); real load path; New Game overwrite modal; Ctrl+Q+save; **Ctrl+S** sync save + log line |
| **PR5** | Game Over wipe; `save-load` + `main-menu` spec updates; acceptance |

PR order: PR1 → PR2 → PR3 → PR4 → PR5 → Acceptance.

---

## PR1 — Snapshot / restore

### Tests

- New game → snapshot → restore → player position, floor depth, inventory slots match
- NPC with `AIState` deques + `Predator.prey` round-trip
- Map `explored` flags preserved
- `message_log` entries preserved
- `PlayerProgression` rune bonuses preserved

---

## PR2 — File store

### Tests

- Write + rotate produces primary + bak1..bak3
- Corrupt primary (bad hash) → load falls back to bak1
- `probe()` true when primary exists; false when directory empty
- `delete_all` removes all slot files

---

## PR3 — Background autosave

### Tests

- Coordinator receives snapshot; mock store called once per coalesced batch
- Autosave not called when vore modal active (stable gate)
- Turn counter triggers at interval
- Descent triggers save schedule

---

## PR4 — Menu integration

### Tests

- Menu shows Load disabled when no save
- Menu shows Load enabled when valid save
- New Game with save → confirm required; Escape preserves save
- New Game confirm Y + name → old saves deleted
- Ctrl+Q (idle only) opens quit + background save; cancel **n** keeps save; **Y** → menu
- Ctrl+S (idle only) sync save + "Game saved."; blocked during inventory/vore/etc.
- Engulfed player turn end triggers autosave
- Menu omits Load Game when no save file

---

## PR5 — Permadeath wipe + specs

### Tests

- `game_over.open()` deletes save files
- Load after game over finds no save

---

## Risk assessment

| Risk | Mitigation |
|------|------------|
| Large save files (80×44 map + entities) | Compact JSON; numpy lists; acceptable for v1 |
| Thread race with ECS mutation | Snapshot built on main thread at turn boundary; worker only serializes bytes |
| Windows atomic rename edge cases | Write tmp in same directory; `os.replace` |
| Entity ID remap bugs | Dedicated round-trip tests per component with references |
| Stale floor prefetch after load | Cancel + reschedule from loaded depth |
| Save during partial write (power loss) | Rotation keeps bak1..3; tmp file ignored by load |
| Schema drift when content JSON changes | `save_format_version`; document breaking changes |

---

## Manual playtest themes (acceptance)

- Play 20+ turns, quit with Ctrl+Q **Y**, Load Game → identical map/entities/inventory
- Kill process during play → Load Game recovers last autosave (some turn loss OK)
- Corrupt `autosave.json` manually → Load still works from bak1
- New Game with existing save → confirm; cancel name entry → save still loads
- Get digested → Load Game disabled; save files gone from disk