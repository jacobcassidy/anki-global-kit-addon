"""Anki Desktop note-editor integration."""

import json
from functools import partial
from pathlib import Path

from aqt import gui_hooks
from aqt.editor import Editor

from ..settings import get_editor_settings
from ..settings.constants import USER_FILES_DIR
from .features.paste.cleanup import clean_paste_mime, finish_paste_layout
from .features.shortcuts.labels import shortcut_label

ADDON_DIR = Path(__file__).resolve().parents[2]
EDITOR_ASSET = ADDON_DIR / "desktop" / "editor" / "assets" / "js" / "editor.min.js"
EDITOR_STYLES_DIR = ADDON_DIR / "desktop" / "editor" / "assets" / "css"
ICON_ASSET = ADDON_DIR / "desktop" / "shared" / "assets" / "inline-code.svg"


def _inject_features(editor: Editor) -> None:
    if not EDITOR_ASSET.is_file():
        return
    editor_settings = get_editor_settings()
    settings = json.dumps(editor_settings, separators=(",", ":"))
    settings = settings.replace("<", "\\u003c")
    styles = {
        "ui": _read_editor_styles(
            "editor-ui.min.css",
            custom_filename="editor-ui.css",
            include_custom=editor_settings["anki_editor_custom_ui_styles"],
        ),
        "fields": _read_editor_styles(
            "editor-fields.min.css",
            custom_filename="editor-fields.css",
            include_custom=editor_settings["anki_editor_custom_fields_styles"],
        ),
    }
    styles_json = json.dumps(styles, separators=(",", ":"))
    styles_json = styles_json.replace("<", "\\u003c")
    script = EDITOR_ASSET.read_text(encoding="utf-8")
    editor.web.eval(
        "globalThis.ankiGlobalKitEditorSettings = Object.assign("
        "globalThis.ankiGlobalKitEditorSettings || {}, "
        f"{settings});\n"
        f"globalThis.ankiGlobalKitEditorStyles = {styles_json};\n{script}"
    )


def _read_editor_styles(
    filename: str,
    *,
    custom_filename: str,
    include_custom: bool = True,
) -> str:
    """Combine packaged editor CSS with a user's upgrade-safe overrides."""
    paths = [EDITOR_STYLES_DIR / filename]
    if include_custom:
        paths.append(USER_FILES_DIR / custom_filename)
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in paths
        if path.is_file()
    )


def _toggle_inline_code(editor: Editor) -> None:
    editor.web.eval("globalThis.ankiGlobalKitEditor?.toggleInlineCode();")


def _add_button(buttons: list, editor: Editor) -> None:
    settings = get_editor_settings()
    if not settings["anki_editor_inline_code_button"]:
        return
    tip = "Inline Code"
    if settings["anki_editor_inline_code_shortcut_enabled"]:
        tip += f" ({shortcut_label(settings['anki_editor_inline_code_shortcut'])})"
    buttons.append(editor.addButton(
        icon=str(ICON_ASSET),
        cmd="anki_global_kit_inline_code",
        func=_toggle_inline_code,
        tip=tip,
    ))


def _add_shortcut(shortcuts: list, editor: Editor) -> None:
    settings = get_editor_settings()
    if settings["anki_editor_inline_code_shortcut_enabled"]:
        shortcuts.append((
            settings["anki_editor_inline_code_shortcut"],
            partial(_toggle_inline_code, editor),
        ))


def initialize() -> None:
    gui_hooks.editor_did_init_buttons.append(_add_button)
    gui_hooks.editor_did_init_shortcuts.append(_add_shortcut)
    gui_hooks.editor_did_load_note.append(_inject_features)
    gui_hooks.editor_will_process_mime.append(clean_paste_mime)
    gui_hooks.editor_did_paste.append(finish_paste_layout)
