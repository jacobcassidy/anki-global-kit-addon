# Remove Legacy Compatibility Code

## Audit scope

This inventory covers active first-party Desktop, card, editor, and shared source, runtime templates, build and packaging scripts, and the tests and documentation describing their contracts. Generated bundles duplicate their source and should be rebuilt after implementation. Vendored dependencies and historical documentation are outside the removal inventory.

The supported minimum is Anki Desktop **26.05** (`addon/manifest.json`). The audit checked the official 26.05 source for editor shortcuts, cloze handlers, and color definitions. This is a source audit; no live Anki behavior was verified and no runtime code was removed.

## Findings

| Area                                             | Disposition                                                                                                                                                |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Modifier-plus-Tab indentation                    | Retire only if support for these saved and newly customized bindings is deliberately dropped. Obsolete fallback literals can be cleaned up independently.  |
| Card-only `CodeBlock+` values in editor settings | Remove the editor migration when those older or accidentally saved values no longer need support.                                                          |
| Anki color-token fallback chains                 | Simplify to the primary tokens already present in the supported minimum. These are redundant API fallbacks, rather than a documented saved-data migration. |
| Older unscoped syntax styles and palette         | Consolidate after accounting for current Pygments output and existing saved markup. This is not a safe wholesale stylesheet deletion.                      |

### 1. Modifier-plus-Tab indentation

The defaults now use punctuation keys. The following code retains the old modifier-plus-Tab behavior, including support for new custom Tab bindings:

- `addon/desktop/shortcuts/reviewer.py`: `_indentation_tab_action()` matches Tab combinations and retains the old `Alt+Tab` and `Control+Tab` fallback literals. Normal callers receive complete settings from the configuration service, so those literals do not define the release defaults.
- The same file's `_card_tab_action()` wrapper and `_tab_shortcut_target()` resolve those shortcuts to card, preview, or editor webviews.
- `_PreferencesShortcutFilter.eventFilter()` has a dedicated `Tab`/`Backtab` branch that intercepts `ShortcutOverride` and `KeyPress` events and invokes the JavaScript action.
- `_editor_webviews`, `_register_editor_tab_shortcut()`, and `_register_editor_webview()` exist for this routing. Their `editor_did_init_shortcuts` and `editor_did_load_note` registrations in `initialize()` can go with it.
- `src/cards/js/inputs/setup.js`: `watchQuestionInputs()` publishes `ankiGlobalKitIndentQuestion` and `ankiGlobalKitUnindentQuestion`. Their only first-party callers are the Tab routing in `reviewer.py`, so they can go when that routing is removed.

Retiring these bindings requires settings validation and browser runtime matching to agree with the new policy. Removing only the Qt branch would leave custom Tab settings accepted while making their Desktop behavior unreliable. Do not remove general shortcut recording merely because it can record Tab combinations for other configurable actions.

Keep `changeTextareaIndentation()` and the general indentation matching currently named `handleTabIndentation()` in `src/cards/js/inputs/tab-navigation.js`. They implement current punctuation shortcuts and toolbar actions too. The analogous editor indentation functions in `src/editor/js/formatting/blocks.js` also remain current behavior. Historical `tab` names in settings keys and function names are not unused implementations; renaming persisted keys would introduce a separate migration.

Affected coverage: `tests/python/desktop/test_reviewer_shortcuts.py`, `test_bootstrap.py`, and Tab-specific assertions in `test_card_shortcut_input.py`; `tests/javascript/cards/tab-navigation.test.js` and `tests/javascript/editor/editor-blocks.test.js`. Many tests use old Tab bindings to exercise general indentation. Update those fixtures to current shortcuts and retain the row, selection, list, and undo behavior they cover.

### 2. Card-only shortcut alias migration in editor settings

`addon/desktop/config/service.py`: the first loop in `get_editor_settings()` recognizes `CodeBlock+` values and expands them to native editor modifiers for these settings:

- `anki_editor_inline_code_shortcut`
- `anki_editor_indent_increase_shortcut`
- `anki_editor_indent_decrease_shortcut`

This loop is explicitly covered as migration of card-only aliases accidentally saved in editor settings by `tests/python/desktop/test_editor_settings.py`. It can be removed when that saved-data compatibility is retired. Define how unsupported saved values are handled so they are not passed through as invalid Qt shortcuts.

Keep the active card-side `CodeBlock+C` alias, its recorder, formatting, normalization, runtime matching, and physical-key fallback. Those are used by current card shortcuts. Keep the separate `Control+` and Qt/browser modifier translations as current platform behavior.

### 3. Redundant Anki color-token fallback chains

`addon/desktop/ui/theme.py`: `get_theme_color(token_name, *fallback_names)` tries alternate tokens when a primary token is absent. All primary tokens used by the following chains are defined in Anki 26.05's [color map](https://github.com/ankitects/anki/blob/26.05/ts/lib/sass/_vars.scss). Simplify these calls and then remove the helper's alternate-name iteration while retaining `theme_manager.var()` for theme-aware colors.

- `addon/desktop/ui/shortcut_input.py`, `CardShortcutInput.__init__()`: the `BUTTON_BG`, `BUTTON_GRADIENT_START`, `BUTTON_GRADIENT_END`, and `BUTTON_DISABLED` chains.
- `addon/desktop/ui/shortcut_rows.py`, `style_shortcut_option()`: the `FLAG_2` chain.
- The same file's `build_shortcut_rows()`: the `ACCENT_DANGER` chain.
- `addon/desktop/settings/pages/editor/editor_fields.py`, `build_editor_fields_section()`: both `ACCENT_DANGER` chains.

This removes defensive support for missing API tokens. It does not replace semantic Anki colors with static colors or remove light/dark theme handling.

### 4. Older unscoped syntax styling

`src/shared/css/syntax-highlighting.css`: the block beginning at `/* BOLD */` contains the older unscoped `pre .…` Pygments token rules. They style saved token markup outside the new `.global-kit-code-block` theme boundary as well as matching tokens inside current blocks.

`src/shared/css/variables.css`: the `--syntax-*` palette supplies those older rules. The new theme system uses `--global-kit-syntax-*`, generated by `addon/desktop/syntax_highlighting/themes.py` and exported into `src/shared/css/generated/cassidy-dark.css`.

Removal requires consolidation rather than deleting every Pygments selector:

- Current `render_code()` in `addon/desktop/syntax_highlighting/rendering.py` still emits ordinary Pygments classes using `HtmlFormatter(nowrap=True, classprefix="")`. Keep Pygments support in the new theme generator.
- The generator's `_TOKEN_SELECTORS` does not cover every class in the older stylesheet. Account for classes such as `.n`, `.nv`, `.mi`, and `.se` and inherited token roles before removing rules that currently provide their presentation.
- Existing fields may contain highlighted markup without `.global-kit-code-block`. Removing the broad rules drops that presentation unless users explicitly convert the content. Document the scope and any migration; do not silently rewrite fields.
- `src/editor/css/editor-fields.css` still uses several `--syntax-gray-*` variables for ordinary `pre` and inline `code` presentation. Move those consumers to appropriate maintained tokens before deleting their variables.
- Keep `.syntax-highlights { padding: 0 !important; }` while `src/cards/js/syntax-highlighting/index.js` still applies that class to current submitted-answer code.
- Regenerate theme fallback CSS and built card/editor assets from their sources after consolidating the styles.

Relevant coverage includes `tests/python/desktop/test_syntax_highlighting.py`, `tests/javascript/cards/syntax-highlighting.test.js`, and the editor code-block and Markdown tests. Existing saved snippets require visual review in addition to isolated rendering checks.

## Earlier candidates excluded after review

- **Shortcut labels:** exclude `getPlatformString()` label fallbacks in `installBlockFormatting()` from this cleanup, as requested.
- **Anki list-handler suppression:** keep the `keydown` interception in `src/editor/js/formatting/blocks.js`. Anki 26.05 still registers the list and indentation handlers that the kit replaces; the comment calling them old does not establish obsolescence. See [BlockButtons.svelte](https://github.com/ankitects/anki/blob/26.05/ts/editor/editor-toolbar/BlockButtons.svelte).
- **Cloze `keyup` suppression:** keep it in `src/editor/js/cloze/shortcuts.js` unless supported Chromium behavior is established separately. Anki 26.05 still selects `keyup` for one cloze shortcut on Apple platforms with Chromium 112 or earlier. This is platform/runtime handling, not merely support for an older add-on. See [ClozeButtons.svelte](https://github.com/ankitects/anki/blob/26.05/ts/editor/ClozeButtons.svelte).
- **Editor API refresh:** do not delete the assignments in `src/editor/js/index.js` based on the older-bundle comment. The code also supports normal reinjection on note loads and settings saves, and the indentation methods are not supplied by the object initializer. Any consolidation needs to preserve current initialization and callback registration. The API is also populated by `installCodeBlockHighlighting()` and `installMarkdownHighlighting()`.

## Other current behavior to retain

- Platform detection, Anki client integration, Qt/browser modifier translation, physical-key matching, key-name aliases, shifted punctuation normalization, and shortcut labels.
- Missing-setting defaults and malformed-setting recovery, including browser defaults needed when Desktop-injected settings are unavailable.
- Shortcut conflict validation in `_configured_editor_shortcuts()`: manually edited configuration still needs validation, even after older saved values are retired.
- Repeated bundle initialization guards, observer cleanup, shadow-DOM selection handling, and delayed field-style installation.
- Current saved Pygments blocks, generated theme fallback CSS, supported language aliases, and plain-code behavior for unsupported languages or processing limits.
- Note-type confirmation/revalidation, explicit stylesheet installation for existing types, public media filenames, saved configuration keys, and current HTML/bridge contracts.

## Implementation completion checks

- Keep each cleanup scoped to the behavior identified above and document changes to accepted saved shortcuts or existing note presentation.
- Update the applicable tests without losing coverage of current indentation, formatting, platform, and rendering behavior.
- Run focused tests for the changed area, build the affected assets, and check asset freshness when generated files change.
- Verify supported Anki editor and review behavior where native event interception or saved markup is affected; report source checks and live verification separately.
