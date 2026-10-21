# Broad repository restructuring plan

## Summary

Organize the repository around runtime responsibilities, shared Desktop services, and shipped assets. Retain `addon/` as the directly installable Anki package and preserve the existing card, editor, and shared browser-source boundaries.

Make Settings a consumer of Desktop functionality rather than the owner of configuration, media installation, note-type operations, and shortcut utilities. Service ownership and Settings separation have the highest priority for the upcoming [syntax highlighting integration](syntax-highlighting-plan.md). Asset consolidation and test relocation need not block that feature.

This document records proposed work. The reorganization has not been implemented or verified in live Anki.

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
2. Consolidate shipped assets:
   - Move card assets from `addon/web/assets/` into `addon/assets/cards/`, retaining `js/` and `css/` subdivisions.
   - Move editor assets from `addon/desktop/editor/assets/` into `addon/assets/editor/`, also retaining `js/` and `css/` subdivisions.
   - Move shared icons and fonts into `addon/assets/icons/` and `addon/assets/fonts/`, keeping their associated notices.
   - Update source imports, Desktop asset loading, build/watch outputs, manifest paths, package rules, and validation together. Preserve installed media filenames and template imports.
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
6. Preserve browser-source boundaries:
   - Move the shared Markdown renderer into `src/shared/js/markdown/` and update its card, editor, and test consumers.
   - Keep review observation, answer budgets, and review language modules under cards. Keep selection, native undo, and editor block manipulation under editor.
   - Move code into shared modules only when runtimes actually share it. Avoid a general-purpose `utils/` directory.
7. Normalize documentation:
   - Use `docs/plans/` consistently and move publishing and dependency instructions into `docs/development/`.
   - Normalize the highlighting restructuring document's name to `highlighting-restructure-plan.md` under `docs/plans/`.
   - Update documentation links, source-tree descriptions, and `AGENTS.md` as each move lands. In particular, explicitly replace the existing guidance that locates note-type operations under Settings when relocating that service.

## Delivery and validation

- Deliver separate stages for tests/documentation, Desktop services, Settings/shortcuts, and asset paths. Use reviewable commits on a non-main branch and preserve behavior at each stage.
- Run the existing JavaScript and Python suites after relevant moves, ensuring test discovery has not silently omitted nested tests.
- Run relevant lint and formatting checks, the add-on build, asset checks, and package validation. Verify that the archive contains all required resources and notices, and excludes local metadata and user data.
- Verify the development symlink still points to a directly usable `addon/` package. Check profile asset installation, editor asset injection, and template resource resolution after path changes.
- Preserve note-type confirmation requirements, managed-media scope, native undo behavior, and cross-client functionality. Do not mix structural moves with feature changes.
- Report automated checks separately from live Anki and cross-client verification. Live acceptance should cover startup, Settings, editor controls, reviewer shortcuts, and managed-media refresh.

## Assumptions and defaults

- Keep Python source inside the installable add-on rather than introducing a separate Python staging build.
- Keep generated bundles tracked initially, preserving the existing development and packaging workflow while ownership changes settle.
- Retain `addon/templates/`, `addon/user_files/`, and root development commands. Do not relocate or overwrite local user customizations.
- Treat this as the broad target layout. Reconcile narrower highlighting plans with it as the relevant stages are implemented; do not create unused directories solely to match the diagram.
