"""Public interface for syntax highlighting services."""

from .rendering import SyntaxHighlightingError, render_code

__all__ = ["SyntaxHighlightingError", "render_code"]
