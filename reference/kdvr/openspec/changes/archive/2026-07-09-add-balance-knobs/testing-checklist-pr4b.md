# Manual testing checklist — PR4b (placeholder flag)

Run: `python -m src.main`

**No stock content change** — same five species, same feel.

## Happy path

- [ ] New game: bat / wolf / knight / rabbit / shark only (no new monsters)
- [ ] No load warnings about unknown `placeholder` trait
- [ ] Combat / vore / runes / difficulty still work as after PR4

## Docs only (optional read)

- [ ] `data/SCHEMA.md` has **Placeholder content checklist** for future filler species

## Automated

- [x] `python -m pytest tests/test_entity_placeholder_pr4b.py -v`
