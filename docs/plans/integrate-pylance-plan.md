# Integrate Pylance type checking into validation

## Status and purpose

Implemented on 2026-10-24. The pinned Pyright CLI checks all agreed first-party Python directories with the locked Anki 26.05/Qt environment. The initial diagnostics are resolved, and type checking runs alongside Ruff in `npm run check`, the commit hook, and CI. VS Code interpreter selection and live Pylance/Anki behavior still need to be verified in the actual application; CLI and isolated tests do not establish those results.

Use the official Pyright CLI, which supplies the type checker used by Pylance. Keep Pylance as the editor language server and Ruff as the formatter/linter. Type checking reports problems that generally require code changes; it does not provide a general automatic fix equivalent to `ruff check --fix`.

Pylance has additional editor capabilities and can bundle a different checker version, so identical diagnostics are not guaranteed. Align configuration, import resolution, and interpreter selection, and investigate remaining differences rather than promising exact parity.

## Starting repository state (before integration)

- `pyproject.toml` declares Python `>=3.11`, development dependencies containing only Ruff, and Ruff's Python 3.11 target. There is no shared Pyright configuration.
- `package.json` has Python lint/format commands but no type-checking command. `npm run check` currently runs Prettier and Ruff formatting checks.
- `.vscode/settings.json` configures Ruff formatting and fixes on save without selecting a project Python environment or shared type-checking policy.
- `lefthook.yml` runs Ruff lint fixes and formatting for staged Python files, but no type checker.
- `.github/workflows/tests.yml` uses Python 3.13, installs uv, and runs linting, formatting, builds, asset verification, and isolated tests without type checking.
- Runtime code imports Anki, Qt, and bundled libraries. Tests use dynamic module loading and Anki/Qt stand-ins. Neither missing development dependencies nor test stand-ins should be mistaken for the real supported API types.

Recheck these paths at implementation time. The [third architecture refactor plan](refactor-3-plan.md) may move Python modules, assets, and tooling; configure the layout that actually exists rather than requiring that refactor first.

## Implementation

### 1. Establish a reproducible development environment

1. Add an exact Pyright version to npm development dependencies and update `package-lock.json`. Use the repository-local executable through npm scripts rather than a globally installed checker or an unpinned download.
2. Add development-only Anki and Qt packages to the uv environment and update `uv.lock`. Verify available package versions, Python requirements, and typing information against minimum-supported Anki Desktop **26.05** before choosing pins. Do not assume the Desktop version string is identical to its package version syntax.
3. Resolve the declared Python 3.11 floor versus CI's Python 3.13 environment explicitly. Select a checker language target and development interpreter supported by the relevant Anki packages. Preserve the existing supported runtime contract unless a separately justified change is documented.
4. Ensure `uv sync --locked` creates the environment used by both local validation and CI. Keep these dependencies out of the release archive; do not vendor Anki, Qt, or Pyright into the add-on.

Exit criteria: a clean checkout can install locked dependencies and resolve `anki`, `aqt`, and the Qt imports used by the add-on without relying on an installed GUI application or a developer's machine-specific paths.

### 2. Share configuration between Pyright and Pylance

Add `[tool.pyright]` to `pyproject.toml` as the authoritative type-checking configuration:

- Start with `typeCheckingMode = "basic"`. Tighten checks separately after establishing a clean baseline.
- Define explicit coverage for first-party Python in `addon/`, `scripts/`, `tests/python/`, and Python helpers under `tests/support/`. Inventory any additional Python tooling before finalizing the include list.
- Exclude vendored dependencies, virtual environments, generated distribution directories, and caches from first-party checking. Exclusion does not prevent imported files from being consulted; verify actual analyzer output.
- Set the agreed Python language target and configure portable environment/import resolution. Use execution environments or additional paths only where the actual import layout requires them, including bundled-library imports in tests.
- Use real dependency types first. Add small, documented local stubs only for genuine gaps in external typing; do not replace the Anki API with permissive test mocks for analysis.
- Keep missing-import diagnostics enabled. Do not globally disable type errors to make the check pass.

Update `.vscode/settings.json` so developers select the project `.venv` interpreter, and enable workspace diagnostics if needed to expose errors outside open files. Avoid duplicating type-checking settings that belong in `pyproject.toml`. Pylance uses VS Code's selected interpreter, so CLI environment settings alone do not configure the editor.

Add `.vscode/extensions.json` recommendations for Python, Pylance, and Ruff if appropriate. Preserve existing formatting and fix-on-save settings.

Exit criteria: CLI and editor analyze the same project scope with matching intended rules and dependency versions. Verify the actual selected interpreter and Pylance output; configuring a default interpreter may not replace an existing workspace selection.

### 3. Fix the initial diagnostics

Run Pyright before enabling a blocking hook or CI gate. Classify findings as environment/configuration errors, genuine code/type errors, external typing gaps, or dynamic-test modeling problems.

- Fix import resolution first so missing dependencies do not obscure real diagnostics.
- Correct optional-value handling, collection/container annotations, callback signatures, Qt overrides, and attribute access where diagnostics identify real mismatches.
- Model dynamic test helpers with useful return types, protocols, or explicit stand-ins where practical. Keep isolated tests independent of a live Anki process.
- Use narrow casts only when a runtime invariant is established. Any unavoidable suppression must name the diagnostic and explain the external limitation.
- Avoid broad `Any` replacements, blanket file ignores, weakened checking rules, or excluding difficult first-party files merely to obtain a green result.
- Preserve behavior, saved settings, platform-specific modifiers, hooks, and public interfaces. Test behavior changes that prove necessary to fix a real defect, and document them separately from annotation-only changes.

If coverage must be introduced in phases, list every temporary exclusion and its removal work explicitly. Do not mark integration complete while agreed first-party coverage remains deferred.

### 4. Integrate the checks into normal work

1. Add `npm run typecheck:py` to run the pinned local Pyright against the shared project configuration and uv environment. Ensure interpreter discovery works from a clean checkout on supported developer platforms and CI.
2. Add the command to `npm run check` after the existing formatting checks, retaining the separate Ruff lint and formatting commands.
3. Add a Lefthook type-check step after Ruff fixes/formatting whenever Python or type-checker configuration changes are staged. Run project-wide checking rather than passing only `{staged_files}`: changes can break callers in other files, and explicit CLI file arguments override the configured include scope. Include dependency/configuration changes among the hook triggers.
4. Update `.github/workflows/tests.yml` to install locked Python development dependencies explicitly and run the same type-checking command, directly or through `npm run check`. Avoid duplicate CI runs of the same check. Ensure a type-check failure blocks the dependent release job.
5. Update `AGENTS.md` to require running and fixing type-checking diagnostics alongside Ruff for Python changes before committing. Document `npm run typecheck:py`, shared configuration, environment setup, and the distinction between type checking, isolated tests, and live Anki verification in the README/development instructions.

Keep commits scoped and independently usable on a non-main branch. Stage only files belonging to this work; preserve unrelated user changes.

## Validation and acceptance

- Install from the updated npm and uv lockfiles in a clean environment, then run `npm run typecheck:py` with zero errors across the agreed first-party scope.
- Verify Pylance resolves representative Anki/Qt imports and uses the intended interpreter and shared settings. Record checker-version or Pylance-only diagnostic differences explicitly.
- Temporarily introduce a representative type mismatch and confirm the CLI, commit hook, and CI command fail; remove it before committing. Verify the hook checks affected callers outside the staged file and also runs after relevant configuration/dependency changes.
- Run `npm run lint`, `npm run check`, and `npm test`. Regenerate and verify assets if fixing runtime source or theme generation affects tracked outputs.
- Verify the add-on package excludes development dependencies, checker files intended only for tooling, virtual environments, and local editor state. Shared repository configuration need not be shipped with the add-on.
- Report editor verification, CLI results, isolated tests, and live Anki checks separately. Type checking does not establish live Qt or cross-client behavior.

Completion means the environment is reproducible, the initial diagnostics are fixed, the CLI/editor configuration is aligned, local hooks and CI enforce the check, and agent/developer instructions require it. A configuration-only change with unresolved or hidden diagnostics is not complete.

## References

- [Pyright installation and its relationship to Pylance](https://github.com/microsoft/pyright/blob/main/docs/installation.md)
- [Pyright configuration, environment resolution, and diagnostic settings](https://github.com/microsoft/pyright/blob/main/docs/configuration.md)
- [Pyright command-line options](https://github.com/microsoft/pyright/blob/main/docs/command-line.md)
- [Anki add-on documentation](https://addon-docs.ankiweb.net/)
