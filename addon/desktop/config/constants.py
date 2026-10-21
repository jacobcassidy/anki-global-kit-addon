"""Pure release defaults and reusable Desktop layout values."""

import json

from ..paths import ADDON_DIR

ADDON_PACKAGE_NAME = __package__.split(".", maxsplit=1)[0]
VERSION = json.loads((ADDON_DIR / "manifest.json").read_text(encoding="utf-8"))[
    "version"
]
SECTION_SPACING = 24
MARKDOWN_BLOCK_SPACING = 12
NOTE_TYPES_ROW_PADDING = 4
NESTED_INDENT = 20
COLOR_TRANSPARENT = "transparent"
ZERO_MARGINS = (0, 0, 0, 0)
