# Manual testing — PR6 rain + clues

How to run: `python -m src.main`

## Happy path

- [ ] Status shows rain cycling: **light rain** → **rain** → **heavy rain** → back (about 10 AUT per step)
- [ ] Heavy rain shortens how far you can see
- [ ] Walking leaves mud prints (`"`); they are easier to notice in heavy rain
- [ ] When the raptor moves nearby you may get **Movement N/E/…** and a `!`
- [ ] Heavy rain more often hides real movement and more often shows false **Wind** / **Rain in the canopy** with `?`
- [ ] Sneak is quieter than run (harder to hear)
- [ ] Esc still leaves; F targeting still works

## Audio

- [ ] No crash from missing rain samples (fade is a stub; no wav in the tree yet)

## Pointer

`openspec/changes/velociraptor-hunt/tasks.md` (PR6).
