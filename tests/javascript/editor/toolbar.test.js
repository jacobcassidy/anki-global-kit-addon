import assert from 'node:assert/strict';
import test from 'node:test';
import { JSDOM } from 'jsdom';
import { refreshEditorToolbar } from '../../../src/editor/js/toolbar.js';

test('editor toolbar settings refresh custom buttons together while preserving individual choices and native buttons', () => {
  const commands = [
    'anki_global_kit_inline_code',
    'anki_global_kit_blockquote',
    'anki_global_kit_paste_markdown_as_html',
    'anki_global_kit_syntax_highlighting',
    'anki_global_kit_syntax_language',
    'anki_global_kit_code_block_options',
  ];
  const dom = new JSDOM(
    `<body><button data-command="bold"></button>${commands.map((command) => `<button data-command="${command}"></button>`).join('')}</body>`,
  );
  const previousDocument = globalThis.document;
  const previousSettings = globalThis.ankiGlobalKitEditorSettings;
  globalThis.document = dom.window.document;
  globalThis.ankiGlobalKitEditorSettings = {
    anki_editor_toolbar_enabled: false,
    anki_editor_inline_code_button: false,
  };

  try {
    const buttons = [...document.querySelectorAll('[data-command^="anki_global_kit_"]')];
    refreshEditorToolbar();
    assert.ok(buttons.every((button) => button.style.display === 'none'));
    assert.equal(document.querySelector('[data-command="bold"]').style.display, '');

    globalThis.ankiGlobalKitEditorSettings.anki_editor_toolbar_enabled = true;
    refreshEditorToolbar();
    assert.equal(buttons[0].style.display, 'none');
    assert.ok(buttons.slice(1).every((button) => button.style.display === ''));

    globalThis.ankiGlobalKitEditorSettings.anki_editor_inline_code_button = true;
    globalThis.ankiGlobalKitEditorSettings.anki_editor_syntax_highlighting_button = false;
    refreshEditorToolbar();
    assert.equal(buttons[0].style.display, '');
    assert.ok(buttons.slice(3).every((button) => button.style.display === 'none'));
  } finally {
    globalThis.document = previousDocument;
    globalThis.ankiGlobalKitEditorSettings = previousSettings;
    dom.window.close();
  }
});
