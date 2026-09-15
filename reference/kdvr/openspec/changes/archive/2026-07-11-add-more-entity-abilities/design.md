# Design: More entity abilities

**Status:** Design complete (2026-07-11). Open questions resolved. Awaiting explicit PR1 authorization before implementation.

**Terminology:** defeated, stunned, digested.

---

## Approved scope

### In this change (implement)

| Item | Kind | Summary |
|------|------|---------|
| **Hands** | Ability | Finish shipped stub: traverse and **open** closed doors on step |
| **Wander** | Ability | Mindless drift — no targeting; explore only (DCSS spore / living fire style) |
| **NoChase** | Ability | Evil — chase visible quarry; drop pursuit when quarry leaves LOS |
| **PreferVore** | Ability | When a vore attempt is otherwise legal, **100%** attempt (skip `vore_decision_chance` roll) |
| **RangedVoreN** | Ability (`N` = 2–9) | Vore attempt at Chebyshev distance `[2, N]` with LOS; on **hit**, pull prey to predator tile then normal engulf; on **miss**, no pull |
| **Stationary** | **Mobility type** | New `mobility` value — entity does not voluntarily move; holds its spawn tile (see below) |

### Deferred (todo backlog — not this change)

| Item | Notes |
|------|-------|
| **Thorns** | Reflect melee damage to attacker on hit — revisit in a future abilities pass |

Unnamed brainstorm candidates from the first review are **dropped** (not blacklisted; may return in a future brainstorm).

---

## Shipped baseline (unchanged unless noted)

Existing abilities: `Fast`, `Slow`, `Erratic`, `Coward`, `Supercoward`, `SmiteN`, `RangeN`, `SummonN <id>`, `Knockback`, `Lifedrain`.

**Vore today:** adjacent only; `should_attempt_vore()` also rolls `vore_decision_chance(hp_frac)` after eligibility checks (`src/systems/vore.py`). Player path opens modal; NPC path is log-only then `engulf_npc()` co-locates prey on hit.

**Hands stub today:** explore/chase BFS may treat `DOOR_CLOSED` as traversable for entities with `Hands`; doors are **not** opened on step yet (`enhancements-3`).

---

## Ability specifications

### Hands

**Token:** `Hands` (fixed id)

**Behavior:**

- During movement (explore, chase, flee, erratic steps), bumping a **closed door** **opens** it without moving (same as player bump-open — turn consumed, actor stays put).
- **80%** open → `DOOR_OPEN`; **20%** break → `FLOOR` (DCSS-style anti-footsie).
- Explore/chase BFS reachability treats closed doors as passable for `Hands` holders; actual step onto a closed door is the bump interaction above, then a later turn may walk through.
- Non-`Hands` entities unchanged.

**Logs (FOV-gated):**

| Outcome | Player sees opener | Door only in FOV | Category |
|---------|-------------------|------------------|----------|
| Open | *"{Name} opens the door."* | *"Something opens the door."* | routine |
| Break | *"{Name} breaks down the door!"* | *"Something breaks down the door!"* | caution (yellow) |

Templates in `src/messages.py`.

**Species fit (content PRs, not blocking):** kobold, gnoll mercenary, owl mage.

---

### Wander

**Token:** `Wander` (fixed id)

**Behavior:**

- Entity **never enters chase mode** and has **no animosity targeting** — mindless dungeon hazards (DCSS spores, magical fire).
- When not fleeing (`Coward` / `Supercoward` / baseline neutral flee) and not in a combat-forced action, intent is **explore only** (weighted-random far goals per `enhancements-3`).
- May still deal **bump damage** to anything in its path; does **not** pursue after contact.
- `Wander` does **not** block: `SummonN` on first sight or vore attempts when legal (rare on mindless spawns).
- Stacks with `Slow` / `Fast` / `Erratic` unless a combination is explicitly forbidden at implementation time.

**Logs:** None (movement-only temperament).

**Species fit:** mindless evil hazards (spores, living fire) — **not** rabbits (rabbits use baseline neutral flee + explore).

---

### NoChase

**Token:** `NoChase` (fixed id)

**Behavior:**

- **Evil only** (meaningful on evil predators; ignored for good/neutral movement semantics).
- **While quarry is visible:** normal evil chase — pursue player or valid visible targets, melee, ranged, vore as usual.
- **When quarry leaves LOS:** immediately give up — **no** last-known tile pursuit, **no** memory-blind trail, **no** chase momentum steps. Resume explore (or visible neutral/opportunistic targets).
- Thematic: *"Yeah, get out of here!"* — opportunistic aggression without chase-down.
- Memory fields (`last_known_primary`, `last_known_neutral`) are **cleared** on turns where no quarry is visible.

**Logs:** None.

**Species fit:** lazy or territorial evils that fight what they see but won't hunt (e.g. tunnel slug, tarantula).

**Not combinable with `Wander` in content** (redundant); not a load error.

---

### PreferVore

**Token:** `PreferVore` (fixed id)

**Behavior:**

- When `should_attempt_vore()` (or the ranged-vore eligibility helper) would return eligible **except** for the decision roll, **skip the RNG decision roll** and treat the attempt as committed (100%).
- Does **not** bypass other guards: `VoreCapable`, alignment, LOS, adjacency/range, `VoreMercy`, `Engulfed`, narrative-type prefs, `is_vore_eligible` HP threshold, predator already holding prey, etc.
- Applies to **both** adjacent vore and `RangedVoreN` attempts.

**Logs:** None beyond existing vore attempt lines.

---

### RangedVoreN

**Token:** `RangedVore2` … `RangedVore9` (parameterized family; duplicate tokens collapse to max `N` like `SmiteN` / `RangeN`)

**Behavior:**

- Enables vore attempts against eligible prey at **Chebyshev distance** in `[2, N]` with **line of sight** (same LOS helper as combat/vore today).
- **Adjacent** eligible prey still use the normal adjacent vore path (distance 1 is not a ranged vore shot).
- Eligible prey: same rules as adjacent vore — player (modal path) and good/neutral NPCs (`is_vore_eligible`, not `Engulfed`, not `VoreMercy`, etc.).
- **Decision:** roll `vore_decision_chance` unless predator has `PreferVore` (then 100% when legal).
- **Hit resolution:** same `resolve_vore_hit()` as adjacent vore.
- **On hit:** move prey to predator's tile (co-locate), then `engulf_npc()` / player engulf flow — same as adjacent success. Thematic “tongue / telekinesis lasso” is narrative-only.
- **On miss:** no position change; attempt still consumes the predator's action (same as adjacent miss).
- **Stunned 0 HP prey:** `RangedVoreN` is **not** subject to the Path/Smite “close on stunned” rule. That rule exists only so damage shooters stop plinking a 0 HP target. A legal ranged vore shot **may** target stunned prey at range (prey ≤50% HP, in `[2, N]`, LOS, other guards pass).
- **Decision / AI:** When a ranged vore shot is **legal**, the predator **must consider** it among valid actions that turn — same fuzzy `vore_decision_chance(hp_frac)` roll as adjacent vore (100% if `PreferVore`). It is **not** guaranteed over chase, damage ranged, or melee. Weaker prey → higher chance via existing HP-fraction curve.
- **Dual tongue (stock pattern):** e.g. `Range5` + `RangedVore5` on a frog — same reach for slap vs grab. When prey **>50% HP**, only damage ranged applies. When prey **≤50% HP**, both damage ranged and ranged vore are valid considerations; vore branch uses decision roll / `PreferVore`.

**Logs:**

- Player target: existing vore modal + initiation logs (no separate pull line required for v1).
- NPC target: existing NPC vore hit/miss pools.

**Species fit:** giant frog (future), owl mage (telekinetic themes), other “grab from afar” predators.

**Incompatibilities:** none with `Erratic`. `RangedVoreN` may stack with `RangeN` / `SmiteN` per dual-tongue pattern above.

---

## Mobility specification: Stationary

**Not an ability.** Extend `mobility` on `entities.json` entries.

**New value:** `stationary` (loader accepts alongside `ground`, `fly`, `aquatic`).

**Behavior:**

- Entity **does not take voluntary movement steps** — explore, chase, flee, erratic random, and coward flee steps that would move the entity are skipped (turn may still pass via wait or no-op step).
- **`Coward` on stationary:** no effect (flee cannot move). Content-authoring mistake if combined; **not** a load error — `Coward` simply does nothing. Per baseline coward rules, when flee is blocked the entity **attacks or waits**; stationary entities attack adjacent threats in desperation rather than idle forever.
- Entity **may still attack** via bump combat when a legal target is in range (adjacent for ground; aquatic shore rules unchanged for water-bound stationary if we ever need it).
- Entity **may still** use ranged abilities, vore attempts, and summons without moving.
- **Knockback** may move a stationary entity; designer accepts this edge case for v1.
- **Spawn:** placed once at spawn; no explore goal picking.
- **Follow / descent:** stationary goods do not “follow” the player between floors unless designer later opts in — v1: **do not follow** (same as evil/neutral today).

**Traversal:** `stationary` entities are not “on” water/fly tiles unless explicitly placed there at spawn; no mobility traversal table entry needed beyond “cannot move.”

**Species fit:** tunnel slug turret, guarded idol, future “fixed” encounters.

**Specs to update:** `openspec/specs/dungeon/spec.md`, `data/SCHEMA.md`, entity loader validation.

---

## Resolved decisions

| Decision | Outcome |
|----------|---------|
| Ability shortlist | **Locked** — Hands, Wander, PreferVore, RangedVoreN |
| Stationary | **Mobility field**, not `abilities[]` |
| Thorns | **Deferred** to `openspec/changes/todo/spec.md` |
| Unlisted brainstorm items | **Dropped** for now (not blacklisted) |
| PreferVore rename | `PreferVore` replaces working name `VorePriority` |
| PreferVore semantics | 100% attempt when legal; does not bypass eligibility guards |
| RangedVore + stunned | **May** ranged-vore stunned prey; Path/Smite close rule does **not** apply |
| RangedVore AI | **Consider** among valid moves; `vore_decision_chance` unless `PreferVore` |
| Dual tongue | `RangeN` + `RangedVoreN` same N — damage when prey >50% HP; both considered when ≤50% HP |
| Hands logs | Door-only FOV → *"Something opens the door."*; see opener → *"{Name} opens the door."* |
| Stationary + Coward | Allowed; Coward no-op on stationary; attack when cornered |
| PR order | **Locked** — see PR plan below |
| Wander vs NoChase | **2026-07-11** — Wander = mindless hazard; NoChase = opportunistic evil (visible only) |

---

## PR plan

*(Awaiting explicit “proceed PR1” before code.)*

| PR | Deliverable | Rationale |
|----|-------------|-----------|
| **PR1** | `PreferVore` — parser, `should_attempt_vore` decision bypass, tests | Smallest vore-layer hook; prerequisite for RangedVore decision path |
| **PR2** | `Wander` — intent pipeline branch, tests | Isolated AI; no vore/combat changes |
| **PR3** | `Hands` — door open on step, FOV logs, tests | Movement layer + `messages.py` |
| **PR4** | `stationary` mobility — loader, AI movement gate, dungeon spec, tests | Orthogonal mobility work before complex ranged vore |
| **PR5** | `RangedVoreN` — parser, eligibility, pull-on-hit, intent consideration, tests | Largest slice; builds on PR1 decision rules |
| **PR6** | Content — assign tokens / mobility in `entities.json` | Data-only after all mechanics land |
| **PR7** | Live spec merge, acceptance checklist, archive | Final gate |

---

## References

- `openspec/specs/npc-abilities/spec.md`
- `openspec/specs/vore/spec.md`
- `openspec/specs/dungeon/spec.md` (mobility)
- `openspec/specs/enhancements-3/spec.md` (explore / Hands stub)