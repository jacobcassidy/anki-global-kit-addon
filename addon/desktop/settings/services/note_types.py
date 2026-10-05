"""Create topic-specific Anki Global Kit note types from template parts."""

from copy import deepcopy
from html import escape
from pathlib import Path

from anki.consts import MODEL_CLOZE
from aqt import mw
from aqt.utils import askUser, showInfo, showWarning


ADDON_DIR = Path(__file__).resolve().parents[3]
TEMPLATE_DIR = ADDON_DIR / "templates" / "note-types" / "parts"
HTML_DIR = TEMPLATE_DIR / "html"
STYLING_DIR = TEMPLATE_DIR / "styling"
SCRIPT_PATH = TEMPLATE_DIR / "script" / "card-script.js"
TOPICS = (
    "Command Line",
    "CSS",
    "Git",
    "JavaScript",
    "PHP",
    "Python",
    "React",
    "Regex",
    "Ruby",
    "TypeScript",
    "Vocabulary",
    "WordPress",
)
FORMATS = {
    "Advance": {
        "front": "advance-front.html",
        "back": "advance-back.html",
        "fields": [
            "Question",
            "Answer",
            "Type Hint",
            "Compare",
            "Bonus Question",
            "Bonus Answer",
            "Bonus Type Hint",
            "Bonus Compare",
            "Notes",
        ],
        "cloze": False,
    },
    "Cloze": {
        "front": "cloze-front.html",
        "back": "cloze-back.html",
        "fields": [
            "Cloze Question",
            "Type Hint",
            "Bonus Question",
            "Bonus Answer",
            "Bonus Type Hint",
            "Bonus Compare",
            "Notes",
        ],
        "cloze": True,
    },
}


def _read_template(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _topic_style_path(topic: str) -> Path:
    if topic not in TOPICS:
        return STYLING_DIR / "style-default.css"
    style_name = "shell" if topic == "Command Line" else topic.lower()
    return STYLING_DIR / f"style-{style_name}.css"


def _card_template(filename: str, topic: str, script: str) -> str:
    html = _read_template(HTML_DIR / filename)
    html = html.replace(
        '<h1 class="topic">Topic</h1>',
        f'<h1 class="topic">{escape(topic)}</h1>',
    )
    return f"{html.rstrip()}\n\n<script>\n{script.rstrip()}\n</script>\n"


def _create_note_type(
    name: str,
    topic: str,
    spec: dict[str, object],
    existing_notetype: dict[str, object] | None = None,
) -> None:
    models = mw.col.models
    if existing_notetype is not None:
        notetype = deepcopy(existing_notetype)
        fields_by_name = {field["name"]: field for field in notetype["flds"]}
        for field_name in spec["fields"]:
            if field_name not in fields_by_name:
                field = models.new_field(field_name)
                field["ord"] = len(notetype["flds"])
                notetype["flds"].append(field)
                fields_by_name[field_name] = field
        template = (
            deepcopy(notetype["tmpls"][0])
            if notetype["tmpls"]
            else models.new_template("Cloze" if spec["cloze"] else "Card 1")
        )
        notetype["tmpls"] = [template]
        template["ord"] = 0
        template["name"] = "Cloze" if spec["cloze"] else "Card 1"
    elif spec["cloze"]:
        stock_cloze = next(
            (model for model in models.all() if model["type"] == MODEL_CLOZE), None
        )
        if stock_cloze is None:
            raise RuntimeError("Anki's built-in cloze note type was not found.")
        notetype = deepcopy(stock_cloze)
        notetype["id"] = 0
        notetype["name"] = name
        notetype["flds"] = []
        notetype["tmpls"] = [deepcopy(stock_cloze["tmpls"][0])]
        template = notetype["tmpls"][0]
        template["ord"] = 0
        template["name"] = "Cloze"
    else:
        notetype = models.new(name)
        template = models.new_template("Card 1")
        notetype["tmpls"] = [template]

    if existing_notetype is None:
        for field_name in spec["fields"]:
            models.add_field(notetype, models.new_field(field_name))

    script = _read_template(SCRIPT_PATH)
    template["qfmt"] = _card_template(spec["front"], topic, script)
    template["afmt"] = _card_template(spec["back"], topic, script)
    imports = _read_template(STYLING_DIR / "imports.css")
    topic_style = _read_template(_topic_style_path(topic))
    notetype["css"] = f"{imports.rstrip()}\n\n{topic_style.rstrip()}\n"
    if existing_notetype is None:
        notetype["sortf"] = 0
        models.add(notetype)
    else:
        models.update_dict(notetype)


def create_selected_note_types(
    selections: dict[str, set[str]],
    overwrites: dict[str, set[str]] | None = None,
    deletions: dict[str, set[str]] | None = None,
) -> bool:
    """Apply selected note type creates, replacements, and empty-type deletions."""
    if mw.col is None:
        showWarning("Open an Anki profile before creating Anki Global Kit note types.")
        return False

    selected = [
        (topic, card_format)
        for topic, selected_formats in selections.items()
        for card_format in FORMATS
        if card_format in selected_formats
    ]
    overwrites = overwrites or {}
    deletions = deletions or {}

    existing_names = {entry.name for entry in mw.col.models.all_names_and_ids()}
    requested = [
        (topic, card_format, f"{topic} ({card_format})")
        for topic, card_format in selected
    ]
    names_to_create = [item for item in requested if item[2] not in existing_names]
    names_to_overwrite = [
        item
        for item in requested
        if item[2] in existing_names and item[1] in overwrites.get(item[0], set())
    ]
    skipped = [
        item[2]
        for item in requested
        if item[2] in existing_names and item not in names_to_overwrite
    ]

    requested_deletions = [
        (topic, card_format, f"{topic} ({card_format})")
        for topic, selected_formats in deletions.items()
        for card_format in FORMATS
        if card_format in selected_formats
    ]
    names_to_delete = []
    for topic, card_format, name in requested_deletions:
        notetype = mw.col.models.by_name(name)
        if notetype is None:
            showWarning(
                f"The note type {name} no longer exists. Reopen settings and try again."
            )
            return False
        if mw.col.models.use_count(notetype):
            showWarning(
                f"The note type {name} contains notes and cannot be deleted here. "
                "Move its notes to another note type in Anki first."
            )
            return False
        names_to_delete.append((topic, card_format, name))

    if not names_to_create and not names_to_overwrite and not names_to_delete:
        if skipped:
            showInfo(
                "All selected note types already exist in this profile. "
                "Select Replace beside an existing format to update it."
            )
        else:
            showInfo("Select at least one note type action to apply.")
        return False

    selected_for_templates = {
        (topic, card_format)
        for topic, card_format, _name in names_to_create + names_to_overwrite
    }
    required_paths = (
        [SCRIPT_PATH, STYLING_DIR / "imports.css"]
        if selected_for_templates
        else []
    )
    for topic, card_format in selected_for_templates:
        spec = FORMATS[card_format]
        required_paths.extend(HTML_DIR / spec[side] for side in ("front", "back"))
        required_paths.append(_topic_style_path(topic))
    missing = [
        str(path.relative_to(ADDON_DIR))
        for path in required_paths
        if not path.is_file()
    ]
    if missing:
        showWarning(
            "Anki Global Kit card template files are missing. Rebuild or reinstall "
            "the add-on package.\n\n" + "\n".join(missing)
        )
        return False

    confirmation = []
    if names_to_create:
        names = "\n".join(f"• {name}" for _, _, name in names_to_create)
        confirmation.append(f"Create these new note types?\n{names}")
    if names_to_overwrite:
        names = "\n".join(f"• {name}" for _, _, name in names_to_overwrite)
        confirmation.append(
            "Replace these existing note types with the kit templates and styling?\n"
            "Their notes and fields will be kept; missing kit fields will be added, "
            "and custom card templates may be replaced.\n"
            f"{names}"
        )
    if names_to_delete:
        names = "\n".join(f"• {name}" for _, _, name in names_to_delete)
        confirmation.append(
            "Delete these empty note types? They contain no notes.\n" + names
        )
    if not askUser(
        "Apply the selected note type changes in the active Anki profile?\n\n"
        + "\n\n".join(confirmation)
    ):
        return False

    # Recheck after confirmation so notes added while the dialog was open are safe.
    for _topic, _card_format, name in names_to_delete:
        notetype = mw.col.models.by_name(name)
        if notetype is None:
            showWarning(
                f"The note type {name} no longer exists. Reopen settings and try again."
            )
            return False
        if mw.col.models.use_count(notetype):
            showWarning(
                f"The note type {name} now contains notes and cannot be deleted. "
                "Move its notes to another note type in Anki first."
            )
            return False

    created = []
    overwritten = []
    deleted = []
    try:
        for topic, card_format, name in names_to_create:
            _create_note_type(name, topic, FORMATS[card_format])
            created.append(name)
        for topic, card_format, name in names_to_overwrite:
            existing_notetype = mw.col.models.by_name(name)
            if existing_notetype is None:
                raise RuntimeError(
                    f"The existing note type {name} could not be loaded."
                )
            _create_note_type(
                name,
                topic,
                FORMATS[card_format],
                existing_notetype,
            )
            overwritten.append(name)
        for _topic, _card_format, name in names_to_delete:
            notetype = mw.col.models.by_name(name)
            if notetype is None:
                raise RuntimeError(f"The note type {name} could not be loaded.")
            mw.col.models.remove(notetype["id"])
            deleted.append(name)
    except Exception as error:
        details = "\n".join(created + overwritten + deleted) if (
            created or overwritten or deleted
        ) else "None"
        showWarning(
            "Anki Global Kit could not apply all selected note type changes.\n\n"
            f"Applied changes:\n{details}\n\nError: {error}"
        )
        return False

    message_parts = []
    if created:
        message_parts.append("Created note types:\n" + "\n".join(created))
    if overwritten:
        message_parts.append("Replaced note types:\n" + "\n".join(overwritten))
    if deleted:
        message_parts.append("Deleted empty note types:\n" + "\n".join(deleted))
    if skipped:
        message_parts.append(
            "Already present and left unchanged:\n" + "\n".join(skipped)
        )
    if created or overwritten or deleted:
        message_parts.append(
            "Sync this profile to make the note type changes available on other devices."
        )
    showInfo("\n\n".join(message_parts))
    return True
