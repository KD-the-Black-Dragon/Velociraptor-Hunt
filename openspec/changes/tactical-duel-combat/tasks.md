# Tasks: tactical-duel-combat

**Status:** Design Q&A locked — **do not implement any PR until the user explicitly authorizes that PR.**

PR order is for **implementation efficiency** (core math first, then wire session, then UI/AI polish). Designer does not require a specific order.

---

## PR1 — Strike momentum engine + fumble + always-land core

Pure / low-UI foundation everything else calls.

- [ ] `match_strike_momentum.py` (or equivalent): factor weights from JSON; `StrikeMomentumResult` (total, factors, tier, incoming flag)
- [ ] Factors: relative balance, measure band, defender remaining AUT, ability base, buffs/debuffs, beast target bonus, optional flank
- [ ] Timid basic-attack expression: negative attacker balance → jab-level profile for basic attacks
- [ ] Fumble chance table by high balance only; verbiage; checked before momentum effects that open Incoming
- [ ] Match resolve: default always-land; remove/bypass classic accuracy-vs-evade as primary miss
- [ ] Unit tests for factors, tiers, fumble, jab-level gate
- [ ] Manual checklist optional if not yet player-visible; else note “dev only”

## PR2 — Integrate resolve paths: chip, crisis damage, narrative log

- [ ] Wire fumble → momentum → tiered outcome in `match_session` melee/ability paths
- [ ] Non-crisis: passive shield/parry/beast + chip (slight scale with momentum, capped)
- [ ] Crisis Ignore path: full breakthrough hurt (not free full block)
- [ ] Narrative templates in `messages.py` by tier/outcome; **no damage numbers** in log
- [ ] Severity thresholds in JSON
- [ ] Tests: chip path, crisis path, no numeric dmg tails
- [ ] Manual checklist `testing-checklist-pr2.md` if playable mid-change

## PR3 — Incoming gate + reaction economy + NPC emergency sim

- [ ] Incoming only when `incoming` / breakthrough+ vs PC
- [ ] Options **1 Dodge / 2 Block / 3 Ignore**; remove Counter
- [ ] Dodge = exact 1-tile footwork costs (AP required, balance, AUT); usable during cooldown; AUT append
- [ ] Block = exact brace costs; AUT append
- [ ] Ignore free
- [ ] Dodge outcome table ~60/30/10 + footwork-momentum adjust
- [ ] Beast: no Block option; no brace maneuver for beasts
- [ ] NPC reaction simulation (dodge/block/ignore weights; beasts dodge/ignore only)
- [ ] Pending reaction carries momentum result for resolve
- [ ] Tests: threshold, costs, AP gate, AUT append, beast filters, no counter
- [ ] Manual checklist `testing-checklist-pr3.md`

## PR4 — Opponent readout + momentum debug HUD

- [ ] Sidebar: name, plan, balance, stamina, personality (flags default on)
- [ ] Strike momentum debug: last/pending total + factor lines when flag on
- [ ] Always show focus foe in the pit
- [ ] `last_plan_label` updates from AI + reactions
- [ ] Tests for line builders
- [ ] Manual checklist `testing-checklist-pr4.md`

## PR5 — AI timidity, feint, punish-close + beast candidates

- [ ] JSON weights: hold/feint/retreat; Ferocity curves; punish-on-close window
- [ ] Low Ferocity hang-back; high Ferocity sudden commit (not bump-bot)
- [ ] Beast AI: no brace candidates; uses dodge in emergency sim
- [ ] All attacks go through strike momentum
- [ ] Plan labels reflect behavior
- [ ] Tests with fixed seeds where practical
- [ ] Manual checklist `testing-checklist-pr5.md`

## Final acceptance

- [ ] Live specs: `battle-sport` + `gladiavore-match` (momentum, Incoming, reactions, log, readout, beasts)
- [ ] DESIGN_CANON: Incoming = breakthrough crisis; reaction keys; fumble wording; no Counter
- [ ] Full pytest procedure after designer final sign-off
- [ ] Archive change on acceptance

---

## Notes

- One PR at a time after explicit authorization (or whole-batch if designer says so).
- Data-driven weights; no entity-id hardcoding.
- Terminology: defeated / stunned / digested.
