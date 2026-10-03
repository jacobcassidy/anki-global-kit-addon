"""Access Anki's theme-aware colors from Desktop settings widgets."""

from aqt import colors
from aqt.theme import theme_manager


def get_theme_color(token_name: str, *fallback_names: str) -> str:
    """Return a semantic Anki color for the active theme.

    Anki 2.1.61 exposes light/dark token dictionaries but predates
    ``theme_manager.var()``, so select from the dictionary when needed.
    """
    token = next(
        (
            color
            for name in (token_name, *fallback_names)
            if (color := getattr(colors, name, None)) is not None
        ),
        None,
    )
    if token is None:
        names = ", ".join(repr(name) for name in (token_name, *fallback_names))
        raise AttributeError(f"Anki color tokens {names} are unavailable")

    color_getter = getattr(theme_manager, "var", None)
    if color_getter is not None:
        return color_getter(token)

    theme = "dark" if theme_manager.night_mode else "light"
    return token[theme]
