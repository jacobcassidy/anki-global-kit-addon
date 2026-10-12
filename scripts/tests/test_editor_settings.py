"""Check migration of card-only aliases accidentally saved in editor settings."""

import unittest

from anki_stubs import load_settings_services


class EditorSettingsTests(unittest.TestCase):
    def test_saved_code_block_alias_expands_for_every_native_editor_shortcut(self):
        keys = (
            "anki_editor_inline_code_shortcut",
            "anki_editor_indent_increase_shortcut",
            "anki_editor_indent_decrease_shortcut",
        )
        for mac in (False, True):
            with self.subTest(mac=mac):
                services = load_settings_services(mac=mac, config={key: "CodeBlock+C" for key in keys})
                settings = services.config.get_editor_settings()
                expected = "Ctrl+Meta+C" if mac else "Ctrl+Alt+C"
                for key in keys:
                    self.assertEqual(settings[key], expected)
                self.assertEqual(services.config.get_card_web_settings()["card_input_markdown_code_block_shortcut"], "CodeBlock+C")


if __name__ == "__main__":
    unittest.main()
