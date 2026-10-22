"""Check default detection and restoration for local controls and synced themes."""

import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from tests.support.anki_stubs import load_module


class ThemeSelector:
    def __init__(self, theme):
        self.choices = ["monokai", "cassidy-dark"]
        self.index = self.choices.index(theme)

    def currentData(self):
        return self.choices[self.index]

    def findData(self, theme):
        return self.choices.index(theme)

    def setCurrentIndex(self, index):
        self.index = index


class SettingsBindingsTests(unittest.TestCase):
    def setUp(self):
        prefix = "kit_bindings.desktop"
        defaults = ModuleType(f"{prefix}.config.defaults")
        defaults.DEFAULT_SETTINGS = {"enabled": True}
        shortcut_input = ModuleType(f"{prefix}.ui.shortcut_input")
        shortcut_input.CardShortcutInput = type("CardShortcutInput", (), {})
        with patch.dict(
            sys.modules,
            {defaults.__name__: defaults, shortcut_input.__name__: shortcut_input},
        ):
            self.bindings = load_module(
                f"{prefix}.settings.bindings", "addon/desktop/settings/bindings.py"
            )
        self.checked = True
        self.controls = {
            "enabled": SimpleNamespace(
                isChecked=lambda: self.checked,
                setChecked=lambda checked: setattr(self, "checked", checked),
            )
        }

    def test_either_custom_theme_enables_restoration_with_local_defaults(self):
        for mode in ("light", "dark"):
            with self.subTest(mode=mode):
                themes = {
                    name: ThemeSelector("monokai" if name == mode else "cassidy-dark")
                    for name in ("light", "dark")
                }
                self.assertFalse(
                    self.bindings.controls_match_defaults(
                        self.controls, theme_controls=themes
                    )
                )
                self.bindings.restore_control_defaults(
                    self.controls, theme_controls=themes
                )
                self.assertTrue(
                    self.bindings.controls_match_defaults(
                        self.controls, theme_controls=themes
                    )
                )
                self.assertEqual(themes[mode].currentData(), "cassidy-dark")

    def test_local_controls_still_restore_when_themes_are_at_defaults(self):
        themes = {mode: ThemeSelector("cassidy-dark") for mode in ("light", "dark")}
        self.checked = False
        self.assertFalse(
            self.bindings.controls_match_defaults(self.controls, theme_controls=themes)
        )
        self.bindings.restore_control_defaults(self.controls, theme_controls=themes)
        self.assertTrue(
            self.bindings.controls_match_defaults(self.controls, theme_controls=themes)
        )

    def test_existing_callers_can_compare_and_restore_without_theme_controls(self):
        self.checked = False
        self.assertFalse(self.bindings.controls_match_defaults(self.controls))
        self.bindings.restore_control_defaults(self.controls)
        self.assertTrue(self.bindings.controls_match_defaults(self.controls))
