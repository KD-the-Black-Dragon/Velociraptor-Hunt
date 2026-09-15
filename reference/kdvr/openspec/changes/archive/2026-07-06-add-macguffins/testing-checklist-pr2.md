# Manual checklist — PR2 (spawn)

Run game: `python -m src.main`

- [ ] Macguffin glyphs visible on eligible floors (examine cursor)
- [ ] NPCs do not walk onto macguffin tiles
- [ ] Player can step onto macguffin tiles
- [ ] Multiple macguffins on one floor occupy distinct tiles
- [ ] Macguffins do not share tiles with floor runes

Automated: `pytest tests/test_macguffins_pr2.py -q`