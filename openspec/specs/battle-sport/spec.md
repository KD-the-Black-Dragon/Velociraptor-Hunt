# Spec: Battle Sport (measure, balance severity, player commands, fuzzy AI)

## Purpose

Define **behavioral requirements** for Gladiavore’s measure-first arena sport: steep balance, weapon measure, ready/brace/footwork/directed attack, footwork momentum, and personality-weighted enemy **and** ally AI.

**Implementation status:** Design frozen in `openspec/changes/battle-pace-program/BATTLE_SPORT_SPEC.md`. Requirements below are **binding once the Battle Sport batch is implemented**; until then they are the accepted contract for that work (not yet all true in code).

**Related:** `openspec/specs/gladiavore-match/spec.md` (base match AUT, HUD, grapple UX). On ship, that file must not contradict this one; prefer extending match spec or keeping cross-links.

## Terminology

- Enemies are **defeated**; 0 stamina fighters are **stunned** / downed; permanent removal is **digested**.
- Do not use kill / die / death in product prose.

---

## Requirements

### Balance severity

- Balance is an integer centered at **0**, clamped in data (default −10…+10).
- Region **−5…+5** is relatively mild; beyond ±5 penalties escalate **steeply**.
- At **+10**, attack land rate is on the order of **~5%** of the balance-0 baseline (feel target; exact curve in JSON).
- High positive balance: large **accuracy** penalty; **slight damage increase**; damage “sweet spot” near **+5** — further aggression is a net loss.
- High negative balance: **damage** suffers; **slight** AC/block benefit; **accuracy is not** reduced by low balance alone.
- ±6 and worse are overall undesirable; ±9/±10 are terrible.
- Resolution always uses **actual** stats after balance (and other modifiers).

### Always armed / weapons

- Every combatant has a weapon (including **natural** weapons such as teeth/claws).
- No fully unarmed combatants; no disarming; last weapon cannot be removed (swap only).
- Weapons may be marked **non-swappable** (e.g. beast natural weapons).

### Weapon measure

- Each weapon defines **attack delay** (basic attack AUT) and **per-band effectiveness**.
- Range bands derive from geometry (Chebyshev; knight treated as band-2-reachable where rules say so).
- Sword-like weapons are strong at R1 and comfortable at R2; spears are poor in the hug and want proper measure (curves in data).
- R5+ basic combat intent is not a useful steel action (no-op at input layer).
- R3–4 may resolve as **feint** / false lunge rather than full steel when appropriate.

### Ready actions

- **`.`** and **Numpad 5** are the **same** command: **keep watch** (near-neutral; not a turtle dump).
- **`d`** is **brace** (real defensive commitment).
- Normal steps apply only a **slight** aggressive balance lean (data).

### Player combat commands

- Invalid intents and cancelled targeting are **no-ops** (no AUT/AP/balance).
- **`f`** footwork: targeting; legal 2-straight or knight-move; AP + aggressive balance; compound cost on spam; Esc cancels.
- **ctrl+direction** issues a directed basic attack using weapon delay + measure.
- Footwork is a practiced burst technique, not a free faster step.
- Emergency reaction dodge is distinct from footwork.

### Footwork momentum

- Successful footwork applies short-lived directional **momentum** (JSON duration).
- Emergency dodge is easier with momentum and **very hard** against reverse direction.

### Personality attributes

- Fighters have **Ferocity, Cunning, Tenacity, Appetite** on scale **0–10** (**5** neutral).
- Values are rolled from **per-entity min/max** ranges at spawn (no species composition layer).
- **Ferocity** drives close pressure and preferred aggression; 10 is relentless charge; 0 is defensive/timid hang at negative balance with brace-first response.
- **Cunning** drives frequency of **abilities and footwork** (0 = never; 1–2 rare). Does not grant abilities not on the entity kit.
- **Tenacity** drives **morale shock** under stamina loss (threshold ~N×10% lost since last shock ended); shock forces low Ferocity (0–2) for 8–16 AUT.
- **Appetite** drives vore/clinch recklessness when vore-capable; 0 = only helpless/downed; no-op if not vore-capable.
- Entities have data-driven **ability lists**; AI uses only listed, legal abilities. Seed content may be small.

### Enemy AI

- Fuzzy choice among legal player-parity intents using attributes + measure geometry + noise.
- Imperfect roleplay; may use aggressive +6…+8 style; must not treat +9/+10 as a desired home.
- Clinch greed allowed; mercy timers are **not** required in the first Battle Sport ship.

### Ally AI

- Full fuzzy system with **different** priorities from enemies (employer service + self-preservation flavors).
- Same attribute set; Appetite no-op if non-vore.
- Beast allies may swallow enemies; **digestion damage** is allowed in green and red.
- On green, when prey reaches 0 stamina they are **defeated** and must be **released/regurgitated immediately** (no permanent green digest).

### Talk orders

- `T` → one ally or **all** → **Attack!** (free play, default) / **Help me!** / **Stay close!**
- **Help me!** prefers enemies that took **aggressive** actions against the PC recently (including **feints**); window data-driven (~3–5 AUT). If none, behave as Stay close.
- **Stay close!** prefers Chebyshev distance ≤ 2 from PC.
- Orders are always obeyed this ship; after ~10 AUT, rising chance to forget and resume free play.

### Call for help

- Available when PC is downed, grappled, being swallowed, or fully swallowed.
- Downed/grappled: Talk → Help me!
- Swallow modal (not fully engulfed): option **3** calls help and **advances** the swallow phase with **no** escape and **no** conserve bonus.
- Fully swallowed: modal ends; Talk available again.
- Calls made while **being swallowed or fully swallowed** have **50%** chance to be heard.
- Free Talk applies to the Talk path only, not swallow option 3.

### AI common sense (balance)

- No AI prefers living at +9/+10; reset pressure applies.
- Preferred balance homes are data-driven by Ferocity (provisional tables OK).

---

## Non-goals (Battle Sport batch)

- Clinch mercy / re-grab cooldown systems
- Disobedient trait
- Full ability counter web and large ability content pass
- Jump/vault, ZoC, deep openings matrix
- Crowd/patrons/background victory depth
- Full wrestling math fairness pass

---

## Source of truth

| Artifact | Role |
|----------|------|
| `openspec/changes/battle-pace-program/BATTLE_SPORT_SPEC.md` | Full design freeze narrative |
| `openspec/changes/*/design.md` | Per-module implementation design |
| This file | Behavioral requirements for verification and ship |
