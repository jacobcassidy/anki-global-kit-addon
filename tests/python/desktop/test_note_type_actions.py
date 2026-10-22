"""Check destructive-operation confirmations and partial-change reporting."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tests.support.anki_stubs import (
    OpChanges,
    load_note_type_actions,
    load_note_type_service,
)


class NoteTypeActionTests(unittest.TestCase):
    def setUp(self):
        notetype = {
            "id": 42,
            "name": "Python (Advance)",
            "type": 0,
            "tmpls": [
                {"name": name, "ord": ordinal}
                for ordinal, name in enumerate(("First", "Reverse", "Extra"))
            ],
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
            {"Python": {"Advance"}},
            {"Python": {"Advance"}},
            {},
            parent=object(),
            on_complete=self.complete,
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
            {},
            {},
            {"Python": {"Advance"}},
            parent=object(),
            on_complete=self.complete,
        )
        self.ui.confirm.assert_not_called()
        self.ui.factory.assert_not_called()
        self.assertIn("contains notes", self.ui.warning.call_args.args[0])
        self.complete.assert_called_once_with(False)

    def test_partial_failure_returns_changes_so_anki_can_refresh(self):
        plan = self.service.plan_note_type_changes(
            {"Python": {"Advance"}}, {"Python": {"Advance"}}
        )
        changes = OpChanges(notetype=True)
        error = self.service.NoteTypeApplyError(
            ("Created (Advance)",), OSError("write failed"), changes
        )
        with patch.object(
            self.ui.actions, "apply_note_type_changes", side_effect=error
        ):
            outcome = self.ui.actions._apply_plan(self.col, plan)
        self.assertIs(outcome.changes, changes)
        self.assertIs(outcome.error, error)
        self.assertIsNone(outcome.result)

    def test_additive_syntax_styling_requires_explicit_confirmation(self):
        self.ui.actions.mw.col = self.col
        self.ui.confirm.return_value = True

        with patch.object(
            self.ui.actions, "select_note_types", return_value=("Python (Advance)",)
        ):
            self.ui.actions.enable_syntax_styling(object())

        confirmation = self.ui.confirm.call_args.args[0]
        self.assertIn("Python (Advance)", confirmation)
        self.assertIn('+ @import url("_syntax-highlighting.css");', confirmation)
        self.assertIn(
            "does not change fields, card templates, notes, or cards", confirmation
        )
        self.ui.factory.assert_called_once()
        self.ui.operation.run_in_background.assert_called_once()

    def syntax_types(self):
        self.ui.actions.mw.col = self.col
        types = {
            "Basic": {"id": 1, "css": "user CSS"},
            "Cloze": {"id": 2, "css": "other CSS"},
            "Kit": {"id": 3, "css": '@import url("_syntax-highlighting.css");'},
        }
        self.col.models.all_names_and_ids = lambda: [
            SimpleNamespace(name=name) for name in types
        ]
        self.col.models.by_name = types.get
        return types

    def test_syntax_styles_confirm_all_checked_types_and_omit_enabled_types(self):
        self.syntax_types()
        self.ui.confirm.return_value = True
        with patch.object(
            self.ui.actions, "select_note_types", return_value=("Basic", "Cloze")
        ) as select:
            self.ui.actions.enable_syntax_styling(parent := object())
        select.assert_called_once_with(parent, ["Basic", "Cloze"])
        self.ui.confirm.assert_called_once()
        confirmation = self.ui.confirm.call_args.args[0]
        self.assertIn("2 note types", confirmation)
        self.assertIn("• Basic\n• Cloze", confirmation)
        self.assertNotIn("• Kit", confirmation)
        op = self.ui.factory.call_args.kwargs["op"]
        with patch.object(
            self.ui.actions, "apply_syntax_style_imports", return_value=OpChanges()
        ) as apply:
            op(self.col)
        plans, collection = apply.call_args.args
        self.assertEqual(tuple(plan.name for plan in plans), ("Basic", "Cloze"))
        self.assertIs(collection, self.col)

    def test_canceling_selection_or_confirmation_does_not_start_updates(self):
        for selected, confirmed in (((), True), (("Basic",), False)):
            with self.subTest(selected=selected, confirmed=confirmed):
                self.setUp()
                self.syntax_types()
                self.ui.confirm.return_value = confirmed
                with patch.object(
                    self.ui.actions, "select_note_types", return_value=selected
                ):
                    self.ui.actions.enable_syntax_styling(object())
                self.ui.factory.assert_not_called()
                if not selected:
                    self.ui.confirm.assert_not_called()

    def test_all_types_already_enabled_does_not_open_an_empty_picker(self):
        types = self.syntax_types()
        types["Basic"]["css"] = types["Cloze"]["css"] = types["Kit"]["css"]
        with patch.object(self.ui.actions, "select_note_types") as select:
            self.ui.actions.enable_syntax_styling(object())
        select.assert_not_called()
        self.ui.factory.assert_not_called()
        self.assertIn("already include", self.ui.info.call_args.args[0])

    def test_syntax_styles_partial_failure_refreshes_and_reports_applied_types(self):
        self.syntax_types()
        self.ui.confirm.return_value = True
        with patch.object(
            self.ui.actions, "select_note_types", return_value=("Basic", "Cloze")
        ):
            self.ui.actions.enable_syntax_styling(object())
        changes = OpChanges(notetype=True)
        error = self.service.NoteTypeApplyError(
            ("Basic",), OSError("write failed"), changes
        )
        op = self.ui.factory.call_args.kwargs["op"]
        with patch.object(
            self.ui.actions, "apply_syntax_style_imports", side_effect=error
        ):
            outcome = op(self.col)
        self.assertIs(outcome.changes, changes)
        self.ui.operation.success.call_args.args[0](outcome)
        message = self.ui.warning.call_args.args[0]
        self.assertIn("Applied changes:\nBasic", message)
        self.assertIn("write failed", message)
        self.ui.info.assert_not_called()


if __name__ == "__main__":
    unittest.main()
