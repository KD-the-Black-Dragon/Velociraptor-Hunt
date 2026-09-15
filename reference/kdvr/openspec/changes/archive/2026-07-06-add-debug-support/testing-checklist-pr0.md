# Manual checklist — PR0 (OpenSpec bootstrap)

No gameplay changes. Verify artifacts only.

- [ ] `openspec/changes/add-debug-support/proposal.md` exists
- [ ] `openspec/changes/add-debug-support/design.md` exists
- [ ] `openspec/changes/add-debug-support/tasks.md` exists
- [ ] `openspec/changes/add-debug-support/log-interpretation-guide.md` exists
- [ ] PR order in design.md matches tasks.md (PR1 → PR2 → PR3 → PR4 → PR5)
- [ ] User decisions reflected: `{user_data}/logs/`, always on, entities-only validation, soft ability warnings
- [ ] `log-interpretation-guide.md` is a usable message-in-a-bottle for future triage / Grok Build
- [ ] `openspec/WORKFLOW.md` active change pointer → `add-debug-support`