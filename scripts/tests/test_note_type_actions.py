"""Check destructive-operation confirmations and partial-change reporting."""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from anki_stubs import OpChanges, load_note_type_actions, load_note_type_service


class NoteTypeActionTests(unittest.TestCase):
    def setUp(self):
        notetype = {
            "id": 42, "name": "Python (Advance)", "type": 0,
            "tmpls": [{"name": name, "ord": ordinal} for ordinal, name in enumerate(("First", "Reverse", "Extra"))],
        }
        models = SimpleNamespace(
            all_names_and_ids=lambda: [SimpleNamespace(name=notetype["name"], id=42)],
            by_name=lambda _name: notetype,
            use_count=lambda _nt: 0,
            template_use_count=lambda _id, ordinal: {1: 2, 2: 3}.get(ordinal, 0),
        )
        self.col = SimpleNamespace(models=models)
        self.service = load_note_type_service(self.col)
        self.ui = load_note_type_actions(self.service)
        self.complete = Mock()

    def replace(self):
        self.ui.actions.apply_selected_note_type_changes(
            {"Python": {"Advance"}}, {"Python": {"Advance"}}, {},
            parent=object(), on_complete=self.complete,
        )

    def test_confirmation_lists_removed_template_names_counts_and_cards(self):
        self.replace()
        message = self.ui.confirm.call_args.args[0]
        self.assertIn("Python (Advance)", message)
        self.assertIn("Additional templates to remove: 2 (Reverse, Extra)", message)
        self.assertIn("Cards to remove: 5", message)
        self.assertIn("scheduling will be lost", message)
        self.ui.factory.assert_not_called()
        self.complete.assert_called_once_with(False)

    def test_approval_is_required_before_starting_a_collection_operation(self):
        self.ui.confirm.return_value = True
        self.replace()
        self.ui.factory.assert_called_once()
        self.ui.operation.run_in_background.assert_called_once()
        self.complete.assert_not_called()

    def test_populated_delete_never_reaches_confirmation_or_background_work(self):
        self.col.models.use_count = lambda _nt: 1
        self.ui.actions.apply_selected_note_type_changes(
            {}, {}, {"Python": {"Advance"}}, parent=object(), on_complete=self.complete,
        )
        self.ui.confirm.assert_not_called()
        self.ui.factory.assert_not_called()
        self.assertIn("contains notes", self.ui.warning.call_args.args[0])
        self.complete.assert_called_once_with(False)

    def test_partial_failure_returns_changes_so_anki_can_refresh(self):
        plan = self.service.plan_note_type_changes({"Python": {"Advance"}}, {"Python": {"Advance"}})
        changes = OpChanges(notetype=True)
        error = self.service.NoteTypeApplyError(("Created (Advance)",), OSError("write failed"), changes)
        with patch.object(self.ui.actions, "apply_note_type_changes", side_effect=error):
            outcome = self.ui.actions._apply_plan(self.col, plan)
        self.assertIs(outcome.changes, changes)
        self.assertIs(outcome.error, error)
        self.assertIsNone(outcome.result)


if __name__ == "__main__":
    unittest.main()
