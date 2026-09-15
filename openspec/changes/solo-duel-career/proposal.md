# Proposal: Solo duel career (Style 1) + freeze team campaign (Style 2)

## Problem

The product currently centers on **team management** and **multi-opponent** match cards. The designer wants to **focus on 1-on-1 duels** for a simpler career loop (equipment / PC upgrades only), **without deleting** the existing team / multi-enemy work.

## Solution

Introduce two **campaign styles**:

| Style | Name (working) | Status |
|-------|----------------|--------|
| **1** | **Solo Duels** | **Active focus** — career, upgrades, 1v1 only |
| **2** | **Company** (current) | **On ice** — preserved, not the default product path |

Solo Duels reuses hub economy, sand-pit combat, Battle Sport, green/red, instant-action patterns, but:

- No hire / roster / Talk / allies in matches  
- Match offers only **exactly one enemy** (one entity, count 1)  
- Instant Action card list filtered the same way when used for practice  

Company mode remains in code/data; entry is **hidden or gated** so it is not the normal New Game path until reopened.

## Scope

### In (this change)

- Campaign style field on career (save-compatible default)
- Solo Duels as default New Game path
- Hub UI: hide team actions in Solo; skip starter ally picks
- Match card offers: solo-eligible cards only
- Spawn: enforce single opponent
- Instant Action: optional filter to solo cards (or separate pool)
- Docs: DESIGN_CANON + live specs + “Company freeze” note
- Tests for solo path; existing team tests remain but may require style=company fixture

### Out

- Deleting roster / Talk / multi-enemy systems  
- Rewriting combat for a different engine  
- Full Company-mode feature work  
- New deep content pass (can add 1v1 cards as needed)

## Success

New Game → Solo Duels career → only 1v1 matches; team hub options gone; multi-enemy cards never offered. Company code still loads and can be re-enabled later without archaeology.
