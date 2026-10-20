import { markdownToHtml } from '../../../cards/js/markdown/render.js';
import { getEditorSelection } from '../helpers/selection.js';
import { editWithNativeUndo } from '../helpers/edit-transaction.js';

function insertMarkdown(markdown, requireSelection) {
  if (!markdown) return false;
  const selection = getEditorSelection();
  if (!selection?.rangeCount) return false;
  const range = selection.getRangeAt(0);
  if (requireSelection && (range.collapsed || !range.toString())) return false;
  const element = (node) => (node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement);
  const field = element(range.startContainer)?.closest('anki-editable,[contenteditable="true"]');
  if (!field || field.closest('.cm-editor') || !field.contains(range.endContainer)) return false;
  const html = markdownToHtml(markdown);
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

export function convertSelectedMarkdownToHtml() {
  const selection = getEditorSelection();
  if (!selection?.rangeCount) return false;
  const range = selection.getRangeAt(0);
  return insertMarkdown(range.toString(), true);
}

export function pasteMarkdownAsHtml(markdown) {
  return insertMarkdown(markdown, false);
}
