# Design: Ranged NPC overhaul

## Resolved decisions

| Topic | Decision |
|-------|----------|
| Ally damage −50% | **Data only** in `entities.json` for stock good shooters; ceil on odds. No code multiplier. |
| Who has shots | All NPCs with **RangeN** or **SmiteN** (good + evil, including dragon and modded). Not the player. |
| Max shots source | Per difficulty: `good_ranged_shots` / `evil_ranged_shots` integers in `depth_scaling.json`. |
| Stock values | Easier / Normal / Hard: **good 2, evil 2**. Nightmare: **good 2, evil 3**. |
| Omit defaults | Missing knobs → **2** / **2**. Validate integers **≥ 1** (0 would disable all NPC ranged permanently — reject at load). |
| Shot spend | Path or Smite attempt spends **1** (hit or miss). Cannot attempt at 0. |
| RangedVoreN | Does **not** spend a shot. |
| Reload | Full turn; **+1** shot up to max; **silent** (no message log). |
| Priority at 0 shots | Prefer reload; only **melee** and **vore** outrank. |
| Priority at 1 shot | Reload only if **idle** (no visible target and not actively chasing). Never reload to max while engaging/chasing. |
| Good ally top-up | Good RangeN/SmiteN prefer reload up to max whenever **no enemy in sight** (stricter than evil idle rule). |
| Vore-commit vs shoot | On commit: **no Path/Smite that turn**; attempt vore or step toward target. |
| NoChase | Unchanged meaning: no pursuit after quarry leaves LOS. Hunger-close applies while quarry is **visible**. |
| Fairness extras | Rejected: min engagement distance redesign, post-reload accuracy, shots UI, dragon special-case. Accepted: good ally top-up (above). |
| AI philosophy | **DCSS centaur-like**: strong at range, a bit inefficient, weak/harmless-feeling once player is adjacent (existing “no shoot at distance 1” stays). Do not add clever flee-from-melee for shooters in this change. |
| Run snapshot | Difficulty already snapshotted at New Game; max shots come from that profile for the run. |
| Save | Persist current shots (and max if needed for clamp); missing → fill to max on load. |

---

## 1. Ally ranged damage (JSON)

Stock good shooters today → after ceil-half:

| Entity | Ability | Before | After |
|--------|---------|--------|-------|
| `ram_crossbow` | Range5 | 7–10 | **4–5** |
| `sheep_cleric` | Smite5 | 9–12 | **5–6** |

Formula per field: `ceil(n / 2)` → `(n + 1) // 2` in integers.

Evil shooters unchanged by this pass. Melee fields unchanged.

---

## 2. Difficulty knobs

Add to each profile in `data/depth_scaling.json` (snake_case, matching `cv_daze_*`):

```json
"good_ranged_shots": 2,
"evil_ranged_shots": 2
```

Nightmare: `"evil_ranged_shots": 3`.

Loader / `DifficultyProfile`:

- Parse optional ints; default **2** / **2**
- Require **≥ 1** or load error
- Document in `SCHEMA.md` and `balance` spec

Resolution at spawn (and when attaching Abilities that include RangeN/SmiteN):

```text
max_shots = profile.good_ranged_shots if alignment == GOOD else profile.evil_ranged_shots
# Neutral with RangeN/SmiteN (if any): treat as evil knob OR skip shots — stock has none.
# Decision: neutrals use evil_ranged_shots if they ever get RangeN/SmiteN (rare); document.
```

**Neutral policy:** if a RangeN/SmiteN neutral exists, use `evil_ranged_shots` (hostile-ish pressure). Stock has none.

---

## 3. Shots component / state

**Recommended shape** (implementer may adjust naming):

```text
RangedMagazine(current: int, maximum: int)
```

- Attach only when entity has RangeN or SmiteN at spawn/apply time.
- `current` starts at `maximum`.
- Clamp `current` to `[0, maximum]` after reload / load.
- Depth bake / prefixes do **not** change `maximum`.
- Summons with RangeN/SmiteN get magazine from **current run difficulty** + their alignment at spawn.

**Spend gate:** `try_path_engagement` / `try_smite_engagement` (and any shared “will shoot” helper) require `current >= 1` before attempting; on attempt decrement by 1.

**Reload action:** set `current = min(maximum, current + 1)`; consume the NPC turn (same as a wait/move end_visit).

---

## 4. AI priority (intent sketch)

After existing higher-priority branches (summon, coward flee, **vore modal / NPC vore / ranged vore**):

For RangeN/SmiteN NPCs with a magazine:

```text
1. If vore-eligible (evil) and decision commits → attempt vore OR step toward quarry; do not shoot; do not reload.
2. If adjacent melee/vore opportunity that outranks reload (existing adjacent resolution) → do that.
3. If current == 0 → reload (unless step 1–2 already took the turn).
4. If can Path/Smite with current >= 1 → shoot (spend).
5. If good and no enemy in sight and current < maximum → reload.
6. If current == 1 and idle (no visible target, not chasing) → reload.
7. Else existing reposition / chase / explore.
```

**Idle (evil / general at 1 shot):** no visible hostile/engagement target **and** AI chase state is not actively pursuing (no entity chase target / memory chase as used today). Holding ground while watching a visible quarry is **not** idle.

**Good “no enemy in sight”:** no visible evil (or whatever good Path/Smite already treats as shootable hostiles) in FOV. Following the player with no evils visible → prefer top-up reload.

**NoChase:** unchanged. Fox archer / owl mage still fight visible quarry; hunger-close only while visible; after LOS break they still drop pursuit.

---

## 5. Centaur-like feel (preserve, don’t over-engineer)

Already true / keep:

- Path/Smite refuse distance 1 → entering melee stops the pincushion.
- Evil Path “stand ground” / no fancy kite in this change.
- Weak melee on several shooters (fox, owl) already makes melee contact relatively safe vs their ranged output.

Do **not** in this change: teach shooters to flee melee, kite optimally, or telegraph magazines.

---

## 6. Save compatibility

| Risk | Mitigation |
|------|------------|
| New magazine state | Encode `current` (+ `maximum` if not re-derivable). Missing on load → `current = maximum` from run difficulty + alignment + abilities. |
| New depth_scaling keys | Optional with defaults 2/2. |
| Ally damage JSON change | Old saves keep instance Fighter stats already baked; only **new** spawns / new games get halved ally damage. Acceptable (same as other balance JSON edits). |

---

## 7. Performance

O(1) magazine checks on existing ranged engagement paths. Reload is one branch in the visit pipeline — no extra map scans beyond “visible enemies” already computed for chase/targeting. Prefer reuse of existing visible-hostile helpers.

---

## 8. Files (expected)

- `data/entities.json` — ally ranged_* 
- `data/depth_scaling.json` — knobs
- `data/SCHEMA.md`
- `src/data/depth_scaling_config.py` / `depth_scaling_loader.py`
- `src/components.py` (or adjacent) — magazine
- `src/spawn.py` — init magazine
- `src/systems/abilities.py` — spend gate on Path/Smite
- `src/systems/ai/visit.py` (and helpers) — reload + hunger override ordering
- `src/save/codec.py` — persist
- `src/messages.py` — only if a future log line is added (not this change)
- Live specs: `npc-abilities`, `balance`; possibly `ranged-targeting`
- Tests: loader defaults; spend/reload; AI priority fixtures; good top-up; evil vore-commit blocks shoot; save round-trip

---

## Open implementation notes (non-blocking)

- Exact component name and whether `maximum` is stored vs re-read from difficulty each time — prefer **store maximum at spawn** so mid-run difficulty file edits / weird loads don’t reshape living NPCs.
- Whether reload is a named helper `try_ranged_reload(...)` returning bool for visit pipeline clarity — yes, preferred.
