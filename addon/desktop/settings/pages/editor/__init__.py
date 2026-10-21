"""Anki editor settings tab and its feature sections."""

from dataclasses import dataclass

from aqt.qt import QVBoxLayout, QWidget

from ....ui.constants import SECTION_SPACING
from ....ui.layouts import make_scroll_area
from .editor_fields import EditorFieldsSection, build_editor_fields_section
from .editor_styles import build_editor_styles_section
from .editor_text_handling import build_editor_text_handling_section
from .editor_toolbar import build_editor_toolbar_section


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
    text_handling, text_controls = build_editor_text_handling_section(
        content, current_settings
    )
    toolbar, toolbar_controls = build_editor_toolbar_section(content, current_settings)
    styles, style_controls = build_editor_styles_section(content, current_settings)
    layout.addWidget(fields.widget)
    layout.addWidget(text_handling)
    layout.addWidget(toolbar)
    layout.addWidget(styles)
    layout.addStretch()

    return EditorTab(
        make_scroll_area(parent, content),
        {
            **fields.controls,
            **text_controls,
            **style_controls,
            **toolbar_controls,
        },
        fields,
    )
