# Design: Gladiavore foundation

| Field | Value |
|-------|-------|
| **Author** | Lead designer + Grok (agent assists) |
| **Date opened** | 2026-07-16 |
| **Status** | Active — design phase; **no implementation until named PR authorized** |
| **Change name** | `gladiavore-foundation` |
| **Primary product** | Gladiavore (not K.D.'s Vore Roguelike) |
| **Last design intake** | 2026-07-16 (PR7 injuries + DESIGN_CANON.md consolidation) |
| **Permanent Q&A canon** | **`DESIGN_CANON.md`** (read after compact; do not re-ask locked decisions) |

**Terminology (mandatory):**

| Term | Meaning |
|------|---------|
| **Defeated** | Enemy reaches 0 stamina and is removed as a combatant under match rules |
| **Stunned / incapacitated** | Fighter at 0 **stamina HP** — exhausted, not lethally harmed |
| **Digested** | Permanent removal after engulf + digestion; **only** way the PC’s run ends; allies leave roster permanently |
| **Base stat / skill** | Unmodified trained value |
| **Actual** | Base ± all modifiers; **always** used in resolution |
| **AUT** | Arbitrary Unit of Time (DCSS-like energy/cooldown clock) |
| **Ally** | Combatant on the roster who fights in arenas until digested |
| **Service** | One-time purchased instant effect (heal once, one training session, etc.) |
| **Retainer** | Heavy up-front cost; recurring boon every fight or between fights for the rest of the run |
| **Grapple HP** | Wrestling durability in grapple; **snapshots current stamina** on grab; tracks with further stamina loss; swallow only at 0 |

Avoid *kill / die / death* in specs, UI, logs, and agent prose.

---

## 1. Vision

### 1.1 Elevator pitch

**Gladiavore** is a **fast career roguelike** set in **pure fantasy beast-pits**: larger-than-life animals, anthro gladiators, and grand creatures (dire wolves, gnolls, kobold packs, hydras, dragons, gryphons — **no humans**). You manage gold, a small roster, gear, and training between **curated arena matches**. Combat is **tactical and cinematic** (UnReal World–like play-by-play), runs on an **AUT time system**, and escalates hard: easy early, **match 4 already dangerous**, **~10 wins extraordinary**.

In **red** matches, every foe is **vore-capable**. Grapple is a real wrestling scene (grapple HP), not a single swallow roll. Once **engulfed**, useful options shrink hard (near game-over) but the **player always keeps AUT agency** — even useless actions remain choosable; the game **never** fully takes control away. The PC **never** vores; only **beast companion** allies may be vore-capable hires.

### 1.2 Design pillars

1. **Career over crawl** — Abstract downtime hub + match; no dungeon delve product loop.
2. **AUT first** — Actions cost recovery time until the *next* action; entities act when ready; **player wins ties**. Cooldown **never** means “cannot defend.” Sacred: tactical RPG pacing, not mash-to-attack.
3. **Every match is the set piece** — ~20×20 curated arenas; space, pushback, hazards (ZoC **not** MVP).
4. **Tactical give-and-take** — Staredowns, shield lines, feints, AP races, openings — not identical chip.
5. **Actions shape posture** — Balance integer from what you *do*; no stance toggles.
6. **Automatic best-effort fighting** — Hold = brace/turtle; move trades turtle for dodge; attack spends defense; no mode-boop.
7. **Stamina vs injuries** — Exhaustion ends many bouts; injuries are rare-ish severe-hit consequences; full stamina between matches.
8. **Vore is a crisis** — Grab → grapple HP war → engulf (near game-over) → digestion on AUT.
9. **Red preferred, green is mercy** — Same difficulty ramp; green under-pays so pure-green falls behind; red keeps gold on curve but punishes entering hurt.
10. **Roster as resource + story** — PC + up to **4** allies; deploy PC + up to **2**; gold refund ~70% of hire+training on digest (data/difficulty); “vore shield” play allowed.
11. **Player agency always** — At 0 stamina the PC can still talk and crawl; while engulfed the PC still picks actions on AUT (may be futile). **Never** a full soft-lock / cutscene-only state.
12. **Cinematic informational prose** — Impacts/near-misses in log; incoming attack in reaction modal — avoid triple-spam.
13. **Harvest, rebrand** — KDVR systems as parts; product is Gladiavore.

### 1.3 Explicit non-goals

- PC-initiated vore  
- Humans as cast  
- Tank-controls / facing minigame  
- Forced examine for critical info  
- Retirement from the games (once a gladiator, you’re in)  
- Upkeep taxes / forced gold loss  
- DF-level simulation  
- Renown as spendable currency  
- Crowd as MVP (stub only)  
- Gear upgrades as MVP (buy better is default)  
- Background-specific victory (long-term; MVP = high score / renown)

### 1.4 Inspirations

| Source | Take |
|--------|------|
| *We Who Are About To Die* | Career, training spend, patrons (thin), later background goals |
| *Battle Brothers* | Named roster, injuries matter |
| *DCSS* | AUT, `a`/`?` abilities, `T` talk patterns |
| *UnReal World* | Cinematic combat lines; optional attack-reaction modal |
| 7DRL shell | ASCII, turn/energy-based, top-down |

### 1.5 Text voice

- **Informational + slightly cinematic**  
- Combat: situation-dependent lines from roll outcomes (“Your sword clangs against the gnoll warrior’s shield”, awkward standoff when both flub)  
- **Not** bland “You miss.” / **Not** sports-announcer hype  
- Digestion flaunt: predator-centric, KDVR-like multiple unique lines per predator  

---

## 2. Product identity and KDVR relationship

### 2.1 Identity

| Item | Target |
|------|--------|
| Display name | **Gladiavore** |
| Package / entry | Rename in PR1 |
| User data | **Gladiavore** |
| Active change | `openspec/changes/gladiavore-foundation/` |
| Lineage doc | `KDVR_REFERENCE.md` |

### 2.2 KDVR strategy

Soft quarantine: harvest in place; `KDVR_REFERENCE.md`; eventually prune dungeon-only assets. Do not expand dungeon-delve features. Reskin KDVR creatures as early beasts/humanoids is **encouraged**.

### 2.3 Superseded

`balance-pass` and KDVR dungeon product direction — not active.

---

## 3. Career structure

### 3.1 Run loop

```text
New career (difficulty; background stub; start ally picks)
  → Downtime (“You have some downtime before your next match…”)
  → Pick match card (3 of N for this round)
  → Match (AUT combat)
  → After-action recap
  → Settlement (gold, renown score, injuries persist, roster changes)
  → …
  → PC digested → career over → high-score / renown
```

**Run ends only when the PC is digested.**  
No injury can prevent match participation (debuffs only).  
Player is **obligated** to take a match each round (no sitting out).

**MVP victory:** maximize **renown** (high score table).  
**Later:** background-specific goals (WWAATD-like). **No retirement.**

### 3.2 Pacing and difficulty ramp

| Milestone | Intent |
|-----------|--------|
| Matches 1–3 | Pretty easy; player should **generally not** lose 1–2 |
| Match 4+ | Threat if not paying attention; ramp keeps worsening |
| ~10 wins | **Extraordinary** achievement |
| Difficulties | Easier / Normal / Hard / Nightmare — **reimagine** for this style later |

### 3.3 Green vs red (economy of risk)

| | **Green** | **Red** |
|--|-----------|---------|
| Role | Mercy / heal-up when hurt | **Default** path (most rounds) |
| Availability | On **predefined rounds** only; more often on **Easier** | Most round card pools are **all red** |
| Difficulty ramp | **Same** opponent curve | Same |
| Rewards | Low; **not enough to keep up** if overused | Higher; pure-red gold **stays ahead of curve** |
| Vore | May grapple; **must release** before lethal digest; uninterested in finishing 0-HP swallows | Primary goal: **digest as many as possible** |
| Expected fail | Team incap / mid-match surrender | **PC digested** |
| Surrender | **Mid-match only** (no upfront forfeit); payout scales with show; deny if way too early | **No** (generally) |
| Entering hurt | Safer when injured | Red while injured can end poorly |
| Round clock | Advances on win/lose/draw/**surrender** | Advances on resolution |

### 3.4 Match cards (round offers)

- Designer authors a **premade pool per round** (e.g. 10 cards for round 2).  
- Each visit: present **3 random cards** from that pool.  
- Card fields (v1): opponent set, green|red, arena, **payout multiplier**, round band.  
- Patron objectives validated separately (never impossible); not necessarily authored on the card.  
- Opponents scale with **round index**.

### 3.5 After-action recap

After every match: major events, gold, renown, injuries, digestions, patron objective hit/miss. Ally digest listed factually; **no renown penalty**; **no ally emotional reactions**. Vore in red is **normal bloodsport**.

### 3.6 Crowd

**Mechanical force**, designed to matter (not tomato spam / easy max like weak WWAATD implementations). **Stub only; not MVP.**

### 3.7 Difficulties

Four tiers remain desired; numbers/feel reimagined when combat exists. Not blocking hub/match skeleton.

---

## 4. Downtime hub

### 4.1 Framing

Abstract menu, not a city map:

> “You have some downtime before your next match. Here are ways you can spend it.”

### 4.2 Actions

| Action | Notes |
|--------|--------|
| Shop (gear) | Shop-only acquisition; replace-by-buying-better; upgrades later non-MVP |
| Hire allies | Market; gold; some free/ultra-cheap scrubs |
| Services | One-shot: doctor heal, one training, beast trainer session, etc. |
| Retainers | Expensive permanent recurring boons |
| Manage loadout | Shared armory; outfit PC and employees |
| Training / perks | Permanent +1s; named abilities/passives; prereqs OK, not deep trees |
| Assign squad | Who enters next match vs rest |
| Select match | 3 cards for this round |

**No upkeep.** Gold only leaves by voluntary spend.

### 4.3 Economy feel

| Topic | Intent |
|-------|--------|
| Win payout | **Fast progression** — each win funds a **meaningful** upgrade of some kind |
| Green fail | Low appearance fee if performance is terrible |
| Injury heal | **Fairly expensive; often not worth it** (play around debuffs) |
| Hires | Wide band: worthless scrubs → quick learners → expensive finished goods |
| Bankruptcy | Cannot be force-drained; may be poor if you waste gold |

### 4.4 Patrons (thin)

- **Three** patrons early.  
- Objectives only: “do the thing → extra gold.”  
- Miss = **missed bonus only**.  
- More patronage systems later.

### 4.5 Background (stub)

- Eventually a **choice** with starting stat bonuses and long-term victory goals.  
- MVP: stub background; start by **picking 2 allies for free** from a **generated hire market** (not a fixed starter pair).

---

## 5. Roster and personnel

### 5.1 Taxonomy

| Term | Meaning |
|------|---------|
| **Ally** | Combatant; fights until **digested** by an enemy |
| **Service** | One-time instant bonus (heal once, single train) |
| **Retainer** | Permanent recurring boon for the run (e.g. post-fight heal every match) after heavy up-front cost |

Player hires **combatants** as allies. Medical/training purchases are services/retainers, not “allies.”

### 5.2 Caps

| Cap | Rule |
|-----|------|
| **Roster** | **PC + up to 4 allies** (5 combatants max on payroll) |
| **Match deployment** | **PC always** + up to **2 allies**; some cards force **solo** or **1 ally max** |
| **Bench** | Non-deployed allies rest |

### 5.3 Ally generation

- **Procedural** within **hire-tier archetypes** (scrub / quick learner / finished goods, etc.) on randomized ranges.  
- Randomized stats, species (anthro/beast), abilities, traits.  
- **Name** + mad-lib backstory: *Originally a [job] from [location] who became a gladiator because [reason].*  
- Investment: battle gains and upgrades **not freely re-bought as identical** → loss hurts **time/curation**.  
- **Gold compensation** on ally digest: about **70% of (hire price + training spent)** — tunable via **JSON / difficulty**. Does **not** resurrect them.  
- Emergent **“hire as vore shields”** is allowed and can be darkly funny.

### 5.4 Vore-capable allies

**Beast companions only** (tame/sapient vore monsters for hire). Ordinary anthro hires are not PC-side predators unless later designed otherwise.

### 5.5 Orders and obedience

- Default: **always obey**.  
- **Disobedient** trait: chance to ignore orders.  
- No ambient morale refusal without that trait.

### 5.6 Digest presentation

- Spotlight on **predator flaunt** text (≈6 unique lines per predator, KDVR spirit).  
- Recap lists the loss. Business as usual.

---

## 6. Loadout, skills, training

### 6.1 Gear rules

| Rule | Detail |
|------|--------|
| Between fights only | Equip in hub; **no mid-battle inventory browsing** |
| Exceptions mid-battle | Weapon/shield may be **disarmed / thrown** |
| Shield | **Distinct** item type; turtle/block behavior |
| Consumables | Strict loadout: throwables yes; buff potions maybe |
| Armory | **Shared**; player outfits whole roster |
| Shop | Only gear source |
| Upgrades | Optional later; not MVP |

### 6.2 Skill list (minimal)

Weapon / domain skills (specialization tradeoff: shiny weapon you don’t know vs solid weapon you do):

1. One-handed Swords  
2. One-handed Polearms  
3. One-handed Hafted  
4. Two-handed Swords  
5. Two-handed Polearms  
6. Two-handed Hafted  
7. Shields  
8. Wrestling  
9. **Physicality** (strength + agility umbrella; ties to stamina capacity)  
10. **Mentality** (battle tactics umbrella)

No dozen primary attributes beyond this skill set.

### 6.3 Training

- Buy permanent **+1s** on skills.  
- Learn **named abilities** and **passives**.  
- Prerequisites OK; **not** deep skill trees.  
- Shared PC ability pool; gated by level/stats and/or **which trainers appear** (spend now vs wait for preferred trainer).  
- Stamina max tied primarily to **Physicality**.  
- **No** multi-match fatigue layer beyond injuries.

### 6.4 Stamina between matches

**Always full refresh.** Injuries persist until healed (natural slow and/or expensive service).

### 6.5 Injuries (vague regions + severity — not gore)

**Tone:** Not a hospital sim and not a gore showcase. No visceral wound text, no clinical diagnoses, no blood-detail log spam. Injuries are **short labels** that mean **stat/skill penalties**.

**Display format (mandatory):**

```text
Injured {Region}: {Severity}
```

Examples: `Injured Arm: Minor`, `Injured Leg: Moderate`, `Injured Head: Major`.

**Severity tiers:** **Minor** / **Moderate** / **Major** only (no “critical/fatal” medical ladder).

**Regions (locked):** Arm, Leg, Head, Torso only.

| Region | Stat impact |
|--------|-------------|
| **Arm** | Accuracy + damage |
| **Leg** | Step AUT mult + evade |
| **Head** | Accuracy (focus) |
| **Torso** | Max stamina fraction + AC |

**Penalties:** Minor / Moderate / Major = **10% / 20% / 30%** (`data/injuries.json`).

**Aggravation:** Same region steps Minor → Moderate → Major (severe hits may step twice). Different regions stack.

**How they appear (unchanged philosophy):**

| Blow | Injury intent |
|------|----------------|
| Scratches / grazes | **Never** cause injury |
| Solid hit | Chance of **Minor** on a region, or **aggravate** existing on that region |
| Large chunk in one blow | Strong chance of **Moderate**, or **+1 severity** on an existing region |

**Rules:**

- Debuffs apply to **actual** stats immediately and **linger across matches**.  
- Stamina still **fully refreshes** between matches; injuries do not.  
- **Never** block match participation (debuffs only).  
- Healing: expensive hub service; natural slow heal optional later.  
- Log/UI: only the label + “performance is hindered” style if needed — **no** gruesome description.  
- Applies to PC and allies (allies show in roster status).

**Healing:** pay **per severity step** (JSON gold table). PC and allies.  
**Balance data policy:** all combat AUT/AP/power numbers in JSON (`match_combat.json`, `aut_costs.json`, `injuries.json`, `match_recovery.json`, etc.).

---

## 7. Combat systems

### 7.1 AUT (highest combat priority)

DCSS-style **Arbitrary Unit of Time** — this is a **tactical RPG** with a roguelike UI, **not** mash-bump combat.

**Clock rules**

- Each entity has a ready time after acting.  
- Actions resolve immediately, then impose **AUT cooldown** until that entity may issue another **command**.  
- Clock advances to the next ready entity.  
- **Player always wins ties.**  
- Everything slow and timing-based: swallow **multi-phase always**, on the order of **≥4–5 AUT per phase** (tunable, but “sizable”).

**Cooldown ≠ helplessness (critical)**

| Cooldown means | Cooldown does **NOT** mean |
|----------------|----------------------------|
| Time until you can issue the **next action** | Frozen / unable to defend |
| Recovery to neutral after a big swing | Automatic defense penalty |

**Defense is never modified by “being on cooldown.”**  
Overaggression may hurt defense via the **balance bar**.  
Individual **moves** may temporarily lower a shield or create a window (property of that move), but that is **not** a generic cooldown rule.

**Starting AUT cost table (defaults; data-driven later)**

| Action | AUT cost (intent) |
|--------|-------------------|
| Step (1 tile) | **0.4–0.5** |
| Wait / brace | ~1.0 |
| Weakest jab | ~1.0 (attacks are *at least* this) |
| Typical attack | **>1.0** (noticeably longer recovery) |
| Heavy / haymaker-class | Clearly longer — you do **not** axe-swing then instantly dance |
| Jump | Multi-tile; cost + short debuffs (not free) |
| Free Talk | **0 AUT** |
| Paid second talk (spends action) | ~0.5–1.0 (tunable) |
| Swallow phase (predator) | **≥4–5 AUT** per phase |

Fantasy: big attack commits you until you recover to act again; you are **not** a pinata for the whole cooldown solely because of the clock.

**Per-entity timing stats** (like KDVR Acc/Ev/AC/damage — **per entity definition**, not a blunt species global):

- Action speed / cooldown multipliers as needed  
- AP max and **AP recharge rate** (world-time based)

**AP regen:** on **world AUT** — default **+1 AP per 1.0 AUT** of world time, or per-entity rate (e.g. every **0.9 AUT**).  
**AP max** baseline ~10. Everyone has AP.

**Stunned / 0 stamina agency & recovery bank**

| Actor | At 0 stamina |
|-------|----------------|
| **PC** | Still acts on AUT: **talk**, **crawl** (step AUT × **3**), and recovery choices. Never fully locked out of input. |
| **NPC allies / enemies** | **Cannot act** (except as prey in swallow/digest pipelines handled by predator timing) |

**Recovery model (PC — and allies if/when mirrored later)**

Stamina still **regenerates over time** while down, but **displayed/usable HP stays 0** until the fighter **actively recovers**:

1. While incapacitated, the **AP meter is replaced by a Recovery bar**.  
2. Recovery bar fills with world time (rate TBD; data-driven).  
3. When the bank is **full**, the fighter may use a **Recover** action/ability → stand with **5 HP** and resume normal actions.  
4. **Recover is optional.** The player may **refuse** to stand (e.g. green match: “play dead,” let allies finish or take the loss) to avoid prolonging a hopeless fight and risking **injury**.  
5. Regenerating “more than 1 HP worth” before stand is required — the **5 HP on recover** is the design target (not auto-stand at 1).

**Second wind (special / once-per-match class)**

- Named ability or passive: tap **hysterical strength / willpower** to restore some stamina mid-crisis.  
- May apply a **debuff** (pushing through on fumes).  
- Frequency: once per match or similar gate (data).  
- Complements the recovery bank; does not replace it.

**Free Talk:** costs **0 AUT**. Free Talk buff **only returns after 1.0 AUT** of world time (not “once per player turn” in the classic sense).

> Implementation note: replacing KDVR’s player-then-monsters loop is foundational for MATCH.

### 7.2 Space and movement

| Topic | Rule |
|-------|------|
| Default arena size | **~20×20** |
| Move | **8-direction**; no facing |
| Facing | **None** |
| **ZoC** | **Not in MVP** (may return later) |
| Pushback | Common; typically **1–2 tiles** even when blocked on shield |
| Walls / hazards | Backed into wall/hazard is **bad**; knock into hazard deals extra |
| Reach | Spears: **+1 tile**; throwables exist |
| Jump (`J`) | Multi-tile; short debuffs; can clear pits/hazards |

**Flanking (no facing gotchas)** — bonus from **angular separation** of attackers on the same target:

| Separation | Effect |
|------------|--------|
| **45°** | **Penalty** (attackers interfere with each other) |
| **90°** | Bonus |
| **135°** | Bigger bonus |
| **180°** | Biggest bonus |

### 7.3 Balance meter (sliding scale)

| Property | Rule |
|----------|------|
| Type | Integer; **0 = ideal center** |
| Negative | More defensive / turtle posture |
| Positive | More aggressive / overextended |
| Sources | Actions only (no stance toggle) |
| Hold still | Shifts **defensive** (brace/turtle — not “noop”) |
| Bump attack | Shifts **aggressive**; attack chains grow reckless |
| Specials | Each ability tilts per its data |

**Reward shape (critical)**

- System **rewards staying near 0**, with room for **moderate** lean either way.  
- **Moderate** aggression or defense can be **beneficial to a degree** (commits that match the moment).  
- **Far extremes stack penalties rapidly**:

| Extreme | Intent |
|---------|--------|
| **Overextended (+)** | **↓ accuracy, ↓ defense, ↑ damage dealt** — wild swinging; hard to land through a solid guard; easy to get **counterattacked**. Deterrent to pure attack-attack-attack. |
| **Cowering (−)** | Stats also **suffer** — pure endless shield-hide is **not** optimal; defense erodes when you never contest. |

Exact breakpoints/curves are data later; philosophy is **sweet spot near neutral**, soft benefits mid-band, hard punish at extremes.

**AI implication:** enemies play **imperfectly** by **personality**, not optimal theory. They over-attack or over-turtle on purpose so a balanced PC can **pick gaps**. Player should not face perfect robots.

### 7.4 Automatic defense posture (no stance toggle)

The fighter always tries to carry out orders **well**, but is not a mode-switch robot:

| Behavior | Effect (intent) |
|----------|-----------------|
| Passing / holding | Brace, raise guard, turtle |
| Moving | Less turtle, more dodge; lots of movement **tires** (stamina) |
| Attacking | Penalizes defense |
| Abilities / items | Per definition |

Fantasy: staredown, circle, feint, spend AP, race recharge — not boop-berserk.

### 7.5 Smart bump / awareness (behind the scenes)

Bump is **not** one fixed attack profile. A hidden **awareness / vulnerability** score (from measurable factors: turtle level, distraction, flank, grapple, low stamina, etc.) selects profile:

| Situation | Bump tends toward |
|-----------|-------------------|
| Target highly distracted / opened | All-out |
| Target full turtle | Jab / feint |

Exact formula later; principle locked.

### 7.6 Openings, counters, and strategy rock-paper-scissors

Every durable strategy needs a **counter**. Examples of intent (not full matrix yet):

| Strategy | Counter fantasy |
|----------|-----------------|
| Heavy turtle / giant shield | Hook Shield, shield-line disruption, push to wall/hazard |
| Pure mobility / kiting | Leg attacks, snares, space denial |
| Reckless power | Punish windows; other attackers exploit balance |
| Creating openings | Dedicated abilities exist to **make** targets open |

Awareness inputs include: turtle level, distraction, flank, low stamina, recovery after big move, knockdown, and **recently countered**.  
**Vague reads** (“Open / Guarded / Turtle”-class) appear on the **right-hand enemy bar** — not exact STS intents.

### 7.7 Knockdown / shove

- Push **1–2 tiles** typical.  
- Severity of being down scales with shape (AP, injuries, stamina).  
- Healthy shove ≠ disaster; beaten-up + wrestling can be dire.

### 7.8 Reaction modal (every incoming attack on PC)

On **every** attack targeting the PC, present a reaction choice (URW-like):

1. **Dodge** — **8-way** direction keys; destination tile must be **open** (not solid, not occupied by NPC). Invalid direction rejected / not selectable.  
2. Parry/Block  
3. Counterattack  
4. Ignore  

**Fatigue from reactions:** constant dodging is costly; fine vs one foe, **very taxing vs three** (swarm pressure). Exact stamina/AP drain TBD; principle locked.

**Log vs modal split (anti-spam)**

| Channel | Content |
|---------|---------|
| **Reaction modal** | Incoming action (“The gnoll swings its axe at you!”) |
| **Message log** | **Impacts and near-misses only** (“Sparks fly as the gnoll's axe rakes across your shield!” / dodged) |

**Do not** dump start-attack + raise-shield + bounce as three log lines.

### 7.9 Damage model

- Primary: **stamina** damage; bouts often end by **exhaustion**.  
- Temp effects (poison etc.) as temporary stat/stamina drains OK.  
- **Injuries** from big single hits (see §6.5).  
- No gore-cut-out visceral weapon fantasy.

### 7.10 Seed abilities (PC kit examples)

| Ability | Intent |
|---------|--------|
| **Haymaker** | Dump defense; explosive all-in. High risk/backfire unless target disadvantaged; needs more AP to be truly effective; desperation OK |
| **Shield push** | Knockback + brief immobilize; hazard/wall damage; better vs turtle |
| **Hook Shield** | Hook weapon around their shield; better the more they turtle |

Plus personal kit + learned moves from trainers over the career.

### 7.11 Talk (`T`) flow

1. `T` → Talk modal  
2. Which ally? (1 / 2 / both)  
3. What order? (list)  
4. If needs target → KDVR-style cyan-X cycle targeting; Enter confirms  

**v1 orders:** **Attack** (favor poking/aggression) and **Defend** (favor turtle/protect).  

**Economy:** Talk costs **1 AP**. **Free Talk** buff: first talk **0 AUT** and does not consume the action; buff **returns only after 1.0 AUT** world time. A second talk before refresh consumes the action (AUT cost). Allowed while grappled / low stamina under same rules.

### 7.12 Targeting / examine / intent UI

| Feature | Rule |
|---------|------|
| Target cycle | Cyan X; Enter confirm (harvest KDVR ranged targeting) |
| Examine | Flavor + useful description; **never required** for critical mechanics |
| Enemy mood | Vague category (e.g. Scared → more evasive pool), **not** STS exact intent icons |
| AP / balance | **Meter art** preferred |
| Log | Cinematic play-by-play lines |

### 7.13 Player body

Always ambiguous anthro **`@`**: head, torso, shoulders, arms, legs, hands, feet assumed. No further mandatory species traits on PC.

### 7.14 Content cast

- **No humans.**  
- Early: dire rats, weak kobolds (knives/clubs), etc.  
- All enemies **vore-capable, period.**  
- Reskin KDVR entities freely for early content.

---

## 8. Grapple and vore

**Stub early, expand later** — a real grapple system is required; v1 may be oversimplified. Must not be a surprise when depth is added.

### 8.1 Who

| Actor | Vore? |
|-------|--------|
| PC | **Never** initiates |
| Anthro allies | No (default) |
| Beast companion allies | May be vore-capable |
| All enemies | Yes — **every** enemy is vore-capable |

Content prefs: OV/CV/AV toggles; **cannot disable all three**.

### 8.2 Grab and 0-stamina swallow

- Grab succeeds → **grapple state** (not instant swallow), except:  
- **Red + victim at 0 stamina:** no grapple war required; **swallow phases may begin immediately** (still multi-phase, slow AUT).  
- Healthy high-Wrestling targets should usually break free; grappler specialists test Wrestling.  
- Opposed Wrestling / grip math: **stub simply at first**; fair system needs dedicated design pass later.

### 8.3 Grapple HP

- On grab: **grapple HP = current stamina**.  
- Further **stamina damage while grappled also reduces grapple HP** (pools move together).  
- Predator goal: grapple HP → **0**, then multi-phase swallow.  
- Prey stub options: **break away**, **counter-strike**; richer maneuvers later.  
- Avoid one always-correct button long-term.

### 8.3b Grapple scene isolation (fairness / cinema)

A grapple is a **owned scene**, not a free multi-hit pile-on:

| Rule | Detail |
|------|--------|
| Prey hit sources | **Only** the current predator may damage the prey (crush/secure/digest pipeline). Other attackers cannot land damage on obscured prey. |
| Enemy allies of predator | **Do not** target or swing at the prey (risk of poking their own larger ally; prey is wrapped/obscured). They may wait or seek free targets. |
| Prey-side allies | **May and should** hit the predator (large target; rescue motivation). Assist damage can force release. |
| PC input | While PC is prey, **grapple options own input** — reaction modal does not stack on top of grab. |
| Design intent | Cinematic 1vX is possible because the X are **not a hive mind** and get in each other's way. Unfair “grappled *and* free attacks you can't defend” is forbidden. |

### 8.4 External help

Ally damage can force release if threat is real; token pokes on dragons do nothing.

### 8.5 Engulfed (second phase)

- Options become **low-percent / often useless** — but **PC still chooses actions on AUT**.  
- Miracle escape: critically hurt predator, belly injury/queasiness, or timely **forced regurgitation** by allies.  
- **No cutting out.**  
- Digestion: drain remaining stamina, then AUT strike timer.  
- Engulfed ≈ game over short of miracle **without** removing input.

### 8.6 Green vs red (0 HP and vore)

| | **Green** | **Red** |
|--|-----------|---------|
| Enemy goal | Win the bout; **not** permanent digest | **Digest as many as possible** |
| 0 HP allies | Effectively **removed / irrelevant**; enemies uninterested in swallow; **must regurgitate** before lethal digest | **Vore magnets**; swallow phases can start **without** grapple |
| 0 HP PC | Still crawls/talks; never removed by damage alone | Same agency; high swallow risk |
| Enemy 0 HP | **Defeated and removed** | Defeated and removed; recap may say beast ally **devoured** fallen foes for flavor |

### 8.7 Match cards & rounds (combat-adjacent)

- **Most rounds are all-red.** Green cards on **predefined rounds**; more frequent on **Easier**.  
- Card fields: opponent set, green/red, arena, **payout multiplier**, round band; patron objectives **sanity-checked** separately (not necessarily card-authored).  
- Round advances on green **win, lose, draw, or mid-match surrender**.  
- Surrender is **mid-match only** (fight a bit, then cry off) — **no pre-match forfeit**.

---

## 9. PR plan (updated emphasis)

### PR1 — Re-identity + agent reference

Branding, user data, `KDVR_REFERENCE.md`, AGENTS/README. No combat rewrite.

### PR2 — Career shell + downtime hub (stub)

Abstract downtime copy; gold/renown; stub shop/hire/train/assign; **round card picker stub** (3 of N).

### PR3 — Match vertical slice + **AUT core**

One ~20×20 curated arena; **AUT scheduler** (player tie priority); step ~0.4–0.5 AUT; attacks ≥1.0 with heavier >1.0; cooldown never applies generic defense penalty; win by defeating foes; recap stub; hub return.  
*AUT is foundational — not optional flavor.*

### PR4 — Combat skeleton (AP world-time regen, balance, abilities UX, meters)

AP max ~10; regen per world AUT; balance from hold/attack/specials; skills actuals; `a`/`?`; seed abilities stub; enemy bar vague reads stub.

### PR5 — Pushback, flanking angles, reaction modal, log/modal split

Push 1–2; flank table; every-hit reaction with directional dodge + fatigue principle; anti-spam logging. **No ZoC.**

### PR6 — Allies, Talk, roster PC+4 deploy PC+2

Hire tiers; ~70% refund stub; Attack/Defend orders; Free Talk 0 AUT / refresh 1 AUT.

### PR7 — Injuries by severity + services/retainers hooks

### PR8 — Grapple/vore stub (expandable)

Grapple HP = current stamina; multi-phase swallow ≥4–5 AUT; red 0-HP magnets; green release rules; PC agency always; fair Wrestling math may stay crude.

### PR9 — Match cards + economy + green surrender

JSON card catalog; 3-of-N offers; green rounds filter; economy bases; mid-match green surrender with early deny + scaled payout.

### PR10 — Thin patrons (3) + objectives

Three patrons; one sanity-checked objective per match; gold bonus on hit; miss = no bonus only.

### PR11+ — Crowd, difficulties, ZoC revisit, counter matrix depth, prune KDVR

*(Numbering may flex; **do not implement without named auth**.)*

---

## 10. Resolved decisions (cumulative)

> **Canonical permanent copy:** [`DESIGN_CANON.md`](./DESIGN_CANON.md) — full Q&A record for post-compact sessions.  
> This table is a compact index; prefer DESIGN_CANON when in doubt.

| # | Topic | Decision |
|---|--------|----------|
| 1 | Setting | Pure fantasy beast-pits; anthros/animals/grand beasts; **no humans** |
| 2 | Prose | Informational + slightly cinematic; URW-like combat lines |
| 3 | Background | Stub now; choice later; **no retirement**; background victory long-term |
| 4 | Hub | Abstract downtime menu |
| 5 | Crowd | Mechanical, meaningful; **stub, not MVP** |
| 6 | Pacing | Easy 1–3; threat 4+; ~10 wins extraordinary |
| 7 | Green/red economy | Same ramp; green under-rewards; red preferred; hurt+red risky |
| 8 | Match offers | Premade per-round card pools; show **3** random |
| 9 | MVP end | High score / renown; only **PC digest** ends run |
| 10 | Must fight | Always participate; injuries never bench |
| 11 | Difficulties | Four tiers; reimagine later |
| 12 | Start | Select a couple allies; background may vary later |
| 13 | Ally/Service/Retainer | Taxonomy locked |
| 14 | Ally gen | Procgen stats/species/abilities + mad-lib story |
| 15 | Ally loss | Gold infusion; investment time hurts; vore-shield OK |
| 16 | Obedience | Always; **Disobedient** trait exception only |
| 17 | Digest social | Predator flaunt; recap; no renown hit; no ally drama |
| 18 | Roster | **PC + 4 allies** max; deploy **PC + 2** (some cards solo/1-ally) |
| 18b | Digest refund | ~**70%** of hire+training; JSON/difficulty tunable |
| 18c | Hire tiers | Archetypes on random ranges (scrub / learner / finished) |
| 19 | Costs | Hire+heal+gear; no upkeep |
| 20 | Inventory | Hub loadout; disarm/throw only mid-fight |
| 21 | Shield | Distinct type |
| 22 | Consumables | Strict; throwables yes |
| 23 | Gear source | Shop only; upgrades non-MVP |
| 24 | Armory | Shared |
| 25 | Skills | 8 weapon/shield/wrestle + Physicality + Mentality |
| 26 | Training | +1s, abilities/passives; trainer availability tradeoff |
| 27 | Stamina max | Tied to Physicality |
| 28 | Fatigue | Injuries only |
| 29 | Arena size | ~20×20 start |
| 30 | Move | 8-dir; no facing; strong opposite-side flanking |
| 31 | ZoC | **Not MVP** |
| 31b | Push | 1–2 tiles; walls/hazards matter |
| 31c | Flank angles | 45° penalty; 90/135/180 rising bonus |
| 32 | Reach | Spears +1; throwables |
| 33 | Time | **AUT** sacred; player wins ties; slow tactical pacing |
| 33b | Cooldown | Next-action recovery only; **never** generic defense penalty |
| 33c | AUT defaults | Step 0.4–0.5; jab ~1.0; heavier attacks longer; swallow phase ≥4–5 |
| 33d | Speed stats | Per-entity (not pure species blanket) |
| 33e | AP regen | World AUT (default +1 / 1.0 AUT); per-entity rate OK |
| 33f | 0 stam PC | Talk + crawl (**3×** step AUT); NPCs at 0 cannot act |
| 33g | Recovery bank | While down: AP UI → Recovery bar; full bank → optional **Recover** → **5 HP** stand; may refuse (play dead) |
| 33h | Second wind | Once/match-class willpower recover; may debuff |
| 33i | Dodge | 8-way into **open** tile only |
| 33j | Start allies | Pick **2 free** from generated market |
| 33k | Balance curve | Reward near 0; moderate lean OK; extremes punish (overext: −acc/−def/+dmg; cower: stats suffer); imperfect personality AI |
| 34 | Reaction modal | **Every** incoming attack; directional dodge; multi-dodge fatiguing |
| 35 | Smart bump | Awareness-driven jab vs all-out |
| 36 | Hold still | Turtle, not noop |
| 37 | Balance hooks | Hold def; attack agg; specials per-move |
| 38 | Extremes | Penalties later |
| 39 | Knockdown | Situational severity |
| 40 | Turtle break | Push/hook/space/hazard — not just DPS |
| 41 | Counter/AoE | Especially vs weak swarms |
| 42 | Damage | Stamina primary; injury on big hits |
| 43 | AP | ~10 max, ~1/turn regen baseline; all entities |
| 44 | Kit | Signature + learned; Haymaker, Shield push, Hook Shield |
| 45 | Jump | Multi-tile + short debuffs; hazard vault |
| 46 | Talk UX | Ally → order → target; Attack/Defend first |
| 47 | Free Talk | 0 AUT; buff returns after **1.0 AUT**; second talk spends action |
| 48 | Grapple HP | = **current stamina**; falls with further stamina damage |
| 48b | Swallow | Multi-phase **always**; ≥4–5 AUT/phase; red 0-stam skips grapple war |
| 48c | Grapple math | Stub first; deepen later (expected) |
| 49 | Engulfed | Low-value actions remain; **never** full input lock; rare regurg; no cut-out |
| 50 | Digestion | Drain HP then AUT strikes |
| 50b | Green/red 0 HP | Green: allies irrelevant / must regurg; red: vore magnets |
| 50c | Enemy 0 HP | Defeated removed; recap flavor for beast devour optional |
| 50d | Cards | Mostly red; green on set rounds; payout mult; round always advances |
| 50e | Surrender | Green mid-match only; no upfront forfeit |
| 50f | Log split | Modal = incoming; log = impact/near-miss only |
| 50g | Start fantasy | Everyperson gladiator; sword+shield first; pick weapon later |
| 50h | Agency | **Never** fully remove player control |
| 50i | Wave 3 | Dodge 8-way open; crawl 3×; free market 2; recovery bank + optional stand; balance sweet-spot curve |
| 50j | Injury presentation | Vague `Injured {Region}: {Minor\|Moderate\|Major}` only; no gore/diagnosis; maps to stat loss |
| 50k | Injury regions | Arm, Leg, Head, Torso only; 10/20/30% in JSON; PC+allies; heal per step |
| 50l | Combat numbers | Abilities + basic maneuvers fully data-driven in JSON |
| 51 | Ally vore | Beast companions only |
| 52 | Content prefs | OV/CV/AV toggles; not all off |
| 53 | Green loss | Incap / surrender (scaled); no full digest |
| 54 | Red loss | Digest expected |
| 55 | Surrender | Green only; early deny / payout cut |
| 56 | Stamina refresh | Full between matches |
| 57 | Patrons | 3; objectives; miss = no bonus |
| 58 | Progression speed | Fast; win → meaningful buy |
| 59 | Heal price | Expensive, often skip |
| 60 | Hire band | Scrubs ↔ learners ↔ finished |
| 61 | Examine | Flavor; not required for crit info |
| 62 | Intent UI | Mood category, not exact intent |
| 63 | Meters | Art meters preferred |
| 64 | PC glyph | Ambiguous anthro `@` |
| 65 | Early foes | Rats/kobolds; all vore-capable; reskin KDVR OK |
| 66 | Cut policy | Cut dominant single-option strategies; keep tactical stare-down fantasy |
| 67 | Sacred | **AUT above other combat ambitions** |

---

## 11. Open questions (deferred / not blocking)

| ID | Topic | Status |
|----|--------|--------|
| Q-GRAPPLE-MATH | Fair opposed Wrestling / grip / breakaway economy | Stub first; dedicated pass later |
| Q-DODGE-COST | Exact stamina/AP drain for directional multi-dodge | Principle locked; numbers later |
| Q-HEAVY-AUT | Exact haymaker / power attack AUT table | “Clearly > jab” locked |
| Q-ZOC-LATER | Whether ZoC returns after MVP | Deferred |
| Q-COUNTER-MATRIX | Full ability counter web | Progressive content |
| Q-RECOVERY-RATE | How fast Recovery bar fills (AUT) | Data later; structure locked |
| Q-SECOND-WIND | Exact HP restored + debuff | Data later; structure locked |
| Q-BALANCE-CURVE | Numeric breakpoints for moderate vs extreme | Data later; shape locked |
| Q-ALLY-RECOVERY | Do allies use same recovery bank UI/rules? | Default yes when implemented; confirm later |

---

## 12. Contradiction / ambiguity check (wave 2)

| Item | Resolution |
|------|------------|
| Roster “4” vs “PC+2” | **PC + 4 allies** on roster; **PC + 2** in match (not “4 including PC”) |
| ZoC wanted vs cut | **No ZoC in MVP** (was aspirational; cut for MVP) |
| “Nearly helpless” engulfed vs always agency | Helpless in **effectiveness**, not in **input** |
| Cooldown vs defense | Explicitly **decoupled**; only move-specific windows or balance bar |
| Green surrender vs must participate | Must enter match; may surrender **mid-fight** only |

No remaining hard self-contradictions in designer answers after these fixes.

---

## 13. Document history

| Date | Note |
|------|------|
| 2026-07-16 | Foundation opened. |
| 2026-07-16 | Wave-1 Q&A integrated. |
| 2026-07-16 | Wave-2 integrated: AUT costs & cooldown≠defense, PC+4 roster, 70% refund, no ZoC MVP, flank angles, reaction/dodge fatigue, grapple HP=current, multi-phase swallow, always agency, prose split, injury severity. |
| 2026-07-16 | Wave-3: 8-way open dodge; crawl 3× AUT; start pick 2 free from market; recovery bank + optional Recover to 5 HP + second wind; balance sweet-spot curve + imperfect AI. |
| 2026-07-16 | Injury design: vague region+severity labels only; no gore; logical stat loss; catalog draft in §6.5. |
| 2026-07-16 | **DESIGN_CANON.md** created — permanent consolidation of all designer Q&A through PR7. |
| 2026-07-17 | Grapple scene isolation: prey only hit by current predator; no reaction stack while held; enemy pack hesitates on obscured prey; rescuers hit predator (§8.3b). |
