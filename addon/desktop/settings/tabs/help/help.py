"""Build the read-only help tab."""

from aqt.qt import QTextBrowser, QTextCursor, QVBoxLayout, QWidget

from ...constants import ADDON_DIR, SECTION_SPACING


def build_help_tab(parent: QWidget) -> QWidget:
    tab = QWidget(parent)
    layout = QVBoxLayout(tab)
    layout.setSpacing(SECTION_SPACING)
    browser = QTextBrowser(tab)
    browser.setReadOnly(True)
    browser.setOpenExternalLinks(True)
    browser.document().setDocumentMargin(16)
    browser.document().setIndentWidth(24)
    help_path = ADDON_DIR / "HELP.md"
    browser.setMarkdown(
        help_path.read_text(encoding="utf-8")
        if help_path.is_file()
        else "Help content is not available in this add-on package."
    )
    block = browser.document().begin()
    first_heading = True
    while block.isValid():
        if block.blockFormat().headingLevel() > 0:
            block_format = block.blockFormat()
            block_format.setTopMargin(0 if first_heading else 16)
            cursor = QTextCursor(block)
            cursor.setBlockFormat(block_format)
            first_heading = False
        block = block.next()
    layout.addWidget(browser)
    return tab
