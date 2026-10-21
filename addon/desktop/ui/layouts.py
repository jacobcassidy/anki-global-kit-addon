"""Reusable Qt layout helpers."""

from aqt.qt import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    Qt,
    QVBoxLayout,
    QWidget,
)

from .constants import ZERO_MARGINS
from .help import HelpIndicator
from .theme import get_theme_color


def add_checkbox_row(
    parent_layout: QVBoxLayout,
    checkbox: QCheckBox,
    description: str | None = None,
    trailing_widget: QWidget | None = None,
    validation_label: QLabel | None = None,
) -> None:
    checkbox.setStyleSheet(
        f"QCheckBox:disabled {{ color: {get_theme_color('FG_DISABLED')}; }}"
    )
    row_widget = QWidget(parent_layout.parentWidget())
    if validation_label is not None:
        row_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum,
        )
    content_layout = QVBoxLayout(row_widget)
    content_layout.setContentsMargins(*ZERO_MARGINS)
    content_layout.setSpacing(0)
    content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    row = QHBoxLayout()
    row.setContentsMargins(*ZERO_MARGINS)
    content_layout.addLayout(row)
    row.addWidget(checkbox)
    if description is not None:
        row.addStretch()
        help_indicator = HelpIndicator(checkbox.text(), description, row_widget)
        row.addWidget(help_indicator)
    elif trailing_widget is None:
        row.addStretch()
    if trailing_widget is not None:
        row.addStretch()
        row.addWidget(trailing_widget)
    if validation_label is not None:
        validation_label.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum,
        )
        content_layout.addWidget(validation_label)
    parent_layout.addWidget(row_widget)


def add_button_row(
    parent_layout: QVBoxLayout, button: QPushButton, *, align_right: bool = True
) -> None:
    row_widget = QWidget(parent_layout.parentWidget())
    row = QHBoxLayout(row_widget)
    row.setContentsMargins(*ZERO_MARGINS)
    if align_right:
        row.addStretch()
        row.addWidget(button)
    else:
        row.addWidget(button)
        row.addStretch()
    parent_layout.addWidget(row_widget)


def make_scroll_area(parent: QWidget, content: QWidget) -> QScrollArea:
    scroll_area = QScrollArea(parent)
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.Shape.NoFrame)
    scroll_area.setWidget(content)
    scroll_area.setAutoFillBackground(False)
    scroll_area.viewport().setAutoFillBackground(False)
    content.setAutoFillBackground(False)
    return scroll_area
