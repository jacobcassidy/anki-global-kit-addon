"""Build the read-only help tab."""

from aqt.qt import (
    QDesktopServices,
    QPushButton,
    QTextBrowser,
    QTextCursor,
    QUrl,
    QVBoxLayout,
    QWidget,
)

from ...configs.constants import ADDON_DIR, MARKDOWN_BLOCK_SPACING, SECTION_SPACING
from ...ui.widgets import add_button_row


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
    layout.addWidget(browser, 1)
    github_button = QPushButton("View Help on GitHub", tab)
    github_button.setAutoDefault(False)
    github_button.clicked.connect(
        lambda checked=False: QDesktopServices.openUrl(
            QUrl(
                "https://github.com/jacobcassidy/anki-global-kit-addon/"
                "blob/main/addon/HELP.md"
            )
        )
    )
    add_button_row(layout, github_button, align_right=False)
    return tab
