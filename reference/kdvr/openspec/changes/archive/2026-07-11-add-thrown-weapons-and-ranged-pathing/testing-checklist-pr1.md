# Manual checklist — PR1 SmiteN rename

Run: `python -m src.main`

## Smite ability (dev spawn or future content)

Stock wolves have no Smite ability. PR1 is infrastructure — verify via tests or a temporary `Smite2` wolf in a throwaway mod if desired.

- [ ] Wand evoke (`v`) still hits evil targets; log uses **smite** (*"You smite the wolf for …"*)
- [ ] Wand miss uses *"You smite … but miss."*
- [ ] No regression: melee bump still uses *hit* / *miss* (not smite)

## Regression

- [ ] New game starts normally
- [ ] Evil wolves still melee chase as before (no Smite on stock wolf)
- [ ] Help overlay unchanged (throw keys land in PR6)

## Automated

- [ ] `python -m pytest tests/test_ability_parser.py tests/test_npc_abilities_smite.py tests/test_npc_abilities_knockback.py tests/test_npc_abilities_lifedrain.py tests/test_enhancements_2.py::test_message_templates_smite_and_shoot -v`