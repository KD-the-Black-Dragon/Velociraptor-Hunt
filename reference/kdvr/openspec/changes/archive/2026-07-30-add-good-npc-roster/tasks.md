# Tasks: add-good-npc-roster

**Active PR:** *(none — change accepted and archived 2026-07-30)*  
**Rule:** One PR at a time.

**Regression note (designer):** JSON/data only. **Skip full `pytest tests/`** on final acceptance.

---

## PR0 — OpenSpec

- [x] `proposal.md`, `design.md`, `tasks.md`
- [x] Designer lock (boar-at-arms, otter warden, equal bands, naming, knight buff, champion→1000, ranged=melee stats, ~95% 1v1)
- [x] `AGENTS.md` pointer → `add-good-npc-roster`

---

## PR1 — Stock good roster content

Data only unless a load bug forces a tiny fix.

- [x] Retune **`knight`**: spawn **5–7** weight 1; combat per design table; **do not** rewrite examine / intros / names pool
- [x] Add **`dog_squire`** (2–4, cyan, `q`, names `Squire …`, intros)
- [x] Add **`ferret_guard`**, **`lion_warrior`**, **`otter_warden`**, **`boar_at_arms`** (melee ladder; cyan; unique glyphs)
- [x] Add **`ram_crossbow`** (`Range5`; melee stats **==** ranged stats; names `Crossbow …`)
- [x] Add **`sheep_cleric`** (`Smite5`; melee stats **==** ranged stats; names `Cleric …`)
- [x] Add **`badger_champion`** (17–1000; peer gryphon; names `Champion …`)
- [x] Apply locked combat table from `design.md`
- [x] Full examine text for each **new** id
- [x] `data/names.json` pools for every new id (title schemes per design)
- [x] `introduction` (+ optional `introduction_log_category: "speech"`) for every new id
- [x] Light `npc-data` spec note if needed
- [x] `testing-checklist-pr1.md`
- [x] Manual playtest sign-off

**No full regression suite.**

---

## PR2 — Acceptance

- [x] Post-playtest JSON retunes if any *(none — designer sign-off as shipped)*
- [x] Update `design.md` Resolved decisions if numbers moved *(no number changes)*
- [x] Archive → `openspec/changes/archive/2026-07-30-add-good-npc-roster/`
- [x] Clear / update `AGENTS.md` active change pointer
- [x] **Do not** run full `pytest tests/` (designer waiver)


---

## Manual testing focus (PR1)

See `testing-checklist-pr1.md`. High level:

- Depth 2: squire appears; depth 1 still no goods
- Knight only mid-early (5–7) and clearly stronger
- Band hand-offs: guard → warrior → warden → boar-at-arms → champion
- Ram Path and sheep Smite; melee hits as hard as ranged/smite
- Names: Sir only on knights; Squire/Guard/Warrior/Warden/Crossbow/Cleric/Champion/`…-at-arms`
- 1v1 peers feel lopsided for goods; packs / OOD can swallow them
