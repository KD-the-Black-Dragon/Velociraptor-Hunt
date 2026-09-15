# Manual testing — PR13–PR15 intelligence pack

How to run: `python -m src.main`

One playtest for the whole pack.

## Rifle scope (PR13)

- [ ] Aimed rifle: **no peripheral** — a line, longer than walk; **blind inside ~3 tiles**
- [ ] Shotgun / revolver aimed cones still feel like a wedge
- [ ] Hipfire / walk cone still wide

## Sounds and glyphs (PR13)

- [ ] Sneak makes **no** `?`. Walk sometimes, run almost always.
- [ ] Medium/heavy rain: fewer real steps heard, **more** false `?`
- [ ] `?` appears on the tile left, not the landing tile
- [ ] Visible red `r` is never covered by `?`. Last-known dim `r` beats `?` when you cannot see her.

## Mind (PR14)

- [ ] She sits in 3-deep grass, then relocates; does not mill in the open
- [ ] Light rain: conservative. Heavy: daring, including a rear rush if your back is turned
- [ ] Just before light rain she turtles
- [ ] Aimed at / shot at: she leaves the cone instead of shuffling in it
- [ ] Two nearby running/jogging sounds in a short span: she treats that as “you are there”
- [ ] Diagonal-forward (she can; you cannot)
- [ ] She does not know empty magazines

## Difficulty (PR15)

- [ ] Nightmare feels faster / longer storms than Easier
- [ ] She still does not cheat coordinates

## Regression

- [ ] Training F2, dart, rain beds, Esc, Continue Hunt
