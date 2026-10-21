"""Policy for optional per-deck syntax highlighting language memory."""

from .preferences import get_deck_languages, set_deck_language


def remembered_language(
    collection, deck_id: int | str | None, enabled_languages: list[object]
) -> str | None:
    """Return a remembered language only when enabled and still available."""
    if deck_id is None or isinstance(deck_id, bool) or not str(deck_id).isdecimal():
        return None

    remembered = get_deck_languages(collection).get(str(deck_id))
    if remembered is None or remembered not in enabled_languages:
        return None

    return remembered


def remember_language(
    collection,
    deck_id: int | str | None,
    language: str,
    supported_languages: set[str],
) -> bool:
    """Persist an explicit, supported choice for a resolvable deck."""
    if (
        deck_id is None
        or isinstance(deck_id, bool)
        or not str(deck_id).isdecimal()
        or language not in supported_languages
    ):
        return False

    set_deck_language(collection, deck_id, language)
    return True
