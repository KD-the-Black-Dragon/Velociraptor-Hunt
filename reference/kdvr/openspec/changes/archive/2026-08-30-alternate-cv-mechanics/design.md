# Design: Alternate CV Mechanics + NPC Dazed

**Change id:** `alternate-cv-mechanics`

---

## Resolved decisions

| Topic | Decision |
|-------|----------|
| Options label | **Alternate CV Mechanics** with **No** / **Yes** (default No) |
| Missing/null setting | Treat as **No** |
| Duration data | `depth_scaling.json` per difficulty: `cv_daze_min_turns`, `cv_daze_max_turns` (all difficulties **5**/**5**) |
| Missing knobs on a profile | Default both to **5** (mod-friendly) |
| RNG | Inclusive integer roll `[min, max]` |
| Stacking daze | New roll **adds** to remaining `Dazed.remaining`; no second “appears dazed” if already dazed |
| Run binding | Snapshot `alternate_cv_mechanics` at **New Game** on `GameEngine` (like `vore_content_prefs`); persist in autosave; Options mid-run does not change current run |
| Scope | Player CV struggle 0 damage; daze on player CV escape; daze on CV NPC digest-complete only |
| Same-phase digest skip | Keep existing `skip_turn_entities` after NPC digest; daze covers subsequent turns |
| Off path | Identical to today’s CV / other types |

---

## Dazed status (NPCs only)

### Representation

- Component **`Dazed(remaining: int)`** — do **not** reuse `Stunned`.
- Never apply to entities with `Player` tag.
- Save: encode/decode component; absent on old saves is fine.

### Apply

```text
apply_daze(entity, turns, game_map, message_log):
  if Player in entity.tags or turns <= 0: return
  existing = entity.components.get(Dazed)
  if existing is None:
    entity.components[Dazed] = Dazed(remaining=turns)
    if visible: log "{name} appears dazed."
  else:
    existing.remaining += turns   # stack; no second "appears" line
```

```text
roll_cv_daze_turns(profile, rng) -> int
  return rng.randint(min_turns, max_turns)  # inclusive; load validates min<=max, both >= 0
```

### AI

In monster visit pipeline (near `Stunned` skip), before action selection:

```text
if Dazed on monster:
  remaining -= 1
  if remaining <= 0:
    pop Dazed
    if visible: log "{name} is no longer dazed."
  continue  # no AI action this turn
```

The turn that hits 0 is still skipped; the **next** world-phase opportunity may act.

Daze is applied only after `Predator` is cleared (escape / digest-complete). No intentional daze-while-holding.

### Render

`render_entities`: if `Dazed`, set tile `bg` to blue (e..g. `DAZED_BG = (20, 50, 140)`). While `Predator` is present, keep existing dark-red holding BG.

### Messages

Via `src/messages.py`:

- `npc_appears_dazed(name)` → `"{character} appears dazed."`
- `npc_no_longer_dazed(name)` → `"{character} is no longer dazed."`

FOV-gated with `entity_visible_to_player`.

---

## Alternate CV mechanics

### Settings + Options

| Layer | Behavior |
|-------|----------|
| `SettingsStore.alternate_cv_mechanics: bool = False` | `bool(data.get("alternate_cv_mechanics", False))`; persist; setter |
| Options row | `Alternate CV Mechanics:  [No] ► Yes` (Left/Right/Enter); place after 4K row; bump indices |
| `GameEngine.alternate_cv_mechanics: bool` | From settings at New Game / arena; restore from save (missing → False) |

### Data (`depth_scaling.json`)

Each difficulty object:

```json
"cv_daze_min_turns": 5,
"cv_daze_max_turns": 5
```

Expose on `DifficultyProfile`. Use run’s difficulty profile + `engine.rng` to roll.

### Struggle (`try_struggle`)

When run flag Yes and holding predator’s `narrative_type == "CV"`: apply **0** struggle damage (still log struggle). Escape roll unchanged; fail still increments `failed_struggles`. Pass `alternate_cv_mechanics` explicitly from `engine_input`.

### Player CV escape → daze

On successful escape release: if flag Yes and pre-clear `narrative_type == "CV"` → `apply_daze(predator, roll(...))`. Do **not** daze when predator is removed as defeated.

### NPC CV digest-complete → daze

In `complete_npc_digestion`, after `pop(Predator)`: if flag Yes and type was `CV` → `apply_daze`. Keep same-phase `skip_turn_entities`.

### Off / non-CV

No new branches; behavior identical to today.

---

## Save compatibility

| Field | Mitigation |
|-------|------------|
| Settings key | Default False |
| Run snapshot flag | Default False if missing |
| `Dazed` | Soft-absent |
| depth_scaling knobs | Default 5/5 if omitted |

---

## PR plan

| PR | Scope |
|----|--------|
| **PR1** | Dazed component; apply/tick; AI skip; blue BG; messages; save; tests |
| **PR2** | depth_scaling fields + loader; Settings + Options; engine/run snapshot |
| **PR3** | Wire Alternate CV struggle / escape daze / NPC CV digest daze; tests |
| **PR4** | Live specs + SCHEMA/README; acceptance; archive |

---

## Testing (pinned fixtures)

- Off → struggle still damages (including CV).
- On + CV → 0 struggle damage; escape chance unchanged.
- On + OV/AV → normal struggle damage; **no** escape daze.
- On + player escapes **CV** → daze; stacking adds.
- On + NPC **CV** digest-complete → daze; OV/AV digest → no daze.
- AI countdown / expire; FOV messages; save round-trip.
