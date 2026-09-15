# Proposal: NPC Vore Message Logs (Consolidated)

## Why

NPC-on-NPC vore logging was partially implemented ahead of design. Off-screen logging shipped with six flat JSON fields that diverge from the dominant typed-object pattern. Wolf and shark lack CV/AV off-screen content, so those events are silent.

## What

- Consolidated design for all NPC vore **log** surfaces (on-screen hit/miss, off-screen hit, off-screen digest)
- Migrate `offscreen_ov` … `offscreen_av_digest` → `offscreen_vore` and `offscreen_digest` objects keyed by OV/CV/AV
- Add placeholder CV/AV off-screen lines for wolf and shark
- Update specs and SCHEMA to match
- Remove dead `pick_npc_vore_message()` helper

## Out of scope

- Player `vore_narratives` modals and `digestion_player_modal`
- Off-screen failed vore messages
- Global fallback pools for off-screen events
- New evil species beyond content updates to wolf/shark

## Spec targets

`openspec/specs/vore/spec.md`, `digestion/spec.md`, `npc-data/spec.md`, `enhancements-3/spec.md` (PR2)

## Full design

`openspec/design-work/2a662950-design-doc.md`