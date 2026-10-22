import { getEditorSelection } from './helpers/selection.js';

const BUTTON_SETTINGS = {
  anki_global_kit_inline_code: 'anki_editor_inline_code_button',
  anki_global_kit_blockquote: 'anki_editor_blockquote_button',
  anki_global_kit_paste_markdown_as_html: 'anki_editor_paste_markdown_as_html_button',
  anki_global_kit_syntax_highlighting: 'anki_editor_syntax_highlighting_button',
  anki_global_kit_syntax_language: 'anki_editor_syntax_highlighting_button',
  anki_global_kit_code_block_options: 'anki_editor_syntax_highlighting_button',
};

function refreshCodeBlockOptions() {
  const button = document.querySelector('[data-command="anki_global_kit_code_block_options"]');

  if (!button) return;

  const selection = getEditorSelection();
  const range = selection?.rangeCount ? selection.getRangeAt(0) : null;
  const node = range?.commonAncestorContainer;
  const element = node?.nodeType === Node.ELEMENT_NODE ? node : node?.parentElement;
  const codeBlock = element?.closest('pre');

  button.disabled = !codeBlock;
  button.style.color = codeBlock ? '' : 'var(--fg-disabled)';
}

export function refreshEditorToolbar() {
  const settings = globalThis.ankiGlobalKitEditorSettings || {};
  const enabled = settings.anki_editor_toolbar_enabled !== false;

  for (const [command, setting] of Object.entries(BUTTON_SETTINGS)) {
    for (const button of document.querySelectorAll(`[data-command="${command}"]`)) {
      button.style.display = enabled && settings[setting] !== false ? '' : 'none';
    }
  }

  for (const group of document.querySelectorAll('[data-anki-global-kit-toolbar-group]')) {
    const buttons = [...group.querySelectorAll('[data-command]')];
    const visible = buttons.filter((button) => button.style.display !== 'none');
    const radius = 'var(--anki-global-kit-toolbar-group-radius, 5px)';

    group.style.display = visible.length ? 'inline-flex' : 'none';

    for (const button of buttons) {
      button.style.setProperty('--border-left-radius', button === visible[0] ? radius : '0');
      button.style.setProperty('--border-right-radius', button === visible.at(-1) ? radius : '0');
    }
  }

  refreshCodeBlockOptions();
}

const TOOLBAR_STATE_KEY = Symbol.for('ankiGlobalKitEditorToolbar');
const toolbarState = (document[TOOLBAR_STATE_KEY] ||= { listenersInstalled: false });

if (!toolbarState.listenersInstalled) {
  toolbarState.listenersInstalled = true;
  document.addEventListener('selectionchange', refreshCodeBlockOptions);
  document.addEventListener('focusin', refreshCodeBlockOptions, true);
}
