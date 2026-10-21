# Syntax highlighting restructuring plan

## Summary

Make targeted structural changes before and during the [syntax highlighting integration](../plans/syntax-highlighting-plan.md). Clarify ownership of shared rendering, Desktop services, settings behavior, and generated theme assets while retaining the existing `src/cards`, `src/editor`, and `src/shared` boundaries.

This document records proposed work. The restructuring and syntax highlighting feature have not been implemented or verified in live Anki.

## Preparatory changes

1. Move managed-media installation out of Settings into `addon/desktop/media/`:
   - Move the asset manifest to `manifest.py` and the installer to `installation.py`.
   - Update profile initialization, settings callers, build/package checks, and test imports to use the new locations.
   - Keep public media filenames, reserved-asset scope, and existing installation behavior unchanged.
   - Keep note-type operations in `addon/desktop/settings/services/note_types.py`.
2. Move the pure Markdown renderer from `src/cards/js/markdown/render.js` to `src/shared/js/markdown/render.js`:
   - Update card, editor, and test imports.
   - Keep review observation and the upcoming highlight.js engine under `src/cards/js/syntax-highlighting/`.
   - Remove the editor's dependency on the card tokenizer when Desktop Markdown highlighting is routed through Python, as specified in the integration plan.
3. Separate configuration data from Qt presentation constants:
   - Extract shared filesystem paths into `addon/desktop/paths.py`.
   - Extract fallback defaults from `settings/configs/constants.py` into `settings/configs/defaults.py`; keep release defaults in `addon/config.json` and maintain alignment.
   - Keep Qt presentation constants and platform-specific UI hints with Settings.
   - Keep path and default modules independent of Qt presentation code so rendering and build tooling can consume them without importing the settings dialog.
4. Align the README and repository guide with the existing `docs/PUBLISHING.md` and `docs/DEPENDENCIES.md` locations instead of their stale `docs/dev/` references. Update the repository guide's module ownership descriptions as paths move.

## Changes during syntax highlighting implementation

1. Extend the proposed `addon/desktop/syntax_highlighting/` package with explicit service boundaries:
   - `dependencies.py`: isolated loading of the bundled Pygments dependency.
   - `tasks.py`: the single active Desktop rendering task and its lifecycle, including busy and cancellation state.
   - `preferences.py`: collection-scoped light/dark theme preferences.
   - Keep the planned `language_memory.py` responsible for deck-language preferences and `rendering.py` independent of Qt, editor state, and collection operations.
   - Keep editor target validation, stale-result checks, and UI orchestration in the editor feature.
2. Extract settings behavior from `settings/ui/dialog.py`:
   - Add `settings/ui/bindings.py` for reading, restoring, and tracking typed controls, including checkboxes, shortcuts, dropdowns, language lists, and integers.
   - Add `settings/services/save.py` for coordinated persistence, stylesheet installation, and recovery.
   - Keep the dialog responsible for composition, validation feedback, and invoking Save. Follow the integration plan's requirement to retain staged edits and keep the dialog open after a failed save.
3. Separate generated theme defaults from handwritten styling:
   - Keep shared structural rules in `src/shared/css/syntax-highlighting.css`.
   - Generate a clearly named companion, `src/shared/css/syntax-highlighting-fallback.generated.css`, from the Cassidy Dark preset and import it into both card and editor styles.
   - Add `scripts/syntax_themes.py` for fallback generation and freshness checking. Build and watch must regenerate it when its preset inputs change; validation must detect stale output.
   - Keep collection-selected `_syntax-highlighting.css` as a runtime managed-media output rather than a repository file containing local collection preferences.
   - Preserve legacy styling during the transition and avoid maintaining a second handwritten fallback palette.

## Validation and delivery

- Deliver preparatory refactors separately from feature behavior, in reviewable commits on a non-main branch.
- Verify moved services and renderer imports with the existing JavaScript and Python tests, updating test loaders and stubs as necessary.
- Run relevant lint and formatting checks, `npm run build:addon`, `npm run check:assets`, and package validation after structural moves. Confirm public media names and archive contents remain correct.
- During feature implementation, cover typed settings binding behavior, save failure/recovery, dependency isolation, task lifecycle, theme preferences, and fallback stylesheet freshness using the integration plan's acceptance cases.
- Verify that changing the Cassidy Dark definition refreshes both bundled fallbacks through build and watch, while runtime theme media remains collection-specific.
- Report isolated automated validation separately from live Anki and cross-client verification.

## Assumptions and deferred changes

- Retain the current card/editor/shared source split and the integration plan's vendor, custom-theme, editor-feature, and settings-tab directories.
- Defer moving `scripts/tests/` or renaming `addon/web/`; neither is required for syntax highlighting.
- Preserve existing settings keys, public media filenames, note-type confirmation requirements, and user data throughout structural refactors.
- Update the syntax highlighting integration plan's source tree and path references to match these changes when implementation begins.
