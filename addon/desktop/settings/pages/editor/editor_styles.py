"""Settings section for default and custom Desktop editor stylesheets."""

from aqt.qt import QCheckBox, QGroupBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget
from aqt.utils import openFolder

from ....paths import USER_FILES_DIR
from ....ui.constants import NESTED_INDENT
from ....ui.layouts import add_checkbox_row

STYLESHEET_SETTINGS = (
    (
        "anki_editor_custom_fields_styles",
        "Enable custom editor fields stylesheet",
        "editor-fields.css",
        "Controls the appearance of text fields in the Desktop editor, including fonts, colors, spacing, and field borders.",
    ),
    (
        "anki_editor_custom_ui_styles",
        "Enable custom editor UI stylesheet",
        "editor-ui.css",
        "Controls the appearance of the Desktop editor interface, including the toolbar and editor window layout.",
    ),
)


def build_editor_styles_section(parent: QWidget, current_settings: dict):
    section = QGroupBox("Editor Styles", parent)
    layout = QVBoxLayout(section)
    controls = {}

    def view_stylesheet_folder() -> None:
        USER_FILES_DIR.mkdir(parents=True, exist_ok=True)
        openFolder(str(USER_FILES_DIR))

    for key, label, filename, description in STYLESHEET_SETTINGS:
        field_styles = filename == "editor-fields.css"
        default_key = (
            "anki_editor_default_fields_styles"
            if field_styles
            else "anki_editor_default_ui_styles"
        )
        default_name = "Editor Field" if field_styles else "Editor UI"
        default_styles = QCheckBox(
            f"Enable Anki Global Kit's default {default_name} styles", section
        )
        default_styles.setChecked(current_settings[default_key])
        add_checkbox_row(
            layout,
            default_styles,
            "Apply the kit's built-in field stylesheet and syntax theme styling. Custom field styles are controlled separately."
            if field_styles
            else "Apply the kit's built-in editor interface stylesheet. Custom UI styles are controlled separately.",
        )
        controls[default_key] = default_styles
        enabled = QCheckBox(label, section)
        enabled.setChecked(current_settings[key])
        name = "Editor Fields" if filename == "editor-fields.css" else "Editor UI"
        view_stylesheet = QPushButton(f"View custom {name} stylesheet", section)
        view_stylesheet.setAutoDefault(False)
        view_stylesheet.setToolTip(f"Open user_files, which contains {filename}.")
        view_stylesheet.clicked.connect(view_stylesheet_folder)
        row = QWidget(section)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(NESTED_INDENT, 0, 0, 0)
        row_layout.addWidget(view_stylesheet)
        row_layout.addStretch()
        add_checkbox_row(layout, enabled, description)
        layout.addWidget(row)
        controls[key] = enabled
    return section, controls
