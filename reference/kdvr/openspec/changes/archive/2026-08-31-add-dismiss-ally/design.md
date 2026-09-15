# Design: Dismiss ally (Shift+D)

| Field | Value |
|-------|-------|
| **Date** | 2026-08-31 |
| **Status** | Accepted — archived 2026-08-31 |
| **Change id** | `add-dismiss-ally` |
| **Live spec target** | Extend `openspec/specs/command-allies/spec.md` (Dismiss requirement) and/or thin companion section; help/tutorial lines |

**Terminology:** defeated, stunned, digested — never kill/die/death. Dismiss is **exit / remove**, not defeat.

---

## Creative intent (designer)

Players who prefer solo play, or who want a clean slate of allies on the next floor, need a deliberate **Dismiss** command. Shift+D enters targeting; confirming a good ally removes them with a quiet exit line.

---

## Resolved decisions

| Topic | Decision | Source |
|-------|----------|--------|
| Binding | **Shift+D** (`KeySym.D` + Shift). Plain `d` stays Drop. | Designer |
| Turn cost | **Free** — no turn on open, cancel, invalid, or successful dismiss | Designer Q&A |
| Valid target | **Good** NPCs only | Designer |
| Engulfing goods | Non-issue — goods never engulf others | Designer note |
| Engulfed good | Not dismissible as a free ally; tile selection prefers the visible predator → invalid line | Designer Q&A |
| Targeting rules | **Same cursor / visibility family as Examine / throw** | Designer Q&A |
| Invalid message | Exact: `Invalid target. (Allied NPCs only)` | Designer |
| Success message | Exact: `{NPC name} exits the dungeon.` | Designer |
| Busy / engulfed copy | Same invalid line (no distinct busy text) | Designer |
| Help / tutorial | Help overlay **yes**; tutorial Actions list **yes** (short line) | Designer Q&A |
| Defeat / XP / loot | **No** — clean despawn (`entity.clear()`-class), do **not** `fire_entity_defeated` | Design default |
| Esc | Cancels targeting, no message (Examine-like) | Design default |
| After invalid Enter | Remain in dismiss targeting | Design default |
| After successful dismiss | Exit targeting mode | Design default |
| Player engulfed / stunned | May open dismiss (free UX tool); still only good free allies are valid | Design default |
| Modal stacking | Blocked while other gameplay modals active (inventory, examine, throw, vore, etc.), same class as Examine entry | Design default |

---

## Requirements

### 1. Input and mode

| Item | Decision |
|------|----------|
| Enter mode | Shift+D while PLAY and no blocking modal |
| Cursor | Starts on player tile (same as Examine) |
| Move | Movement keys / numpad move cursor, clamped to map (reuse Examine cursor move helper or shared cursor util) |
| Confirm | Enter / keypad Enter |
| Cancel | Esc → leave mode, no log |
| HUD / cursor draw | Reuse Examine-style cursor presentation where practical (distinct mode flag so input routes correctly) |

Implementation may add `DismissState` parallel to `ExamineState`, or a shared lightweight “map cursor mode” with a dismiss confirm handler — prefer **smallest clear split** from Examine so Enter semantics stay separate.

### 2. Validity

A tile confirm is **valid** iff the primary fighter/NPC on that tile (Examine-style “top” fighter pick, excluding player) has **`Alignment.GOOD`** and is **not engulfed** (no `Engulfed` tag / not held as prey).

**Invalid examples:** empty floor, player, evil, neutral (rabbit), item-only tile, stairs, engulfed ally (if ever selectable), tiles with only a predator holding prey.

Invalid → log invalid line; **do not** clear mode.

### 3. Removal

On valid confirm:

1. Resolve display name (same naming helper other log lines use — proper name when present).
2. Log `{name} exits the dungeon.` via `src/messages.py`.
3. Remove entity cleanly from the world (clear components / registry entry). No combat defeat pipeline, no XP, no corpse/loot unless some unrelated system already ties to clear (prefer none).
4. Reset dismiss mode.

Followers / come-here / good-quota: removal naturally drops follower count for descent and future floors; no special quota rewrite.

### 4. Discovery

| Surface | Text (approx.) |
|---------|----------------|
| Help overlay | `Shift+D - dismiss ally (target good NPC)` |
| Tutorial Actions | Short line near other action keys, e.g. `Shift+D to dismiss an ally you no longer want` |

### 5. Messages

| Event | Message |
|-------|---------|
| Success | `{NPC name} exits the dungeon.` |
| Invalid | `Invalid target. (Allied NPCs only)` |

No kill/defeat wording.

### 6. Save / performance

- No new save fields.
- O(1) despawn; targeting is player-driven cursor work only.

---

## Risks / edge cases

| Risk | Mitigation |
|------|------------|
| Shift+D vs Drop `d` | Require Shift; document in help |
| Accidental dismiss | Targeting + Enter; Esc cancels; no AoE |
| Stats inflation | Skip `fire_entity_defeated` |
| Engulfed ally | Invalid / unreachable via predator priority |
| Tests pinned to live names | Use fixtures / helpers; assert message templates |

---

## Out of scope

- Dismiss all / confirm dialog  
- Neutrals  
- Ordering walk-off-map  
- Changing Come Here behavior  
