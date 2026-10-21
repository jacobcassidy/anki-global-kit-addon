"""Packaged asset locations and public filenames."""

from ..paths import (
    CARD_ASSET_DIR,
    EDITOR_ASSET_DIR,
    FONT_ASSET_DIR,
    ICON_ASSET_DIR,
)

JS_ASSET_NAME = "_anki-global-kit.min.js"
CSS_ASSET_NAME = "_anki-global-kit.min.css"
FONT_ASSET_NAME = "_meslolgl-nf.woff2"
FONT_LICENSE_ASSET_NAME = "_meslolgl-nf-license.txt"
SYNTAX_CSS_ASSET_NAME = "_syntax-highlighting.css"

ASSET_PATHS = {
    JS_ASSET_NAME: CARD_ASSET_DIR / "js" / JS_ASSET_NAME,
    CSS_ASSET_NAME: CARD_ASSET_DIR / "css" / CSS_ASSET_NAME,
    FONT_LICENSE_ASSET_NAME: FONT_ASSET_DIR / FONT_LICENSE_ASSET_NAME,
    FONT_ASSET_NAME: FONT_ASSET_DIR / FONT_ASSET_NAME,
}
ASSET_NAMES = tuple(ASSET_PATHS)

EDITOR_ASSET_PATHS = {
    "editor.min.js": EDITOR_ASSET_DIR / "js" / "editor.min.js",
    "editor-fields.min.css": EDITOR_ASSET_DIR / "css" / "editor-fields.min.css",
    "editor-ui.min.css": EDITOR_ASSET_DIR / "css" / "editor-ui.min.css",
}
ICON_ASSET_PATHS = {path.name: path for path in ICON_ASSET_DIR.glob("*.svg")}
