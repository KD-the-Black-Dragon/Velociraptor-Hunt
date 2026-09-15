# Manual checklist — PR11

Run: `python -m src.main`

Design reference: `design.md` § **PR11 — UI visualization polish**.

## 1 — Window resize (grow + shrink)

- [ ] Resize window **smaller** — map viewport shrinks; sidebar, log, status corner remain usable
- [ ] Resize window **larger** again — map viewport **grows back** (not stuck at old max)
- [ ] Repeated shrink/grow cycles feel stable (no crash, no stale layout)
- [ ] At ~1366×768 usable area, UI remains playable (floor clamp)

## 2 — Sidebar spacing (two-line NPCs)

- [ ] Player name on its own row; `HP nn/nn [bar]` on the row **below**
- [ ] **Blank row** between each evil NPC entry
- [ ] Each evil NPC: **name row**, then **bar-only row** below (no `HP x/y` on NPCs)
- [ ] Good NPCs at bottom: same two-line pattern
- [ ] Layout resembles playtest mock (Hero / HP / gap / wolf / bar / gap / …)

## 3 — Modals on screen center

- [ ] Examine description, inventory, vore, digestion, game over — centered on **full window**, not only map column
- [ ] Modals may overlap sidebar/log (expected)
- [ ] Examine / evoke **cursors** still on map only

## 4 — Standard player HP bar

- [ ] **Standard** preset: full player HP line visible (no trailing clip of `]`)

## 5 — Sidebar padding

- [ ] **One blank row** above player name at top of sidebar
- [ ] **1–2 blank rows** below lowest good NPC (not flush against bottom panels)

## 6 — Status corner width

- [ ] Bottom-right panel visibly wider; depth/ailments not cramped
- [ ] Message log + status corner still tile cleanly (no gaps/overlap)

## 7 — NPC condition estimate bars

- [ ] NPC bars 6 characters wide inside brackets
- [ ] All seven fill levels appear in play/tests: `[------]` … `[######]` (0–6 `#` chars, none skipped)
- [ ] Fill is coarse estimate (`round(6 * hp / max_hp)`), not exact player HP numbers on NPC lines
- [ ] Player bar still long with exact `HP nn/nn`

## 8 — Quit confirm Shift

- [ ] Ctrl+Q → quit prompt
- [ ] Press **Shift alone** — **no** “Please type capital 'Y'…” message
- [ ] **Shift+Y** still confirms; **n** still cancels

## Regression

- [ ] Options preset switch (Standard / Wide) still works on new game
- [ ] Camera, FOV sidebar filter, message log 8 lines, status corner ailments
- [ ] Main menu / name entry / options still fit  layout console