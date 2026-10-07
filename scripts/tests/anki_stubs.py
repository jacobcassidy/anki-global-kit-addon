"""Load real add-on services without running the Anki entry point."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PACKAGE = "kit.desktop.settings"


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_settings_services(*, mac=False, config=None):
    aqt = ModuleType("aqt")
    aqt.mw = SimpleNamespace(addonManager=SimpleNamespace(getConfig=lambda _name: config or {}))
    utils = ModuleType("aqt.utils")
    utils.is_mac = mac
    utils.showWarning = Mock()
    with patch.dict(sys.modules, {"aqt": aqt, "aqt.utils": utils}):
        load_module(f"{SETTINGS_PACKAGE}.configs.asset_manifest", "addon/desktop/settings/configs/asset_manifest.py")
        load_module(f"{SETTINGS_PACKAGE}.configs.constants", "addon/desktop/settings/configs/constants.py")
        settings = load_module(f"{SETTINGS_PACKAGE}.services.config", "addon/desktop/settings/services/config.py")
        assets = load_module(f"{SETTINGS_PACKAGE}.services.assets", "addon/desktop/settings/services/assets.py")
    return SimpleNamespace(config=settings, assets=assets, mw=aqt.mw, warning=utils.showWarning)


def load_shortcut_helpers(*, mac=False):
    utils = ModuleType("aqt.utils")
    utils.is_mac = mac
    with patch.dict(sys.modules, {"aqt.utils": utils}):
        return load_module(f"{SETTINGS_PACKAGE}.helpers.shortcuts", "addon/desktop/settings/helpers/shortcuts.py")


def load_editor_integration(settings, *, mac=False):
    aqt = ModuleType("aqt")
    aqt.gui_hooks = SimpleNamespace()
    editor = ModuleType("aqt.editor")
    editor.Editor = object
    settings_package = ModuleType(SETTINGS_PACKAGE)
    settings_package.get_editor_settings = lambda: settings
    constants = ModuleType(f"{SETTINGS_PACKAGE}.configs.constants")
    constants.USER_FILES_DIR = ROOT / "addon/user_files"
    paste = ModuleType("kit.desktop.editor.features.paste.cleanup")
    paste.clean_paste_mime = Mock()
    paste.finish_paste_layout = Mock()
    labels = ModuleType("kit.desktop.editor.features.shortcuts.labels")
    labels.shortcut_label = lambda keys: keys
    helpers = load_shortcut_helpers(mac=mac)
    with patch.dict(sys.modules, {
        "aqt": aqt, "aqt.editor": editor, SETTINGS_PACKAGE: settings_package,
        constants.__name__: constants, paste.__name__: paste, labels.__name__: labels,
        helpers.__name__: helpers,
    }):
        return load_module("kit.desktop.editor.integration", "addon/desktop/editor/integration.py")
