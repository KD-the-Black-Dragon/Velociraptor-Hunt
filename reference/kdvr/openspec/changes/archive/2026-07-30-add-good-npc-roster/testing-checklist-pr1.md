# Manual testing checklist — PR1 (good NPC roster)

**How to run:** `python -m src.main`

Data-only change: new good allies + knight spawn/combat retune. No full automated suite required.

## Happy path

- [ ] Game starts without load errors (`entities.json` / `names.json`)
- [ ] **Depth 1:** no good allies among fresh spawns (rats only era)
- [ ] **Depth 2–4:** **dog squire** (`q`, cyan) can appear; introduces with `Squire …` name when coast is clear
- [ ] **Depth 5–7:** **dog knight** can appear; **not** depth 3-only / not deep floors; combat feels stronger than pre-PR1 knights
- [ ] **Depth 6–8:** **ram crossbow** (`c`) can appear; Path shots work; melee hits feel as hard as bolts
- [ ] **Depth 8–10:** **ferret guard** (`e`) can appear; `Guard …` names
- [ ] **Depth 11–13:** **lion warrior** (`L`) can appear; `Warrior …` names
- [ ] **Depth 12–14:** **sheep cleric** (`p`) can appear; Smite works; melee equals Smite punch
- [ ] **Depth 14–16:** **otter warden** (`o`) can appear; `Warden …` names
- [ ] **Depth 17–19:** **boar-at-arms** (`A`) can appear; names end with `-at-arms` (no “man”)
- [ ] **Depth 17+:** **badger champion** (`B`) can appear; continues on deep floors; `Champion …` names

## Combat / design intent

- [ ] Good vs expected peer 1v1: good wins handily (not a coin flip)
- [ ] Goods get threatened or swallowed when **outnumbered** or facing **out-of-depth** heavies
- [ ] Goods never use vore; still follow / rescue as allies
- [ ] Ram/sheep do **not** stand still ignoring the fight (`NoChase` absent)

## UI / presentation

- [ ] All new goods (and knight) render **cyan**
- [ ] Glyphs distinct: `q e L o A B c p` (+ knight `k`)
- [ ] Intros use full title names (`Squire Bob`, `Crossbow Bram`, `Garrick-at-arms`, etc.)
- [ ] Knight intros still work; names still `Sir …` only for knights

## Save / load

- [ ] Mid-run save/load still works (new species optional on old saves)
- [ ] Existing knight on a deep pre-PR1 floor: load does not crash (old entity state OK)

## Performance

- [ ] No noticeable hitch from extra species definitions (data-only; spawn weights still 1 for goods)

## Edge / regression

- [ ] Depth 3 no longer relies on knight as the only good (squire band has ended; knight starts at 5)
- [ ] Follower descent still works with mixed good species
- [ ] Fox/owl evils still behave; ram/sheep feel like good counterparts without weak-melee glass kit
