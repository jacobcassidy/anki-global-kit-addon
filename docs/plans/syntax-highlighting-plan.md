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
- Keep dependency loading behind the service interface and isolate the bundled, pinned Pygments copy from other add-ons' copies. Before editor integration, establish the loading mechanism and prove that a different Pygments version can coexist when loaded before or after the Kit. Do not replace another add-on's loaded modules or reuse an arbitrary installed version. If the isolated dependency cannot load, show a clear error and leave the field unchanged. Users must not need to install Python packages themselves.
- Keep `rendering.py` independent of Qt, clipboard access, editor state, and collection operations. Its interface accepts source text and a language alias and returns escaped token HTML plus the normalized language identifier.
- Return token markup rather than editor insertion wrappers. Preserve source whitespace, blank lines, tabs, and trailing newlines; do not use the third-party add-on's `stripall=True` behavior.
- Expose language labels and aliases for the picker, and reject invalid language identifiers without changing the field.
- Restrict discovery and lookup to the bundled Pygments lexers/themes and explicitly registered Kit-owned presets. Exclude external plugin entry points from enumeration and resolution, including fallback lookups. Another installed package must not add, replace, or change available choices; the registry must be reproducible for a given Kit release.
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

- Add a dedicated **Syntax Highlighting** tab to Settings. Put all settings for this feature there: toolbar visibility, shortcut enable/binding, editor language visibility, default language, **Remember last language per deck**, line-number defaults, submitted-answer highlighting enable, theme selections, and a preview. Integrate it with the existing settings dialog's loading, saving, reset, and validation behavior.
- Move **Enable syntax highlighting for submitted answers** from Cards → Card Reviews to Syntax Highlighting. Preserve the existing `card_review_syntax_highlighting` key, default, and saved value, and remove the old control so there is only one location. Keep **Enable Markdown to HTML rendering** under Cards → Card Reviews.
- Show all available languages in a checkable list with two distinct groups: **Shown in editor** for checked languages first, followed by **Other languages** for unchecked languages. Sort both groups alphabetically by display name, ignoring case. Checking or unchecking a language moves it immediately to the correct alphabetical position in the other group, without duplicates and while preserving keyboard focus.
- Add search by display name or alias across both groups. Search filters visibility without changing check states; clearing it restores the full alphabetically sorted groups. Support keyboard navigation and checkbox activation. Label each language **Review supported** or **Desktop only**, based on the bundled JavaScript language registry rather than its editor check state.
- In the editor dropdown, place the currently selected language first and sort the remaining enabled languages alphabetically, ignoring case. Keep both Settings groups fully alphabetical; do not pin the selected language there.
- Persist language choices using canonical language identifiers. Limit the editor language picker and default-language choices to checked languages. If the configured default is unchecked, select the first checked language alphabetically; if none are checked, disable highlighting and show an explanation directing the user to this tab. Keep that empty selection valid and reversible.
- Treat this list as editor visibility configuration, not a limit on either rendering engine. Changing the checked languages must not rewrite existing blocks, remove their language metadata, or disable supported review languages or explicit Markdown fence languages. Existing blocks retain their recorded language when highlighted again, even if that language is hidden from the picker.
- Keep release defaults in `addon/config.json` and align the Python and browser fallback defaults. Extend existing configuration reading, validation, and saving rather than adding another persistence mechanism.
- Extend the settings dialog's value reading, writing, change detection, and reset behavior beyond its current checkbox/shortcut controls. Support language/theme dropdowns, language lists, and positive integer starting numbers with explicit types. Save commits valid changes, Cancel discards staged changes, and Reset restores the defined defaults in the UI until saved.
- Recover malformed saved values individually using defaults while retaining other valid settings. Validate list entries as supported canonical language identifiers, preserving valid entries; an intentionally empty language list remains valid. Flag invalid new UI input and block Save until corrected. Preserve unrelated stored settings and collection-scoped deck memory when saving.
- Use `anki_editor_` settings for authoring controls and keep those controls local to the Desktop installation. Theme selections are collection-scoped, synced preferences as described below, available to the theme service and settings UI without being overwritten by an ordinary local-settings save.
- Keep previews read-only. A successful settings save refreshes editor presentation and managed theme media without rewriting note fields. Follow the coordinated save and recovery behavior below.
- Add a separate confirmed note-type action to the existing note-type service: enable Kit code styling by adding only the syntax stylesheet import. Do not invoke Replace, change card templates, remove cards, or alter fields.
- Show the target note type and exact styling change before confirmation. Re-read the current note type before applying the additive, idempotent update through documented `col.models` APIs.

### Settings save and stylesheet recovery

- Generate and validate the requested theme CSS before committing staged settings. Keep the previous local settings, collection theme preferences, and working stylesheet available for recovery during the save.
- Treat settings persistence and stylesheet installation as one successful Save from the user's perspective. If installation or another application step fails, preserve or restore the previous working settings and stylesheet, leave the dialog open with staged edits intact, and explain the error with a retry path. Do not report success or close the dialog after a failed save.
- If a partial write requires restoration, verify that restoration succeeded. If recovery itself fails, report the actual state and recovery error clearly rather than claiming the previous working state was preserved. Keep unrelated settings and media outside the operation.

### Initial defaults

- Check these 13 languages by default, listed alphabetically in Settings: **Bash, CSS, Go, HTML, JavaScript, JSON, Markdown, PHP, Python, Ruby, Rust, SQL, TypeScript**. Other available languages start unchecked. This does not reduce the 19-language review engine's coverage.
- Set the default language to **Python**. With Python selected, the initial editor dropdown order is **Python, Bash, CSS, Go, HTML, JavaScript, JSON, Markdown, PHP, Ruby, Rust, SQL, TypeScript**; selecting another language moves that language to the top and re-sorts the remainder.
- Enable the configurable Highlight Code shortcut with the portable Qt binding `Alt+S`, displayed as **Alt+S** on Windows/Linux and **Option+S (⌥S)** on macOS. Register and validate it through the existing native shortcut machinery; browser character handling must account for the produced character if a browser handler is needed.
- Start new blocks with line numbers **off** and a starting number of **1**. Starting numbers must be positive integers. Settings define defaults for new blocks; existing blocks retain their own saved options.
- Use **Cassidy Dark** for both light and dark mode. Per-deck language memory remains off until enabled, as described below.

## Authoring behavior

### Target and language selection

Use this target order for the proposed Kit action:

1. If the caret or selection is wholly inside one recognized code block, update that complete block.
2. Otherwise, use a nonempty selection from one rich-text editor field to create a code block.
3. Otherwise, use the clipboard's plain text at the field's caret.

Reject selections crossing fields or crossing a code-block boundary into unrelated content. Empty input is a no-op. Preserve meaningful whitespace; do not read clipboard HTML as executable markup.

This deliberately improves on the inspected Syntax Highlighter implementation, which uses any nonempty `selectedText()` result and otherwise reads clipboard text. That implementation does not inspect the block around the caret and normalizes nonbreaking spaces only on the selection path.

Resolve the language in this order:

1. A language explicitly selected by the user in this editor for the current note and destination deck.
2. The existing code block's recorded, supported language.
3. A recognized Topic language that is checked for editor visibility.
4. The resolved deck's remembered language, when memory is enabled and that language is checked for editor visibility.
5. The configured enabled default language, falling back to the first checked language alphabetically as described in Settings.

An explicit dropdown choice overrides automatic selection for the current note, including later highlighting actions on that note. Clear that override and recalculate when the note or destination deck changes; do not clear it after every successful action. Discard an override if its language becomes unchecked or unsupported. Keep the override separate from per-deck memory: choosing a dropdown value alone does not persist a deck preference, while a successful explicit application can do so when memory is enabled.

Use canonical aliases in saved markup. An empty checked-language list continues to disable the editor action.

### Editing inside code blocks

- Within a Kit code block, Enter inserts a newline, including on an empty final line. It must not exit the block or trigger list continuation.
- With a collapsed caret at the end of the block, Arrow Down moves to a following normal paragraph, creating that paragraph if needed. Keep Enter available for intentional blank lines within code.
- Keep Tab and Shift+Tab as normal focus navigation. Apply the existing configured indentation shortcuts inside code, preserving source whitespace and the caret/selection.
- Paste into a code block as plain text, preserving line breaks and indentation while discarding clipboard HTML formatting.
- Do not automatically retokenize on every keystroke or paste. Users refresh highlighting through the existing Highlight Code action; ordinary editing must preserve source, block metadata, and native undo/redo.

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
- Save line-number visibility and the starting number in each block's metadata. Re-highlighting preserves those options rather than reapplying current Settings defaults; a block starting at 50 must still start at 50 afterward.
- Provide explicit access to the current block's numbering options so users can change visibility or the starting number without changing defaults for new blocks. Apply the change as one undoable block edit, preserving source, language, and cloze-handling metadata.
- Preserve intentional Anki cloze content by default, including contiguous delimiters, cloze numbers, answer content, hints, and supported nesting. Highlighting must not split cloze markers across token spans or change their meaning.
- When cloze-like syntax such as `{{c1::answer::hint}}` occurs in a new or unclassified block, offer **Preserve Anki clozes** by default and an explicit **Literal code** alternative for code intended to display that syntax. Save the selected handling mode in the code block's metadata and reuse it when highlighting again, without repeated prompts. Do not infer literal-versus-active intent from syntax alone.
- In Literal code mode, preserve the visible/copied source but ensure that Anki does not interpret those sequences as active clozes. Keep the protection compatible with text extraction and repeated highlighting. If either handling mode cannot preserve the structure safely, explain the problem and leave the original field unchanged.
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

### Processing limits and failure behavior

- Retain the initial Desktop authoring maximum of **50,000 source characters per code block**. Use the smaller provisional review limits below for JavaScript on all review clients, including Desktop. Limits apply to source text, excluding token markup and line-number decorations. Code beyond a limit stays readable as plain code, with its complete source preserved rather than truncated.
- For review, allow at most **10,000 source characters per code block**, **20,000 total code characters per submitted answer**, and **20 code blocks per submitted answer**. Each submitted answer has its own budget. Process blocks in document order; skip an oversized block, and when the remaining total budget cannot fit the next eligible block or the block-count budget is reached, leave that block and all subsequent blocks as plain code. Never partially highlight or truncate a block to fit a budget.
- Validate these provisional review limits on representative mobile devices with ordinary, malformed, and difficult language fixtures before release. Character and block-count caps bound submitted work, not execution time; do not present them as proven safe limits or guarantees against freezes. Verify any Web Worker approach in the supported Anki clients before relying on it for isolation or termination.
- For a new Desktop insertion above the limit, insert an escaped, unhighlighted code block and explain that the highlighting limit was exceeded. For an existing block above the limit, preserve its source and apply plain-code presentation as one undoable change. Do not silently strip intentional cloze handling or its metadata when using the fallback.
- Allow only **one active Desktop highlighting task across the add-on**, with no accumulating request queue. Repeated or concurrent actions receive clear busy feedback. Canceling a request or changing its target prevents later result application; the active worker still occupies the slot until it actually finishes or is terminated.
- Keep the original field unchanged on Desktop rendering failure, unsafe conversion, or cancellation, and provide a clear explanation. Review-time failures fall back to escaped plain code without interrupting the review flow or changing comparison results.
- Do not describe a background thread or discarded callback as an enforceable processing timeout. A hard timeout requires a worker that can actually be terminated; establish and verify such a mechanism before claiming that behavior. Test responsiveness and resource use, not only eventual completion.

## Themes, assets, and compatibility

- Let `themes.py` combine Kit-owned presets with Pygments presets and generate the selected light and dark definitions. Register the built-in **Cassidy Dark** preset under the stable identifier `cassidy-dark`.
- Keep Cassidy Dark's definition in `addon/desktop/syntax_highlighting/custom_themes/cassidy_dark.py`, separate from the vendored dependency. Initialize its palette, code-block foreground/background, and token font styles from the existing shared syntax stylesheet and syntax color variables. Use this same appearance in both modes; do not create a lighter variant or introduce a separate Kit Classic preset. This is the starter definition for the user's later theme edits.
- Default both light and dark theme settings to `cassidy-dark` in release defaults and runtime fallbacks. A missing, empty, or unsupported selection falls back to Cassidy Dark for that mode. Reset restores Cassidy Dark for both modes. Preserve valid explicitly selected alternatives across restarts and upgrades, and retain independent mode selectors so users can choose different presets later.
- Store the light/dark preset identifiers in collection configuration under `anki_global_kit.syntax_highlighting.themes`, using supported collection configuration APIs. Sync this pair with the collection so Desktop installations use the same choices when generating the shared media file. Keep local authoring controls outside that synced preference and regenerate theme media after a saved or synchronized theme selection changes.
- Bundle readable Cassidy Dark fallback variables and scoped rules with the review assets and editor styles, generated from the same preset definition. Use them when `_syntax-highlighting.css` is missing, has not downloaded, or cannot load; let the generated selected-theme stylesheet take precedence when available. Do not maintain a separate hand-edited fallback palette.
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

1. Establish isolated dependency loading and prove coexistence in both load orders, then add the pure rendering/theme services, initial Cassidy Dark preset, and package coverage.
2. Add editor targeting and insertion, the Python coordinator, language picker, configurable action, and per-deck language-memory service and deck resolution.
3. Add the dedicated Syntax Highlighting settings tab, grouped language checklist, theme settings/previews, shared styling, generated media delivery, and the confirmed note-type styling action.
4. Integrate Desktop Markdown rendering and replace the review tokenizer with the bundled JavaScript engine, language registry, and shared theme-role mapping.
5. Document migration, supported review languages, and tokenization differences; complete cross-client and performance verification.

Automated coverage:

- Render representative existing languages and newly supported HTML, CSS, Markdown, PowerShell, and Kotlin; validate aliases and invalid-language failures.
- Verify exact source preservation, escaping, Unicode, indentation, trailing newlines, literal template-like syntax, and cloze handling.
- Cover selection, clipboard, existing-block targeting, highlighted spans, empty input, invalid selections, and stale background results.
- Verify repeated highlighting updates the same block without duplicated wrappers or line numbers. Cover native undo/redo through browser or live integration checks where DOM-only tests cannot establish behavior.
- Cover Enter on ordinary and empty final lines, Arrow Down exiting to an existing or newly created paragraph, Tab/Shift+Tab focus navigation, configured indentation shortcuts, and plain-text paste. Verify ordinary editing does not automatically retokenize or damage block metadata.
- Verify per-block line-number visibility and starting numbers survive re-highlighting and global-default changes. Cover a start number of 50, explicit block-option edits, source preservation, and undo/redo.
- Verify settings defaults/types, shortcut conflicts and modifier labels, theme generation/scoping, and light/dark selection.
- Verify the exact 13-language checked defaults, Python selection, selected-first editor ordering versus fully alphabetical Settings groups, Alt+S/Option+S registration and conflict handling, and line numbers off with a starting number of 1.
- Cover typed dropdown/list/integer saving, Cancel, Reset, change detection, individual fallback for malformed saved fields, per-entry language validation, invalid UI input blocking Save, and preservation of unrelated stored settings.
- Verify the submitted-answer highlighting toggle appears only in Syntax Highlighting, retains its existing key/value/default, and leaves the Markdown rendering toggle under Cards.
- Inject CSS-generation, validation, installation, and settings-persistence failures. Verify no false successful save, the previous working settings/style are preserved or restored, staged edits remain in the open dialog for retry, and recovery failures are reported accurately.
- Verify Cassidy Dark appears in both mode selectors, starts from the existing Kit syntax appearance, and produces the same palette and token styles in both modes. Cover fresh settings, missing/empty/unsupported selections, reset, persistence of explicit alternatives, and regeneration after a preset-definition edit without rewriting note fields.
- Verify synced collection theme selections produce consistent media across Desktop installations, local editor controls remain local, and missing or delayed theme CSS uses Cassidy Dark until the selected stylesheet loads.
- Render shared fixtures through Pygments and JavaScript for all planned review languages. Check equivalent theme roles where both engines classify them, exact source preservation, and intentional tokenization differences without requiring identical HTML.
- Cover review aliases, explicit-fence versus Topic priority, unsupported explicit labels, engine failures, disabled highlighting, editor-hidden languages, and review behavior independent of deck memory.
- Cover dynamically submitted answers, repeated initialization/rerendering, preserved saved Pygments spans, HTML-like source, multiline Unicode text, and unchanged answer-comparison results and difference markers.
- Verify that checked and unchecked language groups are separate and each alphabetically sorted; toggling moves items between groups without duplicates or focus loss. Cover persistence, reset, default-language changes, an empty enabled list, and existing blocks using hidden languages. Verify name/alias search filters both groups without changing check states, clearing search restores both groups, keyboard navigation works, and support labels reflect the review registry.
- Verify language priority: current explicit dropdown choice, existing block, enabled Topic language, enabled remembered deck language, then enabled default. Verify manual choices survive repeated actions on the same note, reset on note/deck changes, and are invalidated if hidden or unsupported. Cover disabled memory, hidden remembered languages, unsupported stored aliases, and an empty enabled list.
- Verify memory updates only after successful explicit language application, preserves the global default and other decks' entries, survives reopening/renaming, and is isolated between collections. Cover cancel/failure, automatic detection, ordinary block refresh, and a deck change while rendering.
- Verify deck resolution for the Add window's destination versus the main window's current deck, a specific edited card, filtered cards' original decks, notes whose cards share one deck, and ambiguous notes with cards in multiple decks. Verify independent parent/child deck choices and safe behavior for deleted or unavailable decks.
- Verify settings saves and resets do not erase learned collection preferences, disabling/re-enabling retains them, and memory writes do not alter notes or managed media. Verify collection sync behavior manually between Desktop installations.
- Verify `_syntax-highlighting.css` is the exact media filename everywhere and the new feature's names do not reuse third-party branding.
- Verify confirmed styling installation is additive and idempotent and that cancellation leaves the note type unchanged.
- Verify active clozes and hints remain valid, literal cloze-like source remains literal, the chosen handling mode survives highlighting again, and unsupported structures leave the original field unchanged. Cover undo/redo and copied source in both modes.
- Cover the Desktop 50,000-character boundary, complete plain-code fallback above it, Desktop failures/cancellation leaving the field unchanged, one-task concurrency across editors, busy feedback without queued work, and stale results.
- Cover review boundaries of 10,000 characters per block, 20,000 characters per submitted answer, and 20 blocks. Verify independent answer budgets, document-order processing, oversized-block skipping, remaining-budget fallback without partial blocks or truncation, and unchanged comparison results. Benchmark difficult/malformed inputs and mobile responsiveness before accepting the provisional limits for release.
- Verify isolated Pygments loading with another version loaded before and after the Kit, and clear dependency-load failure without user-installed packages or field mutation.
- Verify external Pygments plugins cannot appear in discovery or be resolved through lookup, while bundled lexers/themes and Kit-owned presets remain available and consistent across installations of the same release.
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
