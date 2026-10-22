import assert from 'node:assert/strict';
import test from 'node:test';
import { execFileSync } from 'node:child_process';
import { JSDOM } from 'jsdom';
import { refreshEditorToolbar } from '../../../src/editor/js/toolbar.js';

test('editor toolbar settings refresh custom buttons together while preserving individual choices and native buttons', () => {
  const commands = [
    'anki_global_kit_inline_code',
    'anki_global_kit_blockquote',
    'anki_global_kit_paste_markdown_as_html',
    'anki_global_kit_syntax_highlighting',
    'anki_global_kit_syntax_language',
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

test('rendered toolbar groups retain gaps and rounded edges without the optional UI stylesheet', () => {
  const html = execFileSync(
    'python3',
    [
      '-c',
      `
from unittest.mock import Mock
from tests.support.anki_stubs import load_editor_integration, load_settings_services
integration = load_editor_integration(load_settings_services().config.get_editor_settings())
editor = Mock()
editor.addButton.side_effect = lambda **kwargs: f'<button class="anki-addon-button linkb" data-command="{kwargs["cmd"]}"></button>'
buttons = []
integration._add_button(buttons, editor)
print(''.join(buttons))
`,
    ],
    { cwd: new URL('../../../', import.meta.url), encoding: 'utf8' },
  );
  const dom = new JSDOM(
    `<body><button data-command="bold"></button><div class="button-group btn-group"><div style="display: contents; --border-left-radius: 5px; --border-right-radius: 5px;">${html}</div></div></body>`,
  );
  const previousDocument = globalThis.document;
  const previousSettings = globalThis.ankiGlobalKitEditorSettings;

  globalThis.document = dom.window.document;

  try {
    const settings = {};

    globalThis.ankiGlobalKitEditorSettings = settings;

    const toolbar = document.querySelector('[data-anki-global-kit-toolbar]');
    const radius = 'var(--anki-global-kit-toolbar-group-radius, 5px)';

    assert.equal(toolbar.style.columnGap, 'var(--anki-global-kit-toolbar-group-gap, 0.3rem)');

    const checkGroups = (expected) => {
      refreshEditorToolbar();
      const groups = [...toolbar.querySelectorAll('[data-anki-global-kit-toolbar-group]')];
      const visibleGroups = groups.filter((group) => group.style.display !== 'none');

      assert.deepEqual(
        visibleGroups.map((group) => group.dataset.ankiGlobalKitToolbarGroup),
        expected,
      );

      for (const group of visibleGroups) {
        const visible = [...group.querySelectorAll('button')].filter((button) => button.style.display !== 'none');

        for (const button of visible) {
          assert.equal(
            button.style.borderRadius,
            'var(--border-left-radius) var(--border-right-radius) var(--border-right-radius) var(--border-left-radius)',
          );
          assert.equal(button.style.getPropertyValue('--border-left-radius'), button === visible[0] ? radius : '0');
          assert.equal(
            button.style.getPropertyValue('--border-right-radius'),
            button === visible.at(-1) ? radius : '0',
          );
        }
      }

      assert.equal(document.querySelector('[data-command="bold"]').className, '');
    };

    checkGroups(['syntax-highlighting', 'inline-code', 'convert-markdown', 'blockquote']);
    settings.anki_editor_blockquote_button = false;
    checkGroups(['syntax-highlighting', 'inline-code', 'convert-markdown']);
    settings.anki_editor_paste_markdown_as_html_button = false;
    checkGroups(['syntax-highlighting', 'inline-code']);
    settings.anki_editor_syntax_highlighting_button = false;
    checkGroups(['inline-code']);
    settings.anki_editor_blockquote_button = true;
    checkGroups(['inline-code', 'blockquote']);
    settings.anki_editor_inline_code_button = false;
    checkGroups(['blockquote']);
    settings.anki_editor_blockquote_button = false;
    checkGroups([]);
    settings.anki_editor_toolbar_enabled = false;
    checkGroups([]);
    settings.anki_editor_toolbar_enabled = true;
    settings.anki_editor_inline_code_button = true;
    settings.anki_editor_syntax_highlighting_button = true;
    checkGroups(['syntax-highlighting', 'inline-code']);
  } finally {
    globalThis.document = previousDocument;
    globalThis.ankiGlobalKitEditorSettings = previousSettings;
    dom.window.close();
  }
});
