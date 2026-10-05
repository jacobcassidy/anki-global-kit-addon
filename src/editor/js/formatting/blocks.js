import { getEditorSelection } from '../helpers/selection.js';
import { getEditorSettings } from '../settings.js';

const FIELD = 'anki-editable,[contenteditable="true"]';
const BLOCK = 'li,div,p,pre,h1,h2,h3,h4,h5,h6,blockquote';
const isList = (node) => node?.matches?.('ul,ol');
const elementOf = (node) => (node?.nodeType === 1 ? node : node?.parentElement);
const BOUNDARY = '[data-anki-global-kit-edit-boundary]';
const trackedFields = new WeakSet();

function clonePoint(field, clone, node, offset) {
  const path = [];
  for (let current = node; current !== field; current = current.parentNode) {
    path.unshift([...current.parentNode.childNodes].indexOf(current));
  }
  return [path.reduce((current, index) => current.childNodes[index], clone), offset];
}

function textOffset(root, node, offset) {
  const range = document.createRange();
  range.selectNodeContents(root);
  range.setEnd(node, offset);
  return range.toString().length;
}

function boundaryAt(root, offset, forward = false) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node;
  let last;
  while ((node = walker.nextNode())) {
    if (offset < node.length || (offset === node.length && !forward)) return [node, offset];
    offset -= node.length;
    last = node;
  }
  return last ? [last, last.length] : [root, 0];
}

function rangeAt(root, start, end, forward = []) {
  const range = document.createRange();
  range.setStart(...boundaryAt(root, start, forward[0]));
  range.setEnd(...boundaryAt(root, end, forward[1]));
  return range;
}

function ownContent(item) {
  return [...item.childNodes].filter((node) => !isList(node));
}

function normalizeLists(root) {
  // Chromium's indent command places a nested UL/OL directly under another
  // list. Attach it to the preceding item before splitting or converting runs.
  for (const list of root.querySelectorAll('ul,ol')) {
    for (const child of [...list.children]) {
      if (isList(child) && child.previousElementSibling?.matches('li')) {
        child.previousElementSibling.append(child);
      }
    }
  }
}

function overlaps(range, node) {
  if (!node.textContent && node.nodeName !== 'BR' && !node.childNodes.length) return false;
  const other = document.createRange();
  other.selectNodeContents(node);
  return (
    range.compareBoundaryPoints(Range.END_TO_START, other) < 0 &&
    range.compareBoundaryPoints(Range.START_TO_END, other) > 0
  );
}

// Normalize loose text/BR rows only; existing blocks, lists, and inline markup survive.
function normalizeRows(root) {
  let row;
  for (const node of [...root.childNodes]) {
    if (node.nodeType === 1 && (node.matches(BLOCK) || isList(node))) {
      row = null;
      continue;
    }
    if (!row) {
      row = document.createElement('div');
      root.insertBefore(row, node);
    }
    if (node.nodeName === 'BR') {
      if (!row.childNodes.length) row.append(node);
      else node.remove();
      row = null;
    } else row.append(node);
  }
  if (!root.childNodes.length) root.append(document.createElement('div'));
}

function selectedBlocks(root, range) {
  if (range.collapsed) {
    const element = elementOf(range.startContainer);
    const block = element?.closest('li') || element?.closest(BLOCK);
    return [block && block !== root ? block : root.firstElementChild].filter(Boolean);
  }
  return [...root.querySelectorAll(BLOCK)].filter((block) => {
    // A list item owns its paragraphs but not its descendants' list items.
    if (block.closest('li') !== block && block.closest('li')) return false;
    if (block.matches('li')) return ownContent(block).some((node) => overlaps(range, node));
    if (block.querySelector(BLOCK)) return false;
    return overlaps(range, block);
  });
}

function listDepth(item) {
  let depth = 0;
  for (let parent = item.parentElement; parent; parent = parent.parentElement) {
    if (isList(parent)) depth += 1;
  }
  return depth;
}

function selectedLevel(blocks) {
  const items = blocks.filter((block) => block.matches('li'));
  if (!items.length) return blocks;
  const depth = Math.min(...items.map(listDepth));
  return items.filter((item) => listDepth(item) === depth);
}

function listShell(list, tag, index = 0) {
  const shell = document.createElement(tag);
  for (const attribute of list.attributes) {
    if (!['start', 'type', 'reversed'].includes(attribute.name) || tag === list.localName) {
      shell.setAttribute(attribute.name, attribute.value);
    }
  }
  if (tag === 'ol' && list.localName === 'ol' && index) {
    const start = Number(list.getAttribute('start') || (list.hasAttribute('reversed') ? list.children.length : 1));
    shell.start = start + (list.hasAttribute('reversed') ? -index : index);
  }
  return shell;
}

function convertItems(items, tag) {
  const chosen = new Set(items);
  const remove = items.every((item) => item.parentElement.localName === tag);
  for (const list of new Set(items.map((item) => item.parentElement))) {
    const fragment = document.createDocumentFragment();
    let run;
    let previousTag;
    [...list.children].forEach((item, index) => {
      const targetTag = chosen.has(item) ? (remove ? null : tag) : list.localName;
      if (!targetTag) {
        const block = document.createElement('div');
        block.append(...item.childNodes);
        fragment.append(block);
        run = null;
      } else {
        if (!run || previousTag !== targetTag) {
          run = listShell(list, targetTag, index);
          fragment.append(run);
        }
        run.append(item);
      }
      previousTag = targetTag;
    });
    list.replaceWith(fragment);
  }
}

function indentation(block) {
  return (block.textContent.match(/^[ \t\u00a0]*/) || [''])[0].replace(/\t/g, '    ').length;
}

function listFromRows(blocks, tag) {
  let stack = [];
  let previous;
  for (const block of blocks) {
    if (!block.textContent.trim() && blocks.length > 1) continue;
    const depth = indentation(block);
    // Separate runs when the selection crosses containers or unselected rows.
    if (!previous || previous.nextSibling !== block || previous.parentNode !== block.parentNode) stack = [];
    while (stack.length && stack[stack.length - 1].depth > depth) stack.pop();
    if (!stack.length || stack[stack.length - 1].depth < depth) {
      const list = document.createElement(tag);
      const parent = stack[stack.length - 1];
      if (parent) parent.item.append(list);
      else {
        block.before(list);
        if (depth) list.style.marginInlineStart = `${depth}ch`;
      }
      stack.push({ depth, list, item: null });
    }
    const item = document.createElement('li');
    for (const attribute of block.attributes) item.setAttribute(attribute.name, attribute.value);
    item.append(...block.childNodes);
    // Literal leading whitespace becomes structural nesting, retaining rich inline nodes.
    let remaining = (item.textContent.match(/^[ \t\u00a0]*/) || [''])[0].length;
    const walker = document.createTreeWalker(item, NodeFilter.SHOW_TEXT);
    let text;
    while (remaining && (text = walker.nextNode())) {
      const removed = Math.min(remaining, text.length);
      text.deleteData(0, removed);
      remaining -= removed;
    }
    stack[stack.length - 1].list.append(item);
    stack[stack.length - 1].item = item;
    previous = block;
    // Keep the old row as a temporary position anchor until the run is complete.
  }
  for (const block of blocks) if (!block.childNodes.length) block.remove();
}

function quoteBlocks(blocks) {
  const remove = blocks.every(
    (block) =>
      block.matches('blockquote') ||
      block.parentElement?.matches('blockquote') ||
      (block.matches('li') && ownContent(block).every((node) => node.nodeName === 'BLOCKQUOTE')),
  );
  for (const block of blocks) {
    if (remove) {
      const quote = block.matches('blockquote')
        ? block
        : block.parentElement?.matches('blockquote')
          ? block.parentElement
          : block.querySelector(':scope > blockquote');
      if (quote) quote.replaceWith(...quote.childNodes);
    } else if (block.matches('li')) {
      if (ownContent(block).every((node) => node.nodeName === 'BLOCKQUOTE')) continue;
      const quote = document.createElement('blockquote');
      block.prepend(quote);
      quote.append(...ownContent(block).filter((node) => node !== quote));
    } else {
      if (block.matches('blockquote') || block.parentElement?.matches('blockquote')) continue;
      const quote = document.createElement('blockquote');
      if (block.matches('div')) {
        // Keep the indentation container outside the quote.
        quote.append(...block.childNodes);
        block.append(quote);
      } else {
        block.replaceWith(quote);
        quote.append(block);
      }
    }
  }
}

/** Prepare the HTML away from the live editor; commit it through native undo. */
export function formatBlockContent(root, range, format) {
  normalizeRows(root);
  normalizeLists(root);
  const blocks = selectedBlocks(root, range);
  if (!blocks.length) return false;
  if (format === 'blockquote') quoteBlocks(blocks);
  else {
    const selected = selectedLevel(blocks);
    if (selected[0]?.matches('li')) convertItems(selected, format === 'ordered-list' ? 'ol' : 'ul');
    else listFromRows(selected, format === 'ordered-list' ? 'ol' : 'ul');
  }
  return true;
}

export function toggleEditorBlock(format) {
  const selection = getEditorSelection();
  if (!selection?.rangeCount) return false;
  const range = selection.getRangeAt(0);
  const field = elementOf(range.startContainer)?.closest(FIELD);
  if (!field || field.closest('.cm-editor') || !field.contains(range.endContainer)) return false;
  const start = textOffset(field, range.startContainer, range.startOffset);
  const end = textOffset(field, range.endContainer, range.endOffset);
  const clone = field.cloneNode(true);
  const startPoint = clonePoint(field, clone, range.startContainer, range.startOffset);
  const endPoint = clonePoint(field, clone, range.endContainer, range.endOffset);
  normalizeRows(clone);
  normalizeLists(clone);
  const cloneRange = document.createRange();
  const resolvePoint = (point, offset) =>
    point[0] !== clone && clone.contains(point[0])
      ? [
          point[0],
          Math.min(point[1], point[0].nodeType === Node.TEXT_NODE ? point[0].length : point[0].childNodes.length),
        ]
      : boundaryAt(clone, offset);
  cloneRange.setStart(...resolvePoint(startPoint, start));
  cloneRange.setEnd(...resolvePoint(endPoint, end));
  const points = [cloneRange.startContainer, cloneRange.endContainer].map((node, index) => ({
    node,
    offset: index ? cloneRange.endOffset : cloneRange.startOffset,
    length: node.nodeType === Node.TEXT_NODE ? node.length : 0,
  }));
  if (!formatBlockContent(clone, cloneRange, format)) return false;
  const offsets = points.map(({ node, offset, length }) =>
    clone.contains(node)
      ? textOffset(
          clone,
          node,
          node.nodeType === Node.TEXT_NODE ? Math.max(0, offset - (length - node.length)) : offset,
        )
      : start,
  );
  field.focus();
  // Blink otherwise keeps the old outer UL/OL when replacing an entire list.
  // Invisible inline boundaries force replacement to include that container.
  // Native undo restores the boundaries too, so remove them before Anki's input
  // listener reads the field. Redo still uses the browser's original transaction.
  if (!trackedFields.has(field)) {
    trackedFields.add(field);
    field.addEventListener(
      'input',
      () => {
        for (const boundary of field.querySelectorAll(BOUNDARY)) boundary.remove();
      },
      true,
    );
  }
  const firstBoundary = document.createElement('span');
  firstBoundary.setAttribute('data-anki-global-kit-edit-boundary', '');
  firstBoundary.textContent = '\u2060';
  field.prepend(firstBoundary);
  field.append(firstBoundary.cloneNode(true));
  const replacement = document.createRange();
  replacement.selectNodeContents(field);
  selection.removeAllRanges();
  selection.addRange(replacement);
  // execCommand is the editor's native editing primitive. Direct DOM replacement
  // would bypass its undo history and input notification.
  if (!document.execCommand('insertHTML', false, clone.innerHTML)) {
    for (const boundary of field.querySelectorAll(BOUNDARY)) boundary.remove();
    selection.removeAllRanges();
    selection.addRange(range);
    return false;
  }
  selection.removeAllRanges();
  selection.addRange(
    rangeAt(
      field,
      ...offsets,
      points.map(({ offset }) => offset === 0),
    ),
  );
  return true;
}

function stop(event) {
  event.preventDefault();
  event.stopImmediatePropagation();
}

export function installBlockFormatting() {
  document.addEventListener(
    'click',
    (event) => {
      const button = event.composedPath().find((node) => node?.matches?.('button'));
      if (!button || button.disabled) return;
      const labels = globalThis.ankiGlobalKitEditorListLabels || {};
      let shortcuts;
      try {
        shortcuts = globalThis.require?.('anki/shortcuts');
      } catch {
        // Older editor builds can use the Qt shortcut labels supplied by Python.
      }
      const format = Object.keys(labels).find((key) => {
        const command = key === 'unordered-list' ? 'Control+,' : 'Control+.';
        const label = shortcuts?.getPlatformString?.(command) || labels[key];
        return button.title.endsWith(`(${label})`);
      });
      if (format && toggleEditorBlock(format)) stop(event);
    },
    true,
  );
  document.addEventListener(
    'keydown',
    (event) => {
      if (event.isComposing || event.altKey) return;
      const field = event.composedPath().find((node) => node?.matches?.(FIELD));
      if (!field) return;
      const primary = /Mac|iPhone|iPad/.test(navigator.platform) ? event.metaKey : event.ctrlKey;
      if (primary && !event.shiftKey && [',', '.', '/'].includes(event.key)) {
        const format = { ',': 'unordered-list', '.': 'ordered-list', '/': 'blockquote' }[event.key];
        if (toggleEditorBlock(format)) stop(event);
      } else if (
        event.key === 'Tab' &&
        !event.ctrlKey &&
        !event.metaKey &&
        getEditorSettings().anki_editor_tab_indentation
      ) {
        const selection = getEditorSelection();
        if (elementOf(selection?.focusNode)?.closest('li')) {
          stop(event);
          document.execCommand(event.shiftKey ? 'outdent' : 'indent');
        } else if (!event.shiftKey) {
          stop(event);
          document.execCommand('insertText', false, '    ');
        }
      }
    },
    true,
  );
}
