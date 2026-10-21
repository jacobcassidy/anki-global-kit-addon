# Syntax highlighting integration plan

## Goal and proposed scope

Bring Syntax Highlighter's (/Users/Jacob/Projects/Software/First-Party/Groups/JacobCassidy/Packages/Anki/Anki Third-Party Addons Modifications/Source/_anki-third-party-addons-modifications/272582198) useful Desktop authoring capabilities into Anki Global Kit so users can create highlighted code without installing a second add-on. Integrate with the kit's existing editor controls, settings, styling, media installation, and native undo support.

This document records the proposed implementation. The feature has not been implemented or verified in live Anki.

Include:

- Highlight selected code or plain text from the clipboard through a toolbar action and configurable shortcut.
- Choose a language from Pygments' available lexers.
- Configure the feature in a dedicated Syntax Highlighting settings tab, including a checkable list controlling which languages appear in the editor dropdown next to the highlighting button.
- Apply highlighting again to an existing code block, including blocks containing highlighted spans.
- Optional line numbers with a configurable starting number.
- Theme presets with independent light and dark selections and a preview.
- Consistent styling in editor fields and on cards, including synced clients.
- An explicit action to enable syntax styling on ordinary, non-Kit note types.
- Route Desktop Markdown code-block highlighting through the same rendering service.
- A lighting bolt icon for the editor toolbar button.

Do not include automatic collection-wide conversion, automatic changes to existing note types, per-deck language memory, or separate font-size and centering controls in the initial implementation. Preserve existing content and legacy stylesheets. Expanding the JavaScript review highlighter's language coverage is a separate change.

## Source structure and responsibilities

```text
addon/
├── vendor/
│   └── pygments/                    # Pinned dependency and license notices
├── desktop/
│   ├── syntax_highlighting/
│   │   ├── __init__.py              # Public service interface
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
├── editor/js/formatting/
│   └── code-block.js               # Editor extraction and block updates
├── shared/js/syntax-highlighting/  # Existing JS tokenizer while shared
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
- Associate each request with its editor, note, field, target range, and source snapshot. Discard the response if that target is no longer current or its content has changed.
- Register any JavaScript message handler only for the kit's own commands and the correct editor context. Do not accept arbitrary HTML insertion or arbitrary Python operations through the bridge.

### Settings and note-type operations

- Add a dedicated **Syntax Highlighting** tab to Settings. Put all settings for this feature there: toolbar visibility, shortcut enable/binding, editor language visibility, default language, line-number enable/start, theme selections, and a preview. Integrate it with the existing settings dialog's loading, saving, reset, and validation behavior.
- Show all available languages in a checkable list with two distinct groups: **Shown in editor** for checked languages first, followed by **Other languages** for unchecked languages. Sort both groups alphabetically by display name, ignoring case. Checking or unchecking a language moves it immediately to the correct alphabetical position in the other group, without duplicates and while preserving keyboard focus.
- Persist language choices using canonical language identifiers. Limit the editor language picker and default-language choices to checked languages. If the configured default is unchecked, select the first checked language alphabetically; if none are checked, disable highlighting and show an explanation directing the user to this tab. Keep that empty selection valid and reversible.
- Treat this list as editor visibility configuration, not a limit on Pygments' renderer. Changing the checked languages must not rewrite existing blocks, remove their language metadata, or stop supported explicit Markdown fence languages from rendering. Existing blocks retain their recorded language when highlighted again, even if that language is hidden from the picker.
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

For an existing block, preselect its recorded language. For a new block, preselect a recognized Topic language, then the configured default language. Allow the user to override the language in the picker. Use canonical aliases in saved markup.

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
- Move the current JavaScript tokenizer and language definitions under `src/shared/js/syntax-highlighting/` while both card and editor code consume them. Update imports and keep card-specific observation logic under `src/cards/`.
- Once Desktop Markdown rendering uses Pygments, remove its dependency on the JavaScript tokenizer if it has no remaining editor consumer. Keep review-time highlighting in JavaScript.
- Saved Pygments HTML and its CSS display across clients. Pygments itself runs only on Desktop; answers newly typed on AnkiWeb or mobile retain the JavaScript engine's language coverage.

## Themes, assets, and compatibility

- Let `themes.py` enumerate Pygments presets and generate the selected light and dark definitions. Include the existing Kit appearance as the default preset so installation does not unexpectedly recolor existing Kit content.
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

1. Add the vendored dependency, import adapter, pure rendering/theme services, and package coverage.
2. Add editor targeting and insertion, the Python coordinator, language picker, and configurable action.
3. Add the dedicated Syntax Highlighting settings tab, grouped language checklist, theme settings/previews, shared styling, generated media delivery, and the confirmed note-type styling action.
4. Integrate Desktop Markdown rendering, document migration and limitations, and complete cross-client verification.

Automated coverage:

- Render representative existing languages and newly supported HTML, CSS, Markdown, PowerShell, and Kotlin; validate aliases and invalid-language failures.
- Verify exact source preservation, escaping, Unicode, indentation, trailing newlines, literal template-like syntax, and cloze handling.
- Cover selection, clipboard, existing-block targeting, highlighted spans, empty input, invalid selections, and stale background results.
- Verify repeated highlighting updates the same block without duplicated wrappers or line numbers. Cover native undo/redo through browser or live integration checks where DOM-only tests cannot establish behavior.
- Verify settings defaults/types, shortcut conflicts and modifier labels, theme generation/scoping, and light/dark selection.
- Verify that checked and unchecked language groups are separate and each alphabetically sorted; toggling moves items between groups without duplicates or focus loss. Cover persistence, reset, default-language changes, an empty enabled list, and existing blocks using hidden languages.
- Verify `_syntax-highlighting.css` is the exact media filename everywhere and the new feature's names do not reuse third-party branding.
- Verify confirmed styling installation is additive and idempotent and that cancellation leaves the note type unchanged.
- Verify managed-media updates preserve unrelated files and the archive includes Pygments and notices but excludes local metadata and user data.

Run focused tests while developing, then the project test suites, relevant lint/format checks, `npm run build:addon`, `npm run check:assets`, and package validation. Do not present isolated tests as live Anki verification.

Manual acceptance should cover Anki Desktop 26.05 and a current supported release, Add/Browse editors, note switching while rendering, native undo/redo, light/dark mode, and synced display on AnkiWeb, AnkiMobile, and AnkiDroid. Confirm behavior against official minimum-version APIs before using new hooks or collection operations.

### Dependency measurements and references

The local Syntax Highlighter copy bundles Pygments 2.19.2. Inspection found 338 library files, approximately 4.45 MB of source, approximately 1.20 MB ZIP-compressed, 600 lexer entries, and 49 styles. These measurements describe that copy, not a promised release dependency version or final package size.

A standalone local benchmark for approximately 4,300 characters of Python took about 96 ms including initial imports and averaged about 5.7 ms with initialized imports and lexer. These are not live Anki measurements or guarantees for other inputs. Pygments does not guarantee bounded execution time; validate responsiveness with large snippets before release.

- [Pygments API](https://pygments.org/docs/api/)
- [Pygments HTML formatter](https://pygments.org/docs/formatters/#HtmlFormatter)
- [Pygments styles](https://pygments.org/docs/styles/)
- [Pygments license](https://github.com/pygments/pygments/blob/master/LICENSE)
- [Pygments execution-time considerations](https://pygments.org/docs/security/)
- [Anki hooks and filters](https://addon-docs.ankiweb.net/hooks-and-filters.html)
- [Anki collection APIs](https://addon-docs.ankiweb.net/the-anki-module.html)
