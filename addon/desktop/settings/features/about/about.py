"""Build the add-on information and repository tab."""

from aqt.qt import (
    QDesktopServices,
    QPushButton,
    QTextBrowser,
    QTextCursor,
    QUrl,
    QVBoxLayout,
    QWidget,
)

from ...shared.constants import ADDON_DIR, JS_ASSET_NAME, SECTION_SPACING, VERSION
from ...ui.widgets import add_button_row


def build_about_tab(parent: QWidget) -> QWidget:
    tab = QWidget(parent)
    layout = QVBoxLayout(tab)
    layout.setSpacing(SECTION_SPACING)
    browser = QTextBrowser(tab)
    browser.setReadOnly(True)
    browser.setOpenExternalLinks(True)
    browser.document().setDocumentMargin(16)
    browser.document().setIndentWidth(24)
    about_path = ADDON_DIR / "ABOUT.md"
    about_markdown = (
        about_path.read_text(encoding="utf-8")
        if about_path.is_file()
        else "About text is not available in this add-on package."
    )
    about_markdown = about_markdown.replace("{version}", VERSION).replace(
        "{asset_name}", JS_ASSET_NAME
    )
    browser.setMarkdown(about_markdown)
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
    layout.addWidget(browser, 1)
    repository_button = QPushButton("View GitHub Repo", tab)
    repository_button.setAutoDefault(False)
    repository_button.clicked.connect(
        lambda checked=False: QDesktopServices.openUrl(
            QUrl("https://github.com/jacobcassidy/anki-global-kit-addon")
        )
    )
    add_button_row(layout, repository_button, align_right=False)
    layout.addStretch()
    return tab
