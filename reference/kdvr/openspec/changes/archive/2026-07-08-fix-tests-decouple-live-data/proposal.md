# Proposal: Decouple tests from live `data/` balance

**Status:** Active  
**Source:** Full-suite failures after balance edits to `data/*.json` (2026-07-08).

## Why

Automated tests asserted frozen values from live `data/` (entity stats, spawn density, macguffin depths, narrative phrases). The designer tunes those files freely; tests must not lock balance.

Project rule (already in `conftest.py` / AGENTS.md): pin fixtures — never rely on gameplay balance numbers from `data/`.

## Hybrid plan

| Class | Action |
|-------|--------|
| **A** Stock-snapshot tests | Delete, or reduce to schema smoke (loads, no golden numbers/text) |
| **B** Mechanics that load stock for convenience | Rewrite with inline JSON / test helpers / `spawn_test_npc` |
| **C** Real API/contract tests | Fix for current code (not balance) |

## Out of scope

- Changing live `data/` content
- Gameplay balance retunes
- Full test rewrite of every non-failing data load

## Success

- Full suite failures driven by live balance snapshots eliminated
- Remaining failures are true code bugs or known unrelated flake
