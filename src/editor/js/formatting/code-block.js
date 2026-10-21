import { getEditorSelection } from '../helpers/selection.js';
import { editWithNativeUndo } from '../helpers/edit-transaction.js';

const CODE_SELECTOR = 'pre.agk-code-block > code';
const pending = new Map();
let requestId = 0;

function element(node) {
  return node?.nodeType === Node.ELEMENT_NODE ? node : node?.parentElement;
}

function textFromCode(node) {
  const numberedLines = node.querySelectorAll(':scope > .agk-code-line');
  return numberedLines.length
    ? [...numberedLines].map((line) => line.textContent || '').join('\n')
    : node.textContent || '';
}

function escapeText(text) {
  const node = document.createElement('span');
  node.textContent = text;
  return node.innerHTML;
}

function splitTokenNode(node) {
  if (node.nodeType === Node.TEXT_NODE) {
    return (node.nodeValue || '').split('\n').map(escapeText);
  }
  if (node.nodeType !== Node.ELEMENT_NODE) return [''];

  const lines = [''];
  for (const child of node.childNodes) {
    const childLines = splitTokenNode(child);
    lines[lines.length - 1] += childLines[0] || '';
    for (const continuation of childLines.slice(1)) lines.push(continuation);
  }

  const opening = `<${node.localName}${[...node.attributes]
    .map((attribute) => ` ${attribute.name}="${attribute.value.replaceAll('"', '&quot;')}"`)
    .join('')}>`;
  return lines.map((content) => `${opening}${content}</${node.localName}>`);
}

function tokenHtmlByLine(tokenHtml, start) {
  const container = document.createElement('div');
  container.innerHTML = tokenHtml;
  const lines = [''];
  for (const node of container.childNodes) {
    const nodeLines = splitTokenNode(node);
    lines[lines.length - 1] += nodeLines[0] || '';
    for (const continuation of nodeLines.slice(1)) lines.push(continuation);
  }
  return lines
    .map((line, index) => `<span class="agk-code-line" data-line-number="${start + index}">${line}</span>`)
    .join('');
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
  let clozeMode = target.block?.dataset.clozeMode || '';
  if (!target.block && /\{\{c\d+::/.test(target.source)) {
    clozeMode = globalThis.confirm?.(
      'Preserve Anki clozes in this code? Choose Cancel to display cloze syntax as literal code.',
    )
      ? 'active'
      : 'literal';
  }
  clozeMode ||= 'active';

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
      clozeMode,
      lineNumbers: target.block
        ? target.block.dataset.lineNumbers === 'true'
        : globalThis.ankiGlobalKitEditorSettings?.anki_editor_syntax_highlighting_line_numbers === true,
      lineStart: target.block
        ? Number.parseInt(target.block.dataset.lineStart || '1', 10)
        : globalThis.ankiGlobalKitEditorSettings?.anki_editor_syntax_highlighting_line_number_start || 1,
    })}`,
  );
  return true;
}

function applyHighlightResult(id, source, language, tokenHtml, lineNumbers, lineStart, clozeMode = 'active') {
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
      pre.dataset.lineNumbers = String(Boolean(lineNumbers));
      pre.dataset.lineStart = String(Math.max(1, Number.parseInt(lineStart, 10) || 1));
      pre.dataset.clozeMode = clozeMode === 'literal' ? 'literal' : 'active';
      const code = document.createElement('code');
      code.className = `language-${language}`;
      code.dataset.language = language;
      code.innerHTML = tokenHtmlByLine(tokenHtml, Number(pre.dataset.lineStart));
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

function openCodeBlockOptions() {
  const selection = getEditorSelection();
  if (!selection?.rangeCount) return false;
  const range = selection.getRangeAt(0);
  const code = element(range.startContainer)?.closest(CODE_SELECTOR);
  if (!code || element(range.endContainer)?.closest(CODE_SELECTOR) !== code) return false;

  const field = code.closest('anki-editable,[contenteditable="true"]');
  const pre = code.closest('pre');
  if (!field || !pre) return false;
  const fieldSnapshot = field.innerHTML;
  const dialog = document.createElement('dialog');
  dialog.className = 'agk-code-options';
  dialog.innerHTML = `
    <form method="dialog">
      <h2>Code Block Options</h2>
      <label><input name="lineNumbers" type="checkbox"> Show line numbers</label>
      <label>Starting line number <input name="lineStart" type="number" min="1" step="1"></label>
      <label>Anki cloze syntax
        <select name="clozeMode">
          <option value="active">Preserve Anki clozes</option>
          <option value="literal">Literal code</option>
        </select>
      </label>
      <div class="agk-code-options-actions">
        <button value="cancel">Cancel</button>
        <button value="apply">Apply to Block</button>
      </div>
    </form>`;
  const root = field.getRootNode();
  (root instanceof ShadowRoot ? root : document.body).append(dialog);
  const lineNumbers = dialog.querySelector('[name="lineNumbers"]');
  const lineStart = dialog.querySelector('[name="lineStart"]');
  const clozeMode = dialog.querySelector('[name="clozeMode"]');
  lineNumbers.checked = pre.dataset.lineNumbers === 'true';
  lineStart.value = String(Math.max(1, Number.parseInt(pre.dataset.lineStart || '1', 10) || 1));
  clozeMode.value = pre.dataset.clozeMode === 'literal' ? 'literal' : 'active';

  dialog.addEventListener('close', () => dialog.remove(), { once: true });
  dialog.querySelector('form').addEventListener('submit', (event) => {
    if (event.submitter?.value !== 'apply') return;
    event.preventDefault();
    const nextStart = Number(lineStart.value);
    if (!Number.isInteger(nextStart) || nextStart < 1) {
      lineStart.setCustomValidity('Enter a positive whole number.');
      lineStart.reportValidity();
      return;
    }
    lineStart.setCustomValidity('');

    if (!field.isConnected || field.innerHTML !== fieldSnapshot || !field.contains(pre)) {
      dialog.close();
      return;
    }

    const targetRange = document.createRange();
    targetRange.selectNode(pre);
    const targetSelection = {
      getRangeAt: () => targetRange,
      removeAllRanges: () => selection.removeAllRanges(),
      addRange: (nextRange) => selection.addRange(nextRange),
    };
    editWithNativeUndo(field, targetSelection, (_clone, stagedSelection, resolveNode) => {
      const clonedPre = resolveNode(pre);
      if (!clonedPre) return false;
      clonedPre.dataset.lineNumbers = String(lineNumbers.checked);
      clonedPre.dataset.lineStart = String(nextStart);
      clonedPre.dataset.clozeMode = clozeMode.value;
      clonedPre.querySelectorAll(':scope > code > .agk-code-line').forEach((line, index) => {
        line.dataset.lineNumber = String(nextStart + index);
      });
      const nextRange = document.createRange();
      nextRange.setStartAfter(clonedPre);
      nextRange.collapse(true);
      stagedSelection.removeAllRanges();
      stagedSelection.addRange(nextRange);
    });
    dialog.close();
  });
  dialog.showModal();
  return true;
}

export function installCodeBlockHighlighting() {
  const api = (globalThis.ankiGlobalKitEditor ||= {});
  api.highlightCode = requestHighlight;
  api.applyHighlightResult = applyHighlightResult;
  api.openCodeBlockOptions = openCodeBlockOptions;
}

export { applyHighlightResult, requestHighlight };
