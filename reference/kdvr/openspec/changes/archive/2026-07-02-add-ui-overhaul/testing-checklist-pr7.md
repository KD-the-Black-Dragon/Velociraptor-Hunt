# Manual checklist — PR7

Run: `python -m src.main`

## Sidebar NPC list

- [ ] Visible **evil** NPCs appear below your name/HP (nearest first)
- [ ] Visible **good** NPCs appear at the **bottom** of the sidebar (nearest at bottom edge)
- [ ] **Neutral** NPCs do not appear in the sidebar
- [ ] NPCs outside FOV do not appear
- [ ] Each NPC row shows truncated name + HP bar
- [ ] With many evil/good NPCs visible, overflow lines show (`+k evil`, `+k good`)

## Regression (PR2–PR6)

- [ ] Player name + HP still at top of sidebar
- [ ] Message log 8 lines; map viewport camera-centered
- [ ] Main menu options visible at bottom