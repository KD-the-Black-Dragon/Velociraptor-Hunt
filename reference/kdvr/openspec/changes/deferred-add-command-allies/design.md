# Design: Command Allies (deferred)

**Change id:** `add-command-allies` (future)  
**Status:** Deferred — preserved for when user resumes this work  
**Parent context:** Originally part of Ally Improvement; split 2026-07-02

**Terminology:** defeated, stunned, digested — never kill/die/death.

---

## Overview

Player shouts **Follow me** and **Attack** to good allies currently in FOV. Follow mode makes adjacency to the player top priority; Attack restores default good AI (evil first, follow player second).

Related ally behavior (names, engulfed rescue priority, gratitude) lives in **`add-ally-improvement`**, not here.

---

## Requirements (original intent)

1. Ability to give orders to nearby **Good** entities (all good alignment types, not knights only).
2. **Key 1** (main keyboard `1`, not numpad southwest): player shouts *"Follow me!"* — nearby good allies prioritize staying near the player. Top priority: become **adjacent** to the player. If an evil entity blocks the path, attack that evil (similar to evil frustration when a neutral blocks the path to a primary target). If already adjacent, seek evil to attack. Must **never willingly** increase distance from the player.
3. **Key 2** (main keyboard `2`, not numpad): player shouts *"Attack!"* — revert nearby good allies to current default AI (attack evil first, follow player second).
4. ~~If player engulfed, all good entities prioritize saving the player~~ → **shipped in `add-ally-improvement`** (global rescue priority when predator visible).

---

## Resolved decisions (2026-07-02)

| Topic | Decision |
|-------|----------|
| **Range** | Player **FOV only** — orders affect good entities in FOV at shout time |
| **Scope** | All **good** alignment entities (not neutral rabbit, not evil) |
| **Follow persistence** | Until **Attack** command, or ally **loses track** of player: chase last known position → if still no sight, **stand still a few turns** → if still no sight, **give up** and resume default on-spawn AI (wander, seek evil) |
| **No cheating** | Allies must not home in on hidden player; use normal pursuit / last-known rules only |
| **Shout scope** | Only allies **in range at shout time** receive the order (not future arrivals) |
| **Turn cost** | Shout **consumes a player turn** |
| **While stunned** | Shout **allowed** while player stunned |
| **While engulfed** | Shout allowed; log *"You shout, but it's unlikely anyone heard you."* — **no ally effect** |
| **Modals** | Shout **blocked** while any modal active (inventory, vore, pickup, examine, etc.) |
| **Log — Follow** | *You shout, "Follow me!"* |
| **Log — Attack** | *You shout, "Attack!"* |
| **Zero allies** | **No** confirmation when no good allies in FOV |

---

## Open questions (unresolved — decide before implementation)

| # | Question | Notes |
|---|----------|-------|
| Q1 | **Follow vs visible evil (non-blocker)** | Under follow orders, if evil is visible but **not** blocking path to player: still prioritize reaching player first, or attack any visible evil? |
| Q2 | **Evil blocker geometry** | Use same `_frustration_blockers` geometry (evil between ally and player) or any visible evil while pathing? |
| Q3 | **"Never willingly more distant"** | When no step reduces distance (blocked corridor): wait only, or allow lateral/explore steps that preserve distance? |
| Q4 | **Wait duration** | How many turns standing still before giving up on lost player? (Design session suggested "a few" — pick constant.) |
| Q5 | **Orders across descent** | Do follow/attack orders persist when good allies follow player downstairs? |
| Q6 | **State storage** | New `AIState` fields (`ally_order: follow \| attack \| default`, `lost_player_wait_turns`) vs dedicated component? |
| Q7 | **Follow while player engulfed** | User moved global engulfed rescue to ally-improvement; under follow order, does rescue priority still override follow adjacency? (Likely yes — align with add-ally-improvement.) |

---

## Technical notes (non-normative)

- Input: `KeySym` for `1` / `2` in `GameEngine._handle_gameplay_event()` — distinguish from numpad movement keys
- Hook after player action in `_consume_player_turn()` or as immediate action before world phase
- Default good AI baseline: `pick_good_chase()` in `src/systems/ai.py` (`enhancements-3` spec)
- Likely new spec: `openspec/specs/command-allies/spec.md`

---

## PR plan (draft — not started)

| PR | Scope |
|----|--------|
| PR0 | `AIState` order fields, engine key bindings, shout messages, no AI behavior yet |
| PR1 | Follow mode chase / blocker frustration / adjacency rules |
| PR2 | Attack revert + loss-of-track give-up loop |
| PR3 | Spec + tests + manual checklists |

Adjust when change is activated.

---

## References

- Default good AI: `openspec/specs/enhancements-3/spec.md` — Good AI Priority
- Evil frustration pattern: `src/systems/ai.py` — `_frustration_blockers`, `pick_evil_target`
- Ally improvement (shipped separately): `openspec/changes/add-ally-improvement/`