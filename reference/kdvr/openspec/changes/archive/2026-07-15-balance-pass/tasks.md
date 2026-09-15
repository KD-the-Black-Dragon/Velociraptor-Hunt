# Tasks: balance-pass

Long-lived, iterative. **Do not implement a batch until the designer authorizes that batch by name** (e.g. “implement PR-evade”).

## Setup

- [x] Open change folder (`proposal.md`, `design.md`, `tasks.md`)
- [x] Designer latitude intake complete
- [x] Designer goals intake (Normal primary; floor fantasy; no sim yet)
- [x] Update `Agents.md` current change pointer
- [x] Mark todo “Balance iteration” as opened in this change
- [x] Evade precedent + Normal difficulty feel recorded in `design.md`
- [x] PR-evade and PR-curve-1 designed with checklists (this file + design PR plan)

## Completed batches

- [x] **Batch 0 — docs:** latitude + goals
- [x] **PR0 — global_tuning extraction** *(authorized 2026-07-12)*
- [x] **Baseline-1 — abilities + spawn + light thematic stats**
- [x] **Evade-precedent + Normal-feel (design only)**

---

## PR-evade — implement evade system

**Auth:** authorized and **shipped** 2026-07-12. **Does not include:** mass monster retune (PR-curve-1).

### Design reference

`design.md` → **PR plan → PR-evade** (base evade 1, armor ladder, `natural_evade` rune, `effective_fighter`).

### Checklist

- [x] `data/global_tuning.json`: player `evade` = **1**
- [x] `data/armor.json`: `evade_bonus` per design ladder (robes 0 … plate 6; indigestion 0)
- [x] Armor loader / item registry: parse `evade_bonus` (default 0); SCHEMA.md
- [x] `PlayerProgression.bonus_evade` default 0; save codec soft-default (no format bump)
- [x] Floor runes: `natural_evade` effect type + piece banks; stock `evasion_rune` (weight 2, min_depth 2, pieces_per_bonus 2)
- [x] `effective_fighter`: base + armor + prog evade
- [x] UI: status corner Ev rows; armor inspect Evade bonus line
- [x] Tests: `tests/test_player_evade.py` (+ related suite green)
- [x] Update `design.md` iteration log
- [x] Post manual checklist in chat after implementation

---

## PR-evade-continuous — float evade + continuous hit roll

**Auth:** authorized 2026-07-15 (designer: formula change now; mon EV decimals too).

### Checklist

- [x] `resolve_attack`: `rng.uniform(0, evade)` not `randint`
- [x] `Fighter.evade`, `bonus_evade`, entity/armor/prefix/global_tuning/depth: float
- [x] Save codec: float evade / bonus_evade (soft-read)
- [x] SCHEMA + npc-data + balance specs + design.md
- [x] Tests: continuous hit rates; miss-rate pin updated
- [x] Post manual checklist after tests green

---

## PR-curve-1 — Normal mon hit bands + early survivability

**Auth:** not yet. **Depends on:** PR-evade shipped (or designer allows combined auth).

### Design reference

`design.md` → monster pairing table + F1–3 survivability + **Normal not super-brutal**.

**Auth:** authorized and **shipped** 2026-07-12.

### Checklist

- [x] Retune species `accuracy` / `evade` for on-pace ~50% mon hit / ~67% player hit vs peers
- [x] Light early TTK (rat/bat/wolf HP) — dig dmg left alone
- [x] Normal `depth_scaling` accuracy banks remain tiny (no Hard/Nightmare drift)
- [x] Dragon acc 8.0 — Yeti (always connects through plate E7)
- [x] No stock number pins in tests; existing roster tests still structure-only
- [x] Iteration log + manual checklist in chat

### Manual playtest focus

- [ ] F1–2: cautious melee-only usually fine; mon hits ~50% with robes
- [ ] F3+: items matter; wolf ~50% hit vs robes, you ~67% vs wolf evade 2
- [ ] Mid: peer foes track armor era bands; low-tier falls off
- [ ] F20+ dragon: engage = you lose (nearly always hits)

---

## PR-spawn-freeze — distant spawn AI freeze (anti-swarm)

**Auth:** designer priority 2026-07-12 — **shipped**.

### Checklist

- [x] `SpawnAiFreezeConfig` on difficulty profiles (`depth_scaling.json`)
- [x] `AIState.spawn_freeze_remaining` / `spawn_freeze_consumed` + save soft-default
- [x] Arm freeze at floor spawn from Chebyshev to player
- [x] Tick freeze in `run_monster_turns`; proximity and damage clear; one-shot only
- [x] SCHEMA + tests (`tests/test_spawn_ai_freeze.py`)
- [x] Stock Easier more generous freeze than Hard/Nightmare

### Manual

- [ ] Depth 3: far packs do not all rush at once; near wolves still engage
- [ ] Walking toward a frozen pack wakes them at proximity
- [ ] Damaging a frozen NPC (e.g. wand) wakes them for combat

---

## Playtest-d7 batch *(from designer notes — shipped)*

- [x] Kobold: add `NoChase`
- [x] Slightly tougher early–mid monsters (rat→gnoll band)
- [x] Wand spawn weights cut (magic missile 50→5; pool share ~20–25% not ~70%)
- [x] Longer `spawn_ai_freeze` (Normal: ×3, max 64, offset 5, prox 7)

## Later / unscheduled (deferred out of this change)

- [ ] PR-curve-2+ further mid/deep after next playtest *(deferred)*
- [ ] Easier / Hard / Nightmare differentiation pass *(partial: Hard pare + Easier rename; further deferred)*
- [ ] Optional player accuracy growth / mon evade float ladder for true 75–80% peer hit *(deferred; noted in design)*
- [ ] Sim calibration only after designer certifies a balanced Normal baseline *(baseline accepted; sim optional later)*

## Final acceptance (when designer says done)

- [x] Iteration log complete enough for future re-entry
- [x] Normal accepted; other difficulties as designer cares *(designer: balance acceptable for the moment)*
- [x] Acceptance report + archive move
- [x] Clear `Agents.md` active change pointer
- [x] Update `openspec/changes/todo/spec.md`

## Rules

1. Prefer `data/` JSON; code only for authorized named PRs (PR-evade is code+data).
2. One authorized PR/batch at a time.
3. Never pin live balance numbers in tests.
4. No sim until designer-approved baseline.
