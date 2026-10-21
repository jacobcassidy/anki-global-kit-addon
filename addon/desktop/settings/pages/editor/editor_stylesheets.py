"""Settings section for custom Desktop editor stylesheets."""

from aqt.qt import QCheckBox, QGroupBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget
from aqt.utils import openFolder

from ....paths import USER_FILES_DIR
from ....ui.constants import ZERO_MARGINS
from ....ui.help import HelpIndicator
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


def build_editor_stylesheets_section(parent: QWidget, current_settings: dict):
    section = QGroupBox("Editor Stylesheets", parent)
    layout = QVBoxLayout(section)
    controls = {}

    def view_stylesheet_folder() -> None:
        USER_FILES_DIR.mkdir(parents=True, exist_ok=True)
        openFolder(str(USER_FILES_DIR))

    for key, label, filename, description in STYLESHEET_SETTINGS:
        enabled = QCheckBox(label, section)
        enabled.setChecked(current_settings[key])
        view_stylesheet = QPushButton("View Stylesheet", section)
        view_stylesheet.setAutoDefault(False)
        view_stylesheet.setToolTip(f"Open user_files, which contains {filename}.")
        view_stylesheet.clicked.connect(view_stylesheet_folder)
        row = QWidget(section)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(*ZERO_MARGINS)
        row_layout.addWidget(view_stylesheet)
        row_layout.addWidget(HelpIndicator(label, description, row))
        add_checkbox_row(layout, enabled, trailing_widget=row)
        controls[key] = enabled
    return section, controls
