"""Add-on package identity and release version."""

import json

from ..paths import ADDON_DIR

assert __package__ is not None
ADDON_PACKAGE_NAME = __package__.split(".", maxsplit=1)[0]
VERSION = json.loads((ADDON_DIR / "manifest.json").read_text(encoding="utf-8"))[
    "version"
]
