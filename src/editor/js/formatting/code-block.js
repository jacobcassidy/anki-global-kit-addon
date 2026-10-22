import { getEditorRangeText, getEditorSelection } from '../helpers/selection.js';
import { editWithNativeUndo } from '../helpers/edit-transaction.js';
import { getSyntaxLanguage } from '../../../shared/js/syntax-highlighting/languages.js';
import { enhanceHighlightHtml } from '../../../shared/js/syntax-highlighting/classification/markup.js';

import {
  textFromCode,
  tokenHtmlByLine,
  flattenCodeLines,
  preserveClozeMode,
} from '../../../shared/js/syntax-highlighting/code-lines.js';
import { decorateCodeBlock } from '../../../shared/js/syntax-highlighting/code-block-controls.js';
import { installCodeBlockEditing } from './code-block-editing.js';

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
      decorateCodeBlock(pre, {
        optionsButton: true,
        copyButton: target.block
          ? target.block.dataset.copyButton !== 'false'
          : globalThis.ankiGlobalKitEditorSettings?.anki_editor_syntax_highlighting_copy_button !== false,
      });
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
      clonedCode.innerHTML = tokenHtmlByLine(flattenCodeLines(clonedCode).innerHTML, options.lineStart);
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
  installCodeBlockEditing();

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
