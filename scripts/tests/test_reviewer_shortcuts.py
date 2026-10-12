"""Regression checks for native focus recovery without a DOM focus event."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class Reviewer:
    pass


class Action:
    def __init__(self):
        self.enabled = True

    def isEnabled(self):
        return self.enabled

    def setEnabled(self, enabled):
        self.enabled = enabled


class ReviewerShortcutTests(unittest.TestCase):
    def setUp(self):
        web = Mock()
        web.isAncestorOf.return_value = False
        reviewer = Reviewer()
        reviewer.web = web
        self.mw = SimpleNamespace(state="review", reviewer=reviewer, form=SimpleNamespace(actionPreferences=Action()))
        self.application = Mock()
        self.application.focusWidget.return_value = web
        aqt = ModuleType("aqt")
        aqt.mw = self.mw
        aqt.gui_hooks = SimpleNamespace()
        qt = ModuleType("aqt.qt")
        qt.QApplication = self.application
        qt.QObject = object
        qt.QEvent = SimpleNamespace()
        qt.Qt = SimpleNamespace()
        self.deleted_widgets = set()
        qt.sip = SimpleNamespace(isdeleted=lambda widget: widget in self.deleted_widgets)
        reviewer_module = ModuleType("aqt.reviewer")
        reviewer_module.Reviewer = Reviewer
        utils = ModuleType("aqt.utils")
        utils.is_mac = True
        with patch.dict(sys.modules, {"aqt": aqt, "aqt.qt": qt, "aqt.reviewer": reviewer_module, "aqt.utils": utils}):
            path = Path(__file__).resolve().parents[2] / "addon/desktop/reviewer_shortcuts.py"
            spec = importlib.util.spec_from_file_location("kit.desktop.reviewer_shortcuts", path)
            self.integration = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.integration)

    def test_card_indent_override_accepts_base_keys_and_shifted_glyph_aliases(self):
        self.integration._active_reviewer = self.mw.reviewer
        self.integration.QEvent.Type = SimpleNamespace(ShortcutOverride=1, KeyPress=2)
        self.integration.Qt.Key = SimpleNamespace(Key_Tab=9, Key_Backtab=10, Key_Comma=44, Key_Period=46, Key_Less=60, Key_Greater=62)
        self.integration.Qt.KeyboardModifier = SimpleNamespace(MetaModifier=4, ControlModifier=8, AltModifier=16, ShiftModifier=32)
        settings = ModuleType("kit.desktop.settings")
        config = {"card_input_tab_indentation": True}
        settings.get_settings = lambda: config
        event = Mock()
        event.type.return_value = 1
        event.modifiers.return_value = 8 | 32
        filter = self.integration._PreferencesShortcutFilter()
        with patch.dict(sys.modules, {"kit.desktop.settings": settings}):
            for action, base, shifted in (("increase", ".", ">"), ("decrease", ",", "<")):
                name = f"card_input_tab_indent_{action}_shortcut"
                for configured in (base, shifted):
                    config[name] = f"Ctrl+Shift+{configured}"
                    for key in (base, shifted):
                        with self.subTest(action=action, configured=configured, key=key):
                            event.key.return_value = ord(key)
                            self.assertTrue(filter.eventFilter(self.mw.reviewer.web, event))
                    config[f"{name}_enabled"] = False
                    self.assertFalse(filter.eventFilter(self.mw.reviewer.web, event))
                    config[f"{name}_enabled"] = True
            config["card_input_tab_indentation"] = False
            self.assertFalse(filter.eventFilter(self.mw.reviewer.web, event))
            config["card_input_tab_indentation"] = True
            event.modifiers.return_value = 4 | 32
            self.assertFalse(filter.eventFilter(self.mw.reviewer.web, event))
            event.modifiers.return_value = 8 | 32
            self.integration._active_reviewer = None
            self.assertFalse(filter.eventFilter(self.mw.reviewer.web, event))

    def test_toolbar_focus_keeps_activation_and_navigation_out_of_native_review_actions(self):
        self.integration.QEvent.Type = SimpleNamespace(ShortcutOverride=1, KeyPress=2)
        self.integration.Qt.Key = SimpleNamespace(
            Key_Tab=9, Key_Backtab=10, Key_Comma=44, Key_Period=46, Key_Less=60, Key_Greater=62,
            Key_Space=32, Key_Return=13, Key_Enter=14, Key_Escape=27,
            Key_Left=101, Key_Right=102, Key_Home=103, Key_End=104,
        )
        self.integration.Qt.KeyboardModifier = SimpleNamespace(NoModifier=0, ControlModifier=8)
        event = Mock()
        event.type.return_value = 1
        event.modifiers.return_value = 0
        filter = self.integration._PreferencesShortcutFilter()
        for context in (self.mw.reviewer, SimpleNamespace(_web=self.mw.reviewer.web)):
            with self.subTest(context=context):
                self.integration._on_webview_message(
                    (False, None), "anki-global-kit:question-toolbar-focus", context,
                )
                for key in (32, 13, 14, 27, 101, 102, 103, 104):
                    event.key.return_value = key
                    self.assertTrue(filter.eventFilter(self.mw.reviewer.web, event))
                self.mw.reviewer.web.eval.assert_not_called()
                self.assertTrue(self.mw.form.actionPreferences.isEnabled())
                event.modifiers.return_value = 8
                self.assertFalse(self.integration._toolbar_owns_navigation(event))
                event.modifiers.return_value = 0
                self.application.focusWidget.return_value = object()
                self.assertFalse(self.integration._toolbar_owns_navigation(event))
                self.application.focusWidget.return_value = self.mw.reviewer.web
                self.integration._on_webview_message(
                    (False, None), "anki-global-kit:question-input-blur", context,
                )
                self.assertFalse(filter.eventFilter(self.mw.reviewer.web, event))

    def test_native_control_tab_routes_to_card_before_browser_keydown(self):
        self.integration._active_reviewer = self.mw.reviewer
        self.integration.QEvent.Type = SimpleNamespace(ShortcutOverride=1, KeyPress=2)
        self.integration.Qt.Key = SimpleNamespace(Key_Tab=9, Key_Backtab=10, Key_Comma=44, Key_Period=46, Key_Less=60, Key_Greater=62)
        self.integration.Qt.KeyboardModifier = SimpleNamespace(MetaModifier=4, ControlModifier=8, AltModifier=16, ShiftModifier=32)
        settings = ModuleType("kit.desktop.settings")
        settings.get_settings = lambda: {"card_input_tab_indentation": True}
        settings.get_editor_settings = lambda: {"anki_editor_tab_indentation": True}
        filter = self.integration._PreferencesShortcutFilter()
        with patch.dict(sys.modules, {"kit.desktop.settings": settings}):
            event = Mock()
            event.key.return_value = 9
            event.modifiers.return_value = 4
            event.type.return_value = 1
            self.assertTrue(filter.eventFilter(self.mw.reviewer.web, event))
            self.mw.reviewer.web.eval.assert_called_once_with("globalThis.ankiGlobalKitUnindentQuestion?.();")
            event.type.return_value = 2
            self.assertTrue(filter.eventFilter(self.mw.reviewer.web, event))
            self.mw.reviewer.web.eval.assert_called_once()
            self.integration._active_reviewer = None
            self.assertFalse(filter.eventFilter(self.mw.reviewer.web, event))
            self.integration._active_reviewer = self.mw.reviewer
            settings.get_settings = lambda: {"card_input_tab_indentation": False}
            self.assertFalse(filter.eventFilter(self.mw.reviewer.web, event))

    def test_native_control_tab_routes_to_editor_and_respects_disabled_setting(self):
        self.integration.QEvent.Type = SimpleNamespace(ShortcutOverride=1, KeyPress=2)
        self.integration.Qt.Key = SimpleNamespace(Key_Tab=9, Key_Backtab=10, Key_Comma=44, Key_Period=46, Key_Less=60, Key_Greater=62)
        self.integration.Qt.KeyboardModifier = SimpleNamespace(MetaModifier=4, ControlModifier=8, AltModifier=16, ShiftModifier=32)
        web = Mock()
        self.application.focusWidget.return_value = web
        self.integration._register_editor_tab_shortcut([], SimpleNamespace(web=web))
        settings = ModuleType("kit.desktop.settings")
        settings.get_editor_settings = lambda: {"anki_editor_tab_indentation": True}
        settings.get_settings = lambda: {"card_input_tab_indentation": True}
        event = Mock()
        event.key.return_value = 9
        event.modifiers.return_value = 4
        event.type.return_value = 1
        with patch.dict(sys.modules, {"kit.desktop.settings": settings}):
            filter = self.integration._PreferencesShortcutFilter()
            self.assertTrue(filter.eventFilter(web, event))
            web.eval.assert_called_once_with("globalThis.ankiGlobalKitEditor?.unindent();")
            settings.get_editor_settings = lambda: {"anki_editor_tab_indentation": False}
            self.assertFalse(filter.eventFilter(web, event))
            event.modifiers.return_value = 8
            self.assertFalse(filter.eventFilter(web, event))

    def test_preview_inputs_route_control_tab_without_an_active_study_session(self):
        self.mw.state = "deckBrowser"
        self.integration.QEvent.Type = SimpleNamespace(ShortcutOverride=1, KeyPress=2)
        self.integration.Qt.Key = SimpleNamespace(Key_Tab=9, Key_Backtab=10, Key_Comma=44, Key_Period=46, Key_Less=60, Key_Greater=62)
        self.integration.Qt.KeyboardModifier = SimpleNamespace(MetaModifier=4, ControlModifier=8, AltModifier=16, ShiftModifier=32)
        settings = ModuleType("kit.desktop.settings")
        settings.get_settings = lambda: {"card_input_tab_indentation": True}
        settings.get_editor_settings = lambda: {"anki_editor_tab_indentation": True}
        for attribute in ("_web", "preview_web"):
            with self.subTest(attribute=attribute), patch.dict(sys.modules, {"kit.desktop.settings": settings}):
                web = Mock()
                web.isAncestorOf.return_value = False
                self.application.focusWidget.return_value = web
                preview = SimpleNamespace(**{attribute: web})
                result = self.integration._on_webview_message(
                    (False, None), "anki-global-kit:question-input-focus:unhandled", preview,
                )
                self.assertEqual(result, (True, None))
                event = Mock()
                event.type.return_value = 1
                event.key.return_value = 9
                event.modifiers.return_value = 4
                filter = self.integration._PreferencesShortcutFilter()
                self.assertTrue(filter.eventFilter(web, event))
                web.eval.assert_called_once_with("globalThis.ankiGlobalKitUnindentQuestion?.();")
                self.assertTrue(self.mw.form.actionPreferences.isEnabled())
                settings.get_settings = lambda: {"card_input_tab_indentation": False}
                self.assertFalse(filter.eventFilter(web, event))
                settings.get_settings = lambda: {"card_input_tab_indentation": True}
                self.integration._on_webview_message(
                    (False, None), "anki-global-kit:question-input-blur", preview,
                )
                self.assertFalse(filter.eventFilter(web, event))

    def test_preview_focus_recovery_refreshes_the_preview_not_the_reviewer(self):
        self.mw.state = "deckBrowser"
        web = Mock()
        web.isAncestorOf.return_value = False
        self.application.focusWidget.return_value = web
        self.integration._on_webview_message(
            (False, None), "anki-global-kit:question-input-focus:handled", SimpleNamespace(_web=web),
        )
        self.integration._refresh_question_focus()
        web.eval.assert_called_once_with("globalThis.ankiGlobalKitReportQuestionFocus?.();")
        self.mw.reviewer.web.eval.assert_not_called()

    def test_unrelated_webview_messages_are_not_claimed(self):
        self.assertEqual(self.integration._on_webview_message(
            (False, None), "other-addon-message", SimpleNamespace(_web=Mock()),
        ), (False, None))

    def test_custom_tab_shortcuts_replace_defaults_and_respect_individual_switches(self):
        self.integration.Qt.KeyboardModifier = SimpleNamespace(MetaModifier=4, ControlModifier=8, AltModifier=16, ShiftModifier=32)
        event = Mock()
        config = {
            "card_input_tab_indent_increase_shortcut": "Alt+Shift+Tab",
            "card_input_tab_indent_decrease_shortcut": "Ctrl+Tab",
        }
        event.modifiers.return_value = 4
        self.assertIsNone(self.integration._card_tab_action(event, config))
        event.modifiers.return_value = 16 | 32
        self.assertEqual(self.integration._card_tab_action(event, config), "globalThis.ankiGlobalKitIndentQuestion?.();")
        event.modifiers.return_value = 8
        self.assertEqual(self.integration._card_tab_action(event, config), "globalThis.ankiGlobalKitUnindentQuestion?.();")
        config["card_input_tab_indent_decrease_shortcut_enabled"] = False
        self.assertIsNone(self.integration._card_tab_action(event, config))

    def test_closed_preview_is_pruned_before_focus_recovery_touches_qt(self):
        web = Mock()
        web.isAncestorOf.side_effect = RuntimeError("wrapped C/C++ object has been deleted")
        self.integration._preview_input_webviews.add(web)
        self.deleted_widgets.add(web)
        self.integration._refresh_question_focus()
        self.assertNotIn(web, self.integration._preview_input_webviews)
        web.isAncestorOf.assert_not_called()
        web.eval.assert_not_called()
        # A late focus message must not register the deleted preview again.
        self.integration._on_webview_message(
            (False, None), "anki-global-kit:question-input-focus:handled", SimpleNamespace(_web=web),
        )
        self.assertNotIn(web, self.integration._preview_input_webviews)

    def test_closed_editor_and_preview_are_pruned_before_shortcut_routing(self):
        editor = Mock()
        preview = Mock()
        for web in (editor, preview):
            web.isAncestorOf.side_effect = RuntimeError("wrapped C/C++ object has been deleted")
        self.integration._editor_webviews.add(editor)
        self.integration._preview_input_webviews.add(preview)
        self.deleted_widgets.update((editor, preview))
        self.mw.state = "deckBrowser"
        settings = ModuleType("kit.desktop.settings")
        settings.get_settings = lambda: {"card_input_tab_indentation": True}
        settings.get_editor_settings = lambda: {"anki_editor_tab_indentation": True}
        with patch.dict(sys.modules, {"kit.desktop.settings": settings}):
            self.assertIsNone(self.integration._tab_shortcut_target(Mock()))
        self.assertFalse(self.integration._editor_webviews)
        self.assertFalse(self.integration._preview_input_webviews)
        editor.isAncestorOf.assert_not_called()
        preview.isAncestorOf.assert_not_called()

    def test_deleted_reviewer_and_focus_widgets_are_not_dereferenced(self):
        self.integration._active_reviewer = self.mw.reviewer
        self.integration._command_comma_handled = True
        self.deleted_widgets.add(self.mw.reviewer.web)
        self.assertFalse(self.integration._input_owns_command_comma())
        self.integration._refresh_question_focus()
        self.mw.reviewer.web.isAncestorOf.assert_not_called()
        self.mw.reviewer.web.eval.assert_not_called()

    def test_editor_customized_tab_combinations_and_individual_switches(self):
        self.integration.Qt.KeyboardModifier = SimpleNamespace(MetaModifier=4, ControlModifier=8, AltModifier=16, ShiftModifier=32)
        event = Mock()
        config = {
            "anki_editor_indent_increase_shortcut": "Meta+Shift+Tab",
            "anki_editor_indent_decrease_shortcut": "Alt+Tab",
        }
        event.modifiers.return_value = 4 | 32
        self.assertEqual(self.integration._indentation_tab_action(event, config, "anki_editor_indent"), "globalThis.ankiGlobalKitEditor?.indent();")
        event.modifiers.return_value = 16
        self.assertEqual(self.integration._indentation_tab_action(event, config, "anki_editor_indent"), "globalThis.ankiGlobalKitEditor?.unindent();")
        config["anki_editor_indent_decrease_shortcut_enabled"] = False
        self.assertIsNone(self.integration._indentation_tab_action(event, config, "anki_editor_indent"))
        event.modifiers.return_value = 4
        self.assertIsNone(self.integration._indentation_tab_action(event, config, "anki_editor_indent"))

    def test_native_focus_recovery_refreshes_even_when_ownership_was_reset(self):
        self.integration._refresh_question_focus()
        self.mw.reviewer.web.eval.assert_called_once_with("globalThis.ankiGlobalKitReportQuestionFocus?.();")
        self.integration._on_webview_message(
            (False, None), "anki-global-kit:question-input-focus:handled", self.mw.reviewer,
        )
        self.assertFalse(self.mw.form.actionPreferences.isEnabled())

    def test_card_replacement_resets_then_requests_ownership_after_render(self):
        self.integration._on_webview_message(
            (False, None), "anki-global-kit:question-input-focus:handled", self.mw.reviewer,
        )
        html = self.integration._on_card_will_show("card", None, "reviewQuestion")
        self.assertTrue(self.mw.form.actionPreferences.isEnabled())
        self.assertIn("onShownHook.push", html)
        self.assertIn("ankiGlobalKitReportQuestionFocus", html)
        self.assertIn("ankiGlobalKitReportQuestionFocus", self.integration._on_card_will_show("preview", None, "previewQuestion"))

    def test_native_focus_outside_reviewer_restores_preferences(self):
        self.integration._on_webview_message(
            (False, None), "anki-global-kit:question-input-focus:handled", self.mw.reviewer,
        )
        self.application.focusWidget.return_value = object()
        self.integration._refresh_question_focus()
        self.assertTrue(self.mw.form.actionPreferences.isEnabled())
        self.mw.reviewer.web.eval.assert_not_called()

    def test_non_review_screens_do_not_query_the_card(self):
        self.mw.state = "deckBrowser"
        self.integration._refresh_question_focus()
        self.mw.reviewer.web.eval.assert_not_called()


if __name__ == "__main__":
    unittest.main()
