"""Load canonical pure Desktop modules without running Anki add-on startup."""

import importlib
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parent.parent
ADDON_DIR = ROOT / "addon"
PACKAGE_NAME = "anki_global_kit_headless"


def load_addon_module(module_name: str):
    """Import a module from ``addon/`` under an isolated, startup-free package."""
    if PACKAGE_NAME not in sys.modules:
        package = ModuleType(PACKAGE_NAME)
        package.__path__ = [str(ADDON_DIR)]
        package.__package__ = PACKAGE_NAME
        sys.modules[PACKAGE_NAME] = package

    return importlib.import_module(f"{PACKAGE_NAME}.{module_name}")
