# Gladiavore — design canon (permanent Q&A record)

**Purpose:** Survive conversation compaction and new agent sessions.  
**Do not re-ask the designer** for anything listed here unless they explicitly reopen a topic.

| Field | Value |
|-------|--------|
| **Product** | Gladiavore (not K.D.'s Vore Roguelike) |
| **Change** | `openspec/changes/gladiavore-foundation/` |
| **Also see** | `design.md` (full narrative design), `proposal.md`, `tasks.md`, `KDVR_REFERENCE.md`, `AGENTS.md` |
| **Last consolidated** | 2026-07-17 (battle-pace program + prior foundation) |

---

## 1. Product identity

| Decision | Detail |
|----------|--------|
| Name | **Gladiavore** |
| Lineage | This repo began as a **clone** of KDVR; original game is safe elsewhere; this tree is fully writable |
| Reuse | Harvest systems; do **not** keep dungeon-delve as the product loop |
| User data | `%LOCALAPPDATA%\Gladiavore\` (env `GLADIAVORE_USER_DATA_DIR`) |
| UI fonts | **Map tiles + entity glyphs only** = fixed-width; **everything else** = log font (Source Sans / proportional) |

---

## 2. Fantasy & presentation

| Decision | Detail |
|----------|--------|
| Setting | Pure fantasy **beast-pits**: larger-than-life animals, anthro animals, grand creatures (dire wolves, gnolls, kobolds, hydras, dragons, gryphons…) |
| Humans | **None** in the cast |
| PC body | Ambiguous anthro `@`; head/torso/shoulders/arms/legs/hands/feet assumed only |
| Prose | Informational + slightly cinematic; UnReal World–style combat lines (“sword clangs against shield”), not bland “You miss,” not sports announcer |
| Combat log vs modal | **Modal** = incoming attack (“swings at you!”); **log** = impacts and near-misses only (no triple-spam) |
| Match HUD layout | **Status** right of map (HP/AUT/AP/balance/meta); **action log** bottom only; **reaction modal** dedicated low-right panel (see `match-hud-ux`) |
| Ally bump | No-op (no AUT); `"{Name} is standing there."` |
| Examine | Flavor + useful description; never required for critical info |
| Enemy intent UI | Vague mood category (e.g. Scared), not Slay-the-Spire exact intents |
| Meters | Prefer meter art (ASCII meters OK as stub) |
| Content prefs | OV/CV/AV toggles like KDVR; cannot disable all three |
| AV scope | Clean project rules (engulfment / abdominal crushing only unless designer expands) |

---

## 3. Career structure (WWAATD-inspired)

| Decision | Detail |
|----------|--------|
| Run type | **Career roguelike** until PC is **digested** (primary end) |
| Retirement | **None** once a gladiator |
| Background | Choice later (stat bonuses + long-term victory goals); stub OK; **no** background victory required for MVP |
| MVP victory / score | High score table via **renown** (score only, not spendable currency) |
| Hub | **Abstract** downtime menu: “You have some downtime before your next match…” |
| Crowd | Mechanical force intended; **stub, not MVP**; must matter more than tomato spam if added |
| Patrons | **3** early; thin: random-style objectives for extra gold; miss = missed bonus only |
| Difficulties | Easier / Normal / Hard / Nightmare — **reimagine** later for this style |
| Pacing | Matches 1–3 easy; **match 4+** dangerous if careless; **~10 wins extraordinary** |
| Must fight | Obligated every round; **no** sitting out |
| Injuries | Never prevent match entry (debuffs only) |

### Green vs red

| | Green | Red |
|--|-------|-----|
| Role | Mercy / heal-up; **under-rewards** so pure-green falls behind curve | Default ambitious path; pure-red gold **stays ahead** |
| Difficulty ramp | **Same** opponent curve as red | Same |
| Availability | On **predefined rounds**; more on Easier | **Most rounds all-red** |
| Vore / digest | Control grabs OK; **must release** before lethal digest | Full grapple → swallow → digest stakes |
| Expected fail | Team incap / mid-match surrender | **PC digested** (when grapple ships) |
| Surrender | **Mid-match only**; no upfront forfeit; payout scales with show; deny if way too early | Generally **no** |
| Nonlethal loss | Still **appearance fee + battle XP** | — |
| Ally at 0 HP | Down for bout; survives roster (green) | Vore magnet / digest permanent (when shipped); PR6 stub: red ally down = roster loss + refund |

### Match cards

- Designer authors **premade pool per round** (e.g. 10 cards for round 2).  
- Each visit: show **3 random** cards from that pool.  
- Card ≈ opponent set + green/red + arena + **payout multiplier** + round band.  
- Round clock advances on win/lose/draw/**surrender**.

### Economy feel

| Topic | Decision |
|-------|----------|
| Wins | Fast progression — each win should fund a **meaningful** upgrade |
| Gear | **Shop-only**; replace by buying better; upgrades non-MVP |
| Renown | **Score only** |
| Heal | Injuries only; **expensive, often not worth it** |
| Hires | Wide band: scrub / learner / finished |
| Upkeep | **None** — gold only leaves by voluntary spend |
| Ally digest refund | ~**70%** of hire + training (JSON/difficulty tunable) |

---

## 4. Roster & personnel

| Decision | Detail |
|----------|--------|
| Taxonomy | **Ally** = combatant; **Service** = one-shot; **Retainer** = permanent recurring (heavy upfront) |
| Roster size | **PC + up to 4 allies** |
| Match deploy | **PC always + up to 2 allies**; cards may force solo / 1-ally |
| Start | Pick **2 free** from generated market (starter gate) |
| Ally gen | Procgen: stats, species, tier, mad-lib backstory |
| Hire | Gold market; some free/ultra-cheap |
| Obedience | Always obey unless **Disobedient** trait |
| Ally vore-capable | **Beast companions only** |
| Digest social | Predator flaunt (~6 lines); recap lists loss; **no** renown penalty; **no** ally drama |
| Vore-shield hiring | Emergent dark comedy **allowed** |

---

## 5. Loadout & skills

| Decision | Detail |
|----------|--------|
| In-match inventory | **No** bag browsing; hub equip only |
| Mid-match | Weapon/shield may be disarmed/thrown |
| Shield | **Distinct** item type (turtle/block) |
| Consumables | Strict loadout; throwables yes; potions maybe |
| Armory | **Shared** — player outfits whole roster |
| Skills | One-handed / two-handed × Swords, Polearms, Hafted; **Shields**; **Wrestling**; **Physicality**; **Mentality** |
| Training | Permanent +1s; named abilities/passives; prereqs OK; not deep trees; trainer availability tradeoff |
| Stamina max | Tied to Physicality |
| Between-match stamina | **Always full refresh** |
| Fatigue | **Injuries only** (no multi-match fatigue layer) |

---

## 6. Combat philosophy (tactical RPG, roguelike UI)

### Sacred / first principles

| Decision | Detail |
|----------|--------|
| AUT | **Sacred** — DCSS-like energy; player **wins ties**; slow, timing-based |
| Cooldown | Time until **next command only**; **never** generic defense penalty from cooldown |
| Stance toggles | **Forbidden** — balance from **actions**, not boop modes |
| Base vs actual | Resolution **always** uses actual stats (after buffs/injuries/balance) |
| Damage | Primary = **stamina**; bouts often end by exhaustion |
| PC removal | Digestion only (not 0 HP) |
| PC vore | **Never** |
| All enemies | **Vore-capable, period** |
| Agency | Player **always** has some action choice (even useless); never full cutscene soft-lock |

### AUT / AP defaults (data-driven; tune in JSON)

| Topic | Decision |
|-------|----------|
| Step AUT | ~0.4–0.5 |
| Wait AUT | ~1.0 |
| Weak jab | ~1.0 floor for attacks |
| Heavier attacks | Noticeably longer AUT |
| Swallow phase | Multi-phase always; **≥4–5 AUT** per phase |
| AP | ~10 max; regen ~+1 per 1.0 world AUT (everyone has AP; rates may differ) |
| Speed | **Per-entity** stats, not blanket species globals |
| Crawl | 0 HP step AUT × **3** |
| Free Talk | **0 AUT**; free again after **1.0 AUT**; paid second talk uses AP + spends turn |

### Balance meter

| Decision | Detail |
|----------|--------|
| Type | Integer; **0 = ideal** |
| − | Defensive / turtle |
| + | Aggressive / overextended |
| Hold still | Brace/turtle (not noop) |
| Attack | Shifts aggressive; chains grow reckless |
| Specials | Each ability has balance delta in data |
| Sweet spot | Reward near 0; moderate lean OK; extremes punish hard |
| Overextended | −accuracy, −defense, **+damage** |
| Cowering | Stats also suffer (pure forever-turtle bad) |
| Enemy AI | **Imperfect**, personality gaps — not optimal robots |

### Space

| Decision | Detail |
|----------|--------|
| Arena | Curated ~**20×20**; little procgen |
| Move | 8-direction; **no facing** |
| Flanking | 45° penalty; 90 / 135 / 180 rising bonus |
| ZoC | **Not MVP** |
| Push | 1–2 tiles; wall impact hurts |
| Reach | Spears +1 tile later; throwables yes |
| Jump (`J`) | Multi-tile + short debuffs; vault hazards (later if not shipped) |

### Reaction modal (every attack on PC)

1. Dodge (8-way, open tile only; fatigue scales with multi/repeated dodge)  
2. Parry/Block  
3. Counterattack (esp. valuable vs swarms)  
4. Ignore  

### Smart bump

- Hidden awareness/openness → **jab** vs turtle, **all-out** if open, else standard.  
- Turtle break via push/hook/space — not pure DPS.

### Abilities (seed)

- DCSS-like `a` + letter; `?` full list  
- Haymaker, Shield Push, Hook Shield (numbers in JSON)  
- Signature kit + learned moves over career  

### Talk (`T`)

- Ally 1/2/… or all → **Attack** / **Defend** orders (AI priorities, not full puppet control)  
- Free Talk rules as above  

---

## 7. Injuries (PR7 design)

| Decision | Detail |
|----------|--------|
| Tone | **Not** gore / hospital diagnosis |
| Format | `Injured {Region}: {Minor\|Moderate\|Major}` |
| Regions | **Arm, Leg, Head, Torso** only (no Hand) |
| Penalties | **10% / 20% / 30%** in `data/injuries.json` |
| Who | **PC and allies** |
| Stacking | Per-region severity ladder; severe hit may step **twice** |
| Heal | Gold **per severity step** (expensive) |
| Never | Block participation |

**Region → stats:** Arm = accuracy+damage; Leg = step AUT+evade; Head = accuracy; Torso = max stamina fraction+AC.

---

## 8. Recovery at 0 stamina

| Decision | Detail |
|----------|--------|
| 0 HP | Exhausted / downed — **not** lethal |
| PC at 0 | Still talk + crawl; recovery bar; optional stand |
| Recover | When bar full → optional stand at **5 HP** |
| Play dead | May **refuse** stand (green loss path) |
| Second Wind | Once/match willpower burst; may debuff (`data/match_recovery.json`) |
| NPCs at 0 | Cannot act (except as prey in vore pipelines) |
| Bout end | Player side incap (PC downed + no living allies) or win by defeating enemies |

---

## 9. Vore / grapple (design; PR8+)

| Decision | Detail |
|----------|--------|
| PC | Never initiates |
| Flow | Telegraphed grab → **grapple HP war** → multi-phase swallow → digestion AUT |
| Grapple HP | Starts = **current stamina**; falls with further stamina damage |
| 0 stam red | Swallow phases may start without grapple war |
| Grapple feel | **Wrestling clinch** — legitimate break-away / counter; **separate adjacent tiles** (not stacked) |
| Grapple UI (PC prey) | Red crisis modal like INCOMING; copy **`{PredatorName} grapples you!`** |
| Swallow feel | **Coup de grâce** — prey overpowered, vanishing down the throat; **same tile** as predator |
| Swallow UI (PC prey) | Centered modal (not full-screen fill); narrative top of panel + padding; `1 - struggle \| 2 - conserve strength` |
| Tile danger colors | Yellow predator wrestling; green ally in danger; orange predator swallowing; red predator fully engulfed prey |
| Swallow self-escape | **~1% per struggle** (JSON); miraculous; not grapple break-away formula |
| Swallow choices | **Struggle** (miracle escape) vs **conserve strength** (breathe; last longer once engulfed; **no hard cap**) |
| Swallow UI | Narrative top-center only; bottom `1 - struggle \| 2 - conserve strength`; progress via changing narrative per phase |
| Engulfed | Nearly useless actions, but **input remains** |
| Escape after swallow | Self-escape miraculous only; forced regurg / ally damage / predator defeat; **no cutting out** |
| Ally external help | Real damage can force release (not token pokes) |
| Grapple math fairness | Stub first; deepen later (expected) |
| Scene isolation | Prey only takes hits from **current predator**; other enemies refuse the obscured target; prey allies hit the predator; **no** reaction-modal stack while PC is held |

---

## 10. Content / reuse

| Decision | Detail |
|----------|--------|
| Early foes | Dire rats, kobolds, etc.; reskin KDVR OK |
| All enemies | Vore-capable |
| Start loadout | Everyperson; sword+shield first; pick starting weapon later |
| KDVR quarantine | Soft in-place harvest; `KDVR_REFERENCE.md`; eventually purge dungeon-only product paths |

---

## 11. Process

| Decision | Detail |
|----------|--------|
| OpenSpec | Foundation change; one PR at a time after designer auth |
| Manual test | Checklist in chat each PR; designer black-box playtest |
| Balance numbers | **All in JSON** — abilities, maneuvers, AUT, AP, injury %, heal costs, recovery, roster, etc. |
| Terminology | defeated / stunned / digested — never kill/die/death in product prose |

---

## 12. Battle pace program (locked 2026-07-17 — implement via modules)

**Roadmap:** `openspec/changes/battle-pace-program/ROADMAP.md`  
**Modules:** `weapon-measure` → `ready-actions` → `player-combat-commands` → `footwork-momentum` → `ai-personality-fuzzy`  
**Do not implement from chat alone;** open each module’s design.md, then auth named PRs.

### Sport & philosophy

| Decision | Detail |
|----------|--------|
| Interface | Keep roguelike UI; **not** classic adjacent bump-duel as the default sport |
| Fantasy | “Chivalry 2 as tactical RPG” + light DF contact variety — **not** full DF body-part matrix |
| Intent keys | Optimistic resolution; never “swing at air and look foolish”; invalid → **no-op** / Esc cancel |
| Fairness vs vore | Core steel is fair/readable; oppression reserved for overpowering digest / game-over fantasy |

### Weapon measure

| Decision | Detail |
|----------|--------|
| Sword (gladius-like) | **R1** in-fighting fully/near-fully effective; **R2** out-fighting (thrust/jab) comfortable |
| Spear | **R2** detrimental; **R1** near-useless; wants longer measure |
| Other weapons | Per-weapon curves in JSON (axes, etc.) |
| R3–4 | Feint / false-lunge threat space (not steel for many weapons) |
| R5+ | Too far for useful basic combat intent → no-op |
| Basic attack AUT | Weapon **attack delay** (DCSS-like); same delay across reach for basics |

### Player commands (target keys)

| Key / input | Intent |
|-------------|--------|
| Numpad/arrows step | Normal move; **very slight** aggressive balance lean |
| Numpad **5** | **Keep watch / stand ready** — near-neutral; tiny defensive only from inactivity (not turtle dump) |
| **`d`** | **Brace** — raise shield, become more timid (real defensive commitment) |
| **`f`** | **Footwork** — targeting mode; 2 straight **or knight-move**; AP + aggression; compound spam cost; Esc/invalid cancel |
| Directed attack (e.g. ctrl+dir) | Cone/homing basic attack at measure; easy — not buried in ability menu |
| Reaction modal dodge | **Emergency evade** (blow already coming) — distinct from footwork |
| Footwork → evade | Same-direction OK; reverse direction **very hard** (momentum buffs/debuffs) |

### AI (direction)

| Decision | Detail |
|----------|--------|
| Model | **1–10 personality attributes** + fuzzy weighted choice (CK2 *method*, small attr set) |
| Not | Finite hard archetype enum only (“this is a Berserker type” as sole system) |
| Starter attrs (draft) | Ferocity, Intelligence, Tenacity, Bloodlust — finalize in `ai-personality-fuzzy` design |
| Footwork | Enemies may footwork when personality + situation warrant |
| Quality | Roleplay / imperfect — not perfect play |

### Implementation order (hard deps)

1. `weapon-measure`  
2. `ready-actions` (may parallel weapons; recommended before player-commands “done”)  
3. `player-combat-commands` (intent, footwork, directed attack, feint)  
4. `footwork-momentum`  
5. `ai-personality-fuzzy` (last among these — needs move vocabulary)

---

## 13. Still open (may ask later — do not invent without designer)

| ID | Topic |
|----|--------|
| Q-GRAPPLE-MATH | Fair Wrestling / grip / breakaway economy details |
| Q-ZOC-LATER | Whether ZoC returns after MVP |
| Q-COUNTER-MATRIX | Full ability counter web content |
| Q-ALLY-RECOVERY | Allies use same recovery bank UI? (default yes when implemented) |
| Q-PATRONS-DEPTH | Beyond thin objectives |
| Q-CROWD | Meaningful mechanical crowd when un-stubbed |
| Q-BACKGROUND-VICTORY | WWAATD-style end goals per start |
| Q-DIFFICULTY-REIMAGINE | Four tiers retuned for arena career |
| Q-PACE-NUMBERS | Exact AP/AUT/balance/feint/momentum magnitudes (iterate in module JSON) |
| Q-AI-ATTR-FINAL | Final personality attribute list and weight tables |

---

## 14. Implementation status (for agents after compact)

| PR | Status (as of consolidation) |
|----|------------------------------|
| PR1 Re-identity | Shipped + designer OK |
| PR2 Downtime hub | Shipped + designer OK |
| PR3 Match + AUT | Shipped + designer OK |
| PR4 AP/balance/abilities | Shipped + designer OK |
| Font rule (map vs log) | Shipped + designer OK |
| PR5 Reaction/flank/push | Shipped + designer OK |
| PR6 Roster/hire/talk | Shipped + designer OK |
| PR7 Injuries/recovery/JSON combat | Shipped + designer OK |
| PR8 Grapple vore | Shipped + designer OK (stub; scene isolation) |
| PR9 Match cards / economy / surrender | Shipped + designer OK |
| PR10 Thin patrons / objectives | Shipped (stubs OK; deepen later) |
| PR11 Crowd stub | Shipped (thin favor meter) |
| PR12 Difficulty hooks | Shipped (JSON tiers; reimagine later) |
| PR13 Background stub | Shipped (pick + purse; goals later) |
| PR14 Content expand | Shipped (abilities d/e + cards) |
| PR15 KDVR soft-prune docs | Shipped (hard prune deferred) |
| Foundation first pass | Long-lived change; E2E manual after agent full suite |

---

## 15. How to use this file

1. After compact or new chat: read **AGENTS.md** → this file → `design.md` as needed → `tasks.md` for next PR.  
2. For measure/footwork/AI work: also read **`openspec/changes/battle-pace-program/ROADMAP.md`** and the active module folder.  
3. **Never** reverse a locked row without designer confirmation.  
4. New chat agreements: append to this file **and** `design.md` Resolved decisions.  
5. If code and this file disagree, **stop and ask** — do not silently pick.
