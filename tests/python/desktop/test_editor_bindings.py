"""Check native editor bindings preserve fixed actions and avoid ambiguity."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from xml.etree import ElementTree

from tests.support.anki_stubs import load_editor_integration, load_settings_services


class EditorBindingsTests(unittest.TestCase):
    def test_toolbar_defaults_and_theme_inheriting_icons(self):
        settings = load_settings_services().config.get_editor_settings()
        self.assertFalse(settings["anki_editor_blockquote_button"])
        integration = load_editor_integration(settings)
        editor = Mock()
        editor.addButton.side_effect = lambda **kwargs: (
            f'<button data-command="{kwargs["cmd"]}">'
            '<img class="topbut" src="data:image/svg+xml;base64,PHN2Zy8+">'
            "</button>"
        )
        buttons = []
        integration._add_button(buttons, editor)
        toolbar = ElementTree.fromstring(buttons[0])
        self.assertEqual([len(group) for group in toolbar], [3, 3])
        self.assertIn("display: none;", toolbar[1][0].attrib["style"])
        self.assertEqual(len(list(toolbar.iter("img"))), 0)
        for icon in toolbar.iter("button"):
            self.assertIn("background-color: currentColor", icon[0].attrib["style"])
            self.assertIn("mask: url(", icon[0].attrib["style"])
        markdown = editor.addButton.call_args_list[4].kwargs
        self.assertEqual(markdown["tip"], "Convert Markdown")
        integration.QApplication.clipboard.return_value.text.return_value = "**text**"
        markdown["func"](editor)
        editor.web.eval.assert_called_once_with(
            'globalThis.ankiGlobalKitEditor?.convertMarkdown("**text**");'
        )

    def test_default_and_custom_styles_can_be_selected_independently(self):
        settings = load_settings_services().config.get_editor_settings()
        integration = load_editor_integration(settings)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packaged = root / "packaged"
            custom = root / "custom"
            packaged.mkdir()
            custom.mkdir()
            for name in ("editor-fields", "editor-ui"):
                (packaged / f"{name}.min.css").write_text("packaged")
                (custom / f"{name}.css").write_text("custom")
            with (
                patch.object(integration, "EDITOR_STYLES_DIR", packaged),
                patch.object(integration, "USER_FILES_DIR", custom),
            ):
                for name in ("editor-fields", "editor-ui"):
                    for defaults, overrides, expected in (
                        (True, True, "packaged\ncustom"),
                        (True, False, "packaged"),
                        (False, True, "custom"),
                        (False, False, ""),
                    ):
                        with self.subTest(
                            name=name, defaults=defaults, custom=overrides
                        ):
                            self.assertEqual(
                                integration._read_editor_styles(
                                    f"{name}.min.css",
                                    custom_filename=f"{name}.css",
                                    include_default=defaults,
                                    include_custom=overrides,
                                ),
                                expected,
                            )

    def test_hidden_toolbar_keeps_actions_registered_and_shortcuts_active(self):
        settings = load_settings_services(
            config={"anki_editor_toolbar_enabled": False}
        ).config.get_editor_settings()
        integration = load_editor_integration(settings)
        editor = Mock(currentField=0)
        editor.addButton.side_effect = lambda **kwargs: (
            f'<button data-command="{kwargs["cmd"]}"></button>'
        )
        buttons = []
        integration._add_button(buttons, editor)
        self.assertEqual(len(buttons), 1)
        self.assertEqual(editor.addButton.call_count, 6)
        toolbar = ElementTree.fromstring(buttons[0])
        self.assertEqual([len(group) for group in toolbar], [3, 3])
        self.assertTrue(
            all(group.attrib["style"] == "display: none;" for group in toolbar)
        )
        self.assertTrue(
            all(
                "display: none;" in button.attrib["style"]
                for button in toolbar.iter("button")
            )
        )
        integration._add_shortcut([], editor)
        self.assertTrue(
            editor._anki_global_kit_shortcuts["anki_editor_inline_code_shortcut"][
                0
            ].isEnabled()
        )

        settings["anki_editor_toolbar_enabled"] = True
        settings["anki_editor_blockquote_button"] = True
        settings["anki_editor_syntax_highlighting_button"] = False
        buttons.clear()
        integration._add_button(buttons, editor)
        toolbar = ElementTree.fromstring(buttons[0])
        self.assertIn(
            "column-gap: var(--anki-global-kit-toolbar-group-gap, 0.3rem)",
            toolbar.attrib["style"],
        )
        self.assertEqual(toolbar[0].attrib["style"], "display: none;")
        self.assertTrue(
            all(
                group.attrib["style"] == "display: inline-flex;"
                for group in toolbar[1:]
            )
        )
        self.assertTrue(
            all(
                "display: none" not in button.attrib["style"]
                for group in toolbar[1:]
                for button in group
            )
        )
        self.assertIn(
            "--border-left-radius: var(--anki-global-kit-toolbar-group-radius, 5px)",
            toolbar[1][0].attrib["style"],
        )
        self.assertIn("--border-right-radius: 0", toolbar[1][0].attrib["style"])
        self.assertIn("--border-left-radius: 0", toolbar[1][1].attrib["style"])
        self.assertIn(
            "--border-right-radius: var(--anki-global-kit-toolbar-group-radius, 5px)",
            toolbar[1][2].attrib["style"],
        )

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
            "anki_editor_blockquote_shortcut",
            "anki_editor_indent_increase_shortcut",
            "anki_editor_indent_decrease_shortcut",
        ):
            for keys, action in (
                ("Ctrl+Alt+8", "unordered-list"),
                ("Ctrl+Alt+9", "ordered-list"),
                ("Ctrl+Alt+0", "no-list"),
            ):
                with self.subTest(setting=key, shortcut=keys):
                    integration, bindings, editor = self.bindings({key: keys})
                    matches = [
                        callback for shortcut, callback in bindings if shortcut == keys
                    ]
                    self.assertEqual(len(matches), 1)
                    self.assertIs(matches[0].func, integration._toggle_block)
                    self.assertEqual(matches[0].args[-1], action)

    def test_duplicate_saved_custom_shortcuts_register_only_one_handler(self):
        _, bindings, editor = self.bindings(
            {
                "anki_editor_inline_code_shortcut": "Alt+K",
                "anki_editor_indent_increase_shortcut": "Alt+K",
            }
        )
        self.assertEqual(
            sum(
                shortcut.isEnabled() and keys == "Alt+K"
                for shortcut, keys in editor._anki_global_kit_shortcuts.values()
            ),
            1,
        )

    def test_configured_indent_replaces_native_binding_for_the_same_action(self):
        settings = load_settings_services().config.get_editor_settings()
        integration = load_editor_integration(settings)
        bindings = [("Ctrl+Alt+.", lambda: None)]
        editor = Mock(currentField=0)
        integration._add_shortcut(bindings, editor)
        self.assertFalse(any(keys == "Ctrl+Alt+." for keys, _ in bindings))
        shortcut, keys = editor._anki_global_kit_shortcuts[
            "anki_editor_indent_increase_shortcut"
        ]
        self.assertEqual(keys, "Ctrl+Alt+.")
        shortcut.callback()
        editor.web.eval.assert_called_once_with(
            "globalThis.ankiGlobalKitEditor?.indent();"
        )

    def test_shifted_glyph_alias_does_not_create_a_second_native_handler(self):
        integration, bindings, editor = self.bindings(
            {
                "anki_editor_inline_code_shortcut": "Ctrl+Shift+>",
                "anki_editor_indent_increase_shortcut": "Ctrl+Shift+.",
            }
        )
        matches = [
            shortcut
            for shortcut, keys in editor._anki_global_kit_shortcuts.values()
            if shortcut.isEnabled()
            and integration.normalize_shortcut(keys) == "Ctrl+Shift+."
        ]
        self.assertEqual(len(matches), 1)

    def test_settings_refresh_rebinds_and_disables_existing_editor_shortcuts(self):
        settings = load_settings_services().config.get_editor_settings()
        integration = load_editor_integration(settings)
        editor = Mock(currentField=0)
        integration._add_shortcut([], editor)
        shortcut, _keys = editor._anki_global_kit_shortcuts[
            "anki_editor_inline_code_shortcut"
        ]
        settings["anki_editor_inline_code_shortcut"] = "Alt+K"
        integration.refresh_open_editors()
        self.assertIs(
            editor._anki_global_kit_shortcuts["anki_editor_inline_code_shortcut"][0],
            shortcut,
        )
        self.assertEqual(shortcut.key, "Alt+K")
        self.assertTrue(
            any(
                '"anki_editor_inline_code_shortcut":"Alt+K"' in call.args[0]
                for call in editor.web.eval.call_args_list
            )
        )
        editor.web.eval.reset_mock()
        shortcut.callback()
        editor.web.eval.assert_called_once_with(
            "globalThis.ankiGlobalKitEditor?.toggleInlineCode();"
        )
        settings["anki_editor_inline_code_shortcut_enabled"] = False
        integration.refresh_open_editors()
        self.assertFalse(shortcut.isEnabled())
        editor.web.eval.reset_mock()
        shortcut.callback()
        editor.web.eval.assert_not_called()
        settings["anki_editor_inline_code_shortcut_enabled"] = True
        integration.refresh_open_editors()
        self.assertTrue(shortcut.isEnabled())
        self.assertEqual(
            set(editor._anki_global_kit_shortcuts),
            {
                "anki_editor_inline_code_shortcut",
                "anki_editor_blockquote_shortcut",
                "anki_editor_indent_increase_shortcut",
                "anki_editor_indent_decrease_shortcut",
                "anki_editor_syntax_highlighting_shortcut",
            },
        )

    def test_blockquote_default_is_configurable_and_can_be_disabled(self):
        settings = load_settings_services().config.get_editor_settings()
        integration = load_editor_integration(settings)
        editor = Mock(currentField=0)
        bindings = []
        integration._add_shortcut(bindings, editor)
        shortcut, keys = editor._anki_global_kit_shortcuts[
            "anki_editor_blockquote_shortcut"
        ]
        self.assertEqual(keys, "Ctrl+/")
        self.assertIsNone(integration.editor_fixed_shortcut_action(keys))
        shortcut.callback()
        editor.web.eval.assert_called_once_with(
            'globalThis.ankiGlobalKitEditor?.toggleBlock("blockquote");'
        )
        settings["anki_editor_blockquote_shortcut_enabled"] = False
        integration.refresh_open_editors()
        self.assertFalse(shortcut.isEnabled())
        self.assertNotIn("Ctrl+/", [keys for keys, _callback in bindings])

    def test_refresh_preserves_fixed_actions_and_prunes_deleted_editors(self):
        settings = load_settings_services().config.get_editor_settings()
        integration = load_editor_integration(settings)
        editor = Mock(currentField=0)
        integration._add_shortcut([], editor)
        settings["anki_editor_inline_code_shortcut"] = "Ctrl+Alt+8"
        integration.refresh_open_editors()
        self.assertFalse(
            editor._anki_global_kit_shortcuts["anki_editor_inline_code_shortcut"][
                0
            ].isEnabled()
        )
        editor.web.eval.reset_mock()
        integration.sip.isdeleted = lambda widget: widget is editor.widget
        integration.refresh_open_editors()
        editor.web.eval.assert_not_called()
        self.assertNotIn(editor, integration._open_editors)

    def test_native_list_keys_are_removed_and_new_keys_registered_once(self):
        settings = load_settings_services().config.get_editor_settings()
        integration = load_editor_integration(settings)
        bindings = [(key, lambda: None) for key in ("Ctrl+,", "Ctrl+.", "Ctrl+Alt+8")]
        integration._add_shortcut(bindings, Mock(currentField=0))
        keys = [key for key, _ in bindings]
        self.assertNotIn("Ctrl+,", keys)
        self.assertNotIn("Ctrl+.", keys)
        for key in ("Ctrl+Alt+8", "Ctrl+Alt+9", "Ctrl+Alt+0"):
            self.assertEqual(keys.count(key), 1)


if __name__ == "__main__":
    unittest.main()
