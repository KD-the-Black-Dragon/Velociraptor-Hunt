# Proposal: Instant action (Ctrl+B practice match)

## Problem

Main menu **Ctrl+B** crashes (legacy KDVR arena path). Designers need a fast practice bout against a **known opponent set** without career hub.

## Solution

**Ctrl+B** → **two phases**: (1) Green or Red via keys **1** / **2**; (2) type a **`match_cards.json` card id** (e.g. `r1_wolves`, `r2_mixed_pack`) with a **dynamic filtered list** of valid cards for that kind. Start a **solo** sand-pit match with static PC loadout; on bout end, return to the **main menu**. No save/career side effects.

## Scope

### In

- Ctrl+B two-phase UI (kind → card id)
- Opponent sets from **`data/match_cards.json`** by card `id`
- Dynamic list of valid card ids (+ titles), filtered as user types
- Solo match; sand pit; static gear
- Isolation; recap → main menu
- Tests + checklist

### Out

- Freeform entity lists (`rat x3` typed by hand)
- Career economy / Past Runs
- Loadout UI, allies in instant action
- Headless sim CLI

## Success

Ctrl+B → 2 → type `r1_wolves` (with list helping) → fight alone → Enter on recap → main menu; career save untouched.
