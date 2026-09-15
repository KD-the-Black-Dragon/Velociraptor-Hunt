# Tasks: solo-duel-career

**Do not implement any PR until the designer authorizes** (e.g. “implement SD1” or “implement the whole solo-duel-career batch”).

---

## Setup (design)

- [x] Create change folder (`proposal.md`, `design.md`, `tasks.md`)
- [x] Designer authorize whole batch (implement)

---

## PR SD1 — Campaign style on career

- [x] `campaign_style`: `solo` | `company` on `CareerState` + save
- [x] New Game → `solo`; missing field on load → **`solo`** (pre-alpha)
- [x] Targeted tests

---

## PR SD2 — Solo hub

- [x] Skip starter ally picks for solo
- [x] Hub options without Hire / Assign team
- [x] max_deployed_allies 0 for solo
- [x] Targeted tests + manual checklist

---

## PR SD3 — Solo match pool + spawn guard

- [x] Offer only 1v1-eligible cards
- [x] Runtime guard: exactly one enemy spawn
- [x] Enough solo cards for early rounds (`d1_*` … duel cards)
- [x] Targeted tests + manual checklist

---

## PR SD4 — Instant Action + docs + sign-off

- [x] Instant Action lists only solo-eligible cards for chosen kind
- [x] DESIGN_CANON + live specs; Company freeze note
- [x] Full targeted suite; designer manual sign-off (2026-08-10)

---

## Out of scope

- Deleting team systems  
- Company feature expansion  
- New combat systems beyond gates/filters  
