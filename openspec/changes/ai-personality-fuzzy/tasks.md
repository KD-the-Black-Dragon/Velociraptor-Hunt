# Tasks: ai-personality-fuzzy

**Do not implement any PR until the designer authorizes that PR by name.**

**Do not start implementation PRs until BP-W and BP-P footwork + measure attacks are playable.**

## Setup (design)

- [ ] Write `design.md` (final attr list, candidate intents, weight tables, noise)
- [ ] Designer accept design

## PR A1 — Attribute schema

- [ ] 1–10 attrs on entities; ranges; spawn roll
- [ ] Targeted tests + manual checklist

## PR A2 — Candidate intents

- [ ] AI may choose existing player-parity actions (footwork, measure attack, etc.)
- [ ] Targeted tests + manual checklist

## PR A3 — Fuzzy scorer

- [ ] Geometry fitness (weapon measure) + attr weights + noise
- [ ] JSON-driven weights
- [ ] Targeted tests + manual checklist

## PR A4 — Content ranges

- [ ] Current foes get personality ranges; bosses pin values if needed
- [ ] Targeted tests + manual checklist

## PR A5 — Playtest tune

- [ ] JSON tuning from designer feedback
- [ ] Designer sign-off for module
