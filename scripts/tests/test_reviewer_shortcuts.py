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
        reviewer_module = ModuleType("aqt.reviewer")
        reviewer_module.Reviewer = Reviewer
        utils = ModuleType("aqt.utils")
        utils.is_mac = True
        with patch.dict(sys.modules, {"aqt": aqt, "aqt.qt": qt, "aqt.reviewer": reviewer_module, "aqt.utils": utils}):
            path = Path(__file__).resolve().parents[2] / "addon/desktop/reviewer_shortcuts.py"
            spec = importlib.util.spec_from_file_location("kit.desktop.reviewer_shortcuts", path)
            self.integration = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.integration)

    def test_native_control_tab_routes_to_card_before_browser_keydown(self):
        self.integration._active_reviewer = self.mw.reviewer
        self.integration.QEvent.Type = SimpleNamespace(ShortcutOverride=1, KeyPress=2)
        self.integration.Qt.Key = SimpleNamespace(Key_Tab=9, Key_Comma=44)
        self.integration.Qt.KeyboardModifier = SimpleNamespace(MetaModifier=4, ControlModifier=8)
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
        self.integration.Qt.Key = SimpleNamespace(Key_Tab=9, Key_Comma=44)
        self.integration.Qt.KeyboardModifier = SimpleNamespace(MetaModifier=4, ControlModifier=8)
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
        self.integration.Qt.Key = SimpleNamespace(Key_Tab=9, Key_Comma=44)
        self.integration.Qt.KeyboardModifier = SimpleNamespace(MetaModifier=4, ControlModifier=8)
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
