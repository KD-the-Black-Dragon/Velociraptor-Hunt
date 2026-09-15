# Tasks: Better NPC Exploration

**Status:** Accepted — archived 2026-07-05.

## PR1 — Reachable explore goals (all alignments)

- [x] Add per-entity BFS reachable-tile helper (mobility + closed doors block; `hands` stub hook)
- [x] Pick `explore_goal` via **weighted random** toward farther reachable tiles
- [x] Re-pick when current goal not in reachable set (e.g. door closed)
- [x] Wire into good/evil/neutral explore goal paths
- [x] Unit tests: closed door partitions goal pool; weighted-far bias; aquatic mobility
- [x] Run targeted pytest for PR1
- [x] Deliver manual checklist (`testing-checklist-pr1.md`)

## PR2 — Explore frustration

- [x] Add `explore_frustration` / `explore_frustration_limit` on `AIState`
- [x] Failed step: no move or no BFS path-distance progress; success resets counter
- [x] At limit: clear goal; **force farthest-endpoint pick once**; then resume weighted-random far picks
- [x] Unit + integration tests
- [x] Run targeted pytest for PR2
- [x] Deliver manual checklist (`testing-checklist-pr2.md`)

## PR3 — BFS explore steps + sidestep

- [x] Explore-only step: BFS one-step toward `explore_goal` (shortest route on terrain)
- [x] When no progress step exists: **sidestep** away from goal, avoiding recent tiles
- [x] Oscillation detect (4-step ABAB position/distance) → re-pick goal away from blocker
- [x] Evil NPCs cannot swap with other evil NPCs
- [x] Zero legal moves: stand still (failed step for frustration)
- [x] Chase/follow/flee/memory remain greedy — regression tests
- [x] Run targeted pytest for PR3
- [x] Deliver manual checklist (`testing-checklist-pr3.md`)

## PR4 — Retire PR10 shim + neutral player avoidance

- [x] Remove `recent_positions` / wait-on-recent / neutral-only explore helpers
- [x] Neutral explore uses PR1–PR3 shared path
- [x] Block **player tile** for neutral explore goals and steps (adjacent tiles allowed)
- [x] Replace `tests/test_neutral_explore_antistuck.py` with new explore coverage
- [x] Run targeted pytest for PR4
- [x] Deliver manual checklist (`testing-checklist-pr4.md`)

## Acceptance (after PR4 sign-off)

- [x] Update `openspec/specs/enhancements-3/spec.md` explore rules
- [x] Write `acceptance-report.md` and `testing-checklists.md`
- [x] Run full pytest suite
- [x] Archive to `openspec/changes/archive/2026-07-05-better-npc-exploration/`
- [x] Update `openspec/WORKFLOW.md` active change pointer