# Manual checklist — PR0 (off-screen schema migration)

Run: `python -m src.main`

## OV off-screen (unchanged strings, new JSON shape)

- [ ] Trigger off-screen wolf OV vore hit (NPC vore outside FOV) — distant gulp / muffled swallowing line appears
- [ ] Trigger off-screen wolf OV digestion complete — satisfied rumble line appears

## On-screen regression

- [ ] Visible wolf NPC vore hit still logs swallow/gulp line with predator and prey names
- [ ] Visible wolf NPC vore miss still logs a failure line

## CV off-screen (expected silent until PR1)

- [ ] Off-screen CV vore hit produces **no** log line (content lands in PR1)

## Automated

- [ ] `pytest tests/test_offscreen_vore_data.py tests/test_offscreen_vore_messages.py tests/test_offscreen_digest_messages.py` green