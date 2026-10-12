"""Check native editor bindings preserve fixed actions and avoid ambiguity."""

import unittest
from unittest.mock import Mock

from anki_stubs import load_editor_integration, load_settings_services


class EditorBindingsTests(unittest.TestCase):
    def bindings(self, overrides):
        settings = load_settings_services(config=overrides).config.get_editor_settings()
        integration = load_editor_integration(settings)
        bindings = []
        editor = Mock(currentField=0)
        integration._add_shortcut(bindings, editor)
        return integration, bindings, editor

    def test_every_custom_action_leaves_fixed_block_shortcuts_available(self):
        for key in (
            "anki_editor_inline_code_shortcut",
            "anki_editor_indent_increase_shortcut",
            "anki_editor_indent_decrease_shortcut",
        ):
            for keys, action in (("Ctrl+,", "unordered-list"), ("Ctrl+.", "ordered-list"), ("Ctrl+/", "blockquote")):
                with self.subTest(setting=key, shortcut=keys):
                    integration, bindings, editor = self.bindings({key: keys})
                    matches = [callback for shortcut, callback in bindings if shortcut == keys]
                    self.assertEqual(len(matches), 1)
                    self.assertIs(matches[0].func, integration._toggle_block)
                    self.assertEqual(matches[0].args[-1], action)

    def test_duplicate_saved_custom_shortcuts_register_only_one_handler(self):
        _, bindings, editor = self.bindings({
            "anki_editor_inline_code_shortcut": "Alt+K",
            "anki_editor_indent_increase_shortcut": "Alt+K",
        })
        self.assertEqual(sum(shortcut.isEnabled() and keys == "Alt+K"
                             for shortcut, keys in editor._anki_global_kit_shortcuts.values()), 1)

    def test_configured_indent_replaces_native_binding_for_the_same_action(self):
        settings = load_settings_services().config.get_editor_settings()
        integration = load_editor_integration(settings)
        bindings = [("Ctrl+Shift+.", lambda: None)]
        editor = Mock(currentField=0)
        integration._add_shortcut(bindings, editor)
        self.assertFalse(any(keys == "Ctrl+Shift+." for keys, _ in bindings))
        shortcut, keys = editor._anki_global_kit_shortcuts["anki_editor_indent_increase_shortcut"]
        self.assertEqual(keys, "Ctrl+Shift+.")
        shortcut.callback()
        editor.web.eval.assert_called_once_with("globalThis.ankiGlobalKitEditor?.indent();")

    def test_shifted_glyph_alias_does_not_create_a_second_native_handler(self):
        integration, bindings, editor = self.bindings({"anki_editor_inline_code_shortcut": "Ctrl+Shift+>"})
        matches = [shortcut for shortcut, keys in editor._anki_global_kit_shortcuts.values()
                   if shortcut.isEnabled() and integration.normalize_shortcut(keys) == "Ctrl+Shift+."]
        self.assertEqual(len(matches), 1)

    def test_settings_refresh_rebinds_and_disables_existing_editor_shortcuts(self):
        settings = load_settings_services().config.get_editor_settings()
        integration = load_editor_integration(settings)
        editor = Mock(currentField=0)
        integration._add_shortcut([], editor)
        shortcut, _keys = editor._anki_global_kit_shortcuts["anki_editor_inline_code_shortcut"]
        settings["anki_editor_inline_code_shortcut"] = "Alt+K"
        integration.refresh_open_editors()
        self.assertIs(editor._anki_global_kit_shortcuts["anki_editor_inline_code_shortcut"][0], shortcut)
        self.assertEqual(shortcut.key, "Alt+K")
        self.assertIn('"anki_editor_inline_code_shortcut":"Alt+K"', editor.web.eval.call_args.args[0])
        editor.web.eval.reset_mock()
        shortcut.callback()
        editor.web.eval.assert_called_once_with("globalThis.ankiGlobalKitEditor?.toggleInlineCode();")
        settings["anki_editor_inline_code_shortcut_enabled"] = False
        integration.refresh_open_editors()
        self.assertFalse(shortcut.isEnabled())
        editor.web.eval.reset_mock()
        shortcut.callback()
        editor.web.eval.assert_not_called()
        settings["anki_editor_inline_code_shortcut_enabled"] = True
        integration.refresh_open_editors()
        self.assertTrue(shortcut.isEnabled())
        self.assertEqual(len(editor._anki_global_kit_shortcuts), 3)

    def test_refresh_preserves_fixed_actions_and_prunes_deleted_editors(self):
        settings = load_settings_services().config.get_editor_settings()
        integration = load_editor_integration(settings)
        editor = Mock(currentField=0)
        integration._add_shortcut([], editor)
        settings["anki_editor_inline_code_shortcut"] = "Ctrl+,"
        integration.refresh_open_editors()
        self.assertFalse(editor._anki_global_kit_shortcuts["anki_editor_inline_code_shortcut"][0].isEnabled())
        editor.web.eval.reset_mock()
        integration.sip.isdeleted = lambda widget: widget is editor.widget
        integration.refresh_open_editors()
        editor.web.eval.assert_not_called()
        self.assertNotIn(editor, integration._open_editors)


if __name__ == "__main__":
    unittest.main()
