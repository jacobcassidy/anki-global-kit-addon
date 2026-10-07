const BOUNDARY_ATTRIBUTE = 'data-anki-global-kit-edit-boundary';
const POSITION_ATTRIBUTE = 'data-anki-global-kit-edit-position';
const inputHandlers = new WeakMap();

function nodePath(root, node) {
  const path = [];
  for (let current = node; current !== root; current = current.parentNode) {
    path.unshift([...current.parentNode.childNodes].indexOf(current));
  }
  return path;
}

function nodeAt(root, path) {
  return path.reduce((node, index) => node.childNodes[index], root);
}

function copyRange(from, to, range) {
  const copy = document.createRange();
  copy.setStart(nodeAt(to, nodePath(from, range.startContainer)), range.startOffset);
  copy.setEnd(nodeAt(to, nodePath(from, range.endContainer)), range.endOffset);
  return copy;
}

function selectRange(selection, range) {
  selection.removeAllRanges();
  selection.addRange(range);
}

function cleanEditMarkers(field) {
  const start = field.querySelector(`[${POSITION_ATTRIBUTE}="start"]`);
  const end = field.querySelector(`[${POSITION_ATTRIBUTE}="end"]`);
  let range;
  if (start && end) {
    range = document.createRange();
    range.setStartBefore(start);
    range.setEndBefore(end);
  }
  for (const marker of field.querySelectorAll(`[${BOUNDARY_ATTRIBUTE}], [${POSITION_ATTRIBUTE}]`)) marker.remove();
  if (range) {
    const selection = field.getRootNode().getSelection?.() || window.getSelection();
    if (selection) selectRange(selection, range);
  }
}

/** Stage a formatting change away from the field and apply it as one native edit. */
export function editWithNativeUndo(field, selection, edit, onInput) {
  const originalRange = selection.getRangeAt(0).cloneRange();
  const clone = field.cloneNode(true);
  let plannedRange = copyRange(field, clone, originalRange);
  const stagedSelection = {
    getRangeAt: () => plannedRange,
    removeAllRanges() {},
    addRange(range) {
      plannedRange = range;
    },
  };
  const edited = edit(clone, stagedSelection, (node) =>
    node && field.contains(node) ? nodeAt(clone, nodePath(field, node)) : null,
  );
  if (edited === false) return null;
  if (!clone.contains(plannedRange.startContainer) || !clone.contains(plannedRange.endContainer)) return null;
  if (clone.innerHTML === field.innerHTML) {
    selectRange(selection, copyRange(clone, field, plannedRange));
    return { resolveNode: (node) => nodeAt(field, nodePath(clone, node)) };
  }

  // Bookmarks retain exact caret/selection boundaries when Blink normalizes
  // text nodes during insertion. Remove them before Anki reads the input.
  for (const position of ['end', 'start']) {
    const bookmark = document.createElement('span');
    bookmark.setAttribute(POSITION_ATTRIBUTE, position);
    bookmark.textContent = '\u2060';
    const point = plannedRange.cloneRange();
    point.collapse(position === 'start');
    point.insertNode(bookmark);
  }
  if (!inputHandlers.has(field)) {
    field.addEventListener(
      'input',
      (event) => {
        cleanEditMarkers(field);
        const handler = inputHandlers.get(field);
        handler.notified = true;
        handler.onInput?.(event, field);
      },
      true,
    );
  }
  const handler = { onInput, notified: false };
  inputHandlers.set(field, handler);
  field.focus();

  // Include boundaries outside the old formatting so insertHTML can remove
  // an outer CODE, UL, or OL wrapper. Undo restores these boundaries too.
  const boundary = document.createElement('span');
  boundary.setAttribute(BOUNDARY_ATTRIBUTE, '');
  boundary.textContent = '\u2060';
  field.prepend(boundary);
  field.append(boundary.cloneNode(true));
  const replacement = document.createRange();
  replacement.selectNodeContents(field);
  selectRange(selection, replacement);
  let inserted = false;
  try {
    inserted = document.execCommand('insertHTML', false, clone.innerHTML);
  } finally {
    cleanEditMarkers(field);
    if (!inserted) selectRange(selection, originalRange);
  }
  if (!inserted) return null;
  if (!handler.notified) {
    field.dispatchEvent(new InputEvent('input', { bubbles: true, composed: true, inputType: 'insertFromPaste' }));
  }
  return {};
}
