# Syntax highlighting integration plan

## Goal and proposed scope

Bring Syntax Highlighter's (/Users/Jacob/Projects/Software/First-Party/Groups/JacobCassidy/Packages/Anki/Anki Third-Party Addons Modifications/Source/_anki-third-party-addons-modifications/272582198) useful Desktop authoring capabilities into Anki Global Kit so users can create highlighted code without installing a second add-on. Integrate with the kit's existing editor controls, settings, styling, media installation, and native undo support.

This document records the proposed implementation. The feature has not been implemented or verified in live Anki.

Include:

- Highlight selected code or plain text from the clipboard through a toolbar action and configurable shortcut.
- Choose a language from Pygments' available lexers.
- Optionally remember the last explicitly applied language for each deck.
- Configure the feature in a dedicated Syntax Highlighting settings tab, including a checkable list controlling which languages appear in the editor dropdown next to the highlighting button.
- Apply highlighting again to an existing code block, including blocks containing highlighted spans.
- Optional line numbers with a configurable starting number.
- Theme presets with independent light and dark selections and a preview.
- A built-in **Cassidy Dark** theme, initialized from the existing Kit syntax appearance and used by default in both light and dark mode.
- Consistent styling in editor fields and on cards, including synced clients.
- An explicit action to enable syntax styling on ordinary, non-Kit note types.
- Route Desktop Markdown code-block highlighting through the same rendering service.
- Upgrade review-time JavaScript highlighting across Desktop, AnkiWeb, AnkiMobile, and AnkiDroid to share the new theme styling and broader common-language coverage.
- A lighting bolt icon for the editor toolbar button.

Do not include automatic collection-wide conversion, automatic changes to existing note types, or separate font-size and centering controls in the initial implementation. Preserve existing content and legacy stylesheets. JavaScript review highlighting is included, with consistent theme roles and a defined common language set; exact tokenization parity with every Pygments lexer is not a requirement.

## Source structure and responsibilities

```text
addon/
├── vendor/
│   └── pygments/                    # Pinned dependency and license notices
├── desktop/
│   ├── syntax_highlighting/
│   │   ├── __init__.py              # Public service interface
│   │   ├── custom_themes/
│   │   │   ├── __init__.py          # Kit-owned preset registration
│   │   │   └── cassidy_dark.py      # Editable Cassidy Dark definition
│   │   ├── language_memory.py       # Collection-scoped per-deck preferences
│   │   ├── rendering.py             # Language lookup and token HTML
│   │   └── themes.py                # Preset discovery and theme CSS
│   ├── editor/
│   │   ├── integration.py           # Existing editor hook registration
│   │   └── features/
│   │       └── syntax_highlighting.py
│   └── settings/
│       └── features/syntax_highlighting/
│           ├── __init__.py          # Dedicated settings tab
│           └── languages.py         # Grouped, checkable language list
└── config.json                     # Release defaults

src/
├── cards/js/syntax-highlighting/
│   ├── index.js                    # Review-time targeting and observation
│   ├── engine.js                   # Bundled JavaScript engine adapter
│   ├── languages.js                # Supported review languages and aliases
│   └── tokens.js                   # Engine scopes to shared theme roles
├── editor/js/formatting/
│   └── code-block.js               # Editor extraction and block updates
└── shared/css/
    └── syntax-highlighting.css     # Shared token rules and block styling
```

### Dependency and rendering service

- Bundle a pinned Pygments release and its required notices. Build and package it reproducibly; users should not need to install Python packages themselves.
- Keep dependency loading behind the service interface. Account for other add-ons that import Pygments; do not silently replace another version already loaded into Anki's Python process. Validate the vendoring/import strategy before wiring the editor feature.
- Keep `rendering.py` independent of Qt, clipboard access, editor state, and collection operations. Its interface accepts source text and a language alias and returns escaped token HTML plus the normalized language identifier.
- Return token markup rather than editor insertion wrappers. Preserve source whitespace, blank lines, tabs, and trailing newlines; do not use the third-party add-on's `stripall=True` behavior.
- Expose language labels and aliases for the picker, and reject invalid language identifiers without changing the field.
- Load Pygments on demand. Perform rendering away from the GUI thread using Anki's supported background-task facilities; keep all editor and Qt interaction on the GUI thread. Treat cancellation as cancellation of result application unless the worker actually supports termination.
- Implement the Kit integration independently. Pygments has its own license; do not copy the third-party add-on's implementation or custom theme code into this feature.

### Desktop editor integration

- Keep toolbar, shortcut, language-selection UI, clipboard access, and service orchestration in `editor/features/syntax_highlighting.py`.
- Use the existing `editor/integration.py` to register the feature through supported hooks and refresh saved settings in open editors. Avoid growing that file into the rendering implementation.
- Extend existing shortcut validation and conflict handling. Respect Qt's macOS modifier mapping and the separate standard browser-event mapping.
- Let `code-block.js` own target capture, plain-text extraction, block markup, line-number decorations, and application of returned token HTML.
- Reuse the selection helpers and `editWithNativeUndo` transaction. Applying or refreshing highlighting must be one native undoable edit.
- Associate each request with its editor, note, field, target range, source snapshot, and resolved deck context. Discard the response if that target is no longer current, its content has changed, or its deck context has changed. Discarded requests must not update language memory.
- Register any JavaScript message handler only for the kit's own commands and the correct editor context. Do not accept arbitrary HTML insertion or arbitrary Python operations through the bridge.

### Settings and note-type operations

- Add a dedicated **Syntax Highlighting** tab to Settings. Put all settings for this feature there: toolbar visibility, shortcut enable/binding, editor language visibility, default language, **Remember last language per deck**, line-number enable/start, theme selections, and a preview. Integrate it with the existing settings dialog's loading, saving, reset, and validation behavior.
- Show all available languages in a checkable list with two distinct groups: **Shown in editor** for checked languages first, followed by **Other languages** for unchecked languages. Sort both groups alphabetically by display name, ignoring case. Checking or unchecking a language moves it immediately to the correct alphabetical position in the other group, without duplicates and while preserving keyboard focus.
- Persist language choices using canonical language identifiers. Limit the editor language picker and default-language choices to checked languages. If the configured default is unchecked, select the first checked language alphabetically; if none are checked, disable highlighting and show an explanation directing the user to this tab. Keep that empty selection valid and reversible.
- Treat this list as editor visibility configuration, not a limit on either rendering engine. Changing the checked languages must not rewrite existing blocks, remove their language metadata, or disable supported review languages or explicit Markdown fence languages. Existing blocks retain their recorded language when highlighted again, even if that language is hidden from the picker.
- Keep release defaults in `addon/config.json` and align the Python and browser fallback defaults. Extend existing configuration reading, validation, and saving rather than adding another persistence mechanism.
- Use `anki_editor_` settings for authoring controls. Store theme choices as shared syntax settings because they affect both editor and review presentation; make them available to the theme service as well as the settings UI.
- Keep previews read-only. Saving settings refreshes editor presentation and managed theme media without rewriting note fields.
- Add a separate confirmed note-type action to the existing note-type service: enable Kit code styling by adding only the syntax stylesheet import. Do not invoke Replace, change card templates, remove cards, or alter fields.
- Show the target note type and exact styling change before confirmation. Re-read the current note type before applying the additive, idempotent update through documented `col.models` APIs.

## Authoring behavior

### Target and language selection

Use this target order for the proposed Kit action:

1. If the caret or selection is wholly inside one recognized code block, update that complete block.
2. Otherwise, use a nonempty selection from one rich-text editor field to create a code block.
3. Otherwise, use the clipboard's plain text at the field's caret.

Reject selections crossing fields or crossing a code-block boundary into unrelated content. Empty input is a no-op. Preserve meaningful whitespace; do not read clipboard HTML as executable markup.

This deliberately improves on the inspected Syntax Highlighter implementation, which uses any nonempty `selectedText()` result and otherwise reads clipboard text. That implementation does not inspect the block around the caret and normalizes nonbreaking spaces only on the selection path.

Resolve the starting language in this order:

1. The existing code block's recorded, supported language.
2. A recognized Topic language that is checked for editor visibility.
3. The resolved deck's remembered language, when memory is enabled and that language is checked for editor visibility.
4. The configured enabled default language, falling back to the first checked language alphabetically as described in Settings.

Allow the user to override the language in the picker. Use canonical aliases in saved markup. An empty checked-language list continues to disable the editor action.

### Per-deck language memory

- Add the authoring setting `anki_editor_syntax_highlighting_remember_language_per_deck`, defaulting to false. Disabling it stops both lookups and writes but preserves remembered choices for later re-enabling.
- Keep memory reads and writes in `addon/desktop/syntax_highlighting/language_memory.py`. The editor feature resolves the deck and supplies its ID; the renderer remains independent of decks and collection state.
- Store a mapping of stringified deck IDs to canonical language aliases under the namespaced collection configuration key `anki_global_kit.syntax_highlighting.deck_languages`, using supported collection configuration APIs. This scopes memory to the collection, survives deck renames, and allows it to sync with the collection. Keep the map out of add-on release defaults, generated media, and the ordinary settings-dialog save payload.
- Resolve the deck when the highlighting action runs, not from the main window's globally selected deck. In the Add window, use that window's currently selected destination deck. When editing a specific card, use its original deck for a filtered card and its current deck otherwise. Without a specific card context, use the note's deck only if all its cards resolve to the same original/nonfiltered deck. If the context is ambiguous or unavailable, use normal language fallback without reading or writing deck memory.
- Treat each deck independently; do not inherit preferences from parent decks. If a deck is deleted, ignore its stored entry. A renamed deck keeps its preference because its ID is unchanged.
- Record a preference only after the user explicitly chooses a language and highlighting is successfully applied to the still-current target. A dropdown change alone, canceled/failed/stale operation, automatic Topic detection, or an ordinary refresh of an existing block must not change the preference. An explicit language change while updating an existing block can establish a new preference.
- Keep the configured global default unchanged when a deck preference is recorded. Read the latest mapping and update only the resolved deck's entry, preserving other entries and unrelated collection configuration.
- If a remembered language becomes unchecked, retain its entry but skip it during fallback until it is checked again. Ignore unsupported or malformed stored entries. Recorded languages in existing blocks and explicit Markdown fence languages remain independent of deck memory.
- Resetting feature settings restores the memory toggle to its default and preserves the collection's learned map. Memory is authoring metadata; do not rewrite notes or regenerate CSS when it changes.

### Saved markup and repeated highlighting

- Use a Kit-marked `<pre><code>` structure containing Pygments token spans and language metadata. Keep presentation in CSS classes and variables.
- Extract source from the code content, not the surrounding wrapper or line-number gutter. Existing token spans contribute only their text, so they do not prevent highlighting again.
- Preserve line breaks represented by supported editor markup; a bare `textContent` call is insufficient for arbitrary `<br>` and block-element content.
- Replace old token children rather than nesting a new highlighted wrapper inside the previous one.
- Keep line numbers outside the source text. They must not enter copied code or subsequent rendering input, and wrapped lines must retain alignment.
- Preserve intentional Anki cloze content and test code containing literal braces, `{{...}}`, and `::`. Do not flatten or reinterpret existing cloze structures without an explicit supported conversion.
- Do not automatically rewrite legacy Syntax Highlighter output. Users may select its plain code to create a Kit block, but arbitrary legacy tables, inline styles, and line-number layouts are not an automatic migration target.

### Markdown and cross-client behavior

- Route Desktop Paste Markdown as HTML code blocks through the Python rendering service, then apply the complete insertion as one undoable edit.
- Respect an explicit supported fence language. For an unlabeled fence, use a recognized Topic language; leave unsupported explicit languages and unresolved unlabeled blocks as escaped plain code.
- Remove Desktop Markdown's dependency on the current JavaScript tokenizer after routing it through Pygments. Replace that tokenizer with the review engine described below, keeping its adapter and card observation logic under `src/cards/js/syntax-highlighting/`. Move code into `src/shared/js/` only if another runtime actually consumes it.
- Saved Pygments HTML and its CSS display across clients. Pygments itself runs only on Desktop; newly typed answers use the upgraded JavaScript engine on every review client, including Desktop.

### Review-time JavaScript highlighting

- Replace the current hand-written tokenizer with a pinned highlight.js core and individually imported language modules. Bundle the engine, required language dependencies, and notices into the existing managed card JavaScript asset; do not use a CDN, network requests, or runtime package loading.
- Support the current Python, JavaScript, TypeScript, Java, C, C++, C#, SQL, Bash/shell, JSON, Ruby, Go, Rust, and PHP languages, plus HTML, CSS, Markdown, PowerShell, and Kotlin. Resolve Pygments and JavaScript aliases through an explicit mapping, including HTML's mapping to the JavaScript engine's markup grammar. Do not imply that every Pygments lexer is available during review.
- Use an explicit supported fence language first, otherwise a recognized Topic language for unlabeled code. Do not use source-code auto-detection. An unsupported explicit label remains escaped plain code rather than falling through to Topic; unresolved languages and engine failures also leave readable, escaped source.
- Keep the checked-language list scoped to editor visibility. Review language support is determined by the bundled modules and is unchanged when languages are unchecked. Do not apply per-deck authoring memory or the editor's default language to review-time answers.
- Keep `index.js` responsible for targeting and observing submitted-answer code blocks. Preserve the existing review highlighting enable setting, detect newly rendered answers, and make repeated initialization idempotent. Do not globally highlight every `<pre>` or retokenize existing saved Pygments spans.
- Map JavaScript token scopes to the same theme roles used for Pygments in `tokens.js`, covering comments, keywords, strings, numbers, functions, classes, built-ins, operators, and punctuation where the grammar distinguishes them. Use the base code foreground for unclassified content. Preserve nested token structure and source text.
- Generate CSS for both engines' token selectors from the selected theme definitions in `_syntax-highlighting.css`, using shared CSS variables. Cassidy Dark remains the default in both modes. Maintain consistent colors and font styles for equivalent roles without promising identical token boundaries or distinctions between the two engines.
- Keep styling separate from answer comparison. Highlighting must not alter persisted answers, source whitespace, comparison results, or difference markers. Preserve existing saved markup and avoid nesting duplicate highlight spans during rerenders.
- Measure card bundle size and review latency before and after the change. Import only the planned language set and its dependencies, and validate long and multiline snippets on mobile rather than assuming Desktop performance carries over.

## Themes, assets, and compatibility

- Let `themes.py` combine Kit-owned presets with Pygments presets and generate the selected light and dark definitions. Register the built-in **Cassidy Dark** preset under the stable identifier `cassidy-dark`.
- Keep Cassidy Dark's definition in `addon/desktop/syntax_highlighting/custom_themes/cassidy_dark.py`, separate from the vendored dependency. Initialize its palette, code-block foreground/background, and token font styles from the existing shared syntax stylesheet and syntax color variables. Use this same appearance in both modes; do not create a lighter variant or introduce a separate Kit Classic preset. This is the starter definition for the user's later theme edits.
- Default both light and dark theme settings to `cassidy-dark` in release defaults and runtime fallbacks. A missing, empty, or unsupported selection falls back to Cassidy Dark for that mode. Reset restores Cassidy Dark for both modes. Preserve valid explicitly selected alternatives across restarts and upgrades, and retain independent mode selectors so users can choose different presets later.
- Render Cassidy Dark through the same preview, CSS-variable generation, editor injection, and `_syntax-highlighting.css` delivery path as other presets. Later edits to its definition must take effect through normal theme generation and media refresh without changing the preset identifier or rewriting class-based note content.
- Represent theme colors with CSS variables, including token foreground/background colors and code-block foreground/background colors. Preserve bold, italic, and inherited token styles. Qt controls use Anki color tokens.
- Scope new rules to Kit code blocks. Do not inject global rules for short classes such as `.k` or `.s` into unrelated content.
- Reuse the shared stylesheet for token presentation and layout. Separate palette selection from tokenization so compatible class-based snippets can change themes without rewriting their fields.
- Create a new media file named exactly `_syntax-highlighting.css` containing the selected theme CSS and scoped structural rules. Use this filename consistently in the asset manifest, installer, template imports, note-type styling action, packaging checks, and documentation. Use Kit-owned names for all feature classes and identifiers. Extend the existing media installer to support this generated asset, refreshing it on profile open and after a theme save through Anki's media manager.
- Inject the same selected theme CSS into editor field shadow roots and theme previews using existing style injection facilities. Verify light/dark selection in each supported client context.
- Add the syntax stylesheet import to new Kit template parts. Existing Kit note types acquire that import only through an explicitly confirmed update; document both the additive styling action and the existing Replace workflow accurately.
- Ordinary note types can receive the syntax import through the separate styling action without acquiring Kit layout rules. The dedicated stylesheet must not require the full Kit card stylesheet or its font installation to remain readable.
- Preserve existing legacy class styling until compatibility tests justify narrowing it. Do not overwrite or delete third-party stylesheets, their note-type imports, or unrelated media. Do not reuse third-party branding in feature filenames, CSS classes, identifiers, or documentation.
- Extend the asset manifest, build/package validation, and archive contents for the generated stylesheet, vendored dependency, and notices. No runtime Python dependency is copied into `collection.media`.

## Delivery and validation

Implement in reviewable stages, each with appropriate validation and a separate commit on a non-main branch:

1. Add the vendored dependency, import adapter, pure rendering/theme services, the initial Cassidy Dark preset, and package coverage.
2. Add editor targeting and insertion, the Python coordinator, language picker, configurable action, and per-deck language-memory service and deck resolution.
3. Add the dedicated Syntax Highlighting settings tab, grouped language checklist, theme settings/previews, shared styling, generated media delivery, and the confirmed note-type styling action.
4. Integrate Desktop Markdown rendering and replace the review tokenizer with the bundled JavaScript engine, language registry, and shared theme-role mapping.
5. Document migration, supported review languages, and tokenization differences; complete cross-client and performance verification.

Automated coverage:

- Render representative existing languages and newly supported HTML, CSS, Markdown, PowerShell, and Kotlin; validate aliases and invalid-language failures.
- Verify exact source preservation, escaping, Unicode, indentation, trailing newlines, literal template-like syntax, and cloze handling.
- Cover selection, clipboard, existing-block targeting, highlighted spans, empty input, invalid selections, and stale background results.
- Verify repeated highlighting updates the same block without duplicated wrappers or line numbers. Cover native undo/redo through browser or live integration checks where DOM-only tests cannot establish behavior.
- Verify settings defaults/types, shortcut conflicts and modifier labels, theme generation/scoping, and light/dark selection.
- Verify Cassidy Dark appears in both mode selectors, starts from the existing Kit syntax appearance, and produces the same palette and token styles in both modes. Cover fresh settings, missing/empty/unsupported selections, reset, persistence of explicit alternatives, and regeneration after a preset-definition edit without rewriting note fields.
- Render shared fixtures through Pygments and JavaScript for all planned review languages. Check equivalent theme roles where both engines classify them, exact source preservation, and intentional tokenization differences without requiring identical HTML.
- Cover review aliases, explicit-fence versus Topic priority, unsupported explicit labels, engine failures, disabled highlighting, editor-hidden languages, and review behavior independent of deck memory.
- Cover dynamically submitted answers, repeated initialization/rerendering, preserved saved Pygments spans, HTML-like source, multiline Unicode text, and unchanged answer-comparison results and difference markers.
- Verify that checked and unchecked language groups are separate and each alphabetically sorted; toggling moves items between groups without duplicates or focus loss. Cover persistence, reset, default-language changes, an empty enabled list, and existing blocks using hidden languages.
- Verify language priority: existing block, enabled Topic language, enabled remembered deck language, then enabled default. Cover disabled memory, hidden remembered languages, unsupported stored aliases, and an empty enabled list.
- Verify memory updates only after successful explicit language application, preserves the global default and other decks' entries, survives reopening/renaming, and is isolated between collections. Cover cancel/failure, automatic detection, ordinary block refresh, and a deck change while rendering.
- Verify deck resolution for the Add window's destination versus the main window's current deck, a specific edited card, filtered cards' original decks, notes whose cards share one deck, and ambiguous notes with cards in multiple decks. Verify independent parent/child deck choices and safe behavior for deleted or unavailable decks.
- Verify settings saves and resets do not erase learned collection preferences, disabling/re-enabling retains them, and memory writes do not alter notes or managed media. Verify collection sync behavior manually between Desktop installations.
- Verify `_syntax-highlighting.css` is the exact media filename everywhere and the new feature's names do not reuse third-party branding.
- Verify confirmed styling installation is additive and idempotent and that cancellation leaves the note type unchanged.
- Verify managed-media updates preserve unrelated files and the archive includes Pygments, the bundled JavaScript engine, and their required notices but excludes local metadata and user data. Check the generated card bundle has no external runtime imports or language fetches.

Run focused tests while developing, then the project test suites, relevant lint/format checks, `npm run build:addon`, `npm run check:assets`, and package validation. Do not present isolated tests as live Anki verification.

Manual acceptance should cover Anki Desktop 26.05 and a current supported release, Add/Browse editors, note switching while rendering, native undo/redo, light/dark mode, and synced display on AnkiWeb, AnkiMobile, and AnkiDroid. On every review client, compare saved reference code with newly submitted code under Cassidy Dark and an alternative preset. Record bundle-size changes and mobile responsiveness for long answers. Confirm behavior against official minimum-version APIs before using new hooks or collection operations.

### Dependency measurements and references

The local Syntax Highlighter copy bundles Pygments 2.19.2. Inspection found 338 library files, approximately 4.45 MB of source, approximately 1.20 MB ZIP-compressed, 600 lexer entries, and 49 styles. These measurements describe that copy, not a promised release dependency version or final package size.

A standalone local benchmark for approximately 4,300 characters of Python took about 96 ms including initial imports and averaged about 5.7 ms with initialized imports and lexer. These are not live Anki measurements or guarantees for other inputs. Pygments does not guarantee bounded execution time; validate responsiveness with large snippets before release.

- [Pygments API](https://pygments.org/docs/api/)
- [Pygments HTML formatter](https://pygments.org/docs/formatters/#HtmlFormatter)
- [Pygments styles](https://pygments.org/docs/styles/)
- [Pygments license](https://github.com/pygments/pygments/blob/master/LICENSE)
- [Pygments execution-time considerations](https://pygments.org/docs/security/)
- [highlight.js language imports and bundling](https://highlightjs.org/)
- [highlight.js explicit-language API](https://highlightjs.readthedocs.io/en/latest/api.html)
- [Anki hooks and filters](https://addon-docs.ankiweb.net/hooks-and-filters.html)
- [Anki collection APIs](https://addon-docs.ankiweb.net/the-anki-module.html)
