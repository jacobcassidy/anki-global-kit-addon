# Anki Global Kit Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-02

The first major release convert the scripts and stylesheets into an Anki addon you can now download directly in Anki. With many more features added on to improve the flashcard learning system with Anki. The project has been renamed from `Anki Global Extension` to `Anki Global Kit` to reflect this change.

### Added

- Main features added:
  - You can now style the editor UI, editor fields, and cards with the user_files included in this add-on.
  - A Markdown toolbar with shortcuts are available in cards to go with the native editor markdown options.
  - An inline-code button and shortcut gives you the ability to add short snippets of styled code.
  - A setting panel is now included that give you fine-grain control over many of the new features.

- Added card-side Markdown rendering, syntax highlighting, answer comparison, and configurable question formatting tools.
- Added Advance and Cloze note type templates for the built-in topics, with optional custom topic rows.
- Added selection and overwrite controls for note types. Existing types stay unchanged unless their **Overwrite** checkbox is selected.
- Added a **Delete** checkbox for removing a custom topic row from settings. This only removes the settings row; existing Anki note types and cards are left intact.
- Added separate **Cards** and **Editor** settings for review behavior, shortcuts, formatting, indentation, copying, and paste cleanup.
- Added configurable Markdown shortcuts and formatting toolbar buttons, including list, quote, and code formatting.

### Changed

- Renamed the Note Types action to **Update Selected Note Types** to cover creating and overwriting selected types as well as applying custom topic row changes.
- Focuses the **Save** button when settings open or the selected tab changes, while keeping normal Tab navigation through controls.
- Standardized settings panel colors, spacing, and section backgrounds, and added dividers between note type table columns.

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
