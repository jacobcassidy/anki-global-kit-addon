"""Desktop editor entry points for syntax highlighting."""

import json
import re

from aqt import gui_hooks
from aqt.editor import Editor
from aqt.qt import QApplication

from ...config.service import get_editor_settings
from ...paths import ICON_ASSET_DIR

ICON = ICON_ASSET_DIR / "lightning.svg"
_MESSAGE_PREFIX = "anki-global-kit:syntax-highlight:"
_BUSY = False
_INSTALLED = False


def add_button(buttons: list, editor: Editor) -> None:
    settings = get_editor_settings()
    if not settings.get("anki_editor_syntax_highlighting_button", True):
        return

    buttons.append(
        editor.addButton(
            icon=str(ICON),
            cmd="anki_global_kit_syntax_highlighting",
            func=lambda editor: highlight_selection(editor),
            tip="Highlight Code",
        )
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


def _on_success(
    editor: Editor, request_id: str, source: str, result: tuple[str, str]
) -> None:
    global _BUSY
    _BUSY = False
    if editor.web is None:
        return

    token_html, language = result
    editor.web.eval(
        "globalThis.ankiGlobalKitEditor?.applyHighlightResult("
        f"{json.dumps(request_id)}, {json.dumps(source)}, "
        f"{json.dumps(language)}, {json.dumps(token_html)});"
    )


def _on_failure(error: Exception) -> None:
    global _BUSY
    _BUSY = False
    from aqt.utils import showWarning

    showWarning(f"Could not highlight this code:\n{error}")


def _render_code(source: str, language: str) -> tuple[str, str]:
    from ...syntax_highlighting import render_code

    return render_code(source, language)


def _on_message(handled: tuple[bool, object], message: str, context):
    global _BUSY
    if not message.startswith(_MESSAGE_PREFIX) or not isinstance(context, Editor):
        return handled

    try:
        request = json.loads(message[len(_MESSAGE_PREFIX) :])
    except (TypeError, json.JSONDecodeError):
        return (True, None)

    request_id = request.get("id")
    source = request.get("source")
    language = request.get("language")
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
        op=lambda _collection: _render_code(source, language),
        success=lambda result: _on_success(context, request_id, source, result),
    )
    operation.failure(_on_failure).without_collection().run_in_background()
    return (True, None)


def initialize() -> None:
    global _INSTALLED
    if not _INSTALLED:
        gui_hooks.webview_did_receive_js_message.append(_on_message)
        _INSTALLED = True
