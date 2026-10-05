"""Settings section for question fields and Markdown shortcuts."""

from dataclasses import dataclass

from aqt.qt import (
    QCheckBox,
    QGroupBox,
    QLabel,
    Qt,
    QVBoxLayout,
    QWidget,
)

from ...ui.widgets import CardShortcutInput, add_checkbox_row
from ...ui.shortcut_rows import build_shortcut_rows


MARKDOWN_SHORTCUT_DEFINITIONS = (
    ("card_input_markdown_bold_shortcut", "bold"),
    ("card_input_markdown_italic_shortcut", "italic"),
    ("card_input_markdown_strikethrough_shortcut", "strikethrough"),
    ("card_input_markdown_unordered_list_shortcut", "unordered list"),
    ("card_input_markdown_ordered_list_shortcut", "ordered list"),
    ("card_input_markdown_blockquote_shortcut", "blockquote"),
    ("card_input_markdown_code_block_shortcut", "code block"),
    ("card_input_markdown_inline_code_shortcut", "inline code"),
)


TAB_SHORTCUT_DEFINITIONS = (
    ("card_input_tab_indent_increase_shortcut", "increase indent"),
    ("card_input_tab_indent_decrease_shortcut", "decrease indent"),
)
SHORTCUT_DEFINITIONS = MARKDOWN_SHORTCUT_DEFINITIONS + TAB_SHORTCUT_DEFINITIONS


@dataclass
class CardFieldsSection:
    widget: QGroupBox
    controls: dict[str, QWidget]
    master_toggle: QCheckBox
    shortcut_inputs: dict[str, CardShortcutInput]
    shortcut_enabled: dict[str, QCheckBox]
    shortcut_option_checkboxes: dict[str, QCheckBox]
    reset_links: dict[str, QWidget]
    warning_labels: dict[str, QLabel]
    shortcut_masters: dict[str, QCheckBox]


def build_card_fields_section(parent: QWidget, current_settings: dict) -> CardFieldsSection:
    section = QGroupBox("Card Fields", parent)
    layout = QVBoxLayout(section)
    # Warning rows change size before the enclosing scroll area catches up.
    # Keep spare height below the controls during those layout passes.
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    master_toggle = QCheckBox("Enable Markdown shortcuts", section)
    master_toggle.setChecked(current_settings["card_input_markdown_shortcuts"])
    add_checkbox_row(
        layout,
        master_toggle,
        "Use keyboard shortcuts to apply Markdown formatting in question fields.",
    )

    shortcut_inputs = {}
    shortcut_enabled = {}
    reset_links = {}
    warning_labels = {}
    shortcut_masters = {}

    markdown_rows = build_shortcut_rows(section, master_toggle, MARKDOWN_SHORTCUT_DEFINITIONS, current_settings)
    layout.addWidget(markdown_rows.widget)
    tab_indentation = QCheckBox("Enable indentation shortcuts", section)
    tab_indentation.setChecked(current_settings["card_input_tab_indentation"])
    add_checkbox_row(
        layout,
        tab_indentation,
        "Indent the current or selected rows: four spaces for Python topics, two otherwise. Tab and Shift+Tab move focus.",
    )
    indentation_rows = build_shortcut_rows(section, tab_indentation, TAB_SHORTCUT_DEFINITIONS, current_settings)
    layout.addWidget(indentation_rows.widget)
    for rows in (markdown_rows, indentation_rows):
        shortcut_inputs.update(rows.shortcut_inputs)
        shortcut_enabled.update(rows.shortcut_enabled)
        reset_links.update(rows.reset_links)
        warning_labels.update(rows.warning_labels)
        shortcut_masters.update(rows.shortcut_masters)
    controls: dict[str, QWidget] = {
        "card_input_markdown_shortcuts": master_toggle,
        "card_input_tab_indentation": tab_indentation,
        **shortcut_inputs,
        **shortcut_enabled,
    }
    return CardFieldsSection(
        section,
        controls,
        master_toggle,
        shortcut_inputs,
        shortcut_enabled,
        {key: shortcut_enabled[f"{key}_enabled"] for key, _ in SHORTCUT_DEFINITIONS},
        reset_links,
        warning_labels,
        shortcut_masters,
    )
