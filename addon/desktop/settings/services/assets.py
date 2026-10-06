"""Install and refresh the add-on card assets in the active profile."""

import json
from pathlib import Path

from aqt import mw
from aqt.utils import is_mac, showWarning

from .config import get_settings
from ..configs.constants import (
    ASSET_NAMES, ASSET_PATHS, JS_ASSET_NAME,
)


def update_assets_for_profile() -> None:
    """Install or refresh the managed card assets when a profile opens."""
    if mw.col is None:
        return

    missing = [name for name in ASSET_NAMES if not ASSET_PATHS[name].is_file()]
    if missing:
        showWarning(
            "Anki Global Kit assets have not been built. From the project folder, "
            "run `npm run build:addon`, then restart Anki and try again."
        )
        return

    try:
        for name in ASSET_NAMES:
            data = ASSET_PATHS[name].read_bytes()
            if name == JS_ASSET_NAME:
                web_settings = get_settings()
                for action in ("increase", "decrease"):
                    key = f"card_input_tab_indent_{action}_shortcut"
                    # Keep physical Control consistent when this media file syncs
                    # from Desktop to another client's browser keyboard events.
                    physical_control = "Meta" if is_mac else "Ctrl"
                    web_settings[key] = "+".join(
                        "Control" if part == physical_control else part
                        for part in web_settings[key].split("+")
                    )
                settings = json.dumps(web_settings, separators=(",", ":"))
                data = f"globalThis.ankiGlobalKitSettings={settings};\n".encode() + data
            destination = Path(mw.col.media.dir()) / name
            previous = destination.read_bytes() if destination.is_file() else None
            if previous == data:
                continue

            # MediaManager.write_data intentionally avoids replacing media with
            # different content, so move an older kit-owned file to Anki's media
            # trash first. Keep a copy for recovery if writing the update fails.
            if previous is not None:
                mw.col.media.trash_files([name])
            try:
                stored_name = mw.col.media.write_data(name, data)
                if stored_name != name:
                    raise OSError(
                        f"Anki stored {name} under a different filename: {stored_name}"
                    )
            except Exception:
                if previous is not None:
                    mw.col.media.write_data(name, previous)
                raise
    except Exception as error:  # Anki's media backend reports filesystem errors here.
        showWarning(f"Could not refresh Anki Global Kit card files:\n{error}")
