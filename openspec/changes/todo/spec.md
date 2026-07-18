# todo Specification

## Purpose

**todo** tracks known bugs and improvements **deferred** until an appropriate change module, plus a **future design backlog** of designer-priority ideas not yet opened as OpenSpec changes.

Items here are **not** in active scope; do not implement during unrelated PRs unless the user explicitly redirects.

**Terminology:** defeated, stunned, digested — no kill/die/death.

---

## Future design backlog

Captured 2026-07-09 from post–`add-potion-effects` roadmap discussion. Each item is a **core concept** only — full design and PR plans come when the change is opened.

### Priority content / systems

#### Item: More entity abilities — **shipped**

**Archive:** `openspec/changes/archive/2026-07-11-add-more-entity-abilities/` (2026-07-11). Hands, Wander, NoChase, PreferVore, RangedVoreN, `stationary` mobility. Thorns deferred below.

---

#### Item: Thorns ability (deferred)

**Core concept:** Melee attackers take reflected damage when hitting a `Thorns` holder.

**Purpose:** Spiky species identity (e.g. tarantula) without a full status-effect framework.

**Notes:** Pulled from the 2026-07-11 abilities brainstorm; implement in a future abilities pass when desired.

---

#### Item: More floor-rune types and deeper piece banks

**Core concept:** Grow `floor_runes.json` effect variety and use **piece-based thresholds** more deeply (beyond mild warding multi-piece).

**Purpose:** Exploration progression is the main power curve; more rune identity and slower/steeper banks give balance knobs without XP leveling.

**Notes:** Orthogonal to difficulty depth scaling; keep integer combat math and sticky freeze rules.

---

#### Item: Extra NPC prefixes beyond Elite — **shipped**

**Archive:** `openspec/changes/archive/2026-07-11-add-extra-npc-prefixes/` (2026-07-11). Brute, Berserk, Veteran, Starving, Sniper, Bloated; filter-then-roll `requirements`; `grant_abilities`; `ranged_accuracy`.

**Core concept:** Add more rows to `npc_prefixes.json` (and difficulty `prefix_spawn` as needed) so floor threats can be **visibly and mechanically modified** without new entity ids.

**Purpose:** Free variety and pressure (names + flat bonuses); Elite was the v1 proof of the prefix system.

**Notes:** Still floor-population only for random rolls unless design expands summons later.

---

#### Item: More deep good allies

**Core concept:** Ship additional **good-aligned** species that become available at **deeper depths** (data-driven spawn windows), so alliance / follower fantasy scales with descent.

**Purpose:** Potion of alliance and dog knights already assume depth-eligible goods; only knight exists as a real good. Future “dragon knight at depth 20” style content belongs here.

**Notes:** Weighted good pool at depth is already summon-ready; this is primarily **content + themes**, not new summon code.

---

#### Item: Balance iteration (playtest-driven) — **opened**

**Active change:** `openspec/changes/balance-pass/` (opened 2026-07-12).

**Core concept:** Ongoing **iterative balance** of difficulty curves, spawn bands, density, elite pressure, loot/rune economy, and species threat — driven by designer playtests (“depth X too easy”, power spikes, etc.).

**Purpose:** Soft-yeti deep pressure and early approachability are design goals; content and systems still land frequently, so hard balance freezes are premature.

**How Grok Build can help:** Apply reported, concrete notes (JSON knobs, spawn windows, depth_scaling); profile if lag is blamed; avoid inventing balance without designer feedback. **Code only if data cannot express intent, and only with explicit authorization.**

**Notes:** Long-lived OpenSpec change; complete only on designer sign-off. Prefer fixture-pinned tests; never pin live balance numbers in tests.

---

### Priority engineering (player-invisible)

Do **not** pursue change-for-change’s-sake. Each item below was accepted for **measurable** maintenance or safety value.

#### Items: Five-item engineering pass — **completed**

**Archive:** `openspec/changes/archive/2026-07-10-engineering-maintainability/` (accepted 2026-07-10).

| Item | Core concept (summary) | Status |
|------|------------------------|--------|
| Test helpers for spawn-at-depth / difficulty | Shared fixtures for species @ depth under a difficulty | **Completed** (PR1) |
| Message / string catalog discipline | Full remaining player-facing log strings → `messages.py` | **Completed** (PR2) |
| Save codec / snapshot schema hardening | Field inventory, additive defaults, golden/round-trip; no format bump | **Completed** (PR3) |
| Split GameEngine / thin app shell | Floor → turn → input extracts, then deeper cleanup | **Completed** (PR4–PR7) |
| Modularize AI by intent | Explore → chase/targeting → movement/visit, then deeper cleanup | **Completed** (PR8–PR11) |

**Historical note:** Prior `engineering-cleanup` (archive 2026-07-09) was **save soft-drop + flaky tests**, not this structure pass.

---

### Opened as active change

| Item | Change folder |
|------|----------------|
| Balance difficulty analyzer (hybrid sim) | `openspec/changes/archive/2026-07-12-add-balance-simulator/` *(archived)* |
| More entity abilities | `openspec/changes/archive/2026-07-11-add-more-entity-abilities/` *(archived)* |
| Extra NPC prefixes beyond Elite | `openspec/changes/archive/2026-07-11-add-extra-npc-prefixes/` *(archived)* |
| Player thrown weapons + Smite/Path ranged | `openspec/changes/archive/2026-07-11-add-thrown-weapons-and-ranged-pathing/` *(archived)* |

---

### Explicitly not pursuing (designer decision)

| Idea | Reason |
|------|--------|
| **Externalize vore narratives out of `entities.json`** | Designer **disagrees** there is a problem. Prefers one file per monster for simplicity and **modding** (add a monster without managing a second narrative file). Do **not** split narratives unless the designer revisits this. |
| **Turn-pipeline performance budget / deep-floor profile module** | Not requested now; prior AI/hotpath work already shipped. Only reopen if play/profile shows real lag. |

---

## Historical deferred items (resolved or parked)

### Item: Performance issues — core lag

**When addressed (core):** `openspec/changes/archive/2026-07-05-fix-performance/` — Tier A BFS caching. Live: `openspec/specs/performance/spec.md`.

### Item: Performance — distant NPC throttle

**When addressed:** `openspec/changes/archive/2026-07-08-fix-performance-ai-hotpath/` (D1 simplified explore and D5 stand-still remain out of scope).

### Item: Better NPC exploration

**When addressed:** `openspec/changes/archive/2026-07-05-better-npc-exploration/`.

### Item: Door spite — distant wolf should approach door first

**Enhancement:** When door spite activates for a wolf still far from a slammed door, path to the door then linger — do not freeze in place for the full timer far away.

**Status:** Small follow-up; still open if not done. Not blocking prior exploration acceptance.

---

## Active work

- **`balance-pass`** — `openspec/changes/balance-pass/` (data-first iterative balance; latitude intake in progress).

When starting a backlog item: open `openspec/changes/<name>/` with proposal/design/tasks per `AGENTS.md`, set the Current change pointer, and remove or mark the item here when archived.
