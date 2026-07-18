# Tasks: gladiavore-foundation

Long-lived foundation change for **Gladiavore**.  
**Do not implement any PR until the designer authorizes that PR by name** (e.g. “implement PR1”).

Answering design questions or editing these docs is **not** implementation authorization.

---

## Setup (design)

- [x] Create change folder (`proposal.md`, `design.md`, `tasks.md`)
- [x] Record designer intake (career, combat, vore, hub, green/red, identity)
- [x] Update `AGENTS.md` current change pointer → `gladiavore-foundation`
- [x] Note `balance-pass` superseded for product direction
- [x] Wave-1 full Q&A integrated into `design.md` (AUT sacred, cards, roster taxonomy, grapple HP, etc.)
- [x] Wave-2 integrated (AUT costs, cooldown≠defense, PC+4, no ZoC MVP, agency always, …)
- [x] Wave-3 integrated (dodge, recovery bank, balance curve, start market)
- [ ] Designer review / amend foundation docs
- [ ] Designer sign-off: foundation design accepted (may still iterate open questions)

---

## PR1 — Re-identity + agent reference

**Auth:** authorized 2026-07-16 (designer: implement as much as possible, PR-sliced).  
**Design ref:** `design.md` §2, §13 PR1.  
**Status:** implemented — awaiting designer manual sign-off.

### Checklist

- [x] `pyproject.toml` / package metadata / console script → Gladiavore
- [x] README product name, run instructions, user-data paths → Gladiavore
- [x] User data directory name → `Gladiavore` (platformdirs)
- [x] Main menu / title strings → Gladiavore
- [x] Root `KDVR_REFERENCE.md` (clone lineage, harvest rules, non-product KDVR features)
- [x] `AGENTS.md` project table describes Gladiavore; active change pointer confirmed
- [x] Packaging scripts names updated (`scripts/*alpha*.ps1`)
- [x] Tests that assert old product strings updated
- [x] Targeted tests green (57 identity-related tests)
- [x] Manual checklist posted in chat (`testing-checklist-pr1.md`)
- [x] Designer manual sign-off (2026-07-16)

### Not in PR1

- Hub gameplay, combat rewrite, deleting all KDVR systems, full content reskin

---

## PR2 — Career shell + downtime hub (stub)

**Auth:** authorized 2026-07-16 (after PR1 OK).  
**Design ref:** `design.md` §3–4, §13 PR2.  
**Status:** implemented — awaiting designer manual sign-off.

### Checklist

- [x] New career enters **DOWNTIME** hub (not dungeon floor as product default)
- [x] Hub navigable actions (stubs OK): shop, hire, equip, train/heal, assign, select match
- [x] Gold + renown (score) visible
- [x] Career save skeleton (load/continue)
- [x] Green/red appear in match select UI even if one real fight exists later
- [x] Targeted tests
- [x] Manual checklist posted in chat
- [x] Designer manual sign-off (2026-07-16)

---

## PR3 — Match vertical slice + AUT core

**Auth:** authorized 2026-07-16 (PR2 OK).  
**Design ref:** `design.md` §7.1, §9 PR3.  
**Status:** implemented — awaiting designer manual sign-off.

### Checklist

- [x] One ~20×20 curated arena + MATCH state
- [x] **AUT scheduler**: action cooldowns; next-ready actor; **player wins ties**
- [x] Move + basic attack with distinct AUT costs (`data/aut_costs.json`)
- [x] Win: enemies defeated → recap → hub (gold/renown/round++)
- [x] Loss path stub (green fee / red “haul out” stub; no full digest yet)
- [x] Dungeon New Game not the primary path (career → hub → match)
- [x] Targeted tests
- [x] Manual checklist posted in chat
- [x] Designer manual sign-off (2026-07-16)

---

## PR4 — Combat skeleton (AP, balance, smart bump hooks, abilities UX)

**Auth:** authorized 2026-07-16 (PR3 OK).  
**Design ref:** `design.md` §7.3–7.10.  
**Status:** implemented — awaiting designer manual sign-off.

### Checklist

- [x] AP pool ~10 max, ~1 regen baseline (world AUT)
- [x] Balance integer; hold=def, attack=agg; specials tagged; no stance toggle
- [x] Passive balance→stat effects stubbed but hooked (`actual_fighter`)
- [x] Base vs actual path for resolution
- [x] Abilities: `a` + letter; `?` list; Haymaker / Shield Push / Hook Shield
- [x] Smart-bump awareness hook (jab / standard / all-out)
- [x] Meter UI stubs for AP/balance
- [x] Targeted tests
- [x] Manual checklist posted in chat
- [x] Designer manual sign-off (2026-07-16)

---

## PR5 — Space tactics (pushback, flank, reaction modal; no ZoC)

**Auth:** authorized 2026-07-16 (PR4 OK + font fix).  
**Design ref:** `design.md` §7.2, §7.8.  
**Status:** implemented — awaiting designer manual sign-off.

### Checklist

- [x] Pushback 1–2 tiles; wall impact damage
- [x] Flanking angle table (45 penalty … 180 best)
- [x] Reaction modal on every PC-targeted attack; 8-way dodge into open tiles; dodge fatigue
- [x] Log = impacts/near-misses; modal = incoming announce
- [x] Spear optional deferred
- [x] **No ZoC**
- [x] Targeted tests
- [x] Manual checklist posted in chat
- [x] Designer manual sign-off (2026-07-16)

---

## PR6 — Allies, Talk, roster PC+4 / deploy PC+2

**Auth:** authorized 2026-07-16 (PR5 OK).  
**Design ref:** `design.md` §5, §7.11.  
**Status:** implemented — awaiting designer manual sign-off.

### Checklist

- [x] Roster PC + up to 4 allies; deploy PC + up to 2
- [x] Hire market with tier archetypes (scrub/learner/finished)
- [x] Free starter picks (2) before hub unlocks
- [x] Assign team toggle deploy
- [x] `T` flow: ally/all → Attack/Defend
- [x] Free Talk 0 AUT; returns after 1.0 AUT; second talk AP+turn
- [x] Ally digest (red down) → remove + ~70% refund
- [x] Targeted tests
- [x] Manual checklist posted in chat
- [x] Designer manual sign-off (2026-07-16)

---

## PR7 — Injuries, recovery bank, healing, JSON balance

**Auth:** authorized 2026-07-16 (injury design + PR6 OK).  
**Design ref:** `design.md` §6.4–6.5, recovery, JSON balance policy.  
**Status:** implemented — awaiting designer manual sign-off.

### Checklist

- [x] Injuries: `Injured {Region}: {Severity}` Arm/Leg/Head/Torso; 10/20/30% JSON
- [x] Apply on big hits; aggravate / double-step on severe; PC + allies; persist career
- [x] Full stamina refresh each match; injuries carry
- [x] 0 HP: downed + recovery bar; crawl 3× AUT; optional Recover → 5 HP
- [x] Second Wind (`s`) once/match + short debuff (JSON)
- [x] Hub **Healing** pay per severity step (expensive JSON gold)
- [x] Maneuvers + abilities fully adjustable via `match_combat.json`
- [x] Targeted tests
- [x] Manual checklist posted in chat
- [x] Designer manual sign-off
- [ ] Retainers deferred (not blocking PR7)

---

## PR8 — Grapple HP vore v1

**Auth:** designer authorized (proceed PR8 after PR7 OK).  
**Design ref:** `design.md` §8.  
**Sign-off:** designer approved stub + scene isolation (2026-07-17).

### Checklist

- [x] Grab → grapple HP war → swallow only at 0 grapple HP
- [x] Prey break away / counter; predator grip / grapple damage
- [x] Engulfed near-helpless; AUT digest strikes; rare regurg
- [x] Green: release before digest; red: digest ends PC run
- [x] Beast-only ally vore flag
- [x] Predator flaunt lines + recap
- [x] Grapple scene isolation (prey only hit by predator; no reaction stack)
- [x] Targeted tests + manual checklist
- [x] Designer manual sign-off

---

## PR9 — Match cards + economy + green surrender

**Auth:** designer authorized next step after PR8 OK.  
**Design ref:** `design.md` §3.3–3.4, §8.7; `DESIGN_CANON` match cards / green-red.  
**Sign-off:** designer approved (2026-07-17).

### Checklist

- [x] JSON card catalog (`data/match_cards.json`) with enemies, mult, round bands
- [x] Hub offers **3 of N** eligible cards per round (stable seed)
- [x] Green cards only on predefined green rounds (+ easier extras)
- [x] Win/loss gold+renown from JSON economy (green underpays)
- [x] Mid-match **green** surrender (`G`); early deny; scaled payout
- [x] Spawn enemies from card enemy lists (multi-type OK)
- [x] Targeted tests + manual checklist
- [x] Designer manual sign-off

---

## PR10 — Thin patrons (3) + objectives

**Auth:** designer authorized (proceed PR10 after PR9 OK).  
**Design ref:** `design.md` §4.4; `DESIGN_CANON` patrons.  
**Sign-off:** included in “stubs OK; flesh out per module later” (2026-07-17).

### Checklist

- [x] Three named patrons in `data/patrons.json`
- [x] Per-match objective assignment (sanity-checked vs green/red + allies)
- [x] Match HUD + log show active objective
- [x] Recap: hit → extra gold; miss → note only (no penalty)
- [x] Hub shows patron roster + last result
- [x] Career save field `last_patron_result` (default empty)
- [x] Targeted tests + manual checklist
- [x] Designer direction: stubs OK; deepen later per system

---

## PR11 — Crowd stub

**Auth:** batch remaining foundation (designer: all remaining PRs).

- [x] `data/match_crowd.json` + favor meter
- [x] Hit/miss and match-end shifts; recap mood + high-favor gold crumb
- [x] HUD crowd readout

---

## PR12 — Difficulty hooks (stub reimagine)

- [x] `data/difficulties.json` four tiers
- [x] Enemy HP/damage mult, grab mult, payout mult
- [x] Extra green rounds flag (Easier)

---

## PR13 — Background stub

- [x] `data/backgrounds.json` + pick after name entry
- [x] Starting gold/renown only; goals deferred
- [x] Career `background_id` save field

---

## PR14 — Content expand (light)

- [x] Abilities `d` Low Kick, `e` Shoulder Check
- [x] Additional match cards in catalog

---

## PR15 — KDVR soft-prune docs

- [x] `KDVR_REFERENCE.md` soft-prune status + live Gladiavore specs pointer
- [x] No mass-delete of harvest modules (deferred dedicated prune)

---

## Deferred (future module work — not foundation blockers)

### Battle pace program (primary next design track)

Roadmap: `openspec/changes/battle-pace-program/ROADMAP.md`  
Canon: `DESIGN_CANON.md` §12 Battle pace program  

- [ ] **BP-W** `weapon-measure` — attack delay + range bands (root dep for attacks)
- [ ] **BP-R** `ready-actions` — numpad 5 keep watch vs `d` brace vs step lean
- [ ] **BP-P** `player-combat-commands` — intent core, footwork `f`, directed attack, feint
- [ ] **BP-M** `footwork-momentum` — footwork → emergency evade inertia
- [ ] **BP-A** `ai-personality-fuzzy` — 1–10 attrs + fuzzy AI (after player moves exist)

### Other deferred

- [ ] Crowd as real mechanical force
- [ ] Full difficulty reimagining / balance pass
- [ ] Opening matrix depth; Jump content
- [ ] Background long-term victory goals
- [ ] Hard KDVR asset prune
- [ ] Deeper patronage; more arenas

---

## Final acceptance (foundation first pass)

- [x] Live specs: `openspec/specs/gladiavore-career/`, `gladiavore-match/`
- [x] Targeted foundation suite green (PR3–15 + career path tests)
- [x] Full `tests/` still includes large KDVR-era suite (legacy noise expected); not a hard ship gate for arena career stubs
- [x] Keep change **long-lived** (module deepening continues)
- [x] AGENTS.md active change remains `gladiavore-foundation`
- [ ] Designer E2E manual: `testing-checklist-foundation-e2e.md`
