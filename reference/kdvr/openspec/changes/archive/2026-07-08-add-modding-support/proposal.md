# Proposal: Full modding support

**Status:** Active  
**Change id:** `add-modding-support`  
**Supersedes:** `openspec/changes/deferred-add-modding-support/` (stock `data/` edit notes only; no loader shipped)

## Why

The game is data-driven (`data/*.json`) but has no player-facing mod pipeline: no discovery path, no enable/disable UI, no load order, no safe override of core content. Deferred notes described editing the install tree, not official mods. Crash reports still stub `Loaded mods: (none)`.

The designer wants **full JSON mod capability**: every current game JSON file is extensible; core always loads first; later enabled mods replace by id (or whole file for non-id configs); Options → Mods controls enable/order; session data reloads when leaving Mods.

## What

1. **Mod root** — `{user_data}/mods/<mod_folder>/` with optional JSON files mirroring core filenames.
2. **Per-mod state** — `mod.state` (`E`/`D` + load-order integer); missing/corrupt → regenerate (Enabled, append; conflict repair).
3. **Load pipeline** — core install `data/` first, then enabled mods in order; id catalogs replace by id; three special files whole-replace when present.
4. **UI** — Options → Mods submenu: list, toggle enable, reorder; capital-**Y** gate when an autosave exists (entering Mods deletes that save and ends any active run).
5. **Reload** — leaving Mods reloads all JSON as if restarting the game.
6. **Resilience** — broken mod file is **not silent**: Windows error popup names mod + file + reason; that contribution is skipped; game continues with core + remaining mods.
7. **Saves** — runs pin the mod setup; Load Game refuses incompatible/missing mod content and leaves the player on the main menu.
8. **Diagnostics / docs** — real `Loaded mods` in crash reports; README + SCHEMA modding section.

## Phased delivery

Entities first (prove pipeline + UI), then remaining id catalogs, then whole-file configs, then docs/acceptance. See `tasks.md`.

## Out of scope (this change)

- Python/code mods, custom abilities beyond existing tokens
- Tileset, fonts, binary assets, `SCHEMA.md` / `Readme.txt` as moddable content
- Workshop/network distribution
- Merge semantics other than id-replace / whole-file replace (no deep merge of dungeon bands, etc.)
- Soft “apply next run without touching save” path

## Success

- Drop-in mod folders under user data work for all 11 JSON data files
- Core never removed; overrides only via later mods
- Mods UI is discoverable; enable/order persist; bad state files self-heal
- Changing mods via UI cannot keep an old save/run alive
- Explorer-disabled/deleted mods cannot silently load a broken save
- Tests cover discovery, order, override, UI gate, load refusal, reload
