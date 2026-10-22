"""Settings section for editor formatting behavior."""

from aqt.qt import QCheckBox, QGroupBox, QVBoxLayout, QWidget

from ....ui.layouts import add_checkbox_row


def build_editor_formatting_section(parent: QWidget, current_settings: dict):
    section = QGroupBox("Editor Formatting", parent)
    layout = QVBoxLayout(section)

    copy_source_html = QCheckBox("Copy selected source HTML", section)
    copy_source_html.setChecked(current_settings["anki_editor_copy_source_html"])
    add_checkbox_row(
        layout,
        copy_source_html,
        "When copying selected content from an editor field, include its HTML formatting on the clipboard alongside plain text.",
    )
    normalize_code_spaces = QCheckBox("Normalize spaces around inline code", section)
    normalize_code_spaces.setChecked(
        current_settings["anki_editor_normalize_code_spaces"]
    )
    add_checkbox_row(
        layout,
        normalize_code_spaces,
        "Replace non-breaking spaces adjacent to inline code with regular spaces so typing and spacing around code stays predictable.",
    )
    return section, {
        "anki_editor_copy_source_html": copy_source_html,
        "anki_editor_normalize_code_spaces": normalize_code_spaces,
    }
