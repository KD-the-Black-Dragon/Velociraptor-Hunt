# Design: add-good-npc-roster

| Field | Value |
|-------|-------|
| **Date** | 2026-07-30 |
| **Status** | Accepted and archived 2026-07-30 |
| **Spec** | Light note in `openspec/specs/npc-data/spec.md` (good roster growth); ally-intro behavior already covered by `ally-improvement` |
| **Implementation** | Data-only: `data/entities.json`, `data/names.json` (+ brief SCHEMA/spec notes if useful) |

---

## Goals (designer intent)

| Goal | Design response |
|------|-----------------|
| Flesh out good NPC roster | **8 new** goods + **retuned knight** (spawn **and combat stats**) |
| Dog Squire bottom; Dog Knight 2nd tier | Squire handles early vermin; knight **strengthened** for next band |
| Equal-length melee bands | Melee goods on **length-3** depth windows (slight edge overlap only where needed); ranged **on top** of that ladder |
| Otter fills mid-late gap | **Otter Warden** between lion Warrior and boar-at-arms (no wide 11–17 bands) |
| Boar-at-arms (no “man”) | `boar_at_arms` / display **boar-at-arms**; names like `Garrick-at-arms` |
| Ranged counterparts | Ram Crossbow + Sheep Cleric; **melee stats == ranged stats** (identical acc/dmg) |
| Top tier | Badger Champion vs **gryphon**; spawn through **1000** |
| 1v1 strength | ~**95%+** win vs band peer (Normal depth-scaled evil); goods may be **quite strong** (swallowed goods cannot struggle free) |
| Outnumbered / OOD | Packs and out-of-depth heavies should threaten or defeat goods |
| Names | **`Sir` only on knights**; others use title schemes below |
| Cyan glyphs | Shared cyan `fg`; unique free glyphs |
| Knight text/intros | **Do not rewrite** examine / introductions / existing Sir name *style*; **do** retune combat + spawn; name pool stays Sir-prefixed |
| JSON-only | No Python changes expected |
| Skip final full regression | Acceptance PR does not run full `pytest tests/` |

---

## Locked roster

### Melee ladder (equal length-3 bands)

| Tier | Rank title | Species | Entity `id` | `display_name` | Glyph | Spawn | Primary peer evil (mid-band) |
|------|------------|---------|-------------|----------------|-------|-------|------------------------------|
| 1 | Squire | Dog | `dog_squire` | dog squire | `q` | **2–4** | bat / rat @3 |
| 2 | Knight | Dog | `knight` | dog knight | `k` | **5–7** | slime @6 (also cleans wolf) |
| 3 | Guard | Ferret | `ferret_guard` | ferret guard | `e` | **8–10** | tarantula @9 |
| 4 | Warrior | Lion | `lion_warrior` | lion warrior | `L` | **11–13** | gnoll @12 (slug in band — see stats) |
| 5 | Warden | Otter | `otter_warden` | otter warden | `o` | **14–16** | roc @15 |
| 6 | -at-arms | Boar | `boar_at_arms` | boar-at-arms | `A` | **17–19** | drake @18 (also wyvern) |
| 7 | Champion | Badger | `badger_champion` | badger champion | `B` | **17–1000** | **gryphon** @18 |

Hand-off is sequential: squire ends as knight begins, etc. Champion **overlaps** boar-at-arms from 17 and continues alone past 19.

### Specialists (parallel tracks — on top of melee ladder)

| Role | Species | Entity `id` | `display_name` | Glyph | Abilities | Spawn (length 3) | Peer |
|------|---------|-------------|----------------|-------|-----------|------------------|------|
| Crossbow (Path) | Ram | `ram_crossbow` | ram crossbow | `c` | `Range5` | **6–8** | fox_archer (combat with **identical** melee/ranged numbers) |
| Cleric (Smite) | Sheep | `sheep_cleric` | sheep cleric | `p` | `Smite5` | **12–14** | owl_mage (identical melee/smite numbers) |

Specialists **must not** use `NoChase`.

### Band chart

```text
Depth:     1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 …
squire:       ████████
knight:                ████████
ferret:                         ████████
lion:                                    ████████
otter:                                            ████████
boar:                                                      ████████
champion:                                                  ████████████████ →1000
ram:                    ████████          (parallel)
sheep:                                    ████████  (parallel)
```

Depth **1**: no goods (rat-only era). Depth **2**: squire may appear.

---

## Presentation

### Color

```text
"fg": [120, 220, 255]
```

for all new goods. Knight already uses this (unchanged).

### Glyphs

| Glyph | Entity |
|-------|--------|
| `q` | dog_squire |
| `k` | knight (existing; kobold collision grandfathered) |
| `e` | ferret_guard |
| `L` | lion_warrior |
| `o` | otter_warden |
| `A` | boar_at_arms |
| `B` | badger_champion |
| `c` | ram_crossbow |
| `p` | sheep_cleric |

### Alignment / systems

| Trait | Value |
|-------|-------|
| `alignment` | `good` |
| `mobility` | `ground` |
| Vore fields | **Omit** |
| `placeholder` | omit / false |
| Depth scaling | Not applied to goods (evil-only stock) |

---

## Naming (`data/names.json`)

`ProperName` strings **include the title** (same pattern as current `"Sir Aldric"`). Introduction templates use `{name}` as the full string.

| Entity id | Name pattern (examples) | Notes |
|-----------|-------------------------|--------|
| `knight` | `Sir Aldric`, `Sir Roland`, … | **Only** archetype that uses **Sir**. Keep existing pool (no rewrite required). |
| `dog_squire` | `Squire Bob`, `Squire Cedric`, … | Title prefix `Squire ` |
| `ferret_guard` | `Guard Bob`, `Guard Helga`, … | Title prefix `Guard ` |
| `lion_warrior` | `Warrior Bob`, `Warrior Leo`, … | Title prefix `Warrior ` |
| `otter_warden` | `Warden Bob`, `Warden Ness`, … | Title prefix `Warden ` |
| `boar_at_arms` | `Bob-at-arms`, `Garrick-at-arms`, … | **Suffix** `-at-arms` (no “man”) |
| `badger_champion` | `Champion Bob`, `Champion Brock`, … | Title prefix `Champion ` |
| `ram_crossbow` | `Crossbow Bob`, `Crossbow Bram`, … | Role title, not “Sir” |
| `sheep_cleric` | `Cleric Bob`, `Cleric Agnes`, … | Role title |

Light species puns OK inside the given name portion. ~20–40 entries per pool.

---

## Introductions

Each new good: non-empty `introduction` with `{name}`, optional `introduction_log_category: "speech"`.

- **Do not edit** knight introduction lines.
- Tone by rank: squire eager; guard watchful; warrior bold; warden calm; boar-at-arms gruff professional; champion grim; crossbow measured; cleric gentle-but-firm.

---

## Combat balance

### Rules (locked)

1. **Simulated 1v1** using stock combat: hit if `accuracy - U(0, evade) > 0`; damage `U(dmin,dmax) - U(0, ac)` floored at 0; good strikes first each exchange.
2. Evils evaluated at **mid-band depth** with **Normal** `depth_scaling.json` bonuses applied.
3. Target: good wins **≥ ~95%** of 1v1s vs **primary peer**. Prefer handily over knife-edge.
4. Goods that are swallowed **cannot struggle free** → OK for goods to be **strong** for their band (not glass).
5. **Outnumbered** (2× peer) and **out-of-depth** heavies should often defeat goods (not a requirement of exactly 0% pack WR).
6. **Ranged goods:** `accuracy` / `min_damage` / `max_damage` **equal** `ranged_accuracy` / `ranged_min_damage` / `ranged_max_damage`.
7. No automated tests pin these numbers.

### Locked PR1 combat table

Simulated with Normal scaling; rounded for data authoring. Playtest may nudge ±10–15% if feel is off — log in Resolved decisions.

| id | max_hp | evade | ac | accuracy | damage | ranged_* | abilities | Primary peer check |
|----|--------|-------|-----|----------|--------|----------|-----------|--------------------|
| `dog_squire` | 16 | 2 | 1 | 1.5 | 3–5 | — | `[]` | bat/rat @3 → ~100% 1v1 |
| `knight` | **36** | **2** | **4** | **2.8** | **9–12** | — | `[]` | slime @6 → ~100%; wolf trivial |
| `ferret_guard` | 34 | 2 | 4 | 3.5 | 12–16 | — | `[]` | tarantula @9 → ~100% |
| `lion_warrior` | 48 | 2 | 5 | 4.2 | 14–18 | — | `[]` | gnoll @12 → ~100%; slug @12 → ~99% |
| `otter_warden` | 48 | 2 | 5 | 5.0 | 15–20 | — | `[]` | roc @15 → ~100% |
| `boar_at_arms` | 58 | 2 | 6 | 5.8 | 18–24 | — | `[]` | drake @18 → ~99%; wyvern free |
| `badger_champion` | 72 | 2 | 6 | 6.5 | 20–26 | — | `[]` | gryphon @18–20 → ~100% 1v1 |
| `ram_crossbow` | 28 | 2 | 3 | **4.0** | **7–10** | **same 4.0 / 7–10** | `["Range5"]` | fox Path profile @8 → ~100% |
| `sheep_cleric` | 32 | 2 | 3 | **7.0** | **9–12** | **same 7.0 / 9–12** | `["Smite5"]` | owl Smite profile @14 → ~100% |

**Knight was (old stock):** hp 20, evade 1, ac 3, acc 1.0, dmg 4–6 — **replaced** by the row above so squire owns early vermin and knight owns slime/wolf band.

**Pack note (sim):** 2× peer often loses for mid/late goods (e.g. 2× slime, 2× tarantula, 2× gryphon → near 0% for the good). Early squire can still win 2× bat because vermin chip damage is tiny through any AC; 3+ bats or a wolf-tier threat is the real “outnumbered” case early. That is acceptable.

**Specialist note:** ram/sheep can lose hard 1v1 to pure melee bruisers outside their peer (e.g. cleric vs roc) — expected; their job is peer specialist + general mid contribution, not replacing the melee ladder.

### experience_points

Modest tier ladder (cosmetic until XP ships): squire 15 → knight 25 (keep or set 25) → … → champion 50. Not balance-critical.

---

## Examine spines (PR1 prose)

| id | Theme |
|----|--------|
| `dog_squire` | Junior of the dog knightly order; eager, slightly oversized kit |
| `knight` | **Unchanged** existing examine |
| `ferret_guard` | Wiry ferret in light mail; patrol discipline, twitchy alertness |
| `lion_warrior` | Proud lion with open courage and a warrior’s kit |
| `otter_warden` | Sleek otter with warder’s baton/shield; calm river-scout energy |
| `boar_at_arms` | Stocky boar in practical harness; professional soldier, not a titled knight |
| `ram_crossbow` | Heavy-set ram with a crossbow as tall as dignity; measured aim |
| `sheep_cleric` | Soft-voiced sheep with holy symbol; gentle until the Smite lands |
| `badger_champion` | Broad badger in scarred plate; grim last wall against gryphon-class threats |

---

## Files touched

| File | Change |
|------|--------|
| `data/entities.json` | 8 new entities; **knight spawn + combat stats** |
| `data/names.json` | 8 new pools (knight pool untouched unless a name is missing Sir — keep as-is) |
| `openspec/specs/npc-data/spec.md` | Brief multi-good roster note |
| Tests | Optional load smoke only; **no** full suite on acceptance |

---

## Save compatibility

| Risk | Mitigation |
|------|------------|
| New ids | Additive |
| Knight stronger / narrower spawn | In-flight deep knights keep old stats until defeated; **new** spawns use new stats/window |
| No id renames | `knight` stable |

---

## Implementation notes (PR1)

1. Clone good shape from knight (no vore blocks).
2. Specialists: set melee and ranged fields to **the same** numbers; `Range5` / `Smite5` only.
3. Every new id: matching `names.json` pool + `introduction` array.
4. Knight: change `spawn` to 5–7 weight 1; apply combat table; leave examine/intros/glyph/fg/names pool alone.
5. Manual playtest is acceptance; no full pytest.

---

## Open questions

*(none blocking — remaining are playtest-only)*

Optional later: squire 2×bat still wins often due to vermin damage floor — only retune if designer wants early pack threat higher.

---

## Resolved decisions

| Date | Decision |
|------|----------|
| 2026-07-30 | Open change; data-only; no full regression on acceptance |
| 2026-07-30 | Cyan goods; unique free glyphs preferred |
| 2026-07-30 | Ram = Path counterpart; Sheep = Smite counterpart; Badger = champion vs gryphon |
| 2026-07-30 | Specialists: no `NoChase` |
| 2026-07-30 | **No two lions** |
| 2026-07-30 | **Boar-at-arms** (no “man” in name); id `boar_at_arms` |
| 2026-07-30 | **Otter Warden** added so bands stay short/equal |
| 2026-07-30 | Melee bands **length 3**; ranged parallel length 3 |
| 2026-07-30 | Champion spawn **17–1000** |
| 2026-07-30 | Knight band **5–7** + **combat stats strengthened** (squire owns vermin) |
| 2026-07-30 | Ranged goods: **identical** melee and ranged acc/dmg |
| 2026-07-30 | Names: **Sir only for knights**; Squire/Guard/Warrior/Warden/Crossbow/Cleric/Champion prefixes; `-at-arms` suffix for boar |
| 2026-07-30 | 1v1 target ~**95%+** vs peer (sim-backed table above); strong OK because no prey struggle |
| 2026-07-30 | Knight examine/intros/Sir name pool **not rewritten**; stats + spawn **are** |
| 2026-07-30 | PR1 shipped as design table; designer playtest OK; **no post-playtest retunes** |
| 2026-07-30 | PR2 acceptance; full suite waived; archived |

---

## Risks

| Risk | Mitigation |
|------|------------|
| Goods trivialize floors when several stack | Weight 1; equal short bands; pack vulnerability mid+ |
| Knight buff changes early-mid feel | Playtest depths 5–7 specifically |
| Early squire ignores 2 vermin | Accept or later lower AC/HP if designer wants pack fear earlier |
| Name/intro missing → no intro | Checklist both files per id |
