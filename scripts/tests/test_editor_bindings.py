"""Check native editor bindings preserve fixed actions and avoid ambiguity."""

import unittest

from anki_stubs import load_editor_integration, load_settings_services


class EditorBindingsTests(unittest.TestCase):
    def bindings(self, overrides):
        settings = load_settings_services(config=overrides).config.get_editor_settings()
        integration = load_editor_integration(settings)
        bindings = []
        integration._add_shortcut(bindings, object())
        return integration, bindings

    def test_every_custom_action_leaves_fixed_block_shortcuts_available(self):
        for key in (
            "anki_editor_inline_code_shortcut",
            "anki_editor_indent_increase_shortcut",
            "anki_editor_indent_decrease_shortcut",
        ):
            for keys, action in (("Ctrl+,", "unordered-list"), ("Ctrl+.", "ordered-list"), ("Ctrl+/", "blockquote")):
                with self.subTest(setting=key, shortcut=keys):
                    integration, bindings = self.bindings({key: keys})
                    matches = [callback for shortcut, callback in bindings if shortcut == keys]
                    self.assertEqual(len(matches), 1)
                    self.assertIs(matches[0].func, integration._toggle_block)
                    self.assertEqual(matches[0].args[-1], action)

    def test_duplicate_saved_custom_shortcuts_register_only_one_handler(self):
        _, bindings = self.bindings({
            "anki_editor_inline_code_shortcut": "Alt+K",
            "anki_editor_indent_increase_shortcut": "Alt+K",
        })
        self.assertEqual(sum(keys == "Alt+K" for keys, _ in bindings), 1)

    def test_configured_indent_replaces_native_binding_for_the_same_action(self):
        settings = load_settings_services().config.get_editor_settings()
        integration = load_editor_integration(settings)
        bindings = [("Ctrl+Shift+.", lambda: None)]
        integration._add_shortcut(bindings, object())
        matches = [callback for keys, callback in bindings if keys == "Ctrl+Shift+."]
        self.assertEqual(len(matches), 1)
        self.assertIs(matches[0].func, integration._change_indentation)


if __name__ == "__main__":
    unittest.main()
