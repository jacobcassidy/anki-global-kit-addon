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
    aqt.gui_hooks = hooks
    aqt.mw = SimpleNamespace(form=SimpleNamespace(menuTools=menu))
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
    qt.QObject = QObject
    qt.QApplication = Mock()
    qt.QApplication.instance.return_value = app
    qt.QAction = Mock()
    qt.QIcon = Mock()
    qt.Qt = SimpleNamespace()
    qt.sip = SimpleNamespace(isdeleted=lambda _widget: False)
    utils = ModuleType("aqt.utils")
    utils.is_mac = mac
    for name in ("askUser", "openFolder", "shortcut", "showInfo", "showWarning"):
        setattr(utils, name, Mock())
    editor = ModuleType("aqt.editor")
    editor.Editor = type("Editor", (), {})
    reviewer = ModuleType("aqt.reviewer")
    reviewer.Reviewer = type("Reviewer", (), {})
    operations = ModuleType("aqt.operations")
    operations.CollectionOp = Mock()
    colors = ModuleType("aqt.colors")
    aqt.colors = colors
    theme = ModuleType("aqt.theme")
    theme.theme_manager = Mock()
    anki = ModuleType("anki")
    collection = ModuleType("anki.collection")
    collection.Collection = type("Collection", (), {})
    collection.OpChanges = type("OpChanges", (), {})
    consts = ModuleType("anki.consts")
    consts.MODEL_STD = 0
    consts.MODEL_CLOZE = 1
    stdmodels = ModuleType("anki.stdmodels")
    stdmodels.get_stock_notetypes = Mock()
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
    return SimpleNamespace(modules=modules, hooks=hooks, app=app, menu=menu, qt=qt)
