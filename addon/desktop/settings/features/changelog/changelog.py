"""Build the read-only changelog tab."""

from aqt.qt import (
    QDesktopServices,
    QPushButton,
    QUrl,
    QVBoxLayout,
    QWidget,
)

from ...configs.constants import ADDON_DIR, SECTION_SPACING
from ...ui.widgets import add_button_row
from ...ui.markdown import make_markdown_browser


def build_changelog_tab(parent: QWidget) -> QWidget:
    tab = QWidget(parent)
    layout = QVBoxLayout(tab)
    layout.setSpacing(SECTION_SPACING)
    changelog_path = ADDON_DIR / "CHANGELOG.md"
    if not changelog_path.is_file():
        changelog_path = ADDON_DIR.parent / "CHANGELOG.md"
    browser = make_markdown_browser(
        tab,
        changelog_path.read_text(encoding="utf-8")
        if changelog_path.is_file()
        else "No changelog is available in this add-on package.",
    )
    layout.addWidget(browser, 1)
    github_button = QPushButton("View Changelog on GitHub", tab)
    github_button.setAutoDefault(False)
    github_button.clicked.connect(
        lambda checked=False: QDesktopServices.openUrl(
            QUrl(
                "https://github.com/jacobcassidy/anki-global-kit-addon/"
                "blob/main/CHANGELOG.md"
            )
        )
    )
    add_button_row(layout, github_button, align_right=False)
    return tab
