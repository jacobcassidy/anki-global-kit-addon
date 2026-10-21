# Anki Global Kit Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added generated `_syntax-highlighting.css` media for new Kit note types and a confirmed **Enable Code Styling…** action that adds only the stylesheet import to an existing note type.
- Added optional per-deck language memory storage and upgraded review highlighting to a pinned, locally bundled highlight.js grammar set with per-answer processing limits.
- Added bundled Pygments theme choices, independent light and dark theme settings, read-only previews, collection-synced resolved palettes, and stylesheet recovery during Settings saves.
- Routed Desktop Markdown code fences through the Pygments service and removed the handwritten browser tokenizer.
- Added a checked-language menu beside **Highlight Code**, with Topic and per-deck fallback and collection-synced memory after successful explicit applications.

### Changed

- Standardized shortcut action capitalization and syntax Settings spacing, aligned inputs and language support labels, and added help for shared theme updates and enabling note type code styling.
- Renamed syntax classes and variables to `global-kit`, scoped `.code-line` inside code blocks, and kept authoring metadata on `<pre>` only. Existing highlighted fields from earlier development builds need their markup updated or recreated from source with **Highlight Code**.
- Moved About and Help content beside their Settings pages and the AnkiWeb listing description into publishing documentation. Updated guide links and package validation for the new locations.

### Fixed

- Fixed Settings Save being blocked by the default Blockquote shortcut conflicting with itself, and added feedback when shortcut validation prevents saving.
- Fixed Highlight Code shortcut tooltips, language menu positioning and labels, and the filled lightning icon.
- Fixed light and dark theme previews with Qt-compatible palette rendering, added readable theme names, and kept Note Types content at fixed vertical spacing.
- Fixed Desktop add-on startup after the project restructure by importing user stylesheet paths from their new module. Added coverage that imports the full add-on with Anki and Qt stubs and checks that startup registrations occur once.

## [1.1.1] - 2026-10-12

### Added

- Added automatic GitHub releases after checks pass on `main`, using the latest dated changelog section for the version and notes and attaching the installable add-on archive. Release validation requires matching changelog and package versions; retries skip published releases and can complete interrupted drafts.

## [1.1.0] - 2026-10-12

### Added

- Added keyboard navigation to card formatting toolbars: **Shift+Tab** from an input reaches its toolbar; **Left/Right**, **Home**, and **End** select buttons; **Enter** or **Space** applies formatting; **Escape** returns to the input. Desktop review and preview windows let these keys reach the toolbar without triggering Anki's answer or navigation actions.
- Added `npm run link:addon` to link a development checkout into Anki's add-ons folder on macOS, Windows, and Linux, with support for custom paths and safeguards against overwriting existing folders or links.
- Added asset checks that require matching versions in `package.json`, `package-lock.json`, and `addon/manifest.json`.
- Expanded isolated tests for note type creation, replacement, deletion, confirmation changes, partial success, managed media installation and failed-write recovery, shortcut validation and routing, toolbar navigation, Markdown rendering, and package contents. Updated DOM and Qt test stand-ins for input events and punctuation keys.

### Changed

- Changed the default increase and decrease indent shortcuts to **Command+Shift+.** and **Command+Shift+,** on macOS, and **Ctrl+Shift+.** and **Ctrl+Shift+,** on Windows and Linux. These extend Anki's native list indentation to plain text. **Tab** and **Shift+Tab** continue to move focus. Existing saved shortcuts are retained; use **Restore Defaults** or the individual **RESET** links in settings to adopt the new defaults.
- Consolidated Desktop editor list, blockquote, and inline-code formatting around shared native editing transactions, preserving selection, undo/redo, and Anki's input notifications.
- Read the version shown in settings from the add-on manifest instead of a separate hardcoded value.
- Moved **Features** ahead of **Setup** in the README and made **Card presentation** its first subsection. Stacked light and dark card screenshots in one column, with each front followed by its back, and refreshed the Cards and Editor settings screenshots with presentation-style images showing the new defaults.
- Updated the AnkiWeb listing, setup and shortcut guidance, development and publishing instructions, and bundled font notice documentation. Clarified that card settings sync through media while editor settings apply on Desktop.

### Fixed

- Fixed stale Anki views by running note type changes through Anki's background collection operations and reporting collection changes so Anki refreshes after successful actions, including actions completed before a later failure.
- Strengthened note type confirmation checks by revalidating the active collection, note type identities, replacement impacts, and deletion eligibility after confirmation. Operations stop if a requested new type now exists, a selected type has been replaced, or the confirmed templates or card counts have changed.
- Fixed custom topic labels to display as plain text in settings instead of interpreting names containing HTML-like markup.
- Fixed settings dialogs remaining allocated after they close.
- Fixed toggling inline-code formatting off for a partial selection within a single code span while keeping the surrounding text formatted.
- Protected fixed Desktop editor list and blockquote shortcuts from configurable shortcut conflicts during capture, validation, and registration, including older or manually edited settings, and prevented duplicate configurable bindings.
- Fixed native editor bindings by keeping card-specific code-block shortcut aliases out and normalizing older saved aliases into valid editor key combinations.
- Fixed synced card settings to preserve portable indentation modifiers while retaining explicitly configured physical Control shortcuts.
- Fixed inconsistent handling of shifted comma and period aliases across shortcut matching, validation, and Qt handling. On macOS, card indentation keys now reach focused review and preview inputs before native Anki shortcuts consume them.
- Removed misleading conflict warnings for the intended native editor indent and outdent defaults, and hid disabled Markdown shortcuts from card toolbar tooltips.
- Fixed stale configurable shortcuts and inline-code shortcut tooltips by refreshing them in open Desktop editors when settings are saved.
- Fixed list continuation with **Enter** to respect the Markdown shortcut enable switch and insert ordinary newlines inside fenced code blocks instead of extending list-like code rows.
- Fixed Markdown rendering to preserve ordered list starting numbers, including nested lists and lists following a different list type.
- Fixed SQL highlighting to recognize keywords and built-in names regardless of letter case.
- Fixed watch builds to write and report successful output even when esbuild emits warnings, and to track shared JavaScript changes in rebuild logs.
- Fixed package validation to require the supplied user stylesheet files and their README, leaving an existing archive intact if required files are missing.
- Corrected the 1.0.0 release date to 2026-10-07.

### Removed

- Excluded additional local files and backups in `user_files/` from release archives; only the supplied `README.txt`, `editor-fields.css`, and `editor-ui.css` are packaged from that directory.
- Removed the empty developer TODO document and ignored its path for local use.
- Removed an unused settings spacing constant and duplicated editor formatting transaction code.

## [1.0.0] - 2026-10-07

The first major release packages the card scripts, stylesheets, fonts, and new Desktop editor tools as an Anki add-on. Card features use synced templates and media so they remain available across Anki Desktop, AnkiWeb, AnkiMobile, and AnkiDroid.

### Added

- Added automatic installation and refresh of the kit's managed card JavaScript, CSS, and font files when an Anki Desktop profile opens or switches. Card settings are included in the installed media for syncing to other devices.
- Added a **Tools > Anki Global Kit Settings...** panel with separate **Cards**, **Editor**, and **Note Types** controls, plus **About**, **Help**, and **Changelog** tabs.
- Added independent settings for card input shortcuts, indentation, answer Markdown rendering, syntax highlighting, and the formatting toolbar, along with Desktop editor formatting and appearance options.
- Added card-side Markdown rendering for headings, paragraphs, line breaks, nested ordered and unordered lists, blockquotes, fenced code blocks, inline code, bold, italics, strikethrough, and HTTP(S) links.
- Added a configurable formatting toolbar above card question inputs, with shared SVG icons and shortcut tooltips for bold, italics, strikethrough, inline code, code blocks, lists, and blockquotes.
- Added configurable Markdown shortcuts with individual enable switches, shortcut capture, per-shortcut reset links, inline conflict warnings, and Escape to cancel capture. Formatting applies to the selection or the word at the caret and can be toggled off again.
- Added configurable indentation shortcuts, defaulting to **Alt+Tab** to indent and physical **Control+Tab** to unindent. **Tab** and **Shift+Tab** retain native focus navigation. Card text uses four-space indentation for Python topics and two spaces for other topics.
- Added bundled code syntax highlighting that recognizes fenced-code language names and aliases, falls back to the card topic, and highlights newly rendered answers.
- Added topic-specific **Advance** and **Cloze** note type creation for Command Line, CSS, Git, JavaScript, PHP, Python, React, Regex, Ruby, TypeScript, Vocabulary, and WordPress, plus alphabetically sorted custom topics.
- Added **Create**, **Replace**, and **Delete** controls for each note type format. Replacement requires an explicit selection and confirmation, keeps existing notes and fields, and adds missing kit fields. Deletion is available only for empty note types; uncreated custom topic rows can also be removed.
- Added a Desktop editor inline-code button and configurable shortcut for formatting selections or words, toggling existing code formatting, and starting an empty code span.
- Added Desktop editor indentation, inline-code space normalization, source HTML copying, and external rich-text paste cleanup, each controlled through settings.
- Added physical Control shortcuts for the Desktop editor's Cloze buttons on macOS, leaving Command+Shift+C available for inline code.
- Added separate customizable Desktop editor field and UI stylesheets in `user_files`, with enable switches and **View Stylesheet** buttons.
- Added hover help for settings, Markdown help and About content, a rendered changelog, and buttons linking to the GitHub help, repository, and changelog.
- Added the shared MesloLGL NF font, bundled card and editor assets, an add-on packaging script, and asset path checks.

### Changed

- Renamed the project from `Anki Global Extension` to `Anki Global Kit`.
- Updated card and editor typography, responsive layouts, light and dark palettes, toolbar styling, code blocks, and comparison panels using shared styles and color variables.
- Bundled answer comparison and syntax highlighting with the kit's card assets, removing the need for a separate `_diff_match_patch.js` file or external syntax-highlighting script.
- Updated ordered and unordered list conversion to change only the outermost selected list level while preserving child indentation and list styles. Formatting plain indented text preserves indentation and starts ordered numbering at one for each nested list.
- Standardized macOS shortcut labels and modifier handling, including support for remapped keys and configurable card list and blockquote shortcuts.
- Renamed the Note Types action to **Update Selected Note Types**, grouped actions by card format, and kept table headings visible while scrolling. Existing note types are detected when settings open; pending checkbox selections are cleared across restarts while custom topics are retained.
- Improved settings colors, spacing, section backgrounds, help indicators, shortcut warning layout, and keyboard navigation. **Save** receives focus when settings open or tabs change, and **Restore Defaults** is disabled when settings already match their defaults.
- Reorganized card, Desktop editor, shared assets, runtime template parts, and settings modules, with separate build outputs and a single canonical changelog included in the add-on package.
- Expanded CI to run script, style, and documentation linting, formatting checks, asset validation, and a build freshness check before the test suites.
- Declared the supported Node.js versions in the package metadata and documented the recommended Node.js 24 and Python 3.13 development toolchain.
- Raised the minimum supported Anki Desktop version to **26.05**, whose bundled browser supports the kit's current CSS features. Packaged add-ons declare this minimum in their manifest.

## [0.10.0] - 2025-04-02

### Changed

- Changed project name from `Anki Global Features` to `Anki Global Extension`

## [0.9.0] - 2025-01-23

### Added

- Added screenshots and more details to `README.md`.

### Changed

- Refactored CSS styles for ankiWeb.
- Refactored `balanceQuestionLines()` function.
- Updated CSS margins and paddings for card styles.

## [0.8.0] - 2024-12-10

### Changed

- Simplified `pre` and `code` colors.

## [0.7.0] - 2024-12-09

### Changed

- Updated global style link color.
- Updated global style max widths.

### Fixed

- Fixed DOM div creation for comparison answers.

## [0.6.0] - 2024-12-04

### Added

- Added bonus question title and type hint to card back.

## [0.5.0] - 2024-12-01

### Added

- Added note-types stylings CSS.

### Changed

- Updated HTML/JS to create side-by-side answer comparisons.
- Updated CSS design system to use a simple hue value to change colors between programming languages:

| Language     | Hue Value |
| ------------ | --------- |
| RUBY         | 28        |
| GIT          | 33        |
| HTML         | 46        |
| JAVASCRIPT   | 100       |
| Command Line | 130       |
| NODE         | 140       |
| GSAP         | 146       |
| REACT        | 218       |
| PYTHON       | 245       |
| TYPESCRIPT   | 258       |
| WORDPRESS    | 268       |
| PHP          | 273       |
| CSS          | 299       |

## [0.4.0] - 2024-08-10

### Added

- Added `@import url('_styles_for_syntax_highlighting.css')` to card stylesheets.

### Changed

- Moved Move Syntax Highlighting Addon styles to their own stylesheet.
- Updated `.gitignore` to allow all `/assets` files to be committed.
- Updated `CHANGELOG.md` title
- Updated `README.md` content.
- Updated `_global.js` main function as an IIFE.

## [0.3.0] - 2024-05-08

### Added

- Merged Anki Advanced Types Cards and Anki Global Card Styles into one repo for all **Anki Global Features**:
  - Added `assets/screenshots/download-file-button.png`
  - Added `assets/card-styles/*.css` files
  - Added `collection.media/_global.css` file
  - Added `collection.media/_inconsolata*` files

### Changed

- Formatted JS and CSS files.
- Updated global CSS topic header to remove spacing and rounding.

## [0.2.0] - 2023-08-14

### Added

- MIT License

## [0.1.0]

### Added

- `README.md`
- `CHANGELOG.md`
- `.gitignore`
- `assets/note-types/*.html` files
- `collection.media/_diff_match_patch.js` file
- `collection.media/_global.js` file
