"""Create topic-specific Anki Global Kit note types from template parts."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from html import escape
from pathlib import Path

from anki.consts import MODEL_CLOZE, MODEL_STD
from anki.stdmodels import get_stock_notetypes
from aqt import mw


ADDON_DIR = Path(__file__).resolve().parents[3]
TEMPLATE_DIR = ADDON_DIR / "templates" / "note-types" / "parts"
HTML_DIR = TEMPLATE_DIR / "html"
STYLING_DIR = TEMPLATE_DIR / "styling"
SCRIPT_PATH = TEMPLATE_DIR / "script" / "card-script.js"


@dataclass(frozen=True)
class NoteTypeOperation:
    topic: str
    card_format: str
    name: str


@dataclass(frozen=True)
class NoteTypeTemplateRemoval:
    name: str
    ordinal: int
    card_count: int


@dataclass(frozen=True)
class NoteTypeReplacementImpact:
    name: str
    notetype_id: int
    removed_templates: tuple[NoteTypeTemplateRemoval, ...]

    @property
    def removed_card_count(self) -> int:
        return sum(template.card_count for template in self.removed_templates)


@dataclass(frozen=True)
class NoteTypeChangePlan:
    creates: tuple[NoteTypeOperation, ...]
    overwrites: tuple[NoteTypeOperation, ...]
    deletions: tuple[NoteTypeOperation, ...]
    skipped: tuple[str, ...]
    replacement_impacts: tuple[NoteTypeReplacementImpact, ...]


@dataclass(frozen=True)
class NoteTypeChangeResult:
    created: tuple[str, ...]
    overwritten: tuple[str, ...]
    deleted: tuple[str, ...]
    skipped: tuple[str, ...]


class NoteTypeServiceError(Exception):
    """Base class for note type service failures that the UI can present."""


class NoActiveCollectionError(NoteTypeServiceError):
    pass


class DeletionValidationError(NoteTypeServiceError):
    def __init__(self, name: str, *, missing: bool, after_confirmation: bool = False):
        self.name = name
        self.missing = missing
        self.after_confirmation = after_confirmation


class MissingTemplateFilesError(NoteTypeServiceError):
    def __init__(self, paths: tuple[str, ...]):
        self.paths = paths


class ReplacementValidationError(NoteTypeServiceError):
    """An existing type is missing or incompatible with the requested format."""


class NoteTypeApplyError(NoteTypeServiceError):
    def __init__(self, applied_names: tuple[str, ...], cause: Exception):
        self.applied_names = applied_names
        self.cause = cause


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
    # Anki parses field expressions before the browser decodes HTML entities.
    topic_heading = escape(topic).replace("{", "&#123;").replace("}", "&#125;")
    html = html.replace(
        '<h1 class="topic">Topic</h1>',
        f'<h1 class="topic">{topic_heading}</h1>',
    )
    return f"{html.rstrip()}\n\n<script>\n{script.rstrip()}\n</script>\n"


def _stock_cloze_note_type() -> dict[str, object]:
    # Stock definitions come from Anki, independently of the profile's types.
    # Copy the factory result before customizing its fields and templates.
    for _name, factory in get_stock_notetypes(mw.col):
        notetype = factory(mw.col)
        if notetype["type"] == MODEL_CLOZE:
            return deepcopy(notetype)
    raise NoteTypeServiceError("Anki's stock Cloze definition is unavailable.")


def _validate_replacement_type(
    name: str,
    spec: dict[str, object],
    notetype: dict[str, object] | None,
) -> None:
    if notetype is None:
        raise ReplacementValidationError(
            f"The note type {name} no longer exists. Reopen settings and try again."
        )
    expected_type = MODEL_CLOZE if spec["cloze"] else MODEL_STD
    if notetype["type"] != expected_type:
        expected = "Cloze" if spec["cloze"] else "standard"
        raise ReplacementValidationError(
            f"The note type {name} is not a {expected} note type and cannot be "
            "replaced with this format. Rename this type in Anki before creating "
            "the kit type with this name."
        )


def _replacement_impacts(
    operations: tuple[NoteTypeOperation, ...],
) -> tuple[NoteTypeReplacementImpact, ...]:
    """Validate replacements and count cards belonging to removed standard templates."""
    impacts: list[NoteTypeReplacementImpact] = []
    for operation in operations:
        notetype = mw.col.models.by_name(operation.name)
        _validate_replacement_type(
            operation.name,
            FORMATS[operation.card_format],
            notetype,
        )
        # Cloze card ordinals identify deletions, not separate card templates.
        removed_templates: tuple[NoteTypeTemplateRemoval, ...] = ()
        if notetype["type"] == MODEL_STD:
            removed_templates = tuple(
                NoteTypeTemplateRemoval(
                    name=template["name"],
                    ordinal=template["ord"],
                    card_count=mw.col.models.template_use_count(
                        notetype["id"], template["ord"],
                    ),
                )
                for template in notetype["tmpls"][1:]
            )
        impacts.append(
            NoteTypeReplacementImpact(
                name=operation.name,
                notetype_id=notetype["id"],
                removed_templates=removed_templates,
            )
        )
    return tuple(impacts)


def _create_note_type(
    name: str,
    topic: str,
    spec: dict[str, object],
    existing_notetype: dict[str, object] | None = None,
) -> None:
    models = mw.col.models
    if existing_notetype is not None:
        _validate_replacement_type(name, spec, existing_notetype)
        notetype = deepcopy(existing_notetype)
        fields_by_name = {field["name"]: field for field in notetype["flds"]}
        for field_name in spec["fields"]:
            if field_name not in fields_by_name:
                field = models.new_field(field_name)
                models.add_field(notetype, field)
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
        notetype = _stock_cloze_note_type()
        notetype["id"] = 0
        notetype["name"] = name
        notetype["flds"] = []
        notetype["tmpls"] = [notetype["tmpls"][0]]
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


def plan_note_type_changes(
    selections: dict[str, set[str]],
    overwrites: dict[str, set[str]] | None = None,
    deletions: dict[str, set[str]] | None = None,
) -> NoteTypeChangePlan:
    """Plan changes and validate replacement formats, templates, and deletions."""
    if mw.col is None:
        raise NoActiveCollectionError

    overwrites = overwrites or {}
    deletions = deletions or {}
    selected = [
        (topic, card_format)
        for topic, selected_formats in selections.items()
        for card_format in FORMATS
        if card_format in selected_formats
    ]
    existing_names = {entry.name for entry in mw.col.models.all_names_and_ids()}
    requested = tuple(
        NoteTypeOperation(topic, card_format, f"{topic} ({card_format})")
        for topic, card_format in selected
    )
    creates = tuple(operation for operation in requested if operation.name not in existing_names)
    overwrite_operations = tuple(
        operation
        for operation in requested
        if operation.name in existing_names
        and operation.card_format in overwrites.get(operation.topic, set())
    )
    replacement_impacts = _replacement_impacts(overwrite_operations)
    skipped = tuple(
        operation.name
        for operation in requested
        if operation.name in existing_names and operation not in overwrite_operations
    )
    requested_deletions = tuple(
        NoteTypeOperation(topic, card_format, f"{topic} ({card_format})")
        for topic, selected_formats in deletions.items()
        for card_format in FORMATS
        if card_format in selected_formats
    )
    for operation in requested_deletions:
        notetype = mw.col.models.by_name(operation.name)
        if notetype is None:
            raise DeletionValidationError(operation.name, missing=True)
        if mw.col.models.use_count(notetype):
            raise DeletionValidationError(operation.name, missing=False)

    selected_for_templates = {
        (operation.topic, operation.card_format)
        for operation in (*creates, *overwrite_operations)
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
    missing_paths = tuple(
        str(path.relative_to(ADDON_DIR))
        for path in required_paths
        if not path.is_file()
    )
    if missing_paths:
        raise MissingTemplateFilesError(missing_paths)

    return NoteTypeChangePlan(
        creates=creates,
        overwrites=overwrite_operations,
        deletions=requested_deletions,
        skipped=skipped,
        replacement_impacts=replacement_impacts,
    )


def _revalidate_deletions(
    operations: tuple[NoteTypeOperation, ...],
) -> None:
    if mw.col is None:
        raise NoActiveCollectionError
    for operation in operations:
        notetype = mw.col.models.by_name(operation.name)
        if notetype is None:
            raise DeletionValidationError(
                operation.name,
                missing=True,
                after_confirmation=True,
            )
        if mw.col.models.use_count(notetype):
            raise DeletionValidationError(
                operation.name,
                missing=False,
                after_confirmation=True,
            )


def apply_note_type_changes(plan: NoteTypeChangePlan) -> NoteTypeChangeResult:
    """Apply a previously confirmed note type change plan."""
    if mw.col is None:
        raise NoActiveCollectionError
    if _replacement_impacts(plan.overwrites) != plan.replacement_impacts:
        raise ReplacementValidationError(
            "The note types, additional templates, or card counts changed after "
            "confirmation. Review the selected actions and confirm again."
        )
    _revalidate_deletions(plan.deletions)

    created: list[str] = []
    overwritten: list[str] = []
    deleted: list[str] = []
    try:
        for operation in plan.creates:
            _create_note_type(
                operation.name,
                operation.topic,
                FORMATS[operation.card_format],
            )
            created.append(operation.name)
        for operation in plan.overwrites:
            existing_notetype = mw.col.models.by_name(operation.name)
            if existing_notetype is None:
                raise RuntimeError(
                    f"The existing note type {operation.name} could not be loaded."
                )
            _create_note_type(
                operation.name,
                operation.topic,
                FORMATS[operation.card_format],
                existing_notetype,
            )
            overwritten.append(operation.name)
        for operation in plan.deletions:
            notetype = mw.col.models.by_name(operation.name)
            if notetype is None:
                raise RuntimeError(
                    f"The note type {operation.name} could not be loaded."
                )
            mw.col.models.remove(notetype["id"])
            deleted.append(operation.name)
    except Exception as error:
        applied_names = tuple(created + overwritten + deleted)
        raise NoteTypeApplyError(applied_names, error) from error

    return NoteTypeChangeResult(
        created=tuple(created),
        overwritten=tuple(overwritten),
        deleted=tuple(deleted),
        skipped=plan.skipped,
    )
