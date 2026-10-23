# Convert JavaScript source and tooling to TypeScript

## Status and purpose

Proposed on 2026-10-24. This document plans the migration; implementation has not started.

Convert maintained card, editor, and shared JavaScript modules, their tests, and JavaScript build scripts to TypeScript. Preserve existing runtime behavior, Python integration, supported Anki clients, and installed asset filenames. TypeScript is a development dependency: Anki continues to load ordinary JavaScript bundles and requires no TypeScript runtime.

Recheck the working tree before implementation. The [third architecture refactor plan](refactor-3-plan.md) proposes separate structural changes and contract generation. This migration does not require those changes first. Adapt paths if that work lands first, and carry its documentation conventions forward to TypeScript if implemented. Avoid combining a language conversion with feature redesign or package assembly changes.

## Current repository inventory

The inspected working tree contains:

| Area                | Current implementation                                                      | Migration considerations                                                                       |
| ------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Card runtime        | 22 modules in `src/cards/js/`                                               | Client detection, answer storage, persistent observers, keyboard behavior, DOM access          |
| Editor runtime      | 17 modules in `src/editor/js/`                                              | Python bridge, partial API installation, selection, native undo, shadow DOM, reinjection       |
| Shared browser code | 13 modules in `src/shared/js/`                                              | Markdown, shortcut policy, highlighting, Lezer trees, SVG imports                              |
| Node tooling        | Six JavaScript files in `scripts/`                                          | Build configuration, build/watch, logging, development metadata, add-on linking                |
| Tests and support   | 26 tests in `tests/javascript/`, two JavaScript helpers in `tests/support/` | Direct source imports, JSDOM, SVG loading, compiled-bundle evaluation, Python shortcut fixture |
| Tool configuration  | `eslint.config.js`, `prettier.config.js`                                    | Native tool loading, lint scopes, import resolution, formatting overrides                      |
| Template loader     | `addon/templates/note-types/parts/script/card-script.js`                    | Shipped executable template part, shared load promise, retry behavior                          |

`package.json` declares ESM and Node `^22.22.2 || ^24.15.0 || >=26.0.0`; CI uses Node 24. It has no TypeScript dependency or type-checking configuration. Python checking already runs through `typecheck:py`; preserve it.

`scripts/build.config.js` builds separate browser IIFEs: cards target ES2018, editor targets ES2020. Both use esbuild's SVG text loader. Tests run Node's built-in test runner with `tests/support/register-svg.js`; some import source modules, while others evaluate the checked-in minified bundles. `scripts/verify_package_assets.py` explicitly expects JavaScript entry points and scans only `src/**/*.js` for SVG imports.

## Scope and compatibility requirements

- Convert all maintained runtime modules, Node scripts, and JavaScript tests/helpers to `.ts`. Keep Python, CSS, HTML, JSON configuration, fixtures, and dependency code in their existing languages.
- Keep the public bundles at `addon/assets/cards/js/_anki-global-kit.min.js` and `addon/assets/editor/js/editor.min.js`, with the existing IIFE format, targets, legal notices, SVG handling, card loading sentinel, and template-literal escaping option. Preserve all CSS and font output paths.
- Preserve settings keys/defaults, bridge command strings and callback signatures, browser globals, `Symbol.for` keys, saved markup/classes/data attributes, media names, and note-type behavior. No automatic note-type replacement or user-data migration is needed for this conversion.
- Preserve Anki Desktop 26.05 support and card behavior on AnkiWeb, AnkiDroid, and AnkiMobile. Type annotations do not supply missing browser APIs or polyfills.
- Keep Qt modifier translation in Python and standard browser modifier semantics in browser code. Preserve `event.key` versus intentional physical-key `event.code` matching.
- Retain `eslint.config.js` and `prettier.config.js` as explicit tool-configuration exceptions. Keep the shipped template loader as JavaScript; check it with a dedicated no-emit configuration and its existing behavior tests. Generated bundles, dependency/vendor files, and JavaScript text inside tests are also expected JavaScript.
- Retain esbuild, Node's test runner, and the current repository/package structure. Do not introduce a framework, workspace, second bundler, or runtime schema generator solely for this migration.

## Target layout and execution model

Rename source directories to `src/cards/ts/`, `src/editor/ts/`, and `src/shared/ts/`, preserving their internal responsibility boundaries. Rename `tests/javascript/` to `tests/typescript/`, retaining `cards/`, `editor/`, `shared/`, and `tooling/`. Keep support files under `tests/support/`. Convert the six Node scripts in place to `.ts`, including `scripts/build.config.ts`; preserve basenames otherwise.

Use explicit relative `.ts` imports between converted modules and `import type` for erased imports. Keep real `.js`, `.svg`, and package specifiers where those are the actual resources. Avoid path aliases and extensionless imports so Node and esbuild resolve the same graph.

Use Node's native type stripping for scripts and source-module tests. The existing Node floor is above Node 22.18, where stripping became enabled by default. Node requires explicit extensions, ignores TypeScript compiler configuration at runtime, and supports only erasable TypeScript syntax in this mode. Confirm this path at the declared minimum Node versions before converting the tooling; no additional execution loader is planned. See the [Node 22 TypeScript documentation](https://nodejs.org/docs/latest-v22.x/api/typescript.html).

Continue using esbuild to emit browser JavaScript. Run `tsc --noEmit` separately: esbuild parses TypeScript but does not check types, and its explicit browser targets remain authoritative. See [esbuild's TypeScript documentation](https://esbuild.github.io/content-types/#typescript).

## Type-checking design

### Dependencies and compiler policy

Add pinned development versions of `typescript`, `typescript-eslint`, `@types/node`, `@types/jsdom`, and `@types/diff-match-patch` where the installed packages do not already provide suitable types. Use existing declarations for highlight.js and Lezer. Inspect installed metadata first and select a mutually supported TypeScript/ESLint/Node combination; the repository currently uses ESLint 10. Verify support using the [typescript-eslint compatibility table](https://typescript-eslint.io/users/dependency-versions/), then update `package.json` and `package-lock.json` together. Select Node types matching the oldest supported Node major and exercise actual minimum versions to catch APIs introduced in later minor releases.

Use a shared `tsconfig.base.json` with `strict`, `noEmit`, `isolatedModules`, `verbatimModuleSyntax`, `erasableSyntaxOnly`, `allowImportingTsExtensions`, and consistent filename casing. Use `noUncheckedIndexedAccess` from the first converted modules; handle absent array/regex/record entries deliberately. Keep `exactOptionalPropertyTypes` as a separately evaluated tightening step if it distracts from preserving existing optional-property behavior. Resolve configuration details against the selected compiler's [TSConfig reference](https://www.typescriptlang.org/tsconfig/).

Avoid enums, parameter properties, runtime namespaces, decorators, and other syntax that requires TypeScript-specific code generation. Prefer inferred local types, explicit module boundaries, literal unions, and typed records. Type checking must not depend on emitted intermediate JavaScript.

### Separate runtime environments

| Configuration             | Inputs and environment                                                                                                                                      |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tsconfig.cards.json`     | Card entry/source, imported shared code, browser declarations; ES2018 and DOM/DOM.Iterable libraries, `types: []`, ESNext modules with bundler resolution   |
| `tsconfig.editor.json`    | Editor entry/source, imported shared code, browser declarations; ES2020 and DOM/DOM.Iterable libraries, `types: []`, ESNext modules with bundler resolution |
| `tsconfig.node.json`      | Node scripts; NodeNext module/resolution, explicit Node types, ES2022 libraries without ambient DOM globals                                                 |
| `tsconfig.tests.json`     | TypeScript tests/support and imported source/tooling; NodeNext module/resolution, Node and JSDOM types plus DOM libraries                                   |
| `tsconfig.templates.json` | Existing JavaScript template loader and necessary declarations; browser environment, `allowJs` and `checkJs`, no emit                                       |

Put compiler configurations at the repository root. Use `tsconfig.json` as the editor-facing browser project covering all browser source with the card-compatible library baseline; specialized configs provide authoritative environment checks. Test and tooling directories should have small discovery configs extending their corresponding root configurations so VS Code opens those files in the correct project. Ensure type-aware ESLint, if enabled, discovers these same projects.

Shared modules are checked through both browser consumers. The browser-only checks must remain independent of the test project's broader environment: Node globals must not become available to production card code simply because tests use Node. Include every converted module in at least one authoritative configuration, including modules not currently reachable from an entry point.

During migration, allow mixed JavaScript/TypeScript imports with narrowly scoped `allowJs` and `checkJs: false`. Add converted files to strict checking immediately and track remaining JavaScript explicitly. Remove that transition allowance from source, tooling, and test projects at completion; retain only the intentional JavaScript exceptions.

### Runtime declarations and boundaries

- Put narrow ambient declarations near each runtime, with only genuinely shared host declarations under shared types. Describe optional `pycmd`, card client markers (`study`, `AnkiDroidJS`), injected settings, persistent observers, script-loading state, and `hasMyCustomScript`. Detection-only globals can be `unknown`; do not invent APIs.
- Model `ankiGlobalKitEditor` methods from the actual Python call sites and browser installers. Its installation is incremental, so an initially empty or partial object must not masquerade as a fully installed API. Preserve receiver, argument, return, and optional-method behavior.
- Distinguish externally supplied settings from normalized settings. Keep `addon/config.json` authoritative and retain fallback/default parity checks; TypeScript interfaces do not validate saved JSON or Python-injected values at runtime.
- Type the used subset of `require('anki/NoteEditor')`, editor field metadata, and synchronous stores in `helpers/fields`. Keep this browser host loader separate from Node's module types, and preserve missing-host fallbacks.
- Type bridge requests, response payloads, request IDs, rendered Markdown blocks, and highlighting options next to their owners. Cross-check them against `addon/desktop/editor/features/` and integration code. Retain runtime validation of JSON and stale responses; adding interfaces must not weaken these checks.
- Add a `*.svg` module declaration exporting `string`, matching both esbuild and the test loader. Audit CommonJS interop for `diff-match-patch` through both direct Node imports and bundled execution.
- Use specific DOM element, event, selection/range, observer, map, set, and callback types. Narrow nullable results and event targets with guards. Handle cross-window JSDOM/iframe elements using the relevant document's constructors or existing structural checks; avoid introducing global-constructor assumptions.
- Type state initialized with `null`, `undefined`, empty collections, or empty objects explicitly, including answer output and observer state. Preserve reinjection state and stable `Symbol.for` storage; model symbol properties locally rather than adding unrestricted index signatures to DOM types.
- Use `unknown` at untrusted boundaries and narrow it. Avoid blanket `any`, `@ts-nocheck`, broad fake module declarations, and repeated unchecked assertions. Any unavoidable third-party typing workaround needs a narrow scope and a reason.

## Implementation phases

### Phase 1: Baseline and migration infrastructure

1. Start on `dev` or a dedicated feature branch. Record existing failures and unrelated working-tree changes without including them in migration commits. Run current lint/check, build, asset verification, and tests before renames.
2. Add compiler dependencies/configurations, SVG declarations, and `typecheck:ts`. Aggregate explicit `tsc -p <configuration> --noEmit` invocations so all environments are checked; add the command to `npm run check` alongside the existing Python checks.
3. Extend ESLint's flat configuration to parse and lint `.ts` with typescript-eslint. Scope browser globals to browser files and Node globals to tooling/tests. Replace overlapping core rules with TypeScript equivalents; preserve existing import checks and configure TypeScript resolution with a compatible resolver if needed. Start with recommended rules; add type-aware rules only when project discovery works reliably. Follow the [typescript-eslint flat-config guide](https://typescript-eslint.io/getting-started/).
4. Extend Prettier's single-quote override to `.ts` and Lefthook's ESLint/Prettier globs to `.ts`. Add a full TypeScript check triggered by relevant source, declarations, compiler configs, package files, and build configuration changes; checking only staged files misses import consumers. Preserve Python hooks.
5. Configure VS Code to use the workspace TypeScript SDK. Update CI's check label and ensure type checking runs before building/testing. Add focused compatibility coverage for Node 22.22.2, 24.15.0, and 26.0.0 execution, keeping the existing full CI job on Node 24.
6. Prove one small TypeScript module can be type-checked, imported directly by Node, bundled by esbuild, and tested with an SVG import. Confirm Node stripping and SVG hooks coexist before changing all test entry points.

Exit: mixed-language infrastructure works, converted modules receive strict checks, and the existing application remains buildable.

### Phase 2: Shared modules and common types

1. Convert the shortcut policy and keyboard helpers, then language aliases/registries, code-line helpers, Markdown rendering, classification roles/scopes/language adapters, and code-block controls. Use actual import dependencies to order changes.
2. Type Lezer nodes/trees, highlighting results, Markdown parser stacks, shortcut descriptors, and control options. Preserve runtime behavior where shared controls currently call the Desktop bridge; moving that behavior belongs to the architecture refactor.
3. Rename shared source to `src/shared/ts/` and update imports from both still-JavaScript and converted callers in the same commit. Convert matching shared tests and any needed support files incrementally.
4. Update the asset verifier to scan both `.js` and `.ts` source imports during migration, including icons referenced only by TypeScript. Add a focused regression proving such icons are still required in the package.

Exit: shared modules pass both browser environments' type checks and their existing behavior tests; SVG packaging coverage survives the conversion.

### Phase 3: Card runtime

1. Type and convert runtime settings/state/platform/storage and DOM helpers, then display, inputs, integrations, highlighting, initialization, and the entry point. Keep absent client APIs and unavailable session storage valid states.
2. Rename to `src/cards/ts/`, update relative/shared imports, and change the card build entry point. Update verifier expectations in the same change so package verification remains usable.
3. Convert card tests without changing their behavioral expectations. Preserve loader retry/overlap checks, source-module tests, and tests evaluating the generated IIFE.
4. Build and include the generated card bundle. Review output changes, public names, banner/sentinel, escaping, and size; investigate unexpected growth or runtime helpers.

Exit: card source is strictly checked, existing source/bundle tests pass, and asset verification accepts the new source path with the original installed filename.

### Phase 4: Editor runtime and Python bridge

1. Convert settings, field/store access, selection, request IDs, and editing transactions before their formatting, clipboard, cloze, styles, language menu, toolbar, and initialization consumers.
2. Add the typed editor API and payload contracts while preserving current installation order, reinjection guards, symbol state, request identity, selection snapshots, and stale-result rejection. Compare Python-produced calls with the TypeScript signatures.
3. Rename to `src/editor/ts/`, update imports and the editor build entry point, and update verifier expectations atomically. Retain native undo and all supported editing fallbacks.
4. Convert editor tests and fixtures with typed JSDOM helpers. Represent deliberately incomplete host stubs narrowly and keep missing/malformed input coverage; avoid casting an entire test window or fixture to a complete production API.
5. Build and include the generated editor bundle. Run editor behavior and Python integration tests together, especially shortcut parity, bridge callbacks, and repeated injection.

Exit: editor source is strictly checked and current editing/bridge behavior passes existing isolated tests with stable public APIs.

### Phase 5: Node tooling, remaining tests, and template checking

1. Convert build configuration, logging, metadata, linking, build, and watch scripts. Use esbuild's `BuildOptions`/plugin/result types and explicit error narrowing. Preserve metadata validation, saved settings, symlink behavior, Python generators, watch logging, and output-write behavior.
2. Update npm commands to execute `.ts` scripts directly with Node. Change all script imports, tests, and references together. Update `scripts/verify_package_assets.py` to read `scripts/build.config.ts` and recognize typed build-option declarations; its current source-text matching must not reject `satisfies BuildOptions` or annotations. Keep meaningful validation of entry/output paths.
3. Update watch roots to the new `ts` directories. Verify editing card, editor, and shared TypeScript triggers the correct bundles and that icons, CSS, Python themes, and font notices still rebuild as before. Keep `tsc --watch` as a separate documented feedback command; esbuild watch success alone does not mean types pass.
4. Finish renaming tests to `tests/typescript/**/*.test.ts` and helpers to `.ts`. Update `test:js` to use `node --import ./tests/support/register-svg.ts --test "tests/typescript/**/*.test.ts"`. Retain `test:js` as the documented JavaScript-runtime test command and `lint:js` as the JavaScript/TypeScript lint command; keep `npm test` and `npm run lint` working throughout mixed phases by temporarily including both test extensions/locations.
5. Type-check the retained template loader with JSDoc where necessary, without changing its filename or template assembly. Keep its behavior tests reading the shipped JavaScript file. Retain JavaScript tool configuration files as the documented exception list.
6. Remove transitional `allowJs`, obsolete source copies, temporary mixed test globs, and stale path references from active tooling/docs. Keep historical archived plans intact. Add a maintained-source inventory check that permits only the explicit JavaScript exceptions and excludes generated/vendor files.

Exit: all planned maintained modules/tests/tooling are TypeScript, every compiler environment passes, and clean-checkout npm commands preserve their existing purpose.

### Phase 6: Documentation and acceptance

Update `README.md`, `AGENTS.md`, and the development architecture/dependency/publishing instructions with source paths, compiler dependencies, native Node execution, type-check/watch commands, and JavaScript exceptions. Document the completed migration in `CHANGELOG.md` when implemented; do not describe this planning document as a completed conversion. Coordinate active architecture-plan paths if both efforts remain open.

## Validation and completion criteria

Run focused tests and type checks after each module group, with generated bundles rebuilt before bundle tests. At completion, run from a clean checkout with locked dependencies:

```sh
npm ci
uv sync --locked
npm run lint
npm run check
npm run build
npm run verify:package-assets
npm test
npm run package:addon
git diff --exit-code -- addon/assets/cards addon/assets/editor addon/assets/fonts/_meslolgl-nf-license.txt src/shared/css/generated/cassidy-dark.css
```

The final diff check runs after the intended generated changes are committed; before committing, inspect those changes directly. Verify the archive contains ordinary JavaScript/CSS and existing runtime resources, excludes compiler dependencies and `.ts`/`.d.ts` source, and retains required notices. If Python verification code changes, run Ruff, formatting, and Pyright alongside its focused tests.

Confirm checks actually cover their targets: an intentional temporary type error in a card, editor, Node, test, and template input must fail the corresponding checker; a missing TypeScript-imported icon must fail asset verification. Remove temporary probes before committing. The retained source-module tests and compiled-IIFE tests must both pass; neither substitutes for the other. Exercise build/test/loader execution at the declared Node floors and watch behavior with a disposable development profile.

Record manual acceptance on Anki Desktop 26.05 and a current supported release: reviewer/preview transitions, answer persistence, focus/shortcuts, Markdown/highlighting, Settings propagation, editor copy/cloze/formatting, native undo, bridge responses, and repeated injection. Check macOS modifier handling and another Desktop platform. Sync a disposable collection to AnkiWeb, AnkiDroid, and AnkiMobile and verify card behavior and asset loading. Preserve existing templates without replacement. Record unavailable clients and outstanding checks explicitly; DOM/Qt stubs do not establish live acceptance.

The migration is complete when all intended maintained JavaScript has moved to checked TypeScript, only documented JavaScript exceptions remain, strict checks and existing tests pass, generated/package assets retain public interfaces, and acceptance results and limitations are recorded. Commit each completed phase or coherent smaller group on a non-`main` branch, staging only related source, configuration, tests, docs, and generated assets.

## Risks and rollback

| Risk                                                                | Mitigation                                                                                     |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Successful bundling hides type errors                               | Separate `tsc --noEmit` checks in local validation, hooks, and CI                              |
| Tests import source differently from shipped code                   | Preserve direct-import and compiled-bundle coverage, including SVG and CommonJS interop        |
| Declarations overstate Anki host availability                       | Optional globals, narrow host interfaces, boundary validation, minimum-version/live acceptance |
| DOM assertions hide nullable or cross-window behavior               | Guards, precise local types, existing behavior tests, explicit JSDOM helpers                   |
| Renames silently skip tests, lint, icons, or packaging checks       | Update globs and verifier together; inventory converted files and use focused failure probes   |
| Type conversion changes persistent browser state or bridge behavior | Preserve symbol keys, globals, payloads, and reinjection/stale-response tests                  |

Keep commits buildable and revert a migration group together with its generated bundles and tooling references. No saved-data transformation or automatic note-type replacement is part of this plan. A rollback restores the previous source/tooling/bundles while retaining user settings, notes, templates, and unrelated media. If a behavior fix becomes necessary during conversion, isolate and test it separately so language-only changes remain reviewable.
