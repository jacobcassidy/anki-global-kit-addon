"""Build the read-only help tab."""

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


def build_help_tab(parent: QWidget) -> QWidget:
    tab = QWidget(parent)
    layout = QVBoxLayout(tab)
    layout.setSpacing(SECTION_SPACING)
    help_path = ADDON_DIR / "HELP.md"
    browser = make_markdown_browser(
        tab,
        help_path.read_text(encoding="utf-8")
        if help_path.is_file()
        else "Help content is not available in this add-on package.",
    )
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
