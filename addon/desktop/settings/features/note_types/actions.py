"""Confirm note type changes and present service results and errors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from anki.collection import Collection, OpChanges
from aqt.operations import CollectionOp
from aqt.qt import QWidget
from aqt.utils import askUser, showInfo, showWarning

from ...services.note_types import (
    DeletionValidationError,
    MissingTemplateFilesError,
    NoActiveCollectionError,
    NoteTypeApplyError,
    NoteTypeChangePlan,
    NoteTypeChangeResult,
    NoteTypeServiceError,
    apply_note_type_changes,
    plan_note_type_changes,
)


@dataclass(frozen=True)
class _OperationResult:
    changes: OpChanges
    result: NoteTypeChangeResult | None = None
    error: NoteTypeApplyError | None = None


def _apply_plan(col: Collection, plan: NoteTypeChangePlan) -> _OperationResult:
    # Partial success must still return changes so CollectionOp refreshes Anki.
    try:
        result = apply_note_type_changes(plan, col)
    except NoteTypeApplyError as error:
        return _OperationResult(changes=error.changes, error=error)
    return _OperationResult(changes=result.changes, result=result)


def _show_note_type_service_error(error: NoteTypeServiceError) -> None:
    if isinstance(error, NoActiveCollectionError):
        showWarning("Open an Anki profile before creating Anki Global Kit note types.")
    elif isinstance(error, DeletionValidationError):
        if error.missing:
            showWarning(
                f"The note type {error.name} no longer exists. "
                "Reopen settings and try again."
            )
        elif error.after_confirmation:
            showWarning(
                f"The note type {error.name} now contains notes and cannot be deleted. "
                "Move its notes to another note type in Anki first."
            )
        else:
            showWarning(
                f"The note type {error.name} contains notes and cannot be deleted here. "
                "Move its notes to another note type in Anki first."
            )
    elif isinstance(error, MissingTemplateFilesError):
        showWarning(
            "Anki Global Kit card template files are missing. Rebuild or reinstall "
            "the add-on package.\n\n" + "\n".join(error.paths)
        )
    elif isinstance(error, NoteTypeApplyError):
        applied = "\n".join(error.applied_names) if error.applied_names else "None"
        showWarning(
            "Anki Global Kit could not apply all selected note type changes.\n\n"
            f"Applied changes:\n{applied}\n\nError: {error.cause}"
        )
    else:
        showWarning(str(error))


def apply_selected_note_type_changes(
    selections: dict[str, set[str]],
    overwrites: dict[str, set[str]],
    deletions: dict[str, set[str]],
    *,
    parent: QWidget,
    on_complete: Callable[[bool], None],
) -> None:
    """Plan and confirm collection changes, then report the applied results."""
    try:
        plan = plan_note_type_changes(selections, overwrites, deletions)
    except NoteTypeServiceError as error:
        _show_note_type_service_error(error)
        on_complete(False)
        return

    if not plan.creates and not plan.overwrites and not plan.deletions:
        if plan.skipped:
            showInfo(
                "All selected note types already exist in this profile. "
                "Select Replace beside an existing format to update it."
            )
        else:
            showInfo("Select at least one note type action to apply.")
        on_complete(False)
        return

    confirmation = []
    if plan.creates:
        names = "\n".join(f"• {operation.name}" for operation in plan.creates)
        confirmation.append(f"Create these new note types?\n{names}")
    if plan.overwrites:
        names = "\n".join(f"• {operation.name}" for operation in plan.overwrites)
        replacement_confirmation = (
            "Replace these existing note types with the kit templates and styling?\n"
            "Their notes and fields will be kept; missing kit fields will be added, "
            "and their first card template will be updated.\n"
            f"{names}"
        )
        removals = []
        for impact in plan.replacement_impacts:
            if not impact.removed_templates:
                continue
            template_names = ", ".join(template.name for template in impact.removed_templates)
            removals.append(
                f"• {impact.name}\n"
                f"  Additional templates to remove: {len(impact.removed_templates)} "
                f"({template_names})\n"
                f"  Cards to remove: {impact.removed_card_count}"
            )
        if removals:
            replacement_confirmation += (
                "\n\nThese additional card templates and their associated cards "
                "will be removed. The removed cards' scheduling will be lost.\n"
                + "\n".join(removals)
            )
        confirmation.append(replacement_confirmation)
    if plan.deletions:
        names = "\n".join(f"• {operation.name}" for operation in plan.deletions)
        confirmation.append(
            "Delete these empty note types? They contain no notes.\n" + names
        )
    if not askUser(
        "Apply the selected note type changes in the active Anki profile?\n\n"
        + "\n\n".join(confirmation)
    ):
        on_complete(False)
        return

    def success(outcome: _OperationResult) -> None:
        if outcome.error is not None:
            _show_note_type_service_error(outcome.error)
            on_complete(False)
            return
        _show_note_type_result(outcome.result)
        on_complete(True)

    def failure(error: Exception) -> None:
        if isinstance(error, NoteTypeServiceError):
            _show_note_type_service_error(error)
        else:
            showWarning(f"Anki Global Kit could not update note types: {error}")
        on_complete(False)

    CollectionOp(parent=parent, op=lambda col: _apply_plan(col, plan)).success(
        success
    ).failure(failure).run_in_background()


def _show_note_type_result(result: NoteTypeChangeResult) -> None:
    message_parts = []
    if result.created:
        message_parts.append("Created note types:\n" + "\n".join(result.created))
    if result.overwritten:
        message_parts.append("Replaced note types:\n" + "\n".join(result.overwritten))
    if result.deleted:
        message_parts.append("Deleted empty note types:\n" + "\n".join(result.deleted))
    if result.skipped:
        message_parts.append(
            "Already present and left unchanged:\n" + "\n".join(result.skipped)
        )
    if result.created or result.overwritten or result.deleted:
        message_parts.append(
            "Sync this profile to make the note type changes available on other devices."
        )
    showInfo("\n\n".join(message_parts))
