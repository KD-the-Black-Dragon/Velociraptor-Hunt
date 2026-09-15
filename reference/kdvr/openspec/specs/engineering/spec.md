# engineering Specification

## Purpose

Cross-cutting **maintainability** rules for agents and contributors. Not a player-facing feature domain.

**Terminology:** defeated, stunned, digested — no kill/die/death.

---

## Requirements

### Requirement: Message catalog for message-log prose

Player-visible **message log** lines (including **caution** / **danger** / **positive** / **magical** categories) SHALL be produced via named functions in `src/messages.py` (or a clearly named submodule of that catalog if the file later grows too large).

#### Scenario: New combat or item log line

- GIVEN a system needs a new message-log string
- WHEN the string is implemented
- THEN it is added as a function in `messages.py`
- AND call sites use `messages.<name>(...)` rather than inline string literals

#### Scenario: What stays outside the catalog

The following MAY remain outside `messages.py`:

| Kind | Examples |
|------|----------|
| Data-driven narrative blobs | Vore / digestion / introduction / rescue lines from `entities.json` and related data files |
| Restored save log history | Decoding previously saved log entry text |
| Session / debug logs | `session_log`, `debug_print`, crash reports |
| Exception / internal errors | Tracebacks, `ValueError` messages |
| Modal / menu chrome not in the message log | Confirm dialogs, options labels, help text (prefer consistency, but not this requirement’s scope) |

#### Scenario: Wording stability

- GIVEN an existing player-facing log line is moved into `messages.py`
- WHEN the migration lands
- THEN the exact wording is preserved unless a designer-approved copy change is in scope

### Requirement: Prefer one catalog file

`messages.py` SHOULD remain a single discoverable catalog for message-log strings unless size clearly harms maintainability. Do not invent an i18n key system or external string files without an explicit change.

### Requirement: Entities stay unified for modding

Entity definitions including vore narrative text SHALL remain loadable from a single entity data surface (`entities.json` / mod entity files). Do **not** force mod authors to maintain a second narrative file per monster unless the designer revisits this decision.
