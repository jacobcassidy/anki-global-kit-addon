import { getEditorRangeText, getEditorSelection } from '../helpers/selection.js';
import { editWithNativeUndo } from '../helpers/edit-transaction.js';
import { getSyntaxLanguage } from '../../../shared/js/syntax-highlighting/languages.js';
import { enhanceHighlightHtml } from '../../../shared/js/syntax-highlighting/classification/markup.js';

const CODE_SELECTOR = 'pre.global-kit-code-block > code';
const OPTIONS_MESSAGE_PREFIX = 'anki-global-kit:code-block-options:';
const pending = new Map();
const pendingOptions = new Map();
let requestId = 0;
let explicitLanguage = null;
let rememberedLanguage = null;

function element(node) {
  return node?.nodeType === Node.ELEMENT_NODE ? node : node?.parentElement;
}

function textFromCode(node) {
  const numberedLines = node.querySelectorAll(':scope > .code-line');
  return numberedLines.length
    ? [...numberedLines]
        .map((line) => line.querySelector(':scope > .code-line__content')?.textContent ?? line.textContent ?? '')
        .join('\n')
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
    .map(
      (line, index) =>
        `<span class="code-line"><span class="code-line__number">${start + index}</span><span class="code-line__content">${line}</span></span>`,
    )
    .join('');
}

function preserveClozeMode(code, mode) {
  for (const guard of code.querySelectorAll('[data-global-kit-literal-brace]')) {
    guard.replaceWith(...guard.childNodes);
  }

  code.normalize();

  if (mode !== 'literal') return;

  // Entity escapes become ordinary braces when browser HTML is serialized.
  // Splitting each pair with a span keeps literal clozes inert after saving.
  const owner = code.ownerDocument;
  const walker = owner.createTreeWalker(code, 4);
  const leaves = [];
  let leaf;

  while ((leaf = walker.nextNode())) {
    if (/\{\{|\}\}/.test(leaf.data)) leaves.push(leaf);
  }

  for (const node of leaves) {
    const fragment = owner.createDocumentFragment();

    for (const part of node.data.split(/(\{\{|\}\})/)) {
      if (part === '{{' || part === '}}') {
        const guard = owner.createElement('span');

        guard.dataset.globalKitLiteralBrace = '';
        guard.textContent = part[0];
        fragment.append(guard, owner.createTextNode(part[1]));
      } else {
        fragment.append(owner.createTextNode(part));
      }
    }

    node.replaceWith(fragment);
  }
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
      language: block.dataset.language,
      block,
    };
  }

  if (intersectedCode.length) return null;

  if (!range.collapsed) {
    const source = getEditorRangeText(range);
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

  const enabled = globalThis.ankiGlobalKitEditorSettings?.anki_editor_syntax_highlighting_languages || [];
  if (explicitLanguage && !enabled.includes(explicitLanguage)) explicitLanguage = null;
  const topicText = currentTopicText();
  const topicLanguage = getSyntaxLanguage(topicText);
  const automaticLanguage =
    target.language ||
    (enabled.includes(topicLanguage) ? topicLanguage : null) ||
    (enabled.includes(rememberedLanguage) ? rememberedLanguage : null) ||
    language;
  const selectedLanguage = explicitLanguage || automaticLanguage;

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
      language: selectedLanguage || 'python',
      explicitLanguage: Boolean(explicitLanguage),
      automaticLanguage: automaticLanguage || 'python',
      topicLanguage: topicLanguage || '',
      topicText,
      existingLanguage: target.language || '',
      clozeMode,
      lineNumbers: target.block
        ? target.block.dataset.lineNumbers === 'true'
        : globalThis.ankiGlobalKitEditorSettings?.anki_editor_syntax_highlighting_line_numbers === true,
      lineStart: target.block ? Number.parseInt(target.block.dataset.lineStart || '1', 10) : 1,
    })}`,
  );
  return true;
}

function currentTopicText() {
  const fields = globalThis.require?.('anki/NoteEditor')?.instances?.[0]?.fields;
  const topic = fields?.find((field) =>
    [field.name, field.fieldName, field.field?.name].some(
      (name) => typeof name === 'string' && name.trim().toLowerCase() === 'topic',
    ),
  );
  let html;
  topic?.editingArea?.content?.subscribe?.((value) => {
    html = value;
  })?.();
  if (typeof html !== 'string') return '';
  const content = document.createElement('template');
  content.innerHTML = html;
  return content.content.textContent || '';
}

function setExplicitLanguage(language) {
  explicitLanguage = typeof language === 'string' ? language : null;
}

function setLanguageContext(explicit, remembered) {
  explicitLanguage = typeof explicit === 'string' ? explicit : null;
  rememberedLanguage = typeof remembered === 'string' ? remembered : null;
}

function applyHighlightResult(id, source, language, tokenHtml, lineNumbers, lineStart, clozeMode = 'active') {
  const target = pending.get(String(id));
  pending.delete(String(id));
  if (!target || !target.field.isConnected || target.field.innerHTML !== target.fieldSnapshot) {
    reportApplyResult(id, language, false);
    return false;
  }
  if (target.block && textFromCode(target.block.querySelector('code')) !== target.source) {
    reportApplyResult(id, language, false);
    return false;
  }

  const enrichedHtml = enhanceHighlightHtml(tokenHtml, language);

  const applied = Boolean(
    editWithNativeUndo(target.field, target.selection, (field, selection) => {
      const replacement = selection.getRangeAt(0);
      const pre = document.createElement('pre');
      pre.className = 'global-kit-code-block';
      pre.dataset.language = language;
      pre.dataset.lineNumbers = String(Boolean(lineNumbers));
      pre.dataset.lineStart = String(Math.max(1, Number.parseInt(lineStart, 10) || 1));
      pre.dataset.clozeMode = clozeMode === 'literal' ? 'literal' : 'active';
      const code = document.createElement('code');
      code.innerHTML = tokenHtmlByLine(enrichedHtml, Number(pre.dataset.lineStart));
      preserveClozeMode(code, pre.dataset.clozeMode);
      pre.append(code);
      replacement.deleteContents();
      replacement.insertNode(pre);
      replacement.setStartAfter(pre);
      replacement.collapse(true);
      selection.removeAllRanges();
      selection.addRange(replacement);
    }),
  );
  reportApplyResult(id, language, applied);
  return applied;
}

function reportApplyResult(id, language, applied) {
  globalThis.pycmd?.(`anki-global-kit:syntax-highlight-applied:${JSON.stringify({ id, language, applied })}`);
}

function cancelHighlightResult(id) {
  pending.delete(String(id));
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
  const blockIndex = [...field.querySelectorAll('pre.global-kit-code-block')].indexOf(pre);
  const id = String(++requestId);
  pendingOptions.set(id, { field, fieldSnapshot, blockIndex, selection });
  globalThis.pycmd?.(
    `${OPTIONS_MESSAGE_PREFIX}${JSON.stringify({
      id,
      lineNumbers: pre.dataset.lineNumbers === 'true',
      lineStart: Math.max(1, Number.parseInt(pre.dataset.lineStart || '1', 10) || 1),
      clozeMode: pre.dataset.clozeMode === 'literal' ? 'literal' : 'active',
    })}`,
  );
  return true;
}

function applyCodeBlockOptions(id, options) {
  const target = pendingOptions.get(String(id));
  pendingOptions.delete(String(id));

  if (!target || !Number.isInteger(options.lineStart) || options.lineStart < 1) return false;
  if (options.clozeMode !== 'active' && options.clozeMode !== 'literal') return false;

  const { field, fieldSnapshot, blockIndex, selection } = target;

  if (!field.isConnected || field.innerHTML !== fieldSnapshot) return false;

  // Anki may recreate unchanged field nodes while the native dialog has focus.
  const currentPre = field.querySelectorAll('pre.global-kit-code-block')[blockIndex];

  if (!currentPre) return false;

  const targetRange = document.createRange();
  targetRange.selectNode(currentPre);
  const targetSelection = {
    getRangeAt: () => targetRange,
    removeAllRanges: () => selection.removeAllRanges(),
    addRange: (nextRange) => selection.addRange(nextRange),
  };
  return Boolean(
    editWithNativeUndo(field, targetSelection, (_clone, stagedSelection, resolveNode) => {
      const clonedPre = resolveNode(currentPre);
      if (!clonedPre) return false;
      clonedPre.dataset.lineNumbers = String(options.lineNumbers === true);
      clonedPre.dataset.lineStart = String(options.lineStart);
      clonedPre.dataset.clozeMode = options.clozeMode;
      const clonedCode = clonedPre.querySelector('code');

      // Markdown conversion creates highlighted blocks without line wrappers.
      if (!clonedCode.querySelector(':scope > .code-line')) {
        clonedCode.innerHTML = tokenHtmlByLine(clonedCode.innerHTML, options.lineStart);
      }

      preserveClozeMode(clonedCode, options.clozeMode);
      clonedCode.querySelectorAll(':scope > .code-line').forEach((line, index) => {
        const lineNumber = String(options.lineStart + index);
        const numberElement = line.querySelector(':scope > .code-line__number');
        const contentElement = line.querySelector(':scope > .code-line__content');

        if (!contentElement) {
          const nextContent = line.ownerDocument.createElement('span');
          nextContent.className = 'code-line__content';

          while (line.firstChild) nextContent.append(line.firstChild);

          line.append(nextContent);
        }

        if (numberElement) {
          numberElement.textContent = lineNumber;
        } else {
          const nextNumber = line.ownerDocument.createElement('span');
          nextNumber.className = 'code-line__number';
          nextNumber.textContent = lineNumber;
          line.prepend(nextNumber);
        }
      });
      const nextRange = document.createRange();
      nextRange.setStartAfter(clonedPre);
      nextRange.collapse(true);
      stagedSelection.removeAllRanges();
      stagedSelection.addRange(nextRange);
    }),
  );
}

function cancelCodeBlockOptions(id) {
  pendingOptions.delete(String(id));
}

export function installCodeBlockHighlighting() {
  const api = (globalThis.ankiGlobalKitEditor ||= {});
  api.highlightCode = requestHighlight;
  api.applyHighlightResult = applyHighlightResult;
  api.openCodeBlockOptions = openCodeBlockOptions;
  api.applyCodeBlockOptions = applyCodeBlockOptions;
  api.cancelCodeBlockOptions = cancelCodeBlockOptions;
  api.setExplicitLanguage = setExplicitLanguage;
  api.setLanguageContext = setLanguageContext;
  api.cancelHighlightResult = cancelHighlightResult;
}

export { applyHighlightResult, requestHighlight };
