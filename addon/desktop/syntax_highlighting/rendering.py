"""Pure, on-demand Pygments rendering for Desktop code blocks."""

from __future__ import annotations

import html
import importlib
import re
import sys
import threading

from ..paths import ADDON_DIR

MAX_SOURCE_CHARACTERS = 50_000
_PYGMENTS_VERSION = "2.19.2"
_PYGMENTS_PATH = ADDON_DIR / "vendor"
_IMPORT_LOCK = threading.RLock()
_PYGMENTS_MODULES: dict[str, object] | None = None


class SyntaxHighlightingError(ValueError):
    """Raised when a language or the bundled renderer is unavailable."""


def _load_pygments_modules() -> dict[str, object]:
    """Load the bundled Pygments tree without replacing another add-on's copy."""
    global _PYGMENTS_MODULES

    if _PYGMENTS_MODULES is not None:
        return _PYGMENTS_MODULES

    with _IMPORT_LOCK:
        existing = {
            name: module
            for name, module in sys.modules.items()
            if name == "pygments" or name.startswith("pygments.")
        }
        for name in existing:
            del sys.modules[name]

        sys.path.insert(0, str(_PYGMENTS_PATH))
        try:
            pygments = importlib.import_module("pygments")
            version = getattr(pygments, "__version__", "")
            if version != _PYGMENTS_VERSION:
                raise SyntaxHighlightingError(
                    f"Bundled Pygments version mismatch: expected {_PYGMENTS_VERSION}, got {version}."
                )

            importlib.import_module("pygments.lexers")
            importlib.import_module("pygments.formatters")
            _PYGMENTS_MODULES = {
                name: module
                for name, module in sys.modules.items()
                if name == "pygments" or name.startswith("pygments.")
            }
        finally:
            sys.path.remove(str(_PYGMENTS_PATH))
            for name in tuple(sys.modules):
                if name == "pygments" or name.startswith("pygments."):
                    del sys.modules[name]
            sys.modules.update(existing)

    return _PYGMENTS_MODULES


def _with_bundled_modules():
    """Temporarily expose the cached bundled module tree under Pygments' imports."""

    class ModuleContext:
        def __enter__(self):
            _IMPORT_LOCK.acquire()
            self.previous = {
                name: module
                for name, module in sys.modules.items()
                if name == "pygments" or name.startswith("pygments.")
            }
            for name in self.previous:
                del sys.modules[name]
            sys.modules.update(_load_pygments_modules())
            return self

        def __exit__(self, *_exc):
            global _PYGMENTS_MODULES
            _PYGMENTS_MODULES = {
                name: module
                for name, module in sys.modules.items()
                if name == "pygments" or name.startswith("pygments.")
            }
            for name in tuple(sys.modules):
                if name == "pygments" or name.startswith("pygments."):
                    del sys.modules[name]
            sys.modules.update(self.previous)
            _IMPORT_LOCK.release()

    return ModuleContext()


def available_languages() -> list[tuple[str, str, tuple[str, ...]]]:
    """Return deterministic bundled language labels and aliases."""
    with _with_bundled_modules():
        lexers = importlib.import_module("pygments.lexers")
        return sorted(
            (name, aliases[0], tuple(aliases))
            for name, aliases, _filenames, _mimetypes in lexers.get_all_lexers(
                plugins=False
            )
            if aliases
        )


def select_editor_language(default: str, enabled: list[object]) -> str | None:
    """Choose the enabled default, then the first enabled display name."""
    valid = {item for item in enabled if isinstance(item, str)}
    if default in valid:
        return default
    labels = {
        alias: name for name, alias, _aliases in available_languages() if alias in valid
    }
    return min(labels, key=lambda alias: labels[alias].casefold()) if labels else None


def _get_bundled_lexer(lexers, alias: str, **options):
    """Resolve only aliases in Pygments' bundled lexer registry."""
    mapping = importlib.import_module("pygments.lexers._mapping").LEXERS
    normalized = alias.casefold()
    for module_name, name, aliases, _filenames, _mimetypes in mapping.values():
        if normalized in {item.casefold() for item in aliases}:
            lexers._load_lexers(module_name)
            return lexers._lexer_cache[name](**options)

    raise SyntaxHighlightingError(f"Unsupported code language: {alias}.")


def render_code(
    source: str, language: str, cloze_mode: str = "active"
) -> tuple[str, str]:
    """Return Pygments token HTML and its normalized canonical language alias."""
    if not isinstance(source, str) or not isinstance(language, str):
        raise SyntaxHighlightingError("Code and language must be text values.")
    if len(source) > MAX_SOURCE_CHARACTERS:
        raise SyntaxHighlightingError(
            f"Code exceeds the {MAX_SOURCE_CHARACTERS:,}-character highlighting limit."
        )

    return _render_with_clozes(source, language, cloze_mode)


def _split_clozes(source: str) -> list[tuple[bool, str]]:
    """Split complete, possibly nested Anki clozes from surrounding source."""
    segments = []
    cursor = 0
    marker = re.compile(r"\{\{c\d+::")
    while match := marker.search(source, cursor):
        if match.start() > cursor:
            segments.append((False, source[cursor : match.start()]))
        depth = 1
        position = match.end()
        while position < len(source) and depth:
            if source.startswith("{{", position):
                depth += 1
                position += 2
            elif source.startswith("}}", position):
                depth -= 1
                position += 2
            else:
                position += 1
        if depth:
            segments.append((False, source[match.start() :]))
            cursor = len(source)
            break
        segments.append((True, source[match.start() : position]))
        cursor = position
    if cursor < len(source) or not segments:
        segments.append((False, source[cursor:]))
    return segments


def _render_with_clozes(source: str, language: str, cloze_mode: str) -> tuple[str, str]:
    """Keep active cloze syntax contiguous or encode it as literal code."""
    if cloze_mode not in {"active", "literal"}:
        raise SyntaxHighlightingError("Unknown Anki cloze handling mode.")

    with _with_bundled_modules():
        lexers = importlib.import_module("pygments.lexers")
        formatters = importlib.import_module("pygments.formatters")
        lexer = _get_bundled_lexer(lexers, language, stripnl=False, ensurenl=False)

        formatter = formatters.HtmlFormatter(nowrap=True, classprefix="")
        pygments = importlib.import_module("pygments")
        pieces = []
        for is_cloze, segment in _split_clozes(source):
            if not is_cloze:
                pieces.append(pygments.highlight(segment, lexer, formatter))
                continue
            if cloze_mode == "literal":
                literal = html.escape(segment, quote=False)
                pieces.append(
                    literal.replace("{{", "&#123;&#123;").replace("}}", "&#125;&#125;")
                )
                continue
            header = re.match(r"\{\{c\d+::", segment)
            assert header is not None
            body = html.escape(segment[header.end() : -2], quote=False)
            pieces.append(segment[: header.end()] + body + "}}")
        return "".join(pieces), getattr(lexer, "aliases", [language])[0]
