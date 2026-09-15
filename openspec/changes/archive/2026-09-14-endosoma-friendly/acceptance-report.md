# Acceptance — Endosoma-friendly post-swallow (PR1)

**Status:** Accepted 2026-09-14. Designer playtest signed off; change archived.

**Live spec:** `openspec/specs/hunt/spec.md`  
**Canon:** this folder’s `DESIGN_CANON.md` plus foundation `archive/2026-09-04-velociraptor-hunt/DESIGN_CANON.md` and deferred pack `archive/2026-09-12-hunt-deferred/DESIGN_CANON.md`

## Landed

Options **Post-swallow** (Digest default / Endosoma). Digest is unchanged loss copy. Endosoma: own swallow-angle and post-belly path pools, no belly glyph darkening, GAME OVER *The raptor got you.*, Stats **Times swallowed** (same `digested` counter). Session shuffle bags (not saved). Donor OV/CV/AV Options rows and first-run vore-prefs screen hidden; code kept. Player-facing general copy uses swallow / swallow you whole.

## Tests

Targeted suites for PR1 passed during implementation. Full `pytest tests/` was not required for this close.

## Next

No further PRs in this change. Next product work needs a new `openspec/changes/<name>/`.
