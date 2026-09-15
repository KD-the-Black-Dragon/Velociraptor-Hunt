# Spec: Instant action (Ctrl+B practice match)

## Purpose

Secret main-menu path to start a **solo** Gladiavore sand-pit match against a **match card** opponent set, then return to the main menu without affecting career saves.

## Requirements

### Entry

- From the main menu, **Ctrl+B** SHALL open Instant Action phase A (kind pick).
- Escape from phase A SHALL return to the main menu.
- No save-overwrite prompt; no name entry.

### Phase A — Green or Red

- **1** selects green rules; **2** selects red rules; then proceed to phase B.

### Phase B — Match card id

- Player types a **`match_cards.json` card `id`** (case-sensitive).
- The UI SHALL list cards of the selected kind, filtered dynamically by buffer against id and title.
- Escape returns to phase A.
- Enter on a valid id starts the match; unknown/wrong-kind ids show an error.

### Match

- Sand-pit map; full match combat systems.
- Solo only (`max_allies` forced to 0).
- Static default PC loadout; ephemeral career (not written to career store).
- Difficulty from current Options setting.
- No autosave; Ctrl+S MAY show that instant action is not saved.

### Exit

- Win, loss, surrender, or digest recap: Enter returns to the **main menu**.
- Abandon via quit confirm returns to the main menu without saving.

## Terminology

defeated / stunned / digested — never kill / die / death.
