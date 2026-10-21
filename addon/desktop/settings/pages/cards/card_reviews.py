"""Settings section for answer rendering and syntax highlighting."""

from aqt.qt import QCheckBox, QGroupBox, QVBoxLayout, QWidget

from ....ui.layouts import add_checkbox_row


def build_card_reviews_section(parent: QWidget, current_settings: dict):
    section = QGroupBox("Card Reviews", parent)
    layout = QVBoxLayout(section)
    markdown = QCheckBox("Enable Markdown to HTML rendering", section)
    markdown.setChecked(current_settings["card_review_markdown_rendering"])
    add_checkbox_row(
        layout,
        markdown,
        "Render Markdown as HTML in submitted answers, including formatting such as headings, lists, links, and code blocks.",
    )
    syntax = QCheckBox("Enable syntax highlighting for submitted answers", section)
    syntax.setChecked(current_settings["card_review_syntax_highlighting"])
    add_checkbox_row(
        layout,
        syntax,
        "Highlight supported code languages in submitted answers. This setting does not control the Desktop editor.",
    )
    return section, {
        "card_review_markdown_rendering": markdown,
        "card_review_syntax_highlighting": syntax,
    }
