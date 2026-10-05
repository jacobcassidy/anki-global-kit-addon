"""Reviewer keyboard handling that must run before Qt menu shortcuts."""

from weakref import WeakSet

from aqt import gui_hooks, mw
from aqt.qt import QApplication, QEvent, QObject, Qt, sip
from aqt.reviewer import Reviewer
from aqt.utils import is_mac

_active_reviewer: Reviewer | None = None
_command_comma_handled = False
_shortcut_filter: "_PreferencesShortcutFilter | None" = None
_message_hook_installed = False
_preferences_was_enabled: bool | None = None
_editor_webviews = WeakSet()
_preview_input_webviews = WeakSet()


def _live_webviews(webviews):
    """A weak Python reference can outlive the wrapped Qt widget."""
    for webview in list(webviews):
        if sip.isdeleted(webview):
            webviews.discard(webview)
        else:
            yield webview


def _webview_contains_focus(webview, focused):
    return (
        webview is not None
        and focused is not None
        and not sip.isdeleted(webview)
        and not sip.isdeleted(focused)
        and (focused is webview or webview.isAncestorOf(focused))
    )


def _input_owns_command_comma() -> bool:
    if not (
        is_mac
        and _command_comma_handled
        and _active_reviewer is mw.reviewer
        and mw.state == "review"
    ):
        return False
    focused_widget = QApplication.focusWidget()
    webview = mw.reviewer.web
    return _webview_contains_focus(webview, focused_widget)


def _sync_preferences_action(*_args) -> None:
    global _preferences_was_enabled
    if not is_mac:
        return
    action = getattr(getattr(mw, "form", None), "actionPreferences", None)
    if action is None:
        return
    if _input_owns_command_comma():
        if _preferences_was_enabled is None:
            _preferences_was_enabled = action.isEnabled()
            # Update the native menu before Cocoa processes a key equivalent.
            action.setEnabled(False)
    elif _preferences_was_enabled is not None:
        action.setEnabled(_preferences_was_enabled)
        _preferences_was_enabled = None


def _refresh_question_focus(*_args) -> None:
    """Ask the DOM again after Qt focus returns without a textarea focus event."""
    _sync_preferences_action()
    focused_widget = QApplication.focusWidget()
    for webview in _live_webviews(_preview_input_webviews):
        if _webview_contains_focus(webview, focused_widget):
            webview.eval("globalThis.ankiGlobalKitReportQuestionFocus?.();")
    if mw.state != "review":
        return
    webview = mw.reviewer.web
    if _webview_contains_focus(webview, focused_widget):
        webview.eval("globalThis.ankiGlobalKitReportQuestionFocus?.();")


def _register_editor_tab_shortcut(shortcuts, editor) -> None:
    _register_editor_webview(editor)


def _register_editor_webview(editor) -> None:
    if editor.web is not None and not sip.isdeleted(editor.web):
        _editor_webviews.add(editor.web)


def _card_tab_action(event, settings):
    """Match customized Tab combinations before Qt consumes their keypress."""
    control = Qt.KeyboardModifier.MetaModifier if is_mac else Qt.KeyboardModifier.ControlModifier
    modifiers = {
        "Ctrl": Qt.KeyboardModifier.ControlModifier,
        "Meta": Qt.KeyboardModifier.MetaModifier,
        "Control": control,
        "Alt": Qt.KeyboardModifier.AltModifier,
        "Shift": Qt.KeyboardModifier.ShiftModifier,
    }
    for action, default in (("increase", "Alt+Tab"), ("decrease", "Control+Tab")):
        key = f"card_input_tab_indent_{action}_shortcut"
        if not settings.get(f"{key}_enabled", True):
            continue
        shortcut = settings.get(key, default)
        parts = shortcut.split("+")
        if parts.pop().lower() != "tab":
            continue
        expected = event.modifiers() & ~event.modifiers()
        if not parts or any(part not in modifiers for part in parts):
            continue
        for part in parts:
            expected |= modifiers[part]
        if event.modifiers() == expected:
            return "globalThis.ankiGlobalKitIndentQuestion?.();" if action == "increase" else "globalThis.ankiGlobalKitUnindentQuestion?.();"
    return None


def _tab_shortcut_target(event):
    """Only claim Control+Tab in webviews whose indentation setting is enabled."""
    from .settings import get_editor_settings, get_settings

    focused = QApplication.focusWidget()
    if focused is None:
        return None
    for webview in _live_webviews(_editor_webviews):
        if _webview_contains_focus(webview, focused):
            control = Qt.KeyboardModifier.MetaModifier if is_mac else Qt.KeyboardModifier.ControlModifier
            if get_editor_settings()["anki_editor_tab_indentation"] and event.modifiers() == control:
                return webview, "globalThis.ankiGlobalKitEditor?.unindent();"
            return None
    for webview in _live_webviews(_preview_input_webviews):
        if _webview_contains_focus(webview, focused):
            settings = get_settings()
            script = _card_tab_action(event, settings)
            if settings["card_input_tab_indentation"] and script:
                return webview, script
            return None
    if mw.state == "review" and _active_reviewer is mw.reviewer:
        webview = mw.reviewer.web
        if _webview_contains_focus(webview, focused):
            settings = get_settings()
            script = _card_tab_action(event, settings)
            if settings["card_input_tab_indentation"] and script:
                return webview, script
    return None


class _PreferencesShortcutFilter(QObject):
    """Route native Control+Tab and let the card input handle Command+Comma."""

    def eventFilter(self, watched, event) -> bool:
        if (
            event.type() in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress)
            and event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab)
            and (target := _tab_shortcut_target(event)) is not None
        ):
            # Chromium can lose the Tab key in the subsequent native KeyPress.
            # Handle the intact ShortcutOverride before focus traversal wins.
            event.accept()
            if event.type() == QEvent.Type.ShortcutOverride:
                target[0].eval(target[1])
            return True
        if (
            event.type() == QEvent.Type.ShortcutOverride
            and _input_owns_command_comma()
            and event.key() == Qt.Key.Key_Comma
        ):
            # Qt maps physical Command to ControlModifier on macOS, while
            # browser KeyboardEvent maps it to metaKey.
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                event.accept()
                # Stop the receiver from ignoring our ShortcutOverride. Qt will
                # deliver the subsequent KeyPress normally to the webview.
                return True
        return False


def _on_webview_message(handled: tuple[bool, object], message: str, context):
    global _active_reviewer, _command_comma_handled
    if message not in {
        "anki-global-kit:question-input-focus:handled",
        "anki-global-kit:question-input-focus:unhandled",
        "anki-global-kit:question-input-blur",
    }:
        return handled
    is_focus = message != "anki-global-kit:question-input-blur"
    if not isinstance(context, Reviewer):
        # The JS-message hook supplies the window owning the card webview.
        # Browse previewers expose _web; template previews expose preview_web.
        webview = getattr(context, "preview_web", None) or getattr(context, "_web", None)
        if webview is None or sip.isdeleted(webview):
            return handled
        if is_focus:
            _preview_input_webviews.add(webview)
        else:
            _preview_input_webviews.discard(webview)
        return (True, None)
    if context is not mw.reviewer:
        return handled
    _active_reviewer = context if is_focus else None
    _command_comma_handled = message.endswith(":handled") if is_focus else False
    _sync_preferences_action()
    return (True, None)


def _on_card_will_show(html: str, card, kind: str) -> str:
    global _active_reviewer, _command_comma_handled
    if kind in {"reviewQuestion", "reviewAnswer"}:
        # Replacing a card's DOM does not reliably blur its old textarea.
        _active_reviewer = None
        _command_comma_handled = False
        _sync_preferences_action()
    if kind in {
        "reviewQuestion", "reviewAnswer", "previewQuestion", "previewAnswer",
        "clayoutQuestion", "clayoutAnswer",
    }:
        # The Python hook runs before the asynchronous card DOM replacement.
        html += (
            "<script>onShownHook.push(function () {"
            "globalThis.ankiGlobalKitReportQuestionFocus?.();"
            "});</script>"
        )
    return html


def initialize() -> None:
    """Install the Qt shortcut override and receive card input focus state."""
    global _shortcut_filter, _message_hook_installed
    app = QApplication.instance()
    if app is not None and _shortcut_filter is None:
        _shortcut_filter = _PreferencesShortcutFilter(app)
        app.installEventFilter(_shortcut_filter)
        app.focusChanged.connect(_refresh_question_focus)
    if not _message_hook_installed:
        gui_hooks.editor_did_init_shortcuts.append(_register_editor_tab_shortcut)
        gui_hooks.editor_did_load_note.append(_register_editor_webview)
        gui_hooks.webview_did_receive_js_message.append(_on_webview_message)
        gui_hooks.card_will_show.append(_on_card_will_show)
        gui_hooks.state_did_change.append(_sync_preferences_action)
        _message_hook_installed = True
