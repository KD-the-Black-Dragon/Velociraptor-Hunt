# Design: 4K window size memory + position clamp

## Problem (current)

`App.apply_display_layout_from_settings` calls `enforce_minimum_window_size`, which **grows** the window to the new floor when 4K turns On but never **shrinks** when 4K turns Off. Meanwhile `sync_window_from_sdl` always writes live pixels into `client_width` / `client_height`, so the oversized 4K frame permanently overwrites the normal preference.

## Resolved decisions

| Topic | Decision |
|-------|----------|
| Scope of size/position rules | **Windowed only** — ignore while fullscreen |
| Dual size sets | `window.client_*` = normal; `window.four_k_client_*` = 4K; optional until first enable |
| First 4K enable | Seed `four_k_client_* = 2 ×` live windowed client size; apply; **do not** change `client_*` |
| Later toggles | Swap live size between the two sets (no re-doubling) |
| Resize while 4K On | Update **only** `four_k_client_*` (+ shared `x`/`y`) |
| Resize while 4K Off | Update **only** `client_*` (+ shared `x`/`y`) |
| Maximized + toggle | **Stay maximized**; skip size swap and skip position apply |
| Position clamp | On each 4K toggle in windowed non-maximized: `x = max(0, x)`, `y = max(30, y)` |
| Position clamp on exit fullscreen | Same floors when leaving fullscreen into a **normal windowed** frame; skip if restoring maximized |
| Shared position | One `x`/`y` for both modes |
| Startup with 4K On | Open at `four_k_client_*` if present; else seed `2 × client_*` into 4K fields and open at that |
| Clamp constants | Hardcoded `0` / `30` (UI chrome / title-bar recoverability — not gameplay balance) |

## Settings shape

Under `settings.json` → `window`:

```json
{
  "client_width": 1920,
  "client_height": 1080,
  "four_k_client_width": 3840,
  "four_k_client_height": 2160,
  "x": 100,
  "y": 80,
  "maximized": false,
  "fullscreen": false
}
```

- Missing `four_k_client_width` / `four_k_client_height` ⇒ “never enabled” (past-version safe).
- Persist optional keys only once seeded (or always write when present — either is fine; prefer write when not `None`).

## Toggle algorithm (Options row / F10)

After flipping `four_k_scaling` and before/with layout reload:

1. If **fullscreen**: apply layout/min-size only; **no** size swap, **no** position clamp. Done.
2. Sync live SDL → prefs using the **outgoing** mode’s size set (so the size the user had is remembered).
3. If **maximized**: apply layout/min-size only; **no** size swap, **no** position move. Done.
4. **Windowed, not maximized:**
   - If turning **On** and 4K size unset: `four_k_client_* = 2 ×` current live client size.
   - Target size = 4K set if On else normal `client_*`.
   - Clamp target to the **new** layout’s minimum client floor.
   - Set `window.size = target`.
   - Clamp position: `x = max(0, x)`, `y = max(30, y)`; set `window.position`.
   - Persist prefs (normal set unchanged when turning On except for the pre-sync of outgoing normal size from step 2 — which is intentional so last normal size is fresh).
5. Continue existing path: reload baseline, resize console, reload log font, enqueue settings.

**Critical invariant:** turning On must not assign live/grown pixels into `client_width` / `client_height`.

## Sync from SDL

`sync_window_from_sdl` (and callers) need the active scaling flag:

- Fullscreen: unchanged (do not overwrite windowed sizes).
- Maximized: update `maximized` only (existing).
- Else if `four_k_scaling`: write size → `four_k_client_*`; update `x`/`y`.
- Else: write size → `client_*`; update `x`/`y`.

## Startup

`prepare_initial_preferences` / `apply_startup_window`:

- If `four_k_scaling` and 4K size present → request that size.
- If `four_k_scaling` and 4K size absent → seed `2 × client_*`, persist, request that size.
- Else → request `client_*`.

Position restore uses saved `x`/`y` (startup need not force the toggle clamp unless we want belt-and-suspenders; **toggle clamp is mandatory**; optional soft clamp on startup is nice-to-have if cheap).

## Implementation touchpoints

| Area | Likely files |
|------|----------------|
| Prefs fields + serialize | `src/ui/window_state.py` |
| Sync routing by mode | `window_state.sync_window_from_sdl`, `WindowController` |
| Toggle apply | `App.apply_display_layout_from_settings` and/or new helper e.g. `apply_four_k_window_geometry` |
| Startup size choice | `WindowController.prepare_initial_preferences` / `apply_startup_window` |
| Spec | `openspec/specs/ui-layout/spec.md` |
| Tests | New focused tests for seed/swap/clamp/sync routing; extend settings parse tests |

## Performance

O(1) preference math and one SDL size/position set per toggle. No per-frame cost.

## Risks

| Risk | Mitigation |
|------|------------|
| First seed `2×` exceeds desktop | Accept (user asked for double); they can resize; 4K set remembers their choice |
| Bloated `client_*` already on disk from prior bug | Off restores that value; user resizes once under Off to fix normal set; On no longer worsens it |
| Race: resize event after toggle writes wrong set | Apply flag flip before sync/size; ensure sync uses post-toggle flag for *incoming* writes after apply |
| Maximized then un-maximize after toggle | Active set receives the restored size via sync — OK |
