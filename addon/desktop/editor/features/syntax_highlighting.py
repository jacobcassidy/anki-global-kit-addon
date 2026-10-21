"""Desktop editor entry points for syntax highlighting."""

import json
import re
from html import escape

from aqt import gui_hooks
from aqt.editor import Editor
from aqt.qt import QApplication

from ...config.service import get_editor_settings
from ...paths import ICON_ASSET_DIR

ICON = ICON_ASSET_DIR / "lightning.svg"
OPTIONS_ICON = ICON_ASSET_DIR / "code-block.svg"
_MESSAGE_PREFIX = "anki-global-kit:syntax-highlight:"
_MARKDOWN_MESSAGE_PREFIX = "anki-global-kit:markdown-highlight:"
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
    buttons.append(
        editor.addButton(
            icon=str(OPTIONS_ICON),
            cmd="anki_global_kit_code_block_options",
            func=open_code_block_options,
            tip="Code Block Options…",
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


def open_code_block_options(editor: Editor) -> None:
    editor.web.eval("globalThis.ankiGlobalKitEditor?.openCodeBlockOptions();")


def _on_success(
    editor: Editor,
    request_id: str,
    source: str,
    result: tuple[str, str],
    line_numbers: bool,
    line_start: int,
    cloze_mode: str,
) -> None:
    global _BUSY
    _BUSY = False
    if editor.web is None:
        return

    token_html, language = result
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
    if message.startswith(_MARKDOWN_MESSAGE_PREFIX) and isinstance(context, Editor):
        return _on_markdown_message(message, context)

    if not message.startswith(_MESSAGE_PREFIX) or not isinstance(context, Editor):
        return handled

    try:
        request = json.loads(message[len(_MESSAGE_PREFIX) :])
    except (TypeError, json.JSONDecodeError):
        return (True, None)

    request_id = request.get("id")
    source = request.get("source")
    language = request.get("language")
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
        ),
    )
    operation.failure(_on_failure).without_collection().run_in_background()
    return (True, None)


def initialize() -> None:
    global _INSTALLED
    if not _INSTALLED:
        gui_hooks.webview_did_receive_js_message.append(_on_message)
        _INSTALLED = True
