# Manual checklist — PR3 (inline log markup + speech introductions)

Run: `python -m src.main`

## Speech introductions (data-driven)

- [ ] Walk adjacent to a knight with no evil visible → introduction line appears in **white** (`SPEECH`).
- [ ] Subsequent knight log lines (combat, etc.) remain **grey** routine color.

## Inline markup (optional JSON content)

If you add a test line with markup to any log string (e.g. `[[magical]]glows[[/]]` in a narrative pool):
- [ ] Colored word renders in the correct hue on the same wrapped row.
- [ ] Text before/after the span uses the message default category.

## Regression

- [ ] Word wrap still works for long single-color and multi-color lines.
- [ ] Category colors from PR2 unchanged for non-markup messages.
- [ ] No debug stdout without `DEBUG_STDOUT=1`.