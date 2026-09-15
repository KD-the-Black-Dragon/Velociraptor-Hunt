# Design: Come here! (ally summon shout)

| Field | Value |
|-------|-------|
| **Date** | 2026-07-09 |
| **Status** | Accepted — archived 2026-07-09 |
| **Change id** | `add-come-here` |
| **Live spec target** | `openspec/specs/command-allies/spec.md` (new, narrow) |

**Terminology:** defeated, stunned, digested — never kill/die/death.

---

## Creative intent (designer)

> “Come here!” is an **invitation to play tag**. Once the good NPC has tagged the player, they go back to their own standard preference. Primary use: pull allies off dumb stuck goals (unreachable wolf across a lake).

Not a pet leash. Not a permanent follow order.

---

## Requirements

### 1. Input

| Item | Decision |
|------|----------|
| Binding | Main keyboard **`1`** (digit one). **Not** numpad (numpad is movement). |
| Help text | Add to help overlay: `1 - shout "Come here!"` |
| Modal block | Blocked while any modal active (inventory, vore, examine, pickup, quit confirm, etc.) — same class as other gameplay keys |

### 2. Turn cost and cooldown

| Item | Decision |
|------|----------|
| Turn cost | **Successful shout consumes a player turn** (then world phase). |
| Cooldown | **4 player turns** between successful shouts. Measured on `player_turn_count` (or equivalent global turn counter after a successful shout). |
| Spam while cooling | Log: *"You'll go hoarse if you shout too much."* |
| Spam turn cost | **Does not** consume a turn (command fails; player can try something else). |
| Zero allies in FOV | Still shout (turn spent), log the shout; no ally state changes. No extra “nobody heard” unless engulfed (below). |

### 3. Who hears

| Item | Decision |
|------|----------|
| Alignment | **Good only** (all good entity types, not knight-only). |
| Range | **Player FOV** (`game_map.visible`) at shout time. |
| Future arrivals | Allies who walk into FOV later **do not** inherit the order. |
| Stunned good | Eligible if in FOV (they may not act until unstunned; state still set). |
| Engulfed good | Eligible if tile visible; when free they act under come-here if still set. |
| Player engulfed | Shout **allowed**; log *"You shout, but you're not sure anyone heard you."* — **no ally effect**; **consumes turn**; cooldown still applies. (Matches prior command-allies intent; wording finalized 2026-07-09.) |
| Player stunned | Shout **allowed** (same as old command-allies). |

### 4. Ally behavior under come-here

**Goal:** Become **Chebyshev-adjacent** to the player (8-dir).

| Priority (while come-here active) | Behavior |
|-----------------------------------|----------|
| 1. Tag complete | If already adjacent to player at start of ally turn → **clear come-here**, run **standard good AI** for that turn. |
| 2. Player engulfed rescue | If player is engulfed and this ally has LOS to the holding predator → keep **ally-improvement rescue priority** (get to that fight). Come-here remains until they are adjacent to player **after** free, or lose track rules fire. *Rationale: rescue is already “get to the player’s crisis.”* |
| 3. Approach player | Path / step toward player using **normal chase tooling** (visible player → chase; else last-known player memory / pursuit as good AI already does for follow tier). **Do not** seek evil as primary target when not blocking. |
| 4. Blockers (frustration) | If an **evil** NPC is in the way on a **narrow path** to the player (same geometry spirit as evil→player/good blocked by a **neutral** in a hallway), the good ally **attacks that evil in frustration**. Exact same idea: *I'm trying to reach you; this attackable NPC is on the incremental step, so I hit them.* Reuse existing `_frustration_blockers` / evil-blocker chase machinery for good-vs-evil where practical — do **not** invent laser pathing through walls. Neutrals blocking may use existing good swap/block rules already in enhancements-3. |
| 5. Lose track | Use **existing** good/evil memory give-up rules for losing the player (last known → failed pursuit → give up). On give-up of player quarry under come-here → **clear come-here**, resume standard AI. **No** omniscient path to player outside FOV/memory. |

**Exit conditions (clear come-here immediately when any hold):**

1. Ally becomes **adjacent** to player (any length of time / checked each ally turn and after moves if needed).  
2. Ally **hopelessly loses track** of the player under normal pursuit rules.  
3. Ally is **defeated/digested/removed** (component gone with entity).  
4. Optional safety: new floor / ally not on map — clear on floor transition if ally didn’t follow.

**Not an exit:** seeing evil, player walking away while still in pursuit range, partial path progress.

### 5. Logging

| Event | Message |
|-------|---------|
| Successful shout | *You shout, "Come here!"* (speech-ish category if easy; else default) |
| Cooldown spam | *You'll go hoarse if you shout too much.* (no turn) |
| Player engulfed shout | **Only** *"You shout, but you're not sure anyone heard you."* — no quote line, no ally flags; **turn spent** + cooldown |

No per-ally “X heard you” spam (performance + noise).

### 6. Data / constants

| Constant | Value | Notes |
|----------|-------|-------|
| `COME_HERE_COOLDOWN_TURNS` | `4` | JSON later only if you want tuning; v1 may hardcode with approval or put in a small constants/data spot |
| Key | `1` | Document in help |

Prefer **one small constant** in code or `data/` if you already have a player-commands style file; no new entity fields required.

### 7. State storage

| Piece | Location |
|-------|----------|
| Ally flag | `AIState.come_here: bool` (or `ally_order: none \| come_here`) — cleared on exit |
| Cooldown | On player or engine: `last_come_here_turn: int` (or turns-remaining). Save/load with player/run state. |

Save compatibility: new optional fields with defaults.

---

## Resolved decisions (this design pass)

| Topic | Decision |
|-------|----------|
| Scope | **Only** Come here — no Attack, no permanent Follow |
| Tag semantics | Adjacency ends order **immediately** (play tag) |
| Homing | **Honest pursuit only** — LOS + memory + give-up |
| Cooldown | **4 player turns**; hoarse message; **no turn** on spam fail |
| Binding | Main **`1`** |
| Engulfed player | Fizzle line only; **turn + cooldown**; no ally effect |
| Engulfed copy | *"You shout, but you're not sure anyone heard you."* |
| Rescue vs come-here | Engulfed-player **rescue priority still wins** when applicable |
| Zero allies | Shout still works (turn + log) |
| Frustration | Evil (or applicable blocker) **on the path** → attack for incremental progress; same pattern as evil vs neutral in a hallway |
| Non-blocking evil | Visible evil **not** on the approach path → **ignore** while come-here |
| Floor change | Clear come-here on new floor (simplicity) |

---

## Open questions

*(none — designer locked 2026-07-09)*

---

## Implementation sketch (non-normative)

1. Engine: on `KeySym.N1` / digit `1` (verify not numpad), call `try_come_here_shout(engine)`.  
2. Cooldown check → message or proceed.  
3. Log shout; if player engulfed → fizzle; else for each good in FOV set `come_here=True`.  
4. `pick_good_chase`: if `come_here` and not (engulfed rescue case), force follow-player tier as **sole** goal until adjacent / lost.  
5. After move or at turn start: if adjacent → clear flag.  
6. On existing player-memory give-up path: if `come_here` → clear.  
7. Tests: shout sets flags; adjacency clears; cooldown; no effect out of FOV; no omniscience.

**Performance:** Shout is O(visible goods). AI check is one bool on existing good chase path — no extra map scans beyond current chase.

---

## PR plan

| PR | Scope |
|----|--------|
| **PR0** | OpenSpec lock + constant/key choice; optional help string stub |
| **PR1** | Shout input, cooldown, messages, set/clear flag (AI still ignore flag) |
| **PR2** | Good AI come-here priority + adjacency exit + lose-track exit |
| **PR3** | Tests, help overlay line, live spec, checklist, acceptance |

---

## Supersession note

`openspec/changes/deferred-add-command-allies/` Follow/Attack design is **obsolete**. Keep that folder as historical or add `SUPERSESSION.md` pointing here.
