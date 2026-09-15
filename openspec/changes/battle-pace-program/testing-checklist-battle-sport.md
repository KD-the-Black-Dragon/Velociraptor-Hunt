# Manual testing checklist — Battle Sport batch

**Designer sign-off:** 2026-08-10 — all manual checks pass (including post-feedback footwork 1-tile + balance floors/ceilings + status effect lines).

Run: `python -m src.main`

## Happy path

- [ ] New career → hub → match starts; help line mentions footwork / keep watch / brace / ctrl+dir
- [ ] **Keep watch** (`.` / 5): defensive slide, **stops around −5** (not −10 fortress)
- [ ] **Brace** (`d`): stronger defensive; can go deeper than watch
- [ ] **Step**: slow walk; aggression climbs but **caps near +5** from walking alone
- [ ] **Footwork** (`f`): cursor; legal **1-tile and 2-tile**; Enter confirms; Esc cancels; **Shift+dir** = quick 1-tile
- [ ] Status under balance bar: Acc/Dmg/Eva/AC buffs **green**, debuffs **orange**
- [ ] **ctrl+direction**: attacks at measure when a foe is in that cone; empty direction = no-op (no wasted swing)
- [ ] Balance at high + (spam attacks): accuracy collapses — hard to land near +10
- [ ] Enemies do more than pure rush: may watch, brace, footwork, or hold measure; rats feel aggressive
- [ ] Talk → ally/all → **1 Attack! / 2 Help me! / 3 Stay close!**
- [ ] Help me! after being hit: allies prefer recent aggressors (or stay close if none)
- [ ] Reaction dodge after footwork: reverse direction feels worse

## Vore / green

- [ ] Swallow modal shows **3 - call for help**; option advances swallow
- [ ] Fully swallowed: Talk works; Help me! may fail to be heard (~50%)
- [ ] Green: digestion damage OK; defeated at 0 stam (no permanent green digest path break)

## Regression

- [ ] Career hub still works after match
- [ ] Match HUD: status right, log bottom, reaction low-right
- [ ] Ally bump still no-op with “standing there”
- [ ] Abilities menu (`a`) still works
- [ ] Grapple / swallow UI still usable

## Performance

- [ ] Multi-enemy match remains responsive (no multi-second freezes on NPC turns)
