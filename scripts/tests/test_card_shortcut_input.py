"""Check real shortcut recorder methods with isolated Qt event and button stubs."""

import ast
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class Button:
    def text(self):
        return self.label

    def setText(self, label):
        self.label = label

    def eventFilter(self, watched, event):
        return False


class CardShortcutInputTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[2] / "addon/desktop/settings/ui/widgets.py"
        qt = ModuleType("aqt.qt")
        for item in ast.parse(path.read_text()).body:
            if isinstance(item, ast.ImportFrom) and item.module == "aqt.qt":
                for name in item.names:
                    setattr(qt, name.name, Button)
        qt.Qt = SimpleNamespace(
            Key=SimpleNamespace(Key_Tab=9, Key_Backtab=10, Key_Escape=27, Key_Backspace=8,
                Key_Delete=127, Key_Control=101, Key_Alt=102, Key_Shift=103, Key_Meta=104),
            KeyboardModifier=SimpleNamespace(ControlModifier=1, MetaModifier=2, AltModifier=4, ShiftModifier=8),
        )
        qt.QEvent = SimpleNamespace(Type=SimpleNamespace(
            ShortcutOverride=1, KeyPress=2, KeyRelease=3, FocusOut=4, MouseButtonPress=5,
        ))
        class Sequence:
            SequenceFormat = SimpleNamespace(PortableText=0)
            def __init__(self, key):
                self.key = key
            def toString(self, _):
                return "Tab" if self.key == 9 else "Backtab"
        qt.QKeySequence = Sequence
        utils = ModuleType("aqt.utils")
        utils.is_mac = True
        constants = ModuleType("kit.desktop.settings.configs.constants")
        for name in ("COLOR_TRANSPARENT", "NESTED_INDENT", "SHORTCUT_MIN_WIDTH", "SHORTCUT_MODIFIER_HINT", "SHARED_ASSET_DIR", "ZERO_MARGINS"):
            setattr(constants, name, 0)
        theme = ModuleType("kit.desktop.settings.ui.theme")
        theme.get_theme_color = Mock()
        shortcuts = ModuleType("kit.desktop.settings.helpers.shortcuts")
        shortcuts.format_shortcut = lambda value: value
        shortcuts.normalize_shortcut = lambda value: value
        shortcuts.reserved_shortcut_warnings = lambda: {}
        shortcuts.split_shortcut = lambda value: (
            ["+"] if value == "+" else
            [*value[:-2].split("+"), "+"] if value.endswith("++") else
            value.split("+")
        )
        modules = {"aqt.qt": qt, "aqt.utils": utils,
            "kit.desktop.settings.configs.constants": constants,
            "kit.desktop.settings.ui.theme": theme,
            "kit.desktop.settings.helpers.shortcuts": shortcuts}
        with patch.dict(sys.modules, modules):
            spec = importlib.util.spec_from_file_location("kit.desktop.settings.ui.widgets", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        self.module = module
        self.input = module.CardShortcutInput.__new__(module.CardShortcutInput)
        self.input.label = ""
        self.input._capturing = True
        self.input._captured_tab = False
        self.input._shortcut_validator = None
        self.input._set_validation_message = Mock()
        self.input._notify_change_listeners = Mock()
        self.input._stop_capture = Mock()

    def event(self, type, modifiers, key=9):
        event = Mock()
        event.type.return_value = type
        event.modifiers.return_value = modifiers
        event.key.return_value = key
        event.text.return_value = "\t"
        return event

    def test_modified_tab_is_recorded_before_native_focus_traversal(self):
        for modifiers, expected in ((4, "Alt+Tab"), (2, "Meta+Tab"), (4 | 8, "Alt+Shift+Tab")):
            with self.subTest(modifiers=modifiers):
                event = self.event(1, modifiers)
                self.assertTrue(self.input.eventFilter(self.input, event))
                self.assertEqual(self.input.stored_shortcut(), expected)
                event.accept.assert_called()
                self.assertTrue(self.input.eventFilter(self.input, self.event(2, modifiers, key=0)))
                self.assertEqual(self.input.stored_shortcut(), expected)
                self.input._stop_capture.assert_not_called()

    def test_plain_tab_ends_capture_and_retains_native_focus_navigation(self):
        self.assertFalse(self.input.eventFilter(self.input, self.event(2, 0)))
        self.input._stop_capture.assert_called_once()

    def test_tab_defaults_round_trip_without_spurious_reset_links(self):
        for label, expected in (("⌥Tab", "Alt+Tab"), ("⌃Tab", "Meta+Tab")):
            self.input.label = label
            self.assertEqual(self.input.stored_shortcut(), expected)

    def test_editor_combinations_remain_native_qt_shortcuts(self):
        for mac, label, expected in (
            (True, "⌃⌘C", "Ctrl+Meta+C"),
            (False, "Ctrl+Alt+C", "Ctrl+Alt+C"),
        ):
            with self.subTest(mac=mac):
                self.module.is_mac = mac
                self.input.label = label
                self.assertEqual(self.input.stored_shortcut(), expected)

    def test_only_card_code_block_field_uses_portable_alias(self):
        self.input._code_block_alias = True
        for mac, label in ((True, "⌃⌘C"), (False, "Ctrl+Alt+C")):
            with self.subTest(mac=mac):
                self.module.is_mac = mac
                self.input.label = label
                self.assertEqual(self.input.stored_shortcut(), "CodeBlock+C")


if __name__ == "__main__":
    unittest.main()
