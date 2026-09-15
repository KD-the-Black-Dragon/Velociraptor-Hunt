# Proposal: Engineering cleanup (saves, tests, docs)

**Status:** Design review  
**Change id:** `engineering-cleanup`

## Why

Frequent game updates should not strand players mid-run. The save format is currently **strict equality** on `save_format_version` (only `1`), while features keep adding optional fields. Parallel CI also shows a handful of **flaky** tests that waste time and erode trust. AGENTS.md still had stale “mods not planned / not implemented” wording (cleaned in PR0).

## What

1. **AGENTS.md** — accurate modding + save-compat policy (done early).  
2. **Save resilience** — almost nothing content-side should void a run: unknown items/entities/abilities **strip and resume** (e.g. removed longsword); hard-fail only corruption, true format breaks, newer-than-game saves, or mod fingerprint mismatch.  
3. **Flaky tests** — skip noisy perf gate; harden Summon1 / vore modal / RangeN setups per designer notes.  
4. **Optional polish (if time / freebie):** tcod `tiles` FutureWarning migration.

## Out of scope

- New gameplay features  
- Balance / content packs  
- Full rewrite of save system or ECS  
- Guaranteeing load of **future** saves on **older** game binaries (backward load of newer format) unless easy  

## Success

- Designer can ship often without forcing “new game only.”  
- Documented save version + migration rules agents must follow.  
- Known flakes fixed or quarantined with a clear reason.  
- AGENTS.md matches reality.
