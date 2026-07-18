# Proposal: ai-personality-fuzzy

## Problem

Even with perfect player measure tools, enemies that only rush adjacent and bump force roguelike pace. AI must use the **same move vocabulary** with **personality-weighted fuzzy choice** (CK2-like attributes, not a tiny enum of archetypes).

## Solution

Open **`ai-personality-fuzzy`**: 1–10 attributes (e.g. Ferocity, Intelligence, Tenacity, Bloodlust), species ranges, per-turn candidate intents scored by geometry fitness + weights + noise.

## Scope

### In

- Attribute schema + roll/ranges on entities
- Candidate intents: hold measure, step, footwork, poke/commit, brace, clinch bias when legal
- Fuzzy scorer; JSON weights; imperfect noise
- Seed ranges for current match fauna

### Out

- Full CK2 trait encyclopedia
- Perfect tactical search
- Implementing player footwork/attacks (must already exist)
- Crowd-driven AI; full grapple redesign

## Dependencies

- **Hard:** `weapon-measure`, `player-combat-commands` (footwork + measure attacks)
- **Preferred:** `footwork-momentum`, `ready-actions` (brace as candidate)
- **Must not implement first** among battle-pace modules

## Program

See `openspec/changes/battle-pace-program/ROADMAP.md` (module **BP-A**).
