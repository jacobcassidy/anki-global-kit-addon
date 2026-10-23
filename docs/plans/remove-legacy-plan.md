# Remove Legacy Compatibility Code

## Audit scope

This inventory covers active first-party Desktop, card, editor, and shared source, runtime templates, build and packaging scripts, and the tests and documentation describing their contracts. Generated bundles duplicate their source and should be rebuilt after implementation. Vendored dependencies and historical documentation are outside the removal inventory.

Implemented on **2026-10-23** on `refactor-legacy-removal`. The original inventory and requirements below are retained as the baseline; the implementation status records the resulting behavior.

The supported minimum remains Anki Desktop **26.05** (`min_point_version: 260500` in `addon/manifest.json`). The original audit checked the official 26.05 source for editor shortcuts, cloze handlers, and color definitions. Implementation rechecked the upstream 26.05 color map. The excluded list/cloze handlers and editor reinjection behavior remain unchanged.

## Implementation status

| Area                               | Result                                                                                                                                                                                                                                                                                                                                                                                                      |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Modifier-plus-Tab indentation      | Removed dedicated Qt Tab routing, editor webview registration hooks, and card indentation globals. Settings rejects new Tab/Backtab indentation bindings; saved bindings recover to current defaults in Desktop and browser paths. Current punctuation, Preferences, focus-reporting, and toolbar behavior is retained.                                                                                     |
| Editor `CodeBlock+` migration      | Removed alias expansion. All editor shortcut settings recover unsupported aliases to their corresponding release defaults; card `CodeBlock+C` remains supported. Recovery does not write configuration, preserves switches, and occurs before native duplicate/fixed-binding checks. Settings save persists the displayed replacement values.                                                               |
| Anki color-token fallback chains   | Removed all alternate-token arguments and the helper's iteration. Required tokens still resolve through `theme_manager.var()` and fail explicitly when unavailable.                                                                                                                                                                                                                                         |
| Unscoped syntax styles and palette | Consolidated saved `pre` markup, `.agk-code-block`, and `.syntax-highlights` into generated theme rules. Covered every standard token class in bundled Pygments, retained emphasis/error indicators, removed the duplicate stylesheet rules and all `--syntax-*` definitions/consumers, and moved inline code and line numbers to maintained variables. Saved fields and synced palettes are not rewritten. |

The syntax consolidation intentionally makes older unscoped snippets follow selected semantic theme colors. Number and string subtypes inherit maintained roles; unclassified names use the foreground. README and changelog document this presentation change and the replacement variables for custom CSS. Newly resolved Pygments presets with no text color now choose a contrasting foreground; existing synced palettes retain their saved values.

Validation completed: **270 JavaScript tests**, **120 Python tests**, rebuilt assets, generated-theme freshness, package-asset verification, and focused formatting/lint checks. A local Chromium fixture passed **248 computed-style checks** across fallback/selected palettes, saved/current/submitted code, light/dark mode switching, line numbers, ordinary inline code, and editor shadow roots; its rendered preview was inspected.

Live Anki verification remains outstanding: native event interception, cross-client review/preview/editor focus behavior, and actual Qt widget states were not exercised. Isolated tests and a local Chromium fixture do not establish live Anki behavior.

## Original findings and implementation requirements

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

Implementation sequence if Tab indentation support is retired:

1. Define and document one policy for saved and newly recorded Tab indentation bindings. Recommended target: reject new Tab bindings for the four card/editor indentation settings and use the corresponding current default for unsupported saved bindings at runtime. Do not write configuration during reads; persist a replacement only through Settings save. Preserve each action's enabled setting and master switch.
2. Apply that policy in `addon/desktop/settings/dialog.py` (candidate validation and conflict checks), `addon/desktop/config/service.py` (saved settings), `src/cards/js/runtime/settings.js`, and the card/editor indentation handlers. Ensure manually edited configuration and browser settings injected without normalization cannot reactivate Tab indentation. Treat Tab/Backtab spelling and modifier combinations consistently. Keep the restriction specific to indentation; do not change the shared keyboard matcher or recorder to reject Tab for every action.
3. Check `_configured_editor_shortcuts()` in `addon/desktop/editor/integration.py` so unsupported saved indentation bindings cannot become native `QShortcut` registrations. Apply existing fixed-shortcut and duplicate-binding checks to any recovered defaults as well.
4. Remove the dedicated Tab routing, editor webview registry, two editor hook registrations, and two card-side indentation globals listed above only after all input paths follow the policy.

Keep `_PreferencesShortcutFilter` and its installation. Its `_card_indent_shortcut_override()` punctuation handling, Command+Comma Preferences handling, and `_toolbar_owns_navigation()` handling are current behavior. Keep `_preview_input_webviews`, `_toolbar_webviews`, `_live_webviews()`, focus reporting, and the card/message hooks: these also support current punctuation shortcuts and toolbar navigation outside the Tab branch.

Keep `changeTextareaIndentation()` and the general indentation matching currently named `handleTabIndentation()` in `src/cards/js/inputs/tab-navigation.js`. They implement current punctuation shortcuts and toolbar actions too. The analogous editor indentation functions in `src/editor/js/formatting/blocks.js` also remain current behavior. Historical `tab` names in settings keys and function names are not unused implementations; renaming persisted keys would introduce a separate migration.

Affected coverage: `tests/python/desktop/test_reviewer_shortcuts.py`, `test_bootstrap.py`, `test_card_settings.py`, `test_editor_settings.py`, and `test_settings_bindings.py`; `tests/javascript/cards/tab-navigation.test.js` and `tests/javascript/editor/editor-blocks.test.js`. Many tests use old Tab bindings to exercise general indentation. Update those fixtures to current shortcuts and retain the row, selection, list, and undo behavior they cover. Keep the generic Tab recording/label assertions in `test_card_shortcut_input.py`; add indentation-specific rejection coverage at the validation boundary instead. Test saved-config recovery, disabled actions, native Tab/Shift+Tab navigation, and current punctuation shortcuts on macOS and non-macOS paths.

### 2. Card-only shortcut alias migration in editor settings

`addon/desktop/config/service.py`: the first loop in `get_editor_settings()` recognizes `CodeBlock+` values and expands them to native editor modifiers for these settings:

- `anki_editor_inline_code_shortcut`
- `anki_editor_indent_increase_shortcut`
- `anki_editor_indent_decrease_shortcut`

This loop is explicitly covered as migration of card-only aliases accidentally saved in editor settings by `tests/python/desktop/test_editor_settings.py`. It can be removed when that saved-data compatibility is retired.

Recommended target: treat `CodeBlock+` as unsupported for editor shortcuts and recover to that setting's release default without writing during reads. Replace the expansion loop with the agreed invalid-value handling, then retain the separate `Control+` translation loop. Check the broader editor shortcut registration and browser matching paths too: `_configured_editor_shortcuts()` currently checks fixed and duplicate bindings, but does not reject this alias. Do not assume removing the expansion alone makes a saved alias harmless; shared shortcut normalization still recognizes it.

Update `test_editor_settings.py` to assert the chosen recovery for all three previously migrated settings on both platform paths. Cover manually supplied editor aliases before native registration and browser matching, preserve conflict validation after recovery, and assert that card `CodeBlock+C` is unchanged. Include any other editor shortcut settings if the implementation applies the same unsupported-alias rule to them.

Keep the active card-side `CodeBlock+C` alias, its recorder, formatting, normalization, runtime matching, and physical-key fallback. Those are used by current card shortcuts. Keep the separate `Control+` and Qt/browser modifier translations as current platform behavior.

### 3. Redundant Anki color-token fallback chains

`addon/desktop/ui/theme.py`: `get_theme_color(token_name, *fallback_names)` tries alternate tokens when a primary token is absent. All primary tokens used by the following chains are defined in Anki 26.05's [color map](https://github.com/ankitects/anki/blob/26.05/ts/lib/sass/_vars.scss). Simplify these calls and then remove the helper's alternate-name iteration while retaining `theme_manager.var()` for theme-aware colors.

- `addon/desktop/ui/shortcut_input.py`, `CardShortcutInput.__init__()`: the `BUTTON_BG`, `BUTTON_GRADIENT_START`, `BUTTON_GRADIENT_END`, and `BUTTON_DISABLED` chains.
- `addon/desktop/ui/input_styles.py`, `style_settings_input()`: the `BUTTON_BG` and `BUTTON_DISABLED` chains for line edits and spin boxes.
- `addon/desktop/ui/shortcut_rows.py`, `style_shortcut_option()`: the `FLAG_2` chain.
- The same file's `build_shortcut_rows()`: the `ACCENT_DANGER` chain.
- `addon/desktop/settings/pages/editor/editor_fields.py`, `build_editor_fields_section()`: one remaining `ACCENT_DANGER` call inside the action-row loop. Indentation warning labels now come from `build_shortcut_rows()`.
- `addon/desktop/settings/pages/syntax_highlighting/__init__.py`, `LanguageStatusDelegate.paint()`: the `BUTTON_BG` chain for language Auto badges.

This removes defensive support for missing API tokens. It does not replace semantic Anki colors with static colors or remove light/dark theme handling.

After updating every caller, reduce `get_theme_color()` to one token name and retain explicit failure for an unavailable required token. Update isolated Qt/color stubs to expose the supported tokens rather than relying on fallback behavior. Exercise settings inputs, shortcut conflict/validation colors, and language Auto badges; visually check enabled, disabled, hover, and pressed states in both Anki themes.

### 4. Older unscoped syntax styling

`src/shared/css/syntax-highlighting.css`: the block beginning at `/* BOLD */` contains the older unscoped `pre .…` Pygments token rules. They style saved token markup outside the new `.agk-code-block` theme boundary as well as matching tokens inside current blocks.

`src/shared/css/variables.css`: the `--syntax-*` palette supplies those older rules and several current consumers. The new theme system uses `--agk-syntax-*`, generated by `addon/desktop/syntax_highlighting/themes.py` and exported into `src/shared/css/generated/cassidy-dark.css`. The generated fallback itself still references `--syntax-*`; the older palette is not dead code.

Removal requires consolidation rather than deleting every Pygments selector:

- Current `render_code()` delegates to `_render_with_clozes()` in `addon/desktop/syntax_highlighting/rendering.py`, which still emits ordinary Pygments classes using `HtmlFormatter(nowrap=True, classprefix="")`. Keep Pygments support in the new theme generator.
- The generator already handles `.n`/`.nx` explicitly as foreground and `.nv` through the variable role. Its rules cover both `.agk-code-block` and `.syntax-highlights`. Do not list these classes as missing. `_TOKEN_SELECTORS` still omits older rules for classes including `.mi`, `.se`, `.sd`, `.ch`, `.cp`, `.nd`, and generic emphasis/diff tokens. Inventory all old selectors against actual formatter output and role inheritance; mapping only the base `.m` or `.s` selector does not match spans whose sole class is `.mi` or `.se`.
- Existing fields may contain highlighted markup without either theme boundary. Removing the broad rules drops that presentation unless users explicitly convert the content. Recommended first stage: keep the unscoped saved-markup rules until their presentation is preserved by a consolidated fallback or an explicit user conversion workflow is documented. Do not silently rewrite fields. Consolidated rules must not override selected themes inside current blocks.
- `src/editor/css/editor-fields.css` still uses several `--syntax-gray-*` variables for ordinary `pre` and inline `code` presentation. `src/shared/css/syntax-highlighting.css` also uses `--syntax-gray-600` for current line numbers. Move these consumers to maintained semantic CSS variables before deleting their palette entries, preserving ordinary inline-code contrast and line-number visibility in light and dark modes.
- `_CASSIDY_DARK_SYNTAX_VARIABLES` and `_theme_variables_css(..., use_shared_variables=True)` in `themes.py` deliberately generate fallback references to the older palette. Remove or replace this dependency before deleting palette variables. Keep colors in maintained theme/palette definitions and generated CSS custom properties, rather than adding color literals to component rules. Preserve collection-selected palettes: resolved theme exports already use saved color values instead of these fallback references.
- Keep `.syntax-highlights { padding: 0 !important; }` while `src/cards/js/syntax-highlighting/index.js` still applies that class to current submitted-answer code.
- Remove only palette entries with no remaining first-party consumer, including generator string references. Document changes to the shared palette if user CSS overrides can be affected. Regenerate theme fallback CSS and built card/editor assets from their sources after consolidating the styles.

Relevant coverage includes `tests/python/desktop/test_syntax_highlighting.py`, `tests/javascript/shared/syntax-theme-styles.test.js`, `tests/javascript/cards/syntax-highlighting.test.js`, and the editor code-block and Markdown tests. The Python suite explicitly asserts that packaged fallback CSS follows `--syntax-*`; update that assertion only when the dependency is intentionally replaced. Keep mode-switch coverage that resets inherited bold/italic styles. Add representative Pygments subtype coverage and compare scoped blocks, unscoped saved snippets, and submitted answers under fallback and selected light/dark palettes. Existing saved snippets require visual review in addition to isolated rendering checks.

Suggested sequence: complete token coverage first, consolidate saved-markup fallback rules second, migrate current palette consumers third, and delete unused palette definitions last. If a safe saved-markup replacement is not part of the implementation, leave those rules and their required variables in place and mark that part deferred.

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

- Implement color-token cleanup independently first; it does not change saved shortcut or field-markup contracts. Handle Tab retirement and editor alias retirement as separate changes with their documented recovery policies. Keep syntax consolidation in its own change because saved content and generated assets need broader review.
- Keep each cleanup scoped to the behavior identified above and document changes to accepted saved shortcuts or existing note presentation.
- Update the applicable tests without losing coverage of current indentation, formatting, platform, and rendering behavior.
- Run focused Python tests with `python3 -m unittest tests.python.desktop.<test_module>` and JavaScript tests with `node --import ./tests/support/register-svg.js --test <test-file>`. Run the broader `npm test` suite after shared shortcut or theme changes, plus formatting and lint checks for the edited files.
- Run `npm run build` whenever card/editor source or theme generation changes. It runs `scripts/export_syntax_themes.py` before bundling. Include the affected generated files in the same commit and check freshness with `python3 scripts/export_syntax_themes.py --check` and `npm run verify:package-assets`.
- Verify supported Anki editor and review behavior where native event interception or saved markup is affected; report source checks and live verification separately.
- For shortcut changes, cover review, browser/template previews, and editor fields; check focus traversal, current punctuation bindings, toolbar keyboard navigation, and Preferences handling on macOS. For syntax changes, visually compare current and saved blocks, ordinary `pre`/inline `code`, and line numbers in light/dark modes, including an existing collection palette.
- Update `README.md` and/or `CHANGELOG.md` for implemented user-visible changes. Recheck that excluded behavior remains intact, stage only the scoped change, and commit on a branch other than `main` after validation.
