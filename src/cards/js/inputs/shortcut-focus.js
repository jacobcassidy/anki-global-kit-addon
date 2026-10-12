import { hasMacCommandCommaHandler } from './markdown-shortcuts.js';

/** Refresh Desktop shortcut ownership even when a textarea emits no new focus event. */
export function reportQuestionShortcutFocus(markdownEnabled, shortcuts) {
  if (document.activeElement?.closest?.('.card-formatting-toolbar')) {
    globalThis.pycmd('anki-global-kit:question-toolbar-focus');
  } else if (document.activeElement?.matches('.question-input')) {
    const handled = hasMacCommandCommaHandler(markdownEnabled, shortcuts);
    globalThis.pycmd(`anki-global-kit:question-input-focus:${handled ? 'handled' : 'unhandled'}`);
  } else {
    globalThis.pycmd('anki-global-kit:question-input-blur');
  }
}
