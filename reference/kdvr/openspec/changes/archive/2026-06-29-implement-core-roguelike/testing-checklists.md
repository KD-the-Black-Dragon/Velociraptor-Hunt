# Phase Testing Checklists

Run `python -m src.main` from the project root unless noted otherwise.

---

## Phase 1 — Project Scaffold

- [ ] Command runs without traceback: `pip install -e .`
- [ ] Command runs without traceback: `python -m src.main`
- [ ] Window title bar reads **KD's Vore Roguelike**
- [ ] Window shows title text and "Press Escape to quit." on a black/dark background
- [ ] Pressing **Escape** closes the window cleanly
- [ ] Clicking the window **X** button closes the window cleanly
- [ ] Resizing the window does not crash the game (console stretches)
- [ ] File exists: `data/Alloy_curses_12x12.png`

**Pass criteria:** Window opens, displays placeholder text, exits on Escape or close.

---

## Phase 2 — Map and Tiles

- [ ] `python -m src.main` shows a procedurally generated dungeon (not a blank screen)
- [ ] Walls render as `#` in a brownish tone; floors render as `.` in a yellowish tone
- [ ] Multiple separate rooms are visible, connected by corridors
- [ ] The outer edge of the map is wall; you cannot see open void outside the map bounds
- [ ] HUD at the bottom shows control hints and current view mode
- [ ] Press **R** — a new dungeon layout generates (layout visibly changes)
- [ ] Press **D** — toggles dimming demo; distant explored tiles appear darker than nearby ones
- [ ] Press **D** again — full bright visibility returns
- [ ] **Escape** still closes cleanly

**Pass criteria:** Procedural dungeon renders with distinct wall/floor; regenerate and dimming toggle work.

---

## Phase 3 — ECS Foundation

- [ ] `python -m src.main` still opens without errors
- [ ] A white `@` appears on the dungeon floor (player entity)
- [ ] Player spawns inside a room (on `.` floor, not inside a `#` wall)
- [ ] HUD shows `HP: 30/30`
- [ ] HUD shows welcome message: "Welcome to KD's Vore Roguelike."
- [ ] Press **R** — new dungeon generates and `@` moves to a new room; welcome message resets
- [ ] **D** dimming demo still works with player-centered visibility
- [ ] **Escape** still closes cleanly

**Pass criteria:** Player entity visible at dungeon entrance with HP HUD and message log; prior phase controls still work.

---

## Phase 4 — Player Movement and Input

- [ ] Arrow keys move `@` in four cardinal directions
- [ ] Vi-keys (`h/j/k/l/y/u/b/n`) and numpad (`2/4/6/8/1/3/7/9`) also work
- [ ] Diagonal movement works, including corner cuts past wall corners
- [ ] Corner-cutting: sliding diagonally between two walls moves through the gap
- [ ] Walking into a `#` wall does not move the player
- [ ] Press **S** (debug) — HUD shows `[STUNNED]` and `HP: 0/30`; movement keys do nothing
- [ ] Press **S** again — stunned clears, movement works again
- [ ] **R**, **D**, and **Escape** still work as before

**Pass criteria:** 8-direction movement with corner cuts allowed; stunned gate blocks movement.

---

## Phase 5 — Field of View

- [ ] On new game, only a limited area around `@` is lit; the rest of the map is black/unexplored
- [ ] Moving reveals new tiles; they appear bright while in sight
- [ ] Tiles you've left remain visible but **dimmed** (explored memory)
- [ ] Walls block sight — areas behind walls stay dark until you walk around them
- [ ] `@` is only drawn while in the currently visible region (always true when playing)
- [ ] **R** regen resets exploration — only the starting room area is visible again
- [ ] Movement, **S** debug stun, and **Escape** still work

**Pass criteria:** FOV updates each move; explored-but-hidden tiles dim; walls block vision.

---

## Phase 6 — Monsters and AI

- [ ] Red `o` monsters appear somewhere on the map (3–5 per new game)
- [ ] Monsters are not on top of `@` at game start
- [ ] Monsters off-screen or behind walls are hidden until FOV reveals them
- [ ] Walk into a corridor where a monster can see you — it moves toward you on your next step
- [ ] Monsters stop at walls and cannot pass through `#`
- [ ] Monsters halt adjacent to `@` (cannot occupy your tile)
- [ ] Monsters out of sight do not move toward you
- [ ] **R** regen spawns a fresh set of monsters
- [ ] Prior controls (move, FOV, **S**, **Escape**) still work

**Pass criteria:** 3–5 monsters chase when they have line of sight; monster turns run after each player move.

---

## Phase 7 — Combat

- [ ] Bumping a monster (`o`) deals damage; you do not move onto its tile
- [ ] Message log shows hit damage (e.g. "You hit the monster for 4 damage.")
- [ ] Monster at 0 HP disappears; log says **defeated** (never "killed")
- [ ] Let a monster reach you — it deals damage on its turn
- [ ] Player HP in HUD decreases when hit
- [ ] At 0 HP you become **stunned**: `[STUNNED]` shows, movement keys stop working
- [ ] Press **S** (debug heal) — HP restores, stunned clears, movement works again
- [ ] Monster adjacent to you attacks instead of standing still on its turn
- [ ] Prior phases still work (FOV, regen, Escape)

**Pass criteria:** Bump combat works both ways; monsters defeated and player stunned per spec terminology.

---

## Phase 8 — Items and Inventory

- [ ] At least one magenta `!` potion visible on the map (after exploring)
- [ ] Walking onto `!` picks it up; glyph disappears; log shows slot letter (starts at `a`)
- [ ] Press the slot letter — HP increases by 10 (up to max); slot empties
- [ ] Press an empty slot letter — log says slot is empty; no turn passes
- [ ] Get stunned (**S** debug), press potion letter — potion works and stunned clears if HP > 0
- [ ] Movement uses arrows/numpad only (letter keys are for items)
- [ ] Combat, FOV, **R**, and **Escape** still work

**Pass criteria:** Pickup, 26-slot inventory, letter-key use, stunned recovery via potion.

---

## Phase 9 — HUD and Polish

- [ ] HUD shows **KD's Vore Roguelike** title and `HP current/max`
- [ ] HP bar (`#` filled, `-` empty) updates when you take damage or heal
- [ ] `[STUNNED]` / `** STUNNED **` appears when stunned; HP text turns warmer color
- [ ] `Items: a:!` (etc.) shows occupied inventory slots on the status line
- [ ] Up to **5** recent messages visible in the HUD log area
- [ ] Defeat a monster — log says **defeated**, never kill/die
- [ ] Full game loop still works end-to-end

**Pass criteria:** Polished HUD with HP bar, inventory summary, 5-line log; terminology audit clean.

---

## Phase 10 — Acceptance Verification

Automated suite: `python -m pytest tests/test_acceptance.py -v`

- [ ] All automated acceptance tests pass
- [ ] One manual play session confirms the full loop (explore → fight → loot → heal)
- [ ] Spec AC 1–8 satisfied (see `acceptance-report.md`)
- [ ] No `src/vore` module exists
- [ ] Ready to archive `implement-core-roguelike` change when satisfied

**Pass criteria:** Automated tests green + one confirmatory play session.