"""Collection-scoped syntax highlighting preferences."""

PREFERENCES_KEY = "anki_global_kit.syntax_highlighting"
DECK_LANGUAGES_KEY = f"{PREFERENCES_KEY}.deck_languages"
THEMES_KEY = f"{PREFERENCES_KEY}.themes"
THEME_FORMAT_VERSION = 1


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


def get_themes(collection) -> dict[str, dict]:
    """Return validated collection-synced light and dark theme records."""
    value = collection.get_config(THEMES_KEY, {})
    if not isinstance(value, dict) or value.get("version") != THEME_FORMAT_VERSION:
        return {}

    result = {}
    for mode in ("light", "dark"):
        record = value.get(mode)
        if not isinstance(record, dict):
            continue
        try:
            from .themes import validate_resolved_theme

            result[mode] = validate_resolved_theme(record)
        except (TypeError, ValueError):
            continue
    return result


def set_themes(collection, themes: dict[str, dict]) -> None:
    """Store a complete validated light/dark theme pair in collection config."""
    if not isinstance(themes, dict) or set(themes) != {"light", "dark"}:
        raise ValueError("Both light and dark theme records are required.")

    from .themes import validate_resolved_theme

    validated = {}
    for mode in ("light", "dark"):
        record = validate_resolved_theme(themes[mode])
        previous = get_themes(collection).get(mode, {})
        record["revision"] = (
            max(int(previous.get("revision", 0)), int(record.get("revision", 0))) + 1
        )
        validated[mode] = record

    collection.set_config(THEMES_KEY, {"version": THEME_FORMAT_VERSION, **validated})
