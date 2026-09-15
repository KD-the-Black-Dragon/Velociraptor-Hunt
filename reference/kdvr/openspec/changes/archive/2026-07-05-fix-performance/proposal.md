# Proposal: Fix Performance

**Status:** Accepted — archived 2026-07-05 (Tier A only).

**Source:** `openspec/changes/todo/spec.md` — Performance issues (core lag fixed; distant throttle deferred).

## Delivered

| Phase | Outcome |
|-------|---------|
| Investigation | `investigation-report.md`, `tools/profile_turn.py` |
| Tier A (PR2–PR3) | BFS caching + registry cache; ~461 ms → ~77 ms/default turn |
| Tier B | **Deferred** → `deferred-fix-performance-distant-throttle/` |

## Live spec

`openspec/specs/performance/spec.md`

## Archive

`openspec/changes/archive/2026-07-05-fix-performance/`