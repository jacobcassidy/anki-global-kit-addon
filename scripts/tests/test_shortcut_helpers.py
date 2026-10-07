"""Check normalization agrees with shifted punctuation shortcut matching."""

import unittest

from anki_stubs import load_shortcut_helpers


class ShortcutHelpersTests(unittest.TestCase):
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
