"""Read, restore, and compare settings controls."""

from ..config.defaults import DEFAULT_SETTINGS
from ..ui.shortcut_input import CardShortcutInput


def read_control_value(key: str, widget) -> object:
    if isinstance(widget, CardShortcutInput):
        return widget.stored_shortcut()
    return widget.isChecked()


def restore_control_defaults(controls: dict, defaults: dict = DEFAULT_SETTINGS) -> None:
    for key, widget in controls.items():
        if isinstance(widget, CardShortcutInput):
            widget.set_shortcut(defaults[key])
        else:
            widget.setChecked(defaults[key])


def controls_match_defaults(controls: dict, defaults: dict = DEFAULT_SETTINGS) -> bool:
    return all(
        read_control_value(key, widget) == defaults[key]
        for key, widget in controls.items()
    )
