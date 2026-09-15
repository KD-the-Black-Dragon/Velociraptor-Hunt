# Design: Engulfed flavor text

**Change id:** `engulfed-flavor-text`

---

## Resolved decisions

| Topic | Decision |
|-------|----------|
| Data shape | Top-level optional `engulfed_flavor`: `{ OV, CV, AV → string[] }` |
| Empty / missing | Omit field / omit key / `[]` → no lines; **no-op** (no empty log line) |
| Cadence | Every **3rd** completed **world phase** of this engulfment (3, 6, 9…) |
| Placeholders | `{predator}` / `{prey}` via existing format helpers + sentence capitalization |
| Stock content | Schema + systems only; no stock entity fills |
| Log color | `MessageCategory.SPEECH` `(255,255,255)` |

---

## Data

### Schema

```json
"engulfed_flavor": {
  "OV": ["..."],
  "CV": ["..."],
  "AV": ["..."]
}
```

Document under optional entity fields in `data/SCHEMA.md`.

### Load

Mirror `offscreen_vore` / `digestion_complete`:

- Add to `_ENTITY_TRAITS`.
- Parse with a variant of `_parse_narrative_type_lines` that **allows empty arrays** (drop empty keys; field becomes `None` if nothing left). Present non-empty string lists → `dict[str, tuple[str, ...]]`.
- Store on `EntityDefinition.engulfed_flavor`.
- Index in `NarrativeIndex` with `engulfed_flavor_lines(entity_id, narrative_type)` / `pick_engulfed_flavor_line(..., rng)`.

Invalid types (non-object field, non-string list entries) → load error as usual for bad mod/core data.

---

## Runtime

### Counter

`Predator.engulfed_flavor_phases: int = 0`

- Set/left at 0 when `Predator` is assigned on engulf.
- Persist in save codec; missing → `0`.
- Cleared with `pop(Predator)`.

Constant: `ENGULFED_FLAVOR_EVERY_N_WORLD_PHASES = 3` (named constant in code; not difficulty-tuned unless requested later).

### Emit

Helper e.g. `maybe_emit_engulfed_flavor(engine)` called at **end of `run_world_turn`**:

```text
if player is None or Engulfed not in player: return
predator = find_predator_holding_prey(...)
if predator is None: return
state = predator.components[Predator]
state.engulfed_flavor_phases += 1
if state.engulfed_flavor_phases % 3 != 0: return
pool = index.engulfed_flavor_lines(species_id, state.narrative_type)
if not pool: return
line = format...(rng.choice(pool), predator, player)
message_log.add(line, category=MessageCategory.SPEECH)
```

World phases skipped (digest modal before world, haste, etc.) do **not** increment.

---

## PR plan

| PR | Scope |
|----|--------|
| **PR1** | Parse + registry + narrative index + SCHEMA + loader tests |
| **PR2** | Predator counter + save + `run_world_turn` emit + unit tests |
| **PR3** | Live vore spec + acceptance / archive |

---

## Testing

Pinned JSON / tmp entities only. Cover omit/empty, type gating, 3/6 cadence, no blank lines, SPEECH category, placeholder format, counter reset on new engulf.
