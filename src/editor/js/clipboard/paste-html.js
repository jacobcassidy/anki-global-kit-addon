import { getEditorSelection } from '../helpers/selection.js';

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
  const selection = getEditorSelection();
  if (!selection?.rangeCount) return false;
  const range = selection.getRangeAt(0);
  const element = (node) => (node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement);
  const field = element(range.startContainer)?.closest('anki-editable,[contenteditable="true"]');
  if (!field || !field.contains(range.endContainer)) return false;

  // Anki's empty editable field uses a lone BR as its caret placeholder. If
  // left in place, inserting a block before it produces a visible trailing BR.
  if (field.childNodes.length === 1 && field.firstChild.nodeName === 'BR' && !field.textContent.trim()) {
    field.firstChild.remove();
    range.setStart(field, 0);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
  }

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
  const fragment = range.createContextualFragment(body.innerHTML);
  const lastInsertedNode = fragment.lastChild;
  range.deleteContents();
  range.insertNode(fragment);
  if (lastInsertedNode) {
    range.setStartAfter(lastInsertedNode);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
  }
  field.dispatchEvent(
    new InputEvent('input', {
      bubbles: true,
      composed: true,
      inputType: 'insertFromPaste',
    }),
  );
  return true;
}
