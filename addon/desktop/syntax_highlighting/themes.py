"""Pure theme validation and CSS generation."""

from __future__ import annotations

import re

from .custom_themes import PRESETS
from .rendering import _with_bundled_modules

_COLOR = re.compile(r"#[0-9a-fA-F]{6}\Z")
_TOKEN_SELECTORS = {
    "comment": ".c, .c1, .cm, .cs, .hljs-comment, .hljs-quote",
    "punctuation": ".p, .hljs-punctuation",
    "muted": ".x, .go, .gt, .hljs-text",
    "builtin": ".nb, .bp, .hljs-built_in, .hljs-literal",
    "keyword": ".k, .kd, .kn, .kp, .kr, .kt, .hljs-keyword",
    "function": ".nf, .fm, .hljs-title.function_, .hljs-function",
    "class": ".nc, .nn, .hljs-title.class_",
    "attribute": ".na, .nl, .hljs-attr, .hljs-attribute",
    "constant": ".m, .no, .kc, .hljs-number, .hljs-symbol",
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

    return {
        "id": preset["id"],
        "name": preset["name"],
        "colors": dict(colors),
        "styles": {key: list(value) for key, value in preset["styles"].items()},
    }


def available_themes() -> list[tuple[str, str]]:
    """Return stable identifiers and display names for bundled presets."""
    with _with_bundled_modules():
        styles = __import__("pygments.styles", fromlist=["get_all_styles"])
        pygments_styles = styles.get_all_styles()
    return sorted(
        [
            ("cassidy-dark", "Cassidy Dark"),
            *[(f"pygments:{name}", name) for name in pygments_styles],
        ],
        key=lambda item: item[1].casefold(),
    )


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
        "name": style_name,
        "colors": colors,
        "styles": {"bold": bold, "italic": italic},
    }


def _style_color(value: str | None, fallback: str) -> str:
    if isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{6}", value):
        return f"#{value}"

    if isinstance(value, str) and _COLOR.fullmatch(value):
        return value

    return fallback


def generate_theme_css(preset_id: str = "cassidy-dark") -> str:
    """Generate deterministic token and block styling from a registered preset."""
    preset = resolve_preset(preset_id)
    colors = preset["colors"]
    css = [
        ":root,\nanki-editable {",
        f"  --agk-syntax-background: {colors['background']};",
        f"  --agk-syntax-foreground: {colors['foreground']};",
    ]
    for role, color in colors.items():
        if role not in {"background", "foreground"}:
            css.append(f"  --agk-syntax-{role}: {color};")
    css.extend(
        [
            "}",
            "",
            ".agk-code-block {",
            "  overflow-inline: auto;",
            "  background: var(--agk-syntax-background);",
            "  color: var(--agk-syntax-foreground);",
            "  white-space: pre;",
            "}",
        ]
    )

    for role, selectors in _TOKEN_SELECTORS.items():
        declarations = [f"  color: var(--agk-syntax-{role});"]
        if role in preset["styles"].get("bold", []):
            declarations.append("  font-weight: 700;")
        if role in preset["styles"].get("italic", []):
            declarations.append("  font-style: italic;")
        css.extend(["", f".agk-code-block :is({selectors}) {{", *declarations, "}"])

    return "\n".join(css) + "\n"
