"""Render Desktop settings icons with Anki's active theme colors."""

import weakref
from xml.etree import ElementTree

from aqt import gui_hooks
from aqt.qt import QByteArray, QLabel, QPixmap

from ..configs.constants import SHARED_ASSET_DIR
from .theme import get_theme_color


def _help_indicator_pixmap(pixel_ratio: float) -> QPixmap:
    svg = ElementTree.parse(SHARED_ASSET_DIR / "help-indicator.svg").getroot()
    foreground = get_theme_color("CANVAS")
    background = get_theme_color("FG_SUBTLE")
    pixel_size = round(16 * pixel_ratio)
    svg.set("width", str(pixel_size))
    svg.set("height", str(pixel_size))
    for element in svg.iter():
        for attribute in ("fill", "stroke"):
            if element.get(attribute) == "currentColor":
                element.set(attribute, foreground)
        if element.get("data-icon-role") == "background":
            element.set("fill", background)
    pixmap = QPixmap()
    pixmap.loadFromData(QByteArray(ElementTree.tostring(svg, encoding="utf-8")), "SVG")
    pixmap.setDevicePixelRatio(pixel_ratio)
    return pixmap


def install_help_indicator_icon(label: QLabel) -> None:
    """Set a 16px icon and refresh it on theme changes without retaining its widget."""
    label_ref = weakref.ref(label)

    def refresh() -> None:
        widget = label_ref()
        if widget is not None:
            widget.setPixmap(_help_indicator_pixmap(widget.devicePixelRatioF()))

    label.setFixedSize(16, 16)
    refresh()
    gui_hooks.theme_did_change.append(refresh)
    label.destroyed.connect(lambda *_args: gui_hooks.theme_did_change.remove(refresh))
