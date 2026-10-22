"""Default descriptions for empty Kit editor fields."""

import json

from ...media.manifest import JS_ASSET_NAME

COMPARE_PLACEHOLDER = "Leave blank unless compare is wanted"


def add_compare_placeholder(js: str, note, _editor) -> str:
    """Supply the Compare hint without changing saved note types or field values."""
    notetype = note.note_type()
    if not any(
        JS_ASSET_NAME in template.get(side, "")
        for template in notetype["tmpls"]
        for side in ("qfmt", "afmt")
    ):
        return js
    fields = notetype["flds"]
    if not any(
        field["name"] == "Compare" and not field.get("description") for field in fields
    ):
        return js
    descriptions = [
        field.get("description", "")
        or (COMPARE_PLACEHOLDER if field["name"] == "Compare" else "")
        for field in fields
    ]
    descriptions_json = json.dumps(descriptions).replace("<", "\\u003c")
    return f"{js}\nsetDescriptions({descriptions_json});"
