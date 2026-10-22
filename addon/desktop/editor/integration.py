"""Anki Desktop note-editor integration."""

import json
from functools import partial
from weakref import WeakSet, ref

from aqt import gui_hooks, mw
from aqt.editor import Editor
from aqt.qt import QApplication, QKeySequence, QShortcut, sip

from ..config.service import get_editor_settings
from ..media.manifest import EDITOR_ASSET_PATHS
from ..paths import ICON_ASSET_DIR, USER_FILES_DIR
from ..shortcuts.formatting import EDITOR_BLOCK_SHORTCUTS as BLOCK_SHORTCUTS
from ..shortcuts.formatting import editor_fixed_shortcut_action, normalize_shortcut
from ..shortcuts.labels import shortcut_label
from .buttons import toolbar_button, toolbar_groups
from .features import field_descriptions, syntax_highlighting

EDITOR_ASSET = EDITOR_ASSET_PATHS["editor.min.js"]
EDITOR_STYLES_DIR = EDITOR_ASSET_PATHS["editor-ui.min.css"].parent
ICON_ASSET = ICON_ASSET_DIR / "code-inline.svg"
BLOCKQUOTE_ICON = ICON_ASSET.with_name("blockquote.svg")
PASTE_MARKDOWN_ICON = ICON_ASSET.with_name("markdown.svg")
_open_editors = WeakSet()


def _inject_features(editor: Editor) -> None:
    if not EDITOR_ASSET.is_file():
        return
    editor_settings = get_editor_settings()
    settings = json.dumps(editor_settings, separators=(",", ":"))
    settings = settings.replace("<", "\\u003c")
    list_labels = json.dumps(
        {
            name: shortcut_label(keys)
            for name, keys in BLOCK_SHORTCUTS.items()
            if name in ("unordered-list", "ordered-list")
        }
    )
    indent_labels = json.dumps(
        {
            action: shortcut_label(
                editor_settings[f"anki_editor_indent_{action}_shortcut"]
            )
            if editor_settings["anki_editor_tab_indentation"]
            and editor_settings[f"anki_editor_indent_{action}_shortcut_enabled"]
            else ""
            for action in ("increase", "decrease")
        }
    )
    styles = {
        "ui": _read_editor_styles(
            "editor-ui.min.css",
            custom_filename="editor-ui.css",
            include_default=editor_settings["anki_editor_default_ui_styles"],
            include_custom=editor_settings["anki_editor_custom_ui_styles"],
        ),
        "fields": _read_editor_styles(
            "editor-fields.min.css",
            custom_filename="editor-fields.css",
            include_default=editor_settings["anki_editor_default_fields_styles"],
            include_custom=editor_settings["anki_editor_custom_fields_styles"],
        ),
    }
    if mw.col is not None and editor_settings["anki_editor_default_fields_styles"]:
        from ..syntax_highlighting.preferences import get_themes
        from ..syntax_highlighting.themes import generate_theme_pair_css

        themes = get_themes(mw.col)
        styles["fields"] += "\n" + generate_theme_pair_css(
            themes.get("light"), themes.get("dark"), editor=True
        )
    styles_json = json.dumps(styles, separators=(",", ":"))
    styles_json = styles_json.replace("<", "\\u003c")
    script = EDITOR_ASSET.read_text(encoding="utf-8")
    editor.web.eval(
        "globalThis.ankiGlobalKitEditorSettings = Object.assign("
        "globalThis.ankiGlobalKitEditorSettings || {}, "
        f"{settings});\n"
        f"globalThis.ankiGlobalKitEditorListLabels = {list_labels};\n"
        f"globalThis.ankiGlobalKitEditorIndentLabels = {indent_labels};\n"
        f"globalThis.ankiGlobalKitEditorStyles = {styles_json};\n{script}"
        "\nglobalThis.ankiGlobalKitEditorRefreshFormattingTooltips?.();"
        "\nfor (const button of document.querySelectorAll('[data-command=\"anki_global_kit_inline_code\"]')) {"
        f"button.title = {json.dumps(_inline_code_tip(editor_settings))};"
        "}"
        "\nfor (const button of document.querySelectorAll('[data-command=\"anki_global_kit_syntax_highlighting\"]')) {"
        f"button.title = {json.dumps(syntax_highlighting.highlight_code_tip(editor_settings))};"
        "}"
        "\nfor (const button of document.querySelectorAll('[data-command=\"anki_global_kit_blockquote\"]')) {"
        f"button.title = {json.dumps(_button_tip('Blockquote', 'anki_editor_blockquote_shortcut', editor_settings))};"
        "}"
        "\nfor (const button of document.querySelectorAll('[data-command=\"anki_global_kit_paste_markdown_as_html\"]')) {"
        f"button.title = {json.dumps(_button_tip('Convert Markdown', 'anki_editor_convert_markdown_shortcut', editor_settings))};"
        "}"
    )
    syntax_highlighting.set_editor_language_context(editor)


def _read_editor_styles(
    filename: str,
    *,
    custom_filename: str,
    include_default: bool = True,
    include_custom: bool = True,
) -> str:
    """Combine packaged editor CSS with a user's upgrade-safe overrides."""
    paths = [EDITOR_STYLES_DIR / filename] if include_default else []
    if include_custom:
        paths.append(USER_FILES_DIR / custom_filename)
    return "\n".join(
        path.read_text(encoding="utf-8") for path in paths if path.is_file()
    )


def _toggle_inline_code(editor: Editor) -> None:
    editor.web.eval("globalThis.ankiGlobalKitEditor?.toggleInlineCode();")


def _toggle_block(editor: Editor, format_name: str) -> None:
    editor.web.eval(
        f"globalThis.ankiGlobalKitEditor?.toggleBlock({json.dumps(format_name)});"
    )


def _convert_markdown(editor: Editor) -> None:
    markdown = QApplication.clipboard().text()
    editor.web.eval(
        f"globalThis.ankiGlobalKitEditor?.convertMarkdown({json.dumps(markdown)});"
    )


def _change_indentation(editor: Editor, action: str) -> None:
    method = "indent" if action == "increase" else "unindent"
    editor.web.eval(f"globalThis.ankiGlobalKitEditor?.{method}();")


def _add_button(buttons: list, editor: Editor) -> None:
    settings = get_editor_settings()
    custom_buttons = []
    syntax_highlighting.add_button(custom_buttons, editor, settings)

    custom_buttons.append(
        toolbar_button(
            editor,
            settings,
            "anki_editor_paste_markdown_as_html_button",
            icon=str(PASTE_MARKDOWN_ICON),
            cmd="anki_global_kit_paste_markdown_as_html",
            func=_convert_markdown,
            tip=_button_tip(
                "Convert Markdown", "anki_editor_convert_markdown_shortcut", settings
            ),
        )
    )
    custom_buttons.append(
        toolbar_button(
            editor,
            settings,
            "anki_editor_blockquote_button",
            icon=str(BLOCKQUOTE_ICON),
            cmd="anki_global_kit_blockquote",
            func=lambda editor: _toggle_block(editor, "blockquote"),
            tip=_button_tip("Blockquote", "anki_editor_blockquote_shortcut", settings),
        )
    )
    custom_buttons.append(
        toolbar_button(
            editor,
            settings,
            "anki_editor_inline_code_button",
            icon=str(ICON_ASSET),
            cmd="anki_global_kit_inline_code",
            func=_toggle_inline_code,
            tip=_inline_code_tip(settings),
        )
    )
    buttons.append(
        toolbar_groups(
            [
                ("syntax-highlighting", "Syntax Highlighting", custom_buttons[:3]),
                ("formatting", "Formatting", custom_buttons[3:]),
            ]
        )
    )


def _inline_code_tip(settings: dict) -> str:
    tip = "Inline Code"
    if (
        settings["anki_editor_inline_code_shortcut_enabled"]
        and settings["anki_editor_inline_code_shortcut"]
    ):
        tip += f" ({shortcut_label(settings['anki_editor_inline_code_shortcut'])})"
    return tip


def _button_tip(label: str, key: str, settings: dict) -> str:
    tip = label
    if settings[f"{key}_enabled"] and settings[key]:
        tip += f" ({shortcut_label(settings[key])})"
    return tip


def _add_shortcut(shortcuts: list, editor: Editor) -> None:
    # Replace Anki's native list bindings, leaving Command+Comma to Preferences.
    replaced = {
        normalize_shortcut(keys)
        for keys in (*BLOCK_SHORTCUTS.values(), "Ctrl+,", "Ctrl+.")
    }
    shortcuts[:] = [
        entry for entry in shortcuts if normalize_shortcut(entry[0]) not in replaced
    ]
    for name, keys in BLOCK_SHORTCUTS.items():
        shortcuts.append((keys, partial(_toggle_block, editor, name)))
    settings = get_editor_settings()
    for keys in _configured_editor_shortcuts(settings).values():
        normalized = normalize_shortcut(keys)
        shortcuts[:] = [
            entry for entry in shortcuts if normalize_shortcut(entry[0]) != normalized
        ]
    _open_editors.add(editor)
    if not isinstance(getattr(editor, "_anki_global_kit_shortcuts", None), dict):
        editor._anki_global_kit_shortcuts = {}
    _refresh_editor_shortcuts(editor, settings)


def _configured_editor_shortcuts(settings: dict) -> dict[str, str]:
    """Validate saved bindings before registering or refreshing native keys."""
    configurable = {}
    for action in ("blockquote", "convert_markdown"):
        key = f"anki_editor_{action}_shortcut"
        if settings[f"{key}_enabled"]:
            configurable[key] = settings[key]
    if settings["anki_editor_inline_code_shortcut_enabled"]:
        configurable["anki_editor_inline_code_shortcut"] = settings[
            "anki_editor_inline_code_shortcut"
        ]
    if settings.get("anki_editor_syntax_highlighting_shortcut_enabled", True):
        configurable["anki_editor_syntax_highlighting_shortcut"] = settings.get(
            "anki_editor_syntax_highlighting_shortcut", "Alt+S"
        )
    if settings["anki_editor_tab_indentation"]:
        for action in ("increase", "decrease"):
            key = f"anki_editor_indent_{action}_shortcut"
            if settings[f"{key}_enabled"] and settings[key]:
                configurable[key] = settings[key]
    registered = set()
    active = {}
    for name, keys in configurable.items():
        normalized = normalize_shortcut(keys)
        # Saved configuration may predate UI validation or be edited directly.
        # Preserve fixed actions and register each configurable key only once.
        if not keys or editor_fixed_shortcut_action(keys) or normalized in registered:
            continue
        registered.add(normalized)
        active[name] = keys
    return active


def _activate_editor_shortcut(editor_ref, name: str) -> None:
    editor = editor_ref()
    if editor is None or sip.isdeleted(editor.widget) or editor.currentField is None:
        return
    configured = _configured_editor_shortcuts(get_editor_settings()).get(name)
    shortcut, registered = editor._anki_global_kit_shortcuts[name]
    if (
        not shortcut.isEnabled()
        or not configured
        or normalize_shortcut(configured) != normalize_shortcut(registered)
    ):
        return
    if name == "anki_editor_inline_code_shortcut":
        _toggle_inline_code(editor)
    elif name == "anki_editor_blockquote_shortcut":
        _toggle_block(editor, "blockquote")
    elif name == "anki_editor_convert_markdown_shortcut":
        _convert_markdown(editor)
    elif name == "anki_editor_syntax_highlighting_shortcut":
        syntax_highlighting.highlight_selection(editor)
    else:
        _change_indentation(editor, "decrease" if "decrease" in name else "increase")


def _refresh_editor_shortcuts(editor: Editor, settings: dict) -> None:
    # Keep references to the kit's own shortcuts, so a settings save can rebind
    # them without touching other add-ons' shortcuts or rebuilding the editor.
    shortcuts = editor._anki_global_kit_shortcuts
    for shortcut, _keys in shortcuts.values():
        shortcut.setEnabled(False)
    for name, keys in _configured_editor_shortcuts(settings).items():
        if name in shortcuts:
            shortcut = shortcuts[name][0]
            shortcut.setKey(QKeySequence(keys))
        else:
            shortcut = QShortcut(
                QKeySequence(keys),
                editor.widget,
                activated=partial(_activate_editor_shortcut, ref(editor), name),
            )
        shortcuts[name] = (shortcut, keys)
        shortcut.setEnabled(True)


def refresh_open_editors() -> None:
    """Apply saved settings to native bindings and existing editor webviews."""
    settings = get_editor_settings()
    for editor in list(_open_editors):
        if sip.isdeleted(editor.widget) or sip.isdeleted(editor.web):
            _open_editors.discard(editor)
            continue
        _refresh_editor_shortcuts(editor, settings)
        _inject_features(editor)


def initialize() -> None:
    syntax_highlighting.initialize()
    gui_hooks.editor_did_init_buttons.append(_add_button)
    gui_hooks.editor_did_init_shortcuts.append(_add_shortcut)
    gui_hooks.editor_will_load_note.append(field_descriptions.add_compare_placeholder)
    gui_hooks.editor_did_load_note.append(_inject_features)
    gui_hooks.editor_did_load_note.append(
        syntax_highlighting.reset_editor_language_context
    )
