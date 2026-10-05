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
        self.assertEqual(self.integration._on_card_will_show("preview", None, "previewQuestion"), "preview")

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
