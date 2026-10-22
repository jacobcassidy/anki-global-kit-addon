"""Desktop editor entry points for syntax highlighting."""

import json
import re
from html import escape

from aqt import gui_hooks
from aqt.editor import Editor
from aqt.qt import QApplication

from ...config.service import get_editor_settings
from ...paths import ICON_ASSET_DIR
from ...shortcuts.labels import shortcut_label
from ..buttons import toolbar_button

ICON = ICON_ASSET_DIR / "lightning-rounded-narrow-angled.svg"
OPTIONS_ICON = ICON_ASSET_DIR / "ellipsis.svg"
_MESSAGE_PREFIX = "anki-global-kit:syntax-highlight:"
_MARKDOWN_MESSAGE_PREFIX = "anki-global-kit:markdown-highlight:"
_APPLIED_MESSAGE_PREFIX = "anki-global-kit:syntax-highlight-applied:"
_OPTIONS_MESSAGE_PREFIX = "anki-global-kit:code-block-options:"
_LANGUAGE_MENU_PREFIX = "anki-global-kit:language-menu:"
_BUSY = False
_INSTALLED = False
_PENDING_EXPLICIT_APPLIES: dict[str, tuple[Editor, int | None, str]] = {}


def add_button(buttons: list, editor: Editor, settings: dict | None = None) -> None:
    settings = get_editor_settings() if settings is None else settings
    buttons.append(
        toolbar_button(
            editor,
            settings,
            "anki_editor_syntax_highlighting_button",
            icon=str(ICON),
            cmd="anki_global_kit_syntax_highlighting",
            func=lambda editor: highlight_selection(editor),
            tip=highlight_code_tip(settings),
        )
    )
    buttons.append(
        toolbar_button(
            editor,
            settings,
            "anki_editor_syntax_highlighting_button",
            icon=None,
            cmd="anki_global_kit_syntax_language",
            func=show_language_menu,
            label=_language_button_label(settings),
            id="anki_global_kit_syntax_language",
            tip="Choose the language for syntax highlighting",
        )
    )
    buttons.append(
        toolbar_button(
            editor,
            settings,
            "anki_editor_syntax_highlighting_button",
            icon=str(OPTIONS_ICON),
            cmd="anki_global_kit_code_block_options",
            func=open_code_block_options,
            tip="Code Block Options…",
        )
    )


def highlight_code_tip(settings: dict) -> str:
    tip = "Highlight Code"
    shortcut = settings.get("anki_editor_syntax_highlighting_shortcut")
    if settings.get("anki_editor_syntax_highlighting_shortcut_enabled") and shortcut:
        tip += f" ({shortcut_label(shortcut)})"
    return tip


def _language_button_label(settings: dict, language: str | None = None) -> str:
    alias = language or settings.get(
        "anki_editor_syntax_highlighting_default_language", "python"
    )
    if alias not in settings.get("anki_editor_syntax_highlighting_languages", []):
        try:
            from ...syntax_highlighting.rendering import select_editor_language

            alias = select_editor_language(
                settings.get(
                    "anki_editor_syntax_highlighting_default_language", "python"
                ),
                settings.get("anki_editor_syntax_highlighting_languages", []),
            )
        except ModuleNotFoundError:
            alias = None
    try:
        from ...syntax_highlighting.rendering import available_languages

        names = {item[1]: item[0] for item in available_languages()}
    except ModuleNotFoundError:
        names = {}
    return names.get(alias, alias or "Choose language")


def _set_language_choice(editor: Editor, language: str) -> None:
    settings = get_editor_settings()
    enabled = settings.get("anki_editor_syntax_highlighting_languages", [])
    if language not in enabled:
        return

    editor._anki_global_kit_language_override = language
    editor._anki_global_kit_language_deck_id = _resolve_editor_deck_id(editor)
    if editor.web is not None:
        editor.web.eval(
            "globalThis.ankiGlobalKitEditor?.setExplicitLanguage("
            f"{json.dumps(language)});"
            "(() => { const button = document.querySelector('[data-command=\"anki_global_kit_syntax_language\"]');"
            f"if (button) button.textContent = {json.dumps(_language_button_label(settings, language))};"
            "})();"
        )


def show_language_menu(editor: Editor, anchor: list | None = None) -> None:
    from aqt.qt import QCursor, QMenu, QPoint

    from ...syntax_highlighting.rendering import (
        available_languages,
        select_editor_language,
    )

    settings = get_editor_settings()
    enabled = settings.get("anki_editor_syntax_highlighting_languages", [])
    if not enabled:
        from aqt.utils import showWarning

        showWarning(
            "Choose at least one language in the Syntax Highlighting settings tab to enable code highlighting."
        )
        return

    names = {alias: name for name, alias, _aliases in available_languages()}
    selected = getattr(editor, "_anki_global_kit_language_override", None)
    if selected not in enabled:
        selected = getattr(editor, "_anki_global_kit_language_remembered", None)
    if selected not in enabled:
        selected = select_editor_language(
            settings.get("anki_editor_syntax_highlighting_default_language", "python"),
            enabled,
        )
    ordered = sorted(
        (alias for alias in enabled if alias in names and alias != selected),
        key=lambda alias: names[alias].casefold(),
    )
    menu = QMenu(editor.parentWindow)
    if selected in names:
        current = menu.addAction(names[selected])
        current.setEnabled(False)
        menu.addSeparator()
    for language in ordered:
        action = menu.addAction(names[language])
        action.triggered.connect(
            lambda _checked=False, alias=language: _choose_language(editor, alias)
        )

    def open_menu(rect) -> None:
        if editor.web is None:
            return
        position = QCursor.pos()
        rect = anchor if isinstance(anchor, list) and len(anchor) == 2 else rect
        if isinstance(rect, list) and len(rect) == 2:
            zoom = editor.web.zoomFactor()
            position = editor.web.mapToGlobal(
                QPoint(round(rect[0] * zoom), round(rect[1] * zoom))
            )
        menu.exec(position)

    if editor.web is not None:
        editor.web.evalWithCallback(
            "(() => { const button = document.querySelector("
            "'[data-command=\"anki_global_kit_syntax_language\"]');"
            "if (!button) return null; const rect = button.getBoundingClientRect();"
            "return [rect.left, rect.bottom]; })()",
            open_menu,
        )


def set_editor_language_context(editor: Editor, *, reset: bool = False) -> None:
    """Refresh transient choices and collection memory after loading a note."""
    settings = get_editor_settings()
    enabled = settings.get("anki_editor_syntax_highlighting_languages", [])
    override = getattr(editor, "_anki_global_kit_language_override", None)
    if reset:
        override = None
        editor._anki_global_kit_language_override = None
        editor._anki_global_kit_language_deck_id = None
    if override not in enabled:
        override = None
        editor._anki_global_kit_language_override = None
    deck_id = _resolve_editor_deck_id(editor)
    editor._anki_global_kit_language_context_deck_id = deck_id
    remembered = None
    if deck_id is not None and settings.get(
        "anki_editor_syntax_highlighting_remember_language_per_deck"
    ):
        from ...syntax_highlighting.language_memory import remembered_language

        remembered = remembered_language(editor.mw.col, deck_id, enabled)
    editor._anki_global_kit_language_remembered = remembered
    if editor.web is not None:
        editor.web.eval(
            "globalThis.ankiGlobalKitEditor?.setLanguageContext("
            f"{json.dumps(override)}, {json.dumps(remembered)});"
        )
        label = _language_button_label(settings, override or remembered)
        editor.web.eval(
            "(() => { const button = document.querySelector('[data-command=\"anki_global_kit_syntax_language\"]');"
            f"if (button) button.textContent = {json.dumps(label)};"
            "})();"
        )


def reset_editor_language_context(editor: Editor) -> None:
    set_editor_language_context(editor, reset=True)


def _choose_language(editor: Editor, language: str) -> None:
    _set_language_choice(editor, language)
    if editor.web is not None:
        editor.web.eval("globalThis.ankiGlobalKitEditor?.highlightCode('', null);")


def _resolve_editor_deck_id(editor: Editor) -> int | None:
    if getattr(editor, "addMode", False):
        chooser = getattr(editor.parentWindow, "deck_chooser", None)
        return _positive_id(getattr(chooser, "selected_deck_id", None))

    card = getattr(editor, "card", None)
    if card is not None:
        deck_id = _positive_id(getattr(card, "odid", 0)) or _positive_id(
            getattr(card, "did", None)
        )
        return deck_id

    note = getattr(editor, "note", None)
    collection = getattr(editor.mw, "col", None)
    note_id = _positive_id(getattr(note, "id", None))
    if note_id is None or collection is None:
        return None
    try:
        deck_ids = collection.db.list(
            "select distinct case when odid > 0 then odid else did end from cards where nid = ?",
            note_id,
        )
    except (AttributeError, RuntimeError):
        return None

    return int(deck_ids[0]) if len(deck_ids) == 1 else None


def _positive_id(value) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value > 0:
        return int(value)
    if isinstance(value, str) and value.isdecimal() and int(value) > 0:
        return int(value)
    return None


def _resolve_authoring_language(
    request: dict, editor: Editor, deck_id: int | None, explicit: bool
) -> tuple[str, bool]:
    from ...syntax_highlighting.rendering import (
        available_languages,
        select_editor_language,
    )

    settings = get_editor_settings()
    enabled = settings.get("anki_editor_syntax_highlighting_languages", [])
    rows = available_languages()
    supported = {alias for _name, alias, _aliases in rows}
    requested = request.get("language")
    if explicit and requested in enabled and requested in supported:
        return requested, True

    existing = request.get("existingLanguage")
    if isinstance(existing, str) and existing in supported:
        return existing, False

    topic_text = request.get("topicText")
    if isinstance(topic_text, str):
        matches = []
        for name, alias, aliases in rows:
            if alias not in enabled:
                continue
            for candidate in {name, *aliases}:
                if re.search(
                    rf"(?<![a-z0-9]){re.escape(candidate)}(?![a-z0-9])",
                    topic_text,
                    re.IGNORECASE,
                ):
                    matches.append((len(candidate), alias))
        if matches:
            return max(matches)[1], False

    if (
        deck_id is not None
        and settings.get("anki_editor_syntax_highlighting_remember_language_per_deck")
        and editor.mw.col is not None
    ):
        from ...syntax_highlighting.language_memory import remembered_language

        remembered = remembered_language(editor.mw.col, deck_id, enabled)
        if remembered in supported:
            return remembered, False

    return (
        select_editor_language(
            settings.get("anki_editor_syntax_highlighting_default_language", "python"),
            enabled,
        )
        or "python",
        False,
    )


def highlight_selection(editor: Editor) -> None:
    from aqt.utils import showWarning

    settings = get_editor_settings()
    languages = settings.get("anki_editor_syntax_highlighting_languages", [])
    if not languages:
        showWarning(
            "Choose at least one language in the Syntax Highlighting settings tab to enable code highlighting."
        )
        return

    clipboard = QApplication.clipboard().text()
    from ...syntax_highlighting.rendering import select_editor_language

    language = select_editor_language(
        settings.get("anki_editor_syntax_highlighting_default_language", "python"),
        languages,
    )
    if language is None:
        return
    editor.web.eval(
        "globalThis.ankiGlobalKitEditor?.highlightCode("
        f"{json.dumps(clipboard)}, {json.dumps(language)});"
    )


def open_code_block_options(editor: Editor) -> None:
    editor.web.eval("globalThis.ankiGlobalKitEditor?.openCodeBlockOptions();")


def _show_code_block_options(editor: Editor, request: dict) -> None:
    from aqt.qt import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QSpinBox,
        Qt,
        QVBoxLayout,
    )

    dialog = QDialog(editor.parentWindow)
    dialog.setWindowTitle("Code Block Options")
    layout = QVBoxLayout(dialog)
    form = QFormLayout()
    line_numbers = QCheckBox("Show line numbers", dialog)
    line_numbers.setChecked(request.get("lineNumbers") is True)
    form.addRow(line_numbers)
    line_start = QSpinBox(dialog)
    line_start.setRange(1, 2_147_483_647)
    initial_start = request.get("lineStart")
    line_start.setValue(
        initial_start if type(initial_start) is int and initial_start > 0 else 1
    )
    form.addRow("Starting line number", line_start)
    cloze_mode = QComboBox(dialog)
    cloze_mode.addItem("Preserve Anki clozes", "active")
    cloze_mode.addItem("Literal code", "literal")
    cloze_mode.setCurrentIndex(1 if request.get("clozeMode") == "literal" else 0)
    form.addRow("Anki cloze syntax", cloze_mode)
    cloze_label = form.labelForField(cloze_mode)

    if cloze_label is not None:
        cloze_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

    layout.addLayout(form)
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok,
        dialog,
    )
    apply_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
    assert apply_button is not None
    apply_button.setText("Apply to Block")
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    if dialog.exec() != QDialog.DialogCode.Accepted or editor.web is None:
        if editor.web is not None:
            editor.web.eval(
                "globalThis.ankiGlobalKitEditor?.cancelCodeBlockOptions("
                f"{json.dumps(request['id'])});"
            )
        dialog.deleteLater()
        return

    options = {
        "id": request["id"],
        "lineNumbers": line_numbers.isChecked(),
        "lineStart": line_start.value(),
        "clozeMode": cloze_mode.currentData(),
    }
    editor.web.eval(
        "globalThis.ankiGlobalKitEditor?.applyCodeBlockOptions("
        f"{json.dumps(options['id'])}, {json.dumps(options, separators=(',', ':'))});"
    )
    dialog.deleteLater()


def _on_success(
    editor: Editor,
    request_id: str,
    source: str,
    result: tuple[str, str],
    line_numbers: bool,
    line_start: int,
    cloze_mode: str,
    explicit_language: bool,
    deck_id: int | None,
) -> None:
    global _BUSY
    _BUSY = False
    if editor.web is None:
        return

    if _resolve_editor_deck_id(editor) != deck_id:
        editor.web.eval(
            "globalThis.ankiGlobalKitEditor?.cancelHighlightResult("
            f"{json.dumps(request_id)});"
        )
        set_editor_language_context(editor, reset=True)
        return

    token_html, language = result
    if explicit_language:
        _PENDING_EXPLICIT_APPLIES[request_id] = (editor, deck_id, language)
    editor.web.eval(
        "globalThis.ankiGlobalKitEditor?.applyHighlightResult("
        f"{json.dumps(request_id)}, {json.dumps(source)}, "
        f"{json.dumps(language)}, {json.dumps(token_html)}, "
        f"{json.dumps(line_numbers)}, {line_start}, {json.dumps(cloze_mode)});"
    )


def _on_failure(error: Exception) -> None:
    global _BUSY
    _BUSY = False
    from aqt.utils import showWarning

    showWarning(f"Could not highlight this code:\n{error}")


def _render_markdown_blocks(code_blocks: list[dict]) -> tuple[list[dict], int]:
    from ...syntax_highlighting import render_code
    from ...syntax_highlighting.rendering import MAX_SOURCE_CHARACTERS

    rendered = []
    oversized = 0
    for block in code_blocks:
        source = block["source"]
        language = block["language"]
        if not language:
            continue
        if len(source) > MAX_SOURCE_CHARACTERS:
            oversized += 1
            continue
        try:
            token_html, canonical = render_code(source, language)
        except ValueError:
            continue
        rendered.append(
            {"index": block["index"], "language": canonical, "html": token_html}
        )
    return rendered, oversized


def _on_markdown_success(editor: Editor, request_id: str, html: str, result) -> None:
    global _BUSY
    _BUSY = False
    if editor.web is None:
        return
    rendered, oversized = result
    editor.web.eval(
        "globalThis.ankiGlobalKitEditor?.applyMarkdownHighlightResult("
        f"{json.dumps(request_id)}, {json.dumps(html)}, {json.dumps(rendered)});"
    )
    if oversized:
        from aqt.utils import showWarning

        from ...syntax_highlighting.rendering import MAX_SOURCE_CHARACTERS

        showWarning(
            f"{oversized} Markdown code block(s) exceeded the "
            f"{MAX_SOURCE_CHARACTERS:,}-character highlighting limit and were inserted as plain code."
        )


def _on_markdown_failure(error: Exception, editor: Editor, request_id: str) -> None:
    global _BUSY
    _BUSY = False
    if editor.web is not None:
        editor.web.eval(
            "globalThis.ankiGlobalKitEditor?.failMarkdownHighlight("
            f"{json.dumps(request_id)});"
        )
    _on_failure(error)


def _fail_markdown_request(editor: Editor, request_id: str) -> None:
    if editor.web is None:
        return
    editor.web.eval(
        "globalThis.ankiGlobalKitEditor?.failMarkdownHighlight("
        f"{json.dumps(request_id)});"
    )


def _on_markdown_message(message: str, context: Editor):
    global _BUSY
    try:
        request = json.loads(message[len(_MARKDOWN_MESSAGE_PREFIX) :])
    except (TypeError, json.JSONDecodeError):
        return (True, None)
    if not isinstance(request, dict):
        return (True, None)

    request_id = request.get("id")
    html = request.get("html")
    blocks = request.get("codeBlocks")
    if (
        not isinstance(request_id, str)
        or not re.fullmatch(r"\d{1,12}", request_id)
        or not isinstance(html, str)
        or len(html) > 2_000_000
        or not isinstance(blocks, list)
        or len(blocks) > 100
    ):
        if isinstance(request_id, str) and re.fullmatch(r"\d{1,12}", request_id):
            _fail_markdown_request(context, request_id)
        return (True, None)

    validated = []
    for block in blocks:
        if not isinstance(block, dict):
            return (True, None)
        index = block.get("index")
        source = block.get("source")
        language = block.get("language")
        if (
            type(index) is not int
            or index < 0
            or not isinstance(source, str)
            or not isinstance(language, str)
            or len(language) > 80
        ):
            _fail_markdown_request(context, request_id)
            return (True, None)
        validated.append({"index": index, "source": source, "language": language})

    if _BUSY:
        _fail_markdown_request(context, request_id)
        from aqt.utils import showWarning

        showWarning(
            "Syntax highlighting is already processing code. Try again when it finishes."
        )
        return (True, None)

    _BUSY = True
    from aqt.operations import QueryOp

    operation = QueryOp(
        parent=context,
        op=lambda _collection: _render_markdown_blocks(validated),
        success=lambda result: _on_markdown_success(context, request_id, html, result),
    )
    operation.failure(
        lambda error: _on_markdown_failure(error, context, request_id)
    ).without_collection().run_in_background()
    return (True, None)


def _render_code(source: str, language: str, cloze_mode: str) -> tuple[str, str]:
    from ...syntax_highlighting import render_code

    return render_code(source, language, cloze_mode)


def _on_message(handled: tuple[bool, object], message: str, context):
    global _BUSY
    if message.startswith(_LANGUAGE_MENU_PREFIX) and isinstance(context, Editor):
        try:
            anchor = json.loads(message[len(_LANGUAGE_MENU_PREFIX) :])
        except (TypeError, json.JSONDecodeError):
            return (True, None)
        if isinstance(anchor, list) and len(anchor) == 3:
            selected = anchor.pop()
            enabled = get_editor_settings().get(
                "anki_editor_syntax_highlighting_languages", []
            )
            if isinstance(selected, str) and selected in enabled:
                context._anki_global_kit_language_override = selected
        show_language_menu(context, anchor[:2] if isinstance(anchor, list) else None)
        return (True, None)

    if message.startswith(_OPTIONS_MESSAGE_PREFIX) and isinstance(context, Editor):
        try:
            request = json.loads(message[len(_OPTIONS_MESSAGE_PREFIX) :])
        except (TypeError, json.JSONDecodeError):
            return (True, None)
        if (
            isinstance(request, dict)
            and isinstance(request.get("id"), str)
            and re.fullmatch(r"\d{1,12}", request["id"])
            and context.web is not None
        ):
            _show_code_block_options(context, request)
        return (True, None)

    if message.startswith(_MARKDOWN_MESSAGE_PREFIX) and isinstance(context, Editor):
        return _on_markdown_message(message, context)

    if message.startswith(_APPLIED_MESSAGE_PREFIX) and isinstance(context, Editor):
        return _on_highlight_applied(message, context)

    if not message.startswith(_MESSAGE_PREFIX) or not isinstance(context, Editor):
        return handled

    try:
        request = json.loads(message[len(_MESSAGE_PREFIX) :])
    except (TypeError, json.JSONDecodeError):
        return (True, None)
    if not isinstance(request, dict):
        return (True, None)

    request_id = request.get("id")
    source = request.get("source")
    language = request.get("language")
    explicit_language = request.get("explicitLanguage") is True
    request_deck_id = _resolve_editor_deck_id(context)
    cloze_mode = request.get("clozeMode")
    if cloze_mode not in {"active", "literal"}:
        cloze_mode = "active"
    line_numbers = request.get("lineNumbers") is True
    line_start = request.get("lineStart")
    if type(line_start) is not int or line_start < 1:
        line_start = 1
    if (
        not isinstance(request_id, str)
        or not re.fullmatch(r"\d{1,12}", request_id)
        or not isinstance(source, str)
        or not isinstance(language, str)
        or len(language) > 80
    ):
        return (True, None)
    if not source:
        return (True, None)
    if context.web is None:
        return (True, None)

    context_deck_id = getattr(
        context, "_anki_global_kit_language_context_deck_id", request_deck_id
    )
    deck_changed = context_deck_id != request_deck_id
    explicit_deck_id = getattr(
        context, "_anki_global_kit_language_deck_id", context_deck_id
    )
    if deck_changed:
        if explicit_deck_id != request_deck_id:
            explicit_language = False
            context._anki_global_kit_language_override = None
            context._anki_global_kit_language_deck_id = None
    language, explicit_language = _resolve_authoring_language(
        request, context, request_deck_id, explicit_language
    )
    if deck_changed or (
        request.get("explicitLanguage") is True and not explicit_language
    ):
        set_editor_language_context(context, reset=not explicit_language)

    from ...syntax_highlighting.rendering import MAX_SOURCE_CHARACTERS

    if len(source) > MAX_SOURCE_CHARACTERS:
        context.web.eval(
            "globalThis.ankiGlobalKitEditor?.applyHighlightResult("
            f"{json.dumps(request_id)}, {json.dumps(source)}, "
            f"{json.dumps(language)}, {json.dumps(escape(source, quote=False))}, "
            f"{json.dumps(line_numbers)}, {line_start}, {json.dumps(cloze_mode)});"
        )
        from aqt.utils import showWarning

        showWarning(
            f"This block exceeds the {MAX_SOURCE_CHARACTERS:,}-character limit and was inserted as plain code."
        )
        return (True, None)
    if _BUSY:
        from aqt.utils import showWarning

        showWarning(
            "Syntax highlighting is already processing code. Try again when it finishes."
        )
        return (True, None)

    _BUSY = True
    from aqt.operations import QueryOp

    operation = QueryOp(
        parent=context,
        op=lambda _collection: _render_code(source, language, cloze_mode),
        success=lambda result: _on_success(
            context,
            request_id,
            source,
            result,
            line_numbers,
            line_start,
            cloze_mode,
            explicit_language,
            request_deck_id,
        ),
    )
    operation.failure(_on_failure).without_collection().run_in_background()
    return (True, None)


def _on_highlight_applied(message: str, context: Editor):
    try:
        request = json.loads(message[len(_APPLIED_MESSAGE_PREFIX) :])
    except (TypeError, json.JSONDecodeError):
        return (True, None)
    if not isinstance(request, dict):
        return (True, None)
    request_id = request.get("id")
    if not isinstance(request_id, str):
        return (True, None)

    pending = _PENDING_EXPLICIT_APPLIES.pop(request_id, None)
    if pending is None:
        return (True, None)
    editor, deck_id, language = pending
    if (
        editor is not context
        or request.get("applied") is not True
        or request.get("language") != language
        or deck_id is None
        or _resolve_editor_deck_id(editor) != deck_id
    ):
        return (True, None)

    settings = get_editor_settings()
    collection = getattr(editor.mw, "col", None)
    if collection is None or not settings.get(
        "anki_editor_syntax_highlighting_remember_language_per_deck"
    ):
        return (True, None)

    from ...syntax_highlighting.language_memory import remember_language
    from ...syntax_highlighting.rendering import available_languages

    supported = {alias for _name, alias, _aliases in available_languages()}
    remember_language(collection, deck_id, language, supported)
    set_editor_language_context(editor)
    return (True, None)


def initialize() -> None:
    global _INSTALLED
    if not _INSTALLED:
        gui_hooks.webview_did_receive_js_message.append(_on_message)
        _INSTALLED = True
