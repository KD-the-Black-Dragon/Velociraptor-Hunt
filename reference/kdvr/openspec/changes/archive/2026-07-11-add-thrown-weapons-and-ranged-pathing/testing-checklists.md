# add-thrown-weapons-and-ranged-pathing — Combined manual testing

Run `python -m src.main` from the project root.

## Automated gate (acceptance)

```bash
python -m pytest tests/ -v -n 4
```

Per `AGENTS.md` full-suite workflow (failed-twice serial reruns as needed).

---

## PR1 — SmiteN rename

- [ ] Wand evoke (`v`) uses **smite** log lines (*"You smite the …"*)
- [ ] Wand miss: *"You smite … but miss."*
- [ ] Melee bump still uses hit/miss (not smite)
- [ ] Stock wolf has no ranged ability — baseline melee chase

## PR2 — Path core (engine)

- [ ] No new player keys yet; wand/melee unchanged

## PR3 — NPC RangeN (Path) AI

| Species | Ability | Type | Log |
|---------|---------|------|-----|
| **wolf** | `Range6` | Path | *shoots* |
| **slime** | `Smite3` | Smite | *smites* |

- [ ] Wolf at distance 2–6 with clear beam **shoots**
- [ ] Slime at distance 3 **smites**
- [ ] Distance 1 → melee for both
- [ ] Rear wolf blocked when front wolf on beam
- [ ] Wand smites through good ally (Smite ignores intermediates)
- [ ] Bat/cave rat Erratic — no ranged shots

## PR4 — Projectile animation

- [ ] Wolf Path shot: **cyan `*`** trail along full beam (in FOV)
- [ ] Player throw anim completes **before** NPCs move
- [ ] Slime smite: **magenta `*`** flash on source then target (no travel)
- [ ] Off-screen shot: no projectile drawn

## PR5 — Throwables data + starter

- [ ] New game: `a` dagger (wielded), `b` robes (worn), `c` **5 rocks**
- [ ] Rocks spawn depth 1–3; light brown `.` visible on floor
- [ ] Pickup stacks rocks into slot `c`
- [ ] Save/load preserves rock stack count

## PR6 — Player throw (`f` / `F`)

- [ ] `f` opens target cursor (no pick modal); auto best `max_damage`
- [ ] `F` lists throwables; manual pick works
- [ ] Target prompt: *"Throw {item} at which target?"*
- [ ] Cyan `X` cursor; cycle valid evil targets near→far (numpad6 forward, numpad4 backward)
- [ ] Confirm on evil + clear path: stack decrements, turn consumed
- [ ] Miss: *"Your throw misses the …"*
- [ ] Good/neutral: *"Not the best target."* — no turn
- [ ] Empty tile: *"There's no target there."* — no turn
- [ ] Ally in beam: *"Something is in the way."* — no turn
- [ ] Engulfed: pack keys blocked

## PR7 — Catalog + fox archer + help

- [ ] Deeper floors show rarer throwables (brick, dart, knife, …)
- [ ] Fox archer depth 5+ **shoots** (Path); ally blocks shot
- [ ] Help (`F1` / `?`): `f - throw best throwable`, `F - pick throwable to throw`

## Full regression

- [ ] Main menu, descent, save/load, combat, vore modal
- [ ] Melee, quaff, evoke, rest, examine unchanged
- [ ] FOV log gating for NPC combat messages
- [ ] Performance: no noticeable turn lag with many NPCs

**Pass criteria:** live specs in `openspec/specs/ranged-targeting/`, updated `inventory-items`, `equipment-catalog`, `npc-abilities`; pytest green; manual items above checked.