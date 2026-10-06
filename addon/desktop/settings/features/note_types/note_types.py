"""Compose the Note Types tab and coordinate checkbox and topic state."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from aqt import mw
from aqt.qt import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    Qt,
    QTimer,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import showWarning

from ...services.config import save_note_type_selections
from ...services.note_types import FORMATS, TOPICS
from ...ui.widgets import HelpIndicator
from ...configs.constants import (
    ADDON_PACKAGE_NAME,
    NOTE_TYPES_ROW_PADDING,
    ZERO_MARGINS,
)
from .actions import apply_selected_note_type_changes
from .table import NoteTypesTable


@dataclass
class NoteTypesTab:
    widget: QWidget
    collect_selections: Callable[[], dict[str, dict[str, bool]]]


def build_note_types_tab(parent: QWidget) -> NoteTypesTab:
    note_types_tab = QWidget(parent)
    note_types_layout = QVBoxLayout(note_types_tab)
    note_types_layout.setSpacing(8)
    note_types_layout.addWidget(
        QLabel("Select the note types you want to create or modify:")
    )
    table = NoteTypesTable(note_types_tab)

    addon_config = mw.addonManager.getConfig(ADDON_PACKAGE_NAME) or {}
    saved_selections = addon_config.get("note_type_selections", {})
    if not isinstance(saved_selections, dict):
        saved_selections = {}
    # Persist topic rows, but restore checked states from the collection only.
    # Pending Create selections belong to the open panel, not saved settings.
    saved_selections = {
        topic: {} for topic in saved_selections if isinstance(topic, str)
    }
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
        table.clear()
        note_type_checks.clear()
        overwrite_checks.clear()
        delete_checks.clear()
        table.add_headers()

        existing_names = (
            {item.name for item in mw.col.models.all_names_and_ids()}
            if mw.col is not None
            else set()
        )
        topics = (*TOPICS, *custom_topics)
        last_data_row = len(topics) + 2 + int(bool(custom_topics))
        custom_topics_start = 3 + len(TOPICS)
        if custom_topics:
            table.add_horizontal_divider(custom_topics_start, table.column_count)
        for index, topic in enumerate(topics):
            row = 3 + index
            if custom_topics and index >= len(TOPICS):
                row += 1
            row_style = "noteTypesAlternateCell" if index % 2 else "noteTypesNormalCell"
            topic_label = QLabel(topic, table.body)
            table.make_cell(
                row,
                0,
                topic_label,
                row_style,
                corner="bottomLeft" if row == last_data_row else None,
                horizontal_padding=2 * NOTE_TYPES_ROW_PADDING,
            )
            for column in (1, 5):
                table.make_divider_cell(row, column, row_style)
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
                checkbox = QCheckBox(table.body)
                exists = type_name in existing_names
                checkbox.setChecked(
                    exists or saved_topic_checks.get(card_format, False)
                )
                checkbox.setEnabled(not exists)
                checkbox.toggled.connect(update_note_types_button_state)
                table.make_cell(
                    row,
                    selected_column,
                    checkbox,
                    row_style,
                    Qt.AlignmentFlag.AlignCenter,
                )
                note_type_checks[topic][card_format] = checkbox

                overwrite_checkbox = QCheckBox(table.body)
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
                delete_checkbox = QCheckBox(table.body)
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
                is_custom_topic = topic in custom_topics
                can_delete = (exists and note_count == 0) or (
                    is_custom_topic and not exists
                )
                delete_control: QWidget = delete_checkbox
                if exists and note_count > 0:
                    delete_control = HelpIndicator(
                        "Delete",
                        "You must delete or move all notes to another note type "
                        "before this note type can be deleted.",
                        table.body,
                    )
                delete_checkbox.setChecked(
                    saved_topic_deletes.get(card_format, False) and can_delete
                )
                delete_checkbox.setEnabled(can_delete)
                if not exists:
                    delete_checkbox.setToolTip(
                        "Remove this uncreated custom topic"
                        if is_custom_topic
                        else "Available after this note type has been created"
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
                    lambda checked, create=checkbox, replace=overwrite_checkbox: (
                        (create.setChecked(False), replace.setChecked(False))
                        if checked
                        else None
                    )
                )
                delete_checkbox.toggled.connect(update_note_types_button_state)
                table.make_cell(
                    row,
                    overwrite_column,
                    overwrite_checkbox,
                    row_style,
                    Qt.AlignmentFlag.AlignCenter,
                )
                table.make_cell(
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

        table.sync_column_widths()
        if table.scroll.widget() is not None:
            table.update_height()
        update_note_types_button_state()

    def persist_note_type_selections() -> None:
        save_note_type_selections(collect_selections())

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
        saved_selections[topic] = {card_format: True for card_format in FORMATS}
        rebuild_note_types_grid()
        QTimer.singleShot(0, table.update_height)
        persist_note_type_selections()

    rebuild_note_types_grid()
    table.attach()
    note_types_layout.addWidget(table.scroll, 1)

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
        checked_deletions = {
            topic: {
                card_format
                for card_format, checkbox in formats.items()
                if checkbox.isChecked() and checkbox.isEnabled()
            }
            for topic, formats in delete_checks.items()
        }
        existing_names = (
            {item.name for item in mw.col.models.all_names_and_ids()}
            if mw.col is not None
            else set()
        )
        deletions = {
            topic: {
                card_format
                for card_format in formats
                if f"{topic} ({card_format})" in existing_names
            }
            for topic, formats in checked_deletions.items()
        }
        pending_custom_topic_removals = {
            topic
            for topic, formats in checked_deletions.items()
            if topic in custom_topics
            and any(
                f"{topic} ({card_format})" not in existing_names
                for card_format in formats
            )
        }
        has_model_changes = (
            any(
                card_format in FORMATS
                and f"{topic} ({card_format})" not in existing_names
                for topic, formats in selections.items()
                for card_format in formats
            )
            or any(formats for formats in overwrites.values())
            or any(formats for formats in deletions.values())
        )
        if has_model_changes:
            if not apply_selected_note_type_changes(selections, overwrites, deletions):
                return
        elif not pending_custom_topic_removals:
            apply_selected_note_type_changes(selections, overwrites, deletions)
            return

        for topic, formats in overwrites.items():
            for card_format in formats:
                overwrite_checks[topic][card_format].setChecked(False)

        deleted_types = {
            (topic, card_format)
            for topic, formats in checked_deletions.items()
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
        QTimer.singleShot(0, table.update_height)
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
        existing_names = (
            {item.name for item in mw.col.models.all_names_and_ids()}
            if mw.col is not None
            else set()
        )
        return {
            topic: {
                card_format: f"{topic} ({card_format})" in existing_names
                for card_format in formats
            }
            for topic, formats in note_type_checks.items()
        }

    return NoteTypesTab(note_types_tab, collect_selections)
