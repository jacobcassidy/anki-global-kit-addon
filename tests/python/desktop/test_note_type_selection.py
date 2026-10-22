"""Exercise action checkbox transitions through the Note Types panel."""

import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from tests.support.anki_startup import make_startup_stubs
from tests.support.anki_stubs import load_module, load_note_type_service


class Signal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in self.callbacks:
            callback(*args)


class CheckBox:
    def __init__(self, _parent):
        self.checked = False
        self.enabled = True
        self.toggled = Signal()

    def isChecked(self):
        return self.checked

    def setChecked(self, checked):
        if self.checked != checked:
            self.checked = checked
            self.toggled.emit(checked)

    def isEnabled(self):
        return self.enabled

    def setEnabled(self, enabled):
        self.enabled = enabled

    def setToolTip(self, _text):
        pass


class NoteTypeSelectionTests(unittest.TestCase):
    def setUp(self):
        stubs = make_startup_stubs(mac=False)
        prefix = "kit_selection.desktop"
        stubs.qt.Qt = SimpleNamespace(
            AlignmentFlag=SimpleNamespace(AlignTop=1, AlignCenter=2),
            TextFormat=SimpleNamespace(PlainText=0),
        )
        stubs.qt.QCheckBox = CheckBox

        for name in ("QWidget", "QVBoxLayout", "QHBoxLayout", "QLabel", "QPushButton"):
            setattr(stubs.qt, name, Mock())

        buttons = {}

        def button(text, _parent):
            widget = Mock()
            widget.clicked = Signal()
            buttons[text] = widget
            return widget

        stubs.qt.QPushButton.side_effect = button
        collection = SimpleNamespace(
            models=SimpleNamespace(
                all_names_and_ids=lambda: [SimpleNamespace(name="Python (Advance)")],
                by_name=lambda _name: {"id": 42},
                use_count=lambda _notetype: 0,
            )
        )
        stubs.modules["aqt"].mw.col = collection
        stubs.modules["aqt"].mw.addonManager = Mock()
        stubs.modules["aqt"].mw.addonManager.getConfig.return_value = {}
        service = load_note_type_service(collection)
        table = Mock()
        apply = Mock()
        replacements = {
            "config.constants": {"ADDON_PACKAGE_NAME": "kit"},
            "config.service": {"save_note_type_selections": Mock()},
            "note_types.service": {
                "FORMATS": service.FORMATS,
                "TOPICS": service.TOPICS,
            },
            "ui.constants": {"NOTE_TYPES_ROW_PADDING": 2, "ZERO_MARGINS": (0, 0, 0, 0)},
            "ui.help": {"HelpIndicator": Mock()},
            "settings.pages.note_types.actions": {
                "apply_selected_note_type_changes": apply
            },
            "settings.pages.note_types.table": {
                "NoteTypesTable": Mock(return_value=table)
            },
        }

        for suffix, attributes in replacements.items():
            module = ModuleType(f"{prefix}.{suffix}")
            module.__dict__.update(attributes)
            stubs.modules[module.__name__] = module

        with patch.dict(sys.modules, stubs.modules):
            panel = load_module(
                f"{prefix}.settings.pages.note_types.note_types",
                "addon/desktop/settings/pages/note_types/note_types.py",
            )

        panel.build_note_types_tab(Mock())
        row = 3 + service.TOPICS.index("Python")
        self.checks = {
            call.args[1]: call.args[2]
            for call in table.make_cell.call_args_list
            if call.args[0] == row and call.args[1] in (2, 3, 4)
        }
        self.apply = apply
        self.apply_button = buttons["Apply Selected Changes"]

    def test_replace_after_selecting_delete_still_reaches_confirmation(self):
        create, replace, delete = (self.checks[column] for column in (2, 3, 4))
        self.assertTrue(create.isChecked())
        self.assertFalse(create.isEnabled())
        delete.setChecked(True)
        self.assertFalse(create.isChecked())
        replace.setChecked(True)
        self.assertFalse(delete.isChecked())
        self.apply_button.clicked.emit()
        selections, overwrites, deletions = self.apply.call_args.args
        self.assertEqual(selections["Python"], {"Advance"})
        self.assertEqual(overwrites["Python"], {"Advance"})
        self.assertEqual(deletions["Python"], set())

    def test_delete_after_selecting_replace_does_not_also_replace(self):
        self.checks[3].setChecked(True)
        self.checks[4].setChecked(True)
        self.apply_button.clicked.emit()
        selections, overwrites, deletions = self.apply.call_args.args
        self.assertEqual(selections["Python"], set())
        self.assertEqual(overwrites["Python"], set())
        self.assertEqual(deletions["Python"], {"Advance"})
