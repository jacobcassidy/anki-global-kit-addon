import { flattenCodeLines } from '../../../shared/js/syntax-highlighting/code-lines.js';

// Resolve both text and element-boundary carets, including Anki's shadow fields.
export function getFieldInputSelection() {
  let active = document.activeElement;
  let focusedSelection = null;
  while (active?.shadowRoot) {
    const root = active.shadowRoot;
    const selection = root.getSelection?.();
    if (selection?.rangeCount && selection.focusNode) focusedSelection = selection;
    active = root.activeElement;
  }
  if (focusedSelection) return focusedSelection;
  const selection = window.getSelection();
  if (!selection?.rangeCount || !selection.focusNode) return null;
  const node = selection.focusNode;
  const element = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
  if (element?.closest('anki-editable,[contenteditable="true"]')) return selection;
  return null;
}

// Toolbar activation can move focus outside the field's shadow root. Remember
// the field itself so its native selection remains reachable from the button.
// The bundle is evaluated again on note loads and settings saves. Keep the
// listener and remembered field together across those module instances.
const STATE_KEY = Symbol.for('ankiGlobalKitEditorSelection');
function selectionState() {
  return (document[STATE_KEY] ||= { installed: false, lastEditorField: null });
}

export function installSelectionTracking() {
  const state = selectionState();
  if (state.installed) return;
  state.installed = true;
  document.addEventListener(
    'focusin',
    (event) => {
      const field = event.composedPath().find((node) => node?.matches?.('anki-editable'));
      if (field) state.lastEditorField = field;
    },
    true,
  );
}

export function getEditorSelection() {
  const current = getFieldInputSelection();
  if (current?.rangeCount) return current;
  const { lastEditorField } = selectionState();
  if (!lastEditorField?.isConnected) return null;
  const selection = lastEditorField.getRootNode().getSelection?.();
  if (!selection?.rangeCount) return null;
  const range = selection.getRangeAt(0);
  return lastEditorField.contains(range.startContainer) && lastEditorField.contains(range.endContainer)
    ? selection
    : null;
}

function textFromFragment(node, parts) {
  if (node.nodeType === Node.TEXT_NODE) {
    if (node.nodeValue) parts.push(node.nodeValue);

    return;
  }

  if (node.nodeType === Node.ELEMENT_NODE) {
    if (node.matches('.code-block__header,.code-line__number,[data-code-placeholder]')) return;

    if (node.nodeName === 'BR') {
      parts.push('\n');

      return;
    }
  }

  if ([...(node.children || [])].some((child) => child.classList.contains('code-line'))) {
    parts.push(flattenCodeLines(node).textContent);
  } else {
    for (const child of node.childNodes) textFromFragment(child, parts);
  }

  // Keep structural block separators distinct from newlines in selected code.
  if (/^(DIV|P|LI|BLOCKQUOTE|PRE|H[1-6])$/.test(node.nodeName)) parts.push(null);
}

export function getEditorRangeText(range) {
  const parts = [];

  textFromFragment(range.cloneContents(), parts);

  if (parts.at(-1) === null) parts.pop();

  return parts.map((part) => part ?? '\n').join('');
}
