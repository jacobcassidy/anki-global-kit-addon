"""Load real add-on services without running the Anki entry point."""

import importlib.util
from copy import deepcopy
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


class OpChanges:
    """The merge contract used by the collection-operation wrapper."""

    def __init__(self, *, notetype=False):
        self.notetype = notetype

    def MergeFrom(self, other):
        self.notetype |= other.notetype


def load_note_type_service(collection):
    aqt = ModuleType("aqt")
    aqt.mw = SimpleNamespace(col=collection)
    anki_collection = ModuleType("anki.collection")
    anki_collection.Collection = object
    anki_collection.OpChanges = OpChanges
    consts = ModuleType("anki.consts")
    consts.MODEL_STD = 0
    consts.MODEL_CLOZE = 1
    stock = ModuleType("anki.stdmodels")
    stock.get_stock_notetypes = lambda _col: [("Cloze", lambda _col: deepcopy({
        "id": 0, "name": "Cloze", "type": 1, "sortf": 0, "css": "",
        "flds": [{"name": "Text", "ord": 0}],
        "tmpls": [{"name": "Cloze", "ord": 0, "qfmt": "{{cloze:Text}}", "afmt": "{{cloze:Text}}"}],
    }))]
    with patch.dict(sys.modules, {
        "aqt": aqt, "anki.collection": anki_collection,
        "anki.consts": consts, "anki.stdmodels": stock,
    }):
        return load_module(f"{SETTINGS_PACKAGE}.services.note_types", "addon/desktop/settings/services/note_types.py")


def load_note_type_actions(service):
    operations = ModuleType("aqt.operations")
    operation = Mock()
    operation.success.return_value = operation
    operation.failure.return_value = operation
    operations.CollectionOp = Mock(return_value=operation)
    qt = ModuleType("aqt.qt")
    qt.QWidget = object
    utils = ModuleType("aqt.utils")
    utils.askUser = Mock(return_value=False)
    utils.showInfo = Mock()
    utils.showWarning = Mock()
    anki_collection = ModuleType("anki.collection")
    anki_collection.Collection = object
    anki_collection.OpChanges = OpChanges
    with patch.dict(sys.modules, {
        "aqt.operations": operations, "aqt.qt": qt, "aqt.utils": utils,
        "anki.collection": anki_collection, service.__name__: service,
    }):
        actions = load_module(f"{SETTINGS_PACKAGE}.features.note_types.actions", "addon/desktop/settings/features/note_types/actions.py")
    return SimpleNamespace(actions=actions, operation=operation, factory=operations.CollectionOp,
                           confirm=utils.askUser, warning=utils.showWarning)
