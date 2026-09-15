# Design: add-offscreen-vore-messages

Full design document: `openspec/design-work/68a0b2dc-design-doc.md`

## Summary

Per-entity offscreen string arrays in `entities.json`. When NPC vore **succeeds** or NPC **digestion completes** and neither predator nor prey is in player FOV, log one random atmospheric line. Visible events keep existing pools. Missing data → silent.

## JSON keys (snake_case)

| Key | Use |
|-----|-----|
| `offscreen_ov` / `offscreen_cv` / `offscreen_av` | Successful vore hit |
| `offscreen_ov_digest` / `offscreen_cv_digest` / `offscreen_av_digest` | Digestion complete |

## Hooks

- `try_resolve_npc_vore` — hit + not visible → offscreen vore line
- `complete_npc_digestion` — not visible → offscreen digest line