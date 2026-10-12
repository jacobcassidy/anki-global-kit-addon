"""Check normalization agrees with shifted punctuation shortcut matching."""

import unittest

from anki_stubs import load_shortcut_helpers


class ShortcutHelpersTests(unittest.TestCase):
    def test_intended_native_indent_actions_do_not_warn_but_other_overlaps_do(self):
        helpers = load_shortcut_helpers()
        for action, keys, alias, opposite in (
            ("increase", "Ctrl+Shift+.", "Ctrl+Shift+>", "Ctrl+Shift+,"),
            ("decrease", "Ctrl+Shift+,", "Ctrl+Shift+<", "Ctrl+Shift+."),
        ):
            setting = f"anki_editor_indent_{action}_shortcut"
            with self.subTest(action=action):
                self.assertIsNone(helpers.anki_editor_shortcut_warning(setting, keys))
                self.assertIsNone(helpers.anki_editor_shortcut_warning(setting, alias))
                self.assertIsNotNone(helpers.anki_editor_shortcut_warning(setting, opposite))
                self.assertIsNotNone(helpers.anki_editor_shortcut_warning("anki_editor_inline_code_shortcut", keys))
        self.assertEqual(helpers.anki_editor_shortcut_warning("anki_editor_inline_code_shortcut", "Ctrl+B"), "Bold")

    def test_shifted_punctuation_aliases_detect_the_same_shortcut(self):
        for mac in (False, True):
            helpers = load_shortcut_helpers(mac=mac)
            for base, glyph in ((",", "<"), (".", ">")):
                with self.subTest(mac=mac, key=base):
                    self.assertEqual(
                        helpers.normalize_shortcut(f"Ctrl+Shift+{base}"),
                        helpers.normalize_shortcut(f"Shift+Ctrl+{glyph}"),
                    )
                    self.assertNotEqual(
                        helpers.normalize_shortcut(f"Ctrl+{base}"),
                        helpers.normalize_shortcut(f"Ctrl+{glyph}"),
                    )


if __name__ == "__main__":
    unittest.main()
