import { getEditorSelection } from '../helpers/selection.js';
import { editWithNativeUndo } from '../helpers/edit-transaction.js';

const INLINE_TAGS = new Set([
  'A',
  'ABBR',
  'AUDIO',
  'B',
  'BDI',
  'BDO',
  'BR',
  'CITE',
  'CODE',
  'DATA',
  'EM',
  'I',
  'IMG',
  'INPUT',
  'KBD',
  'LABEL',
  'MARK',
  'Q',
  'S',
  'SAMP',
  'SELECT',
  'SMALL',
  'SPAN',
  'STRONG',
  'SUB',
  'SUP',
  'TEXTAREA',
  'TIME',
  'U',
  'VAR',
  'VIDEO',
  'WBR',
]);

// Interpret clipboard plain text as markup and insert the resulting fragment
// into the active Anki field.
export function pasteHtml(html) {
  if (!html) return false;
  const selection = getEditorSelection();
  if (!selection?.rangeCount) return false;
  const range = selection.getRangeAt(0);
  const element = (node) => (node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement);
  const field = element(range.startContainer)?.closest('anki-editable,[contenteditable="true"]');
  if (!field || !field.contains(range.endContainer)) return false;

  // Parse as a document so wrappers and head metadata are handled according
  // to HTML rules, then insert only the document's visible body content.
  const parsedDocument = new DOMParser().parseFromString(html, 'text/html');
  const body = parsedDocument.body;
  const isBlock = (node) => node.nodeType === Node.ELEMENT_NODE && !INLINE_TAGS.has(node.tagName);
  for (const child of [...body.childNodes]) {
    if (child.nodeType !== Node.TEXT_NODE || !/^\s*$/u.test(child.data)) continue;
    const previous = child.previousSibling;
    const next = child.nextSibling;
    if ((!previous || isBlock(previous)) && (!next || isBlock(next))) child.remove();
  }
  if (!body.innerHTML) return false;
  return !!editWithNativeUndo(field, selection, (stagedField, stagedSelection) => {
    const insertion = stagedSelection.getRangeAt(0);
    // Remove Anki's empty-field caret placeholder before inserting a block.
    if (stagedField.childNodes.length === 1 && stagedField.firstChild.nodeName === 'BR') {
      stagedField.firstChild.remove();
      insertion.setStart(stagedField, 0);
      insertion.collapse(true);
    }
    const fragment = insertion.createContextualFragment(body.innerHTML);
    const lastInsertedNode = fragment.lastChild;
    insertion.deleteContents();
    insertion.insertNode(fragment);
    insertion.setStartAfter(lastInsertedNode);
    insertion.collapse(true);
    stagedSelection.addRange(insertion);
  });
}
