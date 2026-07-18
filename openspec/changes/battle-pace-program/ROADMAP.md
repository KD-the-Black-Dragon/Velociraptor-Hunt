# Battle pace program — multi-module OpenSpec roadmap

**Status:** Design plan only. No implementation until the designer authorizes a **named PR** inside an **accepted** module change.  
**Parent pillars:** `openspec/changes/gladiavore-foundation/` + `DESIGN_CANON.md`  
**Session origin:** 2026-07-17 battle-pace design (Chivalry-style measure, footwork, optimistic intent, CK2-like AI attrs).

This file is the **long-term map**. Individual modules live as sibling change folders under `openspec/changes/`. Open a module’s own `proposal.md` / `design.md` / `tasks.md` when that module is the active design focus; do not implement from this roadmap alone.

---

## Product goal (one sentence)

Keep the **roguelike interface**, replace **adjacent bump-duel** pace with **measure-first gladiatorial combat** (reach, footwork, ready vs brace, weapon-defined techniques), then give enemies **personality-weighted fuzzy AI** that uses the same move vocabulary.

---

## Design locks (summary — full detail in DESIGN_CANON § Battle pace)

| Topic | Lock |
|-------|------|
| Sport | Measure-first; not walk-adjacent-and-whack as the default |
| Sword (gladius-like) | R1 in-fighting ≈ full effect; R2 out-fighting (thrust/jab) comfortable |
| Spear | R2 detrimental; R1 near-useless; wants longer measure |
| Other weapons | Per-weapon curves in data |
| R3–4 (sword-shaped) | Feint / false lunge territory — never “swing at air and look foolish” |
| R5+ | No useful basic combat intent → no-op |
| Footwork | `f` + **targeting**; 2 straight **or knight-move**; AP + aggression; compound spam; Esc/invalid = cancel/no-op |
| Numpad 5 | Keep watch / stand ready; **near-neutral** (tiny defensive only from inactivity) |
| `d` | Raise shield / timid brace — real defensive commitment |
| Normal step | Very slight aggressive lean |
| Modal dodge | **Emergency evade** (distinct from footwork); modulated by recent footwork **momentum** |
| Basic attack AUT | Weapon **attack delay** (DCSS-like); same delay across reach for basics |
| Intent keys | Optimistic resolution; never waste turn on out-of-context; invalid → no-op |
| AI | 1–10 **attributes** → fuzzy weights (CK2-style method, small attr set); not a finite archetype enum; imperfect roleplay |

Tweaks during implementation are expected; reverse a lock only with designer confirmation.

---

## Dependency graph

```text
                    ┌─────────────────────────┐
                    │  BP-W  weapon-measure   │
                    │  delay + range bands     │
                    └───────────┬─────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         │                      │                      │
         ▼                      ▼                      │
┌─────────────────┐   ┌─────────────────────┐         │
│ BP-R ready-     │   │ BP-P player-combat- │         │
│ actions         │   │ commands            │         │
│ (5 / d / step)  │   │ (intent, f, poke…)  │         │
└────────┬────────┘   └──────────┬──────────┘         │
         │                       │                    │
         │                       ▼                    │
         │              ┌─────────────────┐           │
         │              │ BP-M momentum-  │           │
         │              │ evade           │           │
         │              └────────┬────────┘           │
         │                       │                    │
         └───────────┬───────────┴────────────────────┘
                     ▼
           ┌─────────────────────┐
           │ BP-A ai-personality │
           │ fuzzy               │
           └─────────────────────┘
```

**Hard rules:**

1. **Weapons before attack-intent behavior** — different moves *feel* different by weapon only after measure data exists.  
2. **Player move vocabulary before AI** — AI scores candidates that already exist.  
3. **Footwork before momentum-evade** — momentum tags are produced by footwork.  
4. **Ready-actions (5/`d`) can parallel weapons** — no hard dep either way; sequence them for playtest clarity (recommended: weapons first, then ready-actions, then player commands).

---

## Module catalog

| ID | Change folder | Purpose | Depends on | Unlocks |
|----|---------------|---------|------------|---------|
| **BP-W** | `weapon-measure` | Attack delay; per-weapon range-band effectiveness; seed archetypes | Foundation match combat | Meaningful pokes / bad measure |
| **BP-R** | `ready-actions` | Keep-watch (5) vs brace (`d`) vs step lean; fix “5 = turtle dump” | Foundation balance meter | Correct “stand ready” feel |
| **BP-P** | `player-combat-commands` | Optimistic intent core; footwork; directed basic attacks; feint ladder | BP-W (for attack PR); BP-R recommended before ship | Full player sport |
| **BP-M** | `footwork-momentum` | Directional momentum buffs/debuffs on emergency evade | BP-P footwork + foundation reaction modal | Chivalry inertia |
| **BP-A** | `ai-personality-fuzzy` | 1–10 attrs; fuzzy intent scoring; enemy footwork/measure use | BP-W, BP-P; BP-M optional but preferred | Non-roguelike enemy pace |

**Later (out of this program’s critical path, still battle-adjacent):**

| ID | Topic | Notes |
|----|--------|--------|
| BP-O | Openings / awareness depth | Smart-bump → full commitment matrix |
| BP-J | Jump / vault (`J`) | After footwork is stable (avoid two multi-tile systems at once) |
| BP-C | Ability counter web | Content after basic steel feels good |
| BP-G | Grapple math fairness | Existing stub; deepen when spacing game exists |

---

## Recommended design → implement order

| Phase | Work | Auth style |
|-------|------|------------|
| 0 | This roadmap + DESIGN_CANON battle-pace section | Docs only |
| 1 | **Design** BP-W end-to-end → designer accept → implement BP-W PRs | One module at a time |
| 2 | **Design** BP-R → accept → implement | |
| 3 | **Design** BP-P (large; multi-PR) → accept → implement PR-by-PR | |
| 4 | **Design** BP-M → accept → implement | |
| 5 | **Design** BP-A → accept → implement | |
| 6 | Optional BP-O / BP-J / BP-G as separate changes | |

**Do not** open BP-A design as “ready to code” until BP-P’s basic attacks + footwork are playable. Design *drafts* for AI attrs can be sketched early; implementation waits.

**Parallelism:** Only BP-W design/implement and BP-R design/implement may run conceptually in parallel (different systems). Prefer serial for one designer playtesting.

---

# Module BP-W — `weapon-measure`

## Problem

Weapons are still mostly damage/accuracy bags. Combat cannot become measure-first until each weapon defines **attack delay** and **effectiveness by range band**.

## In scope

- JSON schema: `attack_delay` (AUT), measure table per band (R1 / R2 / R3 / R4+ or equivalent)
- Band geometry: Chebyshev distance + knight-move treated as band-2-reachable where applicable (shared geometry helper)
- Resolution: basic attacks multiply accuracy/damage (or technique tier) by band effectiveness
- Seed archetypes: gladius-like sword, spear, at least one heavier (axe/mace), short blade
- Examine / UI hints optional in last PR

## Out of scope

- New player keys (ctrl+dir, footwork)
- Feint-at-empty as full system (may stub mult only)
- AI personalities
- Full armory shop content pass

## Suggested PRs

| PR | Deliverable |
|----|-------------|
| **W1** | Schema + loader + validation; geometry helper (range band from actor→target) |
| **W2** | Wire basic attack resolution to delay + band mult (still adjacent-only input OK) |
| **W3** | Seed weapon data (sword / spear / axe or mace / dagger); tests; examine strings for measure feel |

## Acceptance feel

Spear at R1 is obviously worse than sword at R1 **when both can attack**; delays differ by weapon; all numbers in JSON.

## Live spec target

Extend `openspec/specs/gladiavore-match/` or add `openspec/specs/weapon-measure/`.

---

# Module BP-R — `ready-actions`

## Problem

Numpad 5 currently acts like a strong turtle button. Designer wants **two** stand-ready modes: neutral watch vs shield-timid brace.

## In scope

- Numpad 5 → keep watch: near-neutral balance (tiny defensive from inactivity only)
- `d` → brace / raise shield: clear defensive balance + defensive actual-stat lean (JSON)
- Normal step → very slight aggressive lean (JSON)
- Ensure no “stance toggle” UI — still action-driven balance deltas
- Message log: calm “you keep watch” / “you raise your guard” (via `messages.py`)

## Out of scope

- Footwork, pokes, AI
- Full shield item simulation depth (block profiles can stay stub-level)

## Suggested PRs

| PR | Deliverable |
|----|-------------|
| **R1** | Split wait vs brace actions; rebind/repurpose keys; balance deltas from JSON |
| **R2** | Step lean tweak; HUD/log clarity; tests for balance not dumping on 5 |

## Acceptance feel

Spamming 5 does **not** create a fortress; `d` is the timid/shield commitment.

## Depends

Foundation balance meter. Soft-after BP-W only for playtest order.

---

# Module BP-P — `player-combat-commands`

## Problem

Player still fights like a classic roguelike. Need **optimistic intent**, **footwork**, and **easy reach attacks** without ability-menu digs.

## In scope

### Shared intent rules (first)

- Invalid command → **no-op** (no AUT/AP/balance)
- Targeting modes Esc-cancel without cost
- Cone / “general direction” target pick (incl. knight-move foes at band 2)
- Never shame-swing empty air; R5+ no useful action → no-op
- R3–4 with weapon that doesn’t reach → **feint / false lunge** interpretation

### Footwork

- `f` → target tile
- Legal: 2 in straight line **or** knight-move; destination free/valid
- Costs: AP (≈1–2), AUT ≠ step, aggression balance; **compound** on successive footworks
- Invalid destination not selectable / Esc cancels

### Directed basic attack

- Easy binding (e.g. ctrl+direction — exact keymap in design.md)
- Homes to foe in cone; uses **weapon-measure** for effectiveness
- Basic attack AUT = weapon attack delay only

### Integration

- Smart-bump remains optimistic at R1; may call same resolver
- Abilities (`a`) stay specials — not required for poke

## Out of scope

- Momentum → evade matrix (→ BP-M)
- AI using footwork (→ BP-A)
- Jump vault content
- Full openings matrix

## Suggested PRs (do not batch)

| PR | Deliverable | Needs |
|----|-------------|-------|
| **P1** | Intent resolver core: no-op policy, cone target selection, shared API | — |
| **P2** | Footwork targeting + costs + compound spam | P1 |
| **P3** | Directed basic attack at measure (ctrl+dir or chosen bind); weapon bands live | P1, **BP-W** |
| **P4** | Feint ladder R3–4 + empty-cone policy; polish messages | P3 |
| **P5** | Key help / tutorial strings; regression tests; playtest checklist | P2–P4 |

## Acceptance feel

Bouts happen at R2; footwork is first-class; no key wastes a turn for “wrong context”; spear vs sword measure is player-visible.

## Hard dependency

**BP-W** before **P3**. **BP-R** recommended before calling BP-P “done” so ready keys match philosophy.

---

# Module BP-M — `footwork-momentum`

## Problem

Emergency evade should respect **inertia** after footwork (same direction OK; reverse very hard).

## In scope

- After footwork, apply short-lived `momentum` vector (JSON duration in AUT)
- Reaction-modal dodge: bonus same/similar dir, heavy penalty opposite
- Multi-footwork: define refresh/overwrite rule in design.md
- Display optional (status line / examine self later)

## Out of scope

- Redesigning full reaction modal options list
- AI momentum personality (can read same tags in BP-A)

## Suggested PRs

| PR | Deliverable |
|----|-------------|
| **M1** | Momentum component + apply on footwork; evade modifiers |
| **M2** | Tuning hooks JSON; tests for west-footwork / east-evade penalty |

## Depends

BP-P **P2** (footwork). Foundation reaction dodge.

---

# Module BP-A — `ai-personality-fuzzy`

## Problem

Enemy AI that pathfinds to adjacent and bumps recreates roguelike combat even with perfect player tools.

## In scope

- Personality attributes **1–10** (starter set draft: **Ferocity**, **Intelligence**, **Tenacity**, **Bloodlust** — finalize in module design.md)
- Species/entity **ranges**; instance rolls or fixed boss pins
- Each turn: candidate intents (hold measure, step, footwork, poke, commit, brace, seek clinch when legal…)
- Score = geometry fitness (weapon measure) + attribute weights + noise (imperfect)
- Enemies may footwork when personality + situation warrant
- Data-driven weights in JSON; no `if id == "wolf"` logic

## Out of scope

- Full CK2 trait catalog
- Perfect-play tactical search
- Crowd-driven AI (later crowd module)
- Replacing grapple AI entirely (hook bloodlust → grab preference only)

## Suggested PRs

| PR | Deliverable | Needs |
|----|-------------|-------|
| **A1** | Attr schema on entities + loader + roll-on-spawn | — |
| **A2** | Candidate intent list wired to **existing** player-parity actions | BP-P footwork + attacks |
| **A3** | Fuzzy scorer + JSON weights; measure-aware geometry fitness | BP-W, A2 |
| **A4** | Personality presets/ranges for current match foes; noise; tests | A3 |
| **A5** | Playtest tuning pass (JSON only if possible) | A4 |

## Depends

**Hard:** BP-W, BP-P (footwork + directed/basic attacks available to AI).  
**Preferred:** BP-M so AI/player share momentum rules.  
**Soft:** BP-R so brace exists as an AI candidate.

## Acceptance feel

Spear-ish foes try to hold range; reckless high-ferocity foes crash in; low-ferocity miss some free hits; not chess-perfect.

---

## Cross-cutting engineering rules (all modules)

| Rule | Note |
|------|------|
| Data-driven | AUT, AP, balance deltas, band mults, attr weights in JSON |
| Terminology | defeated / stunned / digested — never kill/die/death |
| Save compat | New optional fields default on load |
| No wasted turn | Intent invalid → no-op / Esc cancel |
| AUT sacred | Cooldown ≠ generic defense penalty |
| One PR at a time | Designer auth by name |
| Manual test | Checklist in chat after each PR |
| KDVR | Harvest only if it helps; no dungeon loop |

---

## Suggested OpenSpec folder layout

```text
openspec/changes/
  battle-pace-program/
    ROADMAP.md              ← this file
  weapon-measure/
    proposal.md
    design.md               ← create when module design starts
    tasks.md
  ready-actions/
    proposal.md
    design.md
    tasks.md
  player-combat-commands/
    proposal.md
    design.md
    tasks.md
  footwork-momentum/
    proposal.md
    design.md
    tasks.md
  ai-personality-fuzzy/
    proposal.md
    design.md
    tasks.md
```

**Active change pointer in AGENTS.md:** remain on `gladiavore-foundation` until a module is the sole implementation focus; then set pointer to that module for the implement session. Canon locks still read from foundation `DESIGN_CANON.md`.

---

## What “done” looks like for the whole program

1. Player can footwork, keep watch, brace, and fight at weapon measure without ability menus.  
2. Bad measure is real (especially spear).  
3. Emergency evade respects footwork momentum.  
4. Enemies express 1–10 personalities via fuzzy choice among the **same** verbs.  
5. Live specs updated; foundation loop still career hub → match → hub.

---

## Immediate next step (no code)

1. Designer reviews this roadmap (amend module splits / PR granularity).  
2. When approved: flesh **BP-W `weapon-measure`** `design.md` + `tasks.md` first (weapons are the root dependency for attack behavior).  
3. Implement only after “implement W1” (or equivalent) authorization.

---

## Document history

| Date | Note |
|------|------|
| 2026-07-17 | Initial program roadmap from battle-pace design session. |
