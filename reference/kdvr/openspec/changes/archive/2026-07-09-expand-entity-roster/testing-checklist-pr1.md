# Manual testing checklist — PR1 (entity roster)

Run: `python -m src.main`

## Early floors (1–6)

- [ ] See **cave rat** (`c`) — oily ROUS examine text (not disease/stink)
- [ ] See **slime** (`j`) — silent gel examine
- [ ] **Bat** / **wolf** still present
- [ ] Rat / slime vore text feels on-theme if you get swallowed (oil/tight vs silent gel)

## Mid floors (5–16)

- [ ] **Tarantula** (`S`) appears; examine marks placeholder
- [ ] **Fox archer** (`f`) — prefers bow at range; weak up close
- [ ] **Gnoll mercenary** (`h`) — solid melee; light ranged
- [ ] **No new giant spiders** (deprecated)

## Deeper

- [ ] **Roc** (`R`) around depth 10+ (scarce flyer)
- [ ] **Owl mage** (`M`) — micro-vore text if swallowed
- [ ] **Wyvern / drake / gryphon / dragon** only at their deep bands (or force via deep descent)

## Regression

- [ ] Dog knight still ally
- [ ] Shark still water-only
- [ ] Save/load mid-run
- [ ] Stock floor gen stable with denser variety
- [ ] Performance OK on busy mid floors

## Automated

- [x] `tests/test_expand_entity_roster_pr1.py` + entity load
