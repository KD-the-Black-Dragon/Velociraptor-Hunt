# Design: Tactical duel combat feel

| Field | Value |
|-------|--------|
| **Change** | `openspec/changes/tactical-duel-combat/` |
| **Status** | Design frozen for Q&A (2026-08-15) — **no implementation until PR authorization** |
| **Parent systems** | `match_session`, `match_combat`, `match_combat_resolve`, `match_tactics`, `match_ai`, match HUD, `messages.py`, scheduler |
| **Data** | `match_combat.json` (momentum, fumble, chip, dodge outcomes, readout flags), `match_ai.json`, entity defense profiles |
| **Canon** | DESIGN_CANON: modal = Incoming crises; log = impacts/near-misses; UnReal World prose; balance from actions not stance toggles |

---

## North star

Battles feel like a **real fight** and a **fighting-game contest of timing**:

- Most time is **testing and maneuvering** (measure, feints, footwork, balance).
- You **order** attacks; the game **arbitrates** how hard they land from posture, measure, recovery, and kit — like counterhits in a fighter: you press attack; if timing is right, the system makes it devastating.
- **High strike-momentum** blows that threaten to break through normal defense are rare **cinematic crises** (Incoming).
- **Attrition** (many shield takes) and **explosive punish** (hit them during their big recovery) are both valid.
- Shield **durability / break** deferred.

Exact weights live in JSON and are playtest-tuned.

---

## Naming (avoid collisions)

| Term | Meaning |
|------|---------|
| **Strike momentum** | New scalar (and factor breakdown) scoring how dangerous / how much an attack takes advantage of the defender **this swing** |
| **Footwork momentum** | Existing short-lived directional vector from footwork (helps/hurts emergency dodge) |
| **Balance** | Existing −10…+10 posture meter from actions |

Do not overload “momentum” in code without a prefix (`strike_momentum` vs `footwork_momentum`).

---

## Current baseline (code facts)

| Area | Today |
|------|--------|
| Incoming | Nearly every PC-targeted NPC swing opens modal |
| Reactions | Dodge (stamina fatigue), Parry, Counter (free jab), Ignore |
| Hit math | Accuracy vs evade; AC subtract; balance mostly mults damage/acc |
| Log | Numeric “hits for N” |
| HUD | Player-centric; no foe plan/balance/attrs |
| Balance +acc | Overextended cuts accuracy mult (~5% land at +10) |

---

## 1. Strike momentum (core arbitration)

### Fantasy

Fighters always do the **best they can under the circumstances**. The player (or AI) issues **Attack** (or a named ability); they do **not** micromanage jab vs haymaker on every basic swing.

The game compares **attacker strike factors** vs **defender vulnerability factors**, produces **strike momentum**, and that drives:

- How severe the attack is (chip vs solid vs breakthrough)
- Whether **Incoming** opens (PC defender)
- How NPC defenders choose emergency responses
- Narrative intensity tier
- (Debug) on-screen factor breakdown

This is the fighting-game model: **counterhit / punish is automatic** when you attack into their windup or long recovery — no special “Counter” command.

### When computed

On every weapon swing / basic attack / offensive ability that can deal stamina damage, **after** the action is committed as intent but **before** Incoming / final damage application.

Order:

1. Attacker pays / queues action costs as designed (AUT/AP/balance deltas for the chosen action).
2. **Overbalance fumble check** (attacker only; §4). Fumble → stop; no Incoming; log fumble.
3. **Compute strike momentum** (+ factor breakdown for debug).
4. **Derive attack expression** (jab-level vs standard vs committed) from attacker circumstances (esp. balance) and ability choice.
5. Route: passive resolve vs Incoming / NPC emergency reaction.
6. Apply outcome + narrative log.

### Factor model (data-weighted sum)

All weights in JSON. Implementation returns something like:

```text
StrikeMomentumResult
  total: float          # e.g. 0..100 or -50..+50 — tune scale in data
  factors: list[(id, value, contribution)]  # for debug HUD
  tier: enum            # e.g. chip | solid | breakthrough | devastating
  incoming: bool        # total/tier crossed Incoming threshold
```

**Attacker factors (positive → higher momentum):**

| Factor | Notes |
|--------|--------|
| Balance posture | Positive balance aids aggression **up to a point**; extreme overextend is handled by **fumble**, not by “miss RNG.” Mid-high aggression helps power. |
| Optimal weapon measure | In preferred band → bonus; wrong band → penalty (reuse measure curves as momentum, not hit-chance) |
| Ability commitment | Named abilities (Haymaker, etc.) add a large base; basics add less |
| Buffs / temp edge | Existing debuff/buff mults on attacker |
| Target is **beast** | Momentum **bonus** representing no real parry/shield options |
| Flank / geometry | Optional; can feed momentum instead of old accuracy mult |

**Defender factors (their weakness → higher attacker momentum):**

| Factor | Notes |
|--------|--------|
| Relative balance | Defender overextended or cowering badly → more vulnerable; solid defensive balance → lower momentum through |
| **AUT recovery remaining** | Long remaining cooldown (windup/recovery after big action) → **large vulnerability** (fighting-game punish) |
| Debuffs / injuries | Temp accuracy/damage/defense debuffs |
| Not emergency-committed | If they already chose emergency block this beat, etc. (usually N/A at compute time) |

**Relative balance:** prefer comparing both bars (attacker − defender or table lookup), not attacker balance alone.

### Timid stance → jab-only expression

If attacker **balance is negative** (timid / defensive posture), a **basic attack order** is expressed as a **jab-level** action: low commitment, low breakthrough chance, normally absorbed by passive defense. They are not free to “all-out” purely from a basic attack command while timid.

- Explicit **abilities** may still be usable if legal (AP/etc.), but scorer/UI can warn; design default: abilities remain player-chosen exceptions with their own costs.
- AI at low balance should prefer jab-level / hold / brace rather than abilities unless Ferocity/Appetite extreme.

### Tiers and Incoming

| Tier (illustrative names) | Feel | Incoming (vs PC)? |
|---------------------------|------|-------------------|
| **Chip** | Testing jab; shield takes it | **No** — auto passive defense |
| **Solid** | Real contact, still mostly covered | **No** (or rare; default no) |
| **Breakthrough** | About to crack normal defense — “that axe is really coming” | **Yes** |
| **Devastating** | Full punish (e.g. huge recovery + good attacker posture + ability) | **Yes**; Ignore is especially painful; emergency Block/Dodge are the cinematic scramble |

Thresholds: JSON (`incoming_min_total` or `incoming_min_tier`).

**Ignore fantasy:** only appears on breakthrough+ crises. Choosing Ignore means *I’d rather eat this than spend AUT* — enables slugfest trades (both fighters standing in pocket swinging). Not “still fully passive-block as if nothing special.”

### Fighting-game counterhit

High defender `remaining_aut` (or recently committed long action) is a **first-class momentum factor**. Landing an attack in that window should routinely reach **breakthrough/devastating** without a separate Counter button. Emergency Block may still reduce, but less effectively than against a neutral-timing solid hit (JSON: `block_efficacy_by_tier`).

### Debug vs live UI

| Surface | Dev / pre-alpha default | Later live |
|---------|-------------------------|------------|
| Factor breakdown lines | On (flag) | Off or perk |
| Total strike momentum | On (flag) | Optional / hidden |
| Opponent plan, balance, stamina, personality | On (flag) | Partial hide |

```json
"opponent_readout": {
  "show_plan": true,
  "show_balance": true,
  "show_stamina": true,
  "show_personality": true,
  "show_strike_momentum_debug": true
}
```

Show last resolved (or pending Incoming) momentum against the focus foe when relevant.

---

## 2. Incoming modal (breakthrough crises only)

### When

- Strike momentum tier ≥ Incoming threshold
- Target is PC
- Not obscured grappled prey
- Attacker did **not** fumble

Otherwise resolve immediately (passive path / NPC path).

### Options (PC)

| Key | Name | Effect | Cost |
|-----|------|--------|------|
| **1** | **Dodge** | Emergency footwork step (direction prompt) | **Identical** to 1-tile footwork: same **AP**, **AUT**, **balance** rules. **Cannot** if AP insufficient. **Differences only:** allowed even while waiting on cooldown; AUT **appends** to remaining cooldown |
| **2** | **Block** | Emergency brace into the blow | **Identical** to brace (`d`): same AUT, same sliding balance rules, same AP (0). AUT **appends**. Beasts: **N/A** (see §5) |
| **3** | **Ignore** | No emergency commitment | **0** AP / AUT / balance. Full crisis resolution — high chance of real hurt; sets up possible immediate return attack (slugfest) |
| ~~Counter~~ | **Removed** | — | Automatic punish is via strike momentum when *you* attack into *their* recovery |

### AUT append

```text
next_ready = max(world_aut, current_next_ready) + reaction_aut_cost
```

(or equivalent scheduler helper). Same for Dodge and Block.

### Dodge outcomes (JSON; footwork-momentum adjusts)

Baseline weights (designer OK):

| Outcome | Weight |
|---------|--------|
| **Graze** | ~60% |
| **Full avoid** | ~30% |
| **Still connects** | ~10% |

Same-direction footwork momentum → more avoid; reverse → more connect/fail. AP-fail: cannot choose Dodge (option greyed or message).

### Block outcome

- Apply full brace cost/balance first (append AUT).
- Then resolve strike at reduced breakthrough (emergency cover); still may chip; narrative “barely get the shield up.”
- Stronger than Ignore; weaker than “this was only a chip jab all along.”

### Ignore outcome

- No emergency costs.
- High-momentum hit applies with **minimal** passive save — fantasy is the crisis already beat normal defense; Ignore accepts the trade.
- Passive shield may still flavor a partial take if we want a shred of always-defending, but **must not** make Ignore feel like free full block. Prefer: Ignore ≈ full crisis damage path; Block ≈ scramble save.

---

## 3. Passive defense (non-crisis)

When momentum is **below** Incoming threshold, warriors still **always defend as best they can**:

| Profile | Behavior |
|---------|----------|
| **Shield** | Majority of swings taken on shield → block prose + **chip** |
| **Weapon** (no shield) | Parry prose + chip |
| **Beast** | No true parry/shield; attacker gets beast momentum bonus; higher stamina in content; can **emergency dodge** only |

### Chip

- Fantasy: impact still jars the arm; not sustainable forever; **not** injury-level.
- Baseline small (about 1–2); **may scale slightly** with strike momentum so bigger swings chip a bit more, still capped so shield-tanking is attrition not nuke.
- Log: **state the block/parry only** — never “for 2.”

### Shield durability

Deferred.

---

## 4. Accuracy, fumbles, always-land

### Always accurate (default)

No classic accuracy-vs-evade **random miss** as the primary gate. Contact quality is **strike momentum + defense path**, not a coin flip.

### Fumble = overbalance only

- **Exclusive** cause of fumble: attacker balance too high (overextended region / fumble chance table by balance).
- Replaces the old “accuracy mult crash at +6…+10” as the player-facing explanation: *the attack was ineffective because balance was too high.*
- Checked **before** Incoming and before defense.
- Verbiage:
  - Player: **“You fumble your attack.”**
  - Other: **“{Name} fumbles their attack.”**
- Fumble never opens Incoming.

### Emergency dodge

Can still produce avoid / graze / connect — not a “fumble.”

---

## 5. Beasts and NPC emergency reactions

### Beast rules

| Rule | Detail |
|------|--------|
| Stamina | Generally **higher** max stamina in content |
| Weapon defense | Attacker gains **strike momentum bonus** vs beast (lack of defensive options) |
| Brace | **Cannot brace** (ready action `d` / AI brace illegal) |
| Emergency Block | **Cannot** — no Block option in their reaction sim |
| Emergency Dodge | **Can** — same footwork-like costs if they have AP; AUT append |
| Wrestle | Prefer higher stamina + momentum vuln for steel; main-stamina wrestle edge can ship with grapple hooks in same change if cheap, else follow content pass |

Data: `defense_profile: "beast"` (or `can_brace: false`, `can_emergency_block: false`, `beast_target_momentum_bonus`). **No** `if id == "wolf"`.

### NPC reaction simulation

Opponents facing a **breakthrough+** strike against them should **simulate** a response (not only the PC):

- Evaluate legal options: Dodge (if AP/tile), Block (if not beast), Ignore.
- Weights from AI personality (Ferocity/Cunning/Tenacity), remaining AUT, HP, plan.
- Beasts: Dodge vs Ignore only.
- Results use same cost/append rules as the player.
- Plan label updates (`dodging`, `blocking`, `tanking`, …).

PC still gets the **modal**; NPCs resolve instantly in sim.

---

## 6. Narrative combat log

### Rules

- **No damage numbers** in the action log.
- Intensity from **strike momentum tier** + defense outcome.
- Gameplay-critical lines in **`messages.py`** (tuned with systems).
- Flavor-only corpora (e.g. long vore narratives) stay **data-driven** as today.

| Tier / outcome | Voice examples |
|----------------|----------------|
| Chip / blocked | “Your thrust bounces off the gnoll’s shield.” |
| Light | “You jab the rat.” |
| Solid | “You bash the ogre.” |
| Heavy / devastating | “You beat the ogre like a drum!” |
| Fumble | “You fumble your attack.” |
| Dodge avoid | “…cuts empty air.” |
| Graze | “The blade kisses your shoulder as you slip aside.” |

Severity thresholds (numeric bands) may live in JSON; string templates in `messages.py`.

### HUD

Meters stay numeric (HP, AP, balance, debug momentum).

---

## 7. Opponent readout (always in the pit)

Always show focus foe while in match fight (solo: the enemy).

| Field | Default show |
|-------|----------------|
| Name | yes |
| Plan shorthand | yes |
| Balance meter | yes |
| Stamina cur/max | yes |
| Fer / Cun / Ten / App | yes |
| Strike momentum debug (last/pending factors + total) | yes (flag) |

Placement: status sidebar under player block.

Plan labels from last AI intent / reaction (`watch`, `brace`, `closing`, `feinting`, `attacking`, `ability`, `clinch`/`vore`, `retreating`, `shocked`, `dodging`, …).

---

## 8. AI posture (timid testing → commit)

| Goal | Detail |
|------|--------|
| Timid default | Back up, hold measure, feint more before committing |
| Low Ferocity | Hang back, defend, jab-level; punish rather than charge |
| Player closes fast | Prefer attack to punish entered measure (Ferocity scales boldness) |
| High Ferocity | More sudden commits, still not pure bump-bot |
| Beasts | No brace in candidate set; dodge-capable; appetite/clinch as today |

Weights in `match_ai.json`. Plan labels feed readout.

AI attack orders go through the **same strike momentum** pipeline as the player.

---

## 9. Abilities and “devastating” fantasy

- Abilities remain explicit spends (AP/AUT/balance).
- Their power is largely **strike momentum base** + situation (recovery punish), not a second hidden Counter command.
- Haymaker into a foe with huge remaining AUT + good attacker posture should reach **devastating** tier often — playtest numbers, not hardcoded 999.

Attrition: many chips on shield still win eventually.

---

## 10. Scheduling / edge cases

| Case | Rule |
|------|------|
| PC grappled / obscured | No Incoming stack |
| Dodge with insufficient AP | Option unavailable |
| Beast PC (if ever) | No Block/brace; Dodge/Ignore only |
| Multiple breakthroughs | Single pending reaction |
| Feint | Low/no steel momentum; no Incoming |

---

## 11. Testing strategy

- Pure unit tests for strike momentum factors, tiers, Incoming threshold, fumble table, AUT append, dodge weights, beast option filters.
- Session tests: jab-level no modal; recovery punish → Incoming; Ignore hurt vs Block save; narrative has no `\d+` damage tails.
- Manual checklists per PR.

---

## Resolved decisions

| # | Decision | Source |
|---|----------|--------|
| R1 | Counter **removed**; punish is automatic via strike momentum | Designer 2026-08-15 |
| R2 | **No** simple weak/strong tags alone — **strike momentum** from balance, measure, AUT recovery, ability, buffs/debuffs, beast, etc. | Designer |
| R3 | Attack order = smart arbitration; negative balance → basic attacks are jab-level expression | Designer |
| R4 | Incoming only for **breakthrough+** crises that beat normal defense | Designer |
| R5 | Dodge = **exact** 1-tile footwork (AP/AUT/balance); only diffs: usable off-turn/during cooldown; AUT **appends** | Designer |
| R6 | Block = **exact** emergency brace (same sliding costs) | Designer |
| R7 | Ignore free; crisis path (accept hurt to save AUT / slugfest) | Designer |
| R8 | Dodge outcomes ~60% graze / 30% avoid / 10% connect (footwork-momentum adjusts) | Designer |
| R9 | Fumble **only** from too-high balance; replaces accuracy reduction as the communication; never Incoming | Designer |
| R10 | Always land otherwise; no classic random miss | Designer |
| R11 | Chip small, slightly scales with momentum; not injury-high; log no numbers | Designer |
| R12 | Always-defending on non-crisis; crisis Ignore is not free full block | Designer |
| R13 | Beasts: higher stamina content, attacker momentum bonus, **no brace / no emergency block**, **can emergency dodge** | Designer |
| R14 | NPCs simulate emergency reactions | Designer |
| R15 | Gameplay log lines in `messages.py`; flavor corpora data-driven | Designer |
| R16 | Opponent panel **always** in the pit | Designer |
| R17 | Momentum factor breakdown debug on HUD for development | Designer |
| R18 | Shield durability deferred | Designer |
| R19 | PR order: agent efficiency (no designer sequencing) | Designer |

---

## Open questions (none blocking design)

Minor implementer choices (document in PR if interesting):

| # | Topic | Default if unspecified |
|---|--------|------------------------|
| I1 | Strike momentum scale (0–100 vs unbounded) | 0–100 with JSON weights |
| I2 | Whether abilities are forced-jab when balance &lt; 0 | **No** — only basic attack expression constrained; abilities stay explicit |
| I3 | Exact Ignore damage vs residual passive | Prefer **full crisis** damage path |
| I4 | Wrestle main-stamina for beasts in this change | Ship if grapple hook is small; else content follow-up |

---

## Implementation sketch (modules)

| Module | Responsibility |
|--------|----------------|
| `match_strike_momentum.py` (new) | Pure compute + tier + factor list; load weights from JSON |
| `match_combat_resolve.py` | Fumble; always-land; chip; no acc-evade primary |
| `match_tactics.py` | Reaction kinds without COUNTER; pending carries momentum result |
| `match_session.py` | Wire order of fumble → momentum → Incoming/NPC react → log |
| `match_ai.py` | Timid weights; beast no brace; NPC emergency sim |
| HUD helpers | Opponent block + optional momentum debug |
| `messages.py` | Narrative templates by tier/outcome |
