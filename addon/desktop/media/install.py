"""Install and refresh the add-on card assets in the active profile."""

import json
from pathlib import Path

from aqt import mw
from aqt.utils import showWarning

from ..config.service import get_card_web_settings
from ..syntax_highlighting.preferences import get_themes
from ..syntax_highlighting.themes import generate_theme_pair_css
from .manifest import ASSET_NAMES, ASSET_PATHS, JS_ASSET_NAME, SYNTAX_CSS_ASSET_NAME


def _write_managed_asset(name: str, data: bytes) -> None:
    destination = Path(mw.col.media.dir()) / name
    previous = destination.read_bytes() if destination.is_file() else None
    if previous == data:
        return

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


def update_assets_for_profile() -> bool:
    """Install or refresh the managed card assets when a profile opens."""
    if mw.col is None:
        return False

    missing = [name for name in ASSET_NAMES if not ASSET_PATHS[name].is_file()]
    if missing:
        showWarning(
            "Anki Global Kit assets have not been built. From the project folder, "
            "run `npm run build`, then restart Anki and try again."
        )
        return False

    try:
        for name in ASSET_NAMES:
            data = ASSET_PATHS[name].read_bytes()
            if name == JS_ASSET_NAME:
                web_settings = get_card_web_settings()
                settings = json.dumps(web_settings, separators=(",", ":"))
                data = f"globalThis.ankiGlobalKitSettings={settings};\n".encode() + data
            _write_managed_asset(name, data)

        themes = get_themes(mw.col)
        css = generate_theme_pair_css(themes.get("light"), themes.get("dark"))
        _write_managed_asset(SYNTAX_CSS_ASSET_NAME, css.encode("utf-8"))
        return True
    except Exception as error:  # Anki's media backend reports filesystem errors here.
        showWarning(f"Could not refresh Anki Global Kit card files:\n{error}")
        return False
