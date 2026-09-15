# Proposal: Convenience controls

**Status:** Design complete — awaiting PR authorization  
**Change id:** `convenience-controls`  
**Artifacts:** `design.md`, `tasks.md`, `testing-checklist-pr1.md`, `testing-checklist-pr2.md`

## Why

Two high-frequency roguelike conveniences reduce tedium without changing core combat math:

1. **Autoexplore** — clear safe floors after combat without hammering movement keys.
2. **Force-attack** — swing at a tile without stepping forward (invisible prey, erratic predators, deliberate waiting).

Both patterns are well understood in the genre (DCSS and kin). This project already has adjacent building blocks: incremental **rest** sessions, shared **danger interrupts**, and balance-sim **exploration navigation** in `src/sim/navigation.py`.

## What

### 1. Autoexplore (`)

Press **`` ` ``** (backtick / grave) to autoexplore until interrupted or finished.

| Priority | Goal |
|----------|------|
| 1 | Walk onto **known** floor items and floor runes (tile explored, pickup still present). |
| 2 | Walk toward the nearest tile that will reveal **unseen** walkable area (exploration frontier). |
| 3 | Repeat until neither goal is reachable. |

**Interrupts** (same set as long rest, evaluated after each consumed turn):

- Player targeted by combat (melee or ranged, hit or miss).
- Evil NPC enters player FOV.
- Good ally in player LOS sees evil and shouts alarm.

**Natural end:** log *Exploration complete.* when no known pickups remain **and** no frontier tile is reachable (remaining unseen area is walled off or deep water).

**Start blocked** when engulfed (*You're already exploring something's digestive tract.*), stunned, **below 50% HP**, or evil already in player FOV (*There's an enemy in sight!*) — each with its own message, not rest’s strings.

Uses the same incremental animation model as rest (non-blocking main loop, **any-key cancel**, batched silent turns when the screen fingerprint is unchanged). **No max-turn cap** (unlike rest’s 100-turn limit).

### 2. Force-attack (Ctrl + direction)

**Ctrl** + any movement key (arrows, numpad, TYUGHJBNM) attacks the adjacent tile **without moving**.

| Target at tile | Result |
|----------------|--------|
| Hostile fighter (evil NPC) | Same as bump melee |
| Empty, terrain, good/neutral NPC, closed door | Consume turn; *You attack the empty air.* |
| Player engulfed | Same as normal direction (struggle), not force-attack |

## Success criteria

- `` ` `` starts incremental autoexplore with correct priorities and interrupts.
- Autoexplore ends with *Exploration complete.* or a rest-matched interrupt message.
- Any **KeyDown** during autoexplore cancels silently (rest parity).
- Ctrl+direction force-attacks without movement; empty swing wastes a turn with the specified message.
- Help overlay (`F1` / `?`) documents both bindings.
- Live spec: `openspec/specs/convenience-controls/spec.md`.
- Automated tests mirror `tests/test_rest_until_healed.py` coverage style.

## Out of scope

- Auto-fight, auto-pickup of distant items through walls, or auto-descend.
- New interrupt types (HP healed, autoexplore turn cap, new monsters heard off-screen, etc.).
- Arena-specific disabling of these commands.
- Autoexplore while a modal is open (blocked like other action keys).
- Rebinding keys via Options (fixed bindings v1).
- Balance-sim policy changes (may share extracted navigation helpers only).

## Dependencies

| Area | Relation |
|------|----------|
| `enhancements-1` / `src/systems/rest.py` | Interrupt parity, animation pattern |
| `src/sim/navigation.py` | Frontier + BFS helpers (extract to shared module) |
| `inventory-items` | Floor pickup on step |
| `floor-runes` / `macguffins` | Step-on activation chain |
| `command-allies` | Ally alarm interrupt |

## PR plan (summary)

| PR | Scope |
|----|--------|
| PR1 | Shared danger interrupts + navigation extract; autoexplore session, loop, spec, tests |
| PR2 | Force-attack input + combat helper, spec delta, tests |

See `tasks.md` and `design.md` for detail.