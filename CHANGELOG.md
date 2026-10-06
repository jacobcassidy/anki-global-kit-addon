# Anki Global Kit Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Raised the minimum supported Anki Desktop version to **26.05**, whose bundled browser supports the kit's current CSS features. Packaged add-ons declare this minimum in their manifest.

### Fixed

- Fixed the Desktop answer shortcut to use Command+Enter on macOS and Control+Enter on Windows/Linux, preventing a newline when revealing the answer.
- Scoped AnkiDroid answer storage and cleanup to kit-specific keys, preserving other card scripts' session data and handling unavailable storage without interrupting answer rendering.
- Fixed Desktop inline-code formatting for selections spanning existing code and ordinary text, preserving surrounding markup and avoiding nested code elements.
- Applied Desktop inline-code formatting through native editor transactions so formatting and subsequent typing can be undone and redone independently, including empty code spans.
- Fixed shortcuts containing a literal plus key, preserving the key when saving, matching, checking conflicts, and displaying shortcut labels.
- Created kit Cloze note types from Anki's stock definition instead of copying a profile's customized type, including profiles with no existing Cloze type. Replacement now validates the existing type's format before confirmation and again before applying changes.
- Preserved Anki's new-field marker when adding missing kit fields during replacement, using the model manager to add fields and assign their ordinals when saved.
- Stopped packaging when required top-level files or folders are missing or have the wrong type, reporting the affected paths before opening the output archive.
- Expanded asset validation to editor bundles, referenced shared icons, configured note type template parts, and shared font references. Packaging now requires these checks to pass before opening the output archive.
- Updated the packaged README to describe Create, Replace, and Delete accurately, including confirmation, format compatibility, empty-type deletion, and the complete packaging workflow.
- Aligned repository, issue, help, and listing image URLs with the canonical `anki-global-kit-addon` repository.
- Corrected the card toolbar help text to describe its position above each question input field.
- Corrected the agent repository guide's settings folder map to describe `helpers/` and `configs/` instead of the nonexistent `shared/` folder.
- Removed the unused `highlightSubmittedCode()` helper that duplicated the active submitted-code watcher's highlighting logic.
- Removed the unreferenced `help.svg` asset from the add-on package; settings help controls use `help-indicator.svg`.
- Removed obsolete ESLint ignores for deleted legacy files and an inactive override for an old generated-bundle path.
- Disconnected prior card-rendering and submitted-code observers during repeated initialization, including bundle reloads in the same webview. Observer setup now handles missing targets and disables an existing highlighting observer when highlighting is turned off.
- Consolidated the About, Help, and Changelog tabs' Markdown browser setup and document spacing into a shared settings UI helper.
- Removed the legacy theme API compatibility fallback now that Anki Desktop 26.05+ is required; settings resolve color tokens through `theme_manager.var()` directly.
- Replaced hardcoded card toolbar hover and focus shadow colors with palette-derived CSS variables, using softer shadows in light mode and stronger shadows in dark mode.
- Rendered settings help indicators with Anki's `FG_SUBTLE` and `CANVAS` color tokens, refreshing them on theme changes and scaling the SVG for the display's pixel ratio.
- Split Note Types table widgets and geometry into `table.py`, and confirmation, result, and error dialogs into `actions.py`, leaving checkbox and topic coordination in the main tab module.
- Ignored generated release archives in the repository-root `dist/` folder.
- Added npm commands for the existing JavaScript and Python test suites and a GitHub Actions workflow that runs them on pushes, pull requests, and manual runs.
- Synchronized the npm lockfile with the declared dependencies, removing the unused SCSS lint configuration and its exclusive dependencies without upgrading retained packages.
- Corrected the Note Types deletion help to refer to notes instead of cards, matching the empty-note-type requirement.
- Included the canonical project `LICENSE` at the add-on archive root and required it to exist as a file before packaging opens the output archive.

## [1.0.0] - 2026-10-05

The first major release packages the card scripts, stylesheets, fonts, and new Desktop editor tools as an Anki add-on. Card features use synced templates and media so they remain available across Anki Desktop, AnkiWeb, AnkiMobile, and AnkiDroid.

### Added

- Added automatic installation and refresh of the kit's managed card JavaScript, CSS, and font files when an Anki Desktop profile opens or switches. Card settings are included in the installed media for syncing to other devices.
- Added a **Tools > Anki Global Kit Settings...** panel with separate **Cards**, **Editor**, and **Note Types** controls, plus **About**, **Help**, and **Changelog** tabs.
- Added independent settings for card input shortcuts, indentation, answer Markdown rendering, syntax highlighting, and the formatting toolbar, along with Desktop editor formatting and appearance options.
- Added card-side Markdown rendering for headings, paragraphs, line breaks, nested ordered and unordered lists, blockquotes, fenced code blocks, inline code, bold, italics, strikethrough, and HTTP(S) links.
- Added a configurable formatting toolbar above card question inputs, with shared SVG icons and shortcut tooltips for bold, italics, strikethrough, inline code, code blocks, lists, and blockquotes.
- Added configurable Markdown shortcuts with individual enable switches, shortcut capture, per-shortcut reset links, inline conflict warnings, and Escape to cancel capture. Formatting applies to the selection or the word at the caret and can be toggled off again.
- Added Markdown list indentation with **Tab**, unindentation with **Shift+Tab**, and forward focus navigation with physical **Control+Tab**. Ordinary card text uses four-space indentation for Python topics and two spaces for other topics.
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
- Standardized macOS shortcut labels and modifier handling, including support for remapped keys and configurable list and blockquote shortcuts.
- Renamed the Note Types action to **Update Selected Note Types**, grouped actions by card format, and kept table headings visible while scrolling. Existing note types are detected when settings open; pending checkbox selections are cleared across restarts while custom topics are retained.
- Improved settings colors, spacing, section backgrounds, help indicators, shortcut warning layout, and keyboard navigation. **Save** receives focus when settings open or tabs change, and **Restore Defaults** is disabled when settings already match their defaults.
- Reorganized card, Desktop editor, shared assets, runtime template parts, and settings modules, with separate build outputs and a single canonical changelog included in the add-on package.

### Fixed

- Fixed Markdown toggle behavior inside formatted text and immediately after closing markers, including caret placement, empty selections, fenced code, and inline-code markers inside emphasis.
- Fixed macOS reviewer shortcut conflicts so configured Markdown actions, including Command+Comma, can handle their keys while question inputs are focused.
- Fixed answer comparisons to preserve Unicode code points, rendered line breaks, and normalized nonbreaking spaces, and to avoid duplicate comparison output during repeated initialization.
- Fixed repeated card initialization to preserve typed answers, active input focus, existing rendered answers, and event bindings.
- Fixed bonus questions and notes containing images or other media so they remain visible, and prevented duplicate bonus input hints.
- Fixed duplicate cloze text in answer comparisons and unwanted line breaks in code blocks and list items.
- Fixed shared font, icon, editor webview, and installed card asset paths after reorganizing the package.

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
