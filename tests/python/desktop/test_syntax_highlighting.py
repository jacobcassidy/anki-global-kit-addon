"""Tests for the headless, isolated syntax renderer."""

import json
import sys
import unittest
from copy import deepcopy
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

import pygments

from scripts.addon_module_loader import load_addon_module
from tests.support.anki_stubs import (
    load_editor_integration,
    load_module,
)


class SyntaxRenderingTests(unittest.TestCase):
    def setUp(self):
        self.renderer = load_addon_module("desktop.syntax_highlighting.rendering")

    def test_deck_language_memory_is_collection_scoped_and_validated(self):
        memory = load_addon_module("desktop.syntax_highlighting.language_memory")

        class Collection:
            def __init__(self):
                self.config = {
                    "unrelated": "preserved",
                    "anki_global_kit.syntax_highlighting.deck_languages": {
                        "12": "python",
                        "bad": "sql",
                        "14": 4,
                    },
                }

            def get_config(self, key, default=None):
                return self.config.get(key, default)

            def set_config(self, key, value):
                self.config[key] = value

        collection = Collection()
        self.assertEqual(
            memory.remembered_language(collection, 12, ["python"]), "python"
        )
        self.assertIsNone(memory.remembered_language(collection, 12, ["sql"]))
        self.assertTrue(
            memory.remember_language(collection, 13, "sql", {"python", "sql"})
        )
        self.assertEqual(
            collection.config["anki_global_kit.syntax_highlighting.deck_languages"],
            {"12": "python", "13": "sql"},
        )
        self.assertEqual(collection.config["unrelated"], "preserved")
        self.assertFalse(
            memory.remember_language(collection, None, "python", {"python"})
        )
        self.assertFalse(
            memory.remember_language(collection, 13, "unsupported", {"python"})
        )

    def test_preserves_whitespace_and_escapes_source(self):
        source = "\tprint('<tag>')\n\n"

        html, language = self.renderer.render_code(source, "py")

        self.assertEqual(language, "python")
        self.assertIn("\t", html)
        self.assertIn("\n\n", html)
        self.assertIn("&lt;tag&gt;", html)

    def test_rejects_unsupported_and_too_large_input(self):
        with self.assertRaises(self.renderer.SyntaxHighlightingError):
            self.renderer.render_code("text", "not-a-language")

        with self.assertRaises(self.renderer.SyntaxHighlightingError):
            self.renderer.render_code("x" * 50_001, "python")

    def test_active_cloze_markup_stays_contiguous_and_literal_mode_is_escaped(self):
        source = "answer = {{c1::42::the answer}}\n"

        active, _language = self.renderer.render_code(source, "python", "active")
        literal, _language = self.renderer.render_code(source, "python", "literal")

        self.assertIn("{{c1::42::the answer}}", active)
        self.assertNotIn(
            "<span", active.split("{{c1::42::the answer}}", 1)[1].split("\n", 1)[0]
        )
        self.assertIn("&#123;&#123;c1::42::the answer&#125;&#125;", literal)
        self.assertNotIn("{{c1::", literal)
        with self.assertRaises(self.renderer.SyntaxHighlightingError):
            self.renderer.render_code(source, "python", "unsafe")

    def test_does_not_replace_an_existing_pygments_installation(self):
        self.renderer.render_code("print('ok')", "python")

        self.assertIs(sys.modules["pygments"], pygments)

        self.renderer.render_code("print('again')", "python")
        self.assertIs(sys.modules["pygments"], pygments)

    def test_theme_services_import_without_qt(self):
        themes = load_addon_module("desktop.syntax_highlighting.themes")

        self.assertIn("--global-kit-syntax-background", themes.generate_theme_css())
        available = themes.available_themes()
        self.assertIn(("cassidy-dark", "Cassidy Dark"), available)
        self.assertEqual(
            available, sorted(available, key=lambda item: item[1].casefold())
        )
        for theme_id, _name in available:
            css = themes.generate_theme_css(theme_id)
            self.assertIn(".global-kit-code-block", css)
            self.assertRegex(css, r"--global-kit-syntax-background: #[0-9a-fA-F]{6};")

        self.assertFalse(
            any(name == "aqt" or name.startswith("aqt.") for name in sys.modules)
        )

    def test_theme_labels_and_preview_use_the_resolved_palette(self):
        themes = load_addon_module("desktop.syntax_highlighting.themes")
        choices = dict(themes.available_themes())
        self.assertEqual(choices["pygments:github-dark"], "GitHub Dark")
        self.assertEqual(choices["pygments:friendly_grayscale"], "Friendly Grayscale")
        self.assertEqual(choices["pygments:one-dark"], "One Dark")
        for theme_id in ("pygments:monokai", "pygments:dracula"):
            preset = themes.resolve_preset(theme_id)
            html = themes.theme_preview_html(preset)
            self.assertIn(f"background-color: {preset['colors']['background']}", html)
            self.assertIn(f"color: {preset['colors']['keyword']}", html)
            self.assertNotIn("var(", html)
            self.assertNotIn(":is(", html)

    def test_cassidy_keywords_and_declarations_have_independent_theme_colors(self):
        themes = load_addon_module("desktop.syntax_highlighting.themes")
        preset = themes.resolve_preset("cassidy-dark")
        self.assertEqual(preset["colors"]["keyword"], "#ef9182")
        self.assertEqual(preset["colors"]["declaration"], "#92c1fd")
        css = themes.generate_theme_css()
        declaration_rule = css.split(".global-kit-code-block :is(.kd) {", 1)[1]
        declaration_rule = declaration_rule.split("}", 1)[0]
        self.assertIn("color: var(--global-kit-syntax-declaration);", declaration_rule)
        keyword_selectors = themes._TOKEN_SELECTORS["keyword"].split(", ")
        self.assertIn(".k", keyword_selectors)
        self.assertNotIn(".kd", keyword_selectors)
        highlighted, _language = self.renderer.render_code(
            "const value = 1;", "javascript"
        )
        self.assertIn('<span class="kd">const</span>', highlighted)

    def test_legacy_synced_themes_keep_their_colors_and_styles_during_migration(self):
        themes = load_addon_module("desktop.syntax_highlighting.themes")
        preferences = load_addon_module("desktop.syntax_highlighting.preferences")
        legacy = themes.resolve_preset("cassidy-dark")
        legacy["colors"].pop("declaration")
        legacy["colors"]["keyword"] = "#92c1fd"
        legacy["styles"] = {"bold": ["keyword"], "italic": []}
        legacy["revision"] = 7
        original = deepcopy(legacy)
        config = {
            preferences.THEMES_KEY: {"version": 1, "light": legacy, "dark": legacy}
        }
        collection = SimpleNamespace(
            get_config=lambda key, default=None: config.get(key, default),
            set_config=lambda key, value: config.__setitem__(key, value),
        )

        migrated = preferences.get_themes(collection)
        self.assertEqual(migrated["light"]["colors"]["declaration"], "#92c1fd")
        self.assertIn("declaration", migrated["light"]["styles"]["bold"])
        self.assertEqual(legacy, original)
        preferences.set_themes(collection, migrated)
        self.assertEqual(config[preferences.THEMES_KEY]["version"], 2)
        self.assertEqual(preferences.get_themes(collection)["light"]["revision"], 7)

        updated = themes.resolve_preset("cassidy-dark")
        preferences.set_themes(collection, {"light": updated, "dark": updated})
        self.assertEqual(preferences.get_themes(collection)["light"]["revision"], 8)
        self.assertEqual(
            preferences.get_themes(collection)["light"]["colors"], updated["colors"]
        )
        config[preferences.THEMES_KEY]["version"] = 3
        self.assertEqual(preferences.get_themes(collection), {})

    def test_mode_themes_do_not_repeat_block_and_token_rules(self):
        themes = load_addon_module("desktop.syntax_highlighting.themes")
        light = themes.resolve_preset("pygments:default")
        dark = themes.resolve_preset("pygments:monokai")
        light["styles"] = {"bold": ["keyword"], "italic": []}
        dark["styles"] = {"bold": [], "italic": ["comment"]}
        overrides = themes.generate_theme_pair_css(light, dark)
        combined = themes.generate_theme_css() + overrides

        self.assertNotIn(".global-kit-code-block", overrides)
        self.assertEqual(combined.count(".global-kit-code-block {"), 1)
        for selectors in themes._TOKEN_SELECTORS.values():
            self.assertEqual(
                combined.count(f".global-kit-code-block :is({selectors}) {{"), 1
            )
        light_css, dark_css = overrides.split(".nightMode,", 1)
        self.assertIn(
            f"--global-kit-syntax-background: {light['colors']['background']};",
            light_css,
        )
        self.assertIn(
            f"--global-kit-syntax-background: {dark['colors']['background']};", dark_css
        )
        self.assertIn("--global-kit-syntax-keyword-weight: 700;", light_css)
        self.assertIn("--global-kit-syntax-keyword-weight: 400;", dark_css)
        self.assertIn("--global-kit-syntax-comment-style: normal;", light_css)
        self.assertIn("--global-kit-syntax-comment-style: italic;", dark_css)
        self.assertNotIn(":host-context", overrides)
        editor_css = themes.generate_theme_pair_css(light, dark, editor=True)
        self.assertIn(":host-context(.nightMode) anki-editable", editor_css)
        self.assertIn(":root,\nanki-editable {", editor_css)
        self.assertNotIn(".global-kit-code-block", editor_css)

    def test_highlight_button_tooltip_uses_the_enabled_shortcut(self):
        settings = {
            "anki_editor_syntax_highlighting_shortcut_enabled": True,
            "anki_editor_syntax_highlighting_shortcut": "Alt+S",
        }
        feature = load_editor_integration(settings).syntax_highlighting
        self.assertEqual(feature.highlight_code_tip(settings), "Highlight Code (Alt+S)")
        settings["anki_editor_syntax_highlighting_shortcut_enabled"] = False
        self.assertEqual(feature.highlight_code_tip(settings), "Highlight Code")

    def test_language_menu_is_anchored_below_button_with_webview_zoom(self):
        settings = {
            "anki_editor_syntax_highlighting_languages": ["python"],
            "anki_editor_syntax_highlighting_default_language": "python",
        }
        feature = load_editor_integration(settings).syntax_highlighting
        load_module(
            "kit.desktop.syntax_highlighting.rendering",
            "addon/desktop/syntax_highlighting/rendering.py",
        )
        qt = ModuleType("aqt.qt")
        qt.QMenu = Mock()
        qt.QCursor = Mock()
        qt.QPoint = lambda x, y: (x, y)
        editor = Mock()
        editor._anki_global_kit_language_override = None
        editor.web.zoomFactor.return_value = 1.5
        editor.web.mapToGlobal.return_value = (515, 645)
        with (
            patch.dict(sys.modules, {"aqt.qt": qt}),
            patch.object(feature, "get_editor_settings", return_value=settings),
        ):
            feature.show_language_menu(editor)
            callback = editor.web.evalWithCallback.call_args.args[1]
            qt.QMenu.return_value.exec.assert_not_called()
            callback([10, 30])
        editor.web.mapToGlobal.assert_called_once_with((15, 45))
        qt.QMenu.return_value.exec.assert_called_once_with((515, 645))

    def test_resolved_themes_are_validated_and_collection_scoped(self):
        preferences = load_addon_module("desktop.syntax_highlighting.preferences")
        themes = load_addon_module("desktop.syntax_highlighting.themes")

        class Collection:
            def __init__(self):
                self.config = {"unrelated": "preserved"}

            def get_config(self, key, default=None):
                return self.config.get(key, default)

            def set_config(self, key, value):
                self.config[key] = value

        collection = Collection()
        preset = themes.resolve_preset("pygments:monokai")
        preferences.set_themes(collection, {"light": preset, "dark": preset})
        stored = preferences.get_themes(collection)

        self.assertEqual(stored["light"]["id"], "pygments:monokai")
        self.assertEqual(stored["light"]["revision"], 1)
        self.assertIn(
            ".nightMode",
            themes.generate_theme_pair_css(stored["light"], stored["dark"]),
        )
        self.assertEqual(collection.config["unrelated"], "preserved")
        preferences.set_themes(collection, stored)
        self.assertEqual(preferences.get_themes(collection)["light"]["revision"], 1)
        preferences.set_themes(collection, stored, {"light"})
        self.assertEqual(preferences.get_themes(collection)["light"]["revision"], 2)
        self.assertEqual(preferences.get_themes(collection)["dark"]["revision"], 1)
        malformed = dict(
            preset,
            colors={**preset["colors"], "background": "url(example)"},
        )
        with self.assertRaises(ValueError):
            themes.validate_resolved_theme(malformed)

    def test_only_bundled_lexers_are_enumerated(self):
        languages = self.renderer.available_languages()

        self.assertGreater(len(languages), 500)
        self.assertTrue(
            any(name == "Python" and alias == "python" for name, alias, _ in languages)
        )

    def test_markdown_bridge_uses_pygments_and_leaves_unsupported_code_plain(self):
        integration = load_editor_integration({})
        feature = integration.syntax_highlighting
        load_module("kit.desktop.paths", "addon/desktop/paths.py")
        load_module(
            "kit.desktop.syntax_highlighting",
            "addon/desktop/syntax_highlighting/__init__.py",
        )
        rendered, oversized = feature._render_markdown_blocks(
            [
                {"index": 0, "source": "print('<tag>')", "language": "py"},
                {
                    "index": 1,
                    "source": "<plain>",
                    "language": "not-a-real-language",
                },
                {"index": 2, "source": "x" * 50_001, "language": "python"},
            ]
        )

        self.assertEqual(len(rendered), 1)
        self.assertEqual(rendered[0]["index"], 0)
        self.assertEqual(rendered[0]["language"], "python")
        self.assertIn("&lt;", rendered[0]["html"])
        self.assertEqual(oversized, 1)

    def test_deck_resolution_uses_add_destination_and_filtered_card_original_deck(self):
        integration = load_editor_integration({})
        feature = integration.syntax_highlighting
        add_editor = type(
            "Editor",
            (),
            {
                "addMode": True,
                "parentWindow": type(
                    "AddWindow",
                    (),
                    {
                        "deck_chooser": type(
                            "DeckChooser", (), {"selected_deck_id": 19}
                        )()
                    },
                )(),
            },
        )()
        filtered_editor = type(
            "Editor",
            (),
            {"addMode": False, "card": type("Card", (), {"odid": 7, "did": 88})()},
        )()

        self.assertEqual(feature._resolve_editor_deck_id(add_editor), 19)
        self.assertEqual(feature._resolve_editor_deck_id(filtered_editor), 7)

    def test_language_memory_is_written_only_after_current_successful_explicit_apply(
        self,
    ):
        settings = {
            "anki_editor_syntax_highlighting_remember_language_per_deck": True,
            "anki_editor_syntax_highlighting_languages": ["python"],
        }
        integration = load_editor_integration(settings)
        feature = integration.syntax_highlighting
        load_module("kit.desktop.paths", "addon/desktop/paths.py")
        load_module(
            "kit.desktop.syntax_highlighting",
            "addon/desktop/syntax_highlighting/__init__.py",
        )

        class Collection:
            def __init__(self):
                self.config = {}

            def get_config(self, key, default=None):
                return self.config.get(key, default)

            def set_config(self, key, value):
                self.config[key] = value

        collection = Collection()
        editor = type(
            "Editor",
            (),
            {
                "addMode": True,
                "web": None,
                "mw": type("Anki", (), {"col": collection})(),
                "parentWindow": type(
                    "AddWindow",
                    (),
                    {"deck_chooser": type("Chooser", (), {"selected_deck_id": 19})()},
                )(),
            },
        )()
        feature._PENDING_EXPLICIT_APPLIES["41"] = (editor, 19, "python")
        feature._on_highlight_applied(
            "anki-global-kit:syntax-highlight-applied:"
            + json.dumps({"id": "41", "language": "python", "applied": False}),
            editor,
        )
        self.assertEqual(collection.config, {})

        feature._PENDING_EXPLICIT_APPLIES["42"] = (editor, 19, "python")

        feature._on_highlight_applied(
            "anki-global-kit:syntax-highlight-applied:"
            + json.dumps({"id": "42", "language": "python", "applied": True}),
            editor,
        )

        self.assertEqual(
            collection.config["anki_global_kit.syntax_highlighting.deck_languages"][
                "19"
            ],
            "python",
        )

    def test_editor_language_priority_includes_full_pygments_topic_aliases(self):
        settings = {
            "anki_editor_syntax_highlighting_languages": ["python", "cpp"],
            "anki_editor_syntax_highlighting_default_language": "python",
            "anki_editor_syntax_highlighting_remember_language_per_deck": False,
        }
        integration = load_editor_integration(settings)
        feature = integration.syntax_highlighting
        load_module("kit.desktop.paths", "addon/desktop/paths.py")
        load_module(
            "kit.desktop.syntax_highlighting",
            "addon/desktop/syntax_highlighting/__init__.py",
        )
        editor = type("Editor", (), {"mw": type("Anki", (), {"col": None})()})()

        language, explicit = feature._resolve_authoring_language(
            {
                "language": "python",
                "topicText": "C++ Language Notes",
                "existingLanguage": "",
            },
            editor,
            None,
            False,
        )
        self.assertEqual((language, explicit), ("cpp", False))

        language, explicit = feature._resolve_authoring_language(
            {
                "language": "python",
                "topicText": "Python",
                "existingLanguage": "rust",
            },
            editor,
            None,
            False,
        )
        self.assertEqual((language, explicit), ("rust", False))

        language, explicit = feature._resolve_authoring_language(
            {
                "language": "cpp",
                "topicText": "Python",
                "existingLanguage": "rust",
            },
            editor,
            None,
            True,
        )
        self.assertEqual((language, explicit), ("cpp", True))


if __name__ == "__main__":
    unittest.main()
