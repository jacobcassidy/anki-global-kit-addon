# Pygments syntax highlighting classes

This reference covers the default HTML CSS classes in Pygments **2.19.2**, the version bundled with Anki Global Kit. Token meanings depend on the language lexer; a lexer may use only some of these classes.

## Standard token classes

The table includes every entry in Pygments' `STANDARD_TYPES` mapping. Class names appear without the CSS selector's leading dot: `k` means `class="k"` in HTML and `.k` in CSS. Token names omit the `Token.` prefix; `String` and `Number` are aliases for `Literal.String` and `Literal.Number`.

Sources: [Pygments 2.19.2 token-to-class mapping](https://github.com/pygments/pygments/blob/2.19.2/pygments/token.py#L123-L217) and [official token descriptions](https://pygments.org/docs/tokens/).

| Class name | Token type               | Description                                              |
| ---------- | ------------------------ | -------------------------------------------------------- |
| None       | `Token`                  | Root token; no token class is emitted.                   |
| None       | `Text`                   | Plain text; no token class is emitted.                   |
| `w`        | `Text.Whitespace`        | Spaces, tabs, and other whitespace.                      |
| `esc`      | `Escape`                 | Content designated for formatter escape handling.        |
| `err`      | `Error`                  | Text the lexer identifies as invalid.                    |
| `x`        | `Other`                  | Content outside the lexer's language.                    |
| `k`        | `Keyword`                | General language keywords.                               |
| `kc`       | `Keyword.Constant`       | Constant-valued keywords.                                |
| `kd`       | `Keyword.Declaration`    | Keywords introducing declarations.                       |
| `kn`       | `Keyword.Namespace`      | Keywords introducing imports or namespaces.              |
| `kp`       | `Keyword.Pseudo`         | Keyword-like constructs without keyword status.          |
| `kr`       | `Keyword.Reserved`       | Reserved words.                                          |
| `kt`       | `Keyword.Type`           | Keywords naming built-in types.                          |
| `n`        | `Name`                   | General identifiers.                                     |
| `na`       | `Name.Attribute`         | Attribute names, including markup attributes.            |
| `nb`       | `Name.Builtin`           | Built-in identifiers.                                    |
| `bp`       | `Name.Builtin.Pseudo`    | Implicit built-in names, such as `this`.                 |
| `nc`       | `Name.Class`             | Class identifiers, especially in declarations.           |
| `no`       | `Name.Constant`          | Identifiers representing constants.                      |
| `nd`       | `Name.Decorator`         | Decorator or annotation names.                           |
| `ni`       | `Name.Entity`            | Named entities in markup.                                |
| `ne`       | `Name.Exception`         | Exception identifiers.                                   |
| `nf`       | `Name.Function`          | Function or method identifiers.                          |
| `fm`       | `Name.Function.Magic`    | Special methods, such as `__init__`.                     |
| `py`       | `Name.Property`          | Properties or class attributes.                          |
| `nl`       | `Name.Label`             | Labels for jumps or other labeled constructs.            |
| `nn`       | `Name.Namespace`         | Namespace, module, or import-path names.                 |
| `nx`       | `Name.Other`             | Identifiers assigned to the miscellaneous name category. |
| `nt`       | `Name.Tag`               | Markup or configuration tag names.                       |
| `nv`       | `Name.Variable`          | General variable identifiers.                            |
| `vc`       | `Name.Variable.Class`    | Class or static variables.                               |
| `vg`       | `Name.Variable.Global`   | Global variable identifiers.                             |
| `vi`       | `Name.Variable.Instance` | Instance variable identifiers.                           |
| `vm`       | `Name.Variable.Magic`    | Special variables, such as `__doc__`.                    |
| `l`        | `Literal`                | Literal values without a narrower classification.        |
| `ld`       | `Literal.Date`           | Date literals.                                           |
| `s`        | `String`                 | General string literals.                                 |
| `sa`       | `String.Affix`           | String prefixes or suffixes specifying string behavior.  |
| `sb`       | `String.Backtick`        | Strings delimited by backticks.                          |
| `sc`       | `String.Char`            | Character literals.                                      |
| `dl`       | `String.Delimiter`       | Delimiting identifiers for heredoc or similar strings.   |
| `sd`       | `String.Doc`             | Documentation strings.                                   |
| `s2`       | `String.Double`          | Strings delimited by double quotes.                      |
| `se`       | `String.Escape`          | Escape sequences within strings.                         |
| `sh`       | `String.Heredoc`         | Heredoc string content.                                  |
| `si`       | `String.Interpol`        | Interpolated portions of strings.                        |
| `sx`       | `String.Other`           | Strings assigned to the miscellaneous string category.   |
| `sr`       | `String.Regex`           | Regular-expression literals.                             |
| `s1`       | `String.Single`          | Strings delimited by single quotes.                      |
| `ss`       | `String.Symbol`          | Symbol literals.                                         |
| `m`        | `Number`                 | General numeric literals.                                |
| `mb`       | `Number.Bin`             | Binary numeric literals.                                 |
| `mf`       | `Number.Float`           | Floating-point numeric literals.                         |
| `mh`       | `Number.Hex`             | Hexadecimal numeric literals.                            |
| `mi`       | `Number.Integer`         | Integer literals.                                        |
| `il`       | `Number.Integer.Long`    | Long-integer literals.                                   |
| `mo`       | `Number.Oct`             | Octal numeric literals.                                  |
| `o`        | `Operator`               | Symbolic operators.                                      |
| `ow`       | `Operator.Word`          | Operators spelled as words.                              |
| `p`        | `Punctuation`            | Separators, brackets, and other punctuation.             |
| `pm`       | `Punctuation.Marker`     | Position indicators, such as traceback carets.           |
| `c`        | `Comment`                | General comments.                                        |
| `ch`       | `Comment.Hashbang`       | Interpreter directives beginning with `#!`.              |
| `cm`       | `Comment.Multiline`      | Block or multiline comments.                             |
| `cp`       | `Comment.Preproc`        | Preprocessor directives or language-opening constructs.  |
| `cpf`      | `Comment.PreprocFile`    | Filenames in preprocessor directives.                    |
| `c1`       | `Comment.Single`         | Comments extending to the line end.                      |
| `cs`       | `Comment.Special`        | Special comment content or metadata.                     |
| `g`        | `Generic`                | General tokens for non-source-code formats.              |
| `gd`       | `Generic.Deleted`        | Removed content in a diff.                               |
| `ge`       | `Generic.Emph`           | Emphasized content.                                      |
| `gr`       | `Generic.Error`          | Error-message content.                                   |
| `gh`       | `Generic.Heading`        | Main headings.                                           |
| `gi`       | `Generic.Inserted`       | Added content in a diff.                                 |
| `go`       | `Generic.Output`         | Program or console output.                               |
| `gp`       | `Generic.Prompt`         | Interactive shell or interpreter prompts.                |
| `gs`       | `Generic.Strong`         | Strongly emphasized content.                             |
| `gu`       | `Generic.Subheading`     | Secondary headings.                                      |
| `ges`      | `Generic.EmphStrong`     | Content combining emphasis and strong emphasis.          |
| `gt`       | `Generic.Traceback`      | Traceback content.                                       |

## Custom token classes

Lexers can create additional token subtypes, so there is no finite list of every possible token class. For a subtype absent from `STANDARD_TYPES`, the HTML formatter extends the nearest standard ancestor's class with hyphen-separated subtype names. For example, `Name.Function.Custom` becomes `nf-Custom`; output can also include ancestor classes. The `classprefix` option prepends a configured string to token class names. These rules are defined in the [Pygments 2.19.2 HTML formatter](https://github.com/pygments/pygments/blob/2.19.2/pygments/formatters/html.py).

## Supporting HTML classes

The HTML formatter can also emit these classes depending on its options. They describe layout or presentation rather than token types. `highlight` is the default wrapper class; the `cssclass` option changes it and the corresponding table class. These classes and options are documented in the [HTML formatter reference](https://pygments.org/docs/formatters/#HtmlFormatter) and implemented in the [Pygments 2.19.2 HTML formatter source](https://github.com/pygments/pygments/blob/2.19.2/pygments/formatters/html.py).

| Class name       | Description                                                |
| ---------------- | ---------------------------------------------------------- |
| `highlight`      | Default outer wrapper for highlighted code.                |
| `highlighttable` | Default table wrapper when table line numbers are enabled. |
| `code`           | Table cell containing source code.                         |
| `linenos`        | Line-number table cell or inline line-number span.         |
| `linenodiv`      | Wrapper around the line-number column's content.           |
| `normal`         | Ordinary line numbers in table mode.                       |
| `special`        | Line numbers emphasized at the configured interval.        |
| `hll`            | Lines selected through the `hl_lines` option.              |
| `filename`       | Filename label or its table heading cell.                  |
