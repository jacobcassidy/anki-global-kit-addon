# Broad repository restructuring plan

## Summary

Organize the repository around runtime responsibilities, shared Desktop services, and shipped assets. Retain `addon/` as the directly installable Anki package and preserve the existing card, editor, and shared browser-source boundaries.

Make Settings a consumer of Desktop functionality rather than the owner of configuration, media installation, note-type operations, and shortcut utilities. Service ownership and Settings separation have the highest priority for the upcoming [syntax highlighting integration](syntax-highlighting-plan.md). Asset consolidation and test relocation need not block that feature.

The structural reorganization is implemented. Automated build, asset-path, packaging, and lint checks pass. The JavaScript suite passes; the Python suite still reports four editor-binding failures that were present before the structural moves. Live Anki and cross-client acceptance have not been performed, so this plan does not claim live verification.

## Target layout

The syntax highlighting and vendor directories include planned additions rather than existing functionality.

```text
addon/
├── __init__.py
├── config.json
├── manifest.json
├── desktop/
│   ├── bootstrap.py
│   ├── paths.py
│   ├── config/                 # Defaults, validation, local persistence
│   ├── media/                  # Asset manifest and installation
│   ├── note_types/             # Definitions and collection operations
│   ├── shortcuts/              # Matching, labels, native event handling
│   ├── editor/                 # Editor hooks and feature coordination
│   ├── syntax_highlighting/    # Rendering, themes, tasks, preferences
│   ├── settings/
│   │   ├── dialog.py
│   │   ├── pages/
│   │   ├── bindings.py
│   │   └── save.py
│   └── ui/                    # Reusable Qt controls and styling
├── assets/
│   ├── cards/                 # Built card JavaScript and CSS
│   ├── editor/                # Built editor JavaScript and CSS
│   ├── icons/
│   └── fonts/
├── templates/
├── vendor/
└── user_files/

src/
├── cards/
│   ├── js/
│   └── css/
├── editor/
│   ├── js/
│   └── css/
└── shared/
    ├── js/
    └── css/

tests/
├── javascript/
│   ├── cards/
│   ├── editor/
│   ├── shared/
│   └── tooling/
├── python/
│   ├── desktop/
│   └── tooling/
├── fixtures/
└── support/

scripts/                       # Build, watch, package, development commands

docs/
├── development/
├── plans/
├── design/
└── reference/
```

## Ownership and implementation changes

1. Promote Desktop services out of Settings:
   - Move configuration, media installation, note-type definitions and operations, and shortcut utilities into their respective Desktop packages.
   - Keep shared filesystem paths in `desktop/paths.py` and startup coordination in `desktop/bootstrap.py`. Preserve the required add-on entry point.
   - Have Settings pages invoke these services. Keep feature-specific collection preferences with their feature, including syntax highlighting's deck-language memory and theme preferences.
   - Keep release defaults in `addon/config.json` and preserve existing setting keys and stored values.
   - Treat `addon/config.json` as authoritative for release defaults. Check Python and browser fallback definitions against it, documenting intentional runtime differences and preserving platform-specific shortcut translation. Record existing behavioral inconsistencies as separate fixes rather than changing them during structural moves.
2. Consolidate shipped assets:
   - Move card assets from `addon/web/assets/` into `addon/assets/cards/`, retaining `js/` and `css/` subdivisions.
   - Move editor assets from `addon/desktop/editor/assets/` into `addon/assets/editor/`, also retaining `js/` and `css/` subdivisions.
   - Move shared icons and fonts into `addon/assets/icons/` and `addon/assets/fonts/`, keeping their associated notices.
   - Update source imports, Desktop asset loading, build/watch outputs, manifest paths, package rules, and validation together. Preserve installed media filenames and template imports.
   - Extend the asset manifest to cover editor assets and shared resources where it removes duplicated path definitions. Keep each resource's packaged location and any public media name explicit.
3. Make Settings explicitly responsible for presentation:
   - Rename `settings/features/` to `settings/pages/`.
   - Put reusable Qt controls, icons, and styling helpers under `desktop/ui/`. Split the existing `widgets.py` by responsibility as its controls move.
   - Keep settings bindings, validation feedback, dialog composition, and Save coordination within Settings.
   - Avoid importing the settings dialog from configuration or rendering modules.
4. Give shortcut handling a coherent home:
   - Consolidate shared matching, validation, and label formatting under `desktop/shortcuts/`.
   - Move native handling currently in `reviewer_shortcuts.py` into that package, reflecting its reviewer, editor, and preview responsibilities.
   - Keep context-specific event handling separate from shared matching and formatting. Preserve Qt's macOS modifier mapping and standard browser-event mapping.
5. Move application tests out of `scripts/`:
   - Group JavaScript tests by cards, editor, shared behavior, and tooling. Group Python tests by Desktop behavior and tooling.
   - Move Anki stubs and other test helpers into `tests/support/`; put common source examples in `tests/fixtures/` so Python and JavaScript highlighting tests can share them.
   - Update test discovery, helper imports, repository-root calculations, and CI so all existing tests continue to run.
   - Use recursive JavaScript test discovery and make Python test subdirectories discoverable packages. Give test helpers explicit package imports rather than depending on the old test directory being on the import path.
6. Preserve browser-source boundaries:
   - Move the shared Markdown renderer into `src/shared/js/markdown/` and update its card, editor, and test consumers.
   - Keep review observation, answer budgets, and review language modules under cards. Keep selection, native undo, and editor block manipulation under editor.
   - Move code into shared modules only when runtimes actually share it. Avoid a general-purpose `utils/` directory.
7. Normalize documentation:
   - Use `docs/plans/` consistently and move publishing and dependency instructions into `docs/development/`.
   - Retain `highlighting-restruture-plan.md` at its existing path as a short superseded notice linking to this plan and the syntax highlighting integration plan. Do not maintain a third implementation specification.
   - Update documentation links, source-tree descriptions, and `AGENTS.md` as each move lands. In particular, explicitly replace the existing guidance that locates note-type operations under Settings when relocating that service.
   - Before implementing affected stages, reconcile the syntax highlighting integration plan with this document. This broad plan is authoritative for directory ownership, including `settings/bindings.py` and `settings/save.py`; the integration plan remains authoritative for feature behavior and its theme exporter/output names. The superseded narrower plan provides no competing ownership or path requirements.
8. Define vendored and generated-file tooling policy:
   - Exclude `addon/vendor/` from first-party formatting, linting, and automatic pre-commit rewrites. Preserve pinned upstream dependency files and their notices; continue checking dependency presence and package inclusion.
   - Validate generated files through their generators and freshness checks. Keep each output's generator and inputs explicit rather than editing or independently formatting generated content.
   - Enforce exclusions when tools receive explicit filenames, including Lefthook's staged-file arguments, as well as during repository-wide runs. Configure Ruff's `force-exclude` with the relevant exclusions or filter excluded paths before invocation; apply equivalent protection to other formatting and lint commands.

## Dependency and compatibility contracts

- Desktop services must not import Settings pages or the settings dialog. Reusable UI must not import feature pages; pages and feature coordinators consume services and shared UI.
- Keep pure rendering, paths, and configuration definitions importable without Qt. Keep Anki-dependent persistence and UI adapters separate from those definitions.
- Define and document the supported headless loading path for build tooling and pure-module tests. A normal import through `addon` executes its startup entry point, so moving a module away from Qt imports alone is insufficient. Headless consumers must load the canonical pure modules without executing add-on startup or importing Anki/Qt adapters; preserve normal Anki startup and avoid copied definitions or per-consumer import workarounds.
- Distinguish packaged filesystem paths, build output paths, and public `collection.media` filenames. Resolve packaged resources independently of the working directory and verify lookup through both the development symlink and an installed archive.
- Keep package `__init__.py` files lightweight, except for the required add-on entry point's startup call. Put explicit startup coordination in `desktop/bootstrap.py`, preserving initialization order and assigning each hook and event filter one registration owner.
- Preserve JavaScript globals, Python–JavaScript bridge commands, saved HTML classes and data attributes, and the add-on package/configuration identity as well as public media filenames and settings keys. Internal module moves must not require rewriting existing notes or templates.
- Preserve hook and event-filter registration counts through startup changes. Verify initialization does not introduce duplicate callbacks, controls, or shortcut handlers.

## Delivery and validation

- Deliver separate stages for tests/documentation, Desktop services, Settings/shortcuts, and asset paths. Use reviewable commits on a non-main branch. Each commit must preserve behavior and independently build, test, and package successfully. Different subsystems may migrate in separate commits, but each must use one authoritative implementation and resource location, without duplicate implementations or fallback lookups across old and new layouts.
- Record a before/after inventory of discovered JavaScript and Python tests, accounting for renamed tests explicitly. Run the existing suites after relevant moves and verify nested tests and shared helpers are discovered.
- Add startup/import smoke coverage that exercises package initialization and bootstrap with suitable Anki stubs, rather than loading only individual modules by file path. Verify pure modules import without Qt and startup registers the expected hooks and event filters once.
- Separately exercise the documented headless loading path in a fresh process without Anki or Qt installed. Use the actual build-tool entry point and imports, not only isolated leaf-module loaders; verify it neither imports Anki/Qt adapters nor registers hooks. Once introduced, theme export must pass through this same supported path.
- Verify exclusion behavior with representative vendored and generated files passed explicitly to formatter/linter commands and through staged-file hooks. Confirm their bytes remain unchanged, while ordinary first-party files are still checked and generated-file freshness failures are still detected.
- Run relevant lint and formatting checks, the add-on build, asset checks, and package validation. Verify that the archive contains all required resources and notices, and excludes local metadata and user data.
- Update the hardcoded generated-file paths in `.github/workflows/tests.yml` alongside asset moves. From a clean checkout, build and regenerate all tracked outputs and require no resulting diff, including font notices and theme fallbacks once introduced. Ensure freshness checks actually cover the new output locations.
- Verify watch mode separately from builds: changes to card, editor, and shared JavaScript/CSS and imported icons must rebuild the correct outputs. Include generated theme inputs once introduced, and confirm the watcher follows their generation dependencies.
- Verify the development symlink still points to a directly usable `addon/` package. Check profile asset installation, editor asset injection, and template resource resolution after path changes.
- Test both a clean installation from an extracted release archive and an upgrade from the previous package layout. Inspect how the supported installer handles obsolete files and document the result; verify old package paths cannot affect imports or resource loading. If cleanup is required, restrict it to explicitly identified obsolete Kit-owned files rather than deleting directories broadly.
- Verify upgrades preserve `meta.json`, saved configuration, collection preferences, and user styles. Include saved markup, existing templates, browser globals, and bridge commands in compatibility checks.
- Preserve note-type confirmation requirements, managed-media scope, native undo behavior, and cross-client functionality. Do not mix structural moves with feature changes.
- After each stage, search the repository for retired paths and module names. Update references in active code, tests, tooling, CI, and documentation. Allow historical references in archives, migration notes, and this plan's before/after descriptions, documenting any remaining references so obsolete active lookups cannot be mistaken for intentional history.
- Report automated checks separately from live Anki and cross-client verification. Live acceptance should cover startup, Settings, editor controls, reviewer shortcuts, and managed-media refresh.

## Assumptions and defaults

- Keep Python source inside the installable add-on rather than introducing a separate Python staging build.
- Keep generated bundles tracked initially, preserving the existing development and packaging workflow while ownership changes settle.
- Retain `addon/templates/`, `addon/user_files/`, and root development commands. Do not relocate or overwrite local user customizations.
- Treat this as the broad target layout and resolve narrower plans' directory conflicts before implementing affected stages. Do not create unused directories solely to match the diagram.
