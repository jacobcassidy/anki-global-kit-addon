"""Register editor buttons with their initial settings visibility."""

from aqt.editor import Editor


def toolbar_button(editor: Editor, settings: dict, setting: str, **kwargs) -> str:
    """Keep each action registered so saving settings can reveal it immediately."""
    html = editor.addButton(**kwargs)
    if not settings.get("anki_editor_toolbar_enabled", True) or not settings.get(
        setting, True
    ):
        html = html.replace("<button", '<button style="display: none;"', 1)
    return html
