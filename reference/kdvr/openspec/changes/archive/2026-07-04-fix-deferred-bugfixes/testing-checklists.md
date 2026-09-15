# fix-deferred-bugfixes — Consolidated Manual Checklist

Run: `python -m src.main`

Per-PR detail: `testing-checklist-pr0.md` … `testing-checklist-pr11.md` in this archive folder.

---

## Automated gate

```bash
python -m pytest tests/test_debug_log.py tests/test_message_log_wrap.py tests/test_message_log_categories.py tests/test_log_markup.py tests/test_log_font.py tests/test_log_overlay.py tests/test_help_overlay.py tests/test_status_corner_runes.py tests/test_narrative_capitalization.py tests/test_chase_pursuit_momentum.py tests/test_neutral_explore_antistuck.py tests/test_good_neutral_corridor_swap.py -q
```

---

## PR0 — Debug stdout

- [ ] No debug stdout during normal play (`DEBUG_STDOUT` unset)
- [ ] With `DEBUG_STDOUT=1`, AI frustration / map debug lines appear on console

## PR1 — Log wrap

- [ ] Long log lines wrap within the panel; colors preserved per sub-line

## PR2 — Message categories

- [ ] Routine grey, danger red, caution yellow, positive green, magical cyan
- [ ] Rest interrupt / rune / combat messages use expected colors

## PR3 — Per-word markup

- [ ] Knight introduction line (if sampled) shows multi-color segments when enabled

## PR4 — Log font

- [ ] Message log uses narrow proportional font; map/sidebar unchanged

## PR5 — Full log (Ctrl+P)

- [ ] Ctrl+P opens scrollable full log anytime (including modals)
- [ ] Esc closes; line/page scroll works

## PR6 — Help (F1 / ?)

- [ ] F1 and `?` open help; Esc dismisses
- [ ] Documents rest `5` and Ctrl+P; no debug keys listed

## PR7 — Rune status corner

- [ ] Collected rune HP and combat buffs visible in status corner

## PR8 — Capitalization

- [ ] Vore/digestion template lines capitalize sentence starts and after `.?!`
- [ ] Dash is not a sentence boundary

## PR9 — Pursuit momentum

- [ ] Good/evil pursue to last-known, then momentum, then give-up
- [ ] Wolves do not instantly quit on first corridor bump

## PR10 — Neutral anti-stuck (partial)

- [ ] No two-tile ping-pong
- [ ] Broader wander / player-proximity freeze → deferred to `better-npc-exploration`

## PR11 — Good–neutral corridor

- [ ] Knight swaps through rabbit in 1-wide corridor while following
- [ ] Two knights do not freeze swapping with each other
- [ ] Knights attack evil, follow player only