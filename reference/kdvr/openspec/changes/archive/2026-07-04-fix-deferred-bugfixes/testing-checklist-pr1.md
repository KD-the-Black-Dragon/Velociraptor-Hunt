# Manual checklist — PR1 (message log word wrap)

Run: `python -m src.main`

## Word wrap

- [ ] Trigger a long message (e.g. examine a floor item or entity with a long description, or read several combat lines).
- [ ] Confirm long lines **wrap** within the message log panel instead of being cut off at the right edge.
- [ ] Confirm wrapped continuation lines use the **same color** as the first line of that message.

## Scrolling behavior

- [ ] Add several messages quickly; the log still shows the **most recent** content at the bottom.
- [ ] A single very long message may occupy multiple log rows; newer messages still push older content up.

## Regression

- [ ] Short messages (e.g. "You miss the wolf.") still display on one line as before.
- [ ] Message log panel background and position unchanged.
- [ ] No debug stdout lines in terminal (PR0).