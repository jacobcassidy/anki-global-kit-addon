"""Paths and public filenames for card assets shipped with the add-on."""

from pathlib import Path


ADDON_DIR = Path(__file__).resolve().parents[3]
ASSET_DIR = ADDON_DIR / "web" / "assets"
SHARED_ASSET_DIR = ADDON_DIR / "shared" / "assets"
JS_ASSET_NAME = "_anki-global-kit.min.js"
CSS_ASSET_NAME = "_anki-global-kit.min.css"
FONT_ASSET_NAME = "_mesloLGL-NF.woff2"
ASSET_PATHS = {
    JS_ASSET_NAME: ASSET_DIR / "js" / JS_ASSET_NAME,
    CSS_ASSET_NAME: ASSET_DIR / "css" / CSS_ASSET_NAME,
    FONT_ASSET_NAME: SHARED_ASSET_DIR / "fonts" / FONT_ASSET_NAME,
}
ASSET_NAMES = tuple(ASSET_PATHS)
