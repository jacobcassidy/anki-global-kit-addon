"""Pure theme validation and CSS generation."""

from __future__ import annotations

import re

from .custom_themes import PRESETS

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
    """Return a validated copy of a Kit-owned preset."""
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
