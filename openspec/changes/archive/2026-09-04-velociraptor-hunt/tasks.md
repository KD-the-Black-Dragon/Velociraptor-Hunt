# Tasks: Velociraptor Hunt

**Do not implement any PR until the designer names it.** Canon is in
`DESIGN_CANON.md`. Slice notes are in `design.md` **PR slice plan**.

## PR0 — Project identity (docs)

- [x] Rewrite `AGENTS.md` product table, lineage, current-change pointer, hunt motifs
- [x] Rewrite root `README.md` for Velociraptor Hunt
- [x] Update `KDVR_REFERENCE.md` and `reference/README.md` (donor vs product)
- [x] Add this change: `proposal.md`, `design.md`, `DESIGN_CANON.md`, `tasks.md`
- [x] Point `openspec/config.yaml` at the hunt product
- [x] Note in `pyproject.toml` that the tree is becoming Velociraptor Hunt (package script still donor until a code PR)

## Q&A

- [x] Braindump + rounds 1–4 (see `DESIGN_CANON.md`)
- [x] Round 5: F-then-confirm targeting; blind linear projectile; factors only after F; second A = deep aim; D stand down; run interrupts aim
- [x] PR slice plan (this file + `design.md`)

## PR1 — Identity + hunt shell

- [x] Product-facing name **Velociraptor Hunt** (window, menu, user-data directory target)
- [x] Main menu: New Hunt, Stats (stub OK), Options, Quit — **not** Gladiavore career hub as New Game
- [x] Nameable hunter → weapon select (rifle / shotgun / revolver) → hunt state
- [x] Stub paddock is OK
- [x] Targeted tests + `testing-checklist-pr1.md`
- [ ] Manual checklist in chat after the PR (user playtest)

## PR2 — Paddock, tank, AUT, cone FOV

- [x] Circular-as-possible hard-border jungle; basic procgen (trees, long grass, bushes, openings)
- [x] UnReal World tank (numpad + TYUGHJBNM/arrows fallback)
- [x] Eight facings; vision **cone**
- [x] Hunt AUT data (`0.0` / `1.0`, tenths); wait
- [x] Targeted tests + `testing-checklist-pr2.md`
- [ ] Manual checklist in chat after the PR (user playtest)

## PR3 — Gait + aim stances

- [x] R/S run–walk–sneak; run vision penalty; no run sidestep/backpedal
- [x] A aim/focus, A again deeper aim, D stand down
- [x] Running clears aim; walk/sneak do not
- [x] Targeted tests + `testing-checklist-pr3.md`
- [x] Manual checklist in chat after the PR (user playtest)

## Deferred (do not implement in the current PR)

Recorded 2026-08-31. Not PR4.

- [ ] **Aim confirm / off-center:** Aim must confirm exactly what you are aiming at. It will be allowed **off-center of a 45° facing** — not locked to the eight tank ticks.
- [ ] **Run fatigue, not run mode:** **Run mode** should not cut vision. **Actually running** applies a debuff (short-term fatigue / frantic movement). **That debuff** gives **progressive** penalties to vision and accuracy.
- [ ] **Last-known raptor:** Keep the last seen tile on the map after LOS is lost. Never seen = nothing. Currently in LOS = live raptor only. Seen before but not now = last-known mark only (erase it when seen again). Not in PR5–PR10 as written.
- [ ] **Right-side hunt panel:** Score differential and raptor info belong on the otherwise blank right side of the screen — not crammed into the two bottom lines. PR7 still adds clock/ring; this is the layout home for that plus raptor readout.
- [ ] **Visible projectile:** The hunter’s dart should travel visibly across the map (animation), not resolve in one step.
- [ ] **Rain audio samples:** PR6 ships a 0–1 fade stub only (no wav in tree). Cross-fade real rain layers when assets exist.
- [ ] **Practice dummy mode:** A separate mode (not the live hunt) where the raptor follows **predictable, observable** loops — e.g. run back and forth, sneak back and forth — so rain/sound/print/aim rules can be verified.
- [ ] **Game-over modal:** Final game over is a **centered modal**, not overlay text on the map.
- [x] **Strip bottom key-hints:** Remove “what key does what” from the bottom of the hunt screen (including leftover fragments like `8 fwd, 2 b`). (PR10)
- [x] **Help screen:** `?` / **F1** lists all hunt commands. (PR10)
- [ ] **Sounds are map symbols only:** No bottom-line “Rain in the canopy / Wind from the SE / Movement N.” One shared symbol for “that might have been a raptor.”
- [ ] **Footprints:** Always created (not only in heavy rain). Each print remembers the rain when it was made; heavier rain → longer life; they fade individually. Only **mud** tiles, not grass.
- [ ] **Relative score always on-screen** (until the right-side panel lands, keep ring state visible).
- [ ] **KDVR-exact belly:** Wall color must match KDVR; camera stays **centered on the swallow tile**. The raptor should **walk around a little** during belly and **carry the hunter with it** (this last part is hunt-specific — KDVR monsters with prey in belly do not move).
- [ ] **Vore narratives as KDVR modals:** Swallow / digest lines are **modal windows**, the same pattern as KDVR, not overlay-only text.
- [ ] **Raptor win on adjacency:** The raptor wins by **reaching a tile adjacent to the hunter**. It need not commit a melee attack. Adjacent = hunt lost, raptor wins. (PR8 still requires the raptor’s turn with Chebyshev 1.)
- [ ] **Shift+numpad strafe with NumLock on:** Sidestep works with NumLock **off**, but Shift+numpad 4/6 does **not** strafe when NumLock is **on**. Make strafe work with NumLock on if the key events allow it. Recorded 2026-09-01.

## PR4 — Raptor body

- [x] One raptor; same tank facing + FOV; does not cheat tiles
- [x] Stub AI (wander/idle, fair eyes-on only)
- [x] In-sight HUD includes **facing**
- [x] Targeted tests + `testing-checklist-pr4.md`
- [x] Manual checklist in chat after the PR (user playtest)

## PR5 — Fire + tranq win

- [x] F targeting mode; cursor on visible raptor; may blind-fire; linear projectile
- [x] Loose factors **only** in targeting mode; confirm commits, abort does not
- [x] Deterministic damage (data); ammo; butter-zone stub
- [x] Raptor 0 HP → fire line + bright tranquilized on frozen map → You win + scores
- [x] Targeted tests + `testing-checklist-pr5.md`
- [x] Manual checklist in chat after the PR (user playtest)

## PR6 — Rain + clues

- [x] Rain cycles; vision vs sound; mud footprints; false rain/wind sounds
- [x] Smooth rain audio fade stub (no wav assets — follow-up on deferred list)
- [x] Targeted tests + `testing-checklist-pr6.md`
- [x] Manual checklist in chat after the PR (user playtest)

## PR7 — Clock + ring control

- [x] Hunt clock; center-weighted ring score; 3-state HUD both sides
- [x] Time-over win and time-over loss
- [x] Targeted tests + `testing-checklist-pr7.md`
- [x] Manual checklist in chat after the PR (user playtest)

## PR8 — Loss (swallow / belly / digest)

- [x] One melee connect finishes the hunter
- [x] Spectacle swallow by actual attack + front/side/behind
- [x] KDVR belly: eight red `#`, world hidden, move/still waste turns, meta OK
- [x] Spectacle digest
- [x] Targeted tests + `testing-checklist-pr8.md`
- [x] Manual checklist in chat after the PR (user playtest)
- [x] Game-over / time-over / win-results dismiss only with Enter or Esc

## PR9 — Raptor mind

- [x] Profile player habits (counts / confidence)
- [x] Scramble if it sees aim; circle a staredown; no charge just because eyes-on
- [x] Hold center when definitely winning; **heave** if certain time-loss
- [x] Frontal charge: allowed, usually a bad idea vs ready shotgun/revolver
- [x] Targeted tests + `testing-checklist-pr9.md`
- [x] Manual checklist in chat after the PR (user playtest)

## PR10 — Stats + polish

- [x] Persistent stats screen (locked fields, including per-weapon)
- [x] Help overlay for hunt keys; leftover HUD
- [x] Land behavioral requirements under `openspec/specs/` as appropriate
- [x] Targeted tests + `testing-checklist-pr10.md`

## PR11 — Autosave, abandon, difficulty boards

- [x] Hunt autosave on the KDVR rotating slot (turns, Ctrl+Q, window close)
- [x] Continue Hunt when a hunt save exists
- [x] New Hunt with a save: abandon prompt (Y/n); Yes → games played + games abandoned
- [x] Per-difficulty stats boards; Left/Right cycles Easier / Normal / Hard / Nightmare
- [x] Targeted tests + `testing-checklist-pr11.md`
- [x] Manual checklist in chat after the PR (user playtest)

Do **not** pick up leftover Gladiavore PRs (`tactical-duel-combat`, etc.)
unless a harvest is explicitly requested.
