"""Pure theme validation and CSS generation."""

from __future__ import annotations

import re

from .custom_themes import PRESETS
from .rendering import _with_bundled_modules

_COLOR = re.compile(r"#[0-9a-fA-F]{6}\Z")
_BASE_COLOR_ROLES = {
    "background",
    "foreground",
    "comment",
    "punctuation",
    "muted",
    "builtin",
    "keyword",
    "function",
    "class",
    "attribute",
    "constant",
    "operator",
    "string",
    "error",
}
_ROLE_FALLBACKS = {
    "declaration": "keyword",
    "builtin-constant": "constant",
    "method": "function",
    "namespace": "class",
    "parameter": "foreground",
    "variable": "foreground",
    "library-variable": "builtin",
}
_CASSIDY_DARK_SYNTAX_VARIABLES = {
    "background": "gray-900",
    "foreground": "gray-200",
    "comment": "gray-500",
    "punctuation": "gray-400",
    "muted": "gray-200",
    "builtin": "gray-000",
    "builtin-constant": "purple",
    "keyword": "red",
    "declaration": "blue",
    "function": "cyan",
    "method": "gray-000",
    "class": "cyan",
    "namespace": "purple",
    "parameter": "orange",
    "attribute": "green",
    "variable": "pink",
    "library-variable": "gray-100",
    "constant": "purple",
    "operator": "red",
    "string": "yellow",
    "error": "red-deep",
}
_COLOR_ROLES = _BASE_COLOR_ROLES | set(_ROLE_FALLBACKS)
_STYLE_ROLES = _COLOR_ROLES - {"background", "foreground"}
_TOKEN_SELECTORS = {
    "comment": ".c, .c1, .cm, .cs, .hljs-comment, .hljs-quote",
    "punctuation": ".p, .hljs-punctuation",
    "muted": ".x, .go, .gt, .hljs-text",
    "builtin": ".nb, .ne, .hljs-built_in",
    "builtin-constant": ".kc, .hljs-literal",
    "keyword": ".k, .kn, .kp, .kr, .kt, .hljs-keyword",
    "declaration": ".kd",
    "function": ".nf, .hljs-title.function_, .hljs-function",
    "method": ".fm",
    "class": ".nc, .hljs-title.class_",
    "namespace": ".nn",
    "parameter": ".hljs-params",
    "attribute": ".na, .nl, .hljs-attr, .hljs-attribute, .hljs-property",
    "variable": ".nv, .vc, .vg, .vi, .hljs-variable",
    "library-variable": ".vm, .bp, .hljs-variable.language_",
    "constant": ".m, .no, .hljs-number, .hljs-symbol",
    "operator": ".o, .ow, .hljs-operator",
    "string": ".s, .s1, .s2, .sb, .sc, .sh, .hljs-string, .hljs-regexp",
    "error": ".err, .hljs-invalid",
}


def resolve_preset(preset_id: str) -> dict:
    """Return a validated copy of a Kit or bundled Pygments preset."""
    if preset_id.startswith("pygments:"):
        preset = _resolve_pygments_preset(preset_id.removeprefix("pygments:"))
    else:
        try:
            preset = PRESETS[preset_id]
        except KeyError as error:
            raise ValueError(f"Unknown syntax theme: {preset_id}") from error

    colors = preset.get("colors")
    if not isinstance(colors, dict) or any(
        not isinstance(color, str) or not _COLOR.fullmatch(color)
        for color in colors.values()
    ):
        raise ValueError(f"Syntax theme {preset_id} has invalid colors")

    resolved = validate_resolved_theme(
        {
            "id": preset["id"],
            "name": preset["name"],
            "colors": dict(colors),
            "styles": {key: list(value) for key, value in preset["styles"].items()},
        }
    )
    resolved.pop("revision")
    return resolved


def validate_resolved_theme(record: dict) -> dict:
    """Validate synced theme data without accepting executable CSS or code."""
    if not isinstance(record, dict):
        raise ValueError("Theme data must be an object.")
    preset_id = record.get("id")
    name = record.get("name")
    colors = record.get("colors")
    styles = record.get("styles")
    revision = record.get("revision", 0)
    if (
        not isinstance(preset_id, str)
        or not preset_id
        or len(preset_id) > 128
        or not isinstance(name, str)
        or not name
        or len(name) > 128
        or not isinstance(colors, dict)
        or not _BASE_COLOR_ROLES <= set(colors) <= _COLOR_ROLES
        or any(
            not isinstance(color, str) or not _COLOR.fullmatch(color)
            for color in colors.values()
        )
        or not isinstance(styles, dict)
        or set(styles) != {"bold", "italic"}
        or any(
            not isinstance(roles, list)
            or any(
                not isinstance(role, str) or role not in _STYLE_ROLES for role in roles
            )
            for roles in styles.values()
        )
        or type(revision) is not int
        or revision < 0
    ):
        raise ValueError("Theme data is invalid or unsupported.")
    colors = dict(colors)
    styles = {key: list(styles[key]) for key in ("bold", "italic")}
    # Fill new roles from older palettes without replacing their saved colors.
    for role, fallback in _ROLE_FALLBACKS.items():
        if role not in colors:
            colors[role] = colors[fallback]
            for roles in styles.values():
                if fallback in roles:
                    roles.append(role)
    return {
        "id": preset_id,
        "name": name,
        "colors": colors,
        "styles": {key: sorted(set(styles[key])) for key in ("bold", "italic")},
        "revision": revision,
    }


def available_themes() -> list[tuple[str, str]]:
    """Return stable identifiers and display names for bundled presets."""
    with _with_bundled_modules():
        styles = __import__(
            "pygments.styles", fromlist=["get_all_styles", "get_style_by_name"]
        )
        pygments_styles = [
            (f"pygments:{name}", _theme_display_name(styles.get_style_by_name(name)))
            for name in styles.get_all_styles()
        ]
    return sorted(
        [
            ("cassidy-dark", "Cassidy Dark"),
            *pygments_styles,
        ],
        key=lambda item: item[1].casefold(),
    )


def _theme_display_name(style) -> str:
    """Use the upstream style class name to retain word boundaries."""
    display_names = {
        "abap": "ABAP",
        "algol": "ALGOL",
        "algol_nu": "ALGOL Nu",
        "bw": "Black and White",
        "github-dark": "GitHub Dark",
        "inkpot": "Inkpot",
        "lilypond": "LilyPond",
        "rrt": "RRT",
        "sas": "SAS",
        "staroffice": "StarOffice",
    }
    if style.name in display_names:
        return display_names[style.name]
    name = style.__name__.removesuffix("Style")
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    return name.replace("_", " ").replace("Git Hub", "GitHub")


def _resolve_pygments_preset(style_name: str) -> dict:
    """Translate a bundled Pygments style into the shared token roles."""
    with _with_bundled_modules():
        styles = __import__("pygments.styles", fromlist=["get_style_by_name"])
        tokens = __import__("pygments.token", fromlist=["Token"])
        style = styles.get_style_by_name(style_name)
        token_roles = {
            "comment": tokens.Token.Comment,
            "punctuation": tokens.Token.Punctuation,
            "muted": tokens.Token.Text,
            "builtin": tokens.Token.Name.Builtin,
            "keyword": tokens.Token.Keyword,
            "function": tokens.Token.Name.Function,
            "class": tokens.Token.Name.Class,
            "attribute": tokens.Token.Name.Attribute,
            "constant": tokens.Token.Literal.Number,
            "operator": tokens.Token.Operator,
            "string": tokens.Token.Literal.String,
            "error": tokens.Token.Error,
        }
        default = style.style_for_token(tokens.Token.Name)
        foreground = _style_color(default.get("color"), "#c4c4c4")
        colors = {
            "background": _style_color(style.background_color, "#242424"),
            "foreground": foreground,
        }
        bold = []
        italic = []
        for role, token in token_roles.items():
            token_style = style.style_for_token(token)
            colors[role] = _style_color(token_style.get("color"), foreground)
            if token_style.get("bold"):
                bold.append(role)
            if token_style.get("italic"):
                italic.append(role)

    return {
        "id": f"pygments:{style_name}",
        "name": _theme_display_name(style),
        "colors": colors,
        "styles": {"bold": bold, "italic": italic},
    }


def _style_color(value: str | None, fallback: str) -> str:
    if isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{6}", value):
        return f"#{value}"

    if isinstance(value, str) and _COLOR.fullmatch(value):
        return value

    return fallback


def theme_preview_html(preset: dict) -> str:
    """Render the shared palette with CSS supported by Qt's rich text engine."""
    preset = validate_resolved_theme(preset)
    colors = preset["colors"]
    rules = [
        f"body {{ background-color: {colors['background']}; color: {colors['foreground']}; }}"
    ]
    for role, selectors in _TOKEN_SELECTORS.items():
        declarations = [f"color: {colors[role]};"]
        if role in preset["styles"]["bold"]:
            declarations.append("font-weight: 700;")
        if role in preset["styles"]["italic"]:
            declarations.append("font-style: italic;")
        rules.append(
            f'{selectors}, [data-global-kit-token="{role}"] {{ {" ".join(declarations)} }}'
        )
    return (
        f"<html><head><style>{' '.join(rules)}</style></head>"
        "<body><pre>"
        "<span class='kd'>def</span> <span class='nf'>highlight</span>():\n"
        "    <span class='c1'># a small preview</span>\n"
        "    <span class='k'>return</span> <span class='s1'>'Anki Global Kit'</span>"
        "</pre></body></html>"
    )


def _theme_variables_css(
    preset: dict, selector: str, *, use_shared_variables: bool = False
) -> str:
    """Keep all mode-dependent colors and font styles in custom properties."""
    colors = preset["colors"]
    syntax_variables = (
        _CASSIDY_DARK_SYNTAX_VARIABLES
        if use_shared_variables and preset["id"] == "cassidy-dark"
        else {}
    )
    css = [
        f"{selector} {{",
        f"  --agk-syntax-background: var(--syntax-{syntax_variables['background']});"
        if syntax_variables
        else f"  --agk-syntax-background: {colors['background']};",
        f"  --agk-syntax-foreground: var(--syntax-{syntax_variables['foreground']});"
        if syntax_variables
        else f"  --agk-syntax-foreground: {colors['foreground']};",
    ]
    for role, color in colors.items():
        if role not in {"background", "foreground"}:
            variable = syntax_variables.get(role)
            value = f"var(--syntax-{variable})" if variable else color
            css.append(f"  --agk-syntax-{role}: {value};")
    for role in _TOKEN_SELECTORS:
        if role in preset["styles"]["bold"]:
            css.append(f"  --agk-syntax-{role}-weight: 700;")

        if role in preset["styles"]["italic"]:
            css.append(f"  --agk-syntax-{role}-style: italic;")
    css.append("}")
    return "\n".join(css) + "\n"


def generate_theme_css(
    preset_id: str = "cassidy-dark", resolved: dict | None = None
) -> str:
    """Generate fallback variables and one shared set of block and token rules."""
    preset = (
        validate_resolved_theme(resolved)
        if resolved is not None
        else resolve_preset(preset_id)
    )
    css = [
        _theme_variables_css(
            preset, ":root,\nanki-editable", use_shared_variables=resolved is None
        ).rstrip()
    ]
    css.extend(
        [
            "",
            ".agk-code-block {",
            "  overflow-inline: auto;",
            "  background: var(--agk-syntax-background);",
            "  color: var(--agk-syntax-foreground);",
            "  white-space: pre;",
            "}",
            "",
            ":is(.agk-code-block, .syntax-highlights) :is(.n, .nx) {",
            "  color: var(--agk-syntax-foreground);",
            "}",
        ]
    )

    for role, selectors in _TOKEN_SELECTORS.items():
        declarations = [
            f"  color: var(--agk-syntax-{role});",
            f"  font-style: var(--agk-syntax-{role}-style, normal);",
            f"  font-weight: var(--agk-syntax-{role}-weight, 400);",
        ]
        css.extend(
            [
                "",
                f":is(.agk-code-block, .syntax-highlights) :is({selectors}),",
                f':is(.agk-code-block, .syntax-highlights) [data-global-kit-token="{role}"] {{',
                *declarations,
                "}",
            ]
        )

    return "\n".join(css) + "\n"


def generate_theme_pair_css(
    light: dict | None, dark: dict | None, *, editor: bool = False
) -> str:
    """Override fallback variables without repeating block or token rules."""
    light_theme = (
        validate_resolved_theme(light) if light else resolve_preset("cassidy-dark")
    )
    dark_theme = (
        validate_resolved_theme(dark) if dark else resolve_preset("cassidy-dark")
    )
    light_selector = ":root,\nanki-editable" if editor else ":root"
    dark_selector = ".nightMode,\n.night_mode,\n.night-mode"
    if editor:
        # Qt supports shadow host context selectors. Keep these out of card
        # stylesheets so clients without that selector retain their dark mode.
        dark_selector += (
            ",\n:host-context(.nightMode) anki-editable,\n"
            ":host-context(.night_mode) anki-editable,\n"
            ":host-context(.night-mode) anki-editable"
        )
    light_css = _theme_variables_css(light_theme, light_selector)
    dark_css = _theme_variables_css(dark_theme, dark_selector)
    return light_css + "\n" + dark_css
