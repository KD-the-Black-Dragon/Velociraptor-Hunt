# Manual testing checklist — PR6 (stock catalog)

Run: `python -m src.main`

TEMP starter potions still present (removed in PR7). Also watch floor loot as you descend.

## Catalog feel

- [ ] Healing potions still common early (especially basic heal)
- [ ] Discovery / blinking appear early; less dominant deep
- [ ] Haste / might / tele / alliance / antacid show up mid-dungeon
- [ ] Examine text for each potion is clear and has **no numbers**
- [ ] `i` inspect still shows heal HP amounts for heals only

## Smoke all effects (starter kit OK)

- [ ] Heal, discovery, haste, might, antacid, teleport, blink, alliance

## Automated

- [x] Stock load tests / summon / blink / teleport suites
