# Tasks: four-k-window-size-memory

## PR1 — Dual size sets, toggle swap, position clamp

- [x] Add optional `four_k_client_width` / `four_k_client_height` to `WindowPreferences` (+ load/save; missing = unset)
- [x] Route `sync_window_from_sdl` so 4K On writes only `four_k_client_*`; Off writes only `client_*` (shared `x`/`y`)
- [x] On 4K toggle (windowed, not maximized): seed 2× on first On; swap sizes thereafter; never mutate `client_*` when enabling
- [x] On 4K toggle (windowed, not maximized): clamp `x ≥ 0`, `y ≥ 30` and apply position
- [x] Fullscreen / maximized: skip size swap and position apply; still reload layout / min size
- [x] Startup: if 4K On, open at 4K size (seed 2× `client_*` if unset)
- [x] Targeted unit tests (seed, swap, clamp, sync routing, settings round-trip)
- [x] Manual checklist: `testing-checklist-pr1.md`

## PR2 — Spec + acceptance + archive

- [x] Update `openspec/specs/ui-layout/spec.md` (dual sizes, toggle restore, clamp, sync rules)
- [x] Acceptance report + testing-checklists rollup
- [x] Archive change; set AGENTS **Active change:** *(none)*
- [ ] Full pytest only after designer final sign-off (per AGENTS)
