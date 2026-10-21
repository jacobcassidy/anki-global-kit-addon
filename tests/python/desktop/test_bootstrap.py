"""Check that Desktop startup assigns each registration to one owner."""

import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from tests.support.anki_stubs import ensure_package, load_module


class BootstrapTests(unittest.TestCase):
    def test_repeated_startup_registers_each_hook_and_initializer_once(self):
        ensure_package("kit.desktop")
        aqt = ModuleType("aqt")
        aqt.gui_hooks = SimpleNamespace(profile_did_open=[])
        editor = ModuleType("kit.desktop.editor.integration")
        editor.initialize = Mock()
        media = ModuleType("kit.desktop.media.install")
        media.update_assets_for_profile = Mock()
        settings = ModuleType("kit.desktop.settings.dialog")
        settings.initialize = Mock()
        reviewer = ModuleType("kit.desktop.shortcuts.reviewer")
        reviewer.initialize = Mock()
        with patch.dict(
            sys.modules,
            {
                "aqt": aqt,
                editor.__name__: editor,
                media.__name__: media,
                settings.__name__: settings,
                reviewer.__name__: reviewer,
            },
        ):
            bootstrap = load_module(
                "kit.desktop.bootstrap", "addon/desktop/bootstrap.py"
            )
            bootstrap.initialize()
            bootstrap.initialize()

        self.assertEqual(
            aqt.gui_hooks.profile_did_open, [media.update_assets_for_profile]
        )
        editor.initialize.assert_called_once()
        settings.initialize.assert_called_once()
        reviewer.initialize.assert_called_once()


if __name__ == "__main__":
    unittest.main()
