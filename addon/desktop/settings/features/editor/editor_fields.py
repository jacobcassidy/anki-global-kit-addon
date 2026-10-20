"""Settings section for Anki editor fields and formatting shortcuts."""

from dataclasses import dataclass

from aqt.qt import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    Qt,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import openFolder

from ...configs.constants import DEFAULT_SETTINGS, USER_FILES_DIR, ZERO_MARGINS
from ...ui.shortcut_rows import ShortcutRows, build_shortcut_rows
from ...ui.theme import get_theme_color
from ...ui.widgets import (
    CardShortcutInput,
    HelpIndicator,
    add_checkbox_row,
    make_reset_link,
)

INDENTATION_SHORTCUT_DEFINITIONS = (
    ("anki_editor_indent_increase_shortcut", "increase indent"),
    ("anki_editor_indent_decrease_shortcut", "decrease indent"),
)


@dataclass
class EditorFieldsSection:
    widget: QGroupBox
    controls: dict[str, QWidget]
    shortcut_toggle: QCheckBox
    shortcut_input: CardShortcutInput
    reset_link: QWidget
    warning_label: QLabel
    indentation_rows: ShortcutRows
    action_shortcuts: dict[str, tuple[QCheckBox, CardShortcutInput]]


def build_editor_fields_section(
    parent: QWidget, current_settings: dict
) -> EditorFieldsSection:
    section = QGroupBox("Editor Fields", parent)
    layout = QVBoxLayout(section)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    shortcut_enabled = QCheckBox("Enable inline code shortcut", section)
    shortcut_enabled.setChecked(
        current_settings["anki_editor_inline_code_shortcut_enabled"]
    )
    shortcut_input = CardShortcutInput(
        current_settings["anki_editor_inline_code_shortcut"], section
    )
    shortcut_controls = QWidget(section)
    shortcut_controls_layout = QHBoxLayout(shortcut_controls)
    shortcut_controls_layout.setContentsMargins(*ZERO_MARGINS)
    reset_link = make_reset_link(
        shortcut_controls,
        shortcut_input,
        DEFAULT_SETTINGS["anki_editor_inline_code_shortcut"],
    )
    shortcut_controls_layout.addWidget(reset_link)
    shortcut_controls_layout.addWidget(shortcut_input)

    def set_shortcut_enabled(enabled: bool) -> None:
        shortcut_controls.setEnabled(enabled)
        shortcut_input.set_text_dimmed(not enabled)
        reset_link.setEnabled(
            enabled
            and shortcut_input.stored_shortcut()
            != DEFAULT_SETTINGS["anki_editor_inline_code_shortcut"]
        )

    set_shortcut_enabled(shortcut_enabled.isChecked())
    warning_label = QLabel(section)
    warning_label.setWordWrap(True)
    warning_label.setStyleSheet(
        f"color: {get_theme_color('ACCENT_DANGER', 'FLAG_1', 'FG')};"
    )
    warning_label.hide()
    shortcut_input.set_validation_label(warning_label)
    add_checkbox_row(
        layout,
        shortcut_enabled,
        trailing_widget=shortcut_controls,
        validation_label=warning_label,
    )
    shortcut_enabled.toggled.connect(set_shortcut_enabled)

    action_shortcuts = {}
    for key, label in (
        ("anki_editor_paste_html_shortcut", "Paste as HTML"),
        ("anki_editor_blockquote_shortcut", "Blockquote"),
    ):
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

    tab_indentation = QCheckBox("Enable indentation shortcuts", section)
    tab_indentation.setChecked(
        current_settings.get("anki_editor_tab_indentation", True)
    )
    add_checkbox_row(
        layout,
        tab_indentation,
        "⌘+Option+. indents and ⌘+Option+, outdents on macOS; use Ctrl+Alt+. and Ctrl+Alt+, on Windows and Linux. These shortcuts indent list items or change leading spaces in the current or selected rows. Tab and Shift+Tab move focus.",
    )
    indentation_rows = build_shortcut_rows(
        section, tab_indentation, INDENTATION_SHORTCUT_DEFINITIONS, current_settings
    )
    layout.addWidget(indentation_rows.widget)
    custom_styles = QCheckBox("Enable custom editor fields stylesheet", section)
    custom_styles.setChecked(
        current_settings.get(
            "anki_editor_custom_fields_styles",
            DEFAULT_SETTINGS["anki_editor_custom_fields_styles"],
        )
    )
    view_stylesheet = QPushButton("View Stylesheet", section)
    view_stylesheet.setAutoDefault(False)
    view_stylesheet.setToolTip("Open user_files, which contains editor-fields.css.")

    def view_stylesheet_folder() -> None:
        USER_FILES_DIR.mkdir(parents=True, exist_ok=True)
        openFolder(str(USER_FILES_DIR))

    view_stylesheet.clicked.connect(view_stylesheet_folder)
    stylesheet_controls = QWidget(section)
    stylesheet_controls_layout = QHBoxLayout(stylesheet_controls)
    stylesheet_controls_layout.setContentsMargins(*ZERO_MARGINS)
    stylesheet_controls_layout.addWidget(view_stylesheet)
    stylesheet_controls_layout.addWidget(
        HelpIndicator(
            custom_styles.text(),
            "Controls the appearance of text fields in the Desktop editor, including fonts, colors, spacing, and field borders.",
            stylesheet_controls,
        )
    )
    add_checkbox_row(layout, custom_styles, trailing_widget=stylesheet_controls)
    return EditorFieldsSection(
        section,
        {
            "anki_editor_inline_code_shortcut_enabled": shortcut_enabled,
            "anki_editor_inline_code_shortcut": shortcut_input,
            **{f"{key}_enabled": pair[0] for key, pair in action_shortcuts.items()},
            **{key: pair[1] for key, pair in action_shortcuts.items()},
            "anki_editor_tab_indentation": tab_indentation,
            "anki_editor_custom_fields_styles": custom_styles,
            **indentation_rows.shortcut_inputs,
            **indentation_rows.shortcut_enabled,
        },
        shortcut_enabled,
        shortcut_input,
        reset_link,
        warning_label,
        indentation_rows,
        action_shortcuts,
    )
