"""Settings tab for selecting and maintaining note type rows."""

from dataclasses import dataclass
from collections.abc import Callable

from aqt import mw
from aqt.qt import (
    QCheckBox,
    QDialog,
    QEvent,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPainterPath,
    QPushButton,
    QRectF,
    QRegion,
    QScrollArea,
    Qt,
    QTimer,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import showWarning

from ...config import save_note_type_selections
from ....note_types import FORMATS, TOPICS, create_selected_note_types
from ...widgets import HelpIndicator
from ...constants import (
    ADDON_PACKAGE_NAME,
    NOTE_TYPES_ROW_PADDING,
    ZERO_MARGINS,
)
from ...theme import get_theme_color


@dataclass
class NoteTypesTab:
    widget: QWidget
    collect_selections: Callable[[], dict[str, dict[str, bool]]]


class _RoundedScrollArea(QScrollArea):
    def __init__(self, parent: QWidget, radius: int) -> None:
        super().__init__(parent)
        self._corner_radius = radius
        self.viewport().installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.viewport() and event.type() == QEvent.Type.Resize:
            self._update_viewport_mask()
        return super().eventFilter(watched, event)

    def _update_viewport_mask(self) -> None:
        viewport = self.viewport()
        path = QPainterPath()
        path.addRoundedRect(
            QRectF(viewport.rect()),
            self._corner_radius,
            self._corner_radius,
        )
        viewport.setMask(QRegion(path.toFillPolygon().toPolygon()))


def build_note_types_tab(parent: QWidget) -> NoteTypesTab:
    note_types_tab = QWidget(parent)
    note_types_layout = QVBoxLayout(note_types_tab)
    note_types_layout.setSpacing(8)
    note_types_layout.addWidget(
        QLabel("Select the note types you want to create or modify:")
    )
    note_types_scroll = _RoundedScrollArea(note_types_tab, radius=6)
    note_types_scroll.setWidgetResizable(True)
    note_types_scroll.setFrameShape(QFrame.Shape.NoFrame)
    note_types_scroll.setObjectName("noteTypesScroll")
    note_types_scroll.setStyleSheet(
        "QScrollArea#noteTypesScroll { "
        f"border: 1px solid {get_theme_color('BORDER_SUBTLE')}; "
        "border-radius: 6px; "
        "}"
    )
    scroll_viewport = note_types_scroll.viewport()
    scroll_viewport.setObjectName("noteTypesScrollViewport")
    scroll_viewport.setAutoFillBackground(False)
    scroll_viewport.setStyleSheet(
        "QWidget#noteTypesScrollViewport { border-radius: 6px; }"
    )
    note_types_options = QFrame(note_types_scroll)
    note_types_options.setFrameShape(QFrame.Shape.NoFrame)
    note_types_options.setObjectName("noteTypesTable")
    note_types_options.setStyleSheet(
        "QFrame#noteTypesTable { "
        f"background-color: {get_theme_color('CANVAS_ELEVATED')}; "
        "border-radius: 6px; "
        "} "
        "QWidget#noteTypesHeaderCell { "
        f"background-color: {get_theme_color('CANVAS')}; "
        "} "
        "QWidget#noteTypesNormalCell { "
        f"background-color: {get_theme_color('CANVAS_ELEVATED')}; "
        "} "
        "QWidget#noteTypesAlternateCell { "
        f"background-color: {get_theme_color('CANVAS')}; "
        "} "
        "QWidget[tableCorner='topLeft'] { border-top-left-radius: 6px; } "
        "QWidget[tableCorner='topRight'] { border-top-right-radius: 6px; } "
        "QWidget[tableCorner='bottomLeft'] { border-bottom-left-radius: 6px; } "
        "QWidget[tableCorner='bottomRight'] { border-bottom-right-radius: 6px; }"
    )
    note_types_grid = QGridLayout(note_types_options)
    note_types_grid.setContentsMargins(*ZERO_MARGINS)
    note_types_grid.setSpacing(0)
    addon_config = mw.addonManager.getConfig(ADDON_PACKAGE_NAME) or {}
    saved_selections = addon_config.get("note_type_selections", {})
    if not isinstance(saved_selections, dict):
        saved_selections = {}
    custom_topics = sorted(
        (
            topic
            for topic in saved_selections
            if isinstance(topic, str) and topic not in TOPICS
        ),
        key=str.casefold,
    )
    note_type_checks: dict[str, dict[str, QCheckBox]] = {}
    overwrite_checks: dict[str, dict[str, QCheckBox]] = {}
    delete_checks: dict[str, dict[str, QCheckBox]] = {}
    checkbox_size = QCheckBox()
    checkbox_size.setContentsMargins(*ZERO_MARGINS)
    table_row_height = (
        max(
            checkbox_size.sizeHint().height(), note_types_options.fontMetrics().height()
        )
        + 2 * NOTE_TYPES_ROW_PADDING
    )
    note_types_button = QPushButton("Update Selected Note Types", note_types_tab)
    note_types_button.setAutoDefault(False)

    def update_note_types_button_state(*_args) -> None:
        has_selection = (
            any(
                checkbox.isChecked() and checkbox.isEnabled()
                for formats in note_type_checks.values()
                for checkbox in formats.values()
            )
            or any(
                checkbox.isChecked() and checkbox.isEnabled()
                for formats in overwrite_checks.values()
                for checkbox in formats.values()
            )
            or any(
                checkbox.isChecked() and checkbox.isEnabled()
                for formats in delete_checks.values()
                for checkbox in formats.values()
            )
        )
        note_types_button.setEnabled(has_selection)

    def add_note_type_horizontal_divider(row: int, column_span: int) -> None:
        divider = QFrame(note_types_options)
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Plain)
        divider.setLineWidth(1)
        divider.setFixedHeight(1)
        divider.setContentsMargins(*ZERO_MARGINS)
        divider.setStyleSheet(f"color: {get_theme_color('BORDER_SUBTLE')};")
        note_types_grid.addWidget(divider, row, 0, 1, column_span)

    def make_table_cell(
        row: int,
        column: int,
        content: QWidget,
        row_style: str,
        alignment=None,
        corner: str | None = None,
        row_span: int = 1,
        column_span: int = 1,
        horizontal_padding: int = NOTE_TYPES_ROW_PADDING,
        hidden_content: QWidget | None = None,
    ) -> QWidget:
        cell = QWidget(note_types_options)
        cell.setObjectName(row_style)
        if corner is not None:
            cell.setProperty("tableCorner", corner)
        cell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        cell.setFixedHeight(table_row_height * row_span)
        cell_layout = QHBoxLayout(cell)
        cell_layout.setContentsMargins(
            horizontal_padding,
            NOTE_TYPES_ROW_PADDING,
            horizontal_padding,
            NOTE_TYPES_ROW_PADDING,
        )
        cell_layout.setSpacing(0)
        if hidden_content is not None:
            hidden_content.hide()
            cell_layout.addWidget(hidden_content)
        content.setContentsMargins(*ZERO_MARGINS)
        if alignment is None:
            cell_layout.addWidget(content)
        else:
            cell_layout.addWidget(content, alignment=alignment)
        note_types_grid.addWidget(cell, row, column, row_span, column_span)
        return cell

    def make_header_label(label: str, size_adjustment: int = 0) -> QLabel:
        heading = QLabel(label, note_types_options)
        heading_font = heading.font()
        heading_font.setBold(True)
        heading_font.setPointSize(
            max(1, heading_font.pointSize() - 4 + size_adjustment)
        )
        heading.setFont(heading_font)
        return heading

    def make_divider_cell(
        row: int, column: int, row_style: str, row_span: int = 1
    ) -> None:
        cell = QWidget(note_types_options)
        cell.setObjectName(row_style)
        cell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        cell.setFixedHeight(table_row_height * row_span)
        cell_layout = QHBoxLayout(cell)
        cell_layout.setContentsMargins(*ZERO_MARGINS)
        cell_layout.setSpacing(0)
        divider = QFrame(cell)
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFrameShadow(QFrame.Shadow.Plain)
        divider.setLineWidth(1)
        divider.setStyleSheet(f"color: {get_theme_color('BORDER_SUBTLE')};")
        cell_layout.addWidget(divider, alignment=Qt.AlignmentFlag.AlignHCenter)
        note_types_grid.addWidget(cell, row, column, row_span, 1)

    def rebuild_note_types_grid() -> None:
        saved_checks = {
            topic: {name: checkbox.isChecked() for name, checkbox in formats.items()}
            for topic, formats in note_type_checks.items()
        }
        saved_overwrites = {
            topic: {name: checkbox.isChecked() for name, checkbox in formats.items()}
            for topic, formats in overwrite_checks.items()
        }
        saved_deletes = {
            topic: {name: checkbox.isChecked() for name, checkbox in formats.items()}
            for topic, formats in delete_checks.items()
        }
        for column in range(9):
            note_types_grid.setColumnMinimumWidth(column, 0)
            note_types_grid.setColumnStretch(column, 0)
        for column in (2, 3, 4, 6, 7, 8):
            note_types_grid.setColumnStretch(column, 1)
        for index in range(note_types_grid.count() - 1, -1, -1):
            item = note_types_grid.takeAt(index)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        note_type_checks.clear()
        overwrite_checks.clear()
        delete_checks.clear()
        column_count = 9
        topic_spacer = make_header_label("\u200b", size_adjustment=2)
        topic_spacer.setStyleSheet("color: transparent;")
        topic_spacer.setAccessibleName("")
        make_table_cell(
            0,
            0,
            topic_spacer,
            "noteTypesHeaderCell",
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "topLeft",
            horizontal_padding=2 * NOTE_TYPES_ROW_PADDING,
        )
        make_table_cell(
            1,
            0,
            make_header_label("TOPIC"),
            "noteTypesHeaderCell",
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            horizontal_padding=2 * NOTE_TYPES_ROW_PADDING,
        )
        make_table_cell(
            0,
            2,
            make_header_label("ADVANCE", size_adjustment=2),
            "noteTypesHeaderCell",
            Qt.AlignmentFlag.AlignCenter,
            column_span=3,
        )
        make_table_cell(
            0,
            6,
            make_header_label("CLOZE", size_adjustment=2),
            "noteTypesHeaderCell",
            Qt.AlignmentFlag.AlignCenter,
            "topRight",
            column_span=3,
        )
        for column in (1, 5):
            make_divider_cell(0, column, "noteTypesHeaderCell", row_span=2)

        add_note_type_horizontal_divider(2, column_count)

        action_columns = {
            "CREATE": (2, 6),
            "REPLACE": (3, 7),
            "DELETE": (4, 8),
        }
        for action, columns in action_columns.items():
            for column in columns:
                heading = make_header_label(action)
                make_table_cell(
                    1,
                    column,
                    heading,
                    "noteTypesHeaderCell",
                    Qt.AlignmentFlag.AlignCenter,
                )

        existing_names = (
            {item.name for item in mw.col.models.all_names_and_ids()}
            if mw.col is not None
            else set()
        )
        topics = (*TOPICS, *custom_topics)
        last_data_row = len(topics) + 2 + int(bool(custom_topics))
        custom_topics_start = 3 + len(TOPICS)
        if custom_topics:
            add_note_type_horizontal_divider(custom_topics_start, column_count)
        for index, topic in enumerate(topics):
            row = 3 + index
            if custom_topics and index >= len(TOPICS):
                row += 1
            row_style = "noteTypesAlternateCell" if index % 2 else "noteTypesNormalCell"
            topic_label = QLabel(topic, note_types_options)
            make_table_cell(
                row,
                0,
                topic_label,
                row_style,
                corner="bottomLeft" if row == last_data_row else None,
                horizontal_padding=2 * NOTE_TYPES_ROW_PADDING,
            )
            for column in (1, 5):
                make_divider_cell(row, column, row_style)
            note_type_checks[topic] = {}
            overwrite_checks[topic] = {}
            delete_checks[topic] = {}
            saved_topic_checks = saved_checks.get(
                topic, saved_selections.get(topic, {})
            )
            saved_topic_overwrites = saved_overwrites.get(topic, {})
            saved_topic_deletes = saved_deletes.get(topic, {})

            for format_index, card_format in enumerate(FORMATS):
                selected_column = 2 + format_index * 4
                overwrite_column = selected_column + 1
                delete_column = selected_column + 2
                type_name = f"{topic} ({card_format})"
                checkbox = QCheckBox(note_types_options)
                exists = type_name in existing_names
                checkbox.setChecked(
                    exists or saved_topic_checks.get(card_format, False)
                )
                checkbox.setEnabled(not exists)
                checkbox.toggled.connect(update_note_types_button_state)
                make_table_cell(
                    row,
                    selected_column,
                    checkbox,
                    row_style,
                    Qt.AlignmentFlag.AlignCenter,
                )
                note_type_checks[topic][card_format] = checkbox

                overwrite_checkbox = QCheckBox(note_types_options)
                overwrite_checkbox.setChecked(
                    saved_topic_overwrites.get(card_format, False)
                )
                overwrite_checkbox.setEnabled(exists)
                overwrite_checkbox.setToolTip(
                    "Replace this existing note type"
                    if exists
                    else "Available after this note type has been created"
                )
                overwrite_checkbox.toggled.connect(update_note_types_button_state)
                delete_checkbox = QCheckBox(note_types_options)
                notetype = (
                    mw.col.models.by_name(type_name)
                    if mw.col is not None and exists
                    else None
                )
                note_count = (
                    mw.col.models.use_count(notetype)
                    if mw.col is not None and notetype is not None
                    else 0
                )
                can_delete = exists and note_count == 0
                delete_control: QWidget = delete_checkbox
                if exists and note_count > 0:
                    delete_control = HelpIndicator(
                        "Delete",
                        "You must delete or move all cards to another note type "
                        "before this note type can be deleted.",
                        note_types_options,
                    )
                delete_checkbox.setChecked(
                    saved_topic_deletes.get(card_format, False) and can_delete
                )
                delete_checkbox.setEnabled(can_delete)
                if not exists:
                    delete_checkbox.setToolTip(
                        "Available after this note type has been created"
                    )
                elif note_count:
                    delete_checkbox.setToolTip(
                        "Move all notes to another note type in Anki before deleting"
                    )
                else:
                    delete_checkbox.setToolTip("Delete this empty note type")
                overwrite_checkbox.toggled.connect(
                    lambda checked, delete=delete_checkbox: (
                        delete.setChecked(False) if checked else None
                    )
                )
                delete_checkbox.toggled.connect(
                    lambda checked, replace=overwrite_checkbox: (
                        replace.setChecked(False) if checked else None
                    )
                )
                delete_checkbox.toggled.connect(update_note_types_button_state)
                make_table_cell(
                    row,
                    overwrite_column,
                    overwrite_checkbox,
                    row_style,
                    Qt.AlignmentFlag.AlignCenter,
                )
                make_table_cell(
                    row,
                    delete_column,
                    delete_control,
                    row_style,
                    Qt.AlignmentFlag.AlignCenter,
                    "bottomRight"
                    if row == last_data_row and delete_column == 8
                    else None,
                    hidden_content=delete_checkbox
                    if delete_control is not delete_checkbox
                    else None,
                )
                overwrite_checks[topic][card_format] = overwrite_checkbox
                delete_checks[topic][card_format] = delete_checkbox

        note_types_grid.activate()
        table_height = note_types_grid.sizeHint().height()
        if note_types_scroll.widget() is not None:
            note_types_scroll.setMaximumHeight(table_height)
            note_types_options.updateGeometry()
        update_note_types_button_state()

    def persist_note_type_selections() -> None:
        selections = {
            topic: {
                card_format: checkbox.isChecked()
                for card_format, checkbox in formats.items()
            }
            for topic, formats in note_type_checks.items()
        }
        save_note_type_selections(selections)

    def add_custom_topic() -> None:
        dialog = QInputDialog(parent)
        dialog.setWindowTitle("Add Topic")
        dialog.setInputMode(QInputDialog.InputMode.TextInput)
        dialog.setLabelText("Topic name:")
        topic_input = dialog.findChild(QLineEdit)
        if topic_input is not None:
            topic_input.setStyleSheet("QLineEdit { padding: 2px 4px; }")
        accepted = dialog.exec() == QDialog.DialogCode.Accepted
        topic = dialog.textValue()
        topic = topic.strip()
        if not accepted:
            return
        if not topic:
            showWarning("Enter a topic name before adding it.")
            return
        if any(
            existing.casefold() == topic.casefold()
            for existing in (*TOPICS, *custom_topics)
        ):
            showWarning("A topic with that name already exists.")
            return
        custom_topics.append(topic)
        custom_topics.sort(key=str.casefold)
        saved_selections[topic] = {card_format: False for card_format in FORMATS}
        rebuild_note_types_grid()
        QTimer.singleShot(0, update_note_types_table_height)
        persist_note_type_selections()

    def update_note_types_table_height() -> None:
        note_types_grid.activate()
        note_types_scroll.setMaximumHeight(note_types_grid.sizeHint().height())
        note_types_options.updateGeometry()
        note_types_scroll.updateGeometry()

    rebuild_note_types_grid()
    note_types_scroll.setWidget(note_types_options)
    note_types_scroll.setMaximumHeight(note_types_grid.sizeHint().height())
    note_types_layout.addWidget(note_types_scroll, 1)

    def create_note_types_from_panel(checked=False) -> None:
        selections = {
            topic: {
                card_format
                for card_format, checkbox in formats.items()
                if checkbox.isChecked()
                and (
                    checkbox.isEnabled()
                    or overwrite_checks[topic][card_format].isChecked()
                )
            }
            for topic, formats in note_type_checks.items()
        }
        overwrites = {
            topic: {
                card_format
                for card_format, checkbox in formats.items()
                if checkbox.isChecked()
            }
            for topic, formats in overwrite_checks.items()
        }
        deletions = {
            topic: {
                card_format
                for card_format, checkbox in formats.items()
                if checkbox.isChecked() and checkbox.isEnabled()
            }
            for topic, formats in delete_checks.items()
        }
        if not create_selected_note_types(selections, overwrites, deletions):
            return

        deleted_types = {
            (topic, card_format)
            for topic, formats in deletions.items()
            for card_format in formats
        }
        for topic, card_format in deleted_types:
            note_type_checks[topic][card_format].setChecked(False)
            delete_checks[topic][card_format].setChecked(False)
            if isinstance(saved_selections.get(topic), dict):
                saved_selections[topic][card_format] = False

        existing_names = (
            {item.name for item in mw.col.models.all_names_and_ids()}
            if mw.col is not None
            else set()
        )
        for topic in list(custom_topics):
            if (topic, "Advance") not in deleted_types and (
                topic,
                "Cloze",
            ) not in deleted_types:
                continue
            if all(
                f"{topic} ({card_format})" not in existing_names
                for card_format in FORMATS
            ):
                custom_topics.remove(topic)
                saved_selections.pop(topic, None)

        rebuild_note_types_grid()
        QTimer.singleShot(0, update_note_types_table_height)
        if deleted_types:
            persist_note_type_selections()

    note_types_button.clicked.connect(create_note_types_from_panel)
    add_button = QPushButton("+", note_types_tab)
    add_button.setAutoDefault(False)
    add_button.setFixedWidth(32)
    add_button.setToolTip("Add a custom topic row")
    add_button.clicked.connect(add_custom_topic)
    note_types_controls = QWidget(note_types_tab)
    note_types_controls_layout = QHBoxLayout(note_types_controls)
    note_types_controls_layout.setContentsMargins(*ZERO_MARGINS)
    note_types_controls_layout.addWidget(add_button)
    note_types_controls_layout.addStretch()
    note_types_controls_layout.addWidget(note_types_button)
    note_types_layout.addWidget(note_types_controls)

    def collect_selections() -> dict[str, dict[str, bool]]:
        return {
            topic: {
                card_format: checkbox.isChecked()
                for card_format, checkbox in formats.items()
            }
            for topic, formats in note_type_checks.items()
        }

    return NoteTypesTab(note_types_tab, collect_selections)
