const BUTTON_SETTINGS = {
  anki_global_kit_inline_code: { setting: 'anki_editor_inline_code_button', group: 'inline-code' },
  anki_global_kit_blockquote: { setting: 'anki_editor_blockquote_button', group: 'formatting' },
  anki_global_kit_paste_markdown_as_html: {
    setting: 'anki_editor_paste_markdown_as_html_button',
    group: 'formatting',
  },
  anki_global_kit_syntax_highlighting: {
    setting: 'anki_editor_syntax_highlighting_button',
    group: 'syntax-highlighting',
  },
  anki_global_kit_syntax_language: {
    setting: 'anki_editor_syntax_highlighting_button',
    group: 'syntax-highlighting',
  },
  anki_global_kit_code_block_options: {
    setting: 'anki_editor_syntax_highlighting_button',
    group: 'syntax-highlighting',
  },
};

export function refreshEditorToolbar() {
  const settings = globalThis.ankiGlobalKitEditorSettings || {};
  const enabled = settings.anki_editor_toolbar_enabled !== false;
  const selector = Object.keys(BUTTON_SETTINGS)
    .map((command) => `[data-command="${command}"]`)
    .join(',');

  let previousGroup;

  for (const button of document.querySelectorAll(selector)) {
    const { setting, group } = BUTTON_SETTINGS[button.dataset.command];
    const visible = enabled && settings[setting] !== false;

    button.style.display = visible ? '' : 'none';
    button.classList.toggle(
      'anki-global-kit-toolbar-group-start',
      visible && previousGroup !== undefined && previousGroup !== group,
    );

    if (visible) previousGroup = group;
  }
}
