# Third architecture refactor plan

## Status and purpose

Planned; implementation has not started. Refactor the existing project incrementally while preserving its behavior, saved data, public interfaces, and supported clients.

Keep the runtime-first organization: Python Desktop integration in `addon/`, review JavaScript/CSS in `src/cards/`, editor JavaScript/CSS in `src/editor/`, and genuinely reusable web behavior in `src/shared/`. Improve the boundaries between these areas before changing the packaging layout.

This plan updates and supersedes the target architecture in the [second architecture refactor plan](refactor-2-plan.md). It carries forward its contracts, shared-code boundaries, note-type separation, lifecycle ownership, and resource/package assembly work, and adds complete editor feature ownership and shortcut separation. Keep the earlier plan unchanged as design history.

It also incorporates the [Desktop shortcuts refactor plan](refactor-shortcuts.md), with revised feature boundaries: feature action callbacks and shortcut contributions stay with their owning feature, and native editor shortcut coordination lives in `editor/features/shortcuts/`. Shared Desktop shortcut support and the reviewer/preview adapter remain in `desktop/shortcuts/`. Toolbar rendering and presentation belong to the toolbar feature. Reusable editor infrastructure is grouped under `editor/support/` and `src/editor/js/support/`, while feature-specific helpers stay with their feature. Browser-only features remain represented in the feature inventory without empty Python modules.

The existing layout and `AGENTS.md` remain authoritative until the corresponding implementation phase updates them together. Preserve feature behavior documented in the [syntax highlighting plan](archive/syntax-highlighting-plan.md). Inventory the current branch at implementation time, including completed legacy-removal work; preserve current shortcut recovery policies and do not restore retired Tab handling or editor `CodeBlock+` compatibility from earlier plans.

## Goals and constraints

- Give every editor feature a named home under `features/` in each runtime where it has an implementation.
- Keep feature actions, toolbar contributions, request handlers, state, and feature-local helpers with their owners. Group reusable editor transport, selection, field access, and transaction code under `support/`; keep lifecycle coordination in integration/runtime.
- Treat the editor toolbar and style installation as features with explicit ownership.
- Move native editor shortcut registration out of `editor/integration.py` into `editor/features/shortcuts/`, consuming shortcut contributions from each owning feature's `<feature>/shortcuts.py`, including small features.
- Make features traceable through an explicit catalog, matching runtime names, feature-oriented tests, and documented dependencies.
- Remove Desktop bridge dependencies from shared web controls.
- Centralize settings, asset, and bridge contracts without duplicating release defaults.
- Split the shared syntax theme service into palette definitions, Pygments adaptation, resolution, validation, CSS generation, and preview generation under `syntax_highlighting/themes/`.
- Separate note-type definitions, template assembly, change planning, and collection writes.
- Give card and editor runtimes explicit ownership of initialization, updates, and cleanup.
- Separate editable resources from generated bundles and assembled installable packages.
- Keep one repository, the current Python/JavaScript toolchains, separate card/editor bundles, and runtime-based tests. Introduce no application framework or package workspace solely for this refactor.
- Preserve existing settings keys, add-on/configuration identity, browser globals, bridge command strings, media filenames, saved HTML classes/data attributes, and note-type names and fields.
- Keep Anki Desktop 26.05 as the minimum. Verify version-sensitive integration changes against that target and official documentation during implementation.
- Keep colors token-based, web sizing in `rem` where appropriate, native editor toolbar spacing, and fixed/configurable shortcut conflict rules.
- Do not combine these structural changes with new features or unrelated behavior fixes.

## Target repository layout

```text
addon/                       # Python source and release configuration
resources/                   # Editable static assets and supplied user-file defaults
contracts/                   # Cross-runtime schemas and interface definitions
src/
├── cards/{js,css}/
├── editor/{js,css}/
└── shared/{js,css}/
scripts/                     # Generators, build, assembly, watch, package, verification
tests/
├── javascript/{cards,editor,shared,tooling}/
├── python/{desktop,tooling}/
├── fixtures/
└── support/
docs/
dist/                        # Ignored assembled packages and release archive
```

The following trees describe the final source layout. Existing implementation files remain unless a move or split is specified. Python package `__init__.py` files are omitted below except where their role matters; retain them where required. Do not create empty directories merely to match a diagram.

### Add-on source tree

```text
addon/
├── __init__.py                        # Required Anki entry point; starts bootstrap
├── config.json                        # Authoritative release defaults, including selections
├── manifest.json                      # Package metadata and minimum Anki version
├── README.md                          # Packaged add-on instructions
├── desktop/
│   ├── bootstrap.py                   # One owner for startup and hook registration
│   ├── paths.py                       # Paths inside an assembled runtime package
│   ├── generated/                     # Deterministic contract outputs; never hand-edit
│   │   ├── assets.py
│   │   └── bridge.py
│   ├── config/
│   │   ├── constants.py
│   │   ├── defaults.py                # Reads canonical config.json
│   │   ├── validation.py              # Type/schema validation without Qt
│   │   └── service.py                 # Anki persistence and runtime settings translation
│   ├── media/
│   │   ├── manifest.py                # Resolves generated asset definitions to runtime paths
│   │   └── install.py                 # Writes only managed media through Anki APIs
│   ├── note_types/
│   │   ├── definitions.py             # Topics, formats, fields, style mappings
│   │   ├── models.py                  # Plans, operations, impacts, results, service errors
│   │   ├── templates.py               # Assembly from supplied parts; no collection writes
│   │   ├── planning.py                # Plans from an explicit collection and current state
│   │   ├── service.py                 # Revalidation and application through col.models
│   │   └── stylesheet.py              # Existing CSS-import recognition
│   ├── shortcuts/
│   │   ├── helpers.py                 # Pure string parsing and normalization
│   │   ├── definitions.py             # Shared aliases and reserved/built-in tables
│   │   ├── validation.py              # Reservations and conflict warnings
│   │   ├── policy.py                  # Current unsupported-value/recovery policy
│   │   ├── labels.py                  # Display labels and modifier hints
│   │   ├── qt_helpers.py              # Reusable Qt matching where consumers need it
│   │   └── reviewer.py                # Reviewer routing, focus ownership, Qt filter
│   ├── editor/
│   │   ├── integration.py             # Anki lifecycle and feature coordination
│   │   ├── catalog.py                 # Ordered feature contributions and inventory
│   │   ├── support/
│   │   │   └── bridge.py              # Safe transport and supplied-command dispatch
│   │   └── features/
│   │       ├── shortcuts/
│   │       │   ├── registration.py    # Editor binding lifecycle and activation guards
│   │       │   ├── definitions.py     # Pure aggregation of feature shortcut declarations
│   │       │   └── validation.py      # Editor-specific reservations and conflicts
│   │       ├── toolbar/
│   │       │   ├── buttons.py         # Generic editor button/group rendering
│   │       │   └── presentation.py    # Toolbar assembly and presentation refresh
│   │       ├── markdown/
│   │       │   ├── actions.py         # Convert action and clipboard access
│   │       │   ├── bridge.py          # Markdown request validation and responses
│   │       │   ├── shortcuts.py       # Setting references and conversion action identifier
│   │       │   └── toolbar.py         # Markdown button contribution
│   │       ├── inline_code/
│   │       │   ├── actions.py
│   │       │   ├── shortcuts.py       # Required even for small shortcut-bearing features
│   │       │   └── toolbar.py
│   │       ├── blockquote/
│   │       │   ├── actions.py
│   │       │   ├── shortcuts.py
│   │       │   └── toolbar.py
│   │       ├── lists/
│   │       │   ├── actions.py
│   │       │   └── shortcuts.py       # Pure fixed-key/action declarations
│   │       ├── indentation/
│   │       │   ├── actions.py
│   │       │   └── shortcuts.py
│   │       ├── fields/
│   │       │   └── placeholders.py    # Temporary editor field hints, such as Compare
│   │       ├── styles/
│   │       │   ├── sources.py         # Read packaged CSS and optional user overrides
│   │       │   └── injection.py       # Assemble and inject editor style payloads
│   │       └── syntax_highlighting/
│   │           ├── actions.py
│   │           ├── bridge.py         # Editor-only commands, guarded requests, and results
│   │           ├── language_memory.py # Per-deck editor language memory
│   │           ├── language_menu.py  # Native Qt language menu and selection behavior
│   │           ├── language_selection.py # Editor default/allowed language choice and label
│   │           ├── ui.py              # Other editor-only controls, if needed after extraction
│   │           ├── shortcuts.py       # Highlight and exit-code-block declarations
│   │           └── toolbar.py
│   ├── syntax_highlighting/
│   │   ├── preferences.py
│   │   ├── rendering.py
│   │   └── themes/
│   │       ├── __init__.py            # Lightweight public API facade
│   │       ├── cassidy_dark_theme.py  # Kit-owned palette and font styles
│   │       ├── pygments_themes.py     # Discover/adapt bundled Pygments styles
│   │       ├── service.py             # List and resolve available themes
│   │       ├── validation.py          # Validate resolved/synced palettes
│   │       ├── css.py                 # Fallback and light/dark CSS generation
│   │       └── preview.py             # Theme preview HTML
│   ├── settings/
│   │   ├── dialog.py
│   │   ├── bindings.py
│   │   ├── save.py
│   │   └── pages/
│   │       ├── cards/{__init__,card_fields,card_reviews,card_toolbar}.py
│   │       ├── editor/{__init__,editor_fields,editor_styles,editor_text_handling,editor_toolbar}.py
│   │       ├── note_types/{__init__,actions,note_types,selection,table}.py
│   │       ├── syntax_highlighting/__init__.py
│   │       ├── changelog/{__init__,changelog}.py
│   │       └── help/
│   │           ├── __init__.py
│   │           ├── help.py
│   │           └── help-content.md   # Retained beside its owning Settings page
│   └── ui/
│       ├── constants.py
│       ├── help.py
│       ├── icons.py
│       ├── input_styles.py
│       ├── layouts.py
│       ├── lists.py
│       ├── markdown.py
│       ├── shortcut_input.py
│       ├── shortcut_rows.py
│       └── theme.py
└── vendor/                            # Pinned ignored dependencies and upstream notices
    ├── pygments/
    └── pygments-LICENSE
```

Keep vendored dependencies in their current source location during this refactor, with their existing bootstrap process and first-party lint/format exclusions. Copy only declared dependencies into assembled packages. Moving dependency provisioning is outside scope.

`addon/assets/`, `addon/templates/`, and the supplied `addon/user_files/` templates leave the source tree in the final assembly phase. Local `addon/meta.json` and user-created files are runtime state; migrate them separately and exclude them from commits and release inputs.

### Editor browser source tree

```text
src/editor/
├── js/
│   ├── index.js                       # Thin runtime entry point
│   ├── catalog.js                     # Explicit browser feature composition
│   ├── runtime/                       # Mount, settings updates, disposal
│   ├── support/
│   │   ├── editing/
│   │   │   ├── selection.js           # Field/shadow selection and source extraction
│   │   │   ├── edit-transaction.js    # Native undo and selection preservation
│   │   │   └── rows.js                # Operations shared by block editing features
│   │   ├── fields.js                  # Anki field/store access for editor consumers
│   │   └── bridge/
│   │       ├── transport.js           # Desktop transport and supplied-action facade
│   │       └── request-id.js          # IDs remain unique across reinjection
│   └── features/
│       ├── toolbar/
│       ├── markdown/
│       ├── inline-code/
│       ├── blockquote/
│       ├── lists/
│       ├── indentation/
│       ├── syntax-highlighting/
│       │   ├── index.js               # Feature setup and cleanup
│       │   ├── highlighting.js        # Selection, requests, and result application
│       │   ├── language-menu.js       # Browser-side language menu behavior
│       │   └── code-block-editing.js  # Code-block editing and exit behavior
│       ├── cloze/
│       ├── code-copy/
│       ├── code-spaces/
│       └── styles/
└── css/
    ├── editor-ui.css                  # Existing document stylesheet entry
    ├── editor-fields.css              # Existing field stylesheet entry
    └── features/                      # Styles grouped by their owning feature
```

Use Python underscores and JavaScript hyphens for matching feature names. Every Python editor feature lives in its own directory; never implement a feature as a standalone module directly under `editor/features/`, even when it currently needs only one implementation file. Put feature-specific actions, adapters, metadata, UI, and helpers in descriptively named modules within that directory. Every shortcut-bearing feature has its own pure `shortcuts.py`, regardless of feature size; features without shortcut contributions do not add empty shortcut files. Browser feature directories have clear entry modules. Do not add empty Python counterparts for browser-only behavior, or empty browser counterparts for Python-only hooks. Keep stylesheet entry points and output names stable while extracting feature styles; move feature-specific rules into matching files under `css/features/` only where meaningful.

### Test organization

Keep runtime-based discovery under `tests/javascript/` and `tests/python/`. Within editor coverage, group tests by the same feature names and keep separate runtime, shared-support (transport, fields, editing), shortcut, and bundle integration coverage. Move tests only with their owning phase and update discovery/import helpers together. Compare the discovered inventory before and after moves so reorganizing tests cannot silently drop coverage.

### Resource source tree

```text
resources/
├── README.md                          # Ownership, assembly mapping, generation rules
├── icons/
│   ├── blockquote.svg
│   ├── check.svg
│   ├── code-block.svg
│   ├── code-inline.svg
│   ├── copy.svg
│   ├── ellipsis.svg
│   ├── global-kit.svg
│   ├── help-indicator.svg
│   ├── indent-decrease.svg
│   ├── indent-increase.svg
│   ├── lightning-bolt.svg
│   ├── list-ordered.svg
│   ├── list-unordered.svg
│   ├── markdown.svg
│   ├── text-bold.svg
│   ├── text-italic.svg
│   └── text-strikethrough.svg
├── fonts/
│   ├── _meslolgl-nf.woff2
│   ├── FONT-LICENSES.md                # Source for generated combined notice
│   └── licenses/*.txt                 # Preserve every existing upstream notice
├── licenses/
│   └── javascript/
│       ├── diff-match-patch.txt
│       ├── highlight.js.txt
│       └── lezer.txt
├── templates/
│   ├── README.md
│   └── note-types/parts/
│       ├── html/
│       │   ├── advance-front.html
│       │   ├── advance-back.html
│       │   ├── cloze-front.html
│       │   └── cloze-back.html
│       ├── script/card-script.js
│       └── styling/
│           ├── imports.css
│           ├── style-default.css
│           ├── style-css.css
│           ├── style-git.css
│           ├── style-javascript.css
│           ├── style-php.css
│           ├── style-python.css
│           ├── style-react.css
│           ├── style-regex.css
│           ├── style-ruby.css
│           ├── style-shell.css
│           ├── style-typescript.css
│           ├── style-vocabulary.css
│           └── style-wordpress.css
└── user_files/
    ├── README.txt
    ├── editor-fields.css              # Supplied default, never a developer's live override
    └── editor-ui.css                  # Supplied default, never a developer's live override
```

Executable application JavaScript/CSS stays in `src/`. Template scripts and styling fragments stay with their template resources. Theme implementations remain with Desktop syntax highlighting; generated fallback CSS remains under `src/shared/css/generated/`. Help Markdown remains beside its Settings page. Keep the root `CHANGELOG.md` and `LICENSE` canonical and copy them into release packages.

### Assembled runtime package

```text
dist/
├── addon/                             # Persistent development package; dev link targets here
│   ├── __init__.py
│   ├── config.json
│   ├── manifest.json
│   ├── README.md
│   ├── CHANGELOG.md
│   ├── LICENSE
│   ├── desktop/                       # Copied Python source and generated definitions
│   ├── vendor/
│   ├── assets/
│   │   ├── cards/
│   │   │   ├── js/_anki-global-kit.min.js
│   │   │   └── css/_anki-global-kit.min.css
│   │   ├── editor/
│   │   │   ├── js/editor.min.js
│   │   │   └── css/{editor-fields,editor-ui}.min.css
│   │   ├── icons/*.svg
│   │   └── fonts/
│   │       ├── _meslolgl-nf.woff2
│   │       ├── _meslolgl-nf-license.txt # Generated from font notice sources
│   │       ├── FONT-LICENSES.md
│   │       └── licenses/*.txt
│   ├── templates/                     # Copied template resources
│   ├── user_files/                    # Defaults plus preserved local development overrides
│   └── meta.json                      # Local only; never a release input
├── release/addon/                     # Fresh isolated staging with supplied defaults only
└── anki-global-kit.ankiaddon           # Archive entries relative to release/addon/
```

Keep the installed runtime paths familiar. Python must resolve files relative to its assembled package, never by reaching outside it into repository `resources/`. The card installer continues copying reserved files into the active profile's `collection.media` root. `_syntax-highlighting.css` remains generated for that profile from its theme preferences, rather than becoming a static packaged fallback.

## Contract ownership

| Contract                | Canonical source                          | Consumers and generated outputs                                         |
| ----------------------- | ----------------------------------------- | ----------------------------------------------------------------------- |
| Release settings values | `addon/config.json`                       | Python defaults and generated browser fallback values                   |
| Settings metadata       | `contracts/settings.json`                 | Types, card/editor exposure, validation, documented translation rules   |
| Static asset identities | `contracts/assets.json`                   | Build/assembly paths, Python manifest definitions, package verification |
| Bridge messages         | `contracts/bridge.json`                   | Python and JavaScript command constants and payload validation          |
| Note-type definitions   | `addon/desktop/note_types/definitions.py` | Planning, template assembly, tests, package verification                |

Do not move default values into the settings schema or generate a competing release config. Generate browser fallbacks from `addon/config.json`, including only settings each runtime consumes. Preserve `note_type_selections` as a release-config entry managed through its existing service, rather than exposing it as an ordinary browser control.

Use a small generator with a non-mutating `--check` mode. Track deterministic Python outputs in `addon/desktop/generated/` and JavaScript outputs in `src/shared/js/generated/`; they must import without Anki or Qt. Keep generation independent of generated consumers to avoid bootstrap cycles. Validate schemas, unknown setting references, and output freshness.

Keep build source paths, assembled package paths, and public media names separate in the asset contract. Include generated per-profile assets as managed identities without requiring a static source file. Read canonical JSON directly in build tools where practical instead of generating extra wrappers.

Preserve existing bridge commands, globals, payload shapes, and safe serialization. Centralization does not require a new transport or protocol version. Keep Qt modifier translation in Desktop adapters and standard browser modifier interpretation in browser code; account for intentional runtime differences when generating fallback settings.

## Editor feature ownership

### Complete inventory

Every user-facing editor feature belongs under `editor/features/` or `src/editor/js/features/` for each runtime it uses. `integration.py`, browser entry points, and generic transport contain lifecycle or dispatch code; feature implementations have an explicit owner in the following inventory.

| Feature                                                | Python owner under `editor/features/` | Browser owner under `js/features/`                                     |
| ------------------------------------------------------ | ------------------------------------- | ---------------------------------------------------------------------- |
| Native editor shortcuts                                | `shortcuts/`                          | Python implementation; browser actions remain in their owning features |
| Toolbar                                                | `toolbar/`                            | `toolbar/`                                                             |
| Convert Markdown to HTML                               | `markdown/`                           | `markdown/`                                                            |
| Inline code                                            | `inline_code/`                        | `inline-code/`                                                         |
| Blockquote                                             | `blockquote/`                         | `blockquote/`                                                          |
| Lists                                                  | `lists/`                              | `lists/`                                                               |
| Indentation                                            | `indentation/`                        | `indentation/`                                                         |
| Syntax highlighting, language menu, code-block editing | `syntax_highlighting/`                | `syntax-highlighting/`                                                 |
| Field placeholders                                     | `fields/placeholders.py`              | Uses Anki's existing field-description API                             |
| Editor styles                                          | `styles/`                             | `styles/`                                                              |
| Cloze keyboard behavior                                | Browser implementation only           | `cloze/`                                                               |
| Copy source/code                                       | Browser implementation only           | `code-copy/`                                                           |
| Code space normalization                               | Browser implementation only           | `code-spaces/`                                                         |

Update this inventory when the baseline identifies additional features. Keep `catalog.py` and `catalog.js` as explicit composition lists for their runtime. Document each feature's settings references, action identifiers, bridge commands, source entry points, styles, shared-service dependencies, and tests in the developer feature map. Document browser-only/Python-only entries explicitly; a feature's absence from another runtime must be explained by its responsibilities.

### Feature contributions and catalog

A feature supplies its actions, button descriptions, shortcut contributions, settings-key references, and optional lifecycle/message handlers through a small, explicit interface. Every Python feature has a directory; implementation belongs in descriptive modules within that directory, including for small features. Shortcut-bearing Python features export their pure shortcut declarations from `<feature>/shortcuts.py` and assemble contributions with their action callbacks through an explicit entry point or the catalog. Use plain functions and small data structures, with no filesystem discovery or general plugin framework.

The catalog establishes feature participation and existing action/group ordering. It passes feature shortcut declarations and action callbacks to the editor shortcuts feature, button contributions to the toolbar, and command handlers to bridge dispatch. Keep ordering explicit, including current configurable-shortcut priority. Derive each runtime's dispatch and toolbar lists from its catalog so adding a feature does not require another feature-specific branch in integration.

Feature catalogs compose implementations; canonical settings, asset identities, and bridge strings remain in the contract sources above. Catalogs refer to those definitions rather than creating competing metadata/default tables. Assemble the canonical editor fixed-shortcut map from pure feature declarations through `editor/features/shortcuts/definitions.py`; Settings reservations, native registration, and browser injection consume that same aggregate. Shared aliases and common warning tables remain in `desktop/shortcuts/definitions.py`. Browser and Python composition lists may differ according to runtime responsibilities.

### Shared editor support

Use `addon/desktop/editor/support/` and `src/editor/js/support/` for infrastructure genuinely reused by several editor features. Organize it by concrete responsibility, such as editing or transport. Start code with its feature and extract a shared operation when actual consumers need the same behavior. Feature-specific helpers, integrations, generators, and other supporting files remain with their owner unless their responsibility belongs to runtime coordination or build tooling.

Python support initially contains `support/bridge.py`, extracted from generic serialization/invocation in integration and feature handlers. It safely serializes browser arguments, invokes existing browser actions, and dispatches incoming commands to handlers supplied during composition. Feature-specific payload validation, limits, warnings, pending requests, and result/failure behavior remain in feature bridge modules. Add other Python support modules only when real shared consumers justify them.

Use the following browser migration map:

| Current implementation                                     | Target under `src/editor/js/`         | Consumers/responsibility                                                         |
| ---------------------------------------------------------- | ------------------------------------- | -------------------------------------------------------------------------------- |
| `helpers/selection.js`                                     | `support/editing/selection.js`        | Field/shadow-root selection and selected source for multiple formatting features |
| `helpers/edit-transaction.js`                              | `support/editing/edit-transaction.js` | Shared native undo transactions, marker cleanup, and selection preservation      |
| `helpers/fields.js`                                        | `support/fields.js`                   | Field/store access used by Markdown, syntax highlighting, and styles             |
| `helpers/request-id.js`                                    | `support/bridge/request-id.js`        | Common request identities retained across bundle reinjection                     |
| Shared row/range operations from `formatting/blocks.js`    | `support/editing/rows.js`             | Operations actually reused by lists, blockquote, and indentation                 |
| Generic Desktop communication from feature implementations | `support/bridge/transport.js`         | Safe transport and existing global API facade bound to supplied feature actions  |

These locations replace the earlier standalone editor `editing/` and `bridge/` infrastructure directories. Preserve Anki-specific field handling, request identities, public API names, native edit semantics, and lifetime ownership while moving code. Extract common mechanics only; keep feature-specific selection policies and asynchronous target snapshots in their features.

Keep `integration.py`, browser `runtime/`, and catalogs outside support as the explicit lifecycle/composition owners. Build generators remain under `scripts/`; shared Desktop shortcut services remain in `desktop/shortcuts/`; syntax rendering/themes remain in `desktop/syntax_highlighting/`; common card/editor web behavior remains in `src/shared/`. A reusable toolbar renderer still belongs to `features/toolbar/`, and native editor registration still belongs to `features/shortcuts/`.

Do not introduce `features/utils/`, `support/toolbar/`, or `support/shortcuts/` as alternate homes for those feature implementations. A helper used only by Markdown stays under `features/markdown/`; inline-code caret workarounds stay with inline code; style insertion/retry helpers stay with styles. The styles feature separates stylesheet source reading and override selection in `sources.py` from payload assembly and editor injection in `injection.py`. Keep syntax theme resolution and CSS generation in `desktop/syntax_highlighting/`. Put feature-local helpers in the owning directory, using descriptive module names; do not create empty support or helper modules to match a diagram.

### Toolbar is a feature

Move `editor/buttons.py` into `editor/features/toolbar/buttons.py`. Move browser `toolbar.js` into `js/features/toolbar/`. Toolbar rendering, grouping, visibility, disabled-state handling, tooltip presentation, and presentation refresh belong to this feature. Keep the existing native group spacing and token-based styling.

Individual features own their button labels, icon references, setting references, and action callbacks. The toolbar renders those contributions. Replace positional slices of `custom_buttons` with explicit ordered contributions/groups supplied through the catalog. A Markdown or blockquote addition should require changing its owning feature and composition, while the renderer remains generic.

Keep genuinely shared Qt widgets in `desktop/ui/` when multiple Desktop areas consume them. Keep editor-specific toolbar helpers with the toolbar feature; do not introduce another generic `editor/ui/` folder for its implementation.

Apply this ownership rule to all Desktop UI code, not only toolbar code: Qt widgets, dialogs, labels, layout helpers, and presentation functions used only by an editor feature belong in that feature's package. For example, syntax-highlighting menus and controls belong beside its actions and bridge; a `ui.py` module is appropriate when that gives the feature a clear home. Keep `desktop/ui/` for controls and presentation utilities with real consumers in multiple Desktop areas, such as Settings and the editor. Settings-page UI remains under `desktop/settings/pages/`, owned by its Settings page. During migration, check actual imports and call sites before moving each `desktop/ui/` module; split a module when only some of its pieces are editor-specific. Do not move code into a feature solely because it creates a Qt widget.

### Actions and shortcut contributions

Move `_toggle_inline_code()`, blockquote/list action adapters, `_convert_markdown()`, indentation adapters, exit-code-block behavior, and syntax-highlighting action entry points to their owning features. Toolbar and native keyboard activation invoke the same feature callbacks. Preserve clipboard-read timing, selected-field guards, existing browser globals, and current feature calls.

Each feature owns its shortcut contribution: action identifier, references to existing shortcut/enabled settings, any fixed key declaration, and the associated action callback supplied during composition. Configurable defaults remain in `addon/config.json`. Every shortcut-bearing Python editor feature must use `<feature>/shortcuts.py`, including small features. This applies to `markdown/shortcuts.py`, `inline_code/shortcuts.py`, `blockquote/shortcuts.py`, `lists/shortcuts.py`, `indentation/shortcuts.py`, and `syntax_highlighting/shortcuts.py`. Keep action implementations and toolbar contributions in sibling modules; do not inline shortcut declarations into a feature action module or package initializer.

Keep each feature's `shortcuts.py` pure and separate from Qt-dependent action callbacks so Settings, configuration validation, and headless tools can import it safely. For example, `features/lists/shortcuts.py` owns fixed list bindings, while `features/shortcuts/definitions.py` assembles their canonical aggregate. Metadata modules and package initializers must load without importing integration, Qt, Settings services, or runtime catalogs. Bind callbacks to declared action identifiers at composition time. Detect duplicate declarations instead of silently overriding them.

### Editor shortcuts is a feature

Move `_add_shortcut()`, configurable-binding selection, native activation guards, shortcut creation/reuse/rebinding/disabling, and the weak registered-editor registry from integration into `editor/features/shortcuts/registration.py`. Keep editor-specific fixed reservations, duplicate-binding resolution, and intended native-indentation exceptions under `editor/features/shortcuts/validation.py`. Consume supplied feature declarations/actions through the catalog, preserving existing action priority and activation guards.

This feature coordinates native registration across all editor actions. Individual features contribute their shortcuts to it rather than independently creating competing `QShortcut` objects. Expose a small API such as `register(shortcuts, editor, contributions)`, `refresh_bindings(editor, settings, contributions)`, and `iter_live_editors()`. Preserve editor-widget ownership, weak activation references, object reuse, and cleanup. Keep registration free of a hardcoded feature-action dispatch chain.

`editor/integration.py` remains the Anki hook coordinator. It connects the native registration entry point once and coordinates Settings refresh: obtain settings, iterate live registered editors, refresh bindings, and dispatch feature settings/presentation updates. The shortcuts feature owns its editor registry and native binding lifecycle. Neither registration nor individual action features import `editor/integration.py`. Do not create a central `editor/actions.py` or a native registration module at `desktop/shortcuts/editor.py`.

The native editor shortcuts feature needs no empty browser counterpart. Browser action implementations and any feature-specific key handling remain under their owning browser features, consuming the injected fixed map and existing platform conventions. Keep their registrations/lifecycle coordinated through the browser catalog/runtime.

### Shared Desktop shortcut support

Retain `desktop/shortcuts/` for the existing consumers beyond the editor: Settings shortcut capture/conflict checks for cards and editor, configuration recovery for both contexts, and Desktop reviewer/preview keyboard routing. Shared parsing, normalization, labels, common reserved/built-in tables, reusable Qt matching, and genuinely shared policy belong here.

Keep `reviewer.py` outside editor features. It owns card review/preview focus tracking, card indentation overrides, card-toolbar navigation ownership, and Preferences restoration. Preserve these behaviors and the Desktop-only adapter boundary; review behavior needed across clients remains in `src/cards/`.

Editor-specific key definitions and validation move to the editor shortcuts feature. Shared validation accepts supplied definitions when needed and must not import editor catalogs or feature implementations. Settings can combine shared checks with the pure editor reservation API explicitly. Keep the existing shared recovery policy for card/editor saved values, preserving its behavior without introducing a configuration-to-feature-runtime dependency.

### Markdown and highlighting

Move Markdown request validation, conversion-limit warnings, background-request coordination, and result/failure responses out of `features/syntax_highlighting.py` into `features/markdown/bridge.py`. Browser selection preference, Markdown conversion, pending request snapshots, code-block result assembly, and insertion stay in `js/features/markdown/`.

Both Markdown and syntax-highlighting features call the reusable renderer under `desktop/syntax_highlighting/`. Keep Pygments rendering, source-size limits, and language discovery there because both features and the Settings page consume them. Keep `rendering.py` limited to plain-input rendering and language metadata; it must not import Anki editor classes, Qt, Settings, or editor feature modules. Move editor-only default/allowed language selection to `editor/features/syntax_highlighting/language_selection.py`. Per-deck language memory belongs to `editor/features/syntax_highlighting/language_memory.py`, where its editor-only policy can stay with the feature. Theme resolution and generation stay in the shared theme service. Shared rendering and theme services must not import editor feature modules, toolbar code, or editor bridge handlers. Preserve any shared serialization/scheduling required by the renderer without coupling Markdown's request lifecycle to the syntax-highlighting feature's UI state.

The Desktop editor feature owns toolbar and shortcut contributions, editor settings access, native Qt language-menu presentation, per-editor and per-deck state, syntax-highlight/code-block-options message handling, and guarded result delivery. Keep the native menu in `language_menu.py`; use `ui.py` only for other syntax-highlighting controls that remain after the menu has a clear owner. Keep `language_selection.py` as pure feature policy over supplied settings and shared language metadata. The syntax-highlighting bridge handles only syntax-highlight and code-block-options requests; Markdown conversion requests and their pending state belong to the Markdown feature. Both feature bridges call the shared renderer directly and own their own request lifecycle.

The browser editor feature owns DOM selection, request IDs and payload assembly for its commands, code-block DOM changes, native editor transaction integration, and result application. Its `language-menu.js` owns the browser-side menu opened from code-block language labels; it does not own the native Qt toolbar menu. Keep generic transport in `support/bridge/transport.js` and keep command names and payload schemas in generated contracts. Shared browser syntax-highlighting helpers expose DOM presentation or pure language/classification operations through explicit inputs and callbacks; they do not call `pycmd` or access editor globals. Card review keeps its own highlighting engine and lifecycle, using only those shared helpers it actually needs.

The trace for a conversion is: toolbar or shortcut contribution, Markdown action, browser conversion, Markdown request handler when code blocks need rendering, shared renderer, Markdown response, then guarded browser insertion. Every application step has a Markdown owner; shared dependencies are explicit.

### Shared editing and lifecycle

Split `formatting/blocks.js` by behavior: blockquote owns quote toggling, lists own list transformations, and indentation owns indentation behavior. Extract only operations actually shared by these features into `support/editing/`, such as row traversal, selection mapping, and native edit transactions. Preserve selection, native undo/redo, list nesting, saved code rows, and toolbar controls during extraction.

Move browser `helpers/selection.js` and `helpers/edit-transaction.js` into `support/editing/`, `helpers/fields.js` into `support/fields.js`, and `helpers/request-id.js` into `support/bridge/`. Keep the runtime responsible for lifecycle coordination of support-owned state/listeners. Keep feature-specific entry/exit workarounds, normalization listeners, and clipboard behavior with their features. Move code-block highlighting/editing and browser language menus into the syntax-highlighting feature, copy behavior into code-copy, cloze handling into cloze, and style installation into styles. The browser syntax-highlighting feature owns editor DOM behavior and invokes the Desktop feature through the stable bridge contract; shared browser helpers and the card runtime must not depend on that feature.

The browser runtime coordinates feature mount, settings updates, note-context resets, and disposal. Features own their listeners, observers, timers, and pending operations, returning cleanup functions or registering them with the runtime. Toolbar and styles mount in an explicit dependency order. Preserve a stable runtime identity across reinjection and keep existing browser globals as thin dispatch facades to the current feature actions.

## Syntax theme service

Replace `addon/desktop/syntax_highlighting/themes.py` with a `themes/` package. Keep this service outside editor features because Settings, editor styles, card-media installation, and build/export tooling all consume it.

| Current responsibility                                                                           | Target module under `syntax_highlighting/themes/` |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------- |
| `custom_themes/cassidy_dark.py` palette and font-style `PRESET`                                  | `cassidy_dark_theme.py`                           |
| Bundled Pygments discovery, style display names, token-role adaptation, and adaptation fallbacks | `pygments_themes.py`                              |
| `available_themes()` and `resolve_preset()` orchestration                                        | `service.py`                                      |
| `validate_resolved_theme()`, palette-role validation, and existing role fallback rules           | `validation.py`                                   |
| `generate_theme_css()`, `generate_theme_pair_css()`, CSS variables, and token-selector rules     | `css.py`                                          |
| `theme_preview_html()`                                                                           | `preview.py`                                      |
| Existing public theme functions used by consumers                                                | Lightweight exports from `__init__.py`            |

Use `pygments_themes.py` to identify the bundled theme provider explicitly; avoid the ambiguous name `default_themes.py`. Enumerate and adapt the existing vendored Pygments styles without copying their palettes into first-party source. Move the Kit-owned Cassidy Dark definition into `cassidy_dark_theme.py` and remove `custom_themes/` after its consumers migrate. Preserve the existing preset identifiers and fallback choices, including `cassidy-dark` and `pygments:<name>`.

Keep `themes/__init__.py` as a small public facade so imports such as `from ...syntax_highlighting.themes import generate_theme_pair_css` and `load_addon_module("desktop.syntax_highlighting.themes")` continue working. It must not register hooks, import Qt/Settings/editor features, enumerate Pygments styles, or generate artifacts on import. Internal modules import sibling implementations directly, avoiding cycles through facade exports. Preserve startup-free loading and the renderer's bundled-module isolation when accessing Pygments.

Theme preferences remain in `syntax_highlighting/preferences.py`, including collection storage, validation calls, format versions, and revisions. Preserve resolved saved palettes, IDs, display names, role fallback behavior, bold/italic resets, light/dark mode independence, card/editor selectors, and generated CSS behavior during extraction. This refactor does not change default selections or duplicate release defaults. Preserve CSS-variable-based consumption of palette colors.

`themes/css.py` and `themes/preview.py` provide reusable generation functions. `scripts/export_syntax_themes.py` remains the build entry point that writes the generated fallback stylesheet; profile media installation remains responsible for the collection-specific `_syntax-highlighting.css`. Update generator, watcher, package verification, headless-loader support, tests, and consumers as needed for the file-to-package transition. Regenerate affected tracked CSS/bundles and check output freshness before committing the implementation.

## Dependency rules

- `src/shared/` may use browser APIs but must not invoke `pycmd`, access `ankiGlobalKitEditor`, or import card/editor application modules. Shared controls receive callbacks or capabilities from their owning runtime.
- Shared code owns common DOM presentation and interactions. Editor selection, native undo integration, and Desktop commands remain editor responsibilities; review observation and answer persistence remain card responsibilities.
- Individual action features must not import `integration.py`, catalogs, or the editor shortcuts registration module. Catalogs/coordinators compose feature contributions; generic transport dispatches handlers supplied during composition.
- The toolbar consumes feature button contributions; other features must not depend on its internal renderer. Editor `support/` modules must not import feature implementations, catalogs, or integration; shared editing/transport receives explicit inputs or supplied callbacks. Feature-specific helpers remain inside their owning feature.
- Feature bridge modules use `support/bridge` transport and generated contracts; generic transport must not import concrete feature handlers. Shared renderer and theme services must not import editor features. Theme data/validation/resolution/generation remain startup-free, with Pygments access isolated through the existing bundled-module mechanism.
- Shared shortcut helpers, common definitions/validation, recovery policy, and pure editor feature shortcut declarations/aggregates remain free of Anki/Qt imports. Shared Desktop support must not import editor feature implementations; Settings explicitly combines shared and editor-specific pure validation. Qt matching helpers resolve explicit inputs; runtime routers own Settings access, target selection, focus, event acceptance, and action invocation.
- Desktop services must not import Settings pages or the dialog. Settings collects user intent, presents confirmations, and calls services.
- Note-type template assembly and definitions must load without Anki/Qt. Planning receives a collection explicitly; application/revalidation uses documented collection APIs. Resolve `mw.col` at UI or hook boundaries.
- Keep `scripts/addon_module_loader.py` as the supported startup-free import path. Pure-module imports must neither execute `addon/__init__.py` nor register hooks.
- Keep package initializers lightweight and startup registration owned by `desktop/bootstrap.py` and its explicit feature coordinators.
- Add focused import/dependency checks for these boundaries instead of introducing a general dependency-injection framework.

## Delivery phases

### Phase 0: Establish the compatibility baseline

1. Inventory current settings, generated outputs, public media names, bridge commands/globals, template markup, test discovery, package entries, and runtime initialization owners. Include completed card-loader, shortcut-policy, and legacy-removal work when implementation begins; use the checked-out source as the baseline rather than restoring older behavior from a plan.
2. Record current automated results and known limitations. Keep unrelated working-tree changes outside refactor commits.
3. Add only missing regression coverage needed for the boundary changes: reinjection, settings refresh, note-type plan revalidation, unmanaged-media preservation, and package isolation. Reuse existing tests where they already cover these behaviors.
4. Record a feature map linking current Python actions, JavaScript implementations, toolbar entries, shortcuts, settings, bridge handlers, styles, and tests to their proposed owners. Include toolbar and styles as features and identify browser-only entries.
5. Document the source/runtime/resource distinction and the order below. Do not move resources yet.

Exit criteria: a recorded compatibility inventory and an understood test baseline; failures are resolved or explicitly identified before attributing later regressions to the refactor.

### Phase 1: Centralize settings, asset, and bridge contracts

1. Add the three canonical contract files, generator, generated modules, and freshness checks. Keep current output/resource locations during this phase.
2. Replace handwritten card/editor fallback defaults with generated values and thin runtime normalization. Preserve current enabled states, shortcut behavior, and handling of malformed saved configuration.
3. Have `desktop/media/manifest.py`, build tooling, and verification consume the same asset identities. Replace verification that parses build-script strings with checks of structured definitions and actual outputs.
4. Move Python/JavaScript bridge literals into generated definitions, preserving the existing external interface. Extract shared editor serialization/invocation into `desktop/editor/support/bridge.py` and generic browser transport into `src/editor/js/support/bridge/transport.js`; keep lifecycle coordination in `integration.py` and pass feature handlers into bridge dispatch explicitly.
5. Add generation to build/watch/package dependencies and CI. A schema/default change must regenerate affected consumers before bundling.

Exit criteria: no duplicated fallback values or public asset/bridge definitions in active consumers; intentional runtime translations are documented and tested; generation is repeatable and `--check` detects stale outputs.

### Phase 2: Decouple shared code-block controls

1. Refactor `src/shared/js/syntax-highlighting/code-block-controls.js` into common decoration/interaction behavior accepting explicit optional callbacks for language menus and options.
2. Supply Desktop behavior through the owning editor feature adapter under `src/editor/js/features/`. Supply card capabilities under `src/cards/js/` without relying on Desktop globals. Preserve existing copy behavior and focus/selection outcomes.
3. Keep editor-specific manipulation and native undo integration outside shared controls. Keep card scope restrictions so ordinary cards remain untouched.
4. Add a focused dependency check preventing shared imports of application modules and direct Desktop bridge calls.

Exit criteria: shared code runs with no Desktop bridge present, existing card/editor bundle regressions pass, and editor actions still reach the same Python handlers.

### Phase 3: Establish complete editor feature ownership

1. Introduce explicit Python/browser catalogs and the feature map, preserving current ordering and public interfaces. Move toolbar rendering into `features/toolbar/`, with each feature supplying its button definitions and callbacks.
2. Extract Markdown, inline-code, blockquote, list, and indentation adapters from integration into their feature owners. Move feature-specific labels/tooltips and settings references with them, and create `<feature>/shortcuts.py` for every shortcut-bearing Python feature regardless of size; keep lifecycle dispatch in integration/runtime, generic communication in support/bridge, and style payload preparation with the styles feature.
3. Split the Python syntax-highlighting module by responsibility into its editor feature modules, and move Markdown request handling to Markdown. Keep Pygments rendering/language discovery shared under `desktop/syntax_highlighting/`; move editor language selection and per-deck memory into the editor feature. Preserve renderer safety, feature-owned busy/request state, validation, warnings, and asynchronous result guards.
4. Reorganize browser implementations under `js/features/`, including toolbar, syntax highlighting/language menus/code-block editing, styles, cloze, code-copy, and code-spaces. Extract common editing operations into `support/editing/` and migrate field access/request IDs according to the support map, while preserving DOM structure, selection, and undo behavior. Keep single-feature helpers inside their feature and keep browser/editor bridge contracts explicit.
5. Move custom/packaged CSS composition from integration into the styles feature. Keep document versus field/shadow-root style installation and existing user overrides intact; group feature-specific CSS under matching stylesheet paths where useful.
6. Split the shared theme service into the `syntax_highlighting/themes/` package described above. Move Cassidy Dark and Pygments adaptation into their dedicated modules, preserve the public facade and saved-data/CSS behavior, and remove `custom_themes/` after migration. Update build/watch/export/package tooling for the package layout.
7. Migrate feature tests, imports, build/watch inputs, test support, and dependency checks with each move. Regenerate affected assets at their existing output paths. Keep lifecycle installers working through this phase; complete replacement/disposal coordination in Phase 6.

Exit criteria: every editor feature has a documented owner in the runtime(s) it uses; toolbar and styles are included; integration contains coordination; feature actions can be traced without following feature-specific dispatch branches through infrastructure; and the shared theme package loads headlessly with stable public functions, saved palettes, and generated output.

### Phase 4: Separate shortcut helpers and runtime registration

1. Extract pure parsing/normalization to `desktop/shortcuts/helpers.py`, shared aliases/common tables to `definitions.py`, and common reservations/warnings to `validation.py`. Keep shared unsupported saved-value recovery in the existing `policy.py`; move display formatting and hints into `labels.py`. Move editor-specific validation and fixed-key aggregation into `editor/features/shortcuts/`.
2. Supply platform inputs explicitly to pure helpers. Preserve current aliases, literal plus parsing, shifted punctuation, supported modifier conventions, fixed reservations, intended native-indentation exceptions, and current unsupported-value recovery. Preserve the active card `CodeBlock+` convention without restoring retired editor compatibility.
3. Extract reusable Qt modifier/key matching to `qt_helpers.py` where the current baseline has real consumers. Leave focus ownership, webview selection, Qt event acceptance, Preferences restoration, and reviewer hooks in `reviewer.py`. Do not reintroduce retired Tab interception from the older shortcuts plan.
4. Move native editor registration, guarded activation, binding refresh, and weak registry ownership into `editor/features/shortcuts/registration.py`, consuming the feature-owned shortcut declarations/actions established in Phase 3. Preserve centralized conflict resolution and action priority. Keep Anki hook registration and Settings-facing refresh coordinated once through integration/bootstrap.
5. Update Settings validation, input controls, action labels, browser-map injection, test fixtures, and tooling to consume shared helpers and the pure editor aggregate/validation API. Verify that Settings/headless imports do not load Qt-dependent feature callbacks or catalogs. Preserve shortcut-object reuse and disabling/rebinding without touching other add-ons' bindings.
6. Remove `formatting.py` after internal consumers migrate. Retain forwarding only for a documented external interface; avoid duplicate definitions and temporary central action collections.

Exit criteria: shortcut helpers import without Qt, fixed definitions have one owner, native registration lives in `editor/features/shortcuts/registration.py`, toolbar/keyboard activation reaches the same feature actions, and existing conflict/rebinding/platform behavior is preserved.

### Phase 5: Split note-type responsibilities

1. Extract definitions, dataclasses/errors, template assembly, and planning from `desktop/note_types/service.py` into the target modules. Keep application and immediate pre-write validation in the service.
2. Pass the collection explicitly from Settings/action coordinators. Preserve collection identity checks in confirmed plans and current partial-result/error reporting.
3. Preserve the complete plan/confirm/revalidate/apply sequence. Revalidate replacement targets and removal impact before writing; retain template names and template/card counts in confirmation. Allow deletion only under the existing empty-type/uncreated-topic rules.
4. Update Settings imports and existing tests together. Update `scripts/verify_package_assets.py` to load canonical pure definitions through the headless loader rather than extracting `TOPICS` and `FORMATS` from service source with AST parsing.
5. Keep template parts in their current location until Phase 7. Do not change required markup or existing note types during extraction.

Exit criteria: template assembly loads without Anki/Qt, collection dependencies are explicit, and all create/skip/replace/delete and confirmation-change regressions pass without altered outcomes.

### Phase 6: Establish browser runtime lifecycle ownership

1. Introduce small coordinators under `src/cards/js/runtime/` and `src/editor/js/runtime/` with explicit mount, settings-update, and disposal responsibilities. Keep entry points as thin bootstrap calls.
2. Connect the Phase 3 feature catalogs/installers to lifecycle coordination. Have feature installers return cleanup functions or register resources with their runtime. Separate document-lifetime handlers from card/note-lifetime work so card changes do not reinstall everything.
3. Preserve a stable global runtime handle across bundle reinjection. Dispose an old instance before replacement, clean observers/listeners/timers, and ensure stale asynchronous callbacks cannot update a replaced card or editor context. Keep existing public globals as compatibility facades.
4. Make updated settings reach existing features without accumulating handlers or capturing stale settings. Distinguish settings refresh from full runtime replacement.
5. Preserve answer storage, client detection, AnkiWeb integration, editor selection/native undo, and existing card-loader failure/retry behavior. Use supported client hooks where verified; retain observation where required.

Exit criteria: repeated bundle evaluation, card transitions, editor note loads, settings updates, and disposal produce one active owner for each resource. Existing answer persistence and keyboard behavior remain unchanged across simulated clients.

### Phase 7: Move resources and assemble installable packages

1. Move editable icons, fonts/notices, JavaScript dependency notices, template parts, and supplied user-file defaults into `resources/` using the target tree. Move only supplied tracked user-file defaults; preserve local overrides separately.
2. Add an assembly script with explicit development and release modes. Copy Python/vendor/resources, build bundles, generate notices, and verify the complete staged package. Retain runtime `assets/` and `templates/` paths and public filenames.
3. Change source SVG imports to `resources/icons/`. Update `scripts/build.config.js`, `font_notices.py`, `export_syntax_themes.py` where affected, the asset contract, package verification, and source/bundle tests in the same migration.
4. Build the development package at `dist/addon/`. Update `scripts/link_addon.js` to assemble before linking while retaining the installed `anki-global-kit-dev` destination and configuration identity. Recognize the previous checkout-owned source symlink and migrate it explicitly; continue refusing to overwrite unrelated destinations.
5. Before switching the development link, preserve local `meta.json`, settings, and all existing user files, including overrides of supplied filenames. Development assembly must preserve those files and seed defaults only when missing. Never replace the persistent development directory wholesale while it is linked into Anki.
6. Make watch mode perform initial assembly and follow Python, resources, contracts, generated dependencies, and browser sources. Copy Python edits and report when an Anki restart is needed. Stage only successful generated builds, serialize dependent work, and remove obsolete Kit-owned staged outputs without deleting runtime state.
7. Build release staging afresh at `dist/release/addon/` from declared source inputs and supplied defaults. Never package from the persistent development directory. Exclude `meta.json`, arbitrary user files, caches, local preferences, and stale outputs. Retain required dependency notices and embedded JavaScript notices.
8. Once all consumers use assembly, remove tracked bundles from the old source asset paths and stop tracking assembled bundle/font-notice copies. Keep generated contract modules and syntax fallback CSS tracked with freshness checks. Update ignore rules, format/lint exclusions, staged-file hooks, CI, `AGENTS.md`, and development/publishing documentation atomically with the workflow change.
9. Test the development-link migration, clean archive installation, and upgrade from the prior layout. Restrict any obsolete-file cleanup to verified Kit-owned files; document installer behavior instead of assuming old files disappear.

Exit criteria: a clean checkout can build, link, verify, and package through documented commands. The extracted release works without repository files, and development rebuilds preserve local state. Existing media names and installed runtime paths remain valid.

## Validation and acceptance

Run checks appropriate to each phase and regenerate affected tracked outputs before committing. Keep commits reviewable and independently usable on a non-main branch. Check the actual repository root and current branch immediately before each commit; stage only that phase's files.

Automated validation:

- Run relevant JavaScript/Python tests per phase, then `npm test` at integration points. Compare discovered test inventory with the baseline when paths or discovery change.
- Run relevant lint/format checks. Before completing the refactor, run `npm run lint`, `npm run check`, `npm run build`, `npm run verify:package-assets`, and `npm run package:addon`.
- Add a generator freshness command to CI. Clean builds must reproduce all tracked generated files without a diff; ignored assembled outputs must independently pass manifest/archive verification.
- Check feature-catalog coverage and dependency direction: no user-facing behavior left in integration/transport, no feature imports from editor support or shared rendering services, and no duplicate fixed shortcut maps or action definitions. Verify that feature-local helpers stay with their owner and that extracted support operations have actual shared consumers.
- Cover Markdown selection versus clipboard conversion, rendering limits/failures, stale results, and shared renderer scheduling after handler extraction. Cover inline-code entry/exit, quote/list nesting, indentation, saved code rows, copy, cloze, style installation, toolbar visibility/order, and native undo/redo.
- Cover pure shared-helper and editor-declaration/aggregate imports without Qt, labels and modifier mapping on both platform paths, feature-contribution completeness, the required `<feature>/shortcuts.py` structure for small and large shortcut-bearing features, and duplicate declarations, fixed reservations, shared/editor validation boundaries, policy recovery, duplicate assignments, activation guards, object reuse, native/browser parity, Settings rebinding, deleted-editor pruning, and preservation of unrelated bindings.
- Verify startup registration once, headless imports in a fresh process, contract validation, shared-code boundaries, lifecycle cleanup, and note-type revalidation with targeted regressions.
- Cover the theme file-to-package transition: public facade/headless imports, Pygments discovery and isolation, Cassidy Dark resolution, saved palette validation/revisions, preview generation, independent light/dark styles, and card/editor CSS selectors. Verify generated CSS freshness and unchanged output for the same theme inputs.
- Exercise the assembly/watch dependency chain for settings, bridge definitions, icons, template parts, Python modules, nested theme package sources, font notice sources, and removed resources. Check failures leave the last successful runnable assets intact.
- Inspect archive contents and resource resolution after extraction outside the repository. Verify required notices and supplied defaults are present, with local metadata and user data excluded.
- Search active source, tests, tooling, CI, and documentation for retired paths and commands. Historical plans/archive references may remain when clearly identified as history.

Live acceptance, reported separately from isolated tests:

- Use a disposable profile on minimum-supported Anki Desktop and a current supported Desktop version. Check startup, profile switching, Settings save/refresh, editor controls and shortcuts, preview/reviewer behavior, managed-media refresh, and native undo.
- Exercise note-type create/skip/replace/delete confirmations and stale-plan rejection with disposable notes. Verify replacement field/note preservation and the stated removal counts.
- Verify macOS Qt/browser modifier handling and another Desktop platform. Cover configurable conflicts and fixed shortcuts without changing established key semantics.
- Sync a disposable collection and check AnkiWeb, AnkiDroid, and AnkiMobile: question/answer transitions, answer persistence, Markdown, highlighting, copy controls, focus, and repeated reviews.
- Verify existing templates and saved markup continue working without automatic replacement. If a necessary markup change emerges, isolate it, document migration, and retain explicit Replace confirmation.
- Verify upgrade and development-link migration preserve saved configuration, collection preferences, user styles, and unrelated media.

Do not claim live verification from Qt stubs or DOM simulations. Record unavailable clients and unfinished acceptance explicitly.

## Completion and rollback

The refactor is complete when feature ownership, shortcut separation, contracts, shared-code boundaries, note-type separation, lifecycle coordination, and package assembly are implemented; canonical definitions have one owner; package/resource paths are verified; documented commands work from a clean checkout; and acceptance results and limitations are recorded. Every editor feature must have an inventory entry and an implementation under `features/` in each runtime where it needs one, including toolbar, native shortcuts, and styles. Every shortcut-bearing Python editor feature has a dedicated `<feature>/shortcuts.py`, including small features. Reusable editor transport/editing/field utilities live under the corresponding `support/` tree, feature-local helpers remain with their feature, and integration/runtime retains lifecycle coordination. Shared Desktop shortcut support remains reusable by Settings, configuration, and reviewer/preview code. The shared theme service uses the `themes/` package with separate Cassidy Dark/Pygments modules and stable public imports, saved theme records, and generated CSS.

Keep compatibility facades only where external interfaces require them; remove temporary internal forwarding modules after consumers migrate. Update `README.md`, `CHANGELOG.md`, `docs/development/architecture.md`, dependency/publishing instructions, and `AGENTS.md` to describe the resulting system. Do not mark implementation phases complete when only this plan exists.

Phases 1–6 retain the current installation layout and can be reverted independently without migrating saved data. Treat Phase 7's source moves, tooling, link migration, and documentation as one coordinated transition. Preserve a recovery copy of development metadata/user files before migration and document how to relink the previous checkout. Never restore developer metadata or overrides into a release package as part of rollback.
