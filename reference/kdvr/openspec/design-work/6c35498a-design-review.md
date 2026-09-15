## Design Document Review: Ally Improvement (Re-review)

**Document:** `openspec/design-work/6c35498a-design-doc.md`  
**Change id:** `add-ally-improvement`  
**Reviewer:** design-doc-reviewer (codebase-verified)  
**Review type:** Re-review after author revisions

### Summary

**0 open issues — approved for implementation**

All 13 issues from the initial review are properly addressed. Revisions align with the codebase.

**Verdict:** Approved for implementation (PR0)

**Open issue count:** 0

### Open Issues

*None.*

### Strengths

- Exact engine hook order, combat rescuer/RNG wiring, and data parse semantics are unambiguous.
- Rescue AI branch fits existing `pick_good_chase` / `find_predator_holding_prey` / bump-attack path.
- PR independence sound (PR0 → PR1/PR2 parallel → PR3).
- Command Allies fully deferred in `todo` spec.