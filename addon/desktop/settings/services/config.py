"""Read and write add-on settings."""

from aqt import mw
from aqt.utils import is_mac

from ..configs.constants import ADDON_PACKAGE_NAME, DEFAULT_SETTINGS


def _read_settings(*, editor: bool) -> dict[str, object]:
    """Read known settings, using defaults for values with the wrong JSON type."""
    config = mw.addonManager.getConfig(ADDON_PACKAGE_NAME) or {}
    if not isinstance(config, dict):
        config = {}
    settings = {}
    for name, default in DEFAULT_SETTINGS.items():
        if name.startswith("anki_editor_") != editor:
            continue
        value = config.get(name, default)
        # Exact types keep numbers such as 0/1 from acting as boolean settings.
        settings[name] = value if type(value) is type(default) else default
    return settings


def get_settings() -> dict[str, object]:
    settings = _read_settings(editor=False)
    for name in ("card_input_tab_indent_increase_shortcut", "card_input_tab_indent_decrease_shortcut"):
        # These new settings already store Qt modifier names. Only translate
        # the portable physical-Control default, never swap a saved Meta key.
        settings[name] = settings[name].replace("Control+", "Meta+" if is_mac else "Ctrl+")
    return settings


def get_editor_settings() -> dict[str, object]:
    settings = _read_settings(editor=True)
    for name in ("anki_editor_indent_increase_shortcut", "anki_editor_indent_decrease_shortcut"):
        settings[name] = settings[name].replace("Control+", "Meta+" if is_mac else "Ctrl+")
    return settings


def save_note_type_selections(selections: dict[str, dict[str, bool]]) -> None:
    config = mw.addonManager.getConfig(ADDON_PACKAGE_NAME) or {}
    config["note_type_selections"] = selections
    mw.addonManager.writeConfig(ADDON_PACKAGE_NAME, config)


def write_settings(settings: dict[str, object]) -> None:
    mw.addonManager.writeConfig(ADDON_PACKAGE_NAME, settings)
