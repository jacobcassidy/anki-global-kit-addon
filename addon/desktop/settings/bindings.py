"""Read, restore, and compare settings controls."""

from ..config.defaults import DEFAULT_SETTINGS
from ..ui.shortcut_input import CardShortcutInput


def read_control_value(key: str, widget) -> object:
    if isinstance(widget, CardShortcutInput):
        return widget.stored_shortcut()
    if hasattr(widget, "get_value"):
        return widget.get_value()
    if hasattr(widget, "currentData"):
        return widget.currentData()
    if hasattr(widget, "value"):
        return widget.value()
    return widget.isChecked()


def restore_control_defaults(
    controls: dict,
    defaults: dict = DEFAULT_SETTINGS,
    *,
    theme_controls: dict | None = None,
) -> None:
    for key, widget in controls.items():
        if isinstance(widget, CardShortcutInput):
            widget.set_shortcut(defaults[key])
        elif hasattr(widget, "set_value"):
            widget.set_value(defaults[key])
        elif hasattr(widget, "setCurrentIndex"):
            index = widget.findData(defaults[key])
            widget.setCurrentIndex(max(index, 0))
        elif hasattr(widget, "setValue"):
            widget.setValue(defaults[key])
        else:
            widget.setChecked(defaults[key])
    for selector in (theme_controls or {}).values():
        index = selector.findData("cassidy-dark")
        selector.setCurrentIndex(max(index, 0))


def controls_match_defaults(
    controls: dict,
    defaults: dict = DEFAULT_SETTINGS,
    *,
    theme_controls: dict | None = None,
) -> bool:
    return all(
        read_control_value(key, widget) == defaults[key]
        for key, widget in controls.items()
    ) and all(
        selector.currentData() == "cassidy-dark"
        for selector in (theme_controls or {}).values()
    )
