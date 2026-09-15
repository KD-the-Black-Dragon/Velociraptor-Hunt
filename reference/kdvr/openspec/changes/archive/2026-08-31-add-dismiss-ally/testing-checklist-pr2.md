# Manual testing — PR2 (Dismiss discovery + specs)

**How to run:** `python -m src.main`

PR2 adds Help / Tutorial discoverability. Core dismiss behavior shipped in PR1.

## Happy path

- [ ] F1 / `?` help lists **`Shift+D - dismiss ally (target good NPC)`** near Come here
- [ ] Tutorial Actions includes **Shift+D to dismiss an ally you no longer want**
- [ ] Spot-check PR1: Shift+D → target good → Enter → exits message; plain `d` still Drop

## Edge cases / regression

- [ ] Help still lists Come here (`1`)
- [ ] Shift+W wear / plain `d` drop still work
- [ ] Dismiss still free (no turn) and invalid line unchanged

## Automated

```bash
python -m pytest tests/test_dismiss_ally_pr1.py -v
```

Full suite deferred until release-build anticipation (per AGENTS).
