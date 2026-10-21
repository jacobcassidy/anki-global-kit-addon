"""Coordinate add-on startup and assign hook registration ownership."""

from aqt import gui_hooks

from .editor.integration import initialize as initialize_editor
from .media.install import update_assets_for_profile
from .settings.dialog import initialize as initialize_settings
from .shortcuts.reviewer import initialize as initialize_reviewer

_initialized = False


def initialize() -> None:
    global _initialized
    if _initialized:
        return

    gui_hooks.profile_did_open.append(update_assets_for_profile)
    initialize_settings()
    initialize_editor()
    initialize_reviewer()
    _initialized = True
