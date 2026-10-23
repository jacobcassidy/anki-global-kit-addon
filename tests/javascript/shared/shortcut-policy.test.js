import assert from 'node:assert/strict';
import test from 'node:test';
import { getEditorSettings } from '../../../src/editor/js/settings.js';
import { recoverIndentationShortcut } from '../../../src/shared/js/shortcut-policy.js';

test('raw editor settings recover unsupported aliases and indentation bindings without saving', () => {
  const saved = {
    anki_editor_inline_code_shortcut: 'CodeBlock+C',
    anki_editor_convert_markdown_shortcut: 'CodeBlock+M',
    anki_editor_indent_increase_shortcut: 'Alt+Tab',
    anki_editor_indent_decrease_shortcut: 'Meta+Shift+Backtab',
    anki_editor_tab_indentation: false,
    anki_editor_indent_increase_shortcut_enabled: false,
  };

  globalThis.ankiGlobalKitEditorSettings = { ...saved };

  try {
    const current = getEditorSettings();

    assert.equal(current.anki_editor_inline_code_shortcut, 'Ctrl+Shift+C');
    assert.equal(current.anki_editor_convert_markdown_shortcut, 'Alt+M');
    assert.equal(current.anki_editor_indent_increase_shortcut, 'Ctrl+Alt+.');
    assert.equal(current.anki_editor_indent_decrease_shortcut, 'Ctrl+Alt+,');
    assert.equal(current.anki_editor_tab_indentation, false);
    assert.equal(current.anki_editor_indent_increase_shortcut_enabled, false);
    assert.deepEqual(globalThis.ankiGlobalKitEditorSettings, saved);
    assert.equal(recoverIndentationShortcut('Alt+]', 'Ctrl+Alt+.'), 'Alt+]');
    assert.equal(recoverIndentationShortcut('', 'Ctrl+Alt+.'), '');
  } finally {
    delete globalThis.ankiGlobalKitEditorSettings;
  }
});

test('card runtime settings recover Tab bindings and preserve the card CodeBlock alias', async () => {
  globalThis.ankiGlobalKitSettings = {
    card_input_tab_indent_increase_shortcut: 'Alt+Tab',
    card_input_tab_indent_decrease_shortcut: 'Control+Backtab',
    card_input_tab_indent_decrease_shortcut_enabled: false,
  };

  try {
    const { settings } = await import('../../../src/cards/js/runtime/settings.js');

    assert.equal(settings.cardInputTabShortcutsMap.increase, 'Ctrl+Alt+.');
    assert.equal(settings.cardInputTabShortcutsMap.decrease, '');
    assert.equal(settings.cardInputMarkdownShortcutsMap.codeBlock, 'CodeBlock+C');
  } finally {
    delete globalThis.ankiGlobalKitSettings;
  }
});
