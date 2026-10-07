"""Compose and manage the Anki Global Kit settings dialog."""

from __future__ import annotations

from aqt import gui_hooks, mw
from aqt.qt import (
    QAction,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QIcon,
    QLabel,
    QPushButton,
    QTabWidget,
    QTimer,
    Qt,
    QVBoxLayout,
)

from ..services.assets import update_assets_for_profile
from ..services.config import get_editor_settings, get_settings, write_settings
from ..configs.constants import (
    DEFAULT_SETTINGS,
    SECTION_SPACING,
    SHORTCUT_MODIFIER_HINT,
    SHARED_ASSET_DIR,
)
from .theme import get_theme_color
from ..helpers.shortcuts import (
    anki_editor_format_shortcut_warnings,
    anki_shortcut_warnings,
    format_shortcut,
    normalize_shortcut,
    reserved_shortcut_warnings,
    shortcut_has_required_modifier,
)
from ..features.about import build_about_tab
from ..features.cards import SHORTCUT_DEFINITIONS, build_cards_tab
from .shortcut_rows import style_shortcut_option
from ..features.changelog import build_changelog_tab
from ..features.editor import build_editor_tab
from ..features.editor.editor_fields import INDENTATION_SHORTCUT_DEFINITIONS
from ..features.help import build_help_tab
from ..features.note_types import build_note_types_tab
from .widgets import CardShortcutInput


def open_settings() -> None:
    """Show the settings dialog and coordinate its settings pages."""
    dialog = QDialog(mw)
    dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
    dialog.setStyleSheet(
        "QTextBrowser { "
        f"background-color: {get_theme_color('CANVAS_ELEVATED')}; "
        f"border: 1px solid {get_theme_color('BORDER_SUBTLE')}; "
        "border-radius: 6px; "
        "}"
    )
    dialog.setWindowTitle("Anki Global Kit Settings")
    dialog.setMinimumWidth(560)
    layout = QVBoxLayout(dialog)
    layout.setSpacing(SECTION_SPACING)
    tabs = QTabWidget(dialog)
    layout.addWidget(tabs)

    current_settings = get_settings()
    current_settings.update(get_editor_settings())

    cards = build_cards_tab(dialog, current_settings)
    tabs.addTab(cards.widget, "Cards")
    editor = build_editor_tab(dialog, current_settings)
    tabs.addTab(editor.widget, "Editor")

    settings_note = QLabel(
        "Sync your collection with AnkiWeb to apply changes on your other devices."
    )
    settings_note.setWordWrap(True)
    settings_note.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    layout.addWidget(settings_note)

    note_types = build_note_types_tab(dialog)
    tabs.addTab(note_types.widget, "Note Types")
    tabs.addTab(build_changelog_tab(dialog), "Changelog")
    tabs.addTab(build_about_tab(dialog), "About")
    tabs.addTab(build_help_tab(dialog), "Help")

    def update_sync_note_visibility(index: int) -> None:
        settings_note.setVisible(index in (0, 1, 2))

    tabs.currentChanged.connect(update_sync_note_visibility)
    update_sync_note_visibility(tabs.currentIndex())

    all_controls = {**cards.controls, **editor.controls}
    fields = cards.fields
    editor_fields = editor.fields
    markdown_shortcut_definitions = SHORTCUT_DEFINITIONS
    markdown_shortcut_inputs = fields.shortcut_inputs
    markdown_shortcut_checkboxes = fields.shortcut_enabled
    markdown_shortcut_option_checkboxes = fields.shortcut_option_checkboxes
    question_markdown_shortcuts = fields.master_toggle
    editor_inline_code_shortcut = editor_fields.shortcut_input
    editor_inline_code_shortcut_enabled = editor_fields.shortcut_toggle

    editor_definitions = (("anki_editor_inline_code_shortcut", "inline code"),) + INDENTATION_SHORTCUT_DEFINITIONS
    editor_inputs = {"anki_editor_inline_code_shortcut": editor_inline_code_shortcut, **editor_fields.indentation_rows.shortcut_inputs}
    editor_checks = {"anki_editor_inline_code_shortcut_enabled": editor_inline_code_shortcut_enabled, **editor_fields.indentation_rows.shortcut_enabled}

    def editor_shortcut_active(key):
        return editor_checks[f"{key}_enabled"].isChecked() and (
            key == "anki_editor_inline_code_shortcut" or all_controls["anki_editor_tab_indentation"].isChecked()
        )

    restore_button = QPushButton("Restore Defaults", dialog)
    restore_button.setAutoDefault(False)

    def setting_value(key: str, widget):
        if isinstance(widget, CardShortcutInput):
            return widget.stored_shortcut()
        return widget.isChecked()

    def restore_defaults(*_args) -> None:
        for key, widget in all_controls.items():
            if isinstance(widget, CardShortcutInput):
                widget.set_shortcut(DEFAULT_SETTINGS[key])
            else:
                widget.setChecked(DEFAULT_SETTINGS[key])

    restore_button.clicked.connect(restore_defaults)

    def update_restore_button(*_args) -> None:
        has_custom_settings = any(
            setting_value(key, widget) != DEFAULT_SETTINGS[key]
            for key, widget in all_controls.items()
        )
        restore_button.setEnabled(has_custom_settings)
        restore_button.setToolTip(
            "" if has_custom_settings else "All settings are using defaults."
        )

    for widget in all_controls.values():
        if isinstance(widget, QCheckBox):
            widget.toggled.connect(update_restore_button)
        else:
            widget.add_change_listener(update_restore_button)
    update_restore_button()

    dialog_buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save,
        Qt.Orientation.Horizontal,
        dialog,
    )
    cancel_button = dialog_buttons.button(QDialogButtonBox.StandardButton.Cancel)
    save_button = dialog_buttons.button(QDialogButtonBox.StandardButton.Save)
    assert cancel_button is not None and save_button is not None
    save_button.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
    tabs.currentChanged.connect(lambda _index: save_button.setFocus())
    cancel_button.clicked.connect(dialog.reject)
    save_button.setDefault(True)

    validation_state = {"invalid": [], "duplicates": [], "reserved": []}

    def refresh_shortcut_warnings(*_args) -> None:
        messages = {key: [] for key, _label in markdown_shortcut_definitions}
        editor_messages = {key: [] for key, _label in editor_definitions}
        editor_active_shortcuts = []
        active_shortcuts = []
        conflict_highlights = set()
        validation_state["invalid"] = []
        validation_state["duplicates"] = []
        validation_state["reserved"] = []

        for key, label in markdown_shortcut_definitions:
            if fields.shortcut_masters[key].isChecked():
                enabled_key = f"{key}_enabled"
                if not markdown_shortcut_checkboxes[enabled_key].isChecked():
                    continue
                shortcut = markdown_shortcut_inputs[key].stored_shortcut()
                if not shortcut:
                    continue
                active_shortcuts.append((shortcut, key, label))
                if not shortcut_has_required_modifier(shortcut):
                    messages[key].append(f"Use {SHORTCUT_MODIFIER_HINT} with this key.")
                    validation_state["invalid"].append(label)
                reserved_action = reserved_shortcut_warnings().get(
                    normalize_shortcut(shortcut)
                )
                if reserved_action:
                    messages[key].append(
                        f"{format_shortcut(shortcut)} is reserved for "
                        f"{reserved_action}. Choose another shortcut."
                    )
                    validation_state["reserved"].append(label)

        seen_shortcuts = {}
        for shortcut, key, label in active_shortcuts:
            normalized = normalize_shortcut(shortcut)
            if normalized in seen_shortcuts:
                other_key, other_label = seen_shortcuts[normalized]
                current_order = markdown_shortcut_inputs[key].change_order()
                other_order = markdown_shortcut_inputs[other_key].change_order()
                if current_order >= other_order:
                    warning_key, warning_label = key, other_label
                    highlighted_key = other_key
                else:
                    warning_key, warning_label = other_key, label
                    highlighted_key = key
                messages[warning_key].append(
                    f"{format_shortcut(shortcut)} conflicts with the "
                    f"{warning_label} shortcut. Choose another."
                )
                conflict_highlights.add(highlighted_key)
                validation_state["duplicates"].append((other_label, label))
            else:
                seen_shortcuts[normalized] = (key, label)

        for key, checkbox in markdown_shortcut_option_checkboxes.items():
            checkbox.shortcut_conflict = key in conflict_highlights
            style_shortcut_option(
                checkbox,
                inactive=not fields.shortcut_masters[key].isChecked(),
            )

        for key, label in editor_definitions:
            if not editor_shortcut_active(key):
                continue
            shortcut = editor_inputs[key].stored_shortcut()
            if key == "anki_editor_inline_code_shortcut":
                shortcut = shortcut or DEFAULT_SETTINGS[key]
            if not shortcut:
                continue
            editor_active_shortcuts.append((shortcut, key, label))
            if not shortcut_has_required_modifier(shortcut):
                editor_messages[key].append(f"Use {SHORTCUT_MODIFIER_HINT} with this key.")
                validation_state["invalid"].append(f"Anki editor {label}")
            reserved_action = reserved_shortcut_warnings().get(normalize_shortcut(shortcut))
            if reserved_action:
                editor_messages[key].append(
                    f"{format_shortcut(shortcut)} is reserved for {reserved_action}. Choose another shortcut."
                )
                validation_state["reserved"].append(f"Anki editor {label}")

        editor_seen = {}
        editor_conflicts = set()
        for shortcut, key, label in editor_active_shortcuts:
            normalized = normalize_shortcut(shortcut)
            if normalized in editor_seen:
                other_key, other_label = editor_seen[normalized]
                editor_messages[key].append(
                    f"{format_shortcut(shortcut)} conflicts with the {other_label} shortcut. Choose another."
                )
                editor_conflicts.add(other_key)
                validation_state["duplicates"].append((f"Editor {other_label}", f"Editor {label}"))
            else:
                editor_seen[normalized] = (key, label)
        for key, _label in INDENTATION_SHORTCUT_DEFINITIONS:
            checkbox = editor_checks[f"{key}_enabled"]
            checkbox.shortcut_conflict = key in editor_conflicts
            style_shortcut_option(checkbox, inactive=not all_controls["anki_editor_tab_indentation"].isChecked())

        built_in_shortcuts = anki_shortcut_warnings()
        editor_built_in_shortcuts = {
            **built_in_shortcuts,
            **anki_editor_format_shortcut_warnings(),
        }
        for shortcut, key, _label in active_shortcuts:
            description = built_in_shortcuts.get(normalize_shortcut(shortcut))
            if description:
                messages[key].append(
                    f"The {format_shortcut(shortcut)} shortcut may "
                    f"conflict with Anki's {description} shortcut."
                )
        for shortcut, key, _label in editor_active_shortcuts:
            description = editor_built_in_shortcuts.get(normalize_shortcut(shortcut))
            if description:
                editor_messages[key].append(
                    f"The {format_shortcut(shortcut)} shortcut may conflict with Anki's {description} shortcut."
                )

        for key, _label in markdown_shortcut_definitions:
            message = "\n".join(messages[key])
            markdown_shortcut_inputs[key].set_persistent_validation_message(message)
        for key, _label in editor_definitions:
            editor_inputs[key].set_persistent_validation_message("\n".join(editor_messages[key]))

    def validate_shortcut_candidate(key: str, candidate: str) -> str | None:
        if not fields.shortcut_masters[key].isChecked():
            return None
        candidate_normalized = normalize_shortcut(candidate)
        for other_key, other_label in markdown_shortcut_definitions:
            if other_key == key or not fields.shortcut_masters[other_key].isChecked():
                continue
            if not markdown_shortcut_checkboxes[f"{other_key}_enabled"].isChecked():
                continue
            other_shortcut = markdown_shortcut_inputs[other_key].stored_shortcut()
            if (
                other_shortcut
                and normalize_shortcut(other_shortcut) == candidate_normalized
            ):
                return (
                    f"{format_shortcut(candidate)} conflicts with the "
                    f"{other_label} shortcut. Choose another."
                )
        return None

    def validate_editor_shortcut_candidate(key, candidate):
        if not editor_shortcut_active(key):
            return None
        for other_key, label in editor_definitions:
            if other_key == key or not editor_shortcut_active(other_key):
                continue
            other = editor_inputs[other_key].stored_shortcut()
            if other and normalize_shortcut(other) == normalize_shortcut(candidate):
                return f"{format_shortcut(candidate)} conflicts with the {label} shortcut. Choose another."
        return None

    for key, _label in markdown_shortcut_definitions:
        markdown_shortcut_inputs[key].set_shortcut_validator(
            lambda candidate, key=key: validate_shortcut_candidate(key, candidate)
        )
        markdown_shortcut_inputs[key].add_change_listener(refresh_shortcut_warnings)
        markdown_shortcut_checkboxes[f"{key}_enabled"].toggled.connect(
            refresh_shortcut_warnings
        )
    question_markdown_shortcuts.toggled.connect(refresh_shortcut_warnings)
    all_controls["card_input_tab_indentation"].toggled.connect(refresh_shortcut_warnings)
    for key, _label in editor_definitions:
        editor_inputs[key].set_shortcut_validator(
            lambda candidate, key=key: validate_editor_shortcut_candidate(key, candidate)
        )
        editor_inputs[key].add_change_listener(refresh_shortcut_warnings)
        editor_checks[f"{key}_enabled"].toggled.connect(refresh_shortcut_warnings)
    all_controls["anki_editor_tab_indentation"].toggled.connect(refresh_shortcut_warnings)
    refresh_shortcut_warnings()

    def save_current_settings(*_args) -> None:
        settings = {
            key: setting_value(key, widget) for key, widget in all_controls.items()
        }
        if not settings["anki_editor_inline_code_shortcut"]:
            settings["anki_editor_inline_code_shortcut"] = DEFAULT_SETTINGS[
                "anki_editor_inline_code_shortcut"
            ]
        settings["note_type_selections"] = note_types.collect_selections()
        refresh_shortcut_warnings()
        if any(validation_state.values()):
            return
        save_settings(dialog, settings)

    save_button.clicked.connect(save_current_settings)
    buttons_layout = QHBoxLayout()
    buttons_layout.addWidget(restore_button)
    buttons_layout.addStretch()
    buttons_layout.addWidget(dialog_buttons)
    layout.addLayout(buttons_layout)

    QTimer.singleShot(0, save_button.setFocus)
    dialog.exec()


def save_settings(dialog: QDialog, settings: dict[str, object]) -> None:
    write_settings(settings)
    update_assets_for_profile()
    dialog.accept()


def initialize() -> None:
    gui_hooks.profile_did_open.append(update_assets_for_profile)
    settings_action = QAction("Anki Global Kit Settings...", mw)
    settings_icon = QIcon(str(SHARED_ASSET_DIR / "global-kit.svg"))
    settings_icon.setIsMask(True)
    settings_action.setIcon(settings_icon)
    settings_action.setIconVisibleInMenu(True)
    settings_action.triggered.connect(lambda checked=False: open_settings())
    mw.form.menuTools.addAction(settings_action)
