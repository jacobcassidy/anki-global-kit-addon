"""Register editor buttons with their initial settings visibility."""

import re

from aqt.editor import Editor

GROUP_RADIUS = "var(--anki-global-kit-toolbar-group-radius, 5px)"


def toolbar_button(editor: Editor, settings: dict, setting: str, **kwargs) -> str:
    """Keep each action registered so saving settings can reveal it immediately."""
    html = editor.addButton(**kwargs)
    # Masks inherit Anki's foreground, including --fg-disabled, in both themes.
    html = re.sub(
        r'<img class="topbut" src="([^"]+)">',
        lambda match: (
            '<span aria-hidden="true" style="position: absolute; inset: 4px; '
            "background-color: currentColor; "
            f"mask: url('{match[1]}') center / contain no-repeat;\"></span>"
        ),
        html,
    )
    if not settings.get("anki_editor_toolbar_enabled", True) or not settings.get(
        setting, True
    ):
        html = html.replace("<button", '<button style="display: none;"', 1)
    return html


def toolbar_groups(groups: list[tuple[str, str, list[str]]]) -> str:
    """Render independent groups inside Anki's single add-on button component."""
    rendered = []
    for name, label, buttons in groups:
        visible = [
            index
            for index, button in enumerate(buttons)
            if "display: none;" not in button
        ]
        rounded_buttons = []
        for index, button in enumerate(buttons):
            left = GROUP_RADIUS if visible and index == visible[0] else "0"
            right = GROUP_RADIUS if visible and index == visible[-1] else "0"
            styles = (
                f"--border-left-radius: {left}; --border-right-radius: {right}; "
                "border-radius: var(--border-left-radius) var(--border-right-radius) "
                "var(--border-right-radius) var(--border-left-radius); "
            )
            if '<button style="' in button:
                button = button.replace(
                    '<button style="', f'<button style="{styles}', 1
                )
            else:
                button = button.replace("<button", f'<button style="{styles}"', 1)
            rounded_buttons.append(button)
        display = "inline-flex" if visible else "none"
        rendered.append(
            f'<span data-anki-global-kit-toolbar-group="{name}" '
            f'role="group" aria-label="{label}" style="display: {display};">'
            f"{''.join(rounded_buttons)}</span>"
        )
    return (
        '<span data-anki-global-kit-toolbar="" role="group" aria-label="Anki Global Kit" '
        'style="display: inline-flex; align-items: center; '
        'column-gap: var(--anki-global-kit-toolbar-group-gap, 0.3rem);">'
        f"{''.join(rendered)}</span>"
    )
