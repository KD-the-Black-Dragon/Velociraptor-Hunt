# Design: Deferred Bugfixes (UI + AI)

## Resolved Decisions (2026-07-04)

| # | Decision |
|---|----------|
| 1 | Default log color: **very light grey** — midpoint between midrange grey `(128,128,128)` and white `(255,255,255)` → stock **`(192, 192, 192)`** (playtest may tune) |
| 2 | Seven message categories with fixed RGB constants (see below); unused categories reserved for future content (`SPEECH` for ally introductions in PR3) |
| 3 | Per-word JSON colors: **in scope**, **own PR** for easy revert |
| 4 | Log font must be **non-fixed-width**; everything else stays CP437 |
| 5 | No font preference — agent picks a readable narrow proportional monospace TTF |
| 6 | Log history capacity **100** entries |
| 7 | Full-log scroll: one arrow key = one **wrapped display line** |
| 8 | Full log and help are **free meta commands** — available anytime (including modals, rest animation) |
| 9 | Help does **not** list debug keys |
| 10 | Help opens on **F1** and **?** (Shift+/); **Esc** dismisses |
| 11 | Help documents rest (`5`) and full log (`Ctrl+P`) |
| 12 | Status corner shows **max HP rune bonus** as its own row |
| 13 | `accuracy_damage` and combat buffs on **one row** (“combat buffs row”) |
| 14 | Pursuit momentum **3–6** turns; give-up after **8–12** turns without regaining LOS |
| 15 | Good–neutral corridor fix: **swap on bump** when good follows/chases; root cause is AI `can_move_to` treating neutrals as hard blocks (player uses `try_action` swap) |
| 16 | Neutral fix: **explore oscillation only** (no flee-loop changes) |
| 17 | Capitalization **Option 1 only**, own PR |
| 18 | Capitalize: line start; after `.` `?` `!` only — **not** after `-` |
| 19 | Capitalization applies to **`{predator}`/`{prey}` template paths** only (not hardcoded player modal strings) |
| 20 | Debug stdout gated behind env flag (not removed) |
| 21 | **Many small PRs** preferred over large batches |
| 22 | **PR10 playtest sign-off (partial):** two-tile ping-pong fixed; **wait-on-recent** and greedy goals leave neutrals clustered in small reachable pockets and can **freeze near the player** — acceptable shim until `better-npc-exploration` ships BFS reachable goals for **all alignments** |

---

## Message categories

Constants in `src/message_log.py` (names illustrative):

| Category | RGB (stock) | Use |
|----------|-------------|-----|
| `ROUTINE` | `(192, 192, 192)` | Attacks, misses, hits, pickup, dialogue, exploration, mundane combat |
| `DANGER` | `(255, 80, 80)` | Digestion, stunned, command blocked by enemy presence, imminent game over |
| `CAUTION` | `(255, 220, 80)` | Rest interrupted by enemy/alarm, future poison |
| `POSITIVE` | `(80, 220, 120)` | Healed, escaped engulfment, regen milestones if ever logged |
| `MAGICAL` | `(100, 220, 255)` | Rune activation, player buffs, enemy debuffs |
| `SPEECH` | `(255, 255, 255)` | NPC dialogue such as good-ally `introduction` lines (data-driven in PR3) |
| `RARE` | `(255, 100, 255)` | Reserved: bosses, MacGuffins, unique one-time events |

`MessageLog.add(text, *, category=MessageCategory.ROUTINE)` replaces ad-hoc `fg=` at call sites.

### Current message → category mapping (implementation guide)

| Category | Examples (non-exhaustive) |
|----------|---------------------------|
| ROUTINE | Combat hit/miss/defeat, swap places, door open, examine, welcome, wait/rest start/end (non-danger), NPC mundane logs, going deeper messages |
| DANGER | Engulfed pack blocked, going deeper while engulfed, stunned too tired (if treated as danger), player being digested, item destroyed?, evil-in-FOV rest pre-check |
| CAUTION | Rest halt: under attack, danger approaches, ally alarm; future poison |
| POSITIVE | No longer stunned, freed from predator, fully healed (rest end), rune max HP heal portion if logged |
| MAGICAL | Rune activated log line |
| SPEECH | *(none today — PR3 wires `introduction` from entities.json)* |
| RARE | *(none today)* |

**Rest module alignment:** pre-check/halt messages that were red under `add-rest-until-healed-or-danger` split per new scheme — **danger** for “too dangerous to rest” / engulfed; **caution** for attack interrupt and ally alarm; **positive/default** for successful rest end.

Update `openspec/specs/enhancements-1/spec.md` color notes when rest PR colors migrate.

---

## PR0 — Debug stdout env gate

Gate all development `print(..., flush=True)` behind `DEBUG_STDOUT=1` via `src/debug_log.py` (`debug_print`, `debug_stdout_enabled`). Truthy values: `1`, `true`, `yes`, `on` (case-insensitive).

| Source | Messages |
|--------|----------|
| `ai.py` | evil frustration, good attempted player swap |
| `map_gen.py` | rejected attempts |
| `engine.py` | floor_init rejects, prefetch miss |
| `floor_prefetch.py` | hit/miss/ready/failed |

Tests that assert stdout (e.g. `test_evil_frustration_debug_to_stdout`) set env in test or patch helper.

---

## PR1 — Message log word wrap

- Add `wrap_log_entry(text, width) -> list[str]` (reuse `_wrap_words` logic from `render.py`).
- `render_message_log` / panel: expand entries to wrapped lines; show tail `max_lines` wrapped lines.
- Each wrapped sub-line inherits parent `LogEntry` color/category.
- Unit tests: long string wraps; HUD shows end of wrapped stream.

---

## PR2 — Message color categories

- Add `MessageCategory` enum + RGB table above.
- Migrate all `message_log.add(..., fg=ALERT_MESSAGE_FG)` and bare adds to explicit categories.
- Deprecate `ALERT_MESSAGE_FG` / `DEFAULT_MESSAGE_FG` in favor of categories (aliases during migration OK).
- Tests: spot-check category on representative messages (rest caution, combat routine, rune magical).

---

## PR3 — Per-word JSON colors + speech introductions (implemented 2026-07-04)

**Revertible slice.** Inline markup in any string passed to `MessageLog.add`:

```json
"introduction_log_category": "speech",
"introduction": ["I am {name}, sworn to aid you."],
"npc_vore_hit": { "OV": ["{predator} [[magical]]glows[[/]] as it swallows {prey}!"] }
```

- Parser: `src/log_markup.py` — `[[category]]text[[/]]`; aliases (`cyan`, `white`, …); unknown tags stay literal.
- `LogEntry.segments` stores colored spans; `render_message_log` prints segments with x-offset per row.
- `introduction_log_category` on `EntityDefinition` (data-driven); knight stock value `speech`.
- `ally_introduction.py` uses `definition.introduction_log_category` (defaults to `ROUTINE` when omitted).

---

## PR4 — Proportional log font

- Load a narrow monospace **TTF** (e.g. bundled under `data/fonts/`).
- Render **message log region only** using tcod font rendering API (separate from CP437 tile blit for map).
- Map viewport, sidebar, status corner, menus: unchanged CP437 tileset.
- Fallback: if TTF path fails, log warning once and keep CP437 for log (test documents fallback).

---

## PR5 — Full log overlay (`Ctrl+P`)

New `LogOverlayState` on engine:

| Input | Action |
|-------|--------|
| `Ctrl+P` | Toggle overlay |
| Arrows / TYUGHJBNM / numpad | Scroll ±1 wrapped display line |
| PageUp / PageDown | Scroll ±1 page (viewport height in lines) |
| `Esc` | Close overlay |

- `MESSAGE_LOG_CAPACITY` → **100**.
- Build wrapped line list from all stored entries on open/refresh.
- Footer: `Esc: close | Arrows: line | PgUp/PgDn: page`
- Render full root console (hide map/sidebar) similar to game-over screen.
- **Not blocked** by vore modal, inventory, examine, rest animation.

---

## PR6 — Help overlay (`F1`, `?`)

New `HelpOverlayState`:

| Input | Action |
|-------|--------|
| `F1` or `?` (Shift+/) | Open |
| `Esc` | Close |

Static curated content (code constant or `data/help.txt`):

- Movement: arrows, numpad, TYUGHJBNM
- Actions: i, d, w, W, q, v, x, `, pickup, descend, wait, **rest `5`**
- Meta: **Ctrl+P** full log, **F1**/**?** help, **Ctrl+Q** quit confirm
- Footer: `Esc: close`
- **No** debug keys (R, S, F2, F3, F4).

---

## PR7 — Rune effects (status corner)

`PlayerStatusEffects.extra_rows` built from `PlayerProgression`:

| Condition | Row (≤10 chars) |
|-----------|-----------------|
| `bonus_max_hp > 0` | `HP +N` |
| combat buffs row | Combine acc/min/max dmg/ac e.g. `+0.2 +1D +1A` or similar compact notation |
| Only non-zero bonuses shown | |

Update `openspec/specs/floor-runes/spec.md` — HUD SHALL show permanent bonuses in status corner.

---

## PR8 — Narrative capitalization (Option 1)

`enforce_sentence_capitalization(text: str) -> str` in `src/text.py`:

- Capitalize index 0 if alphabetic.
- After `.`, `?`, `!` followed by whitespace → capitalize next alphabetic char.
- Do **not** treat `-` as a boundary.

Apply in:

- `format_npc_vore_line`
- `_format_digestion_line`
- Off-screen vore format path
- Any other `{predator}`/`{prey}` template formatters

Also applied to `digestion_player_modal` template paths (dash/hyphen is **not** a sentence boundary).

Unit tests: `"the wolf"` → `"The wolf"` at start; `"gone. the rabbit"` → `"gone. The rabbit"`; `"triumph - you"` unchanged after dash.

---

## PR9 — Pursuit momentum

Extend `AIState`:

```python
chase_momentum_direction: tuple[int, int] | None = None
chase_momentum_turns_left: int = 0
chase_blind_turns: int = 0  # turns without LOS to quarry while chasing memory
```

**When** entity had visible quarry and now uses `last_known_*` memory target:

1. **Reach phase:** path toward memory; on each step update `chase_momentum_direction` to successful direction.
2. **On arriving** at memory tile without regaining LOS: enter momentum — continue `chase_momentum_direction` for `rng.randint(3, 6)` turns; if blocked, pick best alternative excluding backtrack; if boxed in, hold still.
3. **Give-up (reach phase):** increment `chase_frustration` when a step toward last-known fails (blocked bump, no legal step); at `rng.randint(8, 12)` clear memory + momentum → explore. Blind-turn timer does **not** run while still pathing to memory.
4. **Give-up (momentum phase):** after momentum turns exhaust without regaining LOS, clear memory + momentum → explore.

Applies to **Good** and **Evil** chase modes (not neutral flee).

---

## PR10 — Neutral explore anti-stuck (shim — partial fix)

**Playtest (2026-07-04):** Signed off as *good enough for now*. Two-tile ping-pong is fixed. Side effects: neutrals wander within small constrained regions (e.g. 2×5, 3×5); **wait** when all legal steps revisit `recent_positions` can cause a **full stop near the player** (forbidden player tile + recent tiles exhaust legal moves). Proper fix deferred to **`better-npc-exploration`** (BFS reachable goal pick + explore frustration for **all alignments**; retire this shim).

Extend `AIState`:

```python
recent_positions: deque[Position]  # maxlen 6
```

On neutral explore/flee-without-evil:

- After move, push position; if position appears ≥2 times in deque → clear `explore_goal`, pick new goal.
- If no legal move avoids recent positions → **wait** (no move).

Does not change flee-from-evil behavior.

---

## PR11 — Good–neutral corridor swap

**Root cause:** `_choose_chase_direction` uses `can_move_to`, which rejects tiles occupied by `BlocksMovement` entities (including neutrals). Player movement uses `try_action`, which swaps. Good AI never steps into neutral tiles, so knights stall in corridors.

**Fix:**

- Add `can_step_for_chase(...)` (or `allow_swappable_bump` on `can_move_to`) that returns **True** when dest holds an NPC that `can_npc_swap(actor, defender)` would allow.
- Use this in `_choose_chase_direction` for **good** chase/follow only, and **only for neutral** defenders (`GOOD_CHASE_SWAPPABLE_ALIGNMENTS`). Good must not path into other good NPCs (avoids swap ping-pong when multiple knights follow). `pick_good_chase` already limits follow targets to player and attack targets to evil.
- Movement still goes through `try_action` so swap executes on bump.

Neutrals **never** initiate swap (unchanged).

Tests: knight follows player through 1-wide corridor with rabbit; knight ends past rabbit.

---

## Overlay interaction

Both overlays are **meta UI** layered on present:

```
if help_overlay.active: render help; consume Esc/F1/?
elif log_overlay.active: render log; consume scroll/Esc/Ctrl+P
else: normal engine input
```

Ctrl+P while help open: close help or ignore (pick: **toggle log closes help** — document in PR).

---

## Acceptance

- Targeted pytest per PR; full suite on final PR only.
- Manual checklist per PR per `WORKFLOW.md` Rule 3.
- Archive to `openspec/changes/archive/YYYY-MM-DD-fix-deferred-bugfixes/` after final sign-off.