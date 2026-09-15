# Manual checklist — PR2 (acceptance)

Run: `python -m src.main`

## NPC vore log matrix

- [ ] Visible wolf NPC vore **hit** — entity line with predator/prey names
- [ ] Visible wolf NPC vore **miss** — entity miss line
- [ ] Off-screen wolf OV/CV/AV **hit** — atmospheric lines (no swallow pool text)
- [ ] Off-screen wolf vore **miss** — silent
- [ ] Off-screen wolf OV/CV/AV **digest** — atmospheric lines (no on-screen digest pool text)
- [ ] Visible wolf digest — on-screen `digestion_complete` style line

## Player paths unchanged

- [ ] Player vore attempt still opens `vore_narratives` modal (not NPC log lines)

## Automated

- [ ] Full `pytest tests/` green