"""Syntax highlighting settings page."""

from aqt.qt import (
    QCheckBox,
    QColor,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    Qt,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ....syntax_highlighting.rendering import available_languages
from ....syntax_highlighting.themes import (
    available_themes,
    resolve_preset,
    theme_preview_html,
)
from ....ui.constants import SECTION_SPACING, ZERO_MARGINS
from ....ui.help import HelpIndicator
from ....ui.input_styles import style_settings_input
from ....ui.layouts import add_checkbox_row, make_scroll_area
from ....ui.lists import RoundedListWidget
from ....ui.theme import get_theme_color
from ..note_types.actions import enable_syntax_styling

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


class LanguageStatusDelegate(QStyledItemDelegate):
    """Keep native checkboxes and reserve a trailing column for Auto badges."""

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        # Let rows fit the viewport instead of widening for long language names.
        size.setWidth(0)
        size.setHeight(max(size.height(), option.fontMetrics.height() + 8))
        return size

    def paint(self, painter, option, index) -> None:
        option = QStyleOptionViewItem(option)
        self.initStyleOption(option, index)
        status = index.data(Qt.ItemDataRole.UserRole + 2) or ""
        badge_width = option.fontMetrics.horizontalAdvance("Auto") + 12
        status_width = badge_width + 8
        style = option.widget.style()
        text_rect = style.subElementRect(
            QStyle.SubElement.SE_ItemViewItemText, option, option.widget
        )
        option.text = option.fontMetrics.elidedText(
            option.text,
            Qt.TextElideMode.ElideRight,
            max(0, text_rect.width() - status_width),
        )
        # QStyledItemDelegate.paint() would restore the model's unelided text.
        style.drawControl(
            QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget
        )
        if not status:
            return
        badge_rect = option.rect.adjusted(0, 3, -4, -3)
        badge_rect.setLeft(badge_rect.right() - badge_width + 1)
        painter.save()
        painter.setPen(QColor(get_theme_color("BORDER_SUBTLE")))
        painter.setBrush(QColor(get_theme_color("BUTTON_BG", "CANVAS_ELEVATED")))
        painter.drawRoundedRect(badge_rect, 3, 3)
        painter.setPen(QColor(get_theme_color("FG_SUBTLE")))
        painter.drawText(
            badge_rect,
            Qt.AlignmentFlag.AlignCenter,
            status,
        )
        painter.restore()


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
    layout.setSpacing(SECTION_SPACING)
    languages_section = QGroupBox("Languages", page)
    language_layout = QVBoxLayout(languages_section)
    lines_section = QGroupBox("Lines", page)
    lines_layout = QVBoxLayout(lines_section)
    themes_section = QGroupBox("Themes", page)
    themes_layout = QVBoxLayout(themes_section)
    layout.addWidget(languages_section)
    layout.addWidget(lines_section)
    layout.addWidget(themes_section)

    def add_field_row(parent_layout, label: str, control: QWidget) -> None:
        row = QHBoxLayout()
        row.setContentsMargins(*ZERO_MARGINS)
        row.addWidget(QLabel(label, parent_layout.parentWidget()))
        row.addStretch()
        row.addWidget(control)
        parent_layout.addLayout(row)

    search = QLineEdit(languages_section)
    search.setPlaceholderText("Search languages and aliases")
    input_height = page.fontMetrics().height() + 6
    style_settings_input(search, input_height)
    language_layout.addWidget(search)
    groups_layout = QHBoxLayout()
    shown_box = QGroupBox("Shown In Editor", languages_section)
    other_box = QGroupBox("Other Languages", languages_section)
    shown_layout = QVBoxLayout(shown_box)
    other_layout = QVBoxLayout(other_box)
    shown_list = RoundedListWidget(shown_box)
    other_list = RoundedListWidget(other_box)
    for widget in (shown_list, other_list):
        widget.setMinimumHeight(160)
        widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        widget.setItemDelegate(LanguageStatusDelegate(widget))
    shown_layout.addWidget(shown_list)
    other_layout.addWidget(other_list)
    groups_layout.addWidget(shown_box)
    groups_layout.addWidget(other_box)
    language_layout.addLayout(groups_layout)
    language_note = QLabel(
        "All languages support saved highlighting on cards. "
        "Auto languages also highlight typed answers during review.",
        languages_section,
    )
    language_note.setWordWrap(True)
    language_layout.addWidget(language_note)

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
            review_label = "Auto" if alias in REVIEW_LANGUAGES else ""
            item = QListWidgetItem(name, widget)
            item.setData(Qt.ItemDataRole.UserRole, alias)
            item.setData(Qt.ItemDataRole.UserRole + 1, lexer_aliases)
            item.setData(Qt.ItemDataRole.UserRole + 2, review_label)
            item.setToolTip(
                f"{name}\nAutomatically highlights typed answers during review."
                if review_label
                else name
            )
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

    default_language = QComboBox(languages_section)
    default_language.setFixedWidth(220)
    desired_default = current_settings[
        "anki_editor_syntax_highlighting_default_language"
    ]

    def update_default_languages(*_args):
        selected = default_language.currentData()
        default_language.clear()
        default_language.addItem("None selected", "")
        for alias in sorted(checked, key=lambda value: rows[value][0].casefold()):
            default_language.addItem(rows[alias][0], alias)
        index = default_language.findData(selected or desired_default)
        default_language.setCurrentIndex(index if index >= 0 else 0)

    language_control = LanguageListControl(shown_list, other_list, checked, rebuild)
    language_control.add_change_listener(update_default_languages)
    update_default_languages()
    add_field_row(language_layout, "Default language", default_language)
    remember = QCheckBox("Remember last language per deck", languages_section)
    remember.setChecked(
        current_settings["anki_editor_syntax_highlighting_remember_language_per_deck"]
    )
    add_checkbox_row(language_layout, remember)

    line_numbers = QCheckBox("Show line numbers on new code blocks", lines_section)
    line_numbers.setChecked(
        current_settings["anki_editor_syntax_highlighting_line_numbers"]
    )
    add_checkbox_row(
        lines_layout,
        line_numbers,
        "New code blocks start at line 1. Use Code Block Options in the editor to change an individual block's starting line number.",
    )
    theme_controls = {}
    theme_preview_frame = QFrame(themes_section)
    theme_preview_frame.setObjectName("syntaxThemePreview")
    theme_preview_frame.setFixedHeight(150)
    preview_layout = QVBoxLayout(theme_preview_frame)
    preview_layout.setContentsMargins(6, 6, 6, 6)
    theme_preview = QTextBrowser(theme_preview_frame)
    theme_preview.setReadOnly(True)
    preview_layout.addWidget(theme_preview)
    choices = available_themes()
    for mode in ("light", "dark"):
        selector = QComboBox(themes_section)
        selector.setFixedWidth(220)
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
        add_field_row(themes_layout, f"Theme for {mode.title()} Mode", selector)
        theme_controls[mode] = selector

    preview_title = QLabel(themes_section)

    def update_theme_preview(mode="light", *_args):
        theme_id = theme_controls[mode].currentData()
        shared = (themes or {}).get(mode)
        preset = (
            shared if shared and shared["id"] == theme_id else resolve_preset(theme_id)
        )
        theme_preview_frame.setStyleSheet(
            "QFrame#syntaxThemePreview { "
            f"background-color: {preset['colors']['background']}; "
            f"color: {preset['colors']['foreground']}; "
            f"border: 1px solid {get_theme_color('BORDER_SUBTLE')}; "
            "border-radius: 6px; }"
        )
        theme_preview.setStyleSheet(
            "QTextBrowser { border: none; "
            f"background-color: {preset['colors']['background']}; "
            f"color: {preset['colors']['foreground']}; }}"
        )
        theme_preview.setHtml(theme_preview_html(preset))
        preview_title.setText(f"{mode.title()} Mode Theme Preview")

    for mode, selector in theme_controls.items():
        selector.currentIndexChanged.connect(
            lambda _index, mode=mode: update_theme_preview(mode)
        )
        selector.activated.connect(lambda _index, mode=mode: update_theme_preview(mode))
    update_theme_preview()
    themes_layout.addWidget(preview_title)
    themes_layout.addWidget(theme_preview_frame)
    publish_modes = set()
    publish_button = QPushButton(
        "Update Shared Theme from This Installation", themes_section
    )
    publish_button.setAutoDefault(False)
    publish_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    publication_help = (
        "Stage the selected local theme definitions for collection sync when you save."
        " This replaces the shared light and dark palettes with this installation's "
        "bundled definitions, even if the theme names have not changed. "
        "Other devices receive the updated palettes after syncing."
    )
    publish_button.setToolTip(publication_help)

    def stage_theme_publication():
        publish_modes.update(theme_controls)
        publish_button.setText("Shared Theme Update Staged")

    publish_button.clicked.connect(stage_theme_publication)
    publication_row = QHBoxLayout()
    publication_row.addWidget(publish_button)
    publication_row.addWidget(
        HelpIndicator("Update Shared Theme", publication_help, themes_section)
    )
    publication_row.addStretch()
    themes_layout.addLayout(publication_row)
    syntax_style_button = QPushButton("Enable Code Styling…", themes_section)
    syntax_style_button.setAutoDefault(False)
    syntax_style_button.setToolTip(
        "Add only the syntax stylesheet import to an existing note type"
    )
    syntax_style_button.clicked.connect(lambda: enable_syntax_styling(parent))
    syntax_style_row = QHBoxLayout()
    syntax_style_row.addWidget(syntax_style_button)
    syntax_style_row.addWidget(
        HelpIndicator(
            "Enable Code Styling",
            "Choose an existing note type and confirm to add the shared syntax "
            "highlighting stylesheet import. This lets saved Highlight Code blocks "
            "use your selected themes during card review. Notes, fields, card "
            "templates, and other styling are preserved. Sync afterward to apply "
            "the stylesheet on other devices.",
            themes_section,
        )
    )
    syntax_style_row.addStretch()
    themes_layout.addLayout(syntax_style_row)
    layout.addStretch()

    theme_snapshot = {
        mode: {
            "id": (themes or {}).get(mode, {}).get("id", "cassidy-dark"),
            "revision": (themes or {}).get(mode, {}).get("revision", 0),
        }
        for mode in ("light", "dark")
    }

    return (
        make_scroll_area(parent, page),
        {
            "anki_editor_syntax_highlighting_remember_language_per_deck": remember,
            "anki_editor_syntax_highlighting_line_numbers": line_numbers,
            "anki_editor_syntax_highlighting_languages": language_control,
            "anki_editor_syntax_highlighting_default_language": default_language,
        },
        theme_controls,
        theme_snapshot,
        publish_modes,
    )
