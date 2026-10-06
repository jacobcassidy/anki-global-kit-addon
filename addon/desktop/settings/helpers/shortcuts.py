"""Shortcut formatting, normalization, and warning rules."""

from aqt.utils import is_mac


def split_shortcut(shortcut: str) -> list[str]:
    """Split Qt shortcut names while retaining a literal plus as the final key."""
    if shortcut == "+":
        return ["+"]
    parts = shortcut.split("+")
    if shortcut.endswith("++"):
        parts[-2:] = ["+"]
    return parts


def format_shortcut(shortcut: str) -> str:
    """Format Qt Ctrl/Meta shortcut names for the current platform."""
    if not shortcut:
        return ""
    if shortcut.startswith("CodeBlock+"):
        return ("⌃⌘" if is_mac else "Ctrl+Alt+") + shortcut.split("+", 1)[1]
    parts = split_shortcut(shortcut)
    if is_mac:
        symbols = {
            "Ctrl": "⌘",
            "Meta": "⌃",
            "Alt": "⌥",
            "Shift": "⇧",
        }
        return "".join(symbols.get(part, part) for part in parts)
    return "+".join(parts)


def normalize_shortcut(shortcut: str) -> str:
    """Return a comparable shortcut string across platform-specific labels."""
    if not shortcut:
        return ""
    parts = split_shortcut(shortcut)
    key = parts.pop().upper()
    if shortcut.startswith("CodeBlock+"):
        modifiers = {"Ctrl", "Meta"} if is_mac else {"Ctrl", "Alt"}
    else:
        modifiers = set(parts)
    order = ("Ctrl", "Meta", "Alt", "Shift")
    return "+".join([*(part for part in order if part in modifiers), key])


def shortcut_has_required_modifier(shortcut: str) -> bool:
    modifiers = set(split_shortcut(normalize_shortcut(shortcut))[:-1])
    return bool(modifiers & {"Ctrl", "Alt", "Meta"})


def anki_shortcut_warnings() -> dict[str, str]:
    """Known built-in shortcuts worth warning users about if they overlap."""
    return {
        normalize_shortcut(shortcut): description
        for shortcut, description in (
            ("Ctrl+Enter", "Add a note"),
            ("Ctrl+Shift+;", "Open the Debug Console"),
            ("Ctrl+Alt+T", "Switch Browser between Cards and Notes"),
            *(
                (f"Ctrl+{number}", f"Flag a card with {number}")
                for number in range(1, 8)
            ),
        )
    }


def anki_editor_format_shortcut_warnings() -> dict[str, str]:
    """Built-in Anki editor formatting and list shortcuts."""
    return {
        normalize_shortcut(shortcut): description
        for shortcut, description in (
            ("Ctrl+B", "Bold"),
            ("Ctrl+I", "Italic"),
            ("Ctrl+U", "Underline"),
            ("Ctrl+Shift+X", "Strikethrough"),
            ("Ctrl+=", "Subscript"),
            ("Ctrl+Shift+=", "Superscript"),
            ("Ctrl+,", "Unordered list"),
            ("Ctrl+.", "Ordered list"),
            ("Ctrl+Shift+,", "Outdent list item"),
            ("Ctrl+Shift+.", "Indent list item"),
        )
    }


def reserved_shortcut_warnings() -> dict[str, str]:
    """Shortcuts reserved for common text editing actions."""
    return {
        normalize_shortcut(shortcut): description
        for shortcut, description in (
            ("Ctrl+C", "Copy"),
            ("Ctrl+V", "Paste"),
            ("Ctrl+X", "Cut"),
            ("Ctrl+A", "Select All"),
            ("Ctrl+Z", "Undo"),
            ("Ctrl+Y", "Redo"),
            ("Ctrl+Shift+Z", "Redo"),
            ("Ctrl+Insert", "Copy"),
            ("Shift+Insert", "Paste"),
            ("Shift+Delete", "Cut"),
        )
    }
