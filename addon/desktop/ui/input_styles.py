"""Style editable settings fields to match shortcut inputs."""

from aqt.qt import QWidget

from .constants import COLOR_TRANSPARENT
from .theme import get_theme_color


def style_settings_input(widget: QWidget, height: int) -> None:
    widget.setFixedHeight(height)
    widget.setStyleSheet(
        "QLineEdit, QSpinBox { padding: 0 4px; border-radius: 2px; "
        f"border: 1px solid {COLOR_TRANSPARENT}; "
        f"background: {get_theme_color('BUTTON_BG', 'CANVAS_ELEVATED')}; "
        f"color: {get_theme_color('FG')}; }}"
        "QLineEdit:focus, QSpinBox:focus { "
        f"border-color: {get_theme_color('BORDER_FOCUS')}; }}"
        "QLineEdit:disabled, QSpinBox:disabled { "
        f"color: {get_theme_color('FG_DISABLED')}; "
        f"background: {get_theme_color('BUTTON_DISABLED', 'BUTTON_BG', 'CANVAS')}; }}"
    )
