"""Shared settings defaults, paths, and Qt styling constants."""

import json

from aqt.utils import is_mac

from .asset_manifest import ADDON_DIR

USER_FILES_DIR = ADDON_DIR / "user_files"
SHARED_ASSET_DIR = ADDON_DIR / "shared" / "assets" / "icons"
ADDON_PACKAGE_NAME = __package__.split(".", maxsplit=1)[0]
VERSION = json.loads((ADDON_DIR / "manifest.json").read_text(encoding="utf-8"))["version"]
SECTION_SPACING = 24
MARKDOWN_BLOCK_SPACING = 12
NOTE_TYPES_ROW_PADDING = 4
NESTED_INDENT = 20
SHORTCUT_MIN_WIDTH = 80
ZERO_MARGINS = (0, 0, 0, 0)
COLOR_TRANSPARENT = "transparent"
SHORTCUT_MODIFIER_HINT = (
    "Command, Control, or Option" if is_mac else "Ctrl, Alt, or Meta"
)
DEFAULT_SETTINGS = {
    "card_input_markdown_shortcuts": True,
    "card_input_markdown_bold_shortcut": "Ctrl+B",
    "card_input_markdown_bold_shortcut_enabled": True,
    "card_input_markdown_italic_shortcut": "Ctrl+I",
    "card_input_markdown_italic_shortcut_enabled": True,
    "card_input_markdown_strikethrough_shortcut": "Ctrl+Shift+X",
    "card_input_markdown_strikethrough_shortcut_enabled": True,
    "card_input_markdown_inline_code_shortcut": "Ctrl+Shift+C",
    "card_input_markdown_inline_code_shortcut_enabled": True,
    "card_input_markdown_code_block_shortcut": "CodeBlock+C",
    "card_input_markdown_code_block_shortcut_enabled": True,
    "card_input_markdown_unordered_list_shortcut": "Ctrl+,",
    "card_input_markdown_unordered_list_shortcut_enabled": True,
    "card_input_markdown_ordered_list_shortcut": "Ctrl+.",
    "card_input_markdown_ordered_list_shortcut_enabled": True,
    "card_input_markdown_blockquote_shortcut": "Ctrl+/",
    "card_input_markdown_blockquote_shortcut_enabled": True,
    "card_input_tab_indentation": True,
    "card_input_tab_indent_increase_shortcut": "Alt+Tab",
    "card_input_tab_indent_increase_shortcut_enabled": True,
    "card_input_tab_indent_decrease_shortcut": "Meta+Tab" if is_mac else "Ctrl+Tab",
    "card_input_tab_indent_decrease_shortcut_enabled": True,
    "card_review_markdown_rendering": True,
    "card_review_syntax_highlighting": True,
    "card_toolbar_enabled": True,
    "card_toolbar_bold": True,
    "card_toolbar_italic": True,
    "card_toolbar_strikethrough": True,
    "card_toolbar_code_block": True,
    "card_toolbar_inline_code": True,
    "card_toolbar_unordered_list": True,
    "card_toolbar_ordered_list": True,
    "card_toolbar_indent_increase": True,
    "card_toolbar_indent_decrease": True,
    "card_toolbar_blockquote": True,
    "anki_editor_inline_code_shortcut_enabled": True,
    "anki_editor_inline_code_shortcut": "Ctrl+Shift+C",
    "anki_editor_tab_indentation": True,
    "anki_editor_indent_increase_shortcut": "Alt+Tab",
    "anki_editor_indent_increase_shortcut_enabled": True,
    "anki_editor_indent_decrease_shortcut": "Meta+Tab" if is_mac else "Ctrl+Tab",
    "anki_editor_indent_decrease_shortcut_enabled": True,
    "anki_editor_custom_fields_styles": True,
    "anki_editor_custom_ui_styles": True,
    "anki_editor_inline_code_button": True,
    "anki_editor_normalize_code_spaces": True,
    "anki_editor_copy_source_html": True,
    "anki_editor_paste_cleanup": True,
}
