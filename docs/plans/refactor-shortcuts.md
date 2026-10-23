# Desktop shortcuts refactor plan

## Status and purpose

Planned; implementation has not started. Separate reusable shortcut helpers, shortcut definitions, validation rules, and runtime registration while preserving existing behavior.

This plan refines the shortcuts and editor boundaries in the [second architecture refactor plan](refactor-2-plan.md). Its shortcuts layout replaces that plan's retained `shortcuts/formatting.py`, and native editor shortcut registration moves from `editor/integration.py` into `shortcuts/editor.py`. Coordinate the architecture documentation when implementing these changes.

## Goals and constraints

- Make common helpers importable across Settings, editor, and reviewer code without importing their runtime state.
- Give each shortcut definition and runtime registry one owner.
- Preserve existing shortcuts, settings keys, defaults, warning messages, action priority, browser globals, and bridge commands.
- Preserve fixed shortcut reservations and browser/native parity through the existing injection of the Python shortcut map.
- Preserve Anki Desktop 26.05 support and the supported hook/API behavior. Verify version-sensitive changes against the minimum target and official documentation during implementation.
- Keep this refactor separate from new features, shortcut changes, and unrelated behavior fixes.

## Target layout

```text
addon/desktop/
├── shortcuts/
│   ├── __init__.py       # Package marker; no startup side effects
│   ├── helpers.py        # Pure shortcut string operations
│   ├── definitions.py    # Shortcut maps, aliases, and action names
│   ├── validation.py     # Reservations and conflict warnings
│   ├── labels.py         # Display labels and modifier hints
│   ├── qt_helpers.py     # Shared Qt key/modifier matching
│   ├── editor.py         # Native editor registration and rebinding
│   └── reviewer.py       # Reviewer routing, focus ownership, and hooks
└── editor/
    ├── actions.py        # Actions shared by toolbar and shortcut callers
    ├── integration.py    # Editor lifecycle, asset injection, toolbar coordination
    ├── buttons.py
    └── features/
```

Keep existing files under `editor/features/`. Remove `shortcuts/formatting.py` after migrating its internal consumers; retain a forwarding module only if an identified external interface requires it.

## Module responsibilities

### Reusable helpers

Move `split_shortcut()`, `normalize_shortcut()`, and `shortcut_has_required_modifier()` from `formatting.py` to `helpers.py`.

- Accept explicit inputs and return values without changing application state.
- Pass platform information explicitly where needed, for example `normalize_shortcut(value, *, is_mac=False)`; callers supply the actual platform.
- Keep these helpers free of Anki, Qt, Settings, editor, reviewer, and hook imports.
- Preserve literal plus keys, aliases, modifier ordering, shifted punctuation equivalence, and the existing `CodeBlock+` convention.
- Keep helpers specific to shortcut processing. Shared access means explicit imports, with mutable runtime state retained by its owning module.

### Definitions

Move `EDITOR_BLOCK_SHORTCUTS`, key aliases, fixed action labels, built-in shortcut tables, and reserved text-editing shortcut tables into `definitions.py`.

Store raw definitions once and normalize them through the shared helpers when evaluating conflicts. Preserve the existing map shape consumed by native registration and browser injection. Keep configurable release defaults in `addon/config.json`; do not introduce another defaults table here.

### Validation

Move `editor_fixed_shortcut_action()`, `anki_shortcut_warnings()`, `anki_editor_format_shortcut_warnings()`, `anki_editor_shortcut_warning()`, and `reserved_shortcut_warnings()` into `validation.py`.

Use definitions and helpers to evaluate reservations and warnings. Keep the exception for an indentation setting using its intended native indentation binding. Return results to callers; Settings remains responsible for presenting messages and accepting or rejecting saved assignments.

### Labels

Move `format_shortcut()` and `SHORTCUT_MODIFIER_HINT` into `labels.py`, alongside `shortcut_label()`.

Keep parsing and normalization in `helpers.py`. Keep the Anki `shortcut()` adapter within `labels.py`; preserve the existing differences between Settings formatting and tooltip labels until their equivalence is established. Labels must remain consistent with the current platform semantics.

### Qt helpers and reviewer behavior

Extract common modifier resolution and event matching from `_indentation_tab_action()` and `_card_indent_shortcut_override()` into `qt_helpers.py`.

- Accept an event or explicit key/modifier values, shortcut text, and platform information.
- Return a match result without executing JavaScript, reading Settings, registering hooks, accepting events, or changing focus.
- Preserve exact modifier matching, disabled bindings, Tab/Backtab handling, and shifted punctuation aliases.
- On macOS, preserve Anki's Qt mapping: `Ctrl` means physical Command and `Meta` means physical Control. Browser keyboard events retain their standard `metaKey`/`ctrlKey` mapping.

Keep selection of the target webview, JavaScript action selection, Preferences ownership, weak webview registries, event acceptance, and hook registration in `reviewer.py`. Keep `_live_webviews()` and `_webview_contains_focus()` local unless another runtime consumer actually needs them.

### Native editor registration

Move these responsibilities from `editor/integration.py` into `shortcuts/editor.py`:

- `_add_shortcut()` and filtering/replacement of native list bindings.
- `_configured_editor_shortcuts()` and the existing configurable-action priority.
- `_activate_editor_shortcut()` and its field, widget, configuration, and enabled-state guards.
- `_refresh_editor_shortcuts()` and creation, reuse, rebinding, and disabling of Kit-owned `QShortcut` objects.
- The weak registry of registered editors and pruning of deleted Qt widgets/webviews.

Expose a small API such as `register(shortcuts, editor)`, `refresh_bindings(editor, settings)`, and `iter_live_editors()`. Keep shortcut instances owned by their editor widget and preserve weak references in activation callbacks.

Move browser action wrappers shared by toolbar buttons and shortcuts into `editor/actions.py`: inline code, block formatting, Markdown conversion, indentation, exiting code blocks, and the syntax-highlighting action adapter. Preserve clipboard timing and existing feature calls. Both `editor/integration.py` and `shortcuts/editor.py` use these actions, avoiding an import cycle between integration and registration.

Keep `editor/integration.py` responsible for toolbar construction, asset/settings injection, editor lifecycle coordination, and presentation refresh. Its `initialize()` connects `editor_did_init_shortcuts` to `shortcuts.editor.register` through the existing startup path. Registration must still occur once.

Keep `refresh_open_editors()` as the Settings-facing coordinator: obtain settings, iterate live registered editors, refresh their native bindings through `shortcuts/editor.py`, and inject updated browser assets/settings through the existing editor integration. Native registration must not import or call `editor/integration.py` to refresh presentation.

## Dependency rules

- `helpers.py` and `definitions.py` have no Anki/Qt dependencies.
- `validation.py` depends on helpers and definitions; it has no UI or runtime side effects.
- `labels.py` may use Anki's label adapter and shared string helpers.
- `qt_helpers.py` may import Qt, but has no editor/reviewer/Settings ownership.
- Runtime modules consume helpers, definitions, validation, and action adapters. Low-level modules never import runtime modules.
- `editor/actions.py` must not import `editor/integration.py` or native registration.
- Python remains authoritative for fixed editor shortcuts. Browser handlers continue consuming the injected map without a duplicate fallback map.
- Keep module imports explicit; avoid wildcard exports and package-level startup behavior.

## Implementation sequence

1. Record existing shortcut behavior and test inventory, including platform-specific labels, validation, native registration, and Settings refresh.
2. Extract definitions, pure helpers, validation, and labels. Update Settings, shortcut input controls, editor callers, syntax-highlighting tooltips, and test support imports together.
3. Extract Qt matching helpers and migrate the reviewer paths while retaining their context checks and action routing.
4. Add `editor/actions.py`, move native registration and registry ownership into `shortcuts/editor.py`, and reconnect initialization and Settings refresh without import cycles or duplicate hooks.
5. Update browser shortcut fixtures to read the relocated authoritative Python map. Remove obsolete internal imports and `formatting.py` after all consumers migrate.
6. Update `AGENTS.md`, `docs/development/architecture.md`, and the second architecture refactor plan to match the resulting layout. Document the completed refactor in `CHANGELOG.md` as appropriate.

Keep each phase independently usable and commit it after validation on a non-main branch. Stage only files belonging to that phase.

## Validation and acceptance

During implementation, add or retain coverage for:

- Pure helper imports in a fresh process without Anki/Qt stubs.
- Literal plus keys, key aliases, modifier ordering, shifted punctuation, and platform-specific `CodeBlock+` behavior.
- macOS/non-macOS labels and Qt/browser modifier semantics.
- Fixed shortcut reservations, built-in warnings, intended indentation exceptions, duplicate assignments, disabled settings, and invalid saved conflicts.
- Fixed-map parity among Settings reservations, native registration, browser injection, and browser handling.
- Registration once, reuse of existing shortcut objects, settings rebinding/disabling, and preservation of other add-ons' bindings.
- Activation after settings changes, no selected field, deleted editors/widgets, weak-reference cleanup, and Settings refresh of open editor webviews.
- Reviewer/preview focus routing, toolbar navigation ownership, Preferences restoration, and Tab indentation handling.
- Toolbar and keyboard actions invoking the same action adapters.

Run relevant Python and JavaScript tests per phase, then `npm test`, `npm run lint`, `npm run check`, `npm run build`, and `npm run verify:package-assets` before completion. Regenerate affected tracked bundles with source changes. Search active source, test support, and tooling for retired imports.

Perform live acceptance on the minimum supported Anki Desktop version and a current supported version, covering macOS and another Desktop platform where available. Check toolbar actions, keyboard actions, native undo, Settings save/rebinding, editor closure, reviewer/preview focus, and Preferences behavior. Report live checks separately from isolated Qt/DOM tests and record unavailable environments explicitly.

## Completion criteria

Helpers are independently reusable, shortcut definitions have one owner, native editor registration lives in `shortcuts/editor.py`, and `editor/integration.py` coordinates editor presentation and lifecycle. Existing behavior and public interfaces remain intact, automated checks pass, and validation limitations are documented. Creating this plan does not mark implementation complete.
