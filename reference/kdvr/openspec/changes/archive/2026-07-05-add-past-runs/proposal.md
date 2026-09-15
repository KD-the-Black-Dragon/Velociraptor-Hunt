# Proposal: Game Over Stats + Past Runs

**Status:** Accepted — archived 2026-07-05.

## Why

Game over today shows only the player name and digestion recap. High Scores is a stub with no persistence. Players cannot review prior runs or see how far they got, how many monsters they defeated, or how many runes they collected.

## What

| Area | Deliverable |
|------|-------------|
| Run statistics | Per-run counters: player-credited monster defeats, floor runes consumed |
| Game over modal | Add monsters defeated, runes collected, depth reached; structured ending text |
| Past Runs | Replace High Scores stub with scrollable history of **all** completed runs |
| Persistence | `{user_data}/past_runs.json`, append on game over only, cap 65535 entries |
| Main menu | Rename to **Past Runs**; omit option when history is empty (like Load Game) |

**Unchanged:** quit-to-menu does not record a run; autosave wipe on game over stays as today.

## Out of scope

- Macguffin / final-boss victory endings (future module uses same game over hook + new `ending_kind`)
- Leaderboard semantics (no “high score” filtering; all runs kept)
- Export / cloud sync of past runs
- Recording abandoned or quit runs

## Related specs (update on acceptance)

- `openspec/specs/main-menu/spec.md` — Past Runs option, visibility gating, scroll screen
- New `openspec/specs/past-runs/spec.md` — recording, schema, sort order, game over recap fields

## Full design

`design.md` and PR checklist in `tasks.md`.