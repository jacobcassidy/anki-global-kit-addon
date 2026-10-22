const BUTTON_SETTINGS = {
  anki_global_kit_inline_code: 'anki_editor_inline_code_button',
  anki_global_kit_blockquote: 'anki_editor_blockquote_button',
  anki_global_kit_paste_markdown_as_html: 'anki_editor_paste_markdown_as_html_button',
  anki_global_kit_syntax_highlighting: 'anki_editor_syntax_highlighting_button',
  anki_global_kit_syntax_language: 'anki_editor_syntax_highlighting_button',
};

const TOOLBAR_STATE_KEY = Symbol.for('ankiGlobalKitEditorToolbar');

function installToolbarObserver() {
  if (typeof document === 'undefined' || typeof MutationObserver === 'undefined') return;

  const toolbarState = (document[TOOLBAR_STATE_KEY] ||= { listenersInstalled: false });

  if (toolbarState.listenersInstalled) return;

  toolbarState.listenersInstalled = true;
  new MutationObserver((mutations) => {
    if (mutations.some(({ attributeName }) => attributeName === 'disabled')) {
      for (const button of document.querySelectorAll('[data-command="anki_global_kit_syntax_language"]')) {
        if (button.disabled) button.disabled = false;
      }
    }
  }).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['disabled'],
    subtree: true,
  });
}

export function refreshEditorToolbar() {
  installToolbarObserver();

  const settings = globalThis.ankiGlobalKitEditorSettings || {};
  const enabled = settings.anki_editor_toolbar_enabled !== false;

  for (const [command, setting] of Object.entries(BUTTON_SETTINGS)) {
    for (const button of document.querySelectorAll(`[data-command="${command}"]`)) {
      button.style.display = enabled && settings[setting] !== false ? '' : 'none';

      if (command === 'anki_global_kit_syntax_language') button.disabled = false;
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
}
