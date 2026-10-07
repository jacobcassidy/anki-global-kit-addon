"""Exercise collection safety guards and note-type update payloads."""

from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from anki_stubs import OpChanges, load_note_type_service


def existing_type(name="Python (Advance)", *, kind=0, templates=3):
    return {
        "id": 42, "name": name, "type": kind, "sortf": 1, "css": "user CSS",
        "flds": [{"name": "Question", "ord": 0}, {"name": "Custom Field", "ord": 1}],
        "tmpls": [{"name": f"User Card {ordinal + 1}", "ord": ordinal,
                   "qfmt": "user front", "afmt": "user back"} for ordinal in range(templates)],
    }


class Models:
    """Stateful stand-in for the documented col.models methods used by the service."""

    def __init__(self, notetype=None):
        self.types = {notetype["name"]: deepcopy(notetype)} if notetype else {}
        self.notes = {}
        self.cards = []
        self.writes = []
        self.fail_name = None

    def all_names_and_ids(self):
        return [SimpleNamespace(name=n["name"], id=n["id"]) for n in self.types.values()]

    def by_name(self, name):
        # Return the cached object, so accidental in-place mutation is observable.
        return self.types.get(name)

    def use_count(self, notetype):
        return len(self.notes.get(notetype["id"], []))

    def template_use_count(self, notetype_id, ordinal):
        return sum(card["mid"] == notetype_id and card["ord"] == ordinal for card in self.cards)

    def new(self, name):
        return {"id": 0, "name": name, "type": 0, "sortf": 0, "flds": [], "tmpls": [], "css": ""}

    def new_field(self, name):
        return {"name": name, "ord": None}

    def add_field(self, notetype, field):
        notetype["flds"].append(field)

    def new_template(self, name):
        return {"name": name, "ord": None}

    def add_dict(self, notetype):
        if notetype["name"] == self.fail_name:
            raise OSError("injected backend write failure")
        saved = deepcopy(notetype)
        saved["id"] = max((n["id"] for n in self.types.values()), default=0) + 1
        self.types[saved["name"]] = saved
        self.writes.append(("add", saved["name"]))
        return SimpleNamespace(changes=OpChanges(notetype=True))

    def update_dict(self, notetype):
        self.types[notetype["name"]] = deepcopy(notetype)
        self.writes.append(("update", notetype["name"]))
        return OpChanges(notetype=True)

    def remove(self, notetype_id):
        name = next(name for name, nt in self.types.items() if nt["id"] == notetype_id)
        del self.types[name]
        self.writes.append(("remove", name))
        return OpChanges(notetype=True)


class NoteTypeTests(unittest.TestCase):
    def setUp(self):
        self.models = Models(existing_type())
        self.col = SimpleNamespace(models=self.models)
        self.service = load_note_type_service(self.col)

    def replacement_plan(self):
        return self.service.plan_note_type_changes({"Python": {"Advance"}}, {"Python": {"Advance"}})

    def test_existing_types_are_skipped_without_replace_opt_in(self):
        before = deepcopy(self.models.types)
        plan = self.service.plan_note_type_changes({"Python": {"Advance"}})
        result = self.service.apply_note_type_changes(plan, self.col)
        self.assertEqual(result.skipped, ("Python (Advance)",))
        self.assertEqual(self.models.types, before)
        self.assertEqual(self.models.writes, [])

    def test_standard_and_cloze_creation_use_the_requested_fields_and_safe_heading(self):
        topic = "Custom <b>{{Question}}</b>"
        plan = self.service.plan_note_type_changes({topic: {"Advance", "Cloze"}})
        result = self.service.apply_note_type_changes(plan, self.col)
        self.assertEqual(len(result.created), 2)
        for card_format, kind in (("Advance", 0), ("Cloze", 1)):
            nt = self.models.by_name(f"{topic} ({card_format})")
            self.assertEqual(nt["type"], kind)
            self.assertEqual([f["name"] for f in nt["flds"]], self.service.FORMATS[card_format]["fields"])
            self.assertEqual(len(nt["tmpls"]), 1)
            self.assertIn("Custom &lt;b&gt;&#123;&#123;Question&#125;&#125;&lt;/b&gt;", nt["tmpls"][0]["qfmt"])
            self.assertIn("_anki-global-kit.min.js", nt["tmpls"][0]["qfmt"])
        self.assertTrue(result.changes.notetype)

    def test_replacement_keeps_identity_fields_sort_order_notes_and_cached_source(self):
        self.models.notes[42] = [["original question", "custom value"]]
        old = self.models.by_name("Python (Advance)")
        before = deepcopy(old)
        notes = deepcopy(self.models.notes)
        result = self.service.apply_note_type_changes(self.replacement_plan(), self.col)
        new = self.models.by_name("Python (Advance)")
        self.assertEqual(new["id"], 42)
        self.assertEqual(new["sortf"], 1)
        self.assertEqual(new["flds"][:2], before["flds"])
        self.assertEqual(self.models.notes, notes)
        self.assertEqual(old, before)
        self.assertEqual(new["tmpls"][0]["ord"], 0)
        self.assertEqual(len(new["tmpls"]), 1)
        self.assertEqual(result.overwritten, ("Python (Advance)",))
        self.assertEqual(self.models.writes, [("update", "Python (Advance)")])

    def test_cloze_card_ordinals_do_not_count_as_removed_templates(self):
        nt = existing_type("Python (Cloze)", kind=1, templates=1)
        self.models.types = {nt["name"]: nt}
        self.models.cards = [{"mid": 42, "ord": 2}, {"mid": 42, "ord": 7}]
        plan = self.service.plan_note_type_changes({"Python": {"Cloze"}}, {"Python": {"Cloze"}})
        self.assertEqual(plan.replacement_impacts[0].removed_templates, ())
        self.service.apply_note_type_changes(plan, self.col)
        self.assertEqual(self.models.by_name(nt["name"])["type"], 1)

    def test_plan_counts_only_cards_in_the_additional_standard_templates(self):
        self.models.cards = [{"mid": 42, "ord": 0}, {"mid": 42, "ord": 1},
                             {"mid": 42, "ord": 2}, {"mid": 42, "ord": 2}, {"mid": 99, "ord": 1}]
        impact = self.replacement_plan().replacement_impacts[0]
        self.assertEqual([(t.name, t.card_count) for t in impact.removed_templates],
                         [("User Card 2", 1), ("User Card 3", 2)])
        self.assertEqual(impact.removed_card_count, 3)

    def test_changed_replacement_identity_templates_or_card_counts_reject_before_writes(self):
        for change in ("identity", "template", "card_count"):
            with self.subTest(change=change):
                self.setUp()
                plan = self.replacement_plan()
                if change == "identity":
                    self.models.types["Python (Advance)"]["id"] = 99
                elif change == "template":
                    self.models.types["Python (Advance)"]["tmpls"][1]["name"] = "New template name"
                else:
                    self.models.cards.append({"mid": 42, "ord": 1})
                with self.assertRaises(self.service.ReplacementValidationError):
                    self.service.apply_note_type_changes(plan, self.col)
                self.assertEqual(self.models.writes, [])

    def test_changed_collection_and_newly_existing_create_target_reject_before_writes(self):
        plan = self.service.plan_note_type_changes({"Git": {"Advance"}})
        with self.assertRaises(self.service.NoteTypePlanChangedError):
            self.service.apply_note_type_changes(plan, SimpleNamespace(models=self.models))
        self.models.types["Git (Advance)"] = existing_type("Git (Advance)")
        with self.assertRaises(self.service.NoteTypePlanChangedError):
            self.service.apply_note_type_changes(plan, self.col)
        self.assertEqual(self.models.writes, [])

    def test_populated_note_type_cannot_be_deleted(self):
        self.models.notes[42] = [["existing note"]]
        with self.assertRaises(self.service.DeletionValidationError):
            self.service.plan_note_type_changes({}, deletions={"Python": {"Advance"}})
        self.assertEqual(self.models.writes, [])

    def test_delete_revalidates_notes_and_identity_after_confirmation(self):
        for change in ("notes", "identity"):
            with self.subTest(change=change):
                self.setUp()
                plan = self.service.plan_note_type_changes({}, deletions={"Python": {"Advance"}})
                if change == "notes":
                    self.models.notes[42] = [["added during confirmation"]]
                    expected = self.service.DeletionValidationError
                else:
                    self.models.types["Python (Advance)"]["id"] = 99
                    expected = self.service.NoteTypePlanChangedError
                with self.assertRaises(expected):
                    self.service.apply_note_type_changes(plan, self.col)
                self.assertEqual(self.models.writes, [])

    def test_empty_note_type_can_be_deleted(self):
        plan = self.service.plan_note_type_changes({}, deletions={"Python": {"Advance"}})
        result = self.service.apply_note_type_changes(plan, self.col)
        self.assertEqual(result.deleted, ("Python (Advance)",))
        self.assertIsNone(self.models.by_name("Python (Advance)"))

    def test_incompatible_type_and_missing_template_stop_planning(self):
        self.models.types["Python (Advance)"]["type"] = 1
        with self.assertRaises(self.service.ReplacementValidationError):
            self.replacement_plan()
        with patch.object(self.service, "SCRIPT_PATH", self.service.ADDON_DIR / "missing-script.js"):
            with self.assertRaises(self.service.MissingTemplateFilesError):
                self.service.plan_note_type_changes({"Git": {"Advance"}})
        self.assertEqual(self.models.writes, [])

    def test_partial_failure_reports_only_applied_names_and_merged_changes(self):
        self.models.fail_name = "Git (Cloze)"
        plan = self.service.plan_note_type_changes({"Git": {"Advance", "Cloze"}})
        with self.assertRaises(self.service.NoteTypeApplyError) as failure:
            self.service.apply_note_type_changes(plan, self.col)
        self.assertEqual(failure.exception.applied_names, ("Git (Advance)",))
        self.assertTrue(failure.exception.changes.notetype)
        self.assertIsNone(self.models.by_name("Git (Cloze)"))

    def test_no_active_collection_rejects_planning(self):
        self.service.mw.col = None
        with self.assertRaises(self.service.NoActiveCollectionError):
            self.service.plan_note_type_changes({"Git": {"Advance"}})


if __name__ == "__main__":
    unittest.main()
