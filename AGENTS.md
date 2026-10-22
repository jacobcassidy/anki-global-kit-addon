# Repository guide for agents

## Project purpose

Anki Global Kit combines Anki Desktop features with card-side JavaScript and CSS. Desktop code runs in the add-on. Card assets are installed into the active profile's `collection.media` folder; card templates load those files and Anki sync carries the media and template changes to AnkiWeb and the mobile clients.

The add-on can create missing topic and format note types in the active profile. It does not modify existing types automatically: users must select **Replace** and confirm before kit templates and styling are applied. Replacement keeps notes and fields, adds missing kit fields, and updates the first card template and styling. For standard note types, additional templates and their associated cards are removed; the confirmation must list their names and template and card removal counts, and the service must revalidate this impact before applying changes. **Delete** is available only for empty note types or uncreated custom topics.

## Repository map

- `addon/__init__.py` — Required Anki add-on entry point; initializes the Desktop features.
- `addon/desktop/` — Python code that runs in Anki Desktop.
  - `bootstrap.py` owns startup and hook registration; `paths.py` contains shared filesystem paths.
  - `config/`, `media/`, `note_types/`, and `shortcuts/` own Desktop configuration, asset installation, note-type operations, and shortcut handling.
  - `settings/pages/` contains Settings presentation; `settings/bindings.py`, `settings/save.py`, and `settings/dialog.py` coordinate controls and saving.
  - Help Markdown, including the project description, lives beside its Settings page as `help/help-content.md`.
  - `ui/` contains reusable Qt controls and presentation constants; `editor/` contains editor integration and feature coordination.
- `addon/assets/icons/` — SVG icons shared by the card toolbar, Desktop editor, and settings UI.
- `addon/assets/fonts/` — Packaged shared card and editor fonts.
- `addon/assets/cards/` — Built card assets grouped into `css/` and `js/`. The installer copies managed files into the active profile's `collection.media` root under their public filenames.
- `addon/assets/editor/` — Built Desktop editor assets grouped into `css/` and `js/`.
- `addon/templates/note-types/parts/` — HTML, script, and styling parts used to create note types.
- `src/cards/js/` — Card-side JavaScript.
  - `inputs/` handles textarea setup, answer persistence/submission, keyboard navigation, and Markdown shortcuts.
  - `display/` controls question, answer, hint, note, and comparison display.
  - Markdown conversion lives in `src/shared/js/markdown/` for card and editor consumers.
  - `syntax-highlighting/` detects languages from the topic and highlights code.
  - `runtime/` detects clients, holds state, and initializes features.
  - `integrations/` contains client-specific integrations such as AnkiWeb layout handling.
- `src/cards/css/` — Card styles. `index.css` imports the module stylesheets.
- `src/editor/js/` and `src/editor/css/` — Desktop editor JavaScript and styles.
- `src/shared/js/` and `src/shared/css/` — Code shared between card and editor targets when runtime behavior is genuinely common.
- `tests/` — JavaScript and Python tests grouped by runtime responsibility; shared stubs live under `tests/support/`.
- `scripts/` — esbuild configuration, build, and watch scripts.
- `docs/reference/screenshots/` — Screenshots of card layouts and settings pages.
- `docs/development/` — Developer, dependency, and publishing instructions.
  - `ankiweb-description.md` contains the AnkiWeb listing content and is not shipped in the add-on archive.
- `README.md` — User-facing features and setup.

## Build and generated files

Install JavaScript development dependencies with `npm install`. Build the card assets from the repository root:

```sh
npm run build
```

The build bundles the card and Desktop editor sources into:

- `addon/assets/cards/js/_anki-global-kit.min.js`
- `addon/assets/cards/css/_anki-global-kit.min.css`
- `addon/assets/editor/js/editor.min.js`
- `addon/assets/editor/css/editor-fields.min.css` and `editor-ui.min.css`

When changing source files that feed these builds, regenerate the affected minified assets with `npm run build` and include those generated files in the same commit as the source changes.

The packaged shared card and editor font is kept in `addon/assets/fonts/`. `scripts/font_notices.py` combines `FONT-LICENSES.md` and the adjacent `licenses/*.txt` into `_meslolgl-nf-license.txt` during builds and packaging; Python 3 is required for this step. Update the source notices and regenerate the companion rather than editing the generated file. `addon/desktop/media/manifest.py` maps public filenames to packaged paths, and `addon/desktop/media/install.py` installs managed assets under their public names in the `collection.media` root. Run `npm run verify:package-assets` to verify the source, build, package, template, and media paths, including notice freshness. These generated files are included in the add-on package. Update `scripts/build.config.js` if source entry points or output names change, along with the installer and template references when renaming installed assets. The watch script watches card, editor, and shared JavaScript and CSS, imported icons, syntax theme Python sources, and font notice sources.

Useful project scripts:

- `npm test` — Run the JavaScript and Python test suites.
- `npm run test:scripts` — Run JavaScript tests with Node's built-in test runner.
- `npm run test:python` — Run Python tests with unittest and isolated Qt stubs.
- `npm run lint:scripts` — JavaScript linting.
- `npm run lint:styles` — CSS linting.
- `npm run lint:docs` — Markdown linting.
- `npm run check` — Prettier formatting check.

## Implementation boundaries

- Use token or variable-based colors throughout the project; do not add static hardcoded colors. Anki Desktop settings and other Qt components must use Anki color tokens, while webview components must use CSS variables.
- Use `rem` for CSS sizing throughout the app unless another unit is specifically needed for the layout or behavior.
- Put review-time behavior in `src/cards/` when it needs to run across Anki clients. Put editor behavior in `src/editor/` and use `addon/desktop/editor/` for its Desktop integration. Do not assume Python add-on code runs outside Anki Desktop.
- Use the Python add-on for Desktop installation, configuration, and collection operations. Settings presentation lives in `addon/desktop/settings/pages/`, coordinated by `dialog.py`, `bindings.py`, and `save.py`. Shared services live in the Desktop `config/`, `media/`, `note_types/`, and `shortcuts/` packages; reusable Qt controls and presentation constants live in `desktop/ui/`. Connect to Anki through documented hooks and APIs instead of patching internal functions when a supported hook exists.
- When adding a button or keyboard shortcut to Anki Global Kit, add the corresponding control or configuration to Anki Global Kit Settings as appropriate.
- Reserve every new fixed editor shortcut against configurable shortcuts. Add fixed bindings to `EDITOR_BLOCK_SHORTCUTS` and ensure Settings rejects conflicting assignments.
- Keep release defaults in `addon/config.json`, including `note_type_selections`. Anki manages `addon/meta.json` as local installation metadata and saved configuration; leave it untracked and excluded from release archives. Do not copy local selections or platform-specific saved shortcuts into release defaults.
- Treat media filenames as public interfaces: the installer, templates, and stylesheet imports must use identical names.
- The add-on refreshes the kit's reserved asset names through Anki's media manager on `profile_did_open`. Keep installation scoped to those managed assets; do not overwrite user templates or unrelated media without an explicit opt-in design.
- Create, replace, and delete note types through Anki's documented `col.models` APIs. Never replace or delete a user's type without explicit selection and confirmation; deletion is limited to empty types. If a kit type name already exists and Replace was not selected, leave it unchanged and report that to the user.
- Note type operations live in `addon/desktop/note_types/service.py` and read runtime template parts from `addon/templates/note-types/parts/{html,script,styling}/`. These are the source templates used to create or explicitly replace kit types.
- Preserve cross-client behavior. Check platform-specific code in `src/cards/js/runtime/platform.js` and `src/cards/js/inputs/` before changing answer storage or keyboard behavior.
- On macOS, Anki's Qt/webview keyboard handling swaps the usual modifier names: Anki's `Ctrl` setting corresponds to physical Command (⌘), while `Meta` corresponds to physical Control (⌃). Browser keyboard events use the standard mapping: Command sets `event.metaKey`, and physical Control sets `event.ctrlKey`. Do not apply the Qt modifier swap to browser events. Keep shortcut labels consistent with that mapping. Use `event.key` when matching the character produced by the current keyboard layout; use `event.code` only when a shortcut intentionally targets a physical key regardless of layout (for example, the physical C key).
- If changing required template markup or CSS imports, update the applicable runtime parts under `addon/templates/note-types/parts/` and document any user migration in `README.md` or the changelog. Existing note types receive the change only after the user selects Replace and confirms.
- Keep gaps between custom Anki editor toolbar button groups at Anki's native default size. Do not add extra wrapper gaps; Anki's button spacing already supplies the standard gap.

## Repository guidance

- Finish each task or feature by committing its completed changes after appropriate validation.
- Match the existing commit message style and formatting; use a plain, sentence-case imperative subject without adding prefixes or changing the format.
- When relevant, document completed tasks or features in `CHANGELOG.md` and/or `README.md`.

## Code Spacing Rules

- Put a blank line before each JSDoc block, except at the start of a file.
- Separate a control-flow statement from the preceding statement at the same level with a blank line. This includes `if`, loops, `switch`, `try`, `return`, `throw`, `break`, and `continue`. Do not pad the start of a block or detach `else`, `catch`, `finally`, or `do...while` continuations.
- Put a blank line after a completed block, control-flow statement, or multiline expression statement when another statement follows at the same level. Keep function-call arguments and chained expressions together.
- Put a blank line after a standalone `let`, `const`, or `var` when the next statement is not another variable declaration. Keep consecutive variable declarations together; do not pad before closing syntax or inside loop headers.
- Put a blank line after every export declaration, including `export const`, before any following code or comment.
- Separate a `const` declaration spanning more than three source lines from neighboring statements with blank lines, including adjacent variable declarations.

Exceptions to these spacing rules:

- Keep a `const` and the single-line statement that immediately precedes its block’s closing syntax together, even when the `const` spans multiple lines. Retain any required blank line before the `const`.
- If every statement directly inside a code block fits on one source line, omit blank lines between them. Apply this separately to nested blocks. Keep comments attached to their code and preserve spacing before JSDoc blocks.

## Git commits

- Never create or amend commits on `main`. Check the current branch immediately
  before committing. If a commit is requested while `main` is checked out,
  including an explicit request to commit to `main`, ask the user whether to
  switch to `dev` or another branch and wait for their choice before committing.
- Stage only files belonging to that change. Do not include unrelated user work.
- Check the repository root before committing, especially when accessing this
  directory through a symlink. If no repository is available, report that and
  arrange repository setup rather than claiming a commit was created.
- Report validation performed and any limitations; do not claim live Anki
  verification when only syntax checks or isolated tests were run.

## Anki development references

The minimum supported Anki Desktop version is **26.05** (`min_point_version: 260500` in `addon/manifest.json`). Keep this minimum aligned with the setup documentation and AnkiWeb listing.

Use the official documentation as the primary API reference for Anki-specific work:

- [Writing Anki add-ons](https://addon-docs.ankiweb.net/) — add-on architecture and development overview.
- [Hooks and filters](https://addon-docs.ankiweb.net/hooks-and-filters.html) — supported extension points.
- [Reviewer JavaScript](https://addon-docs.ankiweb.net/reviewer-javascript.html) — `card_will_show` and card display contexts.
- [The `anki` module](https://addon-docs.ankiweb.net/the-anki-module.html) — collection/media access from Python add-ons.
- [Add-on folders](https://addon-docs.ankiweb.net/addon-folders.html) — local add-on layout and packaging.
- [Sharing add-ons](https://addon-docs.ankiweb.net/sharing.html) — `.ankiaddon` archive format.
- [Card templates](https://docs.ankiweb.net/templates/intro.html) — front/back templates and styling.
- [Media](https://docs.ankiweb.net/media.html) and [syncing](https://docs.ankiweb.net/syncing.html) — Anki media and sync behavior.
- [AnkiDroid manual](https://docs.ankidroid.org/) and [AnkiMobile manual](https://docs.ankimobile.net/) — client-specific behavior and setup.

For each feature, prefer documentation and hooks that match the supported Anki versions. Verify version-sensitive APIs against the actual minimum-version target before relying on them.
