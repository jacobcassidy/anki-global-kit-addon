"""Note Types table widgets, headers, spacing, and scroll geometry."""

from __future__ import annotations

from aqt.qt import (
    QCheckBox,
    QEvent,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPainterPath,
    QRectF,
    QRegion,
    QScrollArea,
    Qt,
    QWidget,
)

from ...configs.constants import NOTE_TYPES_ROW_PADDING, ZERO_MARGINS
from ...ui.theme import get_theme_color


class _RoundedScrollArea(QScrollArea):
    def __init__(self, parent: QWidget, radius: int) -> None:
        super().__init__(parent)
        self._corner_radius = radius
        self._header = None
        self._header_grid = None
        self._body_grid = None
        self._header_viewport = QWidget(self)
        self.viewport().installEventFilter(self)
        self.horizontalScrollBar().valueChanged.connect(self._update_header)
        self.horizontalScrollBar().rangeChanged.connect(self._update_header)
        self.verticalScrollBar().rangeChanged.connect(self._update_header)

    def set_table_header(
        self, header: QWidget, header_grid: QGridLayout, body_grid: QGridLayout
    ) -> None:
        self._header = header
        self._header_grid = header_grid
        self._body_grid = body_grid
        header.setParent(self._header_viewport)
        header.show()
        self.widget().installEventFilter(self)
        self.setViewportMargins(0, header.sizeHint().height(), 0, 0)
        self._update_viewport_mask()
        self._update_header()

    def _update_header(self, *_args) -> None:
        if self._header is None:
            return
        viewport_rect = self.viewport().geometry()
        header_height = self._header.sizeHint().height()
        self._header_viewport.setGeometry(
            viewport_rect.x(),
            viewport_rect.y() - header_height,
            viewport_rect.width(),
            header_height,
        )
        self._body_grid.activate()
        for column in range(self._body_grid.columnCount()):
            self._header_grid.setColumnMinimumWidth(
                column, self._body_grid.cellRect(0, column).width()
            )
        self._header_grid.activate()
        self._header.setGeometry(
            -self.horizontalScrollBar().value(),
            0,
            self.widget().width(),
            header_height,
        )
        self._header_grid.activate()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.viewport() and event.type() == QEvent.Type.Resize:
            self._update_viewport_mask()
        if event.type() == QEvent.Type.Resize:
            self._update_header()
        return super().eventFilter(watched, event)

    def _update_viewport_mask(self) -> None:
        viewport = self.viewport()
        path = QPainterPath()
        path.setFillRule(Qt.FillRule.WindingFill)
        path.addRoundedRect(
            QRectF(viewport.rect()),
            self._corner_radius,
            self._corner_radius,
        )
        if self._header is not None:
            # Only the bottom corners of the scrolling body are rounded.
            top_edge = QPainterPath()
            top_edge.addRect(QRectF(0, 0, viewport.width(), self._corner_radius))
            path = path.united(top_edge)
        viewport.setMask(QRegion(path.toFillPolygon().toPolygon()))


class NoteTypesTable:
    """Own the fixed headers and scrolling table used by the Note Types tab."""

    column_count = 9

    def __init__(self, parent: QWidget) -> None:
        self.scroll = _RoundedScrollArea(parent, radius=6)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setObjectName("noteTypesScroll")
        self.scroll.setStyleSheet(
            "QScrollArea#noteTypesScroll { "
            f"border: 1px solid {get_theme_color('BORDER_SUBTLE')}; "
            "border-radius: 6px; "
            "}"
        )
        scroll_viewport = self.scroll.viewport()
        scroll_viewport.setObjectName("noteTypesScrollViewport")
        scroll_viewport.setAutoFillBackground(False)
        scroll_viewport.setStyleSheet(
            "QWidget#noteTypesScrollViewport { "
            "border-top-left-radius: 0; border-top-right-radius: 0; "
            "border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; "
            "}"
        )
        self.body = QFrame(self.scroll)
        self.body.setFrameShape(QFrame.Shape.NoFrame)
        self.body.setObjectName("noteTypesTable")
        self.body.setStyleSheet(
            "QFrame#noteTypesTable { "
            f"background-color: {get_theme_color('CANVAS_ELEVATED')}; "
            "border-top-left-radius: 0; border-top-right-radius: 0; "
            "border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; "
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
        self.grid = QGridLayout(self.body)
        self.grid.setContentsMargins(*ZERO_MARGINS)
        self.grid.setSpacing(0)
        self.header = QFrame(self.scroll)
        self.header.setFrameShape(QFrame.Shape.NoFrame)
        self.header.setStyleSheet(self.body.styleSheet())
        self.header_grid = QGridLayout(self.header)
        self.header_grid.setContentsMargins(*ZERO_MARGINS)
        self.header_grid.setSpacing(0)

        checkbox_size = QCheckBox()
        checkbox_size.setContentsMargins(*ZERO_MARGINS)
        self.row_height = (
            max(checkbox_size.sizeHint().height(), self.body.fontMetrics().height())
            + 2 * NOTE_TYPES_ROW_PADDING
        )

    def _grid_for_row(self, row: int) -> tuple[QGridLayout, int]:
        if row < 3:
            return self.header_grid, row
        return self.grid, row - 3

    def add_horizontal_divider(self, row: int, column_span: int) -> None:
        divider = QFrame(self.body)
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Plain)
        divider.setLineWidth(1)
        divider.setFixedHeight(1)
        divider.setContentsMargins(*ZERO_MARGINS)
        divider.setStyleSheet(f"color: {get_theme_color('BORDER_SUBTLE')};")
        grid, grid_row = self._grid_for_row(row)
        grid.addWidget(divider, grid_row, 0, 1, column_span)

    def make_cell(
        self,
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
        cell = QWidget(self.body)
        cell.setObjectName(row_style)
        if corner is not None:
            cell.setProperty("tableCorner", corner)
        cell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        cell.setFixedHeight(self.row_height * row_span)
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
        grid, grid_row = self._grid_for_row(row)
        grid.addWidget(cell, grid_row, column, row_span, column_span)
        return cell

    def make_header_label(self, label: str, size_adjustment: int = 0) -> QLabel:
        heading = QLabel(label, self.body)
        heading_font = heading.font()
        heading_font.setBold(True)
        heading_font.setPointSize(
            max(1, heading_font.pointSize() - 4 + size_adjustment)
        )
        heading.setFont(heading_font)
        return heading

    def make_divider_cell(
        self,
        row: int,
        column: int,
        row_style: str,
        row_span: int = 1,
    ) -> None:
        cell = QWidget(self.body)
        cell.setObjectName(row_style)
        cell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        cell.setFixedHeight(self.row_height * row_span)
        cell_layout = QHBoxLayout(cell)
        cell_layout.setContentsMargins(*ZERO_MARGINS)
        cell_layout.setSpacing(0)
        divider = QFrame(cell)
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFrameShadow(QFrame.Shadow.Plain)
        divider.setLineWidth(1)
        divider.setStyleSheet(f"color: {get_theme_color('BORDER_SUBTLE')};")
        cell_layout.addWidget(divider, alignment=Qt.AlignmentFlag.AlignHCenter)
        grid, grid_row = self._grid_for_row(row)
        grid.addWidget(cell, grid_row, column, row_span, 1)

    def update_height(self) -> None:
        self.grid.activate()
        self.header_grid.activate()
        self.scroll.setMaximumHeight(
            self.grid.sizeHint().height()
            + self.header_grid.sizeHint().height()
            + 2 * self.scroll.frameWidth()
        )
        self.body.updateGeometry()
        self.scroll.updateGeometry()
        self.scroll._update_header()

    def clear(self) -> None:
        for grid in (self.header_grid, self.grid):
            for column in range(self.column_count):
                grid.setColumnMinimumWidth(column, 0)
                grid.setColumnStretch(column, 0)
            for index in range(grid.count() - 1, -1, -1):
                item = grid.takeAt(index)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
        for column in (2, 3, 4, 6, 7, 8):
            self.grid.setColumnStretch(column, 1)

    def add_headers(self) -> None:
        topic_spacer = self.make_header_label("\u200b", size_adjustment=2)
        topic_spacer.setStyleSheet("color: transparent;")
        topic_spacer.setAccessibleName("")
        self.make_cell(
            0,
            0,
            topic_spacer,
            "noteTypesHeaderCell",
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "topLeft",
            horizontal_padding=2 * NOTE_TYPES_ROW_PADDING,
        )
        self.make_cell(
            1,
            0,
            self.make_header_label("TOPIC"),
            "noteTypesHeaderCell",
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            horizontal_padding=2 * NOTE_TYPES_ROW_PADDING,
        )
        self.make_cell(
            0,
            2,
            self.make_header_label("ADVANCE", size_adjustment=2),
            "noteTypesHeaderCell",
            Qt.AlignmentFlag.AlignCenter,
            column_span=3,
        )
        self.make_cell(
            0,
            6,
            self.make_header_label("CLOZE", size_adjustment=2),
            "noteTypesHeaderCell",
            Qt.AlignmentFlag.AlignCenter,
            "topRight",
            column_span=3,
        )
        for column in (1, 5):
            self.make_divider_cell(0, column, "noteTypesHeaderCell", row_span=2)

        self.add_horizontal_divider(2, self.column_count)

        action_columns = {
            "CREATE": (2, 6),
            "REPLACE": (3, 7),
            "DELETE": (4, 8),
        }
        for action, columns in action_columns.items():
            for column in columns:
                heading = self.make_header_label(action)
                self.make_cell(
                    1,
                    column,
                    heading,
                    "noteTypesHeaderCell",
                    Qt.AlignmentFlag.AlignCenter,
                )

    def sync_column_widths(self) -> None:
        # Include heading labels in the body's minimum column widths so both
        # grids have enough room, even when the body contains only checkboxes.
        for column in range(self.column_count):
            for row in (0, 1):
                item = self.header_grid.itemAtPosition(row, column)
                if item is None:
                    continue
                _, _, _, column_span = self.header_grid.getItemPosition(
                    self.header_grid.indexOf(item.widget())
                )
                if column_span == 1:
                    self.grid.setColumnMinimumWidth(
                        column,
                        max(
                            self.grid.columnMinimumWidth(column),
                            item.sizeHint().width(),
                        ),
                    )

    def attach(self) -> None:
        """Attach the body and fixed header after the initial rows have been built."""
        self.scroll.setWidget(self.body)
        self.scroll.set_table_header(self.header, self.header_grid, self.grid)
        self.update_height()
