"""Shared nested shortcut rows for card and editor settings."""

from dataclasses import dataclass
from aqt.qt import QCheckBox, QHBoxLayout, QLabel, QSizePolicy, Qt, QVBoxLayout, QWidget
from ..configs.constants import DEFAULT_SETTINGS, NESTED_INDENT, ZERO_MARGINS
from .theme import get_theme_color
from .widgets import CardShortcutInput, make_reset_link


@dataclass
class ShortcutRows:
    widget: QWidget
    shortcut_inputs: dict[str, CardShortcutInput]
    shortcut_enabled: dict[str, QCheckBox]
    reset_links: dict[str, QWidget]
    warning_labels: dict[str, QLabel]
    shortcut_masters: dict[str, QCheckBox]


def style_shortcut_option(checkbox: QCheckBox, *, inactive: bool) -> None:
    if inactive:
        color = get_theme_color("FG_DISABLED")
    elif getattr(checkbox, "shortcut_conflict", False):
        color = get_theme_color("FLAG_2", "FLAG_1", "FG_LINK")
    else:
        color = get_theme_color("FG")
    checkbox.setStyleSheet(f"QCheckBox {{ color: {color}; }}")


def build_shortcut_rows(section: QWidget, master: QCheckBox, definitions, current_settings: dict) -> ShortcutRows:
    shortcut_inputs = {}
    shortcut_enabled = {}
    reset_links = {}
    warning_labels = {}
    shortcut_masters = {}
    shortcut_rows = QWidget(section)
    shortcut_rows.setSizePolicy(
        QSizePolicy.Policy.Preferred,
        QSizePolicy.Policy.Maximum,
    )
    shortcut_rows_layout = QVBoxLayout(shortcut_rows)
    shortcut_rows_layout.setContentsMargins(NESTED_INDENT, 0, 0, 0)
    shortcut_rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    for key, label in definitions:
        row_container = QWidget(shortcut_rows)
        row_container.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum,
        )
        row_container_layout = QVBoxLayout(row_container)
        row_container_layout.setContentsMargins(*ZERO_MARGINS)
        row_container_layout.setSpacing(0)
        row_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        row_widget = QWidget(row_container)
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(*ZERO_MARGINS)
        enabled_key = f"{key}_enabled"
        checkbox = QCheckBox(f"Enable {label} shortcut", row_widget)
        checkbox.shortcut_conflict = False
        style_shortcut_option(checkbox, inactive=not master.isChecked())
        checkbox.setChecked(
            current_settings.get(enabled_key, DEFAULT_SETTINGS[enabled_key])
        )
        row.addWidget(checkbox)
        row.addStretch()

        shortcut_input = CardShortcutInput(
            current_settings.get(key, DEFAULT_SETTINGS[key]), row_widget,
            code_block_alias=key == "card_input_markdown_code_block_shortcut",
        )
        reset_link = make_reset_link(row_widget, shortcut_input, DEFAULT_SETTINGS[key])
        row.addWidget(reset_link)
        row.addWidget(shortcut_input)

        def set_row_enabled(
            enabled: bool,
            shortcut=shortcut_input,
            reset=reset_link,
            default=DEFAULT_SETTINGS[key],
        ) -> None:
            active = enabled and master.isChecked()
            shortcut.setEnabled(active)
            shortcut.set_text_dimmed(not active)
            reset.setEnabled(active and shortcut.stored_shortcut() != default)

        set_row_enabled(checkbox.isChecked())
        checkbox.toggled.connect(set_row_enabled)
        warning_label = QLabel(row_container)
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet(
            f"color: {get_theme_color('ACCENT_DANGER', 'FLAG_1', 'FG')};"
        )
        warning_label.hide()
        shortcut_input.set_validation_label(warning_label)
        row_container_layout.addWidget(row_widget)
        row_container_layout.addWidget(warning_label)
        shortcut_rows_layout.addWidget(row_container)
        shortcut_inputs[key] = shortcut_input
        shortcut_enabled[enabled_key] = checkbox
        reset_links[key] = reset_link
        warning_labels[key] = warning_label
        shortcut_masters[key] = master

    def set_shortcut_rows_enabled(enabled: bool) -> None:
        shortcut_rows.setEnabled(enabled)
        for key, _label in definitions:
            shortcut_input = shortcut_inputs[key]
            active = enabled and shortcut_enabled[f"{key}_enabled"].isChecked()
            shortcut_input.setEnabled(active)
            shortcut_input.set_text_dimmed(not active)
            style_shortcut_option(
                shortcut_enabled[f"{key}_enabled"], inactive=not enabled
            )
            reset_links[key].setEnabled(
                active and shortcut_input.stored_shortcut() != DEFAULT_SETTINGS[key]
            )

    master.toggled.connect(set_shortcut_rows_enabled)
    set_shortcut_rows_enabled(master.isChecked())

    return ShortcutRows(shortcut_rows, shortcut_inputs, shortcut_enabled, reset_links, warning_labels, shortcut_masters)
