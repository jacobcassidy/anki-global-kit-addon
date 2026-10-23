"""Stub Anki and Qt boundaries while importing the complete add-on package."""

from types import ModuleType, SimpleNamespace
from unittest.mock import Mock


def make_startup_stubs(*, mac: bool):
    """Provide startup hooks and Qt types without replacing any Kit modules."""
    aqt = ModuleType("aqt")
    hooks = SimpleNamespace(
        profile_did_open=[],
        editor_did_init_buttons=[],
        editor_did_init_shortcuts=[],
        editor_will_load_note=[],
        editor_did_load_note=[],
        webview_did_receive_js_message=[],
        card_will_show=[],
        state_did_change=[],
        theme_did_change=[],
    )
    menu = Mock()
    setattr(aqt, "gui_hooks", hooks)
    setattr(aqt, "mw", SimpleNamespace(form=SimpleNamespace(menuTools=menu)))
    qt = ModuleType("aqt.qt")
    for name in (
        "QByteArray",
        "QCheckBox",
        "QDesktopServices",
        "QDialog",
        "QDialogButtonBox",
        "QEvent",
        "QFrame",
        "QGridLayout",
        "QGroupBox",
        "QHBoxLayout",
        "QInputDialog",
        "QKeySequence",
        "QLabel",
        "QLineEdit",
        "QListWidget",
        "QListWidgetItem",
        "QPainterPath",
        "QPixmap",
        "QPoint",
        "QPushButton",
        "QRectF",
        "QRegion",
        "QScrollArea",
        "QShortcut",
        "QSizePolicy",
        "QTabWidget",
        "QTextBrowser",
        "QTextCursor",
        "QTimer",
        "QUrl",
        "QVBoxLayout",
        "QWidget",
    ):
        setattr(qt, name, type(name, (), {}))

    class QObject:
        def __init__(self, parent):
            self.parent = parent

    app = Mock()
    setattr(qt, "QObject", QObject)
    setattr(qt, "QApplication", Mock())
    qt.QApplication.instance.return_value = app
    setattr(qt, "QAction", Mock())
    setattr(qt, "QIcon", Mock())
    setattr(qt, "Qt", SimpleNamespace())
    setattr(qt, "sip", SimpleNamespace(isdeleted=lambda _widget: False))
    utils = ModuleType("aqt.utils")
    setattr(utils, "is_mac", mac)
    for name in ("askUser", "openFolder", "shortcut", "showInfo", "showWarning"):
        setattr(utils, name, Mock())
    editor = ModuleType("aqt.editor")
    setattr(editor, "Editor", type("Editor", (), {}))
    reviewer = ModuleType("aqt.reviewer")
    setattr(reviewer, "Reviewer", type("Reviewer", (), {}))
    operations = ModuleType("aqt.operations")
    setattr(operations, "CollectionOp", Mock())
    colors = ModuleType("aqt.colors")
    setattr(aqt, "colors", colors)
    theme = ModuleType("aqt.theme")
    setattr(theme, "theme_manager", Mock())
    anki = ModuleType("anki")
    collection = ModuleType("anki.collection")
    setattr(collection, "Collection", type("Collection", (), {}))
    setattr(collection, "OpChanges", type("OpChanges", (), {}))
    consts = ModuleType("anki.consts")
    setattr(consts, "MODEL_STD", 0)
    setattr(consts, "MODEL_CLOZE", 1)
    stdmodels = ModuleType("anki.stdmodels")
    setattr(stdmodels, "get_stock_notetypes", Mock())
    modules = {
        module.__name__: module
        for module in (
            aqt,
            qt,
            utils,
            editor,
            reviewer,
            operations,
            colors,
            theme,
            anki,
            collection,
            consts,
            stdmodels,
        )
    }
    modules["anki.utils"] = utils
    return SimpleNamespace(modules=modules, hooks=hooks, app=app, menu=menu, qt=qt)
