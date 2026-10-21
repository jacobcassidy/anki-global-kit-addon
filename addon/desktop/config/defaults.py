"""Release defaults loaded from Anki's add-on configuration file."""

import json

from ..paths import ADDON_DIR

_release_config = json.loads((ADDON_DIR / "config.json").read_text(encoding="utf-8"))
DEFAULT_SETTINGS = {
    name: value
    for name, value in _release_config.items()
    if name != "note_type_selections"
}
