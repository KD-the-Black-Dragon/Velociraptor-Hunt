# Proposal: Offscreen Vore Message Logs

## Why

NPC vore and digestion off-screen are silent today unless predator or prey is in the player's FOV. Players get no ambient feedback from distant evil activity.

## What

- Six optional string-array fields per entity in `entities.json` (`offscreen_ov`, `offscreen_cv`, `offscreen_av`, `offscreen_ov_digest`, `offscreen_cv_digest`, `offscreen_av_digest`)
- On successful **off-screen** NPC vore hit: random line from the matching `offscreen_{type}` array
- On **off-screen** NPC digestion complete: random line from `offscreen_{type}_digest`
- No message for off-screen failed vore; no message when arrays are missing or empty
- On-screen behavior unchanged

## Out of scope

- Player vore modal / player digestion modal paths
- Offscreen messages for failed vore or digestion ticks mid-process
- Item or ability hooks

## Spec target

`openspec/specs/vore/spec.md` and `openspec/specs/digestion/spec.md` (PR2)