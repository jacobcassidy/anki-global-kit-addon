"""Check Settings saves report both installation and recovery failures."""

import sys
import unittest
from copy import deepcopy
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from tests.support.anki_startup import make_startup_stubs
from tests.support.anki_stubs import load_module


class SettingsSaveTests(unittest.TestCase):
    def setUp(self):
        stubs = make_startup_stubs(mac=False)
        prefix = "kit_save.desktop"
        self.local = {"card_toolbar_enabled": True, "unrelated": "preserved"}
        self.previous = deepcopy(self.local)
        self.themes = {"version": 3}
        self.previous_themes = deepcopy(self.themes)
        self.refresh = Mock()
        self.install = Mock()
        manager = Mock()
        manager.getConfig.side_effect = lambda _name: deepcopy(self.local)

        def write_config(_name, settings):
            self.local = deepcopy(settings)

        def set_config(_key, themes):
            self.themes = deepcopy(themes)

        manager.writeConfig.side_effect = write_config
        stubs.modules["aqt"].mw.addonManager = manager
        stubs.modules["aqt"].mw.col = SimpleNamespace(
            get_config=lambda _key, _default: deepcopy(self.themes),
            set_config=set_config,
        )
        replacements = {
            "config.constants": {"ADDON_PACKAGE_NAME": "kit"},
            "config.service": {
                "write_settings": lambda settings: write_config("kit", settings)
            },
            "media.install": {"update_assets_for_profile": self.install},
            "editor.integration": {"refresh_open_editors": self.refresh},
            "syntax_highlighting.preferences": {
                "THEME_FORMAT_VERSION": 3,
                "get_themes": Mock(),
                "set_themes": Mock(),
            },
            "syntax_highlighting.themes": {"resolve_preset": Mock()},
        }

        for suffix, attributes in replacements.items():
            module = ModuleType(f"{prefix}.{suffix}")
            module.__dict__.update(attributes)
            stubs.modules[module.__name__] = module

        modules = patch.dict(sys.modules, stubs.modules)
        modules.start()
        self.addCleanup(modules.stop)
        self.save = load_module(
            f"{prefix}.settings.save", "addon/desktop/settings/save.py"
        )
        self.warning = stubs.modules["aqt.utils"].showWarning
        self.dialog = Mock()

    def save_changed_settings(self):
        self.save.save_settings(self.dialog, {"card_toolbar_enabled": False})

    def test_failed_save_and_failed_recovery_do_not_claim_assets_were_restored(self):
        self.install.side_effect = [False, False]
        self.save_changed_settings()
        self.assertEqual(self.install.call_count, 2)
        self.assertEqual(self.local, self.previous)
        self.assertEqual(self.themes, self.previous_themes)
        message = self.warning.call_args.args[0]
        self.assertIn("restoring the previous settings also failed", message)
        self.assertIn("could not restore the previous card assets", message)
        self.assertNotIn("were restored", message)
        self.dialog.accept.assert_not_called()
        self.refresh.assert_not_called()

    def test_successful_recovery_reports_restoration_and_leaves_dialog_open(self):
        self.install.side_effect = [False, True]
        self.save_changed_settings()
        self.assertEqual(self.local, self.previous)
        self.assertEqual(self.themes, self.previous_themes)
        self.assertIn("previous settings were restored", self.warning.call_args.args[0])
        self.dialog.accept.assert_not_called()
        self.refresh.assert_not_called()

    def test_successful_save_preserves_other_settings_and_refreshes_editors(self):
        self.install.return_value = True
        self.save_changed_settings()
        self.assertEqual(self.local, {**self.previous, "card_toolbar_enabled": False})
        self.install.assert_called_once_with()
        self.refresh.assert_called_once_with()
        self.dialog.accept.assert_called_once_with()
        self.warning.assert_not_called()
