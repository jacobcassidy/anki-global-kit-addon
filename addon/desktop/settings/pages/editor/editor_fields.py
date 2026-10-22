"""Settings section for Anki editor fields and formatting shortcuts."""

from dataclasses import dataclass

from aqt.qt import QCheckBox, QGroupBox, QHBoxLayout, QLabel, Qt, QVBoxLayout, QWidget

from ....config.defaults import DEFAULT_SETTINGS
from ....ui.constants import ZERO_MARGINS
from ....ui.layouts import add_checkbox_row
from ....ui.shortcut_input import CardShortcutInput, make_reset_link
from ....ui.shortcut_rows import ShortcutRows, build_shortcut_rows
from ....ui.theme import get_theme_color

EDITOR_SHORTCUT_DEFINITIONS = (
    ("anki_editor_blockquote_shortcut", "Blockquote"),
    ("anki_editor_convert_markdown_shortcut", "Convert Markdown"),
    ("anki_editor_inline_code_shortcut", "Inline Code"),
    ("anki_editor_syntax_highlighting_shortcut", "Syntax Highlighting"),
)
INDENTATION_SHORTCUT_DEFINITIONS = (
    ("anki_editor_indent_decrease_shortcut", "Decrease Indent"),
    ("anki_editor_indent_increase_shortcut", "Increase Indent"),
)


@dataclass
class EditorFieldsSection:
    widget: QGroupBox
    controls: dict[str, QWidget]
    indentation_rows: ShortcutRows
    action_shortcuts: dict[str, tuple[QCheckBox, CardShortcutInput]]


def build_editor_fields_section(
    parent: QWidget, current_settings: dict
) -> EditorFieldsSection:
    section = QGroupBox("Editor Fields", parent)
    layout = QVBoxLayout(section)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    action_shortcuts = {}
    definitions = sorted(
        (*EDITOR_SHORTCUT_DEFINITIONS, ("anki_editor_tab_indentation", "Indentation")),
        key=lambda item: item[1].casefold(),
    )
    for key, label in definitions:
        if key == "anki_editor_tab_indentation":
            tab_indentation = QCheckBox("Enable Indentation shortcuts", section)
            tab_indentation.setChecked(current_settings["anki_editor_tab_indentation"])
            add_checkbox_row(
                layout,
                tab_indentation,
                "⌘+Option+. indents and ⌘+Option+, outdents on macOS; use Ctrl+Alt+. and Ctrl+Alt+, on Windows and Linux. These shortcuts indent list items or change leading spaces in the current or selected rows. Tab and Shift+Tab move focus.",
            )
            indentation_rows = build_shortcut_rows(
                section,
                tab_indentation,
                INDENTATION_SHORTCUT_DEFINITIONS,
                current_settings,
            )
            layout.addWidget(indentation_rows.widget)
            continue

        enabled_key = f"{key}_enabled"
        enabled = QCheckBox(f"Enable {label} shortcut", section)
        enabled.setChecked(current_settings[enabled_key])
        input_widget = CardShortcutInput(current_settings[key], section)
        controls_widget = QWidget(section)
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(*ZERO_MARGINS)
        reset = make_reset_link(controls_widget, input_widget, DEFAULT_SETTINGS[key])
        controls_layout.addWidget(reset)
        controls_layout.addWidget(input_widget)
        validation = QLabel(section)
        validation.setWordWrap(True)
        validation.setStyleSheet(
            f"color: {get_theme_color('ACCENT_DANGER', 'FLAG_1', 'FG')};"
        )
        validation.hide()
        input_widget.set_validation_label(validation)

        def set_action_enabled(
            value,
            *,
            controls=controls_widget,
            field=input_widget,
            reset_link=reset,
            setting=key,
        ):
            controls.setEnabled(value)
            field.set_text_dimmed(not value)
            reset_link.setEnabled(
                value and field.stored_shortcut() != DEFAULT_SETTINGS[setting]
            )

        set_action_enabled(enabled.isChecked())
        enabled.toggled.connect(set_action_enabled)
        add_checkbox_row(
            layout,
            enabled,
            trailing_widget=controls_widget,
            validation_label=validation,
        )
        action_shortcuts[key] = (enabled, input_widget)

    return EditorFieldsSection(
        section,
        {
            **{f"{key}_enabled": pair[0] for key, pair in action_shortcuts.items()},
            **{key: pair[1] for key, pair in action_shortcuts.items()},
            "anki_editor_tab_indentation": tab_indentation,
            **indentation_rows.shortcut_inputs,
            **indentation_rows.shortcut_enabled,
        },
        indentation_rows,
        action_shortcuts,
    )
