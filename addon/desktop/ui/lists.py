"""Rounded settings lists that match the note type table's presentation."""

from aqt.qt import QEvent, QFrame, QListWidget, QPainterPath, QRectF, QRegion

from .theme import get_theme_color


class RoundedListWidget(QListWidget):
    """Clip list rows inside a rounded border and alternate semantic backgrounds."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("roundedSettingsList")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAlternatingRowColors(True)
        self.setStyleSheet(
            "QListWidget#roundedSettingsList { "
            f"border: 1px solid {get_theme_color('BORDER_SUBTLE')}; "
            "border-radius: 6px; "
            f"background-color: {get_theme_color('CANVAS_ELEVATED')}; "
            f"alternate-background-color: {get_theme_color('CANVAS')}; }}"
        )
        viewport = self.viewport()
        assert viewport is not None
        viewport.installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:
        viewport = self.viewport()
        if (
            viewport is not None
            and watched is viewport
            and event.type() == QEvent.Type.Resize
        ):
            path = QPainterPath()
            path.addRoundedRect(QRectF(viewport.rect()), 5, 5)
            viewport.setMask(QRegion(path.toFillPolygon().toPolygon()))
        return super().eventFilter(watched, event)
