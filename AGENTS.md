# AGENTS.md

Master instructions for AI agents and contributors working on **Gladiavore**. Read this file at the start of every task, especially after conversation compaction.

Active feature work lives under `openspec/changes/<change-name>/`. Live specs live under `openspec/specs/`.

**Lineage:** This tree began as a clone of **K.D.'s Vore Roguelike (KDVR)**. The product is **Gladiavore**, not KDVR. Read **`KDVR_REFERENCE.md`** before harvesting. KDVR-only modules live under **`reference/kdvr/`** (not product runtime). Do not continue dungeon-crawl as the product loop.

---

## Project

| Item | Detail |
|------|--------|
| Game | **Gladiavore** — career roguelike; curated arena matches + downtime hub; libtcod ASCII/turn-based |
| Fantasy | Gladiatorial career (WWAATD / Battle Brothers–inspired); predators may digest fighters in red matches |
| Language | Python 3.11+ |
| Engine | libtcod 16.x |
| Architecture | Lightweight ECS (`tcod.ecs` or thin custom registry) |
| Run | `python -m src.main` |
| Tests | `python -m pytest tests/ -v -n 4` (see **Full test suite runs**; targeted runs: **Test parallelization**) |
| Game data | `data/*.json` — schema reference in `data/SCHEMA.md` (will retarget as Gladiavore content lands) |
| User data | Outside install dir — product name **Gladiavore** (see `README.md`; rebrand in foundation PR1 if still KDVR-named in code) |
| Profiling | `tools/profile_turn.py` (use when investigating turn cost) |
| Foundation design | `openspec/changes/gladiavore-foundation/` |
| **Permanent Q&A / design canon** | `openspec/changes/gladiavore-foundation/DESIGN_CANON.md` — **read after compact; do not re-ask locked decisions** |
| KDVR harvest rules | `KDVR_REFERENCE.md`; quarantined code under `reference/kdvr/` |

**Terminology (mandatory):** enemies are **defeated** (never killed); fighters at 0 stamina HP are **stunned** / incapacitated; permanent removal via vore is **digested**. Do not use kill / die / death in code, logs, specs, or agent prose.

**Combat motifs (Gladiavore):** **base stats** vs **actual stats** (resolution always uses actual); **balance** meter from actions (not stance toggles); **ability points**; openings/vulnerabilities over pure chip damage. Details: foundation `design.md`.

**Modding:** KDVR-era modding shipped in tree — re-evaluate for Gladiavore; do not expand unless the active change says so. Spec: `openspec/specs/modding/spec.md` (historical until revised).

---

## Current change pointer

Update this line when starting or archiving a change:

**Active change:** long-lived pillars `openspec/changes/gladiavore-foundation/`; recently signed off: `openspec/changes/grapple-swallow-modals/`, `openspec/changes/match-hud-ux/`; **Battle Sport (design frozen, not implemented):** `openspec/changes/battle-pace-program/BATTLE_SPORT_SPEC.md` + `openspec/specs/battle-sport/spec.md` + module `design.md` files (`weapon-measure`, `ready-actions`, `player-combat-commands`, `footwork-momentum`, `ai-personality-fuzzy`) — implement only after designer authorizes whole batch; superseded product work: `openspec/changes/balance-pass/` (KDVR-era); last archived: `openspec/changes/archive/2026-07-15-convenience-controls/`

---

## Project Philosophy

The user is the game's **lead designer**. Preserve the creative vision exactly, but treat implementation details as flexible.

When the user proposes a technical solution, interpret it as an expression of **intent**, not a mandatory implementation.

The user is not a programming or Python expert. Requests that sound technical may still be **creative direction**. Your role is to find the best technical path to achieve that vision.

- **Creative direction** (e.g. good vs evil NPCs, vore tone, UI feel) — implement faithfully; clarify mechanical meaning if needed, but do not push back on the creative choice itself.
- **Technical direction** (e.g. "use a double here") — you own the engineering decision; explain tradeoffs and recommend the better approach when it differs from what was said.

If a different implementation better satisfies the design while improving performance, maintainability, readability, extensibility, or robustness, explain the tradeoffs and recommend the better approach. Do not silently substitute your preference — discuss first when the choice is non-obvious.

---

## Performance First

Player responsiveness is a primary design goal.

Before implementing any feature:

- Consider its asymptotic complexity.
- Consider worst-case behavior.
- Consider large numbers of NPCs.
- Consider future content growth.
- Avoid per-frame work unless absolutely necessary.

After implementation, perform a second review asking:

- Can this be cached?
- Can work be deferred?
- Can work be event-driven?
- Can this allocation be avoided?
- Is there unnecessary iteration?
- Is there a simpler algorithm?

Do not assume "fast enough" merely because current content is small.

**Performance vs design:** There is no default rule for whether to preserve exact AI decisions, player-visible outcomes only, or something in between. When a request or design likely has significant performance cost — especially NPC AI, which is both heavy and highly interactive — present alternatives with pros and cons and let the user choose between performance and design fidelity. Never optimize in a way that changes gameplay without disclosure and approval.

---

## Preserve Existing Behavior

Whenever optimizing or refactoring:

- Preserve gameplay behavior unless explicitly instructed otherwise.
- Prefer implementation improvements over gameplay compromises.
- Only recommend simplifying gameplay if meaningful performance gains cannot reasonably be achieved otherwise — and only after presenting tradeoffs to the user.

---

## Data-Driven Design

Whenever practical:

- Put gameplay values into JSON.
- Avoid hardcoded numbers, names, dialogue, and entity-specific logic.
- Design systems so new content can be added without modifying Python code.

Whenever introducing a hardcoded value, ask whether it belongs in data instead.

**Hardcoding policy:**

- **No new hardcoded gameplay values without user approval.** Existing hardcoding is grandfathered unless the user asks to change it.
- **No logic hardcoded to a single entity type** (e.g. no `if id == "wolf"`). Use data, abilities, and shared systems instead.
- **Secondary attribute traits may be hardcoded** when they describe behavior classes shared across many entities — e.g. `good`, `evil`, `ranged2`, `erratic`, alignment rules, FOV rules, UI patterns.

---

## Extensibility

Assume future additions.

Design code that naturally supports:

- more monsters
- more items
- more abilities
- more dungeon generators
- more equipment
- more dialogue
- mods (shipped — see Modding line above)

Avoid implementations that require future copy-and-paste.

---

## Simplicity

Prefer the simplest implementation that satisfies:

- correctness
- readability
- maintainability
- extensibility
- performance

Avoid clever code, unnecessary abstraction, and premature generalization.

---

## Regression Safety

Protect existing behavior.

Whenever changing code:

- Identify affected systems and likely regressions.
- Update or add automated tests when practical.
- Pin test data via isolated fixtures (`tests/*_test_helpers`, inline minimal JSON in tests) — not live `data/` balance values you tune during playtest.
- Never rely on gameplay balance numbers inside automated tests.

Some areas (pure visual feel, subjective layout) may be manual-only when automated tests are impractical.

---

## Manual Testing

The user validates work through **black-box playtesting**, not code review or white-box testing.

After **every PR the user can meaningfully playtest**, the agent **must** post an explicit manual checklist **in chat** (not only as a file reference).

Include:

- How to run: `python -m src.main`
- Happy path — concrete checkbox-style items
- Edge cases and regression risks from earlier PRs (brief)
- UI behavior
- Save/load (if applicable)
- Performance considerations (if applicable)
- Pointer to `openspec/changes/<change>/testing-checklist-prN.md` for the full list

Do not consider a PR complete until the user has performed manual testing. Wait for user sign-off (or bug reports) before starting the next PR.

---

## OpenSpec Workflow

Follow the project's OpenSpec process. We do not require OpenSpec slash commands, but we follow the same artifact shape.

**This gate applies to all work** — features, bug fixes, tweaks, docs — unless the user explicitly says to skip OpenSpec. Only the user may override.

### Before coding

| Phase | Artifacts | Required |
|-------|-----------|----------|
| New feature or domain | `proposal.md`, `design.md`, `tasks.md` in `openspec/changes/<name>/` | Yes — all three exist and PR plan is clear |
| PR-sized slice | Current PR section in `tasks.md` | Yes — know which PR is active |
| Acceptance | `testing-checklists.md`, `acceptance-report.md`, archive folder | End of change only |

**Artifact roles:**

- Behavioral requirements → `openspec/specs/<capability>/spec.md` (create or extend when the change lands).
- Implementation detail → `design.md` in the change folder.
- PR checklist → `tasks.md` (one checkbox per PR).
- Per-PR manual steps → `testing-checklist-prN.md` in the change folder.

**Never** skip planning.

### PR implementation gate (mandatory)

**Do not implement any PR until the user explicitly authorizes it.**

Answering clarifying questions, approving design decisions, or reviewing `proposal.md` / `design.md` / `tasks.md` is **not** implementation authorization. Updating design docs after Q&A is **not** authorization. Only the user may authorize coding.

**Authorization looks like** the user clearly telling you to implement — e.g. “implement PR1”, “go ahead with PR1”, “proceed with the plan”, “start coding PR1”. If unsure, **stop and ask**.

**Before the gate opens**, you may:

- Draft or revise OpenSpec artifacts (`proposal.md`, `design.md`, `tasks.md`)
- Answer questions and record **Resolved decisions** in `design.md`
- Present the plan and wait

**After the gate opens** (user authorized one PR), you may implement **only** that PR — still **one PR at a time**.

**Never** begin coding automatically after design review. **Never** treat “move on to whatever is next” as PR authorization unless the user also explicitly approves implementation of a named PR.

### One PR at a time

- Implement **only the next unchecked PR** in `tasks.md` **after user authorization for that PR**.
- Do not batch multiple PRs unless the user explicitly asks.
- When a PR is done:
  1. Run **targeted tests** for that PR (**parallelize** when multi-file / large — see **Test parallelization**).
  2. Check off the PR in `tasks.md`.
  3. Post the **Manual Testing** checklist in chat.
- Run the **full** `pytest tests/` suite only after the user's **final sign-off** on the change (final acceptance PR). Follow **Full test suite runs** below.

### Midstream changes update the spec

Any ad-hoc design or behavior change agreed in chat (playtest feedback, bug fix that changes intent, new rule) must be reflected in writing **before or with** the code:

| Change type | Update |
|-------------|--------|
| New behavior / requirement | `openspec/specs/.../spec.md` or change `design.md` + note in `proposal.md` |
| PR scope shift | `tasks.md` and relevant `testing-checklist-prN.md` |
| Resolved decision | `design.md` **Resolved decisions** table |

Do not leave specs contradicting the game.

### Session startup (after compact or new chat)

1. Read this file (`AGENTS.md`).
2. Find active change: `openspec/changes/` (non-archive folders only).
3. **If active change is `gladiavore-foundation`:** read **`openspec/changes/gladiavore-foundation/DESIGN_CANON.md`** first (locked designer Q&A). Do not re-ask those decisions.
4. Read `tasks.md` — identify first unchecked PR.
5. Read that PR's section in `design.md` if implementing.
6. **Do not code** until the user has authorized that PR (see **PR implementation gate**). If unclear which PR is active or whether implementation is authorized, ask.

### Archive completed changes

Move to `openspec/changes/archive/YYYY-MM-DD-<name>/` on final acceptance PR. Update the **Current change pointer** above.

---

## Ask When Uncertain

If requirements are ambiguous:

- Ask questions.
- Identify assumptions.
- Explain tradeoffs.

Do not invent gameplay. Do not silently choose game mechanics.

---

## Code Quality

Generated code should be:

- readable and well-structured
- documented where appropriate — match the codebase's **light docstring** style on new public APIs and loaders
- consistent with the existing codebase
- free of dead code, debug prints, and unused imports
- **message-log prose** via `src/messages.py` (not inline literals) — see `openspec/specs/engineering/spec.md`

Leave the project cleaner than you found it.

**Run tests yourself** — do not tell the user to run commands you can run.

### Test parallelization

The host machine is powerful. **Use parallel pytest whenever practical** so targeted suites finish quickly.

| Case | Command pattern |
|------|-----------------|
| Multi-file / large targeted set | `python -m pytest path1 path2 … -n 4` |
| Single-file / few tests / debugging one failure | serial OK: `python -m pytest path::test -v` |

- Prefer **`-n 4`** via **pytest-xdist** (`dev` extra: `pytest-xdist`). Avoid `-n auto` when it spawns so many workers that OpenBLAS/memory OOM causes false failures.
- If xdist is missing, install dev deps (`pip install -e ".[dev]"`) rather than running multi-thousand-test suites serially.
- Parallelize any targeted run that covers many files or is expected to take more than a few seconds.
- Serial is fine for a single test or when isolating a flaky failure.

### Full test suite runs

When running the **entire** `pytest tests/` suite (typically final acceptance), follow this procedure exactly. Do **not** re-run the full suite wholesale after a partial failure — work through the lists below.

**Worker default:** **4 workers** (`python -m pytest tests/ -v -n 4`). The user may override and request a different count (usually **1** or **4**); use that count for step 1 and step 8.

| Step | Action |
|------|--------|
| 1 | Run the full suite. Default: **4 workers** (`-n 4`). |
| 2 | User may override the worker count (usually **1** or **4**); if they do, use that count in steps 1 and 8. |
| 3 | Split results into **passed** and **failed**. |
| 4 | Re-run **only the failed cases serially** (`-n 0` or omit `-n`) — multithreading is known to cause some flakiness. |
| 5 | Split into **passed at least once** (passed on step 1 or step 4) and **failed twice** (failed on both step 1 and step 4). |
| 6 | Investigate and fix **only** the **failed twice** cases. |
| 7 | Re-run **only** the **failed twice** cases serially. Iterate fix → rerun within reason. If failures persist despite reasonable fixes, **inform the user** — do not loop indefinitely. |
| 8 | Re-run the **passed first try** list (cases that passed on step 1 and were never in the step-4 failure set) using the **same worker count as step 1** (4 or 1, per user). |
| 9 | Re-run the **failed at least once** list (everything that failed on step 1, whether or not it passed on step 4) **serially**. |
| 10 | **Stop.** Report results to the user: what passed, what was fixed, and any remaining failures. |

**Lists shorthand:**

- **Passed first try** — green on the initial parallel (or serial) full-suite run; never sent to step 4.
- **Failed at least once** — red on step 1 (includes cases that recovered on step 4).
- **Failed twice** — red on both step 1 and step 4; only these may drive code changes during the run.

**Commands:**

```text
# Step 1 — full suite (default 4 workers; use -n 1 if user requested serial)
python -m pytest tests/ -v -n 4

# Step 4 / 7 / 9 — serial reruns of a specific list
python -m pytest path::test_name path2::other -v
```

---

## User Experience

Whenever implementing a feature, consider:

- responsiveness
- keyboard usability
- discoverability
- consistency with existing UI
- informative error messages

If a user-facing error is possible, prefer a friendly dialog over a traceback.

**Accessibility:** Aspirational — add it when it is a freebie; do not block features for extensive accessibility work unless the user asks.

---

## Content and visibility rules

- **AV content:** Clean scope only — engulfment and abdominal crushing. No expanded AV semantics unless the user explicitly approves.
- **NPC log visibility:** Combat, regen, vore, rescue, and digestion messages are gated on player FOV unless a spec explicitly says otherwise.

---

## Save Compatibility

Players must be able to resume runs after frequent updates whenever practical.

**Before any change that touches persistence or game data, silently ask:** *Could this break an existing autosave?* Then mitigate:

| Risk | Preferred mitigation |
|------|----------------------|
| New optional state (enchantment, rings, flags) | Default on load if missing (e.g. enchantment `0`) |
| New content only (new bats/items) | No action — old saves simply lack them |
| Removed/renamed item or entity **id** | **Soft-drop** on load (clear slot / despawn entity); notice player; do **not** treat as corrupt |
| Renamed save fields | Dual-read old+new for a while, or migrate |
| True wire-format break | Bump `save_format_version` + migration; **consult designer** first |
| Cannot mitigate without design choice | **Consult the designer** — never silently hard-break loads |

Also:

- Prefer additive save fields; avoid requiring new keys without defaults.
- Preserve JSON schema compatibility for `data/` when practical.
- Mod fingerprint mismatch remains a separate, intentional gate.
- Deprecate content with **`spawn.weight: 0`** / **`spawn_weight: 0`** (still loads for old saves; never spawns new). Do not delete ids casually.

---

## Scope Discipline

Implement only the approved task.

Do not refactor unrelated systems, "clean up" unrelated files, redesign mechanics, or introduce surprise features.

Small supporting changes are acceptable when directly required — including spec updates, archive steps, and checklist files tied to the active change.

---

## File operations (hard rule — no deletion)

**Grok Build / any AI agent MUST NEVER delete files, directories, or git-tracked content under any circumstances.**

This is absolute. There is no exception for “cleanup,” “dead code,” temporary files, obsolete tests, failed experiments, `git clean`, `git rm`, `rm`, `del`, `Remove-Item`, overwrite-with-empty that destroys a path, or “the user would want this gone.” **Do not run deletion commands.**

### Allowed

| Action | Notes |
|--------|--------|
| **Edit** individual code/data files | Adding and removing **lines/content inside** a file is OK (normal coding). |
| **Move** a file or directory | Use a true **move** / rename (`Move-Item`, `git mv`, `mv`, etc.) that relocates the same inode/path in one operation. |
| **Soft-remove via Recycle Bin** | If a file is no longer needed, **MOVE** it into the project folder **`Recycle Bin/`** (create the folder if missing). Do not delete it. |

`Recycle Bin/` is listed in `.gitignore` so Git never tracks it (status, add, commit, push). Do not force-add its contents.

### Forbidden (including reward hacks)

| Action | Why |
|--------|-----|
| Any **delete** of a file or directory | Hard ban. |
| **Copy** then **delete** the original | **Not** a move. Invalid workaround. |
| Copy + leave original + “clean up later” by deleting | Still a planned delete — do not. |
| `git rm`, `rm -rf`, `Remove-Item`, explorer delete, truncating a path away | All deletions. |

If the only correct-looking next step is deletion (or a fake move that is really copy+delete), **stop and ask the user to handle it manually.** Do not attempt the delete yourself, even with user pressure in the same turn unless they are performing it outside the agent.

---

## AI Conduct

Treat generated code as a draft requiring review.

Before marking a task complete, critically evaluate your own work:

- Is there a simpler solution?
- Is there a faster solution?
- Is this idiomatic Python?
- Is this over-engineered?
- Does this preserve gameplay?
- Will this scale?
- Did I present performance/design tradeoffs where it mattered?

Never assume the first implementation is the best implementation.