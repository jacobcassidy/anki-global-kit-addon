"""Anki Desktop add-on features."""

from . import editor, reviewer_shortcuts, settings


def initialize() -> None:
    settings.initialize()
    editor.initialize()
    reviewer_shortcuts.initialize()
