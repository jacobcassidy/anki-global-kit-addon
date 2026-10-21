"""Pure, on-demand Pygments rendering for Desktop code blocks."""

from __future__ import annotations

import importlib
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


def _get_bundled_lexer(lexers, alias: str, **options):
    """Resolve only aliases in Pygments' bundled lexer registry."""
    mapping = importlib.import_module("pygments.lexers._mapping").LEXERS
    normalized = alias.casefold()
    for module_name, name, aliases, _filenames, _mimetypes in mapping.values():
        if normalized in {item.casefold() for item in aliases}:
            lexers._load_lexers(module_name)
            return lexers._lexer_cache[name](**options)

    raise SyntaxHighlightingError(f"Unsupported code language: {alias}.")


def render_code(source: str, language: str) -> tuple[str, str]:
    """Return Pygments token HTML and its normalized canonical language alias."""
    if not isinstance(source, str) or not isinstance(language, str):
        raise SyntaxHighlightingError("Code and language must be text values.")
    if len(source) > MAX_SOURCE_CHARACTERS:
        raise SyntaxHighlightingError(
            f"Code exceeds the {MAX_SOURCE_CHARACTERS:,}-character highlighting limit."
        )

    with _with_bundled_modules():
        lexers = importlib.import_module("pygments.lexers")
        formatters = importlib.import_module("pygments.formatters")
        lexer = _get_bundled_lexer(lexers, language, stripnl=False, ensurenl=False)

        formatter = formatters.HtmlFormatter(nowrap=True, classprefix="")
        html = importlib.import_module("pygments").highlight(source, lexer, formatter)
        return html, getattr(lexer, "aliases", [language])[0]
