"""Reusable settings help indicators and their popup."""

from aqt.qt import QFrame, QLabel, QPoint, Qt, QTimer, QVBoxLayout, QWidget


class HelpPopup(QFrame):
    """A compact tooltip that stays open while the pointer is over it."""

    def __init__(self, owner: "HelpIndicator", description: str) -> None:
        super().__init__(
            owner,
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint,
        )
        self.owner = owner
        popup_layout = QVBoxLayout(self)
        popup_layout.setContentsMargins(8, 6, 8, 6)
        message = QLabel(description, self)
        message.setWordWrap(True)
        message.setMaximumWidth(464)
        popup_layout.addWidget(message)
        self.setMaximumWidth(560)
        self.adjustSize()

    def enterEvent(self, event) -> None:
        self.owner.hide_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.owner.hide_timer.start()
        super().leaveEvent(event)


class HelpIndicator(QLabel):
    """Show an immediate, wrapped help popup while hovered."""

    def __init__(self, setting_name: str, description: str, parent: QWidget) -> None:
        from .icons import install_help_indicator_icon

        super().__init__(parent)
        self.setAccessibleName(f"Help: {setting_name}")
        self.setCursor(Qt.CursorShape.WhatsThisCursor)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setContentsMargins(0, 0, 0, 0)
        install_help_indicator_icon(self)
        self.popup = HelpPopup(self, description)
        self.popup.adjustSize()

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(150)
        self.hide_timer.timeout.connect(self.popup.hide)

    def enterEvent(self, event) -> None:
        self.hide_timer.stop()
        self.popup.move(self.mapToGlobal(QPoint(0, self.height() + 4)))
        self.popup.show()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.hide_timer.start()
        super().leaveEvent(event)
