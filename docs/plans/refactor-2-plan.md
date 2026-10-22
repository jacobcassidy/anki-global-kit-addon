# Second architecture refactor plan

## Status and purpose

Planned; implementation has not started. Refactor the existing project incrementally while preserving its behavior, saved data, public interfaces, and supported clients.

Keep the runtime-first organization: Python Desktop integration in `addon/`, review JavaScript/CSS in `src/cards/`, editor JavaScript/CSS in `src/editor/`, and genuinely reusable web behavior in `src/shared/`. Improve the boundaries between these areas before changing the packaging layout.

This plan follows the completed [broad repository restructuring plan](archive/broad-restructure-plan.md). For this second refactor, it proposes replacing that plan's directly installable source `addon/` with an assembled development package and moving editable static assets into `resources/`. The existing layout and `AGENTS.md` remain authoritative until the corresponding implementation phase updates them together. Preserve feature behavior documented in the [syntax highlighting plan](archive/syntax-highlighting-plan.md).

## Goals and constraints

- Remove Desktop bridge dependencies from shared web controls.
- Centralize settings, asset, and bridge contracts without duplicating release defaults.
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
│   │   ├── formatting.py
│   │   ├── labels.py
│   │   └── reviewer.py
│   ├── editor/
│   │   ├── integration.py             # Hook/shortcut coordination and editor ownership
│   │   ├── bridge.py                  # Serialize bootstrap data and invoke browser actions
│   │   ├── buttons.py
│   │   └── features/
│   │       ├── field_descriptions.py
│   │       └── syntax_highlighting.py
│   ├── syntax_highlighting/
│   │   ├── language_memory.py
│   │   ├── preferences.py
│   │   ├── rendering.py
│   │   ├── themes.py
│   │   └── custom_themes/cassidy_dark.py
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

## Dependency rules

- `src/shared/` may use browser APIs but must not invoke `pycmd`, access `ankiGlobalKitEditor`, or import card/editor application modules. Shared controls receive callbacks or capabilities from their owning runtime.
- Shared code owns common DOM presentation and interactions. Editor selection, native undo integration, and Desktop commands remain editor responsibilities; review observation and answer persistence remain card responsibilities.
- Desktop services must not import Settings pages or the dialog. Settings collects user intent, presents confirmations, and calls services.
- Note-type template assembly and definitions must load without Anki/Qt. Planning receives a collection explicitly; application/revalidation uses documented collection APIs. Resolve `mw.col` at UI or hook boundaries.
- Keep `scripts/addon_module_loader.py` as the supported startup-free import path. Pure-module imports must neither execute `addon/__init__.py` nor register hooks.
- Keep package initializers lightweight and startup registration owned by `desktop/bootstrap.py` and its explicit feature coordinators.
- Add focused import/dependency checks for these boundaries instead of introducing a general dependency-injection framework.

## Delivery phases

### Phase 0: Establish the compatibility baseline

1. Inventory current settings, generated outputs, public media names, bridge commands/globals, template markup, test discovery, package entries, and runtime initialization owners. Include the latest completed card-loader work when implementation begins.
2. Record current automated results and known limitations. Keep unrelated working-tree changes outside refactor commits.
3. Add only missing regression coverage needed for the boundary changes: reinjection, settings refresh, note-type plan revalidation, unmanaged-media preservation, and package isolation. Reuse existing tests where they already cover these behaviors.
4. Document the source/runtime/resource distinction and the order below. Do not move resources yet.

Exit criteria: a recorded compatibility inventory and an understood test baseline; failures are resolved or explicitly identified before attributing later regressions to the refactor.

### Phase 1: Centralize settings, asset, and bridge contracts

1. Add the three canonical contract files, generator, generated modules, and freshness checks. Keep current output/resource locations during this phase.
2. Replace handwritten card/editor fallback defaults with generated values and thin runtime normalization. Preserve current enabled states, shortcut behavior, and handling of malformed saved configuration.
3. Have `desktop/media/manifest.py`, build tooling, and verification consume the same asset identities. Replace verification that parses build-script strings with checks of structured definitions and actual outputs.
4. Move Python/JavaScript bridge literals into generated definitions, preserving the existing external interface. Extract editor serialization/invocation into `desktop/editor/bridge.py`; keep registration and feature coordination in `integration.py`.
5. Add generation to build/watch/package dependencies and CI. A schema/default change must regenerate affected consumers before bundling.

Exit criteria: no duplicated fallback values or public asset/bridge definitions in active consumers; intentional runtime translations are documented and tested; generation is repeatable and `--check` detects stale outputs.

### Phase 2: Decouple shared code-block controls

1. Refactor `src/shared/js/syntax-highlighting/code-block-controls.js` into common decoration/interaction behavior accepting explicit optional callbacks for language menus and options.
2. Supply Desktop behavior through an editor adapter under `src/editor/js/`. Supply card capabilities under `src/cards/js/` without relying on Desktop globals. Preserve existing copy behavior and focus/selection outcomes.
3. Keep editor-specific manipulation and native undo integration outside shared controls. Keep card scope restrictions so ordinary cards remain untouched.
4. Add a focused dependency check preventing shared imports of application modules and direct Desktop bridge calls.

Exit criteria: shared code runs with no Desktop bridge present, existing card/editor bundle regressions pass, and editor actions still reach the same Python handlers.

### Phase 3: Split note-type responsibilities

1. Extract definitions, dataclasses/errors, template assembly, and planning from `desktop/note_types/service.py` into the target modules. Keep application and immediate pre-write validation in the service.
2. Pass the collection explicitly from Settings/action coordinators. Preserve collection identity checks in confirmed plans and current partial-result/error reporting.
3. Preserve the complete plan/confirm/revalidate/apply sequence. Revalidate replacement targets and removal impact before writing; retain template names and template/card counts in confirmation. Allow deletion only under the existing empty-type/uncreated-topic rules.
4. Update Settings imports and existing tests together. Update `scripts/verify_package_assets.py` to load canonical pure definitions through the headless loader rather than extracting `TOPICS` and `FORMATS` from service source with AST parsing.
5. Keep template parts in their current location until Phase 5. Do not change required markup or existing note types during extraction.

Exit criteria: template assembly loads without Anki/Qt, collection dependencies are explicit, and all create/skip/replace/delete and confirmation-change regressions pass without altered outcomes.

### Phase 4: Establish browser runtime lifecycle ownership

1. Introduce small coordinators under `src/cards/js/runtime/` and `src/editor/js/runtime/` with explicit mount, settings-update, and disposal responsibilities. Keep entry points as thin bootstrap calls.
2. Have feature installers return cleanup functions or register resources with their runtime. Separate document-lifetime handlers from card/note-lifetime work so card changes do not reinstall everything.
3. Preserve a stable global runtime handle across bundle reinjection. Dispose an old instance before replacement, clean observers/listeners/timers, and ensure stale asynchronous callbacks cannot update a replaced card or editor context. Keep existing public globals as compatibility facades.
4. Make updated settings reach existing features without accumulating handlers or capturing stale settings. Distinguish settings refresh from full runtime replacement.
5. Preserve answer storage, client detection, AnkiWeb integration, editor selection/native undo, and existing card-loader failure/retry behavior. Use supported client hooks where verified; retain observation where required.

Exit criteria: repeated bundle evaluation, card transitions, editor note loads, settings updates, and disposal produce one active owner for each resource. Existing answer persistence and keyboard behavior remain unchanged across simulated clients.

### Phase 5: Move resources and assemble installable packages

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
- Verify startup registration once, headless imports in a fresh process, contract validation, shared-code boundaries, lifecycle cleanup, and note-type revalidation with targeted regressions.
- Exercise the assembly/watch dependency chain for settings, bridge definitions, icons, template parts, Python modules, theme sources, font notice sources, and removed resources. Check failures leave the last successful runnable assets intact.
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

The refactor is complete when all five architectural changes are implemented, canonical definitions have one owner, package/resource paths are verified, documented commands work from a clean checkout, and acceptance results and limitations are recorded.

Keep compatibility facades only where external interfaces require them; remove temporary internal forwarding modules after consumers migrate. Update `README.md`, `CHANGELOG.md`, `docs/development/architecture.md`, dependency/publishing instructions, and `AGENTS.md` to describe the resulting system. Do not mark implementation phases complete when only this plan exists.

Phases 1–4 retain the current installation layout and can be reverted independently without migrating saved data. Treat Phase 5's source moves, tooling, link migration, and documentation as one coordinated transition. Preserve a recovery copy of development metadata/user files before migration and document how to relink the previous checkout. Never restore developer metadata or overrides into a release package as part of rollback.
