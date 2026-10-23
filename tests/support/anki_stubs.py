"""Load real add-on services without running the Anki entry point."""

import importlib.util
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
DESKTOP_PACKAGE = "kit.desktop"


def ensure_package(name):
    """Create package shells so relative imports avoid add-on startup."""
    parts = name.split(".")
    for index in range(1, len(parts) + 1):
        package_name = ".".join(parts[:index])
        if package_name in sys.modules:
            continue
        package = ModuleType(package_name)
        package_root = ROOT / "addon" / Path(*parts[1:index])
        package.__path__ = [str(package_root)]
        package.__package__ = package_name
        sys.modules[package_name] = package


def load_module(name, relative_path):
    ensure_package(name.rpartition(".")[0])
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_settings_services(*, mac=False, config=None):
    aqt = ModuleType("aqt")
    setattr(
        aqt,
        "mw",
        SimpleNamespace(
            addonManager=SimpleNamespace(getConfig=lambda _name: config or {})
        ),
    )
    utils = ModuleType("aqt.utils")
    setattr(utils, "is_mac", mac)
    setattr(utils, "showWarning", Mock())
    with patch.dict(sys.modules, {"aqt": aqt, "anki.utils": utils, "aqt.utils": utils}):
        load_module(f"{DESKTOP_PACKAGE}.paths", "addon/desktop/paths.py")
        load_module(
            f"{DESKTOP_PACKAGE}.media.manifest",
            "addon/desktop/media/manifest.py",
        )
        load_module(
            f"{DESKTOP_PACKAGE}.syntax_highlighting.themes",
            "addon/desktop/syntax_highlighting/themes.py",
        )
        load_module(
            f"{DESKTOP_PACKAGE}.config.constants",
            "addon/desktop/config/constants.py",
        )
        load_module(
            f"{DESKTOP_PACKAGE}.config.defaults",
            "addon/desktop/config/defaults.py",
        )
        settings = load_module(
            f"{DESKTOP_PACKAGE}.config.service",
            "addon/desktop/config/service.py",
        )
        assets = load_module(
            f"{DESKTOP_PACKAGE}.media.install",
            "addon/desktop/media/install.py",
        )
    return SimpleNamespace(
        config=settings, assets=assets, mw=aqt.mw, warning=utils.showWarning
    )


def load_shortcut_helpers(*, mac=False):
    utils = ModuleType("aqt.utils")
    setattr(utils, "is_mac", mac)
    with patch.dict(sys.modules, {"anki.utils": utils, "aqt.utils": utils}):
        return load_module(
            f"{DESKTOP_PACKAGE}.shortcuts.formatting",
            "addon/desktop/shortcuts/formatting.py",
        )


def load_editor_integration(settings, *, mac=False):
    aqt = ModuleType("aqt")
    setattr(aqt, "gui_hooks", SimpleNamespace())
    setattr(aqt, "mw", SimpleNamespace(col=None))
    editor = ModuleType("aqt.editor")
    setattr(editor, "Editor", object)
    qt = ModuleType("aqt.qt")
    setattr(qt, "QApplication", Mock())
    setattr(qt, "QMenu", Mock())
    setattr(qt, "QKeySequence", str)
    setattr(qt, "sip", SimpleNamespace(isdeleted=lambda _widget: False))

    class Shortcut:
        def __init__(self, key, parent):
            self.key = key
            self.parent = parent
            self.callback = None
            self.activated = SimpleNamespace(
                connect=lambda callback: setattr(self, "callback", callback)
            )
            self.enabled = True

        def setKey(self, key):
            self.key = key

        def setEnabled(self, enabled):
            self.enabled = enabled

        def isEnabled(self):
            return self.enabled

    setattr(qt, "QShortcut", Shortcut)
    settings_package = ModuleType(f"{DESKTOP_PACKAGE}.config.service")
    setattr(settings_package, "get_editor_settings", lambda: settings)
    paths = ModuleType(f"{DESKTOP_PACKAGE}.paths")
    setattr(paths, "ADDON_DIR", ROOT / "addon")
    setattr(paths, "USER_FILES_DIR", ROOT / "addon/user_files")
    setattr(paths, "ICON_ASSET_DIR", ROOT / "addon/assets/icons")
    manifest = ModuleType(f"{DESKTOP_PACKAGE}.media.manifest")
    setattr(manifest, "JS_ASSET_NAME", "_anki-global-kit.min.js")
    setattr(
        manifest,
        "EDITOR_ASSET_PATHS",
        {
            "editor.min.js": ROOT / "addon/assets/editor/js/editor.min.js",
            "editor-fields.min.css": ROOT
            / "addon/assets/editor/css/editor-fields.min.css",
            "editor-ui.min.css": ROOT / "addon/assets/editor/css/editor-ui.min.css",
        },
    )
    labels = ModuleType("kit.desktop.shortcuts.labels")
    setattr(labels, "shortcut_label", lambda keys: keys)
    helpers = load_shortcut_helpers(mac=mac)
    with patch.dict(
        sys.modules,
        {
            "aqt": aqt,
            "aqt.editor": editor,
            "aqt.qt": qt,
            f"{DESKTOP_PACKAGE}.config.service": settings_package,
            paths.__name__: paths,
            manifest.__name__: manifest,
            labels.__name__: labels,
            helpers.__name__: helpers,
        },
    ):
        return load_module(
            "kit.desktop.editor.integration", "addon/desktop/editor/integration.py"
        )


class OpChanges:
    """The merge contract used by the collection-operation wrapper."""

    def __init__(self, *, notetype=False):
        self.notetype = notetype

    def MergeFrom(self, other):
        self.notetype |= other.notetype


def load_note_type_service(collection):
    aqt = ModuleType("aqt")
    setattr(aqt, "mw", SimpleNamespace(col=collection))
    anki_collection = ModuleType("anki.collection")
    setattr(anki_collection, "Collection", object)
    setattr(anki_collection, "OpChanges", OpChanges)
    consts = ModuleType("anki.consts")
    setattr(consts, "MODEL_STD", 0)
    setattr(consts, "MODEL_CLOZE", 1)
    stock = ModuleType("anki.stdmodels")
    setattr(
        stock,
        "get_stock_notetypes",
        lambda _col: [
            (
                "Cloze",
                lambda _col: deepcopy(
                    {
                        "id": 0,
                        "name": "Cloze",
                        "type": 1,
                        "sortf": 0,
                        "css": "",
                        "flds": [{"name": "Text", "ord": 0}],
                        "tmpls": [
                            {
                                "name": "Cloze",
                                "ord": 0,
                                "qfmt": "{{cloze:Text}}",
                                "afmt": "{{cloze:Text}}",
                            }
                        ],
                    }
                ),
            )
        ],
    )
    with patch.dict(
        sys.modules,
        {
            "aqt": aqt,
            "anki.collection": anki_collection,
            "anki.consts": consts,
            "anki.stdmodels": stock,
        },
    ):
        return load_module(
            f"{DESKTOP_PACKAGE}.note_types.service",
            "addon/desktop/note_types/service.py",
        )


def load_note_type_actions(service):
    aqt = ModuleType("aqt")
    setattr(aqt, "mw", SimpleNamespace(col=None))
    operations = ModuleType("aqt.operations")
    operation = Mock()
    operation.success.return_value = operation
    operation.failure.return_value = operation
    setattr(operations, "CollectionOp", Mock(return_value=operation))
    qt = ModuleType("aqt.qt")
    setattr(qt, "QWidget", object)
    for name in (
        "QDialog",
        "QDialogButtonBox",
        "QHBoxLayout",
        "QLabel",
        "QListWidget",
        "QListWidgetItem",
        "QPushButton",
        "Qt",
        "QVBoxLayout",
    ):
        setattr(qt, name, Mock())
    utils = ModuleType("aqt.utils")
    setattr(utils, "askUser", Mock(return_value=False))
    setattr(utils, "showInfo", Mock())
    setattr(utils, "showWarning", Mock())
    anki_collection = ModuleType("anki.collection")
    setattr(anki_collection, "Collection", object)
    setattr(anki_collection, "OpChanges", OpChanges)
    with patch.dict(
        sys.modules,
        {
            "aqt": aqt,
            "aqt.operations": operations,
            "aqt.qt": qt,
            "anki.utils": utils,
            "aqt.utils": utils,
            "anki.collection": anki_collection,
            service.__name__: service,
        },
    ):
        actions = load_module(
            "kit.desktop.settings.pages.note_types.actions",
            "addon/desktop/settings/pages/note_types/actions.py",
        )
    return SimpleNamespace(
        actions=actions,
        operation=operation,
        factory=operations.CollectionOp,
        confirm=utils.askUser,
        warning=utils.showWarning,
        info=utils.showInfo,
    )
