# Identifier Classification

JavaScript and Python share a parser-based classifier in `src/shared/js/syntax-highlighting/classification/`. It supplements Pygments in the Desktop editor and highlight.js in typed-answer review. It parses snippets without executing their code or loading their imports.

## Pipeline

1. The existing engine renders escaped syntax HTML.
2. `enhanceHighlightHtml()` reads that detached HTML's text content and calls `classifyCode()`.
3. A language adapter uses its Lezer grammar to collect scopes and bindings, then classifies references and syntax contexts.
4. The markup helper wraps the classified text in spans with `data-global-kit-token` attributes. Existing lexical spans remain intact. The result must preserve the original text content exactly.
5. Editor code receives line wrappers and is inserted through the existing undo transaction. Markdown uses the same enrichment before insertion. Review applies it after highlight.js renders each typed-answer code block.

Saved HTML carries the normalized theme role, so displaying a saved block requires no parser. Existing saved blocks are not rewritten automatically; explicitly highlight them again to add annotations. No compatibility conversion for older generated HTML is provided.

## Modules and Contract

- `index.js` owns the static language registry, cloze protection, parser stepping, deadlines, and output validation. `classifyCode(source, language, { budget })` returns sorted, non-overlapping `{ from, to, role, builtin }` spans. Offsets count UTF-16 units, matching browser text nodes and Lezer offsets.
- `scopes.js` provides scope storage, binding lookup, and iterative tree traversal. Adapters choose their scope parents and implement language-specific binding semantics.
- `roles.js` maps language-neutral classifications to existing theme palette roles. Builtin functions and classes use `builtin`, builtin constants use `builtin-constant`, builtin variables use `library-variable`, and properties use `attribute`.
- `markup.js` owns detached DOM annotation. It can split one classified identifier across multiple lexical text leaves without changing the source or losing lexical formatting. Any failure returns the original engine HTML.
- `languages/javascript.js` and `languages/python.js` own their parsers, binding rules, builtin tables, and contextual classifications. They do not import DOM or Anki APIs.

All colors and font styles come from the existing generated theme variables. An annotation's palette role is an internal HTML interface; do not put concrete colors in the language adapters.

## Binding and Usage Rules

Known local bindings take precedence over builtin names and call syntax. A parameter named `str` or `String` remains a parameter throughout its scope, including when called. Function declarations, directly assigned functions and lambdas, and class declarations retain their known roles at references.

An otherwise unknown direct call target is classified as a function. A named member used as a call target is a method; other named member access is a property. Other unresolved identifier reads are variables. Computed member strings stay strings, and computed index expressions retain their own binding roles. There is no capitalization-based class guessing.

JavaScript uses function and block scopes, namespace imports, destructured/default/rest parameters, class and object methods, and optional member access. Python handles function-wide locals, lambdas, comprehensions, imports, `global` and `nonlocal`, methods declared in classes, and recognized builtin `@property` declarations/accessors. Python `def` and `class` are declarations; ordinary control-flow keywords retain basic syntax coloring.

Builtin tables cover Python builtin names and standard ECMAScript globals. They do not contain browser API or third-party library catalogs. An imported symbol can shadow a builtin without its imported type being known. The classifier does not perform project-wide resolution, type inference, arbitrary alias propagation, or control-flow analysis. Member-call classification describes syntax, not a guarantee about the receiver's runtime type.

Comments, strings, and regex contents receive no identifier overlays. Expressions inside template strings and f-strings are analyzed. Complete cloze ranges are masked with equal-length spaces, preserving newlines, and receive no annotation spans. Recoverable parse errors exclude uncertain ranges without discarding useful surrounding structure.

Literal cloze mode uses small brace guard spans when editor HTML is serialized. These preserve the displayed source while preventing browser entity normalization from turning literal clozes into active Anki clozes. Switching back to active mode removes the guards.

## Limits and Extension

Classification uses a cooperative deadline of 100 ms per editor operation and 25 ms per review answer, shared across blocks in that operation. Checks occur between parser advances and during traversal and annotation. These deadlines cannot interrupt one synchronous parser or browser DOM operation. Existing source-size and review block/answer limits still apply. Exhaustion or failure retains the base engine HTML.

The pinned dependencies are `@lezer/javascript` 1.5.6 and `@lezer/python` 1.1.18. npm locks their runtime dependencies. The complete notices for both grammars and `@lezer/common`, `@lezer/lr`, and `@lezer/highlight` are included in both built scripts. Asset/package checks verify the notices and grammar pins.

To support another language, add a language adapter returning the same roles and register its canonical language identifier. Keep builtin knowledge and binding rules in that adapter. Add fixtures covering declarations, references, shadowing, members, literals, errors, clozes, and Unicode offsets, plus parity tests across the editor and review engines. TypeScript, JSX, project-wide language services, and live classification while typing are outside this first implementation.
