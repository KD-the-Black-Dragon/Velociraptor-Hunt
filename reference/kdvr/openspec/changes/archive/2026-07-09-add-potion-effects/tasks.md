# Tasks: add-potion-effects

**Active PR:** *(none — change accepted and archived 2026-07-09)*  
**Rule:** One PR at a time.

Full design: `design.md`. Summary: `proposal.md`.

---

## PR0 — Design lock

- [x] Designer answers open questions
- [x] `proposal.md` / `design.md` / `tasks.md` locked
- [x] AGENTS.md pointer → `add-potion-effects`
- [x] User authorizes PR1 coding
- [x] Digestion ward stock name → **potion of antacid**

---

## PR1 — PlayerEffects infrastructure

- [x] `PlayerEffects` (haste, might, ward, pending teleport)
- [x] Tick on player turn consumed
- [x] Haste: extra player action before monster phase (final: 2:1)
- [x] Save/load defaults
- [x] Status corner rows
- [x] Tests + `testing-checklist-pr1.md`
- [x] Manual playtest sign-off

---

## PR2 — Instant / buff effects

- [x] Effect dispatch beyond heal
- [x] `magic_mapping`, `haste`, `might`, `digestion_ward` (+ heal regression)
- [x] SCHEMA + loader fields
- [x] Digestion tick respects ward (no dmg, no strikes)
- [x] Stock potions: discovery, haste, might, antacid
- [x] Tests + checklist
- [x] Manual playtest sign-off

---

## PR3 — Delayed teleport

- [x] Queue 3–5; refresh on re-quaff
- [x] Random land walkable unoccupied tile
- [x] Engulfed → teleport escape
- [x] Stock potion of teleportation + TEMP starter slot
- [x] Tests + checklist
- [x] Manual playtest sign-off

---

## PR4 — Blink modal

- [x] Drink → “Blink where?” → valid visible/LOS only
- [x] Cancel: no consume, no turn
- [x] Success: move + consume + turn
- [x] Stock potion of blinking + TEMP starter
- [x] Invalid target caution messages
- [x] Reticle cannot enter unexplored black
- [x] Tests + checklist
- [x] Manual playtest sign-off

---

## PR5 — Summon ally

- [x] Weighted good at depth (data-driven)
- [x] Place nearest legal; full-map last resort
- [x] Consume even on impossible fail
- [x] Stock potion of alliance + TEMP starter
- [x] Summon log: “A dog knight appears…”
- [x] Tests + checklist
- [x] Manual playtest sign-off

---

## PR6 — Stock catalog

- [x] Spawn weight/depth tune pass if needed
- [x] Specs: inventory-items, equipment-catalog (heal + all effects)
- [x] Confirm examine strings utilitarian / number-free
- [x] `testing-checklist-pr6.md`
- [x] Manual playtest sign-off

---

## PR7 — Acceptance + archive

- [x] **Remove TEMP starter playtest potions** (`_STARTER_PLAYTEST_POTIONS` in `inventory.py`)
- [x] Full suite `-n 6`; archive; clear AGENTS pointer
