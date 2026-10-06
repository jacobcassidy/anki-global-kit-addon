import { getEditorSelection, getFieldInputSelection } from '../helpers/selection.js';
import { getEditorSettings } from '../settings.js';
import { normalizeSpaceBeforeCode } from './code-spaces.js';
import { editWithNativeUndo } from '../helpers/edit-transaction.js';

const ENTRY_ATTRIBUTE = 'data-anki-global-kit-inline-code-entry';
const entryCodes = new WeakSet();

// Inline code formatting action.
export function toggleInlineCode(begin = '<code>', end = '</code>') {
  const pendingAnchor = toggleInlineCode.cancelEntry?.(false);
  toggleInlineCode.cancelExit?.();
  let selection = getEditorSelection() || getFieldInputSelection();
  if (!selection || !selection.rangeCount) {
    // A completely empty shadow field may have no native caret range.
    let active = document.activeElement;
    while (active?.shadowRoot?.activeElement) active = active.shadowRoot.activeElement;
    const field = active?.closest?.('anki-editable,[contenteditable="true"]');
    const codes = field?.querySelectorAll('code');
    if (
      codes?.length === 1 &&
      !field.textContent.replace(/[\s\u200b\ufeff]/gu, '') &&
      !field.querySelector('img,hr,input,video,audio,iframe,object,svg,canvas')
    ) {
      field.focus();
      selection = field.getRootNode().getSelection?.() || window.getSelection();
      if (!selection) return;
      const range = document.createRange();
      range.setStartBefore(codes[0]);
      range.collapse(true);
      selection.removeAllRanges();
      selection.addRange(range);
    }
    if (!selection?.rangeCount) return;
  }
  const element = (node) => (node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement);
  const originalRange = selection.getRangeAt(0);
  const field = element(originalRange.startContainer)?.closest('anki-editable, [contenteditable="true"]');
  if (!field || field.closest('.cm-editor') || !field.contains(originalRange.endContainer)) return;
  const effects = {};
  const result = editWithNativeUndo(
    field,
    selection,
    (clone, stagedSelection, resolveNode) => {
      const anchor = resolveNode(pendingAnchor);
      if (anchor?.data.startsWith('\u200b')) anchor.deleteData(0, 1);
      formatInlineCodeContent(clone, stagedSelection, begin, end, effects);
      if (effects.entryAnchor) effects.entryAnchor.parentElement.setAttribute(ENTRY_ATTRIBUTE, '');
    },
    restoreInlineCodeEntry,
  );
  if (!result && pendingAnchor?.isConnected && pendingAnchor.data.startsWith('\u200b')) {
    armInlineCodeEntry(pendingAnchor);
  }
  if (result?.resolveNode && effects.exitCode) {
    const code = result.resolveNode(effects.exitCode);
    armInlineCodeExit(code, selection, (range) => {
      selection.removeAllRanges();
      selection.addRange(range);
    });
  }
}

function restoreInlineCodeEntry(event, field) {
  const codes = [...field.querySelectorAll(`[${ENTRY_ATTRIBUTE}]`)];
  if (event.inputType === 'historyRedo' || event.inputType === 'historyUndo') {
    codes.push(...[...field.querySelectorAll('code')].filter((code) => entryCodes.has(code)));
  }
  for (const code of new Set(codes)) {
    code.removeAttribute(ENTRY_ATTRIBUTE);
    entryCodes.add(code);
    let anchor = [...code.childNodes].find(
      (node) => node.nodeType === Node.TEXT_NODE && node.data.startsWith('\u200b'),
    );
    if (!anchor && !code.textContent && !code.querySelector('br,img,hr,input,video,audio,iframe,object,svg,canvas')) {
      anchor = document.createTextNode('\u200b');
      code.append(anchor);
    }
    if (anchor) {
      const selection = field.getRootNode().getSelection?.() || window.getSelection();
      if (!selection) continue;
      const range = document.createRange();
      range.setStart(anchor, 0);
      range.setEnd(anchor, 1);
      selection.removeAllRanges();
      selection.addRange(range);
      armInlineCodeEntry(anchor);
    }
  }
}

function formatInlineCodeContent(field, selection, begin, end, effects) {
  const range = selection.getRangeAt(0);
  const element = (node) => (node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement);
  const codeAt = (node) => element(node)?.closest('code');
  const empty = (fragment) => !fragment.textContent && !fragment.querySelector('br,img,hr,input,video,audio');
  const select = (r) => {
    selection.removeAllRanges();
    selection.addRange(r);
  };

  const emptyCode = (node) =>
    node?.nodeName === 'CODE' &&
    !node.textContent.replace(/[\s\u200b\ufeff]/gu, '') &&
    !node.querySelector('img,hr,input,video,audio,iframe,object,svg,canvas');
  let code = codeAt(range.startContainer);
  // Chromium can represent an empty inline caret at the parent boundary.
  if (!code && range.collapsed && range.startContainer.nodeType === Node.ELEMENT_NODE) {
    const next = range.startContainer.childNodes[range.startOffset];
    const previous = range.startContainer.childNodes[range.startOffset - 1];
    if (emptyCode(next)) code = next;
    else if (emptyCode(previous)) code = previous;
  }
  if (!code && range.collapsed && range.startContainer.nodeType === Node.TEXT_NODE) {
    const text = range.startContainer;
    if (range.startOffset === text.length && emptyCode(text.nextSibling)) code = text.nextSibling;
    else if (range.startOffset === 0 && emptyCode(text.previousSibling)) code = text.previousSibling;
  }
  if (range.collapsed) {
    if (code) {
      if (emptyCode(code)) {
        const container = range.startContainer;
        const offset = range.startOffset;
        const inside = code.contains(container);
        const parent = code.parentNode;
        const index = Array.prototype.indexOf.call(parent.childNodes, code);
        const children = Array.from(code.childNodes);
        code.replaceWith(...children);
        if (inside && container !== code) {
          range.setStart(container, offset);
        } else {
          range.setStart(parent, index + (container === code ? offset : 0));
        }
        range.collapse(true);
        select(range);
        return;
      }
      const tail = range.cloneRange();
      tail.setEnd(code, code.childNodes.length);
      if (empty(tail.cloneContents())) {
        // Move to the boundary after the code. Chromium may pull typed text
        // back into the code, so arm a one-insertion boundary workaround.
        const outside = code.nextSibling;
        if (outside?.nodeType === Node.TEXT_NODE) range.setStart(outside, 0);
        else range.setStartAfter(code);
        range.collapse(true);
        select(range);
        effects.exitCode = code;
        return;
      }
      // A caret inside code toggles the entire element, including spaces.
      const prefix = document.createRange();
      prefix.selectNodeContents(code);
      prefix.setEnd(range.startContainer, range.startOffset);
      const contents = document.createRange();
      contents.selectNodeContents(code);
      toggleInlineCodeWord({ range: contents, offset: prefix.toString().length }, code, selection);
      return;
    }
    // A caret inside a word toggles that word without requiring selection.
    // At word boundaries keep the existing empty-code insertion behavior.
    const block = element(range.startContainer)?.closest(
      'div,p,pre,blockquote,li,td,th,h1,h2,h3,h4,h5,h6,anki-editable',
    );
    const word = inlineCodeWordAtCaret(range, block || field, false);
    if (word && word.offset > 0 && (word.offset < word.range.toString().length || word.beforePunctuation)) {
      toggleInlineCodeWord(word, null, selection);
      return;
    }
    code = document.createElement('code');
    // A real character keeps Chromium's native typing inside an empty inline element.
    const anchor = document.createTextNode('\u200b');
    code.append(anchor);
    range.insertNode(code);
    if (getEditorSettings().anki_editor_normalize_code_spaces) normalizeSpaceBeforeCode(code);
    // Replacing the selected placeholder records its removal in the same
    // native transaction as typing, so Undo can restore an empty code span.
    range.setStart(anchor, 0);
    range.setEnd(anchor, 1);
    select(range);
    effects.entryAnchor = anchor;
    return;
  }

  if (begin === '<code>' && end === '</code>' && toggleMixedInlineCodeSelection(field, range, selection)) {
    return;
  }

  // Handle both selection of the element and selection of its text contents.
  if (!code && range.startContainer === range.endContainer && range.endOffset === range.startOffset + 1) {
    const child = range.startContainer.childNodes[range.startOffset];
    if (child?.nodeName === 'CODE') code = child;
  }
  if (code) {
    const contents = document.createRange();
    contents.selectNodeContents(code);
    const before = contents.cloneRange();
    const after = contents.cloneRange();
    const coversStart = range.compareBoundaryPoints(Range.START_TO_START, contents) <= 0;
    const coversEnd = range.compareBoundaryPoints(Range.END_TO_END, contents) >= 0;
    if (!coversStart && code.contains(range.startContainer)) before.setEnd(range.startContainer, range.startOffset);
    if (!coversEnd && code.contains(range.endContainer)) after.setStart(range.endContainer, range.endOffset);
    if ((coversStart || empty(before.cloneContents())) && (coversEnd || empty(after.cloneContents()))) {
      const first = code.firstChild;
      const last = code.lastChild;
      if (first) {
        code.replaceWith(...Array.from(code.childNodes));
        range.setStartBefore(first);
        range.setEndAfter(last);
        select(range);
      } else {
        range.setStartBefore(code);
        range.collapse(true);
        code.remove();
        select(range);
      }
    }
    return;
  }

  // Preserve the existing block-aware wrapping behavior for plain selections.
  wrap2.call({ node: field }, begin, end, selection);
}

/** Toggle mixed selections without nesting code or moving surrounding markup. */
function toggleMixedInlineCodeSelection(field, range, selection) {
  if (!field || !field.contains(range.endContainer)) return false;
  const element = (node) => (node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement);
  const segments = [];
  const walker = document.createTreeWalker(field, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
  let node;
  while ((node = walker.nextNode())) {
    const isText = node.nodeType === Node.TEXT_NODE;
    if (isText ? !node.length : !node.matches('br,img,hr,input,video,audio,iframe,object,embed,svg,canvas')) continue;
    // Media contents belong to the media element, rather than another text run.
    if (element(node.parentNode)?.closest('video,audio,iframe,object,embed,svg,canvas')) continue;
    const selected = document.createRange();
    if (isText) selected.selectNodeContents(node);
    else selected.selectNode(node);
    if (
      range.compareBoundaryPoints(Range.END_TO_START, selected) >= 0 ||
      range.compareBoundaryPoints(Range.START_TO_END, selected) <= 0
    )
      continue;
    if (isText && range.startContainer === node) selected.setStart(node, range.startOffset);
    if (isText && range.endContainer === node) selected.setEnd(node, range.endOffset);
    if (selected.collapsed) continue;
    segments.push({ range: selected, code: element(node)?.closest('code') });
  }
  const uncoded = segments.filter((segment) => !segment.code);
  const codes = [...new Set(segments.map((segment) => segment.code).filter(Boolean))];
  if (!uncoded.length) {
    // A mixed selection becomes several code elements. A second invocation
    // removes only their selected portions, preserving code outside the range.
    if (codes.length < 2) return false;
    removeCodeFromSelection(codes, range, selection);
    return true;
  }
  if (!(
    codes.length ||
    element(range.startContainer)?.closest('code') ||
    element(range.endContainer)?.closest('code') ||
    range.cloneContents().querySelector('code')
  ))
    return false;

  // Work backwards so splitting a text node does not move later boundaries.
  for (const segment of uncoded.reverse()) {
    const code = document.createElement('code');
    segment.range.surroundContents(code);
    segment.range.selectNodeContents(code);
  }
  const first = segments[0].range;
  const last = segments[segments.length - 1].range;
  const restored = document.createRange();
  restored.setStart(first.startContainer, first.startOffset);
  restored.setEnd(last.endContainer, last.endOffset);
  selection.removeAllRanges();
  selection.addRange(restored);
  return true;
}

function removeCodeFromSelection(codes, range, selection) {
  const replacements = codes
    .filter((code) => !code.parentElement.closest('code'))
    .map((code) => {
      const contents = document.createRange();
      contents.selectNodeContents(code);
      const selected = contents.cloneRange();
      if (code.contains(range.startContainer)) selected.setStart(range.startContainer, range.startOffset);
      if (code.contains(range.endContainer)) selected.setEnd(range.endContainer, range.endOffset);
      const before = contents.cloneRange();
      before.setEnd(selected.startContainer, selected.startOffset);
      const after = contents.cloneRange();
      after.setStart(selected.endContainer, selected.endOffset);
      const left = code.cloneNode(false),
        right = code.cloneNode(false);
      left.append(before.cloneContents());
      right.append(after.cloneContents());
      const fragment = selected.cloneContents();
      for (const nested of [...fragment.querySelectorAll('code')].reverse()) nested.replaceWith(...nested.childNodes);
      return { code, left, right, fragment, first: fragment.firstChild, last: fragment.lastChild };
    });
  const hasContent = (node) =>
    node.textContent || node.querySelector('br,img,hr,input,video,audio,iframe,object,embed,svg,canvas');
  for (const { code, left, right, fragment } of [...replacements].reverse()) {
    code.replaceWith(...(hasContent(left) ? [left] : []), fragment, ...(hasContent(right) ? [right] : []));
  }
  const restored = document.createRange();
  restored.setStartBefore(replacements[0].first);
  restored.setEndAfter(replacements[replacements.length - 1].last);
  selection.removeAllRanges();
  selection.addRange(restored);
}

// Remove only our temporary caret anchor, before Anki saves the first real edit.
function armInlineCodeEntry(anchor) {
  const root = anchor.getRootNode();
  const controller = new AbortController();
  const options = { capture: true, signal: controller.signal };
  const cancel = (removeAnchor = true) => {
    if (removeAnchor && anchor.isConnected && anchor.data.startsWith('\u200b')) anchor.deleteData(0, 1);
    controller.abort();
    if (toggleInlineCode.cancelEntry === cancel) toggleInlineCode.cancelEntry = null;
    return anchor;
  };
  toggleInlineCode.cancelEntry = cancel;
  root.addEventListener(
    'beforeinput',
    (event) => {
      if (!event.inputType.startsWith('insert') || !anchor.isConnected || !anchor.data.startsWith('\u200b')) return;
      const selection = root.getSelection?.() || window.getSelection();
      if (!selection?.rangeCount) return;
      const current = selection.getRangeAt(0);
      const index = [...anchor.parentNode.childNodes].indexOf(anchor);
      if (
        current.collapsed &&
        ((current.startContainer === anchor && current.startOffset <= 1) ||
          (current.startContainer === anchor.parentNode && [index, index + 1].includes(current.startOffset)))
      ) {
        const replacement = document.createRange();
        replacement.setStart(anchor, 0);
        replacement.setEnd(anchor, 1);
        selection.removeAllRanges();
        selection.addRange(replacement);
      } else if (!current.intersectsNode(anchor)) cancel();
    },
    options,
  );
  root.addEventListener(
    'input',
    (event) => {
      // Ignore the synthetic input used to announce creation of the code element.
      if (event.inputType || event.isTrusted) cancel();
    },
    options,
  );
  root.addEventListener('focusout', cancel, options);
}

// Chromium can pull a boundary caret back into the preceding <code>.
// Make code non-editable only during the next native insertion, then restore it.
function armInlineCodeExit(code, selection, select) {
  const root = code.getRootNode();
  const controller = new AbortController();
  const options = { capture: true, signal: controller.signal };
  const original = code.getAttribute('contenteditable');
  let locked = false;
  const restore = () => {
    if (locked) {
      if (original === null) code.removeAttribute('contenteditable');
      else code.setAttribute('contenteditable', original);
      locked = false;
    }
  };
  const cancel = () => {
    restore();
    controller.abort();
    if (toggleInlineCode.cancelExit === cancel) toggleInlineCode.cancelExit = null;
  };
  toggleInlineCode.cancelExit = cancel;
  root.addEventListener('pointerdown', cancel, options);
  root.addEventListener('focusout', cancel, options);
  root.addEventListener(
    'keydown',
    (event) => {
      if (
        [
          'ArrowLeft',
          'ArrowRight',
          'ArrowUp',
          'ArrowDown',
          'Home',
          'End',
          'PageUp',
          'PageDown',
          'Escape',
          'Tab',
          'Backspace',
          'Delete',
        ].includes(event.key)
      )
        cancel();
    },
    options,
  );
  root.addEventListener(
    'beforeinput',
    (event) => {
      if (!event.inputType.startsWith('insert') || !code.isConnected || !selection.rangeCount) {
        cancel();
        return;
      }
      const current = selection.getRangeAt(0);
      const boundary = document.createRange();
      boundary.setStartAfter(code);
      boundary.collapse(true);
      const atBoundary =
        current.collapsed &&
        (current.compareBoundaryPoints(Range.START_TO_START, boundary) === 0 ||
          (current.startContainer === code.nextSibling && current.startOffset === 0));
      let atCodeEnd = false;
      if (current.collapsed && code.contains(current.startContainer)) {
        const tail = current.cloneRange();
        tail.setEnd(code, code.childNodes.length);
        atCodeEnd = !tail.toString() && !tail.cloneContents().querySelector('br,img,hr');
      }
      if (!atBoundary && !atCodeEnd) {
        cancel();
        return;
      }
      locked = true;
      code.setAttribute('contenteditable', 'false');
      select(boundary);
      root.addEventListener('input', cancel, options);
      setTimeout(cancel, 0);
    },
    options,
  );
}

// Find a token delimited by whitespace or prose punctuation, crossing inline formatting but not blocks.
function inlineCodeWordAtCaret(caret, scope, insideCode) {
  if (!scope) return null;
  const segments = [];
  let text = '',
    position = 0;
  const blocks = 'div,p,pre,blockquote,ul,ol,li,table,h1,h2,h3,h4,h5,h6,br,img,hr';
  function visit(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      const start = text.length;
      const probe = document.createRange();
      probe.selectNodeContents(node);
      if (caret.startContainer === node) position = start + caret.startOffset;
      else if (probe.compareBoundaryPoints(Range.END_TO_END, caret) <= 0) position = start + node.length;
      segments.push({ node, start, end: start + node.length });
      text += node.data;
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      if (
        node !== scope &&
        (node.matches(blocks) || (!insideCode && node.matches('code')) || node.contentEditable === 'false')
      ) {
        text += ' ';
        return;
      }
      for (const child of node.childNodes) visit(child);
    }
  }
  visit(scope);
  let start = position,
    end = position;
  while (start > 0 && !/[\s,.:;?]/u.test(text[start - 1])) start--;
  while (end < text.length && !/[\s,.:;?]/u.test(text[end])) end++;
  if (start === end) return null;
  const first = segments.find((s) => s.start <= start && s.end > start);
  const last = segments.find((s) => s.start < end && s.end >= end);
  if (!first || !last) return null;
  const range = document.createRange();
  range.setStart(first.node, start - first.start);
  range.setEnd(last.node, end - last.start);
  return { range, offset: position - start, beforePunctuation: position === end && /[,.:;?]/u.test(text[end] || '') };
}

function toggleInlineCodeWord(word, code, selection) {
  const range = word.range;
  let fragment;
  if (code) {
    const before = document.createRange();
    before.selectNodeContents(code);
    before.setEnd(range.startContainer, range.startOffset);
    const after = document.createRange();
    after.selectNodeContents(code);
    after.setStart(range.endContainer, range.endOffset);
    const left = code.cloneNode(false),
      right = code.cloneNode(false);
    left.append(before.cloneContents());
    right.append(after.cloneContents());
    fragment = range.cloneContents();
    // Also remove old nested code wrappers within this token.
    for (const nested of Array.from(fragment.querySelectorAll('code')).reverse())
      nested.replaceWith(...nested.childNodes);
    const replacement = document.createDocumentFragment();
    if (left.textContent || left.querySelector('br,img,hr,input,video,audio')) replacement.append(left);
    const nodes = Array.from(fragment.childNodes);
    replacement.append(fragment);
    if (right.textContent || right.querySelector('br,img,hr,input,video,audio')) replacement.append(right);
    code.replaceWith(replacement);
    restore(nodes);
  } else {
    const wrapper = document.createElement('code');
    wrapper.append(range.extractContents());
    range.insertNode(wrapper);
    const caret = document.createRange();
    caret.setStartAfter(wrapper);
    caret.collapse(true);
    selection.removeAllRanges();
    selection.addRange(caret);
    return;
  }
  function restore(nodes) {
    let remaining = word.offset;
    const texts = [];
    function collect(node) {
      if (node.nodeType === Node.TEXT_NODE) texts.push(node);
      else for (const child of node.childNodes) collect(child);
    }
    nodes.forEach(collect);
    for (const node of texts) {
      if (remaining <= node.length) {
        const caret = document.createRange();
        caret.setStart(node, remaining);
        caret.collapse(true);
        selection.removeAllRanges();
        selection.addRange(caret);
        return;
      }
      remaining -= node.length;
    }
  }
}

// Block-aware wrapping adapted from Wrapper meta-addon and Anki PR #3038.
function wrap2(begin, end, selection) {
  const { node: base } = this;
  const range = selection.getRangeAt(0);
  if (!range) {
    return;
  }

  // Inline code must stay inside the selected block, even at its edges.
  // Keep the original range instead of expanding it around the parent div.
  if (begin === '<code>' && end === '</code>' && !range.collapsed) {
    const preview = range.cloneContents();
    const blocks = 'div,p,pre,blockquote,ul,ol,li,table,h1,h2,h3,h4,h5,h6';
    if (!preview.querySelector(blocks)) {
      const code = document.createElement('code');
      code.appendChild(range.extractContents());
      range.insertNode(code);
      range.setStartAfter(code);
      range.collapse(true);
      selection.removeAllRanges();
      selection.addRange(range);
      return;
    }
  }

  // The staged field is detached. Keep field boundaries inside it and only
  // expand around ancestors that have a parent to anchor the range to.
  let startParent = range.startContainer.parentNode;
  if (
    range.startContainer !== base &&
    startParent?.parentNode &&
    startParent !== base &&
    startParent.tagName !== 'ANKI-EDITABLE' &&
    startParent.firstChild === range.startContainer &&
    range.startOffset === 0
  ) {
    range.setStartBefore(startParent);
  }

  let endParent = range.endContainer.parentNode;
  if (
    range.endContainer !== base &&
    endParent?.parentNode &&
    endParent !== base &&
    endParent.tagName !== 'ANKI-EDITABLE' &&
    endParent.lastChild === range.endContainer &&
    ((range.endContainer.nodeType !== Node.ELEMENT_NODE &&
      range.endOffset === range.endContainer.textContent?.length) ||
      (range.endContainer.nodeType === Node.ELEMENT_NODE && range.endOffset === range.endContainer.childNodes.length))
  ) {
    range.setEndAfter(endParent);
  }
  let expand;
  do {
    expand = false;
    if (startParent instanceof ShadowRoot || endParent instanceof ShadowRoot) {
      break;
    }

    if (
      startParent?.parentNode &&
      startParent.parentNode !== base &&
      startParent.parentNode.tagName !== 'ANKI-EDITABLE' &&
      startParent.parentNode.firstChild === startParent &&
      range.isPointInRange(startParent.parentNode, startParent.parentNode.childNodes.length)
    ) {
      startParent = startParent.parentNode;
      range.setStartBefore(startParent);
      expand = true;
    }
    if (
      endParent?.parentNode &&
      endParent.parentNode !== base &&
      endParent.parentNode.tagName !== 'ANKI-EDITABLE' &&
      endParent.parentNode.lastChild === endParent &&
      range.isPointInRange(endParent.parentNode, 0)
    ) {
      endParent = endParent.parentNode;
      range.setEndAfter(endParent);
      expand = true;
    }
    if (
      range.endOffset === 0 &&
      range.endContainer !== base &&
      range.endContainer.parentNode &&
      range.endContainer.tagName !== 'ANKI-EDITABLE'
    ) {
      range.setEndBefore(range.endContainer);
      expand = true;
    }
  } while (expand);

  const fragment = range.extractContents();
  if (fragment.childNodes.length === 0) {
    const container = document.createElement('div');
    container.innerHTML = begin + end;
    range.insertNode(container.firstChild);
  } else {
    const div = document.createElement('div');
    for (const node of Array.from(fragment.childNodes)) {
      div.appendChild(node);
    }
    div.innerHTML = begin + div.innerHTML + end;
    for (const node of div.childNodes) {
      range.insertNode(node);
    }
  }
}
