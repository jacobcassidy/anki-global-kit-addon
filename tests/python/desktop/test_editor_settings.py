"""Check recovery of unsupported saved shortcuts without changing configuration."""

import unittest
from unittest.mock import Mock

from tests.support.anki_stubs import load_settings_services


class EditorSettingsTests(unittest.TestCase):
    def test_saved_code_block_alias_recovers_defaults_for_editor_shortcuts(self):
        keys = (
            "anki_editor_inline_code_shortcut",
            "anki_editor_indent_increase_shortcut",
            "anki_editor_indent_decrease_shortcut",
            "anki_editor_blockquote_shortcut",
            "anki_editor_convert_markdown_shortcut",
            "anki_editor_exit_code_block_shortcut",
            "anki_editor_syntax_highlighting_shortcut",
        )
        for mac in (False, True):
            with self.subTest(mac=mac):
                services = load_settings_services(
                    mac=mac, config={key: "CodeBlock+C" for key in keys}
                )
                settings = services.config.get_editor_settings()
                defaults = load_settings_services(mac=mac).config.get_editor_settings()
                for key in keys:
                    self.assertEqual(settings[key], defaults[key])
                self.assertEqual(
                    services.config.get_card_web_settings()[
                        "card_input_markdown_code_block_shortcut"
                    ],
                    "CodeBlock+C",
                )

    def test_tab_recovery_preserves_switches_and_does_not_write_config(self):
        for mac in (False, True):
            for shortcut in (
                "Alt+Tab",
                "Control+Tab",
                "Meta+Shift+Backtab",
                "Ctrl+tAb",
            ):
                config = {
                    "unrelated": "kept",
                    "card_input_tab_indentation": False,
                    "anki_editor_tab_indentation": False,
                }
                keys = [
                    f"{prefix}_{action}_shortcut"
                    for prefix in ("card_input_tab_indent", "anki_editor_indent")
                    for action in ("increase", "decrease")
                ]
                config.update({key: shortcut for key in keys})
                config.update({f"{key}_enabled": False for key in keys})
                snapshot = dict(config)
                services = load_settings_services(mac=mac, config=config)
                services.mw.addonManager.writeConfig = Mock()
                settings = {
                    **services.config.get_settings(),
                    **services.config.get_editor_settings(),
                }
                for key in keys:
                    self.assertEqual(
                        settings[key],
                        "Ctrl+Alt+." if "increase" in key else "Ctrl+Alt+,",
                    )
                    self.assertFalse(settings[f"{key}_enabled"])
                self.assertFalse(settings["card_input_tab_indentation"])
                self.assertFalse(settings["anki_editor_tab_indentation"])
                self.assertEqual(config, snapshot)
                services.mw.addonManager.writeConfig.assert_not_called()
                web = services.config.get_card_web_settings()
                self.assertEqual(web[keys[0]], "Ctrl+Alt+.")


if __name__ == "__main__":
    unittest.main()
