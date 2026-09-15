# main-menu Specification

## Purpose

The **main menu** is the application's root UI: a minimalist title screen, navigation to new game / stubs / options, and the return target after gameplay ends or the player quits to menu. It wires **player display name**, **vore content preferences** (Oral Vore / Cock Vore / Anal Vore toggles), and **post-digestion recap** into a cohesive flow.

Builds on core, vore, digestion, **save-load**, **past-runs**, and **ui-layout**. Menu and persistence logic live in dedicated modules; gameplay remains in `GameEngine`. Menu screens use the same **tile scale** as gameplay (~2× glyph height).

**Terminology:** defeated, stunned, digested — no kill/die/death.

## Requirements

### Requirement: Main Menu Presentation

On launch, the game SHALL show a **minimalist black screen** (full console cleared to black). The title SHALL appear as the PNG logo at `images/logo.png`, **centered** in the upper band of the viewport (scaled to roughly 55–65% of viewport width, remaining above the option list). Menu options SHALL appear **below the logo**, smaller, near the bottom of the screen.

When a valid autosave exists (`SaveStore.probe()` on menu enter), options are:

1. New Game  
2. Load Game  
3. Past Runs *(only if `PastRunsStore.probe()` — see `past-runs` spec)*  
4. Options  
5. Credits  
6. Exit  

**Load Game** is omitted when no valid autosave exists. **Past Runs** is omitted when no completed-run history exists. **Credits** is always listed immediately above **Exit**. The menu therefore shows four to six options depending on probe results.

#### Scenario: Application opens to main menu

- GIVEN the player starts the application
- WHEN the window appears
- THEN the main menu is shown
- AND no dungeon gameplay is active

#### Scenario: Title and options visible

- GIVEN the main menu is active
- WHEN the frame is rendered
- THEN the title logo is centered in the upper band and visually dominant
- AND all visible menu options are listed toward the bottom (four to six per probe results)

#### Scenario: Title and options stay aligned when window width changes

- GIVEN the main menu is active
- WHEN the root console width changes (window resize)
- THEN the title logo remains horizontally centered in the viewport
- AND all menu option rows share the same left column

### Requirement: Main Menu Navigation

The player SHALL move the menu highlight with **Up** and **Down** (arrow keys and/or the project's movement key bindings where practical). **Enter** SHALL activate the highlighted option. **Escape** on the main menu SHALL be a no-op or SHALL not start gameplay (implementation may treat Escape as no-op on root menu only).

**Ctrl+Q** on the main menu SHALL be a **no-op** (does not exit the application).

#### Scenario: Highlight moves between options

- GIVEN the main menu with "New Game" highlighted
- WHEN the player presses Down twice
- THEN the third listed option is highlighted (Past Runs when history exists, otherwise Options)

#### Scenario: Enter activates option

- GIVEN "Exit" is highlighted
- WHEN the player presses Enter
- THEN the application exits

#### Scenario: Ctrl+Q on main menu is no-op

- GIVEN the main menu is active
- WHEN the player presses Ctrl+Q
- THEN the main menu remains active
- AND the application does not exit

### Requirement: New Game and Player Name

Selecting **New Game** when a valid autosave exists SHALL first show an **overwrite confirmation** overlay on the main menu:

**"A saved game exists and will be overwritten. Proceed? (Y/n)"**

- **Capital `Y`** — proceed to name entry (save files are **not** deleted yet).
- **Lowercase `n`** or **Escape** — dismiss overlay; return to main menu; existing save unchanged.

When no autosave exists, **New Game** SHALL go directly to name entry.

The **name entry** prompt: the player MAY type a display name. **Enter** with a non-empty trimmed name SHALL start a new dungeon run using that name. **Enter** with an empty or whitespace-only name SHALL start a new run with display name **"Anonymous"** (no error message). If overwrite was confirmed, autosave files SHALL be deleted **only at this point** (when the new `GameEngine` is created). **Escape** from name entry SHALL cancel and return to the main menu without starting a game; any existing save SHALL remain.

Name entry UX defaults (no alternate layout required): single-line prompt, printable ASCII, **Backspace**, max **24** characters.

The chosen name SHALL appear on the **post-digestion recap** and in the **playfield sidebar** (see `ui-layout` and core rendering requirements).

#### Scenario: Named new game

- GIVEN the name entry prompt
- WHEN the player types `Alex` and presses Enter
- THEN a new game starts
- AND the player display name is `Alex`

#### Scenario: Anonymous default

- GIVEN the name entry prompt
- WHEN the player presses Enter without entering text
- THEN a new game starts
- AND the player display name is `Anonymous`

#### Scenario: Cancel name entry

- GIVEN the name entry prompt
- WHEN the player presses Escape
- THEN no new game starts
- AND the main menu is shown

#### Scenario: Overwrite confirm declined

- GIVEN a valid autosave and the overwrite confirmation overlay
- WHEN the player presses lowercase `n`
- THEN the main menu is shown
- AND the autosave remains loadable

#### Scenario: Overwrite proceeds to name entry

- GIVEN a valid autosave and the overwrite confirmation overlay
- WHEN the player presses capital `Y`
- THEN the name entry prompt is shown
- AND the autosave is not deleted until name entry confirms

### Requirement: In-Game HUD Player Name

During active gameplay, the HUD SHALL display the player's **display name** in place of the static title **"KD's Vore Roguelike"** (currently rendered via `GAME_TITLE` in `render_hud`).

#### Scenario: HUD shows player name

- GIVEN a new game started with display name `Alex`
- WHEN the dungeon HUD is rendered
- THEN the HUD title area shows `Alex`
- AND does not show `KD's Vore Roguelike`

### Requirement: Load Game

**Load Game** SHALL appear on the main menu only when `SaveStore.probe()` finds a valid autosave. Selecting it SHALL restore the newest non-corrupt backup and enter **PLAY** immediately (no name entry). Layout SHALL resolve at the current window size using the **`ui_preset` frozen in the save**, not live global settings. An initial autosave SHALL refresh the slot in place after load.

See `openspec/specs/save-load/spec.md` for file format, fallback chain, and snapshot contents.

#### Scenario: Load restores run

- GIVEN a valid autosave for player `Alex` on floor 2
- WHEN the player selects Load Game
- THEN PLAY begins with restored state matching the save
- AND the player display name is `Alex`

#### Scenario: Load unavailable without save

- GIVEN no valid autosave files
- WHEN the main menu is shown
- THEN Load Game is not listed among options

### Requirement: Past Runs

**Past Runs** SHALL appear on the main menu only when `PastRunsStore.probe()` finds at least one completed run. Selecting it SHALL open the scrollable Past Runs screen defined in `openspec/specs/past-runs/spec.md` (two-line entries, no column headers, Escape to return).

#### Scenario: Past Runs omitted when empty

- GIVEN no past-run history on disk
- WHEN the main menu is shown
- THEN Past Runs is not listed among options

#### Scenario: Past Runs opens history screen

- GIVEN at least one completed run on disk
- WHEN the player selects Past Runs
- THEN the Past Runs screen is shown with entries sorted per `past-runs` spec

#### Scenario: Past Runs backs out

- GIVEN the Past Runs screen is shown
- WHEN the player presses Escape
- THEN the main menu is shown

### Requirement: Credits

**Credits** SHALL appear on the main menu always, immediately **above Exit**, regardless of `SaveStore.probe()` or `PastRunsStore.probe()` results. Selecting it SHALL open a full-screen informational page styled like the in-game help overlay and message log (`MESSAGE_LOG_BACKGROUND`, colored static lines, proportional Source Sans 3 when the bundled log TTF loads; CP437 fallback otherwise).

The page SHALL display:

- Title **KD's Vore Roguelike**
- Credit line: K.D. — Curator of Voracious Beasts
- Plain-text links: `patreon.com/KD_Dragon`, `furaffinity.net/user/kd` (not clickable)
- Font attributions: Source Sans 3 (SIL OFL 1.1); CP437 tile font via libtcod
- Library attributions: Python 3.11+ (PSF License Agreement), tcod, tcod-ecs, numpy, Pillow, attrs (transitive MIT)
- Footer **Esc: close** (centered)

**Escape** SHALL return to the main menu. **Ctrl+Q** on the credits screen SHALL be a no-op. URLs SHALL not open a browser or perform network requests.

#### Scenario: Credits always visible above Exit

- GIVEN the main menu is shown with any combination of Load Game and Past Runs probes
- WHEN the frame is rendered
- THEN **Credits** is listed immediately above **Exit**

#### Scenario: Credits opens informational screen

- GIVEN the main menu with **Credits** highlighted
- WHEN the player presses Enter
- THEN the credits screen is shown with title, authorship, links, and attributions

#### Scenario: Credits backs out

- GIVEN the credits screen is shown
- WHEN the player presses Escape
- THEN the main menu is shown

### Requirement: Options and Vore Content Preferences

**Options** SHALL list the three narrative types with **spelled-out UI labels**:

- **Oral Vore** (internal: `OV`)
- **Cock Vore** (internal: `CV`)
- **Anal Vore** (internal: `AV`)

Each row SHALL show an on/off indication. The player SHALL toggle types using the controls defined in design (default: **Left/Right** or **Enter** on the highlighted row). Settings SHALL map to `VoreContentPreferences` (or successor) stored globally in `{user_data}/settings.json` (see `src/user_data.py`).

Rules:

- **At least one** of OV, CV, AV MUST remain enabled at all times.
- If exactly **one** type is enabled, attempting to disable that last enabled type SHALL be a **no-op** (no change, no error required).
- Changes SHALL **persist automatically** (save on each toggle or on leaving Options — see design).
- **Escape** or a dedicated **Back** action SHALL return to the main menu with settings saved.

A **UI Layout** row SHALL cycle layout presets (**Standard**, **Wide**, …) defined in `data/ui_layout.json`. The selected preset id SHALL persist as `ui_preset` in `{user_data}/settings.json` and SHALL apply on the **next new game** (see `ui-layout` spec).

A **Fullscreen** row SHALL display **Fullscreen: Off | On** with the active value bracketed. **Left/Right** or **Enter** on the highlighted row SHALL toggle fullscreen immediately (see `ui-layout` spec). The preference SHALL persist as `window.fullscreen` in `{user_data}/settings.json`. Default on fresh install: **Off**.

An **Alternate CV Mechanics** row SHALL display **Alternate CV Mechanics: No | Yes** with the active value bracketed. **Left/Right** or **Enter** SHALL toggle the preference. It SHALL persist as `alternate_cv_mechanics` in `{user_data}/settings.json`. Default / missing / null: **No**. The value SHALL be **snapshotted onto the run at New Game** (and arena / depth-jump starts) like vore content prefs; Load Game restores the save's flag. Mid-run Options changes affect the **next** New Game only. Behavioral rules: `openspec/specs/vore/spec.md` (**Alternate CV Mechanics**) and `digestion` (**Dazed** / CV digest daze).

This **supersedes** the prior vore rule that OV is always enabled; OV MAY be disabled only when CV or AV remains enabled.

#### Scenario: Toggle Cock Vore off

- GIVEN Options with Oral Vore, Cock Vore, and Anal Vore enabled
- WHEN the player disables Cock Vore
- THEN CV is disabled in preferences
- AND OV and AV remain enabled

#### Scenario: Cannot disable last type

- GIVEN Options with only Anal Vore enabled
- WHEN the player attempts to disable Anal Vore
- THEN AV remains enabled

#### Scenario: Options persist

- GIVEN the player disabled Anal Vore in Options and returned to the main menu
- WHEN the application is restarted
- THEN AV remains disabled per saved settings

### Requirement: Vore Preferences Scope (Global Initiation Filter)

Vore content preferences are **global** (profile-level), not per-save-slot in v1. They govern **which narrative types a predator may initiate** on a **new vore attack** — type selection, attempt eligibility, and initiation-phase modal/log text. They SHALL **not** alter digestion or other **follow-through** narrative for prey **already engulfed**; that outcome uses the `narrative_type` locked on the predator at engulf time.

On **New Game**, the engine SHALL snapshot the current global preferences into the run (`GameEngine.vore_content_prefs`). That snapshot is fixed for the run until a new game starts. **Load Game** SHALL restore prefs from the save, not re-read global settings. Changing Options mid-session affects the **next** new game, not an in-progress or loaded run.

Monster spawn tables are unchanged in v1: creatures still appear even if none of their supported types are currently enabled; they simply **cannot initiate** vore until at least one shared type is enabled.

#### Scenario: New game snapshots global prefs

- GIVEN global settings with only Anal Vore enabled
- WHEN the player starts a new game
- THEN the run's initiation filter allows only `AV`
- AND predators without `AV` in their supported types do not initiate vore

#### Scenario: Engulfed follow-through ignores later pref changes

- GIVEN a player engulfed under narrative type `CV` (stored on the predator)
- AND global settings later disable Cock Vore
- WHEN digestion modal and completion narrative play
- THEN `CV` digestion content is still used
- AND initiation prefs do not re-filter the locked engulf outcome

### Requirement: Exit

Selecting **Exit** SHALL terminate the application immediately (same outcome as successful quit today).

Closing the application window (**X** button) SHALL terminate the process the same way as **Exit** (not return to main menu).

#### Scenario: Exit from menu

- GIVEN the main menu
- WHEN the player highlights Exit and presses Enter
- THEN the application closes

### Requirement: Quit Confirmation from Gameplay

**Ctrl+Q** during active gameplay (dungeon only — not during modals) SHALL **not** exit the process immediately. It SHALL open a **quit confirmation** prompt:

**"Do you want to quit? (Y/n)"**

Input handling:

- **Capital `Y`** — return to the **main menu** immediately (in-memory run discarded; resumable via Load Game if autosave succeeded).
- **Lowercase `n`** — dismiss the prompt and resume gameplay.
- **Any other key** — show message **"Please type capital 'Y' or lowercase 'n' only."** and remain on the quit prompt until valid input.

While a **modal** is active (vore narrative, digestion narrative, or post-digestion recap), **Ctrl+Q** SHALL be a **no-op**. Only **Enter** (or numpad Enter) SHALL advance the modal.

#### Scenario: Ctrl+Q opens quit confirmation

- GIVEN an in-progress game with no modal active
- WHEN the player presses Ctrl+Q
- THEN the quit confirmation prompt is shown
- AND gameplay input is suspended until the prompt is resolved

#### Scenario: Ctrl+Q during modal is no-op

- GIVEN a vore, digestion, or game-over recap modal is active
- WHEN the player presses Ctrl+Q
- THEN no quit confirmation is shown
- AND the modal remains active

#### Scenario: Confirm quit with Y

- GIVEN the quit confirmation prompt is shown
- WHEN the player presses capital `Y`
- THEN the main menu is shown
- AND the in-memory run is discarded
- AND a valid autosave remains if the quit-save succeeded

#### Scenario: Ctrl+Q queues background save

- GIVEN an in-progress game with no modal active
- WHEN the player presses Ctrl+Q
- THEN a background autosave is queued
- AND the quit confirmation prompt is shown

#### Scenario: Cancel quit with n

- GIVEN the quit confirmation prompt is shown
- WHEN the player presses lowercase `n`
- THEN gameplay resumes
- AND the quit confirmation prompt is dismissed

#### Scenario: Invalid quit confirmation input

- GIVEN the quit confirmation prompt is shown
- WHEN the player presses any key other than capital `Y` or lowercase `n`
- THEN the message `Please type capital 'Y' or lowercase 'n' only.` is shown
- AND the quit confirmation prompt remains active

### Requirement: Manual Save (Ctrl+S)

During gameplay, when the idle command gate passes, **Ctrl+S** SHALL write a synchronous autosave. On success the message log SHALL show **"Game saved."** On failure (e.g. file locked) it SHALL show **"Save failed."** without crashing. See `save-load` spec.

### Requirement: Post-Digestion Recap and Menu Return

After player digestion, the existing recap flow (digestion modal, then recap showing name and fate) SHALL remain. The recap SHALL display the player's **dynamic display name** (from New Game entry, not the stub `"Player"`). **Enter** on the recap SHALL return to the **main menu** (not `SystemExit`). **All autosave files SHALL be deleted when game over opens** (before recap); Load Game SHALL NOT appear until a new run creates a save.

The recap SHALL include a **final fate** line (e.g. digested-by wording from digestion game over), plus **Monsters defeated**, **Runes collected**, and **Depth** counts from the completed run. The recap SHALL **not** display turns survived, score, or similar run metrics. Completing game over SHALL append a past-run record (see `past-runs` spec).

#### Scenario: Recap shows player name, fate, and stats

- GIVEN a player named `Alex` who was digested with 2 monsters defeated, 1 rune, depth 4
- WHEN the game over recap is shown
- THEN the screen includes `Alex`
- AND includes digested-by fate
- AND includes `Monsters defeated: 2`, `Runes collected: 1`, and `Depth: 4`
- AND does not include turns survived or score

#### Scenario: Recap returns to menu

- GIVEN the post-digestion recap is shown
- WHEN the player presses Enter
- THEN the main menu is shown

#### Scenario: Recap menu has no Load Game

- GIVEN the player was digested and had a prior autosave
- WHEN game over opens
- THEN all autosave files are deleted
- AND the main menu after recap omits Load Game until a new run saves

### Requirement: Debug Keys During Gameplay

Debug keys **R**, **F2**, and **S** SHALL remain active during gameplay after the main menu exists (unchanged from current behavior).

## Supersedes

| Spec | Change |
|------|--------|
| `digestion/spec.md` | Game over Enter → main menu (not exit); no score on recap |
| `vore/spec.md` | OV no longer forced always-on; options menu owns toggles |
| `core-roguelike/spec.md` | Application entry at main menu; HUD shows player name; quit confirmation on Ctrl+Q |
| `save-load/spec.md` | Normative autosave, load, wipe-on-defeat behavior |

## Acceptance Criteria

1. Launch shows black title menu; four to six options per probe results (Credits always above Exit).
2. New Game with overwrite confirm when save exists; name entry with Anonymous fallback; name on digestion recap and in HUD.
3. Load Game restores autosave when present; omitted when absent. Past Runs shows completed-run history when present; omitted when absent.
4. Options toggles Oral Vore / Cock Vore / Anal Vore with at-least-one-enabled rule; persisted.
5. Options cycles UI layout preset (Standard / Wide); persisted; applies on new game.
6. Options toggles fullscreen (Off / On); immediate effect; persisted in `window.fullscreen`.
6b. Options toggles Alternate CV Mechanics (No / Yes); default No; snapshotted at New Game; see `vore` / `digestion` specs.
7. Exit and window close terminate app; Ctrl+Q on menu is no-op; Ctrl+Q in play shows Y/n confirmation and queues save; Ctrl+S manual save when idle.
8. Digestion recap Enter returns to menu with run stats (no score line); game over wipes autosave and records past run.
9. Vore/digestion narrative pools respect saved preferences.
10. Debug keys R / F2 / S still work in gameplay.
11. Automated tests cover preference rules, name default, quit confirmation, and menu state transitions where feasible.