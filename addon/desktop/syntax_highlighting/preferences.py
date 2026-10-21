"""Collection-scoped syntax highlighting preferences."""

PREFERENCES_KEY = "anki_global_kit.syntax_highlighting"
DECK_LANGUAGES_KEY = f"{PREFERENCES_KEY}.deck_languages"


def get_deck_languages(collection) -> dict[str, str]:
    """Read valid-shaped deck language preferences from collection config."""
    value = collection.get_config(DECK_LANGUAGES_KEY, {})

    if not isinstance(value, dict):
        return {}

    return {
        deck_id: language
        for deck_id, language in value.items()
        if isinstance(deck_id, str)
        and deck_id.isdecimal()
        and isinstance(language, str)
    }


def set_deck_language(collection, deck_id: int | str, language: str) -> None:
    """Update one deck while preserving other saved preferences."""
    if isinstance(deck_id, bool) or not str(deck_id).isdecimal():
        raise ValueError("A valid deck ID is required.")

    if not isinstance(language, str) or not language:
        raise ValueError("A canonical language alias is required.")

    preferences = get_deck_languages(collection)
    preferences[str(deck_id)] = language
    collection.set_config(DECK_LANGUAGES_KEY, preferences)
