# Proposal: Sidebar NPC columns and overflow fix

## Problem

NPC health bars in the sidebar do not behave well below 1080p-class heights. Overflow summaries (`+# evil`) disappear before individual NPC rows are dropped. Longer NPC names need a two-column layout. **Wide** preset selection must reliably change map vs sidebar widths on the next new game.

## Scope

- Two-column evil/good bands with per-column caps (5 evil, 2 good)
- Dynamic height budgeting that always preserves overflow summary lines
- Name truncation only in two-column mode
- Restore **Wide** preset application via consistent `baseline_layout` refresh on resize/options
- Update `openspec/specs/ui-layout/spec.md`

## Out of scope

- Neutral NPC sidebar entries
- Numeric NPC HP in sidebar
- Player HP bar layout changes