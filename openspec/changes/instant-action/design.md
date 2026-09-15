# Design: Instant action (Ctrl+B)

| Field | Value |
|-------|--------|
| **Change** | `instant-action` |
| **Status** | **Shipped + designer sign-off** (manual checklist OK 2026-08-10) |
| **Lineage** | Harvest UX intent from KDVR Ctrl+B; **product loop is Gladiavore match** + **`data/match_cards.json`** |
| **Related** | `data/match_cards.json`, `src/match_session.py`, `src/app.py`, `src/match_cards.py` |

**Terminology:** defeated / stunned / digested — never kill / die / death.

---

## 1. Product intent

| Goal | Detail |
|------|--------|
| Fast practice | Main menu → few keys → real bout |
| Controlled foes | Pick a **match card** (opponent set) by **card id** |
| Kind first | Choose **green** or **red** rules before picking the set |
| Real rules | Same AUT / balance / measure / AI / vore as career matches |
| Isolation | No autosave, career store, or Past Runs |
| Exit | Bout end → recap → **main menu** |

---

## 2. Entry

| Item | Rule |
|------|------|
| Hotkey | **Ctrl+B** from main menu |
| Visible menu | No labeled row required for v1 |
| Save prompt | **None** |
| Name entry | **Skip** — fixed name e.g. `Sparrer` |
| Onboarding | Unchanged; Ctrl+B only when main menu is reachable |

---

## 3. Two-phase setup (locked)

```text
MENU --Ctrl+B--> PHASE A: kind --1/2--> PHASE B: card id --Enter--> MATCH
                   Esc ↓                    Esc ↓
                    MENU <---- back one / or Esc to menu (see below)
```

### Phase A — Green or Red

| Item | Rule |
|------|------|
| Title | `Instant Action` |
| Prompt | Choose match rules |
| **1** | **Green** (mercy / no permanent digest) |
| **2** | **Red** (full stakes) |
| Esc | Main menu |
| Other keys | No-op (or ignore) |

Selected kind is stored for the bout and **defines match rules** (`card.kind` for the session).

### Phase B — Opponent set (match card id)

| Item | Rule |
|------|------|
| Title | `Instant Action — {Green\|Red}` |
| Prompt | Type a **match card id** |
| Source of truth | **`data/match_cards.json` → `cards[]`** |
| Valid id | A card’s **`id`** field (e.g. `r1_wolves`, `r1_bats`, `r2_mixed_pack`, `r1_green_spar`) |
| Input | Case-sensitive buffer; type the id; Enter confirms |
| Esc | Back to **Phase A** (kind pick), not straight to menu — second Esc on Phase A exits to menu |

### Dynamic valid list

- Build list from **all cards** in `match_cards.json` (or filter — see below).
- Each line shows: **`{id}`** — `{title}` (and optionally original data kind for clarity).
- **Dynamic filter:** as the buffer changes, list shows only cards whose **`id`** (and optionally **title**, case-insensitive) **contains** the typed substring. Empty buffer → show all eligible cards.
- Multi-column layout if height/width allows; scroll later if needed (v1: scroll or truncate with “…” if many).

**Eligible cards vs kind (resolved):**

| Approach | Rule |
|----------|------|
| **List filter** | Show **only cards whose `kind` matches Phase A** (green pick → green cards only; red → red cards only). |
| **Bout kind** | Always the Phase A choice (matches the card’s data kind under this filter). |

This keeps “valid options” aligned with green/red. If a pack is needed under both rules, author two cards in JSON (or a later dual-kind tool).

### Validation (Phase B Enter)

| Failure | Message |
|---------|---------|
| Empty | `Enter a match card id.` |
| Unknown id | `Unknown match card id.` |
| Id exists but wrong kind for Phase A | `That card is not a {green\|red} match.` (should be rare if list is filtered) |

On success: start match using that card’s **`enemies`** array (and title for recap), **solo**, sand pit.

---

## 4. Match setup

### 4.1 Map and combat

| Item | Rule |
|------|------|
| Map | **Sand pit** (~20×20) — locked |
| Combat | Full `MatchSession` (Battle Sport, vore, HUD) |
| Allies | **None** — force `max_allies: 0` / no deploy even if card allows allies in career |
| Difficulty | Options → Difficulty at start |
| Economy | No gold/renown applied to any persistent career |

### 4.2 Card usage

| Field from JSON | Instant action use |
|-----------------|--------------------|
| `id` | Typed selection key |
| `title` | Recap / log header |
| `kind` | Must match Phase A (list filtered); session uses Phase A kind |
| `enemies` | Spawn plan (`entity_id` + `count`) |
| `payout_mult` | Ignored for persistence (may show 0 in recap) |
| `max_allies` | Forced **0** for instant solo |
| `min_round` / `max_round` | **Ignored** (any card id is available in instant action) |

### 4.3 Ephemeral career

Throwaway `CareerState`: fixed name, no allies, static PC stats/weapon (current match defaults). **No** career store or autosave writes.

Flag: `instant_action=True` on session and/or app.

### 4.4 Isolation

| Action | Behavior |
|--------|----------|
| Autosave | No-op |
| Ctrl+S | Soft “Instant action — not saved.” (no file write) |
| Past Runs | No entry |
| Hub | Never entered |

---

## 5. Outcomes and exit

| End | Behavior |
|-----|----------|
| Win / loss / digest / green surrender | Recap → Enter → **main menu** |
| Recap footer | `Press Enter to return to the main menu.` |
| Ctrl+Q | Existing quit flow; confirm → menu without save |

Clear match session + ephemeral career on exit.

---

## 6. App phase flow

```text
MENU
  Ctrl+B → INSTANT_KIND (1 green / 2 red)
             Esc → MENU
             1|2 → INSTANT_CARD (type card id, dynamic list)
                      Esc → INSTANT_KIND
                      Enter valid → MATCH (instant)
                                      recap Enter → MENU
```

Prefer new phases or a small state machine inside one `InstantActionState` with `step: kind | card` rather than reusing KDVR evil-entity entry.

---

## 7. Implementation sketch

| Piece | Notes |
|-------|--------|
| `src/instant_action.py` | State (kind step / card step), filter list, start match |
| `match_cards` loader | List cards by kind; resolve id → enemies |
| `start_match` | `instant_action=True`, force solo, custom recap footer, no economy apply |
| `app.py` | Wire Ctrl+B; remove crash stubs for broken ENTITY_ENTRY path or repurpose cleanly |
| `messages.py` | All strings |
| Optional JSON | Caps / help only — **card content stays in `match_cards.json`** |

### PRs

| PR | Deliverable |
|----|-------------|
| **IA1** | Two-phase UI: kind pick + card id entry with dynamic filtered list; Esc navigation; no crash |
| **IA2** | Start solo sand-pit match from card; isolation flags; static loadout |
| **IA3** | All ends → menu; Ctrl+S soft message; tests; checklist |

---

## 8. Resolved decisions

| ID | Decision |
|----|----------|
| IA-HOTKEY | Ctrl+B |
| IA-PHASES | (1) Green/Red via **1** / **2**; (2) type **match card id** |
| IA-CARDS | Opponent sets = **`match_cards.json` card `id`s** (e.g. `r1_wolves`) |
| IA-LIST | Dynamic filter on typed buffer; eligible = cards of selected kind |
| IA-MAP | Sand pit |
| IA-SOLO | No allies |
| IA-GEAR | Static for v1 |
| IA-EXIT | Main menu after bout |
| IA-KIND-PREFIX | Dropped — kind is Phase A only |

---

## 9. Open questions (defaults if silent)

| ID | Question | Default |
|----|----------|---------|
| Q-IA-FILTER-TITLE | Filter list by title substring as well as id? | **Yes** — id or title contains buffer |
| Q-IA-SCROLL | Many cards overflow? | Truncate with note; scroll only if freebie |

---

## 10. Non-goals

- Freeform `rat x3` entity syntax (use cards instead)  
- Career rewards / Past Runs  
- Loadout editor  
- KDVR 1×10 hallway  
- Headless sim CLI  
