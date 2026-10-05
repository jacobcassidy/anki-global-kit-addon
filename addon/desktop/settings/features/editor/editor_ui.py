"""Settings section for the Anki editor interface."""

from aqt.qt import QCheckBox, QGroupBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget
from aqt.utils import openFolder

from ...configs.constants import DEFAULT_SETTINGS, USER_FILES_DIR, ZERO_MARGINS
from ...ui.widgets import HelpIndicator, add_checkbox_row


def build_editor_ui_section(parent: QWidget, current_settings: dict):
    section = QGroupBox("Editor UI", parent)
    layout = QVBoxLayout(section)
    inline_code_button = QCheckBox("Show inline code button in editor toolbar", section)
    inline_code_button.setChecked(current_settings["anki_editor_inline_code_button"])
    add_checkbox_row(
        layout,
        inline_code_button,
        "Add an inline code button to the Desktop editor toolbar for formatting selected text or starting an inline code span.",
    )
    custom_styles = QCheckBox("Enable custom Editor UI stylesheet", section)
    custom_styles.setChecked(
        current_settings.get(
            "anki_editor_custom_ui_styles",
            DEFAULT_SETTINGS["anki_editor_custom_ui_styles"],
        )
    )
    view_stylesheet = QPushButton("View Stylesheet", section)
    view_stylesheet.setAutoDefault(False)
    view_stylesheet.setToolTip("Open user_files, which contains editor-ui.css.")

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
            "Controls the appearance of the Desktop editor interface, including the toolbar and editor window layout.",
            stylesheet_controls,
        )
    )
    add_checkbox_row(layout, custom_styles, trailing_widget=stylesheet_controls)
    return section, {
        "anki_editor_inline_code_button": inline_code_button,
        "anki_editor_custom_ui_styles": custom_styles,
    }
