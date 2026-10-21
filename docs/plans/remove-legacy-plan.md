# Remove Legacy Compatibility Code

## Purpose

Track compatibility code that can be removed after deciding that older saved settings or older Anki editor builds no longer need support. Platform-specific shortcut translation and key-name normalization are current behavior and are outside this cleanup.

## Active compatibility paths

### Old modifier-plus-Tab indentation shortcuts

- `addon/desktop/shortcuts/reviewer.py`: `_indentation_tab_action()` and `_card_tab_action()` route saved card or editor indentation shortcuts ending in `Tab`.
- The current defaults use punctuation keys. The Tab branch remains reachable when a stored shortcut uses a modifier plus Tab, even though Tab and Shift+Tab now move focus.
- Remove this branch only when intentionally dropping support for those saved shortcuts. Confirm settings capture and runtime routing no longer present or consume modifier-plus-Tab bindings.

### Card-only `CodeBlock+C` alias in editor settings

- `addon/desktop/config/service.py`: `get_editor_settings()` expands a saved `CodeBlock+C` value into the editor's platform shortcut form.
- `addon/desktop/shortcuts/formatting.py`: `format_shortcut()` and `normalize_shortcut()` interpret the `CodeBlock+` prefix.
- `addon/desktop/ui/shortcut_input.py`: `stored_shortcut()` emits `CodeBlock+C` for the card code-block shortcut recorder.
- `src/shared/js/keyboard-shortcuts.js`: `matchesKeyboardShortcut()` handles the card alias, including its physical-key fallback.
- The card shortcut remains an active feature. The cleanup candidate is the conversion of this card-only alias when it appears in Desktop editor settings; remove that conversion only if old or accidentally saved editor values need no longer be supported. Keep card-side alias handling while the card feature uses it.

### Older Anki editor-build handling

- `src/editor/js/formatting/blocks.js`: `installBlockFormatting()` falls back to locally constructed platform labels when `anki/shortcuts` is unavailable, and suppresses Anki's old web list handlers.
- `src/editor/js/index.js`: refreshes indentation methods on `ankiGlobalKitEditor` when a bundle is injected into an editor webview initialized by an older bundle.
- `src/editor/js/cloze/shortcuts.js`: listens on `keyup` as well as `keydown` to suppress older Anki cloze handlers.
- Remove these paths only after establishing the minimum Anki editor behavior that can be relied on and checking the supported minimum version.

## Not legacy

Keep the general platform translations in `addon/desktop/config/service.py`, the ordinary Qt/browser key-name aliases in `addon/desktop/shortcuts/formatting.py` and `src/shared/js/keyboard-shortcuts.js`, and shifted punctuation normalization. These handle current platform, Qt, browser, and keyboard-layout differences. They are not retained solely for older versions or saved values.

## Completion checks

- Inspect active settings defaults and shortcut capture, validation, and runtime routing before removing each candidate.
- Remove or update tests that assert the retired compatibility behavior; retain tests for current platform translations and card-side code-block shortcuts.
- Update user-facing shortcut documentation if the supported saved bindings change.
- Build the Desktop editor and card assets and run the relevant shortcut tests after implementation.
