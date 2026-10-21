const BUTTON_SETTINGS = {
  anki_global_kit_inline_code: 'anki_editor_inline_code_button',
  anki_global_kit_blockquote: 'anki_editor_blockquote_button',
  anki_global_kit_paste_markdown_as_html: 'anki_editor_paste_markdown_as_html_button',
  anki_global_kit_syntax_highlighting: 'anki_editor_syntax_highlighting_button',
  anki_global_kit_syntax_language: 'anki_editor_syntax_highlighting_button',
  anki_global_kit_code_block_options: 'anki_editor_syntax_highlighting_button',
};

export function refreshEditorToolbar() {
  const settings = globalThis.ankiGlobalKitEditorSettings || {};
  const enabled = settings.anki_editor_toolbar_enabled !== false;

  for (const [command, setting] of Object.entries(BUTTON_SETTINGS)) {
    for (const button of document.querySelectorAll(`[data-command="${command}"]`)) {
      button.style.display = enabled && settings[setting] !== false ? '' : 'none';
    }
  }
}
