# Design: Improve text UX

| Field | Value |
|-------|-------|
| **Date** | 2026-07-08 |
| **Status** | Accepted — archived 2026-07-09 |
| **Change id** | `improve-text-ux` |
| **Spec targets** | Extend relevant live specs (vore/digestion/ui) or thin `openspec/specs/text-ux/spec.md` on acceptance |

---

## Resolved decisions

| Topic | Decision |
|-------|----------|
| `{predator}` | Required in NPC→player **vore** attempt/success modal phases (format before display, same name helper as logs). Digestion player modal already formats; verify/keep. |
| `{prey}` in player modals | **Not** supported / not required. Never needed for player-as-prey prose. |
| Unknown placeholders (e.g. `{predtaor}`) | Leave **verbatim** — data/modder issue, obvious in play. Prefer not crashing on bad keys (safe format that leaves missing keys literal). |
| SCHEMA markup | List canonical categories + aliases from `src/log_markup.py` / `MessageCategory`. |
| Min-window clip | Word-wrap + clamp X/Y to console; long lines wrap. |
| New-game Y/n position | Lower band like mod-mismatch notice (`height//2 + offset`), clear of title banner. |
| Chrome | Shared dark panel + padding + simple border for bare confirms/notices. Unified helper for menu/play confirms (layout + chrome; input can stay per-screen). |
| Help overlay | **No change.** |
| Log font scope | **All word-heavy sentence UI:** vore, digestion narrative, examine description, inventory (i/q/w/W/v), ground pickup, Y/n dialogs with body text. Fixed-width OK for map, short tokens, main menu options, Options/Mods **lists**. Full sentence in fixed-width when log font is available = **bug**. |
| Font trial (PR4) | **Player digestion modal** — **approved** (size +2, width 80% of prior max, top + side padding). |
| Narrative modal model | Digestion proportional dialog is the **reference** for: vore attempt/success modals, examine descriptions (same chrome + log font + padding language). |
| Game over font | **Title fixed** (“GAME OVER”); **body / fate lines log font**. |
| Dialog font unity | **Whole dialog** (body + footers like `Proceed? (Y/n)` / `Esc: close`) uses log font when the dialog is proportional — not mixed fonts in one panel. |
| Font rollout (PR5) | Narrative first (vore + examine) using digestion model; then utilitarian lists after inventory layout is decided. |
| Inventory / utilitarian modals | **Relaxed** vs narrative: may use multi-column layout; log font still preferred for labels. **Full 26-item layout is open design** (see below). |
| On-screen NPC swallow/digest log color | **Default `caution`** when the player **witnesses** (predator and/or prey in player FOV — same visibility gate as today’s on-screen NPC vore logs) a **successful** NPC swallow of another NPC, or **digestion complete** of NPC prey. No per-line markup required. |
| Explicitly **not** caution-default | Failed NPC vore attempt (miss) lines; **offscreen** vore/digest atmospheric lines (heard only, not witnessed in FOV). |
| Manual markup | Inline `[[category]]…[[/]]` still works and may override segments; default message category for these witnessed success lines is `caution` unless a future rule says otherwise. |
| PR batching | PR1 → **PR2 caution logs** → PR3 dialog chrome → PR4 font trial → PR5 font rollout → PR6 accept. |

---

## Extra idea #2 — “single menu dialog API” (elaboration)

Today each prompt reimplements:

- centering
- Y position (some mid-screen, some lower)
- capital-Y / invalid message
- bare text vs box

**Value add:** one small helper (or two: `MenuDialog` for main-menu overlays, `PlayDialog` for in-run confirms) that owns:

| Concern | Why |
|---------|-----|
| Vertical band | Always under logo / safe zone at min height |
| Word wrap | Long “saved game will be overwritten…” stays on-screen |
| Chrome | One look for all Y/n notices |
| Input contract | Capital Y / n / Esc already duplicated 4+ times |

**Not** a heavy framework — just stop copy-pasting slightly different `console.print` blocks. New-game, mod-mismatch, quit, mods-enter, macguffin can all call it. If you prefer minimal scope, PR2 can still unify **layout + chrome** without forcing one input state machine.

---

## Implementation notes

### 1. `{predator}` in vore modals

Path: `pick_vore_narrative_variant` → `VoreModalState.open_attempt` currently stores **raw** phase strings.

Fix: when opening player-targeted vore modal, format each phase with predator display/log name (same as `format_npc_vore_line` / `_format_player_digestion_phase`). Use safe format: missing keys stay in the string.

### 2. SCHEMA

Expand “Inline log color markup” with table of canonical names and aliases (mirror code). **Done PR1.**

### 2b. Default caution for witnessed NPC swallow / digest (added midstream)

**In scope (default log category = `MessageCategory.CAUTION`):**

| Event | Visibility | Notes |
|-------|------------|--------|
| NPC successfully vores another NPC | On-screen path (`log_visible` today: predator **or** prey in player FOV) | Hit/success line only — `npc_vore_hit` / pool hit templates |
| NPC digestion of NPC prey completes | Same on-screen gate as existing digest-complete logging | `digestion_complete` lines when logged as witnessed |

**Out of scope (keep current default / not force caution):**

| Event | Why |
|-------|-----|
| NPC vore **miss** / fail | User exclusion |
| Offscreen vore / offscreen digest | “Heard only,” not witnessed in LOS/FOV |
| Player engulfed / player digestion modals | Different surfaces; not this rule |
| Good pleas / other combat logs | Unchanged unless already colored |

**Implementation sketch:** at `message_log.add(...)` call sites for the two in-scope paths, pass `category=MessageCategory.CAUTION` (or equivalent). Prefer not requiring data authors to wrap every line in `[[caution]]…[[/]]`.

### 3–4, F. Layout + chrome

Extract shared render for “centered dialog box with wrapped lines”:

- Background fill (existing modal bg tone is fine)
- Margin from console edges ≥ 1
- Optional multi-line body + error line

Apply to new-game confirm, load/mod notices, quit, mods-enter, macguffin (sentence prompts).

### 5. Proportional font trial — **approved**

**Trial target:** player digestion completion modal (`src/ui/proportional_dialog.py`).

**Approved look (designer, 2026-07-08):**

- Log font size **+2** vs message log
- Max panel width **80%** of original fraction (0.72 → ~0.576 of root)
- Extra **top** pad (~1 line height) and **horizontal** inset (+14px beyond log pad)
- Chrome: dark fill + border; footer “Press Enter”

**Rollout (PR5+):** reuse this as the model for **narrative** modals (vore attempt/success, examine). Utilitarian inventory/pickup lists need a separate layout solution (next section) before forcing a single tall column in proportional font.

**Policy going forward:** if UI shows a full English sentence, it must use log font when available.

### 5b. Full inventory list layout — **locked** (2026-07-08)

**Problem:** Inventory has up to **26** letter slots (`a`–`z`). A single column overflows any reasonable modal height.

**Playtest aid (TEMP):** Removed after PR6 sign-off (was 25 daggers + robes for multi-column layout playtest).

**Direction: multi-column grid** (not scroll-first).

| Decision | Choice |
|----------|--------|
| Columns | **Dynamic by window width**, max **3** |
| Fill order | **Down column, then next** (a–z column-major) |
| Long names | **Wrap within cell** (not ellipsis) |
| Short vs many | **Same rule:** 1 column when few (≤8); up to 2 for medium (≤14); up to 3 when many **and** width allows |
| Panel width | **Content-hugging** for 1–3 cols (short labels stay compact; long names grow width up to max). Do not stretch columns to fill the window. |
| Filtered lists (wield/quaff/evoke/pickup) | **Same multi-column chrome** |
| Font | **Same as digestion modals** (`dialog_font_from_log_font`: log face +2) |

**Surfaces:** inventory inspect list, drop, wield, wear, quaff, evoke pick, ground pickup. Item **detail** (inspect letter) stays single-column narrative (same font).

### 6. Fixed-width remains

- Map viewport entities/tiles  
- Sidebar short labels and bars  
- Status corner short status  
- Main menu option rows / Options / Mods **list chrome** (short labels OK fixed)

---

## PR plan

| PR | Scope |
|----|--------|
| **PR0** | This proposal/design/tasks; AGENTS pointer |
| **PR1** | `{predator}` in player vore modals + safe format; SCHEMA markup categories; new-game confirm lower + wrap (shared helper start) — **done** |
| **PR2** | Default **caution** color for on-screen NPC swallow success + on-screen NPC digest-complete logs (not miss, not offscreen) |
| **PR3** | Shared dialog chrome + apply to quit / mods-enter / macguffin / menu notices; min-size clamp |
| **PR4** | **Trial:** proportional digestion modal — **approved** (tweaks applied) |
| **PR4b** | Inventory full-pack layout design + TEMP full starter loadout for playtest (this pause) |
| **PR5** | Narrative rollout: vore + examine (digestion model); inventory only after multi-column design locked |
| **PR6** | Utilitarian inventory/pickup multi-column + log font (as decided) |
| **PR7** | Remaining sentence dialogs / game-over body; acceptance |

Do not start PR4 until designer signs off the PR3 trial look.

---

## Non-goals

- Redesigning help overlay  
- Changing combat log sentence content  
- Forcing proportional on pure ASCII map art  
