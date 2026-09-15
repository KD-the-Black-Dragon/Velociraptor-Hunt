# Design: add-npc-abilities

Full design document: `openspec/design-work/7fa6b405-design-doc.md`

## PR1 shipped

- `ranged_accuracy` / `ranged_min_damage` / `ranged_max_damage` on entities + `Fighter`
- `Range2` on wolf (playtest); ranged damage 4–4, melee 6–6
- `resolve_ranged_engagement()` — shoot only in `[2, N]`; adjacent melee; stunned 0 HP → close
- FOV-gated shoot log lines in `src/messages.py`