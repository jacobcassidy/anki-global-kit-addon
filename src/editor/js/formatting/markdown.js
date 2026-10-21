import { markdownToHtml } from '../../../cards/js/markdown/render.js';
import { getSyntaxLanguage, highlightCodeText } from '../../../cards/js/syntax-highlighting/tokenizer.js';
import { getEditorSelection } from '../helpers/selection.js';
import { editWithNativeUndo } from '../helpers/edit-transaction.js';

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

export function highlightMarkdownCodeBlocks(html, topicText = '') {
  const container = document.createElement('div');
  container.innerHTML = html;

  container.querySelectorAll('pre > code').forEach((code) => {
    const explicitLanguage = getSyntaxLanguage(code.dataset.language);
    const language = explicitLanguage || getSyntaxLanguage(topicText);
    if (!language) return;

    code.innerHTML = highlightCodeText(code.textContent || '', language);
    code.classList.add('syntax-highlights', `language-${language}`);
  });

  return container.innerHTML;
}

function insertMarkdown(markdown) {
  if (!markdown) return false;
  const selection = getEditorSelection();
  if (!selection?.rangeCount) return false;
  const range = selection.getRangeAt(0);
  const element = (node) => (node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement);
  const field = element(range.startContainer)?.closest('anki-editable,[contenteditable="true"]');
  if (!field || field.closest('.cm-editor') || !field.contains(range.endContainer)) return false;
  const html = highlightMarkdownCodeBlocks(markdownToHtml(markdown), getTopicText());
  if (!html) return false;

  return Boolean(
    editWithNativeUndo(field, selection, (stagedField, stagedSelection) => {
      const insertion = stagedSelection.getRangeAt(0);
      const fragment = insertion.createContextualFragment(html);
      const lastInsertedNode = fragment.lastChild;
      if (!lastInsertedNode) return false;
      insertion.deleteContents();
      insertion.insertNode(fragment);
      insertion.setStartAfter(lastInsertedNode);
      insertion.collapse(true);
      stagedSelection.addRange(insertion);
    }),
  );
}

export function pasteMarkdownAsHtml(markdown) {
  return insertMarkdown(markdown);
}
