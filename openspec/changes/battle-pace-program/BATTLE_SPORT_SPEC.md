# Battle Sport — design freeze (hard specification)

| Field | Value |
|-------|--------|
| **Status** | **Design frozen** — documentation complete; **no implementation until designer authorizes the whole batch** |
| **Product** | Gladiavore |
| **Parent** | `openspec/changes/gladiavore-foundation/` + `DESIGN_CANON.md` |
| **Roadmap** | `ROADMAP.md` (module dependency map) |
| **Live requirements target** | `openspec/specs/battle-sport/spec.md` |
| **Frozen** | 2026-08-10 (designer Q&A + R-series) |
| **Process** | One authorization → implement full batch; automated tests per phase; **one** manual playtest at end; designer handles git commits |

**Terminology:** defeated / stunned / digested — never kill / die / death in product prose.

This file is the **authoritative design freeze** for the Battle Sport batch. Module folders hold implementation-oriented `design.md` detail; if they conflict with this file, **this file wins** until the designer reopens a topic.

---

## 1. Product goal

Keep the **roguelike interface**, replace **adjacent bump-duel** as the default pace with **measure-first gladiatorial combat** (reach, footwork, ready vs brace, weapon-defined techniques), enforce a **steep balance curve** so relentless attack collapses accuracy, and give enemies **and** allies **personality-weighted fuzzy AI** that uses the **same move vocabulary** (with different goals).

---

## 2. Batch scope

### In (full implementations — no light stubs unless unavoidable)

| Phase | Work |
|-------|------|
| 0 | These hard specs + module `design.md` + canon updates (**this work**) |
| 1 | Balance severity retune (`match_combat` balance passives) |
| 2 | `weapon-measure` — delay, bands, natural weapons, `swappable` |
| 3 | `ready-actions` — `.` ≡ Numpad 5 keep watch; `d` brace; step lean |
| 4 | `player-combat-commands` — intent, footwork, ctrl+dir attack, feint |
| 5 | `footwork-momentum` — emergency dodge vs footwork direction |
| 6 | `ai-personality-fuzzy` — enemy + ally fuzzy, orders, morale, crisis help |
| 7 | Live specs sync, full automated suite, consolidated manual checklist |

### Out of batch

- Clinch mercy / re-grab cooldowns (inevitable later; not this batch)
- Disobedient trait
- Full ability content / counter web
- Jump (`J`), ZoC, deep openings matrix
- Crowd / patrons / background victory depth
- Full grapple math fairness revamp

---

## 3. Balance meter (severity freeze)

| Property | Rule |
|----------|------|
| Type | Integer; **0 = ideal**; clamp **−10…+10** |
| Sources | Actions only (no stance toggles) |
| Shape | **−5…+5** relatively tame; each step past ±5 gets **rapidly worse** (exponential / logarithmic inspired) |
| **±6 and beyond** | Overall **bad** |
| **±9 / ±10** | **Terrible**; never a place you want to live |
| **+10 accuracy** | Land roughly **~5%** of attacks vs balance 0 baseline (feel target) |
| Overextended (+) | **↓ accuracy hard**, **↑ damage slightly**; damage sweet spot ~**+5**; above that tradeoff is **not worth it** mathematically |
| Cowering (−) | **↓ damage**; **slight ↑ AC / blocking**; **accuracy unaffected** by low balance |
| Common sense (AI) | Nobody **targets** living at **+9 / +10** — prefer reset (watch / brace / reposition) |
| Style band | **+6…+8** allowed as **aggressive style** (esp. high Ferocity minions) |
| Preferred homes | Per Ferocity in **JSON** (provisional; retune after playtest). Example intent: F0 ≈ −7; F5 ≈ 0…+2; F10 ≈ +5…+7; never prefer +9/+10 |
| Reset sloppiness | Controlled by **Ferocity** (low Cunning does **not** mean sloppy balance reset) |

All magnitudes live in JSON (`data/match_combat.json` or successor). Tests pin **fixture** curves, not live balance numbers as sacred constants.

---

## 4. Weapons, measure, and armament rules

### 4.1 Always armed

- Every combatant has a **weapon** — steel or **natural** (e.g. “wolf teeth”).
- **Nobody** is totally unarmed.
- **No disarming.**
- Cannot remove your **only** weapon; **swap only**.
- Data boolean **`swappable`**: if false (typical beast natural weapon), player cannot swap it out on that fighter.

### 4.2 Measure bands

Geometry: **Chebyshev** distance actor→target. Knight-move adjacency treated as **band-2-reachable** where rules say so (shared helper).

| Band | Intent |
|------|--------|
| R1 | In-fighting (adjacent) |
| R2 | Out-fighting / thrust measure |
| R3–4 | Feint / false-lunge threat space for many weapons |
| R5+ | Too far for useful basic combat intent → **no-op** |

### 4.3 Archetype curves (design intent; numbers in JSON)

| Weapon fantasy | R1 | R2 | Longer |
|----------------|----|----|--------|
| Sword (gladius-like) | Full / near-full | Comfortable thrust/jab | Feint space then no-op |
| Spear | Near-useless | Detrimental relative to ideal longer measure; wants **longer** than hug | Per JSON (ideal past R1) |
| Heavy (axe/mace) | Strong commit, slower delay | Weaker / awkward | JSON |
| Short blade | Strong R1, falls off faster | JSON | JSON |
| Natural (teeth/claws) | Own profile in data | Own profile | Own profile |

### 4.4 Attack delay

- Basic attack AUT = weapon **`attack_delay`** (DCSS-like).
- Same delay across reach for basics; band changes **effectiveness**, not a second delay table (unless data later adds technique-specific delays).

---

## 5. Player commands

| Input | Intent |
|-------|--------|
| Arrows / numpad step | Move; **very slight** aggressive balance lean (JSON) |
| **`.`** and **Numpad 5** | **Same command:** keep watch / stand ready — near-neutral; tiny defensive only from inactivity (**not** turtle dump) |
| **`d`** | **Brace** — raise guard / timid commitment; real defensive balance + defensive actual-stat lean (JSON) |
| **`f`** | **Footwork** targeting: legal **2 in straight line** or **knight-move**; destination free/valid; costs AP + aggression; **compound** cost on successive footworks; Esc/invalid = cancel / no-op |
| **ctrl + direction** | Directed basic attack: cone/homing; uses weapon measure + delay |
| Reaction dodge | **Emergency evade** (blow already coming) — **not** footwork |
| Invalid command | **No-op** (no AUT / AP / balance) |
| R5+ basic intent | No-op — never shame-swing empty air |
| R3–4 | Feint / false lunge when weapon does not deliver full steel |

Smart-bump at R1 remains optimistic and should share the same resolver as directed basics where practical.

Abilities: existing `a` + letter menu; seed content stays modest this batch.

---

## 6. Footwork momentum

- After footwork resolves, apply short-lived **momentum** vector (JSON duration in AUT).
- Reaction-modal dodge: **same / similar direction** OK; **reverse direction very hard**.
- Multi-footwork: refresh/overwrite rule in module design + JSON.
- AI reads the same tags when it footworks.

---

## 7. Personality attributes (all fighters)

### 7.1 Model

| Property | Rule |
|----------|------|
| Scale | **0–10 integer**; **5 = neutral** |
| Low pole | Inverse of high (no separate Timid/Coward stats) |
| Source | **Per entity** `minFerocity` / `maxFerocity` (etc.); roll **inclusive** on spawn |
| Species | **No species layer** — each entity is a curated archetype |
| Bosses | Same system (own entity min/max) |
| Purpose | Choose among **valid** moves; may create **exploitable / minion-grade** styles |
| Not | A substitute for shared combat rules (legality, measure math, +9/+10 common sense) |

### 7.2 Attributes

| Attr | High (6–10) | Low (0–4) | Notes |
|------|-------------|-----------|--------|
| **Ferocity** | Close pressure; **10** = classic roguelike charge-down; prefers higher aggression balance home | **0** = watch/brace, hang **−6…−8**, light pokes so not deeper negative; back/side steps; on approach **brace first** (not kite) | **5** = desired baseline pace (maneuver, commit sometimes). Also favors **bigger/bolder** basic profiles when choosing among them. Controls **reset sloppiness** toward preferred band |
| **Cunning** | More **abilities** and **footwork** (technical fighting) | **0 = never** abilities or footwork; **1–2 = rare** | Footwork = practiced burst technique (close for strike or escape) — not “move faster.” High F + low C = “ogre walk up and punch” |
| **Tenacity** | Unworried by damage; stays in after commitment | Blood-shy; morale shock from small losses | Allies: high = protect player even while low stamina; low = panic/self-save when low stamina |
| **Appetite** | Vore recklessness: clinch higher-stamina targets; “I’m going for it” approach+grab | **0** = only **helpless / downed** if vore-capable | **No-op** if fighter cannot vore. Mid values = low-stamina opportunism |

### 7.3 Morale shock (Tenacity)

| Property | Rule |
|----------|------|
| Trigger | Sliding scale: roughly **Tenacity N** → rethink after losing about **N×10%** of max stamina **since last shock ended** (Tenacity 1 ≈ after 10%, etc.; exact table JSON) |
| Effect | Apply **Morale Shock** status: treat **Ferocity as forced 0–2** (roll or clamp each panic — default uniform 0–2 in JSON) until wear-off |
| Behavior under shock | Biased to **defensive** moves via that temporary low Ferocity |
| Duration | **8–16 world AUT**, re-rolled **each** panic |
| After | Return to normal rolled Ferocity; obligated to keep fighting |

### 7.4 Abilities and AI

- NPCs have **AP** and ability kits **like the player**.
- Each entity has a **data-driven ability list**; may use any ability in the game that is on **its list** and currently **legal**.
- This batch: seed subset content (Haymaker, Shield Push, Hook Shield, etc.); architecture remains open to all abilities.
- **Cunning** only changes **how often** they fire abilities they already have — not which abilities exist on the sheet.

---

## 8. Enemy AI

| Goal fantasy | “Who can I pressure / eat?” |
|--------------|------------------------------|
| Method | Fuzzy weighted choice over **candidate intents** (CK2-like method; small attr set) |
| Candidates | Hold measure, step, keep watch, brace, footwork, basic/directed attack profiles, seed abilities, clinch approach when legal |
| Geometry | Weapon measure fitness |
| Noise | Imperfect; roleplay over optimal robots |
| Clinch | Appetite-driven; **no mercy timer** this batch (later inevitable) |
| Balance | Preferred band by Ferocity; **+9/+10** common-sense reset; +6…+8 style OK for aggressive builds |

---

## 9. Ally AI

| Goal fantasy | Survive the bout / serve the employer — imperfectly |
|--------------|------------------------------------------------------|
| Method | **Full fuzzy** this batch; **shared verbs**, **different** utility function from enemies |
| Attrs | Same four; Appetite no-op if non-vore |
| Balance | Same preferred-band rules as enemies (player should hire good attrs) |
| Vore | Beast allies free to swallow enemies with same mechanics |
| Green | Digestion **damage** always allowed. At **0 stamina** prey is **defeated** (removed as combatant). Fatal permanent digest not allowed → **immediate regurgitate** / release as defeated (verbiage; not a second death system) |
| Crisis auto-spike | **No** hard auto priority spike when PC is downed/grappled/swallowed — player uses **Help me!** |

### 9.1 Talk orders

Flow: **`T` → pick ally or all → pick order**.

| Order | Meaning |
|-------|---------|
| **Attack!** | Default = **act freely** (engage-friendly free play). Match **starts** in this state with **no** forget timer until another order is given |
| **Help me!** | Prefer enemies that performed **aggressive** actions on the PC recently (includes **feints**), window ~**3–5 world AUT** (JSON). If **none** qualify → behave as **Stay close!** |
| **Stay close!** | Prefer Chebyshev distance to PC **≤ 2** |

| Property | Rule |
|----------|------|
| All | Broadcast: “Everyone, …” |
| Obedience | **Always obey** this batch (Disobedient trait not shipped) |
| Memory | Solid obey for ~**10 AUT**, then **rising chance to forget** last order and resume free play (JSON curve) |

### 9.2 Call for help (crisis)

| PC state | Input |
|----------|--------|
| Downed | Talk → **Help me!** |
| Grappled | Talk → **Help me!** |
| Swallow modal (not fully engulfed) | New modal **option 3**: call for help; **advances swallow phase** with **no** escape roll and **no** conserve bonus |
| Fully swallowed | Modal gone; normal **Talk** available again |

| Property | Rule |
|----------|------|
| Heard chance | While **being swallowed or fully swallowed**, call for help has **50%** chance to be **heard at all** (JSON). Downed/grapple Talk help: **always heard** (default unless data says otherwise) |
| Free Talk | Free Talk rules apply to Talk → Help me! only. Swallow option 3 is **not** free Talk; it advances the swallow process |
| Effect when heard | Same as Help me! tagging for allies (current predator / recent aggressors) |

---

## 10. Green vs red (vore damage clarification)

| Topic | Rule |
|-------|------|
| Digestion **damage** | Allowed in **green and red** as a means of incapacitating (stamina loss) |
| Prey at **0 stamina** | **Defeated** / removed as arena combatant (same as other defeat paths for enemies) |
| Green permanent digest | **Not** allowed — if ally/enemy “digest pipeline” would finish, **regurgitate immediately** at 0 stam; text/obligation |
| Red permanent digest | Existing career rules (PC digest ends run; ally digest roster loss + refund when applicable) |

Do not conflate “digestion damage” with “removed from game permanently.”

---

## 11. Implementation process (this batch only)

| Rule | Detail |
|------|--------|
| Authorization | Designer says implement the **whole Battle Sport batch** (or equivalent) once |
| Manual playtest | **Once** at end of batch |
| Automated tests | After each phase; full suite before presenting manual checklist |
| Git | Designer commits; agent does not need to commit |
| Data-driven | AUT, AP, balance, bands, attrs, weights, timers in JSON |
| Save compat | New optional fields default on load |
| Module order | Balance severity → weapon-measure → ready-actions → player-commands → momentum → AI (see `ROADMAP.md`) |

---

## 12. Module file index

| Module | Folder | Design detail |
|--------|--------|---------------|
| Program freeze | `battle-pace-program/` | **This file** + `ROADMAP.md` |
| Weapon measure | `weapon-measure/` | `design.md` |
| Ready actions | `ready-actions/` | `design.md` |
| Player commands | `player-combat-commands/` | `design.md` |
| Momentum | `footwork-momentum/` | `design.md` |
| Fuzzy AI | `ai-personality-fuzzy/` | `design.md` |
| Live requirements | `openspec/specs/battle-sport/` | `spec.md` |

---

## 13. Document history

| Date | Note |
|------|------|
| 2026-08-10 | Design freeze from multi-turn designer Q&A; hard file created (docs only, no code). |
