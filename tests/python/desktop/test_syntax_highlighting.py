"""Tests for the headless, isolated syntax renderer."""

import json
import sys
import unittest

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

        self.assertIn("--agk-syntax-background", themes.generate_theme_css())
        available = themes.available_themes()
        self.assertIn(("cassidy-dark", "Cassidy Dark"), available)
        self.assertEqual(
            available, sorted(available, key=lambda item: item[1].casefold())
        )
        for theme_id, _name in available:
            css = themes.generate_theme_css(theme_id)
            self.assertIn(".agk-code-block", css)
            self.assertRegex(css, r"--agk-syntax-background: #[0-9a-fA-F]{6};")

        self.assertFalse(
            any(name == "aqt" or name.startswith("aqt.") for name in sys.modules)
        )

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
