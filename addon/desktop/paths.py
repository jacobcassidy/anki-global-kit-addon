"""Filesystem paths shared by Desktop services."""

from pathlib import Path

ADDON_DIR = Path(__file__).resolve().parent.parent
USER_FILES_DIR = ADDON_DIR / "user_files"
ASSET_DIR = ADDON_DIR / "assets"
CARD_ASSET_DIR = ASSET_DIR / "cards"
EDITOR_ASSET_DIR = ASSET_DIR / "editor"
ICON_ASSET_DIR = ASSET_DIR / "icons"
FONT_ASSET_DIR = ASSET_DIR / "fonts"
