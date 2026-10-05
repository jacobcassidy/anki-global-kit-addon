"""Anki editor settings tab and its feature sections."""

from dataclasses import dataclass

from aqt.qt import QVBoxLayout, QWidget

from ...configs.constants import SECTION_SPACING
from ...ui.widgets import make_scroll_area
from .editor_fields import EditorFieldsSection, build_editor_fields_section
from .editor_formatting import build_editor_formatting_section
from .editor_ui import build_editor_ui_section


@dataclass
class EditorTab:
    widget: QWidget
    controls: dict
    fields: EditorFieldsSection


def build_editor_tab(parent: QWidget, current_settings: dict) -> EditorTab:
    content = QWidget(parent)
    layout = QVBoxLayout(content)
    layout.setSpacing(SECTION_SPACING)

    fields = build_editor_fields_section(content, current_settings)
    formatting, formatting_controls = build_editor_formatting_section(
        content, current_settings
    )
    ui, ui_controls = build_editor_ui_section(content, current_settings)
    layout.addWidget(fields.widget)
    layout.addWidget(formatting)
    layout.addWidget(ui)
    layout.addStretch()

    return EditorTab(
        make_scroll_area(parent, content),
        {**fields.controls, **formatting_controls, **ui_controls},
        fields,
    )
