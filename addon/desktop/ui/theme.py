"""Access Anki's theme-aware colors from Desktop settings widgets."""

from aqt import colors
from aqt.theme import theme_manager


def get_theme_color(token_name: str) -> str:
    """Return a required semantic Anki color for the active theme."""
    return theme_manager.var(getattr(colors, token_name))
