# Proposal: Engineering maintainability pass

**Status:** Design locked (2026-07-09) — coding after PR1 authorization  
**Change id:** `engineering-maintainability`  
**Source:** Five priority-engineering items from `openspec/changes/todo/spec.md` (2026-07-09 backlog)

## Why

Content and systems keep landing. The two largest code files (`systems/ai.py` ~3.5k LOC, `engine.py` ~1.7k LOC) and cross-cutting hygiene gaps raise merge risk, review cost, and test friction. This pass is **player-invisible**: no new gameplay, no balance retunes, no content packs.

Prior `engineering-cleanup` (2026-07-09) shipped save soft-drop and flaky-test hardening. This change is the **structure + deeper maintainability** follow-up.

## What (the five items)

| # | Item | Outcome |
|---|------|---------|
| 1 | **Test helpers for spawn-at-depth / difficulty** | Shared fixtures for species @ depth under a difficulty |
| 2 | **Message / string catalog discipline** | Policy + **all remaining** player-facing log literals → `messages.py` |
| 3 | **Save codec / snapshot schema hardening** | Field inventory, additive defaults, round-trip tests; no format bump |
| 4 | **Split GameEngine / thin app shell** | Extract floor / turn / input in **separate PRs**, then a **deeper cleanup** PR |
| 5 | **Modularize AI by intent** | Extract explore → chase/targeting → movement/visit in **separate PRs**, then **deeper cleanup** |

## How we reduce blast radius (designer)

- **Many small PRs** (12 total including acceptance), not one mega-refactor.
- **Deeper cleanup** (names, public API, dead code) only in dedicated engine/AI cleanup PRs — not mixed into a huge move.
- **Mandatory manual smoke after every PR** before the next starts: launch, new game, game-over path, plus anything the PR likely touched.
- Prefer **extra PR splits** mid-stream if a slice is still too large.

## Explicitly out of scope

| Idea | Why |
|------|-----|
| Externalize vore narratives from `entities.json` | Designer — keep unified for modding |
| Turn-pipeline performance budget / deep-floor profile | Not requested |
| Gameplay features / balance iteration | Separate backlog |
| Intentional AI/combat/spawn behavior changes | Preserve existing behavior |

## Success

- All five backlog items complete via the sliced PR plan.
- Full suite green at final acceptance.
- Designer never had to accept a “green suite / black screen” PR without a smoke gate.
- Todo marks the five items completed when archived.

## Risk note

Engine and AI work remains the highest risk. Mitigation is **slice size + smoke frequency + no gameplay edits in move PRs**, not speed.
