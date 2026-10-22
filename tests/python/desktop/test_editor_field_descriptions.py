"""Check Compare hints preserve native descriptions and saved note data."""

import json
import unittest
from copy import deepcopy
from types import SimpleNamespace

from tests.support.anki_stubs import load_editor_integration


class EditorFieldDescriptionTests(unittest.TestCase):
    def test_compare_hint_preserves_other_descriptions_and_saved_fields(self):
        feature = load_editor_integration({}).field_descriptions
        notetype = {
            "tmpls": [{"qfmt": "_anki-global-kit.min.js"}],
            "flds": [
                {"name": "Question", "description": "Enter a question"},
                {"name": "Compare", "description": ""},
                {
                    "name": "Bonus Compare",
                    "description": "Leave blank unless compare is wanted",
                },
            ],
        }
        note = SimpleNamespace(note_type=lambda: notetype, fields=["Question", "", ""])
        before = deepcopy(notetype)
        result = feature.add_compare_placeholder("loadNote();", note, None)
        descriptions = json.loads(result.split("setDescriptions(")[1][:-2])
        self.assertEqual(
            descriptions,
            [
                "Enter a question",
                "Leave blank unless compare is wanted",
                "Leave blank unless compare is wanted",
            ],
        )
        self.assertTrue(result.startswith("loadNote();\n"))
        self.assertEqual(notetype, before)
        self.assertEqual(note.fields, ["Question", "", ""])

        notetype["flds"][1]["description"] = "Custom compare hint"
        self.assertEqual(
            feature.add_compare_placeholder("loadNote();", note, None), "loadNote();"
        )

        notetype["flds"][1]["description"] = ""
        notetype["tmpls"] = [{"qfmt": "{{Question}}"}]
        self.assertEqual(
            feature.add_compare_placeholder("loadNote();", note, None), "loadNote();"
        )

        notetype["tmpls"] = [{"qfmt": "_anki-global-kit.min.js"}]
        notetype["flds"].pop(1)
        self.assertEqual(
            feature.add_compare_placeholder("loadNote();", note, None), "loadNote();"
        )
