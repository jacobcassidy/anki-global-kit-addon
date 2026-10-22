"""Settings section for the custom Desktop editor toolbar."""

from aqt.qt import QCheckBox, QGroupBox, QVBoxLayout, QWidget

from ....ui.constants import NESTED_INDENT
from ....ui.layouts import add_checkbox_row

BUTTON_SETTINGS = (
    (
        "anki_editor_syntax_highlighting_button",
        "Show Syntax Highlighting button",
        "Show Highlight Code, its language selector, and Code Block Options in the Desktop editor toolbar.",
    ),
    (
        "anki_editor_inline_code_button",
        "Show Inline Code button",
        "Add an Inline Code button for formatting selected text or starting an Inline Code span.",
    ),
    (
        "anki_editor_paste_markdown_as_html_button",
        "Show Convert Markdown to HTML button",
        "Convert selected Markdown text to formatted HTML, or insert converted clipboard text when nothing is selected.",
    ),
    ("anki_editor_blockquote_button", "Show Blockquote button", None),
)


def build_editor_toolbar_section(parent: QWidget, current_settings: dict):
    section = QGroupBox("Editor Toolbar", parent)
    layout = QVBoxLayout(section)
    enabled = QCheckBox("Show custom formatting toolbar", section)
    enabled.setChecked(current_settings["anki_editor_toolbar_enabled"])
    add_checkbox_row(
        layout,
        enabled,
        "Show Anki Global Kit's custom formatting buttons in the Desktop editor. Keyboard shortcuts work independently.",
    )
    button_container = QWidget(section)
    button_layout = QVBoxLayout(button_container)
    button_layout.setContentsMargins(NESTED_INDENT, 0, 0, 0)
    buttons = {}
    for key, label, description in BUTTON_SETTINGS:
        checkbox = QCheckBox(label, button_container)
        checkbox.setChecked(current_settings[key])
        add_checkbox_row(button_layout, checkbox, description)
        buttons[key] = checkbox
    layout.addWidget(button_container)
    button_container.setEnabled(enabled.isChecked())
    enabled.toggled.connect(button_container.setEnabled)
    return section, {"anki_editor_toolbar_enabled": enabled, **buttons}
