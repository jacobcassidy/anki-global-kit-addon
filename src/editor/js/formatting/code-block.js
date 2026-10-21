import { getEditorSelection } from '../helpers/selection.js';
import { editWithNativeUndo } from '../helpers/edit-transaction.js';

const CODE_SELECTOR = 'pre.agk-code-block > code';
const pending = new Map();
let requestId = 0;

function element(node) {
  return node?.nodeType === Node.ELEMENT_NODE ? node : node?.parentElement;
}

function textFromCode(node) {
  return node.textContent || '';
}

function sourceFromFragment(node) {
  if (node.nodeType === Node.TEXT_NODE) return node.nodeValue || '';
  if (node.nodeName === 'BR') return '\n';
  const children = [...node.childNodes].map(sourceFromFragment);
  const content = children.join('');
  return node !== node.ownerDocument && /^(DIV|P|LI|BLOCKQUOTE)$/.test(node.nodeName) ? `${content}\n` : content;
}

function readSelectionTarget(clipboardText) {
  const selection = getEditorSelection();
  if (!selection?.rangeCount) return null;
  const range = selection.getRangeAt(0);
  const start = element(range.startContainer);
  const end = element(range.endContainer);
  const field = start?.closest('anki-editable,[contenteditable="true"]');
  if (!field || !field.contains(range.endContainer) || field.closest('.cm-editor')) return null;

  const code = start?.closest(CODE_SELECTOR);
  const endCode = end?.closest(CODE_SELECTOR);
  const intersectedCode = [...field.querySelectorAll(CODE_SELECTOR)].filter((item) => range.intersectsNode(item));
  if (code || endCode) {
    if (!code || code !== endCode) return null;
    const block = code.closest('pre');
    const source = textFromCode(code);
    const targetRange = document.createRange();
    targetRange.selectNode(block);
    return {
      field,
      liveSelection: selection,
      range: targetRange,
      source,
      language: code.dataset.language,
      block,
    };
  }

  if (intersectedCode.length) return null;

  if (!range.collapsed) {
    const fragment = range.cloneContents();
    const source = sourceFromFragment(fragment).replace(/\n$/, '');
    return source ? { field, liveSelection: selection, range: range.cloneRange(), source } : null;
  }

  return clipboardText ? { field, liveSelection: selection, range: range.cloneRange(), source: clipboardText } : null;
}

function requestHighlight(clipboardText, language) {
  const target = readSelectionTarget(clipboardText);
  if (!target || !target.source) return false;

  const id = String(++requestId);
  target.selection = {
    getRangeAt: () => target.range,
    removeAllRanges: () => target.liveSelection.removeAllRanges(),
    addRange: (range) => target.liveSelection.addRange(range),
  };
  target.fieldSnapshot = target.field.innerHTML;
  pending.set(id, target);
  globalThis.pycmd?.(
    `anki-global-kit:syntax-highlight:${JSON.stringify({
      id,
      source: target.source,
      language: target.language || language || 'python',
    })}`,
  );
  return true;
}

function applyHighlightResult(id, source, language, tokenHtml) {
  const target = pending.get(String(id));
  pending.delete(String(id));
  if (!target || !target.field.isConnected || target.field.innerHTML !== target.fieldSnapshot) return false;
  if (target.block && textFromCode(target.block.querySelector('code')) !== target.source) return false;

  return Boolean(
    editWithNativeUndo(target.field, target.selection, (field, selection) => {
      const replacement = selection.getRangeAt(0);
      const pre = document.createElement('pre');
      pre.className = 'agk-code-block';
      pre.dataset.language = language;
      const code = document.createElement('code');
      code.className = `language-${language}`;
      code.dataset.language = language;
      code.innerHTML = tokenHtml;
      pre.append(code);
      replacement.deleteContents();
      replacement.insertNode(pre);
      replacement.setStartAfter(pre);
      replacement.collapse(true);
      selection.removeAllRanges();
      selection.addRange(replacement);
    }),
  );
}

export function installCodeBlockHighlighting() {
  const api = (globalThis.ankiGlobalKitEditor ||= {});
  api.highlightCode = requestHighlight;
  api.applyHighlightResult = applyHighlightResult;
}

export { applyHighlightResult, requestHighlight };
