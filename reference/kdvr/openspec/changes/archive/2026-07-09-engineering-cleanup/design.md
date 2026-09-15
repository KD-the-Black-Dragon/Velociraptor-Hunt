# Design: Engineering cleanup

| Field | Value |
|-------|-------|
| **Date** | 2026-07-09 |
| **Status** | Design review |
| **Change id** | `engineering-cleanup` |
| **Spec targets** | Extend `openspec/specs/save-load/spec.md`; optional thin `openspec/specs/engineering/spec.md` |

---

## PR0 — AGENTS.md (done at design start)

| Stale line | Fix |
|------------|-----|
| Extensibility: “mods (planned core feature)” | “mods (shipped)” |
| Save Compatibility: “mod compatibility (mods not yet implemented)” | Shipped mods + stronger forward-compat language |

No gameplay code.

---

## 1. Save compatibility (primary product goal)

### Product intent (designer)

> Avoid the Itch.io “update voided my run” feeling. Prefer resume **minus broken bits** over refuse to load.

### What actually invalidates a save today?

Honest answer: **not many day-to-day content edits**—but a few **hard gates** do, and **missing content can crash later** even if load “succeeds.”

#### A. Hard fail at load time (run never starts)

| Cause | Why | How common with frequent updates |
|-------|-----|----------------------------------|
| **`save_format_version` ≠ current** | `store.validate_envelope` requires **exact** match to `SAVE_FORMAT_VERSION` (1). | Only if we **bump the number** without a migrator. Additive fields don’t need a bump. |
| **Corrupt JSON / hash mismatch** | `payload_sha256` doesn’t match `run` (disk corruption, partial write). | Rare; bak1–bak3 exist for this. |
| **Missing required structure** | No `run` object, no player entity id, etc. | Rare; our snapshots always write a full run. |
| **Mod fingerprint mismatch** | Enabled mods list in save ≠ current Options mods. | **Intentional** (modding design)—not the same as “game updated.” Player can re-enable the same mods. |

#### B. Load “works” but run blows up or acts wrong later (soft corruption)

These are the **longsword removed** class of problems. Today inventory stores **`item_id` strings**; decode does **not** check the item registry. Failures appear when something **looks up** the id:

| Cause | Example | Desired product behavior (designer) |
|-------|---------|-------------------------------------|
| **Item removed from data** | Save has `longsword`; `weapons.json` no longer has it | Drop the slot / unequip; log something friendly; **resume without the item** — not crash |
| **Entity type removed** | Floor NPC or summon id gone | Remove entity or replace with safe stub; log; resume |
| **Ability token unknown** | Saved ability string no longer parses | Strip ability; warn; resume |
| **New required field we forget to default** | Old save lacks `come_here` | Should default — **already** mostly true for optional `.get`; bugs if someone requires a key without default |
| **Balance-only changes** | Dagger damage 5→6 | Save keeps old stats on the **instance** (Fighter numbers are snapshotted). World data changes apply to **new** spawns. Usually fine. |
| **Renamed id** | `longsword` → `long_sword` | Looks like “removed item” unless we dual-read old id |

#### C. What does **not** need to void a save

| Change | Why it’s fine |
|--------|----------------|
| New monsters/items/abilities in JSON | Old saves simply don’t have them yet |
| New optional AI/UI fields | Decode with defaults |
| Narrative text rewrites | Not stored in save (or only past log lines) |
| Most balance tweaks | Instance stats already frozen on entities |
| Bugfixes that don’t rename fields | Transparent |

### Design answer to “what would even invalidate a save?”

**Only these should ever hard-block load:**

1. File unreadable / integrity hash fails (and all backups fail).  
2. Save is from a **newer** game (we can’t invent unknown structure).  
3. Save is from an **impossibly old** format we explicitly stopped migrating (rare, deliberate).  
4. **Mod set mismatch** (existing rule—player can fix by matching mods).

**Everything else** (removed longsword, removed wolf variant, unknown ability, missing optional keys) should be **load + sanitize + resume**, with a short log/notice when something was dropped.

### Policy (locked direction)

| Layer | Rule |
|-------|------|
| **Wire format** | Prefer additive fields + defaults. Bump `save_format_version` only for true layout breaks; migrate when possible. |
| **Content ids** | On load (or first use), if `item_id` / entity id / ability is unknown → **strip with message**, continue. Never treat as “save corrupt.” |
| **Mods** | Keep fingerprint gate (different problem than Itch updates). |
| **Player messaging** | Prefer one summary: e.g. *“Some items or creatures from this save are no longer in the game and were removed.”* rather than a crash. |

### Concrete engineering work (PR1)

1. Document the above in live `save-load` spec.  
2. **Sanitize pass** after decode (or lazy-safe lookups):  
   - Inventory slots: drop unknown `item_id`; clear equip pointers to empty slots.  
   - Floor items: despawn unknown ids.  
   - NPCs: remove or skip entities with unknown type id (if stored).  
   - Abilities: strip unknown tokens.  
3. Collect dropped ids for one log line / menu notice on load.  
4. Version range + migration **hook** so a future bump doesn’t force a hard cut.  
5. Tests: load snapshot with fake `longsword` → slot empty, game runs; load missing `come_here` → defaults; corrupt hash still fails; mod mismatch still fails.

### Open choices (soft defaults)

| # | Question | Default |
|---|----------|---------|
| S1 | Notice only in message log vs modal on Load Game? | **Log + one-line menu notice if anything stripped** |
| S2 | Unknown NPC on floor: delete vs replace with generic? | **Delete** (simpler) |
| S3 | Dual-read renames for one release? | **Yes when we rename ids** |

---

## 2. Flaky tests (locked decisions 2026-07-09)

From recent full-suite runs under `pytest -n 6`. Designer guidance applied below.

### A. Perf p95 — **SKIP / drop as gate**

| Decision | **Do not treat as a blocking regression test.** |
|----------|--------------------------------------------------|
| Rationale | Designer will notice real lag in play. Parallel CI noise is not worth the flake. |
| Action (PR2) | Skip under normal suite (`pytest.mark.skip` or exclude from default CI), or delete the p95 assert and keep `tools/profile_turn.py` for manual use. Prefer **skip with reason** so the tool remains discoverable. |

### B. Summon1 outside FOV — **clarify intent, then harden**

| Design fact | Summon is for when the wolf has a **combat reason** (sees a target: player/good). Not “summon for fun in empty dark.” Also **no room to place** (crowded / surrounded) → no summon. |
| Setup need | Fixture wolf **with Summon1**, outside **player** FOV, but **must still see a valid target** (e.g. knight or player? — verify code: likely sees evil’s own FOV target). |
| Flake cause | Test asserts rabbits ≥ 1 after one AI tick without guaranteeing “sees target + has open tile + ability fires.” |
| Action (PR2) | Re-read Summon1 rules in code/spec; rebuild test as: (1) wolf has Summon1, (2) valid target in **wolf** LOS, (3) open spawn tiles, (4) deterministic fire or multi-tick with seed, (5) still assert no “summons aid” log when **player** can’t see the wolf. |

### C. Vore Enter advances phases — **deliberate setup**

| Decision | Setup must be **forced**: player adjacent to wolf, **player HP = 0** (stunned) so vore attempt is reliable / 100% path. |
| Action (PR2) | Harden `_open_vore_modal` / `place_adjacent_wolf`: explicit wolf spawn (not `next(iter_wolves)`), isolate AIs, HP 0, assert modal open. Strengthen phase-advance assert after that. |

### D. RangeN prefers knight — **clear geometry, no other NPCs**

| Decision | Player far but in LOS; knight nearer; **no other NPCs** in the world for that test. |
| Action (PR2) | Wipe/isolate all non-fixture entities; place player, wolf, knight only; assert by identity or stable id. |

### Priority

1. C + D isolation (clear, designer-approved).  
2. B after re-reading summon rules.  
3. A skip — no more “failed suite because laptop was busy.”

---

## 3. Optional polish (backlog within change if time)

| Item | Notes |
|------|--------|
| tcod `tiles["ch"]` FutureWarning | Mass test/render churn; pure hygiene |
| Deep-floor profile | Manual / `tools/profile_turn.py` after save work |
| Door spite approach | Still in `todo/spec.md` — **separate** gameplay change, not this module |

---

## PR plan

| PR | Scope |
|----|--------|
| **PR0** | OpenSpec bootstrap; **AGENTS.md cleanup** (mods + save policy wording) |
| **PR1** | Save load: multi-version accept + migration hook + defaults audit + tests + friendlier errors |
| **PR2** | Flaky test stabilization (isolation / determinism / perf job policy) |
| **PR3** | Optional warnings cleanup if free; full suite; acceptance; archive |

---

## Resolved decisions (this design pass)

| Topic | Decision |
|-------|----------|
| Product goal | Never “void the run” for content removal; strip and resume |
| Hard-fail load | Corruption, future format, deliberate min version, mod fingerprint only |
| Missing longsword etc. | Soft-drop with notice — not corrupt |
| Version strategy | Additive defaults preferred; migrate on hard bumps |
| Perf p95 test | **Skip** (designer notices lag in play) |
| Summon1 / vore / RangeN tests | Harden per designer geometry rules |
| AGENTS | Cleaned in PR0 |

---

## Open questions (soft)

| # | Question | Default |
|---|----------|---------|
| Q1 | Load strip notice: log only vs short menu line? | **Log + short menu notice if anything stripped** |
| Q2 | Unknown floor NPC: delete vs stub? | **Delete** |
| Q3 | tcod FutureWarnings in this change? | **No** unless freebie |

---

## References

- `src/save/schema.py`, `store.py`, `snapshot.py`, `codec.py`  
- Live save-load spec: `openspec/specs/save-load/spec.md`  
- Recent suite flakes (2026-07-09 full runs)
