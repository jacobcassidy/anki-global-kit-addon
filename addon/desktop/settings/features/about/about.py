"""Build the add-on information and repository tab."""

from aqt.qt import (
    QDesktopServices,
    QPushButton,
    QUrl,
    QVBoxLayout,
    QWidget,
)

from ...configs.constants import (
    ADDON_DIR,
    SECTION_SPACING,
    VERSION,
)
from ...configs.asset_manifest import JS_ASSET_NAME
from ...ui.widgets import add_button_row
from ...ui.markdown import make_markdown_browser


def build_about_tab(parent: QWidget) -> QWidget:
    tab = QWidget(parent)
    layout = QVBoxLayout(tab)
    layout.setSpacing(SECTION_SPACING)
    about_path = ADDON_DIR / "ABOUT.md"
    about_markdown = (
        about_path.read_text(encoding="utf-8")
        if about_path.is_file()
        else "About text is not available in this add-on package."
    )
    about_markdown = about_markdown.replace("{version}", VERSION).replace(
        "{asset_name}", JS_ASSET_NAME
    )
    browser = make_markdown_browser(tab, about_markdown)
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
