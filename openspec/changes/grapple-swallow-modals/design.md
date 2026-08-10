# Design: Grapple / swallow modals + swallow escape retune

**Change:** `openspec/changes/grapple-swallow-modals/`  
**Related:** `match-hud-ux` (reaction panel pattern), foundation §9 vore/grapple, `data/match_vore.json`

---

## Fantasy (locked intent)

| Phase | Feel | Player agency |
|-------|------|----------------|
| **Grapple** | Wrestling match — legitimate fight for freedom | Break away (real odds), counter, brace |
| **Swallow** | Coup de grâce — prey is utterly exhausted; world fades | Struggle (miraculous ~1%) **or** conserve strength to last slightly longer inside |
| **Engulfed** | Digestion crisis | Near-helpless thrash; rescue / regurg remain the real outs |

**UI metaphor for swallow:** distracting, interface-blocking — PC and player lose clear awareness of the arena. Not a “press Enter to continue” slideshow; still **command choices** each prey AUT.

---

## UI

### Grapple modal (PC prey only)

- **Placement / style:** Same red low-right modal family as **INCOMING!** (bordered panel; does not cover map/status/log).
- **Headline:** `{PredatorName} grapples you!` (dynamic via `entity_log_name` / display name).
- **Body (short):** Grapple HP meter line; option keys.
- **Options (unchanged keys):**
  - `1` Break away  
  - `2` Counter-strike  
  - `.` / wait: brace  
- **Remove** from status-column chrome (status may still show a one-line “in grapple” if useful, but the **modal owns the crisis copy**).

### Swallow modal (PC prey only)

- **Placement / style:** **Large, interface-blocking** modal (center or near-full panel haze + panel). Map/status/log **obscured or heavily muted** — intentional disorientation.
- **Not** a recap-style Enter-dismiss; input is **only** swallow choices (plus green surrender / quit if already allowed).
- **Headline / phase:** e.g. `SWALLOWING` + predator name + phase `i/n`.
- **Narrative body:** Seed 1–2 stub lines per phase index from JSON (or `messages.py` templates); structure ready for longer prose later.
- **Options:**
  1. **Struggle** — attempt miracle break free  
  2. **Conserve strength** — no escape roll; mark endurance for stomach phase  
- Footer keys match options. No free thrash-from-any-direction that looks like movement (movement keys may map to Struggle or be ignored — **recommend:** only `1`/`2` accepted so it feels modal).

### Engulfed

- Out of this PR’s large-modal scope unless cheap: keep status/footer thrash UX; apply **conserved strength** bonus when digest starts.

---

## Math (JSON-driven)

### Grapple break-away

Unchanged formula (`break_away_base_chance` + grapple HP fraction bonus). This is the **legitimate** escape window.

### Swallow struggle escape

| Today (wrong) | Target |
|---------------|--------|
| `break_away_chance(...) * 0.35` ≈ **12–26%**/try | **Fixed ~1%** per struggle (`swallow_struggle_escape_chance: 0.01` in `match_vore.json`) |

- Do **not** scale swallow escape by remaining grapple HP (war already ended at 0).
- Ally-as-prey auto-break during swallow: same 1% (or lower) — do not leave allies on the old high formula.

### Conserve strength (recommended default)

| Choice | Immediate | Later (ENGULFED) |
|--------|-----------|------------------|
| Struggle (fail) | AUT spent; narrative fail line | No bonus |
| Struggle (success, ~1%) | Release; end grapple | — |
| Conserve | AUT spent; no escape roll; `conserved_strength += 1` (cap e.g. 3) | Each point adds **+1** to effective `digest_strikes_to_end` **or** reduces one digest strike’s damage — **prefer +1 strikes needed per conserve, max +2** so red runs don’t become free wins |

Green still aborts before lethal digest per existing rules.

### Other outs (unchanged intent)

- Ally damage → force release (assist fraction)  
- Predator low HP regurg  
- Predator defeated  

These remain the **non-miracle** outs once swallow starts.

---

## Implementation sketch

1. Extend present path: `match_grapple_modal_lines` / `match_swallow_modal_payload` (fullscreen-ish texture like recap haze + panel).  
2. Status lines: drop full grapple control block for PC-held cases (modal owns it).  
3. `_prey_break_away`: branch SWALLOW → JSON 1% chance; separate message keys.  
4. Swallow input: only `1` struggle / `2` conserve (not every direction).  
5. `GrappleState.conserved_strength: int = 0`.  
6. Tests: chance unit test; modal line content; struggle does not use grapple formula; conserve increments field.

---

## Resolved decisions

| Topic | Decision | Date |
|-------|----------|------|
| Grapple UI | Red modal like INCOMING; `{name} grapples you!` | 2026-08-04 |
| Swallow UI | Large interface-blocking **interactive** modal (not Enter-only) | 2026-08-04 |
| Phase fantasy | Grapple = real escape; swallow = coup de grâce | 2026-08-04 |
| Swallow self-escape | **~1% per struggle** (JSON) | 2026-08-04 |
| Swallow choices | Struggle vs conserve strength (last longer inside) | 2026-08-04 |
| Swallow modal chrome | Narrative top-center only; bottom `1 - struggle \| 2 - conserve strength`; no phase counters/explanations | 2026-08-04 |
| Conserve mechanic | +1 digest endurance per conserve, **no hard cap** (winded prey focusing on breath) | 2026-08-04 |
| Green vore | Control grabs OK; **must release before lethal digest** (swallow phases allowed; no lethal finish) — DESIGN_CANON | 2026-07 |

---

## Open

| Topic | Notes |
|-------|-------|
| Exact conserve numbers | Default +1 strike / max +2 unless designer amends |
| Swallow prose volume | Stub first; more narrative content later |
| Whether ENGULFED also gets a large modal | Later unless freebie |
