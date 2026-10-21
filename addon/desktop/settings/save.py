"""Coordinate saving settings and applying them to open Desktop surfaces."""

from aqt.qt import QDialog

from ..config.service import write_settings
from ..media.install import update_assets_for_profile


def save_settings(dialog: QDialog, settings: dict[str, object]) -> None:
    from ..editor.integration import refresh_open_editors

    write_settings(settings)
    update_assets_for_profile()
    refresh_open_editors()
    dialog.accept()
