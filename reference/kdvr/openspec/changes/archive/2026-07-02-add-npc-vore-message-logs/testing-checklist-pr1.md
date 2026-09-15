# Manual checklist — PR1 (off-screen CV/AV content)

Run: `python -m src.main`

## Wolf off-screen (dungeon tone)

- [ ] Off-screen CV vore hit — crushing / muffled thrashing atmospheric line
- [ ] Off-screen AV vore hit — displaced air / unseen prey line
- [ ] Off-screen CV digest — wet squelch line
- [ ] Off-screen AV digest — compression fading line

## Shark off-screen (aquatic tone — if you can spawn shark in water)

- [ ] Off-screen CV/AV lines differ in tone from wolf (water/current wording)

## Regression

- [ ] Off-screen OV vore and digest still work for wolf
- [ ] Visible on-screen vore hit/miss unchanged

## Automated

- [ ] `pytest tests/test_offscreen_vore_messages.py tests/test_offscreen_digest_messages.py tests/test_npc_data_pr1.py::test_load_default_entities_json` green