"""Reusable Qt controls and layout helpers for settings pages."""

from __future__ import annotations

from aqt.qt import (
    QApplication,
    QCheckBox,
    QEvent,
    QFrame,
    QHBoxLayout,
    QIcon,
    QLabel,
    QKeySequence,
    QPoint,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTimer,
    Qt,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import is_mac

from ..configs.constants import (
    COLOR_TRANSPARENT,
    NESTED_INDENT,
    SHORTCUT_MIN_WIDTH,
    SHORTCUT_MODIFIER_HINT,
    SHARED_ASSET_DIR,
    ZERO_MARGINS,
)
from .theme import get_theme_color
from ..helpers.shortcuts import (
    format_shortcut,
    normalize_shortcut,
    reserved_shortcut_warnings,
)


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


class CardShortcutInput(QPushButton):
    """Show a clickable shortcut label and capture keys until clicked outside."""

    _change_sequence = 0

    def __init__(self, shortcut: str, parent: QWidget) -> None:
        super().__init__(format_shortcut(shortcut) or "none", parent)
        self._capturing = False
        self._captured_tab = False
        self._capture_generation = 0
        self._transient_validation_message = ""
        self._persistent_validation_message = ""
        self._change_listeners = []
        self._change_order = 0
        self._text_dimmed = False
        self._shortcut_validator = None
        self.setCheckable(True)
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(SHORTCUT_MIN_WIDTH)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolTip("Click to record a shortcut. Click outside to finish.")
        button_bg = get_theme_color("BUTTON_BG", "CANVAS_ELEVATED")
        button_hover_bg = get_theme_color(
            "BUTTON_GRADIENT_START", "BUTTON_BG", "CANVAS_ELEVATED"
        )
        button_pressed_bg = get_theme_color(
            "BUTTON_GRADIENT_END", "BUTTON_BG", "CANVAS_ELEVATED"
        )
        button_disabled_bg = get_theme_color("BUTTON_DISABLED", "BUTTON_BG", "CANVAS")
        self._base_style_sheet = (
            f"QPushButton {{ text-align: right; padding: 0 4px; "
            f"border: 1px solid {COLOR_TRANSPARENT}; "
            "border-radius: 2px; "
            f"background: {button_bg}; }}"
            f"QPushButton:hover {{ background: {button_hover_bg}; }}"
            f"QPushButton:checked {{ "
            f"background: {get_theme_color('CANVAS_INSET')}; "
            f"border: 1px solid {COLOR_TRANSPARENT}; }}"
            f"QPushButton:pressed, QPushButton:checked:pressed "
            f"{{ background: {button_pressed_bg}; "
            f"border: 1px solid {COLOR_TRANSPARENT}; }}"
            f"QPushButton:focus {{ border: 1px solid "
            f"{get_theme_color('BORDER_FOCUS')}; }}"
            f"QPushButton:disabled {{ "
            f"background: {button_disabled_bg}; }}"
        )
        self._apply_text_style()
        self.toggled.connect(self._apply_text_style)
        self.clicked.connect(self._start_capture)
        application = QApplication.instance()
        if application:
            application.installEventFilter(self)

    def _start_capture(self) -> None:
        self._capturing = self.isChecked()
        if self._capturing:
            self._capture_generation += 1
            self.setFocus()
        else:
            self._clear_transient_validation()

    def _stop_capture(self) -> None:
        if not self._capturing:
            return
        self._capturing = False
        self.setChecked(False)
        self._clear_transient_validation()

    def _clear_transient_validation(self) -> None:
        generation = self._capture_generation
        QTimer.singleShot(0, lambda: self._clear_transient_if_current(generation))

    def _clear_transient_if_current(self, generation: int) -> None:
        if generation == self._capture_generation:
            self._set_validation_message("")

    def set_shortcut(self, shortcut: str) -> None:
        self.setText(format_shortcut(shortcut) or "none")
        self._mark_changed()
        self._notify_change_listeners()

    def _mark_changed(self) -> None:
        type(self)._change_sequence += 1
        self._change_order = type(self)._change_sequence

    def change_order(self) -> int:
        return self._change_order

    def set_text_dimmed(self, dimmed: bool) -> None:
        self._text_dimmed = dimmed
        self._apply_text_style()

    def _apply_text_style(self, *_args) -> None:
        if not hasattr(self, "_base_style_sheet"):
            return
        if self._text_dimmed or not self.isEnabled():
            color = get_theme_color("FG_DISABLED")
        elif self.isChecked():
            color = get_theme_color("FG_LINK")
        else:
            color = get_theme_color("FG")
        self.setStyleSheet(
            f"{self._base_style_sheet} QPushButton {{ color: {color}; "
            "font-weight: normal; }"
        )

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.EnabledChange:
            self._apply_text_style()

    def add_change_listener(self, callback) -> None:
        self._change_listeners.append(callback)
        callback()

    def _notify_change_listeners(self) -> None:
        self._apply_text_style()
        for callback in self._change_listeners:
            callback()

    def eventFilter(self, watched, event) -> bool:
        if self._capturing and watched is self:
            if self._captured_tab and event.type() == QEvent.Type.KeyPress:
                self._captured_tab = False
                event.accept()
                return True
            if event.type() == QEvent.Type.KeyRelease:
                self._captured_tab = False
            modified_tab = (
                event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab)
                and event.modifiers() & (
                    Qt.KeyboardModifier.ControlModifier
                    | Qt.KeyboardModifier.AltModifier
                    | Qt.KeyboardModifier.MetaModifier
                )
            ) if event.type() in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress) else False
            if modified_tab and event.type() == QEvent.Type.ShortcutOverride:
                # Capture the intact Tab combination before Qt focus traversal.
                self._captured_tab = True
                self.keyPressEvent(event)
                return True
            if modified_tab and event.type() == QEvent.Type.KeyPress:
                event.accept()
                return True
            if event.type() == QEvent.Type.FocusOut:
                self._stop_capture()
            elif event.type() == QEvent.Type.KeyPress and event.key() in (
                Qt.Key.Key_Tab,
                Qt.Key.Key_Backtab,
            ):
                self._stop_capture()
        if self._capturing and event.type() == QEvent.Type.MouseButtonPress:
            if watched is not self and not (
                isinstance(watched, QWidget) and self.isAncestorOf(watched)
            ):
                self._stop_capture()
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:
        if not self._capturing:
            super().keyPressEvent(event)
            return
        if event.key() == Qt.Key.Key_Escape:
            self._capturing = False
            self.setChecked(False)
            self._set_validation_message("")
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            self.setText("none")
            self._set_validation_message("")
            self._notify_change_listeners()
            event.accept()
            return

        modifier_keys = {
            Qt.Key.Key_Control,
            Qt.Key.Key_Alt,
            Qt.Key.Key_Shift,
            Qt.Key.Key_Meta,
        }
        if event.key() in modifier_keys:
            event.accept()
            return

        required_modifiers = (
            Qt.KeyboardModifier.ControlModifier
            | Qt.KeyboardModifier.AltModifier
            | Qt.KeyboardModifier.MetaModifier
        )
        if not event.modifiers() & required_modifiers:
            self._set_validation_message(
                f"Shortcuts must include at least one modifier key: {SHORTCUT_MODIFIER_HINT}."
            )
            event.accept()
            return

        modifiers = event.modifiers()
        parts = []
        # Store Qt's modifier names on every platform: Ctrl is Command on macOS,
        # while Meta is physical Control there.
        modifier_names = (
            (
                (Qt.KeyboardModifier.ControlModifier, "Ctrl"),
                (Qt.KeyboardModifier.AltModifier, "Alt"),
                (Qt.KeyboardModifier.ShiftModifier, "Shift"),
                (Qt.KeyboardModifier.MetaModifier, "Meta"),
            )
            if is_mac
            else (
                (Qt.KeyboardModifier.ControlModifier, "Ctrl"),
                (Qt.KeyboardModifier.AltModifier, "Alt"),
                (Qt.KeyboardModifier.ShiftModifier, "Shift"),
                (Qt.KeyboardModifier.MetaModifier, "Meta"),
            )
        )
        for modifier, name in modifier_names:
            if modifiers & modifier:
                parts.append(name)

        key_name = (
            "Tab" if event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab)
            else QKeySequence(event.key()).toString(QKeySequence.SequenceFormat.PortableText)
            or event.text().upper()
        )
        if key_name and key_name not in parts:
            parts.append(key_name)

        text = "+".join(parts)
        reserved_action = reserved_shortcut_warnings().get(normalize_shortcut(text))
        if reserved_action:
            self._set_validation_message(
                f"{format_shortcut(text)} "
                f"is reserved for {reserved_action}. "
                "Choose another shortcut."
            )
            event.accept()
            return
        if self._shortcut_validator is not None:
            message = self._shortcut_validator(text)
            if message:
                self._set_validation_message(message)
                event.accept()
                return
        if is_mac:
            symbols = {"Ctrl": "⌘", "Alt": "⌥", "Shift": "⇧", "Meta": "⌃"}
            text = "".join(symbols.get(part, part) for part in parts)
        self.setText(text)
        self._mark_changed()
        self._set_validation_message("")
        self._notify_change_listeners()
        event.accept()

    def set_validation_label(self, label: QLabel) -> None:
        self._validation_label = label
        self._render_validation_message()

    def set_persistent_validation_message(self, message: str) -> None:
        self._persistent_validation_message = message
        self._render_validation_message()

    def set_shortcut_validator(self, validator) -> None:
        self._shortcut_validator = validator

    def _set_validation_message(self, message: str) -> None:
        self._transient_validation_message = message
        self._render_validation_message()

    def _render_validation_message(self) -> None:
        label = getattr(self, "_validation_label", None)
        if label is None:
            return
        message = "\n".join(
            part
            for part in (
                self._persistent_validation_message,
                self._transient_validation_message,
            )
            if part
        )
        label.setText(message)
        label.setVisible(bool(message))

    def stored_shortcut(self) -> str:
        text = self.text().strip()
        if not text or text.lower() == "none":
            return ""
        if is_mac:
            symbols = {"⌃": "Meta", "⌥": "Alt", "⇧": "Shift", "⌘": "Ctrl"}
            modifiers = []
            while text and text[0] in symbols:
                modifiers.append(symbols[text[0]])
                text = text[1:]
        else:
            pieces = text.split("+")
            text = pieces.pop() if pieces else ""
            modifiers = [
                {"Shift": "Shift", "Alt": "Alt"}.get(part, part) for part in pieces
            ]
        key = "Tab" if text.lower() == "tab" else text.upper()
        modifier_set = set(modifiers)
        if (is_mac and modifier_set == {"Ctrl", "Meta"}) or (
            not is_mac and modifier_set == {"Ctrl", "Alt"}
        ):
            if key == "C":
                return "CodeBlock+C"
        order = ("Ctrl", "Alt", "Shift", "Meta")
        return "+".join([*(part for part in order if part in modifier_set), key])


class ResetShortcutLink(QLabel):
    """A small text link that resets one shortcut and disables at its default."""

    def __init__(
        self, parent: QWidget, shortcut_input: CardShortcutInput, default_shortcut: str
    ) -> None:
        super().__init__("RESET", parent)
        self.shortcut_input = shortcut_input
        self.default_shortcut = default_shortcut
        font = self.font()
        font.setPointSizeF(max(6.0, font.pointSizeF() - 4.0))
        self.setFont(font)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet(
            f"QLabel {{ color: {get_theme_color('FG_LINK')}; "
            "text-decoration: none; }"
            f"QLabel:hover {{ color: {get_theme_color('FG_LINK')}; "
            "text-decoration: none; }"
            f'QLabel[pressed="true"] '
            f"{{ color: {get_theme_color('FG_LINK')}; text-decoration: none; }}"
            f"QLabel:disabled {{ color: {get_theme_color('FG_DISABLED')}; }}"
        )
        self.setProperty("pressed", False)
        self.shortcut_input.add_change_listener(self._update_state)
        self._update_state()

    def _update_state(self) -> None:
        is_default = self.shortcut_input.stored_shortcut() == self.default_shortcut
        self.setEnabled(not is_default)
        self.setVisible(not is_default)
        self.setCursor(
            Qt.CursorShape.ArrowCursor
            if is_default
            else Qt.CursorShape.PointingHandCursor
        )
        self.setToolTip(
            "This shortcut already uses its default."
            if is_default
            else "Reset this shortcut to its default."
        )

    def _set_pressed(self, pressed: bool) -> None:
        self.setProperty("pressed", pressed)
        self.style().unpolish(self)
        self.style().polish(self)

    def _reset(self) -> None:
        if self.isEnabled():
            self.shortcut_input.set_shortcut(self.default_shortcut)

    def mousePressEvent(self, event) -> None:
        if self.isEnabled() and event.button() == Qt.MouseButton.LeftButton:
            self._set_pressed(True)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            was_pressed = self.property("pressed")
            self._set_pressed(False)
            if was_pressed and self.rect().contains(event.position().toPoint()):
                self._reset()
                event.accept()
                return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        if self.isEnabled() and event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
            Qt.Key.Key_Space,
        ):
            self._reset()
            event.accept()
            return
        super().keyPressEvent(event)


def make_reset_link(
    parent: QWidget, shortcut_input: CardShortcutInput, default_shortcut: str
) -> ResetShortcutLink:
    return ResetShortcutLink(parent, shortcut_input, default_shortcut)


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
        super().__init__(parent)
        self.setAccessibleName(f"Help: {setting_name}")
        self.setCursor(Qt.CursorShape.WhatsThisCursor)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setContentsMargins(0, 0, 0, 0)
        icon_pixmap = QIcon(str(SHARED_ASSET_DIR / "help-indicator.svg")).pixmap(16, 16)
        self.setPixmap(icon_pixmap)
        self.setFixedSize(icon_pixmap.size())
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
