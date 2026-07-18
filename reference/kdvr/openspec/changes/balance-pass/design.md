# Design: Comprehensive data balance pass

| Field | Value |
|-------|-------|
| **Author** | Lead designer + Grok (agent assists) |
| **Date opened** | 2026-07-12 |
| **Status** | Active — latitude locked; baseline / spawn curve next |
| **Change name** | `balance-pass` |
| **Primary lever** | `data/*.json` (incl. `global_tuning.json` after extraction) |

---

## Overview

Playtest-driven, long-horizon tuning of stock balance. Latitude is locked below. Iterate in small data batches; **no balance sim** until designer certifies a balanced baseline. Code only with explicit authorization (exception already granted: pull day‑1 combat/regen/vore/loot constants into JSON).

**Progression philosophy (unchanged):** player power from **gear + floor runes**, not XP. Threat from species table, density, depth bake, prefixes. **There is no pure combat game-over** — fate is vore/digestion (or stun path into that fantasy).

**Terminology:** defeated / stunned / digested.

---

## Project context (scan snapshot, 2026-07-12)

Recent shipped work that affects balance feel:

| Area | Notes |
|------|--------|
| Difficulty + depth scaling | `data/depth_scaling.json` — Easier/Normal/Hard/Nightmare; evil-only bake |
| Density | `data/dungeon_spawn.json` + per-difficulty `density_multiplier` |
| Prefixes | Elite, Brute, Berserk, Veteran, Starving, Sniper, Bloated (designer-vetted) |
| Roster | ~17 evil + knight + rabbit; many placeholders still weighted |
| Abilities | Thematic; distance on RangeN/SmiteN tunable; see latitude |
| Throwables, potions, wands | Full loot ladders |
| Depth jump | **Out of scope for this balance pass** |
| Macguffins | **Out of scope** (victory objects, not survivability knobs) |
| Balance sim | Exists but **not used** until baseline is designer-approved |

---

## Goals (designer)

| Question | Answer |
|----------|--------|
| Primary difficulty | **Normal** first (Easier/Hard/Nightmare later / lighter touch this pass) |
| Floor 1 | **Very easy** — literally only rats, nothing else |
| Floor 2 | Add **bats** — annoying weak Erratic dancer |
| Floor 3 | Add **wolves** as real bruiser; **knights** first appear |
| Floor 4+ | Ramp more sharply (player has some potions/wands by now) |
| New threats | Each floor introduces a credible new threat when roster allows; later every 2–3 floors |
| Floors 5–12 | Credible ramp; game-over risk if not paying attention |
| Floors 13–20 | Pressure rises; floor **20+ dragons** remain **Yeti / you lose** if you stay and fight |
| Combat vs vore | **Invalid split** — no pure combat game-over; **survivability** is the curve (engulf/digest risk) |
| Balance sim | **Do not use** until designer says a build is balanced; then for regression when adding content |

### Difficulty ladder (four levels) — Normal is the active target

| Difficulty | Intended feel (designer) |
|------------|--------------------------|
| **Easier** | *(not primary this pass)* gentler density/curve when we get to it |
| **Normal** | **Not a free ride**, but **OK most of the time if you use your items.** Not super-brutal. “I have to spend potions/wands, and when I do, I feel fine.” |
| **Hard** | *(later)* steeper; more punish for mistakes |
| **Nightmare** | *(later)* extreme |

**Normal amendments (2026-07-12):**

- Do **not** tune Normal as a masochist / soft-lock gauntlet before the Macguffin race.
- Consumables are **part of the expected toolkit** from ~F3 onward, not shameful panic only.
- **Dragons (F20+ / 21+ all dragons)** stay **certain doom if engaged** — Skifree Yeti end — independent of “Normal is fair.” The fair ramp is **1–19**; the end is the spike.
- Depth scaling / density on Normal should support the above, not Nightmare-by-another-name.

### Difficulty-curve principles (designer 2026-07-12) — **keep going forward**

| Principle | Target |
|-----------|--------|
| Floor **1–2** survivability | ~**90%** for reasonably cautious **melee-only** play (no panic consumable dependence) |
| Floor **3** | Starts needing **occasional consumables** to stay safe |
| Player accuracy (on pace) | ~**75%** hit rate vs foes of **moderate / equal-depth** strength, with good rune pace + relatively latest gear |
| Monster accuracy (on pace) | ~**50%** hit rate vs player in that same scenario |
| Low-tier falloff | Weaker species (rats, then bats) may become nearly harmless before they stop spawning — power-growth fantasy |
| Number scale | Designer suspects many current stats look **too small**; re-evaluate after math + playtest |

**On pace** means: collecting floor runes at a healthy rate and wearing depth-appropriate weapon/armor (not raw F1 dagger forever at depth 10).

### Combat math (engine — do not forget when tuning)

```text
Hit:    accuracy - continuous_uniform(0, evade) > 0
        (if evade <= 0, roll is 0 → any accuracy > 0 always hits)
        P(hit) ≈ min(1, accuracy/evade) when evade > 0 and accuracy > 0
Damage: uniform_int(min_damage, max_damage) - uniform_int(0, ac), floor 0
```

**Resolved 2026-07-15 (designer):** evade is a **float**, same family as accuracy — not integer-only. The engine used `randint(0, evade)` which created discrete hit cliffs (`k/(E+1)` only). That was a bug vs the npc-data spec (`uniform(0, evade)`). Continuous uniform is the intended model; armor/runes/monsters may use fractional evade.

### Evade precedent (designer 2026-07-12) — **new; no prior sacred values**

Player evade was a **stub** (stock `0`) never examined. This pass **sets the real system**.

| Decision | Choice |
|----------|--------|
| Player can gain evade | **Yes** — base + **armor** + **runes** |
| Armor theming | Evade is **not** pure “dodge speed.” Heavy armor **raises** evade as **glancing / reinforced plate / dirty contact** — “hit a strong spot” or “didn’t land clean,” not only footwork |
| Runes | May raise evade (new effect and/or extend warding — implementation detail when coded) |
| Absolute number scale | **Irrelevant** if ratios and feel are good; no preference for big vs small integers |
| 75% / 50% targets | **Per-floor, mathematical**, from expected on-pace weapon + armor + runes — not one global accuracy number |

#### Hit-rate table (engine formula)

`P(hit) = |{ r ∈ 0..E : accuracy > r }| / (E+1)`  (E=0 → always hit if accuracy > 0)

| acc \\ evade | 0 | 1 | 2 | 3 | 4 | 5 | 7 |
|--------------|---|---|---|---|---|---|---|
| ≤1.0 | 100% | **50%** | 33% | 25% | 20% | 17% | 12% |
| (1, 2] e.g. 1.5–2.0 | 100% | 100% | **67%** | **50%** | 40% | 33% | 25% |
| (2, 3] e.g. 2.5 | 100% | 100% | 100% | **75%** | 60% | **50%** | 38% |
| (3, 4] | 100% | 100% | 100% | 100% | 80% | 67% | **50%** |

Exact **50%** only for **odd** evade (1, 3, 5, 7, …). Exact **75%** at evade **3** with acc in (2, 3].

#### On-pace player accuracy today (optimistic: best depth-eligible weapon + armor AC ladder + all 3 runes/floor)

Approx player accuracy = `1.5 + weapon.accuracy_bonus + E[accuracy runes×0.03]` (might ignored).

| Entering depth | ~weapon (optimistic) | ~pAcc | Hit vs mon E=2 | Hit vs mon E=3 |
|----------------|----------------------|-------|----------------|----------------|
| 1 (starter dagger, not club) | dagger +0.16 | **~1.66** | **67%** | 50% |
| 3–9 | mace…battleaxe | **~1.56–1.70** | **67%** | 50% |
| 10–19 | greatsword…warhammer | **~1.8–2.0** | **67%** | 50% |
| 20+ | same + more acc runes | **~2.0–2.1** | 100% | **75%** |

**Implication:** with current weapon/rune accuracy growth, the player sits in the **(1, 2]** band for almost all of depths 1–19. Against that:

- **Peer monster evade = 2** → player hit **~67%** (accept as the practical “~75%” band until accuracy growth is buffed).
- **Peer monster evade = 3** → player hit **only 50%** (too swingy / weak for “on pace” — reserve for hard elites or intentional tanks).

If we later want true **75%** mid-game, we must either raise on-pace accuracy into **(2, 3]** (more/better accuracy runes, weapon bonuses) **or** keep peer evade at 2.

#### Proposed player evade composition (design; not shipped until authorized PR)

```text
player_evade = base_evade
             + armor.evade_bonus
             + progression.bonus_evade   # runes
```

Recommended **base_evade = 1** (global_tuning) so F1 robes can land on an odd total without armor bonus.

**Armor evade_bonus ladder** (aligned with “heavier = more glances”; indigestion suit combat-glass):

| Armor | ac_bonus (now) | proposed evade_bonus | F1 base1 total E |
|-------|----------------|----------------------|------------------|
| robes | 1 | **0** | **1** |
| leather | 2 | **2** | **3** |
| waxed hide | 1 | **0–1** (dig-focused) | 1–2 |
| ringmail | 4 | **2** | **3** |
| oiled ringmail | 3 | **2** | **3** |
| chainmail | 6 | **4** | **5** |
| oiled chainmail | 5 | **4** | **5** |
| plate | 8 | **6** | **7** |
| indigestion suit | 0 | **0** | **1** (belly tank, not combat glance) |

**Rune (resolved for PR-evade):** new effect type `natural_evade` with integer `amount` (default pieces 1/1 like other runes). Stock: **one** optional early-mid rune row **or** grant evade on existing warding via dual progress — **prefer dedicated `natural_evade` rune** so warding stays AC-identity. Stock first cut:

| Field | Value |
|-------|--------|
| id | `evasion_rune` (display: rune of evasion / glancing) |
| weight | 2 |
| min_depth | 2 |
| effect | `{ "type": "natural_evade", "amount": 0.5, "pieces_per_bonus": 2, "pieces_granted": 1 }` (float EV; two pieces → +0.5) |

So on-pace evade from runes grows slowly (piece bank); armor remains the main step-ups. Difficulty `rune_pieces_multiplier` applies as for other piece banks.

**effective_fighter:**  
`evade = player.Fighter.evade` (from global_tuning base at spawn) `+ armor.evade_bonus + prog.bonus_evade`  
(Today evade is only the raw Fighter field — never armor/runes.)

#### Monster accuracy / evade pairing (on-pace peer) — **PR-curve-1**, not PR-evade

| Player total E (on pace) | Monster acc for **~50%** | Monster evade for **player ~67–75%** |
|--------------------------|--------------------------|--------------------------------------|
| 1 (robes) | acc in **(0, 1]** e.g. **0.75** | **2** (player pAcc~1.66 → 67%) |
| 3 (leather / early mail) | acc in **(1, 2]** e.g. **1.5** | **2** while pAcc≤2; else **3** if pAcc>2 |
| 5 (chain) | acc in **(2, 3]** e.g. **2.5** | grow peer evade with player power |
| 7 (plate) | acc in **(3, 4]** e.g. **3.5** | peer evade 2–3+ |

**Low-tier falloff:** older species keep low accuracy/damage; as player E and AC rise, their hit *and* chip fall off before `max_depth` — intentional. On **Normal**, falloff should feel like power fantasy, not “trash packs still delete you.”

#### Early floors (with proposed E)

| Floor | Player E (proposed) | Peer mon acc ~50% | Peer mon evade | Player hit ~ |
|-------|---------------------|-------------------|----------------|--------------|
| 1–2 rat/bat | **1** (base+robes) | **~0.5–1.0** | rat **1** (player often 100% — training) / bat **2** (67%) | easy clears |
| 3 wolf | still **1** if robes; **3** if leather found | **~0.75** or **~1.5** | **2** | 67% player |

F1–2 ~90% melee-only still dominated by **density + damage/TTK**, not only hit%.

---

## PR plan (code + data)

### PR-evade — evade system plumbing *(design complete; implement only when authorized)*

**Goal:** Player evade is real: base + armor glancing + rune bank. **No** full monster retune in this PR (keep stock mon numbers so delta is reviewable); optional tiny smoke that robes+base E≥1.

| # | Task |
|---|------|
| 1 | `global_tuning.json` player `evade`: stock **1** (was 0) |
| 2 | `armor.json`: add `evade_bonus` per ladder above; loader/schema default **0** |
| 3 | `PlayerProgression.bonus_evade: int = 0`; save codec soft-default 0 |
| 4 | `floor_runes`: parse + apply `natural_evade`; stock `evasion_rune` row |
| 5 | `effective_fighter`: include armor + prog evade; throw path if needed |
| 6 | Sidebar/UI: show evade if already shows AC (match existing pattern; no layout redesign) |
| 7 | SCHEMA.md + any inventory examine if armor stats listed |
| 8 | Tests: fixture-only parse/apply evade_bonus and natural_evade; effective_fighter unit test with fixture armor — **no** stock balance asserts |
| 9 | Manual checklist: F1 evade 1 with robes; equip leather → +2; step evasion rune pieces |

**Out of PR-evade:** mass mon accuracy rewrite; density; depth_scaling Normal retune.

### PR-curve-1 — Normal hit bands + early survivability *(after PR-evade; separate auth)*

**Goal:** On **Normal**, mon accuracy/evade (+ light HP/dmg if needed) match pairing table; F1–3 match 90% / consumable-start feel; do **not** brutalize mid-game.

| # | Task |
|---|------|
| 1 | Retune mon `accuracy` / `evade` by species vs depth role (rat→dragon ladder) |
| 2 | Light TTK pass only if hit bands leave F1–3 wrong (careful dig dmg) |
| 3 | Spot-check Normal `depth_scaling` — no Nightmare-level banks by accident |
| 4 | Designer playtest checklist (items matter ~F3; F1–2 easy; dragon end still Yeti) |

### Later PRs (not designed in detail yet)

- PR-curve-2+: mid/deep Normal after playtest  
- Easier/Hard/Nightmare differentiation  
- Optional accuracy-growth buff if true 75% mid-game desired  

**Status:** **PR-evade** and **PR-curve-1** shipped 2026-07-12. Next: designer playtest on Normal F1–5+; PR-curve-2+ only from feedback.

### Spawn / encounter fantasy (summary)

```text
1:   rats only
2:   + bats (dancers)
3:   + wolves (bruisers) + knights (good)
4+:  sharper ramp; new threat per floor when possible
5–12: pay attention or get digested
13–20: steep lethality → 20 dragons / Macguffin race
```

---

## Latitude model

| Level | Meaning | Agent rule |
|-------|---------|------------|
| **Free** | Main knobs | May propose; edit only in an **authorized batch** |
| **Careful** | Easy to break fantasy or snowball | Small steps; explicit OK |
| **Last resort** | Strong designer preference | Explicit green-light per change |
| **Frozen** | Do not change this pass | Never edit without reopening |
| **Out of scope** | Not this pass | Leave alone |
| **Discuss** | Needs phase conversation | Do not change until discussed |

---

## Resolved latitude (designer 2026-07-12)

### 1. `depth_scaling.json` — **Free**

Density multiplier, runes override, pieces multiplier, prefix_spawn curves, all depth stat schedules.

### 2. `dungeon_spawn.json` — **Free**

Density bands, variance, min/max NPC clamps.

### 3. `entities.json`

| Knob | Latitude |
|------|----------|
| HP, AC, evade, accuracy, melee/ranged damage | **Free** |
| `digestion_damage_per_tick` | **Careful** — 100% while engulfed; only source that damages armor; snowballs easily |
| `digest_time` | **Frozen** — prefer **5** unless lore (super-fast/slow digester). **Not** a balance knob |
| `spawn.weight`, `min_depth`, `max_depth` | **Free** |
| `mobility`, `alignment` | **Frozen** |
| `abilities[]` | **Discuss** (next phase / baseline) — **thematic**, not balance. Exception: if species **already** has RangeN/SmiteN, **distance N may change for balance**. Do **not** add/remove thematic tags (e.g. Bat **must** stay Erratic). Current ability assignments are **not all correct** — go over during baseline |
| Narratives, names, glyphs | **Out of scope** |

### 4. `npc_prefixes.json` — **Free**

Including weights, flat bonuses, **and** ability-granting prefixes (designer already vetted all prefixes).

### 5. `floor_runes.json`

| Knob | Latitude |
|------|----------|
| `runes_per_floor` (stock 3) | **Last resort** — designer likes 3 |
| Weights, depths, effect amounts, pieces | **Free** |
| New rune effect **types** | Allowed with **proposal + approval** (code when needed) |

Difficulty `runes_per_floor_override` remains **Free** via depth_scaling (economy by difficulty), distinct from stock catalog default of 3.

### 6. Gear (`weapons` / `armor` / `throwables` / `potions` / `wands`) — **Free** with identity rules

- Keep **relative power order** within each category (e.g. robes weakest conventional armor; plate / indigestion suit top of their roles — do not swap leather above robes).
- Weapons: preserve **balanced / strong / accurate** identities within depth zones.
- Heavy weapons: **strong but slightly inaccurate**.
- Elegant weapons: **accurate but slightly less strong**.
- Some weapons are **straight upgrades** — preserve that ladder.

### 7. Macguffins — **Out of scope**

Not survivability balance (victory / score).

### 8. `depth_jump_start.json` — **Out of scope**

### 9. Former `constants.py` combat/regen/vore/loot knobs

**Decision:** extract to **`data/global_tuning.json`**, whole-file moddable, then treat as **Free**.

Includes (stock values preserved at extraction):

- Player: max_hp, accuracy, evade, ac, min/max damage  
- Regen: hp amount, every_n player turns, evil every_n  
- Vore: hp_threshold, hit_min/max, escape_base, escape_per_fail, struggle_damage  
- Loot: max_floor_item_placements, min_floor_potions  

### 10. Confirmed freezes / process

- No XP system  
- No `digest_time` depth scaling  
- No mid-run difficulty change  
- Never pin live balance numbers in automated tests  
- Complete only when designer says so  
- No sim use until calibrated baseline  

### Additional

| Topic | Latitude |
|-------|----------|
| `ui_layout`, `names`, `rescue_gratitude` | Out of scope |
| UI / prose | Out of scope |

---

## Working process

1. ~~Latitude intake~~ **done**
2. **Baseline expectations** — abilities audit, floor 1–20 spawn table intent, designer play feel notes
3. **Tweak batches** — one authorized theme at a time; data-only unless code authorized
4. Designer playtest between batches (no sim)
5. Log keep/revert in iteration log
6. When balanced: optional sim calibration for future content
7. Archive on designer complete

### Batch rules

- One authorized batch at a time  
- Data first  
- Fixture-pinned tests only; never assert stock balance numbers  

---

## Resolved decisions

| Date | Decision |
|------|----------|
| 2026-07-12 | Open `balance-pass`; data-first; long iterative |
| 2026-07-12 | Latitude locked (this document) |
| 2026-07-12 | Goals: Normal first; floor 1 rats → 2 bats → 3 wolves+knights; 20 dragon/Macguffin race |
| 2026-07-12 | No pure combat game-over framing |
| 2026-07-12 | No sim until designer-approved baseline |
| 2026-07-12 | **Authorized:** extract player/regen/vore/loot constants → `global_tuning.json` (Free thereafter) |
| 2026-07-12 | `digest_time` frozen (~5); digestion_damage_per_tick careful |
| 2026-07-12 | `runes_per_floor` stock default last resort at 3 |
| 2026-07-12 | Macguffins + depth_jump out of scope |
| 2026-07-12 | abilities[] set in Baseline-1 (see roster table); RangeN/SmiteN distance OK to retune |
| 2026-07-12 | cave_rat → `rat`; giant_spider deleted; rabbit spawn weight 0 |
| 2026-07-12 | F1 rat-only; F2 +bat; F3 +wolf +knight; 21+ evil = dragons only |
| 2026-07-12 | Curve principles: F1–2 ~90% melee-only; F3 consumables start; on-pace player ~75% / monster ~50% hit vs peer foes; low-tier falloff OK; numbers may scale up |
| 2026-07-12 | Evade was stub; **new precedent:** base + armor (glancing/heavy) + runes; per-floor math for 75/50 |
| 2026-07-12 | On-pace pAcc stays ~1.5–2.0 for depths 1–19 → peer mon evade **2** ≈ player 67% hits (practical ~75%) |
| 2026-07-12 | Prefer **odd** player total evade for exact mon 50% hit bands; proposed base_evade=1 + armor ladder |
| 2026-07-12 | Absolute stat magnitudes secondary to feel; ratios/TTK/hit bands primary |
| 2026-07-12 | **Normal:** not free, not super-brutal; OK most of the time **if you use items**; dragons F20+ remain Yeti doom |
| 2026-07-12 | PR-evade designed (base1, armor ladder, natural_evade rune pieces/2); PR-curve-1 is mon retune after |
| 2026-07-15 | **Evade is continuous float** (same family as accuracy). Hit uses `continuous_uniform(0, evade)`, not integer `randint`. Integer-only EV was a bug vs npc-data spec; mon/player/armor/runes may use decimals. Old discrete hit-band tables are historical only. |

---

## Baseline roster decisions (designer 2026-07-12)

### Abilities

| Species | Abilities |
|---------|-----------|
| rat (was cave_rat) | none |
| bat | Erratic, Lifedrain |
| slime | Slow |
| wolf | none |
| shark | none |
| tarantula | NoChase |
| giant_spider | **deleted** |
| fox_archer | Range5, NoChase |
| kobold | Hands, Coward |
| gnoll_mercenary | Range3, Hands |
| tunnel_slug | Slow |
| roc | none |
| owl_mage | Smite5, NoChase |
| wyvern | Knockback |
| drake | Knockback |
| gryphon | Knockback |
| dragon | Range5 |
| knight | none |
| rabbit | none; **spawn.weight 0** (parked) |

### Spawn windows (locked early; mid+ agent-set for ramp)

| Depth | Allowed evils / goods |
|-------|------------------------|
| 1 | **rat only** |
| 2 | rat, bat only |
| 3 | wolf, rat, bat, **knight** only |
| 4–19 | ramp: new threats over time; rats/bats trail off; slime/shark from 4+ |
| 20 | dragons enter; late flyers end around here |
| 21+ | **all dragons** (other evils max_depth ≤ 20) — Skifree-yeti extreme |

### Soft themes (stats guide, not hard mandate)

Rat/bat vermin; wolf low bruiser; slime = slow tanky hit; shark water glass if engaged; tarantula glass cannon; fox ranged pest / weak melee; kobold accurate coward poke; gnoll short-range generalist; tunnel slug = slime upgrade + Slow; roc mid wolf; owl = fox upgrade with Smite; wyvern→drake→gryphon power ladder + Knockback; dragon = run or digested + Range5.

---

## Iteration log

| Batch | Date | Intent | Changes | Outcome |
|-------|------|--------|---------|---------|
| Docs | 2026-07-12 | Latitude + goals | OpenSpec | locked |
| PR0 | 2026-07-12 | Extract global tuning to JSON | `data/global_tuning.json`, loader, mods whole-file, constants aliases, SCHEMA/modding/README, `tests/test_global_tuning.py` | stock values preserved; Free thereafter |
| Baseline-1 | 2026-07-12 | Abilities + spawn + light stats | `entities.json` roster pass; spider deleted; rat rename; rabbit w=0 | awaiting playtest |
| Curve-principles | 2026-07-12 | Survivability + accuracy math | design only (hit formula, F1–3 analysis, open evade gap) | documented |
| Evade-precedent | 2026-07-12 | Armor/rune evade + on-pace tables | design.md only; implement PR pending auth | locked design |
| Normal-feel | 2026-07-12 | Normal = items-OK fair; not brutal; Yeti dragons kept | design goals | locked |
| PR-evade | 2026-07-12 | Ship evade system | global_tuning 1; armor evade_bonus; natural_evade + evasion_rune; effective_fighter; save; status/inspect UI; tests | shipped |
| PR-spawn-freeze | 2026-07-12 | Anti-swarm distant freeze | difficulty `spawn_ai_freeze`; one-shot distance freeze; proximity + damage wake | shipped |
| PR-curve-1 | 2026-07-12 | Hit-band mon acc/evade + light early HP | entities.json retune; dragon Yeti acc 8; peer bands by depth era | shipped |
| Playtest-d7 | 2026-07-12 | Depth 7 feedback | kobold +NoChase; early-mid mon tougher; wand weights 50→5 MM (loot share ~20–25%); freeze longer Normal | pending re-play |
| Playtest-too-hard | 2026-07-12 | Bat/wolf soft; throw packs | bat/wolf toward curve-1; throwables spawn_stack 3–4 floor piles | superseded |
| Playtest-dagger-durability | 2026-07-12 | Silent weapon break felt like soft mon | all weapon durability_max 9999; bat/wolf restored to playtest-d7 toughness | pending re-play |
| Playtest-tarantula-fox | 2026-07-12 | Mid feedback | tarantula tougher (HP/AC/dmg); fox_archer ranged_accuracy 1.6→1.0 | pending re-play |
| Fix-path-ranged-kite | 2026-07-12 | RangeN kite + no stun approach | choose_path_ranged: stand ground; chase stunned; visit holds mid-range | shipped |
| Arena-csv-pass1 | 2026-07-15 | Stronger mid/late threats | slime/tarantula +; kobold/gnoll/roc ++; wyvern/drake/gryphon +; dragon + (HP/acc/dmg only) | pending arena re-run |
| Arena-csv-pass2 | 2026-07-15 | Mixed easy/hard | shark -1bp acc; slime +1bp; tarantula/kobold/drake/gryphon harder; gnoll easier; slug much harder; roc/wyvern slight + | pending re-run |
| Tarantula-sweet | 2026-07-15 | Oscillation analysis | settle **18 HP / 2.06 acc / 11–14 dmg** (between 17-soft and 19-hard) | pending feel check |
| Ranged-centaur | 2026-07-15 | Fox/owl DCSS centaur theme | fox path ~10 shots to 39HP/AC4; owl smite ~15 to 60HP/AC8; melee near-useless | pending arena/play |
| Ranged-low-var | 2026-07-15 | Prefer acc over spike dmg | fox 5–7@3.5; owl 6–8@6.5 (depth-baked ~7–9); max hit small | pending feel |
| PR-evade-continuous | 2026-07-15 | Fix EV cliffs | float evade end-to-end; `rng.uniform(0,E)`; SCHEMA/specs; continuous hit tests | shipped |
| Acc-retune-continuous | 2026-07-15 | Continuous hit rates + slower EV runes | evasion_rune amount **0.5**; wolf 0.55↓; kobold 2.50; roc 3.25; wyvern 3.90; drake 4.80; gryphon 5.10; dragon 9.5 | pending playtest |
| Hard-pare | 2026-07-15 | Hard slightly easier (Normal/Nightmare unchanged) | density 1.15→1.10; freeze gentler; prefixes later/lower cap; stat banks slower (HP/AC/dmg/acc/dig/evade) | pending playtest |

### Tarantula sweet-spot analysis (2026-07-15)

Theme: **NoChase glass cannon** (territorial, high hit/dmg, low bulk). Evade stays **1** (easy to punish when you commit). AC stays **1**.

| Revision | HP | Acc | Dmg | Designer reaction |
|----------|----|-----|-----|-------------------|
| Early glass (curve-1 era) | 9 | ~0.7–1.7 | 6–9 | Later: too soft for mid game |
| Playtest “tougher” | 12 | 1.85 | 7–11 | Base for arena work |
| Arena pass1 stronger | 15 | 1.9 | 8–13 | still climbing |
| Pass2 harder | 18 | 2.0 | 9–14 | still climbing |
| Pass3 slightly harder | **19** | **2.05** | **10–14** | **Too hard** → asked easier |
| Easier | **17** | **2.0** | **9–13** | **Too soft** (“nerf too much”) |
| Restore harden | **18** | **2.05** | **10–14** | Close; **slightly soft** |
| Sweet-spot target | **18** | **2.06** | **11–14** | Between 17-soft and 19-hard |

**Inference:** HP **19** with 10–14 was over the line; HP **17** with 9–13 undershot. HP **18** is the only bulk value not rejected. Avg dmg at soft floor ≈ **11**, at hard ceiling ≈ **12**, current mid ≈ **12** — raise **min** only (11–14, avg 12.5) for a small consistency bump without max-spike thrash. Acc **2.06** is a hair above the last “almost right” 2.05 without jumping a discrete hit band vs common evade.
| Weapon-ladder | 2026-07-15 | Depth spread + acc/dmg/bal cadence | dagger+ultimates kept; club slight dmg upgrade; mid weapons retuned depths 2–17 | pending playtest |

---

## Impasse / code proposals

| Topic | Status |
|-------|--------|
| global_tuning extraction | **Authorized** — implement as PR0 |
| New floor rune effect types | Propose when needed; need approval |
| abilities[] corrections | Discuss in baseline phase — no silent edits |

---

## Related specs

- `openspec/specs/balance/spec.md`
- `openspec/specs/balance-simulator/spec.md` (dormant for this pass)
- `openspec/specs/floor-runes/spec.md`
- `openspec/specs/npc-data/spec.md`
- `openspec/specs/dungeon/spec.md`
- `openspec/specs/modding/spec.md` (whole-file list includes `global_tuning.json` after PR0)
- `data/SCHEMA.md`
