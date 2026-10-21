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
    return section, {"card_review_markdown_rendering": markdown}
