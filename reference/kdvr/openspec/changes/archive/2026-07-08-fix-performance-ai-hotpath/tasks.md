# Tasks: AI Hot-Path Performance (P + D2/D3/D4)

**Active change.** Implement **one PR at a time**. Do not start coding until user authorizes after design review.

## Selection (locked 2026-07-08)

- [x] User opens change; lag confirmed unacceptable
- [x] Re-profile: `default`, `explore_10`, `explore_25`, `scale_25`, `scale_50`
- [x] User selects: **P1–P4 + D2 + D3 + D4** (not D1, not D5)

## PR1 — Group P (behavior-preserving)

- [x] P1: Explore walkability grid cache; BFS uses mask
- [x] P3: Array-based BFS internals (fewer dict/Position allocs on hot path)
- [x] P2: `_ensure_explore_goal` short-circuit via episode distance map
- [x] P4: Sanitize at most once per monster visit; interval K when memory set
- [x] Targeted tests (explore/chase existing suite + any new P helpers)
- [x] Profile note: before/after PR1 on `default`, `explore_25`, `scale_25`
- [x] `testing-checklist-pr1.md` + manual checklist in chat after PR1

## PR2 — Distant throttle D2+D3+D4

- [x] Constants `DISTANT_AI_RADIUS`, `BUSY_FLOOR_NPC_THRESHOLD` (+ K if not in PR1)
- [x] `ai_turn_salt` on `AIState` / spawn; save default for old saves
- [x] Busy count once per `run_monster_turns`; throttle = busy ∧ distant
- [x] D2: skip full visit on half-turn when throttle
- [x] D3: no `last_known_*` position pursuit when throttle; full explore BFS still; skip sanitize when throttle
- [x] Tests: within-R corner chase; beyond-R memory cutoff when busy; gate off ≤N; cadence
- [x] Update `openspec/specs/performance/spec.md`
- [x] `testing-checklist-pr2.md` + manual checklist in chat after PR2

## PR3 — Acceptance

- [x] Full profile vs proposal targets
- [x] User playtest sign-off
- [x] Adjust regression gates if appropriate (`default` p95 150 ms, `explore_10` p95 100 ms)
- [x] Archive to `openspec/changes/archive/2026-07-08-fix-performance-ai-hotpath/`
- [x] Update `AGENTS.md` pointer + `openspec/changes/todo/spec.md`
