import { recoverEditorShortcut, recoverIndentationShortcut } from '../../shared/js/shortcut-policy.js';

const defaults = {
  anki_editor_inline_code_shortcut_enabled: true,
  anki_editor_inline_code_shortcut: 'Ctrl+Shift+C',
  anki_editor_blockquote_shortcut: 'Ctrl+/',
  anki_editor_convert_markdown_shortcut: 'Alt+M',
  anki_editor_exit_code_block_shortcut: 'Alt+Enter',
  anki_editor_syntax_highlighting_shortcut: 'Alt+S',
  anki_editor_tab_indentation: true,
  anki_editor_indent_increase_shortcut: 'Ctrl+Alt+.',
  anki_editor_indent_increase_shortcut_enabled: true,
  anki_editor_indent_decrease_shortcut: 'Ctrl+Alt+,',
  anki_editor_indent_decrease_shortcut_enabled: true,
  anki_editor_inline_code_button: true,
  anki_editor_normalize_code_spaces: true,
  anki_editor_copy_source_html: true,
};

export function getEditorSettings() {
  const settings = { ...defaults, ...globalThis.ankiGlobalKitEditorSettings };

  for (const name of Object.keys(defaults).filter((name) => name.endsWith('_shortcut'))) {
    settings[name] = recoverEditorShortcut(settings[name], defaults[name]);

    if (name.startsWith('anki_editor_indent_')) {
      settings[name] = recoverIndentationShortcut(settings[name], defaults[name]);
    }
  }

  return settings;
}
