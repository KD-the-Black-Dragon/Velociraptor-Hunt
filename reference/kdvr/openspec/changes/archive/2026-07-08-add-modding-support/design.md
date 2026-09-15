# Design: Full modding support

| Field | Value |
|-------|-------|
| **Author** | Systems Design (with lead designer) |
| **Date** | 2026-07-08 |
| **Status** | Draft — awaiting user approval before code |
| **Change id** | `add-modding-support` |
| **Spec target** | New `openspec/specs/modding/spec.md` (on final acceptance) |
| **Depends on** | `src/user_data.py`, data loaders, Options menu, save store, crash report stub |

**Historical notes:** Former stock-tree edit docs live in `openspec/changes/deferred-add-modding-support/design.md` (not the player contract).

---

## Summary

Ship official **JSON-only** modding: discover folders under `{user_data}/mods/`, persist enable + load order in per-mod `mod.state`, load **core then mods**, replace content by rules below, expose **Options → Mods**, reload all game data when leaving Mods, and keep runs bound to one mod setup.

---

## Resolved decisions

| # | Topic | Decision |
|---|--------|----------|
| 1 | Mods during save / run | Allow opening Mods from Options (including during PLAY). If an **autosave exists**, show a capital-**Y** warning: entering Mods **deletes the current saved game** (full autosave chain). Confirming ends any active run (return path toward main menu after Mods / reload). Entering Mods = permission to wipe that save. No separate “abandon run” feature. |
| 2 | Mods UI | List mods; **enable/disable**; **Up/Down reorder**; rewrites `mod.state` files. |
| 3 | Non-id files | **`dungeon_spawn.json`**, **`rescue_gratitude.json`**, **`ui_layout.json`**: if present in a mod, **whole file replaces** the previous layer. |
| 4 | Broken mod JSON | **Do not fail silently.** Show a **Windows error popup** (same class of dialog as stock startup JSON errors — see `src/debug/startup_error.py`) naming **which mod** (folder) and **which file** failed, plus a short reason. **Skip** that file (or that mod’s contribution for that domain); continue with core + remaining mods. Still do not hard-crash the whole game for bad mods. Stock core still hard-fails if core itself is broken. Also append to a log (reuse or mirror `startup_error.log` / session-friendly trail) so the message is recoverable after dismissing the dialog. |
| 5 | Save vs mods | Run pins **exact mod setup**. Load Game with missing/disabled/reordered-incompatible setup **refuses load**, player stays on **main menu** (restore mods via Explorer or New Game). Normal path: UI entry to Mods already deleted the save. |
| 6 | JSON scope | All 11 current `data/*.json` files (see below). Not: tileset, fonts, SCHEMA, Readme. |
| 7 | State file | Per mod: `mod.state` with `E`/`D` + integer order (case-insensitive letter). Missing/unreadable/malformed/contradictory → throw out and regenerate (Enabled, end of list; conflicts renumber sensibly). |
| 8 | Default enable | Newly discovered mods default **Enabled**. |
| 9 | Core precedence | Install `data/` **always** loads first. Later enabled mod wins on id (or whole-file layer). |
| 10 | Partial mods | Mod may ship any subset of the 11 filenames; missing files mean “no change for that layer.” |
| 11 | Mods root | `{user_data}/mods/` via `src/user_data.py` (same tree as saves/settings). |
| 12 | Reload trigger | On **exit** from Mods submenu: full game-data reload (as if restart) for all registries/caches that hold JSON content. |

---

## In-scope data files

| File | Merge rule |
|------|------------|
| `entities.json` | By entity `id` — later replaces earlier definition entirely |
| `weapons.json` | By item `id` |
| `armor.json` | By item `id` |
| `potions.json` | By item `id` |
| `wands.json` | By item `id` |
| `floor_runes.json` | By rune `id` |
| `macguffins.json` | By macguffin `id` |
| `names.json` | By entity id key in `names` object — later pool replaces earlier pool for that key |
| `dungeon_spawn.json` | Whole file replace if mod provides file |
| `rescue_gratitude.json` | Whole file replace if mod provides file |
| `ui_layout.json` | Whole file replace if mod provides file |

**Schema:** Mod files use the same `schema_version` and shapes as core (see `data/SCHEMA.md`). Invalid schema → popup + skip per decision 4.

---

## Package layout

```text
{user_data}/mods/
  CoolWolves/
    mod.state          # e.g. "E 2"
    entities.json     # optional
    weapons.json      # optional
    ...
  AnotherMod/
    mod.state
    dungeon_spawn.json
```

- **Mod id** = folder name (must be a directory; ignore loose files at mods root).
- No separate manifest required in v1 beyond `mod.state` + optional JSON files.
- Empty folder with only regenerated `mod.state` is a no-op content mod (still listed).

### `mod.state` format

```text
E 2
```

| Token | Meaning |
|-------|---------|
| `E` / `D` | Enabled / Disabled (case-insensitive) |
| integer | Relative load order (lower loads earlier among mods; core still first) |

**Repair rules:**

1. Missing file → create `E <max_existing_order + 1>` (or `E 1` if none). First-time discovery of many mods: assign orders alphabetically by folder name.
2. Unreadable / not exactly two tokens / bad letter / non-integer → regenerate as Enabled with a unique order (append).
3. Duplicate orders among mods → stable sort by `(order, folder_name)`, renumber `1..N`, rewrite all affected `mod.state` files.
4. Extra junk lines → treat as malformed → regenerate.

Only **enabled** mods participate in content load; disabled still appear in the Mods UI.

---

## Load pipeline

```text
1. Ensure mods root exists (mkdir ok).
2. Scan subfolders; ensure each has valid mod.state (repair as needed).
3. Sort enabled mods by (order, name).
4. For each data domain:
   a. Load core file from install DATA_DIR.
   b. For each enabled mod in order: if mod has that filename, parse and apply merge rule.
5. Publish registries; clear any module-level caches so reload is real.
6. Record active load list for crash reports and for new-game save pinning.
```

**Performance:** Load once at startup and on Mods exit — not per frame. O(mods × files) at those moments only; fine for small mod counts. Avoid re-reading disk every turn.

**Caching:** Today several loaders cache default registries (`_default_registry`, etc.). Reload must invalidate all of them (single `reload_game_data()` or equivalent coordinator).

**Startup validation:** Core `entities.json` hard-fail path remains. Mods: soft skip **after** an explicit player-visible error dialog (and log). Multiple bad files → one dialog per failure **or** one dialog listing all failures (prefer **one dialog that lists every failed mod/file** if several fail in the same load pass, so the player is not click-bombed). Do not block play after dismiss; do not leave failures silent.

### Bad mod popup (draft copy)

```text
Mod data error

Mod: Cool_Dragon_Mod
File: entities.json
Problem: <short parse/validation reason>

That file was skipped. Other game data still loaded.
```

Reuse/extend `show_startup_error_dialog` (or a sibling) so packaging on Windows still gets a native MessageBox-style warning. Non-Windows: best-effort equivalent (stderr + same log); still never silent.

---

## UI

### Options → Mods

- New row on Options: **Mods** (opens submenu), consistent with existing Options navigation style.
- Mods list: one row per discovered mod folder — display name = folder name; show Enabled/Disabled; highlight reorder + toggle.
- **Left/Right** or **Enter**: toggle E/D (rewrite `mod.state`).
- **Up/Down**: move highlight; with a modifier or dedicated keys for **reorder** — prefer: highlight on mod, **Shift+Up/Down** or **[/]** / explicit “Move up/down” if Shift is awkward in tcod — **implementation choice:** use **Left/Right** for toggle and **`<` / `>`** or **`,` / `.`** for reorder, *or* Up/Down to move selection and **PageUp/PageDown** to reorder. Pick one scheme in PR3 and document in README; keep keyboard-only and consistent with project UX.
- **Escape**: leave Mods → **reload all JSON** → return to Options (or main menu if run was ended).

### Save wipe gate (capital Y)

When the player activates **Mods** and `SaveStore` reports any autosave chain present:

1. Show a standard Y/n-style modal (same capital-**Y** pattern as other destructive confirms in the game).
2. Copy intent: changing/entering mods with a save will **delete the saved game**; ask to proceed.
3. **Y** → delete full autosave chain (`SaveStore.clear` / equivalent); if `App` is in PLAY, end the run (dispose engine, phase back so player cannot continue that run); enter Mods.
4. **n** / Escape → stay on Options; no delete; no Mods.

If **no** autosave files exist: enter Mods with no modal.

**Mid-run without save files:** rare; if PLAY but no save, still end the run when leaving Mods after any config change *or* always end PLAY when Mods was entered — simpler rule: **if PLAY when Mods is confirmed open, always end the run** (save already wiped if it existed). Player should not continue a live session after mod menu.

### Reload on exit

Leaving Mods always reloads data (even if nothing changed) — simple and matches “as if restarting” for data. Cheap at human UI timescale.

---

## Save / load coupling

### Pin on write

Autosave (and any save payload) stores a **mod fingerprint**, e.g.:

```json
"mods": {
  "enabled_in_order": ["CoolWolves", "HardMode"]
}
```

Exact schema field names are implementation detail; must be stable once shipped.

### Load checks

Before restoring a save into PLAY:

1. Read fingerprint from save.
2. Compare to **current** enabled-in-order list (after discovery/repair).
3. If mismatch **or** any fingerprinted mod folder missing **or** content load would lack defs needed — **refuse load**.
4. UX: friendly message (missing/changed mods); remain on **main menu**. Do not delete the save file automatically on failed load (player may restore the mod via Explorer and try again).

If fingerprint missing (pre-modding saves): treat as `enabled_in_order: []` (vanilla only). Vanilla saves load only when no enabled mods **or** when we define “empty fingerprint requires zero enabled mods.” **Decision:** pre-mod saves require **no enabled mods** to load; if any mod is enabled, refuse (mod setup changed relative to vanilla run). Alternatively allow load when mods are enabled but only additive — **rejected**; exact setup must match. Pre-mod = empty list; enable any mod → refuse those old saves until mods disabled.

### New Game

Uses current enabled mod stack; first autosave writes fingerprint.

---

## Error handling

| Case | Behavior |
|------|----------|
| Bad mod JSON | **Windows error popup** with mod folder + filename + reason; skip that contribution; continue load; log the same text |
| Bad core JSON | Existing hard-fail (entities) / existing loader behavior |
| Unknown fields in mod | Same as core: warn, ignore (not a hard error; no error popup required for unknown fields alone) |
| Mods directory unreadable | Treat as no mods; do not crash |
| `mod.state` write fails | Best-effort; surface in UI if toggle fails |
| Save delete fails | Do not enter Mods; show error (avoid orphan “in Mods but save still loadable” if possible) |

---

## Diagnostics

- Crash report `Loaded mods:` → comma-separated enabled mod folder names in load order, or `(none)`.
- Session log: optional milestone on startup / after Mods reload listing enabled mods (nice-to-have in docs PR).

---

## Architecture sketch

```text
src/user_data.py          # MODS_DIR = USER_DATA_DIR / "mods"
src/mods/
  __init__.py
  paths.py                # mod root helpers
  state.py                # mod.state read/write/repair, load order
  discovery.py            # scan folders → ModInfo list
  pipeline.py             # apply layers for each domain
  reload.py               # invalidate caches + reload_game_data()
src/data/*_loader.py      # accept optional multi-path or layered parse hooks
src/mods_menu.py          # UI state + render + input (or under src/ui/)
src/options_menu.py       # Mods row → open submenu / gate
src/save/*                # fingerprint field + load gate
src/debug/context.py      # real loaded_mods string
```

**Loader strategy (engineering choice):** Prefer a thin layer that:

1. Loads core raw JSON (or registry).
2. For each mod file, loads raw JSON and merges into a working structure.
3. Runs existing `parse_*` once on the merged result **or** reuses parse-per-file then dict-merge by id.

Avoid duplicating validation logic. Keep entity validation user-facing path aware of multi-source errors (attribute messages to mod folder when possible).

**Tests:** temp `KDS_USER_DATA_DIR`; fixture mod folders; no dependency on live balance numbers in install `data/` beyond smoke “core loads.”

---

## PR plan (overview)

| PR | Deliverable |
|----|-------------|
| **PR0** | This proposal/design/tasks; AGENTS pointer; supersede deferred notice |
| **PR1** | `MODS_DIR`, discovery, `mod.state` repair, order resolution, unit tests (no merge) |
| **PR2** | Layered load for **entities only**; cache invalidation; override + bad-mod popup (mod+file) + skip tests |
| **PR3** | Options → Mods UI; reorder/toggle; capital-Y save wipe + end run; reload on exit |
| **PR4** | Id catalogs: weapons, armor, potions, wands, floor_runes, macguffins, names |
| **PR5** | Whole-file: dungeon_spawn, rescue_gratitude, ui_layout |
| **PR6** | Save fingerprint + Load Game refusal; crash Loaded mods; README/SCHEMA |
| **PR7** | Acceptance polish, full checklist, archive |

PR boundaries may slip slightly (e.g. fingerprint earlier if PR3 needs it) but **do not** implement later PRs before prior sign-off.

---

## Non-goals (restate)

- Code injection, DLL mods, custom Python
- Asset packs (tiles/fonts)
- Deep merge of spawn bands or gratitude lines
- Cloud/mod browser
- Keeping a run alive across mod changes

---

## Open implementation details (agent may choose; no designer input required)

| Detail | Default lean |
|--------|----------------|
| Reorder keys in Mods UI | **Page Up / Page Down** (and keypad 9/3); Left/Right/Enter toggle enable |
| Skip granularity | Prefer skip single file; if parse is all-or-nothing per registry, skip whole mod contribution for that domain |
| Fingerprint only names vs names+order | **names in order** (order is part of exact setup) |
| Display name | Folder name only in v1 (no `name` in mod.state) |

---

## Player-facing copy (draft)

**Bad mod JSON (Windows error popup — not silent):** see Load pipeline draft; must name mod folder + file + problem.

**Mods entry warning (when save exists):**

```text
Entering the Mods menu will delete your current saved game.
The exact mod setup must stay the same for a run.

Proceed? [Y/n]
```

(Capital **Y** required; match existing confirm tone in the codebase.)

**Load refused:**

```text
Cannot load saved game: mods do not match this save.
Re-enable the same mods, or start a New Game.
```
