import { getEditorSelection, getFieldInputSelection } from '../helpers/selection.js';
import { getEditorSettings } from '../settings.js';

export function normalizeSpaceBeforeCode(code) {
  let previous = code.previousSibling;
  while (previous?.nodeType === Node.TEXT_NODE && !previous.length) previous = previous.previousSibling;
  if (previous?.nodeType === Node.TEXT_NODE && previous.data.endsWith('\u00a0')) {
    const selection = getEditorSelection() || getFieldInputSelection();
    const ranges = Array.from({ length: selection?.rangeCount || 0 }, (_, index) => {
      const range = selection.getRangeAt(index);
      return {
        range,
        start: range.startContainer,
        startOffset: range.startOffset,
        end: range.endContainer,
        endOffset: range.endOffset,
      };
    });
    previous.replaceData(previous.length - 1, 1, ' ');
    // Replacing the space can pull a caret just after it back before it.
    for (const saved of ranges) {
      saved.range.setStart(saved.start, saved.startOffset);
      saved.range.setEnd(saved.end, saved.endOffset);
    }
    return true;
  }
  return false;
}

// Catch typing before existing code, including code not created by our shortcut.
export function installCodeSpaceNormalization() {
  if (installCodeSpaceNormalization.installed) return;
  installCodeSpaceNormalization.installed = true;
  document.addEventListener(
    'input',
    (event) => {
      if (!getEditorSettings().anki_editor_normalize_code_spaces) return;
      const field = event.composedPath().find((node) => node?.matches?.('anki-editable, [contenteditable="true"]'));
      if (!field) return;
      const normalize = () => {
        let changed = false;
        for (const code of field.querySelectorAll('code')) {
          if (normalizeSpaceBeforeCode(code)) changed = true;
        }
        return changed;
      };
      normalize(); // Before Anki serializes the field.
      queueMicrotask(() => {
        if (field.isConnected && normalize()) {
          field.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
        }
      });
    },
    true,
  );
}
