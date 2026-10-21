import { markdownToHtml } from '../../../shared/js/markdown/render.js';
import { getSyntaxLanguage } from '../../../shared/js/syntax-highlighting/languages.js';
import { getEditorSelection } from '../helpers/selection.js';
import { editWithNativeUndo } from '../helpers/edit-transaction.js';
import { enhanceHighlightHtml } from '../../../shared/js/syntax-highlighting/classification/markup.js';
import { createClassificationBudget } from '../../../shared/js/syntax-highlighting/classification/index.js';

const MESSAGE_PREFIX = 'anki-global-kit:markdown-highlight:';
const pending = new Map();
let requestId = 0;

function element(node) {
  return node?.nodeType === Node.ELEMENT_NODE ? node : node?.parentElement;
}

function getStoreValue(store) {
  let value;
  const unsubscribe = store?.subscribe?.((nextValue) => {
    value = nextValue;
  });
  unsubscribe?.();
  return value;
}

function getTopicText() {
  const fields = globalThis.require?.('anki/NoteEditor')?.instances?.[0]?.fields;
  const topicField = fields?.find((field) =>
    [field.name, field.fieldName, field.field?.name].some(
      (name) => typeof name === 'string' && name.trim().toLowerCase() === 'topic',
    ),
  );
  const html = getStoreValue(topicField?.editingArea?.content);
  if (typeof html !== 'string' || !html) return '';
  const content = document.createElement('template');
  content.innerHTML = html;
  return content.content.textContent || '';
}

function selectedTarget() {
  const selection = getEditorSelection();
  if (!selection?.rangeCount) return null;
  const range = selection.getRangeAt(0);
  const field = element(range.startContainer)?.closest('anki-editable,[contenteditable="true"]');
  if (!field || field.closest('.cm-editor') || !field.contains(range.endContainer)) return null;
  return { field, selection, range: range.cloneRange(), snapshot: field.innerHTML };
}

function insertHtml(target, html) {
  if (!target.field.isConnected || target.field.innerHTML !== target.snapshot) return false;
  const selection = {
    getRangeAt: () => target.range,
    removeAllRanges: () => target.selection.removeAllRanges(),
    addRange: (range) => target.selection.addRange(range),
  };

  return Boolean(
    editWithNativeUndo(target.field, selection, (_field, stagedSelection) => {
      const insertion = stagedSelection.getRangeAt(0);
      const fragment = insertion.createContextualFragment(html);
      const lastInsertedNode = fragment.lastChild;
      if (!lastInsertedNode) return false;
      insertion.deleteContents();
      insertion.insertNode(fragment);
      insertion.setStartAfter(lastInsertedNode);
      insertion.collapse(true);
      stagedSelection.removeAllRanges();
      stagedSelection.addRange(insertion);
    }),
  );
}

function markdownBlocks(html, topic) {
  const container = document.createElement('div');
  container.innerHTML = html;
  const blocks = [...container.querySelectorAll('pre > code')].map((code, index) => ({
    index,
    source: code.textContent || '',
    language: code.dataset.language || getSyntaxLanguage(topic) || '',
    explicitLanguage: code.dataset.language || '',
  }));
  return { container, blocks };
}

export function pasteMarkdownAsHtml(markdown) {
  if (!markdown) return false;
  const target = selectedTarget();
  if (!target) return false;

  const html = markdownToHtml(markdown);
  const { container, blocks } = markdownBlocks(html, getTopicText());
  if (!blocks.length) return insertHtml(target, container.innerHTML);

  const id = String(++requestId);
  pending.set(id, target);
  globalThis.pycmd?.(
    `${MESSAGE_PREFIX}${JSON.stringify({
      id,
      html: container.innerHTML,
      codeBlocks: blocks.map(({ index, source, language, explicitLanguage }) => ({
        index,
        source,
        language,
        explicitLanguage,
      })),
    })}`,
  );
  return true;
}

function applyMarkdownHighlightResult(id, html, renderedBlocks) {
  const target = pending.get(String(id));
  pending.delete(String(id));
  if (!target || typeof html !== 'string' || !Array.isArray(renderedBlocks)) return false;
  if (!target.field.isConnected || target.field.innerHTML !== target.snapshot) return false;

  const container = document.createElement('div');
  container.innerHTML = html;
  const budget = createClassificationBudget(100);
  for (const rendered of renderedBlocks) {
    if (!Number.isInteger(rendered.index) || typeof rendered.html !== 'string') continue;
    const code = container.querySelectorAll('pre > code')[rendered.index];
    if (!code || typeof rendered.language !== 'string') continue;
    const pre = code.closest('pre');
    pre.className = 'global-kit-code-block';
    pre.dataset.language = rendered.language;
    pre.dataset.lineNumbers = 'false';
    pre.dataset.lineStart = '1';
    pre.dataset.clozeMode = 'active';
    code.removeAttribute('class');
    code.removeAttribute('data-language');
    code.innerHTML = enhanceHighlightHtml(rendered.html, rendered.language, { budget });
  }

  return insertHtml(target, container.innerHTML);
}

function failMarkdownHighlight(id) {
  pending.delete(String(id));
}

export function installMarkdownHighlighting() {
  const api = (globalThis.ankiGlobalKitEditor ||= {});
  api.pasteMarkdownAsHtml = pasteMarkdownAsHtml;
  api.applyMarkdownHighlightResult = applyMarkdownHighlightResult;
  api.failMarkdownHighlight = failMarkdownHighlight;
}
