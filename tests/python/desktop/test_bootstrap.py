"""Check that Desktop startup assigns each registration to one owner."""

import importlib
import importlib.util
import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from tests.support.anki_startup import make_startup_stubs
from tests.support.anki_stubs import ROOT, ensure_package, load_module


class BootstrapTests(unittest.TestCase):
    def test_entry_point_imports_real_modules_and_registers_once(self):
        package_name = "anki_global_kit_startup_test"
        for mac in (False, True):
            with self.subTest(mac=mac):
                stubs = make_startup_stubs(mac=mac)
                with patch.dict(sys.modules, stubs.modules):
                    spec = importlib.util.spec_from_file_location(
                        package_name,
                        ROOT / "addon/__init__.py",
                        submodule_search_locations=[str(ROOT / "addon")],
                    )
                    assert spec is not None and spec.loader is not None
                    entry = importlib.util.module_from_spec(spec)
                    sys.modules[package_name] = entry
                    spec.loader.exec_module(entry)
                    self.assertIs(importlib.import_module(package_name), entry)
                    entry.initialize()
                    entry.initialize()

                    def module(name):
                        return importlib.import_module(f"{package_name}.desktop.{name}")

                    editor = module("editor.integration")
                    reviewer = module("shortcuts.reviewer")
                    expected_hooks = {
                        "profile_did_open": [module("bootstrap")._on_profile_open],
                        "editor_did_init_buttons": [editor._add_button],
                        "editor_did_init_shortcuts": [
                            editor._add_shortcut,
                        ],
                        "editor_did_load_note": [
                            editor._inject_features,
                            module(
                                "editor.features.syntax_highlighting"
                            ).reset_editor_language_context,
                        ],
                        "editor_will_load_note": [
                            module(
                                "editor.features.field_descriptions"
                            ).add_compare_placeholder
                        ],
                        "webview_did_receive_js_message": [
                            module("editor.features.syntax_highlighting")._on_message,
                            reviewer._on_webview_message,
                        ],
                        "card_will_show": [reviewer._on_card_will_show],
                        "state_did_change": [reviewer._sync_preferences_action],
                        "theme_did_change": [],
                    }
                    self.assertEqual(vars(stubs.hooks), expected_hooks)
                    stubs.qt.QAction.assert_called_once_with(
                        "Anki Global Kit Settings...", stubs.modules["aqt"].mw
                    )
                    stubs.menu.addAction.assert_called_once_with(
                        stubs.qt.QAction.return_value
                    )
                    stubs.app.installEventFilter.assert_called_once_with(
                        reviewer._shortcut_filter
                    )
                    self.assertIsInstance(
                        reviewer._shortcut_filter, reviewer._PreferencesShortcutFilter
                    )
                    stubs.app.focusChanged.connect.assert_called_once_with(
                        reviewer._refresh_question_focus
                    )

    def test_repeated_startup_registers_each_hook_and_initializer_once(self):
        ensure_package("kit.desktop")
        aqt = ModuleType("aqt")
        setattr(aqt, "gui_hooks", SimpleNamespace(profile_did_open=[]))
        editor = ModuleType("kit.desktop.editor.integration")
        setattr(editor, "initialize", Mock())
        media = ModuleType("kit.desktop.media.install")
        setattr(media, "update_assets_for_profile", Mock())
        settings = ModuleType("kit.desktop.settings.dialog")
        setattr(settings, "initialize", Mock())
        reviewer = ModuleType("kit.desktop.shortcuts.reviewer")
        setattr(reviewer, "initialize", Mock())
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

        self.assertEqual(aqt.gui_hooks.profile_did_open, [bootstrap._on_profile_open])
        self.assertIsNone(bootstrap._on_profile_open())
        media.update_assets_for_profile.assert_called_once_with()
        editor.initialize.assert_called_once()
        settings.initialize.assert_called_once()
        reviewer.initialize.assert_called_once()


if __name__ == "__main__":
    unittest.main()
