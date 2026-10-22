"""Coordinate saving settings and applying them to open Desktop surfaces."""

from aqt.qt import QDialog
from aqt.utils import showWarning

from ..config.constants import ADDON_PACKAGE_NAME
from ..config.service import write_settings
from ..media.install import update_assets_for_profile
from ..syntax_highlighting.preferences import (
    THEME_FORMAT_VERSION,
    get_themes,
    set_themes,
)
from ..syntax_highlighting.themes import resolve_preset


def save_settings(
    dialog: QDialog,
    settings: dict[str, object],
    selected_themes: dict[str, str] | None = None,
    theme_snapshot: dict[str, dict] | None = None,
    publish_modes: set[str] | None = None,
) -> None:
    from aqt import mw

    from ..editor.integration import refresh_open_editors

    previous_local = mw.addonManager.getConfig(ADDON_PACKAGE_NAME) or {}
    if not isinstance(previous_local, dict):
        previous_local = {}
    previous_themes = (
        mw.col.get_config("anki_global_kit.syntax_highlighting.themes", {})
        if mw.col is not None
        else None
    )
    updated_themes = None
    if selected_themes and mw.col is not None:
        raw = previous_themes
        if (
            isinstance(raw, dict)
            and type(raw.get("version", 1)) is int
            and raw.get("version", 1) > THEME_FORMAT_VERSION
        ):
            showWarning(
                "This collection has syntax theme data from a newer Kit version. Update Anki Global Kit before changing themes."
            )
            return
        current_themes = get_themes(mw.col)
        candidate_themes = {}
        changed_modes = set()
        publish_modes = publish_modes or set()
        for mode in ("light", "dark"):
            current = current_themes.get(mode)
            selected = selected_themes.get(mode, "cassidy-dark")
            snapshot = (theme_snapshot or {}).get(mode, {})
            if (
                current is not None
                and (
                    current["revision"] != snapshot.get("revision", 0)
                    or current["id"] != snapshot.get("id", "cassidy-dark")
                )
                and selected != current["id"]
            ):
                showWarning(
                    "The collection's syntax theme changed while Settings was open. "
                    "Close Settings, reopen it, and review the current theme before saving."
                )
                return
            if (
                current is not None
                and current["id"] == selected
                and mode not in publish_modes
            ):
                candidate_themes[mode] = current
            else:
                candidate_themes[mode] = resolve_preset(selected)
                changed_modes.add(mode)
        if changed_modes:
            updated_themes = candidate_themes

    try:
        if updated_themes is not None:
            set_themes(mw.col, updated_themes, publish_modes)
        merged_local = dict(previous_local)
        merged_local.update(settings)
        write_settings(merged_local)
        if mw.col is not None and not update_assets_for_profile():
            raise RuntimeError(
                "Anki could not install the selected syntax theme stylesheet."
            )
    except Exception as error:
        try:
            mw.addonManager.writeConfig(ADDON_PACKAGE_NAME, previous_local)
            if mw.col is not None:
                mw.col.set_config(
                    "anki_global_kit.syntax_highlighting.themes", previous_themes
                )
                if not update_assets_for_profile():
                    raise RuntimeError(
                        "Anki could not restore the previous card assets."
                    )
        except Exception as recovery_error:
            showWarning(
                "Settings could not be saved, and restoring the previous settings also failed. "
                f"Save error: {error}\nRecovery error: {recovery_error}"
            )
            return
        showWarning(
            f"Settings could not be saved. The previous settings were restored.\n{error}"
        )
        return

    refresh_open_editors()
    dialog.accept()
