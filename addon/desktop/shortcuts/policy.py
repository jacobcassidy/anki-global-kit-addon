"""Accepted shortcut values shared by Settings and runtime configuration."""

INDENTATION_SHORTCUT_SETTINGS = frozenset(
    f"{prefix}_{action}_shortcut"
    for prefix in ("card_input_tab_indent", "anki_editor_indent")
    for action in ("increase", "decrease")
)


def unsupported_shortcut_message(setting: str, shortcut: str) -> str | None:
    """Explain unsupported bindings without restricting other Tab actions."""
    if setting.startswith("anki_editor_") and shortcut.casefold().startswith(
        "codeblock+"
    ):
        return "CodeBlock aliases are only available for card shortcuts. Choose another shortcut."
    if setting in INDENTATION_SHORTCUT_SETTINGS and shortcut.rsplit("+", 1)[
        -1
    ].strip().casefold() in {"tab", "backtab"}:
        return (
            "Tab is reserved for focus navigation. Choose another indentation shortcut."
        )
    return None


def recover_shortcut(setting: str, shortcut: str, default: str) -> str:
    """Use the release default for unsupported saved bindings without saving."""
    return default if unsupported_shortcut_message(setting, shortcut) else shortcut
