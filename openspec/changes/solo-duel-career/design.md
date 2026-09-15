# Design: Solo duel career + Company freeze

| Field | Value |
|-------|--------|
| **Change** | `solo-duel-career` |
| **Status** | **Shipped + designer sign-off** (manual checklist OK 2026-08-10) |
| **Product** | Gladiavore |
| **Related** | `gladiavore-foundation`, `instant-action`, `match_cards.json`, hub/roster |

**Terminology:** defeated / stunned / digested.

---

## 1. Intent (locked from designer)

| Style | Description | Status |
|-------|-------------|--------|
| **Solo Duels** | Career roguelike: multi-battle career, shop/upgrades on **PC only**, **1-on-1** fights only | **Active focus** |
| **Company** | Current product: hire allies, deploy, multi-opponent cards, Talk | **Temporarily retired** — keep on ice |

Do **not** delete team/multi code. Prefer **gates, filters, and career style flags**.

---

## 2. Campaign style model

### 2.1 Identifier

```text
campaign_style: "solo" | "company"
```

| Value | Meaning |
|-------|---------|
| `solo` | Duels-only career |
| `company` | Current team/multi career |

- Stored on `CareerState` (save field `campaign_style`, default **`solo`**).
- **Pre-alpha:** no shared saves — no legacy migration burden. Missing field on load → **`solo`**. New Game always creates **`solo`** until Company is re-enabled in UI.

### 2.2 How the player enters each style

| Path | Behavior (v1) |
|------|----------------|
| **New Game** | Always **Solo Duels** (no style picker unless freebie) |
| **Company** | Not offered on main menu. Re-enable later via secret hotkey, Options flag, or second menu line |
| **Load Game** | Loads whatever style the save has |
| **Instant Action** | Practice only — filter to **solo-eligible cards** so it matches the focus (still 1v1) |

**Open Q (default):** Company entry = **hidden** (no menu line) until designer reopens. Optional debug: Ctrl+something or `GLADIAVORE_COMPANY=1` — not required for v1.

---

## 3. Solo Duels — product rules

### 3.1 Career / hub

| Feature | Solo |
|---------|------|
| Gold / renown / rounds | Same skeleton |
| Shop / equip / train / heal (PC) | **On** |
| Hire / free starter allies / assign team | **Hidden** (not shown; code paths unused) |
| Starter ally gate | **Skipped** — `starter_picks_done=True` at career create |
| max_deployed_allies | **0** |
| Roster | Always empty; load ignores deploy |
| Patrons that require allies | Skip / filter objectives that need allies |
| Talk in match | N/A (no allies) |

Hub root options (solo): e.g. Shop, Manage equipment, Training, Healing, Select next match, Return to menu. **Omit** Hire, Assign team.

### 3.2 Match selection

- Offers drawn only from cards that are **solo-eligible**:
  - Exactly **one** enemy entry in `enemies`, and  
  - That entry’s **`count` == 1**  
  - (Optionally `max_allies` forced 0 at runtime regardless of JSON)

- Cards with packs (`rat`×3, mixed packs, etc.) remain in `match_cards.json` for Company; **not offered** in Solo.

- Green/red, round bands, economy: same systems, solo card subset only.

- If the solo pool is empty for a round, **relax round filter** or fall back to any solo-eligible card (must never offer multi).

### 3.3 Match runtime

| Rule | Solo |
|------|------|
| Enemies | Enforce spawn of **exactly one** living foe (assert/guard) |
| Allies | Never spawn |
| Map | Sand pit (unchanged) |
| Combat | Full Battle Sport + vore as today |
| Recap | Downtime as today |

### 3.4 Content duty (data)

Author / retag enough **1v1** cards across rounds so the solo career has variety (many cards already are 1v1: gnoll solo, fox duel, green spar with 1 rat, etc.). Multi cards stay for Company.

Optional JSON field later: `"campaign_styles": ["solo","company"]` — v1 can **derive** eligibility from enemy counts without new field.

### 3.5 Instant Action

- Keep Ctrl+B two-phase flow.  
- **Card list:** only solo-eligible cards of the chosen green/red kind (same filter as career).  
- Still solo PC; no allies.

---

## 4. Company style — freeze rules

| Rule | Detail |
|------|--------|
| Code | **Leave in place** (roster, hub hire/assign, Talk, multi spawn, ally AI, digest refund, etc.) |
| Data | Multi-enemy cards **stay** in `match_cards.json` |
| Tests | Keep team/multi tests; pin `campaign_style="company"` where needed |
| Entry | **Not** default New Game; not advertised |
| Docs | `DESIGN_CANON` / this change note: Company is **on ice**, not deleted |

When unfrozen later: show style picker or “Company Campaign” menu line; New Game can branch.

---

## 5. Implementation strategy (preserve work)

```text
career.campaign_style
        │
        ├─ solo  → hub filter, card filter, spawn guard, skip starters
        └─ company → current behavior (unchanged code paths)
```

Prefer:

1. **Branch at UI/offer/spawn**, not deleting modules.  
2. Thin helpers: `is_solo_career(career)`, `solo_eligible_card(def)`, `hub_options_for_style(style)`.  
3. No hard delete of `roster.py`, ally AI, etc.

---

## 6. Save compatibility

| Risk | Mitigation |
|------|------------|
| New field `campaign_style` | Default **`solo`** if missing (pre-alpha; no public save base) |
| Solo save with empty roster | Normal |
| Company saves | Only relevant if someone re-enables Company entry; then style is written explicitly |

---

## 7. PR plan

| PR | Deliverable |
|----|-------------|
| **SD1** | `campaign_style` on career + new_career/load; New Game → solo; company load still works |
| **SD2** | Hub solo options; skip starter picks; force max deploy 0 |
| **SD3** | Match offer filter + spawn 1v1 guard; solo card content pass if pool thin |
| **SD4** | Instant Action solo-only card list; tests; DESIGN_CANON; manual checklist |

Optional single-batch authorization (like Battle Sport / Instant Action).

---

## 8. Resolved decisions

| ID | Decision |
|----|----------|
| SD-TWO-STYLES | Solo Duels active; Company on ice, not deleted |
| SD-1V1 | Solo = one opponent entity, count 1 only |
| SD-NO-TEAM | No hire/deploy/Talk/allies in Solo |
| SD-NEW-GAME | New Game creates Solo |
| SD-DATA | Multi cards stay in JSON for Company |
| SD-PRE-ALPHA | No shared saves — missing style defaults to **solo**; no company-legacy load path required |

---

## 9. Open questions (defaults if silent)

| ID | Question | Default |
|----|----------|---------|
| Q-SD-MENU | Company re-entry method? | **Hidden** entirely for now |
| Q-SD-OLD-SAVE | Missing `campaign_style`? | **`solo`** (pre-alpha; no legacy audience) |
| Q-SD-CARD-FIELD | Explicit `solo` tag on cards? | **Derive** from enemy count; tag later if needed |
| Q-SD-NAME | UI label “Solo Duels” vs “Duel Career”? | **Solo Duels** |

---

## 10. Non-goals

- Removing roster/Talk/ally AI from the repo  
- Redesigning combat for pure 1v1 math beyond existing systems  
- Full Company balance pass while frozen  
