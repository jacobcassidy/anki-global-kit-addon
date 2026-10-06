"""Shared Markdown browser setup and document spacing for settings tabs."""

from aqt.qt import QTextBrowser, QTextCursor, QWidget

from ..configs.constants import MARKDOWN_BLOCK_SPACING


def make_markdown_browser(parent: QWidget, markdown: str) -> QTextBrowser:
    """Create a read-only browser with consistent heading, paragraph, and list spacing."""
    browser = QTextBrowser(parent)
    browser.setReadOnly(True)
    browser.setOpenExternalLinks(True)
    browser.document().setDocumentMargin(16)
    browser.document().setIndentWidth(24)
    browser.setMarkdown(markdown)
    block = browser.document().begin()
    first_heading = True
    while block.isValid():
        if block.blockFormat().headingLevel() > 0:
            block_format = block.blockFormat()
            block_format.setTopMargin(0 if first_heading else MARKDOWN_BLOCK_SPACING)
            cursor = QTextCursor(block)
            cursor.setBlockFormat(block_format)
            first_heading = False
        elif block.textList() is None:
            block_format = block.blockFormat()
            block_format.setBottomMargin(MARKDOWN_BLOCK_SPACING)
            QTextCursor(block).setBlockFormat(block_format)
        else:
            next_block = block.next()
            if not next_block.isValid() or next_block.textList() != block.textList():
                block_format = block.blockFormat()
                block_format.setBottomMargin(MARKDOWN_BLOCK_SPACING)
                QTextCursor(block).setBlockFormat(block_format)
        block = block.next()
    return browser
