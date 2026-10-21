"""Syntax highlighting settings page."""

from aqt.qt import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    Qt,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ....config.defaults import DEFAULT_SETTINGS
from ....syntax_highlighting.rendering import available_languages
from ....syntax_highlighting.themes import available_themes, generate_theme_css
from ....ui.constants import ZERO_MARGINS
from ....ui.layouts import add_checkbox_row
from ....ui.shortcut_input import CardShortcutInput, make_reset_link

DEFAULT_LANGUAGES = {
    "bash",
    "css",
    "go",
    "html",
    "javascript",
    "json",
    "markdown",
    "php",
    "python",
    "ruby",
    "rust",
    "sql",
    "typescript",
}
REVIEW_LANGUAGES = {
    "python",
    "javascript",
    "typescript",
    "java",
    "c",
    "cpp",
    "csharp",
    "sql",
    "bash",
    "json",
    "ruby",
    "go",
    "rust",
    "php",
    "html",
    "css",
    "markdown",
    "powershell",
    "kotlin",
}


class LanguageListControl:
    """Settings binding for the two grouped language lists."""

    def __init__(self, shown_list, other_list, checked, rebuild):
        self.shown_list = shown_list
        self.other_list = other_list
        self.checked = checked
        self.rebuild = rebuild
        self.listeners = []

    def get_value(self):
        return sorted(self.checked)

    def set_value(self, value):
        self.checked.clear()
        self.checked.update(value)
        self.rebuild()
        for callback in self.listeners:
            callback()

    def add_change_listener(self, callback):
        self.listeners.append(callback)


def build_syntax_highlighting_tab(parent: QWidget, current_settings: dict, themes=None):
    page = QWidget(parent)
    layout = QVBoxLayout(page)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    enable_review = QCheckBox("Enable syntax highlighting for submitted answers", page)
    enable_review.setChecked(current_settings["card_review_syntax_highlighting"])
    add_checkbox_row(
        layout,
        enable_review,
        "Highlight supported code languages in submitted answers. This setting does not control the Desktop editor.",
    )
    button = QCheckBox("Show Highlight Code toolbar button", page)
    button.setChecked(current_settings["anki_editor_syntax_highlighting_button"])
    layout.addWidget(button)
    remember = QCheckBox("Remember last language per deck", page)
    remember.setChecked(
        current_settings["anki_editor_syntax_highlighting_remember_language_per_deck"]
    )
    layout.addWidget(remember)
    line_numbers = QCheckBox("Show line numbers on new code blocks", page)
    line_numbers.setChecked(
        current_settings["anki_editor_syntax_highlighting_line_numbers"]
    )
    layout.addWidget(line_numbers)
    start = QSpinBox(page)
    start.setRange(1, 1_000_000)
    start.setValue(
        current_settings["anki_editor_syntax_highlighting_line_number_start"]
    )
    layout.addWidget(QLabel("Starting line number", page))
    layout.addWidget(start)

    shortcut = QCheckBox("Enable Highlight Code shortcut", page)
    shortcut.setChecked(
        current_settings["anki_editor_syntax_highlighting_shortcut_enabled"]
    )
    layout.addWidget(shortcut)
    shortcut_input = CardShortcutInput(
        current_settings["anki_editor_syntax_highlighting_shortcut"], page
    )
    shortcut_row = QWidget(page)
    shortcut_row_layout = QHBoxLayout(shortcut_row)
    shortcut_row_layout.setContentsMargins(*ZERO_MARGINS)
    shortcut_reset = make_reset_link(
        shortcut_row,
        shortcut_input,
        DEFAULT_SETTINGS["anki_editor_syntax_highlighting_shortcut"],
    )
    shortcut_row_layout.addWidget(shortcut_reset)
    shortcut_row_layout.addWidget(shortcut_input)
    layout.addWidget(shortcut_row)
    shortcut_row.setEnabled(shortcut.isChecked())
    shortcut.toggled.connect(shortcut_row.setEnabled)

    search = QLineEdit(page)
    search.setPlaceholderText("Search languages and aliases")
    layout.addWidget(search)
    groups_layout = QHBoxLayout()
    shown_box = QGroupBox("Shown in editor", page)
    other_box = QGroupBox("Other languages", page)
    shown_layout = QVBoxLayout(shown_box)
    other_layout = QVBoxLayout(other_box)
    shown_list = QListWidget(shown_box)
    other_list = QListWidget(other_box)
    shown_layout.addWidget(shown_list)
    other_layout.addWidget(other_list)
    groups_layout.addWidget(shown_box)
    groups_layout.addWidget(other_box)
    layout.addLayout(groups_layout)

    rows = {
        alias: (name, aliases)
        for name, alias, aliases in available_languages()
        if alias
    }
    checked = set(current_settings["anki_editor_syntax_highlighting_languages"])
    checked.intersection_update(rows)

    def fill_list(widget: QListWidget, aliases: list[str]) -> None:
        widget.clear()
        for alias in aliases:
            name, lexer_aliases = rows[alias]
            review_label = (
                "Review supported" if alias in REVIEW_LANGUAGES else "Desktop only"
            )
            item = QListWidgetItem(f"{name} — {review_label}", widget)
            item.setData(Qt.ItemDataRole.UserRole, alias)
            item.setData(Qt.ItemDataRole.UserRole + 1, lexer_aliases)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if alias in checked else Qt.CheckState.Unchecked
            )

    changing = {"active": False}

    def rebuild() -> None:
        query = search.text().strip().casefold()
        shown = sorted(checked, key=lambda alias: rows[alias][0].casefold())
        other = sorted(set(rows) - checked, key=lambda alias: rows[alias][0].casefold())
        changing["active"] = True
        fill_list(shown_list, shown)
        fill_list(other_list, other)
        for widget in (shown_list, other_list):
            for index in range(widget.count()):
                item = widget.item(index)
                alias = item.data(Qt.ItemDataRole.UserRole)
                name, aliases = rows[alias]
                item.setHidden(
                    query not in name.casefold()
                    and not any(query in value.casefold() for value in aliases)
                )
        changing["active"] = False

    def language_changed(item: QListWidgetItem) -> None:
        if changing["active"]:
            return
        alias = item.data(Qt.ItemDataRole.UserRole)
        if item.checkState() == Qt.CheckState.Checked:
            checked.add(alias)
        else:
            checked.discard(alias)
        rebuild()
        for callback in language_control.listeners:
            callback()

    shown_list.itemChanged.connect(language_changed)
    other_list.itemChanged.connect(language_changed)
    search.textChanged.connect(lambda _text: rebuild())
    rebuild()

    default_language = QComboBox(page)
    desired_default = current_settings[
        "anki_editor_syntax_highlighting_default_language"
    ]

    def update_default_languages(*_args):
        selected = default_language.currentData()
        default_language.clear()
        default_language.addItem("No language selected", "")
        for alias in sorted(checked, key=lambda value: rows[value][0].casefold()):
            default_language.addItem(rows[alias][0], alias)
        index = default_language.findData(selected or desired_default)
        default_language.setCurrentIndex(index if index >= 0 else 0)

    language_control = LanguageListControl(shown_list, other_list, checked, rebuild)
    language_control.add_change_listener(update_default_languages)
    update_default_languages()
    layout.addWidget(QLabel("Default language", page))
    layout.addWidget(default_language)

    theme_controls = {}
    theme_preview = QTextBrowser(page)
    theme_preview.setReadOnly(True)
    theme_preview.setMaximumHeight(150)
    choices = available_themes()
    for mode in ("light", "dark"):
        selector = QComboBox(page)
        selected = (themes or {}).get(mode, {}).get("id", "cassidy-dark")
        for theme_id, name in choices:
            selector.addItem(name, theme_id)
        index = selector.findData(selected)
        if index < 0 and selected != "cassidy-dark":
            selector.addItem(
                f"{(themes or {}).get(mode, {}).get('name', selected)} (synced)",
                selected,
            )
            index = selector.findData(selected)
        selector.setCurrentIndex(
            index if index >= 0 else selector.findData("cassidy-dark")
        )
        layout.addWidget(QLabel(f"{mode.title()} theme", page))
        layout.addWidget(selector)
        theme_controls[mode] = selector

    def update_theme_preview(mode="light", *_args):
        theme_id = theme_controls[mode].currentData()
        shared = (themes or {}).get(mode)
        css = (
            generate_theme_css(theme_id, shared)
            if shared and shared["id"] == theme_id
            else generate_theme_css(theme_id)
        )
        sample = (
            "<div class='agk-code-block'><pre><span class='k'>def</span> "
            "<span class='nf'>highlight</span>():\n  "
            "<span class='c1'># a small preview</span>\n  "
            "<span class='k'>return</span> <span class='s1'>'Anki Global Kit'</span></pre></div>"
        )
        preview_class = "nightMode" if mode == "dark" else ""
        theme_preview.setHtml(
            f"<style>{css}</style><div class='{preview_class}'>{sample}</div>"
        )

    for mode, selector in theme_controls.items():
        selector.currentIndexChanged.connect(
            lambda _index, mode=mode: update_theme_preview(mode)
        )
    update_theme_preview()
    layout.addWidget(QLabel("Theme preview", page))
    layout.addWidget(theme_preview)
    publish_modes = set()
    publish_button = QPushButton("Update Shared Theme from This Installation", page)
    publish_button.setToolTip(
        "Stage the selected local theme definitions for collection sync when you save."
    )

    def stage_theme_publication():
        publish_modes.update(theme_controls)
        publish_button.setText("Shared Theme Update Staged")

    publish_button.clicked.connect(stage_theme_publication)
    layout.addWidget(publish_button)

    theme_snapshot = {
        mode: {
            "id": (themes or {}).get(mode, {}).get("id", "cassidy-dark"),
            "revision": (themes or {}).get(mode, {}).get("revision", 0),
        }
        for mode in ("light", "dark")
    }

    return (
        page,
        {
            "card_review_syntax_highlighting": enable_review,
            "anki_editor_syntax_highlighting_button": button,
            "anki_editor_syntax_highlighting_remember_language_per_deck": remember,
            "anki_editor_syntax_highlighting_line_numbers": line_numbers,
            "anki_editor_syntax_highlighting_line_number_start": start,
            "anki_editor_syntax_highlighting_shortcut_enabled": shortcut,
            "anki_editor_syntax_highlighting_shortcut": shortcut_input,
            "anki_editor_syntax_highlighting_languages": language_control,
            "anki_editor_syntax_highlighting_default_language": default_language,
        },
        theme_controls,
        theme_snapshot,
        publish_modes,
    )
